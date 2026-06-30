#!/usr/bin/env python3
"""Validate using-mindthus fidelity output shape."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _runtime.core.io import load_json
from _runtime.core.report import Finding, finding
from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


WHOLE_ELEPHANT_SCHEMA_VERSION = "mindthus-whole-elephant-audit-v0.1"
WHOLE_ELEPHANT_STRATEGIES = {"weighted_synthesis", "whole_first_re_evaluation"}
WHOLE_ELEPHANT_USER_NAMED_OBJECT_RELATIONS = {
    "canonical_object",
    "component_or_interface",
    "umbrella_context",
    "ambiguous_needs_evidence",
}
WHOLE_ELEPHANT_STRING_FIELDS = (
    "whole_object",
    "canonical_object",
    "formal_thesis_subject",
    "umbrella_context",
    "subject_alignment_reason",
    "corrected_thesis",
    "definition_owner",
    "result_controller",
    "decision_consequence",
)
WHOLE_ELEPHANT_HIERARCHY_FIELDS = (
    "user_named_object",
    "whole_object",
    "component_layer",
    "role_layer",
)
WHOLE_ELEPHANT_RECONSTRUCTION_FIELDS = (
    "target_job",
    "main_use_cases",
    "primary_value_carrier",
    "local_interface_role",
)
WHOLE_ELEPHANT_FORMAL_ANSWER_PLAN_FIELDS = (
    "opening_core_thesis",
    "canonical_subject",
    "definition_disposition",
    "local_truth_boundary",
    "definition_consequence",
    "optimization_misdirection",
)
WHOLE_ELEPHANT_DEFINITION_DISPOSITIONS = {
    "grant_as_definition",
    "reject_as_definition",
    "qualify_as_component",
    "blocked_by_missing_evidence",
}

SPEC = FidelitySpec(
    schema_version="using-mindthus-fidelity-v0.1",
    method="using-mindthus",
    report_title="using-mindthus Shape & Evidence Risk Report",
    required_moves=(
        "intervention_boundary",
        "premise_calibration",
        "constraint_separation",
        "judgment_object_routing",
        "method_arbitration",
        "execution_impact",
    ),
    action_postures=frozenset(
        {
            "direct_execute",
            "acquire_information",
            "route",
            "arbitrate",
            "transfer",
            "stop",
            "unclear",
        }
    ),
    truth_boundary="router judgment truth",
)


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_text(value: object) -> str:
    return " ".join(str(value).casefold().split())


def _placeholder_command(value: str) -> bool:
    return "..." in value or "<" in value or ">" in value


def _looks_like_score_concession(value: object) -> bool:
    text = _normalize_text(value)
    return any(marker in text for marker in ("70%", "70分", "half-right", "half right")) or (
        any(marker in text for marker in ("%", "分"))
        and any(marker in text for marker in ("right", "对", "correct", "成立"))
    )


def _looks_like_both_sides_concession(value: object) -> bool:
    text = _normalize_text(value)
    return any(
        marker in text
        for marker in (
            "both sides have a point",
            "both sides are right",
            "两边都有道理",
            "双方都有道理",
            "各有道理",
            "都有道理",
        )
    )


def _looks_like_soft_not_wrong_concession(value: object) -> bool:
    text = _normalize_text(value)
    return any(
        marker in text
        for marker in (
            "i would not say this claim is wrong",
            "i won't say this claim is wrong",
            "i would not say it is wrong",
            "i won't say it is wrong",
            "我不会说这句话错",
            "不能说它错",
            "不能说这句话错",
            "不是错",
            "不算错",
            "只是还不完整",
        )
    )


def _validate_object_hierarchy(audit: dict[str, object]) -> list[Finding]:
    hierarchy = audit.get("object_hierarchy")
    if not isinstance(hierarchy, dict):
        return [
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.object_hierarchy is required",
            )
        ]

    findings: list[Finding] = []
    for field in WHOLE_ELEPHANT_HIERARCHY_FIELDS:
        if not _non_empty_string(hierarchy.get(field)):
            findings.append(
                finding(
                    "block",
                    "invalid-whole-elephant-audit",
                    f"whole_elephant_audit.object_hierarchy.{field} must be a non-empty string",
                )
            )
    return findings


def _validate_whole_object_reconstruction(audit: dict[str, object]) -> list[Finding]:
    reconstruction = audit.get("whole_object_reconstruction")
    findings: list[Finding] = []
    if not isinstance(reconstruction, dict):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.whole_object_reconstruction is required",
            )
        )
        reconstruction = {}
    for field in WHOLE_ELEPHANT_RECONSTRUCTION_FIELDS:
        if not _non_empty_string(reconstruction.get(field)):
            findings.append(
                finding(
                    "block",
                    "invalid-whole-elephant-audit",
                    f"whole_elephant_audit.whole_object_reconstruction.{field} must be a non-empty string",
                )
            )
    if (
        _non_empty_string(reconstruction.get("primary_value_carrier"))
        and _normalize_text(reconstruction.get("primary_value_carrier"))
        == _normalize_text(reconstruction.get("local_interface_role"))
    ):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.whole_object_reconstruction.primary_value_carrier must differ from local_interface_role",
            )
        )
    return findings


def _validate_formal_answer_plan(audit: dict[str, object]) -> list[Finding]:
    plan = audit.get("formal_answer_plan")
    findings: list[Finding] = []
    if not isinstance(plan, dict):
        return [
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.formal_answer_plan is required",
            )
        ]

    for field in WHOLE_ELEPHANT_FORMAL_ANSWER_PLAN_FIELDS:
        if not _non_empty_string(plan.get(field)):
            findings.append(
                finding(
                    "block",
                    "invalid-whole-elephant-audit",
                    f"whole_elephant_audit.formal_answer_plan.{field} must be a non-empty string",
                )
            )

    disposition = plan.get("definition_disposition")
    if _non_empty_string(disposition) and disposition not in WHOLE_ELEPHANT_DEFINITION_DISPOSITIONS:
        choices = ", ".join(sorted(WHOLE_ELEPHANT_DEFINITION_DISPOSITIONS))
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                f"whole_elephant_audit.formal_answer_plan.definition_disposition must be one of: {choices}",
            )
        )

    if (
        _non_empty_string(plan.get("canonical_subject"))
        and _non_empty_string(audit.get("canonical_object"))
        and _normalize_text(plan.get("canonical_subject")) != _normalize_text(audit.get("canonical_object"))
    ):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.formal_answer_plan.canonical_subject must match canonical_object",
            )
        )

    if _looks_like_score_concession(plan.get("opening_core_thesis")):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.formal_answer_plan.opening_core_thesis must not use score-as-concession framing",
            )
        )
    if _looks_like_both_sides_concession(plan.get("local_truth_boundary")):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.formal_answer_plan.local_truth_boundary must name the boundary of the local truth, not a both-sides concession",
            )
        )
    if (
        plan.get("definition_disposition") == "reject_as_definition"
        and _looks_like_soft_not_wrong_concession(plan.get("opening_core_thesis"))
    ):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.formal_answer_plan.opening_core_thesis must not soften a rejected definition into a not-wrong concession",
            )
        )

    forbidden = plan.get("forbidden_answer_forms")
    if not isinstance(forbidden, list) or not forbidden:
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.formal_answer_plan.forbidden_answer_forms must be a non-empty list",
            )
        )
    elif any(not _non_empty_string(item) for item in forbidden):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.formal_answer_plan.forbidden_answer_forms must contain only non-empty strings",
            )
        )
    return findings


def _validate_whole_elephant_audit(audit: object) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(audit, dict):
        return [
            finding(
                "block",
                "missing-whole-elephant-audit",
                "whole_elephant_audit is required when partial_truth_capture_triggered is true",
            )
        ]

    if audit.get("schema_version") != WHOLE_ELEPHANT_SCHEMA_VERSION:
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                f"whole_elephant_audit.schema_version must be {WHOLE_ELEPHANT_SCHEMA_VERSION}",
            )
        )
    for field in WHOLE_ELEPHANT_STRING_FIELDS:
        if not _non_empty_string(audit.get(field)):
            findings.append(
                finding(
                    "block",
                    "invalid-whole-elephant-audit",
                    f"whole_elephant_audit.{field} must be a non-empty string",
                )
            )
    findings.extend(_validate_object_hierarchy(audit))
    findings.extend(_validate_whole_object_reconstruction(audit))
    findings.extend(_validate_formal_answer_plan(audit))

    local_success_points = audit.get("local_success_points")
    if not isinstance(local_success_points, list) or not local_success_points:
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.local_success_points must be a non-empty list",
            )
        )
    elif any(not _non_empty_string(point) for point in local_success_points):
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                "whole_elephant_audit.local_success_points must contain only non-empty strings",
            )
        )

    strategy_choice = audit.get("strategy_choice")
    if strategy_choice not in WHOLE_ELEPHANT_STRATEGIES:
        choices = ", ".join(sorted(WHOLE_ELEPHANT_STRATEGIES))
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                f"whole_elephant_audit.strategy_choice must be one of: {choices}",
            )
        )
    user_named_object_relation = audit.get("user_named_object_relation")
    if user_named_object_relation not in WHOLE_ELEPHANT_USER_NAMED_OBJECT_RELATIONS:
        choices = ", ".join(sorted(WHOLE_ELEPHANT_USER_NAMED_OBJECT_RELATIONS))
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-audit",
                f"whole_elephant_audit.user_named_object_relation must be one of: {choices}",
            )
        )
    return findings


def _validate_whole_elephant_contract(data: object) -> list[Finding]:
    if not isinstance(data, dict) or data.get("applicability") != "applicable":
        return []

    if "partial_truth_capture_triggered" not in data:
        return [
            finding(
                "block",
                "missing-field",
                "partial_truth_capture_triggered must be explicitly true or false",
            )
        ]
    triggered = data.get("partial_truth_capture_triggered")
    if triggered is False:
        return []
    if triggered is not True:
        return [
            finding(
                "block",
                "invalid-field",
                "partial_truth_capture_triggered must be true or false",
            )
        ]

    findings = _validate_whole_elephant_audit(data.get("whole_elephant_audit"))
    validation = data.get("whole_elephant_validation")
    if not isinstance(validation, dict):
        findings.append(
            finding(
                "block",
                "missing-whole-elephant-validation",
                "whole_elephant_validation is required when partial_truth_capture_triggered is true",
            )
        )
    elif validation.get("script_verdict") != "shape_only":
        findings.append(
            finding(
                "block",
                "invalid-whole-elephant-validation",
                "whole_elephant_validation.script_verdict must be 'shape_only'",
            )
        )
    else:
        if not _non_empty_string(validation.get("command")):
            findings.append(
                finding(
                    "block",
                    "missing-whole-elephant-validation-evidence",
                    "whole_elephant_validation.command must name the validator command that ran",
                )
            )
        elif _placeholder_command(validation["command"]):
            findings.append(
                finding(
                    "block",
                    "placeholder-whole-elephant-validation-command",
                    "whole_elephant_validation.command must be the exact command that ran, not a placeholder",
                )
            )
        if not _non_empty_string(validation.get("output_evidence")):
            findings.append(
                finding(
                    "block",
                    "missing-whole-elephant-validation-evidence",
                    "whole_elephant_validation.output_evidence must include observed validator output",
                )
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate using-mindthus fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = load_json(path)
    findings = validate_fidelity_output(data, SPEC)
    findings.extend(_validate_whole_elephant_contract(data))
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
