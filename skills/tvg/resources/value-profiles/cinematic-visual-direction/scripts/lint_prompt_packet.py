#!/usr/bin/env python3
"""Report deterministic cinematic prompt findings without deciding quality or exit."""

from __future__ import annotations

import argparse

from _profile_support import (
    boundary_payload,
    extract_fields,
    load_adapter,
    normalize,
    write_json,
)


CAMERA_TERMS = ("camera", "lens", "viewpoint", "angle", "wide", "close", "镜头", "景别", "视角")
LIGHT_TERMS = ("light", "shadow", "exposure", "glow", "sun", "moon", "灯", "光", "阴影", "曝光")
RELATION_TERMS = ("foreground", "midground", "background", "edge", "behind", "through", "前景", "中景", "远景", "边缘")
COLOSSAL_WITNESS_TERMS = ("human", "person", "crowd", "witness", "vehicle", "instrument", "人", "人群", "目击", "车辆", "仪器")
COLOSSAL_FEEDBACK_TERMS = ("rain", "mist", "dust", "water", "wind", "debris", "cloud", "雨", "雾", "尘", "水", "风", "碎片", "云")


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
    parser.add_argument("--adapter")
    args = parser.parse_args()

    text = normalize(args.prompt)
    findings: list[str] = []
    details: dict = {}
    if not any(term in text for term in CAMERA_TERMS):
        findings.append("missing_camera_relation")
    if not any(term in text for term in LIGHT_TERMS):
        findings.append("missing_light_relation")
    if not any(term in text for term in RELATION_TERMS):
        findings.append("missing_spatial_relation")

    if args.adapter:
        adapter = load_adapter(args.adapter)
        details["adapter"] = adapter["adapter"]
        if adapter["adapter"] == "colossal-pressure":
            if not any(term in text for term in COLOSSAL_WITNESS_TERMS):
                findings.append("missing_colossal_witness_anchor")
            if not any(term in text for term in COLOSSAL_FEEDBACK_TERMS):
                findings.append("missing_colossal_environment_feedback")

    field_codes, field_details = field_findings(args.expected_fields, args.prompt)
    findings.extend(field_codes)
    details.update(field_details)
    write_json(
        boundary_payload(
            finding_codes=findings,
            details=details,
            notes=[
                "Findings are deterministic support signals.",
                "Agentic TVG audit decides relevance, remediation, or exit.",
            ],
        ),
        1 if findings else 0,
    )


if __name__ == "__main__":
    main()
