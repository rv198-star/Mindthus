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


class InitLiteTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
