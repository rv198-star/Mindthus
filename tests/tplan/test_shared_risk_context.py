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
                    "title": "Run shared validation",
                    "role": "success-critical",
                    "mission_contribution": "Validates shared risk context.",
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
        "m-risk",
        "--title",
        "Shared Risk Mission",
        "--objective",
        "Validate shared risk context.",
        "--acceptance-evidence",
        "A1:Shared risk context is runtime-valid.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return mission_dir


def valid_signal():
    return {
        "id": "R1",
        "source_task_id": "T1",
        "scope": "shared_environment",
        "signal": "fsync_unreliable",
        "severity": "high",
        "confidence": "high",
        "affected_surfaces": ["generation", "sqlite"],
        "value_effect": "Expensive reruns may produce invalid evidence.",
        "recommended_gate": "environment_health_gate",
        "recovery_condition": "dd fsync and sqlite commit smoke pass",
        "status": "active",
        "created_at": "2026-06-10T00:00:00+00:00",
        "updated_at": "2026-06-10T00:00:00+00:00",
    }


def write_shared_context(mission_dir, signals):
    mission_path = mission_dir / "mission.json"
    mission = json.loads(mission_path.read_text(encoding="utf-8"))
    mission["shared_context"] = {"risk_signals": signals}
    mission_path.write_text(json.dumps(mission), encoding="utf-8")


def read_mission(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


def read_events(mission_dir):
    events = []
    for line in (mission_dir / "evidence.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


class SharedRiskContextTests(unittest.TestCase):
    def test_check_mission_accepts_valid_shared_risk_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            write_shared_context(mission_dir, [valid_signal()])

            result = run_script("check_mission.py", str(mission_dir))

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_mission_rejects_invalid_shared_risk_signal_enum(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            signal = valid_signal()
            signal["severity"] = "severe"
            write_shared_context(mission_dir, [signal])

            result = run_script("check_mission.py", str(mission_dir))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("risk signal R1 severity unsupported", result.stdout)

    def test_record_risk_context_creates_signal_and_evidence_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

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
                "--affected-surface",
                "sqlite",
                "--value-effect",
                "Expensive reruns may produce invalid evidence.",
                "--recommended-gate",
                "environment_health_gate",
                "--recovery-condition",
                "dd fsync and sqlite commit smoke pass",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = read_mission(mission_dir)
            signals = mission["shared_context"]["risk_signals"]
            self.assertEqual(len(signals), 1)
            self.assertEqual(signals[0]["id"], "R1")
            self.assertEqual(signals[0]["status"], "active")
            self.assertEqual(signals[0]["affected_surfaces"], ["generation", "sqlite"])
            events = read_events(mission_dir)
            self.assertEqual(events[-1]["event_type"], "risk_context_update")
            self.assertEqual(signals[0]["source_evidence_id"], events[-1]["id"])
            self.assertEqual(events[-1]["payload"]["risk_signal"]["id"], "R1")

    def test_resolve_risk_context_marks_signal_resolved_and_records_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            record = run_script(
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
            self.assertEqual(record.returncode, 0, record.stderr)

            result = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "resolve",
                "--task-id",
                "T1",
                "--risk-id",
                "R1",
                "--status",
                "resolved",
                "--summary",
                "Storage smoke passed.",
                "--recovery-note",
                "dd fsync and sqlite commit passed.",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            mission = read_mission(mission_dir)
            signal = mission["shared_context"]["risk_signals"][0]
            self.assertEqual(signal["status"], "resolved")
            events = read_events(mission_dir)
            self.assertEqual(events[-1]["event_type"], "risk_context_recovery")
            self.assertEqual(events[-1]["payload"]["risk_id"], "R1")
            self.assertEqual(events[-1]["payload"]["status"], "resolved")

    def test_survey_and_decision_packet_include_active_risk_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            record = run_script(
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
            self.assertEqual(record.returncode, 0, record.stderr)

            survey_result = run_script("survey.py", str(mission_dir), "--json")
            self.assertEqual(survey_result.returncode, 0, survey_result.stderr)
            survey = json.loads(survey_result.stdout)
            self.assertEqual(survey["shared_context"]["active_risk_signal_count"], 1)
            self.assertEqual(survey["shared_context"]["highest_active_severity"], "high")
            self.assertEqual(survey["shared_context"]["active_risk_signals"][0]["id"], "R1")

            packet_path = Path(tmp) / "packet.json"
            packet_result = run_script(
                "make_decision_packet.py",
                str(mission_dir),
                "--hook",
                "subtraction",
                "--output",
                str(packet_path),
            )
            self.assertEqual(packet_result.returncode, 0, packet_result.stderr)
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["shared_context"]["active_risk_signals"][0]["id"], "R1")
            self.assertEqual(packet["shared_context"]["highest_active_severity"], "high")


if __name__ == "__main__":
    unittest.main()
