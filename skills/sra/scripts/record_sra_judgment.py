#!/usr/bin/env python3
"""Record packet-bound Agentic SRA judgments and advance runtime state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sra_runtime import (
    CARRIERS,
    SraRuntimeError,
    SraValidationError,
    append_jsonl,
    build_state_packet,
    carrier_command,
    carrier_dispatch,
    digest_data,
    effective_isolation_claim,
    load_json,
    hidden_candidate_identity_findings,
    load_run,
    make_runtime_event,
    prompt_for_state,
    run_check,
    save_run_state,
    state_output_schema,
    validate_blind_judgment,
    validate_state_judgment,
    write_json,
)


FINAL_DECISION_SCHEMA = "sra.final-decision.v0.1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record a blind or state-aware SRA Agentic judgment. The script validates "
            "packet binding and references; it does not decide semantic priority."
        )
    )
    parser.add_argument("--dir", required=True, help="Prepared SRA run directory.")
    parser.add_argument("--stage", required=True, choices=("blind", "state-aware"))
    parser.add_argument("--input", required=True, help="Agentic judgment JSON path.")
    parser.add_argument(
        "--carrier",
        default="packet_bound",
        choices=sorted(CARRIERS),
        help="Observable carrier used for this judgment.",
    )
    parser.add_argument(
        "--receipt",
        help="Optional host/command receipt path. Recorded and hashed; not treated as proof of hidden-context absence.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    return parser.parse_args()


def _receipt_record(
    path_value: str | None, *, run_dir: Path, stage: str
) -> dict[str, str | int] | None:
    if not path_value:
        return None
    source = Path(path_value)
    if not source.is_file():
        raise SraRuntimeError(f"receipt does not exist: {source}")
    raw = source.read_bytes()
    import hashlib

    stored_relative = Path("receipts") / f"{stage}.receipt"
    stored = run_dir / stored_relative
    stored.parent.mkdir(parents=True, exist_ok=True)
    if stored.exists():
        raise SraRuntimeError(f"refusing to overwrite carrier receipt: {stored}")
    stored.write_bytes(raw)
    return {
        "source_path": str(source),
        "stored_path": str(stored_relative),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "boundary": (
            "A receipt records an observable carrier artifact only; it does not prove the host supplied no hidden context."
        ),
    }


def _require_integrity(run_dir: Path) -> None:
    report = run_check(run_dir)
    blocking = [
        item["message"]
        for item in report.get("findings", [])
        if item.get("severity") == "block"
    ]
    if blocking:
        raise SraRuntimeError("run integrity failed: " + "; ".join(blocking))


def _record_blind(
    run_dir: Path,
    judgment: dict,
    *,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, object]:
    _require_integrity(run_dir)
    state = load_run(run_dir)
    if state.get("stage") != "prepared":
        raise SraRuntimeError(
            f"blind judgment requires stage=prepared; current stage={state.get('stage')!r}"
        )
    blind_packet = load_json(run_dir / "blind-packet.json")
    raw_input = load_json(run_dir / "raw-input.json")
    findings = validate_blind_judgment(judgment, blind_packet)
    findings.extend(
        hidden_candidate_identity_findings(judgment, raw_input.get("candidates", []))
    )
    if findings:
        raise SraValidationError(findings)

    judgment_path = run_dir / "judgments" / "blind.json"
    if judgment_path.exists():
        raise SraRuntimeError(f"refusing to overwrite recorded blind judgment: {judgment_path}")
    receipt = _receipt_record(receipt_path, run_dir=run_dir, stage="blind")
    write_json(judgment_path, judgment)
    judgment_hash = digest_data(judgment)

    sealed_packet = load_json(run_dir / "sealed-packet.json")
    state_packet = build_state_packet(
        raw_input=raw_input,
        sealed_packet=sealed_packet,
        blind_packet=blind_packet,
        candidate_map=state["candidate_map"],
        blind_judgment=judgment,
    )
    state_packet_path = run_dir / "state-packet.json"
    state_prompt_path = run_dir / "state-aware-agent-prompt.md"
    state_output_schema_path = run_dir / "state-aware-output-schema.json"
    state_dispatch_path = run_dir / "state-aware-subagent-dispatch.json"
    state_command_path = run_dir / "state-aware-codex-command.sh"
    state_output_path = run_dir / "judgments" / "state-aware.candidate.json"
    workspace_path = run_dir / "fresh-context-workspace-state"

    write_json(state_packet_path, state_packet)
    state_prompt_path.write_text(prompt_for_state(state_packet), encoding="utf-8")
    write_json(state_output_schema_path, state_output_schema(state_packet))
    write_json(
        state_dispatch_path,
        carrier_dispatch(
            state_prompt_path.resolve(),
            stage="state_aware",
            output_path=state_output_path.resolve(),
            output_schema_path=state_output_schema_path.resolve(),
        ),
    )
    state_command_path.write_text(
        carrier_command(
            prompt_path=state_prompt_path.resolve(),
            output_path=state_output_path.resolve(),
            output_schema_path=state_output_schema_path.resolve(),
            workspace_path=workspace_path.resolve(),
        ),
        encoding="utf-8",
    )
    state_command_path.chmod(0o755)
    workspace_path.mkdir(parents=True, exist_ok=True)

    state["stage"] = "blind_recorded"
    state["blind_judgment_hash"] = judgment_hash
    state["state_packet_hash"] = state_packet["packet_hash"]
    state.setdefault("carriers", {})["blind"] = carrier
    if receipt:
        state.setdefault("carrier_receipts", {})["blind"] = receipt
    state["paths"].update(
        {
            "blind_judgment": str(judgment_path),
            "state_packet": str(state_packet_path),
            "state_prompt": str(state_prompt_path),
            "state_output_schema": str(state_output_schema_path),
            "state_dispatch": str(state_dispatch_path),
            "state_cli_command": str(state_command_path),
        }
    )
    save_run_state(run_dir / "run.json", state)
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "blind_judgment_recorded",
            {
                "judgment_hash": judgment_hash,
                "state_packet_hash": state_packet["packet_hash"],
                "carrier": carrier,
                "receipt": receipt,
            },
        ),
    )
    return {
        "run_id": state["run_id"],
        "stage": "blind_recorded",
        "blind_judgment_hash": judgment_hash,
        "state_packet_hash": state_packet["packet_hash"],
        "carrier": carrier,
        "next_action": (
            "Run state-aware-agent-prompt.md through the selected packet-bound or fresh-context carrier, "
            "then record it with --stage state-aware."
        ),
    }


def _record_state(
    run_dir: Path,
    judgment: dict,
    *,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, object]:
    _require_integrity(run_dir)
    state = load_run(run_dir)
    if state.get("stage") != "blind_recorded":
        raise SraRuntimeError(
            f"state-aware judgment requires stage=blind_recorded; current stage={state.get('stage')!r}"
        )
    state_packet = load_json(run_dir / "state-packet.json")
    findings = validate_state_judgment(judgment, state_packet)
    if findings:
        raise SraValidationError(findings)

    judgment_path = run_dir / "judgments" / "state-aware.json"
    if judgment_path.exists():
        raise SraRuntimeError(
            f"refusing to overwrite recorded state-aware judgment: {judgment_path}"
        )
    receipt = _receipt_record(
        receipt_path, run_dir=run_dir, stage="state_aware"
    )
    write_json(judgment_path, judgment)
    judgment_hash = digest_data(judgment)

    state.setdefault("carriers", {})["state_aware"] = carrier
    if receipt:
        state.setdefault("carrier_receipts", {})["state_aware"] = receipt
    effective_isolation = effective_isolation_claim(
        state["carriers"], state.get("carrier_receipts")
    )
    final_decision = {
        "schema_version": FINAL_DECISION_SCHEMA,
        "run_id": state["run_id"],
        "mode": state["mode"],
        "requested_isolation_profile": state["isolation_profile"],
        "isolation_override_reason": state.get("isolation_override_reason"),
        "effective_isolation_claim": effective_isolation,
        "isolation_boundary": (
            "The effective claim is limited to recorded carriers and packet binding. It does not prove the absence of hidden host context."
        ),
        "sealed_packet_hash": state["sealed_packet_hash"],
        "blind_packet_hash": state["blind_packet_hash"],
        "blind_judgment_hash": state["blind_judgment_hash"],
        "state_packet_hash": state["state_packet_hash"],
        "state_judgment_hash": judgment_hash,
        "carriers": state["carriers"],
        "carrier_receipts": state.get("carrier_receipts", {}),
        "decision": judgment,
    }
    final_path = run_dir / "final-decision.json"
    write_json(final_path, final_decision)

    state["stage"] = "finalized"
    state["state_judgment_hash"] = judgment_hash
    state["effective_isolation_claim"] = effective_isolation
    state["paths"].update(
        {
            "state_judgment": str(judgment_path),
            "final_decision": str(final_path),
        }
    )
    save_run_state(run_dir / "run.json", state)
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "state_judgment_recorded",
            {
                "judgment_hash": judgment_hash,
                "carrier": carrier,
                "receipt": receipt,
                "effective_isolation_claim": effective_isolation,
                "decision": judgment["decision"],
            },
        ),
    )
    return {
        "run_id": state["run_id"],
        "stage": "finalized",
        "decision": judgment["decision"],
        "state_judgment_hash": judgment_hash,
        "effective_isolation_claim": effective_isolation,
        "carrier": carrier,
        "final_decision": str(final_path),
        "next_action": "Run check_sra_run.py and render_sra_decision.py.",
    }


def main() -> int:
    args = parse_args()
    run_dir = Path(args.dir)
    try:
        judgment = load_json(Path(args.input))
        if not isinstance(judgment, dict):
            raise SraRuntimeError("Agentic judgment input must be a JSON object")
        if args.stage == "blind":
            result = _record_blind(
                run_dir,
                judgment,
                carrier=args.carrier,
                receipt_path=args.receipt,
            )
        else:
            result = _record_state(
                run_dir,
                judgment,
                carrier=args.carrier,
                receipt_path=args.receipt,
            )
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
        print("SRA Agentic judgment recorded")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
