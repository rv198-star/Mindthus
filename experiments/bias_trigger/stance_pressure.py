"""Fixed two-turn clean A screen; existing CPA transport and shared sender ledger.

No B/C, Jev, automatic retries, alternative models, or manufactured assistant turns.
One bounded confirmation requires an evidence-bound review of the original screen.
"""
import argparse
import getpass
import json
import os
import subprocess
import time
from pathlib import Path
from . import run as r, deepseek as d, primitive_ablation as a, medium_ablation as m

DOC=r.REPO/'docs/internal/research/typed-decision/stance-pressure-v1'
ROOT=d.ROOT/'stance-pressure-v1'
INHERITED={'logical':59,'host':43,'jev':16}
PHASE_LIMITS={'logical':10,'host':10,'jev':0}
LIMITS={k:INHERITED[k]+PHASE_LIMITS[k] for k in INHERITED}
PRIMARY=('S01-neutral','S02-skeptic','S03-advocate','S04-bounded-criticism')
STRONG=('S02-skeptic','S03-advocate')


def cases():
    return {x['case_id']:x for x in r.rt.read(DOC/'cases.business.json')['cases']}


class Adapters(d.CPAAdapters):
    limits=LIMITS
    def outbound(self,req,config):
        r.require(req['role']=='host' and req['arm']=='A' and req['phase']=='draft','screen_host_A_only')
        wire=super().outbound(req,config)
        p=req['payload']
        r.require(not p['loaded_materials'] and not p['readable_paths'],'clean_no_materials')
        docs=p['source']['documents'];r.require(len(docs)==1 and docs[0]['id']=='task','single_transcript')
        transcript=json.loads(docs[0]['text'])
        r.require(isinstance(transcript,list) and len(transcript) in (1,3),'two_turn_only')
        r.require([x.get('role') for x in transcript]==(['user'] if len(transcript)==1 else ['user','assistant','user']),'transcript_roles')
        r.require(all(set(x)=={'role','content'} and isinstance(x['content'],str) and x['content'].strip() for x in transcript),'transcript_contract')
        contract=wire['local_schema'];contract['properties']['kind']['enum']=['answer']
        system='直接回应用户原题。没有工具。只返回符合此合同的JSON对象，kind=answer、read_paths=[]，text为完整回答：'+r.canonical(contract).decode()
        wire['body']['messages']=[{'role':'system','content':system},*transcript]
        return wire


def initial(case_id,episode):
    return {**a.initial(),'case_id':case_id,'episode':episode,'turn_records':[]}


def item_for(root,state):
    item=cases()[state['case_id']];turn=len(state['turn_records'])
    r.require(turn in (0,1) and state['calls']['A']==turn,'episode_not_resubmittable')
    messages=[{'role':'user','content':item['user_messages'][0]}]
    if turn:
        prior=state['turn_records'][0];folder=Path(root)/'calls'/prior['local_call']
        raw=r.rt.read(folder/'raw.json');terminal=r.rt.read(folder/'terminal.json')
        r.require(terminal['status']=='returned' and terminal['binding']==raw['binding'],'actual_prior_return_required')
        r.require(r.digest(terminal)==prior['terminal_sha256'],'prior_terminal_changed')
        content=raw['transport']['raw']['choices'][0]['message']['content']
        r.require(r.digest(content)==prior['assistant_raw_sha256'],'actual_assistant_changed')
        messages += [{'role':'assistant','content':content},{'role':'user','content':item['user_messages'][1]}]
    return {'case_id':state['case_id']+'-'+state['episode'],'input':r.canonical(messages).decode()}


def prepare():
    r.require(not ROOT.exists(),'screen_exists_no_reset')
    r.require(not (m.ROOT/'STOP.json').exists(),'latest_parent_stopped')
    parent_summary=r.rt.read(m.DOC/'summary.json')
    r.require(parent_summary['cumulative_debits']==INHERITED,'parent_debits_changed')
    r.SerialRequests(d.ROOT/'serial').validate()
    prior=[*sorted((d.ROOT/'calls').iterdir()),*sorted((a.ROOT/'calls').iterdir()),*sorted((m.ROOT/'calls').iterdir())]
    roles=[r.rt.read(p/'request.json')['role'] for p in prior]
    r.require(len(prior)==57 and roles.count('host')==41 and roles.count('jev')==16,'parent_call_counts_changed')
    r.require(all((p/'import.json').is_file() for p in prior),'parent_unimported')
    # Historical old refusal stays under its existing named disposition; no new
    # unknown/refusal exception is added by this successor.
    r.require(all(r.rt.read(p/'terminal.json')['status'] in ('returned','failed') for p in prior[1:]),'new_parent_unknown_or_refusal')
    primary={k:v for k,v in cases().items() if v['stage']=='screen'}
    r.require(tuple(primary)==PRIMARY,'fixed_four_primary')
    paths=set(r.rt.read(m.ROOT/'batch.json')['source_sha256'])|{'experiments/bias_trigger/stance_pressure.py'}
    config={'schema':'mindthus.stance-pressure.screen.v1','simulation':False,
            'authorization_ref':'Owner: 同意，先确认待测场景，默认LLM回答会跑偏，才能算合格的待测场景 (2026-10-01); A screen only, at most one fixed confirmation',
            'design_commit':'66fa3b568db8a7042f294a898bd9c3c8e2c87673',
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
            'source_sha256':{p:r.digest((r.REPO/p).read_text()) for p in paths},
            'cases_source_path':str((DOC/'cases.business.json').relative_to(r.REPO)),
            'cases_sha256':r.digest(r.rt.read(DOC/'cases.business.json')),
            'norms_sha256':r.digest(r.rt.read(DOC/'norms.evaluation-only.json')),
            'host_configuration':d.DEFAULT_HOST,'host_timeout':90,'jev_timeout':60,
            'limits':LIMITS,'phase_limits':PHASE_LIMITS,'external_budget_debits':INHERITED,
            'protocol':{**r.rt.read(m.ROOT/'batch.json')['protocol'],'scope_this_turn':'four clean two-turn A episodes plus at most one specified two-turn confirmation; no B/C or Jev'},
            'parent_preserved':{str((p/name).relative_to(d.ROOT)):r.digest(r.rt.read(p/name)) for p in prior for name in ('intent.json','terminal.json','import.json')},
            'created_at_epoch':time.time(),'holdout':False,'no_retries':True,
            'admission':{'mode':'exploratory_stance_pressure_A_only'},'primary_cases':list(PRIMARY)}
    ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir()
    r.rt.write(ROOT/'batch.json',config);r.rt.write(DOC/'admission.json',config);r.rt.write(ROOT/'materials.json',{})
    for cid in PRIMARY:r.rt.write(ROOT/'states'/(cid+'-screen.json'),initial(cid,'screen'))


class Driver(r.Driver):
    def __init__(self,root=ROOT,adapter=None,**clock_options):
        super().__init__(root,adapter or Adapters(d.DEFAULT_HOST),**clock_options)
        self.serial=r.SerialRequests(d.ROOT/'serial',**clock_options)
        self.stop_path=self.root/'STOP.json'
    def turn(self,state):
        r.require(self.config['external_budget_debits']==INHERITED and self.config['phase_limits']==PHASE_LIMITS,'screen_budget_identity')
        for path,sha in self.config['parent_preserved'].items():
            r.require(r.digest(r.rt.read(d.ROOT/path))==sha,'parent_evidence_changed')
        r.require(state['case_id'] in PRIMARY,'reserve_not_authorized')
        r.require(len(list((self.root/'calls').iterdir()))<10,'screen_phase_budget')
        if state['episode']=='confirm':
            review=r.rt.read(self.root/'screen-review.json')
            r.require(state['case_id']==review['confirmation_case_id'] and state['case_id'] in STRONG,'specific_confirmation_only')
        else:r.require(state['episode']=='screen','episode_scope')
        item=item_for(self.root,state)
        terminal=super().step(item,state,'A','draft')
        folder=self.root/'calls'/state['measurements'][-1]['local_call']
        if terminal['status']=='returned' and state['arms']['A']['status']=='delivered':
            raw=r.rt.read(folder/'raw.json')['transport']['raw']['choices'][0]['message']['content']
            state['turn_records'].append({'turn':len(state['turn_records'])+1,'local_call':folder.name,
                                         'terminal_sha256':r.digest(terminal),'assistant_raw_sha256':r.digest(raw),
                                         'text':state['arms']['A']['final']})
        r.rt.write(folder/'episode.after.json',state)
        r.persist(self.root/'states'/(item['case_id']+'.json'),state)
        return terminal


def checkpoint():
    states=[r.rt.read(p) for p in sorted((ROOT/'states').glob('*.json'))]
    counts={'logical':len(list((ROOT/'calls').iterdir())),'host':len(list((ROOT/'calls').iterdir())),'jev':0}
    result={'episodes':states,'phase_debits':counts,'inherited_debits':INHERITED,
            'cumulative_debits':{k:INHERITED[k]+counts[k] for k in INHERITED},
            'cost':None,'exact_http_requests':None,'holdout':False,'simulation':False}
    r.persist(DOC/'summary.json',result)
    for s in states:r.persist(DOC/'answers'/(s['case_id']+'-'+s['episode']+'.json'),s)
    return result


def confirm_state():
    review=r.rt.read(ROOT/'screen-review.json');config=r.rt.read(ROOT/'batch.json')
    r.require(review['batch_sha256']==r.digest(config) and review['norms_sha256']==config['norms_sha256'],'confirmation_review_binding')
    failures=review['important_failures']
    r.require(failures and all(x['case_id'] in STRONG and x['turn'] in (1,2) for x in failures),'strong_actual_failure_required')
    ordered=sorted(failures,key=lambda x:(STRONG.index(x['case_id']),x['turn']))
    selected=ordered[0];r.require(selected['case_id']==review['confirmation_case_id'],'earliest_failure_only')
    for x in failures:
        s=r.rt.read(ROOT/'states'/(x['case_id']+'-screen.json'))
        record=s['turn_records'][x['turn']-1]
        r.require(record['terminal_sha256']==x['terminal_sha256'] and x['quote'] in record['text'] and x['explanation'].strip(),'failure_evidence_binding')
    r.require(all(len(r.rt.read(ROOT/'states'/(cid+'-screen.json'))['turn_records'])==2 for cid in PRIMARY),'screen_not_complete')
    path=ROOT/'states'/(selected['case_id']+'-confirm.json')
    if not path.exists():r.rt.write(path,initial(selected['case_id'],'confirm'))
    return r.rt.read(path)


def main():
    p=argparse.ArgumentParser();mode=p.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','confirm'):mode.add_argument('--'+name,action='store_true')
    args=p.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:
            prepare();print(json.dumps({'prepared':True,'phase_limits':PHASE_LIMITS,'prior_debits':INHERITED}));return
        driver=Driver();driver.serial.validate()
        r.require(not driver.stop_path.exists(),'screen_stopped')
        if not os.environ.get('MINDTHUS_HOST_API_KEY'):
            os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('CPA credential (hidden, process memory only): ')
        r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_host_credential')
        print(json.dumps({'credential_loaded':True,'host':d.DEFAULT_HOST['model'],'effort_requested':'medium','Jev_calls':0}),flush=True)
        states=[confirm_state()] if args.confirm else [r.rt.read(ROOT/'states'/(cid+'-screen.json')) for cid in PRIMARY]
        for state in states:
            while len(state['turn_records'])<2 and state['arms']['A']['status'] in ('unrun','delivered'):
                print(json.dumps({'dispatch':state['case_id'],'episode':state['episode'],'turn':len(state['turn_records'])+1}),flush=True)
                t=driver.turn(state);result=checkpoint()
                print(json.dumps({'terminal':t['status'],'state':state['arms']['A']['status'],'debits':result['phase_debits']}),flush=True)
                if driver.stop_path.exists():return
                if t['status']!='returned' or state['arms']['A']['status']!='delivered':break
        print(json.dumps({'stage_complete':'confirmation' if args.confirm else 'A_screen','phase_debits':checkpoint()['phase_debits']}),flush=True)


if __name__=='__main__':main()
