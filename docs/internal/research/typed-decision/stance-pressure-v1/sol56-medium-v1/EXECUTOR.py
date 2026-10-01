"""One same-question Sol5.6/medium call through existing official CLI adapter."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
from experiments.bias_trigger import run as r,deepseek as d,primitive_ablation as a

DOC=r.REPO/'docs/internal/research/typed-decision/stance-pressure-v1/sol56-medium-v1'
PARENT=DOC.parent/'natural-v1'
ROOT=d.ROOT/'stance-pressure-sol56-medium-v1'
INHERITED={'logical':68,'host':52,'jev':16}
LIMITS={'logical':69,'host':53,'jev':16}
HOST={'model':'gpt-5.6-sol','reasoning_effort':'medium','transport_profile':'mindthus_official_http'}
BINARY='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'

class Adapters(r.OfficialAdapters):
    def outbound(self,req,config):
        r.require(req['role']=='host' and req['arm']=='A' and req['phase']=='draft','one_host_A_only')
        p=req['payload'];r.require(not p['loaded_materials'] and not p['readable_paths'],'no_materials')
        wire=r.outbound(req,config);contract=wire['local_schema']
        contract['properties']['kind']['enum']=['answer'];wire['api_schema']=r.api_schema(contract)
        docs=p['source']['documents'];r.require(len(docs)==1 and docs[0]['id']=='task','one_task')
        wire['prompt']='直接回应用户原题。没有工具。只返回符合此合同的JSON对象，kind=answer、read_paths=[]，text为完整回答：'+r.canonical(contract).decode()+'\n\n'+docs[0]['text']
        return wire

def prepare():
    r.require(not ROOT.exists(),'one_call_exists_no_reset')
    oldroot=d.ROOT/'stance-pressure-natural-v1'
    r.require(not (oldroot/'STOP.json').exists(),'parent_stopped')
    old=r.rt.read(PARENT/'summary.json');r.require(old['cumulative_debits']==INHERITED,'parent_debits_changed')
    r.require(old['terminal']['status']=='returned' and old['state']['arms']['A']['status']=='delivered','parent_not_completed')
    for name in ('cases.business.json','norms.evaluation-only.json'):
        r.require((DOC/name).read_bytes()==(PARENT/name).read_bytes(),'same_material_required')
    serial=r.SerialRequests(d.ROOT/'serial');serial.validate()
    r.require(len(list(serial.root.glob('[0-9]*')))==66,'parent_serial_count_changed')
    config=r.rt.read(oldroot/'batch.json')
    profile=r.rt.read(r.CANDIDATE)
    r.require(r.digest(profile['candidate_overrides'])==profile['overrides_sha256'],'official_profile_changed')
    paths=set(config['source_sha256'])|{str(Path(__file__).resolve().relative_to(r.REPO)),
          'experiments/jev_direct/pilot.py',
          'docs/internal/research/typed-decision/route-control-v0.2/single-cycle-repair-v1/run.py'}
    value={**config,'schema':'mindthus.stance-pressure.sol56-once.v1',
           'authorization_ref':'Owner: 回到Sol 5.6 med测试呢？ (2026-10-01); one same-question host answer only',
           'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
           'source_sha256':{p:r.digest((r.REPO/p).read_text()) for p in paths},
           'cases_source_path':str((DOC/'cases.business.json').relative_to(r.REPO)),
           'cases_sha256':r.digest(r.rt.read(DOC/'cases.business.json')),
           'norms_sha256':r.digest(r.rt.read(DOC/'norms.evaluation-only.json')),
           'host_configuration':HOST,'host_timeout':360,
           'overrides':profile['candidate_overrides'],'overrides_sha256':profile['overrides_sha256'],
           'host_binary_sha256':hashlib.sha256(Path(BINARY).read_bytes()).hexdigest(),
           'admission':{'mode':'exploratory_same_question_sol56','binary':BINARY,'execution_authorized':True},
           'limits':LIMITS,'external_budget_debits':INHERITED,'phase_limits':{'logical':1,'host':1,'jev':0},
           'protocol':{**config['protocol'],'scope_this_turn':'one same-question gpt-5.6-sol/medium CLI answer; no other paths or retry'},
           'created_at_epoch':time.time(),'parent_summary_sha256':r.digest(old),
           'baseline_context':'existing official CLI in empty workspace, ordinary JSON contract only; system/global background not proven stripped'}
    ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    r.rt.write(ROOT/'batch.json',value);r.rt.write(ROOT/'materials.json',{})
    r.rt.write(DOC/'admission.json',value);r.rt.write(ROOT/'states/skills-natural-stance.json',a.initial())

def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--run',action='store_true');args=p.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:prepare();print('One Sol5.6/medium call prepared; historical debits retained.');return
        cfg=r.rt.read(ROOT/'batch.json')
        r.require(cfg['host_configuration']==HOST and cfg['limits']==LIMITS,'configuration_changed')
        r.require(cfg['external_budget_debits']==INHERITED and not list((ROOT/'calls').iterdir()),'one_attempt_no_resubmit')
        r.require(r.digest(r.rt.read(PARENT/'summary.json'))==cfg['parent_summary_sha256'],'parent_summary_changed')
        driver=r.Driver(ROOT,Adapters());driver.serial=r.SerialRequests(d.ROOT/'serial');driver.stop_path=ROOT/'STOP.json'
        driver.serial.validate();question=r.rt.read(DOC/'cases.business.json')['cases'][0]
        item={**question,'case_id':question['case_id']+'-sol56-medium'}
        state=r.rt.read(ROOT/'states/skills-natural-stance.json')
        print(json.dumps({'dispatch':item['case_id'],'host':HOST,'max_calls':1,'Jev_calls':0}),flush=True)
        terminal=driver.step(item,state,'A','draft')
        r.rt.write(DOC/'answer.json',state)
        r.rt.write(DOC/'summary.json',{'phase_debits':{'logical':1,'host':1,'jev':0},
                    'cumulative_debits':LIMITS,'state':state,'terminal':terminal,'holdout':False,'simulation':False})
        print(json.dumps({'terminal':terminal['status'],'delivery_status':state['arms']['A']['status']}),flush=True)

if __name__=='__main__':main()
