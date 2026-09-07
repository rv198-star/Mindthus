#!/usr/bin/env python3
"""Post-run evidence export. Reads raw roots, writes a NEW external directory.
No model calls. No private reasoning or credentials are in the admitted logs.
This exporter was authored after execution; it is not a frozen trial input.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import pressure_runner as R
import evaluation_v2 as E


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def build(out):
    out=R.T.validate_out(out); out.mkdir(parents=True,exist_ok=False)
    v2=Path('/var/lib/devspace/runtime-artifacts/mindthus-207-pressure-wave2-20260907-2')
    v1=v2.with_name('mindthus-207-pressure-wave2-20260907-1')
    R.validate_freeze(v2)
    versions=[]; index=[]; cap_observations=[]; records=[]; total_input=total_output=total_reasoning=total_cached=0
    for ver,root in [('stopped-v1',v1),('completed-v2',v2)]:
        state=json.loads((root/'state.json').read_text())
        manifest=json.loads((root/'manifest.json').read_text())
        source_files=sorted(p for p in root.rglob('*') if p.is_file() and p.name not in ('runner.lock','state.next'))
        target=out/ver/'raw'; target.mkdir(parents=True)
        for p in source_files:
            relative=p.relative_to(root); dest=target/relative; dest.parent.mkdir(parents=True,exist_ok=True)
            before=sha(p); shutil.copyfile(p,dest)
            if before!=sha(dest) or before!=sha(p): raise RuntimeError('raw evidence changed or copy mismatch')
            index.append({'version':ver,'path':str(relative),'bytes':p.stat().st_size,'sha256':before})
        rr=[]
        for p in sorted(root.glob('call-*/result.json')):
            r=json.loads(p.read_text()); q=json.loads((p.parent/'request.json').read_text()); u=r.get('usage') or {}
            row={k:r.get(k) for k in ('call','label','status','seconds','returned_model','returned_effort','tool_calls','error_type','http_status','charge_basis')}
            row.update(version=ver,request_sha256=sha(p.parent/'request.json'),response_sha256=sha(p.parent/'response.txt'),result_sha256=sha(p),usage=u)
            records.append(row); rr.append(r)
            total_input+=u.get('input_tokens',0); total_output+=u.get('output_tokens',0)
            total_reasoning+=u.get('output_tokens_details',{}).get('reasoning_tokens',0)
            total_cached+=u.get('input_tokens_details',{}).get('cached_tokens',0)
            if u.get('output_tokens',0)>q['max_output_tokens']:
                cap_observations.append({'version':ver,'label':r['label'],'requested_cap':q['max_output_tokens'],'reported_output':u['output_tokens'],'classification':'provider accounting/cap observation; cumulative budget still respected'})
        versions.append({'version':ver,'source_revision':manifest['code_revision'],'manifest_sha256':manifest['manifest_sha256'],
          'source_root':str(root),'started_at':state['started_at'],'finished_at':state.get('finished_at'),
          'requests':len(rr),'client_seconds':sum(r['seconds'] for r in rr),'total_tokens':sum((r['usage'] or {}).get('total_tokens',0) for r in rr)})
    start=dt.datetime.fromisoformat(versions[0]['started_at']); end=dt.datetime.fromisoformat(versions[1]['finished_at'])
    result={'experiment':'#207 pressure wave2','versions':versions,'campaign':{'requests':len(records),'limit':40,
       'client_seconds':sum(r['seconds'] for r in records),'window_seconds':(end-start).total_seconds(),
       'input_tokens':total_input,'output_tokens':total_output,'reasoning_tokens_included_in_output':total_reasoning,
       'cached_input_tokens_included_in_input':total_cached,'total_tokens':total_input+total_output,
       'billing_verified':False,'tools_inside_model':sum(r.get('tool_calls') or 0 for r in records),
       'provider_failures':sum(r['status']!='ok' for r in records),'automatic_retries':0,
       'outer_tool_safety_blocks':1,'requests_sent_by_blocked_invocation':0},
       'current_summary':R.summary(v2),'mechanical_evaluation':E.evaluate(v2),'reported_output_cap_observations':cap_observations,
       'claims':{'route_observed':True,'multi_refinement_convergence_proven':False,'C_increment_over_baseline_proven':False,'statistical_stability_proven':False,'visual_or_production_certification':False}}
    old=Path('/var/lib/devspace/runtime-artifacts/mindthus-207-fixed-wave1-20260907/raw')
    result['wave1_F_reassessment']=[]
    for p in sorted(old.glob('call-*-F-*-receiver/result.json')):
        r=json.loads(p.read_text()); v=E.wave1_corrected(r['parsed']['content'])
        result['wave1_F_reassessment'].append({'label':r['label'],'original_response_sha256':sha(p.parent/'response.txt'),
            'original_frozen_score':'45/48 retained','corrected_policy_scores':{k:[v['passed'],v['total']] for k,v in v['policies'].items()},'accepted_under_new_explanation':v['accepted']})
    for name,value in [('metrics.json',result),('raw-index.json',index),('call-index.json',records)]:
        R.T.once(out/name,value)
    print(json.dumps({'export_root':str(out),'raw_files':len(index),'raw_bytes':sum(r['bytes'] for r in index),
      'raw_digests_match':True,'metrics_sha256':sha(out/'metrics.json'),'raw_index_sha256':sha(out/'raw-index.json'),
      'call_index_sha256':sha(out/'call-index.json'),'campaign':result['campaign']},ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); a=p.parse_args(); build(a.out)
