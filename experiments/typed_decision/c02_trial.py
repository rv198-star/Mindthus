"""Frozen C02 development planner trial; reuses the existing Session and transport."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from . import c02
from .campaign import observed_transport, request_key, sha, RESERVE_PER_CALL
from .contracts import digest, provider_configuration, require
from .providers import TypeSafeJevProvider
from .session import Limits, Session, implementation_digest, read_record, write_once

DOCS = Path('docs/internal/research/typed-decision')
FREEZE = DOCS / 'c02-development-freeze.json'
LIMITS = Limits(max_calls=24, max_seconds=120, max_request_bytes=98304)


def inputs(repo):
    design = json.loads((repo / DOCS / 'c02-local-contract.json').read_text())
    cases = json.loads((repo / DOCS / 'c02-zh-development.json').read_text())['cases']
    tvg = (repo / 'skills/tvg/SKILL.md').read_text()
    for case in cases:
        case['context']['tvg_contract'] = tvg
    return design, cases


def prepare(repo, provider):
    freeze = json.loads((repo / FREEZE).read_text())
    for path, expected in freeze['file_sha256'].items():
        require(sha(repo / path) == expected, 'C02 frozen source changed:' + path)
    require(freeze['implementation'] == implementation_digest(), 'C02 runtime changed')
    design, cases = inputs(repo)
    require(len(cases) == 12 and len({c['id'] for c in cases}) == 12, 'C02 case count/identity')
    allowlist = set()
    first = c02.specs(design)
    from .contracts import DecisionSpec
    action = DecisionSpec('action', design['action']['question'], design['action']['criteria'],
        c02.READS + ('weaknesses',), version=design['version'], policy_ref='c02-one-local-rewrite-v1',
        fallback_ref='original-tvg-exit-owner')
    for case in cases:
        # Egress enumeration is independent of expected labels and observations.
        view = {k: case['context'][k] for k in c02.READS}
        allowlist.add(request_key(first, view))
        for utility in ('adequate', 'deficit'):
            allowlist.add(request_key([action], {**view, 'weaknesses': {
                'utility': utility, 'support': 'sufficient'}}))
    admission = {'scope': 'c02-development-v1-typesafe', 'implementation': implementation_digest(),
        'provider_configuration': provider_configuration(provider), 'limits': asdict(LIMITS),
        'request_allowlist': sorted(allowlist), 'max_cost_usd': 24 * RESERVE_PER_CALL,
        'reserve_per_call_usd': RESERVE_PER_CALL, 'freeze_sha256': sha(repo / FREEZE),
        'authorization_ref': 'Owner sequential issue implementation; c02-admission.md and c02-protocol.md'}
    return {'admission': admission, 'case_ids': [c['id'] for c in cases],
            'purpose': 'C02 development local decisions, not final artifact/value acceptance',
            'series_jev_cost_cap_usd': .25, 'series_prior_attempts': 0,
            'semantic_revisions_used': 0, 'retry_policy': 'none'}, design, cases


def run(repo, root, provider, manifest, design, cases):
    require(read_record(root / 'campaign.json') == manifest, 'C02 manifest changed')
    require(not (root / 'summary.json').exists(), 'C02 trial finished; read original summary')
    require(provider.is_live, 'C02 live trial requires actual provider')
    original_transport = provider.transport
    provider.transport = observed_transport(root, original_transport)
    rows, reports, stopped = [], [], None
    try:
        for case in cases:
            with Session(root, provider, scope=manifest['admission']['scope'], limits=LIMITS,
                         live_admission=manifest['admission']) as session:
                report = c02.plan(session, case['context'], design)
            result = report['result']
            expected = case['expected']
            matches = {k: result.get(k) == expected[k] for k in ('route', 'action')}
            matches.update({k: expected[k] is None or result['judgments'].get(k) == expected[k]
                            for k in ('utility', 'support')})
            rows.append({'case_id': case['id'], 'expected': expected, 'observed': result,
                         'matches': matches, 'run_id': report['run_id']})
            reports.append(report)
            if result['reason'] in ('local_judgment_unavailable', 'contract_budget_or_recovery_failure'):
                stopped = 'technical_failure'
            elif case['category'] in ('missing_evidence', 'conflicting_target', 'outside_scope') \
                    and result['route'] == 'rewrite_candidate':
                stopped = 'unsupported_rewrite'
            elif result['exit_state'] is not None or result['consumption'] != 'not_executed':
                stopped = 'unauthorized_exit_or_consumption'
            if stopped:
                break
        last = reports[-1] if reports else {}
        totals = {key: sum(r['matches'][key] for r in rows) for key in ('route', 'action', 'utility', 'support')}
        action_rows = [r for r in rows if r['expected']['action'] is not None]
        eligible = len(rows) == 12 and stopped is None and totals['route'] >= 11 and totals['utility'] >= 11 \
            and len(action_rows) == 6 and all(r['matches']['action'] for r in action_rows)
        summary = {'campaign': manifest['admission']['scope'], 'rows': rows, 'matches': totals,
            'cases_observed': len(rows), 'cases_planned': 12, 'stop_reason': stopped,
            'local_decision_gate_met': eligible, 'final_artifact_gate': 'not_evaluated',
            'holdout': 'not_run', 'abc': 'not_run', 'value_qualification': 'unknown',
            'unique_calls': len(list((root / 'calls').glob('*/intent.json'))),
            'trial_usage': last.get('trial_usage'), 'trial_inference_seconds': last.get('trial_inference_seconds'),
            'resolved_runtimes': last.get('resolved_runtimes'),
            'cost_coverage': 'inference telemetry only; host design/generation/review unknown',
            'semantic_revisions_used': 0}
        write_once(root / 'summary.json', summary)
        return summary
    finally:
        provider.transport = original_transport


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'report'))
    parser.add_argument('--state-root', type=Path, required=True)
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    root = args.state_root.resolve()
    require(root != repo and repo not in root.parents, 'C02 state must remain outside repo')
    if args.action == 'report':
        result = read_record(root / 'summary.json')
    else:
        provider = TypeSafeJevProvider()
        manifest, design, cases = prepare(repo, provider)
        if args.action == 'prepare':
            if (root / 'campaign.json').exists():
                require(read_record(root / 'campaign.json') == manifest, 'C02 prepared manifest changed')
            else:
                write_once(root / 'campaign.json', manifest)
            result = {'cases': len(cases), 'request_variants': len(manifest['admission']['request_allowlist']),
                      'maximum_reserved_usd': manifest['admission']['max_cost_usd']}
        else:
            result = run(repo, root, provider, manifest, design, cases)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
