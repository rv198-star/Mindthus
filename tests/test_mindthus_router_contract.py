import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class MindthusRouterContractTests(unittest.TestCase):
    def test_using_mindthus_defines_premise_calibration_as_pre_route_action(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Premise Calibration", text)
        self.assertIn("前置校准", text)
        self.assertIn("不是独立方法论", text)
        self.assertIn("只帮助选择", text)
        self.assertIn("真实对象", text)
        self.assertIn("底层约束", text)
        self.assertIn("目标函数", text)

    def test_agents_mentions_premise_calibration_before_skill_selection(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("premise calibration", text)
        self.assertIn("二手概念", text)
        self.assertIn("真实对象", text)
        self.assertIn("底层约束", text)
        self.assertIn("目标函数", text)

    def test_pressure_tests_cover_premise_calibration_behavior(self):
        text = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "ROI Label Trap",
            "First-Principles Name Trap",
            "Workflow vs Agent False Binary",
            "Trend Slogan Trap",
            "Polished Artifact Trap",
            "second-hand concepts",
            "real object",
            "bottom constraints",
            "objective function",
            "not a standalone method",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
