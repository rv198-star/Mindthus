"""Offline attribution of frozen C01 observations. No inference or label changes."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[5]
SOURCE = REPO / 'docs/internal/research/typed-decision/language-diagnostic'
STAGES = [
    ('native_failed', 'observation.json', 'raw_summary', 'raw_root'),
    ('backup_failed', 'backup-observation.json', 'raw_summary', 'root'),
    ('native_strict', 'proxy-observation.json', 'original_summary', 'trial_root'),
    ('native_rounding', 'rounding-observation.json', 'original_summary', 'trial_root'),
]
NODES = ('entry_mode', 'unresolved_obligation', 'owner', 'applicable')


def aggregate(rows):
    valid = [r for r in rows if r['state'] == 'semantic_observed']
    node_counts = {}
    for node in NODES:
        answers = [r[node] for r in valid if r[node] != 'not_run']
        node_counts[node] = {'observed': len(answers), 'not_run': len(valid)-len(answers),
                             'values': dict(Counter(answers))}
    owner = [r for r in valid if r['owner_match'] is not None]
    return {
        'states': dict(Counter(r['state'] for r in rows)),
        'semantic_views': len(valid),
        'joint_matches': sum(r['joint_match'] for r in valid),
        'entry_matches': sum(r['entry_match'] for r in valid),
        'final_route_matches': sum(r['route_match'] for r in valid),
        'first_divergence': dict(Counter(r['first_divergence'] for r in valid)),
        'nodes': node_counts,
        'owner_observed_matches': sum(r['owner_match'] for r in owner),
        'owner_observed_scored': len(owner),
        'required_implicit_owner_views': sum(r['required_implicit_owner'] for r in valid),
        'explicit_bound_views': sum(r['owner_source'] == 'explicit_binding' for r in valid),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--verify-original', action='store_true')
    args = parser.parse_args()
    if args.verify_original:
        sys.path.insert(0, str(REPO))
        from experiments.typed_decision.session import read_record
    cases = json.loads((SOURCE/'cases.json').read_text())['cases']
    observations = {}
    inputs = [SOURCE/'cases.json', Path(__file__).resolve()]
    verified_summaries = verified_outcomes = 0
    for stage, filename, summary_key, root_key in STAGES:
        path = SOURCE/filename
        inputs.append(path)
        doc = json.loads(path.read_text())
        summary = doc[summary_key]
        if args.verify_original:
            root = Path(doc[root_key])
            assert read_record(root/'summary.json') == summary, filename
            verified_summaries += 1
        for row in summary['rows']:
            key = (row['case_id'], row['arm'])
            assert key not in observations, key
            if args.verify_original:
                for call in row['nodes']:
                    raw = read_record(root/row['arm']/'calls'/call['call_key']/'outcome.json')
                    assert raw['results'] == call['results'], key
                    verified_outcomes += 1
            observations[key] = (stage, row)
    rows = []
    for case in cases:
        for arm in ('source', 'english'):
            stage, raw = observations.get((case['id'], arm), ('unrun', None))
            nodes = {} if raw is None else {k: v for c in raw['nodes'] for k, v in c['results'].items()}
            state = ('unrun' if raw is None else 'mechanical_d0' if raw['mechanical_d0'] else
                     'technical_failure' if any(v['status'] != 'ok' for v in nodes.values()) else
                     'semantic_observed')
            accepted = case['accepted']
            valid = state == 'semantic_observed'
            get = lambda n: ('not_run' if n not in nodes else nodes[n]['value']
                             if nodes[n]['status'] == 'ok' else 'error:'+nodes[n]['status'])
            entry_match = any(get('entry_mode') == a['entry_mode'] for a in accepted) if valid else None
            owner_match = (any(get('owner') == a['owner'] for a in accepted)
                           if valid and 'owner' in nodes else None)
            route_match = raw['score']['fields']['route'] if valid else None
            joint = raw['score']['joint'] if valid else None
            divergence = ('not_scored' if not valid else 'none' if joint else
                          'J1_entry' if not entry_match else
                          'J2_block' if raw['result']['reason'] == 'unresolved_or_conflicting_judgment' else
                          'J4_owner' if owner_match is False else 'other_unattributed')
            explicit = case[arm].get('explicit_method')
            rows.append({
                'case_id': case['id'], 'arm': arm, 'stage': stage, 'family': case['family'],
                'state': state, **{n: get(n) for n in NODES},
                'explicit_method': explicit,
                'owner_source': ('model_choice' if 'owner' in nodes else
                                 'explicit_binding' if explicit and 'applicable' in nodes else 'not_reached'),
                'required_implicit_owner': not explicit and all(a['owner'] is not None for a in accepted),
                'entry_match': entry_match, 'owner_match': owner_match, 'route_match': route_match,
                'joint_match': joint, 'first_divergence': divergence,
                'final_route': raw['result']['route'] if raw else None,
                'reason': raw['result']['reason'] if raw else None,
                'call_keys': raw['call_keys'] if raw else [],
            })
    assert len(rows) == 64
    output = {
        'scope': 'posthoc descriptive attribution; stages and bilingual views are not independent trials',
        'attribution': 'first observed divergence from frozen accepted paths, not proven causal mechanism',
        'label_limits': 'No frozen separate J2/J5 gold labels; report observations, not node accuracy.',
        'input_sha256': {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
        'original_verification': {'enabled': args.verify_original,
                                  'summaries': verified_summaries, 'outcomes': verified_outcomes},
        'all': aggregate(rows),
        'by_arm': {arm: aggregate([r for r in rows if r['arm'] == arm]) for arm in ('source', 'english')},
        'by_stage': {stage: aggregate([r for r in rows if r['stage'] == stage]) for stage, *_ in STAGES},
        'rows': rows,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'observations.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n')
    with (args.output_dir/'rows.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows({**r, 'call_keys': json.dumps(r['call_keys'])} for r in rows)
    print(json.dumps({k: output[k] for k in ('original_verification', 'all', 'by_arm')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
