#!/usr/bin/env python3
"""Initialize a Thinking Value-Gain trace record.

This script creates bookkeeping scaffolding only. It does not perform audit judgment.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def build_trace(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "tvg-trace-v0.2",
        "method_version": "Thinking Value-Gain Methodology v0.2",
        "created_at": now,
        "updated_at": now,
        "module": {
            "id": args.module_id,
            "title": args.module_title,
            "type": args.module_type,
            "downstream_consumer": args.downstream_consumer,
            "freeze_granularity": args.freeze_granularity,
        },
        "value_gain": {
            "claimed_value_gain": "",
            "value_gain_types": [],
            "selected_axes": [],
            "evidence_support": "",
            "remaining_review_bound": [],
        },
        "rounds": [],
        "agentic_exit_audit": {
            "disagreements": [],
            "demo_false_positive_risk": "",
            "overfitting_risk": "",
            "downstream_usability": "",
            "exit_state": "",
            "why_not_another_round": "",
        },
        "script_support": {
            "trace_initialized_by_script": True,
            "script_verdict": "No schema violations were detected only after validation; agentic audit is still required.",
            "script_cannot_decide": [
                "value_gain",
                "demo_false_positive_risk",
                "overfitting_risk",
                "another_round_value",
                "exit_state",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a TVG trace record.")
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--module-title", required=True)
    parser.add_argument("--module-type", required=True)
    parser.add_argument("--downstream-consumer", default="")
    parser.add_argument("--freeze-granularity", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_trace(args), ensure_ascii=False, indent=2) + "\n")
    print(f"initialized_trace: {output}")
    print("script_result: bookkeeping scaffold created; agentic audit is still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
