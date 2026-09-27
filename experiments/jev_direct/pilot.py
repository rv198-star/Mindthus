"""Matched direct-router experiment; uses existing guarded CLI and journal tools."""
from pathlib import Path
import argparse,importlib.util,json,os,re,subprocess,time
from datetime import datetime,timezone
from experiments.typed_decision.contracts import canonical,digest,require,ContractError
from experiments.typed_decision.relationship_runtime import save,_locked
from experiments.typed_decision.session import read_record,RecoveryRequired
from . import router as r
from .full_context import ROUTABLE
from .host_boundary import api_schema,parse_events,cli_schema_failure
REPO=Path(__file__).resolve().parents[2]
ADAPTER=REPO/'docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py'
spec=importlib.util.spec_from_file_location('direct_cli_transport',ADAPTER)
wire=importlib.util.module_from_spec(spec);spec.loader.exec_module(wire)
ARMS=('native','direct')
def obj(p):return {'type':'object','properties':p,'required':list(p),'additionalProperties':False}
def enum(v):return {'type':'string','enum':list(v)}
def identity(repo):
    files=[*Path(repo).glob('experiments/jev_direct/*.py'),Path(repo)/'experiments/jev_direct/routing_cards.json',ADAPTER]
    return {str(p.relative_to(repo)):r.file_hash(p) for p in sorted(files)}
def entry_catalog(repo):
    result={}
    for m in ROUTABLE:
        front=(Path(repo)/f'skills/{m}/SKILL.md').read_text().split('---',2)[1]
        match=re.search(r'^description:\s*(.*)$',front,re.M)
        result[m]={'description':match.group(1).strip('"') if match else '', 'path':f'skills/{m}/SKILL.md'}
    return result

def material(repo,path):
    p=Path(repo)/path
    require(not p.is_symlink() and p.is_file() and p.resolve().is_relative_to(Path(repo).resolve()),'pilot_material_path')
    return {'sha256':r.file_hash(p),'content':p.read_bytes().decode('utf8')}

def prepare(root,cases,*,binary=None,serial_gap_seconds=None):
    root=Path(root).resolve();require(not root.exists() and not root.is_relative_to(REPO),'pilot_fresh_root')
    pack=r.load_pack(REPO)
    for c in cases:r.validate_input(c['raw'])
    require(len({c['id'] for c in cases})==len(cases),'pilot_unique_cases')
    config=Path.home()/'.codex/config.toml';binary=Path(binary or '/usr/bin/codex').resolve();sources=dict(pack['source_sha256'])
    for p in sorted((REPO/'skills').glob('**/*.md')):
        if p.is_file() and not p.is_symlink():sources[str(p.relative_to(REPO))]=r.file_hash(p)
    f={'schema':'mindthus.direct-two-level-pilot.v1','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
       'root':str(root),'code_hashes':identity(REPO),'source_hashes':sources,'pack_sha256':digest(pack),
       'host_model':'gpt-6-sol','host_effort':'xhigh','binary':str(binary),'binary_sha256':r.file_hash(binary),
       'config_sha256':r.file_hash(config) if config.exists() else None,'cases':cases,'arms':list(ARMS),
       'max_jev_calls':2*len(cases),'max_jev_calls_per_case':2,'reserve_per_jev_usd':0.05,
       'max_host_calls_per_arm':4,'max_host_seconds_per_arm':900,'host_timeout':360,
       'same_branch_context':True,'semantic_retries':0,'reviewer_calls_max':2*len(cases),'review_timeout_seconds':480,
       'primary_endpoint':'delivered answer quality and needless blockage; secondary complete calls/tokens/time',
       'claims':'paired development test; no native-plugin automatic-activation or statistical-superiority claim'}
    if serial_gap_seconds is not None:
        require(serial_gap_seconds==60,'pilot_serial_gap')
        f['serial_policy']={'max_in_flight':1,'gap_after_completion_seconds':60,'ledger_version':2}
    save(root/'freeze.json',f)
    save(root/'freeze-binding.json',{'freeze_sha256':digest(f),'case_sha256':{c['id']:digest(c['raw']) for c in cases}})
    return f

def verify_frozen_inputs(root):
    root=Path(root).resolve();f=read_record(root/'freeze.json')
    require(read_record(root/'freeze-binding.json')=={'freeze_sha256':digest(f),'case_sha256':{c['id']:digest(c['raw']) for c in f['cases']}},'pilot_freeze_changed')
    require(f['root']==str(root),'pilot_root_changed')
    require(all(material(REPO,p)['sha256']==h for p,h in f['source_hashes'].items()),'pilot_source_drift')
    config=Path.home()/'.codex/config.toml'
    require(f['binary_sha256']==r.file_hash(f['binary']) and f['config_sha256']==(r.file_hash(config) if config.exists() else None),'pilot_host_drift')
    return f

def verify(root):
    f=verify_frozen_inputs(root)
    from .transport_profile import active
    successor=active(root)
    require(successor is not None or f['code_hashes']==identity(REPO),'pilot_code_drift')
    return f

def exact_tree(root):
    return {str(p.relative_to(root)):r.file_hash(p) for p in sorted(Path(root).rglob('*')) if p.is_file() and not p.name.startswith('.') and p.name!='seal.json'}
def seal(root,result):
    start=read_record(root/'run-start.json');end=datetime.now(timezone.utc)
    result={**result,'freeze_sha256':start['freeze_sha256'],'raw_sha256':start['raw_sha256'],
            'started_at':start['started_at'],'finished_at':end.isoformat(),
            'wall_seconds':(end-datetime.fromisoformat(start['started_at'])).total_seconds()}
    save(root/'result.json',result);save(root/'seal.json',{'files':exact_tree(root)});return result
def unseal(root):
    require(read_record(root/'seal.json')['files']==exact_tree(root),'pilot_terminal_evidence_changed')
    return read_record(root/'result.json')
def safe_code(exc):
    s=str(exc)
    return s if isinstance(exc,ContractError) and re.fullmatch(r'[A-Za-z0-9_.:/-]{1,180}',s) else type(exc).__name__

def host_call(root,label,request,schema,f,prior=None,timeout=None,scheduler=None):
    """One frozen request; a bare intent is never resubmitted."""
    if f.get('serial_policy'):
        from .serial import SerialRequests
        batch=Path(f['root']).resolve()
        require(Path(root).resolve().is_relative_to(batch),'pilot_host_outside_batch')
        scheduler=scheduler or SerialRequests(batch/'serial')
        require(scheduler.root.resolve()==batch/'serial' and scheduler.gap==60,'pilot_serial_root')
        scheduler.validate()
    from .transport_profile import active,guard,observe
    profile=active(Path(f['root']))
    guard(Path(f['root']))
    directory=Path(root)/label;directory.mkdir(parents=True,exist_ok=True)
    sending=api_schema(schema)
    prompt='根据原始任务与实际已加载规则完成当前请求。工具关闭；需要资料时只按schema请求读取，不虚构事实或执行结果。输出规定JSON，不输出隐藏推理。\n'+canonical(request).decode()
    intent={'request_sha256':digest(request),'prompt_sha256':digest(prompt),'schema_sha256':digest(schema),'api_schema_sha256':digest(sending),'model':f['host_model'],'effort':f['host_effort'],'prior_context':prior,'timeout_seconds':timeout or f['host_timeout']}
    if profile:
        intent.update(transport_successor_sha256=digest(profile),protocol_sha256=profile['protocol_sha256'],transport_overrides_sha256=profile['overrides_sha256'])
    if (directory/'intent.json').exists():
        require(read_record(directory/'intent.json')==intent,'pilot_call_identity_changed')
        if not (directory/'outcome.json').exists():raise RecoveryRequired('pilot_unknown_call_no_retry')
        out=read_record(directory/'outcome.json')
        require(read_record(directory/'request.json')==request and json.loads((directory/'schema.json').read_text())==schema and json.loads((directory/'schema.api.json').read_text())==sending and (directory/'prompt.txt').read_text()==prompt,'pilot_cached_request_changed')
        reply=None
        if out['status']=='complete':
            reply=wire._decode_reply(directory/'reply.json',65536)
            require(digest(reply)==out['reply_sha256'],'pilot_cached_reply_changed')
        return reply,out
    require(not (directory/'reply.json').exists(),'pilot_unbound_reply')
    save(directory/'request.json',request)
    for name,value in (('schema.json',schema),('schema.api.json',sending)):
        path=directory/name
        if path.exists():require(json.loads(path.read_text())==value,'pilot_prepared_schema_changed')
        else:path.write_bytes(canonical(value)+b'\n')
    (directory/'prompt.txt').write_text(prompt)
    save(directory/'schema-binding.json',{'local_contract_sha256':digest(schema),'api_schema_sha256':digest(sending),'projection':'remove_uniqueItems_at_schema_nodes_v1'})
    work=directory/'workspace';work.mkdir(exist_ok=True)
    cmd=[f['binary'],'exec']+(['resume'] if prior else [])
    cmd+=['--skip-git-repo-check','-m',f['host_model'],'-c','model_reasoning_effort='+json.dumps(f['host_effort']),'-c','features.shell_tool=false','--json','--output-schema',str(directory/'schema.api.json'),'-o',str(directory/'reply.json')]
    if profile:
        for override in profile['overrides']:cmd+=['-c',override]
        save(directory/'effective-transport-config.json',{'successor_sha256':digest(profile),'protocol_sha256':profile['protocol_sha256'],'overrides':profile['overrides'],'overrides_sha256':profile['overrides_sha256'],'scope':'CLI invocation only','model':f['host_model'],'effort':f['host_effort']})
    cmd+=([prior,'-'] if prior else ['--sandbox','read-only','-C',str(work),'-'])
    env=os.environ.copy()
    for k in ('TYPESAFE_API_KEY','OPENROUTER_API_KEY','MINDTHUS_HOST_API_KEY'):env.pop(k,None)
    start=time.monotonic();usage={'input_tokens':None,'output_tokens':None,'cached_input_tokens':None,'cost_usd':None};context=None;returned=False;reply=None
    elapsed=0.0;failure=None
    try:
        def invoke():
            nonlocal elapsed,failure
            # Waiting/lock interruption has not sent anything. Only persist the
            # host intent once the serial slot has actually been acquired.
            guard(Path(f['root']))
            save(directory/'intent.json',intent)
            call_start=time.monotonic()
            cli_returned=False
            try:
                proc=wire._run_cli(cmd,prompt,env,timeout or f['host_timeout'])
                elapsed=time.monotonic()-call_start;cli_returned=True
                (directory/'cli.stdout.jsonl').write_text(proc.stdout)
                (directory/'cli.stderr.txt').write_text(proc.stderr)
                if profile:observe(Path(f['root']),directory,proc,intent)
                events=parse_events(proc.stdout)
                contexts={e['thread_id'] for e in events if e.get('type')=='thread.started' and isinstance(e.get('thread_id'),str)}
                terminal=proc.returncode==0 and len(contexts)==1 and sum(e.get('type')=='turn.completed' for e in events)==1 and not any(e.get('type')=='turn.failed' for e in events)
                if terminal:
                    # Current stdout may omit turn IDs; any IDs it does expose
                    # must agree within this dedicated CLI invocation.
                    turns={e['turn_id'] for e in events if e.get('type') in ('turn.started','turn.completed') and e.get('turn_id')}
                    terminal=len(turns)<=1 and all(e.get('thread_id',next(iter(contexts))) in contexts for e in events if e.get('type')=='turn.completed')
                if not terminal and len(contexts)==1:
                    context=next(iter(contexts))
                    try:failure=cli_schema_failure(directory,context)
                    except (ContractError,ValueError,KeyError,OSError):pass
                if not terminal and failure is None:
                    raise RecoveryRequired('pilot_remote_completion_unknown')
                return proc
            except (OSError,subprocess.TimeoutExpired) as exc:
                save(directory/'transport-observation.json',{'status':'unknown','local_error':type(exc).__name__,'automatic_retry':False})
                raise RecoveryRequired('pilot_remote_completion_unknown') from exc
            finally:
                if not cli_returned:elapsed=time.monotonic()-call_start
                save(directory/'host-session-observation.json',{'cli_wall_seconds':elapsed,'process_returned':cli_returned,'http_seconds':None,'remote_terminal_inferred_from_exit':False})
        proc=scheduler.call('host:'+str(directory),invoke) if scheduler else invoke();returned=True;events=[]
        for line in proc.stdout.splitlines():
            try:e=json.loads(line)
            except ValueError:continue
            if isinstance(e,dict):events.append(e)
        contexts={e['thread_id'] for e in events if e.get('type')=='thread.started' and isinstance(e.get('thread_id'),str)}
        uses=[e['usage'] for e in events if e.get('type')=='turn.completed' and isinstance(e.get('usage'),dict)]
        if uses:
            for k in usage:
                if k!='cost_usd':usage[k]=uses[-1].get(k)
        if failure is not None:raise ContractError('pilot_confirmed_invalid_json_schema')
        require(proc.returncode==0,'pilot_cli_failed')
        require(not any((e.get('item') or {}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change') for e in events),'pilot_tool_use')
        require(len(contexts)==1,'pilot_context_missing');context=next(iter(contexts))
        require(prior is None or context==prior,'pilot_context_changed')
        reply=wire._decode_reply(directory/'reply.json',65536);wire._wire_check(reply,schema)
        out={'status':'complete','reply_sha256':digest(reply)}
    except ContractError as exc:out={'status':'failed','error':safe_code(exc),'failure_kind':'request_schema' if failure else 'local_validation'}
    out.update(request_sha256=digest(request),schema_sha256=digest(schema),api_schema_sha256=digest(sending),context_ref=failure['thread_id'] if failure else context,elapsed_seconds=elapsed,dispatch_wall_seconds=time.monotonic()-start,usage=usage,process_returned=returned,requested_model=f['host_model'],service_model_attestation='not_observed',automatic_retry=False)
    save(directory/'outcome.json',out);return reply,out

def answer_schema(paths):
    reads={'type':'array','items':enum(paths),'uniqueItems':True} if paths else {'type':'array','items':{'type':'string'},'maxItems':0}
    return obj({'action':enum(['answer','read']),'text':{'type':'string'},'read_paths':reads,'used_methods':{'type':'array','items':enum(ROUTABLE),'uniqueItems':True},'route_objection':{'type':'string'}})

def run_case(root,case_id,arm,provider=None,*,scheduler=None):
    root=Path(root).resolve();f=verify(root);require(arm in ARMS,'pilot_arm')
    if f.get('serial_policy'):
        from .serial import SerialRequests
        scheduler=scheduler or SerialRequests(root/'serial')
        require(scheduler.root.resolve()==(root/'serial').resolve(),'pilot_serial_root')
        require(scheduler.gap==60,'pilot_serial_gap')
        scheduler.validate()
        if provider is not None:
            require(not provider.is_live,'pilot_injected_live_provider_bypasses_serial')
    from .transport_profile import active,guard
    profile=active(root)
    if profile:
        require([case_id,arm] in profile['dispatch_scope'],'transport_dispatch_scope')
        guard(root)
    c=next(c for c in f['cases'] if c['id']==case_id);raw=c['raw'];dest=root/'runs'/case_id/arm
    with _locked(root/('.'+case_id+'.pair-lock')):
        # Both arms bind the same freeze; rewriting freeze plus its adjacent checksum
        # cannot erase a previously executed counterpart's identity.
        for other_arm in ARMS:
            other=root/'runs'/case_id/other_arm
            if (other/'run-start.json').exists():
                old=read_record(other/'run-start.json')
                require(old['freeze_sha256']==digest(f) and old['raw_sha256']==digest(raw),'pilot_cross_arm_identity_changed')
            if (other/'result.json').exists():
                old_result=unseal(other)
                require(old_result['freeze_sha256']==digest(f) and old_result['raw_sha256']==digest(raw),'pilot_cross_arm_result_changed')
        start=dest/'run-start.json'
        if start.exists():
            old=read_record(start);require(old['freeze_sha256']==digest(f) and old['raw_sha256']==digest(raw),'pilot_arm_input_changed')
        else:save(start,{'freeze_sha256':digest(f),'raw_sha256':digest(raw),'started_at':datetime.now(timezone.utc).isoformat()})
        if (dest/'result.json').exists():return unseal(dest)
        if profile:save(dest/('technical-identity-compensation.json' if profile.get('schema')=='mindthus.B1-one-compensation.v1' else 'technical-identity.json'),{'successor_sha256':digest(profile),'protocol_sha256':profile['protocol_sha256']})
        pack=r.load_pack(REPO);loaded={};decision=None;reads=[];methods=[]
        if arm=='direct':
            require(not (dest/'host').exists() or (dest/'route/result.json').exists(),'pilot_host_before_route')
            route_dir=dest/('route-compensation' if profile and profile.get('schema')=='mindthus.B1-one-compensation.v1' else 'route')
            decision=r.route(route_dir,raw,REPO,digest(f),provider,scheduler=scheduler)
            loaded=r.execution_materials(decision,pack,REPO);methods=list(decision['methods'])
            allowed=[p for p in f['source_hashes'] if any(p.startswith('skills/'+m+'/') or p==f'docs/methodologies/{m}.md' for m in methods+decision.get('companion_reference_methods',[]))]
            instruction=('Execute the committed methods in their declared scopes and conditional dependency order. Do not rerun method discovery or silently substitute another method. If materially unsuitable, give a source-based route_objection and a useful bounded answer. For sequential methods let the later judgment use the earlier established result in the answer; reading order alone is not that evidence. No named method or an uncertain route still permits a bounded response or necessary clarification; authority and facts remain constrained.')
            entry=None;catalog=None
        else:
            allowed=list(f['source_hashes']);entry=material(REPO,'skills/using-mindthus/SKILL.md');catalog=entry_catalog(REPO)
            instruction='Use the supplied using-mindthus entry normally: answer directly when sufficient, or request specific necessary method/resource paths and then answer. Do not preload all methods. This is normal discovery, not an instruction to avoid methods.'
        allowed=sorted(set(allowed));schema=answer_schema(allowed);prior=None;total=0.0
        for n in range(f['max_host_calls_per_arm']):
            request={'original_input':raw,'instruction':instruction,'loaded_materials':loaded,'readable_paths':allowed,'entry_skill':entry,'method_catalog':catalog,'route':decision,
                'answer_contract':'Give the actual user-facing answer within 900 Chinese characters unless the user requires less. Hide routing labels. For action=read return empty text and no method claims; for action=answer read_paths must be empty. References and assumptions are not observed execution.'}
            remaining=f['max_host_seconds_per_arm']-total
            if remaining<=0:return seal(dest,{'case':case_id,'arm':arm,'status':'host_budget_exhausted','text':'','route':decision,'host_calls':n,'host_seconds':total})
            reply,out=host_call(dest/'host',str(n),request,schema,f,prior=prior,timeout=min(f['host_timeout'],remaining),scheduler=scheduler);total+=out['elapsed_seconds']
            if out['status']!='complete':return seal(dest,{'case':case_id,'arm':arm,'status':'host_failed','text':'','route':decision,'host_calls':n+1,'reason':out.get('error'),'host_seconds':total,'quality':'not_scored'})
            prior=out['context_ref']
            try:
                if reply['action']=='read':
                    require(reply['text']=='' and reply['used_methods']==[] and reply['read_paths'],'pilot_read_shape')
                    require(n+1<f['max_host_calls_per_arm'],'pilot_read_budget_exhausted')
                    require(set(reply['read_paths'])<=set(allowed),'pilot_read_outside_scope')
                    for p in reply['read_paths']:loaded[p]=material(REPO,p);reads.append(p)
                    continue
                require(not reply['read_paths'] and reply['text'].strip(),'pilot_answer_required')
                actual={m for m in ROUTABLE if f'skills/{m}/SKILL.md' in loaded}
                require(set(reply['used_methods'])<=actual,'pilot_unread_method_claim')
                if arm=='direct':
                    used=set(reply['used_methods']);allowed_used=set(methods)|set(decision.get('companion_reference_methods',[]))
                    require((set(methods)<=used<=allowed_used) or bool(reply['route_objection'].strip()),'pilot_route_silently_overridden')
                    if decision.get('ordering_unresolved'):
                        require(bool(reply['route_objection'].strip()),'pilot_order_conflict_requires_disclosure')
                    if decision.get('unconfirmed_companion_scopes'):
                        require(bool(reply['route_objection'].strip()),'pilot_companion_unconfirmed_requires_disclosure')
            except ContractError as exc:return seal(dest,{'case':case_id,'arm':arm,'status':'host_reply_rejected','text':'','route':decision,'host_calls':n+1,'reason':safe_code(exc),'host_seconds':total})
            return seal(dest,{'case':case_id,'arm':arm,'status':'delivered','text':reply['text'],'used_methods':reply['used_methods'],'route_objection':reply['route_objection'],'route':decision,'requested_reads':reads,'actual_materials':loaded,'actual_entry':entry,'host_calls':n+1,'host_seconds':total,'final_context':prior,'final_reply_ref':str(dest/'host'/str(n)/'reply.json'),'quality':'requires_independent_content_review','pre_route_llm_calls':0 if arm=='direct' else None})
        raise RecoveryRequired('pilot_host_budget_exhausted')

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);p.add_argument('--root',type=Path,required=True);p.add_argument('--cases',type=Path);p.add_argument('--case');p.add_argument('--arm',choices=ARMS);a=p.parse_args()
    out=prepare(a.root,json.loads(a.cases.read_text())) if a.action=='prepare' else run_case(a.root,a.case,a.arm)
    print(json.dumps({k:out.get(k) for k in ('case','arm','status','host_calls','used_methods','route_objection','text')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
