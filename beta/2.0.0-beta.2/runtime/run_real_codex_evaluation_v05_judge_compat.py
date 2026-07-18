#!/usr/bin/env python3
"""Resume frozen v0.5 through a schema-only Judge transport adapter.

The base v0.5 protocol, generated answers, scoring contract, isolation policy, and
budgets remain unchanged.  The adapter removes two API-unsupported ``uniqueItems``
keywords only at the Structured Outputs boundary and keeps the canonical local
Judge validator authoritative.  The four original pre-sampling failures remain
immutable and count against the original 34-call ceiling.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping, Sequence


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
BASE_RUNNER_PATH = RUNTIME_ROOT / "run_real_codex_evaluation_v05.py"
DEFAULT_AUTHORIZATION = (
    BETA_ROOT
    / "authorizations"
    / "issue-119-codex-v0.5-judge-compat.1.pending.json"
)
AMENDMENT_PATH = (
    BETA_ROOT
    / "protocols"
    / "evaluation-protocol-v0.5-judge-compat.1.json"
)
ORIGINAL_SCHEMA = BETA_ROOT / "fixtures" / "judge-output-v0.4.schema.json"
COMPATIBLE_SCHEMA = (
    BETA_ROOT / "fixtures" / "judge-output-v0.4-openai-compatible.schema.json"
)
COMPAT_ID = "0.5-judge-compat.1"
API_ERROR_FRAGMENT = "'uniqueItems' is not permitted"
STATE_SCHEMA = "mindthus-beta2-incremental-evaluation-state-v0.5-judge-compat.1"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load("mindthus_beta2_v05_judge_compat_base", BASE_RUNNER_PATH)
V04 = BASE.V04


class CompatibilityStop(RuntimeError):
    def __init__(self, veto_id: str, reason: str):
        super().__init__(reason)
        self.veto_id = veto_id
        self.reason = reason


_ACTIVE_AMENDMENT: Mapping[str, Any] | None = None


def require(condition: bool, veto_id: str, reason: str) -> None:
    if not condition:
        raise CompatibilityStop(veto_id, reason)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return V04.canonical_sha256(value)


def recovery_root(out_dir: Path) -> Path:
    return out_dir / "recovery" / COMPAT_ID


def _validate_transport_schema() -> dict[str, Any]:
    original = read_json(ORIGINAL_SCHEMA)
    compatible = read_json(COMPATIBLE_SCHEMA)
    expected = json.loads(json.dumps(original))
    removed: list[str] = []
    for name in ("primitive_obligation_results", "unexpected_primitive_actions"):
        node = expected["properties"][name]
        require(
            node.pop("uniqueItems", None) is True,
            "judge-schema-compatibility-drift",
            f"canonical uniqueness keyword differs: {name}",
        )
        removed.append(f"properties.{name}.uniqueItems")
    require(
        compatible == expected,
        "judge-schema-compatibility-drift",
        "API-facing Judge schema changes more than the two rejected keywords",
    )

    def walk(value: object, path: str = "$") -> list[str]:
        found: list[str] = []
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key == "uniqueItems":
                    found.append(f"{path}.{key}")
                found.extend(walk(child, f"{path}.{key}"))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                found.extend(walk(child, f"{path}[{index}]"))
        return found

    require(
        not walk(compatible),
        "judge-schema-compatibility-drift",
        "API-facing Judge schema still contains uniqueItems",
    )
    return {
        "original_schema_sha256": sha256_file(ORIGINAL_SCHEMA),
        "compatible_schema_sha256": sha256_file(COMPATIBLE_SCHEMA),
        "removed_keyword_paths": removed,
        "canonical_local_validation_preserved": True,
    }


def _verify_signed_json(path: Path, digest_field: str, label: str) -> dict[str, Any]:
    require(path.is_file(), "judge-compat-source-drift", f"{label} is missing: {path}")
    payload = read_json(path)
    unsigned = dict(payload)
    digest = unsigned.pop(digest_field, None)
    require(
        digest == canonical_sha256(unsigned),
        "judge-compat-source-drift",
        f"{label} digest differs: {path}",
    )
    return payload


def verify_retained_source(
    out_dir: Path,
    amendment: Mapping[str, Any],
    protocol_sha256: str,
) -> dict[str, Any]:
    source = amendment["retained_source_run"]
    require(
        source["protocol_sha256"] == protocol_sha256,
        "judge-compat-source-drift",
        "retained source protocol differs",
    )
    state_path = out_dir / "run-state-v0.5.json"
    state = _verify_signed_json(state_path, "state_digest", "base v0.5 run state")
    require(
        sha256_file(state_path) == source["run_state_file_sha256"]
        and state.get("status") == "vetoed"
        and state.get("committed_batches") == 0,
        "judge-compat-source-drift",
        "base v0.5 stop state differs",
    )

    observed_cells: list[dict[str, Any]] = []
    for receipt in source["generation_cells"]:
        cell_id = str(receipt["cell_id"])
        record = BASE.completed_cell(out_dir, cell_id)
        path = out_dir / "cells" / cell_id / "record.json"
        require(
            record is not None
            and record["record_digest"] == receipt["record_digest"]
            and sha256_file(path) == receipt["record_file_sha256"]
            and record["answer_sha256"] == receipt["answer_sha256"]
            and record["counted_tokens"] == receipt["counted_tokens"],
            "judge-compat-source-drift",
            f"retained Generator cell differs: {cell_id}",
        )
        isolation_path = Path(str(record["isolation_receipt"]["path"]))
        isolation = BASE._verify_isolation_receipt(isolation_path)
        require(
            isolation["receipt_digest"] == receipt["isolation_receipt_digest"]
            and sha256_file(isolation_path) == receipt["isolation_receipt_file_sha256"],
            "judge-compat-source-drift",
            f"retained Generator isolation differs: {cell_id}",
        )
        observed_cells.append(dict(receipt))
    require(
        len(observed_cells) == 3
        and canonical_sha256(observed_cells) == source["generation_cell_set_digest"],
        "judge-compat-source-drift",
        "retained Generator cell set differs",
    )

    output_id = str(source["failed_output_id"])
    observed_attempts: list[dict[str, Any]] = []
    for receipt in source["failed_judge_attempts"]:
        slot = int(receipt["slot"])
        number = int(receipt["attempt"])
        root = (
            out_dir
            / "judge-attempts"
            / output_id
            / f"slot-{slot}"
            / f"attempt-{number:02d}"
        )
        attempt_path = root / "attempt.json"
        attempt = _verify_signed_json(
            attempt_path, "attempt_digest", "original Judge attempt"
        )
        events_path = root / "events.jsonl"
        stderr_path = root / "stderr.txt"
        require(
            sha256_file(attempt_path) == receipt["attempt_file_sha256"]
            and sha256_file(events_path) == receipt["events_sha256"]
            and sha256_file(stderr_path) == receipt["stderr_sha256"]
            and attempt["attempt_digest"] == receipt["attempt_digest"]
            and attempt.get("returncode") == 1
            and attempt.get("timed_out") is False
            and attempt.get("output_present") is False
            and attempt.get("counted_tokens") == 0
            and not (root / "judge-output.json").exists()
            and API_ERROR_FRAGMENT in events_path.read_text(encoding="utf-8"),
            "judge-compat-source-drift",
            f"original Judge schema rejection differs: slot-{slot}/{number}",
        )
        isolation_path = Path(str(receipt["isolation_receipt_path"]))
        isolation = BASE._verify_isolation_receipt(isolation_path)
        require(
            isolation["receipt_digest"] == receipt["isolation_receipt_digest"]
            and sha256_file(isolation_path) == receipt["isolation_receipt_file_sha256"],
            "judge-compat-source-drift",
            f"original Judge isolation differs: slot-{slot}/{number}",
        )
        observed_attempts.append(dict(receipt))
    require(
        [(item["slot"], item["attempt"]) for item in observed_attempts]
        == [(1, 1), (1, 2), (2, 1), (2, 2)]
        and canonical_sha256(observed_attempts)
        == source["failed_judge_attempt_set_digest"],
        "judge-compat-source-drift",
        "original Judge attempt set differs",
    )

    observed_packets: list[dict[str, Any]] = []
    for receipt in source["failure_packets"]:
        slot = int(receipt["slot"])
        path = out_dir / "human-judge-failure-packets" / f"{output_id}-slot-{slot}.json"
        packet = _verify_signed_json(path, "packet_digest", "Judge failure packet")
        require(
            packet["packet_digest"] == receipt["packet_digest"]
            and sha256_file(path) == receipt["file_sha256"],
            "judge-compat-source-drift",
            f"Judge failure packet differs: slot-{slot}",
        )
        observed_packets.append(dict(receipt))
    require(
        canonical_sha256(observed_packets) == source["failure_packet_set_digest"],
        "judge-compat-source-drift",
        "Judge failure packet set differs",
    )
    return {
        "generation_outputs": 3,
        "generation_calls": 3,
        "judge_attempts": 4,
        "valid_judge_records": 0,
        "committed_batches": 0,
        "counted_tokens": 90_100,
        "failed_output_id": output_id,
        "source_receipt_digest": source["source_receipt_digest"],
    }


def _attempt_root(out_dir: Path, output_id: str, slot: int, number: int) -> Path:
    return (
        out_dir
        / "judge-attempts"
        / output_id
        / f"slot-{slot}"
        / f"attempt-{number:02d}"
    )


def _decode_attempt(
    root: Path,
    attempt: Mapping[str, Any],
    case: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str]:
    output_path = root / "judge-output.json"
    raw = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
    require(
        hashlib.sha256(raw.encode("utf-8")).hexdigest()
        == attempt.get("output_sha256"),
        "untraceable-or-partial-artifact",
        "compatible Judge output digest differs",
    )
    try:
        decoded = json.loads(raw)
        if not isinstance(decoded, Mapping):
            raise ValueError("judge output is not an object")
        normalized = V04.validate_judge_output(decoded, case)
    except (json.JSONDecodeError, TypeError, ValueError):
        normalized = None
    return normalized, raw


def _load_compatible_attempt(
    *,
    root: Path,
    output_id: str,
    slot: int,
    number: int,
    prompt_digest: str,
    blinded_input_digest: str,
    environment_digest: str,
    case: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    attempt = _verify_signed_json(root / "attempt.json", "attempt_digest", "compatible Judge attempt")
    require(
        attempt.get("blinded_output_id") == output_id
        and attempt.get("judge_slot") == slot
        and attempt.get("attempt") == number
        and attempt.get("judge_prompt_sha256") == prompt_digest
        and attempt.get("blinded_input_digest") == blinded_input_digest
        and attempt.get("environment_digest") == environment_digest
        and attempt.get("judge_schema_sha256") == sha256_file(COMPATIBLE_SCHEMA)
        and attempt.get("original_judge_schema_sha256") == sha256_file(ORIGINAL_SCHEMA)
        and attempt.get("judge_compatibility_amendment_id") == COMPAT_ID,
        "untraceable-or-partial-artifact",
        "compatible Judge attempt binding differs",
    )
    require(
        sha256_file(root / "events.jsonl") == attempt.get("events_sha256")
        and sha256_file(root / "stderr.txt") == attempt.get("stderr_sha256"),
        "untraceable-or-partial-artifact",
        "compatible Judge attempt streams differ",
    )
    normalized, _raw = _decode_attempt(root, attempt, case)
    return attempt, normalized


def _execute_compatible_attempt(
    *,
    parent: Path,
    attempt_number: int,
    slot: int,
    output_id: str,
    prompt: str,
    blinded_input_digest: str,
    case: Mapping[str, Any],
    environment: Mapping[str, Any],
    authorization: Mapping[str, Any],
    timeout: int,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    temp_dir = Path(
        tempfile.mkdtemp(prefix=f"attempt-{attempt_number:02d}.partial-", dir=parent)
    )
    answer_path = temp_dir / "judge-output.json"
    model = authorization["judge_model_and_reasoning"]
    command = [
        "codex",
        "exec",
        "--json",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--ephemeral",
        "-s",
        "read-only",
        "-C",
        str(environment["execution_root"]),
        "--model",
        model["model_id"],
        "-c",
        f'model_reasoning_effort="{model["reasoning_effort"]}"',
        "--output-schema",
        str(COMPATIBLE_SCHEMA),
        "-o",
        str(answer_path),
        "-",
    ]
    capture = V04.run_streamed(
        command,
        input_text=prompt,
        cwd=Path(environment["execution_root"]),
        env=environment["env"],
        timeout=timeout,
    )
    events = capture.stdout
    stderr = capture.stderr
    (temp_dir / "events.jsonl").write_text(events, encoding="utf-8")
    (temp_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    evidence = V04.event_evidence(events)
    raw = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    normalized: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        decoded = json.loads(raw)
        if not isinstance(decoded, Mapping):
            raise ValueError("judge output is not an object")
        normalized = V04.validate_judge_output(decoded, case)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        parse_error = str(exc)
    tokens = V04.token_total(evidence["usage"])
    attempt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-attempt-v0.5-judge-compat.1",
        "blinded_output_id": output_id,
        "judge_slot": slot,
        "attempt": attempt_number,
        "returncode": capture.returncode,
        "timed_out": capture.timed_out,
        "output_present": bool(raw),
        "output_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "parse_error": parse_error,
        "usage": evidence["usage"],
        "counted_tokens": tokens,
        "environment_digest": environment["environment_digest"],
        "blinded_input_digest": blinded_input_digest,
        "judge_prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "tool_call_count": len(evidence["loaded_commands"]),
        "tool_call_digests": [
            hashlib.sha256(item.encode("utf-8")).hexdigest()
            for item in evidence["loaded_commands"]
        ],
        "events_sha256": hashlib.sha256(events.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
        "judge_schema_sha256": sha256_file(COMPATIBLE_SCHEMA),
        "original_judge_schema_sha256": sha256_file(ORIGINAL_SCHEMA),
        "judge_compatibility_amendment_id": COMPAT_ID,
        "schema_compatibility_only": True,
        "retry_permitted": False,
    }
    attempt["attempt_digest"] = canonical_sha256(attempt)
    (temp_dir / "attempt.json").write_text(
        json.dumps(attempt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    destination = parent / f"attempt-{attempt_number:02d}"
    V04.finalize_attempt(temp_dir, destination)
    require(
        not evidence["loaded_commands"],
        "judge-environment-contamination",
        f"Judge slot {slot} used a tool for {output_id}",
    )
    return attempt, normalized


def _successful(attempt: Mapping[str, Any], normalized: object) -> bool:
    return bool(
        attempt.get("returncode") == 0
        and attempt.get("timed_out") is False
        and attempt.get("output_present") is True
        and attempt.get("parse_error") is None
        and isinstance(normalized, Mapping)
    )


def _original_history(out_dir: Path, output_id: str, slot: int) -> list[dict[str, Any]]:
    assert _ACTIVE_AMENDMENT is not None
    source = _ACTIVE_AMENDMENT["retained_source_run"]
    if output_id != source["failed_output_id"]:
        return []
    history: list[dict[str, Any]] = []
    for receipt in source["failed_judge_attempts"]:
        if int(receipt["slot"]) != slot:
            continue
        history.append(
            read_json(
                _attempt_root(out_dir, output_id, slot, int(receipt["attempt"]))
                / "attempt.json"
            )
        )
    return history


def _write_failure_packet(
    *,
    out_dir: Path,
    output_id: str,
    slot: int,
    blinded_input_digest: str,
    attempts: Iterable[Mapping[str, Any]],
) -> Path:
    packet: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-compat-failure-packet-v0.5",
        "amendment_id": COMPAT_ID,
        "blinded_output_id": output_id,
        "failed_judge_slot": slot,
        "adjudicator": "William",
        "blinded_input_digest": blinded_input_digest,
        "original_judge_schema_sha256": sha256_file(ORIGINAL_SCHEMA),
        "compatible_judge_schema_sha256": sha256_file(COMPATIBLE_SCHEMA),
        "attempts": [
            {
                "attempt": item["attempt"],
                "attempt_digest": item["attempt_digest"],
                "returncode": item["returncode"],
                "timed_out": item["timed_out"],
                "output_present": item["output_present"],
                "parse_error": item["parse_error"],
            }
            for item in attempts
        ],
        "decision_required": (
            "the no-expansion v0.5 compatibility call failed; no retry or further "
            "semantic call is permitted without William"
        ),
    }
    packet["packet_digest"] = canonical_sha256(packet)
    path = recovery_root(out_dir) / "failure-packets" / f"{output_id}-slot-{slot}.json"
    V04.write_atomic_json(path, packet)
    return path


def compatible_judge_slot(
    *,
    slot: int,
    output_id: str,
    prompt: str,
    blinded_input_digest: str,
    case: Mapping[str, Any],
    environment: Mapping[str, Any],
    authorization: Mapping[str, Any],
    out_dir: Path,
    timeout: int,
) -> tuple[dict[str, Any], int, int]:
    assert _ACTIVE_AMENDMENT is not None
    prompt_digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    existing = V04.existing_judge_record(out_dir, output_id, slot)
    if existing is not None:
        require(
            existing.get("judge_compatibility_amendment_id") == COMPAT_ID
            and existing.get("judge_schema_sha256") == sha256_file(COMPATIBLE_SCHEMA)
            and existing.get("blinded_input_digest") == blinded_input_digest
            and existing.get("judge_prompt_sha256") == prompt_digest,
            "untraceable-or-partial-artifact",
            "retained compatible Judge record differs",
        )
        return existing, 0, 0

    source_output = _ACTIVE_AMENDMENT["retained_source_run"]["failed_output_id"]
    attempt_number = 3 if output_id == source_output else 1
    parent = V04.attempt_parent(out_dir, "judge", f"{output_id}/slot-{slot}")
    observed = sorted(path.name for path in parent.glob("attempt-*"))
    allowed_before = ["attempt-01", "attempt-02"] if attempt_number == 3 else []
    allowed_after = [*allowed_before, f"attempt-{attempt_number:02d}"]
    require(
        observed in (allowed_before, allowed_after),
        "untraceable-or-partial-artifact",
        f"Judge compatibility attempt set differs: {output_id}/slot-{slot}: {observed}",
    )
    root = parent / f"attempt-{attempt_number:02d}"
    if root.is_dir():
        attempt, normalized = _load_compatible_attempt(
            root=root,
            output_id=output_id,
            slot=slot,
            number=attempt_number,
            prompt_digest=prompt_digest,
            blinded_input_digest=blinded_input_digest,
            environment_digest=str(environment["environment_digest"]),
            case=case,
        )
        calls = 0
        tokens = 0
    else:
        attempt, normalized = _execute_compatible_attempt(
            parent=parent,
            attempt_number=attempt_number,
            slot=slot,
            output_id=output_id,
            prompt=prompt,
            blinded_input_digest=blinded_input_digest,
            case=case,
            environment=environment,
            authorization=authorization,
            timeout=timeout,
        )
        calls = 1
        tokens = int(attempt.get("counted_tokens") or 0)
    history = [*_original_history(out_dir, output_id, slot), attempt]
    if not _successful(attempt, normalized):
        packet = _write_failure_packet(
            out_dir=out_dir,
            output_id=output_id,
            slot=slot,
            blinded_input_digest=blinded_input_digest,
            attempts=history,
        )
        raise CompatibilityStop(
            "v0.5-judge-compatibility-exhausted",
            f"compatible Judge slot {slot} failed without retry; packet: {packet}",
        )
    assert isinstance(normalized, Mapping)
    record: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-record-v0.5-judge-compat.1",
        "blinded_output_id": output_id,
        "judge_slot": slot,
        "attempt": attempt_number,
        "attempt_digest": attempt["attempt_digest"],
        "environment_digest": environment["environment_digest"],
        "blinded_input_digest": blinded_input_digest,
        "judge_prompt_sha256": prompt_digest,
        "verdict": dict(normalized),
        "usage": attempt["usage"],
        "counted_tokens": attempt["counted_tokens"],
        "judge_schema_sha256": sha256_file(COMPATIBLE_SCHEMA),
        "original_judge_schema_sha256": sha256_file(ORIGINAL_SCHEMA),
        "judge_compatibility_amendment_id": COMPAT_ID,
        "schema_compatibility_only": True,
        "judge_attempt_history": [
            {
                "attempt": item["attempt"],
                "attempt_digest": item["attempt_digest"],
                "returncode": item["returncode"],
                "timed_out": item["timed_out"],
                "output_present": item["output_present"],
                "transport_schema": (
                    "openai-compatible-v0.5"
                    if item.get("judge_compatibility_amendment_id") == COMPAT_ID
                    else "original-v0.5"
                ),
            }
            for item in history
        ],
    }
    record["record_digest"] = canonical_sha256(record)
    V04.write_atomic_json(
        out_dir / "judge-records" / output_id / f"judge-{slot}.json",
        record,
    )
    return record, calls, tokens


def _new_judge_calls_required(
    out_dir: Path, output_id: str, slots: Iterable[int]
) -> int:
    """Count semantic calls still required, not records still needing finalization."""
    assert _ACTIVE_AMENDMENT is not None
    source_output = _ACTIVE_AMENDMENT["retained_source_run"]["failed_output_id"]
    attempt_number = 3 if output_id == source_output else 1
    return sum(
        not _attempt_root(out_dir, output_id, int(slot), attempt_number).is_dir()
        for slot in slots
    )


def _state_payload(
    *,
    status: str,
    protocol_sha256: str,
    authorization_digest: str,
    generation_calls: int,
    judge_calls: int,
    counted_tokens: int,
    committed_batches: int,
    active_batch: Mapping[str, Any] | None,
    veto_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": STATE_SCHEMA,
        "amendment_id": COMPAT_ID,
        "status": status,
        "protocol_sha256": protocol_sha256,
        "authorization_digest": authorization_digest,
        "generation_calls": generation_calls,
        "judge_calls": judge_calls,
        "counted_tokens": counted_tokens,
        "committed_batches": committed_batches,
        "committed_generation_outputs": committed_batches * 3,
        "committed_judge_records": committed_batches * 6,
        "active_batch_id": active_batch.get("batch_id") if active_batch else None,
        "active_batch_index": active_batch.get("batch_index") if active_batch else None,
        "veto_id": veto_id,
        "reason": reason,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    payload["state_digest"] = canonical_sha256(payload)
    return payload


def _authorization_context(
    path: Path, *, allow_pending: bool
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    authorization = read_json(path)
    validator = V04.repo_path(
        authorization.get("authorization_validator_path"),
        "authorization_validator_path",
    )
    command = ["python3", str(validator), "--authorization", str(path)]
    if allow_pending:
        command.append("--allow-pending")
    report = V04.run_json(command, label="Judge compatibility authorization")
    if allow_pending:
        require(
            report.get("status") in {"pending", "authorized"},
            "authority-or-evidence-regression",
            "Judge compatibility authorization is invalid",
        )
    else:
        require(
            report.get("status") == "authorized",
            "authority-or-evidence-regression",
            "Judge compatibility execution authorization is inactive",
        )
    protocol = read_json(V04.repo_path(authorization["protocol"]["path"], "protocol.path"))
    return report, authorization, protocol


def preflight(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    auth_report, authorization, protocol = _authorization_context(
        args.authorization.resolve(), allow_pending=True
    )
    amendment = read_json(AMENDMENT_PATH)
    require(
        protocol.get("protocol_version") == "0.5",
        "protocol-or-arm-drift",
        "Judge compatibility runner received another base protocol",
    )
    schema = _validate_transport_schema()
    manifests = V04.verify_arm_set(args.arm_manifest, authorization)
    source = verify_retained_source(out_dir, amendment, auth_report["protocol_sha256"])
    generation_calls, judge_calls, counted_tokens = V04.observed_attempt_usage(out_dir)
    require(
        (generation_calls, judge_calls, counted_tokens) == (3, 4, 90_100),
        "judge-compat-source-drift",
        "pre-amendment usage differs",
    )
    report = {
        "status": "ready" if auth_report["status"] == "authorized" else "pending-authorization",
        "amendment_id": COMPAT_ID,
        "protocol_sha256": auth_report["protocol_sha256"],
        "judge_compatibility_protocol_sha256": sha256_file(AMENDMENT_PATH),
        "authorization_status": auth_report["status"],
        "retained_source": source,
        "schema_compatibility": schema,
        "verified_arm_ids": sorted(manifests),
        "remaining_generation_calls": authorization["maximum_generation_calls"] - generation_calls,
        "remaining_judge_calls": authorization["maximum_judge_calls"] - judge_calls,
        "remaining_counted_tokens": authorization["token_or_cost_budget"]["maximum"] - counted_tokens,
        "model_execution_performed": False,
        "semantic_output_generated": False,
    }
    V04.write_atomic_json(recovery_root(out_dir) / "preflight-report.json", report)
    return report, 0


def run_recovery(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    global _ACTIVE_AMENDMENT
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    V04.scan_partial_artifacts(out_dir)
    auth_report, authorization, protocol = _authorization_context(
        args.authorization.resolve(), allow_pending=False
    )
    amendment = read_json(AMENDMENT_PATH)
    _ACTIVE_AMENDMENT = amendment
    require(
        protocol.get("protocol_version") == "0.5",
        "protocol-or-arm-drift",
        "Judge compatibility runner received another base protocol",
    )
    _validate_transport_schema()
    manifests = V04.verify_arm_set(args.arm_manifest, authorization)
    for manifest in manifests.values():
        staging = Path(manifest["host"]["execution_root"]).resolve().parent / "package"
        require(
            not staging.exists(),
            "isolation-evidence-missing",
            f"package staging still exists: {staging}",
        )
    verify_retained_source(out_dir, amendment, auth_report["protocol_sha256"])
    matrix = BASE.read_json(BASE.MATRIX_PATH)
    cases = V04.source_cases(matrix)
    batches = BASE.batch_plan(protocol, auth_report["protocol_sha256"])
    max_batches = int(authorization["maximum_committed_batches"])
    require(
        1 <= max_batches <= len(batches),
        "authority-or-evidence-regression",
        "authorized batch ceiling differs",
    )
    auth_source = args.auth_source.resolve()
    require(
        auth_source.is_file(),
        "authority-or-evidence-regression",
        "Codex auth source is unavailable",
    )
    BASE._configure_isolation(
        out_dir=out_dir,
        manifests=manifests,
        auth_source=auth_source,
    )
    generation_calls, judge_calls, counted_tokens = V04.observed_attempt_usage(out_dir)
    summary = BASE.committed_summary(out_dir, batches)
    previous_digest = summary["last_commit_digest"]
    committed = int(summary["committed_batches"])
    environments = {
        slot: V04.judge_environment(
            out_dir=out_dir,
            runtime_root=args.runtime_root.resolve(),
            auth_source=auth_source,
            slot=slot,
        )
        for slot in (1, 2)
    }
    rubric = BASE.read_json(BASE.JUDGE_RUBRIC)
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    state_path = recovery_root(out_dir) / "run-state.json"

    original_stream = V04.run_streamed
    original_schema = V04.JUDGE_SCHEMA
    original_base_schema = BASE.JUDGE_SCHEMA
    V04.run_streamed = BASE._sandboxed_run_streamed
    V04.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
    BASE.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
    active_batch: Mapping[str, Any] | None = None
    try:
        for batch in batches[committed:max_batches]:
            active_batch = batch
            generation_records: list[dict[str, Any]] = []
            for cell in batch["cells"]:
                record, new_calls, new_tokens = BASE.execute_generator_cell(
                    batch=batch,
                    cell=cell,
                    case=cases[cell["case_id"]],
                    manifest=manifests[cell["arm_id"]],
                    authorization=authorization,
                    protocol_sha256=auth_report["protocol_sha256"],
                    out_dir=out_dir,
                    timeout=args.timeout,
                    generation_calls_used=generation_calls,
                )
                generation_calls += new_calls
                counted_tokens += new_tokens
                generation_records.append(record)
                require(
                    counted_tokens <= authorization["token_or_cost_budget"]["maximum"],
                    "authority-or-evidence-regression",
                    "token ceiling reached",
                )
                V04.write_atomic_json(
                    state_path,
                    _state_payload(
                        status="generating-batch",
                        protocol_sha256=auth_report["protocol_sha256"],
                        authorization_digest=auth_report["authorization_digest"],
                        generation_calls=generation_calls,
                        judge_calls=judge_calls,
                        counted_tokens=counted_tokens,
                        committed_batches=committed,
                        active_batch=batch,
                    ),
                )
            require(
                {record["arm_id"] for record in generation_records} == set(BASE.ARM_ORDER),
                "protocol-or-arm-drift",
                "generated batch arm set differs",
            )

            judged: list[dict[str, Any]] = []
            for record in V04.judge_order(generation_records, seed):
                cell_id = str(record["cell_id"])
                case = cases[str(record["cell_key"]["case_id"])]
                candidate = Path(record["answer_path"]).read_text(encoding="utf-8")
                sensitive = {
                    str(Path(manifest[section][field]).resolve())
                    for manifest in manifests.values()
                    for section, field in (
                        ("host", "home"),
                        ("host", "execution_root"),
                        ("package", "root"),
                    )
                }
                require(
                    not V04.FORBIDDEN_BLINDING_LABEL.search(candidate)
                    and not any(path in candidate for path in sensitive),
                    "judge-environment-contamination",
                    "candidate exposes arm identity",
                )
                output_id = BASE.judge_identity(auth_report["protocol_sha256"], cell_id)
                raw_prompt = V04.user_prompt(case["source"])
                blinded_path = V04.write_blinded_input(
                    out_dir=out_dir,
                    output_id=output_id,
                    prompt=raw_prompt,
                    case=case,
                    candidate=candidate,
                )
                blinded_digest = str(BASE.read_json(blinded_path)["input_digest"])
                prompt = V04.judge_prompt(
                    rubric=rubric,
                    case=case,
                    prompt=raw_prompt,
                    candidate=candidate,
                    blinded_output_id=output_id,
                )
                needed_slots = [
                    slot
                    for slot in (1, 2)
                    if V04.existing_judge_record(out_dir, output_id, slot) is None
                ]
                new_calls_required = _new_judge_calls_required(
                    out_dir, output_id, needed_slots
                )
                require(
                    judge_calls + new_calls_required
                    <= authorization["maximum_judge_calls"],
                    "authority-or-evidence-regression",
                    "Judge call ceiling reached",
                )
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [
                        executor.submit(
                            compatible_judge_slot,
                            slot=slot,
                            output_id=output_id,
                            prompt=prompt,
                            blinded_input_digest=blinded_digest,
                            case=case,
                            environment=environments[slot],
                            authorization=authorization,
                            out_dir=out_dir,
                            timeout=args.timeout,
                        )
                        for slot in (1, 2)
                    ]
                    results = [future.result() for future in futures]
                records = [item[0] for item in results]
                for judge_record, new_calls, new_tokens in results:
                    judge_calls += new_calls
                    counted_tokens += new_tokens
                    judged.append(judge_record)
                require(
                    judge_calls <= authorization["maximum_judge_calls"]
                    and counted_tokens <= authorization["token_or_cost_budget"]["maximum"],
                    "authority-or-evidence-regression",
                    "Judge or token ceiling reached",
                )
                for receipt_path in BASE._judge_receipt_paths(out_dir, output_id, records):
                    BASE._verify_isolation_receipt(receipt_path)
                V04.write_atomic_json(
                    state_path,
                    _state_payload(
                        status="judging-batch",
                        protocol_sha256=auth_report["protocol_sha256"],
                        authorization_digest=auth_report["authorization_digest"],
                        generation_calls=generation_calls,
                        judge_calls=judge_calls,
                        counted_tokens=counted_tokens,
                        committed_batches=committed,
                        active_batch=batch,
                    ),
                )
            commit = BASE._write_batch_commit(
                out_dir=out_dir,
                batch=batch,
                protocol_sha256=auth_report["protocol_sha256"],
                authorization_digest=auth_report["authorization_digest"],
                previous_digest=previous_digest,
                generation_records=generation_records,
                judge_records=judged,
            )
            previous_digest = commit["commit_digest"]
            committed += 1
            V04.write_atomic_json(
                state_path,
                _state_payload(
                    status="batch-committed",
                    protocol_sha256=auth_report["protocol_sha256"],
                    authorization_digest=auth_report["authorization_digest"],
                    generation_calls=generation_calls,
                    judge_calls=judge_calls,
                    counted_tokens=counted_tokens,
                    committed_batches=committed,
                    active_batch=batch,
                ),
            )
            analysis_run = subprocess.run(
                [
                    "python3",
                    str(BASE.ANALYZER_V05),
                    "--run-dir",
                    str(out_dir),
                    "--authorization",
                    str(args.authorization.resolve()),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            require(
                analysis_run.returncode in (0, 3),
                "incremental-batch-integrity-failure",
                "incremental analysis failed after a committed batch: "
                + (analysis_run.stderr.strip() or analysis_run.stdout.strip()),
            )
            analysis = json.loads(analysis_run.stdout)
            require(
                analysis.get("status") != "human-adjudication-required",
                "human-adjudication-required",
                "the committed batch has unresolved binary Judge disagreements",
            )
    except (CompatibilityStop, BASE.EvaluationStop, V04.EvaluationStop, BASE.ISO.IsolationError) as exc:
        veto = getattr(exc, "veto_id", "isolation-evidence-missing")
        # Parallel futures may have finalized attempts before one future raised.  The
        # filesystem is authoritative, so never persist the stale pre-join counters.
        generation_calls, judge_calls, counted_tokens = V04.observed_attempt_usage(
            out_dir
        )
        V04.write_atomic_json(
            state_path,
            _state_payload(
                status="vetoed",
                protocol_sha256=auth_report["protocol_sha256"],
                authorization_digest=auth_report["authorization_digest"],
                generation_calls=generation_calls,
                judge_calls=judge_calls,
                counted_tokens=counted_tokens,
                committed_batches=committed,
                active_batch=active_batch,
                veto_id=veto,
                reason=str(exc),
            ),
        )
        raise CompatibilityStop(veto, str(exc)) from exc
    finally:
        V04.run_streamed = original_stream
        V04.JUDGE_SCHEMA = original_schema
        BASE.JUDGE_SCHEMA = original_base_schema
        _ACTIVE_AMENDMENT = None

    report = BASE.committed_summary(out_dir, batches)
    report.update(
        {
            "status": (
                "matched-complete"
                if committed == len(batches)
                else "authorized-batch-limit-reached"
            ),
            "amendment_id": COMPAT_ID,
            "protocol_sha256": auth_report["protocol_sha256"],
            "authorization_digest": auth_report["authorization_digest"],
            "generation_calls": generation_calls,
            "judge_calls": judge_calls,
            "counted_tokens": counted_tokens,
            "authorized_batch_ceiling": max_batches,
            "budget_expansion": False,
        }
    )
    V04.write_atomic_json(recovery_root(out_dir) / "summary.json", report)
    return report, 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--arm-manifest", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument(
        "--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, code = preflight(args) if args.preflight_only else run_recovery(args)
    except (
        OSError,
        json.JSONDecodeError,
        CompatibilityStop,
        RuntimeError,
    ) as exc:
        report = {
            "status": "vetoed",
            "veto_id": getattr(exc, "veto_id", "authority-or-evidence-regression"),
            "reason": str(exc),
        }
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
