"""Owner disposition for one named timeout; continue nine unsent paths, no replay."""
from pathlib import Path
import subprocess,time
from . import runtime as rt
from .read_contract_successor import REPO,RUNNER
from experiments.typed_decision.contracts import digest,require
from experiments.typed_decision.relationship_runtime import _locked,save
from experiments.typed_decision.session import read_record,RecoveryRequired
from experiments.jev_direct.serial import SerialRequests

BATCH='d91af49c938602c289608fa61e3a0eb4b1fa4e0ddc44b6c7adef3cc26a2ec8ff'
REQUEST='3f5d271f948d80feb91dc7083080d48a05a69fafda03c020cf3ba8aba1f38c5c'
KEY='record-source-1-B:1'
NAME='risk-accepted-000047.json'
PATHS=['record-source-2-B','record-source-2-A','record-source-2-C',
       'skills-scope-1-A','skills-scope-1-B','skills-scope-1-C',
       'skills-scope-2-C','skills-scope-2-B','skills-scope-2-A']


def parent_snapshot(root):
    x=rt.read(root/'read-contract-successor.json')
    require(x['batch_sha256']==BATCH and x['kind']=='read_contract_sending_clarification','named_47_parent')
    require(digest((REPO/RUNNER).read_text())==x['runner_sha256'],'named_47_runner_changed')
    for p,h in x['preserved'].items():require(digest(rt.read(root/p))==h,'named_47_parent_history')
    return x


def verified(root):
    root=Path(root);x=rt.read(root/NAME)
    require(digest(rt.read(root/'batch.json'))==BATCH==x['batch_sha256'],'named_47_batch')
    require(x['request_sha256']==REQUEST and x['call_key']==KEY and x['retry_call_key'] is None
            and x['allowed_paths']==PATHS,'named_47_scope')
    require({p.name for p in root.glob('STOP*.json')}=={'STOP.json','STOP-000047.json'},'named_47_new_stop')
    parent_snapshot(root)
    for p,h in x['preserved'].items():require(digest(rt.read(root/p))==h,'named_47_history')
    require(rt.read(root/'calls/000047/terminal.json')['status']=='unknown'
            and not (root/'serial/000047/completion.json').exists(),'named_47_no_completion')
    s=rt.state(root/'runs/record-source-1-B')
    require(s['stopped']=='unknown' and s['call_count']==2 and s['draft'] is None,'named_47_no_replay')
    return x


def accepted(root,directory,intent):
    root=Path(root);x=verified(root)
    require(directory==root/'serial/000047' and intent['label']==KEY,'named_47_slot_only')
    end=read_record(directory/'accepted-unknown.json')
    require(read_record(root/'serial/bindings/000047/accepted-unknown.json')=={'sha256':digest(end)},'named_47_anchor')
    require(end['intent_sha256']==digest(intent) and end['successor_sha256']==digest(x)
            and end['status']=='risk_accepted_remote_unknown','named_47_binding')
    return end


def register(root):
    root=Path(root)
    with _locked(root/'.execution.lock'),_locked(root/'.dispatch.lock'):
        require(not (root/NAME).exists(),'named_47_already_registered')
        config=rt.read(root/'batch.json');require(digest(config)==BATCH,'named_47_batch')
        parent=parent_snapshot(root)
        require({p.name for p in root.glob('STOP*.json')}=={'STOP.json','STOP-000047.json'},'named_47_stop_scope')
        dirs=sorted((root/'calls').iterdir());require([p.name for p in dirs]==[f'{i:06d}' for i in range(48)],'named_47_48_debits')
        for d in dirs:
            terminal=rt.read(d/'terminal.json');binding=rt.read(d/'binding.json')
            require(terminal['binding']==binding==rt.read(d/'raw.json')['binding'],'named_47_terminal_binding')
            require((d/'import.json').exists(),'named_47_import_required')
            if d.name!='000047':require(terminal['status']=='returned','named_47_other_unknown')
        req=rt.read(dirs[-1]/'request.json');terminal=rt.read(dirs[-1]/'terminal.json')
        require(req['request_sha256']==REQUEST and req['role']=='host' and req['phase']=='draft'
                and terminal['binding']['call_key']==KEY and terminal['status']=='unknown'
                and terminal['error']=='TimeoutExpired','named_47_timeout_only')
        require(rt.read(root/'STOP-000047.json')=={'call_key':KEY,'reason':'unknown','terminal_sha256':digest(terminal)},'named_47_stop_binding')
        try:SerialRequests(root/'serial').validate()
        except RecoveryRequired as exc:require(str(exc)=='serial_unknown_request_no_resubmit','named_47_serial_failure')
        else:require(False,'named_47_requires_unknown')
        require(read_record(root/'serial/000047/intent.json')['label']==KEY,'named_47_serial_key')
        eligible={p.name for p in (root/'runs').iterdir() if not rt.state(p)['stopped'] and rt.state(p)['phase']!='done'}
        require(eligible==set(PATHS) and all(rt.state(root/'runs'/p)['call_count']==0 for p in PATHS),'named_47_unsent_scope')
        source=parent['source_sha256'];changed={p for p,h in source.items() if digest((REPO/p).read_text())!=h}
        require(changed=={'experiments/grounded_judgment/resume_000007.py','experiments/grounded_judgment/dispatch.py'},'named_47_minimal_source')
        source={p:digest((REPO/p).read_text()) for p in source}
        source[str(Path(__file__).resolve().relative_to(REPO))]=digest(Path(__file__).read_text())
        preserved={str(p.relative_to(root)):digest(rt.read(p)) for folder in ('calls','serial','runs') for p in (root/folder).rglob('*.json')}
        for name in ('STOP.json','STOP-000047.json','read-contract-successor.json'):preserved[name]=digest(rt.read(root/name))
        x={'kind':'named_unknown_000047_continuation','status':'risk_accepted_remote_unknown',
           'batch_sha256':BATCH,'request_sha256':REQUEST,'call_key':KEY,'retry_call_key':None,
           'allowed_paths':PATHS,'source_sha256':source,'preserved':preserved,
           'parent_successor_sha256':digest(parent),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
           'local_disposition_at_epoch':time.time(),'wait_proves_remote_completion':False,
           'authority':'Owner accepts specified 000047 remaining remote compute/billing/overlap risk and continuing nine unsent paths; no replay.',
           'owner_budget_comment':'2–3x overrun can be accepted with control/explanation; this continuation retains existing 176/144/32 caps, currently sufficient.',
           'limits':config['admission']['total_limits'],'budgets_reset':False,'prior_calls':48}
        rt.write(root/NAME,x)
        end={'status':'risk_accepted_remote_unknown','intent_sha256':digest(read_record(root/'serial/000047/intent.json')),
             'successor_sha256':digest(x),'local_disposition_at_epoch':x['local_disposition_at_epoch']}
        save(root/'serial/000047/accepted-unknown.json',end)
        save(root/'serial/bindings/000047/accepted-unknown.json',{'sha256':digest(end)})
        from .resume_000007 import NamedSerial
        NamedSerial(root/'serial').validate()
        return verified(root)
