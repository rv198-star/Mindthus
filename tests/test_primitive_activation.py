import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "primitives" / "check.py"
WHOLE_ELEPHANT_SCRIPT = ROOT / "scripts" / "primitives" / "validate_whole_elephant.py"
MANIFEST = ROOT / "scripts" / "primitives" / "manifest.json"


def run_check(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def run_whole_elephant_validator(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        audit_path = Path(tmp) / "audit.json"
        audit_path.write_text(json.dumps(payload), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(WHOLE_ELEPHANT_SCRIPT), str(audit_path)],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )


def formal_answer_plan(canonical_subject: str) -> dict:
    return {
        "opening_core_thesis": f"{canonical_subject} must be defined by its primary value carrier, not by a locally true interface.",
        "canonical_subject": canonical_subject,
        "definition_disposition": "reject_as_definition",
        "local_truth_boundary": "The local signal is valid evidence or interface, not the whole definition.",
        "definition_consequence": "A wrong definition shifts optimization toward the local surface and away from the target result.",
        "optimization_misdirection": "surface optimization over target-result control",
        "forbidden_answer_forms": [
            "score_as_concession",
            "soft_not_wrong_concession",
            "runtime_also_matters_only",
            "umbrella_context_as_thesis_subject",
        ],
    }


def variant_calibration() -> dict:
    return {
        "variant_map": [
            "lightweight local-signal-led variant",
            "composite target-result-led variant",
        ],
        "primary_value_distribution": (
            "the local signal may dominate common lightweight usage, while the "
            "composite variant may carry higher-value stability and decision control"
        ),
        "control_owner_shift": (
            "in one variant the system serves the local signal; in another the local "
            "signal serves the target-result control surface"
        ),
    }


class PrimitiveActivationTests(unittest.TestCase):
    def test_manifest_event_activation_and_primitive_triggers_stay_bidirectional(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        events = manifest["events"]
        primitives = manifest["primitives"]

        for event_name, event in events.items():
            event_primitives = set(event["active_primitives"])
            for item in event.get("conditional_primitives", []):
                event_primitives.add(item["primitive"])
            for primitive_id in event_primitives:
                self.assertIn(
                    event_name,
                    primitives[primitive_id]["trigger"],
                    f"{primitive_id} is active for {event_name} but does not list that trigger",
                )

        for primitive_id, primitive in primitives.items():
            for event_name in primitive["trigger"]:
                event = events[event_name]
                active_or_conditional = set(event["active_primitives"])
                active_or_conditional.update(
                    item["primitive"] for item in event.get("conditional_primitives", [])
                )
                self.assertIn(
                    primitive_id,
                    active_or_conditional,
                    f"{primitive_id} lists {event_name} but the event does not activate it",
                )

    def test_manifest_validator_rejects_activation_trigger_mismatch(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        manifest["primitives"]["whole_elephant_protocol"]["trigger"] = ["before-route"]

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_check(
                "--event",
                "before-answer",
                "--method",
                "using-mindthus",
                "--manifest",
                str(manifest_path),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "events.before-answer.active_primitives includes whole_elephant_protocol but primitive trigger does not include before-answer",
            result.stdout,
        )

    def test_before_answer_activates_aop_answer_aspects(self) -> None:
        result = run_check("--event", "before-answer", "--method", "using-mindthus", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)

        self.assertEqual(report["script_verdict"], "shape_only")
        self.assertEqual(report["event"], "before-answer")
        self.assertEqual(
            [item["id"] for item in report["active_primitives"]],
            [
                "whole_elephant_protocol",
                "core_thesis_extraction",
                "first_sentence_stress_test",
                "essence_wording_guard",
            ],
        )
        self.assertIn("build_compact_visible_audit", report["required_agent_checks"])
        self.assertIn("start_formal_answer_with_core_thesis", report["required_agent_checks"])
        self.assertIn("ensure_no_second_question_gap", report["required_agent_checks"])

        first_sentence = next(
            item for item in report["active_primitives"] if item["id"] == "first_sentence_stress_test"
        )
        self.assertIn("target_result", first_sentence["output_shape"])
        self.assertIn("corrected_owner_or_carrier", first_sentence["output_shape"])
        self.assertIn("final_say_language", first_sentence["output_shape"])
        self.assertIn("controller_inversion", first_sentence["output_shape"])
        self.assertIn("local_interface_role", first_sentence["output_shape"])
        self.assertIn("optimization_consequence", first_sentence["output_shape"])
        self.assertIn("name-global-thesis-first", first_sentence["action_effect"])
        self.assertIn("deny-local-definition-authority", first_sentence["action_effect"])
        self.assertIn("translate-definition-authority-to-final-say", first_sentence["action_effect"])
        self.assertIn("name-controller-inversion-when-variants-differ", first_sentence["action_effect"])

    def test_before_route_activates_frame_fitness_shape_only_reminder(self) -> None:
        result = run_check("--event", "before-route", "--method", "using-mindthus", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)

        self.assertEqual(report["script_verdict"], "shape_only")
        self.assertIs(report["agentic_judgment_required"], True)
        self.assertEqual(
            [item["id"] for item in report["active_primitives"]],
            [
                "minimal_sufficient_lens",
                "frame_fitness_check",
                "whole_elephant_protocol",
                "evidence_claim_ceiling",
            ],
        )
        self.assertIn(
            "is_a_local_frame_claiming_global_authority",
            report["required_agent_checks"],
        )
        self.assertIn(
            "if_partial_truth_triggers_validate_whole_elephant_audit",
            report["required_agent_checks"],
        )
        frame = next(
            item for item in report["active_primitives"] if item["id"] == "frame_fitness_check"
        )
        self.assertEqual(
            frame["output_shape"],
            [
                "true_question",
                "packed_premises",
                "layer_risks",
                "frame_status",
                "reframed_question",
                "routing_decision",
            ],
        )
        self.assertEqual(frame["frame_status_values"], ["clean", "biased", "overloaded", "malformed"])
        self.assertEqual(
            frame["routing_effect"],
            {
                "clean": "normal-route",
                "biased": "name-bias-then-route",
                "overloaded": "split-propositions-then-route",
                "malformed": "correct-question-before-analysis",
            },
        )
        self.assertIn("frame_correctness", report["script_must_not_decide"])

        whole = next(
            item for item in report["active_primitives"] if item["id"] == "whole_elephant_protocol"
        )
        self.assertEqual(
            whole["output_shape"],
            [
                "object_hierarchy",
                "user_named_object_relation",
                "canonical_object",
                "formal_thesis_subject",
                "umbrella_context",
                "subject_alignment_reason",
                "whole_object_reconstruction",
                "variant_map",
                "primary_value_distribution",
                "control_owner_shift",
                "formal_answer_plan",
                "whole_object",
                "local_success_points",
                "strategy_choice",
                "corrected_thesis",
                "definition_owner",
                "result_controller",
                "decision_consequence",
            ],
        )

    def test_frame_fitness_manifest_preserves_shape_only_boundary(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        primitive = manifest["primitives"]["frame_fitness_check"]

        self.assertEqual(primitive["name"], "Frame Fitness Check / 定框适配检查")
        self.assertIn("before-route", primitive["trigger"])
        self.assertIn("preserve-frame", primitive["action_effect"])
        self.assertIn("qualify-frame", primitive["action_effect"])
        self.assertIn("reframe", primitive["action_effect"])
        self.assertIn("block-pending-evidence", primitive["action_effect"])
        self.assertIn("contrarianism-engine", primitive["not_a"])
        self.assertIn("semantic-judge", primitive["not_a"])
        self.assertEqual(
            primitive["output_shape"],
            [
                "true_question",
                "packed_premises",
                "layer_risks",
                "frame_status",
                "reframed_question",
                "routing_decision",
            ],
        )
        self.assertEqual(primitive["frame_status_values"], ["clean", "biased", "overloaded", "malformed"])
        self.assertEqual(
            primitive["routing_effect"],
            {
                "clean": "normal-route",
                "biased": "name-bias-then-route",
                "overloaded": "split-propositions-then-route",
                "malformed": "correct-question-before-analysis",
            },
        )

    def test_routing_effect_keys_must_match_frame_status_values(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        frame = manifest["primitives"]["frame_fitness_check"]
        frame["routing_effect"] = {"clean": "normal-route"}

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_check(
                "--event",
                "before-route",
                "--method",
                "using-mindthus",
                "--manifest",
                str(manifest_path),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("routing_effect keys must match frame_status_values", result.stdout)

    def test_routing_effect_requires_frame_status_values(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        frame = manifest["primitives"]["frame_fitness_check"]
        frame.pop("frame_status_values")

        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = run_check(
                "--event",
                "before-route",
                "--method",
                "using-mindthus",
                "--manifest",
                str(manifest_path),
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("routing_effect requires frame_status_values", result.stdout)

    def test_whole_elephant_manifest_preserves_shape_only_boundary(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        primitive = manifest["primitives"]["whole_elephant_protocol"]

        self.assertEqual(primitive["name"], "Whole Elephant Protocol / 全象流程")
        self.assertIn("before-route", primitive["trigger"])
        self.assertIn("validate-whole-elephant-audit", primitive["action_effect"])
        self.assertIn("semantic-judge", primitive["not_a"])
        self.assertIn("definition-decider", primitive["not_a"])
        self.assertEqual(
            primitive["output_shape"],
            [
                "object_hierarchy",
                "user_named_object_relation",
                "canonical_object",
                "formal_thesis_subject",
                "umbrella_context",
                "subject_alignment_reason",
                "whole_object_reconstruction",
                "variant_map",
                "primary_value_distribution",
                "control_owner_shift",
                "formal_answer_plan",
                "whole_object",
                "local_success_points",
                "strategy_choice",
                "corrected_thesis",
                "definition_owner",
                "result_controller",
                "decision_consequence",
            ],
        )

    def test_whole_elephant_validator_accepts_complete_shape_only_audit(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "green tests",
                    "whole_object": "release readiness",
                    "component_layer": "test suite",
                    "role_layer": "regression signal",
                },
                "whole_object": "release readiness",
                "user_named_object_relation": "component_or_interface",
                "local_success_points": [
                    "green tests are real readiness evidence",
                    "pricing complaints are real value evidence",
                ],
                "strategy_choice": "whole_first_re_evaluation",
                "corrected_thesis": "Release readiness is carried by safe and recoverable shipping capability, not green tests alone.",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery system",
                "subject_alignment_reason": "release readiness is the object being judged; delivery system is context",
                "whole_object_reconstruction": {
                    "target_job": "ship useful changes safely",
                    "main_use_cases": "release, rollback, and recovery decisions",
                    "primary_value_carrier": "operational safety and rollout control",
                    "local_interface_role": "green tests as regression evidence",
                },
                "formal_answer_plan": formal_answer_plan("release readiness"),
                "definition_owner": "safe and recoverable release capability",
                "result_controller": "rollback, monitoring, rollout, and evidence gates",
                "decision_consequence": "do not ship solely because tests are green",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("script_verdict: shape_only", result.stdout)
        self.assertIn("agentic_judgment_required: true", result.stdout)

    def test_whole_elephant_validator_accepts_visible_answer_that_starts_with_core_thesis(self) -> None:
        opening = (
            "Skills are defined by reusable task control, not by the locally valid prompt interface, "
            "so optimizing them as prompt wording misdirects work away from stable task completion."
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skill capability",
                    "component_layer": "prompt text",
                    "role_layer": "attention steering interface",
                },
                "whole_object": "skill capability",
                "canonical_object": "skill capability",
                "formal_thesis_subject": "skill capability",
                "umbrella_context": "agent runtime",
                "subject_alignment_reason": "skill capability is being defined; agent runtime is only context",
                "whole_object_reconstruction": {
                    "target_job": "make task completion stable, reusable, and verifiable",
                    "main_use_cases": "execution, validation, handoff, and recovery",
                    "primary_value_carrier": "scripted task control and verification contract",
                    "local_interface_role": "prompt injection as attention steering",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("skill capability"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["prompt injection is a valid local interface"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "scripted task control and verification contract",
                "result_controller": "scripts, validators, resources, and recovery protocol",
                "decision_consequence": "do not optimize skills as prompt wording",
                "visible_formal_answer": opening
                + " Prompt injection still matters, but only as a subordinate interface.",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_whole_elephant_validator_rejects_core_thesis_that_starts_with_local_concession(self) -> None:
        opening = (
            "Prompt injection is a valid local interface, but skills are defined by reusable task control, "
            "so optimizing them as prompt wording misdirects work away from stable task completion."
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skill capability",
                    "component_layer": "prompt text",
                    "role_layer": "attention steering interface",
                },
                "whole_object": "skill capability",
                "canonical_object": "skill capability",
                "formal_thesis_subject": "skill capability",
                "umbrella_context": "agent runtime",
                "subject_alignment_reason": "skill capability is being defined; agent runtime is only context",
                "whole_object_reconstruction": {
                    "target_job": "make task completion stable, reusable, and verifiable",
                    "main_use_cases": "execution, validation, handoff, and recovery",
                    "primary_value_carrier": "scripted task control and verification contract",
                    "local_interface_role": "prompt injection as attention steering",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("skill capability"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["prompt injection is a valid local interface"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "scripted task control and verification contract",
                "result_controller": "scripts, validators, resources, and recovery protocol",
                "decision_consequence": "do not optimize skills as prompt wording",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "formal_answer_plan.opening_core_thesis must start with the global thesis, not local-truth concession",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_core_thesis_that_over_accommodates_local_truth(self) -> None:
        opening = (
            "Skills are not only prompt injection; scripts and runtime also matter for agent systems."
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skill capability",
                    "component_layer": "prompt text",
                    "role_layer": "attention steering interface",
                },
                "whole_object": "skill capability",
                "canonical_object": "skill capability",
                "formal_thesis_subject": "skill capability",
                "umbrella_context": "agent runtime",
                "subject_alignment_reason": "skill capability is being defined; agent runtime is only context",
                "whole_object_reconstruction": {
                    "target_job": "make task completion stable, reusable, and verifiable",
                    "main_use_cases": "execution, validation, handoff, and recovery",
                    "primary_value_carrier": "scripted task control and verification contract",
                    "local_interface_role": "prompt injection as attention steering",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("skill capability"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["prompt injection is a valid local interface"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "scripted task control and verification contract",
                "result_controller": "scripts, validators, resources, and recovery protocol",
                "decision_consequence": "do not optimize skills as prompt wording",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "formal_answer_plan.opening_core_thesis must not over-accommodate local truth as a generic not-only caveat",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_chinese_local_concession_first(self) -> None:
        opening = (
            "测试通过当然很关键，但 release readiness 还包括回滚、监控和审批。"
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "release readiness",
                    "whole_object": "release readiness",
                    "component_layer": "green tests",
                    "role_layer": "readiness signal",
                },
                "whole_object": "release readiness",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery",
                "subject_alignment_reason": "release readiness is being defined; software delivery is context",
                "whole_object_reconstruction": {
                    "target_job": "ship a useful change safely and recoverably",
                    "main_use_cases": "deploy, observe, recover, and accept residual risk",
                    "primary_value_carrier": "safe recoverable release capability",
                    "local_interface_role": "green tests as readiness evidence",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("release readiness"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["green tests are a strong local readiness signal"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "safe recoverable release capability",
                "result_controller": "rollback, monitoring, rollout, and evidence gates",
                "decision_consequence": "do not define readiness as green tests",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "formal_answer_plan.opening_core_thesis must start with the global thesis, not local-truth concession",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_chinese_not_only_variant_cross_domain(self) -> None:
        opening = (
            "发布准备并非只有测试，还包括回滚、监控、灰度和审批。"
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "release readiness",
                    "whole_object": "release readiness",
                    "component_layer": "green tests",
                    "role_layer": "readiness signal",
                },
                "whole_object": "release readiness",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery",
                "subject_alignment_reason": "release readiness is being defined; software delivery is context",
                "whole_object_reconstruction": {
                    "target_job": "ship a useful change safely and recoverably",
                    "main_use_cases": "deploy, observe, recover, and accept residual risk",
                    "primary_value_carrier": "safe recoverable release capability",
                    "local_interface_role": "green tests as readiness evidence",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("release readiness"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["green tests are a strong local readiness signal"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "safe recoverable release capability",
                "result_controller": "rollback, monitoring, rollout, and evidence gates",
                "decision_consequence": "do not define readiness as green tests",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "formal_answer_plan.opening_core_thesis must not over-accommodate local truth as a generic not-only caveat",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_weak_broader_view_thesis(self) -> None:
        opening = "This needs a broader view."
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "release readiness",
                    "whole_object": "release readiness",
                    "component_layer": "green tests",
                    "role_layer": "readiness signal",
                },
                "whole_object": "release readiness",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery",
                "subject_alignment_reason": "release readiness is being defined; software delivery is context",
                "whole_object_reconstruction": {
                    "target_job": "ship a useful change safely and recoverably",
                    "main_use_cases": "deploy, observe, recover, and accept residual risk",
                    "primary_value_carrier": "safe recoverable release capability",
                    "local_interface_role": "green tests as readiness evidence",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("release readiness"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["green tests are a strong local readiness signal"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "safe recoverable release capability",
                "result_controller": "rollback, monitoring, rollout, and evidence gates",
                "decision_consequence": "do not define readiness as green tests",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "formal_answer_plan.opening_core_thesis must carry definition authority, result control, or optimization consequence",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_chinese_incomplete_concession_first(self) -> None:
        opening = "这个判断有道理但不完整，release readiness 还需要回滚、监控和审批。"
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "release readiness",
                    "whole_object": "release readiness",
                    "component_layer": "green tests",
                    "role_layer": "readiness signal",
                },
                "whole_object": "release readiness",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery",
                "subject_alignment_reason": "release readiness is being defined; software delivery is context",
                "whole_object_reconstruction": {
                    "target_job": "ship a useful change safely and recoverably",
                    "main_use_cases": "deploy, observe, recover, and accept residual risk",
                    "primary_value_carrier": "safe recoverable release capability",
                    "local_interface_role": "green tests as readiness evidence",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("release readiness"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["green tests are a strong local readiness signal"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "safe recoverable release capability",
                "result_controller": "rollback, monitoring, rollout, and evidence gates",
                "decision_consequence": "do not define readiness as green tests",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "formal_answer_plan.opening_core_thesis must start with the global thesis, not local-truth concession",
            result.stdout,
        )

    def test_whole_elephant_validator_allows_global_thesis_with_subordinate_local_importance(self) -> None:
        opening = (
            "发布准备的定义权属于安全可恢复的交付能力，测试也很重要但只是其中一类证据。"
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "release readiness",
                    "whole_object": "release readiness",
                    "component_layer": "green tests",
                    "role_layer": "readiness signal",
                },
                "whole_object": "release readiness",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery",
                "subject_alignment_reason": "release readiness is being defined; software delivery is context",
                "whole_object_reconstruction": {
                    "target_job": "ship a useful change safely and recoverably",
                    "main_use_cases": "deploy, observe, recover, and accept residual risk",
                    "primary_value_carrier": "safe recoverable release capability",
                    "local_interface_role": "green tests as readiness evidence",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("release readiness"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["green tests are a strong local readiness signal"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "safe recoverable release capability",
                "result_controller": "rollback, monitoring, rollout, and evidence gates",
                "decision_consequence": "do not define readiness as green tests",
                "visible_formal_answer": opening,
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_whole_elephant_validator_rejects_missing_variant_calibration(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "spreadsheet formulas",
                    "whole_object": "spreadsheet automation",
                    "component_layer": "formulas",
                    "role_layer": "calculation interface",
                },
                "whole_object": "spreadsheet automation",
                "canonical_object": "spreadsheet automation",
                "formal_thesis_subject": "spreadsheet automation",
                "umbrella_context": "business operations automation",
                "subject_alignment_reason": "spreadsheet automation is being defined; business operations is context",
                "whole_object_reconstruction": {
                    "target_job": "make recurring spreadsheet work repeatable and auditable",
                    "main_use_cases": "calculation, scheduled import, approval, and reporting",
                    "primary_value_carrier": "repeatable workflow control and audit trail",
                    "local_interface_role": "formulas as calculation surface",
                },
                "formal_answer_plan": formal_answer_plan("spreadsheet automation"),
                "local_success_points": ["formulas are a real and common lightweight automation surface"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": "Spreadsheet automation is defined by the variant that carries the target result, not by formulas by default.",
                "definition_owner": "repeatable workflow control and audit trail",
                "result_controller": "scripts, schedules, approvals, imports, formulas, and monitoring",
                "decision_consequence": "do not optimize only formulas when workflow control owns the business result",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("variant_map must be a non-empty list", result.stdout)
        self.assertIn("primary_value_distribution must be a non-empty string", result.stdout)
        self.assertIn("control_owner_shift must be a non-empty string", result.stdout)

    def test_whole_elephant_validator_rejects_single_variant_map(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "variant_map": ["formula-centric spreadsheet automation"],
                "primary_value_distribution": "formulas are common and therefore define automation",
                "control_owner_shift": "scripts serve formulas",
                "object_hierarchy": {
                    "user_named_object": "spreadsheet formulas",
                    "whole_object": "spreadsheet automation",
                    "component_layer": "formulas",
                    "role_layer": "calculation interface",
                },
                "whole_object": "spreadsheet automation",
                "canonical_object": "spreadsheet automation",
                "formal_thesis_subject": "spreadsheet automation",
                "umbrella_context": "business operations automation",
                "subject_alignment_reason": "spreadsheet automation is being defined; business operations is context",
                "whole_object_reconstruction": {
                    "target_job": "make recurring spreadsheet work repeatable and auditable",
                    "main_use_cases": "calculation, scheduled import, approval, and reporting",
                    "primary_value_carrier": "repeatable workflow control and audit trail",
                    "local_interface_role": "formulas as calculation surface",
                },
                "formal_answer_plan": formal_answer_plan("spreadsheet automation"),
                "local_success_points": ["formulas are a real and common lightweight automation surface"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": "Spreadsheet automation is defined by the variant that carries the target result, not by formulas by default.",
                "definition_owner": "repeatable workflow control and audit trail",
                "result_controller": "scripts, schedules, approvals, imports, formulas, and monitoring",
                "decision_consequence": "do not optimize only formulas when workflow control owns the business result",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("variant_map must include at least two candidate variants", result.stdout)

    def test_whole_elephant_validator_allows_single_variant_when_granting_definition(self) -> None:
        opening = (
            "Backup failure is carried by the invalidated service token, so recovery must "
            "restore credential authority before rerunning jobs."
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "variant_map": ["credential rotation invalidated the only backup token"],
                "primary_value_distribution": (
                    "the local credential mechanism carries the whole backup result in this case"
                ),
                "control_owner_shift": (
                    "backup execution depends on credential authority rather than the credential "
                    "being only a surface symptom"
                ),
                "object_hierarchy": {
                    "user_named_object": "credential rotation",
                    "whole_object": "backup failure",
                    "component_layer": "service token",
                    "role_layer": "credential authority",
                },
                "whole_object": "backup failure",
                "canonical_object": "backup failure",
                "formal_thesis_subject": "backup failure",
                "umbrella_context": "backup operations",
                "subject_alignment_reason": "backup failure is being explained; credential rotation is the causal mechanism",
                "whole_object_reconstruction": {
                    "target_job": "complete nightly backup jobs",
                    "main_use_cases": "backup, restore, and incident recovery",
                    "primary_value_carrier": "valid credential authority for every backup job",
                    "local_interface_role": "service token used by backup jobs",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("backup failure"),
                    "opening_core_thesis": opening,
                    "definition_disposition": "grant_as_definition",
                    "local_truth_boundary": "The local credential mechanism owns this failure because every backup job depends on it.",
                    "definition_consequence": "Recovery should restore credential authority before searching for weaker explanations.",
                    "optimization_misdirection": "do not average this with unrelated backup surfaces before fixing the causal owner",
                },
                "local_success_points": ["credential rotation invalidated the only service token"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "component_or_interface",
                "corrected_thesis": opening,
                "definition_owner": "invalidated service token",
                "result_controller": "credential authority for every backup job",
                "decision_consequence": "restore or rotate the service token before rerunning jobs",
                "visible_formal_answer": opening,
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_whole_elephant_validator_allows_same_carrier_interface_for_granted_owner(self) -> None:
        opening = (
            "Backup failure is defined by the invalidated service token because that "
            "single credential controls every backup job."
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "variant_map": ["invalidated service token controls every backup job"],
                "primary_value_distribution": "the same credential mechanism carries the whole backup result",
                "control_owner_shift": "backup jobs serve credential authority; the token is not merely a symptom",
                "object_hierarchy": {
                    "user_named_object": "invalidated service token",
                    "whole_object": "backup failure",
                    "component_layer": "service token",
                    "role_layer": "credential authority",
                },
                "whole_object": "backup failure",
                "canonical_object": "backup failure",
                "formal_thesis_subject": "backup failure",
                "umbrella_context": "backup operations",
                "subject_alignment_reason": "backup failure is being explained; the service token is the causal owner",
                "whole_object_reconstruction": {
                    "target_job": "complete nightly backup jobs",
                    "main_use_cases": "backup, restore, and incident recovery",
                    "primary_value_carrier": "invalidated service token",
                    "local_interface_role": "invalidated service token",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("backup failure"),
                    "opening_core_thesis": opening,
                    "definition_disposition": "grant_as_definition",
                    "local_truth_boundary": "The local service token owns the target result because every backup job depends on it.",
                    "definition_consequence": "Recovery should restore credential authority before searching weaker explanations.",
                    "optimization_misdirection": "do not average this with unrelated backup surfaces before fixing the causal owner",
                },
                "local_success_points": ["the invalidated service token controls every backup job"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "component_or_interface",
                "corrected_thesis": opening,
                "definition_owner": "invalidated service token",
                "result_controller": "credential authority for every backup job",
                "decision_consequence": "restore or rotate the service token before rerunning jobs",
                "visible_formal_answer": opening,
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_whole_elephant_validator_rejects_local_signal_marked_canonical_object(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "green tests",
                    "whole_object": "release readiness",
                    "component_layer": "test suite",
                    "role_layer": "regression signal",
                },
                "whole_object": "release readiness",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery system",
                "subject_alignment_reason": "release readiness is being judged; tests are local evidence",
                "whole_object_reconstruction": {
                    "target_job": "ship useful changes safely",
                    "main_use_cases": "release, rollback, and recovery decisions",
                    "primary_value_carrier": "operational safety and rollout control",
                    "local_interface_role": "green tests as regression evidence",
                },
                "local_success_points": ["green tests are real regression evidence"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": "Release readiness is carried by safe and recoverable shipping capability, not green tests alone.",
                "definition_owner": "safe and recoverable release capability",
                "result_controller": "rollout, observability, rollback, and evidence gates",
                "decision_consequence": "do not ship based on green tests alone",
                "formal_answer_plan": formal_answer_plan("release readiness"),
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "user_named_object_relation cannot be canonical_object when user_named_object is not aligned with canonical_object",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_corrected_thesis_that_contradicts_plan(self) -> None:
        opening = (
            "Release readiness is carried by safe recoverable shipping capability, "
            "so green tests cannot define readiness by themselves."
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "release readiness",
                    "whole_object": "release readiness",
                    "component_layer": "green tests",
                    "role_layer": "readiness signal",
                },
                "whole_object": "release readiness",
                "canonical_object": "release readiness",
                "formal_thesis_subject": "release readiness",
                "umbrella_context": "software delivery",
                "subject_alignment_reason": "release readiness is being defined; software delivery is context",
                "whole_object_reconstruction": {
                    "target_job": "ship a useful change safely and recoverably",
                    "main_use_cases": "deploy, observe, recover, and accept residual risk",
                    "primary_value_carrier": "safe recoverable release capability",
                    "local_interface_role": "green tests as readiness evidence",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("release readiness"),
                    "opening_core_thesis": opening,
                    "definition_disposition": "reject_as_definition",
                },
                "local_success_points": ["green tests are a strong local readiness signal"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": "Green tests define release readiness.",
                "definition_owner": "safe recoverable release capability",
                "result_controller": "rollback, monitoring, rollout, and evidence gates",
                "decision_consequence": "do not define readiness as green tests",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("corrected_thesis must align with formal_answer_plan.opening_core_thesis", result.stdout)

    def test_whole_elephant_validator_rejects_drifting_whole_object_package(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                **variant_calibration(),
                "object_hierarchy": {
                    "user_named_object": "release readiness",
                    "whole_object": "release readiness",
                    "component_layer": "green tests",
                    "role_layer": "readiness signal",
                },
                "whole_object": "public trust in a charity",
                "canonical_object": "public trust in a charity",
                "formal_thesis_subject": "public trust in a charity",
                "umbrella_context": "nonprofit governance",
                "subject_alignment_reason": "release readiness somehow became public trust",
                "whole_object_reconstruction": {
                    "target_job": "ship a useful change safely and recoverably",
                    "main_use_cases": "deploy, observe, recover, and accept residual risk",
                    "primary_value_carrier": "safe recoverable release capability",
                    "local_interface_role": "green tests as readiness evidence",
                },
                "formal_answer_plan": formal_answer_plan("public trust in a charity"),
                "local_success_points": ["green tests are a strong local readiness signal"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": "Public trust is carried by accountable governance.",
                "definition_owner": "accountable governance",
                "result_controller": "transparent reporting and stakeholder trust",
                "decision_consequence": "do not use green tests as the charity trust definition",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("object_hierarchy.whole_object must align with whole_object", result.stdout)

    def test_whole_elephant_validator_rejects_scope_correction_that_transfers_definition_authority(self) -> None:
        opening = (
            "你这句纠正是成立的：如果讨论对象严格限定为 skills，而不是更大的执行系统，"
            "那么 skills 的核心工程价值基本就是“在合适时机注入合适提示词”。"
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skills as reusable context/instruction modules",
                    "component_layer": "skill metadata, trigger description, instruction text, optional scripts/assets/templates, and optional validation routines",
                    "role_layer": "Skills decide what task-specific behavior instructions enter short-term model context and sometimes provide executable support material.",
                },
                "whole_object": "Skills as a mechanism in an LLM product or coding assistant.",
                "canonical_object": "Skills mechanism itself",
                "formal_thesis_subject": "Whether skills are essentially controlled prompt injection",
                "umbrella_context": "Discussion of skills, not the broader Agent system architecture.",
                "subject_alignment_reason": "The user explicitly corrected that the intended object is skills themselves; previous Agent framing over-expanded the object.",
                "whole_object_reconstruction": {
                    "target_job": "Increase the chance that the model applies the right procedure, standards, and constraints for a task.",
                    "main_use_cases": "Routing specialized instructions, increasing salience, preserving procedural detail, attaching reusable scripts/templates, and standardizing output shape.",
                    "primary_value_carrier": "Controlled activation of task-specific instruction/context bundles.",
                    "local_interface_role": "Prompt text injected into the model context.",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("Skills mechanism itself"),
                    "opening_core_thesis": opening,
                    "definition_disposition": "qualify_as_component",
                    "local_truth_boundary": "The reduction is strong for pure skills and for prompt-level gate instructions; optional scripts and validators should be treated as skill-attached assets.",
                    "definition_consequence": "The better distinction is pure prompt skill versus skill package with executable attachments.",
                    "optimization_misdirection": "Over-expanding to Agent architecture hides that skills mainly solve context selection and instruction salience.",
                },
                "local_success_points": [
                    "The user explicitly scoped the topic to skills.",
                    "Most skills work by injecting instruction text into short-term context.",
                    "Activation timing, routing, priority, and context management are engineering around prompt injection.",
                ],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": (
                    "When the object is skills themselves, the user's reduction is mostly right: "
                    "a skill is primarily a packaged instruction/context unit plus activation rules."
                ),
                "definition_owner": "The definition is owned by the skill mechanism's role in context construction and behavior conditioning.",
                "result_controller": "The result is mostly controlled by trigger selection, context priority, instruction wording, model adherence, and any attached executable checks.",
                "decision_consequence": "The correct critique should not drift to Agent architecture; it should distinguish pure prompt skills from skills that bundle scripts or validators.",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "formal_answer_plan.opening_core_thesis must not transfer definition authority while correcting scope",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_scope_correction_object_downgrade(self) -> None:
        opening = (
            "在讨论 Skills 定位时，定义权属于可复用上下文和行为约束注入单元本身，"
            "Agent 只是一个使用场景，不该拥有解释权。"
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "variant_map": [
                    "lightweight prompt/context skill",
                    "skill with reusable procedures and validation support",
                ],
                "primary_value_distribution": (
                    "context packaging is common, while procedural control and validation "
                    "may carry higher-value repeatability"
                ),
                "control_owner_shift": (
                    "the answer corrected an Agent-level umbrella subject but then let "
                    "context injection own the skill definition"
                ),
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skills as reusable LLM context artifacts",
                    "component_layer": "prompt text, trigger descriptions, and optional assets",
                    "role_layer": "context injection and behavior shaping",
                },
                "whole_object": "skills as reusable LLM context artifacts",
                "canonical_object": "skills as reusable LLM context artifacts",
                "formal_thesis_subject": "skills as reusable LLM context artifacts",
                "umbrella_context": "LLM product practice after removing the broader Agent frame",
                "subject_alignment_reason": (
                    "The user corrected the previous Agent framing, so the answer should "
                    "focus on skills themselves."
                ),
                "whole_object_reconstruction": {
                    "target_job": "make reusable instructions and procedures available to an LLM",
                    "main_use_cases": "domain workflows, coding conventions, and repeatable response protocols",
                    "primary_value_carrier": "packaged reusable context with trigger rules and procedural constraints",
                    "local_interface_role": "prompt text injection as the most common runtime carrier",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("skills as reusable LLM context artifacts"),
                    "opening_core_thesis": opening,
                    "definition_disposition": "qualify_as_component",
                    "local_truth_boundary": "The reduction is strongest when discussing runtime delivery into context.",
                    "definition_consequence": "Skills should be described as reusable context/procedure packages.",
                    "optimization_misdirection": "The answer stops discussing Agent architecture and centers context injection.",
                },
                "local_success_points": [
                    "The user correctly rejected the broader Agent scope.",
                    "Many skills are delivered as text in the context window.",
                ],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": (
                    "Skills as reusable LLM context artifacts use text as their main carrier."
                ),
                "definition_owner": (
                    "The Skill artifact's role in LLM context management and behavior shaping."
                ),
                "result_controller": (
                    "skill text, trigger rule, inclusion timing, model compliance, and optional validation"
                ),
                "decision_consequence": "Do not drag Agent architecture into the center of Skills positioning.",
                "visible_formal_answer": opening,
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "canonical_object must not downgrade the user-named object into a local carrier after scope correction",
            result.stdout,
        )

    def test_whole_elephant_validator_rejects_visible_answer_that_starts_with_audit_or_internal_stdout(self) -> None:
        opening = (
            "Skills are defined by reusable task control, not by the locally valid prompt interface, "
            "so optimizing them as prompt wording misdirects work away from stable task completion."
        )
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skill capability",
                    "component_layer": "prompt text",
                    "role_layer": "attention steering interface",
                },
                "whole_object": "skill capability",
                "canonical_object": "skill capability",
                "formal_thesis_subject": "skill capability",
                "umbrella_context": "agent runtime",
                "subject_alignment_reason": "skill capability is being defined; agent runtime is only context",
                "whole_object_reconstruction": {
                    "target_job": "make task completion stable, reusable, and verifiable",
                    "main_use_cases": "execution, validation, handoff, and recovery",
                    "primary_value_carrier": "scripted task control and verification contract",
                    "local_interface_role": "prompt injection as attention steering",
                },
                "formal_answer_plan": {
                    **formal_answer_plan("skill capability"),
                    "opening_core_thesis": opening,
                },
                "local_success_points": ["prompt injection is a valid local interface"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "corrected_thesis": opening,
                "definition_owner": "scripted task control and verification contract",
                "result_controller": "scripts, validators, resources, and recovery protocol",
                "decision_consequence": "do not optimize skills as prompt wording",
                "visible_formal_answer": (
                    "定框审计：true_question 是 skills 是否只是 prompt。"
                    "script_verdict: shape_only。其实 skills 不只是 prompt。"
                ),
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "visible_formal_answer first sentence must start with formal_answer_plan.opening_core_thesis",
            result.stdout,
        )
        self.assertIn("visible_formal_answer must not expose internal script stdout", result.stdout)

    def test_whole_elephant_validator_rejects_missing_fields_and_bad_strategy(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "whole_object": "skills",
                "local_success_points": ["prompt injection is a valid local use"],
                "strategy_choice": "balanced_view",
                "definition_owner": "",
                "result_controller": "scripts and validators",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("strategy_choice must be one of", result.stdout)
        self.assertIn("definition_owner must be a non-empty string", result.stdout)
        self.assertIn("decision_consequence must be a non-empty string", result.stdout)

    def test_whole_elephant_validator_rejects_missing_subject_alignment_fields(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skill bundle",
                    "component_layer": "prompt text",
                    "role_layer": "attention guide",
                },
                "whole_object": "skill bundle",
                "local_success_points": ["prompt injection is a valid local use"],
                "strategy_choice": "whole_first_re_evaluation",
                "definition_owner": "reusable task capability",
                "result_controller": "scripts, resources, validation, and handoff",
                "decision_consequence": "do not optimize only for prompt wording",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical_object must be a non-empty string", result.stdout)
        self.assertIn("formal_thesis_subject must be a non-empty string", result.stdout)
        self.assertIn("umbrella_context must be a non-empty string", result.stdout)
        self.assertIn("subject_alignment_reason must be a non-empty string", result.stdout)

    def test_whole_elephant_validator_rejects_missing_or_invalid_user_named_relation(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "skills",
                    "whole_object": "skill bundle",
                    "component_layer": "prompt text",
                    "role_layer": "attention guide",
                },
                "whole_object": "skill bundle",
                "canonical_object": "skill bundle",
                "formal_thesis_subject": "skill bundle",
                "umbrella_context": "agent runtime",
                "subject_alignment_reason": "skills are the object being defined; runtime is context",
                "local_success_points": ["prompt injection is a valid local use"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "upstream_container",
                "definition_owner": "reusable task capability",
                "result_controller": "scripts, resources, validation, and handoff",
                "decision_consequence": "do not optimize only for prompt wording",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("user_named_object_relation must be one of", result.stdout)

    def test_whole_elephant_validator_rejects_missing_whole_object_reconstruction(self) -> None:
        result = run_whole_elephant_validator(
            {
                "schema_version": "mindthus-whole-elephant-audit-v0.1",
                "object_hierarchy": {
                    "user_named_object": "pricing complaints",
                    "whole_object": "product failure",
                    "component_layer": "price point",
                    "role_layer": "value-friction signal",
                },
                "whole_object": "product failure",
                "canonical_object": "product failure",
                "formal_thesis_subject": "product failure",
                "umbrella_context": "product-market system",
                "subject_alignment_reason": "product failure is being explained; pricing is local evidence",
                "local_success_points": ["pricing can be a real conversion bottleneck"],
                "strategy_choice": "whole_first_re_evaluation",
                "user_named_object_relation": "canonical_object",
                "definition_owner": "repeatable user value delivery",
                "result_controller": "activation, retention, positioning, channel fit, and unit economics",
                "decision_consequence": "do not optimize price before identifying the governing failure mode",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_object_reconstruction is required", result.stdout)
        self.assertIn("whole_object_reconstruction.target_job must be a non-empty string", result.stdout)

    def test_whole_elephant_validator_rejects_missing_corrected_thesis(self) -> None:
        audit = {
            "schema_version": "mindthus-whole-elephant-audit-v0.1",
            "object_hierarchy": {
                "user_named_object": "green tests",
                "whole_object": "release readiness",
                "component_layer": "test suite",
                "role_layer": "regression signal",
            },
            "whole_object": "release readiness",
            "canonical_object": "release readiness",
            "formal_thesis_subject": "release readiness",
            "umbrella_context": "software delivery system",
            "subject_alignment_reason": "release readiness is being judged; tests are local evidence",
            "whole_object_reconstruction": {
                "target_job": "ship useful changes safely",
                "main_use_cases": "release, rollback, and recovery decisions",
                "primary_value_carrier": "operational safety and rollout control",
                "local_interface_role": "green tests as regression evidence",
            },
            "local_success_points": ["green tests are real regression evidence"],
            "strategy_choice": "whole_first_re_evaluation",
            "user_named_object_relation": "canonical_object",
            "definition_owner": "safe and recoverable release capability",
            "result_controller": "rollout, observability, rollback, and evidence gates",
            "decision_consequence": "do not ship based on green tests alone",
        }
        result = run_whole_elephant_validator(audit)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("corrected_thesis must be a non-empty string", result.stdout)

    def test_whole_elephant_validator_rejects_value_carrier_equal_to_local_interface(self) -> None:
        audit = {
            "schema_version": "mindthus-whole-elephant-audit-v0.1",
            "object_hierarchy": {
                "user_named_object": "prompt injection",
                "whole_object": "skill bundle",
                "component_layer": "text interface",
                "role_layer": "attention steering",
            },
            "whole_object": "skill bundle",
            "canonical_object": "skill bundle",
            "formal_thesis_subject": "skill bundle",
            "umbrella_context": "agent runtime",
            "subject_alignment_reason": "skill bundle is being defined; runtime is context",
            "whole_object_reconstruction": {
                "target_job": "make a task capability reusable and verifiable",
                "main_use_cases": "routing, execution, validation, and handoff",
                "primary_value_carrier": "prompt injection",
                "local_interface_role": "prompt injection",
            },
            "local_success_points": ["prompt injection can be a real interface"],
            "strategy_choice": "whole_first_re_evaluation",
            "user_named_object_relation": "canonical_object",
            "corrected_thesis": "Skill bundle value is carried by reusable, verifiable task capability.",
            "definition_owner": "reusable, verifiable task capability",
            "result_controller": "workflow, resources, validation, and failure handling",
            "decision_consequence": "do not optimize only prompt wording",
        }
        result = run_whole_elephant_validator(audit)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "whole_object_reconstruction.primary_value_carrier must differ from local_interface_role",
            result.stdout,
        )

    def test_before_freeze_activates_gate_smells_and_claim_ceiling(self) -> None:
        result = run_check("--event", "before-freeze", "--method", "tvg", "--json")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)

        self.assertEqual(report["script_verdict"], "shape_only")
        self.assertIs(report["agentic_judgment_required"], True)
        self.assertEqual(
            [item["id"] for item in report["active_primitives"]],
            [
                "gate_probes",
                "failure_smells",
                "evidence_claim_ceiling",
            ],
        )
        self.assertIn("gate_success", report["script_must_not_decide"])

    def test_before_continue_adds_tplan_continuation_authorization_only_for_tplan(self) -> None:
        tplan_result = run_check("--event", "before-continue", "--method", "tplan", "--json")
        self.assertEqual(tplan_result.returncode, 0, tplan_result.stderr + tplan_result.stdout)
        tplan_report = json.loads(tplan_result.stdout)
        self.assertIn(
            "continuation_authorization",
            [item["id"] for item in tplan_report["active_primitives"]],
        )

        tvg_result = run_check("--event", "before-continue", "--method", "tvg", "--json")
        self.assertEqual(tvg_result.returncode, 0, tvg_result.stderr + tvg_result.stdout)
        tvg_report = json.loads(tvg_result.stdout)
        self.assertNotIn(
            "continuation_authorization",
            [item["id"] for item in tvg_report["active_primitives"]],
        )

    def test_manifest_has_minimal_shape_for_every_primitive(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["script_boundary"], "shape_only_reminder_not_semantic_judgment")

        for primitive_id, primitive in manifest["primitives"].items():
            self.assertTrue(primitive_id)
            self.assertTrue(primitive["name"])
            self.assertTrue(primitive["short_rule"])
            self.assertTrue(primitive["trigger"])
            self.assertTrue(primitive["action_effect"])
            self.assertTrue(primitive["not_a"])
            self.assertTrue(primitive["owner"])

    def test_release_pack_includes_primitive_activation_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "release"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "build-release-pack.py"), "--out", str(out)],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            for platform in ("claude-code/claude-plugin", "codex", "opencode"):
                self.assertTrue((out / platform / "scripts" / "primitives" / "check.py").is_file())
                self.assertTrue(
                    (out / platform / "scripts" / "primitives" / "validate_whole_elephant.py").is_file()
                )
                self.assertTrue((out / platform / "scripts" / "primitives" / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
