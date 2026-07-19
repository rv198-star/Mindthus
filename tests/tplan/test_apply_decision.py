import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import tplan_runtime


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_mission(tmp, human_in_loop):
    mission_dir = Path(tmp) / "mission"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Define runtime schema",
                    "role": "success-critical",
                    "mission_contribution": "Defines schema.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2",
                    "title": "Write runtime scripts",
                    "role": "success-critical",
                    "mission_contribution": "Implements runtime behavior.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2.1",
                    "parent_id": "T2",
                    "kind": "subtask",
                    "level": 2,
                    "title": "Draft CLI arguments",
                    "role": "supporting",
                    "parent_contribution": "Supplies the CLI argument draft needed by T2.",
                    "parent_acceptance": "T2 can implement script parsing from the draft.",
                    "mission_trace": "via T2 -> A1",
                },
            ]
        ),
        encoding="utf-8",
    )
    result = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "m1",
        "--title",
        "Authority Mission",
        "--objective",
        "Apply or record decisions.",
        "--acceptance-evidence",
        "A1:Runtime exists.",
        "--task-json",
        str(tasks),
        "--human-in-loop",
        str(human_in_loop),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


def valid_path_assessment():
    return {
        "marginal_roi": "positive",
        "path_role": "dominant_path",
        "evidence_delta": "new_evidence_expected",
    }


def valid_risk_assessment():
    return {
        "shared_context_used": ["R1"],
        "invalid_evidence_risk": "high",
        "failure_risk": "medium",
        "risk_adjusted_value": "weak",
        "next_gate": "health_check",
    }


def valid_continuation_authorization():
    return {
        "trigger_reasons": ["repeated_same_path_attempt"],
        "evidence_shape_lint": "pass",
        "defect_classification": "acceptance_blocking",
        "expected_evidence_delta": "new_evidence_expected",
        "authorized_action": "continue_same_path",
    }


def record_active_risk(mission_dir):
    result = run_script(
        "record_risk_context.py",
        str(mission_dir),
        "record",
        "--task-id",
        "T1",
        "--scope",
        "shared_environment",
        "--signal",
        "fsync_unreliable",
        "--severity",
        "high",
        "--confidence",
        "high",
        "--affected-surface",
        "generation",
        "--value-effect",
        "Expensive reruns may produce invalid evidence.",
        "--recommended-gate",
        "environment_health_gate",
        "--recovery-condition",
        "dd fsync and sqlite commit smoke pass",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)


def write_decision(tmp, recommendation="switch"):
    decision = Path(tmp) / "decision.json"
    decision.write_text(
        json.dumps(
            {
                "recommendation": recommendation,
                "rationale": "Switch to the script task because it blocks runtime usability.",
                "confidence": 80,
                "evidence_links": [],
                "proposed_mutations": [
                    {"type": "set_active_task", "task_id": "T2"}
                ],
                "requires_human": False,
                "mission_alignment": "Switching to T2 advances the runtime task that blocks Mission usability.",
                "path_assessment": valid_path_assessment(),
            }
        ),
        encoding="utf-8",
    )
    return decision


class ApplyDecisionTests(unittest.TestCase):
    def test_concurrent_decision_loser_leaves_no_ghost_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = json.loads(write_decision(tmp).read_text(encoding="utf-8"))
            barrier = Barrier(2)
            original_commit = tplan_runtime.commit_mission_state

            def synchronized_commit(*args, **kwargs):
                barrier.wait(timeout=5)
                return original_commit(*args, **kwargs)

            def invoke():
                try:
                    return tplan_runtime.apply_decision(mission_dir, decision)
                except tplan_runtime.TplanError as exc:
                    return str(exc)

            with mock.patch.object(tplan_runtime, "commit_mission_state", synchronized_commit):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(lambda _: invoke(), range(2)))

            self.assertEqual(results.count("applied_decision"), 1)
            self.assertEqual(
                sum("Mission state changed concurrently" in result for result in results),
                1,
            )
            events = [
                json.loads(line)
                for line in (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(
                sum(event.get("event_type") == "decision_applied" for event in events),
                1,
            )

    def test_interrupted_decision_rolls_forward_on_next_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = json.loads(write_decision(tmp).read_text(encoding="utf-8"))
            original_write_json = tplan_runtime.write_json

            def interrupt_after_journal(path, data):
                if path.name == "mission.json" and (mission_dir / ".mission-transaction.json").exists():
                    raise OSError("simulated abrupt interruption")
                return original_write_json(path, data)

            with mock.patch.object(tplan_runtime, "write_json", interrupt_after_journal):
                with self.assertRaisesRegex(OSError, "simulated abrupt interruption"):
                    tplan_runtime.apply_decision(mission_dir, decision)

            self.assertTrue((mission_dir / ".mission-transaction.json").exists())
            recovered = tplan_runtime.read_mission(mission_dir)
            self.assertEqual(recovered["active_task_id"], "T2")
            self.assertFalse((mission_dir / ".mission-transaction.json").exists())
            trace = tplan_runtime.read_execution_trace(mission_dir)
            events = tplan_runtime.read_events(mission_dir)
            applied = [event for event in events if event.get("event_type") == "decision_applied"]
            self.assertEqual(len(applied), 1)
            self.assertTrue(
                any(applied[0]["id"] in record.get("refs", {}).get("evidence_ids", []) for record in trace)
            )

    def test_autonomous_mode_applies_decision_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = write_decision(tmp)
            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("applied_decision", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["active_task_id"], "T2")
            statuses = {task["id"]: task["status"] for task in mission["tasks"]}
            self.assertEqual(statuses["T2"], "active")

    def test_advisory_mode_records_recommendation_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=100)
            decision = write_decision(tmp)
            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("recorded_recommendation", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])
            events = [
                json.loads(line)
                for line in (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(events[-1]["event_type"], "decision_recommendation")

    def test_requires_human_records_recommendation_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "close",
                        "rationale": "Closure is outside delegated authority.",
                        "confidence": 70,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_mission_status", "status": "abandoned"}
                        ],
                        "requires_human": True,
                        "mission_alignment": "Closure affects Mission status and must remain tied to release viability.",
                        "path_assessment": valid_path_assessment(),
                    }
                ),
                encoding="utf-8",
            )
            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("recorded_recommendation", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["mission"]["status"], "active")

    def test_malformed_mutation_fails_without_traceback_or_partial_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "switch",
                        "rationale": "Malformed mutation should not partially mutate Mission state.",
                        "confidence": 80,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_active_task"},
                        ],
                        "requires_human": False,
                        "mission_alignment": "The proposed switch claims to advance runtime usability.",
                        "path_assessment": valid_path_assessment(),
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mutation set_active_task missing field: task_id", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_reserved_human_in_loop_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            mission_path = mission_dir / "mission.json"
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            mission["mission"]["human_in_loop"] = 50
            mission_path.write_text(json.dumps(mission), encoding="utf-8")
            decision = write_decision(tmp)

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("human_in_loop must be 0 or 100 in tplan.v0.1", result.stderr)
            mission = json.loads(mission_path.read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_missing_mission_alignment_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "switch",
                        "rationale": "Switch without Mission alignment should be rejected.",
                        "confidence": 80,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_active_task", "task_id": "T2"},
                        ],
                        "requires_human": False,
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("decision missing field: mission_alignment", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_child_level_decision_accepts_parent_alignment_without_mission_alignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "The child draft is ready for parent review.",
                        "confidence": 75,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "transition_task", "task_id": "T2.1", "status": "completed"},
                        ],
                        "requires_human": False,
                        "parent_alignment": "Completing T2.1 gives T2 its CLI argument draft.",
                        "mission_trace": "via T2 -> A1",
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("applied_decision", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            statuses = {task["id"]: task["status"] for task in mission["tasks"]}
            self.assertEqual(statuses["T2.1"], "completed")

    def test_high_impact_decision_requires_path_assessment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "switch",
                        "rationale": "Switching active tasks is high-impact.",
                        "confidence": 80,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_active_task", "task_id": "T2"},
                        ],
                        "requires_human": False,
                        "mission_alignment": "Switching to T2 advances runtime usability.",
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("decision missing field: path_assessment", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_mission_aligned_continue_requires_path_assessment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "Continue the same Mission-level path.",
                        "confidence": 80,
                        "evidence_links": [],
                        "proposed_mutations": [],
                        "requires_human": False,
                        "mission_alignment": "Continuing this path claims Mission-level leverage.",
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("decision missing field: path_assessment", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])

    def test_path_assessment_must_be_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = write_decision(tmp)
            payload = json.loads(decision.read_text(encoding="utf-8"))
            payload["path_assessment"] = "positive"
            decision.write_text(json.dumps(payload), encoding="utf-8")

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("path_assessment must be an object", result.stderr)

    def test_path_assessment_rejects_unsupported_enum(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = write_decision(tmp)
            payload = json.loads(decision.read_text(encoding="utf-8"))
            payload["path_assessment"]["path_role"] = "only_possible_way"
            decision.write_text(json.dumps(payload), encoding="utf-8")

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("path_assessment path_role unsupported", result.stderr)

    def test_mission_aligned_continue_requires_continuation_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "Continue the same Mission-facing path after a late evidence defect.",
                        "confidence": 70,
                        "evidence_links": [],
                        "proposed_mutations": [],
                        "requires_human": False,
                        "mission_alignment": "The continuation claims to advance Mission acceptance evidence.",
                        "path_assessment": valid_path_assessment(),
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("decision missing field: continuation_authorization", result.stderr)

    def test_valid_continuation_authorization_allows_mission_aligned_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "Continue a bounded same-path action after classifying the defect as acceptance-blocking.",
                        "confidence": 70,
                        "evidence_links": [],
                        "proposed_mutations": [],
                        "requires_human": False,
                        "mission_alignment": "The continuation can produce decision-constraining acceptance evidence.",
                        "path_assessment": valid_path_assessment(),
                        "continuation_authorization": valid_continuation_authorization(),
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_continuation_authorization_rejects_unsupported_enum(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            payload = {
                "recommendation": "continue",
                "rationale": "Continue a bounded same-path action after classifying the defect.",
                "confidence": 70,
                "evidence_links": [],
                "proposed_mutations": [],
                "requires_human": False,
                "mission_alignment": "The continuation can produce decision-constraining acceptance evidence.",
                "path_assessment": valid_path_assessment(),
                "continuation_authorization": valid_continuation_authorization(),
            }
            payload["continuation_authorization"]["defect_classification"] = "minor_bug"
            decision.write_text(json.dumps(payload), encoding="utf-8")

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("continuation_authorization defect_classification unsupported", result.stderr)

    def test_low_impact_child_decision_does_not_require_path_assessment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "The child draft is ready for parent review.",
                        "confidence": 75,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "transition_task", "task_id": "T2.1", "status": "completed"},
                        ],
                        "requires_human": False,
                        "parent_alignment": "Completing T2.1 gives T2 its CLI argument draft.",
                        "mission_trace": "via T2 -> A1",
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_high_impact_decision_with_active_risk_requires_risk_assessment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            record_active_risk(mission_dir)
            decision = write_decision(tmp)

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("decision missing field: risk_assessment", result.stderr)

    def test_risk_assessment_rejects_unsupported_enum(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            record_active_risk(mission_dir)
            decision = write_decision(tmp)
            payload = json.loads(decision.read_text(encoding="utf-8"))
            payload["risk_assessment"] = valid_risk_assessment()
            payload["risk_assessment"]["next_gate"] = "rerun_anyway"
            decision.write_text(json.dumps(payload), encoding="utf-8")

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("risk_assessment next_gate unsupported", result.stderr)

    def test_valid_risk_assessment_passes_with_active_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            record_active_risk(mission_dir)
            decision = write_decision(tmp)
            payload = json.loads(decision.read_text(encoding="utf-8"))
            payload["risk_assessment"] = valid_risk_assessment()
            decision.write_text(json.dumps(payload), encoding="utf-8")

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_low_impact_child_decision_with_active_risk_does_not_require_risk_assessment(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            record_active_risk(mission_dir)
            decision = Path(tmp) / "decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "continue",
                        "rationale": "The child draft is ready for parent review.",
                        "confidence": 75,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "transition_task", "task_id": "T2.1", "status": "completed"},
                        ],
                        "requires_human": False,
                        "parent_alignment": "Completing T2.1 gives T2 its CLI argument draft.",
                        "mission_trace": "via T2 -> A1",
                    }
                ),
                encoding="utf-8",
            )

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_existing_mission_state_blocks_apply_decision_without_disk_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp, human_in_loop=0)
            mission_path = mission_dir / "mission.json"
            broken = json.loads(mission_path.read_text(encoding="utf-8"))
            broken["tasks"][0]["title"] = 123
            mission_path.write_text(json.dumps(broken), encoding="utf-8")
            decision = write_decision(tmp)

            result = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task T1 title must be a string", result.stderr)
            self.assertEqual(json.loads(mission_path.read_text(encoding="utf-8")), broken)
            self.assertEqual((mission_dir / "evidence.jsonl").read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
