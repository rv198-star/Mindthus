"""Frozen same-graph development comparison. Credentials only from process environment."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))
from experiments.typed_decision import c01
from experiments.typed_decision.campaign import request_key, sha, observed_transport
from experiments.typed_decision.contracts import DecisionResult, canonical, digest, provider_configuration, require
from experiments.typed_decision.providers import ChatProvider, TypeSafeJevProvider, post_json
from experiments.typed_decision.review_trial import score_joint
from experiments.typed_decision.session import Session, Limits, implementation_digest, read_record, write_once, safe_failure_reason

DOCS = Path(__file__).resolve().parent
DATA = DOCS.parent/'language-diagnostic'
LIMITS = Limits(max_calls=3, max_seconds=60, max_request_bytes=24576)
RESERVES = {'B': .14, 'C': .002688}
DISPUTED = {'L09','L10','L11','L12','L14','L15','L17','L18'}


def providers():
    return {'B': ChatProvider('anthropic/claude-sonnet-4.6'),
            'C': TypeSafeJevProvider(choice_rounding=True)}


def prepare():
    cases = json.loads((DATA/'cases.json').read_text())['cases']
    root = DATA/'english'
    allowlist = {}
    class Collector:
        def __init__(self, owner, keys): self.owner, self.keys = owner, keys
        def evaluate(self, specs, context):
            self.keys.add(request_key(specs, context))
            require(len(canonical({'state':context,'questions':[s.to_dict() for s in specs]}))
                    <= LIMITS.max_request_bytes, 'projected request too large')
            values = {'entry_mode':'mindthus_intervention','unresolved_obligation':'clear',
                      'owner':self.owner,'applicable':'yes'}
            return {s.id:DecisionResult('ok',values[s.id]) for s in specs}
        def finish(self,*_): return None
    for case in cases:
        keys = set()
        for owner in sorted(c01.METHODS): c01.run(Collector(owner,keys),case['english'],root)
        # Session requires nonempty allowlist, even for the mechanical no-call cases.
        allowlist[case['id']] = sorted(keys) or [digest({'mechanical_only':case['id']})]
    files = [DOCS/'protocol.md', Path(__file__).resolve(), DATA/'cases.json']
    files += sorted(root.rglob('SKILL.md'))
    return {'version':'c01-paired-development-v1','implementation':implementation_digest(),
            'graph':c01.GRAPH,'files':{str(p.relative_to(REPO)):sha(p) for p in files},
            'providers':{a:provider_configuration(p) for a,p in providers().items()},
            'limits':asdict(LIMITS),'reserve_per_call':RESERVES,'global_cost_cap_usd':4,
            'global_call_cap':180,'global_seconds':1200,'allowlist':allowlist,
            'cases':[c['id'] for c in cases],'sensitivity_excluded':sorted(DISPUTED),
            'order':[[c['id'],a] for i,c in enumerate(cases) for a in
                     (('B','C') if i%2==0 else ('C','B'))],
            'authorization':'Owner: 重新设计重测吧; paired-retest/protocol.md',
            'semantic_revisions':0,'retries':0,'purpose':'development attribution; not qualification'}


def scoring(case, report, outcomes):
    result = report['result']
    technical = any(v['status'] in ('provider_error','unsupported')
                    for n in outcomes for v in n['results'].values())
    technical |= result['status'] == 'provider_error'
    observed = {k:result.get(k) for k in ('entry_mode','route','owner')}
    final = score_joint(observed,[{k:a[k] for k in ('route','owner')} for a in case['accepted']])['joint']
    joint = score_joint(observed,case['accepted'])['joint']
    return {'technical_failure':bool(technical),'final_match':bool(final and not technical),
            'joint_match':bool(joint and not technical), 'observed':observed}


def summarize(rows, cases):
    lookup = {(r['case_id'],r['arm']):r for r in rows}
    answer = {}
    for name, ids in [('all_semantic',[c['id'] for c in cases if c01.input_problem(c['english']) is None]),
                     ('sensitivity',[c['id'] for c in cases if c01.input_problem(c['english']) is None
                                     and c['id'] not in DISPUTED])]:
        data = {'planned_pairs':len(ids),'paired':dict(Counter(
            ('both' if lookup[(i,'B')]['final_match'] and lookup[(i,'C')]['final_match'] else
             'B_only' if lookup[(i,'B')]['final_match'] else
             'C_only' if lookup[(i,'C')]['final_match'] else 'neither')
            for i in ids if (i,'B') in lookup and (i,'C') in lookup))}
        for arm in ('B','C'):
            rr = [lookup[(i,arm)] for i in ids if (i,arm) in lookup]
            data[arm] = {'observed':len(rr),'final_matches':sum(r['final_match'] for r in rr),
                         'joint_matches':sum(r['joint_match'] for r in rr),
                         'technical_failures':sum(r['technical_failure'] for r in rr),
                         'unrun':len(ids)-len(rr),
                         'fallbacks':sum(r['result']['route']=='llm_fallback' for r in rr),
                         'semantic_abstentions':sum(any(v['status']=='abstain' for n in r['nodes']
                              for v in n['results'].values()) for r in rr),
                         'reasons':dict(Counter(r['result']['reason'] for r in rr))}
        answer[name] = data
    return answer


def run(root):
    freeze = json.loads((DOCS/'freeze.json').read_text())
    require(prepare() == freeze,'freeze changed')
    require(not root.exists(),'new comparison root required; no automatic restart')
    write_once(root/'campaign.json',freeze)
    cases = json.loads((DATA/'cases.json').read_text())['cases']
    by_id = {c['id']:c for c in cases}
    engines = providers()
    started = time.monotonic()
    rows, wire_records = [], []
    stop = None
    for arm, provider in engines.items():
        validator = provider.validate_runtime
        def locked(runtime, arm=arm, validator=validator):
            validator(runtime)
            lock = root/(arm+'-runtime.json')
            if lock.exists(): require(read_record(lock)==runtime.to_dict(),'resolved runtime drift within trial')
            else: write_once(lock,runtime.to_dict())
        provider.validate_runtime = locked
    for ident, arm in freeze['order']:
        case = by_id[ident]
        trial = root/arm/ident
        provider = engines[arm]
        def transport(url, headers, body, timeout):
            require(len(wire_records)<180,'global call cap')
            require(time.monotonic()-started<1200,'global time cap')
            require(sum(x['accounted_cost_usd'] for x in wire_records)+RESERVES[arm]<=4,
                    'global cost cap')
            if arm=='B':
                body = {**body,'provider':{'only':['Anthropic'],'allow_fallbacks':False,
                        'require_parameters':True,'max_price':{'prompt':3,'completion':15}}}
            require(len(canonical(body))<=32768,'wire byte cap')
            record = {'arm':arm,'case_id':ident,'body_sha256':digest(body),
                      'reserved_usd':RESERVES[arm],'accounted_cost_usd':RESERVES[arm]}
            path = root/'wire'/f'{len(wire_records)+1:03d}.json'
            write_once(root/'wire'/f'{len(wire_records)+1:03d}-intent.json',record)
            try:
                call = observed_transport(trial,post_json) if arm=='C' else post_json
                raw = call(url,headers,body,min(timeout,60))
                usage = raw.get('usage') or {}
                # Allowlisted numeric telemetry only; never persist headers or response prose.
                record['usage'] = {k:v for k,v in usage.items() if k in
                    ('prompt_tokens','completion_tokens','input_tokens','output_tokens','cost')
                    and type(v) in (int,float) and math.isfinite(v) and v>=0}
                cost = record['usage'].get('cost')
                if arm=='B' and cost is not None: record['accounted_cost_usd'] = max(cost,0)
                record['resolved_model_matches'] = raw.get('model')==provider.serving_identity.requested_model
                if arm=='B':
                    record['finish_reason'] = raw.get('choices',[{}])[0].get('finish_reason') in ('stop',)
                require(cost is None or cost<=RESERVES[arm],'observed cost exceeds reserve')
                prompt = record['usage'].get('prompt_tokens',record['usage'].get('input_tokens'))
                require(prompt is None or prompt<=(33280 if arm=='B' else 64000),'input ceiling exceeded')
                completion = record['usage'].get('completion_tokens')
                require(arm!='B' or completion is None or completion<=2048,'output ceiling exceeded')
                return raw
            except Exception as exc:
                record['failure'] = safe_failure_reason(exc)
                raise
            finally:
                write_once(path,record)
                wire_records.append(record)
        provider.transport = transport
        admission = {'scope':'c01-paired-v1-'+arm+'-'+ident,'implementation':freeze['implementation'],
                     'provider_configuration':freeze['providers'][arm],'limits':asdict(LIMITS),
                     'request_allowlist':freeze['allowlist'][ident],
                     'max_cost_usd':3*RESERVES[arm],'reserve_per_call_usd':RESERVES[arm],
                     'authorization_ref':freeze['authorization'],'freeze_sha256':sha(DOCS/'freeze.json')}
        try:
            with Session(trial,provider,scope=admission['scope'],limits=LIMITS,live_admission=admission) as session:
                report = c01.run(session,case['english'],DATA/'english')
            nodes = [read_record(trial/'calls'/key/'outcome.json') for key in report['call_keys']]
            row = {'case_id':ident,'arm':arm,'mechanical_d0':c01.input_problem(case['english']) is not None,
                   'sensitivity_excluded':ident in DISPUTED,**scoring(case,report,nodes),
                   'result':report['result'],'nodes':nodes,'run_id':report['run_id'],
                   'call_keys':report['call_keys'],'usage':report['trial_usage'],
                   'inference_seconds':report['trial_inference_seconds']}
            rows.append(row)
            write_once(root/'rows'/(ident+'-'+arm+'.json'),row)
            if row['technical_failure']: stop='technical_failure'
            if report['result']['consumption']!='not_executed': stop='unauthorized_consumption'
            if not set(case['english']['known_obligations'])<=set(report['result']['obligations']):
                stop='lost_known_obligation'
            if any('failure' in r for r in wire_records): stop=stop or 'wire_or_budget_failure'
            print(json.dumps({'case':ident,'arm':arm,'final_match':row['final_match'],
                              'joint_match':row['joint_match'],'stop':stop}),flush=True)
        except Exception as exc:
            stop='runner_failure:'+type(exc).__name__
        if stop: break
    summary = {'stop_reason':stop,'complete':len(rows)==64 and stop is None,
               'analysis':summarize(rows,cases),'rows':rows,
               'unrun':[pair for pair in freeze['order'] if not any(r['case_id']==pair[0] and
                         r['arm']==pair[1] for r in rows)],
               'total_calls':len(wire_records),'accounted_ceiling_usd':sum(r['accounted_cost_usd'] for r in wire_records),
               'gross_reservations_usd':sum(r['reserved_usd'] for r in wire_records),
               'wire_records':wire_records,'wall_seconds':time.monotonic()-started,
               'qualification':False,'original_A':'not_run','holdout':'not_run',
               'host_translation_design_cost':'unknown'}
    write_once(root/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('rows','wire_records','unrun')},ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('--root',type=Path)
    args=parser.parse_args()
    if args.action=='prepare':
        path=DOCS/'freeze.json'
        require(not path.exists(),'freeze already exists')
        path.write_text(json.dumps(prepare(),ensure_ascii=False,indent=2)+'\n')
        print('freeze_created; no inference')
    else:
        require(args.root is not None,'root required')
        run(args.root)
