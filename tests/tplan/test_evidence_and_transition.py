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
        "Evidence Mission",
        "--objective",
        "Record evidence and transitions.",
        "--acceptance-evidence",
        "A1:Runtime contract exists.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


class EvidenceAndTransitionTests(unittest.TestCase):
    def test_record_evidence_appends_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "feedback",
                "--task-id",
                "T1",
                "--summary",
                "Schema draft exists.",
                "--payload-json",
                '{"path": "skills/tplan/resources/schema.md"}',
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("recorded_evidence:", result.stdout)
            lines = (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            event = json.loads(lines[0])
            self.assertEqual(event["event_type"], "feedback")
            self.assertEqual(event["task_id"], "T1")
            self.assertEqual(event["payload"]["path"], "skills/tplan/resources/schema.md")

    def test_record_step_log_writes_task_local_log_without_evidence_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "record_step_log.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--step-id",
                "S1",
                "--summary",
                "Inspected schema constraints.",
                "--payload-json",
                '{"files": ["skills/tplan/resources/schema.md"]}',
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("recorded_step_log:", result.stdout)

            evidence_lines = (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(evidence_lines, [])

            log_lines = (mission_dir / "logs" / "T1.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(log_lines), 1)
            event = json.loads(log_lines[0])
            self.assertEqual(event["step_id"], "S1")
            self.assertEqual(event["task_id"], "T1")
            self.assertEqual(event["summary"], "Inspected schema constraints.")
            self.assertEqual(event["payload"]["files"], ["skills/tplan/resources/schema.md"])

    def test_archive_task_logs_moves_logs_to_archive_and_writes_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            log = run_script(
                "record_step_log.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--step-id",
                "S1",
                "--summary",
                "Inspected schema constraints.",
            )
            self.assertEqual(log.returncode, 0, log.stderr)

            result = run_script(
                "archive_task_logs.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "Task T1 produced a usable runtime schema boundary.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("archived_task_logs: T1", result.stdout)
            self.assertFalse((mission_dir / "logs" / "T1.jsonl").exists())
            archived = mission_dir / "archive" / "T1" / "step_logs.jsonl"
            self.assertTrue(archived.exists())
            self.assertIn("Inspected schema constraints.", archived.read_text(encoding="utf-8"))
            summary = (mission_dir / "archive" / "T1" / "summary.md").read_text(encoding="utf-8")
            self.assertIn("# Task T1 Summary", summary)
            self.assertIn("Task T1 produced a usable runtime schema boundary.", summary)
            self.assertEqual((mission_dir / "evidence.jsonl").read_text(encoding="utf-8"), "")

    def test_transition_task_sets_active_and_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertEqual(mission["active_task_id"], "T1")
            self.assertEqual(mission["tasks"][0]["status"], "active")

            done = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")
            self.assertEqual(done.returncode, 0, done.stderr)
            mission = json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))
            self.assertIsNone(mission["active_task_id"])
            self.assertEqual(mission["tasks"][0]["status"], "completed")

    def test_transition_task_rejects_unknown_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script("transition_task.py", str(mission_dir), "--task-id", "missing", "--status", "active")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("task missing does not exist", result.stderr)


if __name__ == "__main__":
    unittest.main()
