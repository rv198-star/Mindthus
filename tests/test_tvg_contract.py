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
