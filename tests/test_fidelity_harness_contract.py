import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class FidelityHarnessContractTests(unittest.TestCase):
    def test_internal_design_defines_v0_9_boundaries(self):
        text = (REPO / "docs" / "internal" / "method-fidelity-harness.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Method Fidelity Harness",
            "v0.9",
            "Pre-1.0",
            "约束关键判断动作，不约束判断结论",
            "control faithful execution, not agent judgment freedom",
            "required judgment moves",
            "shape validation",
            "semantic judgment",
            "scripts must not decide semantic truth",
            "Shape & Evidence Risk Report",
            "not_applicable",
            "transfer",
            "challenge premise",
            "SELA pilot",
            "MPG second-method pilot",
            "core extraction",
            "先 B 后 A",
            "tplan",
            "3L5S",
            "TVG",
        ):
            self.assertIn(phrase, text)

    def test_internal_design_blocks_semantic_verdicts(self):
        text = (REPO / "docs" / "internal" / "method-fidelity-harness.md").read_text(
            encoding="utf-8"
        )

        for forbidden in (
            "validator decides the strategy",
            "script-approved conclusion",
            "semantic PASS",
        ):
            self.assertNotIn(forbidden, text)

        for phrase in (
            "shape pass is not semantic approval",
            "review risk, not truth validation",
            "must allow the agent to reject the method",
        ):
            self.assertIn(phrase, text)

    def test_sela_fidelity_casebook_defines_reproducible_baseline(self):
        text = (REPO / "tests" / "sela" / "fidelity_casebook.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("SELA Fidelity Casebook", text)
        self.assertGreaterEqual(text.count("### Case"), 5)

        for phrase in (
            "baseline prompt",
            "constrained prompt",
            "trap map",
            "expected faithful judgment moves",
            "score faithful execution and reasoning quality, not the maintainer's preferred conclusion",
            "best-A vs average-B",
            "long-term trend != immediate cutover",
            "hard boundary",
            "local advantage scalability",
            "timing action posture",
            "misuse challenge",
            "soy sauce",
            "software security review",
            "adaptive tutoring",
            "local journalism",
            "medical triage",
        ):
            self.assertIn(phrase, text)

    def test_shared_shape_evidence_report_contract_is_defined(self):
        text = (REPO / "docs" / "internal" / "shape-evidence-risk-report.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Shape & Evidence Risk Report",
            "review risk, not truth validation",
            "method",
            "artifact path",
            "input source",
            "mode",
            "findings",
            "severity",
            "info / warn / risk / block",
            "code",
            "message",
            "affected judgment move",
            "evidence surface",
            "agentic audit remains required",
            "shape pass is not semantic approval",
            "validator must not output a semantic verdict",
            "tplan",
            "3L5S",
            "TVG",
            "SELA",
            "MPG",
        ):
            self.assertIn(phrase, text)

    def test_remaining_method_surfaces_have_fidelity_contracts(self):
        for skill_name in ("3l5s", "edsp", "wae", "tvg", "using-mindthus"):
            path = REPO / "skills" / skill_name / "resources" / "fidelity-contract.md"
            text = path.read_text(encoding="utf-8")

            for phrase in (
                "Fidelity Contract",
                "required judgment moves",
                "not_applicable",
                "transfer",
                "challenge premise",
                "shape pass is not semantic approval",
                "scripts must not decide semantic truth",
            ):
                self.assertIn(phrase, text, f"{skill_name}: {phrase}")

            skill = (REPO / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("resources/fidelity-contract.md", skill, skill_name)


if __name__ == "__main__":
    unittest.main()
