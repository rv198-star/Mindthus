"""One frozen reviewed development run; no old-score replacement or auto promotion."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from . import c01, c02
from .campaign import observed_transport, request_key, sha, RESERVE_PER_CALL, PRICE_PER_MILLION, INPUT_TOKEN_CEILING
from .contracts import DecisionResult, ContractError, provider_configuration, require
from .session import Limits, Session, implementation_digest, read_record, write_once

DOCS = Path('docs/internal/research/typed-decision/review-remediation')
FREEZE = DOCS / 'live-freeze.json'
LIMITS = Limits(max_calls=23, max_seconds=180, max_request_bytes=98304)
SCOPE = 'reviewed-c01-v3-c02-v2-dev-r1'


def score_joint(observed, accepted, *, unscored=()):
    """Compare complete alternatives; unknown gold is not a match or denominator."""
    if accepted is None:
        return {'joint': None, 'fields': {}, 'abstentions': []}
    require(isinstance(accepted, list) and bool(accepted), 'missing accepted alternatives')
    keys = set(accepted[0])
    require(all(set(a) == keys for a in accepted), 'inconsistent accepted fields')
    require(set(unscored) <= keys, 'unknown unscored field')
    fields = {key: (None if key in unscored else any(
        key in observed and observed[key] == alternative[key] for alternative in accepted))
        for key in sorted(keys)}
    joint = any(all(key in observed and observed[key] == alternative[key]
                    for key in keys - set(unscored)) for alternative in accepted)
    return {'joint': joint, 'fields': fields, 'abstentions': [key for key in sorted(keys)
        if key in observed and observed[key] in ('unclear', 'abstain')]}


def score_totals(rows):
    fields = sorted({k for row in rows for k in row['score']['fields']})
    return {'joint': {'matched': sum(r['score']['joint'] is True for r in rows),
                      'scored': sum(r['score']['joint'] is not None for r in rows)},
            'fields': {key: {'matched': sum(r['score']['fields'].get(key) is True for r in rows),
                            'scored': sum(r['score']['fields'].get(key) is not None for r in rows)}
                       for key in fields},
            'abstentions': [{'case_id': r['case_id'], 'fields': r['score']['abstentions']}
                            for r in rows if r['score']['abstentions']]}


def inputs(repo):
    cases = json.loads((repo / DOCS / 'cases.json').read_text())
    contract = json.loads((repo / DOCS / 'c02-contract-v2.json').read_text())
    tvg = (repo / 'skills/tvg/SKILL.md').read_text()
    for case in cases['c02'] + cases['fidelity_counterexamples']:
        case['context']['tvg_contract'] = tvg
    return contract, cases


def prepare(repo, provider):
    freeze = json.loads((repo / FREEZE).read_text())
    require(freeze['implementation'] == implementation_digest(), 'reviewed runtime changed')
    for name, expected in freeze['file_sha256'].items():
        require(sha(repo / name) == expected, 'reviewed frozen file changed:' + name)
    contract, cases = inputs(repo)
    selected = [c for c in cases['c01'] if c['contract_accepted'] is not None]
    require([c['id'] for c in selected] == ['N02', 'N03', 'N04'], 'reviewed C01 population changed')
    require([c['id'] for c in cases['c02']] == ['N05','N06','N07','N08','N09','N10','N11','N12'],
            'reviewed C02 population changed')
    require(len(cases['fidelity_counterexamples']) == 6, 'fidelity population changed')
    allowlist = set()

    class Collector:
        def __init__(self, owner): self.owner = owner
        def evaluate(self, specs, context):
            allowlist.add(request_key(specs, context))
            values = {'entry_mode':'mindthus_intervention', 'unresolved_obligation':'clear',
                      'owner':self.owner, 'applicable':'yes'}
            return {s.id: DecisionResult('ok', values[s.id]) for s in specs}
        def finish(self, *_): return None

    for case in selected:
        for owner in sorted(c01.METHODS):
            c01.run(Collector(owner), case['context'], repo)
    for case in cases['c02']:
        allowlist.add(request_key(c02.specs(contract), case['context']))
    for case in cases['fidelity_counterexamples']:
        allowlist.add(request_key(c02.specs(contract, recheck=True), case['context']))
    admission = {'scope':SCOPE, 'implementation':implementation_digest(),
        'provider_configuration':provider_configuration(provider), 'limits':asdict(LIMITS),
        'request_allowlist':sorted(allowlist), 'max_cost_usd':23 * RESERVE_PER_CALL,
        'reserve_per_call_usd':RESERVE_PER_CALL, 'freeze_sha256':sha(repo / FREEZE),
        'authorization_ref':'Owner: continue testing; review-remediation/live-protocol.md r1'}
    manifest = {'admission':admission, 'c01_ids':[c['id'] for c in selected],
        'c02_ids':[c['id'] for c in cases['c02']],
        'fidelity_ids':[c['id'] for c in cases['fidelity_counterexamples']],
        'excluded':[{'case_id':c['id'], 'reason':'contract_gold_unadjudicated'}
                    for c in cases['c01'] if c['contract_accepted'] is None],
        'semantic_revisions_allowed':0, 'retry_policy':'none', 'series_call_cap':25,
        'series_reserved_usd':25 * RESERVE_PER_CALL, 'series_ceiling_usd':.07,
        'historical_attempts':60, 'historical_reserved_usd':.161280}
    return manifest, contract, cases


def run(repo, root, provider, manifest, contract, cases):
    require(provider.is_live, 'actual or explicitly injected live transport required')
    require(read_record(root / 'campaign.json') == manifest, 'reviewed manifest changed')
    require(not (root / 'summary.json').exists(), 'reviewed trial already finished')
    # Revalidate source, labels and exact admission before sending anything.
    current, current_contract, current_cases = prepare(repo, provider)
    require(contract == current_contract and cases == current_cases, 'reviewed inputs changed')
    require(current == manifest, 'reviewed admission changed')
    original = provider.transport
    provider.transport = observed_transport(root, original)
    rows = {'c01':[], 'c02':[], 'fidelity':[]}
    stop = None
    last = {}
    todo = [('c01',c) for c in cases['c01'] if c['id'] in manifest['c01_ids']]
    todo += [('c02',c) for c in cases['c02']]
    todo += [('fidelity',c) for c in cases['fidelity_counterexamples']]
    try:
        for group, case in todo:
            with Session(root, provider, scope=SCOPE, limits=LIMITS,
                         live_admission=manifest['admission']) as session:
                if group == 'c01':
                    report = c01.run(session, case['context'], repo)
                    result = report['result']; observed = {k:result.get(k) for k in ('entry_mode','route','owner')}
                    score = score_joint(observed, case['contract_accepted'])
                    technical = result['status'] in ('provider_error','missing_context','unsupported')
                elif group == 'c02':
                    report = c02.plan(session, case['context'], contract)
                    result = report['result']
                    observed = {**result['judgments'], 'route':result['route']}
                    ignored = tuple(k for k in case['accepted'][0] if case['accepted'][0][k] is None)
                    score = score_joint(observed, case['accepted'], unscored=ignored)
                    technical = result['reason'] in ('local_judgment_unavailable','contract_budget_or_recovery_failure')
                else:
                    answers = session.evaluate(c02.specs(contract,recheck=True), case['context'])
                    result = {k:{'status':v.status,'value':v.value} for k,v in answers.items()}
                    report = session.finish({'id':'mindthus.c02-fixed-artifact-diagnostic','version':'2'},
                                            case['context'], result)
                    observed = {'fidelity':answers['recheck_fidelity'].value}
                    score = score_joint(observed, [{'fidelity':case['expected_fidelity']}])
                    technical = any(a.status != 'ok' for a in answers.values())
                last = report
            row = {'case_id':case['id'],'observed':observed,'result':result,
                   'score':score,'run_id':report['run_id'],'call_keys':report['call_keys']}
            if group == 'c02':
                row['raw_action'] = result['judgments'].get('action')
                row['rewrite_handoff_action'] = (result['action'] if result['route'] == 'rewrite_candidate' else None)
                row['consumption'] = result['consumption']
            row_path = root / 'rows' / (case['id']+'.json')
            if row_path.exists():
                require(read_record(row_path) == row, 'reviewed row changed')
            else:
                write_once(row_path, row)
            rows[group].append(row)
            if technical:
                stop = 'technical_failure'
            if group != 'fidelity' and (result.get('consumption') != 'not_executed'
                                        or result.get('exit_state') is not None):
                stop = 'unauthorized_consumption_or_exit'
            if group == 'c02' and case['id'] in ('N08','N09','N10') and result['route']=='rewrite_candidate':
                stop = 'unsupported_rewrite'
            for key in report['call_keys']:
                outcome = read_record(root / 'calls' / key / 'outcome.json')
                tokens = outcome['usage']['input_tokens']
                if tokens is not None and tokens > INPUT_TOKEN_CEILING:
                    stop = 'reported_input_tokens_exceed_reserve_assumption'
                cost = outcome['usage']['cost_usd']
                if cost is not None and cost > RESERVE_PER_CALL:
                    stop = 'reported_cost_exceeds_reserve'
            if stop: break
        totals = {group:score_totals(items) for group,items in rows.items()}
        gates = {group:stop is None and totals[group]['joint']=={'matched':n,'scored':n}
                 for group,n in [('c01',3),('c02',8),('fidelity',6)]}
        observed_ids = {r['case_id'] for group in rows.values() for r in group}
        calls = len(list((root/'calls').glob('*/intent.json')))
        usage = last.get('trial_usage',{})
        summary = {'scope':SCOPE,'rows':rows,'totals':totals,'local_gates':gates,
            'stop_reason':stop,'observed_cases':len(observed_ids),'planned_cases':17,
            'unrun':[c['id'] for _,c in todo if c['id'] not in observed_ids],
            'excluded':manifest['excluded'],'attempts':calls,'reserved_usd':calls*RESERVE_PER_CALL,
            'trial_usage':usage,'estimated_input_cost_usd':None if usage.get('input_tokens') is None else
                usage['input_tokens']*PRICE_PER_MILLION/1_000_000,
            'trial_inference_seconds':last.get('trial_inference_seconds'),
            'resolved_runtimes':last.get('resolved_runtimes'),
            'generation_eligible':gates['c02'] and gates['fidelity'],
            'actual_generation':'not_run','holdout':'not_frozen_or_run','abc':'not_run',
            'semantic_qualification':'bounded development observations only',
            'host_cost':'unknown','semantic_revisions_used':0}
        write_once(root/'summary.json',summary)
        return summary
    finally:
        provider.transport = original
