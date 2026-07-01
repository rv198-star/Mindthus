#!/usr/bin/env python3
"""Report deterministic prompt-packet findings for TVG review."""

from __future__ import annotations

import argparse

from _profile_support import boundary_payload, extract_fields, load_resource, normalize, write_json


HUMAN_SCALE_TERMS = (
    "human",
    "person",
    "people",
    "crowd",
    "pedestrian",
    "driver",
    "observer",
    "witness",
    "diver",
    "submersible",
    "vehicle",
    "street",
    "window",
    "instrument",
)
PHYSICAL_FEEDBACK_TERMS = (
    "push",
    "pull",
    "ripple",
    "scatter",
    "flicker",
    "shake",
    "bend",
    "compress",
    "silt",
    "dust",
    "rain",
    "mist",
    "debris",
    "cable",
    "cloud",
    "water",
    "wind",
)
PARTIAL_VISIBILITY_TERMS = (
    "partial",
    "partly",
    "hidden",
    "occluded",
    "frame",
    "beyond",
    "silhouette",
    "shadow",
    "obscured",
)


def field_findings(expected_fields: str | None, output: str) -> tuple[list[str], dict]:
    if not expected_fields:
        return [], {}
    expected = extract_fields(expected_fields)
    actual = extract_fields(output)
    missing = [field for field in expected if field not in actual]
    extra = [field for field in actual if field not in expected]
    findings: list[str] = []
    if missing:
        findings.append("missing_field")
    if extra:
        findings.append("extra_field")
    if not missing and not extra and actual[: len(expected)] != expected:
        findings.append("field_order_changed")
    return findings, {"missing_fields": missing, "extra_fields": extra, "actual_fields": actual}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--expected-fields")
    args = parser.parse_args()
    text = normalize(args.prompt)
    negative = load_resource("negative-constraints.json")
    finding_codes: list[str] = []
    details: dict = {}

    if not any(term in text for term in HUMAN_SCALE_TERMS):
        finding_codes.append("missing_human_scale_anchor")
    if not any(term in text for term in PHYSICAL_FEEDBACK_TERMS):
        finding_codes.append("missing_physical_environment_feedback")
    if any(term in text for term in negative["forbidden_media_terms"]):
        finding_codes.append("forbidden_media_term")
    if not any(term in text for term in PARTIAL_VISIBILITY_TERMS):
        finding_codes.append("missing_partial_visibility")

    field_codes, field_details = field_findings(args.expected_fields, args.prompt)
    finding_codes.extend(field_codes)
    details.update(field_details)

    payload = boundary_payload(
        finding_codes=finding_codes,
        details=details,
        notes=[
            "Findings are deterministic support signals.",
            "Agentic TVG audit decides remediation or exit.",
        ],
    )
    write_json(payload, 1 if finding_codes else 0)


if __name__ == "__main__":
    main()
