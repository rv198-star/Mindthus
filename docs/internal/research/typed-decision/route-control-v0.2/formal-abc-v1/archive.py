"""Copy only raw test records, never Codex homes or credentials, with hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
DAY = Path('/Users/william/Documents/Codex/2026-09-25')
MAPPING = (
    (DAY / 'mindthus-formal-abc-v1', HERE / 'evidence-20260925' / 'records' / 'arms'),
    (DAY / 'mindthus-formal-abc-review-v1', HERE / 'evidence-20260925' / 'records' / 'review'),
    (DAY / 'mindthus-paired-blind-review-v1', HERE.parent / 'paired-local-codex-v3' /
     'blind-review-v1' / 'evidence-20260925' / 'records'),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def secret() -> bytes:
    path = Path('/Users/william/Documents/Codex/2026-09-22/install-the-typesafe-skill-if-you/.env')
    for line in path.read_text().splitlines():
        if line.startswith('TYPESAFE_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"\'').encode()
    raise ValueError('TypeSafe credential not found for archive scan')


def archive(source: Path, target: Path, credential: bytes) -> dict:
    rows = []
    for path in sorted(source.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(source)
        if any(part.startswith('codex-home') or part == 'workspaces' for part in rel.parts):
            continue
        raw = path.read_bytes()
        if credential and credential in raw:
            raise ValueError('credential present in raw record: ' + str(rel))
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if destination.read_bytes() != raw:
                raise ValueError('archive drift: ' + str(rel))
        else:
            with destination.open('xb') as out:
                out.write(raw)
        rows.append({'path': str(rel), 'sha256': hashlib.sha256(raw).hexdigest(),
                     'bytes': len(raw)})
    manifest = {'schema': 'mindthus.raw-evidence-archive.v1', 'source_root': str(source),
                'exclusions': ['codex-home*', 'workspaces', 'symlinks'],
                'records': rows}
    index = target.parent / ('index-' + target.name + '.json')
    value = json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    if index.exists():
        if index.read_text() != value:
            raise ValueError('archive index drift')
    else:
        index.write_text(value)
    for row in rows:
        if sha(target / row['path']) != row['sha256']:
            raise ValueError('archive verification failed')
    return {'source': str(source), 'archive': str(target), 'records': len(rows),
            'bytes': sum(x['bytes'] for x in rows), 'index_sha256': sha(index)}


if __name__ == '__main__':
    key = secret()
    for source, target in MAPPING:
        print(json.dumps(archive(source, target, key), ensure_ascii=False))
