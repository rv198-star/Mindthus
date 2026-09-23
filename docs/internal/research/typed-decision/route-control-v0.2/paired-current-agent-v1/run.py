"""Nine frozen task snapshots; real Jev and the current Agent, no CPA client.

This driver prepares inputs and collects evidence around existing entry.run. It
never fabricates host answers or executes a parallel implementation of routing.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))
from experiments.typed_decision import entry, route_control as rc, relationship_assessment as rel
from experiments.typed_decision.contracts import canonical, digest, provider_configuration
from experiments.typed_decision.providers import TypeSafeJevProvider
from experiments.typed_decision.current_host import CurrentAgentHost, submit_response
from experiments.typed_decision.relationship_live import deadline_post_json, no_secrets
from experiments.typed_decision.session import implementation_digest, read_record, write_once, RecoveryRequired

ROOT = Path('/srv/agentdock/tmp/mindthus-six-scenes-current-agent-v1')
FREEZE = HERE / 'freeze.json'
AUTH = 'Owner approved named small real Jev/current-Agent end-to-end and advisory/committed development comparison 2026-09-23; PLAN.md'
CONTEXT = 'current-ChatGPT-conversation-six-scenes-20260923-shared-not-independent'

def save(path, value):
    if path.exists():
        assert read_record(path) == value, 'immutable record mismatch'
    else:
        write_once(path, value)

def filesha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def specimens(): return json.loads((HERE/'cases.json').read_bytes())['cases']

def objects(p):
    v = TypeSafeJevProvider(model='jev-1.13.0', choice_rounding=True, transport=deadline_post_json)
    e = CurrentAgentHost(p['authority']['owner_ref'])
    c = CurrentAgentHost(p['authority']['owner_ref'], role='correction') if p['relationship'] else None
    return v, e, c

class Acceptor:
    def __init__(self, case_id, owner):
        self.case_id, self.identity = case_id, owner
        self.configuration = {'kind':'current-agent-source-checked-acceptance.v1','case_id':case_id,'owner':owner}
    def accept(self, edge, artifact, packet):
        path = ROOT/self.case_id/'host-acceptance'/f"{edge['id']}.json"
        if not path.exists():
            return {'owner_ref':self.identity,'dependency_id':edge['id'], 'artifact_sha256':artifact['artifact_sha256'],
                    'accepted':False,'reason':'No actual host review supplied; do not fake acceptance'}
        x = json.loads(path.read_bytes())
        assert x['artifact_sha256'] == artifact['artifact_sha256'] and x['owner_ref'] == self.identity
        return x

def prepare():
    bundle, qs, bindings = rc.load_policy(REPO)
    rows = specimens(); admissions = {}; identities = {}; max_calls = 0
    for row in rows:
        i, p = row['id'], row['packet']; v,e,c = objects(p)
        cr = rc.compile_route(p,REPO,bundle,qs,bindings)
        relation = rel.compile_packet(p['relationship'],REPO) if p['relationship'] else None
        n = (1 if cr.specs else 0) + (2 if relation else 0)
        max_calls += n
        a = {'schema':'mindthus.route-control-live.v1','mode':rc.MODE,'root':str(ROOT/i),
             'implementation':implementation_digest(),'source_bindings':bundle['sources'],
             'provider':provider_configuration(v),'packet_hashes':[digest(p)],'authorization_ref':AUTH,
             'ceilings':{'judgments':n,'corrections':1 if c else 0,'organize':0,'arbitrations':0,
                        'executions':p['task_budget']['max_calls'],'requests':n+(1 if c else 0),'reserve_per_jev_usd':.02},
             'executor':e.configuration,'arbitrator':None,'corrector':c.configuration if c else None,'organizer':None}
        rc._admission(a,ROOT/i,p,v,bundle,{'executor':e,'arbitrator':None,'corrector':c,'organizer':None})
        admissions[i]=a
        identities[i]={'input':digest(p),'route_specs':digest([s.to_dict() for s in cr.specs]),
                       'route_context':digest(cr.context),'route_question_count':len(cr.specs),
                       'relationship_specs':digest([s.to_dict() for s in relation.specs]) if relation else None,
                       'relationship_context':digest(relation.context) if relation else None}
    assert len(rows)==9 and max_calls==12
    f={'schema':'mindthus.six-scenes-freeze.v1','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
       'implementation':implementation_digest(),'files':{n:filesha(HERE/n) for n in ['PLAN.md','cases.json','acceptance.json','run.py']},
       'case_ids':[x['id'] for x in rows],'admissions':admissions,'identities':identities,'max_Jev_calls':max_calls,
       'max_Jev_reserved_usd':.24,'extra_LLM_API_calls':0,'retry':0,'context_ref':CONTEXT,'independent_contexts':False,
       'claim_ceiling':'paired development observation; exposed cases and shared current context; no statistical causal or all-method qualification'}
    save(FREEZE,f)
    print(json.dumps({'freeze':digest(f),'cases':f['case_ids'],'max_Jev_calls':max_calls,'actual_calls':0}))

def verify():
    f=read_record(FREEZE)
    assert f['implementation']==implementation_digest()
    assert all(filesha(HERE/n)==h for n,h in f['files'].items())
    return f

def execute(ids):
    f=verify(); allowed=set(f['case_ids']); assert set(ids)<=allowed
    assert not os.environ.get('MINDTHUS_HOST_API_KEY') and not os.environ.get('OPENROUTER_API_KEY')
    key=sys.stdin.readline().strip()
    assert key or all((ROOT/i/'manifest.json').exists() for i in ids), 'credential required only for actual new Jev requests'
    prior=os.environ.get('TYPESAFE_API_KEY')
    if key: os.environ['TYPESAFE_API_KEY']=key
    try:
        for row in specimens():
            i,p=row['id'],row['packet']
            if i not in ids: continue
            v,e,c=objects(p)
            result=entry.run(ROOT/i,v,p,REPO,mode=rc.MODE,executor=e,corrector=c,
                             live_admission=f['admissions'][i],
                             artifact_acceptor=Acceptor(i,p['authority']['owner_ref']) if p['dependencies'] else None)
            no_secrets(result)
            path=ROOT/'snapshots'/(i+'-'+digest(result)+'.json');save(path,result)
            # Mutable convenience pointer only; original records and snapshot remain immutable.
            (ROOT/(i+'-latest.json')).write_bytes(canonical(result)+b'\n')
            print(json.dumps({'id':i,'status':result.get('status'),'reason':result.get('reason'),
                  'counts':result['counts'],'pending':result['pending'],'host_request':result.get('host_request'),
                  'route':result['route']['per_issue'] if result.get('route') else None,
                  'outputs':{k:v['text'] for k,v in result.get('outputs',{}).items()}},ensure_ascii=False),flush=True)
    finally:
        if prior is None: os.environ.pop('TYPESAFE_API_KEY',None)
        else: os.environ['TYPESAFE_API_KEY']=prior

def view(i):
    row=next(x for x in specimens() if x['id']==i)
    result=read_record(ROOT/(i+'-latest.json'))
    root=ROOT/i; initial=[]
    for p in sorted(root.glob('turns/*/inputs/*/steps/*/calls/*/outcome.json')):
        step=p.relative_to(root).parts[5]
        if step not in ('route','relation__initial'):continue
        r=read_record(p)
        initial.append({'step':step,'source_ref':str(p),'record_sha256':filesha(p),'results':r['results']})
    common={'case_id':i,'original_input':row['packet'],'Jev_initial_observations':initial,
            'initial_observation_sha256':digest(initial),'shared_context_ref':CONTEXT,
            'advisory_instruction':'Treat observations and suggested route as advice; choose a sufficient approach freely. Preserve original sources, scope, uncertainty and permissions. Do not intentionally degrade your answer for comparison.'}
    if result.get('route'):
        common['suggested_route']={k:result['route'][k] for k in ('per_issue','mandatory_reads','artifact_edges','unresolved')}
    save(ROOT/'comparison-inputs'/f'{i}.json',common)
    print(json.dumps(common,ensure_ascii=False,indent=2))
    if result.get('host_request'):
        h=read_record(Path(result['host_request']))
        print('\nCURRENT_HOST_REQUEST\n'+json.dumps({k:v for k,v in h.items() if k!='request'},ensure_ascii=False))
        req=h['request']
        if h['role']=='correction':
            print('NAMED_CORRECTION',json.dumps(req['plan'],ensure_ascii=False))
        elif h['role']=='execution':
            print('BOUND_EXECUTION',json.dumps({k:req[k] for k in ('route_id','revision','issue','execute_methods')},ensure_ascii=False))
            for m,data in req['loaded_methods'].items():
                print('METHOD',m,data['path'],data['sha256']);print(data['content'])

def main():
    a=argparse.ArgumentParser();a.add_argument('action',choices=['prepare','verify','run','view']);a.add_argument('ids',nargs='*');x=a.parse_args()
    if x.action=='prepare':prepare()
    elif x.action=='verify':print(json.dumps({'verified':True,'freeze':digest(verify())}))
    elif x.action=='run':execute(x.ids or read_record(FREEZE)['case_ids'])
    else:verify();view(x.ids[0])
if __name__=='__main__': main()
