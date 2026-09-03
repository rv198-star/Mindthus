#!/usr/bin/env python3
"""Prepare a context-calibrated SRA decision run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from sra_runtime import (
    RUN_SCHEMA,
    SraRuntimeError,
    SraValidationError,
    append_jsonl,
    build_packets,
    carrier_command,
    carrier_dispatch,
    challenge_output_schema,
    coverage_output_schema,
    make_runtime_event,
    now_iso,
    prompt_for_challenge,
    prompt_for_coverage,
    prompt_for_situated,
    save_run_state,
    situated_output_schema,
    load_json,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a context-admission ledger and independent SRA judgment packets. "
            "This script never chooses semantic priority."
        )
    )
    parser.add_argument("--input", required=True, help="SRA decision-context JSON path.")
    parser.add_argument("--dir", required=True, help="New SRA run directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    return parser.parse_args()


def _write_surface(
    *,
    run_dir: Path,
    stage: str,
    packet: dict[str, Any],
    prompt_builder: Callable[[dict[str, Any]], str],
    schema_builder: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, str]:
    prompt_path = run_dir / f"{stage}-agent-prompt.md"
    schema_path = run_dir / f"{stage}-output-schema.json"
    dispatch_path = run_dir / f"{stage}-subagent-dispatch.json"
    command_path = run_dir / f"{stage}-codex-command.sh"
    output_path = run_dir / "judgments" / f"{stage}.candidate.json"
    workspace_path = run_dir / f"fresh-context-workspace-{stage}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt_builder(packet), encoding="utf-8")
    write_json(schema_path, schema_builder(packet))
    write_json(
        dispatch_path,
        carrier_dispatch(
            prompt_path.resolve(),
            stage=stage,
            output_path=output_path.resolve(),
            output_schema_path=schema_path.resolve(),
        ),
    )
    command_path.write_text(
        carrier_command(
            prompt_path=prompt_path.resolve(),
            output_path=output_path.resolve(),
            output_schema_path=schema_path.resolve(),
            workspace_path=workspace_path.resolve(),
        ),
        encoding="utf-8",
    )
    command_path.chmod(0o755)
    workspace_path.mkdir(parents=True, exist_ok=True)
    return {
        f"{stage}_prompt": str(prompt_path),
        f"{stage}_output_schema": str(schema_path),
        f"{stage}_dispatch": str(dispatch_path),
        f"{stage}_cli_command": str(command_path),
    }


def prepare(input_path: Path, run_dir: Path) -> dict[str, object]:
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SraRuntimeError(f"refusing to overwrite non-empty run directory: {run_dir}")

    raw_input = load_json(input_path)
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
            _write_surface(
                run_dir=run_dir,
                stage="coverage",
                packet=built["coverage_packet"],
                prompt_builder=prompt_for_coverage,
                schema_builder=coverage_output_schema,
            )
        )
    if built["view_plan"] == "dual_view":
        paths.update(
            _write_surface(
                run_dir=run_dir,
                stage="challenge",
                packet=built["challenge_packet"],
                prompt_builder=prompt_for_challenge,
                schema_builder=challenge_output_schema,
            )
        )
    paths.update(
        _write_surface(
            run_dir=run_dir,
            stage="situated",
            packet=built["situated_packet"],
            prompt_builder=prompt_for_situated,
            schema_builder=situated_output_schema,
        )
    )

    statuses = {
        "coverage": "pending" if built["coverage_plan"] == "required" else "not_required",
        "challenge": "pending" if built["view_plan"] == "dual_view" else "not_required",
        "situated": "pending",
        "comparison": "pending" if built["view_plan"] == "dual_view" else "not_required",
        "reconciliation": "not_required",
        "finalization": "pending",
    }
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
        "warnings": built["warnings"],
        "carriers": {},
        "carrier_receipts": {},
        "paths": paths,
        "claim_ceiling": (
            "Workflow proves packet, reference, stage, comparison, and observable carrier integrity only. "
            "It does not prove complete context, absent hidden host context, or correct priority."
        ),
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
                "base_packet_hash": built["base_packet"]["packet_hash"],
                "coverage_packet_hash": built["coverage_packet"]["packet_hash"],
                "challenge_packet_hash": built["challenge_packet"]["packet_hash"],
                "situated_packet_hash": built["situated_packet"]["packet_hash"],
                "admitted_context_ids": built["admission"]["admitted_ids"],
                "quarantined_context_ids": built["admission"]["quarantined_ids"],
                "excluded_context_ids": built["admission"]["excluded_ids"],
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
        print("SRA context-calibrated run prepared")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
