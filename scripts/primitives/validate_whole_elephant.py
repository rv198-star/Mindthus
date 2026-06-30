#!/usr/bin/env python3
"""Validate Whole Elephant Protocol audit shape.

This validator only checks whether an agent exposed the required audit fields. It does
not judge semantic truth, definition correctness, evidence sufficiency, or domain value.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus-whole-elephant-audit-v0.1"
ALLOWED_STRATEGIES = {"weighted_synthesis", "whole_first_re_evaluation"}
ALLOWED_USER_NAMED_OBJECT_RELATIONS = {
    "canonical_object",
    "component_or_interface",
    "umbrella_context",
    "ambiguous_needs_evidence",
}
REQUIRED_STRING_FIELDS = (
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
OBJECT_HIERARCHY_FIELDS = (
    "user_named_object",
    "whole_object",
    "component_layer",
    "role_layer",
)
WHOLE_OBJECT_RECONSTRUCTION_FIELDS = (
    "target_job",
    "main_use_cases",
    "primary_value_carrier",
    "local_interface_role",
)
FORMAL_ANSWER_PLAN_FIELDS = (
    "opening_core_thesis",
    "canonical_subject",
    "definition_disposition",
    "local_truth_boundary",
    "definition_consequence",
    "optimization_misdirection",
)
DEFINITION_DISPOSITIONS = {
    "grant_as_definition",
    "reject_as_definition",
    "qualify_as_component",
    "blocked_by_missing_evidence",
}
SCRIPT_MUST_NOT_DECIDE = (
    "semantic_truth",
    "definition_correctness",
    "evidence_sufficiency",
    "domain_value",
    "user_authority",
)


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def normalize_text(value: Any) -> str:
    return " ".join(str(value).casefold().split())


def looks_like_score_concession(value: Any) -> bool:
    text = normalize_text(value)
    return any(marker in text for marker in ("70%", "70分", "half-right", "half right")) or (
        any(marker in text for marker in ("%", "分"))
        and any(marker in text for marker in ("right", "对", "correct", "成立"))
    )


def looks_like_both_sides_concession(value: Any) -> bool:
    text = normalize_text(value)
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


def looks_like_soft_not_wrong_concession(value: Any) -> bool:
    text = normalize_text(value)
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_audit(data: Any) -> list[str]:
    findings: list[str] = []
    if not isinstance(data, dict):
        return ["audit root must be an object"]

    if data.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"schema_version must be {SCHEMA_VERSION}")

    for field in REQUIRED_STRING_FIELDS:
        if not non_empty_string(data.get(field)):
            findings.append(f"{field} must be a non-empty string")

    hierarchy = data.get("object_hierarchy")
    if not isinstance(hierarchy, dict):
        findings.append("object_hierarchy is required")
    else:
        for field in OBJECT_HIERARCHY_FIELDS:
            if not non_empty_string(hierarchy.get(field)):
                findings.append(f"object_hierarchy.{field} must be a non-empty string")

    reconstruction = data.get("whole_object_reconstruction")
    if not isinstance(reconstruction, dict):
        findings.append("whole_object_reconstruction is required")
        reconstruction = {}
    for field in WHOLE_OBJECT_RECONSTRUCTION_FIELDS:
        if not non_empty_string(reconstruction.get(field)):
            findings.append(f"whole_object_reconstruction.{field} must be a non-empty string")
    if (
        non_empty_string(reconstruction.get("primary_value_carrier"))
        and normalize_text(reconstruction.get("primary_value_carrier"))
        == normalize_text(reconstruction.get("local_interface_role"))
    ):
        findings.append(
            "whole_object_reconstruction.primary_value_carrier must differ from local_interface_role"
        )

    plan = data.get("formal_answer_plan")
    if not isinstance(plan, dict):
        findings.append("formal_answer_plan is required")
        plan = {}
    for field in FORMAL_ANSWER_PLAN_FIELDS:
        if not non_empty_string(plan.get(field)):
            findings.append(f"formal_answer_plan.{field} must be a non-empty string")
    disposition = plan.get("definition_disposition")
    if non_empty_string(disposition) and disposition not in DEFINITION_DISPOSITIONS:
        choices = ", ".join(sorted(DEFINITION_DISPOSITIONS))
        findings.append(f"formal_answer_plan.definition_disposition must be one of: {choices}")
    if (
        non_empty_string(plan.get("canonical_subject"))
        and non_empty_string(data.get("canonical_object"))
        and normalize_text(plan.get("canonical_subject")) != normalize_text(data.get("canonical_object"))
    ):
        findings.append("formal_answer_plan.canonical_subject must match canonical_object")
    if looks_like_score_concession(plan.get("opening_core_thesis")):
        findings.append("formal_answer_plan.opening_core_thesis must not use score-as-concession framing")
    if looks_like_both_sides_concession(plan.get("local_truth_boundary")):
        findings.append(
            "formal_answer_plan.local_truth_boundary must name the boundary of the local truth, not a both-sides concession"
        )
    if (
        plan.get("definition_disposition") == "reject_as_definition"
        and looks_like_soft_not_wrong_concession(plan.get("opening_core_thesis"))
    ):
        findings.append(
            "formal_answer_plan.opening_core_thesis must not soften a rejected definition into a not-wrong concession"
        )
    forbidden = plan.get("forbidden_answer_forms")
    if not isinstance(forbidden, list) or not forbidden:
        findings.append("formal_answer_plan.forbidden_answer_forms must be a non-empty list")
    elif any(not non_empty_string(item) for item in forbidden):
        findings.append("formal_answer_plan.forbidden_answer_forms must contain only non-empty strings")

    local_success_points = data.get("local_success_points")
    if not isinstance(local_success_points, list) or not local_success_points:
        findings.append("local_success_points must be a non-empty list")
    elif any(not non_empty_string(point) for point in local_success_points):
        findings.append("local_success_points must contain only non-empty strings")

    strategy_choice = data.get("strategy_choice")
    if strategy_choice not in ALLOWED_STRATEGIES:
        choices = ", ".join(sorted(ALLOWED_STRATEGIES))
        findings.append(f"strategy_choice must be one of: {choices}")

    user_named_object_relation = data.get("user_named_object_relation")
    if user_named_object_relation not in ALLOWED_USER_NAMED_OBJECT_RELATIONS:
        choices = ", ".join(sorted(ALLOWED_USER_NAMED_OBJECT_RELATIONS))
        findings.append(f"user_named_object_relation must be one of: {choices}")

    return findings


def build_report(path: Path, data: Any, findings: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "path": str(path),
        "script_verdict": "shape_only_failed" if findings else "shape_only",
        "agentic_judgment_required": True,
        "findings": findings,
        "script_must_not_decide": list(SCRIPT_MUST_NOT_DECIDE),
        "observed_fields": sorted(data) if isinstance(data, dict) else [],
    }


def print_text_report(report: dict[str, Any]) -> None:
    print("Whole Elephant Protocol Shape Report")
    print(f"path: {report['path']}")
    if report["findings"]:
        for finding in report["findings"]:
            print(f"- BLOCK [invalid-audit]: {finding}")
    else:
        print("- OK [shape]: required audit fields are present")
    print(f"script_verdict: {report['script_verdict']}")
    print("agentic_judgment_required: true")
    print("script_must_not_decide: " + ", ".join(report["script_must_not_decide"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Whole Elephant Protocol audit shape.")
    parser.add_argument("path", help="Path to a Whole Elephant audit JSON file.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        data = {}
        findings = [f"audit-read-failed: {exc}"]
    else:
        findings = validate_audit(data)

    report = build_report(path, data, findings)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
