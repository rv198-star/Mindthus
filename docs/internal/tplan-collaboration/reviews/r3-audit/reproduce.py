from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'skills/tplan/scripts'))
from tests.tplan.test_collaboration_runtime import CollaborationRuntimeTests
import collaboration as col
import tplan_runtime as rt

def initial_and_repair(c,acs):
 if len(acs)>1:
  s=rt.read_mission(c.mission)
  s['mission']['acceptance_evidence'].extend({'id':x,'description':x+' required'} for x in acs if x!='A1')
  rt.find_task(s,'T1')['acceptance_evidence']=list(acs)
  rt.write_mission(c.mission,s)
 c.enable();c.prepare();c.dispatch(execution_state='completed')
 f=c.feedback(source='initial-pass',source_role='C',kind='review')
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],complete=True))
 assert k==0,r
 rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Initial source acceptance',
    'task_id':'T1','payload':{'acceptance_ids':acs}})
 f=c.feedback(source='confirmed-current-defect',source_role='B',kind='blocker')
 task={'id':'T3','title':'Repair current result','role':'success-critical',
       'mission_contribution':'Restores required acceptance','acceptance_evidence':acs,'status':'pending'}
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],disposition='repair',verdict=None,new_tasks=[task],focus='T3'))
 assert k==0,r

def fail_overridden(c):
 initial_and_repair(c,['A1'])
 c.prepare(task_id='T3',delegation_id='D3',intent_id='I3',round_no=1)
 c.dispatch(intent_id='I3',execution_state='completed')
 f=c.feedback(source='repair-current-review-FAIL',delegation_id='D3',artifact='h3',source_role='C',kind='review')
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],delegation='D3',artifact='h3',verdict='FAIL',review_task='T3',focus='T3'))
 assert k==0,r
 rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Ordinary scoped pass',
     'task_id':'T3','payload':{'acceptance_ids':['A1']}})
 rt.transition_task_status(c.mission,'T3','completed')
 s=rt.read_mission(c.mission)
 findings=col.completion_findings(s,rt._read_events_unlocked(c.mission))
 s['mission']['status']='completed';rt.write_mission(c.mission,s)
 return {'mission_status':rt.read_mission(c.mission)['mission']['status'],
  'required_review':s['collaboration']['delegations']['D3']['required_review'],
  'repair_reviews':[(r['delegation_id'],r['verdict']) for r in s['collaboration']['reviews'].values() if r['delegation_id']=='D3'],
  'completion_findings':findings}

def partial_coverage(c):
 initial_and_repair(c,['A1','A2'])
 rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Only A1 repair verified',
     'task_id':'T3','payload':{'acceptance_ids':['A1']}})
 rt.transition_task_status(c.mission,'T3','completed')
 s=rt.read_mission(c.mission)
 findings=col.completion_findings(s,rt._read_events_unlocked(c.mission))
 s['mission']['status']='completed';rt.write_mission(c.mission,s)
 return {'mission_status':rt.read_mission(c.mission)['mission']['status'],
  'repair_required_ACs':rt.find_task(s,'T3')['acceptance_evidence'],
  'repair_passed_ACs':[e['payload']['acceptance_ids'] for e in rt._read_events_unlocked(c.mission) if e.get('task_id')=='T3' and e.get('event_type')=='acceptance_passed'],
  'completion_findings':findings}

def resume_projection(c):
 initial_and_repair(c,['A1'])
 rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Fresh qualified repair acceptance',
     'task_id':'T3','payload':{'acceptance_ids':['A1']}})
 rt.transition_task_status(c.mission,'T3','completed')
 state=rt.read_mission(c.mission)
 return {'completion_findings':col.completion_findings(state,rt._read_events_unlocked(c.mission)),
         'resume_acceptance_gaps':col.build_resume_view(state)['acceptance_gaps']}

def main():
 for name,fn in [('ordinary_repair_acceptance_overrides_required_C_FAIL',fail_overridden),
                ('one_of_two_repair_ACs_satisfies_entire_obligation',partial_coverage),
                ('valid_local_repair_completion_vs_resume',resume_projection)]:
  c=CollaborationRuntimeTests();c.setUp()
  try:
   try:result={'case':name,'result':fn(c)}
   except Exception as e:result={'case':name,'error':type(e).__name__+': '+str(e)}
   print(json.dumps(result,ensure_ascii=False),flush=True)
  finally:c.doCleanups()

if __name__=='__main__':main()
