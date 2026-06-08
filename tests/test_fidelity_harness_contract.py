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


if __name__ == "__main__":
    unittest.main()
