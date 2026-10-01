"""One Owner-authorized medium rerun, reusing clean adapters and shared serial.

Old max products/debits are immutable parents. No new transport or retry policy.
"""
import argparse
import getpass
import json
import os
import subprocess
import time
from pathlib import Path
from . import run as r, deepseek as d, primitive_ablation as a

ROOT=d.ROOT/'primitive-ablation-medium-v1'
DOC=r.DOC/'primitive-ablation-medium-v1'
HOST=d.DEFAULT_HOST
PHASE_LIMITS={'logical':32,'host':24,'jev':8}
INHERITED={'logical':35,'host':27,'jev':8}
LIMITS={k:INHERITED[k]+PHASE_LIMITS[k] for k in INHERITED}


class MediumAdapters(a.CleanAdapters):
    limits=LIMITS
    def check_configuration(self,config):
        super().check_configuration(config)
        r.require(self.host==HOST,'medium_rerun_profile')


def prepare():
    r.require(not ROOT.exists(),'medium_rerun_exists_no_reset')
    old=r.rt.read(a.ROOT/'batch.json')
    r.require(r.digest(r.rt.read(r.DOC/'cases.business.json'))==old['cases_sha256'],'input_changed')
    r.require(r.digest(r.rt.read(r.DOC/'norms.evaluation-only.json'))==old['norms_sha256'],'norms_changed')
    r.require(r.digest(a.packet())==old['primitive_packet_sha256'],'primitive_packet_changed')
    r.require(not (a.ROOT/'STOP.json').exists(),'parent_stopped')
    dirs=[*sorted((d.ROOT/'calls').iterdir()),*sorted((a.ROOT/'calls').iterdir())]
    roles=[r.rt.read(p/'request.json')['role'] for p in dirs]
    r.require(len(dirs)==33 and roles.count('host')==25 and roles.count('jev')==8,'parent_debits_changed')
    r.require(all((p/'import.json').exists() for p in dirs),'parent_unimported')
    r.require(all(r.rt.read(p/'terminal.json')['status']=='returned' for p in dirs[1:]),'parent_new_unknown_or_failure')
    for item in r.rt.read(r.DOC/'cases.business.json')['cases']:
        clean=r.rt.read(a.ROOT/'states'/(item['case_id']+'-clean.json'))
        prompt=r.rt.read(a.ROOT/'states'/(item['case_id']+'-prompt.json'))
        r.require(all(x['status']=='delivered' for x in (clean['arms']['A'],clean['arms']['C'],prompt['arms']['A'])),'parent_not_complete')
    r.SerialRequests(d.ROOT/'serial').validate()
    preserved={}
    paths=[d.ROOT/'batch.json',d.ROOT/'STOP.json',d.ROOT/'new-endpoint-successor.json',a.ROOT/'batch.json']
    paths += [p/name for p in dirs for name in ('intent.json','request.json','terminal.json','import.json')]
    for p in paths:preserved[str(p.relative_to(d.ROOT))]=r.digest(r.rt.read(p))
    source_paths=set(old['source_sha256'])|{'experiments/bias_trigger/medium_ablation.py'}
    config={**old,'schema':'mindthus.primitive-ablation.medium.v1','host_configuration':HOST,
            'authorization_ref':'Owner: 来吧，重跑一次 (2026-10-01), after medium preference; same eight A/B/C paths, at most one handling and no retries',
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip(),
            'source_sha256':{p:r.digest((r.REPO/p).read_text()) for p in source_paths},
            'external_budget_debits':INHERITED,'phase_limits':PHASE_LIMITS,'limits':LIMITS,
            'created_at_epoch':time.time(),'parent_preserved':preserved,
            'parent_result_commit':'4925b5c3ea5266e792f4e83e7b322139bdf410e1',
            'forward_profile_commit':'5165d3915849b4d39018e5e7476e5be4f412a7fe',
            'scope':'one rerun of eight unchanged public cases, clean A / fixed primitive B / Jev C on exact new A; no review model or automatic retry',
            'provider_effort_mapping':'medium is sent explicitly; official DeepSeek maps to default high, CPA actual mapping unverified',
            'protocol':{**old['protocol'],'scope_this_turn':'this medium eight-case A/B/C rerun only; same single sender and 60-second cooldown; no new unknown exception'},
            'comparison_limit':'Repeated public inputs, not independent holdout; A/B prompt treatment, C shares actual A and includes its cost.'}
    ROOT.mkdir();(ROOT/'calls').mkdir();(ROOT/'states').mkdir();DOC.mkdir(exist_ok=True)
    r.rt.write(ROOT/'batch.json',config);r.rt.write(DOC/'admission.json',config)
    r.rt.write(ROOT/'materials.json',{})
    for item in r.rt.read(r.DOC/'cases.business.json')['cases']:
        r.rt.write(ROOT/'states'/(item['case_id']+'-medium-clean.json'),a.initial())
        r.rt.write(ROOT/'states'/(item['case_id']+'-medium-prompt.json'),a.initial({k:v['text'] for k,v in a.packet().items()}))


class MediumDriver(r.Driver):
    def __init__(self,root=ROOT,**clock_options):
        super().__init__(root,MediumAdapters(HOST),**clock_options)
        self.serial=r.SerialRequests(d.ROOT/'serial',**clock_options)
        self.stop_path=self.root/'STOP.json'
    def step(self,item,state,arm,phase):
        r.require(self.config['external_budget_debits']==INHERITED and self.config['phase_limits']==PHASE_LIMITS,'medium_budget_changed')
        for path,sha in self.config['parent_preserved'].items():r.require(r.digest(r.rt.read(d.ROOT/path))==sha,'parent_evidence_changed')
        r.require(r.digest(a.packet())==self.config['primitive_packet_sha256'],'primitive_source_changed')
        r.require(state['calls'][arm]<(2 if arm=='C' else 1),'one_answer_or_one_check_handling')
        prior=[r.rt.read(p/'request.json') for p in (self.root/'calls').iterdir()]
        role='jev' if arm=='C' and phase!='handling' else 'host'
        r.require(len(prior)<PHASE_LIMITS['logical'] and sum(p['role']==role for p in prior)<PHASE_LIMITS[role],'medium_phase_budget')
        return super().step(item,state,arm,phase)


def checkpoint():
    rows=[]
    for item in r.rt.read(r.DOC/'cases.business.json')['cases']:
        clean=r.rt.read(ROOT/'states'/(item['case_id']+'-medium-clean.json'))
        prompt=r.rt.read(ROOT/'states'/(item['case_id']+'-medium-prompt.json'))
        row={'case_id':item['case_id'],'A':clean['arms']['A'],'B':prompt['arms']['A'],'C':clean['arms']['C'],
             'candidate_sha256':clean['snapshot_sha256'],'measurements':clean['measurements']+prompt['measurements']}
        rows.append(row)
        for group in 'ABC':
            r.persist(DOC/'answers'/(item['case_id']+'-'+group+'.json'),{'case_id':item['case_id'],'display_group':group,**row[group]})
    reqs=[r.rt.read(p/'request.json') for p in (ROOT/'calls').iterdir()]
    phase={'logical':len(reqs),'host':sum(q['role']=='host' for q in reqs),'jev':sum(q['role']=='jev' for q in reqs)}
    result={'cases':rows,'phase_debits':phase,'inherited_debits':INHERITED,
            'cumulative_debits':{k:INHERITED[k]+phase[k] for k in INHERITED},
            'cost':None,'exact_http_requests':None,'simulation':False,'holdout':False}
    r.persist(DOC/'summary.json',result);return result


def main():
    p=argparse.ArgumentParser();mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true');mode.add_argument('--run',action='store_true');args=p.parse_args()
    with r._locked(d.ROOT/'.execution.lock'):
        if args.prepare:
            prepare();print(json.dumps({'prepared':True,'budgets':LIMITS,'prior_debits':INHERITED}));return
        driver=MediumDriver();driver.serial.validate()
        if not os.environ.get('MINDTHUS_HOST_API_KEY'):os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('CPA credential (hidden): ')
        r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_host_credential')
        print(json.dumps({'credential_loaded':True,'jev':r.load_official_credential(),'effort_requested':'medium'}),flush=True)
        checkpoint()
        for n,item in enumerate(r.rt.read(r.DOC/'cases.business.json')['cases']):
            for group in ('B','A','C') if n%2 else ('A','B','C'):
                job={**item,'case_id':item['case_id']+('-medium-prompt' if group=='B' else '-medium-clean')}
                s=r.rt.read(ROOT/'states'/(job['case_id']+'.json'));arm='C' if group=='C' else 'A'
                if arm=='C' and s['candidate'] is None:continue
                while s['arms'][arm]['status'] in ('unrun','handling_required'):
                    phase='handling' if s['arms'][arm]['status']=='handling_required' else 'detect'
                    print(json.dumps({'dispatch':item['case_id'],'group':group,'phase':phase}),flush=True)
                    terminal=driver.step(job,s,arm,phase);summary=checkpoint()
                    print(json.dumps({'terminal':terminal['status'],'path_status':s['arms'][arm]['status'],'phase_debits':summary['phase_debits']},ensure_ascii=False),flush=True)
                    if driver.stop_path.exists():return
        print(json.dumps({'complete':True,'phase_debits':checkpoint()['phase_debits']}),flush=True)


if __name__=='__main__':main()
