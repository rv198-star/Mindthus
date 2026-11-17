from __future__ import annotations
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path[:0]=[str(ROOT),str(ROOT/'skills/tplan/scripts')]
from tests.tplan.test_collaboration_runtime import CollaborationRuntimeTests
import collaboration as col
import tplan_runtime as rt

def view(c):
 state=rt.read_mission(c.mission);events=rt.read_events(c.mission);snap=c.snapshot()['data']
 assert snap['resume']==snap['survey']['collaboration_resume']
 return {'findings':rt._mission_completion_findings(state,events),'gaps':snap['resume']['acceptance_gaps'],'status':state['mission']['status']}

def close(c,allowed):
 state=rt.read_mission(c.mission);state['mission']['status']='completed';before=(c.mission/'mission.json').read_bytes()
 try:rt.write_mission(c.mission,state)
 except rt.TplanError as e:
  assert not allowed,str(e)
  assert before==(c.mission/'mission.json').read_bytes()
  return {'outcome':'rejected','reason':str(e),'canonical_bytes_unchanged':True}
 assert allowed,'unexpected completion'
 return {'outcome':'completed'}

def after_completion_fail(c):
 leaf=c._c1_chain(3,('A1','A2'));c._c1_accept(leaf,('A1','A2'),mode='delegated')
 before=view(c);assert not before['findings'] and not before['gaps'],before
 f=c.feedback(source='audit-new-current-C-FAIL',delegation_id='D5',artifact='h5',source_role='C',kind='review')
 payload=c.resolution(f['data']['feedback_id'],delegation='D5',artifact='h5',disposition='answered',verdict='FAIL',complete=False,review_task=leaf,focus='T2')
 payload['goal_relation']['acceptance_ids']=['A1','A2']
 response,code=c.mutate('feedback.resolve',payload);assert code==0,response
 after=view(c);assert after['findings'] and after['gaps'],after
 result=close(c,False)
 return {'before_current_FAIL':before,'after_current_FAIL':after,'mission_close':result,'current_task':leaf}

def split_branches(c):
 c._b1_repair(('A1','A2'));c._c1_accept('T3',('A1','A2'))
 c._c1_successor('T3','T4',('A1',));c._c1_accept('T4',('A1',),mode='local')
 partial=view(c);assert partial['findings'] and partial['gaps'],partial
 close(c,False)
 c._c1_successor('T3','T5',('A2',));c._c1_accept('T5',('A2',),mode='delegated')
 full=view(c);assert not full['findings'] and not full['gaps'],full
 result=close(c,True)
 return {'partial_A1_only':partial,'full_explicit_A1_A2_branches':full,'mission_close':result,'final':view(c)}

if __name__=='__main__':
 for name,fn in [('late_current_reviewer_FAIL_propagates_after_three_level_completion',after_completion_fail),('declared_split_AC_branches_close_with_mixed_local_and_delegated_endpoints',split_branches)]:
  c=CollaborationRuntimeTests();c.setUp()
  try:print(json.dumps({'case':name,'evidence_class':'independent_mechanical_runtime_probe','result':fn(c)},ensure_ascii=False))
  finally:c.doCleanups()
