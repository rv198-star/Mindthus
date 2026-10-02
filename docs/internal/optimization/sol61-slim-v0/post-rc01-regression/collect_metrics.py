import collections,json,pathlib,sys,time
r=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else None
read=lambda p:json.loads(p.read_text())
c=read(r/'batch.json'); rows=[]; all_t=[]; all_m=[]; observations=[]; contexts=[]
for i,p in enumerate(c['plan']):
 name=f"{i:02d}-{p['case']}-{p['model']}-{p['arm']}"; run=r/'runs'/name
 result=read(run/'result.json') if (run/'result.json').exists() else {'status':'in_flight' if list(run.glob('call-*/intent.json')) else 'unrun'}
 ts=[read(f) for f in sorted(run.glob('call-*/terminal.json'))]; ms=[read(f) for f in sorted(run.glob('call-*/measurement.json'))]
 usage=collections.Counter(); missing=0; loads=[]
 for t in ts:
  if t.get('usage') is None: missing+=1
  else: usage.update({k:v for k,v in t['usage'].items() if isinstance(v,(int,float))})
  if t.get('observation'):observations.append(t['observation'])
 for f in sorted(run.glob('call-*/accepted.json')):
  a=read(f)
  if a.get('kind')=='read':loads.extend(a['read_paths'])
 contexts += [read(f) for f in run.glob('call-*/context-observation.json')]
 rows.append(dict(index=i,run=name,**p,status=result['status'],calls=len(list(run.glob('call-*/intent.json'))),
   session_seconds=sum(t['session_seconds'] for t in ts),active_wait_seconds=sum(m['active_wait_seconds'] for m in ms),
   dispatch_wall_seconds=sum(m['dispatch_wall_seconds'] for m in ms),usage=dict(usage),usage_missing_calls=missing,
   loaded_paths=loads,answer_path=f'runs/{name}/answer.txt' if (run/'answer.txt').exists() else None,error=result.get('error')))
 all_t+=ts;all_m+=ms
serial=[read(p)['payload'] for p in sorted((r/'scheduling/serial').glob('[0-9]*/intent.json'))]
parent=read(r/'parent-cooldown.json')['wait_seconds'] if (r/'parent-cooldown.json').exists() else 0
used=sum(x['calls'] for x in rows)
totals=dict(planned=40,statuses=dict(collections.Counter(x['status'] for x in rows)),logical_calls=used,cli_starts=len(all_m),
 new_cap=120,remaining=120-used,historical_calls=98,cumulative_calls=98+used,
 session_seconds=sum(x['session_seconds'] for x in rows),active_wait_seconds=sum(x['active_wait_seconds'] for x in rows),
 initial_cooldown_seconds=parent,outer_retries=sum(m['outer_retries'] for m in all_m),
 min_confirmed_gap_seconds=min((s['actual_gap_seconds'] for s in serial if s['actual_gap_seconds'] is not None),default=None),
 activity_wall_seconds=max((t['ended_at_epoch'] for t in all_t),default=0)-serial[0]['started_at_epoch'] if all_t and serial else None,
 observed_recoveries={k:sum(o.get(k,0) for o in observations) for k in ('sampling_retry_log_count','reconnect_notice_count','auth_or_401_log_count','fallback_or_prewarm_log_count')},
 unexposed_underlying_requests=None,cost=None,context_archives=sum(v.get('archive_available',False) for v in contexts),
 cwd_matches=sum(v.get('cwd_matches') is True for v in contexts),project_AGENTS_messages=sum(v.get('project_AGENTS_message_count',0) for v in contexts),
 stop=read(r/'STOP.json') if (r/'STOP.json').exists() else None)
groups={}
for model in ('gpt-6.1-sol','gpt-6-astra'):
 for arm in ('current','slim'):
  rs=[x for x in rows if x['model']==model and x['arm']==arm];u=collections.Counter()
  for x in rs:u.update(x['usage'])
  groups[model+'/'+arm]=dict(paths=len(rs),delivered=sum(x['status']=='delivered' for x in rs),
   **{k:sum(x[k] for x in rs) for k in ('calls','session_seconds','active_wait_seconds','dispatch_wall_seconds','usage_missing_calls')},
   usage=dict(u),read_requests=sum(len([1 for f in (r/'runs'/x['run']).glob('call-*/accepted.json') if read(f).get('kind')=='read']) for x in rs))
if out:
 out.mkdir(parents=True,exist_ok=True)
 for name,v in [('path-status-40.json',rows),('totals.json',totals),('groups.json',groups)]:
  (out/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(totals,ensure_ascii=False,indent=2))
print(json.dumps(groups,ensure_ascii=False,indent=2))
