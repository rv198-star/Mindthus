import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CANDIDATE = REPO / "docs" / "internal" / "research" / "bidirectional-steelman-convergence.md"
SHARED = REPO / "docs" / "methodologies" / "shared-primitives.md"
USING = REPO / "skills" / "using-mindthus" / "SKILL.md"
PRESSURE = REPO / "tests" / "bidirectional_steelman_pressure_tests.md"


class BidirectionalSteelmanContractTests(unittest.TestCase):
    def test_candidate_exposes_simplified_clite_boundaries(self):
        text = CANDIDATE.read_text(encoding="utf-8")
        for phrase in (
            "Status: experimental **C-lite** research candidate",
            "Bidirectional Steelman Convergence / 双向钢人收敛",
            "not a standalone method",
            "Competitive Steelman / 竞争框架钢人",
            "Decisive Discriminator / 决定性判别变量",
            "same judgment object",
            "same Evidence / Claim Ceiling",
            "Do not force symmetry after evidence becomes asymmetric",
            "There is no mandatory question",
            "direct/deterministic/preference task -> stay asleep",
            "Return To Stable Owner",
            "P2 Treatment Contract",
            "The retired larger C adaptation",
        ):
            self.assertIn(phrase, text)

        for retired_marker in (
            "### 1. Steelman A",
            "### 2. Steelman B",
            "### 4. One Information-Gain Move",
        ):
            self.assertNotIn(retired_marker, text)

    def test_candidate_is_not_promoted_to_stable_surfaces_before_behavior_evidence(self):
        shared = SHARED.read_text(encoding="utf-8")
        using = USING.read_text(encoding="utf-8")
        for text in (shared, using):
            self.assertNotIn("Bidirectional Steelman Convergence / 双向钢人收敛", text)
            self.assertNotIn("Competitive Steelman / 竞争框架钢人", text)
            self.assertNotIn("Decisive Discriminator / 决定性判别变量", text)
        self.assertIn("Pressure Surface Check / 施压面检查", using)
        self.assertIn("pressure is not a route", using)
        self.assertIn("assign its owner", using)

    def test_preregistered_pressure_surface_targets_clite_p2(self):
        text = PRESSURE.read_text(encoding="utf-8")
        for phrase in (
            "A / current Mindthus",
            "B / source protocol",
            "C / C-lite Mindthus adaptation",
            "Competitive Steelman / 竞争框架钢人",
            "Decisive Discriminator / 决定性判别变量",
            "SKILLS / Prompt Carrier Multi-turn",
            "27-inch 4K / 5K / BetterDisplay",
            "Malformed Binary Escape",
            "One User-owned Variable Missing",
            "Decisive Variable Is Externally Verifiable",
            "Negative Controls",
            "C-lite should be rejected",
            "Contaminated-session P0/P1/C-lite runs are protocol-debug evidence only",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
