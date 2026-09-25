"""Export this independent comparison, validating records and branch isolation."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
REPO=Path(__file__).resolve().parents[7];sys.path.insert(0,str(REPO))
from experiments.typed_decision.session import read_record

def sha(data):return hashlib.sha256(data).hexdigest()
def collect(root,dest):
    result=dict(schema='mindthus.independent-comparison-result.v1',root=str(root),results={},reviews={},
                codex_calls=[],jev_calls=[],files=[],excluded_files=[],isolation={})
    members=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if {'cli-home','workspaces'}&set(rel.parts) or not p.is_file():continue
        assert not p.is_symlink()
        data=p.read_bytes();row=dict(path=str(rel),sha256=sha(data),bytes=len(data))
        if p.name in ('events.jsonl','stderr.txt'):
            result['excluded_files'].append(dict(row,reason='retained locally; omit raw process streams and internal reasoning'));continue
        if p.suffix=='.json':
            value=json.loads(data)
            if isinstance(value,dict) and {'payload','sha256'}<=value.keys():read_record(p)
        members.append((str(rel),data));result['files'].append(row)
    for p in sorted((root/'results').glob('*.json')):
        x=read_record(p);reviewed=x.get('reviewed') or {};initial=x.get('initial') or {}
        result['results'][p.stem]=dict(consumption_complete=x.get('consumption_complete'),reason=x.get('reason'),
            pending=x.get('pending',{}),text=reviewed.get('text') or '\n\n'.join(v['text'] for v in x.get('outputs',{}).values()),
            initial_text=initial.get('text'),counts=x.get('counts'),usage=x.get('usage'))
    contexts={};initial_materials={}
    for p in sorted((root/'codex-calls').glob('*/intent.json')):
        intent=read_record(p);op=p.with_name('outcome.json');out=read_record(op) if op.exists() else dict(status='unresolved_intent')
        result['codex_calls'].append(dict(label=p.parent.name,intent=intent,outcome=out))
        group=intent['session_group']
        if group is not None and intent['prior_context'] is None:
            body=json.loads(p.with_name('prompt.txt').read_text().split('\n',1)[1]);q=body['request']
            source=q.get('original_input') or q['condition_packet']['original_input']
            case=group.split('-')[1];expected=read_record(root/'sources'/f'{case}.json')
            assert all(source[k]==expected[k] for k in ('documents','conversation','authority','intervention'))
            assert q.get('candidate') is None and not source.get('issues')
            methods=body.get('available_methods') or q['condition_packet']['loaded_methods']
            initial_materials[group]=sha(json.dumps(methods,sort_keys=True,ensure_ascii=False).encode())
        if group is not None and out.get('context_ref'):
            contexts.setdefault(group,set()).add(out['context_ref'])
    assert all(len(v)==1 for v in contexts.values()),'host context changed'
    flat=[next(iter(v)) for v in contexts.values()]
    assert len(flat)==len(set(flat)),'shared branch host context'
    result['isolation']=dict(host_contexts={k:next(iter(v)) for k,v in contexts.items()},
        distinct_host_contexts=len(flat),initial_method_hashes=initial_materials,
        same_initial_method_materials=len(set(initial_materials.values()))==1,no_common_candidate_files=not (root/'candidates').exists(),
        initially_empty_issue_projections=all(not read_record(p)['issues'] for p in (root/'sources').glob('*.json')))
    for p in sorted((root/'jev-calls').glob('*/*/intent.json')):
        row=read_record(p);op=p.with_name('response.json');response=read_record(op) if op.exists() else {}
        result['jev_calls'].append(dict(**row,elapsed_seconds=response.get('elapsed_seconds'),usage=response.get('validated_usage'),
                                       response_sha256=sha(op.read_bytes()) if op.exists() else None))
    for p in sorted((root/'reviews').glob('*-review-*.json')):
        key=read_record(p.with_name(p.name[0]+'-key-private.json'));x=read_record(p)['judgments']
        invalid = p.stem in ('E-review-1','E-review-2') and (root/'adapters/reviewer-material-recovery.json').exists()
        result['reviews'][p.stem]=dict(scores={key[k]:v for k,v in x['scores'].items()},substantive_differences=x['substantive_differences'],
            qualification='invalid_missing_actual_host_materials' if invalid else 'task_review_with_stated_evidence_boundary')
    result['accounting']=dict(jev_physical_requests=len(result['jev_calls']),codex_cli_invocations=len(result['codex_calls']),
        provisional_cost_usd=0,actual_cost_usd=None,parent_manual_submissions=0,
        timing_scope='route module; CLI includes startup/context/service overhead')
    dest.mkdir(parents=True,exist_ok=True);data=json.dumps(result,ensure_ascii=False,indent=2).encode()+b'\n'
    (dest/'RESULT.json').write_bytes(data)
    with tarfile.open(dest/'evidence.tar.gz','w:gz') as tf:
        for name,value in members+[('RESULT.json',data)]:
            info=tarfile.TarInfo(name);info.size=len(value);info.mode=0o444;info.mtime=0;tf.addfile(info,io.BytesIO(value))
    (dest/'evidence.sha256').write_text(sha((dest/'evidence.tar.gz').read_bytes())+'  evidence.tar.gz\n')
    print(json.dumps(dict(results=len(result['results']),reviews=len(result['reviews']),**result['accounting'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('destination',type=Path);a=p.parse_args();collect(a.root.resolve(),a.destination.resolve())
