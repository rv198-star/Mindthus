#!/usr/bin/env python3
"""Post-run evidence export only. No model requests; writes a new external directory."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import run

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def utc(s): return dt.datetime.fromisoformat(s)

def export(destination):
    destination=run.T.validate_out(destination); destination.mkdir(parents=True,exist_ok=False)
    roots=[Path('/var/lib/devspace/runtime-artifacts/mindthus-207-checkpoints-g1-20260907-'+n) for n in ('1','2')]
    run.validate_freeze(roots[1])
    if digest(roots[0]/'state.json')!=load(run.HERE/'PREDECESSOR-STOP.json')['state_file_sha256']:
        raise ValueError('stopped attempt changed')
    all_index=[]; all_calls=[]; versions=[]
    for version,root in enumerate(roots,1):
        manifest=load(root/'manifest.json'); state=load(root/'state.json')
        # Re-open every committed input, including pre-correction history.
        for path,expected in manifest['inputs'].items():
            raw=subprocess.check_output(['git','show',manifest['code_revision']+':'+path],cwd=run.REPO)
            if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('frozen historical source mismatch: '+path)
        for source in sorted(root.rglob('*')):
            if not source.is_file() or source.name=='runner.lock': continue
            relative=Path('v'+str(version))/source.relative_to(root)
            target=destination/'raw'/relative; target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
            if digest(source)!=digest(target): raise ValueError('copied raw differs')
            all_index.append({'path':str(Path('raw')/relative),'sha256':digest(target),'bytes':target.stat().st_size})
        calls=[]
        for d in sorted(root.glob('call-*')):
            r=load(d/'result.json'); req=load(d/'request.json')
            row={k:r.get(k) for k in ('call','label','status','seconds','returned_model','returned_effort','tool_calls','usage','error_type')}
            row.update(version=version,response_sha256=digest(d/'response.txt'),request_sha256=digest(d/'request.json'),requested_cap=req['max_output_tokens'])
            calls.append(row); all_calls.append(row)
        versions.append({'version':version,'revision':manifest['code_revision'],'manifest_sha256':manifest['manifest_sha256'],
          'requests':len(calls),'client_seconds':sum(r['seconds'] for r in calls),'started_at':state['started_at'],'finished_at':state.get('finished_at'),
          'status':'stopped_fixture_ambiguity' if version==1 else 'completed',
          'usage':{k:sum((r['usage'] or {}).get(k,0) for r in calls) for k in ('input_tokens','output_tokens','total_tokens')}})
    result=load(roots[1]/'mechanical-results.json')
    campaign={'requests':len(all_calls),'request_limit':27,'client_seconds':sum(r['seconds'] for r in all_calls),
      'window_seconds':(utc(versions[1]['finished_at'])-utc(versions[0]['started_at'])).total_seconds(),
      'usage':{k:sum((r['usage'] or {}).get(k,0) for r in all_calls) for k in ('input_tokens','output_tokens','total_tokens')},
      'reasoning_tokens_included_in_output':sum((r['usage'] or {}).get('output_tokens_details',{}).get('reasoning_tokens',0) for r in all_calls),
      'cached_input_tokens_included_in_input':sum((r['usage'] or {}).get('input_tokens_details',{}).get('cached_tokens',0) for r in all_calls),
      'model_request_failures':sum(r['status']!='ok' for r in all_calls),'native_tool_calls':sum(r['tool_calls'] or 0 for r in all_calls),
      'public_probe_calls':sum(row['probe_count'] for row in result['rows']),
      'billing_verified':False,'underlying_model_attested':False,
      'external_tool_block':{'count':1,'model_requests_sent':0,'permissions_changed':False},
      'elapsed_excludes':'MVP construction before first request and post-run semantic review'}
    metrics={'versions':versions,'campaign':campaign,'corrected_wave':result,
      'claim_ceiling':'G1 single trials only; G2 repetitions/terminal rechecks and G3 incremental value not established'}
    run.T.once(destination/'metrics.json',metrics); run.T.once(destination/'raw-index.json',all_index); run.T.once(destination/'call-index.json',all_calls)
    result={'output':str(destination),'raw_files':len(all_index),'raw_bytes':sum(x['bytes'] for x in all_index),
      'historical_inputs_verified':True,'raw_copy_hashes_match':True,'metrics_sha256':digest(destination/'metrics.json'),
      'raw_index_sha256':digest(destination/'raw-index.json'),'call_index_sha256':digest(destination/'call-index.json'),'campaign':campaign}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--out',type=Path,required=True); a=p.parse_args(); export(a.out)
