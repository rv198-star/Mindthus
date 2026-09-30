"""Export existing evidence and blinded products; never dispatch or grade a model."""
import hashlib
import json
import random
import tarfile
from pathlib import Path
from experiments.grounded_judgment import runtime as rt
from experiments.typed_decision.contracts import digest

HERE=Path(__file__).resolve().parent
BATCH=Path('/Users/william/.codex/tmp/gj-extended-v1-run')


def main():
    summary=json.loads((HERE/'summary.json').read_text())
    inputs=rt.read(BATCH/'inputs.json');norms=rt.read(HERE/'norms.evaluation-only.json')
    calls=[]
    for directory in sorted((BATCH/'calls').iterdir()):
        files={p.stem:rt.read(p) for p in sorted(directory.glob('*.json'))}
        calls.append({'local_call':directory.name,**files})
    with open(HERE/'calls.jsonl','w') as f:
        for record in calls:f.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
    index=[]
    with tarfile.open(HERE/'business-evidence.tar.gz','w:gz') as archive:
        for path in sorted(BATCH.rglob('*.json')):
            relative=str(path.relative_to(BATCH));archive.add(path,arcname=relative,recursive=False)
            index.append({'path':relative,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    (HERE/'evidence-index.json').write_text(json.dumps(index,indent=2)+'\n')
    for row in summary['paths']:
        if row['calls']==0:row['status']='not_sent'
    rows={p['path']:p for p in summary['paths']}
    directory=HERE/'blind-review';directory.mkdir(exist_ok=True)
    mapping={};rng=random.Random(20260930)
    for case in inputs:
        arms=list('ABC');rng.shuffle(arms)
        mapping[case]={f'X{i+1}':arm for i,arm in enumerate(arms)}
        packet={'case':case,'source_documents':inputs[case]['documents'],'preregistered_norms':norms[case],
                'review_scope':'Compare first/final core judgments, not style or number of methods; grouping concealed, not independently blind execution.'}
        packet['products']={label:{'draft':rows[case+'-'+arm]['draft'],'final':rows[case+'-'+arm]['final'],
                                  'delivery_status':rows[case+'-'+arm]['status']}
                            for label,arm in mapping[case].items()}
        (directory/(case+'.json')).write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
    (HERE/'private-review-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
    # Diagnostics stay separate from answer text; returned read requests are not drafts.
    for row in summary['paths']:
        related=[c for c in calls if c['binding']['call_key'].rsplit(':',1)[0]==row['path']]
        events=[rt.read(p)['body'] for p in sorted((BATCH/'runs'/row['path']/'events').glob('*.json'))]
        row['local_failures']=[e['payload'] for e in events if e['kind']=='format_failure']
        if row['calls']==0:row['status']='not_sent'
        row['skipped_phases']=[e['payload'] for e in events if e['kind']=='skipped']
        row['atom_states']={state:sum(a['semantic_state']==state for a in row['atoms'].values())
                            for state in ('support','deny','unresolved','unlocated','invalid')}
        row['call_ids']=[c['local_call'] for c in related]
        row['raw_returns']=[{'local_call':c['local_call'],'phase':c['request']['phase'],
            'transport_status':c.get('terminal',{}).get('status'),
            'import_error':c.get('import',{}).get('error'),
            'response':c.get('envelope',{}).get('response')} for c in related]
        row['source_groups']=list(dict.fromkeys('read_contract_successor' if c['binding'].get('technical_successor_sha256') else 'initial' for c in related))
        (HERE/'answers'/(row['path']+'.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
        text='# '+row['path']+'\n\n状态：'+row['status']+'\n\n## 首稿\n\n'+(row['draft'] or '无')
        text+='\n\n## 检查\n\n```json\n'+json.dumps(row['check'],ensure_ascii=False,indent=2)+'\n```'
        text+='\n\n## 最终稿\n\n'+(row['final'] or '无')+'\n'
        if row['status']!='delivered':
            text+='\n## 原始返回与失败（不是答案）\n\n```json\n'+json.dumps({'local_failures':row['local_failures'],'returns':row['raw_returns']},ensure_ascii=False,indent=2)+'\n```\n'
        (HERE/'answers'/(row['path']+'.md')).write_text(text)
    summary['transport_source_groups']={}
    for label in ('initial','read_contract_successor'):
        group=[c for c in calls if ('read_contract_successor' if c['binding'].get('technical_successor_sha256') else 'initial')==label]
        summary['transport_source_groups'][label]={'logical_calls':len(group),
          'session_seconds':sum(c.get('terminal',{}).get('session_seconds') or 0 for c in group),
          'active_wait_seconds':sum((c.get('envelope',{}).get('measurement') or {}).get('active_wait_seconds') or 0 for c in group)}
    if (BATCH/'read-contract-successor.json').exists():
        summary['technical_successor']={'source_commit':rt.read(BATCH/'read-contract-successor.json')['source_commit'],
            'sha256':digest(rt.read(BATCH/'read-contract-successor.json')),'retry':False}
    summary['local_format_failure_paths']=sum(r['status']=='format_failure' for r in summary['paths'])
    summary['delivered_paths']=sum(r['status']=='delivered' for r in summary['paths'])
    summary['arm_totals']={a:{'logical_calls':sum(r['calls'] for r in summary['paths'] if r['path'].endswith('-'+a)),
          'host_calls':sum(r['host_calls'] for r in summary['paths'] if r['path'].endswith('-'+a)),
          'jev_calls':sum(r['jev_calls'] for r in summary['paths'] if r['path'].endswith('-'+a)),
          'session_seconds':sum(r['session_seconds'] for r in summary['paths'] if r['path'].endswith('-'+a)),
          'active_wait_seconds':sum(r['active_wait_seconds'] for r in summary['paths'] if r['path'].endswith('-'+a))} for a in 'ABC'}
    known=[p for p in calls if 'terminal' in p]
    if known:
        starts=[p['intent']['started_at_epoch'] for p in known]
        ends=[p['terminal']['ended_at_epoch'] for p in known]
        summary['first_send_to_last_terminal_seconds']=max(ends)-min(starts)
    summary['returned_calls']=sum(p.get('terminal',{}).get('status')=='returned' for p in calls)
    summary['unknown_calls']=sum(p.get('terminal',{}).get('status')=='unknown' for p in calls)
    summary['failed_calls']=sum(p.get('terminal',{}).get('status')=='failed' for p in calls)
    summary['safety_refusal_calls']=sum(p.get('terminal',{}).get('status')=='safety_refusal' for p in calls)
    summary['raw_usage_by_provider']={}
    for role in ('host','jev'):
        usages=[c.get('envelope',{}).get('measurement',{}).get('usage') for c in calls if c['request']['role']==role]
        fields=set().union(*(u.keys() for u in usages if isinstance(u,dict)))
        summary['raw_usage_by_provider'][role]={'calls_with_usage':sum(isinstance(u,dict) for u in usages),
          'calls_missing_usage':sum(not isinstance(u,dict) for u in usages),
          'known_numeric_fields_sum':{k:sum(u[k] for u in usages if isinstance(u,dict) and type(u.get(k)) in (int,float)) for k in fields},
          'raw_usage_in_calls_jsonl':True,'not_cross_provider_cost':True}
    observations=[c.get('terminal',{}).get('transport_observation') for c in calls if c['request']['role']=='host']
    summary['host_transport_observations']={'cli_starts':sum((c.get('envelope',{}).get('measurement',{}).get('cli_starts') or 0) for c in calls),
          'outer_driver_retries':0,'exact_underlying_requests':None,
          'generation_attempt_count':None,
          'observed_log_counts':{k:sum((o or {}).get(k) or 0 for o in observations) for k in ('auth_or_401_log_count','fallback_or_prewarm_log_count','reconnect_notice_count','sampling_retry_log_count')}}
    summary['observed_recovery_stops']=sum(bool((p.get('terminal',{}).get('transport_observation') or {}).get('stop_subsequent_dispatch')) for p in calls)
    summary['execution_source']=rt.read(BATCH/'execution-source.json')
    summary['full_path_denominator']=24;summary['atomic_denominator_per_arm']=8*13
    summary['reference_scope']='Raw records are immutable; no hash recomputation claimed as independent audit.'
    (HERE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('logical_calls','host_calls','jev_calls','returned_calls','unknown_calls','failed_calls')},ensure_ascii=False))


if __name__=='__main__':main()
