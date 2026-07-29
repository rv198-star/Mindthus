#!/usr/bin/env python3
"""Preflight TPlan Mission identity and project-level shared context."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import (
    MISSION_REENTRY_DISPOSITIONS,
    TplanError,
    build_mission_preflight,
    parse_acceptance_evidence,
    record_and_apply_mission_reentry_decision,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight tplan Mission shared context.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mission-id")
    parser.add_argument(
        "--mission-dir",
        help="Optional runtime directory selected for this Mission candidate.",
    )
    parser.add_argument("--objective")
    parser.add_argument(
        "--acceptance-evidence",
        action="append",
        default=[],
        help="Acceptance evidence as ID:description. Repeat for multiple items.",
    )
    parser.add_argument(
        "--disposition",
        choices=sorted(MISSION_REENTRY_DISPOSITIONS),
        help=(
            "Explicit agentic re-entry disposition. Omit it for read-only candidate "
            "discovery and assessment."
        ),
    )
    parser.add_argument(
        "--rationale",
        help="Required non-empty rationale when --disposition is supplied.",
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
            mission_dir=Path(args.mission_dir) if args.mission_dir else None,
            disposition=args.disposition,
            rationale=args.rationale,
        )
        if args.disposition is not None:
            payload = record_and_apply_mission_reentry_decision(
                Path(args.project_root),
                payload,
            )
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if payload.get("user_message"):
            print(f"message: {payload['user_message']}")
        print(f"action: {payload['action']}")
        if payload.get("mission_id"):
            print(f"mission_id: {payload['mission_id']}")
        if payload.get("identity_action"):
            print(f"identity_action: {payload['identity_action']}")
        if payload.get("candidate_disposition"):
            print(f"candidate_disposition: {payload['candidate_disposition']}")
        print(f"decision_required: {str(bool(payload.get('decision_required'))).lower()}")
        if payload.get("context_file"):
            print(f"context_file: {payload['context_file']}")
        if payload.get("conflicts"):
            print("conflicts: " + ", ".join(payload["conflicts"]))
        if payload.get("warnings"):
            print("warnings: " + ", ".join(payload["warnings"]))
        if payload.get("missing_current_intent"):
            print(
                "missing_current_intent: "
                + ", ".join(payload["missing_current_intent"])
            )
        decision = payload.get("reentry_decision")
        if isinstance(decision, dict):
            print(f"reentry_disposition: {decision['disposition']}")
        receipt = payload.get("decision_receipt")
        if isinstance(receipt, dict):
            print(f"decision_receipt: {receipt['path']}")
            print(
                "decision_application: "
                + str(receipt.get("application", {}).get("status"))
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
