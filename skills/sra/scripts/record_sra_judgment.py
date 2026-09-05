#!/usr/bin/env python3
"""Record independent SRA v0.3 judgments and advance the typed workflow."""

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
    compare_views,
    coverage_blocked_decision,
    create_final_decision,
    digest_data,
    finalization_status_for_outcome,
    load_json,
    load_run,
    make_runtime_event,
    receipt_record,
    run_check,
    save_run_state,
    validate_challenge_judgment,
    validate_coverage_judgment,
    validate_reconciliation_judgment,
    validate_situated_judgment,
    write_json,
    write_stage_surface,
)

STAGES = ("coverage", "challenge", "situated", "reconciliation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record an SRA v0.3 coverage, challenge, situated, or reconciliation "
            "judgment. Scripts validate deterministic consequences and never choose priority."
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


def _terminal_event_type(status: str) -> str:
    return {
        "finalized": "run_finalized",
        "conditional": "run_conditional",
        "blocked": "run_blocked",
    }[status]


def _finalize(
    run_dir: Path,
    state: dict[str, Any],
    *,
    source: str,
    decision: dict[str, Any],
) -> str:
    status = finalization_status_for_outcome(str(decision.get("allocation_outcome")))
    state["statuses"]["finalization"] = status
    final = create_final_decision(
        run_state=state,
        final_source=source,
        decision=decision,
    )
    write_json(run_dir / "final-decision.json", final)
    state["paths"]["final_decision"] = str(run_dir / "final-decision.json")
    return status


def _write_reconciliation_surface(
    run_dir: Path,
    state: dict[str, Any],
    packet: dict[str, Any],
) -> None:
    packet_path = run_dir / "reconciliation-packet.json"
    write_json(packet_path, packet)
    state["paths"]["reconciliation_packet"] = str(packet_path)
    state["paths"].update(
        write_stage_surface(
            run_dir=run_dir,
            stage="reconciliation",
            packet=packet,
        )
    )


def _append_terminal_event(
    run_dir: Path,
    state: dict[str, Any],
    *,
    status: str,
    payload: dict[str, Any],
) -> None:
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            _terminal_event_type(status),
            payload,
        ),
    )


def _advance_after_view(run_dir: Path, state: dict[str, Any]) -> str:
    if not _coverage_ready(state):
        return "Coverage review must become ready before allocation views can finalize."
    statuses = state["statuses"]
    if state["view_plan"] == "situated_only":
        if statuses["situated"] == "recorded" and statuses["finalization"] == "pending":
            situated = load_json(run_dir / "judgments" / "situated.json")
            status = _finalize(
                run_dir,
                state,
                source="situated",
                decision=situated,
            )
            _append_terminal_event(
                run_dir,
                state,
                status=status,
                payload={
                    "source": "situated",
                    "situated_judgment_hash": state["situated_judgment_hash"],
                },
            )
            return f"Run reached {status} from the situated judgment."
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
        detailed="execution_policy" in load_json(run_dir / "base-packet.json"),
    )
    comparison_path = run_dir / "comparison-report.json"
    write_json(comparison_path, comparison)
    state["comparison_hash"] = comparison["comparison_hash"]
    statuses["comparison"] = comparison["status"]
    state["paths"]["comparison_report"] = str(comparison_path)
    conflict_fields = [
        item["field"] for item in comparison["conflict_fields"]
    ]
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "views_compared",
            {
                "status": comparison["status"],
                "comparison_hash": comparison["comparison_hash"],
                "conflict_fields": conflict_fields,
            },
        ),
    )
    if comparison["status"] == "agree":
        statuses["reconciliation"] = "not_required"
        status = _finalize(
            run_dir,
            state,
            source="situated",
            decision=situated,
        )
        _append_terminal_event(
            run_dir,
            state,
            status=status,
            payload={"source": "situated", "challenge_status": "corroborated"},
        )
        return (
            f"Views agree; run reached {status} from the situated judgment with "
            "challenge corroboration."
        )

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
                "conflict_fields": conflict_fields,
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
        status = _finalize(
            run_dir,
            state,
            source="coverage",
            decision=coverage_blocked_decision(judgment, packet),
        )
        _append_terminal_event(
            run_dir,
            state,
            status=status,
            payload={"source": "coverage", "judgment_hash": judgment_hash},
        )
        next_action = "Prepare a new SRA run with the missing decision surface."
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


def _record_view(
    run_dir: Path,
    judgment: dict[str, Any],
    *,
    stage: str,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, Any]:
    _require_integrity(run_dir)
    state = load_run(run_dir)
    if not _coverage_ready(state):
        raise SraRuntimeError("coverage review must be ready before allocation judgment")
    if stage == "challenge":
        if state["view_plan"] != "dual_view" or state["statuses"]["challenge"] != "pending":
            raise SraRuntimeError("challenge judgment is not required or not pending")
        packet = load_json(run_dir / "challenge-packet.json")
        findings = validate_challenge_judgment(judgment, packet)
    else:
        if state["statuses"]["situated"] != "pending":
            raise SraRuntimeError("situated judgment is not pending")
        packet = load_json(run_dir / "situated-packet.json")
        findings = validate_situated_judgment(judgment, packet)
    if findings:
        raise SraValidationError(findings)

    receipt = receipt_record(receipt_path, run_dir=run_dir, stage=stage)
    judgment_hash = _write_judgment(run_dir, stage, judgment)
    state[f"{stage}_judgment_hash"] = judgment_hash
    state["statuses"][stage] = "recorded"
    _record_carrier(state, stage=stage, carrier=carrier, receipt=receipt)
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            f"{stage}_judgment_recorded",
            {"judgment_hash": judgment_hash, "carrier": carrier},
        ),
    )
    next_action = _advance_after_view(run_dir, state)
    save_run_state(run_dir / "run.json", state)
    return {
        "run_id": state["run_id"],
        "stage": stage,
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
    return _record_view(
        run_dir,
        judgment,
        stage="challenge",
        carrier=carrier,
        receipt_path=receipt_path,
    )


def record_situated(
    run_dir: Path,
    judgment: dict[str, Any],
    *,
    carrier: str,
    receipt_path: str | None,
) -> dict[str, Any]:
    return _record_view(
        run_dir,
        judgment,
        stage="situated",
        carrier=carrier,
        receipt_path=receipt_path,
    )


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
    _record_carrier(
        state,
        stage="reconciliation",
        carrier=carrier,
        receipt=receipt,
    )
    status = _finalize(
        run_dir,
        state,
        source="reconciliation",
        decision=judgment,
    )
    append_jsonl(
        run_dir / "trace.jsonl",
        make_runtime_event(
            state["run_id"],
            "reconciliation_judgment_recorded",
            {"judgment_hash": judgment_hash, "carrier": carrier},
        ),
    )
    _append_terminal_event(
        run_dir,
        state,
        status=status,
        payload={"source": "reconciliation", "judgment_hash": judgment_hash},
    )
    save_run_state(run_dir / "run.json", state)
    return {
        "run_id": state["run_id"],
        "stage": "reconciliation",
        "judgment_hash": judgment_hash,
        "allocation_outcome": judgment["allocation_outcome"],
        "finalization": status,
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
        print("SRA v0.3 judgment recorded")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
