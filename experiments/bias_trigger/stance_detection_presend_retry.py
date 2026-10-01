"""One named pre-send repair within the existing two-attempt stage cap; no loop."""
import argparse, json, os, subprocess, time
from pathlib import Path
from . import stance_detection as d
r=d.r
OLD_REQUEST='314a38d160f6885231e5e329f8268c25ab822a48b1bad19a2afce0013e2a3666'
PROXY='http://127.0.0.1:7890'

def verify_old(t,raw,wire):
    r.require(t['binding']['request_sha256']==OLD_REQUEST and t['binding']['call_key']=='S-current-C:0'
              and t['status']=='failed' and t['error']=='transport_failure','named_failed_request_only')
    r.require(raw['binding']==t['binding'] and r.digest(raw['transport'])==t['raw_sha256']
              and r.digest(wire)==t['binding']['wire_sha256'],'old_failure_binding')
    x=raw['transport']['diagnostic']
    r.require(x['request_sha256']==r.digest(wire['body']) and x['generation_send_status']=='pre_send'
              and x['observed_stage']=='connection_establishment_failed' and x['http_response_received'] is False
              and x['pre_send_basis']=='HTTPSConnection.connect raised before generation HTTP write','proven_pre_send_only')

def successor_request(old,item,state,arm,phase,simulation,host_config):
    r.require(arm=='C' and phase=='detect' and simulation is False and state['calls']['C']==1
              and item['case_id']=='S-current' and r.digest(item['packet'])==state['snapshot_sha256'],'one_named_retry_only')
    r.require(old['request_sha256']==OLD_REQUEST and old['sequence']==0,'old_request_identity')
    req={**old,'sequence':1};req['request_sha256']=r.digest({k:v for k,v in req.items() if k!='request_sha256'})
    return req

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--run',action='store_true');args=parser.parse_args()
    r.require(args.prepare!=args.run,'select_prepare_or_run')
    with r._locked(d.PARENT/'.execution.lock'):
        folder=d.ROOT/'calls/000000';old=r.rt.read(folder/'request.json');t=r.rt.read(folder/'terminal.json')
        raw=r.rt.read(folder/'raw.json');wire=r.rt.read(folder/'wire.json');verify_old(t,raw,wire)
        r.require(len(list((d.ROOT/'calls').iterdir()))==1 and not (d.ROOT/'STOP.json').exists(),'no_extra_call_or_unknown')
        state=r.rt.read(d.ROOT/'states/S-current.json');p=r.rt.read(d.DOC/'snapshots.json')['S-current']['packet']
        item={'case_id':'S-current','packet':p};new=successor_request(old,item,state,'C','detect',False,{})
        r.require(r.outbound(new,{})==wire,'exact_old_wire_required')
        path=d.ROOT/'named-presend-repair.json'
        if args.prepare:
            cfg=r.rt.read(d.ROOT/'batch.json');source=dict(cfg['source_sha256'])
            source[str(Path(__file__).resolve().relative_to(r.REPO))]=r.digest(Path(__file__).read_text())
            effective={**cfg,'source_sha256':source,'technical_parent_sha256':r.digest(cfg),
                'technical_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
                'scope':'One named pre-send connection repair only; remaining stage attempt used for S-current, negative deferred',
                'effective_process_network':{'HTTPS_PROXY':PROXY,'from':'existing macOS system proxy; no global change'}}
            proof={'schema':'mindthus.named-presend-repair.v1','old_request_sha256':OLD_REQUEST,
                'old_terminal_sha256':r.digest(t),'old_wire_sha256':r.digest(wire),
                'new_request_sha256':new['request_sha256'],'remaining_attempts':1,'risk_unknown_exception':False,
                'authority':'Owner current detection task; routine repair of observed pre-send path error inside the announced two-attempt cap; no additional budget or semantic rerun',
                'negative_deferred':True,'effective_config':effective,'old_failure_preserved':True,'created_at_epoch':time.time()}
            r.no_secrets(proof);r.rt.write(path,proof);r.rt.write(d.DOC/'named-presend-repair.json',proof)
            print('One named pre-send repair registered; same wire, existing cap, no model request sent.');return
        proof=r.rt.read(path)
        r.require(proof['old_terminal_sha256']==r.digest(t) and proof['old_wire_sha256']==r.digest(wire)
                  and proof['new_request_sha256']==new['request_sha256'],'repair_proof_changed')
        r.require(os.environ.get('HTTPS_PROXY')==PROXY,'existing_process_network_not_loaded')
        credential=r.load_official_credential();r.rt.write(d.ROOT/'retry-credential-entry.json',credential)
        driver=d.Driver(d.ROOT,d.Adapters());driver.config=proof['effective_config']
        driver.request_factory=lambda *a:successor_request(old,*a)
        driver.serial=d.prior.NamedSerial(d.PARENT/'serial');driver.serial.validate()
        began=time.monotonic();terminal=driver.step(item,state,'C','detect');d.checkpoint(began)
        r.rt.write(d.DOC/'S-current.retry.detection.json',{'terminal':terminal,'state':state,
            'old_terminal_sha256':r.digest(t),'new_request_sha256':new['request_sha256'],'retry_wall_seconds':time.monotonic()-began})
        result=state['arms']['C']['result']
        print(json.dumps({'status':terminal['status'],'error':terminal['error'],'session_seconds':terminal['session_seconds'],
            'wait_seconds':terminal['active_wait_seconds'],'correction_triggered':None if result is None else result['needs_revision']}),flush=True)

if __name__=='__main__':main()
