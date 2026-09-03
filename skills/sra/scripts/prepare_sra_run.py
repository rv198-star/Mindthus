#!/usr/bin/env python3
"""Prepare a sealed, context-admitted SRA allocation run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sra_runtime import (
    RUN_SCHEMA,
    SraRuntimeError,
    SraValidationError,
    blind_output_schema,
    build_packets,
    carrier_command,
    carrier_dispatch,
    make_runtime_event,
    now_iso,
    append_jsonl,
    load_json,
    prompt_for_blind,
    save_run_state,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a context-admission ledger, sealed SRA packet, blind packet, and "
            "logical/fresh-context carrier artifacts. This does not decide priority."
        )
    )
    parser.add_argument("--input", required=True, help="SRA context-input JSON path.")
    parser.add_argument("--dir", required=True, help="New SRA run directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    return parser.parse_args()


def prepare(input_path: Path, run_dir: Path) -> dict[str, object]:
    if run_dir.exists() and any(run_dir.iterdir()):
        raise SraRuntimeError(f"refusing to overwrite non-empty run directory: {run_dir}")

    raw_input = load_json(input_path)
    built = build_packets(raw_input)
    run_dir.mkdir(parents=True, exist_ok=True)

    raw_path = run_dir / "raw-input.json"
    admission_path = run_dir / "context-admission.json"
    sealed_path = run_dir / "sealed-packet.json"
    blind_path = run_dir / "blind-packet.json"
    prompt_path = run_dir / "blind-agent-prompt.md"
    output_schema_path = run_dir / "blind-output-schema.json"
    dispatch_path = run_dir / "blind-subagent-dispatch.json"
    command_path = run_dir / "blind-codex-command.sh"
    output_path = run_dir / "judgments" / "blind.candidate.json"
    workspace_path = run_dir / "fresh-context-workspace"
    trace_path = run_dir / "trace.jsonl"

    write_json(raw_path, raw_input)
    write_json(admission_path, built["admission"])
    write_json(sealed_path, built["sealed_packet"])
    write_json(blind_path, built["blind_packet"])
    prompt_path.write_text(prompt_for_blind(built["blind_packet"]), encoding="utf-8")
    write_json(output_schema_path, blind_output_schema(built["blind_packet"]))
    write_json(
        dispatch_path,
        carrier_dispatch(
            prompt_path.resolve(),
            stage="blind",
            output_path=output_path.resolve(),
            output_schema_path=output_schema_path.resolve(),
        ),
    )
    command_path.write_text(
        carrier_command(
            prompt_path=prompt_path.resolve(),
            output_path=output_path.resolve(),
            output_schema_path=output_schema_path.resolve(),
            workspace_path=workspace_path.resolve(),
        ),
        encoding="utf-8",
    )
    command_path.chmod(0o755)
    workspace_path.mkdir(parents=True, exist_ok=True)

    state = {
        "schema_version": RUN_SCHEMA,
        "run_id": raw_input["run_id"],
        "stage": "prepared",
        "mode": built["mode"],
        "isolation_profile": built["isolation_profile"],
        "isolation_override_reason": raw_input.get("isolation_override_reason"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "raw_input_hash": built["raw_input_hash"],
        "context_manifest_hash": built["context_manifest_hash"],
        "sealed_packet_hash": built["sealed_packet"]["packet_hash"],
        "blind_packet_hash": built["blind_packet"]["packet_hash"],
        "candidate_map": built["candidate_map"],
        "context_weights": built["context_weights"],
        "warnings": built["warnings"],
        "carriers": {},
        "paths": {
            "raw_input": str(raw_path),
            "context_admission": str(admission_path),
            "sealed_packet": str(sealed_path),
            "blind_packet": str(blind_path),
            "blind_prompt": str(prompt_path),
            "blind_output_schema": str(output_schema_path),
            "blind_dispatch": str(dispatch_path),
            "blind_cli_command": str(command_path),
            "trace": str(trace_path),
        },
        "claim_ceiling": (
            "The runtime proves deterministic admission, packet, hash, reference, and stage contracts only. "
            "It does not prove complete context, fresh-host isolation, or correct semantic priority."
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
                "isolation_profile": built["isolation_profile"],
                "isolation_override_reason": raw_input.get("isolation_override_reason"),
                "raw_input_hash": built["raw_input_hash"],
                "context_manifest_hash": built["context_manifest_hash"],
                "sealed_packet_hash": built["sealed_packet"]["packet_hash"],
                "blind_packet_hash": built["blind_packet"]["packet_hash"],
                "admitted_context_ids": built["admission"]["admitted_ids"],
                "quarantined_context_ids": built["admission"]["quarantined_ids"],
                "excluded_context_ids": built["admission"]["excluded_ids"],
                "warnings": built["warnings"],
            },
        ),
    )
    return {
        "run_dir": str(run_dir),
        "run_id": raw_input["run_id"],
        "stage": "prepared",
        "mode": built["mode"],
        "isolation_profile": built["isolation_profile"],
        "isolation_override_reason": raw_input.get("isolation_override_reason"),
        "raw_input_hash": built["raw_input_hash"],
        "context_manifest_hash": built["context_manifest_hash"],
        "sealed_packet_hash": built["sealed_packet"]["packet_hash"],
        "blind_packet_hash": built["blind_packet"]["packet_hash"],
        "admitted_context": len(built["admission"]["admitted_ids"]),
        "quarantined_context": len(built["admission"]["quarantined_ids"]),
        "excluded_context": len(built["admission"]["excluded_ids"]),
        "warnings": built["warnings"],
        "next_action": (
            "Run the blind prompt through a packet-bound or fresh-context Agentic carrier, "
            "then record it with record_sra_judgment.py --stage blind."
        ),
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
        print("SRA context-isolated run prepared")
        for key, value in result.items():
            if key != "warnings":
                print(f"{key}: {value}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
