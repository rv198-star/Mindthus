import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tplan_runtime


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission-runtime-persistence"
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
            ]
        ),
        encoding="utf-8",
    )
    result = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "mission-runtime-persistence",
        "--title",
        "Runtime Persistence Mission",
        "--objective",
        "Protect state and evidence ordering.",
        "--acceptance-evidence",
        "A1:Persistence behavior is testable.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


def read_mission(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


def read_events(mission_dir):
    lines = (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def decision_payload():
    return {
        "recommendation": "switch",
        "rationale": "Switch to the script task because it blocks runtime usability.",
        "confidence": 80,
        "evidence_links": [],
        "proposed_mutations": [{"type": "set_active_task", "task_id": "T2"}],
        "requires_human": False,
        "mission_alignment": "Switching to T2 advances the runtime task that blocks Mission usability.",
        "path_assessment": {
            "marginal_roi": "positive",
            "path_role": "dominant_path",
            "evidence_delta": "new_evidence_expected",
        },
    }


def risk_payload():
    return {
        "scope": "shared_environment",
        "signal": "fsync_unreliable",
        "severity": "high",
        "confidence": "high",
        "affected_surfaces": ["generation"],
        "value_effect": "Expensive reruns may produce invalid evidence.",
        "recommended_gate": "environment_health_gate",
        "recovery_condition": "dd fsync and sqlite commit smoke pass",
    }


class RuntimePersistenceTests(unittest.TestCase):
    def test_write_json_keeps_existing_file_when_replace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mission.json"
            path.write_text('{"version": 1}\n', encoding="utf-8")

            with mock.patch.object(tplan_runtime.os, "replace", side_effect=OSError("replace failed")):
                with self.assertRaises(OSError):
                    tplan_runtime.write_json(path, {"version": 2})

            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"version": 1})

    def test_append_event_uses_unique_ids_under_concurrency(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            barrier = threading.Barrier(2)
            original_read_events = tplan_runtime.read_events
            results = []
            errors = []

            def synchronized_read_events(path):
                events = original_read_events(path)
                try:
                    barrier.wait(timeout=2)
                except threading.BrokenBarrierError:
                    pass
                return events

            def worker():
                try:
                    event = tplan_runtime.append_event(
                        mission_dir,
                        {"event_type": "feedback", "summary": "Concurrent append test.", "task_id": "T1"},
                    )
                except Exception as exc:  # pragma: no cover
                    errors.append(exc)
                else:
                    results.append(event["id"])

            with mock.patch.object(tplan_runtime, "read_events", side_effect=synchronized_read_events):
                threads = [threading.Thread(target=worker) for _ in range(2)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()

            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual(len(set(results)), 2)
            for event_id in results:
                self.assertRegex(event_id, r"^E[0-9a-f]{8}$")

    def test_stop_report_transaction_prepare_failure_leaves_no_ghost_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            active = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "active")
            self.assertEqual(active.returncode, 0, active.stderr)
            before = read_mission(mission_dir)

            original_write_json = tplan_runtime.write_json

            def fail_transaction(path, data):
                if path.name == ".mission-transaction.json":
                    raise OSError("disk full")
                return original_write_json(path, data)

            with mock.patch.object(tplan_runtime, "write_json", side_effect=fail_transaction):
                with self.assertRaises(OSError):
                    tplan_runtime.record_stop_report(
                        mission_dir,
                        "T1",
                        "Need human judgment.",
                        {
                            "current_goal": "Design a safe runtime decision boundary.",
                            "attempts": ["Inspected current runtime scripts."],
                            "blocking_issue": "The tradeoff belongs to product judgment.",
                            "why_cannot_continue_safely": "Continuing would invent the acceptance boundary.",
                            "need_from_human": "Confirm the preferred tradeoff.",
                            "resume_condition": "A human decision is recorded.",
                        },
                    )

            self.assertEqual(read_mission(mission_dir), before)
            events = read_events(mission_dir)
            self.assertEqual(events, [])

    def test_record_risk_signal_appends_event_before_mission_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = read_mission(mission_dir)

            with mock.patch.object(tplan_runtime, "write_mission", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    tplan_runtime.record_risk_signal(mission_dir, "T1", risk_payload())

            self.assertEqual(read_mission(mission_dir), before)
            events = read_events(mission_dir)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event_type"], "risk_context_update")
            self.assertEqual(events[0]["payload"]["risk_signal"]["source_evidence_id"], events[0]["id"])

    def test_resolve_risk_signal_appends_event_before_mission_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            tplan_runtime.record_risk_signal(mission_dir, "T1", risk_payload())
            before = read_mission(mission_dir)

            with mock.patch.object(tplan_runtime, "write_mission", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    tplan_runtime.resolve_risk_signal(
                        mission_dir,
                        "T1",
                        "R1",
                        "resolved",
                        "Storage smoke passed.",
                        "dd fsync and sqlite commit passed.",
                    )

            self.assertEqual(read_mission(mission_dir), before)
            events = read_events(mission_dir)
            self.assertEqual(len(events), 2)
            self.assertEqual(events[-1]["event_type"], "risk_context_recovery")
            self.assertEqual(events[-1]["payload"]["risk_id"], "R1")

    def test_apply_decision_transaction_prepare_failure_leaves_no_ghost_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = read_mission(mission_dir)

            original_write_json = tplan_runtime.write_json

            def fail_transaction(path, data):
                if path.name == ".mission-transaction.json":
                    raise OSError("disk full")
                return original_write_json(path, data)

            with mock.patch.object(tplan_runtime, "write_json", side_effect=fail_transaction):
                with self.assertRaises(OSError):
                    tplan_runtime.apply_decision(mission_dir, decision_payload())

            self.assertEqual(read_mission(mission_dir), before)
            events = read_events(mission_dir)
            self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
