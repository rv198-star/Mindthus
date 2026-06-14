import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TVG = REPO / "skills" / "tvg"


class TvgContractTests(unittest.TestCase):
    def test_skill_names_veto_constraints_and_auditor_separation(self):
        text = (TVG / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "veto_constraints",
            "explicit unacceptable states",
            "They are not value-gain axes",
            "must not exit as `freeze`",
            "independent_auditor",
            "separate generator work from the exit auditor",
            "create, waive, or satisfy veto constraints",
            "decide whether independent auditor separation is required",
        ):
            self.assertIn(phrase, text)

    def test_methodology_keeps_veto_constraints_outside_value_axes(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Thinking Value-Gain Methodology — Value-Oriented Deep Thinking（v0.3）",
            "not a generic improvement pass",
            "Veto Constraints",
            "not ordinary value-gain axes",
            "block exit even when the module has improved",
            "must not exit as `freeze`",
            "Do not turn broad good practice into a veto constraint",
            "independent auditor separation",
            "auditor` reads only the final module",
            "must not rewrite the module as part of the same audit",
        ):
            self.assertIn(phrase, text)

    def test_skill_exposes_value_directed_grounded_insight_loop(self):
        text = (TVG / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "value-directed text/artifact transformation loop",
            'standard of "good"',
            "expected_value",
            "exit gate",
            "Thinking Thickness",
            "Grounded Insight Yield",
            "Value Density",
            "output_profile",
            "delivery bias, not an internal workflow fork",
        ):
            self.assertIn(phrase, text)

    def test_methodology_defines_primary_loop_dimensions_and_state_routing(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Sufficient thinking thickness is the substrate of value",
            "Grounded insight yield is the core output",
            "Value density is the delivery quality",
            "Primary Loop Dimensions",
            "`Thinking Thickness`",
            "`Grounded Insight Yield`",
            "`Value Density`",
            "State-Driven Round Routing",
            "`under-thick`",
            "`adequate-but-loose`",
            "`over-thick`",
            "`compact-strengthen`",
            "Exit-side warning checks",
        ):
            self.assertIn(phrase, text)

    def test_methodology_preserves_thickness_before_density_optimization(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Thickness-Before-Density Rule",
            "Value density must not outrank missing thinking thickness",
            "density optimization is premature",
            "retain enough constraints, alternatives, failure paths, evidence boundaries, and review-bound items",
            "compact only after the thinking substrate is sufficient",
            "Thickness Gate",
            "Exit Graded Refinement",
            "output_profile is applied only after the thickness gate is clear",
        ):
            self.assertIn(phrase, text)

    def test_methodology_defines_grounded_novelty_and_stretch_boundaries(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Grounded Novelty",
            "non-obvious",
            "anchored in real constraints",
            "changes understanding, judgment, expression, action",
            "Grounded Stretch Levels",
            "`reality-bound`",
            "`plausible-extension`",
            "`productive-speculation`",
            "`free-fantasy`",
            "unsupported fantasy",
        ):
            self.assertIn(phrase, text)

    def test_methodology_keeps_claim_and_handoff_as_late_stage_warnings(self):
        text = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        for phrase in (
            "Late-Stage Warning Checks",
            "`Claim Calibration`",
            "`Handoff Readiness`",
            "not inside the primary value-gain loop",
            "usually causes labeling, downgrade, or review-bound notes",
            "checked near exit or when the module is explicitly for handoff",
        ):
            self.assertIn(phrase, text)

    def test_output_profile_is_delivery_bias_not_workflow_fork(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        combined = skill + "\n" + method
        for phrase in (
            "Output Profile Bias",
            "`insight_dense`",
            "`balanced`",
            "`coverage_rich`",
            "delivery bias, not an internal workflow fork",
            "must not lower the standard",
            "must not compress before thinking thickness exists",
            "must not permit low-value expansion",
        ):
            self.assertIn(phrase, combined)

    def test_value_profile_is_first_class_optional_input_with_default_resolution(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        combined = skill + "\n" + method + "\n" + public_doc
        for phrase in (
            "value_profile",
            "Value Profile Resolution",
            "default practical-value profile",
            "`default | supplied | inferred-with-warning`",
            "supplied profile",
            "project default profile",
            "profile source conflicts with the artifact being improved",
            "prefer independent profile sources over the artifact sample",
            "profiles cannot override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints",
            "价值定义包",
            "默认通用实用价值",
            "不要从待改造样例反推风格规则",
            "default-practical-value",
            "shaw-brothers-wuxia-fantasy",
            "king-hu-wuxia-cinema",
            "product-surface-taste-review",
            "示范 profile，不是电影史分类结论",
            "设计审美总论",
            "三层 profile 怎么发挥作用",
            "不能证明任何图像模型都会稳定生成对应风格",
        ):
            self.assertIn(phrase, combined)

    def test_value_profile_schema_and_scripts_preserve_agentic_boundary(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        schema = (TVG / "resources" / "trace-record-schema.json").read_text(encoding="utf-8")
        combined = skill + "\n" + method + "\n" + schema
        for phrase in (
            "value_profile",
            "value_semantics",
            "realization_surface",
            "gain_policy",
            "good_means",
            "bad_means",
            "priority_order",
            "derived_axes",
            "evidence_basis",
            "profile_veto_constraints",
            "prompt_self_audit_questions",
            "image_self_audit_questions",
            "source_notes",
            "scripts validate profile shape only",
            "must not decide whether a value profile is true, complete, aesthetically successful, thick enough, or sufficient for exit",
        ):
            self.assertIn(phrase, combined)

    def test_default_gate_resolution_is_required_before_value_gain_loop(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        schema = (TVG / "resources" / "trace-record-schema.json").read_text(encoding="utf-8")
        guide = (TVG / "resources" / "value-profiles" / "profile-construction.md").read_text(encoding="utf-8")
        combined = skill + "\n" + method + "\n" + public_doc + "\n" + schema + "\n" + guide
        for phrase in (
            "Default Gate Resolution",
            "`provisional-default` expected_value",
            "before the first value-gain round",
            "module_responsibility",
            "downstream_use",
            "hard_veto_checks",
            "value_profile_fit_checks",
            "downstream_use_checks",
            "evidence_boundary_checks",
            "exit_blockers",
            "next_round_positive_value_check",
            "unresolved_gate_items",
            "default_gate_correctness",
            "exit_gate_success",
            "scripts validate expected_value, profile, and exit_gate shape only",
            "Gate is not owned by the profile",
            "默认必须先生成一个",
            "防止完全没说明输出期望值的运行看起来像完整运行",
        ):
            self.assertIn(phrase, combined)

    def test_expected_value_is_agent_input_and_gate_is_internal_stop_condition(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        schema = (TVG / "resources" / "trace-record-schema.json").read_text(encoding="utf-8")
        combined = skill + "\n" + method + "\n" + public_doc + "\n" + schema
        for phrase in (
            "expected_value",
            "Expected Value Resolution",
            "Agent input contract",
            "target_artifact",
            "artifact_job",
            "useful_when",
            "hard_constraints",
            "evidence_boundary",
            "output_bias",
            "Gate is an internal stop condition compiled from expected_value",
            "not a user-facing configuration burden",
            "输出期望值",
            "Gate 是 Agent 内部从输出期望值编译出来的停机条件",
        ):
            self.assertIn(phrase, combined)

    def test_profile_construction_guide_separates_profile_power_from_runtime_rescue(self):
        path = TVG / "resources" / "value-profiles" / "profile-construction.md"
        self.assertTrue(path.exists(), "missing TVG value profile construction guide")
        guide = path.read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        combined = guide + "\n" + method + "\n" + public_doc + "\n" + skill
        for phrase in (
            "Single-pass profile power test",
            "Loop-assisted production test",
            "Do not collapse these claims",
            "A weak profile can look strong",
            "profile_control_power",
            "required_runtime_rounds",
            "residual_failure_modes",
            "runtime_rescue_cost",
            "Treating loop-assisted artifact success as proof that the profile itself is strong",
            "单轮弱、但多轮后结果好",
            "运行时救场误当成 profile 本身强",
        ):
            self.assertIn(phrase, combined)

    def test_gate_calibration_uses_storyboard_and_rpd_price_examples(self):
        guide = (TVG / "resources" / "value-profiles" / "profile-construction.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        combined = guide + "\n" + method + "\n" + public_doc
        for phrase in (
            "Cross-Artifact Exit Gate",
            "not a domain quality score",
            "`hard veto gate`",
            "`value-semantics fit gate`",
            "`downstream-use gate`",
            "`next-round positive-value gate`",
            "Shaw storyboard prompt",
            "RPD price-raising document",
            "supports a more credible price justification, not that the customer will accept the higher price",
            "RPD 文档增厚提价",
            "不能证明客户会接受提价",
            "避免编造 ROI、客户事实",
        ):
            self.assertIn(phrase, combined)

    def test_runtime_observability_and_pressure_are_agentic_references(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        schema = (TVG / "resources" / "trace-record-schema.json").read_text(encoding="utf-8")
        combined = skill + "\n" + method + "\n" + public_doc + "\n" + schema
        for phrase in (
            "debug_log",
            "default-off",
            "candidate_pool",
            "value_gain_scoring_reference",
            "enabled by default",
            "always-on reference",
            "scores help compare rounds, not compute decisions",
            "pressure",
            "default pressure value 2",
            "1-5",
            "5-7 rounds",
            "resource investment pressure, not quality score",
            "pressure_correctness",
            "score_based_exit",
            "pressure_based_exit",
            "默认开启",
            "投入强度",
        ):
            self.assertIn(phrase, combined)

    def test_trace_init_debug_log_scoring_and_pressure_defaults_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            result = subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "runtime-defaults",
                    "--module-title",
                    "Runtime defaults",
                    "--module-type",
                    "skill-intro",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            data = json.loads(trace.read_text(encoding="utf-8"))
            self.assertEqual(data["debug_log"]["enabled"], False)
            self.assertEqual(data["debug_log"]["round_entries"], [])
            scoring = data["value_gain_scoring_reference"]
            self.assertEqual(scoring["enabled"], True)
            self.assertEqual(scoring["scale"]["min"], 0)
            self.assertEqual(scoring["scale"]["max"], 5)
            self.assertEqual(scoring["round_scores"], [])
            self.assertGreaterEqual(len(scoring["dimensions"]), 3)
            pressure = data["pressure"]
            self.assertEqual(pressure["value"], 2)
            self.assertEqual(pressure["mode"], "default")
            self.assertEqual(pressure["typical_rounds"], "2")
            self.assertIn("resource investment pressure, not quality score", pressure["meaning"])
            cannot_decide = data["script_support"]["script_cannot_decide"]
            self.assertIn("value_gain_score_correctness", cannot_decide)
            self.assertIn("score_based_exit", cannot_decide)
            self.assertIn("pressure_correctness", cannot_decide)
            self.assertIn("pressure_based_exit", cannot_decide)

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

    def test_trace_init_accepts_debug_log_and_high_pressure_then_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            result = subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "high-pressure",
                    "--module-title",
                    "High pressure",
                    "--module-type",
                    "methodology-intro",
                    "--debug-log",
                    "--pressure-value",
                    "5",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            data = json.loads(trace.read_text(encoding="utf-8"))
            self.assertEqual(data["debug_log"]["enabled"], True)
            self.assertEqual(data["pressure"]["value"], 5)
            self.assertEqual(data["pressure"]["mode"], "explicit")
            self.assertEqual(data["pressure"]["typical_rounds"], "5-7")
            self.assertIn("candidate comparison", data["pressure"]["exploration_passes"])
            data["debug_log"]["round_entries"].append(
                {
                    "round_id": "r1",
                    "input_summary": "baseline draft",
                    "candidate_pool": [
                        {
                            "id": "c1",
                            "text": "TVG moves text toward a sharper standard of good.",
                            "status": "selected",
                            "rationale": "best matches the expected value",
                        }
                    ],
                    "value_axes_checked": ["value density"],
                    "gate_checks": ["next round has a named positive-value hypothesis"],
                    "veto_checks": ["no evidence boundary override"],
                    "next_round_positive_value_hypothesis": "raise information density without losing clarity",
                    "decision": "continue",
                    "decision_rationale": "candidate still lacks concrete example",
                    "agent_judgment_required": True,
                }
            )
            data["value_gain_scoring_reference"]["round_scores"].append(
                {
                    "round_id": "r1",
                    "dimension_scores": [
                        {
                            "dimension_id": "value_density",
                            "score": 3.4,
                            "rationale": "clearer than baseline but still wordy",
                        }
                    ],
                    "overall_reference_score": 3.4,
                    "scoring_basis": "ordinal reference for comparing rounds only",
                    "agent_judgment_required": True,
                }
            )
            trace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

    def test_trace_validation_rejects_invalid_runtime_observability_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "runtime-shape",
                    "--module-title",
                    "Runtime shape",
                    "--module-type",
                    "audit",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            data = json.loads(trace.read_text(encoding="utf-8"))
            data["debug_log"]["enabled"] = "yes"
            data["debug_log"]["round_entries"] = [
                {
                    "round_id": "r1",
                    "input_summary": "baseline",
                    "candidate_pool": [{"id": "c1", "text": "x", "status": "winner", "rationale": "x"}],
                    "value_axes_checked": "not-a-list",
                    "gate_checks": [],
                    "veto_checks": [],
                    "next_round_positive_value_hypothesis": "",
                    "decision": "auto-pass",
                    "decision_rationale": "",
                    "agent_judgment_required": "true",
                }
            ]
            data["value_gain_scoring_reference"]["scale"]["max"] = 4
            data["value_gain_scoring_reference"]["round_scores"] = [
                {
                    "round_id": "r1",
                    "dimension_scores": [{"dimension_id": "value_density", "score": 5.5, "rationale": "x"}],
                    "overall_reference_score": True,
                    "scoring_basis": "x",
                    "agent_judgment_required": True,
                }
            ]
            data["pressure"]["value"] = 6
            data["pressure"]["mode"] = "auto"
            data["pressure"]["exploration_passes"] = "not-a-list"
            trace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 1)
            self.assertIn("debug_log.enabled: expected boolean", validation.stdout)
            self.assertIn("debug_log.round_entries[0].candidate_pool[0].status: unsupported value 'winner'", validation.stdout)
            self.assertIn("debug_log.round_entries[0].value_axes_checked: expected list", validation.stdout)
            self.assertIn("debug_log.round_entries[0].decision: unsupported value 'auto-pass'", validation.stdout)
            self.assertIn("debug_log.round_entries[0].agent_judgment_required: expected boolean", validation.stdout)
            self.assertIn("value_gain_scoring_reference.scale.max: expected 5", validation.stdout)
            self.assertIn("value_gain_scoring_reference.round_scores[0].dimension_scores[0].score: expected number from 0 to 5", validation.stdout)
            self.assertIn("value_gain_scoring_reference.round_scores[0].overall_reference_score: expected number from 0 to 5", validation.stdout)
            self.assertIn("pressure.value: expected integer from 1 to 5", validation.stdout)
            self.assertIn("pressure.mode: unsupported value 'auto'", validation.stdout)
            self.assertIn("pressure.exploration_passes: expected list", validation.stdout)

    def test_trace_init_accepts_value_profile_metadata_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            result = subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "shaw-shot-prompt",
                    "--module-title",
                    "Shaw shot prompt",
                    "--module-type",
                    "cinematic-prompt",
                    "--value-profile-mode",
                    "supplied",
                    "--value-profile-name",
                    "Shaw Brothers studio-era wuxia/fantasy",
                    "--value-profile-artifact-job",
                    "convert a script beat into a multi-shot cinematic prompt",
                    "--value-profile-good",
                    "set-built theatricality is expressed through composition and blocking",
                    "--value-profile-bad",
                    "generic modern AI video prompt inflation",
                    "--value-profile-priority",
                    "studio-era theatricality before naturalistic realism",
                    "--value-profile-derived-axis",
                    "studio-theatricality-depth",
                    "--value-profile-evidence",
                    "independent film-history source notes",
                    "--value-profile-prompt-audit-question",
                    "Does the prompt express studio-era theatricality through blocking rather than modern spectacle?",
                    "--value-profile-image-audit-question",
                    "Does the image read as a set-built widescreen storyboard sheet rather than modern xianxia CG?",
                    "--value-profile-source-note",
                    "Independent source notes support the scoped profile; the script paragraph is not a style source.",
                    "--profile-veto-constraint",
                    "must not infer style rules from the flawed expansion sample",
                    "--value-profile-surface-artifact-role",
                    "director-style cinematic storyboard prompt",
                    "--value-profile-surface-downstream-use",
                    "image generation and storyboard review",
                    "--value-profile-surface-observable-unit",
                    "shot",
                    "--value-profile-surface-observable-unit",
                    "storyboard panel",
                    "--value-profile-surface-granularity-pressure",
                    "split when a physical action changes screen relation",
                    "--value-profile-surface-review-handle",
                    "each shot has function, picture, blocking, and source attribution",
                    "--value-profile-gain-preferred-move",
                    "turn implied script action into visible shot-to-shot cause and effect",
                    "--value-profile-gain-discouraged-move",
                    "adding camera motion without new shot function",
                    "--value-profile-gain-split-rule",
                    "split emotional recognition from physical response when relation changes",
                    "--value-profile-gain-merge-rule",
                    "merge redundant reaction closeups",
                    "--value-profile-gain-density-guidance",
                    "coverage-rich output is allowed only when every unit remains reviewable",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            data = json.loads(trace.read_text(encoding="utf-8"))
            expected_value = data["expected_value"]
            profile = data["value_profile"]
            gate = data["exit_gate"]
            semantics = profile["value_semantics"]
            self.assertEqual(expected_value["mode"], "provisional-default")
            self.assertEqual(expected_value["target_artifact"], "Shaw shot prompt")
            self.assertIn("useful_when", expected_value)
            self.assertIn("hard_constraints", expected_value)
            self.assertIn("evidence_boundary", expected_value)
            self.assertEqual(profile["mode"], "supplied")
            self.assertEqual(profile["name"], "Shaw Brothers studio-era wuxia/fantasy")
            self.assertEqual(gate["mode"], "provisional-default")
            self.assertIn("value_profile_fit_checks", gate)
            self.assertIn("downstream_consumer is not specified", gate["unresolved_gate_items"])
            self.assertIn("freeze_granularity is not specified", gate["unresolved_gate_items"])
            self.assertEqual(
                semantics["good_means"],
                ["set-built theatricality is expressed through composition and blocking"],
            )
            self.assertEqual(semantics["bad_means"], ["generic modern AI video prompt inflation"])
            self.assertEqual(semantics["derived_axes"], ["studio-theatricality-depth"])
            self.assertEqual(
                profile["prompt_self_audit_questions"],
                ["Does the prompt express studio-era theatricality through blocking rather than modern spectacle?"],
            )
            self.assertEqual(
                profile["image_self_audit_questions"],
                ["Does the image read as a set-built widescreen storyboard sheet rather than modern xianxia CG?"],
            )
            self.assertEqual(
                profile["source_notes"],
                ["Independent source notes support the scoped profile; the script paragraph is not a style source."],
            )
            self.assertEqual(
                semantics["profile_veto_constraints"],
                ["must not infer style rules from the flawed expansion sample"],
            )
            self.assertEqual(profile["realization_surface"]["observable_units"], ["shot", "storyboard panel"])
            self.assertEqual(
                profile["realization_surface"]["granularity_pressure"],
                ["split when a physical action changes screen relation"],
            )
            self.assertEqual(
                profile["gain_policy"]["preferred_moves"],
                ["turn implied script action into visible shot-to-shot cause and effect"],
            )
            self.assertEqual(profile["gain_policy"]["merge_rules"], ["merge redundant reaction closeups"])
            self.assertIn("value_profile_truth", data["script_support"]["script_cannot_decide"])
            self.assertIn("default_gate_correctness", data["script_support"]["script_cannot_decide"])
            self.assertIn("exit_gate_success", data["script_support"]["script_cannot_decide"])
            self.assertIn("realization_surface_fit", data["script_support"]["script_cannot_decide"])
            self.assertIn("gain_policy_success", data["script_support"]["script_cannot_decide"])
            self.assertIn("prompt_thickness_success", data["script_support"]["script_cannot_decide"])
            self.assertIn("aesthetic_success", data["script_support"]["script_cannot_decide"])

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            self.assertIn("agentic audit is still required", validation.stdout)

    def test_trace_default_profile_can_omit_optional_profile_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            result = subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "minimal-profile",
                    "--module-title",
                    "Minimal profile",
                    "--module-type",
                    "methodology",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            data = json.loads(trace.read_text(encoding="utf-8"))
            profile = data["value_profile"]
            self.assertIn("value_semantics", profile)
            self.assertNotIn("realization_surface", profile)
            self.assertNotIn("gain_policy", profile)
            self.assertIn("good_means", profile["value_semantics"])
            self.assertIn("profile_veto_constraints", profile["value_semantics"])
            self.assertEqual(data["exit_gate"]["mode"], "provisional-default")
            self.assertIn("unresolved_gate_items", data["exit_gate"])

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

    def test_trace_validation_rejects_invalid_value_profile_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "profile-check",
                    "--module-title",
                    "Profile check",
                    "--module-type",
                    "audit",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            data = json.loads(trace.read_text(encoding="utf-8"))
            data["value_profile"]["mode"] = "scored"
            data["value_profile"]["value_semantics"]["good_means"] = "not-a-list"
            data["value_profile"]["prompt_self_audit_questions"] = "not-a-list"
            data["value_profile"]["image_self_audit_questions"] = "not-a-list"
            data["value_profile"]["source_notes"] = "not-a-list"
            data["value_profile"]["realization_surface"] = {
                "artifact_role": ["not-a-string"],
                "observable_units": "not-a-list",
            }
            data["value_profile"]["gain_policy"] = {
                "preferred_moves": "not-a-list",
            }
            data["expected_value"]["mode"] = "auto-pass"
            data["expected_value"]["useful_when"] = "not-a-list"
            data["expected_value"]["artifact_job"] = ["not-a-string"]
            data["exit_gate"]["mode"] = "auto-pass"
            data["exit_gate"]["hard_veto_checks"] = "not-a-list"
            data["exit_gate"]["next_round_positive_value_check"] = ["not-a-string"]
            trace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 1)
            self.assertIn("value_profile.mode: unsupported value 'scored'", validation.stdout)
            self.assertIn("value_profile.value_semantics.good_means: expected list", validation.stdout)
            self.assertIn("value_profile.prompt_self_audit_questions: expected list", validation.stdout)
            self.assertIn("value_profile.image_self_audit_questions: expected list", validation.stdout)
            self.assertIn("value_profile.source_notes: expected list", validation.stdout)
            self.assertIn("value_profile.realization_surface.artifact_role: expected string", validation.stdout)
            self.assertIn("value_profile.realization_surface.observable_units: expected list", validation.stdout)
            self.assertIn("value_profile.gain_policy.preferred_moves: expected list", validation.stdout)
            self.assertIn("expected_value.mode: unsupported value 'auto-pass'", validation.stdout)
            self.assertIn("expected_value.useful_when: expected list", validation.stdout)
            self.assertIn("expected_value.artifact_job: expected string", validation.stdout)
            self.assertIn("exit_gate.mode: unsupported value 'auto-pass'", validation.stdout)
            self.assertIn("exit_gate.hard_veto_checks: expected list", validation.stdout)
            self.assertIn("exit_gate.next_round_positive_value_check: expected string", validation.stdout)

    def test_default_practical_value_profile_resource_exists(self):
        path = TVG / "resources" / "value-profiles" / "default-practical-value.md"
        self.assertTrue(path.exists(), "missing default practical-value profile resource")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Default Practical-Value Profile",
            "mode: default",
            "value_semantics",
            "decision / action leverage",
            "evidence honesty",
            "handoff usability",
            "risk reduction",
            "reuse without overfitting",
            "execution readiness",
            "This profile is the fallback when no supplied or project default profile is active.",
            "It intentionally uses only the required `value_semantics` layer.",
        ):
            self.assertIn(phrase, text)

    def test_shaw_brothers_profile_resource_exists_and_rejects_sample_contamination(self):
        path = TVG / "resources" / "value-profiles" / "shaw-brothers-wuxia-fantasy.md"
        self.assertTrue(path.exists(), "missing Shaw Brothers wuxia/fantasy value profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Shaw Brothers Studio-Era Wuxia / Fantasy Cinematic Prompt Profile",
            "mode: supplied",
            "value_semantics",
            "realization_surface",
            "gain_policy",
            "profile source must be independent from the artifact being improved",
            "do not infer Shaw Brothers rules from the flawed expansion sample",
            "studio-era / backlot / set-built theatricality",
            "wide-screen composition",
            "saturated color and strong graphic contrast",
            "stylized rather than naturalistic environments",
            "melodramatic emotional punctuation",
            "modern xianxia",
            "generic AI video prompt inflation",
            "prompt_self_audit_questions",
            "image_self_audit_questions",
            "source_notes",
            "scoped profile for cinematic prompt and storyboard image generation",
            "not a universal definition of all Shaw Brothers films",
            "Clear Water Bay",
            "independent source notes",
            "director-style cinematic storyboard prompt",
            "observable_units",
            "split when a physical action changes screen relation",
            "coverage-rich output is allowed only when every added unit remains reviewable",
            "Director-style prompt references may calibrate thickness, shot granularity, and",
            "must not be treated as evidence for Shaw Brothers",
        ):
            self.assertIn(phrase, text)

    def test_shaw_layered_profile_does_not_embed_case_specific_story_objects(self):
        path = TVG / "resources" / "value-profiles" / "shaw-brothers-wuxia-fantasy.md"
        self.assertTrue(path.exists(), "missing Shaw Brothers wuxia/fantasy value profile")
        text = path.read_text(encoding="utf-8")
        forbidden_case_terms = (
            "Daoist",
            "old Daoist",
            "qilin",
            "snow mountain",
            "blood trace",
            "licking",
            "final touch",
            "老道",
            "麒麟",
            "雪山",
            "血痕",
            "舔舐",
        )
        for term in forbidden_case_terms:
            self.assertNotIn(term, text)

    def test_product_surface_taste_profile_is_scoped_not_general_taste_skill(self):
        path = TVG / "resources" / "value-profiles" / "product-surface-taste-review.md"
        self.assertTrue(path.exists(), "missing product-surface taste review profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Product Surface Taste Review Profile",
            "mode: supplied",
            "review and strengthen product surface copy",
            "value_semantics",
            "realization_surface",
            "gain_policy",
            "generic AI/SaaS surface patterns",
            "bad-smell diagnosis",
            "visible surface unit",
            "product state",
            "user job",
            "evidence boundary",
            "must not copy external taste-skill prompts",
            "not a general design taste doctrine",
            "not a replacement for product design review",
            "not a claim that Mindthus can match a specialized taste skill",
        ):
            self.assertIn(phrase, text)

    def test_product_surface_taste_profile_pilot_records_loop_and_claim_ceiling(self):
        path = REPO / "tests" / "tvg_product_surface_taste_profile_pilot_2026_06_14.md"
        self.assertTrue(path.exists(), "missing product-surface taste profile pilot")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "issue #47",
            "Single-Pass Profile Power Test",
            "Loop-Assisted Production Test",
            "profile_control_power: partial",
            "Pressure: `4`",
            "reference_score: 3.3",
            "reference_score: 4.1",
            "reference_score: 4.5",
            "freeze-with-review-bound-warning",
            "bad smell -> visible surface unit -> replacement move -> evidence",
            "does not support a broad claim",
            "dedicated taste-skill",
        ):
            self.assertIn(phrase, text)

    def test_profile_construction_guide_separates_profile_power_from_runtime_rescue(self):
        path = TVG / "resources" / "value-profiles" / "profile-construction.md"
        self.assertTrue(path.exists(), "missing TVG value-profile construction guide")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Single-pass profile power test",
            "Loop-assisted production test",
            "Do not collapse these claims.",
            "Do not build the profile by copying the target artifact",
            "Human Reference Boundary",
            "Human references can be useful, but name their role precisely.",
            "copying the human reference's concrete content into a reusable profile",
            "Gate is not owned by the profile.",
            "next-round positive-value gate",
            "In a Shaw storyboard prompt",
            "In an RPD price-raising document",
            "Scripts may validate record shape",
            "decide profile strength",
        ):
            self.assertIn(phrase, text)

    def test_generated_profile_outputs_are_ignored_not_contract_fixtures(self):
        text = (REPO / ".gitignore").read_text(encoding="utf-8")
        for phrase in (
            ".tplan/missions/clean-room-issue31-value-profile-*/",
            "tests/artifacts/tvg_*.png",
            "tests/tvg_shaw_standard_profile_prompt_loop_*.md",
            "tests/tvg_value_profile_shaw_5round_image_iteration_*.md",
            "tests/tvg_value_profile_shaw_layered_*.md",
            "tests/tvg_value_profile_*_self_iteration_*.md",
            "tests/tvg_value_profile_shaw_pilot_clean_room_*.md",
        ):
            self.assertIn(phrase, text)

    def test_king_hu_wuxia_profile_resource_exists_and_is_scoped(self):
        path = TVG / "resources" / "value-profiles" / "king-hu-wuxia-cinema.md"
        self.assertTrue(path.exists(), "missing King Hu wuxia value profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "King Hu Wuxia Cinema Prompt / Storyboard Profile",
            "mode: supplied",
            "value_semantics",
            "realization_surface",
            "gain_policy",
            "scoped profile for cinematic prompt and storyboard image generation",
            "not a universal definition of all King Hu films",
            "Chinese opera rhythm",
            "editing-shaped bursts",
            "spatial intelligence",
            "delayed action",
            "spiritual or philosophical pressure",
            "female knight-errant",
            "modern wire-fu inflation",
            "generic AI wuxia trailer inflation",
            "prompt_self_audit_questions",
            "image_self_audit_questions",
            "source_notes",
        ):
            self.assertIn(phrase, text)

    def test_king_hu_profile_rejects_shaw_cleanwater_bay_pollution(self):
        path = TVG / "resources" / "value-profiles" / "king-hu-wuxia-cinema.md"
        self.assertTrue(path.exists(), "missing King Hu wuxia value profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Shaw Brothers Clear Water Bay / Movietown backlot theatricality used as a King Hu proxy",
            "must not use saturated red-blue Shaw-style hard-light spectacle as the default color or set logic",
            "Pollution boundary: do not use any existing expanded prompt, prior pilot record, Image2",
            "snow mountain / qilin script as King Hu",
            "A human prompt reference may",
            "concrete beats must not be copied",
            "editing must be translated into panel sequence, partial visibility, occlusion, offscreen implication",
            "loop-assisted prompt/image success as proof that the profile itself is strong",
        ):
            self.assertIn(phrase, text)

    def test_king_hu_profile_uses_layered_construction_without_fixed_shot_recipe(self):
        path = TVG / "resources" / "value-profiles" / "king-hu-wuxia-cinema.md"
        self.assertTrue(path.exists(), "missing King Hu wuxia value profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "watcher knowledge-state shift",
            "split when the viewer's knowledge changes, not merely when a new angle sounds cinematic",
            "translate editing into panel sequence, partial visibility, occlusion, offscreen implication, or abrupt transition cues",
            "use human reference prompts only to calibrate output thickness, shot granularity, and reviewable structure; abstract the lesson, do not copy the content",
            "adding eighteen shots, push-ins, aerials, slow motion, or closeups by default",
            "merge redundant reaction closeups that restate the same emotion without new knowledge or moral pressure",
            "a strong single-pass profile should already steer the first prompt toward spatial setup, delay, and panel function",
            "loop-assisted production may improve a prompt or image, but the final claim must separate profile control from runtime rescue",
        ):
            self.assertIn(phrase, text)

    def test_coverage_rich_preserves_review_and_handoff_structure(self):
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        combined = method + "\n" + public_doc
        for phrase in (
            "Coverage-Rich Review Structure",
            "`coverage_rich` must preserve useful review structure",
            "decision questions",
            "alternatives compared",
            "failure paths",
            "evidence / assumption boundary",
            "review-bound items",
            "decision criteria",
            "success / failure conditions",
            "substitute workflows",
            "adoption risks",
            "覆盖厚度优先要保留评审结构",
            "决策问题",
            "成败条件",
            "待确认项",
        ):
            self.assertIn(phrase, combined)

    def test_insight_dense_preserves_calibrated_claim_tension(self):
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        combined = method + "\n" + public_doc
        for phrase in (
            "Insight-Dense Claim Tension",
            "`insight_dense` keeps one decisive grounded claim",
            "calibrated claim tension",
            "prefer calibrated tension over defensive negation",
            "do not turn claim calibration into generic hedging",
            "洞察密度优先要保留有校准的判断张力",
            "不是把观点压成保守免责声明",
        ):
            self.assertIn(phrase, combined)

    def test_balanced_profile_preserves_proportional_routing(self):
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        public_doc = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        combined = method + "\n" + public_doc
        for phrase in (
            "Balanced Proportionality",
            "`balanced` should preserve executable routing",
            "avoid synthetic scorecards or machinery unless the task naturally needs scoring",
            "keep irreversible-risk boundaries or review cadence when they materially change routing",
            "place irreversible-risk boundaries and minimum review cadence inside the rule body for operational rules",
            "do not defer core routing controls to review-bound notes",
            "give a provisional cadence rather than saying only periodic review",
            "anchor high / medium / low labels when used",
            "平衡档要保持比例感",
            "不要为了显得可执行而制造评分系统",
            "不可逆风险和最低复审节奏要进入规则正文",
            "不要只写定期复审",
        ):
            self.assertIn(phrase, combined)

    def test_exit_audit_template_records_grounded_insight_and_profile_prompts(self):
        text = (TVG / "resources" / "exit-audit-template.md").read_text(encoding="utf-8")
        for phrase in (
            "Grounded Insight And Density Check",
            "thinking_thickness_state",
            "grounded_insight_yield",
            "value_density_result",
            "grounded_stretch_level",
            "output_profile",
            "profile_guardrail_result",
            "audit prompts, not script-scored fields",
        ):
            self.assertIn(phrase, text)

    def test_public_tvg_doc_mentions_grounded_insight_density_and_profiles(self):
        text = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        for phrase in (
            "定向文本强化方法",
            "TVG 让文本更接近某个“好”的标准",
            "不是普通提示词模板",
            "思考厚度",
            "有根洞察",
            "价值密度",
            "不是默认扩写",
            "我没想到，但它说得通",
            "输出档位",
            "洞察密度优先",
            "覆盖厚度优先",
        ):
            self.assertIn(phrase, text)

    def test_ab_pressure_tests_cover_issue_10_state_and_profile_scenarios(self):
        text = (REPO / "tests" / "tvg_ab_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "Issue 10: Thin But Polished Artifact Needs Depth Formation",
            "Issue 10: Adequately Thick But Loose Artifact Needs Refinement",
            "Issue 10: Over-Thick Low-Density Artifact Needs Compact Strengthening",
            "Issue 10: Fresh But Ungrounded Viewpoint Needs Claim Warning Or Rejection",
            "Issue 10: Grounded Stretch Accepts Productive Speculation",
            "Issue 10: Coverage-Rich Profile Allows Useful Thickness Without Bloat",
            "Issue 10: Insight-Dense Profile Must Not Skip Thinking Thickness",
            "Expected issue #10 treatment behavior",
        ):
            self.assertIn(phrase, text)

    def test_issue_10_ab_human_review_packet_exists(self):
        path = REPO / "tests" / "tvg_ab_run_2026-05-31.md"
        self.assertTrue(path.exists(), "missing issue #10 A/B human-review packet")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "TVG Issue #10 A/B Human Review Packet",
            "source_artifact",
            "baseline_output",
            "treatment_output",
            "selected_state_route",
            "output_profile",
            "reviewer_preference_prompt",
            "grounded insight",
            "value density",
            "useful thickness without bloat",
        ):
            self.assertIn(phrase, text)

    def test_issue_10_ab_packet_contains_ai_review_profile_matrix(self):
        path = REPO / "tests" / "tvg_ab_run_2026-05-31.md"
        self.assertTrue(path.exists(), "missing issue #10 A/B review packet")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "AI Review Result Matrix",
            "review_mode: ai-review",
            "human_review_status: not-run",
            "Profile: insight_dense",
            "Profile: balanced",
            "Profile: coverage_rich",
            "ai_reviewer_preference: treatment",
            "ai_review_rationale",
            "Scenario A1",
            "Scenario A2",
            "Scenario B1",
            "Scenario B2",
            "Scenario C1",
            "Scenario C2",
            "Scenario D1",
            "Scenario D2",
            "profile_guardrail_result: clear",
            "not a human review result",
        ):
            self.assertIn(phrase, text)

    def test_issue_10_ab_packet_includes_strong_baseline_coverage_rich_check(self):
        path = REPO / "tests" / "tvg_ab_run_2026-05-31.md"
        self.assertTrue(path.exists(), "missing issue #10 A/B review packet")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Strong Baseline Calibration",
            "strong_baseline_output",
            "旧式认真扩厚",
            "不是证明三个输出档位天然都优于基线",
            "coverage_rich 强基线对照",
            "ai_reviewer_preference: mixed",
            "基线齐平",
            "有用厚度",
            "低价值扩写",
            "修正结论",
        ):
            self.assertIn(phrase, text)

    def test_issue_10_external_opencode_version_ab_packet_exists(self):
        path = REPO / "tests" / "tvg_ab_opencode_run_2026-05-31.md"
        self.assertTrue(path.exists(), "missing OpenCode old-vs-new TVG A/B packet")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "TVG Issue #10 OpenCode Version A/B Packet",
            "runner: opencode",
            "model: opencode/deepseek-v4-flash-free",
            "old_tvg_commit",
            "new_tvg_commit",
            "isolated_project_skills",
            "same_input_prompts",
            "Scenario O1",
            "Scenario O2",
            "Scenario O3",
            "old_tvg_output",
            "new_tvg_output",
            "external_ai_review",
            "review_preference",
        ):
            self.assertIn(phrase, text)

    def test_scripts_still_cannot_score_or_route_issue_10_value_gain(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        combined = skill + "\n" + method
        for phrase in (
            "score `Thinking Thickness`, `Grounded Insight Yield`, or `Value Density`",
            "choose TVG state routes",
            "choose `output_profile`",
            "decide `compact-strengthen`, `refine`, `deepen`, or `freeze`",
        ):
            self.assertIn(phrase, combined)

    def test_exit_audit_template_records_veto_and_independence(self):
        text = (TVG / "resources" / "exit-audit-template.md").read_text(encoding="utf-8")
        for phrase in (
            "Thinking Value-Gain Agentic Exit Audit Template（v0.3）",
            "audit_role",
            "auditor_independence",
            "Veto Constraints",
            "veto_constraint_result",
            "triggered_veto_constraints",
            "veto_resolution",
            "whether the audit was independent when independence was required",
        ):
            self.assertIn(phrase, text)

    def test_trace_init_accepts_veto_constraints_and_validates(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            result = subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "release-note",
                    "--module-title",
                    "Release note",
                    "--module-type",
                    "review",
                    "--downstream-consumer",
                    "release reviewer",
                    "--freeze-granularity",
                    "section",
                    "--veto-constraint",
                    "must not claim production readiness without runtime proof",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            data = json.loads(trace.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "tvg-trace-v0.4")
            self.assertEqual(data["method_version"], "Thinking Value-Gain Methodology v0.4")
            self.assertEqual(data["expected_value"]["mode"], "provisional-default")
            self.assertEqual(data["expected_value"]["target_artifact"], "Release note")
            self.assertIn(
                "must not claim production readiness without runtime proof",
                data["expected_value"]["hard_constraints"],
            )
            self.assertEqual(
                data["value_gain"]["veto_constraints"],
                ["must not claim production readiness without runtime proof"],
            )
            self.assertEqual(data["exit_gate"]["mode"], "provisional-default")
            self.assertEqual(data["exit_gate"]["downstream_use"], "release reviewer")
            self.assertEqual(data["exit_gate"]["module_responsibility"], "review")
            self.assertIn(
                "must not claim production readiness without runtime proof",
                data["exit_gate"]["hard_veto_checks"],
            )
            self.assertIn("audit_role", data["agentic_exit_audit"])
            self.assertIn("auditor_independence", data["agentic_exit_audit"])
            self.assertIn("veto_constraint_result", data["agentic_exit_audit"])
            self.assertIn("veto_constraints", data["script_support"]["script_cannot_decide"])
            self.assertIn("exit_gate_success", data["script_support"]["script_cannot_decide"])
            self.assertIn(
                "auditor_independence_requirement",
                data["script_support"]["script_cannot_decide"],
            )

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            self.assertIn("agentic audit is still required", validation.stdout)

    def test_trace_validation_rejects_invalid_audit_role_and_veto_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            init = TVG / "scripts" / "trace" / "init.py"
            validate = TVG / "scripts" / "trace" / "validate.py"
            subprocess.run(
                [
                    "python3",
                    str(init),
                    "--module-id",
                    "handoff",
                    "--module-title",
                    "Handoff",
                    "--module-type",
                    "handoff",
                    "--output",
                    str(trace),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            data = json.loads(trace.read_text(encoding="utf-8"))
            data["agentic_exit_audit"]["audit_role"] = "self-certified"
            data["agentic_exit_audit"]["veto_constraint_result"] = "passed"
            trace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 1)
            self.assertIn("unsupported value 'self-certified'", validation.stdout)
            self.assertIn("unsupported value 'passed'", validation.stdout)

    def test_ab_pressure_tests_document_expected_before_after_failures(self):
        text = (REPO / "tests" / "tvg_ab_pressure_tests.md").read_text(encoding="utf-8")
        for phrase in (
            "TVG A/B Pressure Tests",
            "A / baseline",
            "B / treatment",
            "Veto Constraint Blocks A Cleaner But Unsafe Freeze",
            "Independent Auditor Prevents Generator Self-Justification",
            "Evidence Preservation Before Destructive Remediation",
            "Independent Auditor Returns A Polished But Incomplete Security Handoff",
            "Expected baseline failure",
            "Expected v0.3 behavior",
            "must not exit if the handoff leaves blocking clients",
            "must not make log capture optional before destructive remediation",
            "legacy-token acceptance rule",
        ):
            self.assertIn(phrase, text)

    def test_ab_run_record_captures_mechanical_and_live_results(self):
        text = (REPO / "tests" / "tvg_ab_run_2026-05-23.md").read_text(encoding="utf-8")
        for phrase in (
            "TVG v0.2 -> v0.3 A/B Run Record",
            "Mechanical A/B",
            "Live Agent A/B",
            "Scenario 1 is useful as a regression check",
            "Scenario 2 confirms the intended behavioral difference",
            "Scenario 3 is a weak but useful additional discriminator",
            "Scenario 4 is the strongest treatment pressure so far",
            "audit_role=independent-auditor",
            "auditor_independence=separated-from-generator",
            "unacceptable states must be named and checked as veto constraints",
            "global skill discovery loaded current v0.3 surfaces",
            "runner limitation",
            "isolating global skill discovery",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
