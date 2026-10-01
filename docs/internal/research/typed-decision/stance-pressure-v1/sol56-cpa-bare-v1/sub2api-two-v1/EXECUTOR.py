"""Owner's two additional attempts; one named old unknown, no general unlock."""
import argparse,getpass,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
DOC=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prior_cpa_bare',DOC.parent/'EXECUTOR.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
r,d=old.r,old.d
ROOT=old.ROOT/'sub2api-two-additional-v1'
INHERITED={'logical':71,'host':55,'jev':16}
LIMITS={'logical':73,'host':57,'jev':16}
HOST={**old.HOST,'endpoint':'https://sub2api.72live.com/v1/chat/completions'}
RESPONSE_MODELS=('gpt-5.6-sol','gpt-5.6')
OLD_REQUEST='94baa762f289b13f586c385707cdafd9d4463e08601efbb41ee97aee5dff1285'
NAME='risk-accepted-cpa-000068.json'


def verified():
    x=r.rt.read(ROOT/NAME);p=old.ROOT/'calls/000000';t=r.rt.read(p/'terminal.json')
    r.require(x['old_request_sha256']==OLD_REQUEST and t['binding']['request_sha256']==OLD_REQUEST
              and t['binding']['call_key']=='skills-natural-stance-sol56-cpa-bare-A:0'
              and t['status']=='unknown' and t['error']=='http_400','only_named_HTTP400')
    for path,sha in x['preserved'].items():r.require(r.digest(r.rt.read(old.ROOT/path))==sha,'old_evidence_changed')
    r.require(not (d.ROOT/'serial/000068/completion.json').exists(),'old_unknown_not_completion')
    return x


class NamedSerial(r.SerialRequests):
    def _accepted_unknown(self,directory,intent):
        x=verified();r.require(directory==self.root/'000068' and intent['label']=='skills-natural-stance-sol56-cpa-bare-A:0','named_000068_only')
        end=r.rt.read(directory/'accepted-unknown.json')
        r.require(r.rt.read(self.anchors/'000068/accepted-unknown.json')=={'sha256':r.digest(end)}
                  and end['intent_sha256']==r.digest(intent) and end['successor_sha256']==r.digest(x)
                  and end['status']=='risk_accepted_remote_unknown','named_disposition_binding')
        return end


class Adapters(d.CPAAdapters):
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
        r.require(messages[0]['content']==old.case()['user_messages'][0] and (n==1 or messages[2]['content']==old.case()['user_messages'][1]),'exact_question')
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
    r.require(not ROOT.exists(),'two_additional_exists_no_reset')
    summary=r.rt.read(old.DOC/'summary.json');r.require(summary['cumulative_debits']==INHERITED,'inherited_debits_changed')
    p=old.ROOT/'calls/000000';t=r.rt.read(p/'terminal.json');raw=r.rt.read(p/'raw.json')
    r.require(t['status']=='unknown' and t['error']=='http_400' and t['binding']==raw['binding']
              and t['binding']['request_sha256']==OLD_REQUEST,'specified_old_error')
    r.require(raw['transport']['diagnostic']['http_status']==400,'old_actual_HTTP400_required')
    r.require(len(list((d.ROOT/'serial').glob('[0-9]*')))==69,'parent_serial_changed')
    ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    paths=['batch.json','STOP.json','calls/000000/intent.json','calls/000000/request.json','calls/000000/wire.json',
           'calls/000000/raw.json','calls/000000/terminal.json','calls/000000/import.json','calls/000000/state.after.json']
    x={'schema':'mindthus.named-cpa-two-additional.v1','status':'risk_accepted_remote_unknown',
       'old_request_sha256':OLD_REQUEST,'old_serial_slot':'000068','old_call_key':t['binding']['call_key'],
       'authority':'Owner: 多试两次？ after the concrete HTTP400/unknown report, then explicitly supplied https://sub2api.72live.com/v1 and its credential; at most two additional generation calls',
       'risks_retained':['possible duplicate computation/billing','old remote overlap cannot be excluded'],
       'local_disposition_at_epoch':time.time(),'remote_status':'unknown','is_completion':False,
       'wait_proves_remote_completion':False,'new_unknown_exception':False,'preserved':{name:r.digest(r.rt.read(old.ROOT/name)) for name in paths},
       'inherited_debits':INHERITED,'new_phase_max':2}
    r.rt.write(ROOT/NAME,x);r.rt.write(DOC/NAME,x)
    serial=d.ROOT/'serial';intent=r.rt.read(serial/'000068/intent.json')
    end={'status':'risk_accepted_remote_unknown','intent_sha256':r.digest(intent),'successor_sha256':r.digest(x),
         'local_disposition_at_epoch':x['local_disposition_at_epoch'],'old_request_sha256':OLD_REQUEST,'remote_status':'unknown','is_completion':False}
    r.rt.write(serial/'000068/accepted-unknown.json',end);r.rt.write(serial/'bindings/000068/accepted-unknown.json',{'sha256':r.digest(end)})
    NamedSerial(serial).validate()
    catalog=r.rt.read(DOC/'MODEL-CATALOG.json');r.require(catalog['http_status']==200 and HOST['model'] in [v['id'] for v in catalog['raw']['data']],'model_not_listed')
    prior=r.rt.read(old.ROOT/'batch.json');source=set(prior['source_sha256'])|{str(Path(__file__).resolve().relative_to(r.REPO))}
    cfg={**prior,'schema':'mindthus.sub2api-two-additional.v1','host_configuration':HOST,'allowed_response_models':list(RESPONSE_MODELS),'catalog_sha256':r.digest(catalog),'authorization_ref':x['authority'],
         'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
         'source_sha256':{name:r.digest((r.REPO/name).read_text()) for name in source},
         'external_budget_debits':INHERITED,'limits':LIMITS,'phase_limits':{'logical':2,'host':2,'jev':0},
         'parent_batch_sha256':r.digest(prior),'named_disposition_sha256':r.digest(x),'created_at_epoch':time.time(),
         'no_retries':False,'retry_bound':2,'new_unknown_stops':True,
         'scope':'At most two new calls: first-question technical retry, then exact follow-up on first valid answer; if explicit ordinary rejection, one technical retry only. No semantic rerun.',
         'allowed_parameter_repair':'max_completion_tokens to max_tokens only if bound invalid_request_error explicitly names the replacement; same 8192 limit'}
    r.rt.write(ROOT/'batch.json',cfg);r.rt.write(ROOT/'materials.json',{});r.rt.write(DOC/'admission.json',cfg)


def checkpoint(began):
    calls=[r.rt.read(p/'terminal.json') for p in sorted((ROOT/'calls').iterdir()) if (p/'terminal.json').exists()]
    counts={'logical':len(calls),'host':len(calls),'jev':0}
    r.persist(DOC/'summary.json',{'phase_debits':counts,'cumulative_debits':{k:INHERITED[k]+counts[k] for k in INHERITED},
        'terminals':calls,'wall_seconds':time.monotonic()-began,'old_remote_unknown_retained':True,'fees':None,'simulation':False,'holdout':False})


def main():
    p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True)
    m.add_argument('--prepare',action='store_true');m.add_argument('--run',action='store_true');args=p.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:prepare();print('Named old-risk disposition and two-additional-call scope registered; no generation sent.');return
        cfg=r.rt.read(ROOT/'batch.json');r.require(cfg['limits']==LIMITS and cfg['external_budget_debits']==INHERITED,'retry_budget_identity')
        r.require(not list((ROOT/'calls').iterdir()),'no_repeat_execution')
        verified();adapter=Adapters();driver=r.Driver(ROOT,adapter);driver.serial=NamedSerial(d.ROOT/'serial');driver.stop_path=ROOT/'STOP.json';driver.serial.validate()
        if not os.environ.get('MINDTHUS_HOST_API_KEY'):os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('CPA credential (hidden, process memory only): ')
        r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_cpa_credential')
        began=time.monotonic();state=old.a.initial();turn=0;stem='skills-sol56-cpa-additional-1'
        for attempt in range(2):
            messages=[{'role':'user','content':old.case()['user_messages'][0]}]
            if turn:
                prior=r.rt.read(ROOT/'calls/000000/terminal.json');raw=r.rt.read(ROOT/'calls/000000/raw.json')
                r.require(prior['status']=='returned' and prior['binding']==raw['binding'] and r.digest(raw['transport'])==prior['raw_sha256'],'actual_first_reply_required')
                text=raw['transport']['raw']['choices'][0]['message']['content'];r.require(text==state['candidate'],'actual_history_binding')
                messages += [{'role':'assistant','content':text},{'role':'user','content':old.case()['user_messages'][1]}]
            item={'case_id':stem,'input':r.canonical(messages).decode()}
            print(json.dumps({'additional_attempt':attempt+1,'turn':turn+1,'model':HOST['model'],'endpoint':HOST['endpoint'],'effort_requested':'medium','token_parameter':adapter.token_field}),flush=True)
            terminal=driver.step(item,state,'A','draft');checkpoint(began)
            r.rt.write(DOC/('attempt-'+str(attempt+1)+'.answer.json'),{'attempt':attempt+1,'turn':turn+1,'text':terminal['response']['text'] if terminal['status']=='returned' else None,'terminal':terminal})
            print(json.dumps({'status':terminal['status'],'session_seconds':terminal['session_seconds'],'wait_seconds':terminal['active_wait_seconds'],'error':terminal['error']}),flush=True)
            if terminal['status'] in ('unknown','safety_refusal') or driver.stop_path.exists():break
            if terminal['status']=='returned':
                if turn:break
                turn=1
            elif attempt==0:
                h=(r.rt.read(ROOT/'calls/000000/raw.json')['transport'].get('diagnostic') or {}).get('http_error_response') or {}
                if h.get('param')=='max_completion_tokens' and 'max_tokens' in h.get('message','') and ('unsupported' in h.get('message','').lower() or 'use' in h.get('message','').lower()):
                    adapter.token_field='max_tokens';adapter.correction={'terminal_sha256':r.digest(terminal),'old_param':'max_completion_tokens','new_param':'max_tokens','same_limit':8192}
                    r.rt.write(ROOT/'parameter-compatibility.json',adapter.correction)
                state=old.a.initial();stem='skills-sol56-cpa-additional-2'
        checkpoint(began)

if __name__=='__main__':main()
