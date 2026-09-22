"""Offline controls for C01 completion recovery 2; no network or credentials."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('c01_recovery_2', HERE / 'run.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def response(model: str, text: str = 'ok') -> dict:
    return {
        'model': model,
        'choices': [{
            'finish_reason': 'stop',
            'message': {'content': text},
        }],
        'usage': {
            'prompt_tokens': 10,
            'completion_tokens': 2,
            'total_tokens': 12,
        },
    }


def main() -> int:
    frozen = json.loads((HERE / 'freeze.json').read_text())
    assert mod.prepare() == frozen

    n03 = mod.n03_case()
    original = mod.post_json
    try:
        calls = []
        def primary_ok(url, headers, body, timeout):
            calls.append(body['model'])
            return response(body['model'])
        mod.post_json = primary_ok
        with tempfile.TemporaryDirectory() as tmp:
            result = mod._host_with_backup(Path(tmp) / 'one', n03['prompt'], 'fixture-secret')
        assert result['effective_model'] == mod.PRIMARY
        assert calls == [mod.PRIMARY]

        calls = []
        def primary_fail_backup_ok(url, headers, body, timeout):
            calls.append(body['model'])
            if body['model'] == mod.PRIMARY:
                raise RuntimeError('simulated technical failure')
            return response(body['model'])
        mod.post_json = primary_fail_backup_ok
        with tempfile.TemporaryDirectory() as tmp:
            result = mod._host_with_backup(Path(tmp) / 'two', n03['prompt'], 'fixture-secret')
        assert result['effective_model'] == mod.BACKUP
        assert calls == [mod.PRIMARY, mod.BACKUP]

        for root_name in ('one', 'two'):
            pass
    finally:
        mod.post_json = original

    print('recovery-2 offline checks: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
