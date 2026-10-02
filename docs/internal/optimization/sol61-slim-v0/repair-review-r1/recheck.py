"""Recheck unchanged malformed/empty return fixtures from the read-only audit."""
import sys,tempfile,json
from pathlib import Path
sys.path.insert(0,'/Users/william/Projects/Github/Mindthus/tests')
import test_slim_batch as t
m=t.m
class BadReplyWithRecovery(t.Fake):
 def invoke(self,*args):
  raw=super().invoke(*args)
  if len(self.prompts)==1:
   raw['reply_text']='{';raw['stderr']='retrying sampling request'
  return raw
class BadReadWithRecovery(t.Fake):
 def invoke(self,*args):
  raw=super().invoke(*args)
  if len(self.prompts)==1:raw['stderr']='retrying sampling request'
  return raw
results={}
for name,fake in [
 ('malformed_reply_after_recovery',BadReplyWithRecovery([t.answer(),t.answer()])),
 ('invalid_read_after_recovery',BadReadWithRecovery([dict(kind='read',text='again',read_paths=['skills/using-mindthus/SKILL.md'],objection=''),t.answer()])),
 ('empty_answer',t.Fake([t.answer(''),t.answer()]))]:
 with tempfile.TemporaryDirectory(prefix='slim-recheck-only-') as tmp:
  root=Path(tmp)/'batch';t.SlimBatchTests().batch(root);clock=t.Clock()
  m.drive(root,adapter=fake,clock=clock.now,monotonic=clock.now,sleep=clock.sleep)
  paths=sorted(root.glob('runs/*/result.json'))
  item=dict(fake_invocations=len(fake.prompts),results=[m.read(p) for p in paths],
    transport_stop=(root/'transport-stop-v2.json').exists(),driver_stop=(root/'STOP.json').exists())
  if name=='empty_answer':
   assert item['results'][0]['error']=='empty_answer' and not (paths[0].parent/'answer.txt').exists()
   assert item['fake_invocations']==2  # Continue the other path, not retry this one.
  else:
   assert item['fake_invocations']==1 and item['transport_stop'] and item['driver_stop']
  results[name]=item
Path('/private/tmp/mindthus-slim-repair-review/after-counterexamples.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('PASS: 3 original return fixtures; all transports simulated')
