import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _parse_markdown_table_after(text: str, heading: str) -> dict[str, tuple[str, str]]:
    start = text.index(heading)
    rows: dict[str, tuple[str, str]] = {}
    for line in text[start:].splitlines():
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells == ["Primitive", "Primary owner", "Short rule"] or set(cells) == {"---"}:
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

    def test_router_defines_objective_priority_and_references_minimal_lens(self):
        for path in (REPO / "AGENTS.md", REPO / "skills" / "using-mindthus" / "SKILL.md"):
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "先尊重用户给出的目标函数",
                "若用户未给出",
                "默认效率优先",
                "最小充分镜头",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")

        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "能直接判断就不要开方法",
            "一个 skill 足够就不要串联",
            "轻量检查足够就不要展开完整流程",
        ):
            self.assertIn(phrase, primitives)

    def test_minimal_sufficient_lens_does_not_change_tplan_activation(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("### 最小充分镜头")
        end = text.index("### Skill 路由", start)
        section = text[start:end]
        self.assertNotIn("tplan", section.lower())

    def test_using_mindthus_defines_intervention_boundary_before_skill_choice(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Intervention Boundary / 介入边界",
            "Direct execution / 直接执行",
            "Information acquisition / 信息补全",
            "Mindthus intervention / Mindthus 介入",
            "do not use Mindthus",
            "facts, files, data, runtime proof, or user clarification",
            "hard judgment point",
        ):
            self.assertIn(phrase, text)

    def test_judgment_object_routing_precedes_individual_skill_routes(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("#### Judgment Object Routing / 判断对象路由")
        first_skill = text.index("#### `sela`", start)
        section = text[start:first_skill]
        for phrase in (
            "Problem-definition failure",
            "False binary or structural ambiguity",
            "Long-term system efficiency versus local advantage",
            "Control-boundary mismatch",
            "Bounded artifact with thin practical value",
            "Mission runtime state",
            "Repeated local repair",
        ):
            self.assertIn(phrase, section)

    def test_tvg_and_tplan_are_non_proactive_routes(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "TVG requires a bounded artifact",
            "tplan requires Mission-level runtime state",
            "do not proactively activate",
            "ordinary complexity is not enough",
        ):
            self.assertIn(phrase, text)

    def test_context_injection_point_is_interface_not_memory_implementation(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Context Injection Point / 上下文注入口",
            "does not implement memory",
            "storage, retrieval, ranking",
            "current user input takes priority",
            "must not silently override",
            "user_preference",
            "long_term_objective",
            "risk_posture",
            "authority_boundary",
        ):
            self.assertIn(phrase, text)

    def test_using_mindthus_defines_judgment_constraint_recognition(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Judgment Constraint Recognition / 判断约束识别",
            "Facts and evidence constrain factual claims",
            "Values and preferences constrain priorities",
            "Interests and incentives constrain stakeholder interpretation",
            "Emotional signals constrain attention",
            "Risk posture and reversibility constrain action strength",
            "Authority boundaries constrain who may decide",
            "do not let values or emotion assert factual claims",
        ):
            self.assertIn(phrase, text)

    def test_using_mindthus_defines_method_arbitration_actions(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Method Arbitration / 方法仲裁",
            "`dominate`",
            "`defer`",
            "`degrade`",
            "`block`",
            "`stop`",
            "TVG vs Anti-Spiral",
            "SELA vs WAE",
            "EDSP vs evidence",
            "3L5S vs direct execution",
        ):
            self.assertIn(phrase, text)

    def test_using_mindthus_requires_execution_impact(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Execution Impact / 执行影响",
            "strategy",
            "risk handling",
            "evidence requirement",
            "next action",
            "stopping condition",
            "method choice",
            "handoff packet",
            "If a judgment changes none of these",
        ):
            self.assertIn(phrase, text)

    def test_using_mindthus_consolidates_pressure_surfaces(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Pressure Surface Check / 施压面检查",
            "Pressure is not a standalone route",
            "low-risk deterministic",
            "Perspective Pressure handles single-view, incentive, or game-theoretic",
            "SELA and EDSP own role pressure",
            "TVG owns bounded-artifact value pressure",
            "Evidence / Claim Ceiling owns proof limits",
            "Anti-Spiral owns repeated local repair pressure",
            "owner, reason, and execution effect",
        ):
            self.assertIn(phrase, text)

    def test_shared_primitives_consolidates_pressure_without_new_method_layer(self):
        text = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Pressure Surface Consolidation / 施压面收束",
            "not a standalone method",
            "not a new route",
            "game-theoretic",
            "incentive",
            "low-risk deterministic",
        ):
            self.assertIn(phrase, text)

    def test_game_theory_is_not_a_standalone_skill(self):
        for name in ("game-theory", "game_theory", "gametheory"):
            self.assertFalse((REPO / "skills" / name).exists(), name)

    def test_agents_mentions_constraints_arbitration_and_execution_impact(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "判断约束",
            "事实 claim",
            "价值、利益、情绪",
            "方法冲突",
            "dominate / defer / degrade / block / stop",
            "执行影响",
        ):
            self.assertIn(phrase, text)

    def test_agents_mentions_entry_boundary_and_context_injection(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "介入边界",
            "直接执行",
            "先补事实",
            "Mindthus 介入",
            "上下文注入口",
            "当前用户输入优先",
        ):
            self.assertIn(phrase, text)

    def test_cognitive_primitives_are_referenced_not_reexpanded_in_router_surfaces(self):
        primitives_path = "docs/methodologies/shared-primitives.md"
        primitives = (REPO / primitives_path).read_text(encoding="utf-8")
        self.assertIn("Cognitive Primitives / 认知原语", primitives)
        self.assertIn("## Cognitive Primitive Index / 认知原语索引", primitives)
        self.assertIn("This is not a new method layer", primitives)
        for phrase in (
            "Minimal Sufficient Lens",
            "Evidence / Claim Ceiling",
            "Perspective Pressure",
            "Anti-Spiral",
            "No Abstract Jargon Wall",
        ):
            self.assertIn(phrase, primitives)

        for path in (REPO / "AGENTS.md", REPO / "skills" / "using-mindthus" / "SKILL.md"):
            text = path.read_text(encoding="utf-8")
            self.assertIn(primitives_path, text, f"{path} should link cognitive primitives")
            for copied_definition in (
                "每个抽象概念至少给出一种支撑",
                "Can this be answered directly?",
                "What evidence constrains this claim?",
                "Before method labels",
            ):
                self.assertNotIn(copied_definition, text, f"{path} copied primitive definition")

    def test_rework_does_not_restore_extra_document_layers(self):
        self.assertFalse((REPO / "docs" / "methodologies" / "threshold-casebook.md").exists())
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("### Route Matrix / 路由矩阵", text)

    def test_cognitive_primitive_index_has_stable_owner_and_rule_mapping(self):
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        rows = _parse_markdown_table_after(primitives, "## Cognitive Primitive Index / 认知原语索引")
        self.assertEqual(
            rows,
            {
                "Minimal Sufficient Lens": (
                    "`using-mindthus`",
                    "能直接判断就不要开方法；一个 skill 足够就不要串联；轻量检查足够就不要展开完整流程。",
                ),
                "Evidence / Claim Ceiling": (
                    "`WAE`",
                    "结论强度不能超过证据；缺事实、领域输入、运行证明或 stakeholder 判断时，降级或阻断。",
                ),
                "Perspective Pressure": (
                    "`SELA` / `EDSP`",
                    "单一视角过度自洽时，用角色压力或激励检查挑战判断。",
                ),
                "Anti-Spiral": (
                    "`anti-spiral-self-audit` / `tplan`",
                    "同一局部对象第三次、负反馈或加层冲动出现时，先停下回看上游。",
                ),
                "No Abstract Jargon Wall": (
                    "`AGENTS.md`",
                    "先用例子、类比或直接后果讲清楚，再使用 Mindthus 术语。",
                ),
            },
        )

    def test_skill_routing_surface_preserves_pre_refactor_route_triggers(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        expected_routes = {
            "sela": ("系统级费效比", "短视选择"),
            "3l5s": ("问题还不清楚", "Discovery -> Definition"),
            "tplan": ("durable task state", "human-in-loop authority"),
            "edsp": ("A/B 都像对", "Extreme Deduction"),
            "wae": ("Workflow / Agentic / Evidence", "控制权"),
            "tvg": ("结构完整但实质浅薄", "bounded artifact"),
        }
        for skill, phrases in expected_routes.items():
            self.assertIn(f"#### `{skill}`", using)
            for phrase in phrases:
                self.assertIn(phrase, using, f"{skill} route missing {phrase!r}")

    def test_cognitive_primitives_are_active_in_their_primary_owner_surfaces(self):
        surfaces = {
            "Minimal Sufficient Lens": (
                REPO / "skills" / "using-mindthus" / "SKILL.md",
                ("最小充分镜头", "shared-primitives.md", "不要为了形式"),
            ),
            "Evidence / Claim Ceiling": (
                REPO / "skills" / "wae" / "SKILL.md",
                ("Evidence should connect claims to observable proof", "confidence caps"),
            ),
            "Perspective Pressure / SELA": (
                REPO / "skills" / "sela" / "SKILL.md",
                ("Multi-Role Check", "System Advocate", "Local Defender", "Timing Auditor"),
            ),
            "Perspective Pressure / EDSP": (
                REPO / "skills" / "edsp" / "SKILL.md",
                ("Multi-Role Challenge", "Builder", "Challenger", "Synthesizer"),
            ),
            "Anti-Spiral / methodology": (
                REPO / "docs" / "methodologies" / "anti-spiral-self-audit.md",
                ("Third touch, stop first", "not an independent Mindthus skill"),
            ),
            "Anti-Spiral / tplan": (
                REPO / "skills" / "tplan" / "SKILL.md",
                ("Anti-Spiral Gate", "third touches", "local repair"),
            ),
            "No Abstract Jargon Wall": (
                REPO / "AGENTS.md",
                ("No Abstract Jargon Wall", "shared-primitives.md", "这对你意味着什么"),
            ),
        }
        for primitive, (path, phrases) in surfaces.items():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{primitive} inactive in {path}: {phrase!r}")

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

    def test_judgment_kernel_acceptance_run_records_live_effectiveness(self):
        text = (
            REPO / "tests" / "mindthus_judgment_kernel_acceptance_run_2026-05-26.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "Mindthus Judgment Kernel Live Acceptance Run",
            "Behavior score",
            "98 / 100",
            "Conservative effective score",
            "92 / 100",
            "current-only evaluation",
            "initially accepted",
            "not a clean old-vs-new A/B",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
