"""One portable live Jev/current-Agent development episode; no OCI identity."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from experiments.typed_decision import entry, route_control as rc
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision.contracts import canonical, digest, provider_configuration, require
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from experiments.typed_decision.session import implementation_digest, read_record, write_once

SOURCE = HERE.parent / 'holdout-candidate-source-v1' / 'evidence-20260925' / 'records' / 'codex-calls' / 'task-candidates' / 'last-message.txt'
AUTH = 'Owner authorized continuing #211 tests locally after OCI became unavailable; 2026-09-25'
OWNER = 'current-codex:portable-211-B1-v1'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packet() -> dict:
    case = next(x for x in json.loads(SOURCE.read_text())['cases'] if x['id'] == 'B1')
    docs = [{'id': 'U', 'revision': '1', 'kind': 'user', 'text': case['user_request']},
            {'id': 'S', 'revision': '1', 'kind': 'source', 'text': case['given_facts']}]
    return {'schema': 'mindthus.route-control-input.v1', 'episode_id': 'portable-211-B1-v1',
            'turn_id': '1', 'revision': '1', 'documents': docs,
            'authority': {'owner_ref': OWNER, 'risk': 'low', 'mode': 'read_only',
                          'known_obligations': []},
            'issues': [{'id': 'I1', 'request_ref': rel.quote(docs[0]),
                        'candidates': ['wae'],
                        'handling': {'value': 'judge', 'owner_ref': OWNER,
                                     'revision': '1', 'refs': [rel.quote(docs[0])]},
                        'assessability': None, 'attention': True}],
            'dependencies': [], 'relationship': None,
            'task_budget': {'max_calls': 1, 'max_seconds': 45}}


def objects():
    return (TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True,
                                transport=deadline_post_json), CurrentAgentHost(OWNER))


def identity(root: Path) -> dict:
    root = root.resolve()
    require(not root.is_relative_to(REPO), 'state_root_inside_repository')
    p = packet()
    provider, host = objects()
    bundle, qs, bindings = rc.load_policy(REPO)
    compiled = rc.compile_route(p, REPO, bundle, qs, bindings)
    require(len(compiled.specs) == 4, 'portable_question_count_changed')
    admission = {'schema': 'mindthus.route-control-live.v1', 'mode': rc.MODE,
                 'root': str(root), 'implementation': implementation_digest(),
                 'source_bindings': bundle['sources'], 'provider': provider_configuration(provider),
                 'packet_hashes': [digest(p)], 'authorization_ref': AUTH,
                 'ceilings': {'judgments': 1, 'corrections': 0, 'organize': 0,
                              'arbitrations': 0, 'executions': 1, 'requests': 1,
                              'reserve_per_jev_usd': .02},
                 'executor': host.configuration, 'corrector': None,
                 'arbitrator': None, 'organizer': None}
    rc._admission(admission, root, p, provider, bundle,
                  {'executor': host, 'corrector': None, 'arbitrator': None, 'organizer': None})
    return {'schema': 'mindthus.portable-current-codex-freeze.v1',
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                     cwd=REPO, text=True).strip(),
            'source_files': {'PLAN.md': sha(HERE / 'PLAN.md'), 'run.py': sha(HERE / 'run.py'),
                             'candidate_source': sha(SOURCE)},
            'implementation': implementation_digest(), 'root': str(root),
            'packet_sha256': digest(p),
            'questions_sha256': digest([s.to_dict() for s in compiled.specs]),
            'context_sha256': digest(compiled.context), 'admission': admission,
            'requested_model': 'jev-1.13.0', 'max_jev_calls': 1,
            'reserve_usd': .02, 'max_host_executions': 1,
            'automatic_retries': 0, 'CPA_calls': 0, 'OpenRouter_calls': 0,
            'claim_ceiling': 'one exposed portable development episode'}


def freeze(root: Path) -> dict:
    frozen = identity(root)
    path = root / 'freeze.json'
    root.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(read_record(path) == frozen, 'portable_freeze_changed')
    else:
        write_once(path, frozen)
    return frozen


def verify(root: Path) -> dict:
    frozen = read_record(root / 'freeze.json')
    expected = identity(root)
    # Later result commits do not change the pre-call source identity.
    expected['source_commit'] = frozen['source_commit']
    require(frozen == expected, 'portable_freeze_changed')
    return frozen


def credential(path: Path) -> str:
    require(stat.S_IMODE(path.stat().st_mode) & 0o077 == 0, 'credential_file_not_private')
    for line in path.read_text().splitlines():
        if line.startswith('TYPESAFE_API_KEY='):
            value = line.split('=', 1)[1].strip().strip('"\'')
            require(bool(value), 'typesafe_credential_absent')
            return value
    raise ValueError('typesafe_credential_absent')


def run(root: Path, credential_file: Path | None) -> dict:
    frozen = verify(root)
    require(not os.environ.get('MINDTHUS_HOST_API_KEY') and
            not os.environ.get('OPENROUTER_API_KEY'), 'forbidden_provider_present')
    old = os.environ.get('TYPESAFE_API_KEY')
    if credential_file:
        os.environ['TYPESAFE_API_KEY'] = credential(credential_file)
    try:
        provider, host = objects()
        result = entry.run(root, provider, packet(), REPO, mode=rc.MODE,
                           executor=host, live_admission=frozen['admission'])
    finally:
        if old is None:
            os.environ.pop('TYPESAFE_API_KEY', None)
        else:
            os.environ['TYPESAFE_API_KEY'] = old
    pointer = root / 'latest.json'
    pointer.write_bytes(canonical(result) + b'\n')
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run', 'submit'))
    parser.add_argument('--state-root', type=Path, required=True)
    parser.add_argument('--credential-file', type=Path)
    parser.add_argument('--host-response', type=Path)
    args = parser.parse_args()
    root = args.state_root.resolve()
    if args.action == 'freeze':
        print(json.dumps({'freeze': digest(freeze(root)), 'model_calls': 0}))
        return
    verify(root)
    if args.action == 'verify':
        print(json.dumps({'verified': True, 'freeze': digest(read_record(root / 'freeze.json'))}))
        return
    if args.action == 'submit':
        require(args.host_response is not None, 'host_response_required')
        submission = json.loads(args.host_response.read_bytes())
        receipt = submit_response(root, REPO, submission)
        print(json.dumps({'receipt': receipt}))
        return
    result = run(root, args.credential_file)
    print(json.dumps({'status': result.get('status'), 'reason': result.get('reason'),
                      'counts': result.get('counts'), 'host_request': result.get('host_request'),
                      'route': result.get('route', {}).get('per_issue') if result.get('route') else None},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
