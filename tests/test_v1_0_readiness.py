import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class V10ReadinessTests(unittest.TestCase):
    def test_v1_0_readiness_record_has_minimum_contract(self):
        text = (REPO / "tests" / "method_fidelity_v1_0_readiness_2026-06-08.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "# v1.0 Readiness Blocker Closure",
            "## Closed Items",
            "## Non-coverage",
            "does not claim universal robustness",
            "## Verification",
            "python3 -m unittest discover -s tests -v",
        ):
            self.assertIn(phrase, text)

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
