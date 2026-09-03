#!/usr/bin/env python3
"""Check a context-calibrated SRA run without judging semantic priority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sra_runtime import run_check


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate SRA packets, independent-view state, typed comparison, references, "
            "hashes, carrier records, and finalization."
        )
    )
    parser.add_argument("--dir", required=True, help="SRA run directory.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_check(Path(args.dir))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("SRA Context-Calibrated Runtime Check")
        print(f"Run: {report.get('run_dir')}")
        print(f"Mode: {report.get('mode', 'unknown')}")
        print(f"View plan: {report.get('view_plan', 'unknown')}")
        print(f"Coverage plan: {report.get('coverage_plan', 'unknown')}")
        print(f"Statuses: {report.get('statuses', {})}")
        print(f"Status: {report.get('status')}")
        print(f"Context boundary: {report.get('observed_context_boundary', 'unknown')}")
        print()
        findings = report.get("findings", [])
        if not findings:
            print("No runtime packet, reference, hash, comparison, or stage risks detected.")
        else:
            for item in findings:
                print(
                    f"- {str(item.get('severity', '')).upper()} "
                    f"[{item.get('code', '')}]: {item.get('message', '')}"
                )
        print()
        print(report.get("truth_boundary", ""))
    return 1 if report.get("status") == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
