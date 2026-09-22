"""Single bounded C01 v4 development feedback; native Jev only, no retries."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
from experiments.typed_decision import c01
from experiments.typed_decision.campaign import request_key, sha, observed_transport
from experiments.typed_decision.contracts import DecisionResult, canonical, digest, provider_configuration, require
from experiments.typed_decision.providers import TypeSafeJevProvider, post_json
from experiments.typed_decision.session import Session, Limits, implementation_digest, read_record, write_once

DOCS = Path(__file__).resolve().parent
METHODS = DOCS.parent/'language-diagnostic/english'
LIMITS = Limits(max_calls=3, max_seconds=60, max_request_bytes=24576)
RESERVE = .002688
SCOPE = 'c01-v4-targeted'

def prepare():
    cases = json.loads((DOCS/'cases.json').read_text())['cases']
    keys = {}
    class Collector:
        def __init__(self, owner, found): self.owner, self.found = owner, found
        def evaluate(self, specs, context):
            self.found.add(request_key(specs, context))
            require(len(canonical({'state':context,'questions':[s.to_dict() for s in specs]})) <= LIMITS.max_request_bytes, 'request ceiling')
            values = {'entry_mode':'mindthus_intervention','unresolved_obligation':'clear','owner':self.owner,'applicable':'yes'}
            return {s.id:DecisionResult('ok',values[s.id]) for s in specs}
        def finish(self,*args): return None
    for case in cases:
        found=set()
        for owner in sorted(c01.METHODS): c01.run(Collector(owner,found),case['context'],METHODS)
        keys[case['id']]=sorted(found) or [digest({'mechanical_only':case['id']})]
    files=[DOCS/'protocol.md',DOCS/'cases.json',Path(__file__).resolve(), *sorted(METHODS.rglob('SKILL.md'))]
    return {'implementation':implementation_digest(),'graph':c01.GRAPH,
            'files':{str(p.relative_to(REPO)):sha(p) for p in files},'allowlist':keys,
            'provider_configuration':provider_configuration(TypeSafeJevProvider(choice_rounding=True)),
            'limits':asdict(LIMITS),'max_calls':39,'max_seconds':300,'max_cost_usd':.12,
            'reserve_per_call_usd':RESERVE,'case_ids':[c['id'] for c in cases],
            'authorization_ref':'Owner requested C01 implementation; c01-implementation/protocol.md'}

def score(case, report, nodes):
    result=report['result']
    answers={k:v for n in nodes for k,v in n['results'].items()}
    technical=result['status'] in ('provider_error','unsupported') or any(v['status'] in ('provider_error','unsupported') for v in answers.values())
    final={k:result.get(k) for k in ('route','owner')} in case['accepted']
    checks={k:answers.get(k,{}).get('status')=='ok' and answers[k]['value']==v for k,v in case['node_checks'].items()}
    return {'technical_failure':technical,'final_match':final and not technical,'node_matches':checks,
            'passed':not technical and final and all(checks.values()), 'observed':{k:v.get('value') for k,v in answers.items()}}

def run(root):
    freeze=json.loads((DOCS/'freeze.json').read_text())
    require(prepare()==freeze,'frozen source changed')
    require(not root.exists(),'terminal root; do not rerun')
    require(REPO not in root.resolve().parents,'trial must be outside repository')
    write_once(root/'campaign.json',freeze)
    cases=json.loads((DOCS/'cases.json').read_text())['cases']
    provider=TypeSafeJevProvider(choice_rounding=True)
    validate=provider.validate_runtime
    def locked(runtime):
        validate(runtime)
        path=root/'resolved-runtime.json'
        if path.exists(): require(read_record(path)==runtime.to_dict(),'resolved runtime drift within trial')
        else: write_once(path,runtime.to_dict())
    provider.validate_runtime=locked
    started=time.monotonic(); calls=0; rows=[]; stopped=None
    for case in cases:
        trial=root/case['id']
        def transport(url,headers,body,timeout):
            nonlocal calls
            remaining=300-(time.monotonic()-started)
            require(remaining>0 and calls<39 and (calls+1)*RESERVE<=.12,'global budget exhausted')
            calls+=1
            write_once(root/'wire-intents'/f'{calls:03d}.json',{'case_id':case['id'],'body_sha256':digest(body),'reserve_usd':RESERVE})
            raw=observed_transport(trial,post_json)(url,headers,body,min(timeout,60,remaining))
            require(time.monotonic()-started<=300,'deadline_exceeded')
            usage=raw.get('usage') or {}
            require(usage.get('input_tokens',0)<=64000,'input ceiling')
            require(usage.get('cost') is None or usage['cost']<=RESERVE,'cost ceiling')
            return raw
        provider.transport=transport
        admission={'scope':SCOPE+'-'+case['id'],'implementation':freeze['implementation'],
                   'provider_configuration':freeze['provider_configuration'],'limits':asdict(LIMITS),
                   'request_allowlist':freeze['allowlist'][case['id']], 'max_cost_usd':3*RESERVE,
                   'reserve_per_call_usd':RESERVE,'authorization_ref':freeze['authorization_ref'],
                   'freeze_sha256':sha(DOCS/'freeze.json')}
        with Session(trial,provider,scope=admission['scope'],limits=LIMITS,live_admission=admission) as session:
            report=c01.run(session,case['context'],METHODS)
        nodes=[read_record(trial/'calls'/k/'outcome.json') for k in report['call_keys']]
        row={'case_id':case['id'],**score(case,report,nodes),'result':report['result'], 'nodes':nodes,
             'usage':report['trial_usage'],'seconds':report['trial_inference_seconds'],'run_id':report['run_id']}
        rows.append(row);write_once(root/'rows'/(case['id']+'.json'),row)
        if row['technical_failure']: stopped='technical_failure'
        if report['result']['consumption']!='not_executed': stopped='unauthorized_consumption'
        if not set(case['context']['known_obligations'])<=set(report['result']['obligations']): stopped='lost_obligation'
        print(json.dumps({'case':case['id'],'passed':row['passed'],'observed':row['observed'],'route':report['result']['route'],'stop':stopped}),flush=True)
        if stopped: break
    summary={'complete':len(rows)==len(cases) and stopped is None,'stop_reason':stopped,'planned':len(cases),
             'passed':sum(r['passed'] for r in rows),'unrun':len(cases)-len(rows),'calls':calls,
             'reserved_usd':calls*RESERVE,'wall_seconds':time.monotonic()-started,'rows':rows}
    write_once(root/'summary.json',summary)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run']);parser.add_argument('--root',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':
        path=DOCS/'freeze.json';require(not path.exists(),'freeze exists')
        path.write_text(json.dumps(prepare(),indent=2)+'\n')
    else:
        require(args.root is not None,'root required');run(args.root)
