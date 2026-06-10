#!/usr/bin/env python3
"""Record or resolve a Mission-level shared risk context signal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tplan_runtime import TplanError, record_risk_signal, resolve_risk_signal


def record_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "scope": args.scope,
        "signal": args.signal,
        "severity": args.severity,
        "confidence": args.confidence,
        "affected_surfaces": args.affected_surface,
        "value_effect": args.value_effect,
        "recommended_gate": args.recommended_gate,
        "recovery_condition": args.recovery_condition,
    }
    if args.summary:
        payload["summary"] = args.summary
    if args.notes:
        payload["notes"] = args.notes
    if args.supersedes:
        payload["supersedes"] = args.supersedes
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record or resolve shared tplan risk context.")
    parser.add_argument("mission_dir")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    record = subparsers.add_parser("record", help="Record a new shared risk signal.")
    record.add_argument("--task-id", required=True)
    record.add_argument("--scope", required=True)
    record.add_argument("--signal", required=True)
    record.add_argument("--severity", required=True)
    record.add_argument("--confidence", required=True)
    record.add_argument("--affected-surface", action="append", required=True)
    record.add_argument("--value-effect", required=True)
    record.add_argument("--recommended-gate", required=True)
    record.add_argument("--recovery-condition", required=True)
    record.add_argument("--summary")
    record.add_argument("--notes")
    record.add_argument("--supersedes", action="append")

    resolve = subparsers.add_parser("resolve", help="Resolve, supersede, or invalidate a risk signal.")
    resolve.add_argument("--task-id", required=True)
    resolve.add_argument("--risk-id", required=True)
    resolve.add_argument("--status", required=True)
    resolve.add_argument("--summary", required=True)
    resolve.add_argument("--recovery-note", required=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        mission_dir = Path(args.mission_dir)
        if args.command == "record":
            result = record_risk_signal(mission_dir, args.task_id, record_payload(args))
        else:
            result = resolve_risk_signal(
                mission_dir,
                args.task_id,
                args.risk_id,
                args.status,
                args.summary,
                args.recovery_note,
            )
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"risk_signal: {result['risk_signal']['id']} {result['risk_signal']['status']}")
        print(f"risk_evidence: {result['event']['id']}")
        print("script_result: shared risk context recorded; semantic relevance remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
