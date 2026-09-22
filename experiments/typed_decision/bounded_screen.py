"""Six predeclared diagnostic calls, not a graph designer or qualification suite."""
from dataclasses import asdict
from pathlib import Path

from . import c01, c02, review_trial
from .campaign import observed_transport, request_key, sha, RESERVE_PER_CALL, PRICE_PER_MILLION
from .contracts import DecisionResult, require
from .session import Limits, Session, read_record, write_once

LIMITS = Limits(max_calls=6, max_seconds=90, max_request_bytes=98304)


def series_admission(series, stage_calls):
    """Count every persisted attempt across stage roots, including failed attempts."""
    intents = list(Path(series).glob('*/calls/*/intent.json'))
    for intent in intents:
        read_record(intent)
        require(intent.with_name('outcome.json').exists(), 'series has unresolved attempt')
        outcome = read_record(intent.with_name('outcome.json'))
        require(all(r['status'] == 'ok' for r in outcome['results'].values()), 'series has technical failure')
        usage = outcome['usage']
        require(usage['input_tokens'] is None or usage['input_tokens'] <= 64000,
                'series input reserve exceeded')
        require(usage['cost_usd'] is None or usage['cost_usd'] <= RESERVE_PER_CALL,
                'series cost reserve exceeded')
    require(len(intents) + stage_calls <= 60, 'series call cap exceeded')
    require((len(intents) + stage_calls) * RESERVE_PER_CALL <= .17, 'series reserve exceeded')
    return {'prior_attempts':len(intents), 'stage_max_calls':stage_calls,
            'reserved_total_ceiling_usd':(len(intents)+stage_calls)*RESERVE_PER_CALL}


def items(repo, contract, cases):
    result = []
    for ident, expected in [('N04','yes'),('N02','no')]:
        case = next(c for c in cases['c01'] if c['id'] == ident)
        captured = []
        class Collector:
            def evaluate(self, specs, context):
                if specs[0].id == 'applicable': captured.append((specs,context))
                values = {'entry_mode':'mindthus_intervention','unresolved_obligation':'clear',
                          'owner':'sra','applicable':'yes'}
                return {s.id:DecisionResult('ok',values[s.id]) for s in specs}
            def finish(self, *_): return None
        c01.run(Collector(),case['context'],repo)
        require(len(captured)==1, 'missing applicability probe')
        specs,context = captured[0]
        result.append({'id':ident,'kind':'applicability_node_only','specs':specs,'context':context,
                       'accepted':[{'applicable':expected}]})
    for ident in ('N07','N08','N11','N12'):
        case = next(c for c in cases['c02'] if c['id']==ident)
        result.append({'id':ident,'kind':'c02_plan','specs':c02.specs(contract),
                       'context':case['context'],'accepted':case['accepted']})
    return result


def prepare(repo, provider, freeze_path):
    full, contract, cases = review_trial.prepare(repo,provider,freeze_path=freeze_path)
    probes = items(repo,contract,cases)
    admission = {**full['admission'], 'scope':full['admission']['scope']+'-screen',
        'limits':asdict(LIMITS), 'max_cost_usd':6*RESERVE_PER_CALL,
        'request_allowlist':sorted(request_key(p['specs'],p['context']) for p in probes)}
    return {'admission':admission, 'ids':[p['id'] for p in probes],
            'scoring':'all 6 joint; node-only C01 is not whole-graph acceptance'},contract,probes


def run(repo, series, root, provider, freeze_path, manifest):
    require(root.parent.resolve()==series.resolve(), 'stage outside series')
    require(not list((root/'calls').glob('*/intent.json')), 'screen cannot resume or retry')
    require(not (root/'summary.json').exists(), 'screen already finished')
    require(read_record(root/'campaign.json')==manifest, 'screen manifest changed')
    current,contract,probes = prepare(repo,provider,freeze_path)
    require(current==manifest, 'screen source or admission changed')
    budget = series_admission(series,6)
    original = provider.transport
    provider.transport = observed_transport(root,original)
    rows=[]; stop=None; report={}
    try:
        for probe in probes:
            with Session(root,provider,scope=manifest['admission']['scope'],limits=LIMITS,
                         live_admission=manifest['admission']) as session:
                if probe['kind']=='applicability_node_only':
                    answers=session.evaluate(probe['specs'],probe['context'])
                    observed={k:a.value for k,a in answers.items()}
                    technical=any(a.status!='ok' for a in answers.values())
                    report=session.finish({'id':'mindthus.c01-applicability-probe','version':'3.1'},
                        probe['context'],{'observed':observed,'whole_graph':False,'consumption':'not_executed'})
                else:
                    report=c02.plan(session,probe['context'],contract)
                    r=report['result'];observed={**r['judgments'],'route':r['route']}
                    technical=r['reason'] in ('local_judgment_unavailable','contract_budget_or_recovery_failure')
                score=review_trial.score_joint(observed,probe['accepted'])
            row={'case_id':probe['id'],'kind':probe['kind'],'observed':observed,'score':score,
                 'run_id':report['run_id'],'call_keys':report['call_keys'],'result':report['result']}
            rows.append(row);write_once(root/'rows'/(probe['id']+'.json'),row)
            if technical: stop='technical_failure'
            for key in report['call_keys']:
                usage=read_record(root/'calls'/key/'outcome.json')['usage']
                if usage['input_tokens'] is not None and usage['input_tokens']>64000: stop='reserve_exceeded'
                if usage['cost_usd'] is not None and usage['cost_usd']>RESERVE_PER_CALL: stop='reserve_exceeded'
            if stop: break
        matched={r['case_id']:r['score']['joint'] for r in rows}
        controls=all(matched.get(i) is True for i in ('N02','N07','N11'))
        repaired=sum(matched.get(i) is True for i in ('N04','N08','N12'))
        passed=stop is None and len(rows)==6 and all(matched.values())
        attempts=len(list((root/'calls').glob('*/intent.json')))
        usage=report.get('trial_usage',{})
        summary={'rows':rows,'totals':review_trial.score_totals(rows),'passed':passed,
            'controls_preserved':controls,'failure_families_repaired':repaired,
            'candidate_2_may_be_considered':stop is None and controls and repaired>=2 and not passed,
            'candidate_2_requires':'specific new root-cause evidence; never automatic',
            'stop_reason':stop,'attempts':attempts,'reserved_usd':attempts*RESERVE_PER_CALL,
            'series_budget':budget,'trial_usage':usage,'resolved_runtimes':report.get('resolved_runtimes'),
            'estimated_input_cost_usd':None if usage.get('input_tokens') is None else
                usage['input_tokens']*PRICE_PER_MILLION/1000000,
            'host_cost':'unknown','full_development':'not_run','holdout':'not_run'}
        write_once(root/'summary.json',summary)
        return summary
    finally: provider.transport=original
