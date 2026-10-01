"""One bound local invalid-deadline repair; no remote-unknown risk exception."""
import argparse
import json
from pathlib import Path
import subprocess
import time
from unittest.mock import patch

from . import stance_routing as s
from experiments.typed_decision import relationship_live as transport
from experiments.typed_decision.relationship_runtime import save
r=s.r
NAME='named-local-deadline-repair.json'


def verify():
    folder=s.ROOT/'calls/000002';req=r.rt.read(folder/'request.json');wire=r.rt.read(folder/'wire.json')
    terminal=r.rt.read(folder/'terminal.json');raw=r.rt.read(folder/'raw.json')
    cfg=r.rt.read(s.ROOT/'local-call-key-repair.json')['effective_config']
    r.require(terminal['binding']['call_key']=='stance-routing-v2:S-current-C:1'
              and terminal['status']=='unknown' and terminal['error']=='ContractError'
              and raw['transport']=={'kind':'transport_error','code':'ContractError','diagnostic':None},'named_local_error_only')
    r.require(raw['binding']==terminal['binding'] and r.digest(raw['transport'])==terminal['raw_sha256']
              and r.digest(wire)==terminal['binding']['wire_sha256'] and req['request_sha256']==terminal['binding']['request_sha256'],'old_error_binding')
    r.require(cfg['host_timeout']==180 and req['phase']=='revision' and req['arm']=='C'
              and terminal['binding']['batch_sha256']==r.digest(cfg)
              and cfg['source_sha256']['experiments/typed_decision/relationship_live.py']==r.digest(Path(transport.__file__).read_text()),'actual_invalid_deadline_source')
    stop=r.rt.read(s.ROOT/'STOP.json')
    r.require(stop['call_key']==terminal['binding']['call_key'] and stop['terminal_sha256']==r.digest(terminal),'only_named_stop')
    # This is a local guard proof, not simulated remote completion. Same actual
    # payload/timeout; the transport context must never be reached.
    with patch.object(transport.multiprocessing,'get_context',side_effect=AssertionError('network worker must not be reached')) as launch:
        try:transport.deadline_post_json(wire['endpoint'],{},wire['body'],cfg['host_timeout'])
        except ValueError as exc:r.require(str(exc)=='invalid_deadline','exact_guard_reason')
        else:raise ValueError('missing_invalid_deadline_guard')
        r.require(launch.call_count==0,'transport_worker_reached')
    return req,wire,terminal,cfg


def prepare():
    r.require(not (s.ROOT/NAME).exists() and len(list((s.ROOT/'calls').iterdir()))==3,'single_local_repair_only')
    req,wire,t,cfg=verify()
    source={**cfg['source_sha256'],str(Path(__file__).relative_to(r.REPO)):r.digest(Path(__file__).read_text())}
    source['experiments/bias_trigger/run.py']=r.digest((r.REPO/'experiments/bias_trigger/run.py').read_text())
    source['experiments/bias_trigger/stance_routing.py']=r.digest((r.REPO/'experiments/bias_trigger/stance_routing.py').read_text())
    effective={**cfg,'host_timeout':90,'source_sha256':source,
               'technical_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
               'parent_effective_config_sha256':r.digest(cfg),'path_limits':{'A':4,'B':2,'C':3},
               'no_automatic_retries':True,'named_local_compensation':{'call_key':t['binding']['call_key'],'max_attempts':1,'counts_against_original_cap':True},
               'scope':'One confirmed local-not-sent C handling compensation, then B route. Same-body handler reuse only; original5-attempt cap remains.'}
    proof={'schema':'mindthus.named-local-guard-reconciliation.v1','old_request_sha256':req['request_sha256'],
       'old_terminal_sha256':r.digest(t),'old_wire_sha256':r.digest(wire),'old_serial_slot':'000084',
       'confirmed_status':'confirmed_local_not_sent','remote_status':'not_contacted_by_this_call',
       'guard_reason':'invalid_deadline','actual_timeout':180,'supported_timeout_max':90,
       'source_sha256':cfg['source_sha256']['experiments/typed_decision/relationship_live.py'],
       'local_guard_verification':{'simulation':True,'same_actual_payload_and_timeout':True,'worker_context_invocations':0,'real_model_calls':0},
       'not_a_risk_acceptance':True,'old_unknown_terminal_preserved':True,'no_successful_provider_completion':True,
       'effective_config':effective,'created_at_epoch':time.time()}
    r.no_secrets(proof);r.rt.write(s.ROOT/NAME,proof);r.rt.write(s.DOC/NAME,proof)
    serial=s.old.PARENT/'serial';intent=r.read_record(serial/'000084/intent.json')
    r.require(intent['label']==t['binding']['call_key'] and not (serial/'000084/completion.json').exists(),'named_serial_only')
    # Serial's returned status describes the local invocation's end. Underlying
    # outcome is explicitly a local failure; no provider success is invented.
    end={'status':'returned','local_outcome':'confirmed_local_not_sent','provider_outcome':'no_request',
         'intent_sha256':r.digest(intent),'ended_at_epoch':t['ended_at_epoch'],
         'request_elapsed_seconds':t['session_seconds'],'elapsed_semantics':'recorded local adapter session; no HTTP duration',
         'reconciliation_sha256':r.digest(proof)}
    save(serial/'000084/completion.json',end);save(serial/'bindings/000084/completion.json',{'completion_sha256':r.digest(end)})
    r.rt.write(s.ROOT/'calls/000002/reconciliation.json',proof)


class Driver(s.Driver):
    path_limits={'A':4,'B':2,'C':3}
    def request_factory(self,item,state,arm,phase,simulation,host_config):
        if arm!='C':return s.request(item,state,arm,phase,simulation,host_config)
        old,wire,t,_=verify()
        r.require(item['case_id']=='S-current' and phase=='handling' and state['calls']['C']==2
                  and state['arms']['C']['status']=='unknown' and state['snapshot_sha256']==r.digest(item['packet']),'one_named_compensation')
        body={k:v for k,v in old.items() if k!='request_sha256'};body['sequence']=2
        req={**body,'request_sha256':r.digest(body)}
        r.require(s.Adapters(host_config).outbound(req,self.config)==wire,'same_generation_wire')
        return req


def reuse_if_equal(driver,item,state):
    if state['arms']['B']['status']!='handling_required':return False
    source=s.ROOT/'calls/000003';t=r.rt.read(source/'terminal.json');raw=r.rt.read(source/'raw.json')
    r.require(t['status']=='returned' and raw['binding']==t['binding'] and r.digest(raw['transport'])==t['raw_sha256'],'actual_handling_source')
    r.require(t['binding']['simulation'] is driver.adapter.simulation,'shared_handling_mode')
    req=s.request(item,state,'B','handling',False,driver.config['host_configuration'])
    candidate_wire=driver.adapter.outbound(req,driver.config);actual_wire=r.rt.read(source/'wire.json')
    r.require(r.digest(actual_wire)==t['binding']['wire_sha256'],'actual_handling_wire_binding')
    if candidate_wire!=actual_wire:return False
    answer=s.accept_handling(item['packet'],t['response'])
    proof={'schema':'mindthus.equal-body-handling-reuse.v1','B_request_not_sent':True,'additional_model_calls':0,
           'planned_B_request_sha256':req['request_sha256'],'source_C_call_key':t['binding']['call_key'],
           'source_C_request_sha256':t['binding']['request_sha256'],'source_C_terminal_sha256':r.digest(t),
           'source_C_raw_sha256':t['raw_sha256'],'identical_wire_sha256':r.digest(actual_wire),
           'independent_B_generation':False,'reason':'Same source, adopted branch, contract, host and exact HTTP body; one common actual handling outcome.'}
    r.rt.write(s.ROOT/'B-common-handling-reuse.json',proof);r.rt.write(s.DOC/'B-common-handling-reuse.json',proof)
    state['arms']['B'].update(status='delivered_shared_handler',handling=answer,final=answer['final'],reuse=proof)
    r.persist(s.ROOT/'states/S-current.json',state)
    return True


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true');a=p.parse_args()
    with r._locked(s.old.PARENT/'.execution.lock'):
        if a.prepare:prepare();print('One local-not-sent reconciliation registered; no model request sent.');return
        proof=r.rt.read(s.ROOT/NAME);verify()
        r.require(s.os.environ.get('HTTPS_PROXY')==s.PROXY,'registered_process_network_not_loaded')
        r.require(len(list((s.ROOT/'calls').iterdir()))==3,'no_replay_or_further_repair')
        s.load_host_entry(None)
        driver=Driver(s.ROOT,s.Adapters(proof['effective_config']['host_configuration']));driver.config=proof['effective_config']
        driver.serial=s.old.prior.NamedSerial(s.old.PARENT/'serial');driver.serial.validate()
        driver.stop_path=s.ROOT/'STOP.after-local-guard-repair.json'
        rows=r.rt.read(s.DOC/'snapshots.json');item={'case_id':'S-current','packet':rows['S-current']}
        for arm,phase in [('C','handling'),('B','detect')]:
            state=r.rt.read(s.ROOT/'states/S-current.json')
            print(json.dumps({'dispatch':item['case_id'],'arm':arm,'phase':phase}),flush=True)
            terminal=driver.step(item,state,arm,phase);s.checkpoint()
            print(json.dumps({'status':terminal['status'],'path_status':state['arms'][arm]['status'],'error':terminal['error'],
                  'session_seconds':terminal['session_seconds'],'wait_seconds':terminal['active_wait_seconds']}),flush=True)
            if terminal['status']!='returned' or driver.stop_path.exists():return
            if arm=='C' and state['arms']['C']['status']!='delivered':return
        reused=reuse_if_equal(driver,item,state);s.checkpoint()
        print(json.dumps({'equal_body_common_handling_reused':reused,'B_status':state['arms']['B']['status'],'new_model_calls':2}),flush=True)


if __name__=='__main__':main()
