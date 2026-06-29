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

    def test_input_framing_audit_is_strong_entry_protocol_inside_using_mindthus(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")

        for phrase in (
            "Input Framing Audit / 输入定框审计",
            "强约束入口协议",
            "在进入判断之前，先检查当前问题是否已经被提问方式绑到错误层级",
            "true_question",
            "packed_premises",
            "layer_risks",
            "frame_status",
            "reframed_question",
            "routing_decision",
            "clean / biased / overloaded / malformed",
            "not keyword rules",
            "No frame-risk signal, no frame check",
            "When frame-risk exists",
            "internal result",
            "No execution impact, omit the frame check",
        ):
            self.assertIn(phrase, using)

        for phrase in (
            "Framing-risk signals, not keyword rules",
            "这些词只是高置信线索",
            "没有这些词时，只要出现打包结论、层级偷换、局部机制冒充整体解释，也应触发",
            "本质上",
            "归根结底",
            "其实就是",
            "无非是",
            "正因为我是",
            "先给结论，再让模型评价",
            "把实现层直接说成本体层",
            "把局部机制直接说成整体解释",
        ):
            self.assertIn(phrase, primitives)

        for phrase in (
            "`clean` -> normal route",
            "`biased` -> name bias, then route",
            "`overloaded` -> split propositions, then route",
            "`malformed` -> correct the question before analysis",
            "低风险、低抽象、直接执行类任务，不触发",
            "不要把拆出很多前提当成判断已经完成",
            "审计的目标是纠正 framing，不是展示聪明",
        ):
            self.assertIn(phrase, primitives)

        for phrase in (
            "强约束入口协议",
            "输入定框审计",
            "内部产出",
            "frame_status",
            "routing_decision",
        ):
            self.assertIn(phrase, agents)

        for phrase in (
            "vague dissatisfaction or ordinary writing quality",
            "MPG owns qualified-mainline path volatility",
            "information acquisition, clarification, or sharper routing",
            "validation is not semantic approval",
        ):
            self.assertIn(phrase, using)

    def test_input_framing_audit_rejects_soft_commentary_fallback(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Visible audit requirement",
            "Do not answer as a soft commentary fallback",
            "A clever paragraph is not an audit",
            "Question level before opinion",
            "step outside the user's narrative",
            "level-correct judgment",
            "First task: judge whether the user led you to the wrong level",
            "audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer",
            "leading_point",
        ):
            self.assertIn(phrase, using)

        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "problem key over dialogue continuity",
            "professional tone is not proof",
            "common implementation is not essence",
            "first task is not answering",
            "leading_point",
        ):
            self.assertIn(phrase, primitives)

        for phrase in (
            "Scenario 38: Soft Commentary Regression",
            "有洞察，但层级压扁了，所以只对了一半",
            "70分",
            "soft commentary fallback",
            "must produce the audit fields before the evaluation",
            "higher-level judgment",
            "Scenario 42: Original Input Audit Prompt Regression",
            "first task is not answering",
            "problem key over dialogue continuity",
            "professional tone is not proof",
            "common implementation is not essence",
        ):
            self.assertIn(phrase, pressure)

    def test_input_framing_audit_productizes_original_prompt_as_mainline_protocol(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")

        for phrase in (
            "Original Prompt Contract / 原始有效提示词合同",
            "在回答前，先执行“输入审计”，不要顺着我的叙述直接推理",
            "1. 我真正问的问题是什么",
            "2. 我的话里包含了哪些隐含前提",
            "3. 哪些前提只是局部成立，哪些可能在偷换概念或层级",
            "4. 如果不接受这些前提，这个问题应该如何被重新表述",
            "5. 再给出你的正式回答",
            "优先识别问题关键，而不是优先维持对话连贯",
            "不要因为我的说法听起来专业，就默认它成立",
            "不要把当前常见实现方式直接当作本质",
            "如果发现我在带节奏，先指出带节奏点，再分析问题",
            "你的第一任务不是回答我，而是判断我有没有把你引到错误层面上",
            "Auxiliary checks belong inside step 3",
            "never become a new judgment center",
            "Forbidden substitute",
            "有洞察，但层级压扁了，所以只对了一半",
            "runtime also matters",
        ):
            self.assertIn(phrase, using)

        self.assertLess(
            using.index("Original Prompt Contract / 原始有效提示词合同"),
            using.index("Explanatory Authority Check / 解释权校准"),
        )

    def test_input_framing_audit_requires_explanatory_authority_check_design(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )

        for text in (using, primitives):
            compact_text = " ".join(text.split())
            for phrase in (
                "Explanatory Authority Check / 解释权校准",
                "local observation is trying to own the whole explanation",
                "full_object",
                "local_frame_role",
                "authority_status",
                "global_owner",
                "downgraded_use",
                "owns_explanation",
                "contributes_locally",
                "misclaims_authority",
                "blocked_by_missing_evidence",
                "concrete higher-level explanatory frame or accountable decision object",
                "not a vague label",
                "observable judgment or action difference",
                "Dominant Carrier Check / 主导承载校准",
                "which part carries stable or repeatable outcomes",
                "target_result",
                "primary_result_bearer",
                "stability_basis",
                "carrier_status",
                "primary_carrier",
                "supporting_surface",
                "incidental_signal",
                "Do not stop at runtime-also-matters",
                "System Subject Check / 系统主体校准",
                "visible actor",
                "system_object",
                "governing_structure",
                "actor_role",
                "subject_status",
                "misassigned_subject",
                "skill/workflow answer must name system_object + primary_result_bearer",
                "prompt/runtime caveat is not enough",
                "local correctness is not explanatory authority",
            ):
                self.assertIn(phrase, compact_text)

        section_start = using.index("Explanatory Authority Check / 解释权校准")
        section_end = using.index("internal result", section_start)
        authority_section = using[section_start:section_end]
        self.assertNotIn("Script determinism check", authority_section)
        self.assertNotIn("carrier, activation, control, state", authority_section)
        self.assertNotIn("A/B", authority_section)

        pressure_compact = " ".join(pressure.split())
        for phrase in (
            "Scenario 39: Explanatory Authority Across Domains",
            "Technology reduction",
            "Release readiness reduction",
            "Product failure reduction",
            "asks who owns the whole explanation",
            "Does not accept vague global_owner labels",
            "observable difference in judgment, evidence, action, or stop condition",
            "Scenario 40: Dominant Carrier Across Domains",
            "asks what carries stable or repeatable outcomes",
            "does not reward runtime-also-matters caveats",
            "primary_result_bearer",
            "stability_basis",
            "Scenario 41: System Subject Inversion",
            "does not reward model-centered caveats",
            "system_object",
            "governing_structure",
            "misassigned_subject",
            "does not reward mechanism checklists",
            "does not reward same-level difference analysis",
        ):
            self.assertIn(phrase, pressure_compact)

    def test_input_framing_audit_requires_core_thesis_extraction(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )

        for text in (using, primitives):
            compact_text = " ".join(text.split())
            for phrase in (
                "Core Thesis Extraction / 主判断收束",
                "formal_answer must start with a one-sentence core thesis",
                "do not leave the main judgment scattered in supporting paragraphs",
                "local truth -> corrected owner/carrier -> practical consequence",
                "the strongest sentence must not be buried at the end",
                "core thesis must name the corrected owner/carrier",
                "generic A-but-B verdict is not enough",
                "Object Anchor / 对象锚定",
                "do not replace the asked object with its larger container",
                "keep asked object as subject in true_question/reframed_question/core thesis",
                "answer the component's positioning before the container's architecture",
                "Essence Wording Guard / 本质措辞护栏",
                "do not restate carrier/interface as essence",
                "corrected thesis must reject false essence claims",
                "Executable Substrate Check / 可执行基底校准",
                "operative subcomponents move work from generation into execution/verification",
                "surface steering is not the higher-level positioning",
                "Composite Object Integrity / 复合对象完整性",
                "do not strip operative subcomponents out of the asked object",
                "answer the assembled capability, not the leftover surface",
            ):
                self.assertIn(phrase, compact_text)

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
            "Agentic-system control-boundary mismatch",
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

    def test_wae_route_requires_agentic_system_domain_gate(self):
        skill = (REPO / "skills" / "wae" / "SKILL.md").read_text(encoding="utf-8")
        methodology = (REPO / "docs" / "methodologies" / "wae.md").read_text(
            encoding="utf-8"
        )
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")

        for text in (skill, methodology):
            for phrase in (
                "agentic-system control-boundary lens",
                "LLMs, agents, skills, prompts, scripts, schemas, workflows, review gates, or evidence gates",
                "Domain Gate",
                "No agentic system, no WAE",
                "No controller mismatch, no WAE",
            ):
                self.assertIn(phrase, text)

        for phrase in (
            "Agentic-system control-boundary mismatch -> `wae`",
            "Do not let `wae` absorb ordinary conceptual, organizational, product, or structural boundaries",
            "No agentic system, no WAE",
        ):
            self.assertIn(phrase, using)

        for phrase in (
            "agentic systems",
            "不是所有边界、责任、流程或证据问题的默认方法",
            "概念分类、组织责任、产品边界或结构判断",
        ):
            self.assertIn(phrase, agents)

    def test_wae_legacy_route_surfaces_are_agentic_scoped(self):
        paths = (
            REPO / "docs" / "superpowers" / "plans" / "2026-05-26-mindthus-judgment-kernel-entry-issues.md",
            REPO / "docs" / "superpowers" / "specs" / "2026-04-28-tplan-v0.1-design.md",
            REPO / "skills" / "mpg" / "resources" / "methodology.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("agentic-system", text.lower(), f"{path} should scope WAE")
            self.assertNotIn("Control-boundary mismatch", text, f"{path} keeps old WAE route")
            self.assertNotIn("- `WAE`: control-boundary lens", text, f"{path} keeps generic WAE wording")

    def test_tvg_exit_audit_is_internal_not_generic_external_audit(self):
        skill = (REPO / "skills" / "tvg" / "SKILL.md").read_text(encoding="utf-8")
        template = (REPO / "skills" / "tvg" / "resources" / "exit-audit-template.md").read_text(
            encoding="utf-8"
        )
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")

        for phrase in (
            "TVG audit is internal to the TVG loop",
            "not a standalone audit method",
            "No active TVG loop, no TVG audit",
            "No bounded artifact value-gain target, no TVG",
            "code, release, workflow, factual, method, strategy, or requirement-boundary audits",
        ):
            self.assertIn(phrase, skill)

        for phrase in (
            "TVG-loop exit audit",
            "must not be used as a generic audit template outside an active TVG run",
            "active TVG run",
        ):
            self.assertIn(phrase, template)

        for phrase in (
            "Do not route to `tvg` merely because the user asks for an audit, review, or check",
            "bounded artifact whose practical value is thin and whose expected value can be named",
            "No active TVG loop, no TVG audit",
        ):
            self.assertIn(phrase, using)

        for phrase in (
            "TVG 的 audit 是内部退出检查",
            "不是通用外部审计路线",
            "外部审计先按对象路由",
        ):
            self.assertIn(phrase, agents)

    def test_tplan_terminology_does_not_present_tvg_as_generic_audit_route(self):
        scoped_route_paths = (
            REPO / "skills" / "tplan" / "resources" / "hooks.md",
            REPO / "docs" / "superpowers" / "specs" / "2026-04-28-tplan-v0.1-design.md",
            REPO / "docs" / "superpowers" / "plans" / "2026-04-28-tplan-v0.1-implementation.md",
        )
        for path in scoped_route_paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("artifact_value_gain", text, f"{path} should use value-gain wording")
            self.assertIn("TVG value-gain exit check", text, f"{path} should scope TVG exit")
        hooks = (REPO / "skills" / "tplan" / "resources" / "hooks.md").read_text(
            encoding="utf-8"
        )
        schema = (REPO / "skills" / "tplan" / "resources" / "schema.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "`artifact_value_gain` is a decision hook, not a Mission Pulse `next_gate`",
            hooks,
        )
        self.assertIn(
            "TVG internal outcomes such as `deepen`, `return-remediate`, `block`, and `freeze` are",
            hooks,
        )
        self.assertIn(
            "Decision hook names such as `artifact_value_gain` are not Mission Pulse `next_gate`",
            schema,
        )
        self.assertIn(
            "not tplan `recommendation` enum values",
            schema,
        )

        no_legacy_depth_paths = scoped_route_paths + (
            REPO / "docs" / "superpowers" / "specs" / "2026-05-09-tplan-linear-continuation-gate-design.md",
            REPO / "tests" / "tplan" / "long_task_ab_tests.md",
        )
        for path in no_legacy_depth_paths:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("artifact depth", text, f"{path} keeps generic depth wording")
            self.assertNotIn("artifact-depth", text, f"{path} keeps generic depth wording")
            self.assertNotIn("depth-audit", text, f"{path} keeps generic audit wording")
            self.assertNotIn("depth_audit", text, f"{path} keeps generic audit hook")

    def test_using_mindthus_defines_low_frequency_method_wakeup_probes(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("#### Wake-Up Probes / 唤醒探针")
        end = text.index("#### Context Injection Point / 上下文注入口", start)
        section = text[start:end]
        for phrase in (
            "`SELA` wake-up",
            "`MPG` wake-up",
            "`EDSP` wake-up",
            "Do not route through `3l5s`",
            "Do not let `wae`",
            "Do not run `tvg`",
            "strategic, path-bearing, or structurally ambiguous",
        ):
            self.assertIn(phrase, section)

    def test_agents_prevents_3l5s_from_becoming_default_judgment_sink(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "3L5S 是默认问题内核，不是默认判断归宿",
            "结构歧义、战略系统/局部取舍、主线承载",
            "不要先绕回 3L5S",
            "直接唤醒 `EDSP`、`SELA` 或 `MPG`",
        ):
            self.assertIn(phrase, text)

    def test_router_pressure_tests_cover_low_frequency_wakeup_experiments(self):
        text = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Method Wake-Up Pressure Tests",
            "positive wake-up",
            "skip case",
            "Scenario 20: SELA Positive Wake-Up",
            "Scenario 21: SELA Skip",
            "Scenario 22: MPG Positive Wake-Up",
            "Scenario 23: MPG Skip",
            "Scenario 24: EDSP Positive Wake-Up",
            "Scenario 25: EDSP Skip",
            "`3L5S` default sink",
        ):
            self.assertIn(phrase, text)

    def test_router_pressure_tests_cover_wae_and_tvg_boundary_bugs(self):
        text = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "WAE And TVG Boundary Bug Pressure Tests",
            "Scenario 26: WAE Positive Agentic-System Control Mismatch",
            "Scenario 27: WAE Skip Non-Agentic Boundary",
            "Scenario 27B: WAE Skip Correct Agentic Control Assignment",
            "Scenario 28: TVG Positive Internal Exit Audit",
            "Scenario 29: TVG Skip External Release Audit",
            "Scenario 30: TVG Skip Code Audit",
            "Scenario 31: TVG Skip External Audit Object Matrix",
            "No agentic system, no WAE",
            "No controller mismatch, no WAE",
            "No active TVG loop, no TVG audit",
            "factual verification",
            "method correctness",
            "requirement boundaries",
            "Mission runtime continuation",
            "generic document review",
            "generic external audit route",
        ):
            self.assertIn(phrase, text)

    def test_router_wakeup_ab_experiment_design_defines_significance_protocol(self):
        text = (REPO / "tests" / "router_wakeup_ab_experiment_design.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Router Wake-Up A/B Experiment Design",
            "Primary endpoint",
            "positive wake-up recall",
            "skip precision",
            "execution impact",
            "Scenario 20-25",
            "holdout",
            "blind",
            "McNemar",
            "non-inferiority",
            "minimum success threshold",
            "effect size",
            "statistically significant",
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

    def test_approximate_quantified_mapping_is_a_cognitive_primitive_not_route(self):
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")

        for phrase in (
            "Approximate Quantified Mapping",
            "非精准量化显影",
            "数字是假设",
            "关系才是重点",
            "variables, directions, dominant terms, sensitivity points, and definition gaps",
            "not a standalone method",
            "not a new route",
        ):
            self.assertIn(phrase, primitives)

        for text in (using, agents):
            for phrase in (
                "Approximate Quantified Mapping",
                "非精准量化显影",
                "hypothetical numbers",
                "not factual measurements",
                "do not compute decisions",
            ):
                self.assertIn(phrase, text)

        start = using.index("#### Judgment Object Routing / 判断对象路由")
        end = using.index("#### Context Injection Point / 上下文注入口", start)
        routing_table = using[start:end]
        self.assertNotIn("Approximate Quantified Mapping", routing_table)
        self.assertNotIn("非精准量化显影", routing_table)

    def test_game_theory_is_not_a_standalone_skill(self):
        for name in ("game-theory", "game_theory", "gametheory"):
            self.assertFalse((REPO / "skills" / name).exists(), name)

    def test_approximate_quantified_mapping_is_not_a_standalone_skill(self):
        for name in ("qdm", "gsm", "approximate-quantified-mapping"):
            self.assertFalse((REPO / "skills" / name).exists(), name)

    def test_pressure_tests_cover_approximate_quantified_mapping_effect_cases(self):
        text = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "Approximate Quantified Mapping Pressure Tests",
            "Scenario 13: Youth Opportunity Compression",
            "Scenario 14: Digit Litigation Stop Condition",
            "Scenario 15: Qualitative Residual Handoff",
            "Expected baseline failure",
            "Expected treatment behavior",
            "hypothetical numbers",
            "数字是假设，关系才是重点",
            "variables, directions, dominant terms, sensitivity points, and definition gaps",
            "do not defend exact digits",
            "qualitative residual",
            "not a standalone skill",
            "not a decision calculator",
        ):
            self.assertIn(phrase, text)

    def test_approximate_quantified_mapping_can_support_but_not_own_judgment(self):
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "can support judgment formation",
            "must not own the judgment",
            "SELA, EDSP, 3L5S, WAE, TVG, or tplan keeps judgment ownership",
            "clarity aid inside an existing judgment owner",
        ):
            self.assertIn(phrase, primitives)

        for phrase in (
            "can be used inside an existing judgment owner",
            "active method keeps decision authority",
            "does not become the judgment owner",
        ):
            self.assertIn(phrase, using)

    def test_approximate_quantified_mapping_has_anti_overuse_threshold(self):
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Use it only when the game relationship is complex enough",
            "multi-variable",
            "口径 conflict",
            "felt outcome flips",
            "Skip it for simple, single-variable, low-stakes, or directly explainable claims",
        ):
            self.assertIn(phrase, primitives)

        for phrase in (
            "Use it only when the relationship is complex enough",
            "skip it for simple adjectives",
            "plain language is enough",
        ):
            self.assertIn(phrase, using)

        for phrase in (
            "Scenario 16: Simple Claim Skips Mapping",
            "Scenario 17: Single-Variable Cost Comparison Skips Mapping",
            "Scenario 18: Missing Evidence Blocks Mapping",
            "Scenario 19: True Multi-Variable Game Triggers Mapping",
            "Expected treatment behavior",
            "skips Approximate Quantified Mapping",
            "single-variable",
            "chooses information acquisition",
            "triggers Approximate Quantified Mapping",
            "plain-language explanation",
            "no hypothetical numbers",
        ):
            self.assertIn(phrase, pressure)

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
            "Approximate Quantified Mapping",
            "非精准量化显影",
            "Frame Fitness Check",
            "定框适配检查",
            "Gate Probes",
            "Failure Smells",
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
                    "先做表达定位：我代表什么立场、文字直接服务谁、要把对方带到哪里；先用例子、类比或直接后果讲清楚，再使用 Mindthus 术语。",
                ),
                "Approximate Quantified Mapping / 非精准量化显影": (
                    "`AGENTS.md` / `using-mindthus`",
                    "数字是假设，关系才是重点；用假设数字显影变量、方向、主导项、敏感项和口径差，不用数字证明或计算结论。",
                ),
                "Frame Fitness Check / 定框适配检查": (
                    "`using-mindthus` / `shared-primitives`",
                    "当局部框架可能接管全局判断时，先判断应保留、限定、重构还是因证据不足阻断。",
                ),
                "Gate Probes / 冻结前定位自省": (
                    "`AGENTS.md` / `shared-primitives`",
                    "交付、冻结、继续、转交或停止前，确认当前产物是什么、现在处于什么状态、接下来服务谁的什么行动。",
                ),
                "Failure Smells / 误用信号": (
                    "`shared-primitives` / 各方法",
                    "看见“像完成但没推进”的信号时先自审；普通信号触发返修或降级，硬边界触发 block / stop。",
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
            "Frame Fitness Check": (
                REPO / "skills" / "using-mindthus" / "SKILL.md",
                (
                    "Frame Fitness Check",
                    "local frame",
                    "preserve frame",
                    "qualify frame",
                    "reframe",
                    "block pending evidence",
                    "SELA",
                ),
            ),
        }
        for primitive, (path, phrases) in surfaces.items():
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{primitive} inactive in {path}: {phrase!r}")

    def test_frame_fitness_check_prevents_local_frame_capture_without_contrarianism(self):
        primitives = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Frame Fitness Check / 定框适配检查",
            "not a new route",
            "local frame",
            "preserve frame",
            "qualify frame",
            "reframe",
            "block pending evidence",
            "No frame-risk signal, no frame check",
            "No evidence, no superior frame claim",
            "No user-value erasure",
            "如果表述本身在错误层级上，先纠正问题层级，再回答",
            "不要因为某个说法在实现层成立，就默认它在定义层也成立",
        ):
            self.assertIn(phrase, primitives)

        for phrase in (
            "Frame Fitness Check / 定框适配检查",
            "local-frame capture",
            "locally true",
            "global judgment",
            "preserve frame",
            "qualify frame",
            "reframe",
            "block pending evidence",
            "can wake `sela`",
            "does not require a full SELA run",
            "wrong level",
            "implementation-layer truth",
            "definition-layer truth",
        ):
            self.assertIn(phrase, using)

        for phrase in (
            "局部框架",
            "全局判断",
            "不是为了唱反调",
            "用户价值、偏好、审美、风险姿态",
            "不能被当作偏见抹掉",
            "如果表述本身在错误层级上，先纠正问题层级，再回答",
            "不要因为某个说法在实现层成立，就默认它在定义层也成立",
        ):
            self.assertIn(phrase, agents)

        for phrase in (
            "Frame Fitness / Local-Frame Capture Pressure Tests",
            "Scenario 32: Skills-As-Prompt Local Frame Capture",
            "Scenario 33: Test Signal Becomes Release Readiness",
            "Scenario 34: Method Route Becomes Whole Judgment",
            "Scenario 35: Legitimate User Preference Skip",
            "Scenario 36: Repeated Local Frame Pressure",
            "local-frame capture",
            "globally misdirected",
            "preserves user preference",
            "Wrong-Level Statement Audit",
            "corrects the question level before answering",
            "implementation-layer truth",
            "definition-layer truth",
            "Scenario 37: Strong Entry Protocol For Packed Premises",
            "true_question",
            "packed_premises",
            "layer_risks",
            "frame_status",
            "routing_decision",
            "malformed",
        ):
            self.assertIn(phrase, pressure)

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
