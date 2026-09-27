"""Offline controls for the compact direct router; synthetic decisions are not model scores."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json,tempfile,unittest,subprocess,shutil
from unittest.mock import patch
from experiments.jev_direct import router as r,pilot as p
from experiments.typed_decision.contracts import DecisionResult,BatchResult,ResolvedRuntime,ContractError,digest
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.session import read_record,RecoveryRequired
from experiments.typed_decision.relationship_runtime import _locked
REPO=Path(__file__).resolve().parents[1]
RAW={'documents':[{'id':'U','revision':'1','kind':'user','text':'请区分当前请求的结构判断与随后资源安排。'}],
     'conversation':[{'document_id':'U','role':'user','order':0,'author_ref':'fixture','source_ref':'fixture'}],
     'authority':{'risk':'low','mode':'read_only'}}
class Provider(TypeSafeJevProvider):
    is_live=False
    def __init__(self,overrides=None):super().__init__();self.overrides=overrides or {};self.states=[]
    def evaluate(self,specs,state,timeout):
        self.states.append(deepcopy(state));result={}
        for s in specs:
            if s.kind=='select':
                v=self.overrides.get(s.id, 'direct' if s.id=='MODE' else 'whole' if s.id.startswith('SCOPE.') else 'none')
                if v not in s.criteria:v=next(iter(s.criteria))
                u={'source':'provider_distribution','confidence':1,'probabilities':{k:float(k==v) for k in s.criteria}}
                result[s.id]=DecisionResult('ok',v,u)
            else:result[s.id]=DecisionResult('ok',self.overrides.get(s.id,0))
        return BatchResult(result,ResolvedRuntime('jev-1.13.0','TypeSafe'))
class RouterTests(unittest.TestCase):
    def setUp(self):self.pack=r.load_pack(REPO);self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def test_complete_catalog_preserved_in_original_state(self):
        s=r.initial_state(RAW,self.pack)
        self.assertEqual(len(s['routing_cards']),10);self.assertEqual(s['original_input'],RAW)
        self.assertNotIn('issues',s);self.assertNotIn('candidates',s)
    def test_source_manifest_is_bound(self):
        self.assertTrue(all(r.file_hash(REPO/f)==h for f,h in self.pack['source_sha256'].items()))
    def test_changed_canonical_source_rejected(self):
        with patch.object(r,'file_hash',return_value='bad'):
            with self.assertRaisesRegex(ContractError,'source_changed'):r.load_pack(REPO)
    def test_question_types_and_unique_ids(self):
        specs=r.questions(r.initial_state(RAW,self.pack),self.pack)
        self.assertEqual({s.kind for s in specs},{'select','assess_proposition','rate'})
        self.assertEqual(len({s.id for s in specs}),len(specs));self.assertEqual(len(specs),71)
    def test_request_below_existing_context_limit(self):
        state=r.initial_state(RAW,self.pack);self.assertLess(len(r.canonical(state)),60000)
    def test_no_llm_front_one_layer(self):
        provider=Provider();out=r.route(self.root/'r',RAW,REPO,'0'*64,provider)
        self.assertEqual(len(provider.states),1);self.assertEqual(out['pre_route_llm_calls'],0)
        self.assertEqual(out['methods'],{});self.assertTrue(out['answer_allowed'])
    def test_second_layer_exact_originals_and_all_cards(self):
        provider=Provider({'MODE':'judgment','READ.edsp':1,'ROLE.edsp':'primary'})
        out=r.route(self.root/'r',RAW,REPO,'0'*64,provider)
        self.assertEqual(len(provider.states),2);self.assertEqual(out['rounds'],2)
        a,b=provider.states;self.assertEqual(a['original_input'],b['original_input']);self.assertEqual(a['routing_cards'],b['routing_cards'])
        for path in self.pack['cards']['edsp']['sources']:self.assertEqual(b['additional_originals'][path],(REPO/path).read_text())
    def test_no_third_layer_even_when_read_requested_again(self):
        provider=Provider({'READ.edsp':1});r.route(self.root/'r',RAW,REPO,'0'*64,provider);self.assertEqual(len(provider.states),2)
    def test_no_permanent_method_pruning_after_second_read(self):
        q1=r.questions(r.initial_state(RAW,self.pack),self.pack)
        q2=r.questions(r.expanded_state(r.initial_state(RAW,self.pack),['edsp'],self.pack,REPO),self.pack)
        self.assertEqual([q.id for q in q1],[q.id for q in q2])
    def test_detail_budget_deferrals_visible(self):
        a={f'READ.{m}':{'status':'ok','value':1} for m in r.ROUTABLE}
        chosen,rest=r.requested_details(a,self.pack);self.assertEqual(len(chosen),2);self.assertEqual(len(rest),6)
    def test_detail_capacity_failure_is_not_silent_truncation(self):
        state=r.initial_state(RAW,self.pack);pack=deepcopy(self.pack);pack['policy']['max_state_bytes']=1
        with self.assertRaisesRegex(ContractError,'detail_capacity'):r.expanded_state(state,['edsp'],pack,REPO)
        self.assertEqual(state['additional_originals'],{})
    def test_joint_roles_and_order_consumed(self):
        provider=Provider({'MODE':'judgment','ROLE.edsp':'primary','ROLE.sra':'stage','REL.edsp.sra':'a_before_b'})
        out=r.route(self.root/'r',RAW,REPO,'0'*64,provider)
        self.assertEqual(set(out['methods']),{'edsp','sra'});self.assertLess(out['load_order'].index('edsp'),out['load_order'].index('sra'))
        self.assertEqual(len(r.execution_materials(out,self.pack,REPO)),4)
    def test_conditional_companion_is_really_loaded(self):
        provider=Provider({'MODE':'judgment','ROLE.mpg':'primary','COMPANION.mpg.sela':1,'REL.mpg.sela':'b_supports_a'})
        out=r.route(self.root/'r',RAW,REPO,'0'*64,provider)
        self.assertEqual(set(out['methods']),{'mpg','sela'});self.assertEqual(out['load_order'][0],'sela')
    def test_reciprocal_companion_present(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'MODE':'judgment','ROLE.sela':'primary','COMPANION.sela.mpg':1}))
        self.assertEqual(set(out['methods']),{'mpg','sela'})
        self.assertIn('skills/mpg/SKILL.md',r.execution_materials(out,self.pack,REPO))
    def test_low_companion_not_silent_waiver(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'MODE':'judgment','ROLE.mpg':'primary','COMPANION.mpg.sela':0.3}))
        self.assertIn('mpg',out['unconfirmed_companion_scopes'])
        self.assertIn('skills/sela/SKILL.md',r.execution_materials(out,self.pack,REPO))
    def test_global_acquire_preserves_independent_method(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'MODE':'acquire','ROLE.sra':'primary'}))
        self.assertIn('sra',out['methods']);self.assertTrue(out['answer_allowed'])
    def test_companion_in_other_scope_does_not_satisfy_this_scope(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'MODE':'judgment','ROLE.mpg':'primary','ROLE.sela':'primary','SCOPE.mpg':'U','SCOPE.sela':'whole','COMPANION.sela.mpg':0.3}))
        self.assertIn('sela',out['unconfirmed_companion_scopes'])
        self.assertEqual(out['companion_checks']['sela']['required_scope'],'whole')
    def test_dependency_cycle_has_no_executable_order(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'MODE':'judgment','ROLE.mpg':'primary','COMPANION.mpg.sela':1,'REL.mpg.sela':'a_before_b'}))
        self.assertTrue(out['ordering_unresolved']);self.assertIsNone(out['execution_order'])
        self.assertEqual(set(out['load_order']),{'sela','mpg'})
    def test_no_unconditional_companion(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'MODE':'judgment','ROLE.mpg':'primary'}))
        self.assertEqual(set(out['methods']),{'mpg'})
    def test_method_uncertainty_keeps_answer_path(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'MODE':'judgment','ROLE.edsp':'unclear'}))
        self.assertTrue(out['answer_allowed']);self.assertEqual(out['methods'],{})
    def test_independent_primitive_applies_without_method(self):
        out=r.route(self.root/'r',RAW,REPO,'0'*64,Provider({'PRIMITIVE.context':1,'THESIS':'context'}))
        self.assertEqual(out['methods'],{});self.assertIn('context',out['cognitive_obligations'])
    def test_provider_error_keeps_unknown_not_false(self):
        a={'MODE':{'status':'provider_error','value':None}};out=r.consume(a,self.pack)
        self.assertEqual(out['mode'],'unclear');self.assertTrue(out['answer_allowed'])
    def test_score_never_computes_route(self):
        a=r.consume({'EFFORT':{'status':'ok','value':3}},self.pack);self.assertEqual(a['methods'],{})
    def test_unsafe_authority_not_granted(self):
        raw=deepcopy(RAW);raw['authority']['mode']='write'
        with self.assertRaisesRegex(ContractError,'read_only'):r.initial_state(raw,self.pack)
    def test_raw_evidence_roles_and_order_validated(self):
        raw=deepcopy(RAW);raw['conversation'][0]['role']='assistant'
        with self.assertRaises(ContractError):r.initial_state(raw,self.pack)
    def test_reentry_uses_old_route_no_supplier_call(self):
        provider=Provider();a=r.route(self.root/'r',RAW,REPO,'0'*64,provider);b=r.route(self.root/'r',RAW,REPO,'0'*64,provider)
        self.assertEqual(a,b);self.assertEqual(len(provider.states),1)
    def test_missing_call_directory_rejected_without_repeat(self):
        import shutil
        provider=Provider();r.route(self.root/'r',RAW,REPO,'0'*64,provider)
        shutil.rmtree(self.root/'r/level-1')
        with self.assertRaises(ContractError):r.route(self.root/'r',RAW,REPO,'0'*64,provider)
        self.assertEqual(len(provider.states),1)
    def test_route_concurrency_blocked(self):
        with _locked(self.root/'r/.route-lock'):
            with self.assertRaises(RecoveryRequired):r.route(self.root/'r',RAW,REPO,'0'*64,Provider())

class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'trial'
        self.f=p.prepare(self.root,[{'id':'X','scenario':'A','raw':RAW,'provenance':'offline fixture'}],binary=shutil.which('codex'));self.commands=[];self.read_first=False
    def cli(self,cmd,prompt,env,timeout):
        self.commands.append(cmd);q=json.loads(prompt.split('\n',1)[1]);route=q['route'];loaded=q['loaded_materials']
        used=list(route['methods']) if route else []
        reply={'action':'answer','text':'这是离线夹具的完整答案。','used_methods':used,'read_paths':[],'route_objection':''}
        if self.read_first and not loaded:reply.update(action='read',text='',read_paths=['skills/edsp/SKILL.md'],used_methods=[])
        Path(cmd[cmd.index('-o')+1]).write_text(json.dumps(reply,ensure_ascii=False))
        out=[{'type':'thread.started','thread_id':'fixture-ctx'}, {'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':5}}]
        return subprocess.CompletedProcess(cmd,0,'\n'.join(json.dumps(e) for e in out),'')
    def run_arm(self,arm='direct',provider=None):
        with patch.object(p.wire,'_run_cli',side_effect=self.cli):return p.run_case(self.root,'X',arm,provider or Provider())
    def test_actual_direct_material_load_no_entry(self):
        out=self.run_arm(provider=Provider({'MODE':'judgment','ROLE.edsp':'primary'}))
        self.assertEqual(out['status'],'delivered');self.assertIsNone(out['actual_entry']);self.assertIn('skills/edsp/SKILL.md',out['actual_materials']);self.assertEqual(len(self.commands),1)
        q=read_record(self.root/'runs/X/direct/host/0/request.json')
        self.assertIsNone(q['entry_skill']);self.assertIsNone(q['method_catalog']);self.assertNotIn('skills/using-mindthus/SKILL.md',q['readable_paths'])
    def test_baseline_reads_normally_without_full_preload(self):
        self.read_first=True;out=self.run_arm('native');self.assertEqual(len(self.commands),2);self.assertIn('resume',self.commands[1])
        q=read_record(self.root/'runs/X/native/host/0/request.json');self.assertEqual(q['loaded_materials'],{});self.assertIsNotNone(q['entry_skill'])
    def test_finished_reentry_no_new_host_call(self):
        a=self.run_arm();b=self.run_arm();self.assertEqual(a,b);self.assertEqual(len(self.commands),1)
    def test_whole_host_directory_removal_rejected(self):
        import shutil
        self.run_arm();shutil.rmtree(self.root/'runs/X/direct/host')
        with self.assertRaises(ContractError):self.run_arm()
        self.assertEqual(len(self.commands),1)
    def test_changed_terminal_text_rejected(self):
        self.run_arm();path=self.root/'runs/X/direct/host/0/reply.json';path.write_text('{"text":"tampered"}')
        with self.assertRaises(ContractError):self.run_arm()
    def test_unknown_cli_not_resent(self):
        class Interrupted(BaseException):pass
        with patch.object(p.wire,'_run_cli',side_effect=Interrupted()):
            with self.assertRaises(Interrupted):p.run_case(self.root,'X','native')
        with patch.object(p.wire,'_run_cli') as call:
            with self.assertRaises(RecoveryRequired):p.run_case(self.root,'X','native')
            call.assert_not_called()
    def test_changed_freeze_between_arms_rejected(self):
        self.run_arm('native')
        f=read_record(self.root/'freeze.json');f['cases'][0]['raw']['documents'][0]['text']='changed input'
        data={'schema':'mindthus.decision-record.v1','payload':f,'sha256':digest(f)}
        (self.root/'freeze.json').write_text(json.dumps(data))
        with self.assertRaisesRegex(ContractError,'freeze_changed'):self.run_arm('direct')
        self.assertEqual(len(self.commands),1)
    def test_cross_arm_edit_of_freeze_and_its_anchor_is_rejected(self):
        self.run_arm('native');f=read_record(self.root/'freeze.json')
        f['cases'][0]['raw']['documents'][0]['text']='new input'
        anchor={'freeze_sha256':digest(f),'case_sha256':{c['id']:digest(c['raw']) for c in f['cases']}}
        for name,value in [('freeze.json',f),('freeze-binding.json',anchor)]:
            (self.root/name).write_text(json.dumps({'schema':'mindthus.decision-record.v1','payload':value,'sha256':digest(value)}))
        with self.assertRaisesRegex(ContractError,'cross_arm_identity_changed'):self.run_arm('direct')
        self.assertEqual(len(self.commands),1)
    def test_conflicted_order_requires_visible_degradation(self):
        out=self.run_arm(provider=Provider({'MODE':'judgment','ROLE.mpg':'primary','COMPANION.mpg.sela':1,'REL.mpg.sela':'a_before_b'}))
        self.assertEqual(out['status'],'host_reply_rejected');self.assertEqual(out['reason'],'pilot_order_conflict_requires_disclosure')
    def test_wall_includes_route_and_execution(self):
        out=self.run_arm();self.assertGreaterEqual(out['wall_seconds'],out['host_seconds'])
        self.assertEqual(out['freeze_sha256'],digest(self.f));self.assertEqual(out['raw_sha256'],digest(RAW))
    def test_declared_limit_rounds_two(self):self.assertEqual(self.f['max_jev_calls_per_case'],2)

if __name__=='__main__':unittest.main()
