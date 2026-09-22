"""Frozen CPA chat consumption trial; no routing inference or model fallback."""
import json
import math
from pathlib import Path
import re
import sys
import time
REPO=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(REPO))
from experiments.typed_decision.contracts import canonical,digest,require
from experiments.typed_decision.providers import post_json
from experiments.typed_decision.session import read_record,write_once,safe_failure_reason
DOCS=Path(__file__).resolve().parent
ENDPOINT='https://cpa.72live.com/v1/chat/completions'
MODEL='deepseek-v4.1-flash'
SYSTEM=('You are the downstream assistant in an admitted read-only C01 integration trial. '
        'Handle the user task using the supplied routing handoff and method contract if present. '
        'Give a useful final answer in Chinese, within 450 Chinese characters unless the task needs less. '
        'Do not report the test or routing machinery. Do not claim external actions or verified facts '
        'that did not occur. No external tools are available. Preserve user constraints and evidence limits.')

def body(case):
    return {'model':MODEL,'temperature':0,'stream':False,'max_tokens':1600,
            'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':case['prompt']}]}

def prepare():
    cases=json.loads((DOCS/'inputs.json').read_text())['cases']
    requests={c['id']:digest(body(c)) for c in cases}
    require(len(cases)==6 and len(requests)==6,'fixed case count')
    require(all(len(canonical(body(c)))<=49152 for c in cases),'request ceiling')
    return {'model':MODEL,'endpoint':ENDPOINT,'requests':requests,'max_calls':6,'max_seconds':240,
            'max_request_bytes':49152,'max_tokens_per_call':1600,'retries':0,'semantic_revisions':0,
            'files':{str(p.relative_to(REPO)):__import__('hashlib').sha256(p.read_bytes()).hexdigest()
                     for p in [DOCS/'inputs.json',DOCS/'protocol.md',Path(__file__).resolve(),
                               REPO/'experiments/typed_decision/providers.py',REPO/'experiments/typed_decision/contracts.py',
                               REPO/'experiments/typed_decision/session.py']},
            'monetary_cost':'unknown unless reported; no USD-cap claim','purpose':'chat handoff consumption; not original-A or holdout'}

def run(root,key):
    frozen=json.loads((DOCS/'freeze.json').read_text())
    require(prepare()==frozen,'frozen inputs/source changed')
    require(not root.exists(),'trial root exists; no resubmission')
    write_once(root/'manifest.json',frozen)
    cases=json.loads((DOCS/'inputs.json').read_text())['cases']
    rows=[];start=time.monotonic();stop=None;resolved=None
    for case in cases:
        remaining=240-(time.monotonic()-start)
        if remaining<=0:stop='budget_exhausted';break
        payload=body(case);raw=None
        require(digest(payload)==frozen['requests'][case['id']],'unfrozen request')
        write_once(root/case['id']/'intent.json',{'request_sha256':digest(payload),'request_bytes':len(canonical(payload)),
                                               'model':MODEL,'source_run_id':case['source_run_id']})
        begin=time.monotonic()
        row={'case_id':case['id'],'status':'failed','usage':{},'cost_usd':None,'answer':None}
        try:
            raw=post_json(ENDPOINT,{'Authorization':'Bearer '+key,'Content-Type':'application/json',
                                  'User-Agent':'Mindthus-C01-integration/1'},payload,min(60,remaining))
            require(time.monotonic()-start<=240,'deadline_exceeded')
            model=raw.get('model')
            row['reported_model']=model if isinstance(model,str) and re.fullmatch(r'[a-zA-Z0-9_./-]{1,128}',model) else None
            usage=raw.get('usage') or {}
            row['usage']={k:v for k,v in usage.items() if k in ('prompt_tokens','completion_tokens','total_tokens','cost')
                          and type(v) in (int,float) and math.isfinite(v) and v>=0}
            row['cost_usd']=None  # CPA usage.cost has no verified currency contract.
            require(model==MODEL and (resolved is None or model==resolved),'model identity mismatch')
            resolved=model
            choices=raw.get('choices')
            require(isinstance(choices,list) and len(choices)==1,'invalid choice count')
            choice=choices[0];finish=choice.get('finish_reason')
            row['finish_reason']=finish if finish in ('stop','length','tool_calls','content_filter') else 'unknown'
            require(finish=='stop','incomplete or nontext completion')
            message=choice.get('message') or {}
            require(not message.get('tool_calls'),'unexpected tool request')
            answer=message.get('content')
            require(isinstance(answer,str) and bool(answer.strip()),'empty answer')
            require(key not in answer,'credential reflection')
            row.update(status='complete',answer=answer)
        except Exception as exc:
            row['error']=safe_failure_reason(exc);stop='technical_failure'
        finally:
            row['elapsed_seconds']=time.monotonic()-begin
            write_once(root/case['id']/'outcome.json',row)
        rows.append(row)
        print(json.dumps({'case':case['id'],'status':row['status'],'model':row.get('reported_model'),
                          'finish_reason':row.get('finish_reason'),'stop':stop}),flush=True)
        if stop:break
    summary={'planned':6,'attempts':len(rows),'complete':len(rows)==6 and stop is None,
             'unrun':6-len(rows),'stop_reason':stop,'rows':rows,'wall_seconds':time.monotonic()-start,
             'resolved_model':resolved,'provider_snapshot':'unobservable behind CPA',
             'new_jev_calls':0,'native_skill_load':'not_observed','qualification':False}
    write_once(root/'summary.json',summary)
    return summary

if __name__=='__main__':
    path=DOCS/'freeze.json';require(not path.exists(),'freeze already exists')
    path.write_text(json.dumps(prepare(),indent=2)+'\n')
