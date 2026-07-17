#!/usr/bin/env python3
"""Complete frozen v0.4 with the OpenAI-compatible Judge schema.

The four original pre-sampling schema rejections remain immutable.  This wrapper
appends attempts 3/4 only for those two failed slots, then delegates the unchanged
workload and analysis to v0.4 with a schema-only compatible Judge call boundary.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import sys
import tempfile
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
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-judge-compat.1.json"
)
COMPAT_PROTOCOL = (
    BETA_ROOT / "protocols" / "evaluation-protocol-v0.4-judge-compat.1.json"
)
ORIGINAL_SCHEMA = BETA_ROOT / "fixtures" / "judge-output-v0.4.schema.json"
COMPATIBLE_SCHEMA = (
    BETA_ROOT / "fixtures" / "judge-output-v0.4-openai-compatible.schema.json"
)
RECOVERY_ANALYZER = RUNTIME_ROOT / "analyze_codex_evaluation_v04_recovery.py"
COMPAT_ID = "0.4-judge-compat.1"
FAILED_OUTPUT_ID = (
    "bd75595351da48405cd5eb84085714f1c8df1dbc01fe7b6bbdfa35b591c31712"
)
API_ERROR_FRAGMENT = "'uniqueItems' is not permitted"


def compat_root(out_dir: Path) -> Path:
    return out_dir / "recovery" / COMPAT_ID


def require(condition: bool, veto_id: str, reason: str) -> None:
    if not condition:
        raise base.EvaluationStop(veto_id, reason)


def copy_bound_source(source: Path, destination: Path, expected_sha256: str) -> None:
    require(source.is_file(), "judge-compat-source-drift", f"source is missing: {source}")
    require(
        base.sha256_file(source) == expected_sha256,
        "judge-compat-source-drift",
        f"source differs: {source}",
    )
    if destination.is_file():
        require(
            base.sha256_file(destination) == expected_sha256,
            "judge-compat-source-drift",
            f"source snapshot differs: {destination}",
        )
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.partial")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def verify_generation_source(
    out_dir: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    base_protocol: Mapping[str, Any],
    amendment: Mapping[str, Any],
) -> list[dict[str, str]]:
    matrix = base.read_json(base.MATRIX_PATH)
    cases = base.source_cases(matrix)
    protocol_sha256 = amendment["base_binding"]["protocol_sha256"]
    receipts: list[dict[str, str]] = []
    for cell in base.expected_cells(base_protocol, "smoke"):
        case = cases[str(cell["case_id"])]
        manifest = manifests[str(cell["arm_id"])]
        cell_id, _key = base.cell_identity(cell, case, manifest, protocol_sha256)
        record = base.completed_cell(out_dir, cell_id)
        require(
            record is not None,
            "judge-compat-source-drift",
            f"retained smoke cell is missing: {cell_id}",
        )
        path = out_dir / "cells" / cell_id / "record.json"
        receipts.append(
            {
                "cell_id": cell_id,
                "record_digest": str(record["record_digest"]),
                "file_sha256": base.sha256_file(path),
            }
        )
    receipts.sort(key=lambda item: item["cell_id"])
    source = amendment["retained_source_run"]
    require(
        len(receipts) == source["completed_generation_outputs"] == 15,
        "judge-compat-source-drift",
        "retained smoke cell count differs",
    )
    require(
        base.canonical_sha256(receipts) == source["generation_cell_set_digest"],
        "judge-compat-source-drift",
        "retained smoke cell set differs",
    )
    return receipts


def load_original_attempt(
    out_dir: Path,
    amendment: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    slot = int(receipt["slot"])
    number = int(receipt["attempt"])
    root = (
        out_dir
        / "judge-attempts"
        / FAILED_OUTPUT_ID
        / f"slot-{slot}"
        / f"attempt-{number:02d}"
    )
    attempt_path = root / "attempt.json"
    events_path = root / "events.jsonl"
    stderr_path = root / "stderr.txt"
    output_path = root / "judge-output.json"
    require(
        attempt_path.is_file() and events_path.is_file() and stderr_path.is_file(),
        "judge-compat-source-drift",
        f"original Judge attempt is incomplete: slot-{slot}/attempt-{number}",
    )
    require(
        base.sha256_file(attempt_path) == receipt["attempt_file_sha256"],
        "judge-compat-source-drift",
        f"original Judge attempt file differs: slot-{slot}/attempt-{number}",
    )
    require(
        base.sha256_file(events_path) == receipt["events_sha256"],
        "judge-compat-source-drift",
        f"original Judge events differ: slot-{slot}/attempt-{number}",
    )
    attempt = base.read_json(attempt_path)
    unsigned = dict(attempt)
    digest = unsigned.pop("attempt_digest", None)
    require(
        digest == base.canonical_sha256(unsigned) == receipt["attempt_digest"],
        "judge-compat-source-drift",
        f"original Judge attempt digest differs: slot-{slot}/attempt-{number}",
    )
    source = amendment["retained_source_run"]["failure_evidence"]
    events = events_path.read_text(encoding="utf-8")
    require(
        attempt.get("blinded_output_id") == FAILED_OUTPUT_ID
        and attempt.get("judge_slot") == slot
        and attempt.get("attempt") == number,
        "judge-compat-source-drift",
        "original Judge attempt identity differs",
    )
    require(
        attempt.get("returncode") == source["returncode"]
        and attempt.get("timed_out") is source["timed_out"]
        and attempt.get("output_present") is source["output_present"]
        and attempt.get("usage") is None
        and attempt.get("counted_tokens") == source["counted_tokens_per_attempt"]
        and not output_path.exists(),
        "judge-compat-source-drift",
        "original Judge failure outcome differs",
    )
    require(
        API_ERROR_FRAGMENT in events and source["api_error"] in events,
        "judge-compat-source-drift",
        "original API schema rejection is missing",
    )
    return attempt


def verify_failure_packets(
    out_dir: Path, amendment: Mapping[str, Any]
) -> list[dict[str, Any]]:
    source = amendment["retained_source_run"]
    observed: list[dict[str, Any]] = []
    failed_by_slot = {
        slot: [
            item
            for item in source["failed_attempts"]
            if int(item["slot"]) == slot
        ]
        for slot in (1, 2)
    }
    for receipt in source["failure_packets"]:
        slot = int(receipt["slot"])
        path = (
            out_dir
            / "human-judge-failure-packets"
            / f"{FAILED_OUTPUT_ID}-slot-{slot}.json"
        )
        require(
            path.is_file() and base.sha256_file(path) == receipt["file_sha256"],
            "judge-compat-source-drift",
            f"original Judge failure packet differs: slot-{slot}",
        )
        packet = base.read_json(path)
        unsigned = dict(packet)
        packet_digest = unsigned.pop("packet_digest", None)
        require(
            packet_digest
            == base.canonical_sha256(unsigned)
            == receipt["packet_digest"],
            "judge-compat-source-drift",
            f"original Judge failure packet digest differs: slot-{slot}",
        )
        require(
            packet.get("blinded_output_id") == FAILED_OUTPUT_ID
            and packet.get("failed_judge_slot") == slot
            and packet.get("judge_schema_sha256") == base.sha256_file(ORIGINAL_SCHEMA)
            and [item.get("attempt_digest") for item in packet.get("attempts", [])]
            == [item["attempt_digest"] for item in failed_by_slot[slot]],
            "judge-compat-source-drift",
            f"original Judge failure packet content differs: slot-{slot}",
        )
        observed.append(dict(receipt))
    require(
        base.canonical_sha256(observed) == source["judge_failure_packet_set_digest"],
        "judge-compat-source-drift",
        "original Judge failure packet set differs",
    )
    return observed


def verify_original_failures(
    out_dir: Path, amendment: Mapping[str, Any]
) -> dict[int, list[dict[str, Any]]]:
    source = amendment["retained_source_run"]
    require(
        base.canonical_sha256(source["failed_attempts"])
        == source["judge_attempt_set_digest"],
        "judge-compat-source-drift",
        "declared original Judge attempt set differs",
    )
    attempts: dict[int, list[dict[str, Any]]] = {1: [], 2: []}
    for receipt in source["failed_attempts"]:
        attempts[int(receipt["slot"])].append(
            load_original_attempt(out_dir, amendment, receipt)
        )
    verify_failure_packets(out_dir, amendment)
    return attempts


def ensure_source_snapshot(out_dir: Path, amendment: Mapping[str, Any]) -> dict[str, Any]:
    source = amendment["retained_source_run"]
    root = compat_root(out_dir) / "pre-amendment"
    receipt_path = root / "receipt.json"
    copies = {
        "run-state.json": (
            out_dir / "run-state.json",
            source["run_state_sha256"],
        ),
        "generation-metadata-repair.json": (
            out_dir / "recovery" / "0.4-recovery.1" / "metadata-repair.json",
            source["generation_metadata_repair_sha256"],
        ),
        "generation-recovery-stop-report.json": (
            out_dir / "recovery" / "0.4-recovery.1" / "stop-report.json",
            source["generation_recovery_stop_report_sha256"],
        ),
    }
    for packet in source["failure_packets"]:
        slot = int(packet["slot"])
        copies[f"judge-failure-slot-{slot}.json"] = (
            out_dir
            / "human-judge-failure-packets"
            / f"{FAILED_OUTPUT_ID}-slot-{slot}.json",
            packet["file_sha256"],
        )
    if receipt_path.is_file():
        receipt = base.read_json(receipt_path)
        unsigned = dict(receipt)
        digest = unsigned.pop("receipt_digest", None)
        require(
            digest == base.canonical_sha256(unsigned),
            "judge-compat-source-drift",
            "Judge compatibility source snapshot digest differs",
        )
        for name, (_source_path, expected_sha) in copies.items():
            require(
                (root / name).is_file()
                and base.sha256_file(root / name) == expected_sha,
                "judge-compat-source-drift",
                f"Judge compatibility source snapshot differs: {name}",
            )
        return receipt
    require(
        base.read_json(out_dir / "run-state.json").get("state_digest")
        == source["run_state_digest"],
        "judge-compat-source-drift",
        "pre-compatibility run-state digest differs",
    )
    require(
        base.existing_judge_record(out_dir, FAILED_OUTPUT_ID, 1) is None
        and base.existing_judge_record(out_dir, FAILED_OUTPUT_ID, 2) is None,
        "judge-compat-source-drift",
        "Judge verdict predates the compatibility source snapshot",
    )
    for name, (source_path, expected_sha) in copies.items():
        copy_bound_source(source_path, root / name, expected_sha)
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-v0.4-judge-compat-source-snapshot-v0.1",
        "amendment_id": COMPAT_ID,
        "base_protocol_sha256": amendment["base_binding"]["protocol_sha256"],
        "source_files": {
            name: expected_sha for name, (_path, expected_sha) in sorted(copies.items())
        },
        "source_judge_attempt_set_digest": source["judge_attempt_set_digest"],
        "source_failure_packet_set_digest": source["judge_failure_packet_set_digest"],
        "snapshotted_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    receipt["receipt_digest"] = base.canonical_sha256(receipt)
    base.write_atomic_json(receipt_path, receipt)
    return receipt


def decode_attempt_output(
    root: Path, attempt: Mapping[str, Any], case: Mapping[str, Any]
) -> tuple[dict[str, Any] | None, str]:
    output_path = root / "judge-output.json"
    raw = output_path.read_text(encoding="utf-8") if output_path.is_file() else ""
    if hashlib.sha256(raw.encode("utf-8")).hexdigest() != attempt.get("output_sha256"):
        raise base.EvaluationStop(
            "untraceable-or-partial-artifact", "compatible Judge output digest differs"
        )
    try:
        decoded = json.loads(raw)
        if not isinstance(decoded, Mapping):
            raise ValueError("judge output is not an object")
        normalized = base.validate_judge_output(decoded, case)
    except (json.JSONDecodeError, TypeError, ValueError):
        normalized = None
    return normalized, raw


def load_compatible_attempt(
    root: Path,
    *,
    output_id: str,
    slot: int,
    number: int,
    case: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
    attempt_path = root / "attempt.json"
    require(
        attempt_path.is_file()
        and (root / "events.jsonl").is_file()
        and (root / "stderr.txt").is_file(),
        "untraceable-or-partial-artifact",
        f"compatible Judge attempt is incomplete: {output_id}/slot-{slot}/{number}",
    )
    attempt = base.read_json(attempt_path)
    unsigned = dict(attempt)
    digest = unsigned.pop("attempt_digest", None)
    require(
        digest == base.canonical_sha256(unsigned),
        "untraceable-or-partial-artifact",
        "compatible Judge attempt digest differs",
    )
    require(
        attempt.get("blinded_output_id") == output_id
        and attempt.get("judge_slot") == slot
        and attempt.get("attempt") == number
        and attempt.get("judge_schema_sha256") == base.sha256_file(COMPATIBLE_SCHEMA)
        and attempt.get("original_judge_schema_sha256")
        == base.sha256_file(ORIGINAL_SCHEMA)
        and attempt.get("judge_compatibility_amendment_id") == COMPAT_ID,
        "untraceable-or-partial-artifact",
        "compatible Judge attempt binding differs",
    )
    require(
        base.sha256_file(root / "events.jsonl") == attempt.get("events_sha256")
        and base.sha256_file(root / "stderr.txt") == attempt.get("stderr_sha256"),
        "untraceable-or-partial-artifact",
        "compatible Judge attempt stream differs",
    )
    normalized, raw = decode_attempt_output(root, attempt, case)
    return attempt, normalized, raw


def execute_compatible_attempt(
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
) -> tuple[dict[str, Any], dict[str, Any] | None, str]:
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
    capture = base.run_streamed(
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
    evidence = base.event_evidence(events)
    raw = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    normalized: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        decoded = json.loads(raw)
        if not isinstance(decoded, Mapping):
            raise ValueError("judge output is not an object")
        normalized = base.validate_judge_output(decoded, case)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        parse_error = str(exc)
    tokens = base.token_total(evidence["usage"])
    attempt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-attempt-v0.4",
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
        "judge_schema_sha256": base.sha256_file(COMPATIBLE_SCHEMA),
        "original_judge_schema_sha256": base.sha256_file(ORIGINAL_SCHEMA),
        "judge_compatibility_amendment_id": COMPAT_ID,
        "schema_compatibility_only": True,
    }
    attempt["attempt_digest"] = base.canonical_sha256(attempt)
    (temp_dir / "attempt.json").write_text(
        json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    destination = parent / f"attempt-{attempt_number:02d}"
    base.finalize_attempt(temp_dir, destination)
    require(
        not evidence["loaded_commands"],
        "judge-environment-contamination",
        f"Judge slot {slot} used a tool for {output_id}",
    )
    return attempt, normalized, raw


def successful_attempt(attempt: Mapping[str, Any], normalized: object) -> bool:
    return bool(
        attempt.get("returncode") == 0
        and attempt.get("timed_out") is False
        and attempt.get("output_present") is True
        and attempt.get("parse_error") is None
        and isinstance(normalized, Mapping)
    )


def write_compatible_record(
    *,
    out_dir: Path,
    output_id: str,
    slot: int,
    attempt: Mapping[str, Any],
    normalized: Mapping[str, Any],
    history: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-record-v0.4",
        "blinded_output_id": output_id,
        "judge_slot": slot,
        "attempt": attempt["attempt"],
        "attempt_digest": attempt["attempt_digest"],
        "environment_digest": attempt["environment_digest"],
        "blinded_input_digest": attempt["blinded_input_digest"],
        "judge_prompt_sha256": attempt["judge_prompt_sha256"],
        "verdict": dict(normalized),
        "usage": attempt["usage"],
        "counted_tokens": attempt["counted_tokens"],
        "judge_schema_sha256": base.sha256_file(COMPATIBLE_SCHEMA),
        "original_judge_schema_sha256": base.sha256_file(ORIGINAL_SCHEMA),
        "judge_compatibility_amendment_id": COMPAT_ID,
        "judge_attempt_history": [
            {
                "attempt": item["attempt"],
                "attempt_digest": item["attempt_digest"],
                "returncode": item["returncode"],
                "timed_out": item["timed_out"],
                "output_present": item["output_present"],
                "schema": (
                    "openai-compatible-v0.4"
                    if item.get("judge_compatibility_amendment_id") == COMPAT_ID
                    else "original-v0.4"
                ),
            }
            for item in history
        ],
    }
    record["record_digest"] = base.canonical_sha256(record)
    base.write_atomic_json(
        out_dir / "judge-records" / output_id / f"judge-{slot}.json", record
    )
    return record


def validate_compatible_record(
    *,
    out_dir: Path,
    output_id: str,
    slot: int,
    case: Mapping[str, Any],
    expected_input_digest: str,
    expected_prompt_digest: str,
    environment_digest: str,
) -> dict[str, Any] | None:
    record = base.existing_judge_record(out_dir, output_id, slot)
    if record is None:
        return None
    require(
        record.get("judge_schema_sha256") == base.sha256_file(COMPATIBLE_SCHEMA)
        and record.get("original_judge_schema_sha256")
        == base.sha256_file(ORIGINAL_SCHEMA)
        and record.get("judge_compatibility_amendment_id") == COMPAT_ID,
        "untraceable-or-partial-artifact",
        "compatible Judge record schema binding differs",
    )
    require(
        record.get("blinded_input_digest") == expected_input_digest
        and record.get("judge_prompt_sha256") == expected_prompt_digest
        and record.get("environment_digest") == environment_digest,
        "judge-environment-contamination",
        "compatible Judge record input/environment differs",
    )
    attempt_number = int(record["attempt"])
    root = (
        out_dir
        / "judge-attempts"
        / output_id
        / f"slot-{slot}"
        / f"attempt-{attempt_number:02d}"
    )
    attempt, normalized, _raw = load_compatible_attempt(
        root,
        output_id=output_id,
        slot=slot,
        number=attempt_number,
        case=case,
    )
    require(
        successful_attempt(attempt, normalized) and record.get("verdict") == normalized,
        "untraceable-or-partial-artifact",
        "compatible Judge verdict differs",
    )
    return record


def write_terminal_packet(
    *,
    path: Path,
    output_id: str,
    slot: int,
    blinded_input_digest: str,
    attempts: Iterable[Mapping[str, Any]],
) -> None:
    packet: dict[str, Any] = {
        "schema_version": "mindthus-beta2-judge-compat-failure-packet-v0.1",
        "amendment_id": COMPAT_ID,
        "blinded_output_id": output_id,
        "failed_judge_slot": slot,
        "adjudicator": "William",
        "blinded_input_digest": blinded_input_digest,
        "original_judge_schema_sha256": base.sha256_file(ORIGINAL_SCHEMA),
        "compatible_judge_schema_sha256": base.sha256_file(COMPATIBLE_SCHEMA),
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
            "the authorized v0.4 compatibility attempts are exhausted; no further "
            "semantic retry is permitted without William"
        ),
    }
    packet["packet_digest"] = base.canonical_sha256(packet)
    base.write_atomic_json(path, packet)


def ensure_failed_slot(
    *,
    out_dir: Path,
    slot: int,
    original_attempts: list[dict[str, Any]],
    prompt: str,
    blinded_input_digest: str,
    case: Mapping[str, Any],
    environment: Mapping[str, Any],
    authorization: Mapping[str, Any],
    timeout: int,
    allow_model_execution: bool,
) -> tuple[dict[str, Any] | None, int, int]:
    prompt_digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    for attempt in original_attempts:
        require(
            attempt.get("environment_digest") == environment["environment_digest"]
            and attempt.get("blinded_input_digest") == blinded_input_digest
            and attempt.get("judge_prompt_sha256") == prompt_digest,
            "judge-compat-source-drift",
            f"original Judge binding differs: slot-{slot}",
        )
    existing = validate_compatible_record(
        out_dir=out_dir,
        output_id=FAILED_OUTPUT_ID,
        slot=slot,
        case=case,
        expected_input_digest=blinded_input_digest,
        expected_prompt_digest=prompt_digest,
        environment_digest=str(environment["environment_digest"]),
    )
    if existing is not None:
        history = existing.get("judge_attempt_history")
        require(
            isinstance(history, list)
            and [item.get("attempt") for item in history]
            == list(range(1, int(existing["attempt"]) + 1)),
            "untraceable-or-partial-artifact",
            f"failed-slot Judge history differs: slot-{slot}",
        )
        return existing, 0, 0
    parent = base.attempt_parent(out_dir, "judge", f"{FAILED_OUTPUT_ID}/slot-{slot}")
    observed = sorted(path.name for path in parent.glob("attempt-*"))
    require(
        observed
        in (
            ["attempt-01", "attempt-02"],
            ["attempt-01", "attempt-02", "attempt-03"],
            ["attempt-01", "attempt-02", "attempt-03", "attempt-04"],
        ),
        "untraceable-or-partial-artifact",
        f"failed-slot Judge attempt set differs: slot-{slot}: {observed}",
    )
    calls = 0
    counted_tokens = 0
    history: list[dict[str, Any]] = [*original_attempts]
    for number in (3, 4):
        root = parent / f"attempt-{number:02d}"
        if root.is_dir():
            attempt, normalized, _raw = load_compatible_attempt(
                root,
                output_id=FAILED_OUTPUT_ID,
                slot=slot,
                number=number,
                case=case,
            )
        elif not allow_model_execution:
            return None, calls, counted_tokens
        else:
            attempt, normalized, _raw = execute_compatible_attempt(
                parent=parent,
                attempt_number=number,
                slot=slot,
                output_id=FAILED_OUTPUT_ID,
                prompt=prompt,
                blinded_input_digest=blinded_input_digest,
                case=case,
                environment=environment,
                authorization=authorization,
                timeout=timeout,
            )
            calls += 1
            counted_tokens += int(attempt.get("counted_tokens") or 0)
        history.append(attempt)
        if successful_attempt(attempt, normalized):
            assert isinstance(normalized, Mapping)
            return (
                write_compatible_record(
                    out_dir=out_dir,
                    output_id=FAILED_OUTPUT_ID,
                    slot=slot,
                    attempt=attempt,
                    normalized=normalized,
                    history=history,
                ),
                calls,
                counted_tokens,
            )
        if number == 3:
            continue
        packet_path = compat_root(out_dir) / "failure-packets" / f"slot-{slot}.json"
        write_terminal_packet(
            path=packet_path,
            output_id=FAILED_OUTPUT_ID,
            slot=slot,
            blinded_input_digest=blinded_input_digest,
            attempts=history,
        )
        raise base.EvaluationStop(
            "v0.4-judge-compatibility-exhausted",
            f"Judge slot {slot} exhausted attempts 3/4; packet: {packet_path}",
        )
    raise AssertionError("unreachable failed Judge compatibility loop")


def compatible_standard_slot(
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
    prompt_digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    existing = validate_compatible_record(
        out_dir=out_dir,
        output_id=output_id,
        slot=slot,
        case=case,
        expected_input_digest=blinded_input_digest,
        expected_prompt_digest=prompt_digest,
        environment_digest=str(environment["environment_digest"]),
    )
    if existing is not None:
        return existing, 0, 0
    parent = base.attempt_parent(out_dir, "judge", f"{output_id}/slot-{slot}")
    require(
        not any(parent.glob("attempt-*")),
        "untraceable-or-partial-artifact",
        f"Judge attempt exists without an atomic record: {output_id}/slot-{slot}",
    )
    calls = 0
    counted_tokens = 0
    history: list[dict[str, Any]] = []
    for number in (1, 2):
        attempt, normalized, _raw = execute_compatible_attempt(
            parent=parent,
            attempt_number=number,
            slot=slot,
            output_id=output_id,
            prompt=prompt,
            blinded_input_digest=blinded_input_digest,
            case=case,
            environment=environment,
            authorization=authorization,
            timeout=timeout,
        )
        calls += 1
        counted_tokens += int(attempt.get("counted_tokens") or 0)
        history.append(attempt)
        if successful_attempt(attempt, normalized):
            assert isinstance(normalized, Mapping)
            return (
                write_compatible_record(
                    out_dir=out_dir,
                    output_id=output_id,
                    slot=slot,
                    attempt=attempt,
                    normalized=normalized,
                    history=history,
                ),
                calls,
                counted_tokens,
            )
        if number == 1:
            continue
        packet_path = (
            out_dir / "human-judge-failure-packets" / f"{output_id}-slot-{slot}.json"
        )
        write_terminal_packet(
            path=packet_path,
            output_id=output_id,
            slot=slot,
            blinded_input_digest=blinded_input_digest,
            attempts=history,
        )
        raise base.EvaluationStop(
            "v0.4-judge-compatibility-exhausted",
            f"Judge slot {slot} exhausted its frozen two attempts; packet: {packet_path}",
        )
    raise AssertionError("unreachable compatible Judge loop")


def failed_judge_context(
    *,
    out_dir: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    base_protocol: Mapping[str, Any],
    amendment: Mapping[str, Any],
    runtime_root: Path,
    auth_source: Path,
) -> tuple[dict[str, Any], str, str, dict[int, dict[str, Any]]]:
    receipts = verify_generation_source(out_dir, manifests, base_protocol, amendment)
    matching = [
        item
        for item in receipts
        if base.judge_identity(
            amendment["base_binding"]["protocol_sha256"], item["cell_id"]
        )
        == FAILED_OUTPUT_ID
    ]
    require(
        len(matching) == 1,
        "judge-compat-source-drift",
        "failed blinded output does not map to exactly one retained smoke cell",
    )
    record = base.completed_cell(out_dir, matching[0]["cell_id"])
    assert record is not None
    matrix = base.read_json(base.MATRIX_PATH)
    cases = base.source_cases(matrix)
    case = cases[str(record["cell_key"]["case_id"])]
    candidate = Path(record["answer_path"]).read_text(encoding="utf-8")
    raw_prompt = base.user_prompt(case["source"])
    blinded_path = base.write_blinded_input(
        out_dir=out_dir,
        output_id=FAILED_OUTPUT_ID,
        prompt=raw_prompt,
        case=case,
        candidate=candidate,
    )
    blinded_digest = str(base.read_json(blinded_path)["input_digest"])
    prompt = base.judge_prompt(
        rubric=base.read_json(base.JUDGE_RUBRIC),
        case=case,
        prompt=raw_prompt,
        candidate=candidate,
        blinded_output_id=FAILED_OUTPUT_ID,
    )
    require(
        auth_source.is_file(),
        "judge-environment-contamination",
        "Codex auth source is unavailable",
    )
    environments = {
        slot: base.judge_environment(
            out_dir=out_dir,
            runtime_root=runtime_root,
            auth_source=auth_source,
            slot=slot,
        )
        for slot in (1, 2)
    }
    return case, prompt, blinded_digest, environments


def ensure_failed_records(
    *,
    out_dir: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    base_protocol: Mapping[str, Any],
    amendment: Mapping[str, Any],
    authorization: Mapping[str, Any],
    runtime_root: Path,
    auth_source: Path,
    timeout: int,
    allow_model_execution: bool,
) -> tuple[int, int, int]:
    original = verify_original_failures(out_dir, amendment)
    ensure_source_snapshot(out_dir, amendment)
    case, prompt, blinded_digest, environments = failed_judge_context(
        out_dir=out_dir,
        manifests=manifests,
        base_protocol=base_protocol,
        amendment=amendment,
        runtime_root=runtime_root,
        auth_source=auth_source,
    )
    generation_calls, judge_calls, counted_tokens = base.observed_attempt_usage(out_dir)
    require(
        16 <= generation_calls <= authorization["maximum_generation_calls"],
        "authority-or-evidence-regression",
        "generation call count falls outside the cumulative v0.4 authority",
    )
    needed_ceiling = sum(
        0
        if base.existing_judge_record(out_dir, FAILED_OUTPUT_ID, slot)
        else 2
        for slot in (1, 2)
    )
    require(
        judge_calls + needed_ceiling <= authorization["maximum_judge_calls"],
        "authority-or-evidence-regression",
        "Judge compatibility call ceiling would be exceeded",
    )
    if not allow_model_execution:
        for slot in (1, 2):
            ensure_failed_slot(
                out_dir=out_dir,
                slot=slot,
                original_attempts=original[slot],
                prompt=prompt,
                blinded_input_digest=blinded_digest,
                case=case,
                environment=environments[slot],
                authorization=authorization,
                timeout=timeout,
                allow_model_execution=False,
            )
        return 0, 0, 0
    futures: list[concurrent.futures.Future[tuple[dict[str, Any] | None, int, int]]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for slot in (1, 2):
            futures.append(
                executor.submit(
                    ensure_failed_slot,
                    out_dir=out_dir,
                    slot=slot,
                    original_attempts=original[slot],
                    prompt=prompt,
                    blinded_input_digest=blinded_digest,
                    case=case,
                    environment=environments[slot],
                    authorization=authorization,
                    timeout=timeout,
                    allow_model_execution=True,
                )
            )
        results = [future.result() for future in futures]
    require(
        all(record is not None for record, _calls, _tokens in results),
        "untraceable-or-partial-artifact",
        "compatible failed-slot Judge records are incomplete",
    )
    new_calls = sum(calls for _record, calls, _tokens in results)
    new_tokens = sum(tokens for _record, _calls, tokens in results)
    require(
        counted_tokens + new_tokens <= authorization["token_or_cost_budget"]["maximum"],
        "authority-or-evidence-regression",
        "v0.4 token ceiling reached during Judge compatibility recovery",
    )
    return 2, new_calls, new_tokens


def run_compatibility(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base.scan_partial_artifacts(out_dir)
    auth_report, authorization, base_protocol = base.authorized_context(
        args.authorization.resolve()
    )
    amendment = base.read_json(COMPAT_PROTOCOL)
    require(
        auth_report.get("judge_compatibility_protocol_sha256")
        == base.sha256_file(COMPAT_PROTOCOL),
        "authority-or-evidence-regression",
        "Judge compatibility authorization differs",
    )
    manifests = base.verify_arm_set(
        [path.resolve() for path in args.arm_manifest], authorization
    )
    base.JUDGE_SCHEMA = COMPATIBLE_SCHEMA
    recovered_records, new_calls, new_tokens = ensure_failed_records(
        out_dir=out_dir,
        manifests=manifests,
        base_protocol=base_protocol,
        amendment=amendment,
        authorization=authorization,
        runtime_root=args.runtime_root.resolve(),
        auth_source=args.auth_source.resolve(),
        timeout=args.timeout,
        allow_model_execution=not args.preflight_only,
    )
    if args.preflight_only:
        return {
            "status": "ready",
            "amendment_id": COMPAT_ID,
            "source_generation_outputs": 15,
            "retained_failed_judge_attempts": 4,
            "compatible_failed_slot_records_already_complete": recovered_records,
            "model_execution_performed": False,
            "next_phase": args.phase,
        }, 0
    base.run_judge_slot = compatible_standard_slot
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
    base.write_atomic_json(
        out_dir / f"{args.phase}-analysis.base-v0.4-judge-compat.json", base_report
    )
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
        label=f"{args.phase} Judge-compatible recovery analysis",
    )
    amended_report["judge_compatibility_amendment_id"] = COMPAT_ID
    amended_report["judge_schema_compatibility_only"] = True
    amended_report["retained_pre_sampling_schema_rejections"] = 4
    base.write_atomic_json(out_dir / f"{args.phase}-analysis.json", amended_report)
    completion: dict[str, Any] = {
        "schema_version": "mindthus-beta2-v0.4-judge-compat-completion-v0.1",
        "amendment_id": COMPAT_ID,
        "phase": args.phase,
        "base_runner_status": base_report.get("status"),
        "amended_analysis_status": amended_report.get("status"),
        "failed_slot_records_completed": recovered_records,
        "compatibility_recovery_calls_this_invocation": new_calls,
        "compatibility_recovery_counted_tokens_this_invocation": new_tokens,
        "source_snapshot_path": str(compat_root(out_dir) / "pre-amendment"),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    completion["completion_digest"] = base.canonical_sha256(completion)
    base.write_atomic_json(
        compat_root(out_dir) / f"{args.phase}-completion.json", completion
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
    parser.add_argument(
        "--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json"
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if args.timeout != 1800:
        parser.error("the frozen Judge compatibility timeout is exactly 1800 seconds")
    return args


def main() -> int:
    args = parse_args()
    try:
        report, code = run_compatibility(args)
    except base.EvaluationStop as exc:
        report = {
            "status": "stopped",
            "amendment_id": COMPAT_ID,
            "veto_id": exc.veto_id,
            "reason": exc.reason,
        }
        code = 2
        if args.out_dir.exists():
            base.write_atomic_json(
                compat_root(args.out_dir.resolve()) / "stop-report.json", report
            )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report = {"status": "blocked", "amendment_id": COMPAT_ID, "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
