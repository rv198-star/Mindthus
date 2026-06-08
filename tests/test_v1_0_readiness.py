import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
JUDGE_RUNNER = REPO / "scripts" / "run-fidelity-judge.py"


def sela_applicable_output() -> dict:
    move = {
        "status": "addressed",
        "finding": "The output executes this SELA move with case-specific reasoning.",
        "failure_criteria_response": "The output names how this move could fail.",
        "evidence_surface": "Scenario facts and stated uncertainty.",
    }
    return {
        "schema_version": "sela-fidelity-v0.1",
        "method": "SELA",
        "applicability": "applicable",
        "plain_language_conclusion": "Use SELA for direction and stage the action.",
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


def sela_exit_output() -> dict:
    return {
        "schema_version": "sela-fidelity-v0.1",
        "method": "SELA",
        "applicability": "challenge_premise",
        "plain_language_conclusion": "The prompt tries to use SELA to skip safety authority.",
        "exit_reason": "Medical triage authority cannot be reduced to system efficiency.",
        "transfer_to": "WAE",
    }


def complete_sela_judge() -> dict:
    dimensions = {}
    for index in range(1, 7):
        dimensions[f"D{index}"] = {
            "score": 2,
            "rationale": f"D{index} was judged against the rubric with concrete evidence.",
            "evidence": f"D{index} evidence excerpt.",
        }
    return {
        "schema_version": "mindthus-fidelity-judge-v0.1",
        "method": "SELA",
        "judge_model": "fixture-judge",
        "rubric": "skills/sela/rubrics/judge.md",
        "dimensions": dimensions,
        "final_assessment": {
            "total_score": 12,
            "summary": "The artifact faithfully executed the SELA moves.",
            "form_compliance_not_enough": True,
        },
    }


def run_judge(output_payload: dict, judge_payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        output_path = Path(tmp) / "sela-output.json"
        judge_path = Path(tmp) / "judge.json"
        output_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        judge_path.write_text(json.dumps(judge_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(
            ["python3", str(JUDGE_RUNNER), "--output", str(output_path), "--judge", str(judge_path)],
            text=True,
            capture_output=True,
            cwd=REPO,
        )


class V10ReadinessTests(unittest.TestCase):
    def test_agpl_dual_license_surface_is_declared(self):
        license_text = (REPO / "LICENSE").read_text(encoding="utf-8")
        commercial_text = (REPO / "COMMERCIAL-LICENSE.md").read_text(encoding="utf-8")
        readme = (REPO / "README.md").read_text(encoding="utf-8")

        for phrase in (
            "GNU AFFERO GENERAL PUBLIC LICENSE",
            "Version 3, 19 November 2007",
            "TERMS AND CONDITIONS",
            "END OF TERMS AND CONDITIONS",
        ):
            self.assertIn(phrase, license_text)

        for phrase in (
            "AGPLv3",
            "commercial dual licensing",
            "closed-source commercial",
            "private SaaS",
            "commercial integration",
            "separate commercial license",
        ):
            self.assertIn(phrase, commercial_text)

        self.assertIn("AGPLv3 + commercial dual licensing", readme)
        self.assertIn("closed-source commercial use requires a separate commercial license", readme)

    def test_release_pack_carries_license_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", "scripts/build-release-pack.py", "--out", tmp, "--force"],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            root = Path(tmp)
            for platform_root in (
                root / "claude-code" / "claude-plugin",
                root / "codex",
                root / "opencode",
            ):
                self.assertTrue((platform_root / "LICENSE").is_file(), platform_root)
                self.assertTrue((platform_root / "COMMERCIAL-LICENSE.md").is_file(), platform_root)

    def test_sela_judge_rubric_reviews_method_exit_legitimacy(self):
        rubric = (REPO / "skills" / "sela" / "rubrics" / "judge.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "escape review",
            "not_applicable",
            "transfer",
            "challenge_premise",
            "the judge must review whether the exit itself is justified",
            "do not automatically pass a method exit",
        ):
            self.assertIn(phrase, rubric)

    def test_fidelity_judge_runner_accepts_complete_sela_judgment(self):
        result = run_judge(sela_applicable_output(), complete_sela_judge())

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Fidelity Judge Report", result.stdout)
        self.assertIn("Total score: 12 / 12", result.stdout)
        self.assertIn("judge automation does not validate strategic truth", result.stdout)

    def test_fidelity_judge_runner_blocks_unreviewed_method_exit(self):
        result = run_judge(sela_exit_output(), complete_sela_judge())

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("escape_review is required", result.stdout)
        self.assertIn("challenge_premise", result.stdout)

    def test_fidelity_judge_runner_accepts_reviewed_method_exit(self):
        judge_payload = complete_sela_judge()
        judge_payload["escape_review"] = {
            "applicability_exit": "challenge_premise",
            "is_exit_justified": True,
            "rationale": "The prompt asks SELA to override clinical safety authority.",
            "reviewer_action": "accept_exit",
        }

        result = run_judge(sela_exit_output(), judge_payload)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("escape review accepted: challenge_premise", result.stdout)

    def test_cross_model_baseline_records_second_model_scope(self):
        text = (REPO / "tests" / "sela" / "cross_model_baseline_2026-06-08.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "SELA Cross-Model Baseline",
            "model_count: 2",
            "baseline-vs-constrained",
            "Model A",
            "Model B",
            "opencode/deepseek-v4-flash-free",
            "stable across both measured models",
            "escape-review guardrail",
            "does not claim universal robustness",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
