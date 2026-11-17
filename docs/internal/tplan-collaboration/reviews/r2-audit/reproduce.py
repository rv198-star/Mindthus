from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'skills/tplan/scripts'))
from tests.tplan.test_collaboration_runtime import CollaborationRuntimeTests
import collaboration as col
import tplan_runtime as rt

def record_acceptance(c):
 rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Initial current version A1 passed',
     'task_id':'T1','payload':{'acceptance_ids':['A1']}})

def reviewed(c):
 c.enable();c.prepare();c.dispatch(execution_state='completed')
 f=c.feedback(source='initial-pass',source_role='C',kind='review')
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],complete=True))
 assert k==0,r
 record_acceptance(c)

def retire_without_result(c):
 c.enable();c.prepare();c.dispatch(execution_state='failed')
 rt.transition_task_status(c.mission,'T1','completed')
 s=rt.read_mission(c.mission)
 return {'task_status':rt.find_task(s,'T1')['status'],
   'original_review_requirement':s['collaboration']['delegations']['D1']['required_review'],
   'adoptions':s['collaboration']['adoptions'],'reviews':s['collaboration']['reviews'],
   'collaboration_completion_findings':col.completion_findings(s)}

def nonmonotonic_current(c):
 c.enable();c.prepare(round_no=2);c.dispatch(execution_state='completed')
 f=c.feedback(source='old-round2-pass',source_role='C',round_no=2)
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],round_no=2,complete=False))
 assert k==0,r
 record_acceptance(c)
 c.prepare(delegation_id='D2',intent_id='I2',round_no=1)
 c.dispatch(intent_id='I2',execution_state='completed')
 f=c.feedback(source='new-round1-fail',delegation_id='D2',artifact='h2',source_role='C',round_no=1,kind='review')
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],delegation='D2',round_no=1,artifact='h2',verdict='FAIL'))
 assert k==0,r
 rt.transition_task_status(c.mission,'T1','completed')
 s=rt.read_mission(c.mission)
 findings=col.completion_findings(s)
 selected=col._task_current_delegation(s['collaboration'],'T1')
 s['mission']['status']='completed';rt.write_mission(c.mission,s)
 return {'current_selected_delegation':selected['delegation_id'],
    'review_outcomes':[(v['delegation_id'],v['verdict']) for v in s['collaboration']['reviews'].values()],
    'completion_findings':findings,'mission_status':rt.read_mission(c.mission)['mission']['status']}

def post_complete_adoption(c):
 reviewed(c)
 s=rt.read_mission(c.mission);s['mission']['status']='completed';rt.write_mission(c.mission,s)
 f=c.feedback(source='late-new-unreviewed-version',source_role='B',artifact='h2',kind='result')
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],artifact='h2',verdict=None))
 s=rt.read_mission(c.mission)
 return {'late_adoption_code':r['code'],'late_adoption_status':r['status'],
    'mission_status':s['mission']['status'],
    'current_artifact':s['collaboration']['adoptions']['D1']['artifact_ref'],
    'current_completion_findings':col.completion_findings(s)}

def repair_without_repair_acceptance(c):
 reviewed(c)
 f=c.feedback(source='confirmed-current-version-defect',source_role='B',kind='blocker')
 task={'id':'T3','title':'Repair current result','role':'success-critical',
       'mission_contribution':'Restores A1','acceptance_evidence':['A1'],'status':'pending'}
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],disposition='repair',verdict=None,new_tasks=[task],focus='T3'))
 assert k==0,r
 rt.transition_task_status(c.mission,'T3','completed')
 s=rt.read_mission(c.mission)
 findings=col.completion_findings(s)
 evidence=rt._read_events_unlocked(c.mission)
 s['mission']['status']='completed';rt.write_mission(c.mission,s)
 return {'mission_status':rt.read_mission(c.mission)['mission']['status'],
   'original_delegation_state':s['collaboration']['delegations']['D1']['status'],
   'current_artifact':s['collaboration']['adoptions']['D1']['artifact_ref'],
   'repair_task_status':rt.find_task(s,'T3')['status'],
   'repair_acceptance_events':sum(1 for e in evidence if e.get('task_id')=='T3' and e.get('event_type')=='acceptance_passed'),
   'completion_findings':findings}

for name,fn in [('retired_only_attempt_erases_acceptance_obligation',retire_without_result),
  ('lower_round_new_FAIL_hidden_by_older_higher_round_PASS',nonmonotonic_current),
  ('closed_mission_accepts_unreviewed_late_adoption',post_complete_adoption),
  ('repair_marked_complete_without_fresh_acceptance',repair_without_repair_acceptance)]:
 c=CollaborationRuntimeTests();c.setUp()
 try:
  try:out={'case':name,'result':fn(c)}
  except Exception as e:out={'case':name,'exception':type(e).__name__+': '+str(e)}
  print(json.dumps(out,ensure_ascii=False),flush=True)
 finally:c.doCleanups()
