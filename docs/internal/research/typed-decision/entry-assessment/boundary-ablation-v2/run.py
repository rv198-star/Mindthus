"""One frozen eight-case physical question-ablation campaign; no hidden retries."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import fcntl
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
from experiments.typed_decision.contracts import (DecisionResult, canonical, digest,
    project_context, provider_configuration, require)
from experiments.typed_decision.providers import TypeSafeJevProvider, post_json
from experiments.typed_decision.session import (Limits, RecoveryRequired, Session,
    implementation_digest, read_record, write_once)

KEYS = tuple(assessment.CHECKS)
ARMS = {'full': KEYS, 'drop_p1': KEYS[1:], 'drop_p2': (KEYS[0], KEYS[2]), 'drop_p3': KEYS[:2]}
ROOT = Path('/srv/agentdock/tmp/mindthus-entry-boundary-ablation-v2')
FREEZE = HERE / 'freeze.json'
LIMITS = Limits(max_calls=1, max_seconds=45, max_request_bytes=98304)
HOST = 'deepseek-v4.1-flash'
ENDPOINT = 'https://cpa.72live.com/v1/chat/completions'
BUDGET = {'jev_calls': 32, 'host_calls': 32, 'jev_reserve_per_call_usd': .01,
          'jev_total_reserve_usd': .32, 'jev_input_tokens_per_call': 16000,
          'inference_seconds': 180, 'host_output_tokens': 800,
          'host_request_bytes': 49152, 'timeout_seconds': 45}
AUTH = 'Owner-approved existing P1/P2 boundary and marginal-value successor; #211'


def load_cases():
    data = json.loads((HERE / 'cases.json').read_text())
    require(data['schema'] == 'mindthus.entry-boundary-cases.v2', 'case_schema')
    cases = data['cases']
    require([r['id'] for r in cases] == ['E%02d' % i for i in range(1, 9)], 'case_ids')
    for row in cases:
        require(set(row['expected_hits']) <= set(KEYS), 'expected_checks')
        require(len(row['quality_criteria']) == 3, 'quality_rubric')
    return cases


def envelope(row, arm):
    """Project only task material. Labels, purpose and quality criteria stay local."""
    ref = 'boundary-v2:' + row['id']
    data = {'state_version': '1', 'task': {
        'request': row['request'], 'constraints': row['constraints'],
        'evidence': [{'source_ref': ref + ':material', 'summary': row['evidence']}],
        'provenance': {'source_ref': ref + ':task', 'revision': '1'},
        'known_obligations': row.get('known_obligations', []), 'explicit_method': None,
        'risk': 'low', 'freshness': 'current',
        'permission': {'mode': 'advisory', 'source_ref': ref + ':owner'}},
        'decision_context': {k: row[k] for k in ('object', 'goal', 'scope')},
        'target': {'id': 'candidate', 'kind': 'candidate_answer', 'version': '1',
                   'source_ref': ref + ':candidate', 'text': row['candidate']},
        'activation': {'event': 'before-answer', 'source_ref': 'owner:bounded-v2-comparison',
                       'reason': 'Inspect the existing candidate under the same declared task.',
                       'frame_risk': True, 'execution_impact': True, 'required': False,
                       'checks': list(ARMS[arm])}}
    data['decision_context']['source_ref'] = ref + ':context'
    assessment.validate_envelope(data)
    return data


class Capture:
    evidence_kind = 'offline_identity_probe'
    def __init__(self, answers=None):
        self.answers, self.specs, self.view = answers, None, None
    def evaluate(self, specs, view):
        self.specs, self.view = specs, project_context(specs, view)
        if self.answers is None:
            return {s.id: DecisionResult('ok', assessment.CHECKS[s.id]['fit']) for s in specs}
        return {s.id: DecisionResult.from_dict(self.answers[s.id], s) for s in specs}
    def finish(self, graph, data, result):
        return {'identity': {'graph': graph, 'input_sha256': digest(data)}, 'result': result}


def identity(data):
    probe = Capture()
    assessment.assess(probe, data, REPO)
    require(probe.specs is not None, 'no_active_batch')
    qs = [s.to_dict() for s in probe.specs]
    view_hash = digest(probe.view)
    return {'request_key': digest({'questions': qs, 'context_sha256': view_hash}),
            'context_sha256': view_hash, 'questions': qs,
            'request_bytes': len(canonical({'state': probe.view, 'questions': qs}))}


def schedule():
    names = list(ARMS)
    return [(row, arm) for i, row in enumerate(load_cases())
            for arm in names[i % 4:] + names[:i % 4]]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()


def prepare(source_commit=None):
    bindings = {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (HERE / 'protocol.md', HERE / 'cases.json', HERE / 'run.py',
                          HERE / 'offline_check.py')}
    _, sources = assessment.source_contracts(REPO)
    requests = {row['id'] + '/' + arm: identity(envelope(row, arm)) for row, arm in schedule()}
    for row in load_cases():
        require(len({requests[row['id'] + '/' + arm]['context_sha256'] for arm in ARMS}) == 1,
                'state_differs_across_arms')
    require(all(r['request_bytes'] <= LIMITS.max_request_bytes for r in requests.values()),
            'request_size')
    return {'schema': 'mindthus.entry-ablation-freeze.v2',
            'source_commit': source_commit or git('rev-parse', 'HEAD'),
            'implementation': implementation_digest(), 'files': bindings, 'sources': sources,
            'root': str(ROOT), 'provider': provider_configuration(TypeSafeJevProvider(choice_rounding=True)),
            'requests': requests, 'order': list(requests), 'limits': asdict(LIMITS),
            'budget': json.loads(canonical(BUDGET)),
            'host': {'endpoint': ENDPOINT, 'model': HOST, 'temperature': 0},
            'authorization_ref': AUTH, 'retries': 0, 'semantic_revisions': 0, 'rechecks': 0}


def verify(frozen):
    require(prepare(frozen['source_commit']) == frozen, 'source_or_freeze_drift')
    require(git('merge-base', '--is-ancestor', frozen['source_commit'], 'HEAD') == '', 'ancestry')


def save(path, payload):
    if path.exists():
        require(read_record(path) == payload, 'immutable_record_changed')
    else:
        write_once(path, payload)


def guard(root):
    intents = list(root.rglob('intent.json'))
    for p in intents:
        if not p.with_name('outcome.json').exists():
            raise RecoveryRequired('unresolved_external_intent')
    jev = [p for p in intents if 'calls' in p.parts]
    host = [p for p in intents if p.parent.name == 'correction']
    require(len(jev) <= BUDGET['jev_calls'] and len(host) <= BUDGET['host_calls'], 'call_budget')
    elapsed = sum(read_record(p.with_name('outcome.json'))['elapsed_seconds'] for p in intents)
    require(elapsed < BUDGET['inference_seconds'], 'inference_time_budget')
    return BUDGET['inference_seconds'] - elapsed


def detector(root, row, arm, frozen, provider):
    folder = root / row['id'] / arm
    result_path = folder / 'detector.json'
    if result_path.exists():
        return read_record(result_path)
    guard(root)
    data = envelope(row, arm)
    key = row['id'] + '/' + arm
    ident = identity(data)
    require(ident == frozen['requests'][key], 'request_identity')
    scope = 'entry-ablation-v2-' + row['id'] + '-' + arm
    admission = {'scope': scope, 'implementation': frozen['implementation'],
        'provider_configuration': frozen['provider'], 'limits': asdict(LIMITS),
        'request_allowlist': [ident['request_key']], 'max_cost_usd': .01,
        'reserve_per_call_usd': .01, 'authorization_ref': AUTH, 'freeze_sha256': digest(frozen)}
    save(folder / 'admission.json', admission)
    with Session(folder / 'detector', provider, scope=scope, limits=LIMITS,
                 live_admission=admission) as session:
        report = assessment.assess(session, data, REPO)
    # Invocation counters differ on recovery; only persist the immutable report fields.
    stable = {k: report[k] for k in ('identity', 'run_id', 'source_ref', 'result', 'call_keys')}
    save(result_path, stable)
    return stable


def check_detector(folder, report):
    for cell in report['result']['matrix']:
        require(cell['status'] in ('ok', 'not_evaluated', 'abstain', 'missing_context'),
                'detector_technical_failure')
    for p in (folder / 'detector' / 'calls').glob('*/outcome.json'):
        usage = read_record(p)['usage']
        require(usage['input_tokens'] is None or usage['input_tokens'] <= BUDGET['jev_input_tokens_per_call'],
                'reported_input_budget')
        require(usage['cost_usd'] is None or usage['cost_usd'] <= .01, 'reported_cost_budget')


def host_body(request):
    task = {k: request[k] for k in ('original_task', 'decision_context', 'current_target',
                                   'instructions', 'boundary')}
    return {'model': HOST, 'temperature': 0, 'max_tokens': BUDGET['host_output_tokens'],
        'stream': False, 'messages': [
            {'role': 'system', 'content': 'Revise this existing candidate once using the named instructions. '
             'Return only the revised Chinese candidate, not diagnostic codes or an audit verdict. '
             'Preserve original evidence, object, goal and scope. Do not invent facts or perform tools.'},
            {'role': 'user', 'content': canonical(task).decode()}]}


def correction(root, row, arm, report, host_key):
    folder = root / row['id'] / arm / 'correction'
    ip, op = folder / 'intent.json', folder / 'outcome.json'
    request = assessment.correction_request(report, envelope(row, arm), REPO)
    body = host_body(request)
    require(len(canonical(body)) <= BUDGET['host_request_bytes'], 'host_request_budget')
    intent = {'request_sha256': digest(body), 'request': body, 'endpoint': ENDPOINT,
              'model': HOST, 'parent_run_id': report['run_id'], 'max_attempts': 1}
    if op.exists():
        require(ip.exists() and read_record(ip) == intent, 'host_request_changed')
        return read_record(op)
    if ip.exists():
        raise RecoveryRequired('unknown_host_attempt')
    remaining = guard(root)
    require(len(list(root.glob('E*/*/correction/intent.json'))) < BUDGET['host_calls'], 'host_call_budget')
    save(ip, intent)
    begin = time.monotonic()
    result = {'status': 'failed', 'model': HOST, 'text': None, 'usage': {},
              'evidence_kind': 'live_model', 'error': None}
    try:
        raw = post_json(ENDPOINT, {'Authorization': 'Bearer ' + host_key,
            'Content-Type': 'application/json', 'User-Agent': 'Mindthus-C01-integration/1'},
            body, min(BUDGET['timeout_seconds'], remaining))
        require(all(not os.environ.get(k) or os.environ[k] not in json.dumps(raw)
                    for k in ('TYPESAFE_API_KEY', 'MINDTHUS_HOST_API_KEY')), 'credential_reflection')
        require(raw.get('model') == HOST, 'host_model_mismatch')
        usage = raw.get('usage') or {}
        for k in ('prompt_tokens', 'completion_tokens'):
            v = usage.get(k)
            require(v is None or (type(v) is int and v >= 0), 'host_usage_shape')
        require(usage.get('completion_tokens') is None or usage['completion_tokens'] <= 800,
                'host_output_budget')
        cost = usage.get('cost')
        require(cost is None or (type(cost) in (float, int) and math.isfinite(cost) and cost >= 0),
                'host_cost_shape')
        result['usage'] = {k: usage.get(k) for k in ('prompt_tokens', 'completion_tokens')}
        result['provider_cost_currency_unknown'] = cost
        choices = raw.get('choices')
        require(isinstance(choices, list) and len(choices) == 1, 'host_response_shape')
        choice = choices[0]
        require(choice.get('finish_reason') == 'stop', 'host_incomplete')
        msg = choice.get('message') or {}
        require(not msg.get('tool_calls'), 'host_tool_request')
        text = msg.get('content')
        require(isinstance(text, str) and bool(text.strip()) and len(text.encode()) <= 16384,
                'host_text_shape')
        result.update(status='complete', text=text.strip())
    except Exception as exc:
        result['error'] = type(exc).__name__
    result['elapsed_seconds'] = time.monotonic() - begin
    save(op, result)
    return result


def summarize(root, frozen, stop):
    rows = []
    for row in load_cases():
        for arm in ARMS:
            folder = root / row['id'] / arm
            dp, cp = folder / 'detector.json', folder / 'correction' / 'outcome.json'
            if not dp.exists():
                rows.append({'case_id': row['id'], 'arm': arm, 'status': 'unrun'})
                continue
            report = read_record(dp)
            result = report['result']
            cells = [c for c in result['matrix'] if c['check_id'] in ARMS[arm]]
            comparisons = {c['check_id']: {'expected_hit': c['check_id'] in row['expected_hits'],
                'observed_hit': c['value'] == assessment.CHECKS[c['check_id']]['hit'],
                'unknown': c['status'] != 'ok' or c['value'] == 'insufficient_context',
                'value': c['value'], 'status': c['status']} for c in cells}
            host = read_record(cp) if cp.exists() else None
            rows.append({'case_id': row['id'], 'arm': arm, 'status': 'observed',
                'action': result['action'], 'hits': result['hits'], 'unresolved': result['unresolved'],
                'obligations': result['obligations'], 'cells': comparisons,
                'correction': host, 'final_candidate': host['text'] if host and host['status'] == 'complete'
                    else row['candidate'], 'quality_review': 'not_reviewed'})
    projections = []
    for row in load_cases():
        fp = root / row['id'] / 'full' / 'detector.json'
        if not fp.exists():
            continue
        full = read_record(fp)['result']
        answers = {c['check_id']: {k: c[k] for k in ('status', 'value', 'uncertainty', 'reason')}
                   for c in full['matrix']}
        for arm in ARMS:
            probe = Capture(answers)
            projected = assessment.assess(probe, envelope(row, arm), REPO)['result']
            projections.append({'case_id': row['id'], 'arm': arm, 'action': projected['action'],
                                'hits': projected['hits'], 'kind': 'policy_projection_not_new_inference'})
    outcomes = [(p, read_record(p)) for p in root.rglob('outcome.json')]
    return {'schema': 'mindthus.entry-ablation-observation.v2', 'freeze_sha256': digest(frozen),
        'source_commit': frozen['source_commit'], 'stop_reason': stop, 'rows': rows,
        'no_check_reference': [{'case_id': r['id'], 'text': r['candidate'], 'new_calls': 0,
            'known_obligations': r.get('known_obligations', []), 'kind': 'existing_candidate_not_original_A'}
            for r in load_cases()], 'policy_projections': projections,
        'counts': {'detector': sum('calls' in p.parts for p, _ in outcomes),
                   'corrector': sum(p.parent.name == 'correction' for p, _ in outcomes)},
        'recorded_inference_seconds': sum(o['elapsed_seconds'] for _, o in outcomes),
        'quality_review': 'author_review_pending', 'qualification': False, 'holdout': False}


def run(root, provider=None, host_key=None):
    frozen = json.loads(FREEZE.read_text())
    verify(frozen)
    require(Path(root).resolve() == Path(frozen['root']).resolve(), 'campaign_root_changed')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.campaign-lock').open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RecoveryRequired('another_campaign_process') from None
        save(root / 'manifest.json', frozen)
        if (root / 'summary.json').exists():
            return read_record(root / 'summary.json')
        require(bool(os.environ.get('TYPESAFE_API_KEY')) and bool(host_key), 'credentials_missing')
        provider = provider or TypeSafeJevProvider(choice_rounding=True)
        require(provider_configuration(provider) == frozen['provider'], 'provider_changed')
        transport = provider.transport
        def checked_transport(url, headers, body, timeout):
            response = transport(url, headers, body, timeout)
            encoded = canonical(response).decode()
            require(all(not os.environ.get(k) or os.environ[k] not in encoded
                        for k in ('TYPESAFE_API_KEY', 'MINDTHUS_HOST_API_KEY')),
                    'credential_reflection')
            return response
        provider.transport = checked_transport
        stop = None
        try:
            guard(root)
            for row, arm in schedule():
                report = detector(root, row, arm, frozen, provider)
                check_detector(root / row['id'] / arm, report)
                print(json.dumps({'phase': 'detector', 'case': row['id'], 'arm': arm,
                    'action': report['result']['action'], 'hits': report['result']['hits']}), flush=True)
            for row, arm in schedule():
                report = read_record(root / row['id'] / arm / 'detector.json')
                if report['result']['action'] == 'request_correction':
                    output = correction(root, row, arm, report, host_key)
                    require(output['status'] == 'complete', 'host_technical_failure')
                    print(json.dumps({'phase': 'correction', 'case': row['id'], 'arm': arm,
                                      'status': output['status']}), flush=True)
            guard(root)
        except Exception as exc:
            # No arbitrary remote error text or credentials; preserve all completed records.
            stop = type(exc).__name__
        summary = summarize(root, frozen, stop)
        save(root / 'summary.json', summary)
        return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'preflight', 'run', 'report'])
    args = parser.parse_args()
    if args.action == 'prepare':
        require(not FREEZE.exists(), 'freeze_already_exists')
        require(not git('status', '--porcelain'), 'commit_source_before_freeze')
        FREEZE.write_bytes(canonical(prepare()) + b'\n')
        print('freeze written; no inference')
    elif args.action == 'preflight':
        verify(json.loads(FREEZE.read_text()))
        print('source/State/32 request identities PASS; no inference')
    elif args.action == 'report':
        print(json.dumps(read_record(ROOT / 'summary.json'), ensure_ascii=False))
    else:
        result = run(ROOT, host_key=os.environ.get('MINDTHUS_HOST_API_KEY'))
        print(json.dumps({k: result[k] for k in ('counts', 'stop_reason', 'qualification')}))
        return int(result['stop_reason'] is not None)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RecoveryRequired) as exc:
        print(json.dumps({'blocked': type(exc).__name__}))
        raise SystemExit(2)
