#!/usr/bin/env python3
"""Run the v0.5 incremental, filesystem-isolated Codex evaluation.

One batch is one case/repeat triplet across Stable, direct-only, and thin-kernel.
The batch order is:

    generate three -> verify enforced isolation -> judge each twice -> commit batch

Only a final batch-commit record makes artifacts count toward analysis.  A later stop
therefore leaves prior Judge-backed batches usable within their partial-result claim
boundary instead of deferring every Judge call until 225 generations have completed.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping, Sequence


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
V04_RUNNER = RUNTIME_ROOT / "run_real_codex_evaluation_v04.py"
ISOLATION_MODULE = RUNTIME_ROOT / "filesystem_isolation_v05.py"
DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.5.pending.json"
)
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
JUDGE_SCHEMA = BETA_ROOT / "fixtures" / "judge-output-v0.4.schema.json"
JUDGE_RUBRIC = BETA_ROOT / "fixtures" / "judge-rubric-v0.4.json"
ANALYZER_V05 = RUNTIME_ROOT / "analyze_incremental_v05.py"
ARM_ORDER = ("stable", "direct-only", "thin-kernel")
GENERATION_SCHEMA = "mindthus-beta2-real-cell-v0.5"
BATCH_COMMIT_SCHEMA = "mindthus-beta2-evaluation-batch-commit-v0.5"
RUN_STATE_SCHEMA = "mindthus-beta2-incremental-evaluation-state-v0.5"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V04 = _load("mindthus_beta2_v04_runner", V04_RUNNER)
ISO = _load("mindthus_beta2_v05_isolation", ISOLATION_MODULE)
ORIGINAL_RUN_STREAMED = V04.run_streamed


class EvaluationStop(RuntimeError):
    def __init__(self, veto_id: str, reason: str):
        super().__init__(reason)
        self.veto_id = veto_id
        self.reason = reason


_CONTEXT: dict[str, Any] | None = None
_CONTEXT_LOCK = threading.Lock()


def canonical_sha256(value: object) -> str:
    return V04.canonical_sha256(value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_atomic_json(path: Path, payload: object) -> None:
    V04.write_atomic_json(path, payload)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _existing_file(root: Path) -> Path:
    if root.is_file():
        return root.resolve()
    for path in sorted(root.rglob("*"), key=str):
        if path.is_file() and not path.is_symlink():
            return path.resolve()
    raise EvaluationStop("protocol-or-arm-drift", f"probe root contains no file: {root}")


def _output_identity(answer_path: Path) -> tuple[str, str, int, int | None]:
    parts = answer_path.parts
    if "generation-attempts" in parts:
        index = parts.index("generation-attempts")
        cell_id = parts[index + 1]
        match = re.match(r"attempt-(\d+)\.partial-", parts[index + 2])
        if not match:
            raise EvaluationStop("isolation-evidence-missing", "generation attempt path differs")
        return "generation", cell_id, int(match.group(1)), None
    if "judge-attempts" in parts:
        index = parts.index("judge-attempts")
        output_id = parts[index + 1]
        slot_match = re.fullmatch(r"slot-(\d+)", parts[index + 2])
        attempt_match = re.match(r"attempt-(\d+)\.partial-", parts[index + 3])
        if not slot_match or not attempt_match:
            raise EvaluationStop("isolation-evidence-missing", "Judge attempt path differs")
        return "judge", output_id, int(attempt_match.group(1)), int(slot_match.group(1))
    raise EvaluationStop("isolation-evidence-missing", "semantic output path is not attributable")


def _receipt_path(
    out_dir: Path, role: str, identifier: str, attempt: int, slot: int | None
) -> Path:
    if role == "generation":
        return out_dir / "isolation-receipts" / role / identifier / f"attempt-{attempt:02d}.json"
    return (
        out_dir
        / "isolation-receipts"
        / role
        / identifier
        / f"slot-{slot}"
        / f"attempt-{attempt:02d}.json"
    )


def _profile_path(receipt_path: Path) -> Path:
    return receipt_path.with_suffix(".sb")


def _manifest_for_home(home: Path) -> Mapping[str, Any] | None:
    assert _CONTEXT is not None
    for manifest in _CONTEXT["manifests"].values():
        if Path(manifest["host"]["home"]).resolve() == home.resolve():
            return manifest
    return None


def _sandboxed_run_streamed(
    command: Sequence[str],
    *,
    input_text: str,
    cwd: Path,
    env: Mapping[str, str],
    timeout: int,
) -> Any:
    """Bind and apply one exact sandbox profile immediately before a semantic call."""

    if _CONTEXT is None:
        raise EvaluationStop("isolation-evidence-missing", "v0.5 isolation context is absent")
    try:
        output_index = list(command).index("-o") + 1
        answer_path = Path(str(command[output_index])).resolve()
    except (ValueError, IndexError) as exc:
        raise EvaluationStop("isolation-evidence-missing", "semantic command has no output path") from exc
    role, identifier, attempt, slot = _output_identity(answer_path)
    out_dir = Path(_CONTEXT["out_dir"])
    receipt_path = _receipt_path(out_dir, role, identifier, attempt, slot)
    profile_path = _profile_path(receipt_path)
    codex_home = Path(str(env["CODEX_HOME"])).resolve()
    process_home = Path(str(env["HOME"])).resolve()
    execution_root = cwd.resolve()
    answer_root = answer_path.parent.resolve()

    manifest = _manifest_for_home(codex_home)
    allowed_read_roots = [execution_root, codex_home, process_home, answer_root]
    allowed_write_roots = [codex_home, process_home, answer_root]
    if manifest is not None:
        allowed_read_roots.append(Path(manifest["package"]["root"]).resolve())
    allowed_files = [Path(_CONTEXT["auth_source"]).resolve()]
    if role == "judge":
        allowed_files.append(JUDGE_SCHEMA.resolve())

    answer_root.mkdir(parents=True, exist_ok=True)
    positive_sentinel = answer_root / ".v05-positive-probe"
    positive_sentinel.write_text("v0.5 isolation positive probe\n", encoding="utf-8")
    positive_targets = [positive_sentinel]
    if manifest is not None:
        positive_targets.append(_existing_file(Path(manifest["package"]["root"])))

    forbidden_targets = [
        Path(path).resolve()
        for path in _CONTEXT["forbidden_targets_by_role"][role]
    ]
    forbidden_targets = [
        path
        for path in forbidden_targets
        if not any(path.is_relative_to(root) for root in allowed_read_roots)
        and path not in allowed_files
    ]
    base_receipt = ISO.prepare_verified_profile(
        profile_path=profile_path,
        receipt_path=receipt_path,
        protected_roots=[Path(path) for path in _CONTEXT["protected_roots"]],
        allowed_read_roots=allowed_read_roots,
        allowed_write_roots=allowed_write_roots,
        allowed_read_files=allowed_files,
        probe_root=answer_root,
        allowed_targets=positive_targets,
        forbidden_targets=forbidden_targets,
    )
    runtime_probe = subprocess.run(
        ISO.sandboxed_command(profile_path, ["codex", "--version"]),
        cwd=execution_root,
        env=dict(env),
        text=True,
        capture_output=True,
    )
    if runtime_probe.returncode != 0 or not runtime_probe.stdout.startswith("codex-cli "):
        raise EvaluationStop(
            "isolation-evidence-missing",
            "Codex runtime cannot start under the exact semantic sandbox profile",
        )
    bound_command = ISO.sandboxed_command(profile_path, command)
    execution_receipt = {
        **{key: value for key, value in base_receipt.items() if key != "receipt_digest"},
        "role": role,
        "execution_identifier": identifier,
        "attempt": attempt,
        "judge_slot": slot,
        "sandboxed_command_sha256": canonical_sha256(list(map(str, bound_command))),
        "sandboxed_runtime_probe": {
            "command": "codex --version",
            "returncode": runtime_probe.returncode,
            "stdout_sha256": _sha256_text(runtime_probe.stdout),
            "stderr_sha256": _sha256_text(runtime_probe.stderr),
            "model_execution_performed": False,
        },
        "semantic_process_profile_applied": True,
    }
    execution_receipt["receipt_digest"] = canonical_sha256(execution_receipt)
    write_atomic_json(receipt_path, execution_receipt)
    with _CONTEXT_LOCK:
        _CONTEXT["applied_receipts"].add(str(receipt_path))
    return ORIGINAL_RUN_STREAMED(
        bound_command,
        input_text=input_text,
        cwd=cwd,
        env=env,
        timeout=timeout,
    )


def _verify_isolation_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EvaluationStop("isolation-evidence-missing", f"isolation receipt is missing: {path}")
    receipt = read_json(path)
    unsigned = dict(receipt)
    digest = unsigned.pop("receipt_digest", None)
    if (
        digest != canonical_sha256(unsigned)
        or receipt.get("status") != "pass"
        or receipt.get("semantic_process_profile_applied") is not True
        or receipt.get("parent_traversal_probe", {}).get("denied") is not True
        or receipt.get("symlink_escape_probe", {}).get("denied") is not True
        or any(not item.get("denied") for item in receipt.get("negative_probes", []))
    ):
        raise EvaluationStop("isolation-evidence-missing", f"isolation receipt failed: {path}")
    profile_path = Path(str(receipt.get("profile_path") or ""))
    if not profile_path.is_file() or ISO.sha256_file(profile_path) != receipt.get(
        "profile_sha256"
    ):
        raise EvaluationStop("isolation-evidence-missing", f"sandbox profile differs: {path}")
    return receipt


def batch_plan(protocol: Mapping[str, Any], protocol_sha256: str) -> list[dict[str, Any]]:
    workload = protocol["workload"]
    smoke_ids = [str(item) for item in workload["smoke_case_ids"]]
    matched_ids = [str(item) for item in workload["matched_case_ids"]]
    repeats = int(workload["planned_repeats"])
    ordered_units = [(case_id, 1, "smoke") for case_id in smoke_ids]
    ordered_units.extend(
        (case_id, repeat, "matched")
        for repeat in range(1, repeats + 1)
        for case_id in matched_ids
        if not (repeat == 1 and case_id in smoke_ids)
    )
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    batches: list[dict[str, Any]] = []
    for index, (case_id, repeat, gate) in enumerate(ordered_units, 1):
        key = {
            "protocol_sha256": protocol_sha256,
            "case_id": case_id,
            "repeat": repeat,
            "unit": "three-arm-triplet-v0.5",
        }
        batches.append(
            {
                "batch_index": index,
                "batch_id": canonical_sha256(key),
                "case_id": case_id,
                "repeat": repeat,
                "gate": gate,
                "cells": [
                    {"case_id": case_id, "arm_id": arm_id, "repeat": repeat}
                    for arm_id in V04.latin_arm_order(seed, case_id, repeat)
                ],
            }
        )
    expected = len(matched_ids) * repeats
    if len(batches) != expected or expected != 75:
        raise EvaluationStop("protocol-or-arm-drift", "v0.5 batch cardinality differs")
    if any({cell["arm_id"] for cell in batch["cells"]} != set(ARM_ORDER) for batch in batches):
        raise EvaluationStop("protocol-or-arm-drift", "v0.5 batch arm set differs")
    return batches


def cell_identity(
    cell: Mapping[str, Any],
    case: Mapping[str, Any],
    manifest: Mapping[str, Any],
    protocol_sha256: str,
) -> tuple[str, dict[str, Any]]:
    key = {
        "protocol_sha256": protocol_sha256,
        "arm_digest": manifest["identity_digest"],
        "surface": "codex-plugin",
        "case_id": cell["case_id"],
        "entry_mode": case["contract"]["entry_mode"],
        "scenario_lifecycle_path": case["contract"]["lifecycle_path"],
        "host_session_mode": "startup",
        "repeat": cell["repeat"],
        "executor": "codex-cli-0.144.4-v0.5-sandboxed",
    }
    return canonical_sha256(key), key


def completed_cell(out_dir: Path, cell_id: str) -> dict[str, Any] | None:
    path = out_dir / "cells" / cell_id / "record.json"
    if not path.is_file():
        return None
    record = read_json(path)
    unsigned = dict(record)
    digest = unsigned.pop("record_digest", None)
    if digest != canonical_sha256(unsigned) or record.get("schema_version") != GENERATION_SCHEMA:
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell digest differs: {cell_id}")
    answer_path = Path(str(record.get("answer_path") or "")).resolve()
    if not answer_path.is_file() or _sha256_text(answer_path.read_text(encoding="utf-8")) != record.get(
        "answer_sha256"
    ):
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell answer differs: {cell_id}")
    receipt = _verify_isolation_receipt(Path(record["isolation_receipt"]["path"]))
    if receipt["receipt_digest"] != record["isolation_receipt"]["digest"]:
        raise EvaluationStop("isolation-evidence-missing", f"cell isolation binding differs: {cell_id}")
    return record


def execute_generator_cell(
    *,
    batch: Mapping[str, Any],
    cell: Mapping[str, Any],
    case: Mapping[str, Any],
    manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    protocol_sha256: str,
    out_dir: Path,
    timeout: int,
    generation_calls_used: int,
) -> tuple[dict[str, Any], int, int]:
    cell_id, key = cell_identity(cell, case, manifest, protocol_sha256)
    existing = completed_cell(out_dir, cell_id)
    if existing:
        if existing.get("cell_key") != key or existing.get("batch_id") != batch["batch_id"]:
            raise EvaluationStop("protocol-or-arm-drift", f"retained cell differs: {cell_id}")
        return existing, 0, 0
    parent = V04.attempt_parent(out_dir, "generation", cell_id)
    if any(parent.glob("attempt-*")):
        raise EvaluationStop(
            "untraceable-or-partial-artifact",
            f"generation attempt exists without a v0.5 cell record: {cell_id}",
        )
    prompt = V04.generator_prompt(V04.user_prompt(case["source"]))
    calls = 0
    counted_tokens = 0
    for attempt_number in (1, 2):
        if generation_calls_used + calls >= authorization["maximum_generation_calls"]:
            raise EvaluationStop("authority-or-evidence-regression", "generation call ceiling reached")
        attempt, capture, answer, evidence = V04.run_generator_attempt(
            cell_id=cell_id,
            prompt=prompt,
            manifest=manifest,
            authorization=authorization,
            out_dir=out_dir,
            attempt_number=attempt_number,
            timeout=timeout,
        )
        calls += 1
        counted_tokens += int(attempt["counted_tokens"])
        receipt_path = _receipt_path(out_dir, "generation", cell_id, attempt_number, None)
        receipt = _verify_isolation_receipt(receipt_path)
        failed = capture.returncode != 0 or capture.timed_out
        if failed and answer:
            raise EvaluationStop(
                "untraceable-or-partial-artifact",
                f"{cell_id} failed after semantic output; retained and not retried",
            )
        if failed and attempt_number == 1:
            continue
        if failed:
            raise EvaluationStop("untraceable-or-partial-artifact", f"{cell_id} retry failed")

        native = dict(evidence["native_telemetry"])
        raw_turn = {
            "usage": evidence["usage"],
            "duration_seconds": capture.wall_time_seconds,
            "first_observable_action_latency_seconds": (
                capture.first_observable_action["offset_seconds"]
                if capture.first_observable_action
                else None
            ),
            "native_telemetry": native,
            "loaded_commands": evidence["loaded_commands"],
            "answer": answer,
            "agent_messages": evidence["agent_messages"],
            "returncode": capture.returncode,
            "timed_out": capture.timed_out,
        }
        required = dict(V04.V04_REQUIRED_EVIDENCE)
        if manifest["arm_id"] == "thin-kernel":
            required["arm.hook_observation_receipt"] = ("deterministic",)
        telemetry = V04.build_turn_telemetry(
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
                "attempt": attempt_number,
            },
            required_evidence=required,
        )
        if telemetry["evidence_gate"]["status"] != "pass":
            raise EvaluationStop(
                "missing-primary-native-evidence",
                f"{cell['case_id']}/{cell['arm_id']} evidence gate blocked",
            )
        record: dict[str, Any] = {
            "schema_version": GENERATION_SCHEMA,
            "cell_id": cell_id,
            "cell_key": key,
            "batch_id": batch["batch_id"],
            "batch_index": batch["batch_index"],
            "arm_id": cell["arm_id"],
            "case_source_receipt": canonical_sha256(case["contract"]["source"]),
            "generation_attempt": {
                "attempt": attempt_number,
                "attempt_digest": attempt["attempt_digest"],
                "path": attempt["path"],
            },
            "isolation_receipt": {
                "path": str(receipt_path),
                "digest": receipt["receipt_digest"],
            },
            "answer_path": str(Path(attempt["path"]) / "answer.txt"),
            "answer_sha256": _sha256_text(answer),
            "event_types": evidence["event_types"],
            "transport_error_event_count": evidence["event_types"].count("error"),
            "loaded_command_digests": [
                _sha256_text(command) for command in evidence["loaded_commands"]
            ],
            "usage": evidence["usage"],
            "counted_tokens": V04.token_total(evidence["usage"]),
            "telemetry": telemetry,
            "host_lifecycle_claim": "startup-session-only",
            "scenario_lifecycle_path": case["contract"]["lifecycle_path"],
        }
        record["record_digest"] = canonical_sha256(record)
        write_atomic_json(out_dir / "cells" / cell_id / "record.json", record)
        return record, calls, counted_tokens
    raise AssertionError("unreachable generator loop")


def judge_identity(protocol_sha256: str, cell_id: str) -> str:
    return _sha256_text(f"{protocol_sha256}:{cell_id}:blinded-output-v0.5")


def _judge_receipt_paths(out_dir: Path, output_id: str, records: Sequence[Mapping[str, Any]]) -> list[Path]:
    return [
        _receipt_path(
            out_dir,
            "judge",
            output_id,
            int(record["attempt"]),
            int(record["judge_slot"]),
        )
        for record in records
    ]


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
        "schema_version": RUN_STATE_SCHEMA,
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


def _commit_path(out_dir: Path, batch_id: str) -> Path:
    return out_dir / "batch-commits" / f"{batch_id}.json"


def validate_batch_commit(
    out_dir: Path,
    batch: Mapping[str, Any],
    previous_digest: str | None,
) -> dict[str, Any] | None:
    path = _commit_path(out_dir, str(batch["batch_id"]))
    if not path.is_file():
        return None
    commit = read_json(path)
    unsigned = dict(commit)
    digest = unsigned.pop("commit_digest", None)
    if (
        digest != canonical_sha256(unsigned)
        or commit.get("schema_version") != BATCH_COMMIT_SCHEMA
        or commit.get("batch_id") != batch["batch_id"]
        or commit.get("batch_index") != batch["batch_index"]
        or commit.get("previous_commit_digest") != previous_digest
        or len(commit.get("generation_records", [])) != 3
        or len(commit.get("judge_records", [])) != 6
    ):
        raise EvaluationStop("untraceable-or-partial-artifact", f"batch commit differs: {path}")
    for item in commit["generation_records"]:
        record = completed_cell(out_dir, str(item["cell_id"]))
        if record is None or record["record_digest"] != item["record_digest"]:
            raise EvaluationStop("untraceable-or-partial-artifact", "committed cell differs")
    for item in commit["judge_records"]:
        record = V04.existing_judge_record(
            out_dir, str(item["blinded_output_id"]), int(item["judge_slot"])
        )
        if record is None or record["record_digest"] != item["record_digest"]:
            raise EvaluationStop("untraceable-or-partial-artifact", "committed Judge differs")
        receipt = _verify_isolation_receipt(Path(item["isolation_receipt_path"]))
        if receipt["receipt_digest"] != item["isolation_receipt_digest"]:
            raise EvaluationStop("isolation-evidence-missing", "committed Judge isolation differs")
    return commit


def _write_batch_commit(
    *,
    out_dir: Path,
    batch: Mapping[str, Any],
    protocol_sha256: str,
    authorization_digest: str,
    previous_digest: str | None,
    generation_records: Sequence[Mapping[str, Any]],
    judge_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    commit: dict[str, Any] = {
        "schema_version": BATCH_COMMIT_SCHEMA,
        "protocol_sha256": protocol_sha256,
        "authorization_digest": authorization_digest,
        "batch_id": batch["batch_id"],
        "batch_index": batch["batch_index"],
        "case_id": batch["case_id"],
        "repeat": batch["repeat"],
        "gate": batch["gate"],
        "previous_commit_digest": previous_digest,
        "generation_records": [
            {
                "cell_id": record["cell_id"],
                "arm_id": record["arm_id"],
                "record_digest": record["record_digest"],
                "isolation_receipt_digest": record["isolation_receipt"]["digest"],
            }
            for record in generation_records
        ],
        "judge_records": [],
        "batch_counted_tokens": sum(int(record.get("counted_tokens") or 0) for record in generation_records)
        + sum(int(record.get("counted_tokens") or 0) for record in judge_records),
        "commit_semantics": "only this record makes the batch count toward v0.5 analysis",
        "committed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    for record in judge_records:
        output_id = str(record["blinded_output_id"])
        receipt_path = _receipt_path(
            out_dir,
            "judge",
            output_id,
            int(record["attempt"]),
            int(record["judge_slot"]),
        )
        receipt = _verify_isolation_receipt(receipt_path)
        commit["judge_records"].append(
            {
                "blinded_output_id": output_id,
                "judge_slot": record["judge_slot"],
                "record_digest": record["record_digest"],
                "isolation_receipt_path": str(receipt_path),
                "isolation_receipt_digest": receipt["receipt_digest"],
            }
        )
    commit["commit_digest"] = canonical_sha256(commit)
    write_atomic_json(_commit_path(out_dir, str(batch["batch_id"])), commit)
    return commit


def committed_summary(out_dir: Path, batches: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    commits: list[dict[str, Any]] = []
    previous: str | None = None
    for batch in batches:
        commit = validate_batch_commit(out_dir, batch, previous)
        if commit is None:
            break
        commits.append(commit)
        previous = commit["commit_digest"]
    return {
        "schema_version": "mindthus-beta2-incremental-summary-v0.5",
        "committed_batches": len(commits),
        "committed_generation_outputs": len(commits) * 3,
        "committed_judge_records": len(commits) * 6,
        "last_commit_digest": previous,
        "smoke_gate_complete": len(commits) >= 5,
        "matched_complete": len(commits) == len(batches),
        "partial_claim_boundary": (
            "Judge-backed descriptive evidence for committed batches only; no full architecture "
            "or non-inferiority conclusion before all 75 batches and endpoint denominators pass"
        ),
    }


def _configure_isolation(
    *,
    out_dir: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    auth_source: Path,
) -> None:
    global _CONTEXT
    control_sentinel = out_dir / "control" / "v05-denied-sentinel.txt"
    control_sentinel.parent.mkdir(parents=True, exist_ok=True)
    control_sentinel.write_text("runner control: model access forbidden\n", encoding="utf-8")
    generator_forbidden = [MATRIX_PATH.resolve(), JUDGE_RUBRIC.resolve(), control_sentinel]
    judge_forbidden = [MATRIX_PATH.resolve(), JUDGE_RUBRIC.resolve(), control_sentinel]
    for manifest in manifests.values():
        manifest_path = Path(manifest["host"]["home"]).parent / "sealed-arm.json"
        if manifest_path.is_file():
            judge_forbidden.append(manifest_path.resolve())
        generator_forbidden.append(_existing_file(Path(manifest["package"]["root"])))
    # A generator may read its own package; role-specific filtering occurs below by
    # allowing the exact own package, which overrides the broader protected-root deny.
    _CONTEXT = {
        "out_dir": str(out_dir.resolve()),
        "manifests": dict(manifests),
        "auth_source": str(auth_source.resolve()),
        "protected_roots": ["/Volumes/Data", str(Path.home().resolve())],
        "forbidden_targets_by_role": {
            "generation": [str(path) for path in generator_forbidden],
            "judge": [str(path) for path in judge_forbidden],
        },
        "applied_receipts": set(),
    }


def run_evaluation(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    V04.scan_partial_artifacts(out_dir)
    auth_report, authorization, protocol = V04.authorized_context(args.authorization.resolve())
    if protocol.get("protocol_version") != "0.5":
        raise EvaluationStop("protocol-or-arm-drift", "v0.5 runner received another protocol")
    manifests = V04.verify_arm_set(args.arm_manifest, authorization)
    for manifest in manifests.values():
        staging = Path(manifest["host"]["execution_root"]).resolve().parent / "package"
        if staging.exists():
            raise EvaluationStop("isolation-evidence-missing", f"package staging still exists: {staging}")
    matrix = read_json(MATRIX_PATH)
    cases = V04.source_cases(matrix)
    batches = batch_plan(protocol, auth_report["protocol_sha256"])
    if not {batch["case_id"] for batch in batches}.issubset(cases):
        raise EvaluationStop("protocol-or-arm-drift", "one or more case sources are unavailable")
    max_batches = int(authorization.get("maximum_committed_batches") or 0)
    if max_batches < 1 or max_batches > len(batches):
        raise EvaluationStop("authority-or-evidence-regression", "authorized batch ceiling differs")

    auth_source = args.auth_source.resolve()
    if not auth_source.is_file():
        raise EvaluationStop("authority-or-evidence-regression", "Codex auth source is unavailable")
    _configure_isolation(out_dir=out_dir, manifests=manifests, auth_source=auth_source)
    generation_calls, judge_calls, counted_tokens = V04.observed_attempt_usage(out_dir)
    summary = committed_summary(out_dir, batches)
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
    rubric = read_json(JUDGE_RUBRIC)
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    state_path = out_dir / "run-state-v0.5.json"

    original = V04.run_streamed
    V04.run_streamed = _sandboxed_run_streamed
    active_batch: Mapping[str, Any] | None = None
    try:
        for batch in batches[committed:max_batches]:
            active_batch = batch
            generation_records: list[dict[str, Any]] = []
            for cell in batch["cells"]:
                record, new_calls, new_tokens = execute_generator_cell(
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
                write_atomic_json(
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
            if {record["arm_id"] for record in generation_records} != set(ARM_ORDER):
                raise EvaluationStop("protocol-or-arm-drift", "generated batch arm set differs")

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
                if V04.FORBIDDEN_BLINDING_LABEL.search(candidate) or any(
                    path in candidate for path in sensitive
                ):
                    raise EvaluationStop("judge-environment-contamination", "candidate exposes arm identity")
                output_id = judge_identity(auth_report["protocol_sha256"], cell_id)
                raw_prompt = V04.user_prompt(case["source"])
                blinded_path = V04.write_blinded_input(
                    out_dir=out_dir,
                    output_id=output_id,
                    prompt=raw_prompt,
                    case=case,
                    candidate=candidate,
                )
                blinded_digest = str(read_json(blinded_path)["input_digest"])
                prompt = V04.judge_prompt(
                    rubric=rubric,
                    case=case,
                    prompt=raw_prompt,
                    candidate=candidate,
                    blinded_output_id=output_id,
                )
                needed = sum(
                    V04.existing_judge_record(out_dir, output_id, slot) is None
                    for slot in (1, 2)
                )
                if judge_calls + (2 * needed) > authorization["maximum_judge_calls"]:
                    raise EvaluationStop("authority-or-evidence-regression", "Judge call ceiling reached")
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [
                        executor.submit(
                            V04.run_judge_slot,
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
                for receipt_path in _judge_receipt_paths(out_dir, output_id, records):
                    _verify_isolation_receipt(receipt_path)
                write_atomic_json(
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
            if counted_tokens > authorization["token_or_cost_budget"]["maximum"]:
                raise EvaluationStop("authority-or-evidence-regression", "token ceiling reached")
            commit = _write_batch_commit(
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
            write_atomic_json(
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
                    str(ANALYZER_V05),
                    "--run-dir",
                    str(out_dir),
                    "--authorization",
                    str(args.authorization.resolve()),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
            )
            if analysis_run.returncode not in (0, 3):
                raise EvaluationStop(
                    "incremental-batch-integrity-failure",
                    "incremental analysis failed after a committed batch: "
                    f"{analysis_run.stderr.strip() or analysis_run.stdout.strip()}",
                )
            analysis = json.loads(analysis_run.stdout)
            if analysis.get("status") == "human-adjudication-required":
                raise EvaluationStop(
                    "human-adjudication-required",
                    "the committed batch has unresolved binary Judge disagreements",
                )
    except (EvaluationStop, V04.EvaluationStop, ISO.IsolationError) as exc:
        veto = getattr(exc, "veto_id", "isolation-evidence-missing")
        write_atomic_json(
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
        raise EvaluationStop(veto, str(exc)) from exc
    finally:
        V04.run_streamed = original

    report = committed_summary(out_dir, batches)
    report.update(
        {
            "status": "matched-complete" if committed == len(batches) else "authorized-batch-limit-reached",
            "protocol_sha256": auth_report["protocol_sha256"],
            "authorization_digest": auth_report["authorization_digest"],
            "generation_calls": generation_calls,
            "judge_calls": judge_calls,
            "counted_tokens": counted_tokens,
            "authorized_batch_ceiling": max_batches,
        }
    )
    write_atomic_json(out_dir / "incremental-summary-v0.5.json", report)
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, code = run_evaluation(args)
    except (OSError, json.JSONDecodeError, EvaluationStop, RuntimeError) as exc:
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
