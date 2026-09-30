"""Bound compensation for the three undelivered paths; no general retry switch."""
from pathlib import Path
import subprocess,time
from . import runtime as rt,resume_000049 as parent49,resume_000047 as parent47
from .read_contract_successor import REPO
from experiments.typed_decision.contracts import digest,require
from experiments.typed_decision.relationship_runtime import _locked
from experiments.typed_decision.session import read_record
from experiments.typed_decision.relationship_runtime import save
from experiments.typed_decision.session import RecoveryRequired
from experiments.jev_direct.serial import SerialRequests

NAME='complete-missing-three.json'
BATCH=parent49.BATCH
PATHS=['display-goal-2-C','mechanism-object-2-A','record-source-1-B']
RETRIES={
 'display-goal-2-C:4':{'local_call':'000011','request_sha256':'8ebee0da86f72f7025b976ab6b21f28a143b0d103c9bcae1a575e4e14a8c8cbb','format_clarification':True},
 'mechanism-object-2-A:2':{'local_call':'000029','request_sha256':'bb473e3b36c51b21a31d129c548c1cfd01a8fbd8541a2a9a56e7056d404e41ee','format_clarification':True},
 'record-source-1-B:2':{'local_call':'000047','request_sha256':parent47.REQUEST,'format_clarification':False}}
LAST_NAME='last-try-000077.json'
LAST_REQUEST='140537d06e092aae21e8e42381165ea3a559a6673100aed00e032a946d319f6c'
LAST_KEY='display-goal-2-C:6'
LAST_RETRIES={**RETRIES,LAST_KEY:{'local_call':'000077','request_sha256':LAST_REQUEST,'format_clarification':False}}


def verified(root):
    root=Path(root);last=(root/LAST_NAME).exists();x=rt.read(root/(LAST_NAME if last else NAME))
    require(digest(rt.read(root/'batch.json'))==BATCH==x['batch_sha256'],'missing_batch')
    require(x['allowed_paths']==PATHS and x['retries']==(LAST_RETRIES if last else RETRIES)
            and x['retry_limit_per_path']==1,'missing_scope')
    require({p.name for p in root.glob('STOP*.json')}==parent49.STOPS|({'STOP-000077.json'} if last else set()),'missing_new_stop')
    if last:
        require(x['last_retry_call_key']==LAST_KEY and x['last_retry_limit']==1
                and x['parent_successor_sha256']==digest(rt.read(root/NAME)),'missing_last_scope')
    for p,h in x['preserved'].items():require(digest(rt.read(root/p))==h,'missing_history')
    for slot in (('000047','000049','000077') if last else ('000047','000049')):
        require(rt.read(root/'calls'/slot/'terminal.json')['status']=='unknown'
                and not (root/'serial'/slot/'completion.json').exists(),'missing_no_completion')
    for name,h in x['prior_delivered'].items():require(digest(rt.state(root/'runs'/name))==h,'missing_delivered_changed')
    return x


def accepted(root,directory,intent):
    root=Path(root);x=verified(root)
    if directory==root/'serial/000077':
        require((root/LAST_NAME).exists() and intent['label']=='display-goal-2-C:5','missing_last_named_slot')
        end=read_record(directory/'accepted-unknown.json')
        require(read_record(root/'serial/bindings/000077/accepted-unknown.json')=={'sha256':digest(end)}
                and end['intent_sha256']==digest(intent) and end['successor_sha256']==digest(x)
                and end['status']=='risk_accepted_remote_unknown','missing_last_binding')
        return end
    require(directory.name in ('000047','000049') and directory.parent==root/'serial','missing_named_slot')
    grant=rt.read(root/(parent47.NAME if directory.name=='000047' else parent49.NAME))
    return parent49.binding(root,directory,intent,grant)


def register_last_try(root):
    """Owner's final attempt for exactly 000077; old debits and unknown stay intact."""
    root=Path(root).resolve()
    with _locked(root/'.execution.lock'),_locked(root/'.dispatch.lock'):
        require(not (root/LAST_NAME).exists(),'missing_last_already_registered')
        parent=rt.read(root/NAME)
        require(parent['retries']==RETRIES and parent['allowed_paths']==PATHS,'missing_last_parent')
        require(digest(rt.read(root/'batch.json'))==BATCH==parent['batch_sha256'],'missing_batch')
        require({p.name for p in root.glob('STOP*.json')}==parent49.STOPS|{'STOP-000077.json'},'missing_new_stop')
        for p,h in parent['preserved'].items():require(digest(rt.read(root/p))==h,'missing_history')
        for name,h in parent['prior_delivered'].items():require(digest(rt.state(root/'runs'/name))==h,'missing_delivered_changed')
        class PriorSerial(SerialRequests):
            def _accepted_unknown(self,directory,intent):
                require(directory.parent==root/'serial' and directory.name in ('000047','000049'),'missing_prior_slot')
                grant=rt.read(root/(parent47.NAME if directory.name=='000047' else parent49.NAME))
                return parent49.binding(root,directory,intent,grant)
        try:PriorSerial(root/'serial').validate()
        except RecoveryRequired as exc:require(str(exc)=='serial_unknown_request_no_resubmit','missing_last_serial')
        else:require(False,'missing_last_requires_unknown')
        calls=sorted((root/'calls').iterdir())
        require([p.name for p in calls]==[f'{i:06d}' for i in range(78)],'missing_last_78_debits')
        for d in calls:
            t=rt.read(d/'terminal.json');b=rt.read(d/'binding.json')
            require(t['binding']==b==rt.read(d/'raw.json')['binding'] and (d/'import.json').exists(),'missing_receipts')
            require(t['status']==('unknown' if d.name in ('000047','000049','000077') else 'returned'),'missing_other_unknown')
        old=rt.read(root/'calls/000077/request.json');terminal=rt.read(root/'calls/000077/terminal.json')
        require(old['request_sha256']==LAST_REQUEST and terminal['binding']['call_key']=='display-goal-2-C:5'
                and old['phase']=='draft' and terminal['error']=='unclassified_cli_failure','missing_last_identity')
        run=root/'runs/display-goal-2-C';s=rt.state(run)
        require(s['stopped']=='unknown' and s['call_count']==6 and s['pending']==old
                and s['phase']=='draft' and s['draft'] is None,'missing_last_state')
        sources=parent['source_sha256'];own=str(Path(__file__).resolve().relative_to(REPO))
        require({p for p,h in sources.items() if digest((REPO/p).read_text())!=h}=={own},'missing_last_minimal_source')
        preserved=dict(parent['preserved'])
        for base in (root/'calls',root/'serial'):
            preserved.update({str(p.relative_to(root)):digest(rt.read(p)) for p in base.rglob('*.json')})
        preserved.update({NAME:digest(parent),'STOP-000077.json':digest(rt.read(root/'STOP-000077.json'))})
        x={**parent,'source_sha256':{p:digest((REPO/p).read_text()) for p in sources},
           'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
           'parent_successor_sha256':digest(parent),'preserved':preserved,'retries':LAST_RETRIES,
           'last_retry_call_key':LAST_KEY,'last_retry_limit':1,'prior_calls':78,
           'authority_quote':'你检查下原因，看能不能排查，不然就最后试一次，不行就放弃',
           'authority_interpretation':'One final technical attempt for 000077, exact input and prior atoms retained. Stop this completion attempt if it fails. If delivered, finish the two already authorized unsent compensations; no further retry allowance.',
           'local_disposition_at_epoch':time.time(),'budgets_reset':False,'wait_proves_remote_completion':False}
        rt.write(root/LAST_NAME,x)
        end={'status':'risk_accepted_remote_unknown','intent_sha256':digest(read_record(root/'serial/000077/intent.json')),
             'successor_sha256':digest(x),'local_disposition_at_epoch':x['local_disposition_at_epoch']}
        save(root/'serial/000077/accepted-unknown.json',end)
        save(root/'serial/bindings/000077/accepted-unknown.json',{'sha256':digest(end)})
        with rt.lock(run):
            rt.append(run,'last_named_technical_attempt',{'successor_sha256':digest(x),'old_request_sha256':LAST_REQUEST,'old_remote_status':'unknown'})
            s['stopped']=None;s['pending']=None;rt.append(run,'state',s)
        from .resume_000007 import NamedSerial
        NamedSerial(root/'serial').validate()
        return verified(root)


def retry_binding(root,x,key,req):
    retry=x['retries'].get(key)
    if retry is None:return {}
    old=rt.read(Path(root)/'calls'/retry['local_call']/'request.json')
    require(old['request_sha256']==retry['request_sha256'] and req['phase']=='draft','missing_retry_identity')
    def comparable(p):return {k:v for k,v in p.items() if k!='output_contract'} if retry['format_clarification'] else p
    require(comparable(req['payload'])==comparable(old['payload']),'missing_retry_input_changed')
    return {'compensates_request_sha256':old['request_sha256'],
            'compensates_local_call':retry['local_call'],
            'sending_contract_changed':req['payload'].get('output_contract')!=old['payload'].get('output_contract')}


def register(root):
    root=Path(root).resolve()
    with _locked(root/'.execution.lock'),_locked(root/'.dispatch.lock'):
        require(not (root/NAME).exists(),'missing_already_registered')
        config=rt.read(root/'batch.json');require(digest(config)==BATCH,'missing_batch')
        parent=parent49.verified(root)
        from .resume_000007 import NamedSerial
        NamedSerial(root/'serial').validate()
        calls=sorted((root/'calls').iterdir())
        require([p.name for p in calls]==[f'{i:06d}' for i in range(76)],'missing_76_debits')
        for d in calls:
            t=rt.read(d/'terminal.json');b=rt.read(d/'binding.json')
            require(t['binding']==b==rt.read(d/'raw.json')['binding'] and (d/'import.json').exists(),'missing_receipts')
            require(t['status']==('unknown' if d.name in ('000047','000049') else 'returned'),'missing_other_unknown')
        states={p.name:rt.state(p) for p in (root/'runs').iterdir()}
        require(len(states)==24 and {k for k,v in states.items() if v['stopped']}==set(PATHS),'missing_only_three')
        delivered={k:digest(v) for k,v in states.items() if v['phase']=='done' and not v['stopped']}
        require(len(delivered)==21,'missing_21_protected')
        for key,retry in RETRIES.items():
            name=key.rsplit(':',1)[0];s=states[name];d=root/'calls'/retry['local_call']
            old=rt.read(d/'request.json');terminal=rt.read(d/'terminal.json')
            require(s['call_count']==int(key.rsplit(':',1)[1]) and s['pending']==old
                    and old['request_sha256']==retry['request_sha256'] and s['phase']=='draft' and s['draft'] is None,'missing_retry_state')
            if retry['format_clarification']:
                require(s['stopped']=='format_failure' and terminal['status']=='returned'
                        and rt.read(d/'envelope.json')['response']['kind']=='read'
                        and rt.read(d/'envelope.json')['response']['text']!=''
                        and (root/'serial'/retry['local_call']/'completion.json').exists(),'missing_format_terminal')
            else:require(s['stopped']=='unknown' and terminal['error']=='TimeoutExpired','missing_named_unknown')
        source=parent['source_sha256'];changed={p for p,h in source.items() if digest((REPO/p).read_text())!=h}
        require(changed=={'experiments/grounded_judgment/dispatch.py','experiments/grounded_judgment/resume_000007.py'},'missing_minimal_source')
        source={p:digest((REPO/p).read_text()) for p in source}
        source[str(Path(__file__).resolve().relative_to(REPO))]=digest(Path(__file__).read_text())
        preserved={str(p.relative_to(root)):digest(rt.read(p)) for folder in ('calls','serial','runs') for p in (root/folder).rglob('*.json')}
        for n in parent49.STOPS|{parent47.NAME,parent49.NAME,'read-contract-successor.json','batch.json','inputs.json'}:preserved[n]=digest(rt.read(root/n))
        x={'kind':'missing_three_compensation','batch_sha256':BATCH,'allowed_paths':PATHS,'retries':RETRIES,
           'retry_call_key':None,'retry_limit_per_path':1,'source_sha256':source,'preserved':preserved,
           'prior_delivered':delivered,'parent_successor_sha256':digest(parent),
           'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
           'authority_quote':'所以我们需要继续跑完吗？能跑完么？',
           'authority_interpretation':'Continue the authorized evaluation to fill only its three missing answers, one technical compensation each; reuse prior accepted 000047 remaining remote-risk disposition.',
           'prior_risk_quote':'允许，但不是无边界的，超预算2-3倍可接受，再多需要有所控制和解释',
           'old_remote_status':'unknown','wait_proves_remote_completion':False,'limits':config['admission']['total_limits'],
           'budgets_reset':False,'prior_calls':76,'registered_at_epoch':time.time()}
        rt.write(root/NAME,x)
        for name in PATHS:
            run=root/'runs'/name;s=states[name]
            with rt.lock(run):
                rt.append(run,'named_technical_compensation',{'successor_sha256':digest(x),'prior_status':s['stopped'],'retry_limit':1})
                s['stopped']=None;s['pending']=None;rt.append(run,'state',s)
        NamedSerial(root/'serial').validate()
        return verified(root)
