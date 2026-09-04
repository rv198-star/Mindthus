#!/usr/bin/env python3
"""Prepare a version-bound, context-calibrated SRA v0.3 decision run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sra_runtime import (
    RUN_CLAIM_CEILING,
    RUN_SCHEMA,
    SraRuntimeError,
    SraValidationError,
    append_jsonl,
    build_packets,
    initial_statuses,
    load_json,
    make_runtime_event,
    now_iso,
    save_run_state,
    write_json,
    write_stage_surface,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build SRA v0.3 context, resource, coverage, challenge, and situated "
            "surfaces. This command never chooses semantic priority."
        )
    )
    parser.add_argument("--input", required=True, help="SRA decision-context JSON path.")
    parser.add_argument("--dir", required=True, help="New SRA run directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    return parser.parse_args()


def prepare(input_path: Path, run_dir: Path) -> dict[str, object]:
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SraRuntimeError(f"refusing to overwrite non-empty run directory: {run_dir}")

    raw_input = load_json(input_path)
    if not isinstance(raw_input, dict):
        raise SraRuntimeError("SRA decision-context input must be an object")
    built = build_packets(raw_input)
    run_dir.mkdir(parents=True, exist_ok=True)

    raw_path = run_dir / "raw-input.json"
    admission_path = run_dir / "context-admission.json"
    base_path = run_dir / "base-packet.json"
    coverage_path = run_dir / "coverage-packet.json"
    challenge_path = run_dir / "challenge-packet.json"
    situated_path = run_dir / "situated-packet.json"
    trace_path = run_dir / "trace.jsonl"

    write_json(raw_path, raw_input)
    write_json(admission_path, built["admission"])
    write_json(base_path, built["base_packet"])
    write_json(coverage_path, built["coverage_packet"])
    write_json(challenge_path, built["challenge_packet"])
    write_json(situated_path, built["situated_packet"])

    paths: dict[str, str] = {
        "raw_input": str(raw_path),
        "context_admission": str(admission_path),
        "base_packet": str(base_path),
        "coverage_packet": str(coverage_path),
        "challenge_packet": str(challenge_path),
        "situated_packet": str(situated_path),
        "trace": str(trace_path),
    }
    if built["coverage_plan"] == "required":
        paths.update(
            write_stage_surface(
                run_dir=run_dir,
                stage="coverage",
                packet=built["coverage_packet"],
            )
        )
    if built["view_plan"] == "dual_view":
        paths.update(
            write_stage_surface(
                run_dir=run_dir,
                stage="challenge",
                packet=built["challenge_packet"],
            )
        )
    paths.update(
        write_stage_surface(
            run_dir=run_dir,
            stage="situated",
            packet=built["situated_packet"],
        )
    )

    statuses = initial_statuses(built["view_plan"], built["coverage_plan"])
    state = {
        "schema_version": RUN_SCHEMA,
        "run_id": raw_input["run_id"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "mode": built["mode"],
        "view_plan": built["view_plan"],
        "coverage_plan": built["coverage_plan"],
        "statuses": statuses,
        "raw_input_hash": built["raw_input_hash"],
        "context_admission_hash": built["context_admission_hash"],
        "base_packet_hash": built["base_packet"]["packet_hash"],
        "coverage_packet_hash": built["coverage_packet"]["packet_hash"],
        "challenge_packet_hash": built["challenge_packet"]["packet_hash"],
        "situated_packet_hash": built["situated_packet"]["packet_hash"],
        "coverage_judgment_hash": None,
        "challenge_judgment_hash": None,
        "situated_judgment_hash": None,
        "comparison_hash": None,
        "reconciliation_packet_hash": None,
        "reconciliation_judgment_hash": None,
        "challenge_map": built["challenge_map"],
        "context_weights": built["context_weights"],
        "governance_overrides": built["governance_overrides"],
        "warnings": built["warnings"],
        "carriers": {},
        "carrier_receipts": {},
        "paths": paths,
        "claim_ceiling": RUN_CLAIM_CEILING,
    }
    save_run_state(run_dir / "run.json", state)
    append_jsonl(
        trace_path,
        make_runtime_event(
            raw_input["run_id"],
            "run_prepared",
            {
                "mode": built["mode"],
                "view_plan": built["view_plan"],
                "coverage_plan": built["coverage_plan"],
                "raw_input_hash": built["raw_input_hash"],
                "context_admission_hash": built["context_admission_hash"],
                "base_packet_hash": built["base_packet"]["packet_hash"],
                "coverage_packet_hash": built["coverage_packet"]["packet_hash"],
                "challenge_packet_hash": built["challenge_packet"]["packet_hash"],
                "situated_packet_hash": built["situated_packet"]["packet_hash"],
                "admitted_context_ids": built["admission"]["admitted_ids"],
                "quarantined_context_ids": built["admission"]["quarantined_ids"],
                "excluded_context_ids": built["admission"]["excluded_ids"],
                "governance_overrides": built["governance_overrides"],
                "warnings": built["warnings"],
            },
        ),
    )

    if built["coverage_plan"] == "required":
        next_action = "Run and record the coverage review before any allocation judgment."
    elif built["view_plan"] == "dual_view":
        next_action = "Run challenge and situated judgments independently; either may finish first."
    else:
        next_action = "Run and record the situated judgment."
    return {
        "run_dir": str(run_dir),
        "run_id": raw_input["run_id"],
        "mode": built["mode"],
        "view_plan": built["view_plan"],
        "coverage_plan": built["coverage_plan"],
        "statuses": statuses,
        "admitted_context": len(built["admission"]["admitted_ids"]),
        "quarantined_context": len(built["admission"]["quarantined_ids"]),
        "excluded_context": len(built["admission"]["excluded_ids"]),
        "governance_overrides": built["governance_overrides"],
        "warnings": built["warnings"],
        "next_action": next_action,
    }


def main() -> int:
    args = parse_args()
    try:
        result = prepare(Path(args.input), Path(args.dir))
    except SraValidationError as exc:
        for item in exc.findings:
            print(f"BLOCK: {item}", file=sys.stderr)
        return 1
    except SraRuntimeError as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("SRA v0.3 context-calibrated run prepared")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
