from __future__ import annotations
import copy,json,runpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT),str(ROOT/'skills/tplan/scripts')]
from tests.tplan.test_collaboration_runtime import CollaborationRuntimeTests
import collaboration as col
import tplan_runtime as rt
initial=runpy.run_path(str(ROOT/'docs/internal/tplan-collaboration/reviews/r3-audit/reproduce.py'))['initial_and_repair']

def pass_and_complete(c,task,delegation,artifact):
 c.prepare(task_id=task,delegation_id=delegation,intent_id='I'+delegation[1:],round_no=1)
 c.dispatch(intent_id='I'+delegation[1:],execution_state='completed')
 rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Current scoped acceptance for '+task,'task_id':task,'payload':{'acceptance_ids':['A1']}})
 f=c.feedback(source='pass-'+delegation,delegation_id=delegation,artifact=artifact,source_role='C',kind='review')
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],delegation=delegation,artifact=artifact,complete=True,review_task=task,focus='T2'))
 assert k==0,r

def nested(c, final_mode):
 initial(c,['A1']);pass_and_complete(c,'T3','D3','h3')
 f=c.feedback(source='new-blocking-defect-in-repair',delegation_id='D3',artifact='h3',source_role='B',kind='blocker')
 t={'id':'T4','title':'Repair the newly confirmed defect in T3','role':'success-critical','mission_contribution':'Restores A1 through bounded successor repair','acceptance_evidence':['A1'],'status':'pending'}
 r,k=c.mutate('feedback.resolve',c.resolution(f['data']['feedback_id'],delegation='D3',artifact='h3',disposition='repair',verdict=None,new_tasks=[t],focus='T4'))
 assert k==0,r
 if final_mode=='delegated':pass_and_complete(c,'T4','D4','h4')
 else:
  rt.append_event(c.mission,{'event_type':'acceptance_passed','summary':'Fresh local successor repair acceptance','task_id':'T4','payload':{'acceptance_ids':['A1']}})
  rt.transition_task_status(c.mission,'T4','completed')
 s=rt.read_mission(c.mission);ev=rt.read_events(c.mission)
 eligible=col.completion_findings(s,ev)
 before=(c.mission/'mission.json').read_bytes()
 s['mission']['status']='completed'
 try:
  rt.write_mission(c.mission,s);outcome='completed'
 except rt.TplanError as e:outcome='rejected: '+str(e)
 current=rt.read_mission(c.mission)
 return {'final_task_statuses':{t['id']:t['status'] for t in current['tasks']},'repair_obligations':list(current['collaboration']['repair_obligations'].values()),'adoptions':current['collaboration']['adoptions'],'scoped_acceptance':[{'task_id':e['task_id'],'acceptance_ids':e['payload'].get('acceptance_ids')} for e in ev if e['event_type']=='acceptance_passed'],'reviews':[(r['delegation_id'],r['verdict']) for r in current['collaboration']['reviews'].values()],'mission_close':outcome,'completion_findings':eligible,'resume_gaps':c.snapshot()['data']['resume']['acceptance_gaps'],'canonical_bytes_unchanged':before==(c.mission/'mission.json').read_bytes()}

if __name__=='__main__':
 for mode in ['local','delegated']:
  c=CollaborationRuntimeTests();c.setUp()
  try:print(json.dumps({'case':'completed_repair_has_valid_'+mode+'_successor','expected_mission_close':'completed','result':nested(c,mode)},ensure_ascii=False))
  finally:c.doCleanups()
