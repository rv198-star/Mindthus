import json
import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TVG = REPO / "skills" / "tvg"
PILLOW_AVAILABLE = importlib.util.find_spec("PIL") is not None


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
            "示范 profile，不是电影史分类结论",
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

    def test_public_tvg_doc_adds_profile_layering_and_case_index(self):
        text = (REPO / "docs" / "methodologies" / "tvg.md").read_text(encoding="utf-8")
        for phrase in (
            "TVG-Profile 是什么",
            "Profile 的分层",
            "`runtime_support`",
            "当前随包提供五类 profile 资源",
            "plain-sharp-skill-intro",
            "cinematic-visual-direction",
            "案例索引",
            "tvg-profile-cases/plain-sharp-skill-intro.md",
            "tvg-profile-cases/film-style-profiles.md",
            "tvg-profile-cases/cinematic-visual-direction.md",
        ):
            self.assertIn(phrase, text)

    def test_tvg_profile_case_pages_exist_and_cover_three_example_lanes(self):
        cases = {
            REPO
            / "docs"
            / "methodologies"
            / "tvg-profile-cases"
            / "plain-sharp-skill-intro.md": (
                "Profile 不一定要从脚本、赛马、",
                "`runtime_support`：没有",
                "这个案例是我们给 TVG-Profile 准备的一条轻量起步线",
            ),
            REPO
            / "docs"
            / "methodologies"
            / "tvg-profile-cases"
            / "film-style-profiles.md": (
                "`shaw-brothers-wuxia-fantasy`",
                "`king-hu-wuxia-cinema`",
                "我们用来展示另一条高级路线",
            ),
            REPO
            / "docs"
            / "methodologies"
            / "tvg-profile-cases"
            / "cinematic-visual-direction.md": (
                "相对通用的影视画面优化",
                "行为样本，不是 source truth",
                "巨物能力没有删除",
            ),
        }
        for path, phrases in cases.items():
            self.assertTrue(path.exists(), path.name)
            text = path.read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, f"{path.name}: {phrase}")

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

    def test_cinematic_visual_direction_profile_is_general_and_four_layered(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        profile = (profile_dir / "profile.md").read_text(encoding="utf-8")
        for phrase in (
            "cinematic visual direction",
            "value_semantics",
            "realization_surface",
            "gain_policy",
            "runtime_support",
            "behavior sample, not source truth",
            "intentionally scene-general",
            "scripts must not decide aesthetic success, profile maturity, or TVG exit",
        ):
            self.assertIn(phrase, profile)
        self.assertIn("colossal-pressure", profile)
        self.assertIn("must not be imposed on quiet landscapes", profile)

        legacy = (
            TVG
            / "resources"
            / "value-profiles"
            / "cinematic-colossal-realism"
            / "profile.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Compatibility Alias", legacy)
        self.assertIn("not a second canonical Profile", legacy)

    def test_cinematic_visual_direction_resources_separate_core_and_colossal_adapter(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        for name in (
            "director-controls.json",
            "negative-constraints.json",
            "field-templates.json",
            "image-audit-rubric.json",
        ):
            payload = json.loads((profile_dir / "resources" / name).read_text(encoding="utf-8"))
            self.assertEqual(payload["profile"], "cinematic-visual-direction")

        controls = json.loads(
            (profile_dir / "resources" / "director-controls.json").read_text(encoding="utf-8")
        )
        self.assertIn("director_shot_spine", controls)
        self.assertIn("director_subtraction_pass", controls)
        self.assertIn("controlled_fracture_coherence", controls)
        self.assertIn("shot_economy_mode", controls)
        self.assertNotIn("decisive_pressure_frame", controls)

        adapter = json.loads(
            (profile_dir / "resources" / "scene-adapters" / "colossal-pressure.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(adapter["adapter"], "colossal-pressure")
        self.assertIn("witness anchor", adapter["realization_surfaces"])
        self.assertIn("three-layer scale ladder", adapter["realization_surfaces"])
        self.assertIn("decisive pressure frame", adapter["gain_moves"])
        self.assertEqual(sorted(adapter["operating_intensity"]), ["2", "3", "4", "5"])

    def test_cinematic_prompt_skeleton_activates_colossal_rules_only_with_adapter(self):
        scripts = (
            TVG / "resources" / "value-profiles" / "cinematic-visual-direction" / "scripts"
        )
        base = subprocess.run(
            ["python3", str(scripts / "build_prompt_skeleton.py"), "一江春水向东流"],
            text=True,
            capture_output=True,
        )
        self.assertEqual(base.returncode, 0, base.stderr)
        base_payload = json.loads(base.stdout)
        self.assertEqual(base_payload["profile"], "cinematic-visual-direction")
        self.assertIsNone(base_payload["resolved_adapter"])
        self.assertNotIn("scene_adapter", base_payload["skeleton"])

        colossal = subprocess.run(
            [
                "python3",
                str(scripts / "build_prompt_skeleton.py"),
                "--adapter",
                "colossal-pressure",
                "中国黑龙盘踞在京城上空",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(colossal.returncode, 0, colossal.stderr)
        payload = json.loads(colossal.stdout)
        self.assertEqual(payload["resolved_adapter"], "colossal-pressure")
        self.assertIn("three-layer scale ladder", payload["skeleton"]["scene_adapter"]["realization_surfaces"])
        self.assertNotIn("aesthetic_success", colossal.stdout)

    def test_cinematic_profile_scripts_report_findings_without_semantic_verdict(self):
        scripts = TVG / "resources" / "value-profiles" / "cinematic-visual-direction" / "scripts"
        lint = subprocess.run(
            [
                "python3",
                str(scripts / "lint_prompt_packet.py"),
                "--adapter",
                "colossal-pressure",
                "--prompt",
                "A huge god, cinematic.",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(lint.returncode, 1, lint.stderr + lint.stdout)
        payload = json.loads(lint.stdout)
        self.assertIn("missing_camera_relation", payload["finding_codes"])
        self.assertIn("missing_colossal_witness_anchor", payload["finding_codes"])
        self.assertIn("missing_colossal_environment_feedback", payload["finding_codes"])
        self.assertNotIn("PASS", lint.stdout)
        self.assertNotIn("freeze", lint.stdout.lower())

        expected = "【镜头角度】\n【景别】\n【前景】\n【远景】"
        output = "【镜头角度】\n低机位\n【前景】\n潜水器\n【远景】\n古神"
        field_lock = subprocess.run(
            [
                "python3",
                str(scripts / "validate_field_lock.py"),
                "--expected-fields",
                expected,
                "--output",
                output,
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(field_lock.returncode, 1, field_lock.stderr + field_lock.stdout)
        self.assertIn("missing_field", json.loads(field_lock.stdout)["finding_codes"])

    def test_legacy_colossal_examples_keep_profile_power_and_runtime_rescue_separate(self):
        examples = TVG / "resources" / "value-profiles" / "cinematic-colossal-realism" / "examples"
        single_pass = (examples / "single-pass-profile-power.md").read_text(encoding="utf-8")
        loop_assisted = (examples / "loop-assisted-image-comparison.md").read_text(encoding="utf-8")
        research_log = (examples / "loop-assisted-research-log.md").read_text(encoding="utf-8")
        self.assertIn("single_pass_profile_power", single_pass)
        self.assertIn("profile_control_power: partial", single_pass)
        self.assertIn("loop_assisted_profile_use", loop_assisted)
        self.assertIn("does not prove the profile is generally strong", loop_assisted)
        self.assertIn("colossal-pressure", loop_assisted)
        self.assertIn("Loop-Assisted Research Log", research_log)

    def test_generic_atlas_contract_preserves_profile_and_human_ownership(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        profile = (profile_dir / "profile.md").read_text(encoding="utf-8")
        workflow = (profile_dir / "examples" / "atlas-search-workflow.md").read_text(
            encoding="utf-8"
        )
        contract = json.loads((TVG / "resources" / "atlas-search-contract.json").read_text(encoding="utf-8"))
        self.assertIn("9 -> 3 -> 9", workflow)
        self.assertIn("search freeze is not final artifact freeze", workflow.lower())
        self.assertIn("post-generation agentic delivery audit", json.dumps(contract))
        self.assertEqual(contract["candidate_id_policy"], "Rnn-E01 through Rnn-E09 in row-major order")
        self.assertEqual(contract["delivery_layouts"], {"direct": "1x1", "shortlist": "2x2"})
        self.assertIn("objectively sufficient", contract["delivery_modes"]["direct"])
        self.assertIn("user taste authority", contract["delivery_modes"]["shortlist"])
        self.assertIn("remains internal", contract["delivery_modes"]["internal-exploration"])
        self.assertIn("output evidence", contract["delivery_modes"]["final-master"])
        self.assertIn("every active scene adapter", contract["profile_evidence"])
        self.assertIn("no delivery board", contract["blocked_run_policy"])
        self.assertIn("colossal-pressure", profile)
        self.assertEqual(contract["script_boundary"], "support_only_agentic_audit_required")

    def test_generic_atlas_trace_example_validates(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        validator = TVG / "scripts" / "atlas" / "validate_trace.py"
        example = profile_dir / "examples" / "atlas-search-trace.example.json"
        result = subprocess.run(
            ["python3", str(validator), str(example), "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertTrue(report["valid"])
        self.assertEqual(report["profile"], "cinematic-visual-direction")
        self.assertEqual(report["round_count"], 2)
        self.assertNotIn("PASS", result.stdout)

    def test_generic_atlas_trace_example_profile_and_adapter_hashes_match_packaged_sources(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        example_path = profile_dir / "examples" / "atlas-search-trace.example.json"
        payload = json.loads(example_path.read_text(encoding="utf-8"))
        profile = payload["profile_snapshot"]
        self.assertEqual(
            profile["sha256"],
            hashlib.sha256((example_path.parent / profile["path"]).resolve().read_bytes()).hexdigest(),
        )
        for adapter in profile["adapters"]:
            self.assertEqual(
                adapter["sha256"],
                hashlib.sha256((example_path.parent / adapter["path"]).resolve().read_bytes()).hexdigest(),
            )

    def test_generic_atlas_trace_rejects_control_boundary_failures(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        validator = TVG / "scripts" / "atlas" / "validate_trace.py"
        example = json.loads(
            (profile_dir / "examples" / "atlas-search-trace.example.json").read_text(
                encoding="utf-8"
            )
        )
        cases = []
        missing_profile = json.loads(json.dumps(example))
        missing_profile["profile_snapshot"] = None
        cases.append((missing_profile, "profile_snapshot: expected an object"))

        missing_profile_hash = json.loads(json.dumps(example))
        missing_profile_hash["profile_snapshot"].pop("sha256")
        cases.append((missing_profile_hash, "profile_snapshot.sha256"))

        missing_adapter_hash = json.loads(json.dumps(example))
        missing_adapter_hash["profile_snapshot"]["adapters"][0].pop("sha256")
        cases.append((missing_adapter_hash, "profile_snapshot.adapters[0].sha256"))

        broken_lineage = json.loads(json.dumps(example))
        broken_lineage["rounds"][1]["candidates"][3]["parent_candidate_id"] = "R00-E02"
        cases.append((broken_lineage, "row lineage must map"))

        no_search_freeze = json.loads(json.dumps(example))
        no_search_freeze["rounds"][-1]["selection"]["gate_result"] = "return-remediate"
        no_search_freeze["rounds"][-1]["selection"]["next_round_positive_value_hypothesis"] = "Another round may help."
        for review in no_search_freeze["rounds"][-1]["selection"]["parent_reviews"]:
            review["next_gain_hypothesis"] = "Another round may help."
            review["exit_rationale"] = None
        cases.append((no_search_freeze, "delivery requires the final round to reach a search-freeze gate"))

        no_delivery_audit = json.loads(json.dumps(example))
        no_delivery_audit["delivery"].pop("delivery_audit")
        cases.append((no_delivery_audit, "delivery.delivery_audit: expected an object"))

        no_delivery_boundary = json.loads(json.dumps(example))
        no_delivery_boundary["delivery"].pop("delivery_boundary")
        cases.append((no_delivery_boundary, "delivery.delivery_boundary: expected an object"))

        ready_with_veto = json.loads(json.dumps(example))
        ready_with_veto["delivery"]["candidates"][0]["veto_findings"] = ["primary read is split"]
        cases.append((ready_with_veto, "ready delivery audit requires no candidate veto findings"))

        skipped_with_residue = json.loads(json.dumps(example))
        skipped_with_residue["finalization"] = {
            "state": "skipped",
            "mode": None,
            "selected_shortlist_ids": ["S01"],
            "outputs": [],
            "reason": "Stopped by user.",
        }
        cases.append((skipped_with_residue, "skipped finalization requires null mode"))

        post_hoc_without_warning = json.loads(json.dumps(example))
        post_hoc_without_warning["rounds"][0]["candidates"][0]["intent_source"] = "post-hoc-with-warning"
        post_hoc_without_warning["rounds"][-1]["selection"]["gate_result"] = "search-freeze"
        cases.append((post_hoc_without_warning, "post-hoc R00 intent requires search-freeze-with-review-bound-warning"))

        for payload, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                trace = Path(tmp) / "trace.json"
                trace.write_text(json.dumps(payload), encoding="utf-8")
                result = subprocess.run(
                    ["python3", str(validator), str(trace)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn(expected, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_generic_atlas_trace_accepts_blocked_run_and_deterministic_compose(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        validator = TVG / "scripts" / "atlas" / "validate_trace.py"
        example = json.loads(
            (profile_dir / "examples" / "atlas-search-trace.example.json").read_text(
                encoding="utf-8"
            )
        )

        blocked = json.loads(json.dumps(example))
        blocked["rounds"][-1]["selection"]["gate_result"] = "blocked"
        blocked["delivery"] = None
        blocked["finalization"] = {
            "state": "skipped",
            "mode": None,
            "selected_shortlist_ids": [],
            "outputs": [],
            "reason": "Required runtime evidence is unavailable.",
        }

        composed = json.loads(json.dumps(example))
        composed["delivery"]["generation_mode"] = "deterministic-compose"
        composed["delivery"]["generation"] = {
            "composition_manifest_path": "artifacts/shortlist-compose.json",
            "composition_manifest_sha256": "0" * 64,
            "raw_atlas_path": "artifacts/shortlist-raw.png",
            "raw_atlas_sha256": "0" * 64,
            "labeled_atlas_path": "artifacts/shortlist-labeled.png",
            "labeled_atlas_sha256": "0" * 64,
        }

        for payload in (blocked, composed):
            with self.subTest(mode=payload.get("delivery", {}).get("generation_mode") if payload.get("delivery") else "blocked"), tempfile.TemporaryDirectory() as tmp:
                trace = Path(tmp) / "trace.json"
                trace.write_text(json.dumps(payload), encoding="utf-8")
                result = subprocess.run(
                    ["python3", str(validator), str(trace)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_generic_atlas_trace_accepts_bounded_direct_delivery_and_legacy_shortlist(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        validator = TVG / "scripts" / "atlas" / "validate_trace.py"
        example = json.loads(
            (profile_dir / "examples" / "atlas-search-trace.example.json").read_text(
                encoding="utf-8"
            )
        )

        direct = json.loads(json.dumps(example))
        candidate = direct["delivery"]["candidates"][0]
        candidate["id"] = "D01"
        candidate["region"] = {"row": 1, "column": 1}
        direct["delivery"].update(
            {
                "mode": "direct",
                "layout": "1x1",
                "delivery_boundary": {
                    "objective_sufficiency_confirmed": True,
                    "material_user_choice_remaining": False,
                    "rationale": "One result satisfies the fixed brief and no remaining taste choice changes the outcome.",
                },
                "candidates": [candidate],
                "delivery_audit": {
                    "result": "ready-for-direct-delivery",
                    "audit_role": "agentic",
                    "rationale": "The single result is objectively sufficient for the fixed brief.",
                    "warnings": [],
                },
            }
        )
        direct["finalization"] = {
            "state": "completed",
            "mode": "accept-tile",
            "selected_delivery_ids": ["D01"],
            "outputs": [
                {
                    "source_delivery_id": "D01",
                    "path": "artifacts/direct-final.png",
                    "sha256": "0" * 64,
                }
            ],
            "reason": "The sufficient direct result is the final master.",
        }

        legacy = json.loads(json.dumps(example))
        legacy["schema_version"] = "tvg-atlas-trace-v1"
        legacy["delivery"].pop("delivery_boundary")

        for payload in (direct, legacy):
            with self.subTest(schema=payload["schema_version"]), tempfile.TemporaryDirectory() as tmp:
                trace = Path(tmp) / "trace.json"
                trace.write_text(json.dumps(payload), encoding="utf-8")
                result = subprocess.run(
                    ["python3", str(validator), str(trace)],
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

        invalid_direct = json.loads(json.dumps(direct))
        invalid_direct["delivery"]["delivery_boundary"]["material_user_choice_remaining"] = True
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.json"
            trace.write_text(json.dumps(invalid_direct), encoding="utf-8")
            result = subprocess.run(
                ["python3", str(validator), str(trace)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("direct delivery requires false", result.stdout)

    def test_generic_atlas_trace_checks_completed_output_bytes(self):
        profile_dir = TVG / "resources" / "value-profiles" / "cinematic-visual-direction"
        validator = TVG / "scripts" / "atlas" / "validate_trace.py"
        payload = json.loads(
            (profile_dir / "examples" / "atlas-search-trace.example.json").read_text(
                encoding="utf-8"
            )
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def write_evidence(relative_path, content):
                target = root / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                return hashlib.sha256(content).hexdigest()

            profile_bytes = b"fixed profile snapshot\n"
            payload["profile_snapshot"]["path"] = "profile.md"
            payload["profile_snapshot"]["sha256"] = write_evidence("profile.md", profile_bytes)
            payload["profile_snapshot"]["adapters"] = []
            write_evidence("artifacts/prompts.json", b"{}\n")

            for round_record in payload["rounds"]:
                generation = round_record["generation"]
                for file_key, hash_key in (
                    ("prompt_path", "prompt_sha256"),
                    ("raw_atlas_path", "raw_atlas_sha256"),
                    ("labeled_atlas_path", "labeled_atlas_sha256"),
                ):
                    generation[hash_key] = write_evidence(generation[file_key], file_key.encode())

            delivery_generation = payload["delivery"]["generation"]
            for file_key, hash_key in (
                ("prompt_path", "prompt_sha256"),
                ("raw_atlas_path", "raw_atlas_sha256"),
                ("labeled_atlas_path", "labeled_atlas_sha256"),
            ):
                delivery_generation[hash_key] = write_evidence(
                    delivery_generation[file_key], file_key.encode()
                )

            output_hash = write_evidence("artifacts/final.png", b"final image bytes")
            payload["finalization"] = {
                "state": "completed",
                "mode": "accept-tile",
                "selected_shortlist_ids": ["S01"],
                "outputs": [
                    {
                        "source_shortlist_id": "S01",
                        "path": "artifacts/final.png",
                        "sha256": output_hash,
                    }
                ],
                "reason": "The user selected S01.",
            }
            trace = root / "trace.json"
            trace.write_text(json.dumps(payload), encoding="utf-8")

            result = subprocess.run(
                ["python3", str(validator), str(trace), "--check-files"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

            (root / "artifacts" / "final.png").write_bytes(b"tampered")
            result = subprocess.run(
                ["python3", str(validator), str(trace), "--check-files"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("finalization.outputs[0].sha256: hash does not match", result.stdout)

    @unittest.skipUnless(PILLOW_AVAILABLE, "Pillow is required for atlas tests")
    def test_generic_atlas_labeler_adds_round_ids_and_visible_lineage(self):
        from PIL import Image, ImageChops

        labeler = TVG / "scripts" / "atlas" / "label_atlas.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "atlas.png"
            output = root / "labeled.png"
            lineage = root / "lineage.json"
            Image.new("RGB", (90, 90), (110, 120, 130)).save(source)
            lineage.write_text(json.dumps({f"R02-E{i:02d}": "R01-E04" for i in range(1, 10)}))
            result = subprocess.run(
                [
                    sys.executable, str(labeler), "--input", str(source), "--output", str(output),
                    "--layout", "3x3", "--id-prefix", "R02-E", "--lineage-json", str(lineage),
                    "--font-size", "10", "--json",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["schema_version"], "tvg-atlas-labels-v1")
            self.assertEqual(report["source"]["decoded_width"], 90)
            self.assertEqual(report["source"]["decoded_height"], 90)
            self.assertEqual(len(report["source"]["sha256"]), 64)
            self.assertEqual([item["id"] for item in report["regions"]], [f"R02-E{i:02d}" for i in range(1, 10)])
            self.assertEqual(report["regions"][0]["parent_candidate_ids"], ["R01-E04"])
            self.assertEqual(report["regions"][-1]["pixel_box"], [60, 60, 90, 90])
            with Image.open(source) as before, Image.open(output) as after:
                self.assertEqual(after.size, before.size)
                self.assertIsNotNone(ImageChops.difference(before, after).getbbox())

    @unittest.skipUnless(PILLOW_AVAILABLE, "Pillow is required for atlas tests")
    def test_generic_atlas_selection_board_crops_only_supplied_ids(self):
        from PIL import Image

        labeler = TVG / "scripts" / "atlas" / "label_atlas.py"
        selector = TVG / "scripts" / "atlas" / "build_selection_board.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "atlas.png"
            labels = root / "labels.json"
            labeled = root / "labeled.png"
            selected = root / "selected.png"
            Image.new("RGB", (90, 90), (100, 110, 120)).save(source)
            label_result = subprocess.run(
                [sys.executable, str(labeler), "--input", str(source), "--output", str(labeled),
                 "--layout", "3x3", "--id-prefix", "R00-E", "--json-output", str(labels)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(label_result.returncode, 0, label_result.stderr)
            self.assertEqual(Path(label_result.stdout.strip()), labels)
            result = subprocess.run(
                [sys.executable, str(selector), "--input", str(source), "--labels-json", str(labels),
                 "--selected", "R00-E01", "R00-E05", "R00-E09", "--output", str(selected), "--json"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual([item["id"] for item in report["selected"]], ["R00-E01", "R00-E05", "R00-E09"])
            self.assertTrue(selected.is_file())

    @unittest.skipUnless(PILLOW_AVAILABLE, "Pillow is required for atlas tests")
    def test_generic_atlas_selection_rejects_labels_from_wrong_same_size_image(self):
        from PIL import Image

        labeler = TVG / "scripts" / "atlas" / "label_atlas.py"
        selector = TVG / "scripts" / "atlas" / "build_selection_board.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_a = root / "a.png"
            source_b = root / "b.png"
            labels = root / "labels.json"
            labeled = root / "labeled.png"
            selected = root / "selected.png"
            Image.new("RGB", (90, 90), (100, 110, 120)).save(source_a)
            Image.new("RGB", (90, 90), (120, 110, 100)).save(source_b)
            labeled_result = subprocess.run(
                [
                    sys.executable, str(labeler), "--input", str(source_a), "--output", str(labeled),
                    "--layout", "3x3", "--id-prefix", "R00-E", "--json-output", str(labels),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(labeled_result.returncode, 0, labeled_result.stderr)
            selected_result = subprocess.run(
                [
                    sys.executable, str(selector), "--input", str(source_b), "--labels-json", str(labels),
                    "--selected", "R00-E01", "R00-E05", "R00-E09", "--output", str(selected),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(selected_result.returncode, 2)
            self.assertIn("source digest does not match", selected_result.stderr)
            self.assertFalse(selected.exists())

    @unittest.skipUnless(PILLOW_AVAILABLE, "Pillow is required for atlas tests")
    def test_generic_atlas_selection_rejects_reordered_or_out_of_bounds_regions(self):
        from PIL import Image

        labeler = TVG / "scripts" / "atlas" / "label_atlas.py"
        selector = TVG / "scripts" / "atlas" / "build_selection_board.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "atlas.png"
            labels = root / "labels.json"
            labeled = root / "labeled.png"
            Image.new("RGB", (90, 90), (100, 110, 120)).save(source)
            result = subprocess.run(
                [
                    sys.executable, str(labeler), "--input", str(source), "--output", str(labeled),
                    "--layout", "3x3", "--id-prefix", "R00-E", "--json-output", str(labels),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(labels.read_text(encoding="utf-8"))
            cases = (
                (list(reversed(payload["regions"])), "row-major order"),
                ([{**payload["regions"][0], "pixel_box": [0, 0, 91, 30]}, *payload["regions"][1:]], "outside the declared layout"),
            )
            for regions, expected in cases:
                with self.subTest(expected=expected):
                    payload["regions"] = regions
                    labels.write_text(json.dumps(payload), encoding="utf-8")
                    selected = root / f"selected-{expected[:3]}.png"
                    selected_result = subprocess.run(
                        [
                            sys.executable, str(selector), "--input", str(source), "--labels-json", str(labels),
                            "--selected", "R00-E01", "R00-E05", "R00-E09", "--output", str(selected),
                        ],
                        text=True,
                        capture_output=True,
                    )
                    self.assertEqual(selected_result.returncode, 2)
                    self.assertIn(expected, selected_result.stderr)


if __name__ == "__main__":
    unittest.main()
