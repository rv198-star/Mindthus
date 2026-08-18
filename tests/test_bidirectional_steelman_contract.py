import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PRIMITIVE = REPO / "docs" / "methodologies" / "primitives" / "bidirectional-steelman-convergence.md"
SHARED = REPO / "docs" / "methodologies" / "shared-primitives.md"
USING = REPO / "skills" / "using-mindthus" / "SKILL.md"
PRESSURE = REPO / "tests" / "bidirectional_steelman_pressure_tests.md"


class BidirectionalSteelmanContractTests(unittest.TestCase):
    def test_primitive_exposes_core_boundaries(self):
        text = PRIMITIVE.read_text(encoding="utf-8")
        for phrase in (
            "Bidirectional Steelman Convergence / 双向钢人收敛",
            "not a standalone method",
            "not a judgment owner",
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

    def test_shared_index_exposes_primitive_as_support_not_owner(self):
        text = SHARED.read_text(encoding="utf-8")
        self.assertIn("Bidirectional Steelman Convergence / 双向钢人收敛", text)
        self.assertIn("primitives/bidirectional-steelman-convergence.md", text)
        self.assertIn("最强竞争立场", text)

    def test_using_mindthus_keeps_trigger_conditional(self):
        text = USING.read_text(encoding="utf-8")
        for phrase in (
            "Bidirectional Steelman Convergence / 双向钢人收敛",
            "real competing-frame judgment",
            "same object",
            "same evidence ceiling",
            "ask at most one",
            "acquire evidence",
            "malformed binary",
            "does not become the judgment owner",
        ):
            self.assertIn(phrase, text)

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
