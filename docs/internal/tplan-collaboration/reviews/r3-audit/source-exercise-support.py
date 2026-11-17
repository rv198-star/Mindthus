"""Controlled source-Agent exercise. Setup supplies fixtures; decisions are external inputs.

There is no run_all, scenario solver, predefined disposition or next-action sequence.
The source Codex Agent observes the inputs, then invokes the helpers with its choices.
All participants, authority events, artifacts, and host facts are isolated test fixtures.
"""
from __future__ import annotations
import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'skills/tplan/scripts'))
from tests.tplan.test_collaboration_runtime import CollaborationRuntimeTests
import collaboration as col
import collaboration_runtime as api
import tplan_runtime as rt

SOURCE='01a1e806-292f-76d0-af7e-f4786d70b3e1'
LOCATION=Path('/private/tmp/mindthus246-source-location')

def world():return Path(LOCATION.read_text().strip())
def directory(case):return world()/case/'collaboration-mission'
def view(case):
 s=rt.read_mission(directory(case))
 c=s.get('collaboration',{})
 return {'mission_id':s['mission']['id'],'objective':s['mission']['objective'],
  'acceptance':s['mission']['acceptance_evidence'],'mission_status':s['mission']['status'],
  'focus':s['active_task_id'],'tasks':{x['id']:{'title':x['title'],'status':x['status']} for x in s['tasks']},
  'collaboration_enabled':bool(c),'delegations':copy.deepcopy(c.get('delegations',{})),
  'intents':copy.deepcopy(c.get('intents',{})),
  'pending':[{k:f.get(k) for k in ('feedback_id','source_event_ref','source_role_id','kind','summary','artifact_ref','artifact_digest','delegation_id','round','contract_version')}
     for f in c.get('feedback',{}).values() if f['status']=='pending'],
  'adoptions':copy.deepcopy(c.get('adoptions',{})),'coordination':copy.deepcopy(c.get('coordination'))}

def log(event):
 event={'source_thread_id':SOURCE,'audited_head':'2753470fcd32ef2482e2af6126354e59aca57dcc',
   'evidence_class':'controlled_source_agent_exercise','real_peer_host_e2e':False,
   'recorded_at':rt.now_iso(),**event}
 p=world()/'source-actions.jsonl'
 with p.open('a') as out:out.write(json.dumps(event,ensure_ascii=False)+'\n')

def execute(case,action,payload,decision,source_call):
 d=directory(case);before=view(case)
 q={'protocol':col.PROTOCOL,'action':'snapshot.get','mission_id':'collaboration-mission',
   'command_id':'source-read','expected_build_hash':rt.runtime_fingerprint()['build_hash'],
   'expected_snapshot':None,'payload':{}}
 snap,k=api.execute(d,q,principal='source-auditor')
 assert k==0,snap
 n=sum(1 for _ in (world()/'source-actions.jsonl').open()) if (world()/'source-actions.jsonl').exists() else 0
 request={**q,'action':action,'command_id':f'source-{case}-{n}',
   'expected_snapshot':snap['data']['expected_snapshot'],'payload':payload}
 response,code=api.execute(d,request,principal='source-auditor')
 log({'case':case,'source_call':source_call,'decision':decision,'request':request,
      'response':response,'exit_code':code,'before':before,'after':view(case)})
 assert code==0,response
 return response

def resolve(case,event,disposition,rationale,next_action,source_call,*,review=False,adopt=False,changes=None,new_tasks=None,next_delegation=None,evidence_refs=()):
 s=rt.read_mission(directory(case));c=s['collaboration']
 f=next(v for v in c['feedback'].values() if v['source_event_ref']==event)
 artifact={'ref':f['artifact_ref'],'digest':f['artifact_digest'],
    'contract_version':f['contract_version'],'round':f['round']} if adopt else None
 r=None
 if review:
  d=c['delegations'][f['delegation_id']]
  r={'reviewer_id':f['source_role_id'],'delegation_id':f['delegation_id'],'round':f['round'],
   'contract_version':f['contract_version'],'artifact_ref':f['artifact_ref'],'artifact_digest':f['artifact_digest'],
   'scope_refs':d['required_review']['scope_refs'],'verdict':'PASS','rationale':rationale}
 payload={'coordinator_generation':1,'feedback_id':f['feedback_id'],'disposition':disposition,
   'goal_relation':{'responsibility':c['coordinator']['responsibility'],'acceptance_ids':['A1'],'rationale':rationale},
   'evidence_refs':list(evidence_refs),'artifact_ref':artifact,'review':r,'task_changes':changes or [],
   'new_tasks':new_tasks or [],'next_delegation':next_delegation,
   'coordination':{'state':'working','focus_task_id':'T2','gap_summary':'Need current outcome evidence for A1',
       'next_action':next_action,'resume_basis':['T2'],'waiting_on':[],'rationale':rationale}}
 return execute(case,'feedback.resolve',payload,{'disposition':disposition,'rationale':rationale,'next_action':next_action},source_call)

def inject(case,event,summary,kind='progress',source='B',artifact=None):
 d=directory(case)
 p={'coordinator_generation':1,'kind':kind,'source_event_ref':event,
    'source_thread_ref':'thread-c' if source=='C' else 'thread-b','source_host_ref':'local',
    'source_role_id':source,'delegation_id':'D1','round':1,'contract_version':'contract-r1',
    'artifact_ref':f'artifact://{artifact}' if artifact else None,
    'artifact_digest':col.digest({'artifact':artifact}) if artifact else None,
    'summary':summary,'original_ref':f'controlled-peer-fixture://{case}/{event}','attachment_refs':[]}
 return execute(case,'feedback.record',p,{'fixture_injection':True,'summary':summary},'fixture-input')

def observe(cases):
 context=json.loads((world()/'fixture-context.json').read_text())
 for case in cases:print(json.dumps({'case':case,'incoming_context':context[case],'state':view(case)},ensure_ascii=False))

def setup():
 w=Path(tempfile.mkdtemp(prefix='mindthus246-source-',dir='/private/tmp'));LOCATION.write_text(str(w))
 context={
 'T23':{'origin':'reference_material','text':'Other-session note for reference only. No delegation is requested.'},
 'T25':{'origin':'controlled_human_event_fixture','text':'For this test Mission, continue only in the current session. Preserve already-running D1 facts and do not dispatch new work.'},
 'T26':{'origin':'controlled_peer_fixtures','text':'B proposes a logging redesign; after your reply a cache/release-scope proposal will arrive.'},
 'T27':{'origin':'controlled_peer_fixture','text':'B provides a local fixture stack trace and asks A to take over debugging.'},
 'T28':{'origin':'controlled_peer_fixtures','text':'Five routine progress updates and three copies of a C concern; no new PASS is supplied yet.'},
 'T29':{'origin':'controlled_peer_then_human_fixtures','text':'C reproducer shows non-atomic two-file writes cannot satisfy replay. Current D1 remains running in workspace/T1; a disjoint replacement path can be designed. A later owner fixture will narrow the goal.'}}
 (w/'fixture-context.json').write_text(json.dumps(context,ensure_ascii=False,indent=2))
 for case in context:
  c=CollaborationRuntimeTests();c.setUp()
  try:
   if case!='T23':
    c.enable();c.prepare();c.dispatch(execution_state='completed' if case=='T28' else 'running')
    r,k=c.mutate('coordination.checkpoint',{'coordinator_generation':1,**c.coordination(focus='T2',next_action='Review the approved contract and verify the remaining A1 evidence')})
    assert k==0,r
   target=w/case/'collaboration-mission';target.parent.mkdir();shutil.copytree(c.mission,target)
  finally:c.doCleanups()
 inject('T26','logging-proposal','Please redesign logging before returning the assigned artifact.')
 inject('T27','debug-handoff','The local test fixture raises an import error. Please take over its debugging.','question')
 for i in range(5):inject('T28',f'progress-{i}',f'Routine progress {i}: no changed contract or artifact.')
 for i in range(3):inject('T28',f'concern-{i}','Same review concern: retry behavior still needs consolidated evidence.','review','C','h1')
 inject('T29','atomic-path-blocker','Controlled fault injection: first file changed and second stayed old after failure; the proposed non-atomic strategy cannot meet the replay criterion.','blocker','C')
 print(str(w));observe(list(context))

if __name__=='__main__':
 if sys.argv[1:] == ['setup']:setup()
 else:observe(sys.argv[1:] or ['T23','T25','T26','T27','T28','T29'])
