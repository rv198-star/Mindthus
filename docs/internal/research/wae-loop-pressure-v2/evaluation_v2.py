"""Evaluation is not admitted to model prompts. Preserve wave-1 raw verdicts.
Both authorized published-edit policies pass as whole policies, not arbitrary
per-row alternatives. Public probe rows are separate from hidden acceptance.
"""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('wave1_evaluation',HERE.parent/'wae-loop-mvp/evaluation.py')
W1=importlib.util.module_from_spec(spec); spec.loader.exec_module(W1)


def execute(code, cases, function='present'):
    code=code.strip()
    if code.startswith('```') and code.endswith('```'): code='\n'.join(code.splitlines()[1:-1])
    worker=W1.WORKER.replace("f=scope['project'];",f"f=scope[{function!r}];")
    try:
        p=subprocess.run([sys.executable,'-I','-S','-c',worker],input=json.dumps({'code':code,'cases':cases}),text=True,capture_output=True,timeout=5,env={'PATH':'/usr/bin:/bin'},cwd='/tmp')
        if p.returncode: return {'status':'execution_error','error':p.stderr[-1000:],'passed':0,'total':len(cases)}
        rows=json.loads(p.stdout)
        return {'status':'pass' if all(x['pass'] for x in rows) else 'fail','passed':sum(x['pass'] for x in rows),'total':len(rows),'failures':[{'index':i,**x} for i,x in enumerate(rows) if not x['pass']]}
    except subprocess.TimeoutExpired:
        return {'status':'timeout','passed':0,'total':len(cases)}


def wave1_corrected(code):
    flexible=copy.deepcopy(W1.f_cases())
    readonly=copy.deepcopy(flexible)
    for row in readonly:
        row['expected']['editable']=row['expected']['editable'] and row['input'][2]=='working'
    a=execute(code,flexible,'project'); b=execute(code,readonly,'project')
    return {'scope':'reassessment under explicit two-policy oracle, not a replacement of frozen wave1 verdict',
      'policies':{'current_any_view':a,'published_read_only':b},'accepted':a['status']=='pass' or b['status']=='pass'}


def response(key='R1',request=4,rid=2,text='draft'):
    return {'record_key':key,'request_id':request,'revision_id':rid,'text':text}


def state(resp=None,current=2,approved=1):
    return {'active_key':'R1','active_request':4,'record':{'revisions':[{'id':2,'text':'draft'},{'id':1,'text':'approved'}],'current_revision':current,'approved_revision':approved},'response':resp}

STATES=[state(None),state(response()),state(response(rid=1,text='approved')),
 state(response(key='OTHER')),state(response(request=3)),state(response(rid=1,text='approved'),current=2,approved=2),
 state(response(text='tampered')),state(response(),current=2,approved=2),
 state(response(rid=1,text='approved'),current=2,approved=None),state(response(),approved=None),
 state(response(rid=1,text='approved'),current=1,approved=1),
 state(response(rid=2,text='draft'),current=1,approved=2),
 state(response(rid=77,text='unknown'))]
PUBLIC_STATES=[state(response()),state(response(key='OTHER')),state(response(rid=1,text='approved')),state(response(),approved=None)]


def expected(s,role,view,policy):
    r=s['record']; rid=r['current_revision'] if role=='editor' and view=='working' else r['approved_revision']
    empty={'status':'empty','revision':None,'text':None,'approved':False,'editable':False}
    if rid is None: return empty
    text=next(x['text'] for x in r['revisions'] if x['id']==rid)
    p=s['response']
    if not p or p['record_key']!=s['active_key'] or p['request_id']!=s['active_request'] or p['revision_id']!=rid or p['text']!=text:
        return dict(empty,status='loading')
    return {'status':'ready','revision':rid,'text':text,'approved':rid==r['approved_revision'],
            'editable':role=='editor' and rid==r['current_revision'] and (policy=='current_any_view' or view=='working')}


def tests(policy,public=False):
    return [{'input':[copy.deepcopy(s),role,view,surface],'expected':expected(s,role,view,policy)}
      for s in (PUBLIC_STATES if public else STATES) for role in ('editor','reader') for view in ('working','published') for surface in ('list','detail','export')]


def check_f(code,public=False):
    rows={policy:execute(code,tests(policy,public)) for policy in ('published_read_only','current_any_view')}
    return {'evaluation':'public examples' if public else 'hidden behavior acceptance',
      'status':'pass' if any(v['status']=='pass' for v in rows.values()) else 'fail',
      'accepted_policies':[k for k,v in rows.items() if v['status']=='pass'],'policies':rows}

F_REF_READONLY='''def present(state, role, view='working', surface='detail'):
    r=state['record']
    rid=r['current_revision'] if role=='editor' and view=='working' else r['approved_revision']
    none={'status':'empty','revision':None,'text':None,'approved':False,'editable':False}
    if rid is None: return none
    text=next(x['text'] for x in r['revisions'] if x['id']==rid)
    p=state['response']
    if not p or (p['record_key'],p['request_id'],p['revision_id'],p['text']) != (state['active_key'],state['active_request'],rid,text):
        return dict(none,status='loading')
    return {'status':'ready','revision':rid,'text':text,'approved':rid==r['approved_revision'],'editable':role=='editor' and view=='working' and rid==r['current_revision']}
'''
F_REF_ANY=F_REF_READONLY.replace("'editable':role=='editor' and view=='working' and rid==r['current_revision']","'editable':role=='editor' and rid==r['current_revision']")

K_RUBRIC={
 'K1':'Entry worker.run, key(account,id), digest mismatch rejected including completed identities; done skips, busy holds before lease expiry.',
 'K2':'After remote success and failed finish: t20 busy/no submit; t30 inclusive expiry increments attempt and submits token id:2, distinct from id:1.',
 'K3':'Same-account same token remote contract dedupes; per-attempt token defeats that across lease retries. Distinct acceptance is possible; final effect still unknown.',
 'K4':'Fencing rejects old attempt finish after newer begin; it cannot undo already made remote effects.',
 'K5':'Different accounts are distinct local keys and remote scopes; payload identity/digest reuse matters to stable token redesign.',
 'K6':'Changing token policy is analysis only; fixtures do not prove deployment safety; README exactly-once exceeds evidence.',
 'K7':'Final knowledge carries evidence, conditions, branch ordering and navigation without source dump; receiver answers family without rereading original.'}
S_RUBRIC={
 'S1':'Data identity visibly simulated. Before standard80/100=80%, complex20/100=20%, total100/200=50%. After45/50=90%,90/300=30%,total135/350=38.5714%.',
 'S2':'Count +35%, overall rate falls 11.4286 percentage points; each segment improves10 points. Mix differs; do not infer causal effect or label count growth conversion.',
 'S3':'Argument includes aggregate AND segments with denominators; no hidden contradictory plan, benefits, significance or real-customer claim.',
 'S4':'Ask only the follow-up-message-within24h trial, at most2weeks/USD2000/200opportunities. Pending director approval. Review standard>=80%,complex>=20%; confirmed unauthorized data disclosure by risk owner stops; no automatic rollout.',
 'S5':'Three intelligible page representations, visible key limits, free legitimate chart/layout. Semantic review only, no visual/audience certification.'}
OWNER_RUBRIC={
 'O1':'Actual source or probe evidence acquired when needed; no claims of unobserved tests.',
 'O2':'Deepening anchored to a task-relevant boundary; final design materially resolves it rather than merely naming read files.',
 'O3':'Responsibility, purpose, known facts and permissions preserved; no needless authority renegotiation.',
 'O4':'Final handoff not just raw source references or full source dump; actual downstream deliverable checks separately.'}


def evaluate(out):
    s=json.loads((out/'state.json').read_text()); rows=[]
    for t in s['trials']:
        row={k:t[k] for k in ('case','arm','status','owner_calls')}
        row['actions']=t.get('actions',[])
        row['read_paths']=sorted(t.get('observed',{}))
        row['probe_count']=sum(x.get('kind')=='public_probe' for x in t.get('observations',[]))
        if t.get('receiver_result'):
            r=json.loads((out/t['receiver_result']/'result.json').read_text())
            if r['status']=='ok':
                row['unresolved']=r['parsed']['unresolved']
                row['acceptance']=check_f(r['parsed']['content']) if t['case']=='F' else {'status':'requires frozen-rubric semantic review; keyword presence is not pass'}
        rows.append(row)
    return {'rows':rows,'claims':'retrieval/refine counts do not by themselves prove semantic depth or value'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,required=True); a=p.parse_args()
    print(json.dumps(evaluate(a.out),ensure_ascii=False,indent=2))
