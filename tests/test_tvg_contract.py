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

    def test_skill_exposes_state_driven_grounded_insight_loop(self):
        text = (TVG / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "state-driven value-gain loop",
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
        ):
            self.assertIn(phrase, combined)

    def test_value_profile_schema_and_scripts_preserve_agentic_boundary(self):
        skill = (TVG / "SKILL.md").read_text(encoding="utf-8")
        method = (TVG / "resources" / "methodology.md").read_text(encoding="utf-8")
        schema = (TVG / "resources" / "trace-record-schema.json").read_text(encoding="utf-8")
        combined = skill + "\n" + method + "\n" + schema
        for phrase in (
            "value_profile",
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
            "must not decide whether a value profile is true, complete, aesthetically successful, or sufficient for exit",
        ):
            self.assertIn(phrase, combined)

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
            self.assertEqual(profile["mode"], "supplied")
            self.assertEqual(profile["name"], "Shaw Brothers studio-era wuxia/fantasy")
            self.assertEqual(
                profile["good_means"],
                ["set-built theatricality is expressed through composition and blocking"],
            )
            self.assertEqual(profile["bad_means"], ["generic modern AI video prompt inflation"])
            self.assertEqual(profile["derived_axes"], ["studio-theatricality-depth"])
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
                profile["profile_veto_constraints"],
                ["must not infer style rules from the flawed expansion sample"],
            )
            self.assertIn("value_profile_truth", data["script_support"]["script_cannot_decide"])
            self.assertIn("aesthetic_success", data["script_support"]["script_cannot_decide"])

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)
            self.assertIn("agentic audit is still required", validation.stdout)

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
            data["value_profile"]["good_means"] = "not-a-list"
            data["value_profile"]["prompt_self_audit_questions"] = "not-a-list"
            data["value_profile"]["image_self_audit_questions"] = "not-a-list"
            data["value_profile"]["source_notes"] = "not-a-list"
            trace.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            validation = subprocess.run(
                ["python3", str(validate), str(trace)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 1)
            self.assertIn("value_profile.mode: unsupported value 'scored'", validation.stdout)
            self.assertIn("value_profile.good_means: expected list", validation.stdout)
            self.assertIn("value_profile.prompt_self_audit_questions: expected list", validation.stdout)
            self.assertIn("value_profile.image_self_audit_questions: expected list", validation.stdout)
            self.assertIn("value_profile.source_notes: expected list", validation.stdout)

    def test_default_practical_value_profile_resource_exists(self):
        path = TVG / "resources" / "value-profiles" / "default-practical-value.md"
        self.assertTrue(path.exists(), "missing default practical-value profile resource")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Default Practical-Value Profile",
            "mode: default",
            "decision / action leverage",
            "evidence honesty",
            "handoff usability",
            "risk reduction",
            "reuse without overfitting",
            "execution readiness",
            "This profile is the fallback when no supplied or project default profile is active.",
        ):
            self.assertIn(phrase, text)

    def test_shaw_brothers_profile_resource_exists_and_rejects_sample_contamination(self):
        path = TVG / "resources" / "value-profiles" / "shaw-brothers-wuxia-fantasy.md"
        self.assertTrue(path.exists(), "missing Shaw Brothers wuxia/fantasy value profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "Shaw Brothers Studio-Era Wuxia / Fantasy Cinematic Prompt Profile",
            "mode: supplied",
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
        ):
            self.assertIn(phrase, text)

    def test_shaw_value_profile_pilot_record_contains_storyboard_and_image_audit(self):
        path = REPO / "tests" / "tvg_value_profile_shaw_pilot_clean_room_2026-06-10.md"
        self.assertTrue(path.exists(), "missing clean-room Shaw value-profile pilot record")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "TVG Value Profile Clean-Room Pilot: Shaw Brothers Snow Mountain Storyboard",
            "active_value_profile: Shaw Brothers studio-era wuxia / fantasy cinematic prompt profile",
            "profile_source_rule: do not infer Shaw Brothers rules from the flawed expansion sample",
            "多镜头分镜提示词",
            "Shot 01",
            "shot_count_decision",
            "shot_count_not_preset: true",
            "single_page_storyboard_image",
            "Image2 Pass 1",
            "Image Self-Audit",
            "single-page storyboard sheet",
            "modern xianxia",
            "modern CG spectacle",
            "naturalistic disaster film",
            "generic AI video prompt inflation",
            "source_attribution_audit",
            "original_script_source",
            "profile_source",
            "independent_storyboard_judgment",
            "possible_pollution_or_uncertainty",
            "claim_supported",
            "evidence_ceiling",
        ):
            self.assertIn(phrase, text)
        self.assertNotIn("shot_count_decision: preset", text)

    def test_king_hu_wuxia_profile_resource_exists_and_is_scoped(self):
        path = TVG / "resources" / "value-profiles" / "king-hu-wuxia-cinema.md"
        self.assertTrue(path.exists(), "missing King Hu wuxia value profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "King Hu Wuxia Cinema Prompt / Storyboard Profile",
            "mode: supplied",
            "scoped profile for cinematic prompt and storyboard image generation",
            "not a universal definition of all King Hu films",
            "Beijing opera",
            "dance-like combat",
            "inn / confined-space faction choreography",
            "widescreen compositions full of graceful character movement",
            "delayed spectacle",
            "spiritual or philosophical pressure",
            "female knight-errant",
            "modern wire-fu inflation",
            "generic AI wuxia trailer inflation",
            "prompt_self_audit_questions",
            "image_self_audit_questions",
            "source_notes",
        ):
            self.assertIn(phrase, text)

    def test_king_hu_profile_self_iteration_record_exists(self):
        path = REPO / "tests" / "tvg_value_profile_king_hu_self_iteration_2026-06-10.md"
        self.assertTrue(path.exists(), "missing King Hu profile self-iteration record")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "TVG Self-Iteration: King Hu Wuxia Cinema Profile",
            "iteration_mode: profile_self_iteration",
            "v1_audit_result: return-remediate",
            "v2_audit_result: freeze-with-review-bound-warning",
            "what_changed",
            "delayed spectacle before action payoff",
            "spatial intelligence before action density",
            "avoid generic AI wuxia trailer inflation",
            "source_attribution_audit",
            "claim_supported",
            "evidence_ceiling",
        ):
            self.assertIn(phrase, text)

    def test_king_hu_profile_rejects_shaw_cleanwater_bay_pollution(self):
        path = TVG / "resources" / "value-profiles" / "king-hu-wuxia-cinema.md"
        self.assertTrue(path.exists(), "missing King Hu wuxia value profile")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "do not use Shaw Brothers Clear Water Bay / Movietown backlot theatricality as a King Hu proxy",
            "do not use saturated red-blue Shaw-style hard-light spectacle as the default color logic",
            "natural or architectural space",
            "ruined fort, inn, courtyard, temple, bamboo, desert edge, mountain path, or village threshold",
            "glimpse editing must be translated into partial visibility, occlusion, offscreen implication, or panel sequencing",
            "the original snow mountain / qilin script is a story constraint, not King Hu evidence",
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
            self.assertEqual(data["schema_version"], "tvg-trace-v0.3")
            self.assertEqual(data["method_version"], "Thinking Value-Gain Methodology v0.3")
            self.assertEqual(
                data["value_gain"]["veto_constraints"],
                ["must not claim production readiness without runtime proof"],
            )
            self.assertIn("audit_role", data["agentic_exit_audit"])
            self.assertIn("auditor_independence", data["agentic_exit_audit"])
            self.assertIn("veto_constraint_result", data["agentic_exit_audit"])
            self.assertIn("veto_constraints", data["script_support"]["script_cannot_decide"])
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
