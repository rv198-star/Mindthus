"""GPT-5.5 comparison of the approved variant; same two turns, no retry/client."""
import argparse,getpass,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
DOC=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('approved_sub2api',DOC.parent/'sol56-cpa-bare-v1/sub2api-two-v1/EXECUTOR.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
r,d,a=prior.r,prior.d,prior.old.a
ROOT=d.ROOT/'stance-pressure-gpt55-prompt-essential-v1'
PARENT=DOC.parent/'sol56-prompt-essential-v1'
PARENT_ROOT=d.ROOT/'stance-pressure-sol56-prompt-essential-v1'
INHERITED={'logical':75,'host':59,'jev':16}
LIMITS={'logical':77,'host':61,'jev':16}
HOST={**prior.HOST,'model':'gpt-5.5'}
RESPONSE_MODELS=('gpt-5.5','gpt-5.5-2026-04-23')

def case():return r.rt.read(DOC/'cases.business.json')['cases'][0]

class Adapters(prior.Adapters):
    limits=LIMITS
    def __init__(self):self.host=dict(HOST);self.endpoint=HOST['endpoint'];self.token_field='max_completion_tokens';self.correction=None
    def check_configuration(self,cfg):
        r.require(cfg['host_configuration']==HOST and cfg['limits']==LIMITS,'sub2api_profile_changed')
    def outbound(self,req,cfg):
        self.check_configuration(cfg)
        r.require(req['role']=='host' and req['arm']=='A' and req['phase']=='draft' and req['requested_configuration']==HOST,'bare_A_only')
        p=req['payload'];r.require(not p['loaded_materials'] and not p['readable_paths'],'bare_no_materials')
        docs=p['source']['documents'];r.require(len(docs)==1 and docs[0]['id']=='task','single_transcript')
        messages=json.loads(docs[0]['text']);n=len(messages)
        r.require(n in (1,3) and req['sequence']==(n-1)//2,'bare_two_turns')
        r.require([m.get('role') for m in messages]==(['user'] if n==1 else ['user','assistant','user']),'bare_roles')
        r.require(all(set(m)=={'role','content'} and isinstance(m['content'],str) and m['content'].strip() for m in messages),'bare_messages')
        r.require(messages[0]['content']==case()['user_messages'][0] and (n==1 or messages[2]['content']==case()['user_messages'][1]),'exact_question')
        body={k:HOST[k] for k in ('model','reasoning_effort','max_completion_tokens')};body.update(stream=False,messages=messages)
        wire={'endpoint':self.endpoint,'body':body}
        if self.token_field=='max_tokens':
            r.require(self.correction is not None,'parameter_fix_requires_explicit_error')
            body['max_tokens']=body.pop('max_completion_tokens')
            wire['compatibility']={'token_parameter':'max_tokens','based_on':self.correction}
        else:r.require(self.token_field=='max_completion_tokens','unsupported_profile')
        return wire
    def classify(self,req,raw):
        wire=self.outbound(req,{'host_configuration':HOST,'limits':LIMITS});sha=r.digest(wire['body'])
        if raw.get('kind')=='not_sent':return 'failed',None,None,raw.get('code')
        if raw.get('kind')=='transport_error':
            diag=raw.get('diagnostic') or {};h=diag.get('http_error_response') or {};error=raw.get('code')
            if diag.get('request_sha256')!=sha:return 'unknown',None,None,error
            if diag.get('http_response_received'):
                code=h.get('code');kind=h.get('type')
                if diag.get('http_status') in (401,403) or code in ('content_policy_violation','content_filter','safety_violation','permission_denied','access_denied','insufficient_permissions') or kind in ('authentication_error','permission_error'):
                    return 'safety_refusal',None,None,error
                if diag.get('http_status')==400 and h.get('body_status')=='json_error_object' and kind=='invalid_request_error':
                    return 'failed',None,None,error
            if diag.get('generation_send_status')=='pre_send' and diag.get('observed_stage')=='connection_establishment_failed':return 'failed',None,None,error
            return 'unknown',None,None,error
        if raw.get('kind')!='cpa_http_json' or raw.get('endpoint')!=self.endpoint or raw.get('request_sha256')!=sha:return 'unknown',None,None,'receipt_binding'
        value=raw['raw'];usage=value.get('usage');choices=value.get('choices')
        if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict):return 'unknown',None,usage,'missing_terminal'
        choice=choices[0];reason=choice.get('finish_reason');message=choice.get('message')
        if not isinstance(message,dict):return ('failed' if reason=='stop' else 'unknown'),None,usage,'message_type'
        if reason=='content_filter' or message.get('refusal'):return 'safety_refusal',None,usage,'content_refusal'
        if reason not in ('stop','length','tool_calls'):return 'unknown',None,usage,'missing_finish_reason'
        if value.get('model') not in RESPONSE_MODELS:return 'failed',None,usage,'model_mismatch'
        if reason!='stop' or message.get('tool_calls'):return 'failed',None,usage,'incomplete_or_tools'
        text=message.get('content')
        if not isinstance(text,str) or not text.strip():return 'failed',None,usage,'empty_answer'
        return 'returned',{'kind':'answer','text':text,'read_paths':[],'objection':''},usage,None


def prepare():
    r.require(not ROOT.exists(),'variant_exists_no_reset')
    parent=r.rt.read(PARENT/'summary.json')
    r.require(parent['cumulative_debits']==INHERITED and len(parent['terminals'])==2
              and all(t['status']=='returned' for t in parent['terminals']),'parent_delivery_or_debits')
    directories,_,_=prior.NamedSerial(d.ROOT/'serial').validate()
    r.require(len(directories)==73,'parent_serial_changed')
    parent_cfg=r.rt.read(PARENT_ROOT/'batch.json')
    catalog=r.rt.read(prior.DOC/'MODEL-CATALOG.json')
    r.require(catalog['http_status']==200 and HOST['model'] in [m['id'] for m in catalog['raw']['data']],'gpt55_not_listed')
    r.require(case()['user_messages']==r.rt.read(PARENT/'cases.business.json')['cases'][0]['user_messages'],'paired_questions_changed')
    r.require((DOC/'norms.evaluation-only.json').read_bytes()==(PARENT/'norms.evaluation-only.json').read_bytes(),'paired_norms_changed')
    source=set(parent_cfg['source_sha256'])|{str(Path(__file__).resolve().relative_to(r.REPO))}
    cfg={**parent_cfg,'schema':'mindthus.gpt55-prompt-essential.v1','simulation':False,'host_configuration':HOST,'allowed_response_models':list(RESPONSE_MODELS),
         'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
         'source_sha256':{name:r.digest((r.REPO/name).read_text()) for name in source},
         'cases_source_path':str((DOC/'cases.business.json').relative_to(r.REPO)),
         'cases_sha256':r.digest(r.rt.read(DOC/'cases.business.json')),
         'norms_sha256':r.digest(r.rt.read(DOC/'norms.evaluation-only.json')),
         'authorization_ref':'Owner: 那我们测下5.5吧 (2026-10-01), same current two-turn variant, GPT-5.5/medium, at most 2 new host generations',
         'external_budget_debits':INHERITED,'limits':LIMITS,'phase_limits':{'logical':2,'host':2,'jev':0},
         'parent_batch_sha256':r.digest(parent_cfg),'parent_summary_sha256':r.digest(parent),
         'scope':'Two first valid replies; second continues actual new first; no technical or semantic retry, Jev, reviewer or correction',
         'no_retries':True,'retry_bound':0,'allowed_parameter_repair':None,
         'created_at_epoch':time.time(),'holdout':False,
         'protocol':{**parent_cfg['protocol'],'scope_this_turn':'two revised conceptual-stance user turns; existing NamedSerial disposition only, no new unknown exception'}}
    r.no_secrets(cfg);ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    r.rt.write(ROOT/'batch.json',cfg);r.rt.write(ROOT/'materials.json',{})
    r.rt.write(DOC/'admission.json',cfg);r.rt.write(ROOT/'states'/(case()['case_id']+'.json'),a.initial())

def checkpoint(state,began):
    ts=[r.rt.read(p/'terminal.json') for p in sorted((ROOT/'calls').iterdir()) if (p/'terminal.json').exists()]
    new={'logical':len(ts),'host':len(ts),'jev':0}
    r.persist(DOC/'summary.json',{'phase_debits':new,'cumulative_debits':{k:INHERITED[k]+new[k] for k in INHERITED},
        'state':state,'terminals':ts,'wall_seconds':time.monotonic()-began,'fees':None,'proxy_downstream_requests':None,
        'simulation':False,'holdout':False,'old_remote_unknown_retained':True})

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true');args=p.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:prepare();print('Two revised turns frozen; zero generation sent.');return
        cfg=r.rt.read(ROOT/'batch.json')
        r.require(cfg['limits']==LIMITS and cfg['external_budget_debits']==INHERITED and cfg['no_retries'],'variant_budget_identity')
        r.require(r.digest(r.rt.read(PARENT/'summary.json'))==cfg['parent_summary_sha256'],'parent_changed')
        r.require(not list((ROOT/'calls').iterdir()),'no_repeat_execution')
        if not os.environ.get('MINDTHUS_HOST_API_KEY'):
            os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('Sub2API credential (hidden, process memory only): ')
        r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_authorized_credential')
        driver=r.Driver(ROOT,Adapters());driver.serial=prior.NamedSerial(d.ROOT/'serial');driver.stop_path=ROOT/'STOP.json';driver.serial.validate()
        state=r.rt.read(ROOT/'states'/(case()['case_id']+'.json'));began=time.monotonic()
        messages=[{'role':'user','content':case()['user_messages'][0]}]
        for turn in range(2):
            r.require(state['calls']['A']==turn,'turn_sequence')
            if turn:
                t=r.rt.read(ROOT/'calls/000000/terminal.json');raw=r.rt.read(ROOT/'calls/000000/raw.json')
                r.require(t['status']=='returned' and raw['binding']==t['binding'] and r.digest(raw['transport'])==t['raw_sha256'],'actual_first_return_binding')
                text=raw['transport']['raw']['choices'][0]['message']['content']
                r.require(text==state['candidate'],'actual_history_required')
                messages += [{'role':'assistant','content':text},{'role':'user','content':case()['user_messages'][1]}]
            item={'case_id':case()['case_id'],'input':r.canonical(messages).decode()}
            print(json.dumps({'turn':turn+1,'model':HOST['model'],'effort_requested':'medium','message_roles':[m['role'] for m in messages],'no_retries':True}),flush=True)
            terminal=driver.step(item,state,'A','draft');checkpoint(state,began)
            answer=terminal['response']['text'] if terminal['status']=='returned' else None
            r.rt.write(DOC/('turn-'+str(turn+1)+'.answer.json'),{'turn':turn+1,'text':answer,'terminal':terminal})
            if answer is not None:(DOC/('turn-'+str(turn+1)+'.reply.txt')).write_text(answer,encoding='utf-8')
            print(json.dumps({'status':terminal['status'],'delivery':state['arms']['A']['status'],'session_seconds':terminal['session_seconds'],'wait_seconds':terminal['active_wait_seconds'],'error':terminal['error']}),flush=True)
            if terminal['status']!='returned' or state['arms']['A']['status']!='delivered' or driver.stop_path.exists():break
        checkpoint(state,began)

if __name__=='__main__':main()
