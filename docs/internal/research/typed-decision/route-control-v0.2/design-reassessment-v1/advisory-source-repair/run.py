"""One fresh F advisory repair verification; no old-ledger mutation."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
P=Path(__file__).parents[1]/'independent-sol56-v1/run.py'
S=importlib.util.spec_from_file_location('sol56_adapter',P)
r=importlib.util.module_from_spec(S);S.loader.exec_module(r);b=r.b
original_schema,original_normalize=r.schema,r.normalize

def schema(q):
    value=original_schema(q)
    if q.get('schema','').endswith('execution-request.v1') and q['policy']=='advisory':
        value['properties']['advisory_status']=b.enum(['answer','bounded_answer','unresolved'])
        value['required'].append('advisory_status')
    return value

def normalize(raw,q,usage):
    out=original_normalize(raw,q,usage)
    if q.get('schema','').endswith('execution-request.v1') and q['policy']=='advisory':
        out['advisory_status']=raw['advisory_status']
    return out

def freeze(root,source):
    packet=b.read_record(source/'sources/F.json');packet['task_budget']={'max_calls':4,'max_seconds':360}
    b.save(root/'sources/F.json',packet)
    home=root/'cli-home';home.mkdir(exist_ok=True);auth=home/'auth.json'
    if not auth.exists():auth.symlink_to(Path.home()/'.codex/auth.json')
    value=dict(schema='mindthus.advisory-source-repair.v1',root=str(root),implementation=b.implementation_digest(),
        runner_sha256=b.sha(__file__),parent_runner_sha256=b.sha(P),base_sha256=b.sha(r.BASE),
        plan_sha256=b.sha(Path(__file__).with_name('PLAN.md')),sources={'F':b.digest(packet)},
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=b.REPO,text=True).strip(),
        source_origin=str(source),configuration=b.CONFIG,codex_binary='/Applications/ChatGPT.app/Contents/Resources/codex',
        stages={'full_jev':3,'host_codex':6,'review_codex':0},
        budget_delta='new repair verification: four execution slots for up to three issue outputs plus owner acceptance; same 360 seconds')
    b.save(root/'freeze.json',value);return value

def verify(root):
    f=b.read_record(root/'freeze.json')
    b.require(f['root']==str(root) and f['implementation']==b.implementation_digest() and f['runner_sha256']==b.sha(__file__)
        and f['parent_runner_sha256']==b.sha(P) and f['base_sha256']==b.sha(r.BASE)
        and f['plan_sha256']==b.sha(Path(__file__).with_name('PLAN.md')),'repair_freeze_changed')
    b.require(b.digest(b.read_record(root/'sources/F.json'))==f['sources']['F'],'repair_source_changed');return f

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run']);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source-root',type=Path);p.add_argument('--credential-file',type=Path);a=p.parse_args();root=a.root.resolve()
    if a.command=='freeze':out=freeze(root,a.source_root.resolve())
    else:
        b.require(a.credential_file.stat().st_mode&0o077==0,'credential_not_private')
        for line in a.credential_file.read_text().splitlines():
            if line.startswith('TYPESAFE_API_KEY='):os.environ['TYPESAFE_API_KEY']=line.split('=',1)[1].strip().strip('"\'')
        r.verify=verify;r.schema=schema;r.normalize=normalize
        out=r.run(root,'F','jev_advisory')
    print(json.dumps({k:out.get(k) for k in ('reason','consumption_complete','pending')},ensure_ascii=False))
