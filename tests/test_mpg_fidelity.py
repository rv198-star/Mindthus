import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "skills" / "mpg" / "scripts" / "validate_mpg_output.py"


def valid_output() -> dict:
    move = {
        "status": "addressed",
        "finding": "The move was handled with path-specific reasoning.",
        "failure_criteria_response": "The answer did not collapse mainline into action.",
        "evidence_surface": "Scenario facts, uncertainty, and trigger boundary.",
    }
    return {
        "schema_version": "mpg-fidelity-v0.1",
        "method": "MPG",
        "applicability": "applicable",
        "plain_language_conclusion": "The mainline may hold, but the carrier should stage exposure.",
        "action_posture": "stage",
        "required_judgment_moves": {
            "qualified_mainline": dict(move),
            "carrier_vehicle_separation": dict(move),
            "counter_force_map": dict(move),
            "exposure_budget": dict(move),
            "optionality_design": dict(move),
            "trigger_conditions": dict(move),
            "mainline_challenge": dict(move),
            "aqm_boundary": dict(move),
        },
    }


def run_validator(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "mpg-output.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(
            ["python3", str(VALIDATOR), str(path)],
            text=True,
            capture_output=True,
            cwd=REPO,
        )


class MpgFidelityTests(unittest.TestCase):
    def test_valid_mpg_output_passes_shape_report(self):
        result = run_validator(valid_output())

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("MPG Shape & Evidence Risk Report", result.stdout)
        self.assertIn("No shape or evidence risks detected", result.stdout)
        self.assertIn("agentic audit remains required", result.stdout)

    def test_missing_required_judgment_move_fails(self):
        payload = valid_output()
        del payload["required_judgment_moves"]["aqm_boundary"]

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required judgment move: aqm_boundary", result.stdout)

    def test_unsupported_action_posture_fails(self):
        payload = valid_output()
        payload["action_posture"] = "buy_everything"

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("action_posture unsupported", result.stdout)

    def test_not_applicable_output_is_allowed_without_required_moves(self):
        result = run_validator(
            {
                "schema_version": "mpg-fidelity-v0.1",
                "method": "MPG",
                "applicability": "transfer",
                "plain_language_conclusion": "MPG is not dominant because no carrier decision exists.",
                "exit_reason": "The user asked for a general explanation, not a path-carrying strategy.",
                "transfer_to": "SELA",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("method exit accepted", result.stdout)

    def test_mpg_contract_and_pilot_cases_preserve_method_boundaries(self):
        contract = (REPO / "skills" / "mpg" / "resources" / "fidelity-contract.md").read_text(
            encoding="utf-8"
        )
        cases = (REPO / "tests" / "mpg" / "fidelity_pilot_cases.md").read_text(
            encoding="utf-8"
        )
        skill = (REPO / "skills" / "mpg" / "SKILL.md").read_text(encoding="utf-8")

        for phrase in (
            "MPG Fidelity Contract",
            "Human-Readable First",
            "Reasoning Durability",
            "AQM visibility layer",
            "not outcome hit rate",
            "mainline / carrier / vehicle",
            "shape pass is not semantic approval",
        ):
            self.assertIn(phrase, contract)

        for phrase in (
            "MPG Fidelity Pilot",
            "AI equity drawdown",
            "company transformation",
            "central-local implementation",
            "at least one non-stock case",
            "not outcome hit rate",
        ):
            self.assertIn(phrase, cases)

        self.assertIn("fidelity contract", skill)
        self.assertIn("Shape & Evidence Risk Report", skill)


if __name__ == "__main__":
    unittest.main()
