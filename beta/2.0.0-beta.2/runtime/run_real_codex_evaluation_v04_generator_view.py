#!/usr/bin/env python3
"""Promote the false-positive v0.4 cell, then continue with a corrected resource view."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import generator_resource_view_v04 as resource_view  # noqa: E402
import run_real_codex_evaluation_v04 as base  # noqa: E402
import run_real_codex_evaluation_v04_evidence_view as evidence_runner  # noqa: E402


AMENDMENT_ID = "0.4-generator-view.1"
AMENDMENT_PATH = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-generator-view.1.json"
)
DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-generator-view.1.json"
)
TARGET_CELL_ID = "21de6914da6970d3fe7522ee39690ed3de187cb95ce70348bbfb04934c8006c4"


def amendment_root(out_dir: Path) -> Path:
    return out_dir / "recovery" / AMENDMENT_ID


def require(condition: bool, veto_id: str, reason: str) -> None:
    if not condition:
        raise base.EvaluationStop(veto_id, reason)


def _source_sets(out_dir: Path) -> dict[str, list[dict[str, str]]]:
    return {
        "cells": evidence_runner.artifact_receipts(
            out_dir, "cells/*/record.json", "record_digest"
        ),
        "generation_attempts": evidence_runner.artifact_receipts(
            out_dir, "generation-attempts/**/attempt.json", "attempt_digest"
        ),
        "judge_attempts": evidence_runner.artifact_receipts(
            out_dir, "judge-attempts/**/attempt.json", "attempt_digest"
        ),
        "judge_records": evidence_runner.artifact_receipts(
            out_dir, "judge-records/*/*.json", "record_digest"
        ),
        "judge_inputs": evidence_runner.artifact_receipts(
            out_dir, "judge-inputs/*.json", "input_digest"
        ),
        "blinded_views": evidence_runner.artifact_receipts(
            out_dir, "blinded-candidate-views/*.json", "receipt_digest"
        ),
    }


def _validate_receipts(
    out_dir: Path, receipts: Iterable[Mapping[str, Any]], digest_field: str
) -> None:
    for item in receipts:
        path = (out_dir / str(item["path"])).resolve()
        try:
            path.relative_to(out_dir.resolve())
        except ValueError as exc:
            raise base.EvaluationStop(
                "generator-view-source-drift", "source receipt leaves run root"
            ) from exc
        require(
            path.is_file() and base.sha256_file(path) == item["file_sha256"],
            "generator-view-source-drift",
            f"retained artifact differs: {path}",
        )
        payload = base.read_json(path)
        require(
            payload.get(digest_field) == item[digest_field],
            "generator-view-source-drift",
            f"retained digest differs: {path}",
        )


def _copy_bound(source: Path, destination: Path, expected_sha256: str) -> None:
    require(
        source.is_file() and base.sha256_file(source) == expected_sha256,
        "generator-view-source-drift",
        f"source snapshot input differs: {source}",
    )
    if destination.is_file():
        require(
            base.sha256_file(destination) == expected_sha256,
            "generator-view-source-drift",
            f"source snapshot copy differs: {destination}",
        )
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.partial")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def _verify_source_sets(
    sets: Mapping[str, list[dict[str, str]]], source: Mapping[str, Any]
) -> None:
    for name, receipts in sets.items():
        require(
            len(receipts) == source[f"{name}_count"],
            "generator-view-source-drift",
            f"source {name} count differs",
        )
        require(
            base.canonical_sha256(receipts) == source[f"{name}_set_digest"],
            "generator-view-source-drift",
            f"source {name} set differs",
        )


def ensure_source_snapshot(
    out_dir: Path, amendment: Mapping[str, Any]
) -> dict[str, Any]:
    source = amendment["retained_source_run"]
    root = amendment_root(out_dir) / "pre-amendment"
    receipt_path = root / "receipt.json"
    copies = {
        "run-state.json": source["run_state_sha256"],
        "stop-report.json": source["stop_report_sha256"],
    }
    digest_fields = {
        "cells": "record_digest",
        "generation_attempts": "attempt_digest",
        "judge_attempts": "attempt_digest",
        "judge_records": "record_digest",
        "judge_inputs": "input_digest",
        "blinded_views": "receipt_digest",
    }
    if receipt_path.is_file():
        receipt = base.read_json(receipt_path)
        unsigned = dict(receipt)
        digest = unsigned.pop("receipt_digest", None)
        require(
            digest == base.canonical_sha256(unsigned),
            "generator-view-source-drift",
            "source snapshot receipt differs",
        )
        for name, expected in copies.items():
            require(
                (root / name).is_file()
                and base.sha256_file(root / name) == expected,
                "generator-view-source-drift",
                f"source snapshot copy differs: {name}",
            )
        for name, digest_field in digest_fields.items():
            require(
                base.canonical_sha256(receipt[name])
                == source[f"{name}_set_digest"],
                "generator-view-source-drift",
                f"source snapshot {name} set differs",
            )
            _validate_receipts(out_dir, receipt[name], digest_field)
        return receipt

    run_state = out_dir / "run-state.json"
    stop_report = out_dir / str(source["stop_report_path"])
    require(
        run_state.is_file()
        and base.sha256_file(run_state) == source["run_state_sha256"]
        and base.read_json(run_state).get("state_digest") == source["run_state_digest"],
        "generator-view-source-drift",
        "source run-state differs",
    )
    require(
        stop_report.is_file()
        and base.sha256_file(stop_report) == source["stop_report_sha256"],
        "generator-view-source-drift",
        "source stop report differs",
    )
    sets = _source_sets(out_dir)
    _verify_source_sets(sets, source)
    _copy_bound(run_state, root / "run-state.json", source["run_state_sha256"])
    _copy_bound(stop_report, root / "stop-report.json", source["stop_report_sha256"])
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-generator-view-source-snapshot-v0.1",
        "amendment_id": AMENDMENT_ID,
        "run_state_sha256": source["run_state_sha256"],
        "stop_report_sha256": source["stop_report_sha256"],
        **sets,
        "snapshotted_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_digest"] = base.canonical_sha256(receipt)
    base.write_atomic_json(receipt_path, receipt)
    return receipt


def _target_context(
    *,
    protocol: Mapping[str, Any],
    auth_report: Mapping[str, Any],
    manifests: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], Mapping[str, Any], dict[str, Any]]:
    cases = base.source_cases(base.read_json(base.MATRIX_PATH))
    for cell in base.expected_cells(protocol, "matched"):
        case = cases[str(cell["case_id"])]
        manifest = manifests[str(cell["arm_id"])]
        cell_id, key = base.cell_identity(
            cell, case, manifest, str(auth_report["protocol_sha256"])
        )
        if cell_id == TARGET_CELL_ID:
            return cell, case, manifest, key
    raise base.EvaluationStop(
        "protocol-or-arm-drift", "generator-view target cell is absent"
    )


def _load_target_attempt(
    out_dir: Path, diagnosis: Mapping[str, Any]
) -> tuple[dict[str, Any], str, dict[str, Any], Path]:
    path = out_dir / "generation-attempts" / TARGET_CELL_ID / "attempt-01"
    attempt_path = path / "attempt.json"
    events_path = path / "events.jsonl"
    stderr_path = path / "stderr.txt"
    answer_path = path / "answer.txt"
    require(
        all(item.is_file() for item in (attempt_path, events_path, stderr_path, answer_path)),
        "generator-view-source-drift",
        "diagnosed attempt is incomplete",
    )
    attempt = base.read_json(attempt_path)
    unsigned = dict(attempt)
    digest = unsigned.pop("attempt_digest", None)
    answer = answer_path.read_text(encoding="utf-8")
    events = events_path.read_text(encoding="utf-8")
    stderr = stderr_path.read_text(encoding="utf-8")
    checks = {
        "attempt_digest": digest,
        "attempt_file_sha256": base.sha256_file(attempt_path),
        "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
        "events_sha256": hashlib.sha256(events.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "counted_tokens": attempt.get("counted_tokens"),
    }
    require(
        digest == base.canonical_sha256(unsigned)
        and all(checks[field] == diagnosis[field] for field in checks),
        "generator-view-source-drift",
        "diagnosed attempt differs",
    )
    require(
        attempt.get("returncode") == 0
        and attempt.get("timed_out") is False
        and attempt.get("answer_present") is True,
        "generator-view-source-drift",
        "diagnosed attempt is not a successful semantic output",
    )
    attempt["path"] = str(path)
    return attempt, answer, base.event_evidence(events), path


def _forbidden_fragments(
    out_dir: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    active_arm: str,
) -> list[str]:
    forbidden = {
        str(out_dir),
        str(base.MATRIX_PATH.resolve()),
        str(base.DEVELOPMENT_CASES.resolve()),
        str(base.PUBLIC_CASES.resolve()),
        str(evidence_runner.compat.COMPATIBLE_SCHEMA.resolve()),
        str(base.JUDGE_RUBRIC.resolve()),
    }
    for arm_id, manifest in manifests.items():
        if arm_id == active_arm:
            continue
        forbidden.update(
            {
                str(Path(manifest["host"]["home"]).resolve()),
                str(Path(manifest["host"]["execution_root"]).resolve()),
                str(Path(manifest["package"]["root"]).resolve()),
            }
        )
    return sorted(forbidden)


def _build_promoted_record(
    *,
    out_dir: Path,
    amendment: Mapping[str, Any],
    auth_report: Mapping[str, Any],
    protocol: Mapping[str, Any],
    manifests: Mapping[str, Mapping[str, Any]],
    source_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    diagnosis = amendment["diagnosis"]
    cell, case, manifest, key = _target_context(
        protocol=protocol, auth_report=auth_report, manifests=manifests
    )
    require(
        cell
        == {"case_id": "b2-dev-lifecycle-clear", "arm_id": "stable", "repeat": 1},
        "protocol-or-arm-drift",
        "diagnosed target identity differs",
    )
    attempt, answer, evidence, attempt_path = _load_target_attempt(out_dir, diagnosis)
    forbidden = _forbidden_fragments(out_dir, manifests, str(cell["arm_id"]))
    original_hits = [
        command
        for command in evidence["loaded_commands"]
        if base.FORBIDDEN_GENERATOR_COMMAND.search(command)
        or "../" in command
        or any(fragment in command for fragment in forbidden)
    ]
    require(
        len(original_hits) == diagnosis["original_detector_trigger_count"],
        "generator-view-source-drift",
        "diagnosed false-positive trigger count differs",
    )
    corrected_hits = resource_view.contaminated_commands(
        evidence["loaded_commands"],
        active_package_root=str(manifest["package"]["root"]),
        active_execution_root=str(manifest["host"]["execution_root"]),
        forbidden_path_fragments=forbidden,
    )
    require(
        len(corrected_hits) == diagnosis["corrected_detector_trigger_count"],
        "cross-arm-contamination",
        "diagnosed attempt contains a real forbidden resource read",
    )
    raw_turn = {
        "usage": evidence["usage"],
        "duration_seconds": attempt["wall_time_seconds"],
        "first_observable_action_latency_seconds": attempt[
            "first_observable_action"
        ]["offset_seconds"],
        "native_telemetry": evidence["native_telemetry"],
        "loaded_commands": evidence["loaded_commands"],
        "answer": answer,
        "agent_messages": evidence["agent_messages"],
        "returncode": attempt["returncode"],
        "timed_out": attempt["timed_out"],
    }
    telemetry = base.build_turn_telemetry(
        raw_turn,
        context={
            "case_id": cell["case_id"],
            "turn_index": 1,
            "entry_mode": case["contract"]["entry_mode"],
            "execution_root": manifest["host"]["execution_root"],
            "allowed_roots": [
                manifest["package"]["root"],
                manifest["host"]["execution_root"],
            ],
            "arm_manifest": manifest,
            "attempt": 1,
        },
        required_evidence=base.V04_REQUIRED_EVIDENCE,
    )
    require(
        telemetry["evidence_gate"]["status"] == "pass",
        "missing-primary-native-evidence",
        "promoted attempt does not satisfy the frozen evidence gate",
    )
    record: dict[str, Any] = {
        "schema_version": "mindthus-beta2-real-cell-v0.4",
        "cell_id": TARGET_CELL_ID,
        "cell_key": key,
        "arm_id": cell["arm_id"],
        "case_source_receipt": base.canonical_sha256(case["contract"]["source"]),
        "generation_attempt": {
            "attempt": 1,
            "attempt_digest": attempt["attempt_digest"],
            "path": str(attempt_path),
        },
        "answer_path": str(attempt_path / "answer.txt"),
        "answer_sha256": attempt["answer_sha256"],
        "event_types": evidence["event_types"],
        "transport_error_event_count": evidence["event_types"].count("error"),
        "usage": evidence["usage"],
        "counted_tokens": base.token_total(evidence["usage"]),
        "telemetry": telemetry,
        "native_first_useful_action_available": bool(
            evidence["first_native_timestamp"]
        ),
        "host_lifecycle_claim": "startup-session-only",
        "scenario_lifecycle_path": case["contract"]["lifecycle_path"],
        "generator_resource_view_amendment": {
            "amendment_id": AMENDMENT_ID,
            "protocol_sha256": auth_report["generator_view_protocol_sha256"],
            "lock_digest": auth_report["generator_view_lock_digest"],
            "promotion": "deterministic-existing-attempt",
            "model_calls_added": 0,
            "source_snapshot_digest": source_receipt["receipt_digest"],
            "prior_veto_retained": True,
        },
    }
    record["record_digest"] = base.canonical_sha256(record)
    return record


def promote_target_attempt(
    *,
    out_dir: Path,
    amendment: Mapping[str, Any],
    auth_report: Mapping[str, Any],
    protocol: Mapping[str, Any],
    manifests: Mapping[str, Mapping[str, Any]],
    source_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_path = amendment_root(out_dir) / "promotion-receipt.json"
    record_path = out_dir / "cells" / TARGET_CELL_ID / "record.json"
    if receipt_path.is_file():
        receipt = base.read_json(receipt_path)
        unsigned = dict(receipt)
        digest = unsigned.pop("receipt_digest", None)
        require(
            digest == base.canonical_sha256(unsigned),
            "generator-view-source-drift",
            "promotion receipt differs",
        )
        record = base.completed_cell(out_dir, TARGET_CELL_ID)
        require(
            record is not None
            and record.get("record_digest") == receipt["record_digest"]
            and record.get("generator_resource_view_amendment", {}).get(
                "amendment_id"
            )
            == AMENDMENT_ID,
            "generator-view-source-drift",
            "promoted cell differs",
        )
        return record
    require(
        not record_path.exists(),
        "generator-view-source-drift",
        "target record predates promotion receipt",
    )
    record = _build_promoted_record(
        out_dir=out_dir,
        amendment=amendment,
        auth_report=auth_report,
        protocol=protocol,
        manifests=manifests,
        source_receipt=source_receipt,
    )
    base.write_atomic_json(record_path, record)
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-generator-view-promotion-v0.1",
        "amendment_id": AMENDMENT_ID,
        "cell_id": TARGET_CELL_ID,
        "attempt_digest": amendment["diagnosis"]["attempt_digest"],
        "record_digest": record["record_digest"],
        "source_snapshot_digest": source_receipt["receipt_digest"],
        "model_calls_added": 0,
        "promoted_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_digest"] = base.canonical_sha256(receipt)
    base.write_atomic_json(receipt_path, receipt)
    base.completed_cell(out_dir, TARGET_CELL_ID)
    return record


def run_generator_view(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base.scan_partial_artifacts(out_dir)
    auth_report, authorization, protocol = base.authorized_context(
        args.authorization.resolve()
    )
    amendment = base.read_json(AMENDMENT_PATH)
    require(
        auth_report.get("generator_view_protocol_sha256")
        == base.sha256_file(AMENDMENT_PATH),
        "authority-or-evidence-regression",
        "generator-view authorization differs",
    )
    manifests = base.verify_arm_set(
        [path.resolve() for path in args.arm_manifest], authorization
    )
    source_receipt = ensure_source_snapshot(out_dir, amendment)
    _build_promoted_record(
        out_dir=out_dir,
        amendment=amendment,
        auth_report=auth_report,
        protocol=protocol,
        manifests=manifests,
        source_receipt=source_receipt,
    )
    if args.preflight_only:
        report, code = evidence_runner.run_evidence_view(args)
        return {
            **report,
            "amendment_id": AMENDMENT_ID,
            "generator_view_preflight": "passed",
            "target_cell_id": TARGET_CELL_ID,
            "promotion_model_calls": 0,
            "model_execution_performed": False,
        }, code

    promote_target_attempt(
        out_dir=out_dir,
        amendment=amendment,
        auth_report=auth_report,
        protocol=protocol,
        manifests=manifests,
        source_receipt=source_receipt,
    )
    original_execute = base.execute_generator_cell
    base.execute_generator_cell = resource_view.execute_generator_cell
    try:
        report, code = evidence_runner.run_evidence_view(args)
    finally:
        base.execute_generator_cell = original_execute
    completion: dict[str, Any] = {
        "schema_version": "mindthus-beta2-generator-view-completion-v0.1",
        "amendment_id": AMENDMENT_ID,
        "phase": args.phase,
        "analysis_status": report.get("status"),
        "target_cell_id": TARGET_CELL_ID,
        "promotion_model_calls": 0,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    completion["completion_digest"] = base.canonical_sha256(completion)
    base.write_atomic_json(
        amendment_root(out_dir) / f"{args.phase}-completion.json", completion
    )
    return {**report, "generator_view_amendment_id": AMENDMENT_ID}, code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "matched"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--arm-manifest", type=Path, action="append", required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument(
        "--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.timeout != 1800:
        parser.error("the frozen generator-view timeout is exactly 1800 seconds")
    if args.phase != "matched":
        parser.error("generator-view recovery is matched-only")
    return args


def main() -> int:
    args = parse_args()
    try:
        report, code = run_generator_view(args)
    except base.EvaluationStop as exc:
        report = {
            "status": "stopped",
            "amendment_id": AMENDMENT_ID,
            "veto_id": exc.veto_id,
            "reason": exc.reason,
        }
        code = 2
        if args.out_dir.exists():
            base.write_atomic_json(
                amendment_root(args.out_dir.resolve()) / "stop-report.json", report
            )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report = {"status": "blocked", "amendment_id": AMENDMENT_ID, "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
