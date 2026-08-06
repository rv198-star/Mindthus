#!/usr/bin/env python3
"""Validate a local Mindthus case export package before manual sharing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from runtime_import import activate_shared_runtime

activate_shared_runtime(__file__)

from _runtime.judgment.case_export import validate_case_package  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "A passing result does not prove anonymity, consent sufficiency, semantic correctness, "
            "or benchmark admission value."
        ),
    )
    parser.add_argument("package", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    findings = validate_case_package(args.package)
    blocks = [item for item in findings if item.severity == "block"]
    warnings = [item for item in findings if item.severity == "warn"]
    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": "mindthus.case-export-validation-report.v1",
                    "package": str(args.package),
                    "status": "invalid" if blocks else "review_required",
                    "block_count": len(blocks),
                    "warning_count": len(warnings),
                    "findings": [
                        {
                            "severity": item.severity,
                            "code": item.code,
                            "message": item.message,
                            "subject": item.subject,
                        }
                        for item in findings
                    ],
                    "sharing_boundary": "manual review and a separate user action remain required",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print("Mindthus Case Export Validation")
        print(f"Package: {args.package}")
        print()
        if not findings:
            print("No known package-shape or suspicious-content indicators detected.")
        else:
            for item in findings:
                subject = f" [{item.subject}]" if item.subject else ""
                print(f"- {item.severity.upper()} [{item.code}]{subject}: {item.message}")
        print()
        print("review_required_before_share: true")
        print("Reminder: this validator does not prove anonymity, consent, or judgment correctness.")
    return 1 if blocks else 0


if __name__ == "__main__":
    raise SystemExit(main())
