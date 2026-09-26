"""Portable one-cycle experiment driver; original entry/Episode/CurrentAgentHost own execution.

prepare creates a new immutable identity, step resumes it, and drive-codex is an
explicit host transport. No historical ledger relocation, CPA, automatic retry,
semantic label substitution or hidden model switch is performed here.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p/'experiments/typed_decision').is_dir())
sys.path.insert(0, str(REPO))
from experiments.typed_decision import comparison_v03 as cmp, route_control_v03 as runtime
from experiments.typed_decision import evaluation_integrity as ev, source_direct_v03 as sd
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision.contracts import digest, canonical, require, provider_configuration, ContractError
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response, validate_submission
from experiments.typed_decision.providers import TypeSafeJevProvider, OpenRouterJevProvider
from experiments.typed_decision.session import read_record, write_once, implementation_digest, RecoveryRequired

# Reuse only the already-tested wire schema and mechanical ref/hash normalizer.
# No old driver run()/freeze(), monkey-patching, machine path or fixture answer is used.
ADAPTER = HERE.parent/'design-reassessment-v1/live-v03-d1/run.py'
spec=importlib.util.spec_from_file_location('existing_wire_schema',ADAPTER)
wire=importlib.util.module_from_spec(spec);spec.loader.exec_module(wire)
CONDITIONS=('pure_codex','jev_advisory','jev_committed')


def save(path, value):
    if path.exists(): require(read_record(path)==value,'immutable_experiment_changed')
    else: write_once(path,value)


def hooks(owner):
    return dict(executor=CurrentAgentHost(owner),corrector=CurrentAgentHost(owner,role='correction'),
                organizer=CurrentAgentHost(owner,role='organize'),arbitrator=CurrentAgentHost(owner,role='arbitration'))


def _new_provider(serving, **kwargs):
    require(serving in ('typesafe', 'openrouter'), 'single_cycle_serving_required')
    cls, model = ((TypeSafeJevProvider, 'jev-1.13.0') if serving == 'typesafe'
                  else (OpenRouterJevProvider, 'typesafe/jev-1.13'))
    return cls(model=model, choice_rounding=True, **kwargs)


def prepare(root, source_path, scenario, cutoff, phase, missing, model, effort, binary, host_endpoint,
            serving='typesafe'):
    require(not root.exists() and not root.is_relative_to(REPO),'fresh_external_root_required')
    selected_provider = provider_configuration(_new_provider(serving))
    raw=json.loads(source_path.read_text());source=raw.get('payload',raw)
    window=ev.prepare_prefix(source,cutoff,auxiliary_availability={'source-limit':1 if scenario=='E' else 0},
                             phase=phase,missing_original=missing)
    data=window['packet'];data['task_budget']={'max_calls':4,'max_seconds':360}
    data['authority']['owner_ref']='current-codex-single-cycle'
    data['host_inferences']['owner_ref']=data['authority']['owner_ref']
    binaries=Path(binary).resolve();require(binaries.is_file(),'codex_binary_required')
    frozen={'schema':'mindthus.single-cycle-experiment.v1','source_commit':subprocess.check_output(
        ['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),'implementation':implementation_digest(),
        'driver_sha256':wire.sha(__file__),'adapter_sha256':wire.sha(ADAPTER),
        'plan_sha256':wire.sha(HERE/'PLAN.md'),'entry_sha256':wire.sha(REPO/'skills/using-mindthus/SKILL.md'),
        'root':str(root),'case':scenario,'window':window['metadata'],'packet':data,
        'model':model,'reasoning_effort':effort,'codex_binary':str(binaries),'host_endpoint_declared':host_endpoint,
        'codex_binary_sha256':wire.sha(binaries),
        'host_config_sha256':wire.sha(Path.home()/'.codex/config.toml') if (Path.home()/'.codex/config.toml').exists() else None,
        'same_branch_context_required':True,'source_protocol':'entry-selected, not native plugin auto-activation',
        'conditions':list(CONDITIONS),'maximum_jev_calls':4,'maximum_cli_calls_per_branch':8,
        'qualification':False,'automatic_retries':0, 'jev_serving':serving,
        'provider_configuration':selected_provider}
    save(root/'freeze.json',frozen)
    for condition in CONDITIONS:
        p=branch_packet(frozen,condition);save(root/'inputs'/f'{condition}.json',p)
        if condition!='pure_codex':
            admission=runtime.prepare_admission(root/'episodes'/condition,provider(root,condition),p,REPO,
                hooks(p['authority']['owner_ref']),authorization_ref='Owner approved one bounded A repair cycle; PLAN.md')
            save(root/'admissions'/f'{condition}.json',admission)
    return frozen


def branch_packet(frozen,condition):
    p=rel.clone(frozen['packet']);p['episode_id']='single-cycle-'+digest([frozen['root'],condition])[:24]
    p['consumption_policy']='advisory' if condition=='jev_advisory' else 'committed'
    return p


def verify(root):
    frozen=read_record(root/'freeze.json')
    require(frozen['root']==str(root) and frozen['implementation']==implementation_digest()
            and frozen['driver_sha256']==wire.sha(__file__) and frozen['adapter_sha256']==wire.sha(ADAPTER)
            and frozen['plan_sha256']==wire.sha(HERE/'PLAN.md')
            and frozen['entry_sha256']==wire.sha(REPO/'skills/using-mindthus/SKILL.md'),'single_cycle_freeze_changed')
    require(frozen['provider_configuration']==provider_configuration(_new_provider(frozen['jev_serving'])),
            'single_cycle_serving_changed')
    config=Path.home()/'.codex/config.toml'
    require(frozen['host_config_sha256']==(wire.sha(config) if config.exists() else None)
            and frozen['codex_binary_sha256']==wire.sha(frozen['codex_binary']), 'single_cycle_host_configuration_changed')
    for condition in frozen['conditions']:
        require(read_record(root/'inputs'/f'{condition}.json')==branch_packet(frozen,condition),'single_cycle_input_changed')
    return frozen


def provider(root,condition):
    def transport(url,headers,body,timeout):
        frozen=verify(root)
        records=list((root/'episodes').glob('*/turns/*/inputs/*/steps/*/calls/*/intent.json'))
        require(len(records)<=frozen['maximum_jev_calls'],'single_cycle_jev_cap')
        # Session already persisted the intent before this one bounded transport.
        return wire.deadline_post_json(url,headers,body,min(timeout,60))
    frozen=read_record(root/'freeze.json')
    return _new_provider(frozen['jev_serving'],transport=transport)


def step(root,condition,response_path=None):
    frozen=verify(root);require(condition in frozen['conditions'],'condition')
    terminal=root/'results'/f'{condition}.json'
    if terminal.exists():
        return read_record(terminal)
    ep=root/'episodes'/condition;p=read_record(root/'inputs'/f'{condition}.json')
    if response_path:
        value=json.loads(response_path.read_text());submit_response(ep,REPO,value.get('payload',value))
    native=condition=='pure_codex'
    result=cmp.run_condition(ep,None if native else provider(root,condition),p,REPO,condition=condition,
        **hooks(p['authority']['owner_ref']),live_admission=None if native else read_record(root/'admissions'/f'{condition}.json'))
    if result.get('status')!='awaiting_current_agent':save(root/'results'/f'{condition}.json',result)
    return result


def schema_for(q):
    # JSON round-trip breaks EACH alias occurrence; deepcopy preserves sibling aliases.
    # The historical adapter stays immutable for old frozen runs.
    schema=rel.clone(wire.schema_for(q));kind=q.get('schema','')
    if kind.endswith('native-request.v1'):
        schema['properties']['artifact_action']=wire.enum(q['artifact_actions'])
        schema['properties']['requested_methods']=wire.arr(wire.enum(q['condition_packet']['method_catalog']))
        schema['required']+=['artifact_action','requested_methods']
    if kind.endswith('organize-request.v1'):
        coverage=wire.obj({'status':wire.enum(['complete','partial']),'unassigned':wire.arr(wire.obj({
            'source_id':wire.STR,'kind':wire.enum(['independent','shared_gate','unclear']),
            'affected_issues':wire.arr(wire.STR),'reason':wire.STR}))})
        schema['properties']['coverage_disposition']=coverage;schema['required'].append('coverage_disposition')
        schema['properties']['issues']['maxItems']=q['max_issues']
        schema['properties']['issues']['items']['properties']['id']['pattern']='^[a-zA-Z][a-zA-Z0-9_.-]{0,95}$'
    if kind.endswith('execution-request.v1'):
        status='scope_status' if q.get('limited_response') else 'advisory_status' if q.get('policy')=='advisory' else None
        if status:
            schema['properties'][status]=wire.enum(['bounded_answer','unresolved'] if status=='scope_status' else ['answer','bounded_answer','unresolved'])
            schema['required'].append(status)
    source=q.get('original_input') or q.get('condition_packet',{}).get('original_input',{})
    source_ids=[d['id'] for d in source.get('documents',[])]
    def constrain(node):
        if not isinstance(node,dict): return
        props=node.get('properties',{})
        if 'source_ids' in props:
            props['source_ids']=wire.arr(wire.enum(source_ids)) if source_ids else {'type':'array','items':{'type':'string'},'maxItems':0}
            props['source_ids']['uniqueItems']=True
        if 'source_id' in props:
            props['source_id']=wire.enum(source_ids) if source_ids else {'type':'string','enum':[]}
        for value in props.values(): constrain(value)
        constrain(node.get('items'))
    constrain(schema)
    props=schema['properties']
    if 'performed_methods' in props:
        methods=(q.get('loaded_methods') or q.get('condition_packet',{}).get('loaded_methods',{}))
        props['performed_methods']=(wire.arr(wire.enum(methods)) if methods else
                                   {'type':'array','items':{'type':'string'},'maxItems':0})
        props['performed_methods']['uniqueItems']=True
    if kind.endswith('organize-request.v1'):
        fields=props['issues']['items']['properties']
        for name in ('actor','goal','scope'):
            fields[name]={'type':'string','description':'A natural-language description, not an identifier or a placeholder.'}
        fields['candidates']['uniqueItems']=True
    if 'text' in props:
        props['text']['description']='Actual complete user-facing answer; empty only for an explicit retain/read_methods action. Not a version or ID.'
    # New coverage/string nodes must also be independent of wire.STR and one another.
    return rel.clone(schema)


def _wire_check(value, spec, path='reply'):
    """Validate only the subset emitted above; runtime semantic validators still apply."""
    def check(ok, code): require(ok, 'host_wire:' + path + ':' + code)
    if 'anyOf' in spec:
        for branch in spec['anyOf']:
            try: _wire_check(value,branch,path); return
            except ContractError: pass
        check(False,'anyOf')
    kind=spec.get('type')
    check((kind=='object' and type(value) is dict) or (kind=='array' and type(value) is list)
          or (kind=='string' and type(value) is str) or (kind=='boolean' and type(value) is bool)
          or (kind=='null' and value is None), 'type')
    if 'enum' in spec: check(value in spec['enum'],'enum')
    if kind=='object':
        props=spec['properties']
        check(set(spec.get('required',[])) <= set(value),'required')
        if spec.get('additionalProperties') is False: check(set(value) <= set(props),'extra_fields')
        for key,item in value.items():
            if key in props: _wire_check(item,props[key],path+'.'+key)
    elif kind=='array':
        check(len(value)>=spec.get('minItems',0) and len(value)<=spec.get('maxItems',100000),'count')
        if spec.get('uniqueItems'): check(len({digest(x) for x in value})==len(value),'duplicate')
        for i,item in enumerate(value): _wire_check(item,spec['items'],path+'.'+str(i))
    elif kind=='string' and 'pattern' in spec:
        check(re.search(spec['pattern'],value) is not None,'pattern')


def _unique_rows(raw, name, field):
    if name in raw:
        values=[row[field] for row in raw[name]]
        require(len(values)==len(set(values)),'host_wire:'+name+':duplicate_identity')


def normalize(raw,q,usage):
    _wire_check(raw,schema_for(q))
    for name,key in (('issues','id'),('accepted','issue_id'),('decisions','finding_id'),
                     ('revisions','issue_id'),('dispositions','finding_id')):
        _unique_rows(raw,name,key)
    kind=q.get('schema','');raw=rel.clone(raw)
    if kind.endswith('native-request.v1') and raw['artifact_action']=='retain':
        require(raw['text']=='' and q['candidate'] is not None,'retain_requires_empty_text')
        raw['text']=q['candidate']
    out=wire.normalize(raw,q,usage)
    if kind.endswith('native-request.v1'):
        out['artifact_action']=raw['artifact_action']
        if raw['artifact_action']=='read_methods':out['requested_methods']=raw['requested_methods']
        else:require(raw['requested_methods']==[],'non_read_method_request')
    if kind.endswith('organize-request.v1'):
        docs={d['id']:d for d in q['original_input']['documents']}
        c=raw['coverage_disposition'];out['coverage_disposition']={'status':c['status'],'unassigned':[
            {'source_ref':rel.quote(docs[x['source_id']]),'kind':x['kind'],
             'affected_issues':x['affected_issues'],'reason':x['reason']} for x in c['unassigned']]}
    for key in ('scope_status','advisory_status'):
        if key in raw:out[key]=raw[key]
    return out



def _prompt(q, handoff):
    return ('只根据当前原始材料与已提供入口处理任务，不调用工具，不读其他分支。输出规定JSON。'
            '正文是实际中文回答，不是ID或版本号；goal/scope/理由使用完整自然语言。'
            'source_ids只能引用输出格式列出的真实文档ID。保留必要未知，正文不超过700字。'
            '仅当本次schema包含artifact_action时，retain使用空text、read_methods请求所需方法；'
            '非read_methods时requested_methods为空。其他阶段按本次request返回。\n'+canonical({'request':q,'host_instruction':handoff['instruction']}).decode())


def _decode_reply(path, limit):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'host_reply_duplicate_json_key');result[key]=value
        return result
    def invalid_constant(_): raise ContractError('host_reply_nonfinite_json')
    content=path.read_bytes();require(len(content)<=limit,'host_reply_size')
    try: result=json.loads(content,object_pairs_hook=pairs,parse_constant=invalid_constant)
    except (UnicodeError,json.JSONDecodeError): raise ContractError('host_reply_invalid_json') from None
    require(type(result) is dict,'host_reply_not_object')
    wire.no_secrets(result)
    return result


def _binding(q, schema, prompt, frozen):
    return {'request_id':q['request_id'],'request_sha256':digest(q),
            'prompt_sha256':digest(prompt),'schema_sha256':digest(schema),
            'model_requested':frozen['model'],'reasoning_effort':frozen['reasoning_effort']}


def _load_completed(directory,q,frozen,limit):
    intent=read_record(directory/'intent.json')
    require(read_record(directory/'request.json')==q,'host_cache_request_changed')
    schema=json.loads((directory/'schema.json').read_text())
    prompt=(directory/'prompt.txt').read_text()
    expected=_binding(q,schema,prompt,frozen)
    require(schema==schema_for(q) and all(intent.get(k)==v for k,v in expected.items()),'host_cache_binding_changed')
    result=read_record(directory/'outcome.json')
    require(result.get('status')=='complete' and result.get('request_binding')==expected,'host_cache_outcome_changed')
    raw=_decode_reply(directory/'reply.json',limit)
    require(result.get('reply_sha256')==digest(raw),'host_cache_reply_changed')
    require(isinstance(result.get('context_ref'),str) and bool(result['context_ref']),'host_context_missing')
    require(intent.get('prior_context') is None or intent['prior_context']==result['context_ref'],'host_resume_context_changed')
    return raw,result


def _restore_context(root,condition,frozen):
    """An outcome saved before session.json is sufficient; an intent alone is not."""
    contexts=set()
    for path in sorted((root/'host-calls'/condition).glob('*/outcome.json')):
        directory=path.parent;intent=read_record(directory/'intent.json')
        q=read_record(directory/'request.json')
        _,out=_load_completed(directory,q,frozen,intent['output_bytes'])
        if not intent['independent_context']: contexts.add(out['context_ref'])
    require(len(contexts)<=1,'host_branch_context_changed')
    session_file=root/'sessions'/f'{condition}.json'
    if contexts: save(session_file,{'context_ref':next(iter(contexts))})
    elif session_file.exists(): raise ContractError('host_session_without_completed_call')


def _run_cli(cmd,prompt,env,timeout):
    # Stop local descendants on timeout; do not claim this cancels server-side work.
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          text=True,env=env,start_new_session=True)
    try: stdout,stderr=proc.communicate(prompt,timeout=timeout)
    except BaseException:
        try: os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        proc.communicate()
        raise
    return subprocess.CompletedProcess(cmd,proc.returncode,stdout,stderr)


def _failure(root,condition,directory,q,stage,exc,*,elapsed=None,usage=None,completed=False):
    # Codes describe local checks. Never export arbitrary server text or raw tracebacks.
    code=str(exc) if isinstance(exc,ContractError) and re.fullmatch(r'[A-Za-z0-9_.:/-]{1,180}',str(exc)) else type(exc).__name__
    record={'status':'rejected' if completed else 'failed','stage':stage,'error_code':code,
            'request_id':q.get('request_id'),'request_sha256':digest(q),
            'transport_completed':completed,'elapsed_seconds':elapsed,
            'usage':usage or dict(wire.rt.UNKNOWN_USAGE),'automatic_retry':False}
    save(directory/'failure.json',record)
    result={'schema':'mindthus.single-cycle-host-failure.v1','condition':condition,
            'status':'host_reply_rejected' if completed else 'host_transport_failed',
            'reason':code,'failure_stage':stage,'consumption_complete':False,
            'failure_record':str(directory/'failure.json'),'pending_local_handoff':True,
            'external_request_repeated':False,'usage':record['usage']}
    save(root/'results'/f'{condition}.json',result)
    return result


def drive(root,condition):
    verify(root)
    require(condition in CONDITIONS,'condition')
    # The Episode lock protects state; this outer lock covers the actual CLI call too.
    with wire.rt._locked(root/'.host-driver.lock'):
        return _drive(root,condition)


def _drive(root,condition):
    frozen=verify(root);ep=root/'episodes'/condition
    terminal=root/'results'/f'{condition}.json'
    if terminal.exists(): return read_record(terminal)
    for path in sorted((root/'host-calls'/condition).glob('*/failure.json')):
        # Interruption between recording rejection and publishing its terminal result.
        fail=read_record(path);q=read_record(path.with_name('request.json'))
        result={'schema':'mindthus.single-cycle-host-failure.v1','condition':condition,
                'status':'host_reply_rejected' if fail['transport_completed'] else 'host_transport_failed',
                'reason':fail['error_code'],'failure_stage':fail['stage'],'consumption_complete':False,
                'failure_record':str(path),'pending_local_handoff':True,
                'external_request_repeated':False,'usage':fail['usage']}
        save(terminal,result);return result
    _restore_context(root,condition,frozen)
    work=root/'workspaces'/condition;work.mkdir(parents=True,exist_ok=True)
    session_file=root/'sessions'/f'{condition}.json'
    for _ in range(frozen['maximum_cli_calls_per_branch']+1):
        result=step(root,condition)
        if result.get('status')!='awaiting_current_agent':return result
        handoff=read_record(Path(result['host_request']));q=handoff['request']
        label=Path(result['host_request']).parent.name;directory=root/'host-calls'/condition/label
        schema=schema_for(q);prompt=_prompt(q,handoff)
        expected=_binding(q,schema,prompt,frozen)
        if (directory/'outcome.json').exists():
            raw,saved=_load_completed(directory,q,frozen,handoff['output_bytes'])
            intent=read_record(directory/'intent.json')
            require(all(intent.get(k)==v for k,v in expected.items()),'host_cached_handoff_changed')
        else:
            if (directory/'intent.json').exists():raise RecoveryRequired('single_cycle_cli_unknown_do_not_repeat')
            require(len(list((root/'host-calls'/condition).glob('*/intent.json')))<frozen['maximum_cli_calls_per_branch'],'single_cycle_cli_cap')
            directory.mkdir(parents=True,exist_ok=True)
            save(directory/'request.json',q)
            (directory/'schema.json').write_text(json.dumps(schema,ensure_ascii=False))
            (directory/'prompt.txt').write_text(prompt)
            independent=handoff['role']=='arbitration'
            prior=read_record(session_file)['context_ref'] if session_file.exists() and not independent else None
            save(directory/'intent.json',{**expected,'prior_context':prior,
                'independent_context':independent,'output_bytes':handoff['output_bytes']})
            cmd=[frozen['codex_binary'],'exec']+(['resume'] if prior else [])
            cmd+=['--skip-git-repo-check','-m',frozen['model'],'-c','model_reasoning_effort='+json.dumps(frozen['reasoning_effort']),
                  '-c','features.shell_tool=false','--json','--output-schema',str(directory/'schema.json'),'-o',str(directory/'reply.json')]
            cmd+=([prior,'-'] if prior else ['--sandbox','read-only','-C',str(work),'-'])
            env=os.environ.copy()
            for key in ('TYPESAFE_API_KEY','OPENROUTER_API_KEY','MINDTHUS_HOST_API_KEY'):env.pop(key,None)
            start=time.monotonic()
            try: proc=_run_cli(cmd,prompt,env,min(240,handoff['allowance_seconds']))
            except (subprocess.TimeoutExpired,OSError) as exc:
                return _failure(root,condition,directory,q,'transport',exc,elapsed=time.monotonic()-start)
            elapsed=time.monotonic()-start;events=[]
            for line in proc.stdout.splitlines():
                try: e=json.loads(line)
                except ValueError: continue
                if isinstance(e,dict):events.append(e)
            contexts={e['thread_id'] for e in events if e.get('type')=='thread.started' and isinstance(e.get('thread_id'),str)}
            tools=[e for e in events if (e.get('item') or {}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change')]
            uses=[e.get('usage') for e in events if e.get('type')=='turn.completed' and isinstance(e.get('usage'),dict)]
            u=uses[-1] if uses else {}
            usage={'input_tokens':u.get('input_tokens'),'output_tokens':u.get('output_tokens'),'cost_usd':None}
            try:
                require(proc.returncode==0 and not tools,'host_cli_failed_or_used_tools')
                require(len(contexts)==1,'host_context_missing_or_ambiguous')
                context=next(iter(contexts))
                require(prior is None or context==prior,'host_resume_context_changed')
                require((directory/'reply.json').is_file(),'host_reply_missing')
                raw=_decode_reply(directory/'reply.json',handoff['output_bytes'])
            except (ContractError,OSError) as exc:
                return _failure(root,condition,directory,q,'transport_reply',exc,elapsed=elapsed,usage=usage)
            saved={'status':'complete','context_ref':context,'elapsed_seconds':elapsed,'usage':usage,
                   'requested_model':frozen['model'],'service_model_attestation':'not_observed',
                   'request_binding':expected,'reply_sha256':digest(raw)}
            save(directory/'outcome.json',saved)
            if not independent:save(session_file,{'context_ref':context})
        try:
            reply=normalize(raw,q,saved['usage'])
            submission={'schema':'mindthus.current-host-response.v1','request_id':handoff['request_id'],
                'request_sha256':handoff['request_sha256'],'owner_ref':handoff['owner_ref'],
                'host_context_ref':saved['context_ref'],'elapsed_seconds':saved['elapsed_seconds'],'reply':reply}
            validate_submission(submission,handoff,REPO)
            save(directory/'submission.json',submission)
            submit_response(ep,REPO,submission)
        except (ContractError,KeyError,TypeError,ValueError) as exc:
            return _failure(root,condition,directory,q,'reply_validation',exc,
                elapsed=saved['elapsed_seconds'],usage=saved['usage'],completed=True)
        save(directory/'consumption.json',{'status':'response_staged','submission_sha256':digest(submission),
            'request_id':handoff['request_id'],'semantic_acceptance':False})
    raise RecoveryRequired('bounded_driver_steps_exhausted')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','step','drive-codex'])
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--source',type=Path)
    parser.add_argument('--scenario',choices=['E','F']);parser.add_argument('--cutoff',type=int)
    parser.add_argument('--phase',choices=ev.PHASES,default='initial');parser.add_argument('--missing',action='append',default=[])
    parser.add_argument('--model',default='gpt-6-sol');parser.add_argument('--effort',default='xhigh')
    parser.add_argument('--codex',default=shutil.which('codex'));parser.add_argument('--host-endpoint',default='configured-current-host')
    parser.add_argument('--condition',choices=CONDITIONS);parser.add_argument('--reply',type=Path)
    parser.add_argument('--serving',choices=('typesafe','openrouter'),default='typesafe')
    args=parser.parse_args();root=args.root.resolve()
    if args.action=='prepare':result=prepare(root,args.source,args.scenario,args.cutoff,args.phase,args.missing,args.model,args.effort,args.codex,args.host_endpoint,args.serving)
    elif args.action=='step':result=step(root,args.condition,args.reply)
    else:result=drive(root,args.condition)
    print(json.dumps({k:result.get(k) for k in ('schema','status','reason','consumption_complete','delivery','host_request')},ensure_ascii=False))

if __name__=='__main__':main()
