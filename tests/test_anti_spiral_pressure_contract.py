import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PRESSURE_TESTS = REPO / "tests" / "anti_spiral_pressure_tests.md"


class AntiSpiralPressureContractTests(unittest.TestCase):
    def test_pressure_tests_cover_activation_and_exit_capabilities(self):
        text = PRESSURE_TESTS.read_text(encoding="utf-8")
        for phrase in (
            "Capability Target",
            "trigger the Anti-Spiral mechanism",
            "exit the spiral",
            "A / baseline",
            "B / treatment",
            "third touch",
            "nearest stable state",
            "mechanical check",
            "upstream cause",
            "subtraction or equal replacement",
        ):
            self.assertIn(phrase, text)

    def test_pressure_tests_cover_distinct_spiral_scenarios(self):
        text = PRESSURE_TESTS.read_text(encoding="utf-8")
        for phrase in (
            "Scenario 1: Third-Touch Prompt Tuning",
            "Scenario 2: Negative Feedback And Additive Fallback",
            "Scenario 3: Probabilistic Self-Scoring Loop",
            "Scenario 4: Downstream Patch Instead Of Upstream Cause",
            "Scenario 5: tplan Weak Evidence Delta",
        ):
            self.assertIn(phrase, text)

    def test_scoring_rewards_both_triggering_and_escape(self):
        text = PRESSURE_TESTS.read_text(encoding="utf-8")
        for phrase in (
            "Activation score",
            "Exit score",
            "Hard failure",
            "continues same-path tuning",
            "adds a fallback layer",
            "uses LLM self-score as the continuation controller",
            "does not restate the root problem",
            "does not identify a stable state",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
