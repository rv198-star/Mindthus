"""Two preregistered integration observations through public entry.run. No tuning.

Authored development inputs, not an independent benchmark. Exactly one Jev batch
and at most one max-effort CPA execution per case. Keys arrive over stdin, never
in shell command text or retained files. Completed records are reused.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys

REPO = Path('/srv/agentdock/projects/Mindthus')
sys.path.insert(0, str(REPO))
from experiments.typed_decision import entry, route_control as rc
from experiments.typed_decision.contracts import canonical, digest, provider_configuration
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json, no_secrets
from experiments.typed_decision.route_control_host import CPARouteHost
from experiments.typed_decision.session import implementation_digest, read_record, write_once

HERE = Path(__file__).resolve().parent
ROOT = Path('/srv/agentdock/tmp/mindthus-route-control-first-live-v1')
CASES = HERE / 'cases.json'
FREEZE = HERE / 'freeze.json'
AUTH = 'Owner approved implementation after route-control v0.2.1 review, DS4.1 Flash max required; bounded first integration only, 2026-09-23'


def save(path, value):
    if path.exists():
        assert read_record(path) == value, 'immutable_record_differs'
    else: write_once(path, value)


def configurations(packet):
    provider = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True, transport=deadline_post_json)
    host = CPARouteHost(packet['authority']['owner_ref'], REPO)
    return provider, host


def prepare():
    bundle, qs, bindings = rc.load_policy(REPO)
    specimens = json.loads(CASES.read_bytes())
    assert specimens['evidence_kind'] == 'authored_development_controls_not_holdout'
    assert len(specimens['cases']) == 2
    spec_hashes, admissions = {}, {}
    for specimen in specimens['cases']:
        packet = specimen['packet']; provider, host = configurations(packet)
        compiled = rc.compile_route(packet, REPO, bundle, qs, bindings)
        assert {s.kind for s in compiled.specs} == {'select', 'rate', 'assess_proposition'}
        key = specimen['id']
        admission = {'schema': 'mindthus.route-control-live.v1', 'mode': rc.MODE,
                     'root': str(ROOT / key), 'implementation': implementation_digest(),
                     'source_bindings': bundle['sources'], 'provider': provider_configuration(provider),
                     'packet_hashes': [digest(packet)], 'authorization_ref': AUTH,
                     'ceilings': {'judgments': 1, 'corrections': 0, 'organize': 0, 'arbitrations': 0,
                                  'executions': 1, 'requests': 1, 'reserve_per_jev_usd': .01},
                     'executor': host.configuration, 'arbitrator': None, 'corrector': None, 'organizer': None}
        rc._admission(admission, ROOT/key, packet, provider, bundle,
                      {'executor':host,'arbitrator':None,'corrector':None,'organizer':None})
        admissions[key] = admission
        spec_hashes[key] = digest([s.to_dict() for s in compiled.specs])
    freeze = {'source_commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
              'implementation': implementation_digest(), 'cases_sha256': hashlib.sha256(CASES.read_bytes()).hexdigest(),
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'request_specs_sha256': spec_hashes, 'admissions': admissions,
              'max_model_calls': 4, 'retries': 0, 'max_jev_reservation_usd': .02,
              'CPA_requested_reasoning_effort': 'max', 'actual_CPA_charges': 'unknown',
              'claims': 'integration only; no original-A comparison, native plugin activation, or all-method qualification'}
    save(FREEZE, freeze)
    print(json.dumps({'prepared':True,'max_calls':4,'cases':2,'source_commit':freeze['source_commit'],
                      'reasoning_effort':'max','calls_performed':0}))


def run():
    freeze = read_record(FREEZE)
    assert freeze['implementation'] == implementation_digest()
    assert freeze['cases_sha256'] == hashlib.sha256(CASES.read_bytes()).hexdigest()
    assert freeze['runner_sha256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    log = (Path('/srv/agentdock/tmp/route-control-implementation/full-regression.log')).read_text()
    assert re.search(r'^OK(?: \(skipped=\d+\))?$', log, re.M), 'full_regression_not_passed'
    specimens = json.loads(CASES.read_bytes())
    credentials = json.loads(sys.stdin.readline())
    names = ['TYPESAFE_API_KEY', 'MINDTHUS_HOST_API_KEY']
    assert set(credentials) == set(names) and all(credentials.values())
    assert not any(os.environ.get(n) for n in names), 'preexisting_credentials'
    summaries = []
    try:
        os.environ.update(credentials)
        for specimen in specimens['cases']:
            key = specimen['id']; packet = specimen['packet']; provider, host = configurations(packet)
            result = entry.run(ROOT/key, provider, packet, REPO, mode=rc.MODE, executor=host,
                               live_admission=freeze['admissions'][key])
            no_secrets(result)
            save(ROOT/(key+'-result.json'),result)
            summary = {'id':key,'counts':result['counts'],'reason':result['reason'],
                       'route':result['route']['per_issue'] if result['route'] else None,
                       'outputs':result['outputs'],'pending':result['pending'],'usage':result['usage']}
            summaries.append(summary)
            print(json.dumps(summary,ensure_ascii=False),flush=True)
            if result['reason'] or any('failed' in v for v in result['pending'].values()):
                print('terminal failure retained; remaining inputs are unrun',flush=True)
                break
        save(ROOT/'summary.json',{'freeze_sha256':digest(freeze),'cases':summaries,'qualification':False})
        paths = list(ROOT.rglob('*.json'))
        hits = []
        for path in paths:
            raw=path.read_text()
            if any(key in raw for key in credentials.values()):hits.append(str(path))
        assert not hits, 'credential_reflection_detected'
        print(json.dumps({'secret_scan_files':len(paths),'hits':hits,'completed_inputs':len(summaries)}),flush=True)
    finally:
        for name in names: os.environ.pop(name,None)
        credentials.clear()


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='run':run()
    else:raise SystemExit(2)
