"""Only the Owner-authorized #220 call 000049 disposition, 84/98 already spent.

Reuse run_batch transport, serial scheduling, terminal classification and stops.
The old unknown never acquires a completion. No other unknown is eligible.
"""
import importlib.util
import json
import hashlib
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('slim_batch_retry_parent',HERE/'run_batch.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PARENT_SHA='9a02be364a2c2d2a2c42a6d8c2b075a276d85fa2186fd11afb618824a52207c5'
REQUEST_SHA='7d23f927a8aab39835d0b5be90584405af7e27b2422a3a11c401b96d65df88c6'
UNKNOWN='runs/31-L02-gpt-6.1-sol-current/call-00'
CHILD='continuation-000049'
DISPOSITION='risk-disposition-000049.json'


def receipt(parent):
    parent=Path(parent).resolve();old=m.read(parent/'batch.json')
    if m.digest(old)!=PARENT_SHA:raise ValueError('not_named_000049_parent')
    m.validate_successor(parent,old)
    calls=sorted(parent.glob('runs/*/call-*/intent.json'))
    if len(calls)!=50:raise ValueError('parent_call_count_changed')
    if len(list(parent.glob('runs/*/call-*/terminal.json')))!=50:raise ValueError('parent_terminal_count_changed')
    evidence=[];spent=0
    for intent in calls:
        t=m.read(intent.with_name('terminal.json'));b=m.read(intent)
        named=intent.parent==parent/UNKNOWN
        if t['binding']!=b or b['simulation'] or t['status']!=('unknown' if named else 'returned'):
            raise ValueError('additional_or_mismatched_unknown')
        if named and b['request_sha256']!=REQUEST_SHA:raise ValueError('wrong_request')
        evidence.append({'path':str(intent.parent.relative_to(parent)),'intent':m.digest(b),'terminal':m.digest(t)})
        spent+=t['session_seconds']
    # Bind this exact recorded failure, including raw diagnostics, to the committed receipt.
    for name in ('intent.json','terminal.json','raw.json'):
        if (parent/UNKNOWN/name).read_bytes()!=(HERE/'isolated-batch-r1'/UNKNOWN/name).read_bytes():
            raise ValueError('named_failure_evidence_changed')
    if not m.dispatch_stopped(parent):raise ValueError('parent_stop_missing')
    if (parent/'scheduling/serial/000049/completion.json').exists():raise ValueError('unknown_must_remain_unknown')
    return dict(root=str(parent),batch_sha256=PARENT_SHA,logical_calls=50,
        earlier_calls=old['parent_receipt']['logical_calls'],evidence_sha256=m.digest(evidence),
        spent_session_seconds=spent,request_sha256=REQUEST_SHA)


def expected(parent,authorization,identity):
    parent=Path(parent).resolve();old=m.read(parent/'batch.json');r=receipt(parent)
    if authorization.get('execution_authorized') is not True or authorization.get('request_sha256')!=REQUEST_SHA:
        raise ValueError('named_authorization_required')
    if authorization.get('cumulative_call_limit')!=98 or authorization.get('technical_retries_max')!=1:
        raise ValueError('named_budget_or_retry_scope')
    if r['earlier_calls']!=34:raise ValueError('earlier_budget_changed')
    c=dict(old)
    c.update(retry_000049=r,authorization=authorization['authorization_ref'],
        retry_authorization=authorization,total_calls_max=98-34-50,
        active_processing_limit_seconds=old['active_processing_limit_seconds']-r['spent_session_seconds'],
        plan=old['plan'][31:],plan_start_index=31,prior_path_calls={'31':1},
        transition_wait_basis='60s_after_named_risk_acceptance_not_proof_of_remote_completion',
        budget_status='named_000049_retry_only_84_of_98_spent',**identity)
    return c


def validate(batch,config):
    parent=Path(config['retry_000049']['root']);batch=Path(batch).resolve()
    if batch!=parent/CHILD:raise ValueError('named_continuation_root_changed')
    identity={k:config[k] for k in ('binary_sha256','cli_version')}
    if config!=expected(parent,config['retry_authorization'],identity):raise ValueError('named_continuation_config_changed')
    d=m.read(parent/DISPOSITION)
    if d.get('status')!='risk_accepted_remote_unknown' or d.get('request_sha256')!=REQUEST_SHA:
        raise ValueError('named_disposition_missing')
    if d.get('continuation_sha256')!=m.digest(config) or d.get('continuation_root')!=str(batch):
        raise ValueError('named_disposition_binding_changed')
    if m.read(batch/'batch-binding.json')!={'sha256':m.digest(config)}:raise ValueError('named_batch_binding')


def prepare(parent,authorization):
    parent=Path(parent).resolve();batch=parent/CHILD
    old=m.read(parent/'batch.json');a=m.adapters(old['adapter_root'])
    with a['_locked'](m.driver_lock_path(parent,old)):
        if batch.exists() or (parent/DISPOSITION).exists():raise ValueError('named_retry_already_registered')
        identity=dict(binary_sha256=hashlib.sha256(Path(m.BINARY).read_bytes()).hexdigest(),
            cli_version=subprocess.check_output([m.BINARY,'--version'],text=True).strip())
        config=expected(parent,authorization,identity)
        # Same exact input, official provider, model, effort and material bytes.
        m.write(batch/'batch.json',config);m.write(batch/'batch-binding.json',{'sha256':m.digest(config)})
        for relative in ('inputs.json','sources/current.json','sources/slim.json'):
            source=m.read(parent/relative);m.write(batch/relative,source)
        m.write(parent/DISPOSITION,dict(status='risk_accepted_remote_unknown',request_sha256=REQUEST_SHA,
            serial_slot='000049',local_disposition_at_epoch=time.time(),remote_completion=None,
            authority=authorization,continuation_root=str(batch),continuation_sha256=m.digest(config),
            previous_calls=84,remaining_calls=14,old_completion_created=False))
        validate(batch,config)
    return batch


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['prepare','run'])
    parser.add_argument('parent');parser.add_argument('--authorization');args=parser.parse_args()
    if args.operation=='prepare':print(prepare(args.parent,m.read(args.authorization)))
    else:m.drive(Path(args.parent).resolve()/CHILD)
