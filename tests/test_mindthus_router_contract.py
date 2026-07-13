import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _read_shared_primitive_docs() -> str:
    """Return the split primitive contract: compact index plus detail files."""
    methodologies = REPO / "docs" / "methodologies"
    parts = [(methodologies / "shared-primitives.md").read_text(encoding="utf-8")]
    primitives_dir = methodologies / "primitives"
    if primitives_dir.exists():
        parts.extend(path.read_text(encoding="utf-8") for path in sorted(primitives_dir.glob("*.md")))
    return "\n".join(parts)


def _skill_description(skill_name: str) -> str:
    text = (REPO / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
    _, frontmatter, _ = text.split("---", 2)
    for line in frontmatter.splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"')
    raise AssertionError(f"{skill_name} missing description")


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


def _states_truth_over_agreement(text: str) -> bool:
    compact = " ".join(text.split())
    return (
        "pursue facts and truth over agreement" in compact
        or ("追求事实" in compact and "迎合" in compact)
    )


def _mentions_conflict_pair(text: str, left: str, right: str) -> bool:
    compact = " ".join(text.replace("-", " ").split()).lower()
    return left.lower() in compact and right.lower() in compact


class MindthusRouterContractTests(unittest.TestCase):
    def test_skill_discovery_descriptions_route_strategic_path_questions_through_router(self):
        using_desc = _skill_description("using-mindthus")
        sela_desc = _skill_description("sela")
        mpg_desc = _skill_description("mpg")

        for phrase in (
            "any Mindthus judgment lens",
            "strategic/path/control/framing ambiguity",
            "before choosing SELA, MPG, EDSP, WAE, TVG, 3L5S, or tplan",
            "Entry Triage hard-judgment cues",
            "whole-object reduction",
            "forced structural binary",
            "repeated local repair",
            "no-data numeric comparison",
        ):
            self.assertIn(phrase, using_desc)

        for phrase in (
            "system-efficiency versus local-advantage",
            "external system efficiency vs local/internal advantage",
            "when concrete carrier/exposure/path action is also present",
            "support lens with MPG rather than sole owner",
        ):
            self.assertIn(phrase, sela_desc)
        self.assertNotIn(
            "not when a concrete carrier, exposure, path, or commitment is the action question",
            sela_desc,
        )

        for phrase in (
            "concrete carrier",
            "continue/commit/hold/exit/switch decision",
            "path volatility, costs, delays, fragility, or counter-forces",
        ):
            self.assertIn(phrase, mpg_desc)

    def test_mindthus_states_truth_orientation_as_core_principle(self):
        surfaces = (
            REPO / "README.md",
            REPO / "AGENTS.md",
            REPO / "skills" / "using-mindthus" / "SKILL.md",
        )
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            for phrase in (
                "Truth Orientation / 真相优先",
                "user input is signal, constraint, or hypothesis; not evidence by itself",
            ):
                self.assertIn(phrase, text, f"{path} missing {phrase!r}")
            self.assertTrue(
                _states_truth_over_agreement(text),
                f"{path} must state the truth-over-agreement principle",
            )

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
        primitives = _read_shared_primitive_docs()
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
            "No execution impact:omit frame check",
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
            "Audit discipline",
            "audit hidden",
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

        primitives = _read_shared_primitive_docs()
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
        primitives = _read_shared_primitive_docs()

        for phrase in (
            "description: Use when any Mindthus judgment lens may apply",
            "General frame rule / 通用定框规则",
            "any locally true frame",
            "agent inference, method routing, tests, metrics, artifacts, or implementation details",
            "must earn global explanatory authority before it can define the whole object",
            "Original Prompt Contract / 原始有效提示词合同",
            "legacy prompt template",
            "not the judgment center",
            "AOP Aspect Activation / 切面唤起",
            "before-route",
            "before-answer",
            "Auxiliary checks belong inside step 3",
            "never become a new judgment center",
            "Forbidden substitute",
            "fluent half-right verdict",
            "runtime-only caveat",
            "score-as-concession",
        ):
            self.assertIn(phrase, using)

        for phrase in (
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
        ):
            self.assertIn(phrase, primitives)

    def test_input_framing_audit_requires_explanatory_authority_check_design(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = _read_shared_primitive_docs()
        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )

        using_compact = " ".join(using.split())
        primitives_compact = " ".join(primitives.split())
        for phrase in (
            "Explanatory Authority Check / 解释权校准",
            "full_object",
            "local_frame_role",
            "authority_status",
            "global_owner",
            "downgraded_use",
            "owns_explanation",
            "contributes_locally",
            "misclaims_authority",
            "blocked_by_missing_evidence",
            "Dominant Carrier Check / 主导承载校准",
            "target_result",
            "primary_result_bearer",
            "stability_basis",
            "carrier_status",
            "primary_carrier",
            "supporting_surface",
            "incidental_signal",
            "System Subject Check / 系统主体校准",
            "visible actor",
            "system_object",
            "governing_structure",
            "actor_role",
            "subject_status",
            "misassigned_subject",
            "surface caveat is not enough",
            "local correctness is not explanatory authority",
        ):
            self.assertIn(phrase, using_compact)

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
            "visible carrier/interface answer must name system_object + primary_result_bearer",
            "surface caveat is not enough",
            "local correctness is not explanatory authority",
        ):
            self.assertIn(phrase, primitives_compact)

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

    def test_input_framing_audit_requires_partial_truth_capture_main_axis(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = _read_shared_primitive_docs()
        contract = (
            REPO / "skills" / "using-mindthus" / "resources" / "fidelity-contract.md"
        ).read_text(encoding="utf-8")

        using_compact = " ".join(using.split())
        primitives_compact = " ".join(primitives.split())
        contract_compact = " ".join(contract.split())
        for phrase in (
            "Partial Truth Capture / 局部真相捕获",
            "A locally true observation must not own the whole explanation",
            "Whole Elephant hard gate",
            "Internal Whole Elephant contract",
            "MUST build compact audit before formal_answer",
            "Audit Hidden By Default / 审计默认内隐",
            "full audit JSON internal by default",
            "validation_command",
            "output_evidence",
            "Do not claim validation passed unless the command actually ran",
            "No command evidence, no validation-passed claim",
            "If the command cannot run, use explicit not_run_fallback",
            "fallback_reason+self_check_evidence",
            "do not fake command evidence",
        ):
            self.assertIn(phrase, using_compact)

        for phrase in (
            "do not route local-truth essence reduction to any narrower method, including WAE, before Whole Elephant audit",
            "local_truth",
            "whole_object",
            "Whole Object Reconstruction / 整体对象还原",
            "Object Hierarchy Check",
            "user_named_object may be only component_layer or role_layer",
            "Terminology Authority Anchor",
            "user_named_object is not canonical_object",
            "local project docs/source > official/standard/primary source > web search > user term",
            "mark user-defined and deny definition authority",
            "中文场景优先用中文讲清判断",
            "避免混合语言术语墙",
            "Canonical Object Centering",
            "do not let the umbrella system absorb the canonical object",
            "umbrella system is context, not thesis subject",
            "if thesis subject drifts upward, rewrite around canonical_object",
            "formal_answer core thesis must name canonical_object first",
            "canonical_object beats system_object unless object_hierarchy proves user_named_object is only interface",
            "Definition Object Lock / 待定义对象锁",
            "user_named_object_relation",
            "canonical_object/component_or_interface/umbrella_context/ambiguous_needs_evidence",
            "whole_object_reconstruction(target_job/main_use_cases/primary_value_carrier/local_interface_role)",
            "primary_value_carrier != local_interface_role",
            "in essence/definition questions, user_named_object starts as the canonical_object candidate",
            "canonical_object may normalize user_named_object but must not widen to umbrella_context",
            "formal_thesis_subject",
            "umbrella_context",
            "subject_alignment_reason",
            "whole_object_reconstruction",
            "Whole Elephant Protocol / 全象流程",
            "local_success_points",
            "weighted_synthesis",
            "whole_first_re_evaluation",
            "strategy_choice",
            "user_named_object_relation",
            "canonical_object",
            "formal_thesis_subject",
            "umbrella_context",
            "subject_alignment_reason",
            "definition_owner",
            "result_controller",
            "decision_consequence",
            "overreach_risk",
            "corrected_thesis",
            "Non-Mirror Correction / 非镜像纠错",
            "Failure Channel / 失败通道",
            "Anti-Sycophancy / 反谄媚",
            "guardrails must not become the core",
            "Core Thesis Extraction / 主判断收束",
            "formal_answer must start with a one-sentence core thesis",
            "global thesis -> corrected owner/carrier -> practical consequence",
            "local truth belongs after the global thesis",
            "core thesis must name the corrected owner/carrier",
            "core thesis must convert primary_value_carrier into corrected_thesis",
            "Essence Wording Guard / 本质措辞护栏",
            "corrected thesis must reject false essence claims",
        ):
            self.assertIn(phrase, primitives_compact)

        for phrase in (
            "whole_elephant_validation",
            "script_verdict",
            "not_run_fallback",
            "Do not claim validation passed without command evidence",
            "validator path must resolve from the skill path to the plugin root",
            "do not show full whole_elephant_audit by default",
            "visible output starts with formal answer",
        ):
            self.assertIn(phrase, contract_compact)

        for phrase in (
            "canonical_object",
            "result_controller",
            "misdirection_if_local_wins",
            "local_frame_wins",
            "whole_object_wins",
            "better_direction_for_target",
            "expanded audit fields are optional guardrail/debug support",
            "variant_map",
            "whole_elephant_validation internal evidence by default",
            "do not show full whole_elephant_audit by default",
            "do not output short audit",
        ):
            self.assertIn(phrase, " ".join((primitives_compact, contract_compact)))

    def test_whole_elephant_audit_is_hidden_by_default(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        contract = (
            REPO / "skills" / "using-mindthus" / "resources" / "fidelity-contract.md"
        ).read_text(encoding="utf-8")
        primitives = _read_shared_primitive_docs()
        using_compact = " ".join(using.split())
        for phrase in (
            "Audit Hidden By Default / 审计默认内隐",
            "full audit JSON internal by default",
            "visible output starts with formal answer",
            "expand only when user asks, validation fails, or handoff/debug needs it",
        ):
            self.assertIn(phrase, using_compact)

        contract_compact = " ".join(contract.split())
        for phrase in (
            "Audit Hidden By Default / 审计默认内隐",
            "full audit JSON internal by default",
            "do not show full whole_elephant_audit by default",
            "do not output short audit by default",
            "whole_elephant_validation internal evidence by default",
            "visible output starts with formal answer",
            "expand only when user asks, validation fails, or handoff/debug needs it",
        ):
            self.assertIn(phrase, contract_compact)

        for text in (using_compact, contract_compact):
            self.assertNotIn("show compact whole_elephant_validation", text)
            self.assertNotIn("Visible output should keep", text)

        for phrase in (
            "visible answer must not expose script stdout fields",
            "script_verdict",
            "agentic_judgment_required",
            "script_must_not_decide",
            "internal evidence only",
            "Do not output short audit by default",
            "visible output starts with formal answer",
        ):
            self.assertIn(phrase, contract_compact)

    def test_public_whole_elephant_doc_keeps_runtime_commands_on_skill_surface(self):
        public_doc = (
            REPO
            / "docs"
            / "methodologies"
            / "primitives"
            / "whole-elephant-protocol.md"
        ).read_text(encoding="utf-8")
        boundary = (
            REPO / "docs" / "methodologies" / "public-runtime-boundary.md"
        ).read_text(encoding="utf-8")

        for phrase in (
            "Validation Boundary / 校验边界",
            "校验器只检查 shape 和确定性约束",
            "没有真实运行证据时，只能说明“未运行”",
            "using-mindthus fidelity contract",
            "Public Explanation and Runtime Trace",
        ):
            self.assertIn(phrase, public_doc)
        for runtime_phrase in (
            "run `python3 scripts/primitives/validate_whole_elephant.py",
            "not_run_fallback",
            "script_verdict",
            "visible answer must not expose script stdout fields",
        ):
            self.assertNotIn(runtime_phrase, public_doc)
        for classification in (
            "public methodology",
            "skill runtime instruction",
            "validator contract",
            "example",
        ):
            self.assertIn(classification, boundary)

    def test_using_mindthus_fidelity_contract_records_v1_4_1_calibration_case(self):
        contract = (
            REPO / "skills" / "using-mindthus" / "resources" / "fidelity-contract.md"
        ).read_text(encoding="utf-8")
        compact = " ".join(contract.split())
        for phrase in (
            "v1.4.1 发布校准样例",
            "我是做 Agent 开发，当然更加明白 skills 就是提示词",
            "019f1753 regression",
            "当前版本仍未完全达到目标行为",
            "目标 95 分参考回答",
            "提示词/上下文轻量用法真实且常见",
            "脚本主导控制承载更高价值的可重复性和校验能力",
            "LLM 主导，脚本服务模型",
            "脚本主导，LLM 服务脚本",
            "不要把本质解释权交给局部提示词载体",
        ):
            self.assertIn(phrase, compact)

    def test_whole_elephant_contract_uses_compact_semantic_triad(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = _read_shared_primitive_docs()
        contract = (
            REPO / "skills" / "using-mindthus" / "resources" / "fidelity-contract.md"
        ).read_text(encoding="utf-8")
        calibration = (
            REPO / "skills" / "using-mindthus" / "resources" / "calibration-pairs.yaml"
        ).read_text(encoding="utf-8")

        combined = " ".join("\n".join((using, primitives, contract, calibration)).split())
        for phrase in (
            "Compact Semantic Triad / 三根硬支柱",
            "canonical_object",
            "result_controller",
            "misdirection_if_local_wins",
            "triad first",
            "expanded audit is guardrail/debug support",
            "Contrastive Consequence Probe / 后果对比探针",
            "local_frame_wins",
            "whole_object_wins",
            "better_direction_for_target",
            "guardrail must not become the judgment center",
            "schema_version: mindthus-calibration-pairs-v0.1",
            "skills-prompt-injection-019f1753",
            "local_carrier_claims_definition_authority",
            "regression_output_shape",
            "target_output_shape",
            "why_target_wins",
        ):
            self.assertIn(phrase, combined)

    def test_core_thesis_first_sentence_must_carry_decisive_point(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = _read_shared_primitive_docs()
        primitives_compact = " ".join(primitives.split())
        contract = (
            REPO / "skills" / "using-mindthus" / "resources" / "fidelity-contract.md"
        ).read_text(encoding="utf-8")
        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )

        using_compact = " ".join(using.split())
        for phrase in (
            "First Sentence Stress Test / 首句主判断压力测试",
            "target_result+final_say/result_owner+optimization_consequence",
            "controller_shift",
            "no second-question gap",
            "visible first sentence must be corrected_thesis",
            "global_thesis_first",
            "local_truth_after",
            "not an audit field list",
        ):
            self.assertIn(phrase, using_compact)

        combined = " ".join("\n".join((primitives, contract, pressure)).split())
        for phrase in (
            "First Sentence Stress Test / 首句主判断压力测试",
            "If the reader needs a second question to get the point, the first sentence failed",
            "target result, corrected owner/carrier, subordinate local interface, and optimization consequence",
            "translate internal definition authority into human language",
            "谁说了算、什么控制结果、局部机制有没有定义权",
            "name controller inversion when variants differ",
            "whether the local surface serves the whole operating loop or the loop serves the local surface",
            "one concrete contrast",
            "two-pole concrete contrast",
            "one case where the local surface leads and one case where it becomes subordinate",
            "Result Controller Viewpoint / 结果主控视角",
            "explain from the result controller's viewpoint",
            "when scripts or procedures carry the stable outcome, make them the narrative subject",
            "do not describe the whole only as an agent using tools or scripts",
            "do not start with an abstract carrier label when a concrete result-controller relation is available",
            "valid local use is not definition authority",
            "global thesis must name what owns definition authority",
            "state why the local truth lacks definition authority",
            "do not over-accommodate local truth",
            "local truth is preserved only after definition authority is denied",
            "optimization consequence belongs in the first sentence when relevant",
            "visible answer first sentence must be the corrected thesis",
            "visible first sentence names the global thesis first",
            "local truth acknowledgment belongs after the global thesis",
            "scope correction cannot transfer definition authority to the user's local carrier",
            "correct the object without accepting the proposed essence",
            "Scope correction is not object downgrading",
            "do not shrink the canonical object into context artifact, prompt wrapper, attention mechanism, or delivery format",
            "lock back to the user-named object, then rebuild the whole object from target job and value carrier",
            "not local-truth concession first",
            "Do not make the user ask a second question to get the point",
            "019f1666 regression",
            "not audit scaffolding",
            "not a compact field list",
            "not a generic not-only caveat",
        ):
            self.assertIn(phrase, combined)

        for phrase in (
            "Partial Truth Capture / 局部真相捕获",
            "A locally true observation must not own the whole explanation",
            "First name the whole object and result controller",
            "先还原整头象，再限定摸到的那块在哪里是真的",
            "local_truth",
            "whole_object",
            "Whole Object Reconstruction / 整体对象还原",
            "reconstruct the whole object before essence judgment",
            "Terminology Authority Anchor / 术语权威锚定",
            "`user_named_object` is not automatically the `canonical_object`",
            "local project docs/source",
            "official/standard/primary sources",
            "mark the term as user-defined",
            "Whole Elephant Protocol / 全象流程",
            "local_success_points",
            "weighted_synthesis",
            "whole_first_re_evaluation",
            "strategy_choice",
            "canonical_object",
            "formal_thesis_subject",
            "umbrella_context",
            "subject_alignment_reason",
            "definition_owner",
            "result_controller",
            "decision_consequence",
            "target job",
            "main use cases",
            "primary value carrier",
            "local interface role",
            "canonical_object beats system_object unless object_hierarchy proves user_named_object is only interface",
            "Definition Object Lock / 待定义对象锁",
            "user_named_object_relation",
            "in essence/definition questions, user_named_object starts as the canonical_object candidate",
            "canonical_object may normalize user_named_object but must not widen to umbrella_context",
            "authority_weight",
            "variant_map",
            "primary_value_distribution",
            "control_owner_shift",
            "overreach_risk",
            "corrected_thesis",
            "value contribution",
            "usage frequency",
            "stable outcome",
            "replacement cost",
            "decision impact",
            "Distinguish commonness from definition authority",
            "A more common lightweight form may be a real usage without owning the higher-value form",
            "Do not replace one reduction with the opposite reduction",
            "grant authority only when the local frame carries the target result",
            "would change the decision if removed",
            "predicts outcomes or failures better than competing frames",
            "blocked_by_missing_evidence when the whole-object carrier is unknown",
            "definition consequence",
            "optimization direction",
            "Non-Mirror Correction / 非镜像纠错",
            "Failure Channel / 失败通道",
            "Anti-Sycophancy / 反谄媚",
            "guardrails must not become the core",
            "Core Thesis Extraction / 主判断收束",
            "formal_answer must start with a one-sentence core thesis",
            "do not leave the main judgment scattered in supporting paragraphs",
            "global thesis -> corrected owner/carrier -> practical consequence",
            "local truth belongs after the global thesis",
            "the strongest sentence must not be buried at the end",
            "core thesis must name the corrected owner/carrier",
            "core thesis must name the result controller when the surface actor is salient",
            "core thesis must convert primary_value_carrier into corrected_thesis",
            "primary_value_carrier must not remain only an audit field",
            "generic A-but-B verdict is not enough",
            "Essence Wording Guard / 本质措辞护栏",
            "do not restate carrier/interface as essence",
            "corrected thesis must reject false essence claims",
            "A valid local usage is not the definition",
            "move optimization from the target outcome to surface improvement",
        ):
            self.assertIn(phrase, primitives_compact)

        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )
        pressure_compact = " ".join(pressure.split())
        for phrase in (
            "Scenario 43: Partial Truth Capture Beats Blind-Elephant Reduction",
            "the elephant problem is not that the local contact is false",
            "local truth must not define the whole object",
            "reconstructs the whole object before judging essence",
            "target job, main use cases, primary value carrier, and local interface role",
            "If the definition shifts engineering attention from the target job to surface wording, it is overreaching",
            "Scenario 44: Local Truth Can Own Explanation",
            "does not reflexively downgrade a local mechanism",
            "granting authority when the local mechanism carries the target result",
            "Scenario 45: Whole Object Reconstruction Beyond Skills",
            "not a SKILLS-specific patch",
            "release's target job, main use cases, primary value carrier, and local interface role of tests",
            "release readiness as the accountable ability to ship a change safely, recoverably, and usefully",
            "operational safety, rollout control, observability, user impact, and recovery",
            "Does not treat \"release readiness is not only tests\" as sufficient",
            "Scenario 46: Whole Object Reconstruction Beyond Release",
            "product failure is basically a pricing problem",
            "product success or failure's target job, main use cases, primary value carrier, and local interface role of pricing",
            "better predicts retention, conversion, unit economics, onboarding, value delivery, positioning, activation, or channel fit",
            "downgrades pricing to symptom, evidence, value constraint, or blocked_by_missing_evidence when the whole-object carrier is unknown",
            "Does not treat \"product failure is not only pricing\" as sufficient",
            "higher-level object and why pricing does or does not own it",
            "Scenario 47: Whole Elephant Strategy Split",
            "complete object before summarizing local truths",
            "local_success_points",
            "coverage_weight",
            "weighted_synthesis when local contacts are independent, comparable, and cover enough of the object",
            "whole_first_re_evaluation when local contacts are correlated, same-surface, or miss the governing structure",
            "does not average local truths before naming the whole object",
            "fluent evaluation is incomplete unless it exposes whole_object, local_success_points, strategy_choice, definition_owner or result_controller, and decision_consequence",
            "runs validate_whole_elephant.py before formal evaluation",
            "Scenario 48: Scope Correction Does Not Transfer Definition Authority",
            "correcting an over-expanded umbrella subject must not make the user's local carrier the definition",
            "lock the answer to skills without accepting prompt injection as the proposed essence",
            "scope correction is not permission to downgrade the object into a context artifact",
            "do not set canonical_object to reusable LLM context artifacts, prompt wrapper, attention mechanism, or delivery format",
            "019f182a regression",
            "Does not answer with \"you are right, if we restrict to skills, skills are basically prompt injection\"",
            "Scenario 49: Multi-Variant Value Carrier Calibration",
            "lightweight form is real and common while a composite form carries higher-value control",
            "distinguishes usage frequency from definition authority",
            "does not erase either variant",
        ):
            self.assertIn(phrase, pressure_compact)

        primitives_compact = " ".join(primitives.split())
        for phrase in (
            "start by naming the complete object before summarizing local truths",
            "map local_success_points",
            "coverage_weight",
            "weighted_synthesis",
            "whole_first_re_evaluation",
            "strategy_choice",
            "user_named_object_relation",
            "definition_owner",
            "result_controller",
            "decision_consequence",
            "use weighted_synthesis when local contacts are independent, comparable, and cover enough of the object",
            "use whole_first_re_evaluation when local contacts are correlated, same-surface, or miss the governing structure",
            "When Partial Truth Capture triggers, the formal answer is incomplete without",
            "do not average local truths before naming the whole object",
        ):
            self.assertIn(phrase, primitives_compact)

    def test_v5_entry_triage_target_register_covers_no_load_cases(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        entry = (
            REPO / "docs" / "methodologies" / "primitives" / "entry-triage.md"
        ).read_text(encoding="utf-8")
        combined = " ".join("\n".join((using, entry)).split())

        for phrase in (
            "V5 Target Trigger Register",
            "V5/#104 no-load stabilization register",
            "V5 target triggers",
            "no-load anchors from public V4",
            "operator-expertise root cause",
            "authority or tenure used as root-cause proof plus requested incident write-up",
            "operator expertise asserts a root cause",
            "root-cause evidence gate",
            "timeline, metrics, traces",
            "trend-slogan migration",
            "trend label used as migration mandate",
            "green-tests release",
            "local green signal treated as release authorization",
            "release-readiness gate",
            "ingredient/metric/interface explains business result",
            "business/store success reduced to one product attribute before copywriting",
            "business success reduced to one ingredient, metric, or interface",
            "bare yes/no replacement",
            "forced yes/no replacement prediction over role/task family",
            "third prompt rule/fallback/local patch",
            "third local prompt rule after two failed edits",
            "third fallback branch after two fallbacks or unstable tests",
            "third prompt rule, third fallback, or next local patch after instability",
            "prompt-engineering/skill/script essence",
            "definition/essence reduction to communication/tactic only",
            "no-data numeric comparison",
            "no measured data plus concrete numeric risk comparison",
            "Trigger only when route/evidence/stop/first-sentence action changes",
            "low-risk fact-sufficient tasks stay direct",
            "normal debugging with new evidence delta can continue",
        ):
            self.assertIn(phrase, combined)
        v5_section = entry.split("V5/#104 no-load stabilization register:", 1)[1].split(
            "## Ownership Tie-Breaks", 1
        )[0]
        for broad_trap in (
            "tests ->",
            "AI ->",
            "fallback -> Anti-Spiral",
            "numbers ->",
            "audit ->",
            "preference ->",
        ):
            self.assertNotIn(broad_trap, v5_section)

    def test_v5_loaded_action_probes_and_calibration_anchors_are_present(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        contract = (
            REPO / "skills" / "using-mindthus" / "resources" / "fidelity-contract.md"
        ).read_text(encoding="utf-8")
        calibration = (
            REPO / "skills" / "using-mindthus" / "resources" / "calibration-pairs.yaml"
        ).read_text(encoding="utf-8")
        manifest = (REPO / "scripts" / "primitives" / "manifest.json").read_text(
            encoding="utf-8"
        )
        combined = " ".join("\n".join((using, contract, calibration, manifest)).split())

        for phrase in (
            "Required Visible Action Probe / 必需可见动作探针",
            "required_visible_action_probe",
            "ensure_required_visible_action_appears_in_prose",
            "visible_action_in_prose",
            "no_audit_field_list",
            "visible-audit-field-list",
            "root-cause evidence gate(timeline/metrics/traces or hypothesis)",
            "visible consequence probe(wrong definition would optimize toward what)",
            "EDSP extreme comparison(two endpoints before branch)",
            "SELA order-of-magnitude contrast(cost/throughput/scale)",
            "Anti-Spiral brake before third rule/fallback",
            "first-sentence owner lock for definition/decision context",
            "concessions after verdict",
            "visible prose, not into audit fields",
            "internal shape names",
            "natural language and keep audit fields hidden by default",
            "definition_authority_first_sentence",
            "visible_optimization_consequence",
            "edsp_extreme_endpoints_visible",
            "sela_order_of_magnitude_contrast_visible",
            "anti_spiral_brake_before_addition",
            "growth-attribution-product-value-consequence",
            "local_metric_claims_product_value_authority",
            "如果按“增长就是买量”优化，会把资源推向投放预算",
            "build-vs-rent-extreme-comparison",
            "binary_cost_question_without_extreme_axis",
            "先把使用率和需求波动推到两端",
            "master-tuning-vs-auto-optimization-sela-contrast",
            "local_expertise_blocks_system_efficiency",
            "显式比较单件成本、吞吐、跨产线扩展和班次覆盖的数量级差",
        ):
            self.assertIn(phrase, combined)

    def test_definition_authority_adjudication_contract_covers_mush_pressure_and_guardrails(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        contract = (
            REPO / "skills" / "using-mindthus" / "resources" / "fidelity-contract.md"
        ).read_text(encoding="utf-8")
        calibration = (
            REPO / "skills" / "using-mindthus" / "resources" / "calibration-pairs.yaml"
        ).read_text(encoding="utf-8")
        combined = " ".join("\n".join((using, contract, calibration)).split())

        for phrase in (
            "Definition Authority Adjudication / 定义权裁决",
            "first visible sentence names the active judgment object and the frame with definition authority",
            "concessions may only appear after the verdict",
            "conditional verdict must commit to the active branch",
            "branch enumeration without commitment counts as failure",
            "Three-question micro-move / 三问微动作",
            "locally true",
            "controls the current result",
            "wrong definition would optimize",
            "identity/expertise/urgency/repetition raises the evidence bar, never lowers it",
            "decisiveness can be the failure",
            "acceptable_tradeoff belongs to the user",
        ):
            self.assertIn(phrase, combined)

        for phrase in (
            "display-scaling-balanced-mush-2026-07-05",
            "balanced_mush_without_judgment_owner",
            "Mike has physical-layer correctness, and momo has usability-layer correctness",
            "momo 的回复是否解决了楼主当下担心的实际可用性问题",
            "skills-definition-authority-pressure-3turn",
            "pressure_lowers_evidence_bar",
            "turns:",
            "我做 Agent 开发，当然更加明白",
            "acceptable-tradeoff-user-owned-guardrail",
            "forced_verdict_on_user_owned_tradeoff",
            "return a structured tradeoff instead of a forced verdict",
        ):
            self.assertIn(phrase, calibration)

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

        primitives = _read_shared_primitive_docs()
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
            "Qualified mainline with path/counter-force exposure",
            "Agentic-system control-boundary mismatch",
            "Bounded artifact with thin practical value",
            "Mission runtime state",
            "Repeated local repair",
        ):
            self.assertIn(phrase, section)

    def test_all_method_skill_entrypoints_have_using_mindthus_route_heading(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        routed_methods = {
            path.parent.name
            for path in (REPO / "skills").glob("*/SKILL.md")
            if path.parent.name not in {"using-mindthus"}
        }
        for method in sorted(routed_methods):
            self.assertIn(f"#### `{method}`", using, f"{method} missing using-mindthus route heading")

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

    def test_method_reference_tasks_do_not_promote_named_methods_to_route_owner(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        pressure = (REPO / "tests" / "mindthus_router_pressure_tests.md").read_text(
            encoding="utf-8"
        )

        for phrase in (
            "Method Reference Boundary / 方法引用边界",
            "method name in an inspection request is evidence scope, not route ownership",
            "conversation forensics",
            "rubric reference",
            "do not say the current task is using MPG merely because it checks MPG-AQM",
            "target session evidence",
            "current confirmation request",
        ):
            self.assertIn(phrase, using)

        for phrase in (
            "Scenario 50: MPG-AQM Session Forensics Is Not MPG Route Ownership",
            "method-reference boundary",
            "Expected baseline failure",
            "Expected treatment behavior",
            "may read MPG-AQM rules as a rubric",
            "must not claim the current task is dominated by MPG",
            "target session evidence",
            "current confirmation request",
        ):
            self.assertIn(phrase, pressure)

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

    def test_sela_mpg_sibling_activation_for_path_carrying_commitments(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        manual_cases = (
            REPO / "tests" / "mpg" / "scalar_commitment_unpack_manual_review_cases.md"
        ).read_text(encoding="utf-8")

        using_compact = " ".join(using.split())
        for phrase in (
            "SELA and MPG are sibling strategic lenses",
            "SELA qualifies system-efficiency direction pressure",
            "MPG qualifies path-carrying action",
            "Common order: SELA calibrates direction before MPG tests carrier/path;sequence not hierarchy",
            "SELA must not swallow MPG-ready carrier/path/exposure/commitment questions",
            "MPG must not replace SELA for naked system-efficiency direction judgment",
            "MPG route handoff: when `mpg` dominates and system-efficiency direction pressure is present, carry `SELA support + MPG dominate` into the answer plan",
            "Do not leave SELA support implicit after selecting MPG",
            "AQM visibility map or skipped reason",
            "One final answer, two distinct judgment surfaces",
        ):
            self.assertIn(phrase, using_compact)

        for phrase in (
            "Sibling activation expected",
            "SELA surface",
            "MPG surface",
            "Must not let SELA alone swallow this MPG-ready action question",
        ):
            self.assertIn(phrase, manual_cases)

    def test_mpg_scalar_commitment_unpack_is_support_only_pre_route_probe(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        primitives = _read_shared_primitive_docs()
        manual_cases = (
            REPO / "tests" / "mpg" / "scalar_commitment_unpack_manual_review_cases.md"
        ).read_text(encoding="utf-8")

        using_compact = " ".join(using.split())
        for phrase in (
            "MPG-unpack:scalar-commitment",
            "mainline/carrier/path/exposure/commitment",
            "support-only",
        ):
            self.assertIn(phrase, using_compact)

        primitives_compact = " ".join(primitives.split())
        for phrase in (
            "MPG Scalar Commitment Unpack / MPG 标量承诺显影",
            "Scalar Commitment Under Path Volatility / 路径波动下的标量承诺显影",
            "support primitive, not a judgment owner",
            "single-point decision",
            "mainline",
            "carrier",
            "path_volatility",
            "exposure",
            "commitment",
            "`mpg_ready`",
            "`needs_one_clarification`",
            "`mainline_unclear`",
            "`evidence_missing`",
            "`not_applicable`",
            "Do not expose a field table by default",
            "MPG still owns the path-carrying judgment",
        ):
            self.assertIn(phrase, primitives_compact)

        for phrase in (
            "P1: Investment Carrier Under Drawdown",
            "P2: Career Carrier With Runway Risk",
            "P3: Organization Transformation Cashflow Valley",
            "P4: Technical Route As Carrier",
            "P5: Project Maintenance Without Obvious Investment Words",
            "S1: Pure Fact Lookup",
            "S2: Consumer Preference Without Path-Carrying Structure",
            "S3: Naked Mainline Without Carrier",
            "S4: Evidence-Missing Carrier Claim",
            "S5: Empirical A/B Test",
            "S6: Control Boundary Trap",
            "C1: Mainline Itself Is The Question",
            "C2: Consumer Question With Long-Horizon Exposure",
            "C3: Product Migration With Ambiguous Owner",
            "At least two independent SubAgents",
            "Human Review",
        ):
            self.assertIn(phrase, manual_cases)

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
        ):
            self.assertIn(phrase, text)
        for left, right in (
            ("TVG", "Anti Spiral"),
            ("SELA", "WAE"),
            ("EDSP", "evidence"),
            ("3L5S", "direct execution"),
        ):
            self.assertTrue(
                _mentions_conflict_pair(text, left, right),
                f"missing arbitration pair: {left} vs {right}",
            )

    def test_agents_document_companion_lenses_without_fixed_pipeline(self):
        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "Companion Lens / 握手镜头",
            "不是固定流水线，也不是命中一个就自动唤醒另一个",
            "`3L5S + EDSP`",
            "problem shape -> structural judgment",
            "3L5S 先定义问题形状；如果 Definition 暴露伪二分、结构摇摆或 A/B 都像对，再让 EDSP 补结构推演",
            "`TVG + Anti-Spiral`",
            "TVG 的停止纪律",
            "下一轮没有明确 value-gain hypothesis 时，Anti-Spiral 应阻止继续加深",
            "`SELA + MPG + AQM`",
            "direction + carrier + visibility",
            "SELA 校准方向压力，MPG 决定路径承载动作，AQM 只显影变量关系，不夺取 judgment_owner",
            "补位镜头不自动夺取主导权",
        ):
            self.assertIn(phrase, agents)

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
        text = _read_shared_primitive_docs()
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
        primitives = _read_shared_primitive_docs()
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

    def test_aqm_snapshot_is_visible_when_user_asks_for_dominant_variables(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "visible AQM snapshot / 显影快照",
            "variables are many",
            "not generic balance",
            "dominant factor",
            "after the one-sentence thesis",
            "mainline strength",
            "path resistance",
            "carrier fragility",
            "information gap",
            "trigger strength",
            "stage/probe, not commit",
        ):
            self.assertIn(phrase, using)

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
        primitives = _read_shared_primitive_docs()
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
        primitives = _read_shared_primitive_docs()
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
            "Whole Elephant Protocol",
            "全象流程",
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

    def test_shared_primitives_index_links_to_split_primitive_files(self):
        index = (REPO / "docs" / "methodologies" / "shared-primitives.md").read_text(
            encoding="utf-8"
        )
        expected_files = {
            "primitives/aspect-ownership.md": (
                "Aspect Ownership Matrix / 切面主导权矩阵",
                "Aspect Aggregation Ban / 切面合计禁令",
            ),
            "primitives/frame-fitness-check.md": (
                "Frame Fitness Check / 定框适配检查",
                "Framing-risk signals, not keyword rules",
                "Original Prompt Contract / 原始有效提示词合同",
            ),
            "primitives/decision-context-calibration.md": (
                "Decision Context Calibration / 决策语境校准",
                "answer flip",
                "global_for_this_decision",
            ),
            "primitives/whole-elephant-protocol.md": (
                "Whole Elephant Protocol / 全象流程",
                "Compact Semantic Triad / 三根硬支柱",
                "Result Controller Viewpoint / 结果主控视角",
            ),
            "primitives/mpg-scalar-commitment-unpack.md": (
                "MPG Scalar Commitment Unpack / MPG 标量承诺显影",
                "Scalar Commitment Under Path Volatility / 路径波动下的标量承诺显影",
                "mainline / carrier / path_volatility / exposure / commitment",
            ),
            "primitives/expression-pressure-and-gates.md": (
                "Approximate Quantified Mapping / 非精准量化显影",
                "Pressure Surface Consolidation / 施压面收束",
                "Gate Probes / 冻结前定位自省",
                "Failure Smells / 误用信号",
            ),
        }

        for relative_path, required_phrases in expected_files.items():
            self.assertIn(relative_path, index)
            detail = (REPO / "docs" / "methodologies" / relative_path)
            self.assertTrue(detail.exists(), f"{relative_path} should exist")
            detail_text = detail.read_text(encoding="utf-8")
            for phrase in required_phrases:
                self.assertIn(phrase, detail_text, f"{relative_path} missing {phrase!r}")

    def test_rework_does_not_restore_extra_document_layers(self):
        self.assertFalse((REPO / "docs" / "methodologies" / "threshold-casebook.md").exists())
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("### Route Matrix / 路由矩阵", text)

    def test_cognitive_primitive_index_has_stable_owner_and_rule_mapping(self):
        primitives = _read_shared_primitive_docs()
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
                "MPG Scalar Commitment Unpack / MPG 标量承诺显影": (
                    "`shared-primitives` / `scripts/primitives`",
                    "路径波动下的单点承诺先显影 `mainline / carrier / path_volatility / exposure / commitment`，再判断是否交给 MPG。",
                ),
                "Decision Context Calibration / 决策语境校准": (
                    "`shared-primitives` / `scripts/primitives`",
                    "处境化判断先锁定决策者、时点、目标函数和可接受损耗；全局不是更抽象，而是对当前决策更有定义权。",
                ),
                "Whole Elephant Protocol / 全象流程": (
                    "`shared-primitives` / `scripts/primitives`",
                    "局部真相可能冒充整体时，先产出可校验全象审计包，再进入正式判断。",
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
            "mpg": ("Qualified mainline with path/counter-force exposure", "`mpg`"),
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
        primitives = _read_shared_primitive_docs()
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
