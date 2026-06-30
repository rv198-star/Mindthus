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


class PrimitiveActivationTests(unittest.TestCase):
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
                "object_hierarchy": {
                    "user_named_object": "green tests",
                    "whole_object": "release readiness",
                    "component_layer": "test suite",
                    "role_layer": "regression signal",
                },
                "whole_object": "release readiness",
                "user_named_object_relation": "canonical_object",
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
