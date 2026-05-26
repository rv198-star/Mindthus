import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _parse_markdown_table_after(text: str, heading: str) -> dict[str, tuple[str, str]]:
    start = text.index(heading)
    lines = text[start:].splitlines()
    rows: dict[str, tuple[str, str]] = {}
    for line in lines:
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells == ["Signal", "Kernel", "Route"] or set(cells) == {"---"}:
            continue
        if len(cells) == 3:
            rows[cells[0]] = (cells[1], cells[2])
    return rows


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

    def test_using_mindthus_exposes_find_deepen_stop_kernel(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "LLM judgment stabilizer",
            "not a general task router",
            "Find the right judgment point",
            "Deepen the artifact where value is thin",
            "Stop when Mindthus is not needed",
            "shared primitives",
            "ordinary LLM execution is enough",
            "thin-value deepening",
        ):
            self.assertIn(phrase, text)

    def test_readme_exposes_kernel_and_shared_primitives_without_overrouting(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "Find the right judgment point",
            "Deepen the artifact where value is thin",
            "Stop when Mindthus is not needed",
            "不是通用任务入口",
            "共享原语",
            "docs/methodologies/shared-primitives.md",
            "docs/methodologies/threshold-casebook.md",
            "docs/maintenance/versioning-policy.md",
        ):
            self.assertIn(phrase, text)

    def test_using_mindthus_route_matrix_covers_expected_branches(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        rows = _parse_markdown_table_after(text, "### Route Matrix / 路由矩阵")
        self.assertEqual(
            rows,
            {
                "clear low-risk edit": ("Stop", "direct execution"),
                "unclear real problem": ("Find", "`3l5s`"),
                "long-term system efficiency vs local advantage": ("Find", "`sela`"),
                "false binary or unstable proposition": ("Find", "`edsp`"),
                "workflow/agent/evidence ownership conflict": ("Find", "`wae`"),
                "bounded artifact is complete-looking but thin": ("Deepen", "`tvg`"),
                "durable mission state or human-in-loop task runtime": ("Find", "`tplan`"),
                "third touch on same local object": ("Stop/Find", "Anti-Spiral"),
                "missing facts/domain/runtime/stakeholder input": (
                    "Stop",
                    "Evidence / Claim Ceiling",
                ),
                "single viewpoint is too self-consistent": (
                    "Find pressure",
                    "Perspective Pressure",
                ),
            },
        )

    def test_threshold_casebook_labels_expected_route_for_each_case(self):
        text = (REPO / "docs" / "methodologies" / "threshold-casebook.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Expected route: Stop -> direct execution",
            "Expected route: Find -> `sela` -> direction judgment, not commitment",
            "Expected route: Find -> `edsp` -> claim ceiling / evidence handoff",
            "Expected route: Find -> `wae` -> separate script order from truth judgment",
            "Expected route: Stop -> Evidence / Claim Ceiling -> block rather than deepen",
            "Expected route: Stop/Find -> Anti-Spiral -> return upstream",
            "Expected route: Find pressure -> Perspective Pressure -> choose synthetic roles or incentive check",
        ):
            self.assertIn(phrase, text)

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
