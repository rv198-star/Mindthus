"""Same-run transport/identifier supplement; never retries a semantic result."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
S=importlib.util.spec_from_file_location('independent_full',Path(__file__).with_name('run.py'))
r=importlib.util.module_from_spec(S);S.loader.exec_module(r);b=r.b
original_normalize=r.normalize
ROOT=None

def normalize(raw,q,usage):
    if q.get('schema','').endswith('organize-request.v1'):
        ids=[i['id'] for i in raw['issues']]
        b.require(len(ids)==len(set(ids)),'duplicate_organizer_ids')
        if not all(b.rel.identifier(i) for i in ids):
            mapping={old:f'I{index+1}' for index,old in enumerate(ids)}
            b.save(ROOT/'adapters'/(r.ACTIVE_LABEL+'-identifier-map.json'),dict(
                request_id=q['request_id'],mapping=mapping,raw_reply_sha256=b.digest(raw),
                reason='Opaque issue identifiers only; preserve every candidate, goal, scope and issue count.'))
            raw={**raw,'issues':[{**item,'id':mapping[item['id']]} for item in raw['issues']]}
    return original_normalize(raw,q,usage)

def run(root,case,condition):
    global ROOT
    ROOT=root;r.verify(root)
    b.save(root/'adapters/transport-identifier-r1.json',dict(source_sha256=b.sha(__file__),
        frozen_runner_sha256=b.sha(Path(__file__).with_name('run.py')),
        network='Explicit HTTPS_PROXY/HTTP_PROXY=http://127.0.0.1:7890, the existing macOS system proxy; same API/model',
        identifier='Map distinct invalid opaque organizer IDs to I1..In; no model retry or judgment change',
        old_results='Preserve all old intents, raw outputs, timing and semantic failures. No completed branch rerun.'))
    os.environ['HTTPS_PROXY']='http://127.0.0.1:7890';os.environ['HTTP_PROXY']='http://127.0.0.1:7890'
    r.normalize=normalize
    return r.run(root,case,condition)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--case',choices=['E','F'],required=True)
    p.add_argument('--condition',choices=r.CONDITIONS,required=True);p.add_argument('--credential-file',type=Path,required=True);a=p.parse_args()
    b.require(a.credential_file.stat().st_mode&0o077==0,'credential_not_private')
    for line in a.credential_file.read_text().splitlines():
        if line.startswith('TYPESAFE_API_KEY='):os.environ['TYPESAFE_API_KEY']=line.split('=',1)[1].strip().strip('"\'')
    out=run(a.root.resolve(),a.case,a.condition)
    print(json.dumps({k:out.get(k) for k in ('status','reason','consumption_complete','pending')},ensure_ascii=False))
