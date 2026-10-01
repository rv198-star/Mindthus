"""Exact old 000000 access-refusal continuation after Owner supplied working API.

Old STOP/403 remain immutable. A fresh unknown/refusal stops this successor.
Probe attempts consume the original cap; there is no ignore-unknown flag.
"""
import argparse
import getpass
import json
import os
import subprocess
import time
from . import run as r,deepseek as d

HOST={**d.HOST,'endpoint':'https://cpa.rn-us.061718.xyz/v1/chat/completions'}
NAME='new-endpoint-successor.json'


def verify(root):
    x=r.rt.read(root/NAME)
    r.require(x['parent_batch_sha256']==r.digest(r.rt.read(root/'batch.json')),'endpoint_successor_parent')
    for path,sha in x['preserved'].items():r.require(r.digest(r.rt.read(root/path))==sha,'old_access_record_changed')
    t=r.rt.read(root/'calls/000000/terminal.json')
    r.require(t['binding']['call_key']=='case-01-A:0' and t['status']=='safety_refusal' and t['error']=='http_403','only_named_access_refusal')
    probe=r.rt.read(root/'external-api-checks/new-endpoint-smoke-retry-outcome.json')
    intent=r.rt.read(root/'external-api-checks/new-endpoint-smoke-retry-intent.json')
    r.require(probe['status']=='returned' and probe['request_sha256']==intent['request_sha256']==r.digest(intent['request_body']),'api_probe_binding')
    r.require(intent['endpoint']==HOST['endpoint'] and probe['model_reported']==HOST['model'] and json.loads(probe['reply'])=={'ok':True},'api_probe_identity')
    r.require(x['effective_config']['external_budget_debits']=={'logical':2,'host':2,'jev':0},'probe_debits_required')
    r.require(x['effective_config']['host_configuration']==HOST,'endpoint_profile')
    return x


class EndpointDriver(r.Driver):
    def __init__(self):
        super().__init__(d.ROOT,d.CPAAdapters(HOST))
        x=verify(self.root);self.config=x['effective_config']
        self.stop_path=self.root/'STOP-after-new-endpoint.json'
    def step(self,*args):
        verify(self.root)
        return super().step(*args)


def register():
    r.require(not (d.ROOT/NAME).exists(),'successor_exists_no_reset')
    r.require(len(list((d.ROOT/'calls').iterdir()))==1,'only_old_refused_call')
    config=r.rt.read(d.ROOT/'batch.json');t=r.rt.read(d.ROOT/'calls/000000/terminal.json')
    r.require(t['status']=='safety_refusal' and t['error']=='http_403','only_old_403')
    paths=['batch.json','STOP.json','calls/000000/intent.json','calls/000000/request.json',
           'calls/000000/wire.json','calls/000000/raw.json','calls/000000/terminal.json',
           'calls/000000/state.after.json','calls/000000/import.json']
    ext=d.ROOT/'external-api-checks';ext.mkdir()
    for name in ('new-endpoint-smoke-intent.json','new-endpoint-smoke-outcome.json',
                 'new-endpoint-smoke-reconciliation.json','new-endpoint-smoke-retry-intent.json',
                 'new-endpoint-smoke-retry-outcome.json','model-catalog-new-endpoint-check.json'):
        r.rt.write(ext/name,r.rt.read(d.DOC/name));paths.append('external-api-checks/'+name)
    hashes={p:r.digest((r.REPO/p).read_text()) for p in config['source_sha256']}
    hashes['experiments/bias_trigger/deepseek_continue.py']=r.digest(__import__('pathlib').Path(__file__).read_text())
    effective={**config,'host_configuration':HOST,'source_sha256':hashes,
               'external_budget_debits':{'logical':2,'host':2,'jev':0},
               'authorization_ref':'Owner explicitly supplied alternative CPA API URL after requesting API connectivity before evaluation; 2026-10-01',
               'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r.REPO,text=True).strip()}
    x={'parent_batch_sha256':r.digest(config),'effective_config':effective,
       'preserved':{p:r.digest(r.rt.read(d.ROOT/p)) for p in paths},
       'scope':'only old 000000 HTTP access refusal, after new explicitly authorized endpoint returned catalog/model and generation; no unknown or model-safety exception',
       'source_commit':effective['source_commit'],'registered_epoch':time.time(),
       'budgets_reset':False,'prior_debits':{'logical':3,'host':3,'jev':0},
       'old_generation_completion_asserted':False,'old_stop_retained':True}
    r.rt.write(d.ROOT/NAME,x);r.rt.write(d.DOC/NAME,x);verify(d.ROOT)
    s=r.rt.read(d.ROOT/'states/case-01.json')
    r.require(s['calls']['A']==1 and s['candidate'] is None,'old_path_attempt_preserved')
    s['arms']['A']['status']='unrun'
    for arm in 'BC':s['arms'][arm]['status']='unrun'
    s['endpoint_successor_sha256']=r.digest(x)
    r.persist(d.ROOT/'states/case-01.json',s)


def checkpoint():
    s=r.checkpoint(d.ROOT,d.DOC)
    s.update(external_setup_host_attempts=2,logical_calls_with_setup=s['logical_calls']+2,
             host_calls_with_setup=s['host_calls']+2,endpoint_successor_sha256=r.digest(r.rt.read(d.ROOT/NAME)))
    r.persist(d.DOC/'summary.json',s);return s


def main():
    p=argparse.ArgumentParser();p.add_argument('--register',action='store_true');p.add_argument('--compare',action='store_true');args=p.parse_args()
    if not os.environ.get('MINDTHUS_HOST_API_KEY'):
        os.environ['MINDTHUS_HOST_API_KEY']=getpass.getpass('CPA credential (hidden): ')
    r.require(bool(os.environ.get('MINDTHUS_HOST_API_KEY')),'missing_host_credential')
    print(json.dumps({'credential_loaded':True,'jev':r.load_official_credential()},ensure_ascii=False),flush=True)
    with r._locked(d.ROOT/'.execution.lock'):
        if args.register:register()
        driver=EndpointDriver();sums=checkpoint()
        if args.compare:
            review=r.rt.read(d.ROOT/'stage-A-review.json')
            r.require(review['important_bias_case_ids'] and review['endpoint_successor_sha256']==r.digest(verify(d.ROOT)),'no_bias_no_comparison')
            r.require(review['norms_sha256']==driver.config['norms_sha256'],'norms_changed')
            for cid,sha in review['candidate_sha256'].items():r.require(r.rt.read(d.ROOT/'states'/(cid+'.json'))['snapshot_sha256']==sha,'review_candidate_changed')
        for i,item in enumerate(r.rt.read(r.DOC/'cases.business.json')['cases']):
            s=r.rt.read(d.ROOT/'states'/(item['case_id']+'.json'))
            arms=(('B','C') if i%2==0 else ('C','B')) if args.compare else ('A',)
            for arm in arms:
                while s['arms'][arm]['status'] in ('unrun','handling_required'):
                    if arm!='A' and s['candidate'] is None:break
                    print(json.dumps({'dispatch':item['case_id'],'arm':arm},ensure_ascii=False),flush=True)
                    phase='handling' if s['arms'][arm]['status']=='handling_required' else 'detect'
                    t=driver.step(item,s,arm,phase);sums=checkpoint()
                    print(json.dumps({'terminal':t['status'],'path_status':s['arms'][arm]['status'],'logical_calls_including_setup':sums['logical_calls_with_setup']},ensure_ascii=False),flush=True)
                    if driver.stop_path.exists():return
        print(json.dumps({'stage_complete':'BC' if args.compare else 'A_screen','logical_calls_including_setup':sums['logical_calls_with_setup']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
