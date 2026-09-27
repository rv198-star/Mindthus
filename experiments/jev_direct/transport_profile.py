"""Forward-only experiment profile; leaves historical freezes and outcomes intact."""
from pathlib import Path
import json
import re
import subprocess
from datetime import datetime, timezone
from experiments.typed_decision.contracts import digest, require
from experiments.typed_decision.relationship_runtime import save
from experiments.typed_decision.session import read_record, RecoveryRequired

BASE = Path(__file__).resolve().parents[2]
DOC = BASE/'docs/internal/research/typed-decision/jev-direct-v2'
CANDIDATE = DOC/'host-transport-boundary-2026-09-27/candidate-profile.json'
PROTOCOL = DOC/'a1-direct-transport-v2/PROTOCOL.json'
NAME = 'transport-successor-v2.json'


def register(root):
    from . import pilot as p
    from .serial import SerialRequests
    root = Path(root).resolve(); f = p.verify_frozen_inputs(root)
    SerialRequests(root/'serial').validate()
    native = p.unseal(root/'technical-retry/A1/native')
    require(native['status'] == 'delivered' and native['total_host_attempts'] == 2,
            'transport_native_history_required')
    require(native['host_evidence_sha256'] == digest(p.exact_tree(root/'runs/A1/native/host')),
            'transport_native_evidence_changed')
    require(not (root/'runs/A1/direct').exists(), 'transport_direct_already_started')
    candidate = json.loads(CANDIDATE.read_text()); protocol = json.loads(PROTOCOL.read_text())
    require(digest(candidate['candidate_overrides']) == candidate['overrides_sha256'], 'transport_candidate_changed')
    prior = read_record(root/'technical-successor.json')
    require(digest(f) == candidate['parent_freeze_sha256'] and
            digest(prior) == candidate['parent_technical_successor_sha256'], 'transport_parent_changed')
    historical = p.exact_tree(root)
    value = {'schema':'mindthus.transport-successor.v2','root':str(root),
        'registered_at':datetime.now(timezone.utc).isoformat(),
        'parent_freeze_sha256':digest(f),'parent_technical_successor_sha256':digest(prior),
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
        'code_hashes':p.identity(BASE),'candidate_sha256':digest(candidate),
        'protocol':protocol,'protocol_sha256':digest(protocol),
        'overrides':candidate['candidate_overrides'],'overrides_sha256':candidate['overrides_sha256'],
        'applies_to':['native','direct'],'dispatch_scope':[['A1','direct']],
        'historical_files':historical,'budgets_reset':False,
        'consumed_host_cli':{'A1/native':2,'A1/direct':0},
        'native_remaining_host_cli':2,'native_remaining_seconds':f['max_host_seconds_per_arm']-prior['previous_budget_debit_seconds']-native['new_host_session_seconds'],
        'direct_remaining_host_cli':f['max_host_calls_per_arm'],
        'direct_remaining_seconds':f['max_host_seconds_per_arm'],
        'historical_underlying_requests':None,'performance_matched_to_old_native':False}
    save(root/NAME,value); save(root/'transport-successor-v2-binding.json',{'sha256':digest(value)})
    return value


def active(root):
    from . import pilot as p
    root = Path(root)
    if not (root/NAME).exists():return None
    x = read_record(root/NAME)
    require(read_record(root/'transport-successor-v2-binding.json') == {'sha256':digest(x)}, 'transport_binding_changed')
    candidate=json.loads(CANDIDATE.read_text());protocol=json.loads(PROTOCOL.read_text())
    require(x['root']==str(root.resolve()) and x['code_hashes']==p.identity(BASE)
            and x['parent_freeze_sha256']==digest(read_record(root/'freeze.json'))
            and x['candidate_sha256']==digest(candidate)
            and x['overrides']==candidate['candidate_overrides']
            and x['overrides_sha256']==digest(x['overrides'])
            and x['protocol']==protocol and x['protocol_sha256']==digest(protocol), 'transport_identity_changed')
    require(all((root/k).is_file() and p.r.file_hash(root/k)==v for k,v in x['historical_files'].items()),
            'transport_history_changed')
    return x


def guard(root):
    if (Path(root)/'transport-stop-v2.json').exists():
        raise RecoveryRequired('transport_unclassified_recovery_stop')


def observe(root, directory, proc, intent):
    """Observable log counts, never inferred HTTP totals. Ambiguous resend stops later work.

    Normal official auth recovery remains enabled. Any observed recovery lacking a
    bound 401/non-acceptance record is left for evidence reconciliation, not guessed.
    """
    text=proc.stdout+'\n'+proc.stderr
    sampling=len(re.findall(r'retrying sampling request', text, re.I))
    reconnect=len(re.findall(r'Reconnecting\.\.\.', text))
    auth=len(re.findall(r'auth_recovery|recovery_succeeded|\b401\b', text, re.I))
    fallback=len(re.findall(r'falling back|fallback|prewarm', text, re.I))
    uncertain=bool(sampling or reconnect or auth or fallback)
    x={'schema':'mindthus.invocation-transport-observation.v2',
       'request_sha256':intent['request_sha256'],'transport_successor_sha256':intent['transport_successor_sha256'],
       'outer_driver_retries':0,'cli_starts':1,'sampling_retry_log_count':sampling,
       'reconnect_notice_count':reconnect,'auth_or_401_log_count':auth,'fallback_or_prewarm_log_count':fallback,
       'actual_underlying_request_count':None,'generation_attempt_count':None,
       'connection_recovery_seconds':None,'authentication_recovery_seconds':None,
       'observation':'unclassified_recovery_requires_reconciliation' if uncertain else 'no_recovery_observed',
       'no_recovery_observed_is_not_zero_http_proof':True,
       'stop_subsequent_dispatch':uncertain}
    save(Path(directory)/'transport-observation-v2.json',x)
    if uncertain:save(Path(root)/'transport-stop-v2.json',{'host_directory':str(directory),'observation_sha256':digest(x)})
    return x
