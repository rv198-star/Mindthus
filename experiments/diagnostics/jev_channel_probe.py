"""Observable one-channel Jev diagnostic; no fallback, retries or secret logging.

The outer plan records intended MCP arguments, not an unavailable platform trace.
This module is outside the frozen routing implementation and never edits a trial.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import time
import urllib.error
import urllib.request

from experiments.typed_decision.contracts import DecisionSpec, ContractError, canonical, digest, require
from experiments.typed_decision.providers import (
    TypeSafeJevProvider, OpenRouterJevProvider, ProviderError, _NoRedirect,
)
from experiments.typed_decision.relationship_runtime import _locked, save
from experiments.typed_decision.session import read_record, RecoveryRequired, safe_failure_reason

REPO = Path(__file__).resolve().parents[2]
CHANNELS = {
    'typesafe': (TypeSafeJevProvider, 'jev-1.13.0', 'TYPESAFE_API_KEY'),
    'openrouter': (OpenRouterJevProvider, 'typesafe/jev-1.13', 'OPENROUTER_API_KEY'),
}
STATE = {'message': '谢谢，问题已经解决了。'}


def specs():
    return [
        DecisionSpec('intent', 'Choose the communicative intent of message.',
                     {'thanks': 'Expresses thanks and completion.', 'request': 'Asks for further work.'}, ('message',)),
        DecisionSpec('resolved', 'Does the message explicitly say the problem is resolved?',
                     {'true': 'It explicitly states resolution.', 'false': 'It does not state resolution.'},
                     ('message',), kind='assess_proposition'),
        DecisionSpec('urgency', 'Rate the urgency for further action conveyed by message.',
                     ['No further action requested.', 'Further action requested without urgency.', 'Urgent action requested.'],
                     ('message',), kind='rate'),
    ]


def prepare(root: Path, channel: str, node_id: str) -> dict:
    require(channel in CHANNELS, 'probe_channel_not_authorized')
    root = root.resolve()
    require(not root.is_relative_to(REPO), 'probe_records_outside_repository')
    cls, model, key = CHANNELS[channel]
    provider = cls(model, choice_rounding=True)
    body = {'model': model, 'state': STATE, 'questions': provider.engine.questions(specs())}
    command = 'python3 -m experiments.diagnostics.jev_channel_probe run --root ' + shlex.quote(str(root)) + ' --channel ' + channel
    plan = {
        'schema': 'mindthus.observable-channel-probe.v1', 'channel': channel,
        'endpoint': provider.serving_identity.endpoint, 'request_sha256': digest(body),
        'credential_env': key, 'code_sha256': __import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),
        'maximum_requests': 1, 'automatic_retry': False, 'purpose': 'channel_diagnostic_not_business_score',
        'outer_arguments_redacted': {
            'node_id': node_id, 'workdir': str(REPO), 'cmd': command,
            'env': {key: '[REDACTED: explicitly supplied tool environment value]'},
            'execution_mode': 'sync', 'timeout_ms': 60000, 'max_output_bytes': 5000,
        },
        'omitted_optional_outer_fields': ['stdin', 'tty', 'skill', 'skill_env', 'yield_time_ms'],
        'trace_status': 'planned_arguments_not_platform_receipt',
    }
    save(root / channel / 'request.json', body)
    save(root / channel / 'outer-plan.json', plan)
    return plan


def run(root: Path, channel: str, *, transport_override=None) -> dict:
    require(channel in CHANNELS, 'probe_channel_not_authorized')
    directory = root.resolve() / channel
    with _locked(directory / '.lock'):
        plan = read_record(directory / 'outer-plan.json')
        body = read_record(directory / 'request.json')
        cls, model, key = CHANNELS[channel]
        require(plan['request_sha256'] == digest(body) and plan['channel'] == channel,
                'probe_request_binding')
        require(plan['code_sha256'] == __import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(), 'probe_code_drift')
        if (directory / 'outcome.json').exists():
            out = read_record(directory / 'outcome.json')
            require(out['plan_sha256'] == digest(plan), 'probe_cached_binding')
            return out
        if (directory / 'intent.json').exists():
            raise RecoveryRequired('probe_prior_call_unknown_no_retry')
        save(directory / 'execution-entered.json', {'plan_sha256': digest(plan), 'channel': channel})
        if not os.environ.get(key):
            out = {'plan_sha256': digest(plan), 'stage': 'credential_preflight',
                   'status': 'credential_not_present', 'http_status': None, 'external_attempts': 0}
            save(directory / 'outcome.json', out)
            return out
        http = {'http_status': None, 'http_response_received': False}

        def transport(url, headers, request, timeout):
            require(url == plan['endpoint'] and request == body, 'probe_destination_or_body_changed')
            if transport_override is not None:
                value = transport_override(url, headers, request, timeout)
                http.update(http_status=200, http_response_received=True)
                return value
            req = urllib.request.Request(url, data=canonical(request), headers=headers, method='POST')
            try:
                with urllib.request.build_opener(_NoRedirect).open(req, timeout=timeout) as response:
                    http.update(http_status=response.status, http_response_received=True)
                    raw = response.read(1048577)
                    require(len(raw) <= 1048576, 'probe_response_too_large')
                    value = json.loads(raw)
                    require(isinstance(value, dict), 'probe_response_shape')
                    return value
            except urllib.error.HTTPError as exc:
                http.update(http_status=exc.code, http_response_received=True)
                # No arbitrary provider body, authorization header or URL query is exported.
                raise ProviderError('http_' + str(exc.code)) from None
            except (urllib.error.URLError, TimeoutError):
                raise ProviderError('transport_failure') from None
            except (UnicodeError, json.JSONDecodeError):
                raise ProviderError('invalid_json') from None

        provider = cls(model, transport=transport, choice_rounding=True)
        require(provider.serving_identity.endpoint == plan['endpoint'], 'probe_endpoint_binding')
        save(directory / 'intent.json', {'plan_sha256': digest(plan), 'request_sha256': digest(body),
             'started_at_utc': datetime.now(timezone.utc).isoformat(), 'credential_source': 'explicit_tool_environment',
             'credential_logged': False, 'automatic_retry': False})
        start = time.monotonic()
        out = {'plan_sha256': digest(plan), 'external_attempts': 1, 'stage': 'provider_call',
               'results': None, 'resolved_runtime': None, 'usage': None}
        try:
            batch = provider.evaluate(specs(), STATE, 30)
            batch.validate(specs())
            out.update(status='inference_returned', results={k: asdict(v) for k, v in batch.results.items()},
                       resolved_runtime=batch.resolved_runtime.to_dict(), usage=batch.usage)
            out['all_three_contracts_valid'] = all(v.status == 'ok' for v in batch.results.values())
        except (ProviderError, ContractError) as exc:
            out.update(status='provider_or_contract_error', error=safe_failure_reason(exc))
        out.update(http, elapsed_seconds=time.monotonic() - start)
        receipt = provider.response_receipt()
        if receipt is not None:
            save(directory / 'provider-receipt.json', receipt)
        save(directory / 'outcome.json', out)
        return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--channel', choices=CHANNELS, required=True)
    parser.add_argument('--node-id')
    args = parser.parse_args()
    if args.action == 'prepare':
        require(bool(args.node_id), 'probe_node_required')
        value = prepare(args.root, args.channel, args.node_id)
    else:
        value = run(args.root, args.channel)
    print(json.dumps(value, ensure_ascii=False))


if __name__ == '__main__':
    main()
