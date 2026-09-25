"""Six independent end-to-end branches using the existing runtime and CLI handoffs."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

BASE=Path(__file__).parents[1]/'live-v03-d1/run.py'
S=importlib.util.spec_from_file_location('base_live_adapter',BASE)
b=importlib.util.module_from_spec(S);S.loader.exec_module(b)
CONDITIONS=('pure_codex','jev_advisory','jev_committed')
original_call,original_schema,original_normalize=b.call,b.schema_for,b.normalize
ACTIVE_LABEL=None

def freeze(root,source_root):
    root.mkdir(parents=True,exist_ok=True)
    for case in ('E','F'):
        source=source_root/'sources'/f'{case}.json'
        b.save(root/'sources'/f'{case}.json',b.read_record(source))
    home=root/'cli-home';home.mkdir(exist_ok=True)
    auth=home/'auth.json'
    if not auth.exists():auth.symlink_to(Path.home()/'.codex/auth.json')
    value=dict(schema='mindthus.independent-full-comparison.v1',root=str(root),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=b.REPO,text=True).strip(),
        implementation=b.implementation_digest(),runner_sha256=b.sha(__file__),base_sha256=b.sha(BASE),
        plan_sha256=b.sha(Path(__file__).with_name('PLAN.md')),review_sha256=b.sha(Path(__file__).with_name('review.py')),configuration=b.CONFIG,
        codex_binary='/Applications/ChatGPT.app/Contents/Resources/codex',
        sources={case:b.digest(b.read_record(root/'sources'/f'{case}.json')) for case in ('E','F')},
        source_origin=dict(root=str(source_root),freeze_sha256=b.sha(source_root/'freeze.json')),
        stages={'full_jev':12,'host_codex':36,'review_codex':6},
        branch_order={'E':list(CONDITIONS),'F':['jev_committed','pure_codex','jev_advisory']},
        qualification='historical_exposed_partial_sources_development_only')
    b.save(root/'freeze.json',value);return value

def verify(root):
    f=b.read_record(root/'freeze.json')
    b.require(f['root']==str(root) and f['implementation']==b.implementation_digest() and
        f['runner_sha256']==b.sha(__file__) and f['base_sha256']==b.sha(BASE) and
        f['plan_sha256']==b.sha(Path(__file__).with_name('PLAN.md')) and
        f['review_sha256']==b.sha(Path(__file__).with_name('review.py')),'independent_freeze_changed')
    for case,h in f['sources'].items():b.require(b.digest(b.read_record(root/'sources'/f'{case}.json'))==h,'independent_source_changed')
    return f

def schema(q):
    result=original_schema(q);kind=q.get('schema','')
    if kind.endswith('native-request.v1'):
        result['properties']['artifact_action']=b.enum(q['artifact_actions'])
        result['required'].append('artifact_action')
        result['properties']['performed_methods']=b.arr(b.enum(q['condition_packet']['loaded_methods']))
    elif kind.endswith('execution-request.v1'):
        result['properties']['performed_methods']=b.arr(b.enum(q['loaded_methods']))
    return result

def normalize(raw,q,usage):
    if q.get('schema','').endswith('native-request.v1'):
        raw=dict(raw)
        if raw['artifact_action']=='retain':
            b.require(raw['text']=='' and q['candidate'] is not None,'retain_requires_empty_wire_text_and_candidate')
            raw['text']=q['candidate']
        out=original_normalize(raw,q,usage);out['artifact_action']=raw['artifact_action'];return out
    return original_normalize(raw,q,usage)

def call(root,label,body,schema,**kwargs):
    f=verify(root);is_review=label.startswith('blind-')
    # Per-branch reservation avoids races when independent branches run together.
    if not (root/'codex-calls'/label/'intent.json').exists():
        if is_review:
            b.require(len(list((root/'codex-calls').glob('blind-*/intent.json')))<f['stages']['review_codex'],'review_cap')
        else:
            group=kwargs.get('session_group') or ACTIVE_LABEL
            b.require(group is not None,'branch_group_required')
            b.require(len(list((root/'codex-calls').glob(group+'-*/intent.json')))<6,'branch_host_cap')
    body=dict(body)
    if 'request' in body:
        q=body['request'];kind=q.get('schema','')
        if kind.endswith('native-request.v1'):
            body['artifact_transport']='artifact_action=retain 时 text 必须为空字符串，绑定保留 candidate 原文；replace 时 text 必须是完整实际答案，不能只写接受说明。'
        if kind.endswith('organize-request.v1'):
            body['available_methods']=b.cmp.prepare_condition(q['original_input'],'pure_codex',b.REPO)['loaded_methods']
    return original_call(root,label,body,schema,**kwargs)

def jev(root,stage):
    provider=b.TypeSafeJevProvider(model='jev-1.13.0',choice_rounding=True)
    label=ACTIVE_LABEL
    def transport(url,headers,body,timeout):
        ident=b.digest(body);directory=root/'jev-calls'/stage/(label+'-'+ident)
        op=directory/'response.json'
        if op.exists():return b.read_record(op)['response']
        if (directory/'intent.json').exists():raise b.RecoveryRequired('independent_jev_intent_unresolved')
        verify(root)
        b.require(len(list((root/'jev-calls'/stage).glob(label+'-*/intent.json')))<3,'branch_jev_cap')
        b.save(directory/'intent.json',dict(branch=label,wire_request_sha256=ident,model='jev-1.13.0',timeout=timeout))
        start=time.monotonic()
        try:raw=b.deadline_post_json(url,headers,body,min(timeout,60))
        except Exception as exc:
            b.save(directory/'failure.json',dict(error_type=type(exc).__name__,elapsed_seconds=time.monotonic()-start));raise
        b.no_secrets(raw);capture=b._JevReceipt();capture.capture_receipt(body,raw)
        b.save(op,{**capture.response_receipt(),'elapsed_seconds':time.monotonic()-start,'branch':label})
        return raw
    provider.transport=transport;return provider

def run(root,case,condition):
    global ACTIVE_LABEL
    b.require(condition in CONDITIONS,'independent_condition')
    ACTIVE_LABEL='full-'+case+'-'+condition
    b.verify=verify;b.schema_for=schema;b.normalize=normalize;b.call=call;b.jev=jev
    # full=True is mandatory; no common candidate path or shared natural() call exists here.
    return b.run(root,case,condition,full=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run']);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source-root',type=Path);p.add_argument('--case',choices=['E','F']);p.add_argument('--condition',choices=CONDITIONS)
    p.add_argument('--credential-file',type=Path);a=p.parse_args()
    if a.credential_file:
        b.require(a.credential_file.stat().st_mode&0o077==0,'credential_not_private')
        for line in a.credential_file.read_text().splitlines():
            if line.startswith('TYPESAFE_API_KEY='):os.environ['TYPESAFE_API_KEY']=line.split('=',1)[1].strip().strip('"\'')
    root=a.root.resolve()
    if a.command=='freeze':result=freeze(root,a.source_root.resolve())
    else:result=run(root,a.case,a.condition)
    print(json.dumps({k:result.get(k) for k in ('status','reason','consumption_complete','pending')},ensure_ascii=False))
