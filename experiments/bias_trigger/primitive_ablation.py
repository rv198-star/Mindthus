"""Owner-authorized clean/plain vs fixed-primitives vs Jev continuation.

Reuse the existing HTTP adapters, consumer and serial ledger. The B generator
uses engine arm A in its own named state; display groups are explicit in manifest.
C inspects the exact clean A and retains it unless the existing checks trigger.
"""
import argparse
import getpass
import json
import os
import subprocess
import time
from pathlib import Path
from . import run as r, deepseek as d, deepseek_continue as parent

ROOT=d.ROOT/'primitive-ablation-v1'
DOC=r.DOC/'primitive-ablation-v1'
HOST=parent.HOST
LIMITS={'logical':32,'host':24,'jev':8}


def packet():
    frame='docs/methodologies/primitives/frame-fitness-check.md'
    context='docs/methodologies/primitives/decision-context-calibration.md'
    a=(r.REPO/frame).read_text();full=(r.REPO/context).read_text()
    b=full.split('## Display-Scaling Calibration Case',1)[0]+full[full.index('## Boundary'):]
    return {'frame':{'source_path':frame,'source_sha256':r.digest(a),'selection':'full general rule; no case answer','text':a},
            'context':{'source_path':context,'source_sha256':r.digest(full),'selection':'general rule plus Boundary; Display-Scaling Calibration Case omitted before execution','text':b}}


def initial(loaded=None):
    return {'candidate':None,'snapshot_sha256':None,'loaded':loaded or {},'readable_paths':[],
            'calls':{a:0 for a in 'ABC'},'arms':{a:{'status':'unrun','final':None} for a in 'ABC'},'measurements':[]}


class CleanAdapters(d.CPAAdapters):
    def __init__(self,host=None):super().__init__(host)
    def outbound(self,req,config):
        wire=super().outbound(req,config)
        if req['role']!='host' or req['phase']!='draft':return wire
        p=req['payload'];docs=p['source']['documents']
        r.require(len(docs)==1 and docs[0]['id']=='task' and not p['readable_paths'],'clean_task_only')
        contract=wire['local_schema'];contract['properties']['kind']['enum']=['answer']
        system='直接回应用户原题。没有工具。只返回符合此合同的JSON对象，kind=answer、read_paths=[]，text为完整回答：'+r.canonical(contract).decode()
        if p['loaded_materials']:
            expected={k:v['text'] for k,v in packet().items()}
            r.require(p['loaded_materials']==expected,'fixed_primitive_packet')
            system+='\n以下固定通用认知规则供回答使用，内部检查无需展示。规则不覆盖原题给定目标、条件或证据上限。\n'+'\n\n'.join(expected.values())
        wire['body']['messages']=[{'role':'system','content':system},{'role':'user','content':docs[0]['text']}]
        return wire


def prepare():
    r.require(not ROOT.exists(),'ablation_exists_no_reset')
    x=parent.verify(d.ROOT)
    r.require(not (d.ROOT/'STOP-after-new-endpoint.json').exists(),'parent_new_stop')
    old=sorted((d.ROOT/'calls').iterdir())
    r.require(len(old)==9 and all((p/'import.json').exists() for p in old),'parent_attempts_changed')
    r.require(all(r.rt.read(p/'terminal.json')['status']=='returned' for p in old[1:]),'parent_not_complete')
    reviewed=r.rt.read(d.ROOT/'stage-A-review.json')
    r.require(not reviewed['important_bias_case_ids'],'parent_review_changed')
    ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir();DOC.mkdir(exist_ok=True)
    prim=packet();r.rt.write(ROOT/'primitive-packet.json',prim);r.rt.write(DOC/'primitive-packet.json',prim)
    preserved={str(p.relative_to(d.ROOT)):r.digest(r.rt.read(p)) for p in (d.ROOT/'batch.json',d.ROOT/parent.NAME,d.ROOT/'stage-A-review.json',d.ROOT/'STOP.json')}
    for p in old:
        for name in ('intent.json','request.json','wire.json','raw.json','terminal.json','import.json','state.after.json'):
            preserved[str((p/name).relative_to(d.ROOT))]=r.digest(r.rt.read(p/name))
    config={**x['effective_config'],'schema':'mindthus.primitive-ablation.v1','created_at_epoch':time.time(),
            'authorization_ref':'Owner: 你先继续完成，完成后拿一个场景的三组对照给我看 (2026-10-01)',
            'external_budget_debits':{'logical':11,'host':11,'jev':0},'phase_limits':LIMITS,
            'parent_preserved':preserved,'primitive_packet_sha256':r.digest(prim),
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
            'source_sha256':{**x['effective_config']['source_sha256'],
                'experiments/bias_trigger/primitive_ablation.py':r.digest(Path(__file__).read_text())},
            'groups':{'A':'new engine-A draft in case-NN-clean state, no directory/AGENTS/materials',
                'B':'independent engine-A draft in case-NN-prompt state; fixed general primitives only',
                'C':'existing two Jev checks of exact new A; at most one same-host handling; otherwise A retained'},
            'presentation_case':'case-06','scope':'eight unchanged cases; first valid outputs; no reviewer model or automatic retry; C runs even when executor considers A sufficient',
            'causal_limit':'A/B isolate the prompt packet. B/C compare packages with different opportunities, not pure judging-model causality.'}
    r.rt.write(ROOT/'batch.json',config);r.rt.write(ROOT/'materials.json',{})
    r.rt.write(DOC/'admission.json',config)
    for item in r.rt.read(r.DOC/'cases.business.json')['cases']:
        r.rt.write(ROOT/'states'/(item['case_id']+'-clean.json'),initial())
        r.rt.write(ROOT/'states'/(item['case_id']+'-prompt.json'),initial({k:v['text'] for k,v in prim.items()}))


class Driver(r.Driver):
    def __init__(self):
        super().__init__(ROOT,CleanAdapters(r.rt.read(ROOT/'batch.json')['host_configuration']))
        self.serial=r.SerialRequests(d.ROOT/'serial')
        self.stop_path=ROOT/'STOP.json'
    def step(self,item,state,arm,phase):
        r.require(len(list((d.ROOT/'calls').iterdir()))==9,'inherited_budget_changed')
        for path,sha in self.config['parent_preserved'].items():r.require(r.digest(r.rt.read(d.ROOT/path))==sha,'parent_evidence_changed')
        r.require(r.digest(packet())==self.config['primitive_packet_sha256'],'primitive_source_changed')
        r.require(state['calls'][arm]<(2 if arm=='C' else 1),'one_answer_or_one_check_handling')
        prior=[r.rt.read(p/'request.json') for p in (ROOT/'calls').iterdir()]
        role='jev' if arm=='C' and phase!='handling' else 'host'
        r.require(len(prior)<32 and sum(p['role']==role for p in prior)<LIMITS[role],'ablation_phase_budget')
        return super().step(item,state,arm,phase)


def checkpoint():
    rows=[]
    for item in r.rt.read(r.DOC/'cases.business.json')['cases']:
        a=r.rt.read(ROOT/'states'/(item['case_id']+'-clean.json'));b=r.rt.read(ROOT/'states'/(item['case_id']+'-prompt.json'))
        row={'case_id':item['case_id'],'A':a['arms']['A'],'B':b['arms']['A'],'C':a['arms']['C'],
             'engine_mapping':{'A':item['case_id']+'-clean:A','B':item['case_id']+'-prompt:A','C':item['case_id']+'-clean:C'},
             'candidate_sha256':a['snapshot_sha256'],'measurements':a['measurements']+b['measurements']}
        rows.append(row)
        for group in 'ABC':r.persist(DOC/'answers'/(item['case_id']+'-'+group+'.json'),{'case_id':item['case_id'],'display_group':group,'engine_path':row['engine_mapping'][group],**row[group]})
    attempts=[r.rt.read(p/'request.json') for p in (ROOT/'calls').iterdir()]
    value={'cases':rows,'phase_logical_calls':len(attempts),'phase_host_calls':sum(p['role']=='host' for p in attempts),
           'phase_jev_calls':sum(p['role']=='jev' for p in attempts),'inherited_host_debits':11,
           'cumulative_logical_debits':len(attempts)+11,'cumulative_host_debits':sum(p['role']=='host' for p in attempts)+11,
           'cost':None,'exact_http_requests':None,'simulation':False,'holdout':False}
    r.persist(DOC/'summary.json',value);return value


def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');args=p.parse_args()
    if not os.environ.get('MINDTHUS_HOST_API_KEY'):os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('CPA credential (hidden): ')
    r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_host_credential')
    print(json.dumps({'credential_loaded':True,'jev':r.load_official_credential()},ensure_ascii=False),flush=True)
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:prepare()
        driver=Driver();checkpoint()
        for n,item in enumerate(r.rt.read(r.DOC/'cases.business.json')['cases']):
            # Alternate A/B order; C always follows the actual A, and all calls
            # share the prior batch's serial ledger and process-wide sender lock.
            for group in ('B','A','C') if n%2 else ('A','B','C'):
                job={**item,'case_id':item['case_id']+('-prompt' if group=='B' else '-clean')}
                s=r.rt.read(ROOT/'states'/(job['case_id']+'.json'));arm='C' if group=='C' else 'A'
                if arm=='C' and s['candidate'] is None:continue
                while s['arms'][arm]['status'] in ('unrun','handling_required'):
                    phase='handling' if s['arms'][arm]['status']=='handling_required' else 'detect'
                    print(json.dumps({'case':item['case_id'],'display_group':group,'phase':phase},ensure_ascii=False),flush=True)
                    t=driver.step(job,s,arm,phase);counts=checkpoint()
                    print(json.dumps({'terminal':t['status'],'path_status':s['arms'][arm]['status'],'cumulative_debits':counts['cumulative_logical_debits']},ensure_ascii=False),flush=True)
                    if driver.stop_path.exists():return
        print(json.dumps({'stage_complete':True,'counts':{k:v for k,v in checkpoint().items() if k!='cases'}},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
