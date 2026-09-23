"""Local artifact handling for current-Agent authored responses; no inference or routing.
Uses the frozen runner unchanged. Latest convenience pointers are plain JSON, not
checksummed journal records; initial comparisons only include initial observations.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import sys
sys.path.insert(0, '/srv/agentdock/projects/Mindthus')
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision.contracts import canonical, digest
from experiments.typed_decision.current_host import submit_response
from experiments.typed_decision.session import read_record, write_once

REPO = Path('/srv/agentdock/projects/Mindthus')
ROOT = Path('/srv/agentdock/tmp/mindthus-six-scenes-current-agent-v1')
BASE = REPO/'docs/internal/research/typed-decision/route-control-v0.2/paired-current-agent-v1'
CONTEXT = 'current-ChatGPT-conversation-six-scenes-20260923-shared-not-independent'
UNKNOWN = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}
CASES = {c['id']: c for c in json.loads((BASE/'cases.json').read_bytes())['cases']}

def save(p, value):
    if p.exists():
        assert read_record(p)==value, 'immutable artifact changed'
    else:
        write_once(p, value)

def latest(i):
    return json.loads((ROOT/(i+'-latest.json')).read_bytes())

def view(i):
    obs=[]
    for p in sorted((ROOT/i).glob('turns/*/inputs/*/steps/*/calls/*/outcome.json')):
        step=p.relative_to(ROOT/i).parts[5]
        if step not in ('route','relation__initial'): continue
        o=read_record(p)
        obs.append({'step':step,'source_ref':str(p), 'record_sha256':hashlib.sha256(p.read_bytes()).hexdigest(), 'results':o['results']})
    result=latest(i)
    value={'case_id':i, 'original_input':CASES[i]['packet'], 'Jev_initial_observations':obs,
           'initial_observation_sha256':digest(obs), 'shared_context_ref':CONTEXT,
           'advisory_instruction':'Treat these initial observations as advice, choose a sufficient approach freely. Preserve sources, scope and permissions. Do not intentionally degrade the answer.'}
    # Preserve the original observation view across later correction/recheck.
    if result.get('route'):
        value['suggested_route']={k:result['route'][k] for k in ('per_issue','mandatory_reads','artifact_edges','unresolved')}
    p=ROOT/'comparison-inputs'/f'{i}.json'
    if p.exists(): return read_record(p)
    save(p,value);return value

def advisory(i, text, methods=()):
    common=view(i)
    save(ROOT/'comparison-outputs'/f'{i}-1.json', {'case_id':i,'mode':'1_advisory',
         'text':text,'methods_read_and_used':list(methods),'context_ref':CONTEXT,
         'initial_observation_sha256':common['initial_observation_sha256'],
         'origin':'current_conversation_agent_authored_now','usage':UNKNOWN,
         'independent_context':False,'author_knows_design_and_controls':True,
         'not_a_committed_execution_receipt':True})

def submit(i, text, *, methods=(), thesis=None, controller=None, discriminator=None, rebind=None):
    view(i)
    h=read_record(Path(latest(i)['host_request']));request=h['request']
    if h['role']=='execution':
        assert sorted(methods)==sorted(request['execute_methods'])
        reply={**h['reply_shape'],'performed_methods':list(methods),'text':text}
    else:
        assert h['role']=='correction'
        doc={'id':request['revision_document_id'],'revision':'current-agent-correction-v1','kind':'candidate','text':text}
        def ref(s):
            assert s and text.count(s)==1
            start=text.index(s);return rel.quote(doc,start,start+len(s))
        proposal=deepcopy(request['original_input']['proposal'])
        old=proposal['candidate']['ref']['document_id']
        def walk(x):
            if isinstance(x,dict):
                if set(x)==rel.REF_FIELDS and x['document_id']==old:
                    assert rebind is not None
                    return ref(rebind)
                return {k:walk(v) for k,v in x.items()}
            if isinstance(x,list):return [walk(v) for v in x]
            return x
        proposal={k:walk(v) for k,v in proposal.items() if k!='candidate'}
        proposal['candidate']={'ref':rel.quote(doc), 'thesis_refs':[ref(thesis)] if thesis else [],
                               'controller_refs':[ref(controller)] if controller else [],
                               'discriminator_refs':[ref(discriminator)] if discriminator else []}
        reply={'text':text,'version':doc['revision'],'receipt_ref':'current-agent:'+i+':correction-v1',
               'proposal':proposal,'usage':UNKNOWN}
    submission={'schema':'mindthus.current-host-response.v1','request_id':h['request_id'],
                'request_sha256':h['request_sha256'],'owner_ref':h['owner_ref'],
                'host_context_ref':CONTEXT,'elapsed_seconds':None,'reply':reply}
    path=submit_response(ROOT/i,REPO,submission)
    print(json.dumps({'case':i,'submitted_role':h['role'],'response':path},ensure_ascii=False))
    return submission
