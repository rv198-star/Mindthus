import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANDIDATE = REPO / "docs" / "internal" / "research" / "bidirectional-steelman-convergence.md"
SHARED = REPO / "docs" / "methodologies" / "shared-primitives.md"
USING = REPO / "skills" / "using-mindthus" / "SKILL.md"
PRESSURE = REPO / "tests" / "bidirectional_steelman_pressure_tests.md"


class BidirectionalSteelmanContractTests(unittest.TestCase):
    def test_candidate_exposes_core_boundaries(self):
        text = CANDIDATE.read_text(encoding="utf-8")
        for phrase in (
            "Status: experimental research candidate",
            "Bidirectional Steelman Convergence / 双向钢人收敛",
            "not a standalone method",
            "The active judgment owner remains",
            "Lock Before Steelman",
            "Steelman A",
            "Steelman B",
            "Decisive Discriminator",
            "One Information-Gain Move",
            "One question` is an upper bound",
            "third-frame escape",
            "No frame lock, no steelman pass",
            "Do not force symmetry after the evidence becomes asymmetric",
            "source bidirectional-steelman protocol",
        ):
            self.assertIn(phrase, text)

    def test_candidate_is_not_promoted_to_stable_surfaces_before_behavior_evidence(self):
        shared = SHARED.read_text(encoding="utf-8")
        using = USING.read_text(encoding="utf-8")
        for text in (shared, using):
            self.assertNotIn("Bidirectional Steelman Convergence / 双向钢人收敛", text)
        self.assertIn("Pressure Surface Check / 施压面检查", using)
        self.assertIn("pressure is not a route", using)
        self.assertIn("assign its owner", using)

    def test_preregistered_pressure_surface_is_present(self):
        text = PRESSURE.read_text(encoding="utf-8")
        for phrase in (
            "A / current Mindthus",
            "B / source protocol",
            "C / Mindthus adaptation",
            "SKILLS / Prompt Carrier Multi-turn",
            "27-inch 4K / 5K / BetterDisplay",
            "Malformed Binary Escape",
            "One User-owned Variable Missing",
            "Decisive Variable Is Externally Verifiable",
            "Negative Controls",
            "C should be rejected or simplified if B performs as well or better",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
