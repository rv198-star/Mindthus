"""Explicit replacement close contract; discoverable by unittest and CI."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'skills' / 'tplan' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from tplan_runtime import _mission_completion_findings, validate_hook_output


def mission():
    return {'schema_version': 'tplan.v0.1', 'mission': {
        'id': 'mission-supersession-fixture', 'status': 'active',
        'acceptance_evidence': [{'id': 'AC_GOAL', 'description': 'Verified outcome'}]},
        'tasks': [dict(id='T0', role='success-critical', status='completed', acceptance_evidence=['AC_GOAL']),
                  dict(id='T1', role='success-critical', status='superseded', acceptance_evidence=['AC_GOAL']),
                  dict(id='T2', role='success-critical', status='completed', acceptance_evidence=['AC_GOAL'])]}


def evidence(task='T2', kind='acceptance_passed', event_id='E1'):
    return dict(id=event_id, timestamp='2026-10-16T00:00:00+00:00', event_type=kind,
                summary='Verified actual result', task_id=task, payload={'acceptance_ids': ['AC_GOAL']})


def decision(pairs=None):
    out = dict(recommendation='close', rationale='T2 fulfills the retired T1 obligation after review',
               confidence=95, evidence_links=['E1'], requires_human=False,
               mission_alignment='All required outcomes are independently verified',
               proposed_mutations=[{'type': 'set_mission_status', 'status': 'completed'}],
               path_assessment=dict(marginal_roi='positive', path_role='dominant_path',
                                    evidence_delta='no_new_evidence_expected'))
    if pairs is not None:
        out['task_replacements'] = pairs
    return out


def close_record(pairs=None):
    return dict(id='D1', timestamp='2026-10-16T01:00:00+00:00', event_type='decision_applied',
                summary='Authorized close', task_id=None, payload=decision(pairs))


PAIR = [{'task_id': 'T1', 'replacement_task_id': 'T2'}]


class SupersededClosureTests(unittest.TestCase):
    def test_explicit_qualified_replacement_closes_without_mutating_history(self):
        m = mission(); original = copy.deepcopy(m)
        self.assertEqual(_mission_completion_findings(m, [evidence(), close_record(PAIR)]), [])
        self.assertEqual(m, original)

    def test_matching_acceptance_and_newer_order_do_not_imply_replacement(self):
        self.assertTrue(_mission_completion_findings(mission(), [evidence(), close_record()]))
        self.assertTrue(_mission_completion_findings(mission(), [evidence()]))

    def test_extra_accepted_task_does_not_ambiguate_explicit_target(self):
        m = mission(); m['tasks'].append(dict(m['tasks'][2], id='T3'))
        self.assertEqual(_mission_completion_findings(m, [evidence(), evidence('T3', event_id='E2'), close_record(PAIR)]), [])

    def test_pending_active_blocked_paused_pruned_abandoned_are_not_discharged(self):
        for status in ('pending', 'active', 'blocked', 'paused', 'pruned', 'abandoned'):
            with self.subTest(status=status):
                m = mission(); m['tasks'][1]['status'] = status
                self.assertTrue(_mission_completion_findings(m, [evidence(), close_record(PAIR)]))

    def test_missing_wrong_scope_or_incomplete_successor_is_rejected(self):
        for change in ({'status': 'pending'}, {'acceptance_evidence': []}, {'role': 'supporting'}):
            with self.subTest(change=change):
                m = mission(); m['tasks'][2].update(change)
                self.assertTrue(_mission_completion_findings(m, [evidence(), close_record(PAIR)]))
        self.assertTrue(_mission_completion_findings(mission(), [evidence(), close_record([{'task_id': 'T1', 'replacement_task_id': 'T99'}])]))

    def test_current_successor_failure_is_not_hidden_by_other_positive_task(self):
        m = mission(); m['tasks'].append(dict(m['tasks'][2], id='T3'))
        events = [evidence(), evidence(kind='acceptance_failed', event_id='E2'), evidence('T3', event_id='E3'), close_record(PAIR)]
        self.assertTrue(_mission_completion_findings(m, events))

    def test_missing_legacy_or_old_task_acceptance_cannot_cover_successor(self):
        for events in ([], [evidence(kind='acceptance')], [evidence('T1')]):
            with self.subTest(events=events):
                self.assertTrue(_mission_completion_findings(mission(), events + [close_record(PAIR)]))

    def test_duplicate_acceptance_or_decision_ids_do_not_authorize_close(self):
        self.assertTrue(_mission_completion_findings(mission(), [evidence(), evidence(), close_record(PAIR)]))
        self.assertTrue(_mission_completion_findings(mission(), [evidence(), close_record(PAIR), close_record(PAIR)]))

    def test_previous_decision_cannot_authorize_current_undeclared_close(self):
        old = close_record(PAIR); old['id'] = 'D0'
        self.assertTrue(_mission_completion_findings(mission(), [old, evidence(), close_record()]))

    def test_ordinary_user_evidence_cannot_forge_replacement_authority(self):
        e = close_record(PAIR); e['event_type'] = 'key_finding'
        self.assertTrue(_mission_completion_findings(mission(), [evidence(), e]))

    def test_hook_rejects_malformed_self_and_conflicting_replacements(self):
        for pairs in ({}, [{'task_id': 'T1', 'replacement_task_id': 'T1'}], PAIR + PAIR,
                      [{'task_id': 'T1'}], [{'task_id': 'T1', 'replacement_task_id': None}]):
            with self.subTest(pairs=pairs):
                self.assertTrue(validate_hook_output(decision(pairs)))
        self.assertEqual(validate_hook_output(decision(PAIR)), [])

    def test_nonclose_or_combined_mutation_cannot_use_replacement_escape(self):
        d = decision(PAIR); d['recommendation'] = 'switch'
        self.assertTrue(validate_hook_output(d))
        d = decision(PAIR); d['proposed_mutations'].append({'type': 'transition_task', 'task_id': 'T1', 'status': 'completed'})
        self.assertTrue(validate_hook_output(d))

    def test_official_transaction_rejects_implicit_then_closes_explicitly_once(self):
        with tempfile.TemporaryDirectory(prefix='tplan-explicit-close-') as raw:
            root = Path(raw); mdir = root / 'mission-close-probe'
            def run(name, *args, ok=True):
                result = subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)], capture_output=True, text=True, timeout=20)
                if ok:
                    self.assertEqual(result.returncode, 0, result.stderr)
                else:
                    self.assertNotEqual(result.returncode, 0)
                return result
            run('init_lite.py', '--dir', mdir, '--mission-id', 'mission-close-probe', '--title', 'Close probe', '--objective', 'Verify replacement', '--acceptance-evidence', 'AC_GOAL:Qualified result', '--active-task-id', 'T0', '--active-task-title', 'Plan', '--active-task-contribution', 'Plan work')
            run('transition_task.py', mdir, '--task-id', 'T0', '--status', 'completed')
            for ident in ('T1', 'T2'):
                run('add_node.py', mdir, '--id', ident, '--kind', 'task', '--title', ident, '--role', 'success-critical', '--mission-contribution', 'Deliver result', '--acceptance-evidence', 'AC_GOAL')
            run('transition_task.py', mdir, '--task-id', 'T1', '--status', 'superseded')
            run('transition_task.py', mdir, '--task-id', 'T2', '--status', 'active')
            run('record_evidence.py', mdir, '--event-type', 'acceptance_passed', '--task-id', 'T2', '--summary', 'Reviewed result', '--payload-json', json.dumps({'acceptance_ids': ['AC_GOAL']}))
            run('transition_task.py', mdir, '--task-id', 'T2', '--status', 'completed')
            events = [json.loads(x) for x in (mdir / 'evidence.jsonl').read_text().splitlines()]
            ev_id = events[-1]['id']; path = root / 'decision.json'
            d = decision(); d['evidence_links'] = [ev_id]; path.write_text(json.dumps(d))
            before = (mdir / 'mission.json').read_bytes()
            rejected = run('apply_decision.py', mdir, '--decision', path, ok=False)
            self.assertIn('T1', rejected.stderr); self.assertEqual((mdir / 'mission.json').read_bytes(), before)
            d['task_replacements'] = PAIR; path.write_text(json.dumps(d))
            run('apply_decision.py', mdir, '--decision', path); run('check_mission.py', mdir)
            m = json.loads((mdir / 'mission.json').read_text())
            self.assertEqual(m['mission']['status'], 'completed')
            self.assertEqual(next(t for t in m['tasks'] if t['id'] == 'T1')['status'], 'superseded')
            trace = [json.loads(x) for x in (mdir / 'execution_trace.jsonl').read_text().splitlines()]
            self.assertEqual(sum(e['event_type'] == 'mission_status_changed' for e in trace), 1)


if __name__ == '__main__':
    unittest.main()
