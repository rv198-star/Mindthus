"""One frozen C01 Chinese development campaign; no native host actions or retries."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import getpass
import json
import os
import math
import re
import sys
from pathlib import Path

from . import c01
from .contracts import ContractError, DecisionResult, digest, project_context, provider_configuration, require
from .providers import TypeSafeJevProvider
from .session import Limits, RecoveryRequired, Session, implementation_digest, read_record, write_once, safe_failure_reason

DOCS = Path('docs/internal/research/typed-decision')
FREEZE = DOCS / 'c01-v2-development-freeze.json'
DATA = DOCS / 'c01-v2-zh-development.json'
LIMITS = Limits(max_calls=78, max_seconds=300, max_request_bytes=98304)
SCOPE = 'c01-v2-zh-development-typesafe-1'
PRICE_PER_MILLION = .042
INPUT_TOKEN_CEILING = 64000
RESERVE_PER_CALL = INPUT_TOKEN_CEILING * PRICE_PER_MILLION / 1_000_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request_key(specs, context) -> str:
    return digest({'questions': [s.to_dict() for s in specs],
                   'context_sha256': digest(project_context(specs, context))})


def prepare(repo: Path, provider, recovery: Path | None = None,
            recovery_reason: str | None = None) -> tuple[dict, list]:
    """Explore possible control paths to admit exact requests; never consult labels."""
    freeze = json.loads((repo / FREEZE).read_text())
    for path, expected in freeze['file_sha256'].items():
        require(sha(repo / path) == expected, 'frozen source/data changed:' + path)
    require(freeze['graph'] == c01.GRAPH, 'frozen graph changed')
    cases = json.loads((repo / DATA).read_text())['cases']
    require(len(cases) == freeze['case_count'] and len({c['id'] for c in cases}) == len(cases),
            'case identity/count mismatch')
    allowlist = set()

    class RequestCollector:
        def __init__(self, owner):
            self.owner = owner

        def evaluate(self, specs, context):
            allowlist.add(request_key(specs, context))
            values = {'entry_mode': 'mindthus_intervention', 'unresolved_obligation': 'clear',
                      'owner': self.owner, 'applicable': 'yes'}
            return {s.id: DecisionResult('ok', values[s.id]) for s in specs}

        def finish(self, *_):
            return None

    for case in cases:
        # The collector explores every eligible owner, independent of expected answers.
        for owner in sorted(c01.METHODS):
            c01.run(RequestCollector(owner), case['context'], repo)
    admission = {
        'scope': SCOPE, 'implementation': implementation_digest(),
        'provider_configuration': provider_configuration(provider), 'limits': asdict(LIMITS),
        'request_allowlist': sorted(allowlist), 'max_cost_usd': .25,
        'reserve_per_call_usd': RESERVE_PER_CALL,
        'authorization_ref': 'Owner request: frozen Chinese development, official serving first; advisory only',
        'freeze_sha256': sha(repo / FREEZE),
    }
    manifest = {
        'schema_version': 'mindthus.c01-live-development.v1', 'admission': admission,
        'case_ids': [c['id'] for c in cases], 'dataset_sha256': sha(repo / DATA),
        'graph_sha256': digest(c01.GRAPH), 'semantic_revisions_used': 0,
        'purpose': 'development-local-judgments-only', 'downstream_consumption': 'not_authorized',
        'pricing': {'source': 'https://docs.typesafe.ai/models', 'checked_on': '2026-09-22',
                    'input_usd_per_million': PRICE_PER_MILLION, 'output_usd': 0,
                    'input_token_ceiling_per_call': INPUT_TOKEN_CEILING,
                    'maximum_reserved_usd': LIMITS.max_calls * RESERVE_PER_CALL,
                    'missing_actual_cost': 'unknown; price-derived estimates reported separately'},
        'retry_policy': 'none; unknown in-flight call stops; never delete/reset a trial to retry',
        'egress': 'frozen synthetic context + exact relevant canonical contracts/questions only',
    }
    if recovery is not None:
        recovery = recovery.resolve()
        parent = read_record(recovery / 'campaign.json')
        terminal = read_record(recovery / 'summary.json')
        require(terminal['stop_reason'] == 'provider_or_contract_failure',
                'technical recovery requires a terminal technical failure')
        require(parent['admission']['implementation'] != admission['implementation'],
                'technical recovery requires a named source delta')
        require(parent['admission']['freeze_sha256'] == admission['freeze_sha256']
                and parent['dataset_sha256'] == manifest['dataset_sha256']
                and parent['graph_sha256'] == manifest['graph_sha256'], 'semantic freeze changed')
        require(isinstance(recovery_reason, str) and bool(recovery_reason.strip())
                and len(recovery_reason) <= 512, 'technical recovery reason required')
        prior = parent.get('technical_recovery', {})
        ordinal = prior.get('ordinal', 0) + 1
        require(ordinal <= 2, 'technical recovery limit reached')
        intents = list((recovery / 'calls').glob('*/intent.json')) + list(
            recovery.glob('transport-diagnostic-*/intent.json'))
        require(all((p.parent / 'outcome.json').exists() for p in intents),
                'unresolved parent call; recovery cannot resubmit')
        reserved = prior.get('prior_reserved_usd', 0) + len(intents) * RESERVE_PER_CALL
        require(reserved + RESERVE_PER_CALL <= .25, 'series budget exhausted')
        admission['max_cost_usd'] = .25 - reserved
        admission['scope'] = SCOPE + '-technical-recovery-' + str(ordinal)
        manifest['technical_recovery'] = {
            'ordinal': ordinal, 'parent_root': str(recovery), 'reason': recovery_reason,
            'parent_summary_sha256': sha(recovery / 'summary.json'),
            'parent_manifest_sha256': sha(recovery / 'campaign.json'),
            'prior_reserved_usd': reserved, 'series_cost_cap_usd': .25,
            'same_semantic_sample': True, 'semantic_revisions_used': 0,
        }
    return manifest, cases


def observed_transport(root: Path, transport):
    """Capture numeric/schema facts before adapter validation; no headers or remote prose."""
    def numeric(value):
        if type(value) in (int, float) and math.isfinite(value):
            return value
        return {'invalid_type': type(value).__name__}

    def call(url, headers, body, timeout):
        record = {'body_sha256': digest(body), 'context_sha256': digest(body['state']),
                  'question_ids': sorted(body['questions'])}
        path = root / 'wire' / (digest(body) + '.json')
        require(not path.exists(), 'wire observation already exists; reconcile before resubmission')
        try:
            raw = transport(url, headers, body, timeout)
        except Exception as exc:
            record['failure'] = safe_failure_reason(exc)
            write_once(path, record)
            raise
        record['response_type'] = type(raw).__name__
        if isinstance(raw, dict):
            model = raw.get('model')
            record['model'] = model if isinstance(model, str) and re.fullmatch(
                r'(?:typesafe/)?jev-\d+\.\d+(?:\.\d+)?(?:-\d{8})?', model) else None
            record['model_type'] = type(model).__name__
            usage = raw.get('usage')
            record['usage_type'] = type(usage).__name__
            if isinstance(usage, dict):
                record['usage'] = {k: numeric(usage[k]) for k in
                                   ('input_tokens', 'output_tokens', 'cost') if k in usage}
            answers = raw.get('answers')
            record['answers_type'] = type(answers).__name__
            record['answers'] = {}
            if isinstance(answers, dict):
                record['extra_answer_count'] = len(set(answers) - set(body['questions']))
                for key, question in body['questions'].items():
                    answer = answers.get(key)
                    item = {'answer_type': type(answer).__name__}
                    if isinstance(answer, dict):
                        item['type'] = answer.get('type') if answer.get('type') in (
                            'choice', 'noul', 'score') else None
                        # This carrier's frozen C01 graph uses only Choice.
                        options = question['criteria']
                        choice = answer.get('choice')
                        item['choice'] = choice if isinstance(choice, str) and choice in options else None
                        item['confidence'] = numeric(answer.get('confidence'))
                        probabilities = answer.get('probabilities')
                        item['probabilities_type'] = type(probabilities).__name__
                        if isinstance(probabilities, dict):
                            item['extra_option_count'] = len(set(probabilities) - set(options))
                            item['probabilities'] = {k: numeric(probabilities[k])
                                                     for k in options if k in probabilities}
                    record['answers'][key] = item
        write_once(path, record)
        return raw
    return call


def observed_answers(report: dict, root: Path) -> dict:
    observed = {}
    for key in report['call_keys']:
        observed.update(read_record(root / 'calls' / key / 'outcome.json')['results'])
    return {key: value['value'] if value['status'] == 'ok' else None
            for key, value in observed.items()}


def score_case(case, report, observed) -> dict:
    expected, result = case['expected'], report['result']
    selected = observed.get('owner')
    if selected is None and 'applicable' in observed:
        selected = case['context'].get('explicit_method')
    return {'case_id': case['id'], 'family_group': case['family_group'],
            'expected': expected, 'observed': {**observed, 'selected_owner': selected,
                                              'route': result['route'], 'status': result['status'],
                                              'reason': result['reason']},
            'run_id': report['run_id'], 'call_keys': report['call_keys'],
            'd0_match': (not report['call_keys'] and result['route'] == expected['route']
                         if expected['entry_mode'] is None else bool(report['call_keys'])),
            'obligation_match': observed.get('unresolved_obligation') == expected['unresolved_obligation']
                                if expected['entry_mode'] is not None else None,
            'entry_match': result['entry_mode'] == expected['entry_mode'],
            'route_match': result['route'] == expected['route'],
            'owner_match': selected == expected['owner'] if expected['owner'] else None,
            'applicability_match': observed.get('applicable') == expected['applicable']
                                   if expected['applicable'] else None}


def stop_reason(case, report) -> str | None:
    result = report['result']
    if result['status'] in ('provider_error', 'unsupported'):
        return 'provider_or_contract_failure'
    if result['consumption'] != 'not_executed':
        return 'unauthorized_consumption'
    if not set(case['context']['known_obligations']) <= set(result['obligations']):
        return 'erased_known_obligation'
    if case['expected']['entry_mode'] == 'mindthus_intervention' and result['route'] == 'direct_execute':
        return 'hard_judgment_sent_to_direct'
    if case['expected']['applicable'] == 'no' and result['route'] == 'intervene':
        return 'explicit_method_precondition_waived'
    if case['expected']['entry_mode'] == 'unclear' and result['route'] == 'intervene':
        return 'owner_forced_on_no_match'
    return None


def summarize(rows, reports, manifest, stopped) -> dict:
    semantic = [r for r in rows if r['expected']['entry_mode'] is not None]
    owners = [r for r in rows if r['expected']['owner'] is not None]
    last = reports[-1] if reports else {}
    usage = last.get('trial_usage', {})
    tokens = usage.get('input_tokens')
    families = {}
    for row in rows:
        matched = all(row[field] is not False for field in
                      ('d0_match', 'entry_match', 'route_match', 'obligation_match',
                       'owner_match', 'applicability_match'))
        family = families.setdefault(row['family_group'], {'case_ids': [], 'all_match': True})
        family['case_ids'].append(row['case_id'])
        family['all_match'] &= matched
    complete = len(rows) == len(manifest['case_ids']) and stopped is None
    entry_matches = sum(r['entry_match'] for r in semantic)
    route_matches = sum(r['route_match'] for r in semantic)
    d0_matches = sum(r['d0_match'] for r in rows)
    no_match = [r for r in semantic if r['expected']['entry_mode'] == 'unclear']
    return {'campaign': manifest['admission']['scope'],
            'technical_recovery': manifest.get('technical_recovery'), 'evidence_kind': 'live_model', 'cases_completed': len(rows),
            'cases_planned': len(manifest['case_ids']), 'stop_reason': stopped,
            'entry_matches': entry_matches, 'route_matches': route_matches,
            'd0_matches': d0_matches,
            'obligation_matches': sum(r['obligation_match'] for r in semantic),
            'development_thresholds_met': complete and d0_matches == 26
                                         and entry_matches >= 23 and route_matches >= 23,
            'family_pairs': families,
            'no_match_coverage': {'correct': sum(r['entry_match'] for r in no_match),
                                  'observed': len(no_match)},
            'abstentions': [r['case_id'] for r in rows if r['observed']['status'] == 'abstain'],
            'provider_status_failures': [r['case_id'] for r in rows
                                        if r['observed']['status'] in ('provider_error', 'unsupported')],
            'false_interventions': [r['case_id'] for r in rows
                                    if r['expected']['route'] != 'intervene'
                                    and r['observed']['route'] == 'intervene'],
            'unique_calls': len({key for r in rows for key in r['call_keys']}),
            'semantic_cases_completed': len(semantic),
            'owner_matches': sum(r['owner_match'] for r in owners),
            'applicability_matches': sum(r['applicability_match'] for r in owners),
            'owner_cases_completed': len(owners), 'case_results': rows,
            'trial_usage': usage, 'trial_inference_seconds': last.get('trial_inference_seconds'),
            'estimated_cost_usd_from_reported_tokens': tokens * PRICE_PER_MILLION / 1_000_000
                                                     if tokens is not None else None,
            'resolved_runtimes': last.get('resolved_runtimes', []),
            'cost_coverage': 'partial; design/review/downstream task costs not measured here',
            'claim_ceiling': 'Agreement with preauthored development labels only; no host or holdout qualification',
            'semantic_revision_used': 0, 'holdout': 'not_run', 'abc': 'not_run'}


def run(repo: Path, root: Path, provider, manifest, cases) -> dict:
    require(provider.is_live, 'campaign requires a live provider')
    require([c['id'] for c in cases] == manifest['case_ids'], 'campaign case order differs')
    require(read_record(root / 'campaign.json') == manifest, 'campaign differs from prepared manifest')
    require(not (root / 'summary.json').exists(), 'campaign already finished; read its immutable summary')
    require(bool(os.environ.get('TYPESAFE_API_KEY')), 'missing_local_Typesafe_credential')
    original_transport = provider.transport
    provider.transport = observed_transport(root, original_transport)
    try:
        rows, reports, stopped = [], [], None
        for case in cases:
            with Session(root, provider, scope=manifest['admission']['scope'], limits=LIMITS,
                         live_admission=manifest['admission']) as session:
                report = c01.run(session, case['context'], repo)
            # Labels are read by the evaluator only, after the model/graph result exists.
            row = score_case(case, report, observed_answers(report, root))
            rows.append(row)
            reports.append(report)
            stopped = stop_reason(case, report)
            if stopped:
                break
            # Pricing bounds are independently checked against reported token telemetry.
            for key in report['call_keys']:
                used = read_record(root / 'calls' / key / 'outcome.json')['usage']
                if used['input_tokens'] is not None and used['input_tokens'] > INPUT_TOKEN_CEILING:
                    stopped = 'reported_tokens_exceed_priced_ceiling'
                if used['cost_usd'] is not None and used['cost_usd'] > RESERVE_PER_CALL:
                    stopped = 'reported_cost_exceeds_reserve'
            if stopped:
                break
        summary = summarize(rows, reports, manifest, stopped)
        write_once(root / 'summary.json', summary)
        return summary
    finally:
        provider.transport = original_transport


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'report'])
    parser.add_argument('--state-root', type=Path, required=True)
    parser.add_argument('--recovery-of', type=Path)
    parser.add_argument('--recovery-reason')
    parser.add_argument('--prompt-key', action='store_true',
                        help='Read the official key with hidden input from a local terminal; never persist it')
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parents[2]
    root = args.state_root.resolve()
    injected_key = False
    try:
        require(not args.prompt_key or args.action == 'run', 'key prompt only applies to run')
        require(root != repo and repo not in root.parents, 'trial state must stay outside repository')
        if args.action == 'report':
            print(json.dumps(read_record(root / 'summary.json'), ensure_ascii=False, indent=2))
            return 0
        provider = TypeSafeJevProvider()
        manifest, cases = prepare(repo, provider, args.recovery_of, args.recovery_reason)
        if args.action == 'prepare':
            if (root / 'campaign.json').exists():
                require(read_record(root / 'campaign.json') == manifest, 'existing campaign changed')
            else:
                write_once(root / 'campaign.json', manifest)
            print(json.dumps({'prepared': str(root / 'campaign.json'), 'cases': len(cases),
                              'request_variants': len(manifest['admission']['request_allowlist']),
                              'max_calls': LIMITS.max_calls, 'max_cost_usd': manifest['admission']['max_cost_usd'],
                              'inference_performed': False}))
        else:
            # Validate the prepared campaign before asking for any credential.
            require(read_record(root / 'campaign.json') == manifest, 'campaign differs from prepared manifest')
            require(not (root / 'summary.json').exists(), 'campaign already finished')
            if args.prompt_key:
                require(sys.stdin.isatty(), 'hidden key prompt requires a local terminal')
                require(not os.environ.get('TYPESAFE_API_KEY'), 'credential already provided by environment')
                os.environ['TYPESAFE_API_KEY'] = getpass.getpass('TypeSafe official API key (hidden): ')
                injected_key = True
            if not os.environ.get('TYPESAFE_API_KEY'):
                print(json.dumps({'status': 'blocked', 'reason': 'missing_local_credential',
                                  'next': 'Use --prompt-key in a local terminal; never paste a key in chat'}))
                return 2
            summary = run(repo, root, provider, manifest, cases)
            print(json.dumps({k: v for k, v in summary.items() if k != 'case_results'},
                             ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, RecoveryRequired) as exc:
        # No remote response, key, request header or arbitrary exception text in logs.
        print(json.dumps({'status': 'blocked', 'error_type': type(exc).__name__}))
        return 2
    finally:
        if injected_key:
            os.environ.pop('TYPESAFE_API_KEY', None)


if __name__ == '__main__':
    raise SystemExit(main())
