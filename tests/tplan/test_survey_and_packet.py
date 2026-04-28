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
                    "mission_contribution": "Defines schema.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T1.1",
                    "parent_id": "T1",
                    "level": 3,
                    "title": "Draft mission fields",
                    "role": "supporting",
                    "mission_contribution": "Supports schema definition.",
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
        "Packet Mission",
        "--objective",
        "Generate survey and packet.",
        "--acceptance-evidence",
        "A1:Schema exists.",
        "--task-json",
        str(tasks),
        "--resource-sufficiency",
        "60",
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    transition = run_script("transition_task.py", str(mission_dir), "--task-id", "T1.1", "--status", "active")
    if transition.returncode != 0:
        raise AssertionError(transition.stderr)
    evidence = run_script(
        "record_evidence.py",
        str(mission_dir),
        "--event-type",
        "feedback",
        "--task-id",
        "T1.1",
        "--summary",
        "Draft fields expanded into a local branch.",
    )
    if evidence.returncode != 0:
        raise AssertionError(evidence.stderr)
    return mission_dir


class SurveyAndPacketTests(unittest.TestCase):
    def test_survey_outputs_state_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script("survey.py", str(mission_dir), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            survey = json.loads(result.stdout)
            self.assertEqual(survey["mission"]["id"], "m1")
            self.assertEqual(survey["active_task"]["id"], "T1.1")
            self.assertEqual(survey["tasks_by_status"]["active"], ["T1.1"])
            self.assertEqual(survey["resource_sufficiency"], 60)

    def test_make_decision_packet_includes_required_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            packet_path = Path(tmp) / "packet.json"
            result = run_script(
                "make_decision_packet.py",
                str(mission_dir),
                "--hook",
                "subtraction",
                "--output",
                str(packet_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["hook"], "subtraction")
            self.assertEqual(packet["mission"]["objective"], "Generate survey and packet.")
            self.assertEqual([task["id"] for task in packet["parent_chain"]], ["T1", "T1.1"])
            self.assertEqual(packet["policy"]["human_in_loop"], 0)
            self.assertEqual(packet["policy"]["resource_sufficiency"], 60)
            self.assertEqual(len(packet["relevant_evidence_events"]), 1)


if __name__ == "__main__":
    unittest.main()
