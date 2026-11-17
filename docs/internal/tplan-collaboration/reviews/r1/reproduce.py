from __future__ import annotations
import copy
import json
import os
import sys
from pathlib import Path
from unittest import mock

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'skills/tplan/scripts'))
from tests.tplan.test_collaboration_runtime import CollaborationRuntimeTests
import collaboration as col
import collaboration_runtime as api
import tplan_runtime as rt

def fresh():
    c=CollaborationRuntimeTests()
    c.setUp()
    return c

def feedback(c, event, delegation='D1', round_no=1, artifact='h1', source='C'):
    p={'coordinator_generation':1,'source_event_ref':event,
       'source_thread_ref':'thread-c' if source=='C' else 'thread-b',
       'source_host_ref':'local','source_role_id':source,'delegation_id':delegation,
       'round':round_no,'contract_version':f'contract-r{round_no}',
       'artifact_ref':f'artifact://{artifact}','artifact_digest':col.digest({'artifact':artifact}),
       'summary':event,'original_ref':f'thread://source/{event}','attachment_refs':[]}
    r,k=c.mutate('feedback.record',p)
    assert k==0,r
    return r['data']['feedback_id']

def resolution(c,fid,delegation='D1',round_no=1,artifact='h1',
               disposition='adopted',verdict='PASS',complete=False,review_task='T1'):
    return {'coordinator_generation':1,'feedback_id':fid,'disposition':disposition,
      'goal_relation':{'responsibility':'Own acceptance','acceptance_ids':['A1'],
        'rationale':'Scope and version checked for the original objective'},
      'evidence_refs':[],
      'artifact_ref':{'ref':f'artifact://{artifact}','digest':col.digest({'artifact':artifact}),
        'contract_version':f'contract-r{round_no}','round':round_no} if disposition=='adopted' else None,
      'review':{'reviewer_id':'C','delegation_id':delegation,'round':round_no,
        'contract_version':f'contract-r{round_no}','artifact_ref':f'artifact://{artifact}',
        'artifact_digest':col.digest({'artifact':artifact}),
        'scope_refs':[f'scope://{review_task}'],'verdict':verdict,
        'rationale':'Observed review of this artifact'} if verdict else None,
      'task_changes':[{'task_id':review_task,'status':'completed'}] if complete else [],
      'new_tasks':[],'next_delegation':None,'coordination':c.coordination()}

def run(name,fn):
    c=fresh()
    try:
        outcome=fn(c)
        print(json.dumps({'probe':name,'outcome':outcome},ensure_ascii=False),flush=True)
    finally:c.doCleanups()

def retired(c):
    c.enable();c.prepare();c.dispatch(send_state='not_sent',execution_state='not_started')
    c.prepare(delegation_id='D2',intent_id='I2',round_no=2)
    c.dispatch(intent_id='I2',execution_state='completed')
    f=feedback(c,'new-round-reviewed',delegation='D2',round_no=2,artifact='h2')
    r,k=c.mutate('feedback.resolve',resolution(c,f,delegation='D2',round_no=2,artifact='h2',complete=True))
    return {'code':r['code'],'status':r['status'],'message':r['message'],
            'old_delegation_state':rt.read_mission(c.mission)['collaboration']['delegations']['D1']['status']}

def fail_after_pass(c):
    c.enable();c.prepare();c.dispatch(execution_state='completed')
    f=feedback(c,'review-pass')
    r,k=c.mutate('feedback.resolve',resolution(c,f))
    assert k==0,r
    rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Original A1 acceptance',
       'task_id':'T1','payload':{'acceptance_ids':['A1']}})
    f=feedback(c,'later-review-fail')
    r,k=c.mutate('feedback.resolve',resolution(c,f,disposition='answered',verdict='FAIL'))
    assert k==0,r
    rt.transition_task_status(c.mission,'T1','completed')
    s=rt.read_mission(c.mission)
    findings=col.completion_findings(s)
    s['mission']['status']='completed'
    rt.write_mission(c.mission,s)
    return {'reviews':[v['verdict'] for v in s['collaboration']['reviews'].values()],
       'completion_findings':findings,'mission_status':rt.read_mission(c.mission)['mission']['status']}

def review_transplant(c):
    c.enable();c.prepare();c.prepare(task_id='T2',delegation_id='D2',intent_id='I2',round_no=2)
    f=feedback(c,'review-about-D1')
    p=resolution(c,f,delegation='D2',round_no=2,disposition='answered',review_task='T2')
    r,k=c.mutate('feedback.resolve',p)
    s=rt.read_mission(c.mission)
    return {'code':r['code'],'message':r['message'],
      'source_feedback_delegation':s['collaboration']['feedback'][f]['delegation_id'],
      'stored_review_delegations':[x['delegation_id'] for x in s['collaboration']['reviews'].values()]}

def running_overlap(c):
    c.enable();c.prepare();c.dispatch(execution_state='running')
    f=feedback(c,'implementation-defect-before-worker-stopped',source='B')
    p=resolution(c,f,disposition='repair',verdict=None)
    p['next_delegation']=c.delegation_payload(delegation_id='D2',intent_id='I2',round_no=2)
    p['next_delegation'].pop('coordinator_generation')
    r,k=c.mutate('feedback.resolve',p)
    s=rt.read_mission(c.mission)
    return {'code':r['code'],'message':r['message'],
      'intents':{key:{'send_state':v['send_state'],'execution_state':v['execution_state']}
        for key,v in s['collaboration']['intents'].items()},
      'delegations':{key:v['status'] for key,v in s['collaboration']['delegations'].items()}}

def progress_routing(c):
    c.enable();c.prepare()
    c.mutate('coordination.checkpoint',{'coordinator_generation':1,**c.coordination()})
    feedback(c,'ordinary-progress-no-design-impact',source='B')
    pulse=rt.build_mission_pulse(c.mission,trigger='manual')
    v=c.snapshot()['data']['resume']
    return {'next_gate':pulse['mission_pulse']['next_gate'],
      'winning_signal':pulse['winning_candidate']['signal'],
      'priority_class':pulse['winning_candidate']['priority_class'],
      'focus':v['focus_task_id'],'next_action':v['next_action']}

def stale_returned_snapshot(c):
    r=c.enable()
    advertised=r['data']['expected_snapshot']
    actual=c.snapshot()['data']['expected_snapshot']
    response,k=c.mutate('delegation.prepare',c.delegation_payload(),expected_snapshot=advertised)
    return {'advertised_equals_actual':advertised==actual,'next_command_code':response['code']}

def recovery_before_identity(c):
    c.enable()
    with mock.patch.object(rt,'_recover_pending_mission_transaction_unlocked',side_effect=OSError('audit prepared crash')):
        r,k=c.mutate('delegation.prepare',c.delegation_payload(),command_id='prepared-to-recover')
    assert r['code']=='outcome_unknown',r
    journal=c.mission/'.mission-transaction.json'
    assert journal.exists()
    before=(c.mission/'mission.json').read_bytes()
    req={'protocol':col.PROTOCOL,'action':'runtime.recover','mission_id':'wrong-mission',
      'command_id':'prepared-to-recover','expected_build_hash':'sha256:'+'0'*64,
      'expected_snapshot':None,'payload':{}}
    r,k=api.execute(c.mission,req,principal=c.principal)
    after=(c.mission/'mission.json').read_bytes()
    return {'request_code':r['code'],'mission_changed_despite_rejection':before!=after,
      'pending_journal_after_rejection':journal.exists(),
      'D1_committed': 'D1' in json.loads(after)['collaboration']['delegations']}

def capacity(c):
    c.enable()
    trace=c.mission/'execution_trace.jsonl'
    data=trace.read_bytes().rstrip(b'\n')
    target=col.MAX_ARTIFACT-100
    trace.write_bytes(data+b' '*(target-len(data)-1)+b'\n')
    before=trace.stat().st_size
    r,k=c.mutate('coordination.checkpoint',{'coordinator_generation':1,**c.coordination()})
    after=trace.stat().st_size
    req={'protocol':col.PROTOCOL,'action':'snapshot.get','mission_id':'collaboration-mission',
      'command_id':'post-capacity','expected_build_hash':rt.runtime_fingerprint()['build_hash'],
      'expected_snapshot':None,'payload':{}}
    read,read_code=api.execute(c.mission,req,principal=c.principal)
    return {'write_code':r['code'],'before_bytes':before,'after_bytes':after,
      'limit':col.MAX_ARTIFACT,'later_read_code':read['code']}

for name,fn in [('retired_attempt_blocks_current_completion',retired),
  ('later_FAIL_hidden_by_old_PASS',fail_after_pass),
  ('review_transplanted_across_contracts',review_transplant),
  ('repair_releases_still_running_scope',running_overlap),
  ('progress_becomes_user_feedback_loopback',progress_routing),
  ('returned_snapshot_is_already_stale',stale_returned_snapshot),
  ('recovery_writes_before_request_identity_check',recovery_before_identity),
  ('trace_growth_bypasses_capacity',capacity)]:
    try:run(name,fn)
    except Exception as exc:
        print(json.dumps({'probe':name,'probe_error':type(exc).__name__+': '+str(exc)},ensure_ascii=False),flush=True)
