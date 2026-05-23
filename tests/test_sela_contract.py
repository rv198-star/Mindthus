import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SELA = REPO / "skills" / "sela"


class SelaContractTests(unittest.TestCase):
    def test_skill_exposes_lightweight_timing_check(self):
        text = (SELA / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Timing Check",
            "时机检查",
            "临时保留",
            "锁死未来",
            "行动窗口",
            "not a new top-level principle",
        ):
            self.assertIn(phrase, text)

    def test_skill_exposes_single_agent_multi_role_sela(self):
        text = (SELA / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Multi-Role Check",
            "single-agent multi-role",
            "System Advocate",
            "Local Defender",
            "Timing Auditor",
            "separate agents are an escalation option, not the default",
            "efficiency judgment into an immediate action",
        ):
            self.assertIn(phrase, text)

    def test_methodology_keeps_timing_check_lightweight(self):
        text = (SELA / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "时机检查",
            "不是独立原则",
            "不是补一套人文价值观",
            "临时保留",
            "锁死未来",
            "行动窗口",
        ):
            self.assertIn(phrase, text)

    def test_methodology_adds_role_pressure_without_efficiency_dogma(self):
        text = (SELA / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "单 Agent 多角色",
            "System Advocate",
            "Local Defender",
            "Timing Auditor",
            "效率至上主义",
            "commit / trial / hold / wait",
            "不默认拆成多个 Agent",
        ):
            self.assertIn(phrase, text)

    def test_public_methodology_mentions_three_role_pressure(self):
        text = (REPO / "docs" / "methodologies" / "sela.md").read_text(encoding="utf-8")
        for phrase in (
            "单 Agent 多角色",
            "System Advocate",
            "Local Defender",
            "Timing Auditor",
            "默认不拆成多个 Agent",
            "长期方向正确",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
