#!/usr/bin/env python3
"""Check SRA context-isolated runtime integrity without judging priority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sra_runtime import run_check


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate SRA run files, hashes, stage order, references, and observable "
            "isolation claims. This does not judge semantic priority."
        )
    )
    parser.add_argument("--dir", required=True, help="SRA run directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_check(Path(args.dir))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("SRA Context-Isolated Runtime Check")
        print(f"Run: {report.get('run_dir')}")
        print(f"Stage: {report.get('stage', 'unknown')}")
        print(f"Status: {report.get('status')}")
        print(f"Isolation requested: {report.get('isolation_profile', 'unknown')}")
        print(f"Recorded carriers: {report.get('recorded_carriers', {})}")
        print()
        findings = report.get("findings", [])
        if not findings:
            print("No runtime shape, reference, hash, or stage risks detected.")
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
