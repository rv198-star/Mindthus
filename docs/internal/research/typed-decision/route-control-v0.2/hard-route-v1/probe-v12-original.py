"""Three-call exposed development probe that v1.2 still rejects original bad candidates."""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[5]
sys.path.insert(0,str(REPO))
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision.contracts import digest, provider_configuration, require
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.relationship_live import deadline_post_json
from experiments.typed_decision.session import implementation_digest, read_record, write_once

ROOT=Path('/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v12-original-probe')
PARENT=Path('/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v1/episodes')
CASES=('S1','S3','K3')
MODEL='jev-1.13.0'


def save(path,value):
    path=Path(path)
    if path.exists(): require(read_record(path)==value,'immutable_probe_record_changed')
    else: write_once(path,value)


def source(cid):
    found=list((PARENT/cid/'C').glob('turns/*/inputs/*/summary.json'))
    require(len(found)==1,'parent_summary_missing')
    summary=read_record(found[0])
    require(summary['original_input'] is not None,'parent_input_missing')
    return found[0],summary


def packet(cid):
    _,summary=source(cid)
    value=rel.clone(summary['original_input'])
    value['episode_id']='hard-route-v12-original-probe-'+cid
    return value


def provider():
    return TypeSafeJevProvider(model=MODEL,choice_rounding=True,transport=deadline_post_json)


def freeze():
    contract,_=rel.load_contract(REPO)
    require(rel.VERSION=='1.2' and rel.POLICY=='mindthus.relationship-frame.v1.2','v12_contract_required')
    obj={'schema':'mindthus.hard-route-v12-original-probe-freeze.v1',
         'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
         'contract_sha256':digest(contract),
         'implementation':implementation_digest(),'provider':provider_configuration(provider()),
         'script_sha256':__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),
         'cases':list(CASES),'parent_summaries':{},'packet_sha256':{},
         'max_jev_calls':3,'reserve_usd':.06,'retries':0,
         'evidence_limit':'exposed original bad candidates; diagnostic development only, not qualification'}
    for cid in CASES:
        path,_=source(cid)
        obj['parent_summaries'][cid]=__import__('hashlib').sha256(path.read_bytes()).hexdigest()
        obj['packet_sha256'][cid]=digest(packet(cid))
        rel.compile_packet(packet(cid),REPO)
    save(ROOT/'freeze.json',obj)


def one(cid):
    require(cid in CASES,'unadmitted_case')
    freeze()
    p=packet(cid)
    compiled=rel.compile_packet(p,REPO)
    item=ROOT/'calls'/cid
    intent={'schema':'mindthus.hard-route-v12-original-probe-intent.v1','case':cid,
            'packet_sha256':digest(p),'identity':compiled.identity,
            'provider':provider_configuration(provider()),'timeout_seconds':45}
    ip=item/'intent.json'; op=item/'outcome.json'
    require(not op.exists() and not ip.exists(),'do_not_repeat_probe')
    require(bool(os.environ.get('TYPESAFE_API_KEY')),'missing_typesafe_credential')
    save(ip,intent)
    start=time.monotonic()
    jev=provider()
    try:
        batch=jev.evaluate(list(compiled.specs),compiled.context,45)
        response={'identity':compiled.identity,'results':{k:asdict(v) for k,v in batch.results.items()}}
        consumed=rel.consume(compiled,response,REPO)
        out={'status':'complete','elapsed_seconds':time.monotonic()-start,
             'resolved_runtime':batch.resolved_runtime.to_dict(),'usage':batch.usage,
             'receipt':jev.response_receipt(),'results':response['results'],
             'action':consumed['action'],'reason':consumed.get('reason'),
             'matrix':consumed['matrix'],
             'repair_kinds':[x['kind'] for x in consumed.get('plan',{}).get('repair_relations',[])]}
    except Exception as exc:
        out={'status':'failed','elapsed_seconds':time.monotonic()-start,
             'error':type(exc).__name__,'receipt':jev.response_receipt()}
    save(op,out)
    print(json.dumps({'case':cid,'status':out['status'],'action':out.get('action'),
                      'repairs':out.get('repair_kinds'),'elapsed_seconds':out['elapsed_seconds']},
                     ensure_ascii=False),flush=True)


if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='freeze': freeze()
    elif len(sys.argv)==2: one(sys.argv[1])
    else: raise SystemExit('usage: probe-v12.py freeze|S1|S3|K3')
