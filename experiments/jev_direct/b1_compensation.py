"""Owner-approved, one-call B1 compensation; the named old remote request stays unknown."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,time
from experiments.typed_decision.contracts import require,digest
from experiments.typed_decision.relationship_runtime import save
from experiments.typed_decision.session import read_record,implementation_digest

OLD_KEY='61784cbf0798ceba12ce2b8dcf0c90a97799011df3848a5904ac0cc9f595a31c'
NAME='B1-compensation-successor.json'


def accepted(root, directory, intent):
    root=Path(root);directory=Path(directory)
    require(directory==root/'serial/000004','B1_exception_slot')
    x=read_record(directory/'accepted-unknown.json')
    require(read_record(root/'serial-bindings/000004/accepted-unknown.json')=={'sha256':digest(x)},'B1_exception_anchor')
    old=root/'runs/B1/direct/route/level-1/journal/calls'/OLD_KEY
    require(x['old_call_key']==OLD_KEY and x['status']=='risk_accepted_remote_unknown'
            and x['intent_sha256']==digest(intent)
            and intent['label']=='jev:'+str(old.parents[2])
            and x['business_intent_sha256']==digest(read_record(old/'intent.json'))
            and x['business_outcome_sha256']==digest(read_record(old/'outcome.json'))
            and x['successor_sha256']==digest(read_record(root/NAME)), 'B1_exception_binding')
    require(not (directory/'completion.json').exists() and not (old/'provider-receipt.json').exists(),'B1_old_unknown_changed')
    return x


def guard_label(root,label):
    root=Path(root)
    if (root/'remaining-nine-successor.json').exists():
        from .transport_profile import active
        scope=active(root)['dispatch_scope'];allowed=[]
        for case,arm in scope:
            allowed+=['host:'+str(root/'runs'/case/arm/'host'/str(n)) for n in range(4)]
            if arm=='direct':allowed+=['jev:'+str(root/'runs'/case/arm/'route'/level) for level in ('level-1','level-2')]
        require(label in allowed,'remaining_nine_dispatch_scope')
    elif (root/NAME).exists():
        allowed=['jev:'+str(root/'runs/B1/direct/route-compensation'/level) for level in ('level-1','level-2')]
        allowed+=['host:'+str(root/'runs/B1/direct/host'/str(n)) for n in range(4)]
        require(label in allowed,'B1_compensation_dispatch_scope')


def register(root):
    from . import pilot as p,transport_profile as t,router as r
    root=Path(root).resolve();f=p.verify_frozen_inputs(root);t.guard(root)
    parent=read_record(root/t.SCOPE_NAME)
    require(read_record(root/'remaining-five-scope-binding.json')=={'sha256':digest(parent)},'B1_parent_binding')
    require(all((root/k).is_file() and r.file_hash(root/k)==v for k,v in parent['historical_files'].items()),'B1_history_changed')
    require(sorted(q.name for q in (root/'serial').glob('[0-9]*'))==[f'{n:06d}' for n in range(5)],'B1_serial_count')
    require(not (root/'runs/B1/direct/route-compensation').exists() and not (root/'runs/B1/direct/host').exists(),'B1_compensation_already_started')
    old=root/'runs/B1/direct/route/level-1/journal/calls'/OLD_KEY
    outcome=read_record(old/'outcome.json');intent=read_record(root/'serial/000004/intent.json')
    require({v['reason'] for v in outcome['results'].values()}=={'ProviderError:transport_failure'},'B1_not_transport_failure')
    req=read_record(root/'runs/B1/direct/route/level-1/request.json');pack=r.load_pack(p.REPO)
    raw=next(c['raw'] for c in f['cases'] if c['id']=='B1')
    state=r.initial_state(raw,pack)
    require(req['state']==state and req['questions']==[q.to_dict() for q in r.questions(state,pack)],'B1_input_changed')
    x={**parent,'schema':'mindthus.B1-one-compensation.v1','parent_scope_sha256':digest(parent),
       'registered_at':datetime.now(timezone.utc).isoformat(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=p.REPO,text=True).strip(),
       'code_hashes':p.identity(p.REPO),'typed_decision_implementation':implementation_digest(),
       'dispatch_scope':[['B1','direct']],'historical_files':p.exact_tree(root),
       'owner_authorization':'Owner explicitly approved the proposed single B1 compensation after a583e8be03d6e19891539ce21748d31cfa3038be',
       'old_call_key':OLD_KEY,'original_layer1_state_sha256':digest(state),'original_questions_sha256':digest(req['questions']),
       'extra_jev_call_budget':1,'B1_jev_attempts_already_used':1,'B1_max_total_jev_attempts':3,
       'batch_jev_attempts_already_used':2,'batch_max_jev_attempts':f['max_jev_calls']+1,
       'new_layer1_attempts_max':1,'original_optional_layer2_allowance':1,
       'consumed_jev_business_calls':2,
       'risks_accepted':['possible duplicate computation and billing','old remote work may overlap new request'],
       'old_remote_terminal':'unknown','wait_proves_no_remote_overlap':False,
       'protocol_exception':'Named old call only; generation-scheduling.v2 otherwise unchanged. Local single sender and >=60s spacing; first usable return; no retry of a new unknown; no safety/permission refusal exception.'}
    save(root/NAME,x);save(root/'B1-compensation-successor-binding.json',{'sha256':digest(x)})
    disposition={'status':'risk_accepted_remote_unknown','old_call_key':OLD_KEY,'intent_sha256':digest(intent),
        'business_intent_sha256':digest(read_record(old/'intent.json')),'business_outcome_sha256':digest(outcome),
        'successor_sha256':digest(x),'local_disposition_at_epoch':time.time(),
        'remote_terminal':'unknown','is_completion':False}
    save(root/'serial/000004/accepted-unknown.json',disposition)
    save(root/'serial-bindings/000004/accepted-unknown.json',{'sha256':digest(disposition)})
    accepted(root,root/'serial/000004',intent)
    return t.active(root)
