import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PRESSURE_TESTS = REPO / "tests" / "multi_role_ab_pressure_tests.md"
RUN_RECORD = REPO / "tests" / "multi_role_ab_run_2026-05-23.md"


class MultiRoleAbContractTests(unittest.TestCase):
    def test_pressure_tests_cover_positive_and_no_negative_scenarios(self):
        text = PRESSURE_TESTS.read_text(encoding="utf-8")
        for phrase in (
            "SELA / EDSP Multi-Role A/B Pressure Tests",
            "Scenario 1: EDSP Validation Control Boundary",
            "Scenario 2: EDSP Low-Risk Deterministic Formatting",
            "Scenario 3: SELA SaaS Onboarding Replacement",
            "Scenario 4: SELA Low-Risk Internal Digest",
            "Scenario 5: SELA AI PR Review Default At The Threshold",
            "Non-trivial judgments gain useful pressure",
            "Lightweight cases do not pay unnecessary overhead",
            "multi_role_used=false",
            "Treatment passes at 6 or higher",
        ):
            self.assertIn(phrase, text)

    def test_pressure_tests_define_expected_no_overhead_boundaries(self):
        text = PRESSURE_TESTS.read_text(encoding="utf-8")
        for phrase in (
            "Avoids agent review for purely mechanical checks",
            "Avoids adding heavyweight process as a default",
            "agentic review adds cost or variance without decision value",
            "Does not recommend immediate full replacement",
            "does not preserve a heavy manual review loop",
            "keeps review overhead far below the saved 6 hours/week",
        ):
            self.assertIn(phrase, text)

    def test_run_record_captures_incremental_positive_gain_and_limited_claim(self):
        text = RUN_RECORD.read_text(encoding="utf-8")
        for phrase in (
            "SELA / EDSP Multi-Role A/B Run Record",
            "Separate agents remain an escalation option, not the default",
            "Observed positive gain",
            "Observed negative gain",
            "No overhead regression",
            "positive incremental value",
            "No negative behavior was observed in this run",
            "The positive gain is incremental, not dramatic",
            "The \"no negative\" claim is limited to these four scenarios",
            "Scenario 5: SELA AI PR Review Default At The Threshold",
            "genuine threshold scenario",
            "no-negative condition clearly",
        ):
            self.assertIn(phrase, text)

    def test_run_record_confirms_low_risk_cases_skip_multi_role(self):
        text = RUN_RECORD.read_text(encoding="utf-8")
        for phrase in (
            "`multi_role_used=false`; recommended deterministic script validation",
            "`multi_role_used=false`; action `commit`; no heavy manual review loop",
            "It did not add Builder/Challenger/Synthesizer ceremony",
            "It kept review cost below the saved 6 hours/week",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
