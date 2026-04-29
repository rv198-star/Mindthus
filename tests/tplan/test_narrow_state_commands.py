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
                    "title": "Define runtime schema",
                    "role": "success-critical",
                    "mission_contribution": "Defines runtime behavior.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2",
                    "title": "Write runtime scripts",
                    "role": "success-critical",
                    "mission_contribution": "Implements runtime behavior.",
                    "acceptance_evidence": ["A1"],
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
        "Narrow Command Mission",
        "--objective",
        "Exercise narrow state commands.",
        "--acceptance-evidence",
        "A1:Runtime behavior exists.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


def mission_state(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


class NarrowStateCommandTests(unittest.TestCase):
    def test_set_active_task_marks_task_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

            result = run_script("set_active_task.py", str(mission_dir), "--task-id", "T2")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("set_active_task: T2", result.stdout)
            mission = mission_state(mission_dir)
            self.assertEqual(mission["active_task_id"], "T2")
            statuses = {task["id"]: task["status"] for task in mission["tasks"]}
            self.assertEqual(statuses["T2"], "active")

    def test_complete_task_marks_task_completed_and_clears_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            active = run_script("set_active_task.py", str(mission_dir), "--task-id", "T1")
            self.assertEqual(active.returncode, 0, active.stderr)

            result = run_script("complete_task.py", str(mission_dir), "--task-id", "T1")

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = mission_state(mission_dir)
            self.assertIsNone(mission["active_task_id"])
            statuses = {task["id"]: task["status"] for task in mission["tasks"]}
            self.assertEqual(statuses["T1"], "completed")

    def test_block_task_rejects_unknown_task_without_partial_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = (mission_dir / "mission.json").read_text(encoding="utf-8")

            result = run_script("block_task.py", str(mission_dir), "--task-id", "missing")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task missing does not exist", result.stderr)
            after = (mission_dir / "mission.json").read_text(encoding="utf-8")
            self.assertEqual(after, before)

    def test_pause_task_marks_task_paused(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

            result = run_script("pause_task.py", str(mission_dir), "--task-id", "T2")

            self.assertEqual(result.returncode, 0, result.stderr)
            statuses = {task["id"]: task["status"] for task in mission_state(mission_dir)["tasks"]}
            self.assertEqual(statuses["T2"], "paused")


if __name__ == "__main__":
    unittest.main()
