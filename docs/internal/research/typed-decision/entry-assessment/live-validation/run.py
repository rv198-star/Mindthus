"""Bounded live development validation for C01-next P1/P2/P3.

This runner never changes question semantics after the freeze. It uses one exact
TypeSafe Jev request admission per batch and one CPA DeepSeek correction per detector
hit. Recheck admission is derived from the immutable host revision and persisted
before the recheck; it cannot be known before that revision exists.
"""
from __future__ import annotations

from dataclasses import asdict
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from experiments.typed_decision import assessment
from experiments.typed_decision.contracts import (
    DecisionResult,
    canonical,
    digest,
    project_context,
    provider_configuration,
    require,
)
from experiments.typed_decision.providers import TypeSafeJevProvider, post_json
from experiments.typed_decision.session import (
    Limits,
    RecoveryRequired,
    Session,
    implementation_digest,
    read_record,
    safe_failure_reason,
    write_once,
)

CASES = HERE / 'cases.json'
PROTOCOL = HERE / 'protocol.md'
FREEZE = HERE / 'freeze.json'
HOST_ENDPOINT = 'https://cpa.72live.com/v1/chat/completions'
HOST_MODEL = 'deepseek-v4.1-flash'
HOST_UA = 'Mindthus-Entry-Validation/1'
CHECK_LIMITS = Limits(max_calls=1, max_seconds=45, max_request_bytes=98304)
JEV_RESERVE_USD = 0.01
JEV_TOTAL_CEILING_USD = 0.12
MAX_INITIAL_BATCHES = 6
MAX_RECHECK_BATCHES = 6
MAX_HOST_CALLS = 6
HOST_MAX_TOKENS = 800
HOST_TIMEOUT = 45
HOST_MAX_REQUEST_BYTES = 49152
AUTH_REF = (
    'Owner-approved small C01-next live validation 2026-09-23; '
    'docs/internal/research/typed-decision/entry-assessment/live-validation/protocol.md'
)
SOURCE_FILES = (
    CASES,
    PROTOCOL,
    HERE / 'run.py',
    REPO / 'experiments/typed_decision/assessment.py',
    REPO / 'experiments/typed_decision/contracts.py',
    REPO / 'experiments/typed_decision/providers.py',
    REPO / 'experiments/typed_decision/session.py',
)


def _load_cases() -> dict:
    raw = json.loads(CASES.read_text(encoding='utf8'))
    require(
        isinstance(raw, dict)
        and raw.get('schema') == 'mindthus.entry-live-validation-cases.v1'
        and raw.get('evidence_kind') == 'authored_development_controls_not_holdout'
        and isinstance(raw.get('cases'), list)
        and len(raw['cases']) == 6,
        'invalid live validation case set',
    )
    ids = [row.get('id') for row in raw['cases']]
    require(len(set(ids)) == 6 and all(isinstance(x, str) and x for x in ids), 'duplicate case ids')
    for row in raw['cases']:
        require(
            set(row) == {'id', 'family', 'expected_hit', 'correction_criteria', 'input'},
            'case shape changed',
        )
        require(
            row['expected_hit'] is None or row['expected_hit'] in assessment.CHECKS,
            'invalid expected hit',
        )
        require(
            isinstance(row['correction_criteria'], list)
            and all(isinstance(x, str) and x.strip() for x in row['correction_criteria']),
            'invalid correction criteria',
        )
        assessment.validate_envelope(row['input'])
    return raw


class _ProbeSession:
    """Capture the exact DecisionSpecs/projected State without provider inference."""

    evidence_kind = 'identity_probe'

    def __init__(self):
        self.specs = None
        self.context = None

    def evaluate(self, specs, context):
        require(self.specs is None, 'probe expected exactly one batch')
        self.specs = list(specs)
        self.context = assessment.clone(context)
        return {
            spec.id: DecisionResult('ok', assessment.CHECKS[spec.id]['fit'])
            for spec in specs
        }

    def finish(self, graph, context, result):
        return {
            'identity': {'graph': graph},
            'run_id': 'identity-probe',
            'source_ref': 'identity-probe',
            'result': result,
        }


def _batch_identity(data: dict, *, stage: str | None = None) -> dict:
    probe = _ProbeSession()
    assessment.assess(probe, assessment.clone(data), REPO, stage=stage)
    require(probe.specs is not None and probe.context is not None, 'case did not activate a batch')
    view = project_context(probe.specs, probe.context)
    questions = [spec.to_dict() for spec in probe.specs]
    request_key = digest({'questions': questions, 'context_sha256': digest(view)})
    request_bytes = len(canonical({'state': view, 'questions': questions}))
    return {
        'request_key': request_key,
        'request_bytes': request_bytes,
        'context_sha256': digest(view),
        'questions_sha256': digest(questions),
        'question_ids': [spec.id for spec in probe.specs],
    }


def _git(*args: str) -> str:
    proc = subprocess.run(
        ['git', *args],
        cwd=REPO,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def _files() -> dict:
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_FILES
    }


def prepare() -> dict:
    cases = _load_cases()
    provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True)
    identities = {}
    for row in cases['cases']:
        identity = _batch_identity(row['input'])
        require(identity['question_ids'] == list(assessment.CHECKS), 'initial checks/order changed')
        require(identity['request_bytes'] <= CHECK_LIMITS.max_request_bytes, 'initial request too large')
        identities[row['id']] = identity
    return {
        'schema': 'mindthus.entry-live-validation-freeze.v1',
        'source_commit': _git('rev-parse', 'HEAD'),
        'implementation': implementation_digest(),
        'source_files': _files(),
        'cases_sha256': hashlib.sha256(CASES.read_bytes()).hexdigest(),
        'protocol_sha256': hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        'case_ids': [row['id'] for row in cases['cases']],
        'case_families': {row['id']: row['family'] for row in cases['cases']},
        'expected_hits': {row['id']: row['expected_hit'] for row in cases['cases']},
        'correction_criteria_sha256': {
            row['id']: digest(row['correction_criteria']) for row in cases['cases']
        },
        'detector': {
            'provider_configuration': provider_configuration(provider),
            'limits': asdict(CHECK_LIMITS),
            'initial_batches': identities,
            'max_initial_batches': MAX_INITIAL_BATCHES,
            'max_recheck_batches': MAX_RECHECK_BATCHES,
            'reserve_per_request_usd': JEV_RESERVE_USD,
            'total_ceiling_usd': JEV_TOTAL_CEILING_USD,
        },
        'corrector': {
            'endpoint': HOST_ENDPOINT,
            'model': HOST_MODEL,
            'temperature': 0,
            'max_tokens': HOST_MAX_TOKENS,
            'timeout_seconds': HOST_TIMEOUT,
            'max_request_bytes': HOST_MAX_REQUEST_BYTES,
            'max_calls': MAX_HOST_CALLS,
            'automatic_retries': 0,
        },
        'policy': {
            'corrections_per_case': 1,
            'rechecks_per_case': 1,
            'semantic_revisions': 0,
            'model_substitutions': 0,
            'technical_retries': 0,
            'claim_ceiling': 'authored Chinese development controls only; not holdout or production qualification',
        },
        'authorization_ref': AUTH_REF,
    }


def _load_freeze() -> dict:
    frozen = json.loads(FREEZE.read_text(encoding='utf8'))
    require(isinstance(frozen, dict) and frozen.get('schema') == 'mindthus.entry-live-validation-freeze.v1',
            'freeze missing/invalid')
    return frozen


def _verify_frozen(frozen: dict) -> dict:
    current_files = _files()
    require(current_files == frozen['source_files'], 'frozen source files changed')
    require(implementation_digest() == frozen['implementation'], 'typed decision implementation changed')
    cases = _load_cases()
    require(hashlib.sha256(CASES.read_bytes()).hexdigest() == frozen['cases_sha256'],
            'case bytes changed')
    require(hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == frozen['protocol_sha256'],
            'protocol bytes changed')
    require([row['id'] for row in cases['cases']] == frozen['case_ids'], 'case order changed')
    provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True)
    require(provider_configuration(provider) == frozen['detector']['provider_configuration'],
            'detector provider configuration changed')
    for row in cases['cases']:
        require(_batch_identity(row['input']) == frozen['detector']['initial_batches'][row['id']],
                'initial request identity changed:' + row['id'])
    require(frozen['policy']['semantic_revisions'] == 0
            and frozen['policy']['technical_retries'] == 0
            and frozen['policy']['corrections_per_case'] == 1
            and frozen['policy']['rechecks_per_case'] == 1,
            'bounded policy changed')
    return cases


def _admission(frozen: dict, provider, case_id: str, phase: str, request_key: str) -> tuple[str, dict]:
    require(phase in ('initial', 'recheck'), 'invalid detector phase')
    scope = 'entry-live-v1-' + case_id + '-' + phase
    payload = {
        'scope': scope,
        'implementation': frozen['implementation'],
        'provider_configuration': provider_configuration(provider),
        'limits': frozen['detector']['limits'],
        'request_allowlist': [request_key],
        'max_cost_usd': JEV_RESERVE_USD,
        'reserve_per_call_usd': JEV_RESERVE_USD,
        'authorization_ref': frozen['authorization_ref'],
        'freeze_sha256': digest(frozen),
    }
    return scope, payload


def _host_body(request: dict) -> dict:
    task = {
        'original_task': request['original_task'],
        'decision_context': request['decision_context'],
        'current_target': request['current_target'],
        'instructions': request['instructions'],
        'boundary': request['boundary'],
        'parent_assessment_ref': request['parent_assessment_ref'],
    }
    return {
        'model': HOST_MODEL,
        'temperature': 0,
        'max_tokens': HOST_MAX_TOKENS,
        'stream': False,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'Perform exactly one bounded correction of the candidate. '
                    'Return only the revised candidate text in Chinese, with no JSON, headings, '
                    'meta commentary, tool calls, or claims beyond supplied evidence. Preserve '
                    'the user object, goal, scope, facts and permissions. Apply the named '
                    'correction instructions and leave unresolved evidence explicit.'
                ),
            },
            {'role': 'user', 'content': canonical(task).decode('utf8')},
        ],
    }


def _host_correct(case_root: Path, request: dict, key: str) -> dict:
    root = case_root / 'correction'
    ip, op = root / 'intent.json', root / 'outcome.json'
    body = _host_body(request)
    request_bytes = len(canonical(body))
    require(request_bytes <= HOST_MAX_REQUEST_BYTES, 'host request exceeds frozen byte ceiling')
    intent = {
        'request_id': request['request_id'],
        'request_sha256': digest(body),
        'request_bytes': request_bytes,
        'endpoint': HOST_ENDPOINT,
        'model': HOST_MODEL,
        'temperature': 0,
        'max_tokens': HOST_MAX_TOKENS,
        'automatic_retries': 0,
        'user_agent': HOST_UA,
    }
    if op.exists():
        require(ip.exists() and read_record(ip) == intent, 'host intent changed')
        return read_record(op)
    if ip.exists():
        raise RecoveryRequired('unresolved host correction:' + case_root.name)
    require(bool(key), 'missing host credential')
    write_once(ip, intent)
    row = {
        'status': 'failed',
        'reply': None,
        'model': HOST_MODEL,
        'reported_model': None,
        'usage': {'input_tokens': None, 'output_tokens': None, 'cost_usd': None},
        'error': None,
        'elapsed_seconds': None,
    }
    begin = time.monotonic()
    try:
        raw = post_json(
            HOST_ENDPOINT,
            {
                'Authorization': 'Bearer ' + key,
                'Content-Type': 'application/json',
                'User-Agent': HOST_UA,
            },
            body,
            HOST_TIMEOUT,
        )
        require(raw.get('model') == HOST_MODEL, 'host model mismatch')
        row['reported_model'] = raw.get('model')
        usage = raw.get('usage') or {}
        row['usage'] = {
            'input_tokens': usage.get('prompt_tokens'),
            'output_tokens': usage.get('completion_tokens'),
            'cost_usd': usage.get('cost'),
        }
        for name, value in row['usage'].items():
            require(value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0),
                    'invalid host usage:' + name)
        if row['usage']['input_tokens'] is not None:
            require(type(row['usage']['input_tokens']) is int, 'host prompt tokens not integer')
        if row['usage']['output_tokens'] is not None:
            require(type(row['usage']['output_tokens']) is int
                    and row['usage']['output_tokens'] <= HOST_MAX_TOKENS,
                    'host output tokens exceed ceiling')
        choices = raw.get('choices')
        require(isinstance(choices, list) and len(choices) == 1, 'host response shape')
        choice = choices[0]
        require(choice.get('finish_reason') == 'stop', 'host incomplete response')
        message = choice.get('message') or {}
        require(not message.get('tool_calls'), 'host requested tools')
        answer = message.get('content')
        require(isinstance(answer, str) and bool(answer.strip()), 'host empty answer')
        require(key not in answer, 'host credential reflection')
        row['reply'] = {
            'text': answer.strip(),
            'version': '2',
            'receipt_ref': 'live-validation:' + case_root.name + ':correction-1',
        }
        row['status'] = 'complete'
    except Exception as exc:
        row['error'] = safe_failure_reason(exc)
    row['elapsed_seconds'] = time.monotonic() - begin
    write_once(op, row)
    return row


def _detector_call(
    frozen: dict,
    provider,
    case_root: Path,
    case_id: str,
    phase: str,
    data: dict,
    expected_identity: dict,
    *,
    stage: str | None = None,
) -> dict:
    actual_identity = _batch_identity(data, stage=stage)
    require(actual_identity == expected_identity, 'detector request identity differs:' + case_id + ':' + phase)
    scope, live = _admission(frozen, provider, case_id, phase, expected_identity['request_key'])
    admission_path = case_root / (phase + '-admission.json')
    admission_record = {
        'phase': phase,
        'case_id': case_id,
        'request_identity': expected_identity,
        'live_admission': live,
    }
    if admission_path.exists():
        require(read_record(admission_path) == admission_record, 'detector admission changed')
    else:
        write_once(admission_path, admission_record)
    with Session(case_root / phase, provider, scope=scope, limits=CHECK_LIMITS,
                 live_admission=live) as session:
        return assessment.assess(session, data, REPO, stage=stage)


def _case_summary(row: dict, initial: dict, correction: dict | None, recheck: dict | None) -> dict:
    hits = initial['result']['hits']
    expected = row['expected_hit']
    defect_ids = set(assessment.CHECKS)
    false_positive = expected is None and bool(defect_ids.intersection(hits))
    expected_detected = None if expected is None else expected in hits
    cross_hits = [hit for hit in hits if expected is not None and hit != expected]
    return {
        'case_id': row['id'],
        'family': row['family'],
        'expected_hit': expected,
        'initial_action': initial['result']['action'],
        'initial_hits': hits,
        'initial_unresolved': initial['result']['unresolved'],
        'expected_detected': expected_detected,
        'false_positive': false_positive,
        'cross_hits': cross_hits,
        'correction_status': correction['status'] if correction else 'not_triggered',
        'correction_reply': correction['reply']['text'] if correction and correction.get('reply') else None,
        'correction_usage': correction['usage'] if correction else None,
        'correction_elapsed_seconds': correction['elapsed_seconds'] if correction else None,
        'recheck_action': recheck['result']['action'] if recheck else None,
        'recheck_hits': recheck['result']['hits'] if recheck else None,
        'recheck_unresolved': recheck['result']['unresolved'] if recheck else None,
        'correction_criteria': row['correction_criteria'],
        'correction_quality': 'author_review_pending' if correction and correction.get('reply') else 'not_applicable',
        'claim_ceiling': 'development observation only',
    }


def _collect_jev_usage(case_root: Path) -> dict:
    rows = []
    for phase in ('initial', 'recheck'):
        for path in sorted((case_root / phase / 'calls').glob('*/outcome.json')):
            record = read_record(path)
            rows.append({
                'phase': phase,
                'input_tokens': record['usage']['input_tokens'],
                'output_tokens': record['usage']['output_tokens'],
                'cost_usd': record['usage']['cost_usd'],
                'elapsed_seconds': record['elapsed_seconds'],
            })
    return {'calls': rows}


def run_campaign(root: Path, typesafe_key: str, host_key: str) -> dict:
    frozen = _load_freeze()
    cases = _verify_frozen(frozen)
    require(bool(typesafe_key) and bool(host_key), 'both credentials required')
    require(not (root / 'summary.json').exists(), 'campaign already complete')
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        'freeze_sha256': digest(frozen),
        'source_commit': frozen['source_commit'],
        'case_ids': frozen['case_ids'],
        'authorization_ref': frozen['authorization_ref'],
    }
    mp = root / 'manifest.json'
    if mp.exists():
        require(read_record(mp) == manifest, 'campaign manifest changed')
    else:
        write_once(mp, manifest)

    previous_ts = os.environ.get('TYPESAFE_API_KEY')
    os.environ['TYPESAFE_API_KEY'] = typesafe_key
    provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True)
    results = []
    try:
        for row in cases['cases']:
            case_id = row['id']
            case_root = root / case_id
            case_root.mkdir(parents=True, exist_ok=True)
            initial = _detector_call(
                frozen,
                provider,
                case_root,
                case_id,
                'initial',
                assessment.clone(row['input']),
                frozen['detector']['initial_batches'][case_id],
            )
            correction = None
            recheck = None
            if initial['result']['action'] == 'request_correction':
                request = assessment.correction_request(initial, row['input'], REPO)
                rp = case_root / 'correction-request.json'
                if rp.exists():
                    require(read_record(rp) == request, 'correction request changed')
                else:
                    write_once(rp, request)
                correction = _host_correct(case_root, request, host_key)
                if correction['status'] == 'complete':
                    reply = correction['reply']
                    revised = {**initial['result']['target'], 'version': reply['version'],
                               'text': reply['text'], 'source_ref': reply['receipt_ref']}
                    if revised['kind'] == 'user_frame':
                        revised['kind'] = 'candidate_frame'
                    next_state = assessment.clone(row['input'])
                    next_state.update(
                        state_version=digest([
                            row['input']['state_version'], request['request_id'], revised
                        ]),
                        target=revised,
                    )
                    revision = {
                        'parent_state_sha256': digest(row['input']),
                        'parent_assessment_ref': initial['source_ref'],
                        'correction_request_id': request['request_id'],
                        'input': next_state,
                    }
                    rvp = case_root / 'revision.json'
                    if rvp.exists():
                        require(read_record(rvp) == revision, 'revision changed')
                    else:
                        write_once(rvp, revision)
                    recheck_identity = _batch_identity(next_state, stage='S2')
                    require(recheck_identity['question_ids'] == list(assessment.CHECKS),
                            'recheck question set changed')
                    recheck_freeze = {
                        'case_id': case_id,
                        'parent_freeze_sha256': digest(frozen),
                        'revision_sha256': digest(revision),
                        'request_identity': recheck_identity,
                        'semantic_revision': 0,
                        'retry': 0,
                    }
                    rfp = case_root / 'recheck-freeze.json'
                    if rfp.exists():
                        require(read_record(rfp) == recheck_freeze, 'recheck freeze changed')
                    else:
                        write_once(rfp, recheck_freeze)
                    recheck = _detector_call(
                        frozen,
                        provider,
                        case_root,
                        case_id,
                        'recheck',
                        next_state,
                        recheck_identity,
                        stage='S2',
                    )
            summary = _case_summary(row, initial, correction, recheck)
            summary['jev_usage'] = _collect_jev_usage(case_root)
            sp = case_root / 'summary.json'
            if sp.exists():
                require(read_record(sp) == summary, 'case summary changed')
            else:
                write_once(sp, summary)
            results.append(summary)
    finally:
        if previous_ts is None:
            os.environ.pop('TYPESAFE_API_KEY', None)
        else:
            os.environ['TYPESAFE_API_KEY'] = previous_ts

    require(len(results) == 6, 'campaign incomplete')
    positive = [r for r in results if r['expected_hit'] is not None]
    negative = [r for r in results if r['expected_hit'] is None]
    jev_calls = [call for r in results for call in r['jev_usage']['calls']]
    host_calls = [r for r in results if r['correction_status'] != 'not_triggered']
    summary = {
        'schema': 'mindthus.entry-live-validation-summary.v1',
        'freeze_sha256': digest(frozen),
        'source_commit': frozen['source_commit'],
        'cases_completed': len(results),
        'positive_detection': {
            'correct': sum(r['expected_detected'] is True for r in positive),
            'total': len(positive),
        },
        'negative_false_positive': {
            'cases': sum(r['false_positive'] is True for r in negative),
            'total': len(negative),
        },
        'cross_hits': {r['case_id']: r['cross_hits'] for r in positive if r['cross_hits']},
        'corrections_triggered': len(host_calls),
        'corrections_completed': sum(r['correction_status'] == 'complete' for r in host_calls),
        'rechecks_completed': sum(r['recheck_action'] is not None for r in results),
        'jev_usage': {
            'calls': len(jev_calls),
            'input_tokens': sum(x['input_tokens'] for x in jev_calls)
                if jev_calls and all(x['input_tokens'] is not None for x in jev_calls) else None,
            'output_tokens': sum(x['output_tokens'] for x in jev_calls)
                if jev_calls and all(x['output_tokens'] is not None for x in jev_calls) else None,
            'cost_usd': sum(x['cost_usd'] for x in jev_calls)
                if jev_calls and all(x['cost_usd'] is not None for x in jev_calls) else None,
            'elapsed_seconds': sum(x['elapsed_seconds'] for x in jev_calls),
        },
        'host_usage': {
            'calls': len(host_calls),
            'input_tokens': sum(r['correction_usage']['input_tokens'] for r in host_calls)
                if host_calls and all(r['correction_usage']['input_tokens'] is not None for r in host_calls) else None,
            'output_tokens': sum(r['correction_usage']['output_tokens'] for r in host_calls)
                if host_calls and all(r['correction_usage']['output_tokens'] is not None for r in host_calls) else None,
            'cost_usd': sum(r['correction_usage']['cost_usd'] for r in host_calls)
                if host_calls and all(r['correction_usage']['cost_usd'] is not None for r in host_calls) else None,
            'elapsed_seconds': sum(r['correction_elapsed_seconds'] for r in host_calls),
        },
        'case_results': results,
        'correction_quality': 'author_review_pending',
        'qualification': False,
        'holdout': False,
        'formal_abc': False,
        'claim_ceiling': frozen['policy']['claim_ceiling'],
    }
    write_once(root / 'summary.json', summary)
    return summary


def _safe_summary(summary: dict) -> dict:
    return {key: value for key, value in summary.items() if key != 'case_results'}


def preflight() -> dict:
    frozen = _load_freeze()
    cases = _verify_frozen(frozen)
    require(len(cases['cases']) == 6, 'preflight case count')
    require(len(frozen['detector']['initial_batches']) == 6, 'preflight batch count')
    require(
        MAX_INITIAL_BATCHES + MAX_RECHECK_BATCHES <=
        int(JEV_TOTAL_CEILING_USD / JEV_RESERVE_USD + 1e-9),
        'global Jev reserve mismatch',
    )
    return {
        'status': 'PASS',
        'inference_performed': False,
        'cases': 6,
        'initial_request_keys': len(frozen['detector']['initial_batches']),
        'implementation': frozen['implementation'],
        'provider_configuration': frozen['detector']['provider_configuration'],
        'credentials_present': {
            'typesafe': bool(os.environ.get('TYPESAFE_API_KEY')),
            'host': bool(os.environ.get('MINDTHUS_HOST_API_KEY')),
        },
        'claim_ceiling': frozen['policy']['claim_ceiling'],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'preflight', 'run', 'report'])
    parser.add_argument('--state-root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--prompt-keys', action='store_true')
    args = parser.parse_args(argv)
    injected = []
    try:
        if args.action == 'prepare':
            payload = prepare()
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_bytes(canonical(payload) + b'\n')
                print(json.dumps({'output': str(args.output), 'sha256': digest(payload),
                                  'inference_performed': False}))
            else:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if args.action == 'preflight':
            print(json.dumps(preflight(), ensure_ascii=False, indent=2))
            return 0
        require(args.state_root is not None, 'state root required')
        root = args.state_root.resolve()
        require(root != REPO and REPO not in root.parents, 'state root must stay outside repository')
        if args.action == 'report':
            print(json.dumps(_safe_summary(read_record(root / 'summary.json')),
                             ensure_ascii=False, indent=2))
            return 0
        require(args.action == 'run', 'unsupported action')
        if args.prompt_keys:
            import getpass
            require(sys.stdin.isatty(), 'hidden credential prompt requires a TTY')
            require(not os.environ.get('TYPESAFE_API_KEY')
                    and not os.environ.get('MINDTHUS_HOST_API_KEY'),
                    'credential already present')
            os.environ['TYPESAFE_API_KEY'] = getpass.getpass('TypeSafe official API key (hidden): ')
            injected.append('TYPESAFE_API_KEY')
            os.environ['MINDTHUS_HOST_API_KEY'] = getpass.getpass('CPA host API key (hidden): ')
            injected.append('MINDTHUS_HOST_API_KEY')
        typesafe_key = os.environ.get('TYPESAFE_API_KEY', '')
        host_key = os.environ.get('MINDTHUS_HOST_API_KEY', '')
        if not typesafe_key or not host_key:
            print(json.dumps({
                'status': 'blocked',
                'reason': 'missing_local_credentials',
                'next': 'run locally with --prompt-keys; do not paste credentials into chat',
            }))
            return 2
        summary = run_campaign(root, typesafe_key, host_key)
        print(json.dumps(_safe_summary(summary), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, RecoveryRequired, subprocess.CalledProcessError) as exc:
        print(json.dumps({'status': 'blocked', 'error_type': type(exc).__name__}))
        return 2
    finally:
        for name in injected:
            os.environ.pop(name, None)


if __name__ == '__main__':
    raise SystemExit(main())
