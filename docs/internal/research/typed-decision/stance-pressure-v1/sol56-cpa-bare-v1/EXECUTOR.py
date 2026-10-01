"""Two minimal CPA messages/turns; reuse transport, consumption and parent serial.

No CLI, system message, skill catalog, tools, JSON-generation contract, Jev or retry.
Plain supplier text is wrapped only locally for the existing answer consumer.
"""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
REPO=Path(__file__).resolve().parents[6]
sys.path.insert(0,str(REPO))
from experiments.bias_trigger import run as r,deepseek as d,primitive_ablation as a

DOC=Path(__file__).resolve().parent
ROOT=d.ROOT/'stance-pressure-sol56-cpa-bare-v1'
PARENT=DOC.parent/'sol56-medium-turn2-v1'
INHERITED={'logical':70,'host':54,'jev':16}
LIMITS={'logical':72,'host':56,'jev':16}
HOST={'model':'gpt-5.6-sol','reasoning_effort':'medium','transport_profile':'cpa_https_json',
      'endpoint':'https://cpa.rn-us.061718.xyz/v1/chat/completions','max_completion_tokens':8192}

def case():return r.rt.read(DOC/'cases.business.json')['cases'][0]

class Adapters(d.CPAAdapters):
    limits=LIMITS
    def __init__(self):self.host=dict(HOST);self.endpoint=HOST['endpoint']
    def check_configuration(self,config):
        r.require(config['host_configuration']==HOST and config['limits']==LIMITS,'bare_profile_changed')
    def outbound(self,req,config):
        self.check_configuration(config)
        r.require(req['role']=='host' and req['arm']=='A' and req['phase']=='draft' and req['requested_configuration']==HOST,'bare_A_only')
        p=req['payload'];r.require(not p['loaded_materials'] and not p['readable_paths'],'bare_no_materials')
        docs=p['source']['documents'];r.require(len(docs)==1 and docs[0]['id']=='task','single_transcript')
        messages=json.loads(docs[0]['text']);n=len(messages)
        r.require(n in (1,3) and req['sequence']==(n-1)//2,'bare_two_turns')
        r.require([m.get('role') for m in messages]==(['user'] if n==1 else ['user','assistant','user']),'bare_message_roles')
        r.require(all(set(m)=={'role','content'} and isinstance(m['content'],str) and m['content'].strip() for m in messages),'bare_message_contract')
        r.require(messages[0]['content']==case()['user_messages'][0] and (n==1 or messages[2]['content']==case()['user_messages'][1]),'exact_user_text')
        body={k:HOST[k] for k in ('model','reasoning_effort','max_completion_tokens')}
        body.update(stream=False,messages=messages)
        return {'endpoint':self.endpoint,'body':body}
    def classify(self,req,raw):
        wire=self.outbound(req,{'host_configuration':HOST,'limits':LIMITS});sha=r.digest(wire['body'])
        if raw.get('kind')=='not_sent':return 'failed',None,None,raw.get('code')
        if raw.get('kind')=='transport_error':
            diag=raw.get('diagnostic') or {};code=raw.get('code')
            if diag.get('request_sha256')!=sha:return 'unknown',None,None,code
            if diag.get('http_response_received') and diag.get('http_status') in (401,403):return 'safety_refusal',None,None,code
            if diag.get('generation_send_status')=='pre_send' and diag.get('observed_stage')=='connection_establishment_failed':return 'failed',None,None,code
            return 'unknown',None,None,code
        if raw.get('kind')!='cpa_http_json' or raw.get('endpoint')!=self.endpoint or raw.get('request_sha256')!=sha:
            return 'unknown',None,None,'cpa_receipt_binding'
        value=raw['raw'];usage=value.get('usage');choices=value.get('choices')
        if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict):return 'unknown',None,usage,'missing_cpa_terminal'
        choice=choices[0];reason=choice.get('finish_reason');message=choice.get('message')
        if not isinstance(message,dict):return ('failed' if reason=='stop' else 'unknown'),None,usage,'cpa_message_type'
        if reason=='content_filter' or message.get('refusal'):return 'safety_refusal',None,usage,'cpa_content_refusal'
        if reason not in ('stop','length','tool_calls'):return 'unknown',None,usage,'missing_cpa_finish_reason'
        if value.get('model')!=HOST['model']:return 'failed',None,usage,'cpa_model_mismatch'
        if reason!='stop' or message.get('tool_calls'):return 'failed',None,usage,'cpa_incomplete_or_tools'
        text=message.get('content')
        if not isinstance(text,str) or not text.strip():return 'failed',None,usage,'cpa_empty_answer'
        return 'returned',{'kind':'answer','text':text,'read_paths':[],'objection':''},usage,None

def prepare():
    r.require(not ROOT.exists(),'bare_episode_exists_no_reset')
    old=r.rt.read(PARENT/'summary.json')
    r.require(old['cumulative_debits']==INHERITED and old['terminal']['status']=='returned','parent_not_completed')
    serial=r.SerialRequests(d.ROOT/'serial');directories,_,_=serial.validate()
    r.require(len(directories)==68,'parent_serial_changed')
    catalog=r.rt.read(DOC/'MODEL-CATALOG.json')
    r.require(catalog['http_status']==200 and HOST['model'] in [x['id'] for x in catalog['raw']['data']],'model_not_listed')
    paths=['experiments/bias_trigger/run.py','experiments/bias_trigger/deepseek.py',
           'experiments/grounded_judgment/core.py','experiments/grounded_judgment/runtime.py','experiments/grounded_judgment/dispatch.py',
           'experiments/typed_decision/providers.py','experiments/typed_decision/relationship_live.py','experiments/typed_decision/transport_diagnostics.py',
           'experiments/jev_direct/serial.py',str(Path(__file__).resolve().relative_to(r.REPO))]
    config={'schema':'mindthus.stance-pressure.sol56-cpa-bare.v1','simulation':False,
            'authorization_ref':'Owner: 重测下CPA渠道，应该有了 (2026-10-01); original Sol5.6/medium two-turn minimal-message test, at most two generation calls',
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
            'source_sha256':{p:r.digest((r.REPO/p).read_text()) for p in paths},
            'cases_source_path':str((DOC/'cases.business.json').relative_to(r.REPO)),
            'cases_sha256':r.digest(r.rt.read(DOC/'cases.business.json')),'norms_sha256':r.digest(r.rt.read(DOC/'norms.evaluation-only.json')),
            'catalog_sha256':r.digest(catalog),'host_configuration':HOST,'host_timeout':90,'jev_timeout':60,
            'limits':LIMITS,'external_budget_debits':INHERITED,'phase_limits':{'logical':2,'host':2,'jev':0},
            'protocol':{**r.rt.read(r.PROTOCOL),'scope_this_turn':'two original user turns; no CLI, Jev, evaluator, correction or retry'},
            'parent_summary_sha256':r.digest(old),'created_at_epoch':time.time(),'holdout':False,'no_retries':True,
            'baseline_context':'API body has only actual user/assistant messages; provider-side hidden context and backend identity not observable'}
    r.no_secrets(config);ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    r.rt.write(ROOT/'batch.json',config);r.rt.write(ROOT/'materials.json',{});r.rt.write(DOC/'admission.json',config)
    r.rt.write(ROOT/'states'/(case()['case_id']+'.json'),a.initial())

def checkpoint(state,began,terminal=None):
    calls=[r.rt.read(p/'terminal.json') for p in sorted((ROOT/'calls').iterdir()) if (p/'terminal.json').exists()]
    counts={'logical':len(calls),'host':len(calls),'jev':0}
    r.persist(DOC/'summary.json',{'phase_debits':counts,'cumulative_debits':{k:INHERITED[k]+counts[k] for k in INHERITED},
        'state':state,'terminals':calls,'elapsed_wall_seconds':time.monotonic()-began,
        'simulation':False,'holdout':False,'fees':None,'proxy_downstream_requests':None})

def main():
    parser=argparse.ArgumentParser();m=parser.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--run',action='store_true');args=parser.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:prepare();print('Frozen two-turn minimal-message scope prepared; no generation sent.');return
        cfg=r.rt.read(ROOT/'batch.json');r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_cpa_credential')
        r.require(cfg['external_budget_debits']==INHERITED and cfg['phase_limits']=={'logical':2,'host':2,'jev':0},'bare_budget_identity')
        r.require(r.digest(r.rt.read(PARENT/'summary.json'))==cfg['parent_summary_sha256'],'parent_summary_changed')
        r.require(not list((ROOT/'calls').iterdir()),'one_execution_no_resubmit')
        state=r.rt.read(ROOT/'states'/(case()['case_id']+'.json'));driver=r.Driver(ROOT,Adapters())
        driver.serial=r.SerialRequests(d.ROOT/'serial');driver.stop_path=ROOT/'STOP.json';driver.serial.validate()
        began=time.monotonic();messages=[{'role':'user','content':case()['user_messages'][0]}]
        for turn in range(2):
            r.require(state['calls']['A']==turn,'turn_sequence_changed')
            if turn:
                prior=r.rt.read(ROOT/'calls/000000/terminal.json');raw=r.rt.read(ROOT/'calls/000000/raw.json')
                r.require(prior['status']=='returned' and raw['binding']==prior['binding'] and r.digest(raw['transport'])==prior['raw_sha256'],'prior_actual_return_required')
                text=raw['transport']['raw']['choices'][0]['message']['content']
                r.require(text==state['candidate'],'actual_history_mismatch')
                messages += [{'role':'assistant','content':text},{'role':'user','content':case()['user_messages'][1]}]
            item={'case_id':case()['case_id'],'input':r.canonical(messages).decode()}
            print(json.dumps({'dispatch_turn':turn+1,'model':HOST['model'],'effort_requested':'medium','message_roles':[x['role'] for x in messages],'max_generation_calls':2}),flush=True)
            terminal=driver.step(item,state,'A','draft');checkpoint(state,began,terminal)
            r.rt.write(DOC/('turn-'+str(turn+1)+'.answer.json'),{'turn':turn+1,'text':state['arms']['A']['final'] if terminal['status']=='returned' else None,'terminal':terminal})
            print(json.dumps({'terminal':terminal['status'],'delivery':state['arms']['A']['status'],'session_seconds':terminal['session_seconds'],'wait_seconds':terminal['active_wait_seconds']}),flush=True)
            if terminal['status']!='returned' or state['arms']['A']['status']!='delivered' or driver.stop_path.exists():break
        checkpoint(state,began)

if __name__=='__main__':main()
