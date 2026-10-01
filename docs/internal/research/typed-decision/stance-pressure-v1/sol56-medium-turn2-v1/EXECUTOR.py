"""One native continuation using the existing CLI runner, driver and shared serial."""
import argparse,hashlib,importlib.util,json,os,subprocess,time
from pathlib import Path
from experiments.bias_trigger import run as r,deepseek as d,primitive_ablation as a
from experiments.jev_direct.host_boundary import parse_events

DOC=r.REPO/'docs/internal/research/typed-decision/stance-pressure-v1/sol56-medium-turn2-v1'
PARENT=DOC.parent/'sol56-medium-v1'
PRIOR=d.ROOT/'stance-pressure-sol56-medium-v1'
ROOT=d.ROOT/'stance-pressure-sol56-medium-turn2-v1'
INHERITED={'logical':69,'host':53,'jev':16}
LIMITS={'logical':70,'host':54,'jev':16}
spec=importlib.util.spec_from_file_location('sol56_parent',PARENT/'EXECUTOR.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)

class Adapters(parent.Adapters):
    def outbound(self,req,config):
        wire=super().outbound(req,config)
        wire.update(resume_thread_id=config['resume']['thread_id'],resume_working_directory=config['resume']['cwd'],
                    resume_parent_terminal_sha256=config['resume']['terminal_sha256'])
        return wire

    def invoke(self,req,wire,directory,config):
        from experiments.jev_direct.pilot import wire as existing
        r.require(wire['resume_thread_id']==config['resume']['thread_id'],'resume_identity')
        r.rt.write(directory/'schema.api.json',wire['api_schema'])
        cmd=[parent.BINARY,'-C',wire['resume_working_directory'],'--sandbox','read-only','exec','resume',
             '--skip-git-repo-check','-m',wire['model'],'-c','model_reasoning_effort='+json.dumps(wire['effort']),
             '-c','features.shell_tool=false','--json','--output-schema',str(directory/'schema.api.json'),
             '-o',str(directory/'reply.json')]
        for option in wire['overrides']:cmd+=['-c',option]
        cmd+=[wire['resume_thread_id'],'-']
        r.rt.write(directory/'cli-command.json',{'argv':cmd,'parent':config['resume'],'generation_retries':0})
        env=os.environ.copy()
        for name in ('TYPESAFE_API_KEY','OPENROUTER_API_KEY','MINDTHUS_HOST_API_KEY'):env.pop(name,None)
        proc=existing._run_cli(cmd,wire['prompt'],env,config['host_timeout'])
        return {'kind':'cli','events':parse_events(proc.stdout),'stdout':proc.stdout,'stderr':proc.stderr,
                'returncode':proc.returncode,'reply_text':(directory/'reply.json').read_text() if (directory/'reply.json').exists() else None}

    def classify(self,req,raw):
        if raw.get('kind')=='cli':
            ids={e.get('thread_id') for e in raw['events'] if e.get('type')=='thread.started'}
            expected=r.rt.read(ROOT/'batch.json')['resume']['thread_id']
            if ids!={expected}:return 'unknown',None,None,'resume_thread_mismatch'
        return r.classify(req,raw)

def prepare():
    r.require(not ROOT.exists(),'one_continuation_exists_no_reset')
    r.require(not (PRIOR/'STOP.json').exists() and not (PRIOR/'transport-stop-v2.json').exists(),'parent_stopped')
    old=r.rt.read(PARENT/'summary.json');raw=r.rt.read(PRIOR/'calls/000000/raw.json')
    r.require(old['cumulative_debits']==INHERITED and old['terminal']['status']=='returned','parent_not_completed')
    r.require(old['terminal']['binding']==raw['binding'],'parent_binding')
    ids=[e['thread_id'] for e in raw['transport']['events'] if e.get('type')=='thread.started']
    r.require(len(ids)==1,'parent_thread_ambiguous');ctx=r.rt.read(PARENT/'CONTEXT-OBSERVATION.json')
    r.require(ids[0]==ctx['thread_id'],'parent_context_mismatch')
    archive=Path(ctx['archive_path']);data=archive.read_bytes();rows=[json.loads(x) for x in data.decode().splitlines()]
    turns=[x['payload'] for x in rows if x['type']=='turn_context']
    replies=[x['payload'] for x in rows if x['type']=='response_item' and x['payload'].get('type')=='message' and x['payload'].get('role')=='assistant']
    r.require(len(turns)==len(replies)==1,'parent_history_changed')
    actual='\n'.join(x.get('text','') for x in replies[0]['content'])
    r.require(json.loads(actual)==json.loads(raw['transport']['reply_text']),'actual_parent_reply_required')
    turn=turns[0];r.require(turn['model']=='gpt-5.6-sol' and turn['effort']=='medium' and turn['sandbox_policy']=={'type':'read-only'},'parent_configuration')
    serial=r.SerialRequests(d.ROOT/'serial');serial.validate()
    r.require(len(list(serial.root.glob('[0-9]*')))==67,'parent_serial_changed')
    config=r.rt.read(PRIOR/'batch.json');paths=set(config['source_sha256'])|{str(Path(__file__).resolve().relative_to(r.REPO))}
    resume={'thread_id':ids[0],'cwd':turn['cwd'],'archive_path':str(archive),'archive_before_bytes':len(data),
            'archive_before_sha256':hashlib.sha256(data).hexdigest(),'terminal_sha256':r.digest(old['terminal']),
            'raw_parent_reply_sha256':r.digest(raw['transport']['reply_text']),'parent_summary_sha256':r.digest(old)}
    value={**{k:v for k,v in config.items() if not k.startswith('local_')},
           'schema':'mindthus.stance-pressure.sol56-turn2.v1',
           'authorization_ref':'Owner: 第二回合补成 [exact cases.business.json text] (2026-10-01); one native continuation only',
           'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
           'source_sha256':{p:r.digest((r.REPO/p).read_text()) for p in paths},
           'cases_source_path':str((DOC/'cases.business.json').relative_to(r.REPO)),
           'cases_sha256':r.digest(r.rt.read(DOC/'cases.business.json')),'norms_sha256':r.digest(r.rt.read(DOC/'norms.evaluation-only.json')),
           'limits':LIMITS,'external_budget_debits':INHERITED,'phase_limits':{'logical':1,'host':1,'jev':0},
           'protocol':{**config['protocol'],'scope_this_turn':'one exact second user turn on the same completed Sol5.6/medium CLI thread'},
           'resume':resume,'primary_cases':['skills-natural-stance-sol56-medium-turn2'],'created_at_epoch':time.time(),
           'parent_summary_sha256':r.digest(old)}
    ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    r.rt.write(ROOT/'batch.json',value);r.rt.write(ROOT/'materials.json',{});r.rt.write(DOC/'admission.json',value)
    r.rt.write(ROOT/'states/skills-natural-stance-sol56-medium-turn2.json',a.initial())

def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--run',action='store_true');args=p.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:prepare();print('One bound native continuation prepared; no request sent.');return
        cfg=r.rt.read(ROOT/'batch.json');resume=cfg['resume']
        r.require(cfg['host_configuration']==parent.HOST and cfg['limits']==LIMITS and cfg['external_budget_debits']==INHERITED,'configuration_changed')
        r.require(not list((ROOT/'calls').iterdir()),'one_attempt_no_resubmit')
        r.require(r.digest(r.rt.read(PARENT/'summary.json'))==resume['parent_summary_sha256'],'parent_summary_changed')
        r.require(hashlib.sha256(Path(resume['archive_path']).read_bytes()).hexdigest()==resume['archive_before_sha256'],'parent_archive_changed')
        item=r.rt.read(DOC/'cases.business.json')['cases'][0];state=r.rt.read(ROOT/'states'/(item['case_id']+'.json'))
        driver=r.Driver(ROOT,Adapters());driver.serial=r.SerialRequests(d.ROOT/'serial');driver.stop_path=ROOT/'STOP.json';driver.serial.validate()
        print(json.dumps({'dispatch':item['case_id'],'resume_thread':resume['thread_id'],'max_calls':1,'Jev_calls':0}),flush=True)
        terminal=driver.step(item,state,'A','draft');r.rt.write(DOC/'answer.json',state)
        data=Path(resume['archive_path']).read_bytes()
        r.rt.write(DOC/'summary.json',{'phase_debits':{'logical':1,'host':1,'jev':0},'cumulative_debits':LIMITS,
                    'state':state,'terminal':terminal,'holdout':False,'simulation':False,
                    'archive_prior_prefix_unchanged':hashlib.sha256(data[:resume['archive_before_bytes']]).hexdigest()==resume['archive_before_sha256']})
        print(json.dumps({'terminal':terminal['status'],'delivery_status':state['arms']['A']['status']}),flush=True)

if __name__=='__main__':main()
