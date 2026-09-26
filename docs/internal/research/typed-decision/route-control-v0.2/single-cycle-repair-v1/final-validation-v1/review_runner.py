"""One explicitly authorized isolated review; writes only visible answer and safe telemetry."""
from pathlib import Path
import subprocess,os,json,hashlib,time,signal,sys
BASE=Path('/srv/agentdock/tmp/mindthus-final-validation-f9d130f')
def sha(b):return hashlib.sha256(b).hexdigest()
def obj(p):return {'type':'object','properties':p,'required':list(p),'additionalProperties':False}
STR={'type':'string'}
SCHEMA=obj({'verdict':{'type':'string','enum':['PASS','REVISE']},'findings':{'type':'array','items':obj({k:dict(STR) for k in ('severity','location','problem','required_fix')})},'summary':dict(STR)})
def run(label,body,schema=SCHEMA,seconds=480):
 directory=BASE/label;directory.mkdir(exist_ok=True)
 if (directory/'intent.json').exists():
  print('EXISTING_REVIEW: no resubmission');return
 (directory/'schema.json').write_text(json.dumps(schema,ensure_ascii=False))
 (directory/'prompt.txt').write_text(body)
 work=directory/'workspace';work.mkdir(exist_ok=True)
 cmd=['/usr/bin/codex','exec','--skip-git-repo-check','-m','gpt-6-sol','-c','model_reasoning_effort="xhigh"','-c','features.shell_tool=false','--sandbox','read-only','-C',str(work),'--json','--output-schema',str(directory/'schema.json'),'-o',str(directory/'answer.json'),'-']
 intent={'label':label,'requested_model':'gpt-6-sol','reasoning_effort':'xhigh','timeout_seconds':seconds,'prompt_sha256':sha(body.encode()),'schema_sha256':sha((directory/'schema.json').read_bytes()),'maximum_calls':1,'automatic_retry':False}
 (directory/'intent.json').write_text(json.dumps(intent,indent=2));print('REVIEW_STARTED',label,flush=True)
 env=os.environ.copy()
 for k in ('TYPESAFE_API_KEY','OPENROUTER_API_KEY','MINDTHUS_HOST_API_KEY'):env.pop(k,None)
 start=time.monotonic();p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,start_new_session=True)
 try:
  out,err=p.communicate(body,timeout=seconds)
  events=[]
  for line in out.splitlines():
   try:e=json.loads(line)
   except ValueError:continue
   if isinstance(e,dict):events.append(e)
  receipt={'status':'complete' if p.returncode==0 and (directory/'answer.json').exists() else 'failed','exit_code':p.returncode,'elapsed_seconds':time.monotonic()-start,'contexts':[e.get('thread_id') for e in events if e.get('type')=='thread.started'],'usage':[e.get('usage') for e in events if e.get('type')=='turn.completed'],'tool_events':sum((e.get('item') or {}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change') for e in events),'model_service_attestation':'not_observed'}
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);p.communicate()
  receipt={'status':'timeout','elapsed_seconds':time.monotonic()-start,'local_process_group_terminated':True,'remote_cancellation_confirmed':False}
 (directory/'outcome.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,ensure_ascii=False),flush=True)
 if (directory/'answer.json').exists():print((directory/'answer.json').read_text(),flush=True)
if __name__=='__main__':
 label='code-audit-480s'
 prompt='请独立只读审计Mindthus当前宿主驱动修复，给出具体正确性结论，不使用工具或修改文件，不输出隐藏推理。旧审查180秒没有完成，用户明确批准适当增加时间；本次480秒。核心目标：Schema别名不得污染自然语言；非法引用不崩溃或隐式修正；真实CLI与回执在中断/重入时不得错配或重发；保留来源、权限、预算。不是新框架设计，不评Jev性能，不要求形式项。请重点查实际调用顺序/缓存/锁/终态路径，限列确实可触发的重要问题（最多6项）。如果无阻塞项PASS，轻微建议说明不阻塞。\n'
 for path in ('docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py','tests/test_host_driver_integrity.py','experiments/typed_decision/current_host.py'):
  prompt+='\n=== '+path+' ===\n'+Path(path).read_text()
 run(label,prompt)
