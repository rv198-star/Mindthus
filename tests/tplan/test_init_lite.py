import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import init_lite


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_lite_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    result = run_script(
        "init_lite.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "m1",
        "--title",
        "Lite Mission",
        "--objective",
        "Keep human-readable recovery state synchronized.",
        "--acceptance-evidence",
        "A1:Recovery state is synchronized.",
        "--active-task-id",
        "T1",
        "--active-task-title",
        "Prepare compact handoff",
        "--active-task-contribution",
        "Keeps enough recovery state to resume.",
        "--latest-state",
        "Initial lite state is ready.",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


class InitLiteTests(unittest.TestCase):
    def test_late_initialization_failure_rolls_back_and_retry_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            argv = [
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "m1",
                "--title",
                "Lite Mission",
                "--objective",
                "Make failed initialization retryable.",
                "--acceptance-evidence",
                "A1:Retry succeeds.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Initialize safely",
                "--active-task-contribution",
                "Provides retryable initialization.",
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                init_lite,
                "initialize_execution_trace",
                side_effect=OSError("simulated late failure"),
            ):
                self.assertEqual(init_lite.main(), 1)

            self.assertFalse((mission_dir / "mission.json").exists())
            with mock.patch.object(sys, "argv", argv):
                self.assertEqual(init_lite.main(), 0)
            self.assertTrue((mission_dir / "mission.json").exists())

    def test_init_lite_creates_active_root_task_without_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"

            result = run_script(
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "m1",
                "--title",
                "Lite Mission",
                "--objective",
                "Prepare a compact handoff without losing recovery state.",
                "--acceptance-evidence",
                "A1:Target is named.",
                "--acceptance-evidence",
                "A2:Recovery state is sufficient.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Prepare compact handoff",
                "--active-task-contribution",
                "Names the target and keeps enough recovery state to resume.",
                "--latest-state",
                "Initial lite state is ready.",
                "--resource-sufficiency",
                "35",
                "--risk-tolerance",
                "60",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["active_task_id"], "T1")
            self.assertEqual(len(mission["tasks"]), 1)

            task = mission["tasks"][0]
            self.assertEqual(task["id"], "T1")
            self.assertEqual(task["kind"], "task")
            self.assertEqual(task["level"], 1)
            self.assertEqual(task["status"], "active")
            self.assertEqual(task["role"], "success-critical")
            self.assertEqual(task["acceptance_evidence"], ["A1", "A2"])
            self.assertFalse(any(node["kind"] == "step" for node in mission["tasks"]))

            narrative = (mission_dir / "mission.md").read_text(encoding="utf-8")
            self.assertIn("## Lite Runtime State", narrative)
            self.assertIn("active_task_id: T1", narrative)
            self.assertIn("latest_state: Initial lite state is ready.", narrative)

            check = run_script("check_mission.py", str(mission_dir))
            self.assertEqual(check.returncode, 0, check.stderr)

    def test_init_lite_refuses_existing_runtime_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = Path(tmp) / "mission"
            mission_dir.mkdir()
            mission_file = mission_dir / "mission.json"
            mission_file.write_text('{"existing": true}\n', encoding="utf-8")

            result = run_script(
                "init_lite.py",
                "--dir",
                str(mission_dir),
                "--mission-id",
                "m1",
                "--title",
                "Lite Mission",
                "--objective",
                "Do not overwrite existing runtime.",
                "--acceptance-evidence",
                "A1:Existing file remains.",
                "--active-task-id",
                "T1",
                "--active-task-title",
                "Prepare compact handoff",
                "--active-task-contribution",
                "Keeps existing runtime safe.",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("mission runtime already exists", result.stderr)
            self.assertEqual(mission_file.read_text(encoding="utf-8"), '{"existing": true}\n')

    def test_state_changing_scripts_refresh_lite_runtime_state_in_narrative(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)

            done = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")

            self.assertEqual(done.returncode, 0, done.stderr)
            narrative = (mission_dir / "mission.md").read_text(encoding="utf-8")
            self.assertIn("mission_status: active", narrative)
            self.assertIn("active_task_id: none", narrative)
            self.assertNotIn("active_task_id: T1", narrative)

            decision = Path(tmp) / "close-decision.json"
            decision.write_text(
                json.dumps(
                    {
                        "recommendation": "close",
                        "rationale": "All lite mission acceptance evidence has been satisfied.",
                        "confidence": 90,
                        "evidence_links": [],
                        "proposed_mutations": [
                            {"type": "set_mission_status", "status": "completed"},
                        ],
                        "requires_human": False,
                        "mission_alignment": "Closing the mission matches the satisfied recovery-state acceptance evidence.",
                        "path_assessment": {
                            "marginal_roi": "positive",
                            "path_role": "dominant_path",
                            "evidence_delta": "new_evidence_expected",
                        },
                    }
                ),
                encoding="utf-8",
            )

            closed = run_script("apply_decision.py", str(mission_dir), "--decision", str(decision))

            self.assertEqual(closed.returncode, 0, closed.stderr)
            narrative = (mission_dir / "mission.md").read_text(encoding="utf-8")
            self.assertIn("mission_status: completed", narrative)
            self.assertIn("active_task_id: none", narrative)

    def test_state_refresh_replaces_noncanonical_lite_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            narrative_path = mission_dir / "mission.md"
            narrative_path.write_text(
                "# Lite Mission\n\n"
                "## Objective\n\n"
                "Keep human-readable recovery state synchronized.\n\n"
                "## Lite Runtime State   \n"
                "- active_task_id: T1\n"
                "- latest_state: Initial lite state is ready."
                "\n\n## Notes\n\n"
                "Keep this section.\n",
                encoding="utf-8",
            )

            done = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")

            self.assertEqual(done.returncode, 0, done.stderr)
            narrative = narrative_path.read_text(encoding="utf-8")
            self.assertEqual(narrative.count("## Lite Runtime State"), 1)
            self.assertIn("active_task_id: none", narrative)
            self.assertIn("latest_state: Task T1 transitioned to completed.", narrative)
            self.assertNotIn("active_task_id: T1", narrative)
            self.assertIn("## Notes\n\nKeep this section.", narrative)

    def test_state_refresh_collapses_duplicate_lite_runtime_state_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_lite_mission(tmp)
            narrative_path = mission_dir / "mission.md"
            narrative_path.write_text(
                "# Lite Mission\n\n"
                "## Objective\n\n"
                "Keep human-readable recovery state synchronized.\n\n"
                "## Lite Runtime State\n\n"
                "- active_task_id: T1\n"
                "- latest_state: First stale copy.\n\n"
                "## Notes\n\n"
                "Keep this section.\n\n"
                "## Lite Runtime State\n\n"
                "- active_task_id: T1\n"
                "- latest_state: Second stale copy.\n",
                encoding="utf-8",
            )

            done = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")

            self.assertEqual(done.returncode, 0, done.stderr)
            narrative = narrative_path.read_text(encoding="utf-8")
            self.assertEqual(narrative.count("## Lite Runtime State"), 1)
            self.assertIn("active_task_id: none", narrative)
            self.assertNotIn("active_task_id: T1", narrative)
            self.assertIn("## Notes\n\nKeep this section.", narrative)


if __name__ == "__main__":
    unittest.main()
