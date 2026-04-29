#!/usr/bin/env python3
"""Validate a tplan decision hook output without mutating Mission state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import decision_validation_report, validate_hook_output


def print_report(report: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    if report["valid"]:
        print("decision_valid: true")
        print("next_action: apply_decision")
    else:
        print("decision_valid: false")
        for error in report["errors"]:
            print(f"error: {error}")
        print("next_action: repair_decision")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a tplan decision JSON file without mutation.")
    parser.add_argument("--decision", required=True)
    parser.add_argument("--json", action="store_true", help="Print machine-readable validation report.")
    args = parser.parse_args()

    try:
        decision = json.loads(Path(args.decision).read_text(encoding="utf-8"))
        errors = validate_hook_output(decision)
    except json.JSONDecodeError as exc:
        errors = [f"invalid JSON: {exc.msg}"]
        decision = None
    except OSError as exc:
        errors = [str(exc)]
        decision = None

    report = decision_validation_report(decision, errors)
    print_report(report, args.json)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
