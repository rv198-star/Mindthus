"""One Owner-accepted DSF request; same batch, wire, budget and transport."""
import argparse
import copy
import getpass
import json
import os
from pathlib import Path
import subprocess
import time

from . import stance_routing_coverage as c
from experiments.typed_decision.relationship_runtime import save
r=c.r;s=c.s
NAME='risk-accepted-000098.json'
KEY='stance-routing-coverage-v1:dsf41-current-B:0'
REQUEST='346106b19d142cc27b46475a158ed1cd7a457c96aaf28215279ac61eb59ec6b5'
TERMINAL='4d285764d1a613de6d94de63acb2fb34cab9d99f4f4831aa200d54413cfbd424'


def old_bound():
    p=c.ROOT/'calls/000011';req=r.rt.read(p/'request.json');wire=r.rt.read(p/'wire.json')
    raw=r.rt.read(p/'raw.json');t=r.rt.read(p/'terminal.json')
    r.require(t['status']=='unknown' and t['error']=='deadline_exceeded'
              and r.digest(t)==TERMINAL and t['binding']['call_key']==KEY
              and t['binding']['request_sha256']==REQUEST==req['request_sha256'],'only_named_unknown')
    r.require(raw['binding']==t['binding'] and r.digest(raw['transport'])==t['raw_sha256']
              and r.digest(wire)==t['binding']['wire_sha256'],'old_request_binding')
    r.require(r.rt.read(c.ROOT/'STOP.json')=={'call_key':KEY,'reason':'unknown','terminal_sha256':TERMINAL},'only_named_stop')
    return req,wire,t


def verified():
    x=r.rt.read(c.ROOT/NAME);old_bound()
    r.require(x['request_sha256']==REQUEST and x['old_terminal_sha256']==TERMINAL
              and x['old_call_key']==KEY and x['max_technical_retries']==1
              and x['limits']==c.LIMITS and x['remote_status']=='unknown'
              and x['is_completion'] is False,'named_authority_scope')
    for path,h in x['preserved'].items():r.require(r.digest(r.rt.read(c.ROOT/path))==h,'old_unknown_changed')
    r.require(not (s.old.PARENT/'serial/000098/completion.json').exists(),'old_unknown_not_completed')
    return x


class NamedSerial(s.old.prior.NamedSerial):
    def _accepted_unknown(self,directory,intent):
        if directory!=self.root/'000098':return super()._accepted_unknown(directory,intent)
        x=verified();r.require(intent['label']==KEY,'only_named_serial_label')
        end=r.read_record(directory/'accepted-unknown.json')
        r.require(r.read_record(self.anchors/'000098/accepted-unknown.json')=={'sha256':r.digest(end)}
                  and end['intent_sha256']==r.digest(intent) and end['successor_sha256']==r.digest(x)
                  and end['status']=='risk_accepted_remote_unknown' and end['is_completion'] is False,'named_disposition_binding')
        return end


def prepare():
    r.require(not (c.ROOT/NAME).exists() and len(list((c.ROOT/'calls').iterdir()))==12,'single_named_preparation')
    req,wire,t=old_bound();st=r.rt.read(c.ROOT/'states/dsf41-current.json')
    r.require(st['calls']=={'A':0,'B':1,'C':0} and st['arms']['B']['status']=='unknown'
              and st['arms']['C']['status']=='pending','named_remaining_state')
    summary=r.rt.read(c.DOC/'summary.json');r.require(summary['cumulative_debits']=={'logical':101,'host':77,'jev':24},'no_budget_reset')
    paths=['batch.json','STOP.json','effective-config-dsf41.json','dsf41-current.packet.json','dsf41-carrier.packet.json']
    paths += [str(p.relative_to(c.ROOT)) for p in (c.ROOT/'calls/000011').glob('*.json')]
    x={'schema':'mindthus.stance-routing.dsf-000098-owner-disposition.v1','status':'risk_accepted_remote_unknown',
       'old_call_key':KEY,'request_sha256':REQUEST,'old_terminal_sha256':TERMINAL,'old_wire_sha256':r.digest(wire),
       'old_serial_slot':'000098','old_local_call':'000011','max_technical_retries':1,
       'authority':'Owner explicitly: 接受上述指定风险，允许DSF补试一次并继续 (2026-10-02)',
       'remote_status':'unknown','is_completion':False,'wait_proves_remote_completion':False,
       'risks_retained':['possible duplicate computation/billing','old remote overlap cannot be excluded'],
       'local_disposition_at_epoch':time.time(),'preserved':{p:r.digest(r.rt.read(c.ROOT/p)) for p in paths},
       'inherited_cumulative_debits':summary['cumulative_debits'],'limits':c.LIMITS,
       'scope':'One same-wire DSF B routing compensation, then original C route/control and independent optional B/C handling. New unknown or refusal stops. No other model reruns.'}
    cfg=r.rt.read(c.ROOT/'effective-config-dsf41.json')
    effective={**cfg,'technical_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
       'parent_effective_config_sha256':r.digest(cfg),'named_disposition_sha256':r.digest(x),
       'source_sha256':{**cfg['source_sha256'],str(Path(__file__).relative_to(r.REPO)):r.digest(Path(__file__).read_text())},
       'named_technical_retry':{'old_call_key':KEY,'old_request_sha256':REQUEST,'new_call_key':c.VERSION+':dsf41-current-B:1','max':1},
       'scope_after_named_authority':x['scope']}
    r.rt.write(c.ROOT/NAME,x);r.rt.write(c.DOC/NAME,x)
    r.rt.write(c.ROOT/'effective-config-dsf41-after-000098.json',effective)
    r.rt.write(c.DOC/'effective-config-dsf41-after-000098.json',effective)
    serial=s.old.PARENT/'serial';intent=r.read_record(serial/'000098/intent.json')
    end={'status':'risk_accepted_remote_unknown','intent_sha256':r.digest(intent),'successor_sha256':r.digest(x),
         'local_disposition_at_epoch':x['local_disposition_at_epoch'],'old_request_sha256':REQUEST,
         'remote_status':'unknown','is_completion':False}
    save(serial/'000098/accepted-unknown.json',end)
    save(serial/'bindings/000098/accepted-unknown.json',{'sha256':r.digest(end)})
    NamedSerial(serial).validate()


class Driver(c.Driver):
    # Only this entry can create requests; the third B slot is the one named
    # compensation, not a new route/revision opportunity for other profiles.
    path_limits={'A':2,'B':3,'C':2}
    def request_factory(self,item,state,arm,phase,simulation,host_config):
        r.require(item['case_id'] in ('dsf41-current','dsf41-carrier')
                  and host_config==c.PROFILES['dsf41'] and arm in 'BC','dsf_remaining_only')
        n=state['calls'][arm]
        if arm=='B' and phase=='detect':
            r.require(item['case_id']=='dsf41-current' and n==1 and state['arms']['B']['status']=='unknown','one_named_route_compensation')
            old,wire,_=old_bound();body={k:v for k,v in old.items() if k!='request_sha256'}
            body.update(sequence=1,simulation=simulation,technical_retry_of={'call_key':KEY,'request_sha256':REQUEST})
            req={**body,'request_sha256':r.digest(body)}
            r.require(c.Adapters(host_config).outbound(req,self.config)==wire,'same_generation_wire')
            return req
        if arm=='B':
            r.require(phase=='handling' and n==2,'one_post_compensation_handling')
            view=copy.deepcopy(state);view['calls']['B']=1
            req=c.request(item,view,arm,phase,simulation,host_config);req['sequence']=n
            req['request_sha256']=r.digest({k:v for k,v in req.items() if k!='request_sha256'})
            return req
        return c.request(item,state,arm,phase,simulation,host_config)


def checkpoint():
    terms=[r.rt.read(p/'terminal.json') for p in sorted((c.ROOT/'calls').iterdir())]
    reqs=[r.rt.read(p/'request.json') for p in sorted((c.ROOT/'calls').iterdir())]
    counts={'logical':len(reqs),'host':sum(q['role']=='host' for q in reqs),'jev':sum(q['role']=='jev' for q in reqs)}
    r.persist(c.DOC/'summary.after-dsf.json',{'phase_debits':counts,
       'cumulative_debits':{k:c.INHERITED[k]+counts[k] for k in c.INHERITED},'limits':c.LIMITS,
       'terminals':terms,'states':{p.stem:r.rt.read(p) for p in (c.ROOT/'states').glob('*.json')},
       'session_seconds':sum(t['session_seconds'] for t in terms),'wait_seconds':sum(t['active_wait_seconds'] for t in terms),
       'loading_seconds':sum(t['loading_seconds'] for t in terms),'outer_automatic_retries':0,'technical_retries':1,
       'old_000098_remote_status':'risk_accepted_remote_unknown','old_000068_remote_status':'risk_accepted_remote_unknown',
       'fees':None,'underlying_requests':None,'simulation':False,'holdout':False})


def run():
    with r._locked(s.old.PARENT/'.execution.lock'):
        verified();r.require(not (c.ROOT/'dsf-retry.started.json').exists(),'no_execution_replay')
        r.require(len(list((c.ROOT/'calls').iterdir()))==12,'no_additional_attempts_before_retry')
        r.require(os.environ.get('HTTPS_PROXY')==s.PROXY and bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'same_registered_process_transport')
        credential=r.load_official_credential()
        driver=Driver(c.ROOT,c.Adapters(c.PROFILES['dsf41']))
        driver.config=r.rt.read(c.ROOT/'effective-config-dsf41-after-000098.json')
        driver.serial=NamedSerial(s.old.PARENT/'serial');driver.serial.validate()
        driver.stop_path=c.ROOT/'STOP.after-000098.json'
        r.rt.write(c.ROOT/'dsf-retry.started.json',{'started_at_epoch':time.time(),'credential':credential,'host_entry':'process memory','same_provider':'CPA.rn-us'})
        def step(cid,arm,phase):
            verified();p=r.rt.read(c.ROOT/(cid+'.packet.json'));st=r.rt.read(c.ROOT/'states'/(cid+'.json'))
            print(json.dumps({'dispatch':cid,'arm':arm,'phase':phase}),flush=True)
            t=driver.step({'case_id':cid,'packet':p,'control':cid.endswith('carrier')},st,arm,phase);checkpoint()
            print(json.dumps({'status':t['status'],'error':t['error'],'path_status':st['arms'][arm]['status'],
                 'route':st['arms'][arm].get('result'),'session_seconds':t['session_seconds'],'wait_seconds':t['active_wait_seconds']}),flush=True)
            return t['status']=='returned' and not driver.stop_path.exists() and st['arms'][arm]['status']!='format_failure'
        for cid,arm in [('dsf41-current','B'),('dsf41-current','C'),('dsf41-carrier','C')]:
            if not step(cid,arm,'detect'):return
        for arm in 'BC':
            st=r.rt.read(c.ROOT/'states/dsf41-current.json')
            if st['arms'][arm]['status']=='handling_required' and not step('dsf41-current',arm,'handling'):return
            row=r.rt.read(c.ROOT/'states/dsf41-current.json')['arms'][arm]
            r.rt.write(c.DOC/('dsf41-'+arm+'.outcome.json'),row)
            if row.get('final') is not None:(c.DOC/('dsf41-'+arm+'.final.reply.txt')).write_text(row['final'])
        checkpoint();r.rt.write(c.ROOT/'dsf41.complete.json',{'ended_at_epoch':time.time(),
             'technical_compensations':1,'no_shared_handling_return':True,'old_unknown_kept':True})
        print('DSF remaining coverage delivered.',flush=True)


def remaining_c_state():
    verified();p=c.ROOT/'calls/000012';t=r.rt.read(p/'terminal.json');raw=r.rt.read(p/'raw.json')
    r.require(len(list((c.ROOT/'calls').iterdir()))==13 and t['status']=='failed'
              and t['binding']['call_key']==c.VERSION+':dsf41-current-B:1'
              and r.digest(t)=='0b13a262edda1b59b1090c9ab785fecb082b4f6e1da323797be0f516933a0c10'
              and raw['binding']==t['binding'] and r.digest(raw['transport'])==t['raw_sha256'],'only_finished_compensation')
    diag=raw['transport'].get('diagnostic') or {}
    r.require(diag.get('generation_send_status')=='pre_send'
              and diag.get('observed_stage')=='connection_establishment_failed'
              and not (c.ROOT/'STOP.after-000098.json').exists(),'no_unknown_or_refusal_continuation')
    state=r.rt.read(c.ROOT/'states/dsf41-current.json')
    r.require(state['calls']=={'A':0,'B':2,'C':0} and state['arms']['B']['status']=='failed'
              and state['arms']['C']['status']=='pending','no_B_replay_and_C_unsent')
    return t


def complete_remaining_c():
    """Finish only the independently authorized C path after the spent B retry."""
    with r._locked(s.old.PARENT/'.execution.lock'):
        b=remaining_c_state()
        r.require(not (c.ROOT/'dsf-C-remainder.started.json').exists(),'no_C_remainder_replay')
        r.require(os.environ.get('HTTPS_PROXY')==s.PROXY and bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'same_registered_process_transport')
        cfg=r.rt.read(c.ROOT/'effective-config-dsf41-after-000098.json')
        cfg={**cfg,'parent_after_000098_config_sha256':r.digest(cfg),
             'technical_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
             'source_sha256':{**cfg['source_sha256'],str(Path(__file__).relative_to(r.REPO)):r.digest(Path(__file__).read_text())},
             'remaining_scope':'Only unsent C route/control and optional once handling; B retry exhausted; no further compensation.'}
        r.rt.write(c.ROOT/'effective-config-dsf41-C-remainder.json',cfg)
        r.rt.write(c.DOC/'effective-config-dsf41-C-remainder.json',cfg)
        credential=r.load_official_credential();driver=Driver(c.ROOT,c.Adapters(c.PROFILES['dsf41']));driver.config=cfg
        driver.serial=NamedSerial(s.old.PARENT/'serial');driver.serial.validate();driver.stop_path=c.ROOT/'STOP.after-000098.json'
        r.rt.write(c.ROOT/'dsf-C-remainder.started.json',{'started_at_epoch':time.time(),'credential':credential,
                    'finished_B_terminal_sha256':r.digest(b),'no_additional_B_retry':True})
        def step(cid,phase):
            verified();p=r.rt.read(c.ROOT/(cid+'.packet.json'));state=r.rt.read(c.ROOT/'states'/(cid+'.json'))
            print(json.dumps({'dispatch':cid,'arm':'C','phase':phase}),flush=True)
            t=driver.step({'case_id':cid,'packet':p,'control':cid.endswith('carrier')},state,'C',phase);checkpoint()
            print(json.dumps({'status':t['status'],'error':t['error'],'path_status':state['arms']['C']['status'],
                       'route':state['arms']['C'].get('result'),'session_seconds':t['session_seconds'],'wait_seconds':t['active_wait_seconds']}),flush=True)
            return t['status']=='returned' and not driver.stop_path.exists() and state['arms']['C']['status']!='format_failure'
        if not step('dsf41-current','detect'):return
        if not step('dsf41-carrier','detect'):return
        state=r.rt.read(c.ROOT/'states/dsf41-current.json')
        if state['arms']['C']['status']=='handling_required' and not step('dsf41-current','handling'):return
        state=r.rt.read(c.ROOT/'states/dsf41-current.json')
        for arm in 'BC':
            r.rt.write(c.DOC/('dsf41-'+arm+'.outcome.json'),state['arms'][arm])
            if state['arms'][arm].get('final') is not None:(c.DOC/('dsf41-'+arm+'.final.reply.txt')).write_text(state['arms'][arm]['final'])
        r.rt.write(c.ROOT/'dsf41.complete.json',{'ended_at_epoch':time.time(),'B_status':state['arms']['B']['status'],
                    'C_status':state['arms']['C']['status'],'technical_compensations':1,'old_unknown_kept':True})
        print('DSF C remainder finished; B explicit failure retained.',flush=True)


def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true')
    g.add_argument('--complete-C-after-B-failure',action='store_true');a=p.parse_args()
    if a.prepare:
        with r._locked(s.old.PARENT/'.execution.lock'):prepare()
        print('Only000098 risk disposition registered; no generation sent.');return
    if not os.environ.get('MINDTHUS_HOST_API_KEY'):os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('Registered CPA credential (hidden): ')
    if a.complete_C_after_B_failure:complete_remaining_c()
    else:run()


if __name__=='__main__':main()
