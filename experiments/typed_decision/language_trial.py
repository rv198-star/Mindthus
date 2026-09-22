"""Frozen C01 language-view comparison; no graph or decision policy changes."""
from dataclasses import asdict
import json
from pathlib import Path
import re

from . import c01, review_trial
from .campaign import sha, request_key, observed_transport, RESERVE_PER_CALL, PRICE_PER_MILLION
from .contracts import DecisionResult, provider_configuration, require
from .session import Session, Limits, implementation_digest, read_record, write_once

DOCS = Path('docs/internal/research/typed-decision/language-diagnostic')
FREEZE = DOCS/'freeze.json'
LIMITS = Limits(max_calls=96, max_seconds=300, max_request_bytes=98304)


def prepare(repo, provider, freeze_path=None):
    freeze_path = freeze_path or FREEZE
    freeze=json.loads((repo/freeze_path).read_text())
    require(freeze['implementation']==implementation_digest(),'language runtime changed')
    require(freeze['graph']==c01.GRAPH,'language graph changed')
    for name,value in freeze['files'].items():
        require(sha(repo/name)==value,'language frozen file changed:'+name)
    cases=json.loads((repo/DOCS/'cases.json').read_text())['cases']
    require(len(cases)==32 and len({c['id'] for c in cases})==32,'language case population changed')
    roots={'source':repo,'english':repo/DOCS/'english'}
    for root in roots.values():
        for owner in sorted(c01.METHODS | {'using-mindthus'}):
            path=root/'skills'/owner/'SKILL.md'
            name=str(path.relative_to(repo))
            require(path.is_file() and name in freeze['files'], 'unbound or missing method translation')
            require(bool(path.read_text().strip()), 'empty method translation')
    admissions={}
    for arm,root in roots.items():
        allowlist=set()
        class Collector:
            def __init__(self,owner):self.owner=owner
            def evaluate(self,specs,context):
                allowlist.add(request_key(specs,context))
                if arm=='english':
                    require(not re.search('[\u3400-\u9fff]',json.dumps(context,ensure_ascii=False)),
                            'English execution view contains CJK')
                values={'entry_mode':'mindthus_intervention','unresolved_obligation':'clear',
                        'owner':self.owner,'applicable':'yes'}
                return {s.id:DecisionResult('ok',values[s.id]) for s in specs}
            def finish(self,*_):return None
        for case in cases:
            for owner in sorted(c01.METHODS):c01.run(Collector(owner),case[arm],root)
        admissions[arm]={'scope':'c01-language-diagnostic-v1-'+arm,'implementation':implementation_digest(),
            'provider_configuration':provider_configuration(provider),'limits':asdict(LIMITS),
            'request_allowlist':sorted(allowlist),'max_cost_usd':96*RESERVE_PER_CALL,
            'reserve_per_call_usd':RESERVE_PER_CALL,'freeze_sha256':sha(repo/freeze_path),
            'authorization_ref':'Owner: revised steps1-4 with faithful English translation; language-diagnostic/protocol.md'}
    manifest={'admissions':admissions,'case_ids':[c['id'] for c in cases],'max_total_calls':192,
        'reserved_ceiling_usd':192*RESERVE_PER_CALL,'total_ceiling_usd':.55,
        'historical_attempts':85,'historical_reserved_usd':.22848,'semantic_revisions':0,
        'retry_policy':'none','source_language':'Chinese/mixed','comparison':'English derived execution view',
        'purpose':'paired synthetic development diagnostic, no production/holdout/ABC qualification'}
    return manifest,cases,roots


def summarize(rows):
    result={}
    for arm in ('source','english'):
        items=[r for r in rows if r['arm']==arm]
        semantic=[r for r in items if not r['mechanical_d0']]
        strata=sorted({r['family'] for r in items})
        result[arm]={'all':review_trial.score_totals(items),
            'semantic_only':review_trial.score_totals(semantic),
            'mechanical_d0':review_trial.score_totals([r for r in items if r['mechanical_d0']]),
            'by_family':{f:review_trial.score_totals([r for r in items if r['family']==f]) for f in strata},
            'fallbacks':[r['case_id'] for r in items if r['observed']['route']=='llm_fallback'],
            'mismatches':[r['case_id'] for r in items if r['score']['joint'] is False]}
    pairs={};semantic_pairs={};disagreements=[]
    for ident in sorted({r['case_id'] for r in rows}):
        pair={r['arm']:r for r in rows if r['case_id']==ident}
        if set(pair)!= {'source','english'}:continue
        key=('both_correct' if all(r['score']['joint'] for r in pair.values()) else
             'english_only' if pair['english']['score']['joint'] else
             'source_only' if pair['source']['score']['joint'] else 'neither')
        pairs[key]=pairs.get(key,0)+1
        if not pair['source']['mechanical_d0']:
            semantic_pairs[key]=semantic_pairs.get(key,0)+1
        if pair['source']['observed']!=pair['english']['observed']:
            disagreements.append({'case_id':ident,**{a:r['observed'] for a,r in pair.items()}})
    return {'arms':result,'paired_joint':pairs,'semantic_paired_joint':semantic_pairs,
            'complete_pairs':sum(pairs.values()),'disagreements':disagreements}


def run(repo,series,provider,manifest,*,freeze_path=None):
    require(provider.is_live,'live or explicitly injected live provider required')
    require(read_record(series/'campaign.json')==manifest,'language manifest changed')
    require(not (series/'summary.json').exists(),'language diagnostic finished')
    require(not list(series.glob('*/calls/*/intent.json')),'language diagnostic cannot restart')
    current,cases,roots=prepare(repo,provider,freeze_path)
    require(current==manifest,'language admission changed')
    for arm in roots:
        require(read_record(series/arm/'campaign.json')==manifest['admissions'][arm],'language arm changed')
    original=provider.transport;rows=[];stop=None;last={};resolved=None
    try:
        for index,case in enumerate(cases):
            arms=('source','english') if index%2==0 else ('english','source')
            for arm in arms:
                root=series/arm;admission=manifest['admissions'][arm]
                provider.transport=observed_transport(root,original)
                with Session(root,provider,scope=admission['scope'],limits=LIMITS,live_admission=admission) as session:
                    report=c01.run(session,case[arm],roots[arm])
                last[arm]=report;r=report['result']
                observed={k:r.get(k) for k in ('entry_mode','route','owner')}
                row={'case_id':case['id'],'family':case['family'],'arm':arm,'observed':observed,
                    'score':review_trial.score_joint(observed,case['accepted']),
                    'mechanical_d0':c01.input_problem(case[arm]) is not None,
                    'result':r,'run_id':report['run_id'],'call_keys':report['call_keys'],'nodes':[]}
                for key in report['call_keys']:
                    outcome=read_record(root/'calls'/key/'outcome.json')
                    row['nodes'].append({'call_key':key,'results':outcome['results']})
                    runtime=outcome['resolved_runtime']
                    if runtime is not None:
                        if resolved is None:resolved=runtime
                        elif runtime!=resolved:stop='cross_view_runtime_drift'
                    if any(x['status']!='ok' for x in outcome['results'].values()):stop='technical_failure'
                    usage=outcome['usage']
                    if usage['input_tokens'] is not None and usage['input_tokens']>64000:stop='input_reserve_exceeded'
                    if usage['cost_usd'] is not None and usage['cost_usd']>RESERVE_PER_CALL:stop='cost_reserve_exceeded'
                if r['status']=='provider_error' or (not row['mechanical_d0'] and
                        r['status'] in ('missing_context','unsupported')):stop='technical_failure'
                if r['consumption']!='not_executed':stop='unauthorized_consumption'
                if not set(case[arm]['known_obligations'])<=set(r['obligations']):stop='lost_known_obligation'
                if case[arm]['known_obligations'] and r['route'] not in ('llm_fallback','original_path'):
                    stop='blocking_obligation_bypassed'
                rows.append(row);write_once(root/'rows'/(case['id']+'.json'),row)
                print(json.dumps({'case':case['id'],'arm':arm,'joint':row['score']['joint'],
                                  'route':r['route'],'stop':stop}),flush=True)
                if stop:break
            if index==7 and stop is None:
                write_once(series/'first-eight-checkpoint.json',{'case_ids':[c['id'] for c in cases[:8]],
                    'completed_views':len(rows),'technical_authority_stop':None,
                    'action':'continue frozen coverage regardless of ordinary semantic mismatch'})
            if stop:break
        attempts={arm:len(list((series/arm/'calls').glob('*/intent.json'))) for arm in roots}
        require(sum(attempts.values())<=192,'language total call cap exceeded')
        summary={'analysis':summarize(rows),'rows':rows,'stop_reason':stop,'completed_views':len(rows),
            'planned_views':64,'unrun':[{'case_id':c['id'],'arm':a} for c in cases for a in roots
                if not any(r['case_id']==c['id'] and r['arm']==a for r in rows)],
            'attempts':attempts,'total_attempts':sum(attempts.values()),
            'reserved_usd':sum(attempts.values())*RESERVE_PER_CALL,
            'usage':{a:last.get(a,{}).get('trial_usage') for a in roots},
            'inference_seconds':{a:last.get(a,{}).get('trial_inference_seconds') for a in roots},
            'estimated_input_cost_usd':{a:None if last.get(a,{}).get('trial_usage',{}).get('input_tokens') is None
                else last[a]['trial_usage']['input_tokens']*PRICE_PER_MILLION/1000000 for a in roots},
            'resolved_runtime':resolved,'translation_and_host_cost':'unknown',
            'translation_latency':'offline preparation; no production latency claim',
            'qualification':'development diagnostic only','holdout':'not_run','abc':'not_run'}
        write_once(series/'summary.json',summary)
        return summary
    finally:provider.transport=original
