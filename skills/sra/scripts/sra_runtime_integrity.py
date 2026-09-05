#!/usr/bin/env python3
"""Deterministic state reconstruction, integrity checking, and repair for SRA v0.3."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sra_domain import *  # noqa: F403
from sra_runtime_core import *  # noqa: F403
from sra_packets import *  # noqa: F403
from sra_carriers import *  # noqa: F403
from sra_carriers import _receipt_hash

RUN_STATE_KEYS = frozenset({
    "schema_version", "run_id", "created_at", "updated_at", "mode", "view_plan",
    "coverage_plan", "statuses", "raw_input_hash", "context_admission_hash",
    "base_packet_hash", "coverage_packet_hash", "challenge_packet_hash",
    "situated_packet_hash", "coverage_judgment_hash", "challenge_judgment_hash",
    "situated_judgment_hash", "comparison_hash", "reconciliation_packet_hash",
    "reconciliation_judgment_hash", "challenge_map", "context_weights",
    "governance_overrides", "warnings", "carriers", "carrier_receipts", "paths",
    "claim_ceiling",
})
RECEIPT_KEYS = frozenset({
    "source_path", "stored_path", "sha256", "bytes", "boundary",
})
PREPARED_INPUT_ANCHOR_FIELDS = (
    "raw_input_hash",
    "context_admission_hash",
    "base_packet_hash",
    "coverage_packet_hash",
    "challenge_packet_hash",
    "situated_packet_hash",
)


def _parse_utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def _is_parseable_utc_timestamp(value: Any) -> bool:
    return _parse_utc_timestamp(value) is not None


def _path_uses_symlink(path: Path, run_dir: Path) -> bool:
    if run_dir.is_symlink():
        return True
    try:
        relative = path.relative_to(run_dir)
    except ValueError:
        return True
    current = run_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _blocked_preflight_report(
    run_dir: Path,
    state: dict[str, Any],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    carriers = state.get("carriers", {})
    receipts = state.get("carrier_receipts", {})
    if not isinstance(carriers, dict):
        carriers = {}
    if not isinstance(receipts, dict):
        receipts = {}
    return {
        "schema_version": CHECK_REPORT_SCHEMA,  # noqa: F405
        "run_dir": str(run_dir),
        "run_id": state.get("run_id"),
        "mode": state.get("mode"),
        "view_plan": state.get("view_plan"),
        "coverage_plan": state.get("coverage_plan"),
        "statuses": state.get("statuses", {}),
        "governance_overrides": state.get("governance_overrides", {}),
        "recorded_carriers": carriers,
        "observed_context_boundary": observed_context_boundary(carriers, receipts),  # noqa: F405
        "status": "blocked",
        "findings": findings,
        "truth_boundary": (
            "Integrity does not prove complete coverage, absent hidden context, "
            "semantic necessity, correct priority, or optimal ROI."
        ),
    }


def _optional_json(path: Path) -> dict[str, Any] | None:
    if path.is_symlink() or path.parent.is_symlink():
        raise SraRuntimeError(f"authoritative JSON path must not use a symbolic link: {path}")  # noqa: F405
    if not path.is_file():
        return None
    value = load_json(path)  # noqa: F405
    if not isinstance(value, dict):
        raise SraRuntimeError(f"JSON object required at {path}")  # noqa: F405
    return value


def _validate_recorded_judgment(
    stage: str,
    judgment: dict[str, Any] | None,
    rebuilt: dict[str, Any],
    reconciliation_packet: dict[str, Any] | None = None,
) -> list[str]:
    if judgment is None:
        return []
    if stage == "coverage":
        return validate_coverage_judgment(  # noqa: F405
            judgment, rebuilt["coverage_packet"]
        )
    if stage == "challenge":
        return validate_challenge_judgment(  # noqa: F405
            judgment, rebuilt["challenge_packet"]
        )
    if stage == "situated":
        return validate_situated_judgment(  # noqa: F405
            judgment, rebuilt["situated_packet"]
        )
    if reconciliation_packet is None:
        return ["reconciliation judgment has no reconstructed conflict packet"]
    return validate_reconciliation_judgment(  # noqa: F405
        judgment, reconciliation_packet
    )


def reconstruct_runtime_expectation(
    run_dir: Path,
    rebuilt: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct legal runtime state from deterministic plan and Agentic judgments."""
    statuses = initial_statuses(  # noqa: F405
        rebuilt["view_plan"], rebuilt["coverage_plan"]
    )
    issues: list[str] = []
    judgments = {
        stage: _optional_json(run_dir / "judgments" / f"{stage}.json")
        for stage in ("coverage", "challenge", "situated", "reconciliation")
    }
    hashes = {
        f"{stage}_judgment_hash": digest_data(value) if value is not None else None  # noqa: F405
        for stage, value in judgments.items()
    }
    valid = {stage: False for stage in judgments}
    comparison: dict[str, Any] | None = None
    reconciliation_packet: dict[str, Any] | None = None
    final_source: str | None = None
    final_decision: dict[str, Any] | None = None

    coverage_ready = rebuilt["coverage_plan"] == "skip"
    coverage = judgments["coverage"]
    if coverage is not None:
        messages = _validate_recorded_judgment("coverage", coverage, rebuilt)
        issues.extend(f"coverage judgment: {message}" for message in messages)
        valid["coverage"] = not messages
        if rebuilt["coverage_plan"] != "required":
            issues.append("coverage judgment exists although coverage is not required")
        if not messages:
            outcome = coverage.get("outcome")
            status_by_outcome = {
                "packet_ready": "recorded_ready",
                "packet_ready_with_warning": "recorded_warning",
                "packet_incomplete": "recorded_incomplete",
            }
            if outcome in status_by_outcome:
                statuses["coverage"] = status_by_outcome[str(outcome)]
                coverage_ready = outcome in {
                    "packet_ready", "packet_ready_with_warning"
                }
                if outcome == "packet_incomplete":
                    statuses["finalization"] = "blocked"
                    final_source = "coverage"
                    final_decision = coverage_blocked_decision(  # noqa: F405
                        coverage, rebuilt["coverage_packet"]
                    )
            else:
                issues.append("coverage judgment has an unsupported outcome")
                coverage_ready = False

    challenge = judgments["challenge"]
    situated = judgments["situated"]
    reconciliation = judgments["reconciliation"]
    if challenge is not None:
        messages = _validate_recorded_judgment("challenge", challenge, rebuilt)
        issues.extend(f"challenge judgment: {message}" for message in messages)
        valid["challenge"] = not messages
        if rebuilt["view_plan"] != "dual_view":
            issues.append("challenge judgment exists outside dual_view")
        if not coverage_ready:
            issues.append("challenge judgment exists before coverage became ready")
        if not messages:
            statuses["challenge"] = "recorded"
    if situated is not None:
        messages = _validate_recorded_judgment("situated", situated, rebuilt)
        issues.extend(f"situated judgment: {message}" for message in messages)
        valid["situated"] = not messages
        if not coverage_ready:
            issues.append("situated judgment exists before coverage became ready")
        if not messages:
            statuses["situated"] = "recorded"

    if final_source == "coverage":
        if challenge is not None or situated is not None or reconciliation is not None:
            issues.append("allocation judgments exist after coverage blocked the run")
    elif coverage_ready and rebuilt["view_plan"] == "situated_only":
        if challenge is not None:
            issues.append("situated_only run contains a challenge judgment")
        if situated is not None and valid["situated"]:
            final_source = "situated"
            final_decision = situated
            statuses["finalization"] = finalization_status_for_outcome(  # noqa: F405
                str(situated.get("allocation_outcome"))
            )
        if reconciliation is not None:
            issues.append("situated_only run contains a reconciliation judgment")
    elif coverage_ready and rebuilt["view_plan"] == "dual_view":
        if challenge is not None and situated is not None and valid["challenge"] and valid["situated"]:
            comparison = compare_views(  # noqa: F405
                run_id=rebuilt["base_packet"]["run_id"],
                challenge_packet_hash=rebuilt["challenge_packet"]["packet_hash"],
                situated_packet_hash=rebuilt["situated_packet"]["packet_hash"],
                challenge_judgment=challenge,
                situated_judgment=situated,
                challenge_map=rebuilt["challenge_map"],
                detailed="execution_policy" in rebuilt["base_packet"],
            )
            statuses["comparison"] = comparison["status"]
            if comparison["status"] == "agree":
                statuses["reconciliation"] = "not_required"
                final_source = "situated"
                final_decision = situated
                statuses["finalization"] = finalization_status_for_outcome(  # noqa: F405
                    str(situated.get("allocation_outcome"))
                )
                if reconciliation is not None:
                    issues.append("reconciliation judgment exists although views agree")
            else:
                statuses["reconciliation"] = "pending"
                reconciliation_packet = build_reconciliation_packet(  # noqa: F405
                    base_packet=rebuilt["base_packet"],
                    situated_packet=rebuilt["situated_packet"],
                    challenge_judgment=challenge,
                    situated_judgment=situated,
                    comparison=comparison,
                )
                if reconciliation is not None:
                    messages = _validate_recorded_judgment(
                        "reconciliation", reconciliation, rebuilt, reconciliation_packet
                    )
                    issues.extend(
                        f"reconciliation judgment: {message}" for message in messages
                    )
                    valid["reconciliation"] = not messages
                    if not messages:
                        statuses["reconciliation"] = "recorded"
                        final_source = "reconciliation"
                        final_decision = reconciliation
                        statuses["finalization"] = finalization_status_for_outcome(  # noqa: F405
                            str(reconciliation.get("allocation_outcome"))
                        )
        elif reconciliation is not None:
            issues.append("reconciliation judgment exists before two valid independent views")

    if rebuilt["coverage_plan"] == "required" and coverage is None:
        if challenge is not None or situated is not None or reconciliation is not None:
            issues.append("allocation judgment exists while required coverage is pending")

    return {
        "statuses": statuses,
        "issues": issues,
        "judgments": judgments,
        "judgment_valid": valid,
        "hashes": hashes,
        "comparison": comparison,
        "reconciliation_packet": reconciliation_packet,
        "final_source": final_source,
        "final_decision": final_decision,
    }


def expected_trace_events(
    rebuilt: dict[str, Any],
    expectation: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    hashes = expectation["hashes"]
    judgments = expectation["judgments"]
    carriers = state.get("carriers", {})
    if not isinstance(carriers, dict):
        carriers = {}
    events: dict[str, dict[str, Any]] = {
        "run_prepared": {
            "mode": rebuilt["mode"],
            "view_plan": rebuilt["view_plan"],
            "coverage_plan": rebuilt["coverage_plan"],
            "raw_input_hash": rebuilt["raw_input_hash"],
            "context_admission_hash": rebuilt["context_admission_hash"],
            "base_packet_hash": rebuilt["base_packet"]["packet_hash"],
            "coverage_packet_hash": rebuilt["coverage_packet"]["packet_hash"],
            "challenge_packet_hash": rebuilt["challenge_packet"]["packet_hash"],
            "situated_packet_hash": rebuilt["situated_packet"]["packet_hash"],
            "admitted_context_ids": rebuilt["admission"]["admitted_ids"],
            "quarantined_context_ids": rebuilt["admission"]["quarantined_ids"],
            "excluded_context_ids": rebuilt["admission"]["excluded_ids"],
            "governance_overrides": rebuilt["governance_overrides"],
            "warnings": rebuilt["warnings"],
        }
    }
    coverage = judgments.get("coverage")
    if coverage is not None and expectation["judgment_valid"].get("coverage"):
        events["coverage_judgment_recorded"] = {
            "outcome": coverage.get("outcome"),
            "judgment_hash": hashes["coverage_judgment_hash"],
            "carrier": carriers.get("coverage"),
        }
    for stage in ("challenge", "situated"):
        if judgments.get(stage) is not None and expectation["judgment_valid"].get(stage):
            events[f"{stage}_judgment_recorded"] = {
                "judgment_hash": hashes[f"{stage}_judgment_hash"],
                "carrier": carriers.get(stage),
            }
    comparison = expectation.get("comparison")
    if isinstance(comparison, dict):
        conflict_fields = [
            item["field"] for item in comparison.get("conflict_fields", [])
        ]
        events["views_compared"] = {
            "status": comparison.get("status"),
            "comparison_hash": comparison.get("comparison_hash"),
            "conflict_fields": conflict_fields,
        }
        if comparison.get("status") == "conflict":
            packet = expectation.get("reconciliation_packet")
            events["reconciliation_requested"] = {
                "packet_hash": (
                    packet.get("packet_hash") if isinstance(packet, dict) else None
                ),
                "conflict_fields": conflict_fields,
            }
    if (
        judgments.get("reconciliation") is not None
        and expectation["judgment_valid"].get("reconciliation")
    ):
        events["reconciliation_judgment_recorded"] = {
            "judgment_hash": hashes["reconciliation_judgment_hash"],
            "carrier": carriers.get("reconciliation"),
        }

    final_source = expectation.get("final_source")
    if final_source is not None:
        finalization = expectation["statuses"]["finalization"]
        final_event = {
            "finalized": "run_finalized",
            "conditional": "run_conditional",
            "blocked": "run_blocked",
        }[finalization]
        if final_source == "coverage":
            payload = {
                "source": "coverage",
                "judgment_hash": hashes["coverage_judgment_hash"],
            }
        elif final_source == "reconciliation":
            payload = {
                "source": "reconciliation",
                "judgment_hash": hashes["reconciliation_judgment_hash"],
            }
        elif rebuilt["view_plan"] == "dual_view":
            payload = {
                "source": "situated",
                "challenge_status": "corroborated",
            }
        else:
            payload = {
                "source": "situated",
                "situated_judgment_hash": hashes["situated_judgment_hash"],
            }
        events[final_event] = payload
    return events


def _trace_order_findings(event_types: list[str]) -> list[str]:
    findings: list[str] = []
    positions = {event_type: index for index, event_type in enumerate(event_types)}

    def require_before(left: str, right: str) -> None:
        if left in positions and right in positions and positions[left] >= positions[right]:
            findings.append(f"trace event {left} must precede {right}")

    if event_types and event_types[0] != "run_prepared":
        findings.append("trace must start with run_prepared")
    for stage_event in (
        "coverage_judgment_recorded",
        "challenge_judgment_recorded",
        "situated_judgment_recorded",
        "views_compared",
        "reconciliation_requested",
        "reconciliation_judgment_recorded",
    ):
        require_before("run_prepared", stage_event)
    for view_event in (
        "challenge_judgment_recorded",
        "situated_judgment_recorded",
    ):
        require_before("coverage_judgment_recorded", view_event)
        require_before(view_event, "views_compared")
    require_before("views_compared", "reconciliation_requested")
    require_before("reconciliation_requested", "reconciliation_judgment_recorded")
    terminal_events = {"run_finalized", "run_conditional", "run_blocked"}
    present_terminal = [item for item in event_types if item in terminal_events]
    if len(present_terminal) > 1:
        findings.append("trace may contain only one terminal event")
    for final_event in terminal_events:
        require_before("run_prepared", final_event)
        if final_event in positions and positions[final_event] != len(event_types) - 1:
            findings.append(f"terminal trace event {final_event} must be last")
    return findings


def _packet_for_stage(
    rebuilt: dict[str, Any],
    expectation: dict[str, Any],
    stage: str,
) -> dict[str, Any]:
    if stage == "coverage":
        return rebuilt["coverage_packet"]
    if stage == "challenge":
        return rebuilt["challenge_packet"]
    if stage == "situated":
        return rebuilt["situated_packet"]
    packet = expectation.get("reconciliation_packet")
    if not isinstance(packet, dict):
        raise SraRuntimeError("reconciliation surface has no reconstructed packet")  # noqa: F405
    return packet


def _required_surface_stages(
    rebuilt: dict[str, Any], expectation: dict[str, Any]
) -> list[str]:
    stages: list[str] = []
    if rebuilt["coverage_plan"] == "required":
        stages.append("coverage")
    if rebuilt["view_plan"] == "dual_view":
        stages.append("challenge")
    stages.append("situated")
    if isinstance(expectation.get("reconciliation_packet"), dict):
        stages.append("reconciliation")
    return stages


def _surface_rel_paths(stage: str) -> tuple[str, ...]:
    return (
        f"{stage}-agent-prompt.md",
        f"{stage}-output-schema.json",
        f"{stage}-subagent-dispatch.json",
        f"{stage}-codex-command.sh",
    )


def _surface_paths(
    run_dir: Path,
    stage: str,
    packet: dict[str, Any],
) -> dict[str, str]:
    surface = stage_surface(run_dir=run_dir, stage=stage, packet=packet)  # noqa: F405
    return {
        f"{stage}_prompt": str(surface["prompt_path"]),
        f"{stage}_output_schema": str(surface["schema_path"]),
        f"{stage}_dispatch": str(surface["dispatch_path"]),
        f"{stage}_cli_command": str(surface["command_path"]),
    }


def expected_paths(
    run_dir: Path,
    rebuilt: dict[str, Any],
    expectation: dict[str, Any],
) -> dict[str, str]:
    paths = {
        "raw_input": str(run_dir / "raw-input.json"),
        "context_admission": str(run_dir / "context-admission.json"),
        "base_packet": str(run_dir / "base-packet.json"),
        "coverage_packet": str(run_dir / "coverage-packet.json"),
        "challenge_packet": str(run_dir / "challenge-packet.json"),
        "situated_packet": str(run_dir / "situated-packet.json"),
        "trace": str(run_dir / "trace.jsonl"),
    }
    for stage in _required_surface_stages(rebuilt, expectation):
        paths.update(
            _surface_paths(
                run_dir,
                stage,
                _packet_for_stage(rebuilt, expectation, stage),
            )
        )
    if isinstance(expectation.get("comparison"), dict):
        paths["comparison_report"] = str(run_dir / "comparison-report.json")
    if isinstance(expectation.get("reconciliation_packet"), dict):
        paths["reconciliation_packet"] = str(run_dir / "reconciliation-packet.json")
    if expectation.get("final_source") is not None:
        paths["final_decision"] = str(run_dir / "final-decision.json")
    return paths


def _check_json_file(
    run_dir: Path,
    relative_path: str,
    expected: Any,
    add: Any,
    code: str,
) -> None:
    path = run_dir / relative_path
    if _path_uses_symlink(path, run_dir):
        add("block", "surface-path", f"derived surface uses a symbolic link: {relative_path}")
        return
    if not path.is_file():
        add("block", "missing-file", f"missing required run file: {relative_path}")
        return
    try:
        actual = load_json(path)  # noqa: F405
    except Exception as exc:
        add("block", code, f"failed to read {relative_path}: {exc}")
        return
    if actual != expected:
        add("block", code, f"{relative_path} does not match deterministic rebuild")


def _check_text_file(
    run_dir: Path,
    relative_path: str,
    expected: str,
    add: Any,
    code: str,
) -> None:
    path = run_dir / relative_path
    if _path_uses_symlink(path, run_dir):
        add("block", "surface-path", f"derived surface uses a symbolic link: {relative_path}")
        return
    if not path.is_file():
        add("block", "missing-file", f"missing required run file: {relative_path}")
        return
    try:
        actual = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        add("block", code, f"failed to read {relative_path}: {exc}")
        return
    if actual != expected:
        add("block", code, f"{relative_path} does not match deterministic rebuild")


def _check_stage_surface(
    run_dir: Path,
    stage: str,
    packet: dict[str, Any],
    add: Any,
) -> None:
    surface = stage_surface(run_dir=run_dir, stage=stage, packet=packet)  # noqa: F405
    _check_text_file(
        run_dir,
        f"{stage}-agent-prompt.md",
        str(surface["prompt"]),
        add,
        f"{stage}-prompt",
    )
    _check_json_file(
        run_dir,
        f"{stage}-output-schema.json",
        surface["schema"],
        add,
        f"{stage}-schema",
    )
    _check_json_file(
        run_dir,
        f"{stage}-subagent-dispatch.json",
        surface["dispatch"],
        add,
        f"{stage}-dispatch",
    )
    _check_text_file(
        run_dir,
        f"{stage}-codex-command.sh",
        str(surface["command"]),
        add,
        f"{stage}-command",
    )
    command_path = run_dir / f"{stage}-codex-command.sh"
    if command_path.is_file() and not (command_path.stat().st_mode & 0o100):
        add("block", f"{stage}-command-mode", f"{stage} command is not executable")


def _check_unexpected_surfaces(
    run_dir: Path,
    required_stages: set[str],
    add: Any,
) -> None:
    for stage in ("coverage", "challenge", "situated", "reconciliation"):
        if stage in required_stages:
            continue
        for relative_path in _surface_rel_paths(stage):
            if (run_dir / relative_path).exists():
                add(
                    "block",
                    "unexpected-surface",
                    f"unexpected derived surface: {relative_path}",
                )


def _run_check_impl(run_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    def add(severity: str, code: str, message: str) -> None:
        findings.append({"severity": severity, "code": code, "message": message})

    run_state_path = run_dir / "run.json"
    if _path_uses_symlink(run_state_path, run_dir):
        add(
            "block",
            "authoritative-path",
            "run.json must be a regular file inside the run directory",
        )
        return _blocked_preflight_report(run_dir, {}, findings)
    state = load_run(run_dir)  # noqa: F405
    missing_state_keys = sorted(RUN_STATE_KEYS - set(state))
    extra_state_keys = sorted(set(state) - RUN_STATE_KEYS)
    if missing_state_keys or extra_state_keys:
        add(
            "block",
            "run-state-shape",
            "run state fields differ from the v0.3 contract: "
            f"missing={missing_state_keys}, extra={extra_state_keys}",
        )
    if state.get("claim_ceiling") != RUN_CLAIM_CEILING:  # noqa: F405
        add(
            "block",
            "claim-ceiling-rebuild",
            "run claim_ceiling does not match the canonical Workflow claim boundary",
        )
    for field in ("created_at", "updated_at"):
        if not _is_parseable_utc_timestamp(state.get(field)):
            add("block", "run-time", f"run state {field} must be a parseable UTC timestamp")
    judgments_dir = run_dir / "judgments"
    if judgments_dir.is_symlink():
        add(
            "block",
            "authoritative-path",
            "judgments directory must not use a symbolic link",
        )
        return _blocked_preflight_report(run_dir, state, findings)
    if not judgments_dir.is_dir():
        add(
            "block",
            "output-directory",
            "judgments output directory must exist inside the run directory",
        )
    authoritative_paths = [run_dir / "raw-input.json", run_dir / "trace.jsonl"]
    authoritative_paths.extend(
        judgments_dir / f"{stage}.json"
        for stage in ("coverage", "challenge", "situated", "reconciliation")
        if (judgments_dir / f"{stage}.json").exists()
        or (judgments_dir / f"{stage}.json").is_symlink()
    )
    for authoritative_path in authoritative_paths:
        if _path_uses_symlink(authoritative_path, run_dir):
            add(
                "block",
                "authoritative-path",
                f"authoritative path must be a regular in-run path: {authoritative_path}",
            )
    if any(item["code"] == "authoritative-path" for item in findings):
        return _blocked_preflight_report(run_dir, state, findings)
    raw_path = run_dir / "raw-input.json"
    if not raw_path.is_file():
        raise SraRuntimeError("raw-input.json is required for reconstruction")  # noqa: F405
    raw = load_json(raw_path)  # noqa: F405
    if not isinstance(raw, dict):
        raise SraRuntimeError("raw-input.json must contain an object")  # noqa: F405
    rebuilt = build_packets(raw)  # noqa: F405
    expectation = reconstruct_runtime_expectation(run_dir, rebuilt)

    for issue in expectation["issues"]:
        add("block", "transition-rebuild", issue)
    for relative_path, expected in (
        ("context-admission.json", rebuilt["admission"]),
        ("base-packet.json", rebuilt["base_packet"]),
        ("coverage-packet.json", rebuilt["coverage_packet"]),
        ("challenge-packet.json", rebuilt["challenge_packet"]),
        ("situated-packet.json", rebuilt["situated_packet"]),
    ):
        _check_json_file(run_dir, relative_path, expected, add, "packet-rebuild")

    required_stages = set(_required_surface_stages(rebuilt, expectation))
    for stage in sorted(required_stages):
        _check_stage_surface(
            run_dir,
            stage,
            _packet_for_stage(rebuilt, expectation, stage),
            add,
        )
    _check_unexpected_surfaces(run_dir, required_stages, add)

    expected_path_map = expected_paths(run_dir, rebuilt, expectation)
    if state.get("paths") != expected_path_map:
        add("block", "paths-rebuild", "run paths do not match deterministic surfaces")

    scalar_expectations = {
        "run_id": raw.get("run_id"),
        "mode": rebuilt["mode"],
        "view_plan": rebuilt["view_plan"],
        "coverage_plan": rebuilt["coverage_plan"],
        "raw_input_hash": rebuilt["raw_input_hash"],
        "context_admission_hash": rebuilt["context_admission_hash"],
        "base_packet_hash": rebuilt["base_packet"]["packet_hash"],
        "coverage_packet_hash": rebuilt["coverage_packet"]["packet_hash"],
        "challenge_packet_hash": rebuilt["challenge_packet"]["packet_hash"],
        "situated_packet_hash": rebuilt["situated_packet"]["packet_hash"],
        "challenge_map": rebuilt["challenge_map"],
        "context_weights": rebuilt["context_weights"],
        "warnings": rebuilt["warnings"],
        "governance_overrides": rebuilt["governance_overrides"],
        "statuses": expectation["statuses"],
    }
    for field, expected in scalar_expectations.items():
        if state.get(field) != expected:
            add(
                "block",
                f"{field.replace('_', '-')}-rebuild",
                f"run state {field} does not match deterministic reconstruction",
            )


    for field, expected in expectation["hashes"].items():
        if state.get(field) != expected:
            add(
                "block",
                "judgment-hash-rebuild",
                f"{field} does not match the recorded judgment",
            )
    comparison = expectation.get("comparison")
    comparison_hash = (
        comparison.get("comparison_hash") if isinstance(comparison, dict) else None
    )
    if state.get("comparison_hash") != comparison_hash:
        add(
            "block",
            "comparison-hash-rebuild",
            "comparison_hash does not match reconstructed state",
        )
    reconciliation_packet = expectation.get("reconciliation_packet")
    reconciliation_packet_hash = (
        reconciliation_packet.get("packet_hash")
        if isinstance(reconciliation_packet, dict)
        else None
    )
    if state.get("reconciliation_packet_hash") != reconciliation_packet_hash:
        add(
            "block",
            "reconciliation-packet-hash-rebuild",
            "reconciliation_packet_hash does not match reconstructed state",
        )

    comparison_path = run_dir / "comparison-report.json"
    if isinstance(comparison, dict):
        _check_json_file(
            run_dir,
            "comparison-report.json",
            comparison,
            add,
            "comparison-rebuild",
        )
    elif comparison_path.exists():
        add(
            "block",
            "unexpected-comparison",
            "comparison-report.json exists before a legal comparison",
        )

    reconciliation_path = run_dir / "reconciliation-packet.json"
    if isinstance(reconciliation_packet, dict):
        _check_json_file(
            run_dir,
            "reconciliation-packet.json",
            reconciliation_packet,
            add,
            "reconciliation-packet-rebuild",
        )
    elif reconciliation_path.exists():
        add(
            "block",
            "unexpected-reconciliation",
            "reconciliation-packet.json exists without a typed conflict",
        )


    carriers = state.get("carriers", {})
    receipts = state.get("carrier_receipts", {})
    if not isinstance(carriers, dict):
        add("block", "carriers", "run carriers must be an object")
        carriers = {}
    if not isinstance(receipts, dict):
        add("block", "carrier-receipts", "run carrier_receipts must be an object")
        receipts = {}
    judgments = expectation["judgments"]
    recorded_stages = {
        stage for stage, judgment in judgments.items() if judgment is not None
    }
    for stage in sorted(recorded_stages):
        if stage not in carriers:
            add("block", "carrier-missing", f"recorded {stage} judgment has no carrier")
    for stage, carrier in carriers.items():
        if stage not in recorded_stages:
            add("block", "carrier-extra", f"carrier recorded without judgment: {stage}")
        if carrier not in CARRIERS:  # noqa: F405
            add("block", "carrier", f"unsupported carrier for {stage}: {carrier}")
        receipt = receipts.get(stage)
        if carrier in {"fresh_subagent", "ephemeral_cli"} and not isinstance(receipt, dict):
            add(
                "warn",
                "fresh-carrier-without-receipt",
                f"{stage} declares {carrier} without an observable receipt",
            )
    for stage, receipt in receipts.items():
        if stage not in carriers:
            add("block", "receipt-extra", f"receipt recorded without carrier: {stage}")
            continue
        if not isinstance(receipt, dict):
            add("block", "receipt-shape", f"{stage} receipt must be an object")
            continue
        missing_receipt_keys = sorted(RECEIPT_KEYS - set(receipt))
        extra_receipt_keys = sorted(set(receipt) - RECEIPT_KEYS)
        if missing_receipt_keys or extra_receipt_keys:
            add(
                "block",
                "receipt-shape",
                f"{stage} receipt fields differ from the canonical contract: "
                f"missing={missing_receipt_keys}, extra={extra_receipt_keys}",
            )
        if receipt.get("boundary") != RECEIPT_BOUNDARY:  # noqa: F405
            add(
                "block",
                "receipt-boundary",
                f"{stage} receipt boundary differs from the canonical claim ceiling",
            )
        if not isinstance(receipt.get("source_path"), str) or not receipt.get("source_path"):
            add("block", "receipt-shape", f"{stage} receipt source_path must be non-empty")
        stored_path = receipt.get("stored_path")
        expected_stored_path = str(Path("receipts") / f"{stage}.receipt")
        if stored_path != expected_stored_path:
            add(
                "block",
                "receipt-path",
                f"{stage} receipt stored_path must be {expected_stored_path}",
            )
            continue
        stored = run_dir / expected_stored_path
        receipts_dir = run_dir / "receipts"
        if receipts_dir.is_symlink() or stored.is_symlink():
            add(
                "block",
                "receipt-path",
                f"{stage} receipt path must not traverse a symbolic link",
            )
            continue
        if not stored.is_file():
            add("block", "receipt-missing", f"{stage} receipt is not recoverable")
        elif _receipt_hash(stored) != receipt.get("sha256"):
            add("block", "receipt-hash", f"{stage} receipt hash does not match")
        elif stored.stat().st_size != receipt.get("bytes"):
            add("block", "receipt-size", f"{stage} receipt byte count does not match")


    final_path = run_dir / "final-decision.json"
    terminal_status = expectation["statuses"].get("finalization")
    if terminal_status in {"finalized", "conditional", "blocked"}:
        expected_state = dict(state)
        expected_state.update({
            "run_id": raw.get("run_id"),
            "mode": rebuilt["mode"],
            "view_plan": rebuilt["view_plan"],
            "coverage_plan": rebuilt["coverage_plan"],
            "statuses": expectation["statuses"],
            "governance_overrides": rebuilt["governance_overrides"],
            "base_packet_hash": rebuilt["base_packet"]["packet_hash"],
            "challenge_packet_hash": rebuilt["challenge_packet"]["packet_hash"],
            "situated_packet_hash": rebuilt["situated_packet"]["packet_hash"],
            "coverage_judgment_hash": expectation["hashes"]["coverage_judgment_hash"],
            "challenge_judgment_hash": expectation["hashes"]["challenge_judgment_hash"],
            "situated_judgment_hash": expectation["hashes"]["situated_judgment_hash"],
            "comparison_hash": comparison_hash,
            "reconciliation_judgment_hash": expectation["hashes"][
                "reconciliation_judgment_hash"
            ],
        })
        expected_final = create_final_decision(  # noqa: F405
            run_state=expected_state,
            final_source=str(expectation["final_source"]),
            decision=expectation["final_decision"],
        )
        _check_json_file(
            run_dir,
            "final-decision.json",
            expected_final,
            add,
            "final-rebuild",
        )
    elif final_path.exists():
        add(
            "block",
            "unexpected-final-file",
            "pending run must not contain final-decision.json",
        )

    trace_path = run_dir / "trace.jsonl"
    if not trace_path.is_file():
        add("block", "missing-file", "missing required run file: trace.jsonl")
    else:
        trace = load_jsonl(trace_path)  # noqa: F405
        event_types = [str(event.get("event_type")) for event in trace]
        for message in _trace_order_findings(event_types):
            add("block", "trace-order", message)
        by_type: dict[str, dict[str, Any]] = {}
        previous_recorded_at: datetime | None = None
        for index, event in enumerate(trace):
            event_type = str(event.get("event_type"))
            if event.get("schema_version") != TRACE_SCHEMA:  # noqa: F405
                add("block", "trace-schema", f"trace event {index} has unsupported schema")
            if event.get("run_id") != raw.get("run_id"):
                add("block", "trace-run", f"trace event {index} has wrong run_id")
            recorded_at = _parse_utc_timestamp(event.get("recorded_at"))
            if recorded_at is None:
                add(
                    "block",
                    "trace-time",
                    f"trace event {index} must use a parseable UTC recorded_at timestamp",
                )
            elif previous_recorded_at is not None and recorded_at < previous_recorded_at:
                add(
                    "block",
                    "trace-time",
                    f"trace event {index} recorded_at precedes the prior event",
                )
            if recorded_at is not None:
                previous_recorded_at = recorded_at
            if event.get("event_id") != expected_runtime_event_id(event):  # noqa: F405
                add("block", "trace-event-id", f"trace event {index} has an invalid event_id")
            if event_type in by_type:
                add("block", "trace-repeat", f"trace event type repeated: {event_type}")
            else:
                by_type[event_type] = event
        expected_events = expected_trace_events(rebuilt, expectation, state)
        actual_types = set(by_type)
        expected_types = set(expected_events)
        for missing in sorted(expected_types - actual_types):
            add("block", "trace-missing", f"missing trace event: {missing}")
        for extra in sorted(actual_types - expected_types):
            add("block", "trace-extra", f"unexpected trace event: {extra}")
        for event_type in sorted(actual_types & expected_types):
            if by_type[event_type].get("payload") != expected_events[event_type]:
                add("block", "trace-payload", f"trace payload differs for {event_type}")

    status = (
        "blocked"
        if any(item["severity"] == "block" for item in findings)
        else "warning"
        if findings
        else "ok"
    )
    return {
        "schema_version": CHECK_REPORT_SCHEMA,  # noqa: F405
        "run_dir": str(run_dir),
        "run_id": raw.get("run_id"),
        "mode": rebuilt["mode"],
        "view_plan": rebuilt["view_plan"],
        "coverage_plan": rebuilt["coverage_plan"],
        "statuses": expectation["statuses"],
        "governance_overrides": rebuilt["governance_overrides"],
        "recorded_carriers": carriers,
        "observed_context_boundary": observed_context_boundary(carriers, receipts),  # noqa: F405
        "status": status,
        "findings": findings,
        "truth_boundary": (
            "Integrity does not prove complete coverage, absent hidden context, "
            "semantic necessity, correct priority, or optimal ROI."
        ),
    }


def run_check(run_dir: Path) -> dict[str, Any]:
    try:
        return _run_check_impl(run_dir)
    except Exception as exc:
        return {
            "schema_version": CHECK_REPORT_SCHEMA,  # noqa: F405
            "run_dir": str(run_dir),
            "status": "blocked",
            "findings": [
                {
                    "severity": "block",
                    "code": "integrity-reconstruction",
                    "message": f"SRA runtime reconstruction failed closed: {exc}",
                }
            ],
            "truth_boundary": (
                "Integrity does not prove complete coverage, absent hidden context, "
                "semantic necessity, correct priority, or optimal ROI."
            ),
        }


def _repair_trace_anchors(run_dir: Path, run_id: str) -> dict[str, Any]:
    anchors: dict[str, Any] = {
        "prepared": None,
        "judgment_hashes": {},
        "carriers": {},
    }
    trace_path = run_dir / "trace.jsonl"
    if not trace_path.is_file():
        return anchors
    trace = load_jsonl(trace_path)  # noqa: F405
    seen: set[str] = set()
    judgment_events = {
        "coverage_judgment_recorded": "coverage",
        "challenge_judgment_recorded": "challenge",
        "situated_judgment_recorded": "situated",
        "reconciliation_judgment_recorded": "reconciliation",
    }
    previous_recorded_at: datetime | None = None
    for index, event in enumerate(trace):
        event_type = event.get("event_type")
        if event.get("schema_version") != TRACE_SCHEMA:  # noqa: F405
            raise SraRuntimeError(f"trace event {index} has unsupported schema")  # noqa: F405
        if event.get("run_id") != run_id:
            raise SraRuntimeError(f"trace event {index} has wrong run_id")  # noqa: F405
        recorded_at = _parse_utc_timestamp(event.get("recorded_at"))
        if recorded_at is None:
            raise SraRuntimeError(f"trace event {index} has invalid recorded_at")  # noqa: F405
        if previous_recorded_at is not None and recorded_at < previous_recorded_at:
            raise SraRuntimeError(  # noqa: F405
                f"trace event {index} recorded_at precedes the prior event"
            )
        previous_recorded_at = recorded_at
        if event.get("event_id") != expected_runtime_event_id(event):  # noqa: F405
            raise SraRuntimeError(f"trace event {index} has invalid event_id")  # noqa: F405
        if not isinstance(event_type, str):
            raise SraRuntimeError(f"trace event {index} has no event_type")  # noqa: F405
        payload = event.get("payload")
        if not isinstance(payload, dict):
            raise SraRuntimeError(f"trace event {index} payload must be an object")  # noqa: F405
        if event_type == "run_prepared":
            if event_type in seen:
                raise SraRuntimeError("trace repeats run_prepared")  # noqa: F405
            anchors["prepared"] = payload
        if event_type in judgment_events:
            if event_type in seen:
                raise SraRuntimeError(f"trace repeats {event_type}")  # noqa: F405
            stage = judgment_events[event_type]
            judgment_hash = payload.get("judgment_hash")
            carrier = payload.get("carrier")
            if not isinstance(judgment_hash, str) or not judgment_hash:
                raise SraRuntimeError(f"trace {event_type} has no judgment_hash")  # noqa: F405
            if carrier not in CARRIERS:  # noqa: F405
                raise SraRuntimeError(f"trace {event_type} has invalid carrier")  # noqa: F405
            anchors["judgment_hashes"][stage] = judgment_hash
            anchors["carriers"][stage] = carrier
        seen.add(event_type)
    return anchors


def _validate_repair_anchors(
    *,
    rebuilt: dict[str, Any],
    expectation: dict[str, Any],
    state: dict[str, Any],
    trace_anchors: dict[str, Any],
) -> None:
    prepared = trace_anchors.get("prepared")
    expected_input_anchor = {
        "raw_input_hash": rebuilt["raw_input_hash"],
        "context_admission_hash": rebuilt["context_admission_hash"],
        "base_packet_hash": rebuilt["base_packet"]["packet_hash"],
        "coverage_packet_hash": rebuilt["coverage_packet"]["packet_hash"],
        "challenge_packet_hash": rebuilt["challenge_packet"]["packet_hash"],
        "situated_packet_hash": rebuilt["situated_packet"]["packet_hash"],
    }

    def complete_input_anchor(value: Any) -> bool:
        return isinstance(value, dict) and all(
            isinstance(value.get(field), str) and bool(value.get(field))
            for field in PREPARED_INPUT_ANCHOR_FIELDS
        )

    if complete_input_anchor(prepared):
        anchor_name = "prepared trace"
        input_anchor = prepared
    elif complete_input_anchor(state):
        anchor_name = "run state"
        input_anchor = state
    else:
        raise SraRuntimeError(  # noqa: F405
            "cannot repair without a complete prepared-input anchor in trace or run state"
        )

    for field in PREPARED_INPUT_ANCHOR_FIELDS:
        if input_anchor.get(field) != expected_input_anchor[field]:
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair changed raw input: {anchor_name} {field} does not match"
            )

    trace_hashes = trace_anchors.get("judgment_hashes", {})
    if not isinstance(trace_hashes, dict):
        trace_hashes = {}
    for stage in ("coverage", "challenge", "situated", "reconciliation"):
        field = f"{stage}_judgment_hash"
        current = expectation["hashes"].get(field)
        trace_anchor = trace_hashes.get(stage)
        state_anchor = state.get(field) if state else None
        anchor = trace_anchor if isinstance(trace_anchor, str) else state_anchor
        if current is None:
            if isinstance(anchor, str) and anchor:
                raise SraRuntimeError(  # noqa: F405
                    f"cannot repair missing Agentic {stage} judgment"
                )
            continue
        if not isinstance(anchor, str) or not anchor:
            raise SraRuntimeError(  # noqa: F405
                f"cannot verify Agentic {stage} judgment before repair"
            )
        if current != anchor:
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair changed Agentic {stage} judgment"
            )


def _recover_carriers(
    state: dict[str, Any],
    trace_anchors: dict[str, Any],
) -> dict[str, str]:
    recovered: dict[str, str] = {}
    state_carriers = state.get("carriers", {})
    if isinstance(state_carriers, dict):
        for stage, carrier in state_carriers.items():
            if carrier in CARRIERS:  # noqa: F405
                recovered[str(stage)] = str(carrier)
    trace_carriers = trace_anchors.get("carriers", {})
    if isinstance(trace_carriers, dict):
        for stage, carrier in trace_carriers.items():
            if carrier in CARRIERS:  # noqa: F405
                recovered[str(stage)] = str(carrier)
    return recovered


def _ordered_trace_types(
    rebuilt: dict[str, Any], expectation: dict[str, Any]
) -> list[str]:
    expected = expected_trace_events(rebuilt, expectation, {"carriers": {}})
    order = ["run_prepared"]
    for event_type in (
        "coverage_judgment_recorded",
        "challenge_judgment_recorded",
        "situated_judgment_recorded",
        "views_compared",
        "reconciliation_requested",
        "reconciliation_judgment_recorded",
        "run_finalized",
        "run_conditional",
        "run_blocked",
    ):
        if event_type in expected:
            order.append(event_type)
    return order


def _remove_path(path: Path) -> None:
    if path.is_file() or path.is_symlink():
        path.unlink()


def _write_rebuilt_trace(
    run_dir: Path,
    rebuilt: dict[str, Any],
    expectation: dict[str, Any],
    state: dict[str, Any],
) -> None:
    event_payloads = expected_trace_events(rebuilt, expectation, state)
    order = _ordered_trace_types(rebuilt, expectation)
    trace_path = run_dir / "trace.jsonl"
    _remove_path(trace_path)
    for event_type in order:
        append_jsonl(  # noqa: F405
            trace_path,
            make_runtime_event(  # noqa: F405
                str(state["run_id"]), event_type, event_payloads[event_type]
            ),
        )


def repair_run(run_dir: Path) -> dict[str, Any]:
    """Rebuild SRA caches and derived artifacts without editing Agentic judgments."""
    if run_dir.is_symlink():
        raise SraRuntimeError("run directory must not be a symbolic link")  # noqa: F405
    raw_path = run_dir / "raw-input.json"
    state_path = run_dir / "run.json"
    trace_path = run_dir / "trace.jsonl"
    judgments_dir = run_dir / "judgments"
    for authoritative_path in (raw_path, state_path, trace_path):
        if (authoritative_path.exists() or authoritative_path.is_symlink()) and (
            _path_uses_symlink(authoritative_path, run_dir)
        ):
            raise SraRuntimeError(  # noqa: F405
                f"authoritative path must not use a symbolic link: {authoritative_path}"
            )
    if judgments_dir.is_symlink():
        raise SraRuntimeError("judgments directory must not use a symbolic link")  # noqa: F405
    for stage in ("coverage", "challenge", "situated", "reconciliation"):
        judgment_path = judgments_dir / f"{stage}.json"
        if (judgment_path.exists() or judgment_path.is_symlink()) and (
            _path_uses_symlink(judgment_path, run_dir)
        ):
            raise SraRuntimeError(  # noqa: F405
                f"Agentic judgment path must not use a symbolic link: {judgment_path}"
            )
    raw = load_json(raw_path)  # noqa: F405
    if not isinstance(raw, dict):
        raise SraRuntimeError("raw-input.json must contain an object")  # noqa: F405
    rebuilt = build_packets(raw)  # noqa: F405

    existing_state: dict[str, Any] = {}
    if state_path.is_file():
        value = load_json(state_path)  # noqa: F405
        if not isinstance(value, dict):
            raise SraRuntimeError("run.json must contain an object")  # noqa: F405
        schema_version = value.get("schema_version")
        if schema_version != RUN_SCHEMA:  # noqa: F405
            raise SraRuntimeError(
                f"SRA run uses {schema_version!r}; repair is version-bound to {RUN_SCHEMA}."
            )
        existing_state = value

    trace_anchors = _repair_trace_anchors(run_dir, str(raw["run_id"]))
    expectation = reconstruct_runtime_expectation(run_dir, rebuilt)
    if expectation["issues"]:
        raise SraRuntimeError(  # noqa: F405
            "cannot repair a run with invalid or illegally ordered Agentic judgments: "
            + "; ".join(expectation["issues"])
        )
    _validate_repair_anchors(
        rebuilt=rebuilt,
        expectation=expectation,
        state=existing_state,
        trace_anchors=trace_anchors,
    )
    carriers = _recover_carriers(existing_state, trace_anchors)
    recorded_stages = {
        stage
        for stage, judgment in expectation["judgments"].items()
        if judgment is not None
    }
    missing_carriers = sorted(recorded_stages - set(carriers))
    if missing_carriers:
        raise SraRuntimeError(  # noqa: F405
            "cannot infer carrier metadata for recorded judgments: "
            + ", ".join(missing_carriers)
        )
    carriers = {
        stage: carrier for stage, carrier in carriers.items() if stage in recorded_stages
    }
    receipts = existing_state.get("carrier_receipts", {})
    if not isinstance(receipts, dict):
        receipts = {}
    receipts = {
        stage: receipt
        for stage, receipt in receipts.items()
        if stage in carriers and isinstance(receipt, dict)
    }
    for stage, receipt in receipts.items():
        if set(receipt) != RECEIPT_KEYS:
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair invalid {stage} receipt shape"
            )
        if receipt.get("boundary") != RECEIPT_BOUNDARY:  # noqa: F405
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair changed {stage} receipt boundary"
            )
        if not isinstance(receipt.get("source_path"), str) or not receipt.get("source_path"):
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair invalid {stage} receipt source_path"
            )
        expected_stored_path = str(Path("receipts") / f"{stage}.receipt")
        if receipt.get("stored_path") != expected_stored_path:
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair invalid {stage} receipt path"
            )
        stored = run_dir / expected_stored_path
        if (run_dir / "receipts").is_symlink() or stored.is_symlink():
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair symbolic-link {stage} receipt path"
            )
        if not stored.is_file():
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair missing {stage} receipt"
            )
        if _receipt_hash(stored) != receipt.get("sha256"):
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair changed {stage} receipt"
            )
        if stored.stat().st_size != receipt.get("bytes"):
            raise SraRuntimeError(  # noqa: F405
                f"cannot repair changed {stage} receipt size"
            )

    for relative_path in (
        "comparison-report.json",
        "reconciliation-packet.json",
        "final-decision.json",
    ):
        _remove_path(run_dir / relative_path)
    for stage in ("coverage", "challenge", "situated", "reconciliation"):
        for relative_path in _surface_rel_paths(stage):
            _remove_path(run_dir / relative_path)

    (run_dir / "judgments").mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "context-admission.json", rebuilt["admission"])  # noqa: F405
    write_json(run_dir / "base-packet.json", rebuilt["base_packet"])  # noqa: F405
    write_json(run_dir / "coverage-packet.json", rebuilt["coverage_packet"])  # noqa: F405
    write_json(run_dir / "challenge-packet.json", rebuilt["challenge_packet"])  # noqa: F405
    write_json(run_dir / "situated-packet.json", rebuilt["situated_packet"])  # noqa: F405

    for stage in _required_surface_stages(rebuilt, expectation):
        packet = _packet_for_stage(rebuilt, expectation, stage)
        if stage == "reconciliation":
            write_json(run_dir / "reconciliation-packet.json", packet)  # noqa: F405
        write_stage_surface(run_dir=run_dir, stage=stage, packet=packet)  # noqa: F405
    comparison = expectation.get("comparison")
    if isinstance(comparison, dict):
        write_json(run_dir / "comparison-report.json", comparison)  # noqa: F405

    comparison_hash = (
        comparison.get("comparison_hash") if isinstance(comparison, dict) else None
    )
    reconciliation_packet = expectation.get("reconciliation_packet")
    reconciliation_packet_hash = (
        reconciliation_packet.get("packet_hash")
        if isinstance(reconciliation_packet, dict)
        else None
    )
    new_state = {
        "schema_version": RUN_SCHEMA,  # noqa: F405
        "run_id": raw["run_id"],
        "created_at": existing_state.get("created_at", now_iso()),  # noqa: F405
        "updated_at": now_iso(),  # noqa: F405
        "mode": rebuilt["mode"],
        "view_plan": rebuilt["view_plan"],
        "coverage_plan": rebuilt["coverage_plan"],
        "statuses": expectation["statuses"],
        "raw_input_hash": rebuilt["raw_input_hash"],
        "context_admission_hash": rebuilt["context_admission_hash"],
        "base_packet_hash": rebuilt["base_packet"]["packet_hash"],
        "coverage_packet_hash": rebuilt["coverage_packet"]["packet_hash"],
        "challenge_packet_hash": rebuilt["challenge_packet"]["packet_hash"],
        "situated_packet_hash": rebuilt["situated_packet"]["packet_hash"],
        "coverage_judgment_hash": expectation["hashes"]["coverage_judgment_hash"],
        "challenge_judgment_hash": expectation["hashes"]["challenge_judgment_hash"],
        "situated_judgment_hash": expectation["hashes"]["situated_judgment_hash"],
        "comparison_hash": comparison_hash,
        "reconciliation_packet_hash": reconciliation_packet_hash,
        "reconciliation_judgment_hash": expectation["hashes"][
            "reconciliation_judgment_hash"
        ],
        "challenge_map": rebuilt["challenge_map"],
        "context_weights": rebuilt["context_weights"],
        "governance_overrides": rebuilt["governance_overrides"],
        "warnings": rebuilt["warnings"],
        "carriers": carriers,
        "carrier_receipts": receipts,
        "paths": expected_paths(run_dir, rebuilt, expectation),
        "claim_ceiling": RUN_CLAIM_CEILING,  # noqa: F405
    }
    if expectation.get("final_source") is not None:
        final = create_final_decision(  # noqa: F405
            run_state=new_state,
            final_source=str(expectation["final_source"]),
            decision=expectation["final_decision"],
        )
        write_json(run_dir / "final-decision.json", final)  # noqa: F405
    _write_rebuilt_trace(run_dir, rebuilt, expectation, new_state)
    save_run_state(state_path, new_state)  # noqa: F405
    report = run_check(run_dir)
    return {
        "run_dir": str(run_dir),
        "run_id": raw["run_id"],
        "status": report["status"],
        "repaired": report["status"] in {"ok", "warning"},
        "findings": report["findings"],
    }
