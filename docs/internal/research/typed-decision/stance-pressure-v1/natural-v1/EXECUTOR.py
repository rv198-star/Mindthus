"""One authorized host call, using existing adapters/driver/parent serial ledger."""
import argparse,getpass,json,os,subprocess,time
from pathlib import Path
from experiments.bias_trigger import run as r,deepseek as d,stance_pressure as s,primitive_ablation as a
DOC=r.REPO/'docs/internal/research/typed-decision/stance-pressure-v1/natural-v1'
ROOT=d.ROOT/'stance-pressure-natural-v1'
INHERITED={'logical':67,'host':51,'jev':16}
LIMITS={'logical':68,'host':52,'jev':16}
class Adapters(s.Adapters):limits=LIMITS

def prepare():
    r.require(not ROOT.exists(),'one_call_exists_no_reset')
    r.require(not (s.ROOT/'STOP.json').exists(),'parent_stopped')
    old=r.rt.read(s.DOC/'summary.json');r.require(old['cumulative_debits']==INHERITED,'parent_debits_changed')
    serial=r.SerialRequests(d.ROOT/'serial');serial.validate()
    r.require(len(list(serial.root.glob('[0-9]*')))==65,'parent_serial_count_changed')
    config=r.rt.read(s.ROOT/'batch.json')
    sources=set(config['source_sha256'])|{str(Path(__file__).resolve().relative_to(r.REPO))}
    value={**config,'schema':'mindthus.stance-pressure.natural-once.v1',
           'authorization_ref':'Owner: 我觉得可以，试试吧 (2026-10-01), exact approved natural prompt, one host answer only',
           'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
           'source_sha256':{p:r.digest((r.REPO/p).read_text()) for p in sources},
           'cases_source_path':str((DOC/'cases.business.json').relative_to(r.REPO)),
           'cases_sha256':r.digest(r.rt.read(DOC/'cases.business.json')),
           'norms_sha256':r.digest(r.rt.read(DOC/'norms.evaluation-only.json')),
           'limits':LIMITS,'external_budget_debits':INHERITED,'phase_limits':{'logical':1,'host':1,'jev':0},
           'protocol':{**config['protocol'],'scope_this_turn':'one approved natural strong-stance host call; no other paths, confirmation or retry'},
           'primary_cases':['skills-natural-stance'],'created_at_epoch':time.time(),
           'parent_summary_sha256':r.digest(old)}
    ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    r.rt.write(ROOT/'batch.json',value);r.rt.write(ROOT/'materials.json',{})
    r.rt.write(DOC/'admission.json',value);r.rt.write(ROOT/'states/skills-natural-stance.json',a.initial())

def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--run',action='store_true');args=p.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:prepare();print('One-call scope prepared; inherited debits retained.');return
        cfg=r.rt.read(ROOT/'batch.json')
        r.require(cfg['limits']==LIMITS and cfg['external_budget_debits']==INHERITED,'one_call_budget_changed')
        r.require(not list((ROOT/'calls').iterdir()),'one_attempt_no_resubmit')
        r.require(r.digest(r.rt.read(s.DOC/'summary.json'))==cfg['parent_summary_sha256'],'parent_summary_changed')
        driver=r.Driver(ROOT,Adapters(cfg['host_configuration']))
        driver.serial=r.SerialRequests(d.ROOT/'serial');driver.stop_path=ROOT/'STOP.json';driver.serial.validate()
        if not os.environ.get('MINDTHUS_HOST_API_KEY'):
            os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('CPA credential (hidden, process memory only): ')
        r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_host_credential')
        question=r.rt.read(DOC/'cases.business.json')['cases'][0]
        item={**question,'input':r.canonical([{'role':'user','content':question['input']}]).decode()}
        state=r.rt.read(ROOT/'states/skills-natural-stance.json')
        print(json.dumps({'credential_loaded':True,'dispatch':question['case_id'],'max_host_calls':1,'Jev_calls':0}),flush=True)
        terminal=driver.step(item,state,'A','draft')
        r.rt.write(DOC/'answer.json',state)
        r.rt.write(DOC/'summary.json',{'phase_debits':{'logical':1,'host':1,'jev':0},
                    'cumulative_debits':LIMITS,'state':state,'terminal':terminal,'holdout':False,'simulation':False})
        print(json.dumps({'terminal':terminal['status'],'delivery_status':state['arms']['A']['status']}),flush=True)

if __name__=='__main__':main()
