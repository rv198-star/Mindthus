#!/usr/bin/env python3
"""Preflight TPlan Mission identity and project-level shared context."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import build_mission_preflight, parse_acceptance_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight tplan Mission shared context.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mission-id")
    parser.add_argument("--objective")
    parser.add_argument(
        "--acceptance-evidence",
        action="append",
        default=[],
        help="Acceptance evidence as ID:description. Repeat for multiple items.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        acceptance = parse_acceptance_evidence(args.acceptance_evidence)
        payload = build_mission_preflight(
            Path(args.project_root),
            mission_id=args.mission_id,
            objective=args.objective,
            acceptance_evidence=acceptance if args.acceptance_evidence else None,
        )
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"action: {payload['action']}")
        if payload.get("mission_id"):
            print(f"mission_id: {payload['mission_id']}")
        if payload.get("context_file"):
            print(f"context_file: {payload['context_file']}")
        if payload.get("conflicts"):
            print("conflicts: " + ", ".join(payload["conflicts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
