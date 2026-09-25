"""Bounded B-arm timeout recovery; original episodes and Jev results stay frozen."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_eval as base
from experiments.typed_decision import relationship_assessment as rel
from experiments.typed_decision import relationship_runtime as rt
from experiments.typed_decision.contracts import DecisionResult, canonical, digest, require
from experiments.typed_decision.session import read_record

ROOT=base.ROOT/'timeout-recovery-v1'
CASES=('S1','K1')
TIMEOUT=100


def original_call(cid):
    return base.ROOT/'codex-calls'/(cid+'-B-judge-1')


def completed_event(path):
    events=[json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    return any(x.get('type')=='turn.completed' for x in events)


def make_prompt(compiled):
    questions={s.id:{'kind':s.kind,'question':s.question,'criteria':s.criteria} for s in compiled.specs}
    return ('Answer the bound relationship questions using only supplied original documents and canonical rules. '
            'Treat the candidate and proposal as unverified. A valid scope correction does not prove an essence claim. '
            'Prefer supported specific judgment over generic pros/cons. Return exactly the schema JSON; abstain when evidence is insufficient.\n\n'
            +canonical({'state':compiled.context,'questions':questions}).decode()+'\n')


def case(cid):
    return next(x for x in base.cases() if x['id']==cid)


def compiled(cid):
    return rel.compile_packet(base.packet(case(cid),'B'),base.REPO)


def freeze():
    require(read_record(base.ROOT/'freeze.json')['source_commit']=='0d97f015708c9eea4e5651e42918f4a678a0394a',
            'parent_freeze_changed')
    originals={}
    for cid in CASES:
        call=original_call(cid)
        intent=read_record(call/'intent.json')
        outcome=read_record(call/'outcome.json')
        require(outcome['status']=='timeout_unknown_billing' and intent['timeout_seconds']==44,
                'not_original_timeout')
        prompt=make_prompt(compiled(cid))
        require(hashlib.sha256(prompt.encode()).hexdigest()==intent['prompt_sha256'],
                'original_question_changed')
        require(base.sha(base.ROOT/'schemas'/(cid+'-B-judge-1.json'))==intent['schema_sha256'],
                'original_schema_changed')
        originals[cid]={'intent_sha256':base.sha(call/'intent.json'),
                        'outcome_sha256':base.sha(call/'outcome.json'),
                        'events_sha256':outcome['events_sha256'],
                        'last_sha256':outcome['last_sha256'],
                        'turn_completed':completed_event(call/'events.jsonl'),
                        'prompt_sha256':intent['prompt_sha256']}
    require(originals['S1']['turn_completed'] and originals['S1']['last_sha256']
            and not originals['K1']['turn_completed'] and originals['K1']['last_sha256'] is None,
            'timeout_evidence_changed')
    obj={'schema':'mindthus.hard-route-timeout-recovery-v1','parent_freeze_sha256':base.sha(base.ROOT/'freeze.json'),
         'source_commit':base.source_commit(),'script_sha256':base.sha(Path(__file__)),
         'cases':list(CASES),'originals':originals,'model':base.MODEL,
         'S1_initial':'validate_and_consume_original_completed_output',
         'K1_initial':'one_new_identical_prompt','route_timeout_seconds':TIMEOUT,
         'max_new_route_calls':3,'max_new_corrections':2,'no_jev_calls':True,
         'comparison':'standalone source-bound consumption; original Episode statuses preserved'}
    base.save(ROOT/'freeze.json',obj)


def answer_to_result(compiled, answer):
    raw=json.loads(answer)
    require(isinstance(raw,dict) and set(raw)=={'answers'} and set(raw['answers'])=={s.id for s in compiled.specs},
            'route_answer_shape')
    answers={}
    for spec in compiled.specs:
        item=raw['answers'][spec.id]
        require(isinstance(item,dict) and set(item)=={'status','value'},'route_item_shape')
        row=DecisionResult(item['status'],item['value'],None,'ordinary_llm_uncalibrated')
        row.validate(spec)
        answers[spec.id]=asdict(row)
    return rel.consume(compiled,{'identity':compiled.identity,'results':answers},base.REPO)


def call_judge(cid,step,compiled):
    label=cid+'-B-timeout-recovery-v1-'+step
    schema=ROOT/'schemas'/(label+'.json')
    schema.parent.mkdir(parents=True,exist_ok=True)
    value=json.dumps(base.schema_for(compiled.specs),ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    require(not schema.exists() or schema.read_text()==value,'recovery_schema_changed')
    if not schema.exists(): schema.write_text(value)
    answer,out=base.codex_call(label,make_prompt(compiled),TIMEOUT,schema)
    require(out['status']=='complete' and answer,'recovery_route_failed')
    return answer,{'label':label,'outcome_sha256':base.sha(base.ROOT/'codex-calls'/label/'outcome.json'),
                   'elapsed_seconds':out['elapsed_seconds']}


def execute(cid):
    require(cid in CASES,'unadmitted_case')
    freeze()
    p=base.packet(case(cid),'B')
    first=rel.compile_packet(p,base.REPO)
    if cid=='S1':
        call=original_call(cid)
        require(completed_event(call/'events.jsonl'),'original_turn_not_complete')
        answer=(call/'last-message.txt').read_text()
        first_call={'source':'recovered_original_completed_output','outcome_sha256':base.sha(call/'outcome.json')}
    else:
        answer,first_call=call_judge(cid,'initial',first)
        first_call['source']='new_identical_prompt'
    initial=answer_to_result(first,answer)
    final=initial
    correction=None
    recheck=None
    if initial['action']=='request_correction':
        request=rt.correction_request(p,{'result':initial})
        corrector=base.CodexCorrector(p['authority']['owner_ref'],base.REPO,cid+'-timeout-recovery-v1','B')
        reply=corrector.correct(request,44)
        revised=rt.revision_packet(request,reply,base.REPO)
        correction={'receipt_ref':reply['receipt_ref'],'revised_text':reply['text'],
                    'reply_sha256':digest(reply)}
        second=rel.compile_packet(revised,base.REPO)
        recheck_answer,recheck=call_judge(cid,'recheck',second)
        final=answer_to_result(second,recheck_answer)
    result={'schema':'mindthus.hard-route-timeout-recovery-result-v1','case':cid,
            'original_packet_sha256':digest(p),'first_call':first_call,
            'initial_action':initial['action'],'initial_reason':initial.get('reason'),
            'initial_matrix':initial['matrix'],'correction':correction,'recheck_call':recheck,
            'final_action':final['action'],'final_reason':final.get('reason'),
            'final_matrix':final['matrix'],'host_consumption':'continue_original' if final['action']=='continue_original'
             else 'return_original_owner','evidence_limit':'standalone recovery; original Episode unchanged'}
    base.save(ROOT/'results'/(cid+'.json'),result)
    print(json.dumps({'case':cid,'initial':initial['action'],'final':final['action'],
                      'corrected':correction is not None,'recheck':recheck is not None,
                      'source_ref':str(ROOT/'results'/(cid+'.json'))},ensure_ascii=False),flush=True)


if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='freeze': freeze()
    elif len(sys.argv)==2: execute(sys.argv[1])
    else: raise SystemExit('usage: retry_comparison.py freeze|S1|K1')
