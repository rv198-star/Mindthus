"""One admitted blind label review; no arm execution, retries or credential storage."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
import review_packet
from experiments.typed_decision.providers import post_json
from experiments.typed_decision.session import read_record, write_once

MODEL = 'glm-5.3-flash'
ENDPOINT = 'https://cpa.72live.com/v1/chat/completions'
MAX_BYTES = 196608
MAX_TOKENS = 6000
TIMEOUT = 90
OWNERS = {'3l5s', 'sra', 'edsp', 'sela', 'mpg', 'wae', 'tvg', 'tplan', None}
ENTRIES = {'direct_execution', 'acquire_information', 'mindthus_intervention', 'unclear', None}
ROUTES = {'direct_execute', 'acquire_information', 'intervene', 'llm_fallback', 'original_path'}
SYSTEM = '''You are a separate pre-results reviewer of candidate task labels. Use only supplied canonical method contracts and task contexts. Family, author labels and previous outcomes are withheld. Judge necessary handling, not merely whether a method might be useful. Do not answer the tasks or invent missing facts. Return a JSON object with exactly one key judgments, an array with one row for every opaque id in the supplied order. Each row has exactly: id, entry_mode, unresolved_obligation, owner, checked_owner, applicable, route, ambiguity, rationale. entry_mode: direct_execution/acquire_information/mindthus_intervention/unclear/null. unresolved_obligation: clear/present/unclear/null. owner and checked_owner: 3l5s/sra/edsp/sela/mpg/wae/tvg/tplan/null. applicable: yes/no/unclear/null. route: direct_execute/acquire_information/intervene/llm_fallback/original_path. ambiguity is boolean; rationale is a brief justification (at most 160 Chinese characters), not a reasoning transcript. owner means FINAL selected method: null for every non-intervene route. checked_owner means the candidate whose applicability was checked and can remain non-null on rejection. Stale, invalid or out-of-scope D0 input goes to original_path with semantic fields null. An unresolved supported duty leads to llm_fallback without erasing that duty. Normal missing facts lead to acquire_information. With admissible entry and clear duties, an explicitly requested method is checked even if the task is simple; its name does not establish applicability. If an entry/owner remains genuinely ambiguous, flag ambiguity rather than force a unique label. Method preference is distinct from task failure. Do not output hidden reasoning or extra text.'''


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def prepared() -> tuple[dict, dict]:
    payload, packet_manifest = review_packet.prepare()
    body = {'model': MODEL, 'temperature': 0, 'max_tokens': MAX_TOKENS, 'stream': False,
            'messages': [{'role': 'system', 'content': SYSTEM},
                         {'role': 'user', 'content': review_packet.canonical(payload).decode()}]}
    size = len(review_packet.canonical(body))
    check(size <= MAX_BYTES, 'review request exceeds budget')
    sources = {**packet_manifest['source_sha256'],
               str(Path(__file__).resolve().relative_to(REPO)):
               hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               str((HERE / 'label_review_check.py').relative_to(REPO)):
               hashlib.sha256((HERE / 'label_review_check.py').read_bytes()).hexdigest()}
    freeze = {'schema': 'mindthus.c01-label-review-admission.v1',
              'endpoint': ENDPOINT, 'model': MODEL, 'max_tokens': MAX_TOKENS,
              'timeout_seconds': TIMEOUT, 'max_request_bytes': MAX_BYTES,
              'request_sha256': review_packet.sha(body), 'request_bytes': size,
              'source_sha256': sources, 'case_ids': [row['id'] for row in payload['cases']],
              'payload_sha256': packet_manifest['payload_sha256'],
              'private_case_id_map': packet_manifest['private_case_id_map'],
              'max_calls': 1, 'retries': 0, 'model_switches': 0,
              'author_labels_transmitted': False, 'charge_currency': 'unknown',
              'qualification': False,
              'supersedes': 'blocked inline tool attempt: no observed provider response'}
    return body, freeze


def validate_judgments(content: str, ids: list[str]) -> list[dict]:
    text = content.strip()
    if text.startswith('```') and text.endswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    data = json.loads(text)
    check(isinstance(data, dict) and set(data) == {'judgments'}, 'review object shape')
    rows = data['judgments']
    check(isinstance(rows, list) and len(rows) == len(ids), 'review case count')
    check(all(isinstance(row, dict) for row in rows), 'review row shape')
    check([row.get('id') for row in rows] == ids, 'review ids/order changed')
    fields = {'id','entry_mode','unresolved_obligation','owner','checked_owner',
              'applicable','route','ambiguity','rationale'}
    for row in rows:
        check(set(row) == fields, 'review fields changed')
        check(row['entry_mode'] in ENTRIES, 'entry enum')
        check(row['unresolved_obligation'] in {'clear','present','unclear',None}, 'duty enum')
        check(row['owner'] in OWNERS and row['checked_owner'] in OWNERS, 'owner enum')
        check(row['applicable'] in {'yes','no','unclear',None}, 'applicability enum')
        check(row['route'] in ROUTES and type(row['ambiguity']) is bool, 'route/ambiguity type')
        check(isinstance(row['rationale'], str) and 0 < len(row['rationale']) <= 400,
              'bounded rationale required')
        check(row['route'] == 'intervene' or row['owner'] is None, 'fallback final owner')
        if row['route'] == 'intervene':
            check(row['owner'] is not None and row['checked_owner'] == row['owner']
                  and row['applicable'] == 'yes', 'inconsistent selected method')
    return rows


def run(root: Path, key: str, *, transport=post_json) -> dict:
    body, current = prepared()
    frozen = json.loads((HERE / 'label-review-freeze.json').read_text())
    check(current == frozen, 'review freeze mismatch')
    check(isinstance(key, str) and bool(key.strip()), 'missing review credential')
    if root.exists():
        check((root / 'outcome.json').exists(), 'unknown prior review; reconcile, never resend')
        check(read_record(root / 'intent.json')['request_sha256'] == frozen['request_sha256'],
              'prior review identity changed')
        return read_record(root / 'outcome.json')
    root.mkdir(parents=True, exist_ok=False)
    write_once(root / 'intent.json', {**frozen, 'private_case_id_map': 'retained in local freeze'})
    write_once(root / 'request.json', body)
    result = {'status': 'failed', 'model': MODEL, 'usage': {}, 'cost_usd': None,
              'request_sha256': frozen['request_sha256'], 'judgments': None,
              'raw_content': None, 'qualification': False}
    started = time.monotonic()
    try:
        raw = transport(ENDPOINT, {'Authorization': 'Bearer ' + key,
                                  'Content-Type': 'application/json',
                                  'User-Agent': 'Mindthus-C01-integration/1'}, body, TIMEOUT)
        check(isinstance(raw, dict), 'response object')
        check(time.monotonic() - started <= TIMEOUT, 'review timeout')
        check(raw.get('model') == MODEL, 'review model mismatch')
        usage = raw.get('usage') or {}
        if isinstance(usage, dict):
            result['usage'] = {name: value for name, value in usage.items()
                               if name in {'prompt_tokens','completion_tokens','total_tokens','cost'}
                               and type(value) in (int,float) and math.isfinite(value) and value >= 0}
        check(result['usage'].get('completion_tokens', 0) <= MAX_TOKENS, 'review token ceiling')
        choices = raw.get('choices')
        check(isinstance(choices, list) and len(choices) == 1, 'review response shape')
        message = choices[0].get('message') or {}
        check(not message.get('tool_calls'), 'unexpected tool call')
        content = message.get('content')
        check(isinstance(content, str) and content.strip(), 'empty review')
        check(key not in content, 'credential reflection')
        result['raw_content'] = content  # preserves invalid/truncated JSON without repairing semantics
        check(choices[0].get('finish_reason') == 'stop', 'incomplete review')
        result['judgments'] = validate_judgments(content, frozen['case_ids'])
        result['status'] = 'complete'
    except Exception as exc:
        result['error_type'] = type(exc).__name__  # never remote error text/headers/reasoning
    result['elapsed_seconds'] = time.monotonic() - started
    check(key not in json.dumps(result, ensure_ascii=False), 'credential in result')
    write_once(root / 'outcome.json', result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze','run'])
    parser.add_argument('--state-root', type=Path)
    args = parser.parse_args()
    if args.action == 'freeze':
        _, freeze = prepared()
        with (HERE / 'label-review-freeze.json').open('x') as output:
            json.dump(freeze, output, ensure_ascii=False, indent=2)
            output.write('\n')
        print(json.dumps({'status':'frozen','request_bytes':freeze['request_bytes'], 'calls':0}))
        return 0
    check(args.state_root is not None, 'state root required')
    result = run(args.state_root, os.environ.get('MINDTHUS_HOST_API_KEY', ''))
    print(json.dumps({name: result.get(name) for name in
                      ['status','model','usage','elapsed_seconds','error_type']}, ensure_ascii=False))
    return 0 if result['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
