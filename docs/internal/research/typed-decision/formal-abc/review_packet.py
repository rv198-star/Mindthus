"""Prepare a blind label-review packet only; no model, credential or network access."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
METHODS = ('using-mindthus', '3l5s', 'sra', 'edsp', 'sela', 'mpg', 'wae', 'tvg', 'tplan')


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def blind_cases(candidates: dict) -> tuple[list[dict], dict[str, str]]:
    """Keep genuine user context, exclude every author-supplied evaluation field."""
    cases = candidates.get('cases')
    if not isinstance(cases, list) or not cases:
        raise ValueError('nonempty candidate list required')
    ids = []
    for row in cases:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id']:
            raise ValueError('candidate id required')
        if not isinstance(row.get('context'), dict):
            raise ValueError('candidate context required')
        ids.append(row['id'])
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate candidate id')
    # Stable non-semantic order: do not expose author strata through ordered case ids.
    ordered = sorted(cases, key=lambda row: sha(['c01-blind-order-v1', row['id']]))
    public, private_map = [], {}
    for index, row in enumerate(ordered, 1):
        review_id = f'R{index:02d}'
        public.append({'id': review_id, 'context': copy.deepcopy(row['context'])})
        private_map[review_id] = row['id']
    return public, private_map


def prepare() -> tuple[dict, dict]:
    source = HERE / 'holdout-candidates.json'
    public, private_map = blind_cases(json.loads(source.read_text(encoding='utf-8')))
    methods = {name: REPO / 'skills' / name / 'SKILL.md' for name in METHODS}
    payload = {
        'cases': public,
        'canonical_contracts': {name: path.read_text(encoding='utf-8')
                                for name, path in methods.items()},
    }
    sources = [source, HERE / 'label-review-protocol.md', Path(__file__).resolve(),
               HERE / 'offline_check.py', *methods.values()]
    manifest = {
        'schema': 'mindthus.c01-blind-review-packet.v1',
        'status': 'prepared_not_sent',
        'payload_sha256': sha(payload),
        'payload_bytes': len(canonical(payload)),
        'candidate_count': len(public),
        'private_case_id_map': private_map,
        'source_sha256': {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sources},
        'model_calls': 0,
        'holdout_qualified': False,
        'note': 'Only payload.json is model-facing. This manifest and author labels remain local.',
    }
    return payload, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory; an existing review packet is never replaced')
    args = parser.parse_args()
    payload, manifest = prepare()
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in (('payload.json', payload), ('manifest.json', manifest)):
        with (args.output / name).open('xb') as stream:
            stream.write(canonical(value) + b'\n')
    print(json.dumps({key: manifest[key] for key in
                      ('status', 'candidate_count', 'payload_sha256', 'model_calls')},
                     ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
