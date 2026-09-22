"""Opt-in read-only C01 -> verified handoff -> CPA answer, with frozen admission."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import time

from . import c01, handoff
from .campaign import request_key
from .contracts import DecisionResult, canonical, digest, provider_configuration, require
from .providers import TypeSafeJevProvider, post_json
from .session import Limits, RecoveryRequired, Session, implementation_digest, read_record, write_once, safe_failure_reason

LIMITS = Limits(max_calls=3, max_seconds=60, max_request_bytes=32768)
RESERVE = .002688
ENDPOINT = 'https://cpa.72live.com/v1/chat/completions'
MODELS = ('deepseek-v4.1-flash', 'glm-5.3-flash')
SYSTEM = ('Handle the task using the verified C01 handoff. Answer usefully in Chinese within '
          '450 Chinese characters unless less is needed. No external tools are available. '
          'Preserve constraints and evidence limits; do not claim unperformed actions. '
          'Do not narrate the experiment or routing machinery.')


def admission(context: dict, method_root: Path, model: str, authorization_ref: str) -> dict:
    require(model in MODELS, 'host model outside authorized channel')
    require(isinstance(authorization_ref, str) and bool(authorization_ref.strip()), 'authority reference required')
    require(isinstance(context, dict), 'context must be an object')
    provider = TypeSafeJevProvider(choice_rounding=True)
    keys = set()
    class Collector:
        def __init__(self, owner): self.owner = owner
        def evaluate(self, specs, state):
            keys.add(request_key(specs, state))
            require(len(canonical({'state': state, 'questions': [s.to_dict() for s in specs]})) <= LIMITS.max_request_bytes,
                    'routing request too large')
            values = {'entry_mode': 'mindthus_intervention', 'unresolved_obligation': 'clear',
                      'owner': self.owner, 'applicable': 'yes'}
            return {s.id: DecisionResult('ok', values[s.id]) for s in specs}
        def finish(self, *args): return None
    for owner in sorted(c01.METHODS): c01.run(Collector(owner), context, method_root)
    files = [method_root / 'skills' / owner / 'SKILL.md' for owner in sorted(c01.METHODS | {'using-mindthus'})]
    return {'schema': 'mindthus.c01-host-admission.v1', 'context': context,
            'method_root': str(method_root.resolve()), 'method_sha256': {
                str(p.relative_to(method_root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            'implementation': implementation_digest(), 'graph': c01.GRAPH,
            'routing': {'provider_configuration': provider_configuration(provider), 'limits': asdict(LIMITS),
                        'request_allowlist': sorted(keys) or [digest({'mechanical_only': context})],
                        'max_cost_usd': 3 * RESERVE, 'reserve_per_call_usd': RESERVE},
            'host': {'endpoint': ENDPOINT, 'model': model, 'max_tokens': 1600, 'max_seconds': 60,
                     'max_request_bytes': 49152, 'max_calls': 1, 'cost_usd': None},
            'authorization_ref': authorization_ref, 'mode': 'read_only_chat_integration',
            'total_call_ceiling': 4, 'automatic_retries': 0, 'qualification': False}


def host_body(bundle: dict, model: str) -> dict:
    return {'model': model, 'temperature': 0, 'max_tokens': 1600, 'stream': False,
            'messages': [{'role': 'system', 'content': SYSTEM},
                         {'role': 'user', 'content': handoff.host_prompt(bundle)}]}


def consume(bundle: dict, root: Path, model: str, key: str, *, transport=post_json) -> dict:
    """One immutable host call; completed outcomes replay, unknown intents never resend."""
    require(model in MODELS and bool(key), 'missing or unapproved host credentials/configuration')
    payload = host_body(bundle, model)
    require(len(canonical(payload)) <= 49152, 'host request ceiling')
    intent = {'request_sha256': digest(payload), 'request_bytes': len(canonical(payload)),
              'model': model, 'endpoint': ENDPOINT, 'handoff_sha256': digest(bundle)}
    if (root / 'intent.json').exists():
        require(read_record(root / 'intent.json') == intent, 'host request changed')
        if not (root / 'outcome.json').exists():
            raise RecoveryRequired('host call may have occurred; reconcile before resubmission')
        return read_record(root / 'outcome.json')
    require(not (root / 'outcome.json').exists(), 'host outcome without intent')
    write_once(root / 'intent.json', intent)
    row = {'status': 'failed', 'answer': None, 'usage': {}, 'cost_usd': None,
           'native_skill_load': 'not_observed'}
    begin = time.monotonic()
    try:
        raw = transport(ENDPOINT, {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, payload, 60)
        require(time.monotonic() - begin <= 60, 'deadline_exceeded')
        reported = raw.get('model')
        row['reported_model'] = reported if reported in MODELS else 'unrecognized'
        usage = raw.get('usage') or {}
        row['usage'] = {k: v for k, v in usage.items() if k in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost')
                        and type(v) in (int, float) and math.isfinite(v) and v >= 0}
        require(reported == model, 'host model mismatch')
        require(row['usage'].get('completion_tokens', 0) <= 1600, 'host output ceiling')
        choices = raw.get('choices')
        require(isinstance(choices, list) and len(choices) == 1, 'host response shape')
        choice = choices[0]
        row['finish_reason'] = choice.get('finish_reason') if choice.get('finish_reason') in (
            'stop', 'length', 'tool_calls', 'content_filter') else 'unknown'
        require(row['finish_reason'] == 'stop', 'host incomplete response')
        message = choice.get('message') or {}
        require(not message.get('tool_calls'), 'host requested unapproved tools')
        answer = message.get('content')
        require(isinstance(answer, str) and bool(answer.strip()), 'host empty response')
        require(key not in answer, 'host credential reflection')
        row.update(status='complete', answer=answer)
    except Exception as exc:
        row['error'] = safe_failure_reason(exc)
    row['elapsed_seconds'] = time.monotonic() - begin
    write_once(root / 'outcome.json', row)
    return row


def run(manifest: dict, root: Path, host_key: str, *, provider=None, host_transport=post_json) -> dict:
    method_root = Path(manifest['method_root'])
    require(admission(manifest['context'], method_root, manifest['host']['model'],
                      manifest['authorization_ref']) == manifest, 'frozen admission changed')
    # Reuse the same journal lock semantics across the whole chain, not just inference.
    import fcntl
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.chain-lock').open('a+b') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise RecoveryRequired('another process owns this chain') from None
        path = root / 'manifest.json'
        if path.exists(): require(read_record(path) == manifest, 'chain manifest changed')
        else: write_once(path, manifest)
        if (root / 'summary.json').exists(): return read_record(root / 'summary.json')
        return _run_locked(manifest, root, host_key, provider, host_transport)


def _run_locked(manifest, root, host_key, provider, host_transport):
    require(bool(host_key), 'host credential required before routing inference')
    provider = provider or TypeSafeJevProvider(choice_rounding=True)
    require(provider_configuration(provider) == manifest['routing']['provider_configuration'], 'routing provider changed')
    scope = 'c01-host-' + digest(manifest)[:24]
    live = {**manifest['routing'], 'scope': scope, 'implementation': manifest['implementation'],
            'authorization_ref': manifest['authorization_ref'], 'freeze_sha256': digest(manifest)}
    with Session(root / 'routing', provider, scope=scope, limits=LIMITS, live_admission=live) as session:
        report = c01.run(session, manifest['context'], Path(manifest['method_root']))
    result = {'routing': report, 'host': None, 'status': 'routing_failed',
              'task_acceptance': 'not_evaluated', 'qualification': False}
    if report['result']['status'] not in ('provider_error', 'unsupported'):
        bundle = handoff.prepare(root / 'routing', report['run_id'], manifest['context'], Path(manifest['method_root']))
        path = root / 'handoff.json'
        if path.exists(): require(read_record(path) == bundle, 'handoff changed')
        else: write_once(path, bundle)
        answer = consume(bundle, root / 'host', manifest['host']['model'], host_key, transport=host_transport)
        result.update(host=answer, status='complete' if answer['status'] == 'complete' else 'host_failed')
    write_once(root / 'summary.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--context', type=Path)
    parser.add_argument('--method-root', type=Path)
    parser.add_argument('--model', choices=MODELS, default=MODELS[0])
    parser.add_argument('--authorization-ref')
    parser.add_argument('--state-root', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == 'prepare':
            require(args.context is not None and args.method_root is not None, 'context and method-root required')
            data = admission(json.loads(args.context.read_text()), args.method_root, args.model, args.authorization_ref)
            write_once(args.manifest, data)
            print(json.dumps({'status': 'prepared', 'manifest': str(args.manifest.resolve()), 'inference_calls': 0}))
        else:
            require(args.state_root is not None, 'state-root required')
            result = run(read_record(args.manifest), args.state_root, os.environ.get('MINDTHUS_HOST_API_KEY', ''))
            print(json.dumps({'status': result['status'], 'answer': (result['host'] or {}).get('answer'),
                              'native_skill_load': 'not_observed', 'qualification': False}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecoveryRequired, handoff.ReplayMismatch) as exc:
        print(json.dumps({'status': 'blocked', 'error_type': type(exc).__name__}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
