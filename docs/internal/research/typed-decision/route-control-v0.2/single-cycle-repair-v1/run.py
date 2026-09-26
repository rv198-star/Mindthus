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
from experiments.typed_decision.contracts import digest, canonical, require, provider_configuration
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
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
    ep=root/'episodes'/condition;p=read_record(root/'inputs'/f'{condition}.json')
    if response_path:
        value=json.loads(response_path.read_text());submit_response(ep,REPO,value.get('payload',value))
    native=condition=='pure_codex'
    result=cmp.run_condition(ep,None if native else provider(root,condition),p,REPO,condition=condition,
        **hooks(p['authority']['owner_ref']),live_admission=None if native else read_record(root/'admissions'/f'{condition}.json'))
    if result.get('status')!='awaiting_current_agent':save(root/'results'/f'{condition}.json',result)
    return result


def schema_for(q):
    schema=wire.schema_for(q);kind=q.get('schema','')
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
    return schema


def normalize(raw,q,usage):
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


def drive(root,condition):
    frozen=verify(root);ep=root/'episodes'/condition;work=root/'workspaces'/condition;work.mkdir(parents=True,exist_ok=True)
    session_file=root/'sessions'/f'{condition}.json'
    for _ in range(frozen['maximum_cli_calls_per_branch']+1):
        result=step(root,condition)
        if result.get('status')!='awaiting_current_agent':return result
        handoff=read_record(Path(result['host_request']));q=handoff['request']
        label=Path(result['host_request']).parent.name;directory=root/'host-calls'/condition/label
        if (directory/'outcome.json').exists():
            saved=read_record(directory/'outcome.json');raw=json.loads((directory/'reply.json').read_text())
        else:
            if (directory/'intent.json').exists():raise RecoveryRequired('single_cycle_cli_unknown_do_not_repeat')
            require(len(list((root/'host-calls'/condition).glob('*/intent.json')))<frozen['maximum_cli_calls_per_branch'],'single_cycle_cli_cap')
            directory.mkdir(parents=True,exist_ok=True)
            schema=schema_for(q);(directory/'schema.json').write_text(json.dumps(schema,ensure_ascii=False))
            prompt=('只根据当前原始材料与已提供入口处理任务，不调用工具，不读其他分支。输出JSON。'
                    '保留必要未知，正文不超过700字。retain时text为空；非read_methods时requested_methods为空。'
                    '按当前request的明确字段与范围返回。\n'+canonical({'request':q,'host_instruction':handoff['instruction']}).decode())
            (directory/'prompt.txt').write_text(prompt)
            independent=handoff['role']=='arbitration'
            prior=read_record(session_file)['context_ref'] if session_file.exists() and not independent else None
            save(directory/'intent.json',{'request_id':q['request_id'],'request_sha256':digest(q),
                'prompt_sha256':digest(prompt),'model_requested':frozen['model'],'reasoning_effort':frozen['reasoning_effort'],
                'prior_context':prior,'schema_sha256':digest(schema)})
            cmd=[frozen['codex_binary'],'exec']+(['resume'] if prior else [])
            cmd+=['--skip-git-repo-check','-m',frozen['model'],'-c','model_reasoning_effort='+json.dumps(frozen['reasoning_effort']),
                  '-c','features.shell_tool=false','--json','--output-schema',str(directory/'schema.json'),'-o',str(directory/'reply.json')]
            cmd+=([prior,'-'] if prior else ['--sandbox','read-only','-C',str(work),'-'])
            env=os.environ.copy()
            for key in ('TYPESAFE_API_KEY','OPENROUTER_API_KEY','MINDTHUS_HOST_API_KEY'):env.pop(key,None)
            start=time.monotonic()
            try:
                proc=subprocess.run(cmd,input=prompt,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,
                                    timeout=min(240,handoff['allowance_seconds']))
            except subprocess.TimeoutExpired:
                save(directory/'failure.json',{'status':'timeout','elapsed_seconds':time.monotonic()-start});raise
            events=[]
            for line in proc.stdout.splitlines():
                try:events.append(json.loads(line))
                except ValueError:pass
            contexts=[e['thread_id'] for e in events if e.get('type')=='thread.started']
            context=contexts[-1] if contexts else prior
            tools=[e for e in events if (e.get('item') or {}).get('type') in ('command_execution','mcp_tool_call','web_search')]
            if proc.returncode or not context or tools or not (directory/'reply.json').exists():
                save(directory/'failure.json',{'status':'host_failed','returncode':proc.returncode,
                    'tool_events':len(tools),'context_observed':bool(context),'elapsed_seconds':time.monotonic()-start})
                raise RuntimeError('host_call_failed; no retry')
            raw=json.loads((directory/'reply.json').read_text());wire.no_secrets(raw)
            uses=[e.get('usage') for e in events if e.get('type')=='turn.completed' and e.get('usage')]
            u=uses[-1] if uses else {}
            saved={'status':'complete','context_ref':context,'elapsed_seconds':time.monotonic()-start,
                   'usage':{'input_tokens':u.get('input_tokens'),'output_tokens':u.get('output_tokens'),'cost_usd':None},
                   'requested_model':frozen['model'],'service_model_attestation':'not_observed','reply_sha256':digest(raw)}
            save(directory/'outcome.json',saved)
            if not independent:
                if session_file.exists():require(read_record(session_file)['context_ref']==context,'branch_context_changed')
                else:save(session_file,{'context_ref':context})
        reply=normalize(raw,q,saved['usage'])
        submit_response(ep,REPO,{'schema':'mindthus.current-host-response.v1','request_id':handoff['request_id'],
            'request_sha256':handoff['request_sha256'],'owner_ref':handoff['owner_ref'],
            'host_context_ref':saved['context_ref'],'elapsed_seconds':saved['elapsed_seconds'],'reply':reply})
    raise RuntimeError('bounded_driver_steps_exhausted')


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
