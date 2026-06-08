#!/usr/bin/env python3
"""Validate and report Method Fidelity judge results.

This runner automates the judge layer's reproducible contract. It checks that a human
or LLM judge returned the required rubric fields, scores, and escape-review coverage.
It does not decide whether the underlying strategic conclusion is true.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus-fidelity-judge-v0.1"
METHOD_DIMENSIONS = {
    "SELA": ("D1", "D2", "D3", "D4", "D5", "D6"),
}
METHOD_RUBRICS = {
    "SELA": Path("skills/sela/rubrics/judge.md"),
}
METHOD_EXIT_VALUES = {"not_applicable", "transfer", "challenge_premise"}
ESCAPE_ACTIONS = {"accept_exit", "reject_exit_and_score_applicable", "transfer_to_human"}


@dataclass(frozen=True)
class Finding:
    code: str
    message: str


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON at {path}: {exc}") from exc


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def add_if_missing(findings: list[Finding], data: dict[str, Any], field: str) -> None:
    if field not in data:
        findings.append(Finding("missing-field", f"missing field: {field}"))


def validate_dimensions(method: str, judge: dict[str, Any], findings: list[Finding]) -> int:
    dimensions = judge.get("dimensions")
    if not isinstance(dimensions, dict):
        findings.append(Finding("invalid-dimensions", "dimensions must be an object"))
        return 0

    total = 0
    for dimension in METHOD_DIMENSIONS[method]:
        item = dimensions.get(dimension)
        if not isinstance(item, dict):
            findings.append(Finding("missing-dimension", f"missing dimension: {dimension}"))
            continue
        score = item.get("score")
        if not is_int(score) or not 0 <= score <= 2:
            findings.append(Finding("invalid-score", f"{dimension}.score must be an integer from 0 to 2"))
        else:
            total += score
        for field in ("rationale", "evidence"):
            if not non_empty_string(item.get(field)):
                findings.append(Finding("empty-dimension-field", f"{dimension}.{field} is empty"))
    return total


def validate_escape_review(output: dict[str, Any], judge: dict[str, Any], findings: list[Finding]) -> None:
    applicability = output.get("applicability")
    if applicability not in METHOD_EXIT_VALUES:
        return

    review = judge.get("escape_review")
    if not isinstance(review, dict):
        findings.append(
            Finding(
                "missing-escape-review",
                f"escape_review is required when output applicability is {applicability}",
            )
        )
        return

    if review.get("applicability_exit") != applicability:
        findings.append(
            Finding(
                "invalid-escape-review",
                f"escape_review.applicability_exit must match output applicability: {applicability}",
            )
        )
    if not isinstance(review.get("is_exit_justified"), bool):
        findings.append(Finding("invalid-escape-review", "escape_review.is_exit_justified must be boolean"))
    if not non_empty_string(review.get("rationale")):
        findings.append(Finding("empty-escape-review", "escape_review.rationale is empty"))
    action = review.get("reviewer_action")
    if action not in ESCAPE_ACTIONS:
        allowed = ", ".join(sorted(ESCAPE_ACTIONS))
        findings.append(
            Finding(
                "invalid-escape-review",
                f"escape_review.reviewer_action unsupported: {action!r}; expected one of: {allowed}",
            )
        )


def validate_judge_result(output: Any, judge: Any) -> tuple[list[Finding], int, str]:
    findings: list[Finding] = []
    if not isinstance(output, dict):
        return [Finding("invalid-output", "method output must be an object")], 0, ""
    if not isinstance(judge, dict):
        return [Finding("invalid-judge", "judge result must be an object")], 0, ""

    method = judge.get("method")
    if method not in METHOD_DIMENSIONS:
        allowed = ", ".join(sorted(METHOD_DIMENSIONS))
        findings.append(Finding("unsupported-method", f"method unsupported: {method!r}; expected one of: {allowed}"))
        return findings, 0, ""

    if output.get("method") != method:
        findings.append(Finding("method-mismatch", f"judge method {method!r} does not match output method"))
    if judge.get("schema_version") != SCHEMA_VERSION:
        findings.append(Finding("invalid-schema-version", f"schema_version must be {SCHEMA_VERSION}"))

    for field in ("judge_model", "rubric"):
        if not non_empty_string(judge.get(field)):
            findings.append(Finding("missing-field", f"{field} must be a non-empty string"))

    total = validate_dimensions(method, judge, findings)

    assessment = judge.get("final_assessment")
    if not isinstance(assessment, dict):
        findings.append(Finding("invalid-final-assessment", "final_assessment must be an object"))
    else:
        if assessment.get("total_score") != total:
            findings.append(
                Finding(
                    "total-score-mismatch",
                    f"final_assessment.total_score must equal dimension score sum: {total}",
                )
            )
        if not non_empty_string(assessment.get("summary")):
            findings.append(Finding("empty-final-assessment", "final_assessment.summary is empty"))
        if assessment.get("form_compliance_not_enough") is not True:
            findings.append(
                Finding(
                    "missing-meta-rule",
                    "final_assessment.form_compliance_not_enough must be true",
                )
            )

    validate_escape_review(output, judge, findings)
    escape = output.get("applicability") if output.get("applicability") in METHOD_EXIT_VALUES else ""
    return findings, total, escape


def render_prompt(output: dict[str, Any], method: str, repo_root: Path) -> str:
    rubric_path = repo_root / METHOD_RUBRICS[method]
    rubric_text = rubric_path.read_text(encoding="utf-8")
    return "\n".join(
        (
            "# Fidelity Judge Prompt",
            "",
            "Judge faithful method execution, not preferred conclusion.",
            "Return JSON using schema_version mindthus-fidelity-judge-v0.1.",
            "When applicability is not_applicable, transfer, or challenge_premise, the judge must review whether the exit itself is justified; do not automatically pass a method exit.",
            "Form compliance is not enough: filled fields can still score 0 or 1.",
            "",
            "## Rubric",
            "",
            rubric_text,
            "",
            "## Artifact Under Review",
            "",
            json.dumps(output, ensure_ascii=False, indent=2),
        )
    )


def print_report(path: Path, findings: list[Finding], total: int, max_total: int, escape: str) -> None:
    print("Fidelity Judge Report")
    print(f"Judge file: {path}")
    print()
    if escape and not findings:
        print(f"escape review accepted: {escape}")
        print()
    if findings:
        for item in findings:
            print(f"- BLOCK [{item.code}]: {item.message}")
    else:
        print(f"Total score: {total} / {max_total}")
        print("No judge-contract risks detected.")
    print()
    print(
        "Reminder: judge automation does not validate strategic truth; "
        "it validates rubric-result shape and required review coverage."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Method output JSON to review.")
    parser.add_argument("--judge", type=Path, help="Completed judge JSON result.")
    parser.add_argument("--method", default="SELA", choices=sorted(METHOD_DIMENSIONS), help="Method rubric to use.")
    parser.add_argument("--print-prompt", action="store_true", help="Print a reproducible judge prompt.")
    args = parser.parse_args()

    output = load_json(args.output)
    repo_root = Path(__file__).resolve().parents[1]

    if args.print_prompt:
        if not isinstance(output, dict):
            raise SystemExit("method output must be an object to render a judge prompt")
        print(render_prompt(output, args.method, repo_root))
        return 0

    if args.judge is None:
        raise SystemExit("--judge is required unless --print-prompt is set")

    judge = load_json(args.judge)
    findings, total, escape = validate_judge_result(output, judge)
    max_total = len(METHOD_DIMENSIONS.get(judge.get("method"), ())) * 2
    print_report(args.judge, findings, total, max_total, escape)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
