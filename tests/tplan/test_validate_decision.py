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


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ValidateDecisionTests(unittest.TestCase):
    def test_validate_decision_accepts_valid_child_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            write_json(
                decision,
                {
                    "recommendation": "continue",
                    "rationale": "The child node can complete its parent-facing draft.",
                    "confidence": 75,
                    "evidence_links": [],
                    "proposed_mutations": [
                        {"type": "transition_task", "task_id": "T1.1", "status": "completed"}
                    ],
                    "requires_human": False,
                    "parent_alignment": "Completing T1.1 gives T1 the needed draft.",
                    "mission_trace": "via T1 -> A1",
                },
            )

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["valid"])
            self.assertEqual(report["errors"], [])
            self.assertIsNone(report["repair_template"])
            self.assertEqual(report["next_action"], "apply_decision")

    def test_validate_decision_reports_invalid_json_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            decision.write_text("{not-json", encoding="utf-8")

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertIn("invalid JSON", report["errors"][0])
            self.assertEqual(report["next_action"], "repair_decision")
            self.assertEqual(report["repair_template"]["recommendation"], "continue")

    def test_validate_decision_reports_missing_fields_with_repair_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            write_json(decision, {"recommendation": "switch"})

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertIn("decision missing field: rationale", report["errors"])
            self.assertIn("proposed_mutations", report["repair_template"])
            self.assertEqual(report["next_action"], "repair_decision")

    def test_validate_decision_reports_bad_mutation_shape_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            decision = Path(tmp) / "decision.json"
            write_json(
                decision,
                {
                    "recommendation": "switch",
                    "rationale": "Switch to the task that unblocks runtime usage.",
                    "confidence": 80,
                    "evidence_links": [],
                    "proposed_mutations": [{"type": "set_active_task"}],
                    "requires_human": False,
                    "mission_alignment": "The switch advances Mission runtime usability.",
                },
            )

            result = run_script("validate_decision.py", "--decision", str(decision), "--json")

            self.assertNotEqual(result.returncode, 0)
            report = json.loads(result.stdout)
            self.assertFalse(report["valid"])
            self.assertIn("mutation set_active_task missing field: task_id", report["errors"])
            self.assertEqual(report["next_action"], "repair_decision")


if __name__ == "__main__":
    unittest.main()
