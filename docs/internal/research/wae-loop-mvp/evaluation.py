"""Frozen evaluation, invisible to tested Owner/recipient prompts.

F: executable observable projection oracle. K/S: references and fixed semantic
rubric; superficial keyword checks are NOT promoted to semantic pass verdicts.
The study author applies K/S rubrics after outputs are frozen, with this limit
explicitly reported. There is no independent human-audience/visual certification.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import sys

F_RECORDS=[
 {'revisions':[{'id':1,'text':'draft'}],'current_revision':1,'approved_revision':None},
 {'revisions':[{'id':1,'text':'approved old'},{'id':2,'text':'unreviewed new'}],'current_revision':2,'approved_revision':1},
 {'revisions':[{'id':1,'text':'old'},{'id':2,'text':'current approved'}],'current_revision':2,'approved_revision':2},
 {'revisions':[{'id':9,'text':'草稿'},{'id':4,'text':'已审'},{'id':2,'text':'historic'}],'current_revision':9,'approved_revision':4},
]


def expected(record,role,view):
    rid=record['approved_revision'] if role=='reader' or view=='published' else record['current_revision']
    if rid is None: return {'revision':None,'text':None,'approved':False,'editable':False}
    text=next(x['text'] for x in record['revisions'] if x['id']==rid)
    return {'revision':rid,'text':text,'approved':rid==record['approved_revision'],
            'editable':role=='editor' and rid==record['current_revision']}


def f_cases():
    return [{'input':[r,role,view,surface],'expected':expected(r,role,view)}
      for r in F_RECORDS for role in ('reader','editor') for view in ('working','published') for surface in ('list','detail','export')]

F_REFERENCE_1='''def project(record, role, view='working', surface='detail'):
    rid = record['approved_revision'] if role == 'reader' or view == 'published' else record['current_revision']
    if rid is None:
        return dict(revision=None, text=None, approved=False, editable=False)
    row = next(x for x in record['revisions'] if x['id'] == rid)
    return dict(revision=rid, text=row['text'], approved=rid == record['approved_revision'], editable=role == 'editor' and rid == record['current_revision'])
'''
F_REFERENCE_2='''def project(record, role, view='working', surface='detail'):
    versions = {r['id']: r['text'] for r in record['revisions']}
    choice = record['current_revision']
    if role != 'editor' or view != 'working':
        choice = record['approved_revision']
    visible = choice is not None
    return {'revision': choice, 'text': versions[choice] if visible else None,
            'approved': visible and choice == record['approved_revision'],
            'editable': visible and role == 'editor' and choice == record['current_revision']}
'''

K_RUBRIC={
 'K1':'Local key is (account,job_id), with done checked before send, and durable marker written only after successful send.',
 'K2':'Successful send plus failed mark_done leaves no done marker; sequential retry invokes send again. External actual duplication is not established.',
 'K3':'External idempotency/deployment contract is unknown; no explicit job id/key is sent by wrapper; successful acknowledgement is not final-effect verification.',
 'K4':'Same ID in another account has a distinct key; changed payload for completed same account/ID is skipped, with no payload comparison.',
 'K5':'Marking done before send risks suppressing a job whose send later fails; moving the marker is not a proven exactly-once repair.',
 'K6':'Navigation and concrete evidence support are usable, stale README claim is qualified; no need to reread source to supply the scoped obligations.',
}
S_RUBRIC={
 'S1':'Accurately distinguishes completions 40->60 (+50%) from opportunities 100->200 and rate 40%->30% (-10 percentage points; -25% relative if used).',
 'S2':'Nonrandom, different cohorts, no control; does not assert causality, savings or a proven benefit. Material caveats in ordinary visible copy.',
 'S3':'A meaningful argument explains why mixed evidence supports learning through a bounded test, not why rollout is already established.',
 'S4':'Ask remains at most 2 weeks, USD2000, 200 opportunities, stop on confirmed safety harm, review for rate >=40% without confirmed harm; no self-approval.',
 'S5':'Three usable page representations preserve audience and decision; freedom of charts/layout; ordinary visible caveats and correct visual meaning.',
}
OWNER_RUBRIC={
 'O1':'Current-role obligation delivered in final artifact, not just privately understood; authoritative contradictions are removed/resolved.',
 'O2':'No invented source facts, permissions, review/test claims or purpose shrinkage.',
 'O3':'No gratuitous renegotiation or irrelevant depth; remaining legal choices retained.',
 'O4':'Handoff package supports its intended recipient; all-work takeover is counted separately.',
}
K_REFERENCES=[
 'worker.py:L1-L10 checks done by (account,id), sends, then marks done. A successful send followed by a failed mark leaves a retry that sends again. gateway.py:L1-L6 supplies no explicit job key and does not reveal external deduplication or final effects; local repeat invocation is not proof of repeated external effect. store.py:L1-L5 distinguishes accounts and ignores payload changes once done. Moving done before send could lose attempts on send failure. README.md:L1-L2 exactly-once claim exceeds this evidence.',
 'Entry: execute in worker.py. Sequence: tuple key -> done check -> send -> durable mark. Failure table: send succeeds/mark fails => absent marker => next send; marker present => skip regardless of payload; account differs => distinct key. Gateway contract unknown (gateway.py:1-6), so external effect multiplicity remains conditional. Pre-marking trades duplicate-call exposure for possible missed delivery. Sources worker.py:1-10; store.py:1-5; README.md:1-2 is overbroad.'
]
S_REFERENCES=[
 '''Mixed evidence, not a proven improvement. Visible copy: 40/100 before, 60/200 after. Completions +50%; completion rate 40% to 30%, down 10 percentage points. Visual: two-row table with both denominators.\n---\nWhat we still need to learn. Different cohorts, no randomized or comparison group; neither causality nor savings established. Visual: observations versus unknowns, not a causal arrow.\n---\nDecision requested: bounded diagnostic pilot, not rollout. At most 2 weeks, USD2,000, 200 opportunities; stop for confirmed safety harm; review for completion rate >=40% without confirmed safety harm. Approval pending. Visual: compact limit/checkpoint panel.''',
 '''Should we learn more? Ask the director to authorize only the defined diagnostic pilot. Visual: decision tree with approve/not approve, neither selected.\n---\nWhy a bounded test, not expansion. Counts 40->60 on opportunities 100->200; rate 40%->30% (-10 percentage points), despite count growth of 50%. Cohorts differ with no control/randomization, so no causal/savings proof. Visual: aligned rate bars plus count table, caveats visible.\n---\nLimits and exit. 2 weeks maximum; USD2,000 ceiling; 200 opportunities maximum; stop on confirmed safety harm. End review asks for >=40% rate and no confirmed safety harm. Visual: stop/review checklist, not a rollout roadmap.'''
]

# Restricted worker: no imports/user filesystem/network, no dynamic reflection;
# subprocess timeout and OS CPU/memory limits. Not a general hostile-code sandbox.
WORKER=r'''
import ast, json, resource, sys
resource.setrlimit(resource.RLIMIT_CPU,(2,2))
resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
p=json.load(sys.stdin); tree=ast.parse(p['code'])
for node in ast.walk(tree):
    if isinstance(node,(ast.Import,ast.ImportFrom,ast.Global,ast.Nonlocal,ast.ClassDef,ast.AsyncFunctionDef,ast.With,ast.AsyncWith)):
        raise ValueError('unsupported statement')
    if isinstance(node,ast.Attribute) and node.attr.startswith('_'): raise ValueError('private attribute')
    if isinstance(node,ast.Name) and node.id.startswith('__'): raise ValueError('private name')
safe={n:__builtins__.__dict__[n] for n in ['dict','list','tuple','set','str','int','float','bool','len','next','iter','range','enumerate','zip','all','any','min','max','sorted','sum','isinstance','ValueError','KeyError','TypeError','Exception']}
scope={'__builtins__':safe}
exec(compile(tree,'<candidate>','exec'),scope)
f=scope['project']; rows=[]
for t in p['cases']:
    before=json.dumps(t['input'],sort_keys=True)
    try:
        result=f(*t['input']); ok=result==t['expected'] and json.dumps(t['input'],sort_keys=True)==before
        rows.append({'pass':ok,'result':result,'expected':t['expected']})
    except Exception as e: rows.append({'pass':False,'error':type(e).__name__})
print(json.dumps(rows,ensure_ascii=False))
'''


def f_check(content):
    code=content.strip()
    if code.startswith('```') and code.endswith('```'):
        code='\n'.join(code.splitlines()[1:-1])
    try:
        p=subprocess.run([sys.executable,'-I','-S','-c',WORKER],input=json.dumps({'code':code,'cases':f_cases()}),text=True,capture_output=True,timeout=5,env={'PATH':'/usr/bin:/bin'},cwd='/tmp')
        if p.returncode: return {'status':'execution_error','error':p.stderr[-1500:],'passed':0,'total':len(f_cases())}
        rows=json.loads(p.stdout)
        return {'status':'pass' if all(r['pass'] for r in rows) else 'fail','passed':sum(r['pass'] for r in rows),'total':len(rows),'failures':[{'case':i,**r} for i,r in enumerate(rows) if not r['pass']]}
    except subprocess.TimeoutExpired:
        return {'status':'timeout','passed':0,'total':len(f_cases())}


def evaluate(out):
    state=json.loads((out/'state.json').read_text()); rows=[]
    for t in state['trials']:
        if not t.get('receiver_result'): continue
        r=json.loads((out/t['receiver_result']/'result.json').read_text())
        if r['status']!='ok': continue
        content=r['parsed']['content']
        row={'case':t['case'],'arm':t['arm'],'receiver_unresolved':r['parsed']['unresolved']}
        if t['case']=='F': row['behavior']=f_check(content)
        elif t['case']=='K':
            row['reference_mentions']=sorted(set(re.findall(r'(?:worker|gateway|store)\.py|README\.md',content)))
            row['semantic_status']='requires frozen-rubric review, not keyword pass'
        else:
            row['page_count']=len(re.split(r'(?m)^\s*---\s*$',content.strip()))
            row['semantic_status']='requires frozen-rubric review; page representation only'
        rows.append(row)
    return {'evaluation_kind':'mechanical surfaces, before semantic author review','rows':rows}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    print(json.dumps(evaluate(a.out),ensure_ascii=False,indent=2))
