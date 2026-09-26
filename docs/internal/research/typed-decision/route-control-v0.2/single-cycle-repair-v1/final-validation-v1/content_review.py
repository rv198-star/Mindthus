"""Anonymous review of actual outputs; uses frozen dimensions and exact evidence spans."""
from pathlib import Path
import sys,json,importlib.util,hashlib
REPO=Path('/srv/agentdock/projects/Mindthus');sys.path.insert(0,str(REPO))
from experiments.typed_decision import evaluation_integrity as ev,relationship_assessment as rel
from experiments.typed_decision.contracts import digest,require
from experiments.typed_decision.session import read_record
BASE=Path('/srv/agentdock/tmp/mindthus-final-validation-f9d130f')
s=importlib.util.spec_from_file_location('review_transport',BASE/'review_runner.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
def enum(v):return {'type':'string','enum':list(v)}
def arr(v):return {'type':'array','items':v}
def prepare(root,scenario):
 frozen=read_record(root/'freeze.json');packet=frozen['packet']
 conditions=['pure_codex','jev_committed']
 order=sorted(conditions,key=lambda c:digest([scenario,c,'f9-final-review-v1']))
 artifacts={};private={};proofs={}
 for n,condition in enumerate(order,1):
  ident='X'+str(n);result=read_record(root/'results'/f'{condition}.json')
  if condition=='pure_codex':
   # A candidate is not automatically a delivered result.
   text=(result.get('reviewed') or {}).get('text','') if result.get('consumption_complete') else ''
  else:
   delivered=(result.get('delivery') or {}).get('accepted_outputs',{})
   text='\n\n'.join(result['outputs'][iid]['text'] for iid in delivered)
  methods={};entry=None;bindings=[];actual_texts=set()
  for hp in sorted((root/'episodes'/condition).glob('turns/*/inputs/*/steps/*/handoff.json')):
   q=read_record(hp)['request'];ip=hp.with_name('intent.json');op=hp.with_name('outcome.json')
   require(read_record(ip)['request_sha256']==digest(q),'review_request_identity')
   if not op.exists():continue
   outcome=read_record(op)
   if outcome.get('status')!='complete':continue
   reply=outcome.get('reply',{})
   if isinstance(reply.get('text'),str):actual_texts.add(reply['text'])
   for row in reply.get('revisions',{}).values():
    if isinstance(row,dict) and isinstance(row.get('text'),str):actual_texts.add(row['text'])
   cp=q.get('condition_packet',{})
   methods.update(q.get('loaded_methods') or cp.get('loaded_methods',{}))
   material=q.get('entry_skill') or cp.get('entry_skill')
   if material:
    if entry is not None:require(entry==material,'review_entry_changed')
    entry=material
   bindings.append({'request_id':q['request_id'],'request_sha256':digest(q),
                    'outcome_sha256':hashlib.sha256(op.read_bytes()).hexdigest(),'path':str(hp.parent)})
  if text:
   for part in ([text] if condition=='pure_codex' else [result['outputs'][iid]['text'] for iid in delivered]):
    require(part in actual_texts,'review_text_not_actual_host_output')
  for material in methods.values():
   require(hashlib.sha256(material['content'].encode()).hexdigest()==material['sha256'],'review_material_hash')
  artifacts[ident]={'text':text,'artifact_sha256':digest(text),'actual_method_materials':methods,'actual_entry_material':entry}
  private[ident]=condition;proofs[ident]=bindings
 request={'original_documents':packet['documents'],'conversation':packet['conversation'],'source_limits':frozen['window'],
          'artifacts':artifacts,'target_dimensions':ev.TARGET_DIMENSIONS[scenario],
          'instruction':'分别评价各匿名实际交付，不猜分支、不以方法名/篇幅/流程状态自动定优劣。原图或历史缺失不能补写；条件结论可以有效。空答须判断是否真缺必要事实，不强行通过或失败。每个维度pass/fail/not_assessable给出原始source_ids和该回答内精确answer_quotes；fail必须说明实际判断/行动后果。source_ids仅原始材料ID；entry/方法正文是各产物实际收到的约束材料，不是新增业务事实。不要将另一份答案作为本产物已有的输入。'}
 dimensions=ev.TARGET_DIMENSIONS[scenario]
 judge=r.obj({'verdict':enum(['pass','fail','not_assessable']),'reason':r.STR,
      'source_ids':arr(enum(d['id'] for d in packet['documents'])),
      'answer_quotes':arr(r.STR),'decision_consequence':r.STR})
 schema=r.obj({'artifacts':r.obj({a:r.obj({'overall_usable':enum(['yes','no','not_assessable']),
                                  'dimensions':r.obj({d:judge for d in dimensions})}) for a in artifacts})})
 dest=BASE/('content-'+scenario);dest.mkdir(exist_ok=True)
 for name,value in [('request.json',request),('private-map.json',private),('source-proofs.json',proofs),('schema.json',schema)]:
  p=dest/name
  if p.exists():require(json.loads(p.read_text())==value,'review_packet_changed')
  else:p.write_text(json.dumps(value,ensure_ascii=False,indent=2))
 return request,schema

def main():
 scenario=sys.argv[1];index=int(sys.argv[2]);root=BASE/('trial-'+scenario)
 request,schema=prepare(root,scenario);label=f'content-{scenario}-review-{index}'
 r.run(label,'独立匿名内容评阅，不使用工具，不输出隐藏推理。\n'+json.dumps(request,ensure_ascii=False),schema,seconds=360)
 directory=BASE/label
 if not (directory/'answer.json').exists():return
 reply=json.loads((directory/'answer.json').read_text());normalized={'artifacts':{}}
 docs={d['id']:d for d in request['original_documents']}
 for aid,row in reply['artifacts'].items():
  result={'overall_usable':row['overall_usable'],'dimensions':{}};text=request['artifacts'][aid]['text']
  for name,j in row['dimensions'].items():
   spans=[]
   for quote in j['answer_quotes']:
    require(bool(quote) and text.count(quote)==1,'review_quote_not_unique_or_absent')
    start=text.index(quote);spans.append({'start':start,'end':start+len(quote),'sha256':digest(quote)})
   result['dimensions'][name]={k:j[k] for k in ('verdict','reason','decision_consequence')}
   result['dimensions'][name].update(source_refs=[rel.quote(docs[i]) for i in j['source_ids']],answer_spans=spans)
  normalized['artifacts'][aid]=result
 ev.validate_review(normalized,request)
 (directory/'validated.json').write_text(json.dumps(normalized,ensure_ascii=False,indent=2))
 print('CONTENT_REVIEW_VALIDATED',scenario,index,flush=True)
if __name__=='__main__':main()
