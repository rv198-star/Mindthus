"""B1 mechanical regression probes; each case uses an isolated temporary Mission."""
from __future__ import annotations

import copy
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / 'skills/tplan/scripts')]
from tests.tplan.test_collaboration_runtime import CollaborationRuntimeTests
import collaboration as col
import tplan_runtime as rt

initial_and_repair = runpy.run_path(str(ROOT / 'docs/internal/tplan-collaboration/reviews/r3-audit/reproduce.py'))['initial_and_repair']


def observe(c, acs=('A1',), kind='acceptance_passed', task='T3'):
    rt.append_event(c.mission, {'event_type': kind, 'summary': 'R4 repair observation',
                               'task_id': task, 'payload': {'acceptance_ids': list(acs)}})


def delegated(c, verdict='PASS'):
    c.prepare(task_id='T3', delegation_id='D3', intent_id='I3', round_no=1)
    c.dispatch(intent_id='I3', execution_state='completed')
    f = c.feedback(source='r4-review', delegation_id='D3', artifact='h3',
                   source_role='C' if verdict else 'B', kind='review' if verdict else 'result')
    result, code = c.mutate('feedback.resolve', c.resolution(f['data']['feedback_id'],
        delegation='D3', artifact='h3', verdict=verdict, review_task='T3', focus='T3'))
    assert code == 0, result


def blocked(c):
    state = rt.read_mission(c.mission)
    events = rt.read_events(c.mission)
    proposed = copy.deepcopy(state)
    rt.find_task(proposed, 'T3')['status'] = 'completed'
    proposed['mission']['status'] = 'completed'
    before = (c.mission / 'mission.json').read_bytes()
    rejections = {}
    for action, fn in (
        ('task_complete', lambda: rt.transition_task_status(c.mission, 'T3', 'completed')),
        ('mission_close', lambda: rt.write_mission(c.mission, proposed)),
    ):
        try:
            fn()
        except rt.TplanError as exc:
            assert 'repair obligation' in str(exc), str(exc)
            rejections[action] = str(exc)
        else:
            raise AssertionError(action + ' unexpectedly succeeded')
    assert before == (c.mission / 'mission.json').read_bytes()
    findings = rt._mission_completion_findings(proposed, events)
    assert any('repair obligation' in item for item in findings), findings
    gaps = col.build_resume_view(proposed, events)['acceptance_gaps']
    assert any(gap.get('collaboration_gap') for gap in gaps), gaps
    return {'task_completion': 'rejected', 'mission_close': 'rejected',
            'mission_status': rt.read_mission(c.mission)['mission']['status'],
            'canonical_bytes_unchanged': True, 'rejections': rejections,
            'completion_findings': findings, 'resume_acceptance_gaps': gaps}


def completed(c):
    rt.transition_task_status(c.mission, 'T3', 'completed')
    state = rt.read_mission(c.mission)
    events = rt.read_events(c.mission)
    assert rt._mission_completion_findings(state, events) == []
    snapshot = c.snapshot()['data']
    assert snapshot['resume']['acceptance_gaps'] == []
    assert snapshot['resume'] == snapshot['survey']['collaboration_resume']
    state['mission']['status'] = 'completed'
    rt.write_mission(c.mission, state)
    return {'task_completion': 'completed', 'mission_status': rt.read_mission(c.mission)['mission']['status'],
            'completion_findings': [], 'resume_acceptance_gaps': [], 'snapshot_and_survey_agree': True}


def probe(c, name):
    acs = ['A1', 'A2'] if name in {'partial_coverage', 'valid_local_repair', 'valid_delegated_repair'} else ['A1']
    initial_and_repair(c, acs)
    if name == 'required_C_FAIL':
        delegated(c, 'FAIL')
    elif name == 'missing_required_review':
        delegated(c, None)
    elif name == 'valid_delegated_repair':
        delegated(c)
    elif name == 'retired_required_review':
        c.prepare(task_id='T3', delegation_id='D3', intent_id='I3', round_no=1)
        c.dispatch(intent_id='I3', execution_state='stopped', stop_requested=True)
    observe(c, acs=acs if name.startswith('valid_') else ['A1'], task='T1' if name == 'unrelated_task_PASS' else 'T3')
    if name == 'latest_FAIL':
        observe(c, kind='acceptance_failed')
        observe(c, task='T1')
    return completed(c) if name.startswith('valid_') else blocked(c)


def main():
    for name in ('required_C_FAIL', 'partial_coverage', 'missing_required_review', 'latest_FAIL',
                 'unrelated_task_PASS', 'retired_required_review', 'valid_local_repair', 'valid_delegated_repair'):
        fixture = CollaborationRuntimeTests()
        fixture.setUp()
        try:
            print(json.dumps({'case': name, 'evidence_class': 'mechanical_runtime_probe',
                              'result': probe(fixture, name)}, ensure_ascii=False), flush=True)
        finally:
            fixture.doCleanups()


if __name__ == '__main__':
    main()
