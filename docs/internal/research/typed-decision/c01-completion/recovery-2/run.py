"""Bounded C01 completion recovery on OCI: N03 host + E01 fresh full path."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from experiments.typed_decision import c01_host, handoff
from experiments.typed_decision.contracts import canonical, digest, require
from experiments.typed_decision.providers import TypeSafeJevProvider, post_json
from experiments.typed_decision.session import (
    implementation_digest,
    read_record,
    safe_failure_reason,
    write_once,
)

DOCS = Path(__file__).resolve().parent
TD = DOCS.parents[1]
METHODS = TD / 'language-diagnostic/english'
ENDPOINT = 'https://cpa.72live.com/v1/chat/completions'
PRIMARY = 'deepseek-v4.1-flash'
BACKUP = 'glm-5.3-flash'
MODELS = (PRIMARY, BACKUP)
UA = 'Mindthus-C01-integration/1'
N03_INPUTS = TD / 'host-trial/inputs.json'
E01_CONTEXT = TD / 'c01-completion/E01-context.json'
AUTH = 'Owner-authorized C01 technical recovery 2; c01-completion/recovery-2/protocol.md'


def n03_case() -> dict:
    cases = json.loads(N03_INPUTS.read_text())['cases']
    rows = [row for row in cases if row['id'] == 'N03']
    require(len(rows) == 1, 'N03 preserved input missing')
    return rows[0]


def host_body(prompt: str, model: str) -> dict:
    require(model in MODELS, 'host model outside recovery authorization')
    return {
        'model': model,
        'temperature': 0,
        'max_tokens': 1600,
        'stream': False,
        'messages': [
            {'role': 'system', 'content': c01_host.SYSTEM},
            {'role': 'user', 'content': prompt},
        ],
    }


def prepare() -> dict:
    n03 = n03_case()
    e01_context = json.loads(E01_CONTEXT.read_text())
    e01 = c01_host.admission(e01_context, METHODS, PRIMARY, AUTH)
    files = [
        Path(__file__).resolve(),
        DOCS / 'protocol.md',
        DOCS / 'offline_check.py',
        N03_INPUTS,
        E01_CONTEXT,
        REPO / 'experiments/typed_decision/c01_host.py',
        REPO / 'experiments/typed_decision/c01.py',
        REPO / 'experiments/typed_decision/handoff.py',
        REPO / 'experiments/typed_decision/providers.py',
        REPO / 'experiments/typed_decision/session.py',
    ]
    return {
        'schema': 'mindthus.c01-completion-recovery-2.v1',
        'implementation': implementation_digest(),
        'files': {
            str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
        'n03': {
            'source_run_id': n03['source_run_id'],
            'handoff_sha256': n03['handoff_sha256'],
            'prompt_sha256': digest(n03['prompt']),
            'requests': {
                model: digest(host_body(n03['prompt'], model)) for model in MODELS
            },
        },
        'e01_manifest': e01,
        'host': {
            'endpoint': ENDPOINT,
            'primary_model': PRIMARY,
            'backup_model': BACKUP,
            'backup_only_after_technical_failure': True,
            'max_tokens': 1600,
            'max_request_bytes': 49152,
            'max_seconds_per_call': 60,
            'max_calls': 4,
            'cost': 'unknown unless returned under a verified currency contract',
        },
        'routing': {
            'provider': 'typesafe',
            'model': 'jev-1.13.0',
            'max_calls': 3,
            'max_seconds': 60,
            'reserve_usd': 0.008064,
        },
        'total_call_ceiling': 7,
        'automatic_retries': 0,
        'semantic_revisions': 0,
        'qualification': False,
    }


def _host_prompt_call(root: Path, prompt: str, model: str, key: str) -> dict:
    payload = host_body(prompt, model)
    require(len(canonical(payload)) <= 49152, 'host request ceiling')
    intent = {
        'request_sha256': digest(payload),
        'request_bytes': len(canonical(payload)),
        'model': model,
        'endpoint': ENDPOINT,
        'user_agent': UA,
    }
    require(not root.exists(), 'host attempt root already exists')
    write_once(root / 'intent.json', intent)
    row = {
        'status': 'failed',
        'answer': None,
        'usage': {},
        'cost_usd': None,
        'model': model,
    }
    begin = time.monotonic()
    try:
        raw = post_json(
            ENDPOINT,
            {
                'Authorization': 'Bearer ' + key,
                'Content-Type': 'application/json',
                'User-Agent': UA,
            },
            payload,
            60,
        )
        reported = raw.get('model')
        row['reported_model'] = reported if reported in MODELS else 'unrecognized'
        require(reported == model, 'host model mismatch')
        usage = raw.get('usage') or {}
        row['usage'] = {
            name: value for name, value in usage.items()
            if name in ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost')
            and type(value) in (int, float)
            and math.isfinite(value)
            and value >= 0
        }
        require(row['usage'].get('completion_tokens', 0) <= 1600, 'host output ceiling')
        choices = raw.get('choices')
        require(isinstance(choices, list) and len(choices) == 1, 'host response shape')
        choice = choices[0]
        finish = choice.get('finish_reason')
        row['finish_reason'] = finish if finish in (
            'stop', 'length', 'tool_calls', 'content_filter'
        ) else 'unknown'
        require(finish == 'stop', 'host incomplete response')
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


def _host_with_backup(root: Path, prompt: str, key: str) -> dict:
    primary = _host_prompt_call(root / 'primary', prompt, PRIMARY, key)
    if primary['status'] == 'complete':
        return {
            'effective_model': PRIMARY,
            'effective': primary,
            'primary': primary,
            'backup': None,
        }
    backup = _host_prompt_call(root / 'backup', prompt, BACKUP, key)
    return {
        'effective_model': BACKUP if backup['status'] == 'complete' else None,
        'effective': backup if backup['status'] == 'complete' else None,
        'primary': primary,
        'backup': backup,
    }


def run(root: Path, host_key: str) -> dict:
    frozen = json.loads((DOCS / 'freeze.json').read_text())
    require(prepare() == frozen, 'recovery freeze/source changed')
    require(not root.exists(), 'recovery root exists; no replay')
    require(bool(host_key), 'CPA credential required')
    write_once(root / 'manifest.json', frozen)

    n03 = n03_case()
    n03_result = _host_with_backup(root / 'N03-host', n03['prompt'], host_key)
    write_once(root / 'N03-summary.json', n03_result)
    print(json.dumps({
        'case': 'N03',
        'status': (n03_result['effective'] or {}).get('status', 'failed'),
        'model': n03_result['effective_model'],
    }), flush=True)

    e01_result = None
    if n03_result['effective'] is not None:
        manifest = frozen['e01_manifest']
        primary_root = root / 'E01-primary'
        e01_result = c01_host.run(manifest, primary_root, host_key)
        effective_host = e01_result.get('host')
        backup = None
        if (
            e01_result['status'] == 'host_failed'
            and effective_host is not None
            and effective_host.get('status') != 'complete'
            and (primary_root / 'handoff.json').exists()
        ):
            bundle = read_record(primary_root / 'handoff.json')
            backup = c01_host.consume(
                bundle,
                root / 'E01-backup-host',
                BACKUP,
                host_key,
            )
            if backup['status'] == 'complete':
                effective_host = backup
        e01_result = {
            'primary_chain': e01_result,
            'backup_host': backup,
            'effective_host': effective_host,
            'effective_complete': (
                e01_result['routing']['result']['status']
                not in ('provider_error', 'unsupported')
                and effective_host is not None
                and effective_host.get('status') == 'complete'
            ),
        }
        write_once(root / 'E01-summary.json', e01_result)
        print(json.dumps({
            'case': 'E01',
            'routing_status': e01_result['primary_chain']['routing']['result']['status'],
            'route': e01_result['primary_chain']['routing']['result']['route'],
            'owner': e01_result['primary_chain']['routing']['result']['owner'],
            'host_status': (e01_result['effective_host'] or {}).get('status'),
            'host_model': (e01_result['effective_host'] or {}).get('reported_model'),
        }), flush=True)

    summary = {
        'n03': n03_result,
        'e01': e01_result,
        'n03_complete': n03_result['effective'] is not None,
        'e01_complete': bool(e01_result and e01_result['effective_complete']),
        'qualification': False,
        'native_skill_load': 'not_observed',
    }
    write_once(root / 'summary.json', summary)
    require(
        all(host_key.encode() not in path.read_bytes()
            for path in root.rglob('*') if path.is_file()),
        'CPA credential in recovery artifact',
    )
    print(json.dumps({
        'n03_complete': summary['n03_complete'],
        'e01_complete': summary['e01_complete'],
        'exact_cpa_key_scan': 'PASS',
    }), flush=True)
    return summary


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else ''
    if action == 'freeze':
        path = DOCS / 'freeze.json'
        require(not path.exists(), 'freeze already exists')
        path.write_text(json.dumps(prepare(), indent=2) + '\n')
    elif action == 'run':
        require(len(sys.argv) == 3, 'usage: run.py run <state-root>')
        run(Path(sys.argv[2]), os.environ.get('MINDTHUS_HOST_API_KEY', ''))
    else:
        raise SystemExit('usage: run.py freeze | run <state-root>')
