"""Normalize frozen results and optionally package evidence outside the repo.

No credentials, request headers or hidden reasoning are admitted. Original
response text bytes are preserved, with request hashes for reproducible prompts.
This exporter is post-run tooling; not an input to the completed experiment.
"""
import argparse
import base64
import gzip
import hashlib
import json
import lzma
from pathlib import Path


def bundle(root):
    calls=[]
    for f in sorted(root.glob('call-*/result.json')):
        r=json.loads(f.read_text()); u=r.get('usage') or {}
        x={k:r.get(k) for k in ('call','label','start','end','seconds','requested_model','returned_model','requested_effort','returned_effort','status','response_id','prompt_sha256','prompt_bytes','http_status','tool_calls','error_type')}
        x['usage']={k:u.get(k) for k in ('input_tokens','output_tokens','total_tokens','input_tokens_details','output_tokens_details')}
        x['gateway_instruction_tokens']=u.get('attribution',{}).get('request_fields',{}).get('instructions',{}).get('input_tokens')
        raw=(f.parent/'response.txt').read_bytes()
        x['response_text']=raw.decode(); x['response_sha256']=hashlib.sha256(raw).hexdigest()
        x['request_file_sha256']=hashlib.sha256((f.parent/'request.json').read_bytes()).hexdigest()
        calls.append(x)
    return {'format':'normalized-response-evidence-v1','raw_runtime_root':str(root),
       'manifest':json.loads((root/'manifest.json').read_text()),
       'events':(root/'events.jsonl').read_text(),'calls':calls}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--out',type=Path);p.add_argument('--print-encoded',action='store_true');p.add_argument('--include-raw',action='store_true');a=p.parse_args()
    data=json.dumps(bundle(a.run),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    encoded=base64.b64encode(lzma.compress(data)).decode()
    if a.out:
        repo=Path(__file__).resolve().parents[4]
        out=a.out.resolve()
        if out==repo or repo in out.parents:raise SystemExit('output must be outside repository')
        out.mkdir(parents=True,exist_ok=False)
        with (out/'evidence.json').open('xb') as f:f.write(data)
        with (out/'evidence.json.xz').open('xb') as f:f.write(lzma.compress(data))
        if a.include_raw:
            inventory=[]
            admitted={'manifest.json','state.json','events.jsonl','request.json','response.txt','result.json'}
            for source in sorted(a.run.rglob('*')):
                if not source.is_file() or source.name not in admitted: continue
                if source.is_symlink(): raise SystemExit('symlink outside evidence contract')
                relative=source.relative_to(a.run); target=out/'raw'/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                raw=source.read_bytes()
                with target.open('xb') as f:f.write(raw)
                digest=hashlib.sha256(raw).hexdigest()
                if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise SystemExit('copy verification failed')
                inventory.append({'path':str(relative),'bytes':len(raw),'sha256':digest})
            with (out/'raw-inventory.json').open('x') as f:json.dump(inventory,f,indent=2)
    print(json.dumps({'json_bytes':len(data),'base64_xz_bytes':len(encoded),'sha256':hashlib.sha256(data).hexdigest(),'calls':len(bundle(a.run)['calls'])}))
    if a.print_encoded:print(encoded)
