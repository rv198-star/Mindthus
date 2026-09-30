"""Bound compensation for the three undelivered paths; no general retry switch."""
from pathlib import Path
import subprocess,time
from . import runtime as rt,resume_000049 as parent49,resume_000047 as parent47
from .read_contract_successor import REPO
from experiments.typed_decision.contracts import digest,require
from experiments.typed_decision.relationship_runtime import _locked
from experiments.typed_decision.session import read_record

NAME='complete-missing-three.json'
BATCH=parent49.BATCH
PATHS=['display-goal-2-C','mechanism-object-2-A','record-source-1-B']
RETRIES={
 'display-goal-2-C:4':{'local_call':'000011','request_sha256':'8ebee0da86f72f7025b976ab6b21f28a143b0d103c9bcae1a575e4e14a8c8cbb','format_clarification':True},
 'mechanism-object-2-A:2':{'local_call':'000029','request_sha256':'bb473e3b36c51b21a31d129c548c1cfd01a8fbd8541a2a9a56e7056d404e41ee','format_clarification':True},
 'record-source-1-B:2':{'local_call':'000047','request_sha256':parent47.REQUEST,'format_clarification':False}}


def verified(root):
    root=Path(root);x=rt.read(root/NAME)
    require(digest(rt.read(root/'batch.json'))==BATCH==x['batch_sha256'],'missing_batch')
    require(x['allowed_paths']==PATHS and x['retries']==RETRIES and x['retry_limit_per_path']==1,'missing_scope')
    require({p.name for p in root.glob('STOP*.json')}==parent49.STOPS,'missing_new_stop')
    for p,h in x['preserved'].items():require(digest(rt.read(root/p))==h,'missing_history')
    for slot in ('000047','000049'):
        require(rt.read(root/'calls'/slot/'terminal.json')['status']=='unknown'
                and not (root/'serial'/slot/'completion.json').exists(),'missing_no_completion')
    for name,h in x['prior_delivered'].items():require(digest(rt.state(root/'runs'/name))==h,'missing_delivered_changed')
    return x


def accepted(root,directory,intent):
    root=Path(root);verified(root)
    require(directory.name in ('000047','000049') and directory.parent==root/'serial','missing_named_slot')
    grant=rt.read(root/(parent47.NAME if directory.name=='000047' else parent49.NAME))
    return parent49.binding(root,directory,intent,grant)


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
