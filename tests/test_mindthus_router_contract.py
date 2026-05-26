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

    def test_anti_spiral_is_activatable_without_becoming_a_skill(self):
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        methodology = (REPO / "docs" / "methodologies" / "anti-spiral-self-audit.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("反螺旋入口", using)
        self.assertIn("同一局部对象第三次", agents)
        self.assertIn("not an independent Mindthus skill", methodology)
        self.assertIn("Third touch, stop first", methodology)

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

    def test_router_defines_objective_priority_and_minimal_sufficient_lens(self):
        for path in (REPO / "AGENTS.md", REPO / "skills" / "using-mindthus" / "SKILL.md"):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "先尊重用户给出的目标函数",
                "若用户未给出",
                "默认效率优先",
                "最小充分镜头",
                "能直接判断就不要开方法",
                "一个 skill 足够就不要串联",
                "轻量检查足够就不要展开完整流程",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

    def test_minimal_sufficient_lens_does_not_change_tplan_activation(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("### 最小充分镜头")
        end = text.index("### Skill 路由", start)
        section = text[start:end]
        self.assertNotIn("tplan", section.lower())

    def test_pressure_tests_measure_outcome_effectiveness(self):
        text = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "Outcome Effectiveness",
            "真实效果指标",
            "faster real-object identification",
            "fewer invalid method calls",
            "less local-loop drift",
            "faster defensible choice",
            "knows where to stop under uncertainty",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
