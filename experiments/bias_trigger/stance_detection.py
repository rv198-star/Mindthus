"""Two authorized Jev detections only, reusing the existing transport/driver/serial."""
import argparse, importlib.util, json, subprocess, time
from pathlib import Path
from . import stance_correction as c
r = c.r
DOC = r.REPO / 'docs/internal/research/typed-decision/stance-pressure-v1/stance-correction-v1'
PARENT = Path('/Users/william/.codex/tmp/bias-trigger-deepseek-v1-run')
ROOT = PARENT / 'stance-correction-detection-v1'
INHERITED = {'logical':82, 'host':66, 'jev':16}
LIMITS = {'logical':84, 'host':66, 'jev':18}
ORDER = ('S-current', 'S-carrier-scope')

def module(name, path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

packets = module('scoped_correction_packets',DOC/'prepare_packets.py')
prior = module('scoped_prior_serial',DOC.parent/'sol56-cpa-bare-v1/sub2api-two-v1/EXECUTOR.py')

def initial(p):
    return {'candidate':p['candidate'],'snapshot_sha256':r.digest(p),'calls':{'A':0,'B':0,'C':0},
            'arms':{'C':{'status':'pending','result':None}},'measurements':[]}

def request(item,state,arm,phase,simulation,host_config):
    r.require(arm=='C' and phase=='detect' and state['calls']['C']==0,'single_detection_only')
    p=item['packet'];r.require(state['snapshot_sha256']==r.digest(p),'scoped_packet_changed')
    req=packets.request(p,'C');req['simulation']=simulation
    req['request_sha256']=r.digest({k:v for k,v in req.items() if k!='request_sha256'})
    return json.loads(r.canonical(req))

def consume(item,state,req,status,response,materials):
    r.require(req['role']=='jev' and req['arm']=='C' and not materials,'detection_only')
    state['calls']['C']+=1;row=state['arms']['C']
    row['status']=status
    if status=='returned':
        result=c.consume(item['packet'],response,'C')
        row.update(result=result,status='correction_triggered' if result['needs_revision'] else 'no_adopted_findings',
                   correction_executed=False)

class Driver(r.Driver):
    request_factory=staticmethod(request)
    result_consumer=staticmethod(consume)

class Adapters(r.OfficialAdapters):
    def check_configuration(self,cfg):
        r.require(cfg['limits']==LIMITS and cfg['external_budget_debits']==INHERITED
                  and cfg['phase_limits']=={'logical':2,'host':0,'jev':2},'detection_budget_changed')
    def outbound(self,req,cfg):
        self.check_configuration(cfg)
        r.require(req['role']=='jev' and req['arm']=='C' and req['phase']=='atoms'
                  and req['requested_configuration']=={'model':'jev-1.13.0','provider':'official'},'official_jev_detection_only')
        return r.outbound(req,cfg)
    def invoke(self,req,wire,directory,cfg):
        r.require(req['role']=='jev' and wire==self.outbound(req,cfg),'bound_jev_invocation')
        raw=super().invoke(req,wire,directory,cfg)
        return {**raw,'endpoint':wire['endpoint'],'request_sha256':r.digest(wire['body'])}
    def classify(self,req,raw):
        if raw.get('kind')=='http_json':
            expected=r.outbound(req,{})
            if raw.get('endpoint')!=expected['endpoint'] or raw.get('request_sha256')!=r.digest(expected['body']):
                return 'unknown',None,None,'jev_receipt_binding'
        return r.classify(req,raw)

def prepare():
    r.require(not ROOT.exists(),'phase_exists_no_reset')
    parent=r.rt.read(PARENT/'prompt-essential-cross-model-v1/batch.json')
    summary=r.rt.read(DOC.parent/'prompt-essential-cross-model-v1/summary.json')
    r.require(summary['cumulative_debits']==INHERITED,'parent_budget_changed')
    serial=prior.NamedSerial(PARENT/'serial');directories,last,_=serial.validate()
    r.require(len(directories)==80 and last['status']=='returned','parent_serial_changed')
    rows=packets.build();r.require(r.digest(rows)==r.digest(r.rt.read(DOC/'snapshots.json')),'prepared_snapshots_changed')
    paths=['experiments/bias_trigger/run.py','experiments/bias_trigger/stance_correction.py',
           'experiments/bias_trigger/stance_detection.py','experiments/grounded_judgment/dispatch.py',
           'experiments/grounded_judgment/exchange.py','experiments/grounded_judgment/core.py',
           'experiments/grounded_judgment/resume_000007.py','experiments/jev_direct/serial.py',
           'experiments/typed_decision/providers.py','experiments/typed_decision/contracts.py',
           'experiments/typed_decision/transport_diagnostics.py','experiments/typed_decision/relationship_live.py',
           str((DOC/'prepare_packets.py').relative_to(r.REPO)),str(Path(prior.__file__).relative_to(r.REPO))]
    cfg={'schema':'mindthus.stance-correction.detection-only.v1','simulation':False,
         'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
         'authorization_ref':'Owner: 先看新的Jev能否识别话题中的潜在问题，然后是否决定触发纠偏 (2026-10-02); detector stage only, at most2 Jev /0 host',
         'external_budget_debits':INHERITED,'limits':LIMITS,'phase_limits':{'logical':2,'host':0,'jev':2},
         'host_configuration':parent['host_configuration'],'host_configuration_unused':True,
         'jev_timeout':60,'source_sha256':{p:r.digest((r.REPO/p).read_text()) for p in paths},
         'cases_source_path':str((DOC/'snapshots.json').relative_to(r.REPO)),'cases_sha256':r.digest(rows),
         'protocol':{**parent['protocol'],'scope_this_turn':'Two Jev detections only; shared parent serial/cooldown and existing named000068 disposition only'},
         'parent_batch_sha256':r.digest(parent),
         'old_000068_remote_status':'risk_accepted_remote_unknown','new_unknown_exception':False,
         'order':list(ORDER),'scope':'Two detections only; no B, host, correction, evaluator, probe or retry',
         'no_retries':True,'retry_bound':0,'created_at_epoch':time.time()}
    r.no_secrets(cfg);ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    r.rt.write(ROOT/'batch.json',cfg);r.rt.write(ROOT/'materials.json',{});r.rt.write(DOC/'detection-admission.json',cfg)
    for name in ORDER:r.rt.write(ROOT/'states'/(name+'.json'),initial(rows[name]['packet']))

def checkpoint(began):
    dirs=sorted((ROOT/'calls').iterdir());ts=[r.rt.read(p/'terminal.json') for p in dirs if (p/'terminal.json').exists()]
    count=sum((p/'intent.json').exists() for p in dirs);counts={'logical':count,'host':0,'jev':count}
    r.persist(DOC/'detection-summary.json',{'simulation':False,'holdout':False,'phase_debits':counts,
        'cumulative_debits':{k:INHERITED[k]+counts[k] for k in INHERITED},'terminals':ts,
        'wall_seconds':time.monotonic()-began,'correction_calls':0,'fees':None,
        'old_000068_remote_status':'unknown','retry_count':0})

def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--run',action='store_true');a=p.parse_args()
    r.require(a.prepare!=a.run,'select_prepare_or_run')
    with r._locked(PARENT/'.execution.lock'):
        if a.prepare:prepare();print('Two Jev detections registered; no model request sent.');return
        cfg=r.rt.read(ROOT/'batch.json');r.require(not list((ROOT/'calls').iterdir()),'no_reexecution_or_retry')
        began=time.monotonic();credential=r.load_official_credential();r.rt.write(ROOT/'credential-entry.json',credential)
        driver=Driver(ROOT,Adapters());driver.serial=prior.NamedSerial(PARENT/'serial');driver.serial.validate()
        rows=r.rt.read(DOC/'snapshots.json')
        for name in ORDER:
            state=r.rt.read(ROOT/'states'/(name+'.json'));item={'case_id':name,'packet':rows[name]['packet']}
            t=driver.step(item,state,'C','detect');checkpoint(began)
            r.rt.write(DOC/(name+'.detection.json'),{'terminal':t,'state':state})
            print(json.dumps({'snapshot':name,'status':t['status'],'error':t['error'],
                'session_seconds':t['session_seconds'],'wait_seconds':t['active_wait_seconds'],
                'correction_triggered':bool((state['arms']['C']['result'] or {}).get('needs_revision'))}),flush=True)
            if t['status']!='returned' or driver.stop_path.exists():break
        checkpoint(began)

if __name__=='__main__':main()
