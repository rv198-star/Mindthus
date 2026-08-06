#!/usr/bin/env python3
"""Validate a bounded TPlan Case Packet v1 before manual sharing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from case_prep_core import validate_tplan_case_packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings = validate_tplan_case_packet(args.package)
    blocks = [item for item in findings if item.severity == "block"]
    payload = {
        "schema_version": "tplan.case-packet-validation.v1",
        "status": "invalid" if blocks else "review_required",
        "package": str(args.package),
        "block_count": len(blocks),
        "warning_count": sum(item.severity == "warn" for item in findings),
        "findings": [item.__dict__ for item in findings],
        "sharing_boundary": "manual review and a separate user action remain required",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status: {payload['status']}")
        for item in findings:
            print(f"{item.severity.upper()} [{item.code}]: {item.message}")
        print("review_required_before_share: true")
    return 1 if blocks else 0


if __name__ == "__main__":
    raise SystemExit(main())
