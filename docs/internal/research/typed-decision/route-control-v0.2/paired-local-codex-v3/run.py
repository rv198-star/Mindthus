"""Eight new local A-F development episodes, reusing the existing entry only."""
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
import cases

from experiments.typed_decision import entry, route_control as rc
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision.contracts import canonical, digest, provider_configuration, require
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from experiments.typed_decision.session import implementation_digest, read_record, write_once

IDS = ('A1', 'A2', 'C1', 'D1', 'E1', 'E2', 'F1', 'F2')
AUTH = 'Owner authorized finishing #211 tests with new local Episodes; 2026-09-25'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outside(root: Path) -> Path:
    root = root.resolve()
    require(not root.is_relative_to(REPO), 'state_root_inside_repository')
    return root


def freeze_path(root: Path) -> Path:
    return root.with_name(root.name + '-freeze.json')


def objects(packet: dict):
    provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True,
                                   transport=deadline_post_json)
    owner = packet['authority']['owner_ref']
    return provider, CurrentAgentHost(owner), (CurrentAgentHost(owner, role='correction')
                                               if packet['relationship'] else None)


class Acceptor:
    def __init__(self, root: Path, owner: str):
        self.root, self.identity = root, owner
        self.configuration = {'kind': 'current-agent-source-checked-acceptance.v1',
                              'owner': owner, 'case_id': 'D1'}

    def accept(self, edge, artifact, packet):
        path = self.root / 'host-acceptance' / (edge['id'] + '.json')
        if path.exists():
            value = json.loads(path.read_bytes())
            require(value['artifact_sha256'] == artifact['artifact_sha256']
                    and value['owner_ref'] == self.identity,
                    'host_artifact_acceptance_changed')
            return value
        return {'owner_ref': self.identity, 'dependency_id': edge['id'],
                'artifact_sha256': artifact['artifact_sha256'],
                'accepted': False, 'reason': 'Original host has not accepted this artifact'}


def admission(root: Path, case_id: str, packet: dict, bundle: dict, specs: int) -> dict:
    provider, executor, corrector = objects(packet)
    relation_calls = 2 if packet['relationship'] else 0
    route_calls = 1 if specs else 0
    post_artifact = 1 if case_id == 'D1' else 0
    judgments = relation_calls + route_calls + post_artifact
    a = {'schema': 'mindthus.route-control-live.v1', 'mode': rc.MODE,
         'root': str(root / case_id), 'implementation': implementation_digest(),
         'source_bindings': bundle['sources'], 'provider': provider_configuration(provider),
         'packet_hashes': [digest(packet)], 'authorization_ref': AUTH,
         'ceilings': {'judgments': judgments, 'corrections': 1 if corrector else 0,
                      'organize': 0, 'arbitrations': 0,
                      'executions': packet['task_budget']['max_calls'],
                      'requests': judgments + (1 if corrector else 0),
                      'reserve_per_jev_usd': .02},
         'executor': executor.configuration, 'corrector': corrector.configuration if corrector else None,
         'arbitrator': None, 'organizer': None}
    rc._admission(a, root / case_id, packet, provider, bundle,
                  {'executor': executor, 'corrector': corrector,
                   'arbitrator': None, 'organizer': None})
    return a


def identity(root: Path) -> dict:
    root = outside(root)
    all_packets = cases.packets()
    bundle, qs, bindings = rc.load_policy(REPO)
    identities, admissions = {}, {}
    for case_id in IDS:
        p = all_packets[case_id]
        c = rc.compile_route(p, REPO, bundle, qs, bindings)
        relation = rel.compile_packet(p['relationship'], REPO) if p['relationship'] else None
        identities[case_id] = {'packet': digest(p),
                               'route_specs': digest([s.to_dict() for s in c.specs]),
                               'route_context': digest(c.context),
                               'relation_specs': digest([s.to_dict() for s in relation.specs]) if relation else None,
                               'relation_context': digest(relation.context) if relation else None}
        admissions[case_id] = admission(root, case_id, p, bundle, len(c.specs))
    return {'schema': 'mindthus.paired-local-codex-development-freeze.v1',
            'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                     cwd=REPO, text=True).strip(),
            'source_files': {'PLAN.md': sha(HERE / 'PLAN.md'),
                             'cases.py': sha(HERE / 'cases.py'),
                             'run.py': sha(HERE / 'run.py'),
                             'candidate_source': sha(cases.SOURCE)},
            'implementation': implementation_digest(), 'source_bindings': bundle['sources'],
            'root': str(root), 'ids': list(IDS), 'identities': identities,
            'admissions': admissions, 'max_new_jev_calls': 11,
            'reserve_per_call_usd': .02, 'max_reserved_usd': .22,
            'CPA_calls': 0, 'OpenRouter_calls': 0, 'automatic_retries': 0,
            'B1_prior': 'portable-current-codex-v2:one valid unresolved Jev call',
            'claim_ceiling': 'exposed local development; not formal holdout'}


def freeze(root: Path) -> dict:
    root = outside(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    require(not root.exists() or not any(root.iterdir()), 'new_cohort_root_must_be_empty')
    value = identity(root)
    fp = freeze_path(root)
    if fp.exists():
        require(read_record(fp) == value, 'paired_freeze_changed')
    else:
        write_once(fp, value)
    return value


def verify(root: Path) -> dict:
    frozen = read_record(freeze_path(root))
    expected = identity(root)
    expected['source_commit'] = frozen['source_commit']
    require(frozen == expected, 'paired_freeze_changed')
    return frozen


def credential(path: Path) -> str:
    require(stat.S_IMODE(path.stat().st_mode) & 0o077 == 0, 'credential_file_not_private')
    for line in path.read_text().splitlines():
        if line.startswith('TYPESAFE_API_KEY='):
            value = line.split('=', 1)[1].strip().strip('"\'')
            require(bool(value), 'typesafe_credential_absent')
            return value
    raise ValueError('typesafe_credential_absent')


def run(root: Path, case_id: str, credential_file: Path | None) -> dict:
    frozen = verify(root)
    require(case_id in IDS, 'unknown_case')
    require(not os.environ.get('MINDTHUS_HOST_API_KEY') and
            not os.environ.get('OPENROUTER_API_KEY'), 'forbidden_provider_present')
    p = cases.packets()[case_id]
    provider, executor, corrector = objects(p)
    old = os.environ.get('TYPESAFE_API_KEY')
    if credential_file:
        os.environ['TYPESAFE_API_KEY'] = credential(credential_file)
    try:
        result = entry.run(root / case_id, provider, p, REPO, mode=rc.MODE,
                           executor=executor, corrector=corrector,
                           live_admission=frozen['admissions'][case_id],
                           artifact_acceptor=Acceptor(root / case_id, p['authority']['owner_ref'])
                           if case_id == 'D1' else None)
    finally:
        if old is None:
            os.environ.pop('TYPESAFE_API_KEY', None)
        else:
            os.environ['TYPESAFE_API_KEY'] = old
    root.with_name(root.name + '-' + case_id + '-latest.json').write_bytes(canonical(result) + b'\n')
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('freeze', 'verify', 'run', 'submit'))
    parser.add_argument('--state-root', type=Path, required=True)
    parser.add_argument('--case', choices=IDS)
    parser.add_argument('--credential-file', type=Path)
    parser.add_argument('--host-response', type=Path)
    args = parser.parse_args()
    root = outside(args.state_root)
    if args.action == 'freeze':
        print(json.dumps({'freeze': digest(freeze(root)), 'model_calls': 0}))
        return
    verify(root)
    if args.action == 'verify':
        print(json.dumps({'verified': True, 'freeze': digest(read_record(freeze_path(root)))}))
        return
    require(args.case is not None, 'case_required')
    if args.action == 'submit':
        require(args.host_response is not None, 'host_response_required')
        receipt = submit_response(root / args.case, REPO,
                                  json.loads(args.host_response.read_bytes()))
        print(json.dumps({'case': args.case, 'receipt': receipt}))
        return
    result = run(root, args.case, args.credential_file)
    print(json.dumps({'case': args.case, 'status': result.get('status'),
                      'reason': result.get('reason'), 'counts': result.get('counts'),
                      'host_request': result.get('host_request'),
                      'route': result.get('route', {}).get('per_issue') if result.get('route') else None,
                      'relationship_action': result.get('relationship', {}).get('action')
                      if isinstance(result.get('relationship'), dict) else None},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
