#!/usr/bin/env python3
"""Record independent SRA judgments and advance the context-calibrated workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sra_runtime import (
    CARRIERS,
    SraRuntimeError,
    SraValidationError,
    append_jsonl,
    build_reconciliation_packet,
    carrier_command,
    carrier_dispatch,
    challenge_output_schema,
    compare_views,
    coverage_blocked_decision,
    create_final_decision,
    digest_data,
    hidden_original_identity_findings,
    load_json,
    load_run,
    make_runtime_event,
    prompt_for_reconciliation,
    receipt_record,
    reconciliation_output_schema,
    run_check,
    save_run_state,
    validate_challenge_judgment,
    validate_coverage_judgment,
    validate_reconciliation_judgment,
    validate_situated_judgment,
    write_json,
)

STAGES = ("coverage", "challenge", "situated", "reconciliation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record an SRA coverage, challenge, situated, or reconciliation judgment. "
            "Scripts validate workflow and references; they never decide priority."
        )
    )
    parser.add_argument("--dir", required=True, help="Prepared SRA run directory.")
    parser.add_argument("--stage", required=True, choices=STAGES)
    parser.add_argument("--input", required=True, help="Agentic judgment JSON path.")
    parser.add_argument("--carrier", default="packet_bound", choices=sorted(CARRIERS))
    parser.add_argument("--receipt", help="Optional observable carrier receipt.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _require_integrity(run_dir: Path) -> None:
    report = run_check(run_dir)
    blocking = [
        item["message"]
        for item in report.get("findings", [])
        if item.get("severity") == "block"
    ]
    if blocking:
        raise SraRuntimeError("run integrity failed: " + "; ".join(blocking))


def _coverage_ready(state: dict[str, Any]) -> bool:
    return state["statuses"]["coverage"] in {
        "not_required",
        "recorded_ready",
        "recorded_warning",
    }


def _record_carrier(
    state: dict[str, Any],
    *,
    stage: str,
    carrier: str,
    receipt: dict[str, Any] | None,
) -> None:
    state.setdefault("carriers", {})[stage] = carrier
    if receipt is not None:
        state.setdefault("carrier_receipts", {})[stage] = receipt


def _write_judgment(run_dir: Path, stage: str, judgment: dict[str, Any]) -> str:
    path = run_dir / "judgments" / f"{stage}.json"
    if path.exists():
        raise SraRuntimeError(f"refusing to overwrite recorded judgment: {path}")
    write_json(path, judgment)
    return digest_data(judgment)


def _finalize(
    run_dir: Path,
    state: dict[str, Any],
    *,
    source: str,
    decision: dict[str, Any],
    blocked: bool = False,
) -> None:
    state["statuses"]["finalization"] = "blocked" if blocked else "finalized"
    final = create_final_decision(run_state=state, final_source=source, decision=decision)
    write_json(run_dir / "final-decision.json", final)
    state["paths"]["final_decision"] = str(run_dir / "final-decision.json")


def _write_reconciliation_surface(
    run_dir: Path,
    state: dict[str, Any],
    packet: dict[str, Any],
) -> None:
    packet_path = run_dir / "reconciliation-packet.json"
    prompt_path = run_dir / "reconciliation-agent-prompt.md"
    schema_path = run_dir / "reconciliation-output-schema.json"
    dispatch_path = run_dir / "reconciliation-subagent-dispatch.json"
    command_path = run_dir / "reconciliation-codex-command.sh"
    output_path = run_dir / "judgments" / "reconciliation.candidate.json"
    workspace_path = run_dir / "fresh-context-workspace-reconciliation"

    write_json(packet_path, packet)
    prompt_path.write_text(prompt_for_reconciliation(packet), encoding="utf-8")
    write_json(schema_path, reconciliation_output_schema(packet))
    write_json(
        dispatch_path,
        carrier_dispatch(
            prompt_path.resolve(),
            stage="reconciliation",
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
    state["paths"].update(
        {
            "reconciliation_packet": str(packet_path),
            "reconciliation_prompt": str(prompt_path),
            "reconciliation_output_schema": str(schema_path),
            "reconciliation_dispatch": str(dispatch_path),
            "reconciliation_cli_command": str(command_path),
        }
    )


def _advance_after_view(run_dir: Path, state: dict[str, Any]) -> str:
    if not _coverage_ready(state):
        return "Coverage review must become ready before allocation views can finalize."
    statuses = state["statuses"]
    if state["view_plan"] == "situated_only":
        if statuses["situated"] == "recorded" and statuses["finalization"] == "pending":
            situated = load_json(run_dir / "judgments" / "situated.json")
            _finalize(run_dir, state, source="situated", decision=situated)
            append_jsonl(
                run_dir / "trace.jsonl",
                make_runtime_event(
                    state["run_id"],
                    "run_finalized",
                    {"source": "situated", "situated_judgment_hash": state["situated_judgment_hash"]},
                ),
            )
            return "Run finalized from the independent situated judgment."
        return "Record the situated judgment."

    if statuses["challenge"] != "recorded" or statuses["situated"] != "recorded":
        return "Record both challenge and situated judgments independently."
    if statuses["comparison"] in {"agree", "conflict"}:
        return "View comparison already exists."

    challenge = load_json(run_dir / "judgments" / "challenge.json")
    situated = load_json(run_dir / "judgments" / "situated.json")
    comparison = compare_views(
        run_id=state["run_id"],
        challenge_packet_hash=state["challenge_packet_hash"],
        situated_packet_hash=state["situated_packet_hash"],
        challenge_judgment=challenge,
        situated_judgment=situated,
        challenge_map=state["challenge_map"],
    )
    write_json(run_dir / "comparison-report.json", comparison)
    state["comparison_hash"] = comparison["comparison_hash"]
    statuses["comparison"] = comparison["status"]
    state["paths"]["comparison_report"] = str(run_dir / "comparison-report.json")
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "views_compared",
            {
                "status": comparison["status"],
                "comparison_hash": comparison["comparison_hash"],
                "conflict_fields": [item["field"] for item in comparison["conflict_fields"]],
            },
        ),
    )
    if comparison["status"] == "agree":
        statuses["reconciliation"] = "not_required"
        _finalize(run_dir, state, source="situated", decision=situated)
        append_jsonl(
            run_dir / "trace.jsonl",
            make_runtime_event(
                state["run_id"],
                "run_finalized",
                {"source": "situated", "challenge_status": "corroborated"},
            ),
        )
        return "Views agree; run finalized from the situated judgment with challenge corroboration."

    base_packet = load_json(run_dir / "base-packet.json")
    situated_packet = load_json(run_dir / "situated-packet.json")
    reconciliation = build_reconciliation_packet(
        base_packet=base_packet,
        situated_packet=situated_packet,
        challenge_judgment=challenge,
        situated_judgment=situated,
        comparison=comparison,
    )
    state["reconciliation_packet_hash"] = reconciliation["packet_hash"]
    statuses["reconciliation"] = "pending"
    _write_reconciliation_surface(run_dir, state, reconciliation)
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "reconciliation_requested",
            {
                "packet_hash": reconciliation["packet_hash"],
                "conflict_fields": [item["field"] for item in comparison["conflict_fields"]],
            },
        ),
    )
    return "Views conflict; run the one-pass targeted reconciliation."


def record_coverage(
    run_dir: Path,
    judgment: dict[str, Any],
    *,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, Any]:
    _require_integrity(run_dir)
    state = load_run(run_dir)
    if state["statuses"]["coverage"] != "pending":
        raise SraRuntimeError("coverage judgment is not pending")
    packet = load_json(run_dir / "coverage-packet.json")
    findings = validate_coverage_judgment(judgment, packet)
    if findings:
        raise SraValidationError(findings)
    receipt = receipt_record(receipt_path, run_dir=run_dir, stage="coverage")
    judgment_hash = _write_judgment(run_dir, "coverage", judgment)
    state["coverage_judgment_hash"] = judgment_hash
    _record_carrier(state, stage="coverage", carrier=carrier, receipt=receipt)
    outcome = judgment["outcome"]
    state["statuses"]["coverage"] = {
        "packet_ready": "recorded_ready",
        "packet_ready_with_warning": "recorded_warning",
        "packet_incomplete": "recorded_incomplete",
    }[outcome]
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "coverage_judgment_recorded",
            {"outcome": outcome, "judgment_hash": judgment_hash, "carrier": carrier},
        ),
    )
    if outcome == "packet_incomplete":
        _finalize(
            run_dir,
            state,
            source="coverage",
            decision=coverage_blocked_decision(judgment),
            blocked=True,
        )
        append_jsonl(
            run_dir / "trace.jsonl",
            make_runtime_event(
                state["run_id"],
                "run_blocked",
                {"source": "coverage", "judgment_hash": judgment_hash},
            ),
        )
        next_action = "Prepare a new SRA run with the missing candidate or evidence surface."
    else:
        next_action = (
            "Record both challenge and situated judgments independently."
            if state["view_plan"] == "dual_view"
            else "Record the situated judgment."
        )
    save_run_state(run_dir / "run.json", state)
    return {
        "run_id": state["run_id"],
        "stage": "coverage",
        "outcome": outcome,
        "judgment_hash": judgment_hash,
        "next_action": next_action,
    }


def record_challenge(
    run_dir: Path,
    judgment: dict[str, Any],
    *,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, Any]:
    _require_integrity(run_dir)
    state = load_run(run_dir)
    if not _coverage_ready(state):
        raise SraRuntimeError("coverage review must be ready before challenge judgment")
    if state["view_plan"] != "dual_view" or state["statuses"]["challenge"] != "pending":
        raise SraRuntimeError("challenge judgment is not required or not pending")
    packet = load_json(run_dir / "challenge-packet.json")
    raw = load_json(run_dir / "raw-input.json")
    findings = validate_challenge_judgment(judgment, packet)
    findings.extend(hidden_original_identity_findings(judgment, raw.get("candidates", [])))
    if findings:
        raise SraValidationError(findings)
    receipt = receipt_record(receipt_path, run_dir=run_dir, stage="challenge")
    judgment_hash = _write_judgment(run_dir, "challenge", judgment)
    state["challenge_judgment_hash"] = judgment_hash
    state["statuses"]["challenge"] = "recorded"
    _record_carrier(state, stage="challenge", carrier=carrier, receipt=receipt)
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "challenge_judgment_recorded",
            {"judgment_hash": judgment_hash, "carrier": carrier},
        ),
    )
    next_action = _advance_after_view(run_dir, state)
    save_run_state(run_dir / "run.json", state)
    return {
        "run_id": state["run_id"],
        "stage": "challenge",
        "judgment_hash": judgment_hash,
        "next_action": next_action,
    }


def record_situated(
    run_dir: Path,
    judgment: dict[str, Any],
    *,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, Any]:
    _require_integrity(run_dir)
    state = load_run(run_dir)
    if not _coverage_ready(state):
        raise SraRuntimeError("coverage review must be ready before situated judgment")
    if state["statuses"]["situated"] != "pending":
        raise SraRuntimeError("situated judgment is not pending")
    packet = load_json(run_dir / "situated-packet.json")
    findings = validate_situated_judgment(judgment, packet)
    if findings:
        raise SraValidationError(findings)
    receipt = receipt_record(receipt_path, run_dir=run_dir, stage="situated")
    judgment_hash = _write_judgment(run_dir, "situated", judgment)
    state["situated_judgment_hash"] = judgment_hash
    state["statuses"]["situated"] = "recorded"
    _record_carrier(state, stage="situated", carrier=carrier, receipt=receipt)
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "situated_judgment_recorded",
            {"judgment_hash": judgment_hash, "carrier": carrier},
        ),
    )
    next_action = _advance_after_view(run_dir, state)
    save_run_state(run_dir / "run.json", state)
    return {
        "run_id": state["run_id"],
        "stage": "situated",
        "judgment_hash": judgment_hash,
        "next_action": next_action,
    }


def record_reconciliation(
    run_dir: Path,
    judgment: dict[str, Any],
    *,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, Any]:
    _require_integrity(run_dir)
    state = load_run(run_dir)
    if state["statuses"]["reconciliation"] != "pending":
        raise SraRuntimeError("reconciliation is not pending")
    packet = load_json(run_dir / "reconciliation-packet.json")
    findings = validate_reconciliation_judgment(judgment, packet)
    if findings:
        raise SraValidationError(findings)
    receipt = receipt_record(receipt_path, run_dir=run_dir, stage="reconciliation")
    judgment_hash = _write_judgment(run_dir, "reconciliation", judgment)
    state["reconciliation_judgment_hash"] = judgment_hash
    state["statuses"]["reconciliation"] = "recorded"
    _record_carrier(state, stage="reconciliation", carrier=carrier, receipt=receipt)
    _finalize(run_dir, state, source="reconciliation", decision=judgment)
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "reconciliation_judgment_recorded",
            {"judgment_hash": judgment_hash, "carrier": carrier},
        ),
    )
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "run_finalized",
            {"source": "reconciliation", "judgment_hash": judgment_hash},
        ),
    )
    save_run_state(run_dir / "run.json", state)
    return {
        "run_id": state["run_id"],
        "stage": "reconciliation",
        "judgment_hash": judgment_hash,
        "allocation_outcome": judgment["allocation_outcome"],
        "next_action": "Run check_sra_run.py and render_sra_decision.py.",
    }


def main() -> int:
    args = parse_args()
    run_dir = Path(args.dir)
    try:
        judgment = load_json(Path(args.input))
        if not isinstance(judgment, dict):
            raise SraRuntimeError("Agentic judgment input must be a JSON object")
        handlers = {
            "coverage": record_coverage,
            "challenge": record_challenge,
            "situated": record_situated,
            "reconciliation": record_reconciliation,
        }
        result = handlers[args.stage](
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
        print("SRA judgment recorded")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
