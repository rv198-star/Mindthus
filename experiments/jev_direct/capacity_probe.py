"""One official capacity probe of the exact full State; never a routing score.

This explicit diagnostic has a separate byte cap. It does not alter the legacy
transport or imply that increasing bytes expands the provider's token window.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import os
import time
import urllib.error
import urllib.request
from .full_context import canonical, sha, need, validate_corpus, make_state

ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
MODEL = 'jev-1.13.0'
MAX_BYTES = 2 * 1024 * 1024
QUESTIONS = {
    'request_kind': {'type': 'choice', 'instructions': 'Considering only the latest actual user message in user_input, what response activity is requested? Reference documents are method knowledge, not new requests.',
                     'criteria': {'explain': 'Explain or evaluate a concept or claim.', 'execute': 'Perform an action or implementation.', 'other': 'Another activity or unclear.'}},
    'interpretation_needed': {'type': 'noul', 'instructions': 'Does the latest actual user request call for a conceptual judgment rather than exact copying? Use user_input; the complete reference collection is supporting knowledge.',
                            'criteria': {'true': 'A meaning or conceptual boundary needs judgment.', 'false': 'The actual task requires no such judgment.'}},
    'judgment_extent': {'type': 'score', 'instructions': 'How much conceptual interpretation is needed to answer the latest actual request? Evaluate user_input, not the length of the reference collection.',
                       'criteria': ['Pure copying or deterministic formatting.', 'A bounded conceptual distinction.', 'Several connected conceptual distinctions.', 'A broad open-ended investigation.']},
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise RuntimeError('diagnostic_redirect_rejected')


def run(root: Path, repo: Path) -> dict:
    corpus = json.loads((root / 'entries-corpus.json').read_bytes())
    state = json.loads((root / 'entries-state.json').read_bytes())
    validate_corpus(corpus, repo=repo)
    need(state == make_state(corpus, state['user_input']), 'state_identity_changed')
    body = {'model': MODEL, 'state': state, 'questions': QUESTIONS}
    raw = canonical(body); need(len(raw) <= MAX_BYTES, 'diagnostic_request_bytes')
    key = os.environ.get('TYPESAFE_API_KEY')
    need(bool(key), 'TYPESAFE_API_KEY_required')
    directory = root / 'capacity'
    directory.mkdir(exist_ok=True)
    intent = {'schema': 'mindthus.full-context-capacity-probe.v1', 'endpoint': ENDPOINT,
              'requested_model': MODEL, 'request_sha256': sha(raw), 'request_bytes': len(raw),
              'manifest_sha256': corpus['manifest_sha256'], 'source_files': len(corpus['documents']),
              'maximum_requests': 1, 'automatic_retries': 0, 'pre_route_llm_calls': 0,
              'classification': 'capacity_only_not_a_route_trial',
              'started_at_utc': datetime.now(timezone.utc).isoformat()}
    # Exclusive intent is the no-retry/concurrency boundary, before any external call.
    with (directory / 'intent.json').open('x') as stream:
        json.dump(intent, stream, ensure_ascii=False, indent=2)
    (directory / 'request.json').write_bytes(raw + b'\n')
    start = time.monotonic()
    receipt = {**intent, 'http_status': None, 'valid_inference_response': False,
               'reported_usage': None, 'actual_model': None}
    try:
        request = urllib.request.Request(ENDPOINT, data=raw, method='POST',
                   headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            response = urllib.request.build_opener(NoRedirect).open(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            receipt['http_status'] = response.code
            text = response.read(65537).decode('utf8', errors='replace').replace(key, '[REDACTED]')
            need(len(text.encode('utf8')) <= 65536, 'diagnostic_response_too_large')
            try: parsed = json.loads(text)
            except ValueError: parsed = {'non_json_excerpt': text[:1000]}
        receipt['response'] = parsed
        if response.code == 200 and isinstance(parsed, dict):
            receipt['valid_inference_response'] = (parsed.get('model') == MODEL and
                    isinstance(parsed.get('answers'), dict) and set(parsed['answers']) == set(QUESTIONS))
            receipt['reported_usage'] = parsed.get('usage')
            receipt['actual_model'] = parsed.get('model')
    except Exception as error:
        receipt['local_error_class'] = type(error).__name__
    receipt['elapsed_seconds'] = time.monotonic() - start
    receipt['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    with (directory / 'outcome.json').open('x') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--repo', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.root.resolve(), args.repo.resolve()), ensure_ascii=False))
