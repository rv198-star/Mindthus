#!/usr/bin/env python3
"""Validate a Mindthus Judgment Trace v1 without judging semantic truth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from runtime_import import activate_shared_runtime

activate_shared_runtime(__file__)

from _runtime.core.report import print_shape_report  # noqa: E402
from _runtime.judgment.trace import TraceValidationError, load_judgment_trace  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="Path to a Judgment Trace JSON file.")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        load_judgment_trace(args.trace)
        findings = []
    except TraceValidationError as exc:
        findings = exc.findings

    if args.json:
        payload = {
            "schema_version": "mindthus.judgment-trace-validation-report.v1",
            "path": str(args.trace),
            "status": "valid" if not findings else "invalid",
            "findings": [
                {
                    "severity": item.severity,
                    "code": item.code,
                    "message": item.message,
                    "subject": item.subject,
                }
                for item in findings
            ],
            "truth_boundary": "shape validation does not prove judgment correctness",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_shape_report(
            title="Mindthus Judgment Trace Validation",
            path=args.trace,
            findings=findings,
            truth_boundary="judgment correctness, causality, or real-world outcome quality",
            no_risks_message="Judgment Trace shape is valid.",
        )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
