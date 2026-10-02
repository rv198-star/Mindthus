"""Portable, offline-only fixtures for the bounded batch wiring tests."""
import atexit
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PIN = 'ed5171bf7b34746027acd730864d9c98ef1dd8d2'

@lru_cache(maxsize=1)
def resources():
    # Clone local objects only. Preserve the exact adapter identity check in production.
    temporary = tempfile.TemporaryDirectory(prefix='mindthus-slim-offline-')
    atexit.register(temporary.cleanup)
    base = Path(temporary.name); adapter = base / 'adapter'
    subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(ROOT), str(adapter)], check=True)
    subprocess.run(['git', 'checkout', '--quiet', '--detach', PIN], cwd=adapter, check=True)
    binary = base / 'codex-offline-fixture'
    binary.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then echo "codex-cli OFFLINE-FIXTURE"; else exit 99; fi\n')
    binary.chmod(0o755)
    return str(adapter), str(binary)
