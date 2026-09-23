"""Successor experiment only. Reuses original entry and runner; no fabricated outputs."""
from pathlib import Path
from copy import deepcopy
import argparse
import importlib.util
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p/'experiments/typed_decision').is_dir())
BASE = HERE.parent/'paired-current-agent-v1'
spec = importlib.util.spec_from_file_location('six_scene_runner', BASE/'run.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
base.HERE=HERE; base.ROOT=Path('/srv/agentdock/tmp/mindthus-six-scenes-scoped-repair-r1')
base.FREEZE=HERE/'freeze.json'
base.AUTH='Owner approved root-cause fixes and successor verification; scoped-repair-r1/README.md; CPA not used'
base.CONTEXT='current-ChatGPT-conversation-six-scenes-repair-r1-shared-not-independent'
from experiments.typed_decision import route_control as rc
from experiments.typed_decision.contracts import digest, provider_configuration
from experiments.typed_decision.session import implementation_digest


def prepare():
    rows=base.specimens();bundle,qs,bindings=rc.load_policy(REPO);admissions={};identities={}
    for row in rows:
        i,p=row['id'],row['packet'];v,e,c=base.objects(p)
        compiled=rc.compile_route(p,REPO,bundle,qs,bindings)
        n=2 if i=='D1' else 1
        a={'schema':'mindthus.route-control-live.v1','mode':rc.MODE,'root':str(base.ROOT/i),
           'implementation':implementation_digest(),'source_bindings':bundle['sources'],
           'provider':provider_configuration(v),'packet_hashes':[digest(p)],'authorization_ref':base.AUTH,
           'ceilings':{'judgments':n,'corrections':0,'organize':0,'arbitrations':0,'executions':p['task_budget']['max_calls'],
                       'requests':n,'reserve_per_jev_usd':.02},
           'executor':e.configuration,'arbitrator':None,'corrector':None,'organizer':None}
        rc._admission(a,base.ROOT/i,p,v,bundle,{'executor':e,'arbitrator':None,'corrector':None,'organizer':None})
        admissions[i]=a;identities[i]={'input':digest(p),'initial_specs':digest([s.to_dict() for s in compiled.specs]),
                                      'context':digest(compiled.context)}
    f={'schema':'mindthus.scoped-repair-freeze.v1',
       'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
       'implementation':implementation_digest(),'case_ids':[r['id'] for r in rows],
       'files':{name:base.filesha(HERE/name) for name in ['README.md','run.py','cases.json','acceptance.json']},
       'parent_runner_sha256':base.filesha(BASE/'run.py'),'admissions':admissions,'identities':identities,
       'max_Jev_calls':4,'max_reserved_usd':.08,'new_CPA_calls':0,'independent_contexts':False,
       'post_artifact_request_rule':'Only accepted actual predecessor artifacts; consumer-only questions; same ledger and frozen ceiling',
       'prior_record_rewrite':False,'retries':0}
    base.save(base.FREEZE,f);print(json.dumps({'prepared':True,'max_Jev_calls':4,'source':f['source_commit']}))


def verify():
    f=base.verify()
    assert f['parent_runner_sha256']==base.filesha(BASE/'run.py')
    return f


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','verify','run']);p.add_argument('ids',nargs='*');a=p.parse_args()
    if a.action=='prepare':prepare()
    elif a.action=='verify':print(json.dumps({'verified':True,'freeze':digest(verify())}))
    else:
        verify()
        base.execute(a.ids or ['B1','C1','D1'])
