"""Offline infrastructure/oracle checks. Zero real model requests."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import runner as r
import evaluation as e
from fixtures import CASES, BOUNDARIES, SLOTS, OWNER_SCHEMA, RECEIVER_SCHEMA


def owner(action='handoff',artifact='complete artifact'):
    return dict(action=action,reason='bounded reason',artifact=artifact,remaining=[],work_performed='actual described change')

class Response:
    status_code=200
    def __init__(self,parsed,usage=True): self.parsed=parsed; self.usage=usage
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def iter_lines(self):
        final={'id':'offline-only','status':'completed','model':'offline-fake','reasoning':{'effort':'high'},
          'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(self.parsed)}]}],
          'usage':{'input_tokens':10,'output_tokens':20,'total_tokens':30} if self.usage else None}
        yield b'data: '+json.dumps({'type':'response.completed','response':final}).encode()

class MVPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.out=Path(self.tmp.name)/'run'; r.initialize(self.out)
    def tearDown(self): self.tmp.cleanup()
    def advance(self,responses,steps=1):
        with patch.dict(r.os.environ,{'OPENAI_API_KEY':'offline-placeholder'}),patch.object(r.requests,'post',side_effect=[Response(x) for x in responses]),contextlib.redirect_stdout(io.StringIO()):
            return r.advance(self.out,steps)
    def skip_probe(self):
        s=r.load(self.out/'state.json'); s['probe']='ok'; r.save_state(self.out,s)
    def test_two_distinct_reference_implementations(self):
        for code in (e.F_REFERENCE_1,e.F_REFERENCE_2): self.assertEqual(e.f_check(code)['passed'],48)
    def test_original_record_wide_badge_bug_detected(self):
        bad=e.F_REFERENCE_1.replace("rid == record['approved_revision']","record['approved_revision'] is not None")
        result=e.f_check(bad); self.assertEqual(result['status'],'fail'); self.assertGreater(len(result['failures']),0)
    def test_reader_draft_leak_detected(self):
        bad=e.F_REFERENCE_1.replace("role == 'reader' or view == 'published'","view == 'published'")
        self.assertEqual(e.f_check(bad)['status'],'fail')
    def test_input_mutation_detected(self):
        bad=e.F_REFERENCE_1.replace("    rid =","    record['touched'] = True\n    rid =")
        self.assertEqual(e.f_check(bad)['status'],'fail')
    def test_code_guard_rejects_import(self):
        self.assertEqual(e.f_check('import os\n'+e.F_REFERENCE_1)['status'],'execution_error')
    def test_no_tools_and_fixed_model_config(self):
        self.assertEqual(r.CONFIG['tools'],[]); self.assertEqual(r.CONFIG['automatic_retries'],0)
        self.assertEqual(r.CONFIG['max_requests'],27)
    def test_frozen_manifest_detects_change(self):
        m=r.load(self.out/'manifest.json'); m['inputs']['runner.py']='tampered'
        (self.out/'manifest.json').write_text(json.dumps(m))
        with self.assertRaises(ValueError): r.validate_freeze(self.out)
    def test_research_never_writes_product_outputs(self):
        for path in (r.REPO,r.REPO/'skills',r.REPO.parent):
            with self.assertRaises(ValueError): r.validate_out(path)
    def test_knowledge_recipient_cannot_see_raw_source_or_owner_history(self):
        t=copy.deepcopy(r.load(self.out/'state.json')['trials'][1]); t['artifact']='bounded handoff'
        prompt=r.receiver_prompt(t)
        self.assertNotIn("def execute",prompt); self.assertNotIn('GUIDANCE',prompt)
        self.assertNotIn('owner_response',prompt); self.assertNotIn('evaluation.py',prompt)
    def test_owner_does_not_see_hidden_queries_or_oracle(self):
        t=r.load(self.out/'state.json')['trials'][1]
        prompt=r.owner_prompt(t)
        self.assertNotIn('Q3:',prompt); self.assertNotIn('F_REFERENCE',prompt); self.assertNotIn('K_RUBRIC',prompt)
    def test_probe_counted(self):
        state=self.advance([{'ok':True}]); self.assertEqual(state['calls'],1); self.assertEqual(state['probe'],'ok')
    def test_handoff_then_fresh_recipient(self):
        self.skip_probe(); state=self.advance([owner(),{'content':e.F_REFERENCE_1,'unresolved':[]}],2)
        self.assertEqual(state['trials'][0]['status'],'completed'); self.assertEqual(state['calls'],2)
    def test_refinement_uses_current_actual_artifact(self):
        self.skip_probe(); s=r.load(self.out/'state.json'); s['current']=2; r.save_state(self.out,s)
        state=self.advance([owner('refine','new S artifact')]); t=state['trials'][2]
        self.assertEqual(t['status'],'owner_pending'); self.assertIn('new S artifact',r.owner_prompt(t))
        self.assertEqual(t['owner_calls'],1)
    def test_need_input_and_stop_do_not_invoke_recipient(self):
        for action in ('need_input','stop'):
            with tempfile.TemporaryDirectory() as td:
                out=Path(td)/'x'; r.initialize(out); s=r.load(out/'state.json');s['probe']='ok';r.save_state(out,s)
                with patch.dict(r.os.environ,{'OPENAI_API_KEY':'offline'}),patch.object(r.requests,'post',return_value=Response(owner(action))) as post,contextlib.redirect_stdout(io.StringIO()):
                    state=r.advance(out,1)
                self.assertEqual(state['trials'][0]['status'],action); self.assertEqual(post.call_count,1)
    def test_last_refine_is_not_forced_handoff(self):
        self.skip_probe(); s=r.load(self.out/'state.json');s['current']=2;r.save_state(self.out,s)
        state=self.advance([owner('refine','a'),owner('refine','b'),owner('refine','c')],3)
        self.assertEqual(state['trials'][2]['status'],'unconverged'); self.assertEqual(state['calls'],3)
    def test_single_call_refine_retains_unconverged(self):
        self.skip_probe(); state=self.advance([owner('refine')]); self.assertEqual(state['trials'][0]['status'],'unconverged')
    def test_duplicate_request_cannot_be_resent(self):
        self.skip_probe(); self.advance([owner()]); s=r.load(self.out/'state.json')
        with self.assertRaisesRegex(RuntimeError,'already exists'):
            r.request(self.out,s,'F-A-owner1','prompt',OWNER_SCHEMA,100)
        self.assertEqual(r.load(self.out/'state.json')['calls'],1)
    def test_request_cap_is_hard(self):
        s=r.load(self.out/'state.json');s['calls']=27
        with self.assertRaisesRegex(RuntimeError,'request budget'): r.check_budget(s,100)
    def test_bad_schema_keeps_response_and_does_not_repair(self):
        self.skip_probe(); state=self.advance([{'action':'handoff'}]);self.assertEqual(state['trials'][0]['status'],'request_failed')
        path=self.out/state['trials'][0]['owner_results'][0]
        self.assertTrue((path/'response.txt').exists());self.assertEqual(r.load(path/'result.json')['status'],'failed')
    def test_unknown_usage_reserves_ceiling(self):
        self.skip_probe()
        with patch.dict(r.os.environ,{'OPENAI_API_KEY':'offline'}),patch.object(r.requests,'post',return_value=Response(owner(),usage=False)),contextlib.redirect_stdout(io.StringIO()):
            state=r.advance(self.out,1)
        self.assertEqual(state['output_charged'],12000)
    def test_inflight_interruption_blocks_resend(self):
        s=r.load(self.out/'state.json');s['inflight']={'call':1};r.save_state(self.out,s)
        with self.assertRaisesRegex(RuntimeError,'interrupted'):r.advance(self.out,1)
    def test_boundaries_and_reference_review_surface(self):
        self.assertEqual([BOUNDARIES[x]['expected'] for x in ('F-ready','K-guarantee','S-missing')],['handoff','need_input','need_input'])
        self.assertEqual(len(e.K_REFERENCES),2);self.assertEqual(len(e.S_REFERENCES),2)
        self.assertEqual(set(CASES),{'F','K','S'});self.assertEqual(len(SLOTS),12)

if __name__=='__main__':unittest.main()
