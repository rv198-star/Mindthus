"""Two isolated, label-anonymous content reviews per preregistered source."""
from pathlib import Path
import sys,json,subprocess
REPO=next(x for x in Path(__file__).resolve().parents if (x/'experiments/jev_direct').is_dir());sys.path.insert(0,str(REPO))
from experiments.jev_direct import pilot as p,router as r
from experiments.typed_decision.evaluation_integrity import TARGET_DIMENSIONS
from experiments.typed_decision.session import read_record
from experiments.typed_decision.relationship_runtime import save,_locked
from experiments.typed_decision.contracts import require,digest
DIMENSIONS={
'A':{'exact_result':'Return apple, pear, plum in that order, one per line.','format_and_scope':'Respect only three lines; no method discussion or unrelated advice.','evidence':'No unnecessary factual assumptions.'},
'B':{'diagnosis':'Distinguish existence of conclusion/evidence fields from verified inventory truth.','minimal_repair':'Assign structure checks, factual evidence and semantic/acceptance responsibility without another empty gate.','verification':'Use the supplied contradictory-pass case as a real falsification check; do not claim actual modifications or executed tests.'},
'C':{'direction_and_path':'Keep credible automation direction distinct from viability of this full-stack carrier now.','resource_and_options':'Honor 15 person-days, compare 40-day build and 8-day migration without inventing prices or demand.','boundaries_and_triggers':'Retain human dispute handling, data exit ability and concrete staged/exit conditions; equivalent feasible postures may pass.'},
'D':{'structure_before_allocation':'Establish a defensible bounded hybrid alternative instead of blindly choosing all-auto/all-human.','dependency_use':'The allocation must actually depend on the preceding established division of routine work and appeals, not merely name two methods.','allocation':'Keep human appeal handling and at most six person-days; postpone nonessential cosmetics. Four-plus-two is available, not a requirement to use exactly those words.'},
'E':TARGET_DIMENSIONS['E'],'F':TARGET_DIMENSIONS['F']}

def review(root,case_id,index):
 root=Path(root).resolve();f=p.verify(root);require(index in (1,2),'review_index')
 rel=Path(__file__).resolve().relative_to(REPO)
 original=subprocess.check_output(['git','show',f['source_commit']+':'+str(rel)],cwd=REPO)
 require(original==Path(__file__).read_bytes(),'review_code_drift')
 c=next(c for c in f['cases'] if c['id']==case_id);raw=c['raw'];dimensions=DIMENSIONS[c['scenario']]
 order=sorted(p.ARMS,key=lambda arm:digest([case_id,arm,'direct-v2-anonymous']))
 artifacts={};private={}
 for n,arm in enumerate(order,1):
  result=p.unseal(root/'runs'/case_id/arm);key='X'+str(n);private[key]=arm
  text=result.get('text','') if result['status']=='delivered' else ''
  if text:
   rp=Path(result['final_reply_ref']);actual=json.loads(rp.read_text())
   require(actual['text']==text and read_record(rp.with_name('outcome.json'))['reply_sha256']==digest(actual),'review_real_answer_binding')
  artifacts[key]={'text':text,'actual_method_and_resource_materials':result.get('actual_materials',{}),
                 'actual_entry_material':result.get('actual_entry'),
                 'actual_cognitive_instructions':(result.get('route') or {}).get('cognitive_obligations',{})}
 request={'original_input':raw,'source_limits':c['provenance'],'artifacts':artifacts,'dimensions':dimensions,
          'instruction':'分别评价每份实际产物，不能以另一份答案充当它已有的输入。只按原始任务、事实和该产物实际得到的规则资料评价，不猜实验臂，不按方法名、篇幅或语气选赢家。可以承认简单解释或等效路线。空答不能当作正确答复；缺必要事实才允许明确的有限回应。每一维度给原始文档source_ids和回答内唯一的完整原文answer_quotes。fail须说明实质后果；不要发明缺失的截图、历史答复或事实。总体可用不代表历史多轮问题已解决。不调用工具、不输出隐藏推理。'}
 ids=[d['id'] for d in raw['documents']]
 dimension=p.obj({'verdict':p.enum(['pass','fail','not_assessable']),'reason':{'type':'string'},
   'source_ids':{'type':'array','items':p.enum(ids)},'answer_quotes':{'type':'array','items':{'type':'string'}},'decision_consequence':{'type':'string'}})
 schema=p.obj({'artifacts':p.obj({a:p.obj({'overall_usable':p.enum(['yes','no','not_assessable']),
                   'dimensions':p.obj({d:json.loads(json.dumps(dimension)) for d in dimensions})}) for a in artifacts})})
 dest=root/'reviews'/case_id;save(dest/'private-map.json',private)
 with _locked(dest/('.review-'+str(index)+'.lock')):
  reply,out=p.host_call(dest,str(index),request,schema,f,timeout=f['review_timeout_seconds'])
  if out['status']!='complete':return out
  for a,row in reply['artifacts'].items():
   text=artifacts[a]['text']
   for d,j in row['dimensions'].items():
    require(set(j['source_ids'])<=set(ids),'review_source')
    for quote in j['answer_quotes']:require(bool(quote) and text.count(quote)==1,'review_quote_not_unique')
    if j['verdict']!='not_assessable':require(j['source_ids'] and (j['answer_quotes'] or not text),'review_evidence')
    if j['verdict']=='fail':require(j['decision_consequence'].strip(),'review_failure_consequence')
  save(dest/str(index)/'validated.json',reply)
  print('REVIEW_VALIDATED',case_id,index,json.dumps({k:v['overall_usable'] for k,v in reply['artifacts'].items()}),flush=True)
  return reply
if __name__=='__main__':review(sys.argv[1],sys.argv[2],int(sys.argv[3]))
