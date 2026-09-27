"""Export request bodies and exercise local wiring WITHOUT model/network calls.

Only first-layer Jev and initial native-host requests are outcome-independent.
Direct-host/second-layer requests in fixture traces are synthetic, never live plans.
"""
import argparse
import ast
import json
import platform
import socket
import subprocess
from pathlib import Path
from unittest.mock import patch
from . import pilot as p, router as r
from .serial import SerialRequests
from experiments.typed_decision.contracts import canonical, digest, project_context, require
from experiments.typed_decision.relationship_runtime import save
from experiments.typed_decision.session import read_record


def prepare(root,binary):
    from tests.test_jev_direct_router import Provider
    from tests.test_jev_direct_local import Clock
    root=Path(root).resolve()
    require(not root.exists(),'offline_fresh_root_required')
    docs=p.REPO/'docs/internal/research/typed-decision/jev-direct-v2'
    cases=json.loads((docs/'cases.json').read_text())
    parent=json.loads((docs/'preregistration.json').read_text())
    frozen=read_record(docs/'freeze.json')
    require(cases==frozen['cases'],'offline_parent_cases_changed')
    parent_commit='8e47cdacc63d3ad53c7fd0f64aa77d9a25e4ebd2'
    old_router=subprocess.check_output(['git','show',parent_commit+':experiments/jev_direct/router.py'],cwd=p.REPO,text=True)
    def functions(source):
        return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    old,current=functions(old_router),functions(Path(r.__file__).read_text())
    semantic_functions=['load_pack','validate_input','initial_state','questions','value','probability',
                        'requested_details','expanded_state','consume','execution_materials']
    require(all(old[n]==current[n] for n in semantic_functions),'offline_routing_semantics_changed')
    pack=r.load_pack(p.REPO)
    # No network: fail even if a future regression accidentally reaches a socket.
    with patch.object(socket.socket,'connect',side_effect=AssertionError('offline_network_forbidden')):
        f=p.prepare(root/'prepared',cases,binary=binary,serial_gap_seconds=60)
        fixture=p.prepare(root/'fixtures',cases,binary=binary,serial_gap_seconds=60)
        clock=Clock();gate=SerialRequests(root/'fixtures/serial',clock=clock.time,sleep=clock.sleep)
        result=[]
        for case in cases:
            cid=case['id'];raw=case['raw'];state=r.initial_state(raw,pack);specs=r.questions(state,pack)
            body={'model':'jev-1.13.0','state':project_context(specs,state),
                  'questions':r.TypeSafeJevProvider(choice_rounding=True).engine.questions(specs)}
            require(len(specs)==71,'offline_question_count')
            require(digest(raw)==parent['states'][cid]['raw_sha256'],'offline_raw_changed')
            require(len(canonical(state))==parent['states'][cid]['state_bytes'],'offline_state_changed')
            require(len(canonical({'state':state,'questions':[s.to_dict() for s in specs]}))==parent['states'][cid]['request_bytes'],'offline_request_changed')
            save(root/'requests'/cid/'direct-level-1.json',body)
            native_first=None
            for arm in parent['execution_order'][cid]:
                counter=[0]
                def fake(cmd,prompt,env,timeout):
                    nonlocal native_first
                    q=json.loads(prompt.split('\n',1)[1]);counter[0]+=1
                    if arm=='native' and counter[0]==1:
                        native_first=q
                        save(root/'requests'/cid/'native-initial.json',q)
                        save(root/'requests'/cid/'native-schema.json',json.loads(Path(cmd[cmd.index('--output-schema')+1]).read_text()))
                        (root/'requests'/cid/'native-prompt.txt').write_text(prompt)
                    reply={'action':'answer','text':'OFFLINE FIXTURE ONLY — not a model or user answer.',
                           'used_methods':list(q['route']['methods']) if q['route'] else ['edsp'],
                           'read_paths':[],'route_objection':''}
                    if arm=='native' and not q['loaded_materials']:
                        reply.update(action='read',text='',used_methods=[],read_paths=['skills/edsp/SKILL.md'])
                    Path(cmd[cmd.index('-o')+1]).write_text(json.dumps(reply))
                    context=cid+'-'+arm+'-fixture'
                    events=[{'type':'thread.started','thread_id':context},
                            {'type':'turn.completed','usage':{'input_tokens':0,'output_tokens':0}}]
                    clock.now+=2
                    return subprocess.CompletedProcess(cmd,0,'\n'.join(json.dumps(e) for e in events),'')
                provider=Provider({'READ.edsp':1,'ROLE.edsp':'primary','MODE':'judgment'})
                with patch.object(p.wire,'_run_cli',side_effect=fake):
                    out=p.run_case(root/'fixtures',cid,arm,provider,scheduler=gate)
                    before=counter[0]
                    again=p.run_case(root/'fixtures',cid,arm,provider,scheduler=gate)
                    require(out==again and counter[0]==before,'offline_resume_called_again')
                require(out['status']=='delivered','offline_fixture_failed')
                result.append({'case':cid,'arm':arm,'offline_fixture_status':out['status'],
                               'live_status':'UNRUN','raw_sha256':out['raw_sha256']})
            require(native_first['original_input']==body['state']['original_input'],'offline_cross_arm_input')
        # Synthetic routing provider itself is in-memory. These additional fake calls
        # verify that the same gate enforces Jev/host interleaving across a restart.
        for label in ['jev-fixture','host-fixture','jev-second-layer-fixture']:
            SerialRequests(root/'fixtures/serial',clock=clock.time,sleep=clock.sleep).call(label,lambda:None)
    unchanged=['max_jev_calls','max_jev_calls_per_case','reserve_per_jev_usd',
               'max_host_calls_per_arm','max_host_seconds_per_arm','host_timeout',
               'host_model','host_effort','semantic_retries','reviewer_calls_max','review_timeout_seconds']
    require(all(f[k]==frozen[k] for k in unchanged),'offline_budget_changed')
    require(f['source_hashes']==frozen['source_hashes'] and f['pack_sha256']==frozen['pack_sha256'],'offline_material_changed')
    gaps=[read_record(x)['actual_gap_seconds'] for x in sorted((root/'fixtures/serial').glob('*/intent.json'))]
    report={'schema':'mindthus.direct-local-offline.v1','parent_commit':'8e47cdacc63d3ad53c7fd0f64aa77d9a25e4ebd2',
            'parent_freeze_sha256':digest(frozen),'local_freeze_sha256':digest(f),
            'unchanged_semantic_functions':semantic_functions,
            'python':platform.python_version(),'platform':platform.platform(),'binary':f['binary'],
            'binary_sha256':f['binary_sha256'],'config_sha256':f['config_sha256'],
            'credentials_read':False,'external_model_calls':0,'business_status':'UNRUN',
            'quality':'NOT_AUDITED','net_benefit':'NOT_MEASURED','cases':result,
            'unchanged_budget_keys':unchanged,'simulated_gaps_seconds':gaps,
            'prepared_requests':'six exact first-layer Jev bodies and six initial native prompts/schemas',
            'conditional_requests':'direct host and layer 2 remain dependent on real Jev outputs; fixtures are NOT pending live requests'}
    save(root/'report.json',report)
    save(root/'index.json',{'files':{str(x.relative_to(root)):r.file_hash(x) for x in sorted(root.rglob('*')) if x.is_file() and not x.name.startswith('.')}})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--binary',type=Path,required=True)
    args=parser.parse_args();result=prepare(args.root,args.binary)
    print(json.dumps({'external_model_calls':0,'business_status':result['business_status'],'root':str(args.root)}))
