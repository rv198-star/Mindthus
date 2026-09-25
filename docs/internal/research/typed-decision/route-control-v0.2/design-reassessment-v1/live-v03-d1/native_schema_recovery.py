"""Declared formatting-only adapter supplement; preserves all original requests/results."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

SPEC=importlib.util.spec_from_file_location('d_frozen_runner',Path(__file__).with_name('run.py'))
b=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(b)

def schema(q):
    result=original_schema(q)
    if q.get('schema')=='mindthus.route-v03-native-request.v1':
        result['properties']['performed_methods']=b.arr(b.enum(q['condition_packet']['loaded_methods']))
    return result
original_schema=b.schema_for

def execute(root,case,condition):
    b.verify(root)
    b.save(root/'adapters/native-schema-r1.json',dict(source_sha256=b.sha(__file__),
        parent_runner_sha256=b.sha(Path(__file__).with_name('run.py')),
        reason='Constrain method IDs to the existing contract; no task or answer policy change'))
    b.schema_for=schema
    label='common-'+case+'-'+condition;ep=root/'episodes'/label
    pending=list(ep.glob('turns/*/inputs/*/steps/correction/handoff.json'))
    call_dir=root/'codex-calls'/(label+'-correction')
    if pending and (call_dir/'outcome.json').exists() and not pending[0].with_name('host-response.json').exists():
        h=b.read_record(pending[0]);q=h['request'];raw=json.loads((call_dir/'answer.json').read_text())
        old=b.read_record(call_dir/'outcome.json')
        # Only the already-observed method-label contract error is eligible.
        b.require(old['status']=='complete' and set(raw['performed_methods'])-set(q['condition_packet']['loaded_methods']),
                  'not_the_known_method_label_error')
        used=list((root/'codex-calls').glob('*-format-r1/intent.json'))
        retry=root/'codex-calls'/(label+'-format-r1')
        b.require((retry/'intent.json').exists() or len(used)<2,'D_codex_technical_budget')
        fixed,receipt=b.call(root,label+'-format-r1',dict(original_request=q,previous_reply=raw,
            instruction='只修复返回格式：text 必须逐字保留。performed_methods 只能列本次实际采用的 canonical 方法ID；若只做直接复核则为[]。其他判断和引用保持原样，不得再做实质修订。'),
            schema(q),session_group=label,timeout=max(1,h['allowance_seconds']-old['elapsed_seconds']))
        b.require(all(fixed[k]==raw[k] for k in raw if k!='performed_methods'),'format_retry_changed_decision')
        usage={k:old['usage'][k]+receipt['usage'][k] if old['usage'][k] is not None and receipt['usage'][k] is not None else None
               for k in old['usage']}
        b.submit_response(ep,b.REPO,dict(schema='mindthus.current-host-response.v1',request_id=h['request_id'],
            request_sha256=h['request_sha256'],owner_ref=h['owner_ref'],host_context_ref=receipt['context_ref'],
            elapsed_seconds=old['elapsed_seconds']+receipt['elapsed_seconds'],reply=b.normalize(fixed,q,usage)))
    return b.run(root,case,condition)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--case',choices=['E','F'],required=True)
    p.add_argument('--condition',choices=['pure_codex','questions_only'],required=True);a=p.parse_args()
    r=execute(a.root.resolve(),a.case,a.condition)
    print(json.dumps({k:r.get(k) for k in ('reason','consumption_complete')},ensure_ascii=False))
