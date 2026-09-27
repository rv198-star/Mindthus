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
SCOPE_NAME = 'remaining-five-scope.json'
REMAINING = [(case, arm) for case, arms in [('B1',('direct','native')),('C1',('native','direct')),('D1',('direct','native')),('E-window',('native','direct')),('F-window',('direct','native'))] for arm in arms]


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
    if (root/SCOPE_NAME).exists():
        parent=x; x=read_record(root/SCOPE_NAME)
        require(read_record(root/'remaining-five-scope-binding.json')=={'sha256':digest(x)}
                and x['parent_transport_successor_sha256']==digest(parent)
                and x['dispatch_scope']==[list(pair) for pair in REMAINING], 'transport_scope_binding_changed')
    from .b1_compensation import NAME as compensation_name
    if (root/compensation_name).exists():
        parent=x; x=read_record(root/compensation_name)
        from experiments.typed_decision.session import implementation_digest
        require(read_record(root/'B1-compensation-successor-binding.json')=={'sha256':digest(x)}
                and x['parent_scope_sha256']==digest(parent) and x['dispatch_scope']==[['B1','direct']]
                and x['typed_decision_implementation']==implementation_digest(), 'B1_successor_changed')
    if (root/'remaining-nine-successor.json').exists():
        parent=x; x=read_record(root/'remaining-nine-successor.json')
        require(read_record(root/'remaining-nine-successor-binding.json')=={'sha256':digest(x)}
                and x['parent_compensation_successor_sha256']==digest(parent)
                and x['dispatch_scope']==[list(pair) for pair in REMAINING if pair!=('B1','direct')]
                and x['extra_compensation_calls_remaining']==0, 'remaining_nine_binding')
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


def register_remaining(root):
    """Append the owner's B–F authorization; no old freeze, scope or debit rewrite."""
    from . import pilot as p
    from .serial import SerialRequests
    root=Path(root).resolve();p.verify_frozen_inputs(root);guard(root)
    SerialRequests(root/'serial').validate()
    parent=read_record(root/NAME)
    require(read_record(root/'transport-successor-v2-binding.json')=={'sha256':digest(parent)},'transport_parent_binding')
    require(all((root/k).is_file() and p.r.file_hash(root/k)==v for k,v in parent['historical_files'].items()),'transport_history_changed')
    native=p.unseal(root/'technical-retry/A1/native');direct=p.unseal(root/'runs/A1/direct')
    require(native['status']==direct['status']=='delivered','scope_A1_not_delivered')
    require(native['host_evidence_sha256']==digest(p.exact_tree(root/'runs/A1/native/host')),'scope_native_history_changed')
    require(not any((root/'runs'/case/arm).exists() for case,arm in REMAINING),'scope_remaining_already_started')
    x={**parent,'schema':'mindthus.remaining-five-scope.v1',
       'parent_transport_successor_sha256':digest(parent),
       'registered_at':datetime.now(timezone.utc).isoformat(),
       'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
       'code_hashes':p.identity(BASE),'dispatch_scope':[list(pair) for pair in REMAINING],
       'scope_authority':'Current owner instruction: run the ten B1–F paths in this order under generation-scheduling.v2; prior A1-only record remains historical',
       'historical_files':p.exact_tree(root),
       'consumed_host_cli':{'A1/native':2,'A1/direct':1,**{c+'/'+a:0 for c,a in REMAINING}},
       'consumed_jev_business_calls':1,'direct_remaining_host_cli':3,
       'direct_remaining_seconds':900-direct['host_seconds'],
       'remaining_path_budgets':{c+'/'+a:{'host_calls':4,'host_seconds':900,'jev_layers':2 if a=='direct' else 0} for c,a in REMAINING}}
    save(root/SCOPE_NAME,x);save(root/'remaining-five-scope-binding.json',{'sha256':digest(x)})
    return active(root)


def register_nine(root):
    from . import pilot as p,b1_compensation as b
    from .serial import SerialRequests
    root=Path(root).resolve();f=p.verify_frozen_inputs(root);guard(root)
    SerialRequests(root/'serial').validate()
    parent=read_record(root/b.NAME)
    require(read_record(root/'B1-compensation-successor-binding.json')=={'sha256':digest(parent)},'nine_parent_binding')
    require(all((root/k).is_file() and p.r.file_hash(root/k)==v for k,v in parent['historical_files'].items()),'nine_history_changed')
    require(p.unseal(root/'runs/B1/direct')['status']=='delivered','nine_B1_not_delivered')
    scope=[list(pair) for pair in REMAINING if pair!=('B1','direct')]
    require(not any((root/'runs'/c/a).exists() for c,a in scope),'nine_path_already_started')
    x={**parent,'schema':'mindthus.remaining-nine.v1','parent_compensation_successor_sha256':digest(parent),
       'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
       'registered_at':datetime.now(timezone.utc).isoformat(),'code_hashes':p.identity(BASE),
       'dispatch_scope':scope,'historical_files':p.exact_tree(root),
       'owner_authorization':'Explicit continuation after d3a58c613: B1/native; C1 native/direct; D1 direct/native; E-window native/direct; F-window direct/native.',
       'extra_compensation_calls_remaining':0,'consumed_jev_business_calls':3,
       'consumed_host_cli':{'A1/native':2,'A1/direct':1,'B1/direct':1,**{c+'/'+a:0 for c,a in scope}},
       'new_layer1_attempts_max':0,
       'new_layer1_attempts_max_scope':'No additional B1 technical compensation; untouched paths retain original normal first/optional-second layers',
       'known_old_risk_continues':True,'new_unknown_exception':False}
    save(root/'remaining-nine-successor.json',x);save(root/'remaining-nine-successor-binding.json',{'sha256':digest(x)})
    return active(root)
