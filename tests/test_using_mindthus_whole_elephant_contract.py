import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VALIDATOR = REPO / "skills" / "using-mindthus" / "scripts" / "validate_using_mindthus_output.py"
TEMPLATE = REPO / "skills" / "using-mindthus" / "templates" / "fidelity-output.json"


def run_validator(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "using-mindthus-output.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return subprocess.run(
            ["python3", str(VALIDATOR), str(path)],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )


def whole_elephant_audit() -> dict:
    return {
        "schema_version": "mindthus-whole-elephant-audit-v0.1",
        "object_hierarchy": {
            "user_named_object": "green tests",
            "whole_object": "release readiness",
            "component_layer": "test suite",
            "role_layer": "regression signal",
        },
        "whole_object": "release readiness as safe, recoverable shipping capability",
        "user_named_object_relation": "canonical_object",
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
        "local_success_points": ["tests catch implementation regressions"],
        "strategy_choice": "whole_first_re_evaluation",
        "corrected_thesis": "Release readiness is carried by safe and recoverable shipping capability, not green tests alone.",
        "definition_owner": "safe and recoverable release capability",
        "result_controller": "rollout, observability, rollback, and evidence gates",
        "decision_consequence": "do not ship based on green tests alone",
        "formal_answer_plan": {
            "opening_core_thesis": "Release readiness is not defined by green tests; it is defined by the ability to ship safely and recover when reality diverges.",
            "canonical_subject": "release readiness",
            "definition_disposition": "reject_as_definition",
            "local_truth_boundary": "Green tests are regression evidence, not the readiness definition.",
            "definition_consequence": "If readiness is defined as tests passing, optimization shifts toward test coverage and away from rollout safety, observability, rollback, and user impact.",
            "optimization_misdirection": "test polishing over operational release control",
            "forbidden_answer_forms": [
                "score_as_concession",
                "soft_not_wrong_concession",
                "runtime_also_matters_only",
                "umbrella_context_as_thesis_subject",
            ],
        },
    }


class UsingMindthusWholeElephantContractTests(unittest.TestCase):
    def template_payload(self) -> dict:
        return json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def test_partial_truth_trigger_requires_whole_elephant_audit(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_audit is required when partial_truth_capture_triggered is true", result.stdout)

    def test_applicable_output_must_declare_partial_truth_trigger_status(self) -> None:
        payload = self.template_payload()
        del payload["partial_truth_capture_triggered"]

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("partial_truth_capture_triggered must be explicitly true or false", result.stdout)

    def test_partial_truth_trigger_requires_shape_only_validation_verdict(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        payload["whole_elephant_audit"] = whole_elephant_audit()
        payload["whole_elephant_validation"] = {"script_verdict": "skipped"}

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_validation.script_verdict must be 'shape_only'", result.stdout)

    def test_partial_truth_trigger_requires_command_evidence_not_verbal_claim(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        payload["whole_elephant_audit"] = whole_elephant_audit()
        payload["whole_elephant_validation"] = {"script_verdict": "shape_only"}

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_validation.command must name the validator command that ran", result.stdout)
        self.assertIn("whole_elephant_validation.output_evidence must include observed validator output", result.stdout)

    def test_partial_truth_trigger_requires_object_hierarchy_not_user_named_object_only(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        del audit["object_hierarchy"]
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_audit.object_hierarchy is required", result.stdout)

    def test_partial_truth_trigger_requires_subject_alignment_fields(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        for field in (
            "canonical_object",
            "formal_thesis_subject",
            "umbrella_context",
            "subject_alignment_reason",
        ):
            del audit[field]
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_audit.canonical_object must be a non-empty string", result.stdout)
        self.assertIn("whole_elephant_audit.formal_thesis_subject must be a non-empty string", result.stdout)
        self.assertIn("whole_elephant_audit.umbrella_context must be a non-empty string", result.stdout)
        self.assertIn("whole_elephant_audit.subject_alignment_reason must be a non-empty string", result.stdout)

    def test_partial_truth_trigger_requires_valid_user_named_object_relation(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        audit["user_named_object_relation"] = "upstream_container"
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_audit.user_named_object_relation must be one of", result.stdout)

    def test_partial_truth_trigger_requires_corrected_thesis(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        del audit["corrected_thesis"]
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_audit.corrected_thesis must be a non-empty string", result.stdout)

    def test_partial_truth_trigger_rejects_value_carrier_equal_to_local_interface(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        audit["whole_object_reconstruction"]["primary_value_carrier"] = "green tests"
        audit["whole_object_reconstruction"]["local_interface_role"] = "green tests"
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "whole_elephant_audit.whole_object_reconstruction.primary_value_carrier must differ from local_interface_role",
            result.stdout,
        )

    def test_partial_truth_trigger_requires_whole_object_reconstruction(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        del audit["whole_object_reconstruction"]
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_audit.whole_object_reconstruction is required", result.stdout)
        self.assertIn(
            "whole_elephant_audit.whole_object_reconstruction.primary_value_carrier must be a non-empty string",
            result.stdout,
        )

    def test_partial_truth_trigger_requires_formal_answer_plan(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        del audit["formal_answer_plan"]
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_audit.formal_answer_plan is required", result.stdout)

    def test_formal_answer_plan_rejects_score_concession_only_answers(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        audit["formal_answer_plan"]["opening_core_thesis"] = "This claim is 70% right and 30% reductionist."
        audit["formal_answer_plan"]["local_truth_boundary"] = "Both sides have a point."
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "whole_elephant_audit.formal_answer_plan.opening_core_thesis must not use score-as-concession framing",
            result.stdout,
        )
        self.assertIn(
            "whole_elephant_audit.formal_answer_plan.local_truth_boundary must name the boundary of the local truth, not a both-sides concession",
            result.stdout,
        )

    def test_formal_answer_plan_requires_definition_disposition_and_optimization_misdirection(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        del audit["formal_answer_plan"]["definition_disposition"]
        del audit["formal_answer_plan"]["optimization_misdirection"]
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "whole_elephant_audit.formal_answer_plan.definition_disposition must be a non-empty string",
            result.stdout,
        )
        self.assertIn(
            "whole_elephant_audit.formal_answer_plan.optimization_misdirection must be a non-empty string",
            result.stdout,
        )

    def test_formal_answer_plan_allows_explicit_optimization_misdirection(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        audit["formal_answer_plan"]["optimization_misdirection"] = (
            "surface wording and attention capture over target-result control"
        )
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_formal_answer_plan_rejects_soft_not_wrong_concession_for_rejected_definition(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        audit = whole_elephant_audit()
        audit["formal_answer_plan"]["definition_disposition"] = "reject_as_definition"
        audit["formal_answer_plan"]["opening_core_thesis"] = "I would not say this claim is wrong; it is just incomplete."
        payload["whole_elephant_audit"] = audit
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "whole_elephant_audit.formal_answer_plan.opening_core_thesis must not soften a rejected definition into a not-wrong concession",
            result.stdout,
        )

    def test_partial_truth_trigger_rejects_placeholder_validation_command(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        payload["whole_elephant_audit"] = whole_elephant_audit()
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 .../scripts/primitives/validate_whole_elephant.py <audit-json>",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("whole_elephant_validation.command must be the exact command that ran, not a placeholder", result.stdout)

    def test_partial_truth_trigger_passes_with_audit_and_shape_only_validation(self) -> None:
        payload = self.template_payload()
        payload["partial_truth_capture_triggered"] = True
        payload["whole_elephant_audit"] = whole_elephant_audit()
        payload["whole_elephant_validation"] = {
            "script_verdict": "shape_only",
            "command": "python3 scripts/primitives/validate_whole_elephant.py /tmp/audit.json",
            "output_evidence": "script_verdict: shape_only",
        }

        result = run_validator(payload)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("No shape or evidence risks detected", result.stdout)


if __name__ == "__main__":
    unittest.main()
