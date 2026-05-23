import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EDSP = REPO / "skills" / "edsp"


class EdspContractTests(unittest.TestCase):
    def test_skill_exposes_single_agent_multi_role_challenge(self):
        text = (EDSP / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Multi-Role Challenge",
            "single-agent multi-role",
            "Builder",
            "Challenger",
            "Synthesizer",
            "separate agents are an escalation option, not the default",
            "do not run Scenario Projection",
        ):
            self.assertIn(phrase, text)

    def test_methodology_protects_l1_with_builder_challenger_synthesizer(self):
        text = (EDSP / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "L1 Multi-Role Challenge",
            "Builder",
            "Challenger",
            "Synthesizer",
            "wrong coordinate system",
            "missed decisive variable",
            "if the Challenger finds a broken skeleton",
            "rebuild L1 rather than continue to L2",
            "Do not default to separate agents",
        ):
            self.assertIn(phrase, text)

    def test_public_methodology_mentions_multi_role_not_multi_agent_default(self):
        text = (REPO / "docs" / "methodologies" / "edsp.md").read_text(encoding="utf-8")
        for phrase in (
            "单 Agent 多角色",
            "Builder",
            "Challenger",
            "Synthesizer",
            "默认不拆成多个 Agent",
            "真正高影响或长期方向判断",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
