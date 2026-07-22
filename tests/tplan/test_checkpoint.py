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
                    "title": "Define adaptive runtime",
                    "role": "success-critical",
                    "mission_contribution": "Defines the adaptive runtime contract.",
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
        "Checkpoint Mission",
        "--objective",
        "Record a compact runtime checkpoint.",
        "--acceptance-evidence",
        "A1:Adaptive runtime contract exists.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    active = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "active")
    if active.returncode != 0:
        raise AssertionError(active.stderr)
    return mission_dir


def create_pending_transaction(mission_dir):
    transaction = {
        "schema_version": "tplan.mission_transaction.v0.2",
        "mission": json.loads((mission_dir / "mission.json").read_text(encoding="utf-8")),
        "trace_text": (mission_dir / "execution_trace.jsonl").read_text(encoding="utf-8"),
        "evidence_text": (mission_dir / "evidence.jsonl").read_text(encoding="utf-8"),
        "latest_state": "A prepared transaction must be recovered by a writer.",
    }
    path = mission_dir / ".mission-transaction.json"
    path.write_text(json.dumps(transaction), encoding="utf-8")
    return path


class CheckpointTests(unittest.TestCase):
    def test_checkpoint_records_optional_log_and_evidence_then_outputs_survey(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

            result = run_script(
                "checkpoint.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--step-id",
                "lite-note",
                "--log-summary",
                "Captured the latest adaptive runtime note.",
                "--log-payload-json",
                '{"mode": "lite"}',
                "--evidence-type",
                "key_finding",
                "--evidence-summary",
                "Checkpoint can combine routine log, sparse evidence, and survey.",
                "--evidence-payload-json",
                '{"surface": "checkpoint"}',
                "--json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["recorded_log"]["id"], "L1")
            self.assertRegex(output["recorded_evidence"]["id"], r"^E[0-9a-f]{8}$")
            self.assertEqual(output["survey"]["mission"]["id"], "m1")
            self.assertEqual(output["survey"]["active_task"]["id"], "T1")
            self.assertEqual(output["survey"]["event_count"], 1)

            log_lines = (mission_dir / "logs" / "T1.jsonl").read_text(encoding="utf-8").splitlines()
            evidence_lines = (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(log_lines), 1)
            self.assertEqual(len(evidence_lines), 1)

            log_event = json.loads(log_lines[0])
            evidence_event = json.loads(evidence_lines[0])
            self.assertEqual(log_event["summary"], "Captured the latest adaptive runtime note.")
            self.assertEqual(log_event["payload"]["mode"], "lite")
            self.assertEqual(evidence_event["event_type"], "key_finding")
            self.assertEqual(evidence_event["summary"], "Checkpoint can combine routine log, sparse evidence, and survey.")
            self.assertEqual(evidence_event["task_id"], "T1")

    def test_checkpoint_rejects_incomplete_evidence_without_partial_log_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

            result = run_script(
                "checkpoint.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--log-summary",
                "This log should not be written.",
                "--evidence-type",
                "key_finding",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("evidence summary is required", result.stderr)
            self.assertFalse((mission_dir / "logs" / "T1.jsonl").exists())
            self.assertEqual((mission_dir / "evidence.jsonl").read_text(encoding="utf-8"), "")

    def test_empty_checkpoint_reports_honest_noop_without_writing_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before_files = {
                path.relative_to(mission_dir): path.read_bytes()
                for path in mission_dir.rglob("*")
                if path.is_file()
            }

            result = run_script("checkpoint.py", str(mission_dir), "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertTrue(output["noop"])
            self.assertIsNone(output["recorded_log"])
            self.assertIsNone(output["recorded_evidence"])
            self.assertEqual(
                {
                    path.relative_to(mission_dir): path.read_bytes()
                    for path in mission_dir.rglob("*")
                    if path.is_file()
                },
                before_files,
            )
            self.assertFalse((mission_dir / "logs" / "T1.jsonl").exists())

            text_result = run_script("checkpoint.py", str(mission_dir))
            self.assertEqual(text_result.returncode, 0, text_result.stderr)
            self.assertIn("checkpoint_noop: survey only", text_result.stdout)
            self.assertNotIn("checkpoint recorded", text_result.stdout)

    def test_empty_checkpoint_refuses_pending_transaction_without_recovering_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            transaction_path = create_pending_transaction(mission_dir)
            watched = [
                mission_dir / "mission.json",
                mission_dir / "mission.md",
                mission_dir / "evidence.jsonl",
                mission_dir / "execution_trace.jsonl",
                transaction_path,
            ]
            before = {path: path.read_bytes() for path in watched}

            result = run_script("checkpoint.py", str(mission_dir), "--json")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pending Mission transaction", result.stderr)
            self.assertEqual({path: path.read_bytes() for path in watched}, before)


if __name__ == "__main__":
    unittest.main()
