import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PULSE_SCHEMA_VERSION = "tplan.pulse.v0.2"


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
                    "kind": "subtask",
                    "level": 2,
                    "title": "Draft mission fields",
                    "role": "supporting",
                    "parent_contribution": "Drafts the fields T1 needs.",
                    "parent_acceptance": "T1 can review concrete field names.",
                    "mission_trace": "via T1 -> A1",
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
        "key_finding",
        "--task-id",
        "T1.1",
        "--summary",
        "Draft fields expanded into a local branch.",
    )
    if evidence.returncode != 0:
        raise AssertionError(evidence.stderr)
    return mission_dir


def mission_tree_snapshot(mission_dir):
    return {
        str(path.relative_to(mission_dir)): path.read_bytes()
        for path in sorted(mission_dir.rglob("*"))
        if path.is_file()
    }


class SurveyAndPacketTests(unittest.TestCase):
    def assert_survey_pulse_payload_fidelity(self, survey, direct_pulse):
        pulse = survey["pulse"]
        outer_survey = dict(survey)
        outer_survey.pop("pulse")
        self.assertEqual(pulse, direct_pulse)
        self.assertEqual(pulse["snapshot"], outer_survey)
        self.assertEqual(pulse["pulse_shape_findings"], [])
        self.assertNotIn("health_score", pulse)
        self.assertNotIn("health_verdict", pulse)

    def test_survey_pulse_payload_fidelity_rejects_filtered_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            direct = run_script("mission_pulse.py", str(mission_dir), "--json")
            self.assertEqual(direct.returncode, 0, direct.stderr)
            direct_pulse = json.loads(direct.stdout)
            filtered_survey = dict(direct_pulse["snapshot"])
            filtered_survey["pulse"] = {
                "schema_version": direct_pulse["schema_version"],
                "script_verdict": direct_pulse["script_verdict"],
                "agentic_judgment_required": direct_pulse["agentic_judgment_required"],
                "snapshot": direct_pulse["snapshot"],
                "review_trigger_candidates": direct_pulse["review_trigger_candidates"],
                "winning_candidate": direct_pulse["winning_candidate"],
                "suppressed_candidates": direct_pulse["suppressed_candidates"],
                "arbitration_trace": direct_pulse["arbitration_trace"],
                "mission_pulse": direct_pulse["mission_pulse"],
                "pulse_shape_findings": [],
            }

        with self.assertRaises(AssertionError):
            self.assert_survey_pulse_payload_fidelity(filtered_survey, direct_pulse)

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

    def test_survey_can_include_read_only_mission_pulse(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = mission_tree_snapshot(mission_dir)
            result = run_script("survey.py", str(mission_dir), "--pulse", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_tree_snapshot(mission_dir)
            self.assertEqual(after, before)
            survey = json.loads(result.stdout)
            direct = run_script("mission_pulse.py", str(mission_dir), "--json")
            self.assertEqual(direct.returncode, 0, direct.stderr)
            direct_pulse = json.loads(direct.stdout)
            self.assertEqual(survey["mission"]["id"], "m1")
            self.assertIn("pulse", survey)
            self.assertEqual(survey["pulse"]["script_verdict"], "shape_only")
            self.assertTrue(survey["pulse"]["agentic_judgment_required"])
            self.assertEqual(survey["pulse"]["schema_version"], PULSE_SCHEMA_VERSION)
            self.assertEqual(survey["pulse"]["mission_pulse"]["schema_version"], PULSE_SCHEMA_VERSION)
            self.assertEqual(survey["pulse"]["mission_pulse"]["next_gate"], "continue")
            self.assertIn("winning_candidate", survey["pulse"])
            self.assertIn("suppressed_candidates", survey["pulse"])
            self.assertIn("arbitration_trace", survey["pulse"])
            self.assertIsNone(survey["pulse"]["winning_candidate"])
            self.assert_survey_pulse_payload_fidelity(survey, direct_pulse)

    def test_survey_pulse_accepts_trigger_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = mission_tree_snapshot(mission_dir)
            result = run_script(
                "survey.py",
                str(mission_dir),
                "--pulse",
                "--pulse-trigger",
                "before_continue",
                "--json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_tree_snapshot(mission_dir)
            self.assertEqual(after, before)
            survey = json.loads(result.stdout)
            direct = run_script("mission_pulse.py", str(mission_dir), "--trigger", "before_continue", "--json")
            self.assertEqual(direct.returncode, 0, direct.stderr)
            direct_pulse = json.loads(direct.stdout)

        self.assertEqual(survey["pulse"]["mission_pulse"]["trigger"], "before_continue")
        self.assertEqual(survey["pulse"]["mission_pulse"]["next_gate"], "continuation_authorization")
        self.assertEqual(survey["pulse"]["gate_owner"], "linear_continuation_gate")
        self.assertIn("winning_candidate", survey["pulse"])
        self.assertIn("suppressed_candidates", survey["pulse"])
        self.assertEqual(survey["pulse"]["winning_candidate"]["signal"], "same_path_continuation")
        self.assertEqual(survey["pulse"]["winning_candidate"]["priority_class"], "same_path_continuation")
        self.assertEqual(survey["pulse"]["suppressed_candidates"], [])
        self.assert_survey_pulse_payload_fidelity(survey, direct_pulse)

    def test_survey_pulse_rejects_unknown_trigger_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script(
                "survey.py",
                str(mission_dir),
                "--pulse",
                "--pulse-trigger",
                "bogus_trigger",
                "--json",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported pulse trigger", result.stderr)

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
