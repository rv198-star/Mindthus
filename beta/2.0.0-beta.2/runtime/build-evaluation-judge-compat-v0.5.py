#!/usr/bin/env python3
"""Build the additive v0.5 Judge transport compatibility amendment on stdout."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
BASE_PROTOCOL = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.json"
BASE_LOCK = BETA_ROOT / "protocols" / "evaluation-protocol-v0.5.lock.json"
BASE_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.json"
ORIGINAL_SCHEMA = BETA_ROOT / "fixtures" / "judge-output-v0.4.schema.json"
COMPATIBLE_SCHEMA = (
    BETA_ROOT / "fixtures" / "judge-output-v0.4-openai-compatible.schema.json"
)
DEFAULT_SOURCE_RUN = (
    REPO_ROOT
    / ".tplan"
    / "missions"
    / "mindthus-beta2-evaluation"
    / "artifacts"
    / "real-v05-smoke-f9bc7232"
    / "run"
)
DEPENDENCIES = [
    BASE_PROTOCOL,
    BASE_LOCK,
    BASE_AUTHORIZATION,
    ORIGINAL_SCHEMA,
    COMPATIBLE_SCHEMA,
    BETA_ROOT / "runtime" / "run_real_codex_evaluation_v05.py",
    BETA_ROOT / "runtime" / "analyze_incremental_v05.py",
    BETA_ROOT / "runtime" / "run_real_codex_evaluation_v05_judge_compat.py",
    Path(__file__).resolve(),
    BETA_ROOT / "runtime" / "freeze-evaluation-judge-compat-v0.5.py",
    BETA_ROOT / "runtime" / "build-execution-authorization-v0.5-judge-compat.py",
    BETA_ROOT / "runtime" / "validate-execution-authorization-v0.5-judge-compat.py",
]


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def display(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve()))


def signed_digest(path: Path, field: str) -> str:
    payload = read_json(path)
    unsigned = dict(payload)
    digest = unsigned.pop(field, None)
    if digest != canonical_sha256(unsigned):
        raise ValueError(f"signed digest differs: {path}")
    return str(digest)


def source_receipt(source_run: Path) -> dict[str, Any]:
    cells: list[dict[str, Any]] = []
    for path in sorted(source_run.glob("cells/*/record.json"), key=str):
        record = read_json(path)
        isolation_path = Path(str(record["isolation_receipt"]["path"]))
        isolation = read_json(isolation_path)
        cells.append(
            {
                "cell_id": record["cell_id"],
                "arm_id": record["arm_id"],
                "record_digest": record["record_digest"],
                "record_file_sha256": sha256_file(path),
                "answer_sha256": record["answer_sha256"],
                "counted_tokens": record["counted_tokens"],
                "isolation_receipt_digest": isolation["receipt_digest"],
                "isolation_receipt_file_sha256": sha256_file(isolation_path),
            }
        )
    cells.sort(key=lambda item: str(item["cell_id"]))
    if len(cells) != 3:
        raise ValueError(f"expected three retained cells, observed {len(cells)}")

    attempts: list[dict[str, Any]] = []
    output_ids: set[str] = set()
    for path in sorted(source_run.glob("judge-attempts/**/attempt.json"), key=str):
        attempt = read_json(path)
        output_id = str(attempt["blinded_output_id"])
        output_ids.add(output_id)
        slot = int(attempt["judge_slot"])
        number = int(attempt["attempt"])
        root = path.parent
        isolation_path = (
            source_run
            / "isolation-receipts"
            / "judge"
            / output_id
            / f"slot-{slot}"
            / f"attempt-{number:02d}.json"
        )
        isolation = read_json(isolation_path)
        attempts.append(
            {
                "slot": slot,
                "attempt": number,
                "attempt_digest": attempt["attempt_digest"],
                "attempt_file_sha256": sha256_file(path),
                "events_sha256": sha256_file(root / "events.jsonl"),
                "stderr_sha256": sha256_file(root / "stderr.txt"),
                "isolation_receipt_path": display(isolation_path),
                "isolation_receipt_digest": isolation["receipt_digest"],
                "isolation_receipt_file_sha256": sha256_file(isolation_path),
            }
        )
    attempts.sort(key=lambda item: (int(item["slot"]), int(item["attempt"])))
    if len(attempts) != 4 or len(output_ids) != 1:
        raise ValueError("expected four failed Judge attempts for one output")
    output_id = next(iter(output_ids))

    packets: list[dict[str, Any]] = []
    for slot in (1, 2):
        path = source_run / "human-judge-failure-packets" / f"{output_id}-slot-{slot}.json"
        packet = read_json(path)
        packets.append(
            {
                "slot": slot,
                "packet_digest": packet["packet_digest"],
                "file_sha256": sha256_file(path),
            }
        )

    state_path = source_run / "run-state-v0.5.json"
    state = read_json(state_path)
    judge_input_path = source_run / "judge-inputs" / f"{output_id}.json"
    judge_input = read_json(judge_input_path)
    source: dict[str, Any] = {
        "path": display(source_run),
        "protocol_sha256": state["protocol_sha256"],
        "authorization_digest": state["authorization_digest"],
        "batch_id": state["active_batch_id"],
        "batch_index": state["active_batch_index"],
        "case_id": "b2-dev-owner-3l5s",
        "generation_calls": 3,
        "completed_generation_outputs": 3,
        "judge_attempts": 4,
        "completed_judge_records": 0,
        "committed_batches": 0,
        "known_counted_tokens": 90_100,
        "run_state_file_sha256": sha256_file(state_path),
        "run_state_digest": signed_digest(state_path, "state_digest"),
        "generation_cells": cells,
        "generation_cell_set_digest": canonical_sha256(cells),
        "failed_output_id": output_id,
        "failed_judge_attempts": attempts,
        "failed_judge_attempt_set_digest": canonical_sha256(attempts),
        "failure_packets": packets,
        "failure_packet_set_digest": canonical_sha256(packets),
        "judge_input_file_sha256": sha256_file(judge_input_path),
        "judge_input_digest": judge_input["input_digest"],
        "failure_evidence": {
            "stage": "before model sampling",
            "returncode": 1,
            "timed_out": False,
            "output_present": False,
            "native_usage_available": False,
            "counted_tokens_per_attempt": 0,
            "api_error": (
                "Invalid schema for response_format 'codex_output_schema': "
                "In context=('properties', 'primitive_obligation_results'), "
                "'uniqueItems' is not permitted."
            ),
            "original_judge_schema_sha256": sha256_file(ORIGINAL_SCHEMA),
        },
    }
    source["source_receipt_digest"] = canonical_sha256(source)
    return source


def build(source_run: Path) -> dict[str, Any]:
    for path in DEPENDENCIES:
        if not path.is_file():
            raise FileNotFoundError(path)
    base_lock = read_json(BASE_LOCK)
    base_authorization = read_json(BASE_AUTHORIZATION)
    source = source_receipt(source_run)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-evaluation-judge-compat-amendment-v0.2",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "base_protocol_version": "0.5",
        "amendment_id": "0.5-judge-compat.1",
        "purpose": (
            "Resume the first v0.5 incremental run after four pre-sampling API "
            "schema rejections, preserving all generated answers and changing only "
            "the Judge Structured Outputs transport view."
        ),
        "base_binding": {
            "protocol_path": display(BASE_PROTOCOL),
            "protocol_sha256": sha256_file(BASE_PROTOCOL),
            "lock_path": display(BASE_LOCK),
            "lock_digest": base_lock["lock_digest"],
            "authorization_path": display(BASE_AUTHORIZATION),
            "authorization_file_sha256": sha256_file(BASE_AUTHORIZATION),
            "authorization_digest": canonical_sha256(base_authorization),
            "authorized_configuration_digest": base_authorization["human_authorization"]
            ["authorized_configuration_digest"],
        },
        "retained_source_run": source,
        "schema_compatibility": {
            "canonical_schema_path": display(ORIGINAL_SCHEMA),
            "canonical_schema_sha256": sha256_file(ORIGINAL_SCHEMA),
            "api_schema_path": display(COMPATIBLE_SCHEMA),
            "api_schema_sha256": sha256_file(COMPATIBLE_SCHEMA),
            "transformation": (
                "remove exactly the two uniqueItems keywords rejected by the "
                "OpenAI Structured Outputs subset"
            ),
            "removed_keyword_paths": [
                "properties.primitive_obligation_results.uniqueItems",
                "properties.unexpected_primitive_actions.uniqueItems",
            ],
            "canonical_local_validation": (
                "unchanged validate_judge_output rejects duplicate primitive entries "
                "and applies every original scoring normalization"
            ),
            "semantic_contract_relaxation": False,
        },
        "recovery_control": {
            "retained_generation_policy": "reuse exactly the three bound v0.5 cells; never regenerate them",
            "original_failure_policy": "retain attempts 1/2 and both human failure packets unchanged",
            "failed_slot_attempt_number": 3,
            "new_slot_attempt_number": 1,
            "retry_policy": "none: the four original failures consumed all initial Judge retry headroom",
            "call_order": (
                "resume immediate Judge for the retained triplet, atomically commit it, "
                "then continue the remaining authorized smoke batches"
            ),
            "batch_commit_semantics": "unchanged frozen v0.5 hash-chained atomic commit",
            "analysis_semantics": "unchanged frozen v0.5 committed-batch-only analyzer",
            "terminal_stop": (
                "any new Judge failure, schema rejection, source drift, isolation failure, "
                "binary disagreement, or original budget breach"
            ),
        },
        "budget_accounting": {
            "original_ceiling": {
                "maximum_committed_batches": 5,
                "maximum_generation_calls": 17,
                "maximum_judge_calls": 34,
                "maximum_counted_tokens": 3_000_000,
            },
            "consumed_before_amendment": {
                "committed_batches": 0,
                "generation_calls": 3,
                "judge_calls": 4,
                "counted_tokens": 90_100,
            },
            "remaining": {
                "committed_batches": 5,
                "generation_calls": 14,
                "judge_calls": 30,
                "counted_tokens": 2_909_900,
            },
            "valid_judge_records_still_required_for_five_batches": 30,
            "future_retry_headroom": 0,
            "budget_expansion": False,
        },
        "human_authorization": {
            "authority": "William",
            "design_instruction": "那按你的建议调整吧",
            "design_evidence_id": "E7c74a48b",
            "design_authorized": True,
            "semantic_recovery_execution_authorized": False,
            "fresh_exact_digest_authorization_required": True,
            "stop_authority": "William",
            "release_preparation": False,
        },
        "dependency_receipts": [
            {"path": display(path), "sha256": sha256_file(path)}
            for path in DEPENDENCIES
        ],
        "freeze": {
            "source_parent_commit": commit,
            "built_at_utc": datetime.now(timezone.utc).isoformat(),
            "semantic_generator_output_generated_before_amendment": True,
            "semantic_judge_output_generated_before_amendment": False,
            "semantic_output_generated_under_amendment_before_freeze": False,
            "immutable_after": "compatibility lock creation and containing git commit",
            "future_change_policy": (
                "another additive amendment or experiment protocol must be frozen "
                "before any further semantic call"
            ),
        },
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, default=DEFAULT_SOURCE_RUN)
    args = parser.parse_args()
    print(json.dumps(build(args.source_run.resolve()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
