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
                    "mission_contribution": "Defines the runtime contract.",
                    "acceptance_evidence": ["A1"],
                }
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
        "Add Node Mission",
        "--objective",
        "Add runtime nodes through scripts.",
        "--acceptance-evidence",
        "A1:Runtime contract exists.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


class AddNodeTests(unittest.TestCase):
    def test_add_node_creates_subtask_with_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "add_node.py",
                str(mission_dir),
                "--id",
                "T1.1",
                "--kind",
                "subtask",
                "--parent-id",
                "T1",
                "--title",
                "Draft schema fields",
                "--parent-contribution",
                "Drafts the fields required by T1.",
                "--parent-acceptance",
                "T1 can review concrete field names.",
                "--mission-trace",
                "via T1 -> A1",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("added_node: T1.1", result.stdout)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            node = next(task for task in mission["tasks"] if task["id"] == "T1.1")
            self.assertEqual(node["kind"], "subtask")
            self.assertEqual(node["level"], 2)
            self.assertEqual(node["status"], "pending")
            self.assertEqual(node["evidence_links"], [])

    def test_add_node_creates_step_directly_under_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "add_node.py",
                str(mission_dir),
                "--id",
                "T1.S1",
                "--kind",
                "step",
                "--parent-id",
                "T1",
                "--title",
                "Inspect schema fields",
                "--parent-contribution",
                "Gives T1 the current schema baseline.",
                "--mission-trace",
                "via T1 -> A1",
                "--step-action",
                "Read the schema and list fields.",
                "--done-condition",
                "Field list exists.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            node = next(task for task in mission["tasks"] if task["id"] == "T1.S1")
            self.assertEqual(node["kind"], "step")
            self.assertEqual(node["level"], 2)

    def test_add_node_rejects_child_under_step_without_partial_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            step = run_script(
                "add_node.py",
                str(mission_dir),
                "--id",
                "T1.S1",
                "--kind",
                "step",
                "--parent-id",
                "T1",
                "--title",
                "Inspect schema fields",
                "--parent-contribution",
                "Gives T1 the current schema baseline.",
                "--mission-trace",
                "via T1 -> A1",
                "--step-action",
                "Read the schema and list fields.",
                "--done-condition",
                "Field list exists.",
            )
            self.assertEqual(step.returncode, 0, step.stderr)

            result = run_script(
                "add_node.py",
                str(mission_dir),
                "--id",
                "T1.S1.1",
                "--kind",
                "step",
                "--parent-id",
                "T1.S1",
                "--title",
                "Inspect one field",
                "--parent-contribution",
                "Adds a lower-level action below a step.",
                "--mission-trace",
                "via T1.S1 -> T1 -> A1",
                "--step-action",
                "Inspect one field.",
                "--done-condition",
                "One field has been inspected.",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("parent T1.S1 cannot be a step", result.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertNotIn("T1.S1.1", {task["id"] for task in mission["tasks"]})


if __name__ == "__main__":
    unittest.main()
