"""Auditable pointer-format repair for formal-abc-v1; never touches an Episode ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from experiments.typed_decision.contracts import canonical, digest, require
from experiments.typed_decision.session import read_record

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-formal-abc-v1')


def normalize(case: str, arm: str) -> dict:
    path = ROOT / case / (arm + '-latest.json')
    raw = path.read_bytes()
    obj = json.loads(raw)
    if isinstance(obj, dict) and obj.get('schema') == 'mindthus.decision-record.v1':
        return {'case': case, 'arm': arm, 'status': 'already_wrapped',
                'sha256': hashlib.sha256(raw).hexdigest()}
    require(isinstance(obj, dict), 'latest_pointer_not_object')
    source_sha = hashlib.sha256(raw).hexdigest()
    preserved = path.parent / 'snapshots' / (arm + '-latest-raw-' + source_sha + '.json')
    preserved.parent.mkdir(parents=True, exist_ok=True)
    if preserved.exists():
        require(preserved.read_bytes() == raw, 'raw_pointer_archive_changed')
    else:
        with preserved.open('xb') as f:
            f.write(raw)
    wrapped = canonical({'schema': 'mindthus.decision-record.v1',
                         'payload': obj, 'sha256': digest(obj)}) + b'\n'
    fd, temp = tempfile.mkstemp(prefix='.latest-repair-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(wrapped)
            f.flush()
            os.fsync(f.fileno())
        require(path.read_bytes() == raw, 'latest_pointer_changed_during_repair')
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    require(read_record(path) == obj, 'latest_pointer_repair_failed')
    return {'case': case, 'arm': arm, 'status': 'wrapped',
            'raw_sha256': source_sha, 'wrapped_sha256': hashlib.sha256(wrapped).hexdigest(),
            'preserved_path': str(preserved)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('case', choices=('HB', 'HC', 'HD'))
    parser.add_argument('arm', choices=('B', 'C'))
    args = parser.parse_args()
    print(json.dumps(normalize(args.case, args.arm), ensure_ascii=False))
