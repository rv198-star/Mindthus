#!/usr/bin/env python3
"""Validate preservation of user-supplied field markers."""

from __future__ import annotations

import argparse

from _profile_support import boundary_payload, extract_fields, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-fields", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    expected = extract_fields(args.expected_fields)
    actual = extract_fields(args.output)
    missing = [field for field in expected if field not in actual]
    extra = [field for field in actual if field not in expected]
    finding_codes: list[str] = []
    if missing:
        finding_codes.append("missing_field")
    if extra:
        finding_codes.append("extra_field")
    if not missing and not extra and actual[: len(expected)] != expected:
        finding_codes.append("field_order_changed")

    write_json(
        boundary_payload(
            finding_codes=finding_codes,
            missing_fields=missing,
            extra_fields=extra,
            actual_fields=actual,
            notes=[
                "Field-lock validation is deterministic support only.",
                "It does not decide prompt quality.",
            ],
        ),
        1 if finding_codes else 0,
    )


if __name__ == "__main__":
    main()
