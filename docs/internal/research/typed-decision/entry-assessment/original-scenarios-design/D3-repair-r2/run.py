"""One frozen D3 invocation harness: calls public entry.run, never duplicates its graph."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
sys.path.insert(0, str(REPO))
from experiments.typed_decision import entry, relationship_assessment as rel, relationship_runtime as rt, relationship_live as live
from experiments.typed_decision.contracts import canonical, digest, provider_configuration, require
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.session import implementation_digest, read_record, write_once

ROOT = Path('/srv/agentdock/tmp/mindthus-relationship-D3-repair-r2')
FREEZE = HERE / 'freeze.json'
OWNER = 'cpa:deepseek-v4.1-flash:relationship-owner'
AUTH = 'Owner authorizes internal repair through actual tests; D3-repair-r2/protocol.md'
SOURCES = ['entry.py', 'relationship_runtime.py', 'relationship_live.py', 'relationship_assessment.py',
           'contracts.py', 'providers.py', 'session.py']


def cases():
    return json.loads((HERE / 'cases.json').read_bytes())


def file_hashes():
    paths = [REPO / 'experiments/typed_decision' / p for p in SOURCES]
    paths += [REPO / rel.CONTRACT, HERE / 'run.py', HERE / 'protocol.md', HERE / 'cases.json']
    return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def prepare():
    require(not FREEZE.exists(), 'freeze_already_exists')
    provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True, transport=live.deadline_post_json)
    host, org = live.CPAHost(OWNER, REPO), live.CPAHost(OWNER, REPO, organizer=True)
    contract, _ = rel.load_contract(REPO)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    admissions = {}
    for episode in cases()['episodes']:
        templates = episode['inputs']
        n = len(templates)
        organize = any(it['packet']['proposal'] is None for it in templates.values())
        admissions[episode['id']] = {
            'schema': live.SCHEMA, 'authorization_ref': AUTH, 'source_commit': commit,
            'implementation': implementation_digest(), 'contract_sha256': digest(contract),
            'profile_sha256': digest(rt.PROFILE), 'mode': rt.MODE,
            'root': str(ROOT / 'episodes' / episode['id']),
            'episode_id': next(iter(templates.values()))['packet']['episode_id'],
            'provider': provider_configuration(provider), 'corrector': host.configuration,
            'organizer': org.configuration if organize else None,
            'input_templates': templates, 'recheck': True,
            'ceilings': {'requests': 3*n + int(organize), 'judgments': 2*n, 'corrections': n,
                         'organize': int(organize), 'reserve_per_jev_usd': .01}}
    payload = {'schema': 'mindthus.relationship-D3-freeze.v1', 'source_commit': commit,
               'files': file_hashes(), 'admissions': admissions, 'root': str(ROOT),
               'order': [e['id'] for e in cases()['episodes']], 'new_question_revisions': 0,
               'retries': 0, 'max_judgments': 2*sum(len(e['inputs']) for e in cases()['episodes']),
               'max_corrections': sum(len(e['inputs']) for e in cases()['episodes']),
               'max_organizers': sum(any(x['packet']['proposal'] is None for x in e['inputs'].values()) for e in cases()['episodes']),
               'sampling': cases()['sampling'], 'qualification': False}
    FREEZE.write_bytes(canonical(payload) + b'\n')
    print(json.dumps({'freeze_sha256': digest(payload), 'admitted_turns': sum(len(e['inputs']) for e in cases()['episodes']), 'model_calls': 0}))


def preflight():
    frozen = json.loads(FREEZE.read_bytes())
    require(frozen['files'] == file_hashes() and frozen['root'] == str(ROOT), 'frozen_sources_or_root_changed')
    require(frozen['order'] == [e['id'] for e in cases()['episodes']], 'frozen_order_changed')
    host, org = live.CPAHost(OWNER, REPO), live.CPAHost(OWNER, REPO, organizer=True)
    provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True, transport=live.deadline_post_json)
    for admission in frozen['admissions'].values():
        for tid, it in admission['input_templates'].items():
            packet = it['packet']
            rt._raw_validate(packet, rel.load_contract(REPO)[0])
            if packet['proposal'] is not None:
                rel.compile_packet(packet, REPO)
            require(admission['corrector'] == host.configuration, 'host_config_drift')
            require(admission['provider'] == provider_configuration(provider), 'provider_config_drift')
            if admission['organizer']: require(admission['organizer'] == org.configuration, 'organizer_drift')
    return frozen


def run():
    frozen = preflight()
    require(bool(os.environ.get('TYPESAFE_API_KEY')) and bool(os.environ.get('MINDTHUS_HOST_API_KEY')),
            'missing_credentials')
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (ROOT / '.campaign-lock').open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (ROOT / 'summary.json').exists():
            print(json.dumps({'already_terminal': True, 'summary': str(ROOT / 'summary.json')})); return
        manifest = {'freeze_sha256': digest(frozen), 'source_commit': frozen['source_commit']}
        rt.save(ROOT / 'manifest.json', manifest)
        rows, stop = [], None
        for eid in frozen['order']:
            adm = frozen['admissions'][eid]
            provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True, transport=live.deadline_post_json)
            host = live.CPAHost(OWNER, REPO)
            org = live.CPAHost(OWNER, REPO, organizer=True) if adm['organizer'] else None
            for tid in adm['input_templates']:
                packet = live.resolve_input(adm, tid)
                result = entry.run(Path(adm['root']), provider, packet, REPO, mode=rt.MODE,
                                   corrector=host, organizer=org, recheck=True, live_admission=adm)
                row = {'episode': eid, 'turn': tid, 'status': result['status'], 'reason': result['reason'],
                       'action': result['action'], 'scope_acceptance': result.get('scope_acceptance'),
                       'source_ref': result['source_ref'], 'final_text': live.output_text(result),
                       'episode_counts': result['episode_counts'], 'task_complete': result['task_complete']}
                rows.append(row)
                print(json.dumps({k: v for k, v in row.items() if k not in ('final_text', 'source_ref')}, ensure_ascii=False), flush=True)
                with rt.Episode(Path(adm['root']), REPO, provider, packet, rel.load_contract(REPO)[0], adm) as ep:
                    state = ep.tally()
                if state['failures']:
                    stop = {'episode': eid, 'turn': tid, 'reason': 'terminal_technical_failure', 'records': state['failures']}
                    break
            if stop: break
        summary = {'schema': 'mindthus.relationship-D3-observation.v1', 'freeze_sha256': digest(frozen),
                   'source_commit': frozen['source_commit'], 'rows': rows, 'stop': stop,
                   'planned_turns': sum(len(e['inputs']) for e in cases()['episodes']), 'completed_turns': len(rows), 'qualification': False,
                   'sampling': frozen['sampling'], 'review': 'author_review_pending'}
        write_once(ROOT / 'summary.json', summary)
        print(json.dumps({'completed_turns': len(rows), 'stop': stop, 'summary': str(ROOT / 'summary.json')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'preflight', 'run'])
    args = parser.parse_args()
    if args.action == 'prepare': prepare()
    elif args.action == 'preflight':
        preflight(); print('D3 frozen sources/input/templates PASS; zero model calls')
    else: run()
