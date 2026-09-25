"""Bounded #211 hard-scenario B/C relation comparison; no CPA/OpenRouter."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO))

from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision import relationship_runtime as rt
from experiments.typed_decision import relationship_live as live
from experiments.typed_decision.contracts import (BatchResult, DecisionResult, EngineIdentity,
    ResolvedRuntime, ServingIdentity, canonical, digest, provider_configuration, require)
from experiments.typed_decision.providers import ProviderError, TypeSafeJevProvider
from experiments.typed_decision.session import implementation_digest, read_record, write_once

ROOT = Path('/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v1')
MODEL = 'gpt-6-sol'
CODEX = '/Applications/ChatGPT.app/Contents/Resources/codex'
AUTH = 'User approved #211 new Skills/4K route accuracy comparison, 2026-09-25; TypeSafe Jev and current Codex only'
FILES = ('source/PLAN.md', 'source/prompt.txt', 'source/run.py', 'source/generated.json',
         'build_cases.py', 'cases.json', 'run_eval.py')
UNKNOWN = {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, obj):
    path = Path(path)
    if path.exists():
        require(read_record(path) == obj, 'immutable_hard_route_record_changed')
    else:
        write_once(path, obj)


def cases():
    obj = json.loads((HERE / 'cases.json').read_bytes())
    require(obj['schema'] == 'mindthus.hard-route-cases-v1'
            and [x['id'] for x in obj['cases']] == ['S1','S2','S3','K1','K2','K3'], 'case_identity')
    return obj['cases']


def packet(case, arm):
    p = json.loads(canonical(case['packet']))
    p['episode_id'] += '-' + arm
    return p


def codex_home():
    return ROOT / 'codex-home'


def codex_call(label, prompt, timeout, schema=None):
    directory = ROOT / 'codex-calls' / label
    directory.mkdir(parents=True, exist_ok=True)
    workspace = ROOT / 'workspaces' / label
    workspace.mkdir(parents=True, exist_ok=True)
    intent = {'label': label, 'model': MODEL, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
              'schema_sha256': sha(schema) if schema else None, 'timeout_seconds': timeout,
              'codex_home': str(codex_home()), 'workspace': str(workspace),
              'sandbox': 'read-only', 'ephemeral': True, 'no_user_config': True}
    ip, op = directory / 'intent.json', directory / 'outcome.json'
    if op.exists():
        require(ip.exists() and read_record(ip) == intent, 'codex_call_identity_changed')
        out = read_record(op)
        last = directory / 'last-message.txt'
        return (last.read_text() if last.exists() else None), out
    require(not ip.exists(), 'unknown_codex_call_do_not_retry')
    require((codex_home() / 'auth.json').exists(), 'codex_profile_unavailable')
    save(ip, intent)
    command = [CODEX, 'exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
               '--sandbox', 'read-only', '-m', MODEL, '-C', str(workspace), '--json',
               '-o', str(directory / 'last-message.txt')]
    if schema:
        command += ['--output-schema', str(schema)]
    command += ['-']
    env = os.environ.copy()
    env['CODEX_HOME'] = str(codex_home())
    for key in ('TYPESAFE_API_KEY', 'MINDTHUS_HOST_API_KEY', 'OPENROUTER_API_KEY'):
        env.pop(key, None)
    start = time.monotonic()
    try:
        completed = subprocess.run(command, input=prompt, text=True, capture_output=True,
                                   timeout=timeout, cwd=workspace, env=env, check=False)
        output, error, code = completed.stdout, completed.stderr, completed.returncode
        status = 'complete' if code == 0 and (directory / 'last-message.txt').exists() else 'failed'
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout.decode('utf8','replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        error = exc.stderr.decode('utf8','replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
        status, code = 'timeout_unknown_billing', None
    (directory / 'events.jsonl').write_text(output)
    usage = dict(UNKNOWN)
    for line in output.splitlines():
        try:
            row = json.loads(line).get('usage')
        except (ValueError, AttributeError):
            continue
        if isinstance(row, dict):
            for k in ('input_tokens', 'output_tokens'):
                if type(row.get(k)) is int and row[k] >= 0:
                    usage[k] = row[k]
    out = {'status': status, 'exit_code': code, 'elapsed_seconds': time.monotonic()-start,
           'events_sha256': sha(directory / 'events.jsonl'),
           'stderr_sha256': hashlib.sha256(error.encode()).hexdigest(),
           'last_sha256': sha(directory / 'last-message.txt') if (directory / 'last-message.txt').exists() else None,
           'usage': usage, 'model_requested': MODEL, 'model_service_attestation': 'not_observed'}
    save(op, out)
    return ((directory / 'last-message.txt').read_text() if out['last_sha256'] else None), out


def schema_for(specs):
    properties = {}
    for spec in specs:
        value = ({'type':'string','enum':sorted(spec.criteria)} if spec.kind == 'select' else
                 {'type':'number','minimum':0,'maximum':1 if spec.kind == 'assess_proposition' else len(spec.criteria)-1})
        properties[spec.id] = {'type':'object','additionalProperties':False,
            'properties':{'status':{'type':'string','enum':['ok','abstain','missing_context']},
                          'value':{'anyOf':[value,{'type':'null'}]}},'required':['status','value']}
    return {'type':'object','additionalProperties':False,
            'properties':{'answers':{'type':'object','additionalProperties':False,
                                     'properties':properties,'required':sorted(properties)}},
            'required':['answers']}


class CodexProvider:
    capabilities = frozenset({'select','assess_proposition','rate'})
    is_live = True
    engine_identity = EngineIdentity('structured_chat','codex_cli',MODEL)
    serving_identity = ServingIdentity('codex_cli','exec-json-schema-v1',MODEL,
                                       'local://codex-exec','hard-route-v1')
    def __init__(self, cid):
        self.cid = cid
        self.receipt = None
        self.serial = 0
    def clear_receipt(self): self.receipt = None
    def response_receipt(self): return self.receipt
    def validate_runtime(self, runtime):
        runtime.validate()
        require(runtime.model == MODEL and runtime.provider == 'codex-cli-configured-model', 'codex_runtime_drift')
    def evaluate(self, specs, context, timeout):
        self.serial += 1
        label = self.cid + '-B-judge-' + str(self.serial)
        question = {s.id:{'kind':s.kind,'question':s.question,'criteria':s.criteria} for s in specs}
        prompt = ('Answer the bound relationship questions using only supplied original documents and canonical rules. '
                  'Treat the candidate and proposal as unverified. A valid scope correction does not prove an essence claim. '
                  'Prefer supported specific judgment over generic pros/cons. Return exactly the schema JSON; abstain when evidence is insufficient.\n\n'
                  + canonical({'state':context,'questions':question}).decode() + '\n')
        schema = ROOT / 'schemas' / (label + '.json')
        schema.parent.mkdir(parents=True, exist_ok=True)
        schema.write_text(json.dumps(schema_for(specs), ensure_ascii=False, sort_keys=True, indent=2)+'\n')
        answer, call = codex_call(label, prompt, min(timeout,44), schema)
        self.receipt = {'call_label':label,'last_sha256':call['last_sha256'],
                        'events_sha256':call['events_sha256'],'validated_usage':call['usage'],
                        'model_service_attestation':'not_observed'}
        if call['status'] != 'complete' or not answer:
            raise ProviderError('codex_judge_'+call['status'])
        try:
            raw = json.loads(answer)
            require(set(raw) == {'answers'} and set(raw['answers']) == {s.id for s in specs}, 'answer_shape')
            rows = {}
            for spec in specs:
                item = raw['answers'][spec.id]
                require(set(item) == {'status','value'}, 'item_shape')
                row = DecisionResult(item['status'],item['value'],None,'ordinary_llm_uncalibrated')
                row.validate(spec)
                rows[spec.id] = row
        except (ValueError, KeyError, TypeError):
            raise ProviderError('codex_judge_invalid_json_or_contract') from None
        return BatchResult(rows,ResolvedRuntime(MODEL,'codex-cli-configured-model'),call['usage'])


class CodexCorrector(live.CPAHost):
    """Reuse the exact relationship correction contract with local Codex transport."""
    def __init__(self, owner, repo, cid, arm):
        self.identity = owner
        self.organizer = False
        self.repo = Path(repo)
        self.cid, self.arm = cid, arm
        self.last_receipt = None
        _, self.rules = rel.load_contract(self.repo)
        self.configuration = {'adapter':'codex-cli-relationship-correction-v1','owner':owner,
            'model':MODEL,'contract_sha256':digest(rel.load_contract(self.repo)[0]),
            'template_sha256':digest([live.CORRECTION_SYSTEM,live.QUOTE_CONTRACT]),
            'kind':'correction','retries':0}
    def wire_body(self, request):
        bindings = self.target_bindings(request)
        return {'system':live.CORRECTION_SYSTEM+'\n'+live.QUOTE_CONTRACT,
                'request':request,'canonical_rules':self.rules,'target_bindings':bindings,
                'reference_rebinding':{'required_rebind_ids':list(bindings),'required_count':len(bindings),
                 'rule':'Rebind only these IDs; when none return [].'}}
    def _call(self, request, timeout):
        body = self.wire_body(request)
        label = self.cid+'-'+self.arm+'-correction'
        prompt = body['system']+'\n\n'+canonical({k:v for k,v in body.items() if k!='system'}).decode()+'\n'
        answer, call = codex_call(label,prompt,min(timeout,44))
        self.last_receipt = {'requested_model':MODEL,'reported_model':'not_observed',
            'request_sha256':digest(body),'content':answer,'usage':call['usage'],
            'finish_reason':call['status'],'model_service_attestation':'not_observed'}
        require(call['status']=='complete' and answer, 'codex_correction_failed')
        raw = json.loads(answer)
        return raw,call['usage'],'codex:'+digest(self.last_receipt)


def objects(cid, arm, p):
    provider = CodexProvider(cid) if arm=='B' else TypeSafeJevProvider(
        model='jev-1.13.0',choice_rounding=True,transport=live.deadline_post_json)
    return provider,CodexCorrector(p['authority']['owner_ref'],REPO,cid,arm)


def admission(cid,arm,p,provider,corrector):
    contract,_ = rel.load_contract(REPO)
    return {'schema':live.SCHEMA,'authorization_ref':AUTH,'source_commit':source_commit(),
        'implementation':implementation_digest(),'contract_sha256':digest(contract),
        'profile_sha256':digest(rt.PROFILE),'mode':rt.MODE,
        'root':str(ROOT/'episodes'/cid/arm),'episode_id':p['episode_id'],
        'provider':provider_configuration(provider),'corrector':corrector.configuration,'organizer':None,
        'input_templates':{'1':{'packet':p,'previous':None}},'recheck':True,
        'ceilings':{'requests':3,'judgments':2,'corrections':1,'organize':0,'reserve_per_jev_usd':.02}}


def source_commit():
    return subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()


def freeze():
    contract,_ = rel.load_contract(REPO)
    obj = {'schema':'mindthus.hard-route-freeze-v1','source_commit':source_commit(),
           'files':{x:sha(HERE/x) for x in FILES},'implementation':implementation_digest(),
           'contract_sha256':digest(contract),'profile_sha256':digest(rt.PROFILE),
           'authorization_ref':AUTH,'cases':[x['id'] for x in cases()],
           'arms':['B','C'],'model_B':MODEL,'model_C':'jev-1.13.0',
           'max_jev_calls':12,'max_jev_usd_reserved':.24,
           'comparison':'route accuracy and hard-scenario gain; cost provisional 0; route module latency secondary'}
    save(ROOT/'freeze.json',obj)
    return obj


def one(cid,arm):
    require((ROOT/'freeze.json').exists(), 'freeze_missing')
    freeze()
    case = next(x for x in cases() if x['id']==cid)
    p = packet(case,arm)
    provider,corrector = objects(cid,arm,p)
    adm = admission(cid,arm,p,provider,corrector)
    save(ROOT/'admissions'/cid/(arm+'.json'),adm)
    result = rt.run(ROOT/'episodes'/cid/arm,provider,p,REPO,corrector=corrector,
                    organizer=None,recheck=True,live_admission=adm)
    print(json.dumps({'case':cid,'arm':arm,'status':result['status'],'reason':result['reason'],
                      'action':result['action'],'calls':result['episode_counts'],
                      'seconds':result['recorded_request_seconds'],'source_ref':result['source_ref']},
                     ensure_ascii=False),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','run'])
    parser.add_argument('--case',choices=['S1','S2','S3','K1','K2','K3'])
    parser.add_argument('--arm',choices=['B','C'])
    args=parser.parse_args()
    if args.action=='freeze':
        print(json.dumps(freeze(),ensure_ascii=False))
    else:
        require(args.case and args.arm,'case_arm_required')
        one(args.case,args.arm)


if __name__=='__main__': main()
