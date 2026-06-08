import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "skills" / "sela" / "scripts" / "validate_sela_output.py"


def valid_output() -> dict:
    move = {
        "status": "addressed",
        "finding": "The move was explicitly handled with concrete scenario logic.",
        "failure_criteria_response": "The output did not skip this SELA trap.",
        "evidence_surface": "Scenario facts and named uncertainty.",
    }
    return {
        "schema_version": "sela-fidelity-v0.1",
        "method": "SELA",
        "applicability": "applicable",
        "plain_language_conclusion": "Use SELA for direction, but stage the action.",
        "action_posture": "stage",
        "required_judgment_moves": {
            "fair_comparison_check": dict(move),
            "local_advantage_scalability": dict(move),
            "system_efficiency_trajectory": dict(move),
            "hard_boundary_check": dict(move),
            "timing_action_posture": dict(move),
            "misuse_challenge": dict(move),
        },
    }


def run_validator(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sela-output.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(
            ["python3", str(VALIDATOR), str(path)],
            text=True,
            capture_output=True,
            cwd=REPO,
        )


class SelaFidelityTests(unittest.TestCase):
    def test_valid_sela_output_passes_shape_report(self):
        result = run_validator(valid_output())

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("SELA Shape & Evidence Risk Report", result.stdout)
        self.assertIn("No shape or evidence risks detected", result.stdout)
        self.assertIn("agentic audit remains required", result.stdout)
        self.assertNotIn("semantic approval", result.stdout)

    def test_missing_required_judgment_move_fails(self):
        payload = valid_output()
        del payload["required_judgment_moves"]["misuse_challenge"]

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required judgment move: misuse_challenge", result.stdout)
        self.assertIn("agentic audit remains required", result.stdout)

    def test_empty_move_finding_fails(self):
        payload = valid_output()
        payload["required_judgment_moves"]["fair_comparison_check"]["finding"] = ""

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fair_comparison_check.finding is empty", result.stdout)

    def test_unsupported_action_posture_fails(self):
        payload = valid_output()
        payload["action_posture"] = "combine"

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("action_posture unsupported", result.stdout)

    def test_not_applicable_output_is_allowed_without_required_moves(self):
        result = run_validator(
            {
                "schema_version": "sela-fidelity-v0.1",
                "method": "SELA",
                "applicability": "not_applicable",
                "plain_language_conclusion": "SELA is not the dominant method here.",
                "exit_reason": "The active issue is clinical governance, not system efficiency tradeoff.",
                "transfer_to": "WAE",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("method exit accepted", result.stdout)
        self.assertIn("agentic audit remains required", result.stdout)

    def test_sela_skill_documents_fidelity_boundary(self):
        text = (REPO / "skills" / "sela" / "SKILL.md").read_text(encoding="utf-8")

        for phrase in (
            "fidelity contract",
            "Shape & Evidence Risk Report",
            "shape pass is not semantic approval",
            "scripts must not decide semantic truth",
        ):
            self.assertIn(phrase, text)

    def test_sela_judge_rubric_and_evaluation_packet_exist(self):
        rubric = (REPO / "skills" / "sela" / "rubrics" / "judge.md").read_text(
            encoding="utf-8"
        )
        packet = (REPO / "tests" / "sela" / "baseline_vs_constrained_evaluation.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "SELA Judge Rubric",
            "0-2",
            "D1 对比公平性审查",
            "D2 局部优势可规模化",
            "D3 系统效率趋势",
            "D4 边界豁免检查",
            "D5 时机动作分级",
            "D6 反驳题目预设",
            "form compliance is not enough",
            "do not score by preferred conclusion",
            "shape validation is not semantic judgment",
        ):
            self.assertIn(phrase, rubric)

        for phrase in (
            "SELA Baseline vs Constrained Evaluation Packet",
            "baseline prompt",
            "constrained prompt",
            "Case 1: soy sauce",
            "Case 2: software security review",
            "Case 3: adaptive tutoring",
            "failure example",
            "single-agent seed run",
            "does not claim cross-model robustness",
            "external measured seed",
        ):
            self.assertIn(phrase, packet)

        self.assertGreaterEqual(packet.count("Baseline score"), 3)
        self.assertGreaterEqual(packet.count("Constrained score"), 3)


if __name__ == "__main__":
    unittest.main()
