#!/usr/bin/env python3
"""Append the frozen v0.4 recovery attempt, then continue the untouched v0.4 runner."""

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
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import run_real_codex_evaluation_v04 as base  # noqa: E402


DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-recovery.1.json"
)
RECOVERY_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-recovery.1.json"
)
RECOVERY_ANALYZER = RUNTIME_ROOT / "analyze_codex_evaluation_v04_recovery.py"
RECOVERY_ID = "0.4-recovery.1"
RECOVERY_CELL_ID = (
    "6721d94969c4893b4d5b7ffcc6b12fb38d334fd551f929114e2e7d1688a39dd5"
)


def recovery_root(out_dir: Path) -> Path:
    return out_dir / "recovery" / RECOVERY_ID


def require(condition: bool, veto_id: str, reason: str) -> None:
    if not condition:
        raise base.EvaluationStop(veto_id, reason)


def copy_bound_source(source: Path, destination: Path, expected_sha256: str) -> None:
    require(source.is_file(), "recovery-source-drift", f"source artifact is missing: {source}")
    require(base.sha256_file(source) == expected_sha256, "recovery-source-drift", f"source artifact differs: {source}")
    if destination.is_file():
        require(base.sha256_file(destination) == expected_sha256, "recovery-source-drift", f"source snapshot differs: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.partial")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def verify_completed_source_cells(out_dir: Path, amendment: Mapping[str, Any]) -> None:
    for item in amendment["retained_source_run"]["completed_cells"]:
        path = out_dir / "cells" / item["cell_id"] / "record.json"
        require(path.is_file(), "recovery-source-drift", f"retained cell is missing: {item['cell_id']}")
        require(base.sha256_file(path) == item["file_sha256"], "recovery-source-drift", f"retained cell file differs: {item['cell_id']}")
        record = base.read_json(path)
        require(record.get("record_digest") == item["record_digest"], "recovery-source-drift", f"retained cell digest differs: {item['cell_id']}")
        base.completed_cell(out_dir, str(item["cell_id"]))


def load_attempt(out_dir: Path, cell_id: str, number: int) -> tuple[dict[str, Any], str, dict[str, Any]]:
    path = out_dir / "generation-attempts" / cell_id / f"attempt-{number:02d}"
    attempt_path = path / "attempt.json"
    require(attempt_path.is_file(), "untraceable-or-partial-artifact", f"attempt is missing: {path}")
    attempt = base.read_json(attempt_path)
    unsigned = dict(attempt)
    digest = unsigned.pop("attempt_digest", None)
    require(digest == base.canonical_sha256(unsigned), "untraceable-or-partial-artifact", f"attempt digest differs: {path}")
    require(attempt.get("cell_id") == cell_id and attempt.get("attempt") == number, "untraceable-or-partial-artifact", f"attempt identity differs: {path}")
    events_path = path / "events.jsonl"
    stderr_path = path / "stderr.txt"
    answer_path = path / "answer.txt"
    require(events_path.is_file() and stderr_path.is_file(), "untraceable-or-partial-artifact", f"attempt streams are missing: {path}")
    events = events_path.read_text(encoding="utf-8")
    stderr = stderr_path.read_text(encoding="utf-8")
    answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    require(hashlib.sha256(events.encode("utf-8")).hexdigest() == attempt.get("events_sha256"), "untraceable-or-partial-artifact", f"attempt events differ: {path}")
    require(hashlib.sha256(stderr.encode("utf-8")).hexdigest() == attempt.get("stderr_sha256"), "untraceable-or-partial-artifact", f"attempt stderr differs: {path}")
    require(hashlib.sha256(answer.encode("utf-8")).hexdigest() == attempt.get("answer_sha256"), "untraceable-or-partial-artifact", f"attempt answer differs: {path}")
    require(bool(answer) == bool(attempt.get("answer_present")), "untraceable-or-partial-artifact", f"attempt answer presence differs: {path}")
    attempt["path"] = str(path)
    return attempt, answer, base.event_evidence(events)


def ensure_source_snapshot(out_dir: Path, amendment: Mapping[str, Any]) -> dict[str, Any]:
    source = amendment["retained_source_run"]
    root = recovery_root(out_dir) / "pre-amendment"
    receipt_path = root / "receipt.json"
    run_state_copy = root / "run-state.json"
    stop_copy = root / "stop-report.json"
    if receipt_path.is_file():
        receipt = base.read_json(receipt_path)
        unsigned = dict(receipt)
        digest = unsigned.pop("receipt_digest", None)
        require(digest == base.canonical_sha256(unsigned), "recovery-source-drift", "pre-amendment receipt digest differs")
        require(base.sha256_file(run_state_copy) == source["run_state_sha256"], "recovery-source-drift", "pre-amendment run-state snapshot differs")
        require(base.sha256_file(stop_copy) == source["stop_report_sha256"], "recovery-source-drift", "pre-amendment stop snapshot differs")
        return receipt
    copy_bound_source(out_dir / "run-state.json", run_state_copy, source["run_state_sha256"])
    copy_bound_source(out_dir / "stop-report.json", stop_copy, source["stop_report_sha256"])
    receipt = {
        "schema_version": "mindthus-beta2-v0.4-recovery-source-snapshot-v0.1",
        "amendment_id": RECOVERY_ID,
        "base_protocol_sha256": amendment["base_binding"]["protocol_sha256"],
        "run_state_path": str(run_state_copy),
        "run_state_sha256": source["run_state_sha256"],
        "stop_report_path": str(stop_copy),
        "stop_report_sha256": source["stop_report_sha256"],
        "retained_cell_count": len(source["completed_cells"]),
        "incomplete_attempt_digest": source["incomplete_cell"]["attempt_digest"],
        "snapshotted_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_digest"] = base.canonical_sha256(receipt)
    base.write_atomic_json(receipt_path, receipt)
    return receipt


def verify_incomplete_attempt(out_dir: Path, amendment: Mapping[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any]]:
    frozen = amendment["retained_source_run"]["incomplete_cell"]
    attempt, answer, evidence = load_attempt(out_dir, RECOVERY_CELL_ID, 1)
    attempt_path = Path(attempt["path"]) / "attempt.json"
    require(base.sha256_file(attempt_path) == frozen["attempt_file_sha256"], "recovery-source-drift", "incomplete attempt file differs")
    checks = {
        "attempt_digest": attempt.get("attempt_digest"),
        "answer_sha256": attempt.get("answer_sha256"),
        "events_sha256": attempt.get("events_sha256"),
        "stderr_sha256": attempt.get("stderr_sha256"),
        "returncode": attempt.get("returncode"),
        "timed_out": attempt.get("timed_out"),
    }
    for field, actual in checks.items():
        require(actual == frozen[field], "recovery-source-drift", f"incomplete attempt {field} differs")
    require(bool(answer), "recovery-source-drift", "retained semantic output disappeared")
    require(attempt.get("usage") is None and attempt.get("counted_tokens") == 0, "recovery-source-drift", "unknown attempt usage was rewritten")
    return attempt, answer, evidence


def forbidden_fragments(
    out_dir: Path, manifests: Mapping[str, Mapping[str, Any]], active_arm: str
) -> list[str]:
    paths = {
        str(out_dir),
        str(base.MATRIX_PATH.resolve()),
        str(base.DEVELOPMENT_CASES.resolve()),
        str(base.PUBLIC_CASES.resolve()),
        str(base.JUDGE_SCHEMA.resolve()),
        str(base.JUDGE_RUBRIC.resolve()),
    }
    for arm_id, manifest in manifests.items():
        if arm_id == active_arm:
            continue
        paths.update(
            {
                str(Path(manifest["host"]["home"]).resolve()),
                str(Path(manifest["host"]["execution_root"]).resolve()),
                str(Path(manifest["package"]["root"]).resolve()),
            }
        )
    return sorted(paths)


def validate_no_contamination(
    evidence_items: Iterable[Mapping[str, Any]], forbidden_paths: Iterable[str]
) -> None:
    contaminated: list[str] = []
    for evidence in evidence_items:
        for command in evidence["loaded_commands"]:
            if (
                base.FORBIDDEN_GENERATOR_COMMAND.search(command)
                or "../" in command
                or any(fragment in command for fragment in forbidden_paths)
            ):
                contaminated.append(command)
    require(not contaminated, "cross-arm-contamination", "recovery loaded forbidden evaluation resources")


def build_recovered_record(
    *,
    cell: Mapping[str, Any],
    case: Mapping[str, Any],
    manifest: Mapping[str, Any],
    key: Mapping[str, Any],
    first: tuple[dict[str, Any], str, dict[str, Any]],
    second: tuple[dict[str, Any], str, dict[str, Any]],
    authorization: Mapping[str, Any],
    recovery_digest: str,
    recovery_lock_digest: str,
    out_dir: Path,
) -> dict[str, Any]:
    first_attempt, _first_answer, first_evidence = first
    second_attempt, answer, second_evidence = second
    require(second_attempt.get("returncode") == 0, "v0.4-recovery-attempt-failed", "recovery attempt returned nonzero")
    require(second_attempt.get("timed_out") is False, "v0.4-recovery-attempt-failed", "recovery attempt timed out")
    require(bool(answer) and second_attempt.get("answer_present") is True, "v0.4-recovery-attempt-failed", "recovery attempt has no final answer")
    require(isinstance(second_evidence.get("usage"), Mapping), "missing-primary-native-evidence", "recovery attempt has no native terminal usage")
    combined_commands = [
        *first_evidence["loaded_commands"],
        *second_evidence["loaded_commands"],
    ]
    combined_messages = [
        *first_evidence["agent_messages"],
        *second_evidence["agent_messages"],
    ]
    first_observable = first_attempt.get("first_observable_action")
    first_offset = (
        float(first_observable["offset_seconds"])
        if isinstance(first_observable, Mapping)
        else second_attempt.get("first_observable_action", {}).get("offset_seconds")
        if isinstance(second_attempt.get("first_observable_action"), Mapping)
        else None
    )
    raw_turn = {
        "usage": second_evidence["usage"],
        "duration_seconds": float(first_attempt["wall_time_seconds"])
        + float(second_attempt["wall_time_seconds"]),
        "first_observable_action_latency_seconds": first_offset,
        "native_telemetry": second_evidence["native_telemetry"],
        "loaded_commands": combined_commands,
        "answer": answer,
        "agent_messages": combined_messages,
        "returncode": 0,
        "timed_out": False,
    }
    required_evidence = dict(base.V04_REQUIRED_EVIDENCE)
    telemetry = base.build_turn_telemetry(
        raw_turn,
        context={
            "case_id": cell["case_id"],
            "turn_index": 1,
            "entry_mode": case["contract"]["entry_mode"],
            "execution_root": manifest["host"]["execution_root"],
            "allowed_roots": [manifest["package"]["root"], manifest["host"]["execution_root"]],
            "arm_manifest": manifest,
            "attempt": 2,
        },
        required_evidence=required_evidence,
    )
    telemetry["measurements"]["failure_count"] = {
        "status": "available",
        "value": 1,
        "provenance": "deterministic",
        "source": "recovery-amendment.retained-attempt-history",
    }
    telemetry["measurements"]["wall_time_seconds"]["source"] = (
        "recovery-amendment.sum-of-attempt-wall-times"
    )
    telemetry["measurements"]["first_observable_action_latency_seconds"]["source"] = (
        "recovery-amendment.first-retained-stream-arrival"
    )
    telemetry.pop("telemetry_digest", None)
    telemetry["telemetry_digest"] = base.canonical_sha256(telemetry)
    measured_tokens = base.token_total(second_evidence["usage"])
    record: dict[str, Any] = {
        "schema_version": "mindthus-beta2-real-cell-v0.4",
        "cell_id": RECOVERY_CELL_ID,
        "cell_key": dict(key),
        "arm_id": cell["arm_id"],
        "case_source_receipt": base.canonical_sha256(case["contract"]["source"]),
        "generation_attempt": {
            "attempt": 2,
            "attempt_digest": second_attempt["attempt_digest"],
            "path": second_attempt["path"],
        },
        "generation_attempt_history": [
            {
                "attempt": 1,
                "attempt_digest": first_attempt["attempt_digest"],
                "path": first_attempt["path"],
                "outcome": "timed-out-after-semantic-output",
            },
            {
                "attempt": 2,
                "attempt_digest": second_attempt["attempt_digest"],
                "path": second_attempt["path"],
                "outcome": "completed",
            },
        ],
        "recovery_amendment": {
            "amendment_id": RECOVERY_ID,
            "protocol_sha256": recovery_digest,
            "lock_digest": recovery_lock_digest,
            "append_only": True,
            "prior_semantic_output_retained": True,
        },
        "recovery_cost_evidence": {
            "attempt_1_wall_time_seconds": first_attempt["wall_time_seconds"],
            "attempt_1_first_observable_action_latency_seconds": first_offset,
            "attempt_1_native_usage": "unknown-unavailable",
            "attempt_2_wall_time_seconds": second_attempt["wall_time_seconds"],
            "attempt_2_counted_tokens": measured_tokens,
            "unknown_usage_reserved_tokens": authorization["recovery_budget"][
                "unknown_usage_reserved_tokens"
            ],
            "efficiency_evidence_status": "right-censored-exclude-paired-unit",
        },
        "answer_path": str(Path(second_attempt["path"]) / "answer.txt"),
        "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "event_types": [*first_evidence["event_types"], *second_evidence["event_types"]],
        "transport_error_event_count": (
            first_evidence["event_types"].count("error")
            + second_evidence["event_types"].count("error")
        ),
        "usage": second_evidence["usage"],
        "counted_tokens": measured_tokens,
        "telemetry": telemetry,
        "native_first_useful_action_available": bool(second_evidence["first_native_timestamp"]),
        "host_lifecycle_claim": "startup-session-only",
        "scenario_lifecycle_path": case["contract"]["lifecycle_path"],
    }
    record["record_digest"] = base.canonical_sha256(record)
    base.write_atomic_json(out_dir / "cells" / RECOVERY_CELL_ID / "record.json", record)
    require(telemetry["evidence_gate"]["status"] == "pass", "missing-primary-native-evidence", f"recovery evidence gate blocked: {telemetry['evidence_gate']['reasons']}")
    return record


def write_recovery_receipt(
    out_dir: Path,
    *,
    status: str,
    first_attempt: Mapping[str, Any],
    second_attempt: Mapping[str, Any],
    record: Mapping[str, Any] | None,
    authorization_report: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-v0.4-recovery-receipt-v0.1",
        "amendment_id": RECOVERY_ID,
        "status": status,
        "cell_id": RECOVERY_CELL_ID,
        "attempt_1_digest": first_attempt["attempt_digest"],
        "attempt_2_digest": second_attempt["attempt_digest"],
        "recovered_cell_record_digest": record.get("record_digest") if record else None,
        "base_protocol_sha256": authorization_report["protocol_sha256"],
        "recovery_protocol_sha256": authorization_report["recovery_protocol_sha256"],
        "recovery_lock_digest": authorization_report["recovery_lock_digest"],
        "unknown_usage_reserved_tokens": authorization_report[
            "unknown_usage_reserved_tokens"
        ],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    payload["receipt_digest"] = base.canonical_sha256(payload)
    base.write_atomic_json(recovery_root(out_dir) / "recovery-attempt.json", payload)
    return payload


def ensure_recovered_cell(
    *,
    out_dir: Path,
    authorization_path: Path,
    arm_paths: Iterable[Path],
    timeout: int,
    allow_model_execution: bool,
) -> tuple[dict[str, Any] | None, bool]:
    amendment = base.read_json(RECOVERY_PROTOCOL)
    ensure_source_snapshot(out_dir, amendment)
    verify_completed_source_cells(out_dir, amendment)
    first = verify_incomplete_attempt(out_dir, amendment)
    auth_report, authorization, protocol = base.authorized_context(authorization_path)
    manifests = base.verify_arm_set(arm_paths, authorization)
    for arm_id, digest in amendment["retained_source_run"]["arm_identity_digests"].items():
        require(manifests[arm_id]["identity_digest"] == digest, "recovery-source-drift", f"{arm_id} arm identity differs")
    matrix = base.read_json(base.MATRIX_PATH)
    cases = base.source_cases(matrix)
    target = next(
        cell
        for cell in base.expected_cells(protocol, "smoke")
        if cell == {
            "case_id": "b2-dev-near-normal-debugging",
            "arm_id": "direct-only",
            "repeat": 1,
        }
    )
    case = cases[target["case_id"]]
    manifest = manifests[target["arm_id"]]
    cell_id, key = base.cell_identity(target, case, manifest, auth_report["protocol_sha256"])
    require(cell_id == RECOVERY_CELL_ID, "protocol-or-arm-drift", "recovery cell identity differs")
    existing = base.completed_cell(out_dir, RECOVERY_CELL_ID)
    if existing is not None:
        recovery = existing.get("recovery_amendment")
        require(isinstance(recovery, Mapping), "untraceable-or-partial-artifact", "recovered cell lacks amendment receipt")
        require(recovery.get("amendment_id") == RECOVERY_ID, "untraceable-or-partial-artifact", "recovered cell amendment differs")
        require(recovery.get("protocol_sha256") == auth_report["recovery_protocol_sha256"], "untraceable-or-partial-artifact", "recovered cell protocol differs")
        history = existing.get("generation_attempt_history")
        require(isinstance(history, list) and [item.get("attempt") for item in history] == [1, 2], "untraceable-or-partial-artifact", "recovery attempt history differs")
        return existing, False

    parent = out_dir / "generation-attempts" / RECOVERY_CELL_ID
    observed = sorted(path.name for path in parent.glob("attempt-*"))
    require(observed in (["attempt-01"], ["attempt-01", "attempt-02"]), "untraceable-or-partial-artifact", f"unexpected recovery attempt set: {observed}")
    if not allow_model_execution:
        if "attempt-02" in observed:
            second_attempt, _answer, _evidence = load_attempt(
                out_dir, RECOVERY_CELL_ID, 2
            )
            require(
                second_attempt.get("returncode") == 0
                and second_attempt.get("timed_out") is False
                and second_attempt.get("answer_present") is True,
                "v0.4-recovery-attempt-failed",
                "retained attempt-02 is not a successful recoverable output",
            )
            return None, False
        return None, False
    if "attempt-02" in observed:
        second = load_attempt(out_dir, RECOVERY_CELL_ID, 2)
    else:
        generation_calls, _judge_calls, _tokens = base.observed_attempt_usage(out_dir)
        require(generation_calls < authorization["maximum_generation_calls"], "authority-or-evidence-regression", "generation call ceiling reached before recovery")
        prompt = base.generator_prompt(base.user_prompt(case["source"]))
        attempt, _capture, answer, evidence = base.run_generator_attempt(
            cell_id=RECOVERY_CELL_ID,
            prompt=prompt,
            manifest=manifest,
            authorization=authorization,
            out_dir=out_dir,
            attempt_number=2,
            timeout=timeout,
        )
        second = (attempt, answer, evidence)
    second_attempt, _second_answer, _second_evidence = second
    if (
        second_attempt.get("returncode") != 0
        or second_attempt.get("timed_out") is not False
        or second_attempt.get("answer_present") is not True
    ):
        write_recovery_receipt(
            out_dir,
            status="terminal-failure",
            first_attempt=first[0],
            second_attempt=second_attempt,
            record=None,
            authorization_report=auth_report,
        )
        raise base.EvaluationStop(
            "v0.4-recovery-attempt-failed",
            "the single additive recovery attempt failed; no further v0.4 recovery is authorized",
        )
    validate_no_contamination(
        (first[2], second[2]),
        forbidden_fragments(out_dir, manifests, target["arm_id"]),
    )
    record = build_recovered_record(
        cell=target,
        case=case,
        manifest=manifest,
        key=key,
        first=first,
        second=second,
        authorization=authorization,
        recovery_digest=auth_report["recovery_protocol_sha256"],
        recovery_lock_digest=auth_report["recovery_lock_digest"],
        out_dir=out_dir,
    )
    write_recovery_receipt(
        out_dir,
        status="completed",
        first_attempt=first[0],
        second_attempt=second_attempt,
        record=record,
        authorization_report=auth_report,
    )
    return record, True


def run_recovery(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base.scan_partial_artifacts(out_dir)
    record, created = ensure_recovered_cell(
        out_dir=out_dir,
        authorization_path=args.authorization.resolve(),
        arm_paths=[path.resolve() for path in args.arm_manifest],
        timeout=args.timeout,
        allow_model_execution=not args.preflight_only,
    )
    if args.preflight_only:
        return {
            "status": "ready",
            "amendment_id": RECOVERY_ID,
            "cell_id": record["cell_id"] if record else RECOVERY_CELL_ID,
            "recovered_cell_already_complete": record is not None,
            "model_execution_performed": False,
            "next_phase": args.phase,
        }, 0
    require(
        record is not None,
        "untraceable-or-partial-artifact",
        "recovery did not produce an atomic cell record",
    )
    base_args = argparse.Namespace(
        phase=args.phase,
        out_dir=out_dir,
        runtime_root=args.runtime_root.resolve(),
        arm_manifest=[path.resolve() for path in args.arm_manifest],
        authorization=args.authorization.resolve(),
        auth_source=args.auth_source.resolve(),
        timeout=args.timeout,
    )
    base_report, base_code = base.run_evaluation(base_args)
    base.write_atomic_json(out_dir / f"{args.phase}-analysis.base-v0.4.json", base_report)
    amended_report = base.run_json(
        [
            "python3",
            str(RECOVERY_ANALYZER),
            "--phase",
            args.phase,
            "--run-dir",
            str(out_dir),
            "--authorization",
            str(args.authorization.resolve()),
        ],
        label=f"{args.phase} recovery analysis",
    )
    base.write_atomic_json(
        recovery_root(out_dir) / f"{args.phase}-completion.json",
        {
            "schema_version": "mindthus-beta2-v0.4-recovery-completion-v0.1",
            "amendment_id": RECOVERY_ID,
            "base_runner_status": base_report.get("status"),
            "amended_analysis_status": amended_report.get("status"),
            "original_stop_report_preserved_at": str(
                recovery_root(out_dir) / "pre-amendment" / "stop-report.json"
            ),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    status = str(amended_report.get("status"))
    code = 0 if status in {"passed", "matched-complete"} else max(base_code, 3)
    return amended_report, code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "matched"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--arm-manifest", type=Path, action="append", required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.timeout != 1800:
        parser.error("the frozen recovery timeout is exactly 1800 seconds")
    return args


def main() -> int:
    args = parse_args()
    try:
        report, code = run_recovery(args)
    except base.EvaluationStop as exc:
        report = {
            "status": "stopped",
            "amendment_id": RECOVERY_ID,
            "veto_id": exc.veto_id,
            "reason": exc.reason,
        }
        code = 2
        if args.out_dir.exists():
            base.write_atomic_json(
                recovery_root(args.out_dir.resolve()) / "stop-report.json", report
            )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report = {"status": "blocked", "amendment_id": RECOVERY_ID, "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
