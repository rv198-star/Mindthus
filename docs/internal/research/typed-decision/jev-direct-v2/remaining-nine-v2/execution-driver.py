from pathlib import Path
import os,shlex,json,time
from datetime import datetime,timezone
from experiments.jev_direct import pilot as p,transport_profile as t
from experiments.jev_direct.serial import SerialRequests
from experiments.typed_decision.relationship_runtime import save,_locked
r=Path('/Users/william/Documents/Codex/2026-09-27/mindthus-jev-direct-live-r2')
for line in (Path.home()/'.config/jev-jarvis/env').read_text().splitlines():
 text=line.strip().removeprefix('export ')
 if text.startswith('TYPESAFE_API_KEY='):
  v=shlex.split(text.split('=',1)[1],comments=True)
  if len(v)==1:os.environ['TYPESAFE_API_KEY']=v[0]
if not os.environ.get('TYPESAFE_API_KEY'):raise RuntimeError('missing_credential_before_dispatch')
with _locked(r/'.remaining-five-lock'):
 scheduler=SerialRequests(r/'serial');scheduler.validate();scope=t.active(r)['dispatch_scope'];t.guard(r)
 began=time.monotonic();start=datetime.now(timezone.utc).isoformat();summaries=[];stop=None
 for case,arm in scope:
  before=time.monotonic();started=datetime.now(timezone.utc).isoformat()
  print(json.dumps({'event':'path_start','case':case,'arm':arm,'time':started}),flush=True)
  try:
   result=p.run_case(r,case,arm,scheduler=scheduler)
   terminal={k:result.get(k) for k in ('status','text','host_calls','host_seconds','used_methods','route_objection','reason')}
   terminal['route_methods']=(result.get('route') or {}).get('methods');terminal['route_rounds']=(result.get('route') or {}).get('rounds')
  except Exception as exc:
   terminal={'status':'execution_stopped','error_type':type(exc).__name__,'error_code':str(exc) if type(exc).__name__=='RecoveryRequired' else p.safe_code(exc)}
  record={'case':case,'arm':arm,'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'operator_wall_seconds':time.monotonic()-before,'terminal':terminal,'outer_driver_retries':0}
  save(r/f'remaining-nine-checkpoints/{case}-{arm}.json',record);summaries.append(record)
  print(json.dumps({'event':'path_end',**record},ensure_ascii=False),flush=True)
  try:scheduler.validate();t.guard(r)
  except Exception as exc:
   stop={'after':case+'/'+arm,'error_type':type(exc).__name__,'error_code':str(exc) if type(exc).__name__=='RecoveryRequired' else p.safe_code(exc)};break
  if terminal['status']=='execution_stopped':stop={'after':case+'/'+arm,**terminal};break
 save(r/'remaining-nine-execution.json',{'started_at':start,'finished_at':datetime.now(timezone.utc).isoformat(),'operator_wall_seconds':time.monotonic()-began,'paths':summaries,'stop':stop,'outer_driver_retries':0})
 print(json.dumps({'event':'batch_end','paths':len(summaries),'stop':stop},ensure_ascii=False),flush=True)
