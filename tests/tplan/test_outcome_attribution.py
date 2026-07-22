import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from outcome_attribution import build_outcome_attribution
from tplan_runtime import TplanError, append_event, commit_mission_state, prepare_event, read_mission


def mission_fixture(status="active"):
    return {
        "mission": {
            "id": "M1",
            "status": "active",
            "acceptance_evidence": [{"id": "A1", "description": "Target host passes."}],
        },
        "active_task_id": "T1",
        "tasks": [
            {
                "id": "T1",
                "parent_id": None,
                "kind": "task",
                "role": "success-critical",
                "status": status,
                "acceptance_evidence": ["A1"],
            },
            {
                "id": "S1",
                "parent_id": "T1",
                "kind": "subtask",
                "role": "supporting",
                "status": "active",
            },
        ],
    }


def event(event_id, event_type, *, task_id="S1", payload=None, summary="Observed result."):
    return {
        "id": event_id,
        "timestamp": "2026-07-22T12:00:00Z",
        "event_type": event_type,
        "summary": summary,
        "task_id": task_id,
        "payload": payload or {},
    }


class OutcomeAttributionTests(unittest.TestCase):
    def test_acceptance_rolls_up_while_failure_is_a_constraint(self):
        mission = mission_fixture()
        events = [
            event("E1", "acceptance_passed", payload={"acceptance_ids": ["A1"]}, summary="A1 passed."),
            event("E2", "acceptance_failed", payload={"acceptance_ids": ["A1"]}, summary="A1 regressed."),
        ]
        report = build_outcome_attribution(mission, events)

        self.assertEqual(report["mission"]["yield_class"], "progress_and_constraint")
        self.assertEqual(report["tasks"]["S1"]["countable_progress"][0]["acceptance_ids"], ["A1"])
        self.assertEqual(len(report["tasks"]["T1"]["constraint_deltas"]), 1)

    def test_legacy_incomplete_acceptance_and_key_finding_are_not_progress(self):
        mission = mission_fixture(status="completed")
        report = build_outcome_attribution(
            mission,
            [
                event("E1", "acceptance", payload={}),
                event("E2", "key_finding", summary="Useful fact, but not acceptance."),
            ],
        )

        self.assertEqual(report["mission"]["countable_progress"], [])
        self.assertEqual(report["tasks"]["T1"]["yield_class"], "unclassified")
        warning_codes = {warning["code"] for warning in report["tasks"]["T1"]["warnings"]}
        self.assertIn("legacy_or_invalid_evidence", warning_codes)
        self.assertIn("completion_without_progress_evidence", warning_codes)

    def test_telemetry_alone_is_visible_without_progress(self):
        mission = mission_fixture()
        trace = [
            {
                "event_type": "span_completed",
                "task_id": "S1",
                "span": {"span_id": "SP1", "attribution": "exact"},
            }
        ]
        report = build_outcome_attribution(mission, [], trace)

        self.assertEqual(report["mission"]["yield_class"], "telemetry_only")
        self.assertEqual(report["tasks"]["T1"]["telemetry"]["span_count"], 1)
        self.assertEqual(report["tasks"]["S1"]["countable_progress"], [])

    def test_applied_mutation_requires_commit_relation_for_path_delta(self):
        mission = mission_fixture()
        applied = event(
            "E1",
            "decision_applied",
            task_id=None,
            payload={"recommendation": "continue", "proposed_mutations": [{"type": "set_active_task"}]},
        )
        unrelated_trace = [
            {
                "event_type": "span_completed",
                "task_id": None,
                "commit_id": "NOT-A-MUTATION",
                "refs": {"evidence_ids": ["E1"]},
                "span": {"span_id": "SP1", "attribution": "mission_overhead"},
            }
        ]
        without_commit = build_outcome_attribution(mission, [applied], unrelated_trace)
        self.assertEqual(without_commit["mission"]["countable_progress"], [])

        trace = [
            {
                "event_type": "active_node_changed",
                "task_id": "S1",
                "commit_id": "C1",
                "payload": {},
                "refs": {"evidence_ids": ["E1"]},
            }
        ]
        with_commit = build_outcome_attribution(mission, [applied], trace)
        self.assertEqual(with_commit["mission"]["countable_progress"][0]["kind"], "path_delta")
        self.assertEqual(with_commit["tasks"]["T1"]["countable_progress"][0]["kind"], "path_delta")
        self.assertEqual(with_commit["tasks"]["S1"]["countable_progress"][0]["commit_ids"], ["C1"])

    def test_completed_snapshot_without_trace_is_writeback_only_with_warning(self):
        mission = mission_fixture(status="completed")
        report = build_outcome_attribution(mission, [])

        task = report["tasks"]["T1"]
        self.assertEqual(task["yield_class"], "writeback_only")
        self.assertEqual(task["state_writebacks"][0]["event_type"], "mission_snapshot_status")
        self.assertIn(
            "completion_without_progress_evidence",
            {warning["code"] for warning in task["warnings"]},
        )

    def test_authorized_empty_continue_is_path_delta(self):
        mission = mission_fixture()
        authorization = {
            "trigger_reasons": ["manual_authorization"],
            "evidence_shape_lint": "pass",
            "defect_classification": "none",
            "expected_evidence_delta": "new_evidence_expected",
            "authorized_action": "continue_same_path",
        }
        applied = event(
            "E1",
            "decision_applied",
            task_id=None,
            payload={
                "recommendation": "continue",
                "proposed_mutations": [],
                "continuation_authorization": authorization,
            },
        )
        report = build_outcome_attribution(mission, [applied])
        self.assertEqual(report["mission"]["countable_progress"][0]["kind"], "path_delta")

    def test_historical_duplicate_evidence_id_warns_and_cannot_drive_commit_projection(self):
        mission = mission_fixture()
        applied = event(
            "EDUP",
            "decision_applied",
            task_id=None,
            payload={"recommendation": "continue", "proposed_mutations": [{"type": "set_active_task"}]},
        )
        blocker = event(
            "EDUP",
            "blocker",
            task_id=None,
            summary="Historical duplicate id creates ambiguity.",
        )
        trace = [
            {
                "event_type": "active_node_changed",
                "task_id": "S1",
                "commit_id": "C1",
                "payload": {},
                "refs": {"evidence_ids": ["EDUP"]},
            }
        ]

        report = build_outcome_attribution(mission, [applied, blocker], trace)

        self.assertEqual(report["mission"]["countable_progress"], [])
        self.assertEqual(report["mission"]["constraint_deltas"], [])
        self.assertEqual(report["mission"]["yield_class"], "unclassified")
        self.assertEqual(report["tasks"]["S1"]["countable_progress"], [])
        self.assertIn(
            "duplicate_evidence_id",
            {warning["code"] for warning in report["mission"]["warnings"]},
        )

    def test_public_append_rejects_reserved_and_invalid_acceptance_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            tasks = Path(tmp) / "tasks.json"
            tasks.write_text(
                json.dumps(
                    [
                        {
                            "id": "T1",
                            "title": "Test attribution",
                            "role": "success-critical",
                            "mission_contribution": "Tests the result boundary.",
                            "acceptance_evidence": ["A1"],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "init_mission.py"),
                    "--dir",
                    str(mission_dir),
                    "--mission-id",
                    "M1",
                    "--title",
                    "Attribution",
                    "--objective",
                    "Test attribution.",
                    "--acceptance-evidence",
                    "A1:Target host passes.",
                    "--task-json",
                    str(tasks),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with self.assertRaisesRegex(TplanError, "do not exist: A9"):
                append_event(
                    mission_dir,
                    {
                        "event_type": "acceptance_passed",
                        "summary": "Unknown acceptance.",
                        "task_id": "T1",
                        "payload": {"acceptance_ids": ["A9"]},
                    },
                )
            with self.assertRaisesRegex(TplanError, "acceptance_ids must be a non-empty list"):
                append_event(
                    mission_dir,
                    {
                        "event_type": "acceptance",
                        "summary": "Incomplete legacy write.",
                        "task_id": "T1",
                        "payload": {},
                    },
                )
            with self.assertRaisesRegex(TplanError, "runtime-reserved"):
                append_event(
                    mission_dir,
                    {
                        "event_type": "decision_applied",
                        "summary": "Spoofed apply.",
                        "task_id": None,
                        "payload": {},
                    },
                )

            before = read_mission(mission_dir)
            after = copy.deepcopy(before)
            after["tasks"][0]["status"] = "active"
            after["active_task_id"] = "T1"
            spoofed = prepare_event(
                mission_dir,
                {
                    "event_type": "decision_applied",
                    "summary": "Spoofed transactional apply.",
                    "task_id": None,
                    "payload": {
                        "recommendation": "continue",
                        "proposed_mutations": [{"type": "set_active_task", "task_id": "T1"}],
                    },
                },
            )
            with self.assertRaisesRegex(TplanError, "runtime-reserved"):
                commit_mission_state(
                    mission_dir,
                    before,
                    after,
                    source={"kind": "test", "name": "public_spoof"},
                    refs={"evidence_ids": [spoofed["id"]]},
                    prepared_evidence_events=[spoofed],
                )

            first = append_event(
                mission_dir,
                {
                    "id": "EDUP",
                    "event_type": "feedback",
                    "summary": "First unique evidence.",
                    "task_id": "T1",
                    "payload": {},
                },
            )
            self.assertEqual(first["id"], "EDUP")
            with self.assertRaisesRegex(TplanError, "evidence ids already exist: EDUP"):
                append_event(
                    mission_dir,
                    {
                        "id": "EDUP",
                        "event_type": "blocker",
                        "summary": "Duplicate evidence.",
                        "task_id": "T1",
                        "payload": {},
                    },
                )

            legacy_duplicate = dict(first)
            legacy_duplicate["event_type"] = "blocker"
            legacy_duplicate["summary"] = "Historical duplicate that predates validation."
            with (mission_dir / "evidence.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(legacy_duplicate) + "\n")
            safe = append_event(
                mission_dir,
                {
                    "id": "ESAFE",
                    "event_type": "feedback",
                    "summary": "A fresh unique event remains writable.",
                    "task_id": "T1",
                    "payload": {},
                },
            )
            self.assertEqual(safe["id"], "ESAFE")

            before = read_mission(mission_dir)
            duplicate_batch = [
                prepare_event(
                    mission_dir,
                    {
                        "id": "EBATCH",
                        "event_type": event_type,
                        "summary": summary,
                        "task_id": "T1",
                        "payload": {},
                    },
                )
                for event_type, summary in (
                    ("feedback", "First batch event."),
                    ("blocker", "Second batch event."),
                )
            ]
            with self.assertRaisesRegex(TplanError, "prepared evidence ids must be unique: EBATCH"):
                commit_mission_state(
                    mission_dir,
                    before,
                    copy.deepcopy(before),
                    source={"kind": "test", "name": "duplicate_batch"},
                    prepared_evidence_events=duplicate_batch,
                )
            self.assertEqual(
                [item["id"] for item in map(json.loads, (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines())],
                ["EDUP", "EDUP", "ESAFE"],
            )


if __name__ == "__main__":
    unittest.main()
