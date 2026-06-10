import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class ExistingValidatorReportContractTests(unittest.TestCase):
    def test_3l5s_report_uses_shared_shape_evidence_language(self):
        draft = """# 3L5S Draft

Mode: single-layer

## Baseline

Current state is known from logs.

## Target

Acceptance evidence exists.

## Gap

The missing part is explicit.

## Strategy

Choose this path because the alternative is slower.

## Breakdown

- Write one verifiable task with acceptance evidence.
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.md"
            path.write_text(draft, encoding="utf-8")
            result = subprocess.run(
                ["python3", "skills/3l5s/scripts/check_3l5s_run.py", str(path)],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("3L5S Shape & Evidence Risk Report", result.stdout)
        self.assertIn("No shape or evidence risks detected", result.stdout)
        self.assertIn("agentic audit remains required", result.stdout)
        self.assertNotIn("semantic approval", result.stdout)

    def test_tvg_trace_report_uses_shared_shape_evidence_language(self):
        trace = {
            "schema_version": "tvg-trace-v0.3",
            "method_version": "Thinking Value-Gain Methodology v0.3",
            "created_at": "2026-06-08T00:00:00Z",
            "updated_at": "2026-06-08T00:00:00Z",
            "module": {
                "id": "example",
                "title": "Example",
                "type": "methodology",
                "downstream_consumer": "maintainer",
                "freeze_granularity": "module",
            },
            "expected_value": {
                "mode": "provisional-default",
                "target_artifact": "Example",
                "artifact_job": "increase practical thinking value for maintainer review",
                "useful_when": ["maintainer can review and hand off without inventing critical truth"],
                "hard_constraints": [
                    "do not override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints"
                ],
                "evidence_boundary": ["separate supported claims from assumptions"],
                "output_bias": "balanced",
                "source": "test fixture",
                "unresolved_expected_value_items": [],
            },
            "value_profile": {
                "mode": "default",
                "name": "default practical-value profile",
                "artifact_job": "increase practical thinking value for maintainer review",
                "value_semantics": {
                    "good_means": ["clearer maintainer review value"],
                    "bad_means": ["longer output without practical value"],
                    "priority_order": ["evidence honesty", "downstream usability"],
                    "derived_axes": [],
                    "evidence_basis": ["TVG default practical-value model"],
                    "profile_veto_constraints": [],
                },
                "prompt_self_audit_questions": [],
                "image_self_audit_questions": [],
                "source_notes": [],
            },
            "exit_gate": {
                "mode": "provisional-default",
                "source": "test fixture",
                "module_responsibility": "methodology",
                "downstream_use": "maintainer",
                "hard_veto_checks": [
                    "do not override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints"
                ],
                "value_profile_fit_checks": ["artifact expresses default practical-value standard"],
                "downstream_use_checks": [
                    "maintainer can review and hand off without inventing critical truth"
                ],
                "evidence_boundary_checks": ["separate supported claims from assumptions"],
                "exit_blockers": [],
                "next_round_positive_value_check": "another round needs a named positive-value hypothesis",
                "unresolved_gate_items": [],
            },
            "value_gain": {
                "claimed_value_gain": "",
                "value_gain_types": [],
                "selected_axes": [],
                "veto_constraints": [],
                "evidence_support": "",
                "remaining_review_bound": [],
            },
            "rounds": [],
            "agentic_exit_audit": {
                "audit_role": "generator-self-audit",
                "auditor_independence": "not-required",
                "disagreements": [],
                "veto_constraint_result": "clear",
                "demo_false_positive_risk": "",
                "overfitting_risk": "",
                "downstream_usability": "",
                "exit_state": "blocked",
                "why_not_another_round": "",
            },
            "script_support": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trace.json"
            path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
            result = subprocess.run(
                ["python3", "skills/tvg/scripts/trace/validate.py", str(path)],
                text=True,
                capture_output=True,
                cwd=REPO,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("TVG Shape & Evidence Risk Report", result.stdout)
        self.assertIn("No shape or evidence risks detected", result.stdout)
        self.assertIn("No schema violations were detected; agentic audit is still required", result.stdout)
        self.assertNotIn("semantic approval", result.stdout)


if __name__ == "__main__":
    unittest.main()
