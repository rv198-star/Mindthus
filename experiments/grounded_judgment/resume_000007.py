"""One specifically authorized exploratory request disposition; no general unlock."""
from pathlib import Path
import os,shlex,time
from . import runtime as rt
from experiments.typed_decision.contracts import digest,require
from experiments.typed_decision.relationship_runtime import _locked,save
from experiments.typed_decision.session import read_record
from experiments.jev_direct.serial import SerialRequests

REQUEST='0c3df7db8af82010010ba1686aa92ce604a7d561b3d314e1442bd0b68a386eb8'
BATCH='a9601496c40872b1ac73655e17b516eaee2a68b728efbe4e338af0a56ebad82c'
NAME='risk-accepted-000007.json'
REPO=Path(__file__).resolve().parents[2]


def load_official_credential():
    path=Path.home()/'.config/jev-jarvis/env'
    if path.is_file():
        for line in path.read_text().splitlines():
            text=line.strip().removeprefix('export ')
            if text.startswith('TYPESAFE_API_KEY='):
                parts=shlex.split(text.split('=',1)[1],comments=True)
                if len(parts)==1:os.environ['TYPESAFE_API_KEY']=parts[0]
    require(bool(os.environ.get('TYPESAFE_API_KEY')),'official_jev_entry_unavailable')
    return {'entry':str(path),'loaded':True,'provider':'TypeSafe official','model':'jev-1.13.0'}


def verified(root):
    root=Path(root);x=rt.read(root/NAME)
    require(digest(rt.read(root/'batch.json'))==BATCH==x['batch_sha256'],'named_batch_only')
    require(x['request_sha256']==REQUEST and x['call_key']=='skills-validator-B:1','named_request_only')
    for path,h in x['preserved'].items():require(digest(rt.read(root/path))==h,'preserved_unknown_changed')
    require(not (root/'serial/000007/completion.json').exists(),'no_fabricated_completion')
    require(rt.read(root/'calls/000007/terminal.json')['status']=='unknown','old_unknown_required')
    return x


class NamedSerial(SerialRequests):
    def _accepted_unknown(self,directory,intent):
        if (self.root.parent/'complete-missing-three.json').exists():
            from .complete_missing import accepted
            return accepted(self.root.parent,directory,intent)
        if (self.root.parent/'retry-000049.json').exists():
            from .resume_000049 import accepted
            return accepted(self.root.parent,directory,intent)
        if (self.root.parent/'risk-accepted-000047.json').exists():
            from .resume_000047 import accepted
            return accepted(self.root.parent,directory,intent)
        root=self.root.parent;x=verified(root)
        require(directory==self.root/'000007' and intent['label']=='skills-validator-B:1','named_slot_only')
        end=read_record(directory/'accepted-unknown.json')
        require(read_record(self.anchors/'000007/accepted-unknown.json')=={'sha256':digest(end)},'disposition_anchor')
        require(end['intent_sha256']==digest(intent) and end['successor_sha256']==digest(x)
                and end['status']=='risk_accepted_remote_unknown','disposition_binding')
        return end


def guard(root):
    root=Path(root);stops=list(root.glob('STOP*.json'))
    if (root/'complete-missing-three.json').exists():
        from .complete_missing import verified as verify_missing
        return verify_missing(root)
    if (root/'retry-000049.json').exists():
        from .resume_000049 import verified as verify_49
        return verify_49(root)
    if (root/'risk-accepted-000047.json').exists():
        from .resume_000047 import verified as verify_47
        return verify_47(root)
    if (root/'read-contract-successor.json').exists():
        from .read_contract_successor import verified as verify_read_contract
        return verify_read_contract(root)
    if (root/NAME).exists():
        x=verified(root)
        require(all(p.name=='STOP.json' and digest(rt.read(p))==x['preserved']['STOP.json'] for p in stops),'new_stop_not_exempt')
        return x
    require(not stops,'batch_stopped')
    return None


def register(root):
    root=Path(root)
    credential=load_official_credential()
    with _locked(root/'.dispatch.lock'):
        require(not (root/NAME).exists(),'disposition_already_registered')
        config=rt.read(root/'batch.json');require(digest(config)==BATCH,'named_batch_only')
        old=rt.read(root/'calls/000007/request.json');terminal=rt.read(root/'calls/000007/terminal.json')
        require(old['request_sha256']==REQUEST and terminal['status']=='unknown'
                and terminal['error']=='unclassified_cli_failure','named_unknown_only')
        require(len(list((root/'calls').iterdir()))==8,'eight_attempts_preserved')
        run=root/'runs/skills-validator-B';s=rt.state(run)
        require(s['stopped']=='unknown' and s['call_count']==2 and s['pending']==old
                and s['phase']=='draft' and s['draft'] is None,'named_retry_state')
        hashes=dict(config['source_sha256'])
        hashes[str(Path(__file__).resolve().relative_to(REPO))]=digest(Path(__file__).read_text())
        changed=[]
        for p,h in list(hashes.items()):
            value=digest((REPO/p).read_text())
            if value!=h:changed.append(p)
            hashes[p]=value
        require(set(changed)<= {'experiments/jev_direct/serial.py','experiments/grounded_judgment/dispatch.py'},'minimal_successor_sources')
        preserved={str(p.relative_to(root)):digest(rt.read(p)) for base in (root/'calls',root/'serial') for p in base.rglob('*.json')}
        preserved['STOP.json']=digest(rt.read(root/'STOP.json'))
        x={'status':'risk_accepted_remote_unknown','batch_sha256':BATCH,'request_sha256':REQUEST,
          'call_key':'skills-validator-B:1','retry_call_key':'skills-validator-B:2','retry_limit':1,
          'authority':'Current Owner explicitly accepts possible duplicate computation/billing/remote overlap for this exact request; no budget increase',
          'source_sha256':hashes,'preserved':preserved,'credential':credential,
          'remaining_path_calls':5,'prior_host_calls':8,'limits':{'logical':88,'host':72,'jev':16},
          'local_disposition_at_epoch':time.time(),'wait_proves_remote_completion':False,
          'order':['skills-text-C','skills-validator-B','skills-validator-A','skills-validator-C','4k-usability-A','4k-usability-B','4k-usability-C','4k-density-B','4k-density-A','4k-density-C']}
        rt.write(root/NAME,x)
        end={'status':'risk_accepted_remote_unknown','intent_sha256':digest(read_record(root/'serial/000007/intent.json')),
             'successor_sha256':digest(x),'local_disposition_at_epoch':x['local_disposition_at_epoch']}
        save(root/'serial/000007/accepted-unknown.json',end)
        save(root/'serial/bindings/000007/accepted-unknown.json',{'sha256':digest(end)})
        with rt.lock(run):
            rt.append(run,'named_risk_disposition',{'successor_sha256':digest(x),'old_request_sha256':REQUEST,'old_remote_status':'unknown'})
            s['stopped']=None;s['pending']=None
            rt.append(run,'state',s)
        NamedSerial(root/'serial').validate()
        return x
