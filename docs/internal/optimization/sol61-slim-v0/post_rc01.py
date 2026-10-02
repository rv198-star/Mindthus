"""Owner-authorized RC01 regression only: 40 paths, 120 new calls, no retry.

Reuse the existing driver/transport/serial ledger. Old 98 calls and the named
historical unknown remain intact; this admission cannot dispose of a new unknown.
"""
import hashlib
import importlib.util
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('post_rc01_driver', HERE / 'run_batch.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
BASELINE = 'e7dbb473e955932f09c80dfb48b90ac1f4f8db43'
CANDIDATE = '131ab6e4d7b04e3964193dc95c869f6eaad16730'
AUTH_FILE = HERE / 'post-rc01-regression' / 'admission.json'
CLAIM = 'post-rc01-regression-binding.json'


def plan():
    cases = m.read(HERE / 'cases.json')['business_cases']
    rows = m.plan(cases)[:32]
    for n, key in enumerate(('F01', 'F02', 'W01', 'W02')):
        for arm in (('current', 'slim') if n % 2 == 0 else ('slim', 'current')):
            rows.append(dict(case=key, arm=arm, model='gpt-6-astra'))
    return rows


def receipt(previous):
    previous = Path(previous).resolve(); old = m.read(previous / 'batch.json')
    if not old.get('retry_000049') or old.get('simulation') is not False:
        raise ValueError('post_rc01_requires_completed_previous_batch')
    m.validate_successor(previous, old)
    if m.dispatch_stopped(previous): raise ValueError('previous_batch_stopped')
    evidence = []
    for intent in sorted(previous.glob('runs/*/call-*/intent.json')):
        binding = m.read(intent); terminal = m.read(intent.with_name('terminal.json'))
        if terminal['binding'] != binding or binding['simulation'] or terminal['status'] != 'returned':
            raise ValueError('previous_unresolved_call')
        evidence.append(dict(intent=m.digest(binding), terminal=m.digest(terminal)))
    if len(evidence) != 14 or old['retry_000049']['logical_calls'] + old['retry_000049']['earlier_calls'] != 84:
        raise ValueError('previous_cost_changed')
    results = list(previous.glob('runs/*/result.json'))
    if len(results) != 13 or any(m.read(p)['status'] != 'delivered' for p in results):
        raise ValueError('previous_paths_incomplete')
    m.adapters(old['adapter_root'])['SerialRequests'](previous / 'scheduling/serial').validate()
    return dict(root=old['parent_receipt']['root'], previous_root=str(previous), logical_calls=98,
        previous_batch_sha256=m.digest(old), evidence_sha256=m.digest(evidence),
        historical_unknown=dict(request_sha256=old['retry_000049']['request_sha256'],
            status='risk_accepted_remote_unknown', remote_completion=None))


def expected(previous, authority, identity):
    if authority != m.read(AUTH_FILE) or authority.get('execution_authorized') is not True:
        raise ValueError('post_rc01_explicit_authority_required')
    if (authority.get('new_calls_max'), authority.get('historical_calls'), authority.get('cumulative_calls_max'),
        authority.get('path_calls_max'), authority.get('technical_retries_max'), authority.get('baseline'),
        authority.get('candidate')) != (120, 98, 218, 3, 0, BASELINE, CANDIDATE):
        raise ValueError('post_rc01_scope_or_budget_changed')
    frozen = m.read(HERE / 'freeze.json')
    for name, sha in frozen['source_files'].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != sha:
            raise ValueError('T0_changed:' + name)
    old = m.read(Path(previous) / 'batch.json'); parent = receipt(previous)
    # Carry the same execution contract, not the exhausted allowance/retry fields.
    keys = ('adapter_pin', 'adapter_root', 'workspace_mode', 'admission', 'host_timeout',
        'active_processing_limit_seconds', 'effort', 'transport_overrides',
        'transport_overrides_sha256', 'overrides', 'isolation', 'protocol', 'protocol_sha256',
        'inputs_sha256', 'evidence_scope')
    c = {k: old[k] for k in keys}
    c.update(schema='mindthus.slim-post-rc01.v1', simulation=False, post_rc01_regression=True,
        baseline=BASELINE, candidate=CANDIDATE, parent_receipt=parent,
        successor_admission=dict(execution_authorized=True, cumulative_call_limit=218),
        regression_admission=authority, authorization=authority['authorization_ref'],
        total_calls_max=120, path_calls_max=3, active_processing_limit_seconds=7200,
        budget_status='120_new_calls_plus_98_preserved_historical', plan=plan(),
        arm_labels=dict(current='RC01', slim='post-RC01 candidate'),
        source_sha256={arm: m.digest(m.materials(sha)) for arm, sha in [('current', BASELINE), ('slim', CANDIDATE)]},
        transition_wait_basis='60s_after_confirmed_previous_terminal; historical accepted unknown not proven complete',
        **identity)
    return c


def validate(batch, config):
    parent = config['parent_receipt']; previous = parent['previous_root']
    identity = {k: config[k] for k in ('binary_sha256', 'cli_version')}
    if config != expected(previous, config['regression_admission'], identity):
        raise ValueError('post_rc01_configuration_changed')
    claim = m.read(Path(parent['root']) / CLAIM)
    if claim != m.successor_record(batch, config):
        raise ValueError('post_rc01_root_or_binding_changed')
    if m.read(Path(batch) / 'batch-binding.json') != dict(sha256=m.digest(config)):
        raise ValueError('post_rc01_batch_binding_changed')


def prepare(batch, previous):
    batch = Path(batch).resolve(); previous = Path(previous).resolve()
    old = m.read(previous / 'batch.json'); a = m.adapters(old['adapter_root'])
    with a['_locked'](m.driver_lock_path(previous, old)):
        if batch.exists(): raise ValueError('fresh_batch_required')
        claim = Path(old['parent_receipt']['root']) / CLAIM
        if claim.exists(): raise ValueError('post_rc01_allowance_already_bound')
        identity = dict(binary_sha256=hashlib.sha256(Path(m.BINARY).read_bytes()).hexdigest(),
            cli_version=subprocess.check_output([m.BINARY, '--version'], text=True).strip())
        c = expected(previous, m.read(AUTH_FILE), identity)
        m.write(batch / 'batch.json', c); m.write(batch / 'batch-binding.json', dict(sha256=m.digest(c)))
        m.write(batch / 'inputs.json', m.read(previous / 'inputs.json'))
        for arm, sha in [('current', BASELINE), ('slim', CANDIDATE)]:
            m.write(batch / 'sources' / (arm + '.json'), m.materials(sha))
        m.write(claim, m.successor_record(batch, c))
        validate(batch, c)
    return batch


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument('operation', choices=['prepare', 'run'])
    parser.add_argument('batch'); parser.add_argument('--previous'); args = parser.parse_args()
    if args.operation == 'prepare': print(prepare(args.batch, args.previous))
    else: m.drive(args.batch)
