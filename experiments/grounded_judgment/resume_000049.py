"""One named SSE draft compensation; existing unknowns stay unknown."""
from pathlib import Path
import subprocess,time
from . import runtime as rt, resume_000047 as parent47
from .read_contract_successor import REPO
from experiments.typed_decision.contracts import digest,require
from experiments.typed_decision.relationship_runtime import _locked,save
from experiments.typed_decision.session import read_record,RecoveryRequired
from experiments.jev_direct.serial import SerialRequests

BATCH=parent47.BATCH
REQUEST='0817e559b299453a5902667c85da2e69ec5b3280eb0bee4c66d0b2d35b4a800a'
KEY='record-source-2-B:1'
NAME='retry-000049.json'
STOPS={'STOP.json','STOP-000047.json','STOP-000049.json'}


def binding(root,directory,intent,x):
    slot=directory.name
    require(slot in ('000047','000049'),'named_49_slot_only')
    expected=parent47.KEY if slot=='000047' else KEY
    require(intent['label']==expected,'named_49_label')
    end=read_record(directory/'accepted-unknown.json')
    require(read_record(root/'serial/bindings'/slot/'accepted-unknown.json')=={'sha256':digest(end)},'named_49_anchor')
    require(end['intent_sha256']==digest(intent) and end['successor_sha256']==digest(x)
            and end['status']=='risk_accepted_remote_unknown','named_49_binding')
    return end


def verified(root):
    root=Path(root);x=rt.read(root/NAME)
    require(digest(rt.read(root/'batch.json'))==BATCH==x['batch_sha256'],'named_49_batch')
    require(x['request_sha256']==REQUEST and x['call_key']==KEY
            and x['retry_call_key']=='record-source-2-B:2' and x['retry_limit']==1
            and x['compensates_local_call']=='000049' and x['allowed_paths']==parent47.PATHS
            and x['path_limits']=={'record-source-2-B':8},'named_49_scope')
    require({p.name for p in root.glob('STOP*.json')}==STOPS,'named_49_new_stop')
    for p,h in x['preserved'].items():require(digest(rt.read(root/p))==h,'named_49_history')
    for slot in ('000047','000049'):
        require(rt.read(root/'calls'/slot/'terminal.json')['status']=='unknown'
                and not (root/'serial'/slot/'completion.json').exists(),'named_49_no_completion')
    s=rt.state(root/'runs/record-source-1-B')
    require(s['stopped']=='unknown' and s['call_count']==2 and s['draft'] is None,'named_49_no_47_replay')
    return x


def accepted(root,directory,intent):
    root=Path(root);x=verified(root)
    if directory==root/'serial/000047':x=rt.read(root/parent47.NAME)
    else:require(directory==root/'serial/000049','named_49_slot_only')
    return binding(root,directory,intent,x)


def register(root):
    root=Path(root).resolve()
    with _locked(root/'.execution.lock'),_locked(root/'.dispatch.lock'):
        require(not (root/NAME).exists(),'named_49_already_registered')
        config=rt.read(root/'batch.json');require(digest(config)==BATCH,'named_49_batch')
        require({p.name for p in root.glob('STOP*.json')}==STOPS,'named_49_stop_scope')
        parent=rt.read(root/parent47.NAME);parent47.parent_snapshot(root)
        require(parent['request_sha256']==parent47.REQUEST and parent['retry_call_key'] is None,'named_49_parent')
        for p,h in parent['preserved'].items():require(digest(rt.read(root/p))==h,'named_49_parent_history')
        class PriorSerial(SerialRequests):
            def _accepted_unknown(self,directory,intent):
                require(directory==root/'serial/000047','named_49_prior_slot')
                return binding(root,directory,intent,parent)
        try:PriorSerial(root/'serial').validate()
        except RecoveryRequired as exc:require(str(exc)=='serial_unknown_request_no_resubmit','named_49_serial_failure')
        else:require(False,'named_49_requires_unknown')
        dirs=sorted((root/'calls').iterdir())
        require([p.name for p in dirs]==[f'{i:06d}' for i in range(50)],'named_49_50_debits')
        for d in dirs:
            t=rt.read(d/'terminal.json');b=rt.read(d/'binding.json')
            require(t['binding']==b==rt.read(d/'raw.json')['binding'] and (d/'import.json').exists(),'named_49_receipts')
            require(t['status']==('unknown' if d.name in ('000047','000049') else 'returned'),'named_49_other_unknown')
        old=rt.read(root/'calls/000049/request.json');t=rt.read(root/'calls/000049/terminal.json')
        raw=rt.read(root/'calls/000049/raw.json')['transport']
        from .dispatch import classify
        require(old['request_sha256']==REQUEST and old['role']=='host' and old['phase']=='draft'
                and t['binding']['call_key']==KEY and classify(old,raw)[0::3]==('unknown','unclassified_cli_failure')
                and raw.get('reply_text') is None and any(e.get('type')=='turn.failed'
                    and e.get('error')=={'message':'stream disconnected before completion: idle timeout waiting for SSE'}
                    for e in raw.get('events',[])),'named_49_sse_only')
        require(rt.read(root/'STOP-000049.json')=={'call_key':KEY,'reason':'unknown','terminal_sha256':digest(t)},'named_49_stop_binding')
        require(read_record(root/'serial/000049/intent.json')['label']==KEY,'named_49_serial_key')
        run=root/'runs/record-source-2-B';s=rt.state(run)
        require(s['stopped']=='unknown' and s['call_count']==2 and s['pending']==old
                and s['phase']=='draft' and s['draft'] is None,'named_49_retry_state')
        source=parent['source_sha256']
        changed={p for p,h in source.items() if digest((REPO/p).read_text())!=h}
        require(changed=={'experiments/grounded_judgment/dispatch.py','experiments/grounded_judgment/resume_000007.py'},'named_49_minimal_source')
        source={p:digest((REPO/p).read_text()) for p in source}
        source[str(Path(__file__).resolve().relative_to(REPO))]=digest(Path(__file__).read_text())
        preserved={str(p.relative_to(root)):digest(rt.read(p)) for folder in ('calls','serial','runs') for p in (root/folder).rglob('*.json')}
        for n in STOPS|{parent47.NAME,'read-contract-successor.json'}:preserved[n]=digest(rt.read(root/n))
        x={'kind':'named_unknown_000049_retry','status':'risk_accepted_remote_unknown',
           'batch_sha256':BATCH,'request_sha256':REQUEST,'call_key':KEY,'retry_call_key':'record-source-2-B:2',
           'retry_limit':1,'compensates_local_call':'000049','allowed_paths':parent47.PATHS,
           'path_limits':{'record-source-2-B':8},'limits':config['admission']['total_limits'],'budgets_reset':False,
           'source_sha256':source,'preserved':preserved,'parent_successor_sha256':digest(parent),
           'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
           'local_disposition_at_epoch':time.time(),'wait_proves_remote_completion':False,'prior_calls':50,
           'authority_quote':'SSE连接空闲超时，这个应该可以重试解决吧',
           'authority_interpretation':'One bounded technical retry of this SSE draft under ongoing continuation and bounded-budget authorization; no general unknown exception.',
           'prior_budget_quote':'允许，但不是无边界的，超预算2-3倍可接受，再多需要有所控制和解释',
           'atoms_sha256':digest(s['atoms']),'composition_sha256':digest(s['composition'])}
        rt.write(root/NAME,x)
        end={'status':'risk_accepted_remote_unknown','intent_sha256':digest(read_record(root/'serial/000049/intent.json')),
             'successor_sha256':digest(x),'local_disposition_at_epoch':x['local_disposition_at_epoch']}
        save(root/'serial/000049/accepted-unknown.json',end)
        save(root/'serial/bindings/000049/accepted-unknown.json',{'sha256':digest(end)})
        with rt.lock(run):
            rt.append(run,'named_risk_disposition',{'successor_sha256':digest(x),'old_request_sha256':REQUEST,'old_remote_status':'unknown','retry_limit':1})
            s['stopped']=None;s['pending']=None;rt.append(run,'state',s)
        from .resume_000007 import NamedSerial
        NamedSerial(root/'serial').validate()
        return verified(root)
