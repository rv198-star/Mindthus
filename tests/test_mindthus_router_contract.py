import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EXPLICIT_ONLY_TOOL_SKILLS = {"case-prep"}


def _read_shared_primitive_docs() -> str:
    """Return the split primitive contract: compact index plus detail files."""
    methodologies = REPO / "docs" / "methodologies"
    parts = [(methodologies / "shared-primitives.md").read_text(encoding="utf-8")]
    primitives_dir = methodologies / "primitives"
    if primitives_dir.exists():
        parts.extend(path.read_text(encoding="utf-8") for path in sorted(primitives_dir.glob("*.md")))
    return "\n".join(parts)


def _read_using_mindthus_contract() -> str:
    """Return the preload entry plus details it explicitly loads on demand."""
    skill_dir = REPO / "skills" / "using-mindthus"
    return "\n".join(
        (
            (skill_dir / "SKILL.md").read_text(encoding="utf-8"),
            _read_shared_primitive_docs(),
            (skill_dir / "resources" / "fidelity-contract.md").read_text(
                encoding="utf-8"
            ),
        )
    )


def _parse_using_mindthus_routes(text: str) -> dict[str, str]:
    """The thin entry maps a judgment gap to an owner, not an output recipe."""
    rows = {}
    start = text.index("### Skill Routing")
    for line in text[start:].splitlines():
        if not line.startswith("|"):
            if rows: break
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells)==2 and cells[1].lower() in {"3l5s","sra","sela","mpg","edsp","wae","tvg","tplan"}:
            rows[cells[1].lower()] = cells[0]
    return rows


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
    # #215 supersedes 38 literal recipe assertions (baseline 1527f32). These
    # checks cover source wiring only; they do not declare semantic model success.
    def test_thin_entry_preserves_truth_user_constraints_and_context_priority(self):
        text=(REPO/"skills/using-mindthus/SKILL.md").read_text()
        for phrase in ("Truth Orientation", "不能混成事实证据", "用户合法取舍", "当前输入优先", "不能静默覆盖"):
            self.assertIn(phrase,text)

    def test_thin_entry_triage_precedes_minimal_routing(self):
        text=(REPO/"skills/using-mindthus/SKILL.md").read_text()
        self.assertLess(text.index("明确、低风险、事实足够"),text.index("### Skill Routing"))
        self.assertIn("缺文件、事实、运行证据或权限",text)
        self.assertIn("最小充分镜头",text)
        routes=_parse_using_mindthus_routes(text)
        self.assertEqual(set(routes),{"3l5s","sra","sela","mpg","edsp","wae","tvg","tplan"})
        self.assertIn("Agentic system",routes['wae'])
        self.assertIn("有界产物",routes['tvg'])
        self.assertIn("持久 Mission",routes['tplan'])
        self.assertNotIn('case-prep',routes)

    def test_thin_entry_conditional_frame_check_allows_sufficient_local_truth(self):
        text=(REPO/"skills/using-mindthus/SKILL.md").read_text()
        for phrase in ("frame-risk 与 execution impact 同时存在", "充分的解释应保留", "不是默认反对用户", "不存在误导时允许局部定义", "因缺证据未决"):
            self.assertIn(phrase,text)

    def test_thin_entry_companion_and_reference_do_not_take_automatic_ownership(self):
        text=(REPO/"skills/using-mindthus/SKILL.md").read_text()
        for phrase in ("SELA owns direction pressure", "MPG owns path-carrying action", "不串固定流水线", "不自动让该方法成为当前 owner"):
            self.assertIn(phrase,text)

    def test_thin_entry_internal_audit_and_scripts_are_conditional(self):
        text=(REPO/"skills/using-mindthus/SKILL.md").read_text()
        for phrase in ("内部审计默认隐藏", "脚本只验证 shape/reference", "未运行不能声称已验证", "不强制每题写字段"):
            self.assertIn(phrase,text)

    def test_thin_entry_has_execution_impact_and_root_cause_boundary(self):
        text=(REPO/"skills/using-mindthus/SKILL.md").read_text()
        for phrase in ("没有变化就退出方法层", "无新证据时 Anti-Spiral", "确认 canonical 根因后才 Root-Cause Replacement", "pressure is not a route"):
            self.assertIn(phrase,text)

    def test_thin_entry_links_all_eight_conditional_primitive_files(self):
        text=(REPO/"skills/using-mindthus/SKILL.md").read_text()
        for path in (REPO/"docs/methodologies/primitives").glob('*.md'):
            if path.name in {'frame-fitness-check.md','entry-triage.md','aspect-ownership.md','decision-context-calibration.md','whole-elephant-protocol.md','expression-pressure-and-gates.md','mpg-scalar-commitment-unpack.md','root-cause-replacement.md'}:
                self.assertIn('docs/methodologies/primitives/'+path.name,text)

    def test_compact_compatibility_contract_remains_explicit_not_default(self):
        text=(REPO/"docs/methodologies/primitives/whole-elephant-protocol.md").read_text() + (REPO/"scripts/primitives/whole_elephant_validator.py").read_text()
        for phrase in ('mindthus-whole-elephant-audit-v0.1','canonical_object','result_controller','misdirection_if_local_wins','visible_formal_answer'):
            self.assertIn(phrase,text)
        self.assertIn('调试',text)
        self.assertIn('不',text)

    def test_legacy_calibration_is_archived_as_development_not_runtime_input(self):
        path=REPO/'docs/internal/optimization/sol61-slim-v0/legacy-fidelity-reference.md'
        self.assertTrue(path.is_file())
        self.assertIn('v1.4.1',path.read_text())
        self.assertNotIn(str(path.relative_to(REPO)),(REPO/'skills/using-mindthus/SKILL.md').read_text())


    def test_skill_discovery_descriptions_route_strategic_path_questions_through_router(self):
        using_desc = _skill_description("using-mindthus")
        sela_desc = _skill_description("sela")
        mpg_desc = _skill_description("mpg")

        for phrase in (
            "fact-sufficient hard-judgment routing",
            "structural, strategic, path, control",
            "Never load for an ordinary request lacking facts",
            "ask directly",
            "SRA only after multiple judgeable candidates share a scarce resource",
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












    def test_root_cause_replacement_calibration_covers_rewrite_and_negative_controls(self):
        calibration = (
            REPO / "skills" / "using-mindthus" / "resources" / "calibration-pairs.yaml"
        ).read_text(encoding="utf-8")
        primitive = (
            REPO / "docs" / "methodologies" / "primitives" / "root-cause-replacement.md"
        ).read_text(encoding="utf-8")
        combined = " ".join("\n".join((calibration, primitive)).split())

        for phrase in (
            "root-replacement-permission-owner",
            "root-replacement-prompt-task-contract",
            "root-replacement-local-bug-negative-control",
            "root-replacement-agent-controller",
            "root-replacement-affirmative-boundary-separation",
            "mandatory refactor",
            "Affirmative Canonicalization / 肯定式正则化",
            "Boundary / veto / safety / authority",
            "Root-Cause Replacement 不要求每个 bug 都重构",
            "兼容层需要明确 owner、期限或 removal condition",
        ):
            self.assertIn(phrase, combined)


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


    def test_minimal_sufficient_lens_does_not_change_tplan_activation(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("## Mainline")
        end = text.index("### Skill Routing", start)
        section = text[start:end]
        self.assertNotIn("tplan", section.lower())




    def test_explicit_only_tool_skills_are_not_passive_router_owners(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        routes = _parse_using_mindthus_routes(using)
        for skill_name in EXPLICIT_ONLY_TOOL_SKILLS:
            self.assertNotIn(skill_name, routes)
            skill = (REPO / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("explicit", skill.lower())
            self.assertIn("do not add passive wake-up routing", skill.lower())



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


    def test_aqm_snapshot_is_visible_when_user_asks_for_dominant_variables(self):
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        details = "\n".join(
            (
                _read_shared_primitive_docs(),
                (REPO / "docs" / "methodologies" / "mpg.md").read_text(
                    encoding="utf-8"
                ),
            )
        )
        self.assertIn("docs/methodologies/primitives/expression-pressure-and-gates.md", using)
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
            self.assertIn(phrase, details)

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

        self.assertIn("docs/methodologies/primitives/expression-pressure-and-gates.md", using)

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

        agents = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(primitives_path, agents)
        using = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for linked_detail in (
            "docs/methodologies/primitives/frame-fitness-check.md",
            "docs/methodologies/primitives/entry-triage.md",
            "docs/methodologies/primitives/expression-pressure-and-gates.md",
        ):
            self.assertIn(linked_detail, using)

        for path in (REPO / "AGENTS.md", REPO / "skills" / "using-mindthus" / "SKILL.md"):
            text = path.read_text(encoding="utf-8")
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
                "Root-Cause Replacement / 根因替换": (
                    "`shared-primitives` / `WAE`",
                    "根因与 canonical owner 明确后，直接替换错误规则；mainline 正面描述目标行为，禁止性语言归入真实 boundary / veto。",
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
