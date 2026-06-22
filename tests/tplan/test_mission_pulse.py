import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Validate pulse route",
                    "role": "success-critical",
                    "mission_contribution": "Keeps the Mission attached to the review route.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2",
                    "title": "Run health gate",
                    "role": "supporting",
                    "mission_contribution": "Checks shared evidence health before rerun.",
                    "acceptance_evidence": [],
                },
                {
                    "id": "T3",
                    "title": "Explore alternate route",
                    "role": "exploratory",
                    "mission_contribution": "Provides an alternate path if the active route stops paying off.",
                    "acceptance_evidence": [],
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
        "Mission Pulse",
        "--objective",
        "Route review signals without creating a new judgment center.",
        "--acceptance-evidence",
        "A1:Pulse routes observable signals to existing gates.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    active = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "active")
    if active.returncode != 0:
        raise AssertionError(active.stderr)
    return mission_dir


def mission_files_snapshot(mission_dir):
    paths = [
        mission_dir / "mission.json",
        mission_dir / "evidence.jsonl",
        mission_dir / "mission.md",
    ]
    return {str(path.relative_to(mission_dir)): path.read_text(encoding="utf-8") for path in paths}


class MissionPulseTests(unittest.TestCase):
    def test_mission_pulse_is_read_only_and_routes_routine_checkpoint_to_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = mission_files_snapshot(mission_dir)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "checkpoint_batch", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_files_snapshot(mission_dir)
            self.assertEqual(after, before)
            pulse = json.loads(result.stdout)

        self.assertEqual(pulse["script_verdict"], "shape_only")
        self.assertTrue(pulse["agentic_judgment_required"])
        self.assertEqual(pulse["mission_pulse"]["schema_version"], "tplan.pulse.v0.1")
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continue")
        self.assertEqual(pulse["mission_pulse"]["trigger"], "checkpoint_batch")
        self.assertEqual(pulse["mission_pulse"]["scope"], "active_node")
        self.assertEqual(pulse["mission_pulse"]["signals"], [])
        self.assertEqual(pulse["gate_owner"], "inline_alignment")
        self.assertNotIn("health_score", pulse)
        self.assertNotIn("health_verdict", pulse)
        self.assertFalse(pulse["review_trigger_candidates"])
        self.assertEqual(pulse["snapshot"]["active_task"]["id"], "T1")

    def test_mission_pulse_routes_active_shared_risk_to_health_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            risk = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_evidence_channel",
                "--signal",
                "evidence_channel_untrusted_until_smoke_check",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "evidence_persistence",
                "--value-effect",
                "Future acceptance evidence may be invalid until the channel is checked.",
                "--recommended-gate",
                "health_check",
                "--recovery-condition",
                "Evidence channel smoke check passes.",
            )
            self.assertEqual(risk.returncode, 0, risk.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "shared_risk", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assertEqual(pulse["script_verdict"], "shape_only")
        self.assertTrue(pulse["agentic_judgment_required"])
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "health_check")
        self.assertEqual(pulse["gate_owner"], "shared_risk_mission_health_route")
        self.assertEqual(pulse["mission_pulse"]["scope"], "mission")
        self.assertIn("active_shared_risk", pulse["mission_pulse"]["signals"])
        self.assertIn("invalid_evidence_risk", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["systemic_probe"], "use_existing_structure")
        self.assertEqual(pulse["snapshot"]["shared_context"]["active_risk_signal_count"], 1)
        self.assertEqual(
            pulse["review_trigger_candidates"][0]["candidate_next_gate"],
            "health_check",
        )
        self.assertIn("R1", pulse["review_trigger_candidates"][0]["source_ids"])
        self.assertNotIn("risk_assessment", pulse)

    def test_mission_pulse_routes_before_continue_to_continuation_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "before_continue", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continuation_authorization")
        self.assertEqual(pulse["gate_owner"], "linear_continuation_gate")
        self.assertIn("same_path_continuation", pulse["mission_pulse"]["signals"])
        self.assertEqual(
            pulse["review_trigger_candidates"][0]["candidate_next_gate"],
            "continuation_authorization",
        )

    def test_mission_pulse_routes_repeated_object_touch_to_anti_spiral(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            for index in range(3):
                result = run_script(
                    "record_step_log.py",
                    str(mission_dir),
                    "--task-id",
                    "T1",
                    "--step-id",
                    f"repair-{index + 1}",
                    "--summary",
                    f"Adjusted the same local prompt section {index + 1}.",
                    "--payload-json",
                    '{"object_id": "prompt:section-a", "change_kind": "add_layer"}',
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "before_continue", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assertEqual(pulse["mission_pulse"]["next_gate"], "anti_spiral_audit")
        self.assertEqual(pulse["gate_owner"], "anti_spiral_runtime_gate")
        self.assertIn("third_touch", pulse["mission_pulse"]["signals"])
        self.assertIn("additive_layering", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["systemic_probe"], "needs_gate")
        self.assertIn("prompt:section-a", pulse["review_trigger_candidates"][0]["source_ids"])

    def test_mission_pulse_routes_branch_cleanup_to_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "branch_cleanup", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assertEqual(pulse["mission_pulse"]["next_gate"], "selection")
        self.assertEqual(pulse["gate_owner"], "selection_hook")
        self.assertIn("branch_cleanup_candidate", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["branch_disposition"], "unclear")
        self.assertEqual(
            pulse["review_trigger_candidates"][0]["candidate_next_gate"],
            "selection",
        )

    def test_mission_pulse_routes_requires_human_status_to_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            stop = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "Cannot continue without user authority.",
                "--current-goal",
                "Route an unclear authority boundary.",
                "--attempt",
                "Checked runtime state.",
                "--blocking-issue",
                "The acceptance authority is unclear.",
                "--why-cannot-continue-safely",
                "Continuing would invent acceptance criteria.",
                "--need-from-human",
                "Confirm the intended acceptance boundary.",
                "--resume-condition",
                "The user confirms the acceptance boundary.",
            )
            self.assertEqual(stop.returncode, 0, stop.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "before_freeze", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assertEqual(pulse["mission_pulse"]["next_gate"], "stop")
        self.assertEqual(pulse["gate_owner"], "stop_report")
        self.assertIn("requires_human", pulse["mission_pulse"]["signals"])
        self.assertIn("authority_boundary_unclear", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["scope"], "mission")


if __name__ == "__main__":
    unittest.main()
