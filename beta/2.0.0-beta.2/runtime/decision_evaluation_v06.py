#!/usr/bin/env python3
"""Deterministic core for the bounded Mindthus Beta route decision v0.6.

This module owns protocol/lock validation, paired-Judge validation, append-only batch
ledger reconstruction, human-adjudication consumption, outcome calculation, and the
zero-model rehearsal.  It never calls a semantic model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
CASES_PATH = BETA_ROOT / "fixtures" / "decision-cases-v0.6.json"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
JUDGE_SCHEMA_PATH = BETA_ROOT / "fixtures" / "paired-judge-output-v0.6.schema.json"
JUDGE_RUBRIC_PATH = BETA_ROOT / "fixtures" / "paired-judge-rubric-v0.6.json"
DEVELOPMENT_CASES_PATH = BETA_ROOT / "fixtures" / "development-cases.jsonl"
PUBLIC_CASES_PATH = REPO_ROOT / "tests" / "judgment_benchmark_50_cases.jsonl"

ARM_IDS = ("stable", "direct-only", "thin-kernel")
BINARY_BASE_AXES = (
    "owner_success",
    "false_wakeup_final_answer",
    "required_visible_action_present",
    "authority_or_evidence_regression",
)
PROTOCOL_SCHEMA = "mindthus-beta2-route-decision-protocol-v0.6"
LOCK_SCHEMA = "mindthus-beta2-route-decision-lock-v0.6"
AUTH_SCHEMA = "mindthus-beta2-route-decision-authorization-v0.6"
CELL_SCHEMA = "mindthus-beta2-route-decision-cell-v0.6"
JUDGE_RECORD_SCHEMA = "mindthus-beta2-paired-judge-record-v0.6"
COMMIT_SCHEMA = "mindthus-beta2-route-decision-batch-commit-v0.6"
ADJUDICATION_SCHEMA = "mindthus-beta2-paired-adjudication-v0.6"
GENERATION_ATTEMPT_SCHEMA = "mindthus-beta2-generation-attempt-v0.6"
JUDGE_ATTEMPT_SCHEMA = "mindthus-beta2-paired-judge-attempt-v0.6"
BLINDED_INPUT_SCHEMA = "mindthus-beta2-paired-blinded-input-v0.6"
BLINDING_RECEIPT_SCHEMA = "mindthus-beta2-paired-blinding-receipt-v0.6"
DISAGREEMENT_SCHEMA = "mindthus-beta2-paired-disagreement-v0.6"
RUN_REPORT_SCHEMA = "mindthus-beta2-route-decision-report-v0.6"
EXPECTED_CODEX_VERSION = "codex-cli 0.144.4"
MAX_COUNTED_TOKENS_PER_CALL = 131_072
NAMESPACE_PREFIX = re.compile(r"(?i)\bmindthus(?:-beta)?:")
GENERATOR_WRAPPER = (
    "Answer the user directly in the user's language. Do not inspect evaluation "
    "fixtures, scoring rubrics, pass criteria, fail signals, or reviewer notes. "
    "Do not mention this evaluation instruction. Keep the answer concise but sufficient."
)


class DecisionError(RuntimeError):
    """Fail-closed deterministic contract error."""

    def __init__(self, code: str, reason: str):
        super().__init__(reason)
        self.code = code
        self.reason = reason


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def verify_digest(payload: Mapping[str, Any], field: str, label: str) -> None:
    unsigned = dict(payload)
    observed = unsigned.pop(field, None)
    if observed != canonical_sha256(unsigned):
        raise DecisionError("artifact-digest-drift", f"{label} digest differs")


def _jsonl_index(path: Path, key: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        row = json.loads(raw)
        value = str(row.get(key) or "")
        if not value or value in index:
            raise DecisionError("case-source-drift", f"duplicate or missing {key}: {path}")
        index[value] = row
    return index


def matrix_index() -> dict[str, dict[str, Any]]:
    payload = read_json(MATRIX_PATH)
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise DecisionError("case-source-drift", "case matrix has no case list")
    result = {str(item.get("case_id") or ""): dict(item) for item in cases}
    if "" in result or len(result) != len(cases):
        raise DecisionError("case-source-drift", "case matrix identities differ")
    return result


def selected_case_ids(config: Mapping[str, Any] | None = None) -> list[str]:
    config = dict(config or read_json(CASES_PATH))
    buckets = config.get("buckets")
    if not isinstance(buckets, Mapping):
        raise DecisionError("case-source-drift", "decision case buckets are missing")
    result: list[str] = []
    for name in ("kernel-benefit", "routing-integrity", "stay-asleep"):
        values = buckets.get(name)
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            raise DecisionError("case-source-drift", f"decision bucket differs: {name}")
        result.extend(values)
    if len(result) != 8 or len(set(result)) != 8:
        raise DecisionError("case-source-drift", "decision workload must contain eight unique cases")
    return result


def case_contracts() -> dict[str, dict[str, Any]]:
    config = read_json(CASES_PATH)
    selected = selected_case_ids(config)
    matrix = matrix_index()
    public = _jsonl_index(PUBLIC_CASES_PATH, "case_id")
    development = _jsonl_index(DEVELOPMENT_CASES_PATH, "case_id")
    contracts: dict[str, dict[str, Any]] = {}
    for case_id in selected:
        if case_id not in matrix:
            raise DecisionError("case-source-drift", f"selected case is absent: {case_id}")
        item = matrix[case_id]
        source = item.get("source")
        if not isinstance(source, Mapping) or source.get("run_eligibility") != "eligible":
            raise DecisionError("case-source-drift", f"selected case is ineligible: {case_id}")
        locator = str(source.get("locator") or "")
        source_row = public.get(locator.rsplit("#", 1)[-1]) if "judgment_benchmark" in locator else development.get(case_id)
        if not isinstance(source_row, Mapping):
            raise DecisionError("case-source-drift", f"case source is unavailable: {case_id}")
        prompt = source_row.get("turns") or source_row.get("prompt")
        if not isinstance(prompt, (str, list)):
            raise DecisionError("case-source-drift", f"case prompt differs: {case_id}")
        contract = {
            key: item[key]
            for key in (
                "case_id",
                "case_type",
                "provenance",
                "entry_mode",
                "lifecycle_path",
                "accepted_execution_owners",
                "expected_primitive_obligations",
                "required_visible_action",
                "required_skill_loads",
                "allowed_skill_loads",
                "stay_asleep_expected",
            )
        }
        contract["source"] = dict(source)
        contract["prompt"] = prompt
        contract["source_row_sha256"] = canonical_sha256(source_row)
        contracts[case_id] = contract
    return contracts


def dependency_receipts() -> list[dict[str, str]]:
    paths = (
        BETA_ROOT / "DECISION-EVALUATION-V0.6.md",
        CASES_PATH,
        MATRIX_PATH,
        JUDGE_SCHEMA_PATH,
        JUDGE_RUBRIC_PATH,
        DEVELOPMENT_CASES_PATH,
        PUBLIC_CASES_PATH,
        BETA_ROOT / "runtime" / "decision_evaluation_v06.py",
        BETA_ROOT / "runtime" / "run_real_codex_evaluation_v06.py",
        BETA_ROOT / "runtime" / "run_real_codex_evaluation_v04.py",
        BETA_ROOT / "runtime" / "filesystem_isolation_v05.py",
        BETA_ROOT / "runtime" / "codex_stream_capture.py",
        REPO_ROOT / "scripts" / "mindthus_beta2_telemetry.py",
    )
    return [
        {"path": str(path.relative_to(REPO_ROOT)), "sha256": sha256_file(path)}
        for path in paths
    ]


def load_manifests(paths: Sequence[Path]) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for raw_path in paths:
        path = raw_path.resolve()
        manifest = read_json(path)
        arm_id = str(manifest.get("arm_id") or "")
        if arm_id not in ARM_IDS or arm_id in manifests:
            raise DecisionError("arm-drift", f"arm manifest set differs: {path}")
        unsigned = dict(manifest)
        observed = unsigned.pop("manifest_digest", None)
        if observed is not None and observed != canonical_sha256(unsigned):
            raise DecisionError("arm-drift", f"arm manifest digest differs: {arm_id}")
        manifests[arm_id] = {
            "arm_id": arm_id,
            "path": str(path),
            "file_sha256": sha256_file(path),
            "identity_digest": manifest.get("identity_digest"),
            "package_tree_sha256": manifest.get("package", {}).get("tree_sha256"),
            "manifest": manifest,
        }
    if set(manifests) != set(ARM_IDS):
        raise DecisionError("arm-drift", "exactly three arm manifests are required")
    if manifests["direct-only"]["package_tree_sha256"] != manifests["thin-kernel"]["package_tree_sha256"]:
        raise DecisionError("arm-drift", "Beta arm package trees differ")
    return manifests


def _source_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True
    )
    if result.returncode != 0:
        raise DecisionError("source-drift", "cannot resolve source commit")
    return result.stdout.strip()


def build_protocol(manifest_paths: Sequence[Path]) -> dict[str, Any]:
    config = read_json(CASES_PATH)
    contracts = case_contracts()
    manifests = load_manifests(manifest_paths)
    case_ids = selected_case_ids(config)
    return {
        "schema_version": PROTOCOL_SCHEMA,
        "protocol_id": "issue-119-codex-route-decision-v0.6",
        "status": "frozen",
        "purpose": "bounded visible-case Codex decision for the current Thin-Kernel Beta route",
        "source_commit": _source_commit(),
        "dependencies": dependency_receipts(),
        "arms": [
            {key: manifests[arm_id][key] for key in ("arm_id", "path", "file_sha256", "identity_digest", "package_tree_sha256")}
            for arm_id in ARM_IDS
        ],
        "workload": {
            "case_ids": case_ids,
            "case_contract_digests": {
                case_id: canonical_sha256(contracts[case_id]) for case_id in case_ids
            },
            "buckets": config["buckets"],
            "pilot_units": config["pilot_units"],
            "repeats": 3,
            "batch_count": 24,
            "generation_outputs": 72,
            "paired_judge_calls": 48,
        },
        "model_roles": {
            "generator": {"model_id": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
            "judge_1": {"model_id": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
            "judge_2": {"model_id": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
        },
        "execution": {
            "surface": "codex-plugin",
            "batch_unit": "case/repeat three-arm triplet",
            "arm_order": "deterministic sha256 rotation",
            "judge_unit": "three opaque candidates per call",
            "judge_slots": 2,
            "candidate_order": "slot-specific deterministic sha256 shuffle",
            "generator_wrapper_sha256": sha256_text(GENERATOR_WRAPPER),
            "built_in_blinding": True,
            "authoritative_state": "reconstructed finalized attempts plus hash-chained commits",
            "pilot_semantic_gate": False,
            "post_adjudication_resume": "reconstruct current ledger; never compare with a pre-run usage snapshot",
        },
        "decision_gates": {
            "kernel_minimum_successes": 9,
            "kernel_minimum_gain_over_direct": 3,
            "quality_noninferiority_delta": -0.05,
            "owner_maximum_loss_cells_vs_stable": 1,
            "routing_minimum_successes": 5,
            "stay_asleep_maximum_false_wakeups": 1,
            "stay_asleep_maximum_additional_vs_stable": 1,
            "thin_authority_regression_maximum": 0,
            "material_input_token_ratio_vs_stable": 0.90,
            "material_wall_time_ratio_vs_stable": 0.90,
            "material_skill_hop_reduction_vs_stable": 0.25,
            "input_token_guardrail_vs_stable": 1.08,
            "wall_time_guardrail_vs_stable": 1.10,
            "input_token_guardrail_vs_direct": 1.08,
            "all_gates_required": True,
            "valid_failure_result": "route-rejected",
        },
        "failure_semantics": {
            "infrastructure": "experiment-invalid",
            "product_gate_failure": "route-rejected",
            "compatibility_amendments": 0,
            "semantic_retry": "one only when zero semantic output and zero counted tokens are proven",
        },
        "proposed_ceiling": {
            "maximum_generation_calls": 74,
            "maximum_paired_judge_calls": 50,
            "maximum_counted_tokens": 4_000_000,
            "maximum_counted_tokens_per_call": MAX_COUNTED_TOKENS_PER_CALL,
            "counted_components": ["input", "output", "reasoning"],
            "token_enforcement": "pre-call full-context reserve plus post-call native usage validation; Codex exposes aggregate usage only after an in-flight call completes",
        },
        "claim_boundary": "visible Codex/Sol-xHigh exploratory route decision only; no release, hidden-set, cross-host, or universal architecture claim",
    }


def freeze_protocol(
    manifest_paths: Sequence[Path], protocol_path: Path, lock_path: Path
) -> dict[str, Any]:
    if protocol_path.exists() or lock_path.exists():
        raise DecisionError("freeze-refused", "v0.6 protocol or lock already exists")
    protocol = build_protocol(manifest_paths)
    write_atomic_json(protocol_path, protocol)
    lock: dict[str, Any] = {
        "schema_version": LOCK_SCHEMA,
        "protocol_path": str(protocol_path.resolve()),
        "protocol_file_sha256": sha256_file(protocol_path),
        "dependency_set_digest": canonical_sha256(protocol["dependencies"]),
        "arm_set_digest": canonical_sha256(protocol["arms"]),
        "source_commit": protocol["source_commit"],
        "semantic_model_execution_before_freeze": False,
    }
    lock["lock_digest"] = canonical_sha256(lock)
    write_atomic_json(lock_path, lock)
    return {"protocol": protocol, "lock": lock}


def verify_protocol(protocol_path: Path, lock_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    protocol = read_json(protocol_path)
    lock = read_json(lock_path)
    if protocol.get("schema_version") != PROTOCOL_SCHEMA or protocol.get("status") != "frozen":
        raise DecisionError("protocol-drift", "v0.6 protocol identity differs")
    if lock.get("schema_version") != LOCK_SCHEMA:
        raise DecisionError("protocol-drift", "v0.6 lock identity differs")
    verify_digest(lock, "lock_digest", "v0.6 lock")
    if lock.get("protocol_file_sha256") != sha256_file(protocol_path):
        raise DecisionError("protocol-drift", "v0.6 protocol file differs")
    if lock.get("dependency_set_digest") != canonical_sha256(protocol.get("dependencies")):
        raise DecisionError("protocol-drift", "v0.6 dependency set differs")
    if lock.get("arm_set_digest") != canonical_sha256(protocol.get("arms")):
        raise DecisionError("protocol-drift", "v0.6 arm set differs")
    expected_dependencies = {item["path"]: item["sha256"] for item in protocol["dependencies"]}
    if expected_dependencies != {item["path"]: item["sha256"] for item in dependency_receipts()}:
        raise DecisionError("protocol-drift", "v0.6 source dependency changed")
    for arm in protocol["arms"]:
        path = Path(arm["path"])
        if not path.is_file() or sha256_file(path) != arm["file_sha256"]:
            raise DecisionError("arm-drift", f"sealed arm changed: {arm['arm_id']}")
        manifest = read_json(path)
        if manifest.get("identity_digest") != arm["identity_digest"]:
            raise DecisionError("arm-drift", f"sealed arm identity changed: {arm['arm_id']}")
    contracts = case_contracts()
    observed_contracts = {
        case_id: canonical_sha256(contracts[case_id]) for case_id in protocol["workload"]["case_ids"]
    }
    if observed_contracts != protocol["workload"]["case_contract_digests"]:
        raise DecisionError("case-source-drift", "v0.6 case contracts changed")
    if protocol.get("execution", {}).get("generator_wrapper_sha256") != sha256_text(
        GENERATOR_WRAPPER
    ):
        raise DecisionError("protocol-drift", "v0.6 Generator wrapper changed")
    return protocol, lock


def _sha_order(seed: str, values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: sha256_text(f"{seed}:{value}"))


def batch_plan(protocol: Mapping[str, Any], protocol_sha256: str) -> list[dict[str, Any]]:
    """Return the frozen 24 matched units, with pilot units first."""

    workload = protocol.get("workload")
    if not isinstance(workload, Mapping):
        raise DecisionError("protocol-drift", "v0.6 workload is missing")
    case_ids = [str(item) for item in workload.get("case_ids", [])]
    repeats = int(workload.get("repeats") or 0)
    pilot_raw = workload.get("pilot_units")
    if case_ids != selected_case_ids() or repeats != 3 or not isinstance(pilot_raw, list):
        raise DecisionError("protocol-drift", "v0.6 workload shape differs")
    pilot = [(str(item.get("case_id") or ""), int(item.get("repeat") or 0)) for item in pilot_raw]
    all_units = [(case_id, repeat) for repeat in range(1, repeats + 1) for case_id in case_ids]
    if len(pilot) != 3 or len(set(pilot)) != 3 or any(item not in all_units for item in pilot):
        raise DecisionError("protocol-drift", "v0.6 pilot units differ")
    ordered = pilot + [item for item in all_units if item not in set(pilot)]
    batches: list[dict[str, Any]] = []
    for index, (case_id, repeat) in enumerate(ordered, 1):
        identity = {
            "protocol_sha256": protocol_sha256,
            "case_id": case_id,
            "repeat": repeat,
            "unit": "three-arm-triplet-v0.6",
        }
        batch_id = canonical_sha256(identity)
        arm_order = _sha_order(f"{batch_id}:arm-order-v0.6", ARM_IDS)
        batches.append(
            {
                "batch_index": index,
                "batch_id": batch_id,
                "case_id": case_id,
                "repeat": repeat,
                "phase": "pilot" if (case_id, repeat) in set(pilot) else "main",
                "cells": [
                    {"case_id": case_id, "repeat": repeat, "arm_id": arm_id}
                    for arm_id in arm_order
                ],
            }
        )
    if len(batches) != 24 or any({cell["arm_id"] for cell in item["cells"]} != set(ARM_IDS) for item in batches):
        raise DecisionError("protocol-drift", "v0.6 batch cardinality differs")
    return batches


def cell_identity(
    *,
    protocol_sha256: str,
    batch: Mapping[str, Any],
    arm: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    key = {
        "protocol_sha256": protocol_sha256,
        "batch_id": batch["batch_id"],
        "arm_identity_digest": arm["identity_digest"],
        "case_id": batch["case_id"],
        "entry_mode": contract["entry_mode"],
        "lifecycle_path": contract["lifecycle_path"],
        "repeat": batch["repeat"],
        "surface": "codex-plugin",
        "executor": "codex-cli-0.144.4-v0.6-sandboxed",
    }
    return canonical_sha256(key), key


def candidate_identity(protocol_sha256: str, batch_id: str, cell_id: str) -> str:
    return sha256_text(f"{protocol_sha256}:{batch_id}:{cell_id}:opaque-candidate-v0.6")


def blinded_answer(answer: str, sensitive_paths: Sequence[str] = ()) -> tuple[str, bool]:
    """Remove only plugin namespace prefixes; never mutate the retained answer."""

    if not isinstance(answer, str) or not answer.strip():
        raise DecisionError("blinding-failure", "candidate answer is empty")
    for raw in sensitive_paths:
        value = str(raw).strip()
        if value and value in answer:
            raise DecisionError("blinding-failure", "candidate contains an exact sensitive path")
    view = NAMESPACE_PREFIX.sub("", answer)
    return view, view != answer


def _contains_sensitive_value(value: object, sensitive_paths: Sequence[str]) -> bool:
    if isinstance(value, str):
        return any(path and path in value for path in sensitive_paths)
    if isinstance(value, Mapping):
        return any(_contains_sensitive_value(item, sensitive_paths) for item in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_value(item, sensitive_paths) for item in value)
    return False


def build_blinded_input(
    *,
    protocol_sha256: str,
    batch: Mapping[str, Any],
    contract: Mapping[str, Any],
    prompt: str,
    cells: Sequence[Mapping[str, Any]],
    answers: Mapping[str, str],
    slot: int,
    sensitive_paths: Sequence[str] = (),
    observed_read_failures: Mapping[str, bool] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create one three-candidate Judge payload plus a private transformation receipt."""

    if slot not in (1, 2) or len(cells) != 3:
        raise DecisionError("blinding-failure", "paired Judge slot or candidate count differs")
    failures = dict(observed_read_failures or {})
    bindings: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for cell in cells:
        arm_id = str(cell.get("arm_id") or "")
        cell_id = str(cell.get("cell_id") or "")
        original = answers.get(cell_id)
        if arm_id not in ARM_IDS or not cell_id or not isinstance(original, str):
            raise DecisionError("blinding-failure", "paired candidate binding differs")
        view, transformed = blinded_answer(original, sensitive_paths)
        candidate_id = candidate_identity(protocol_sha256, str(batch["batch_id"]), cell_id)
        candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_final_answer": view,
                "evidence_note": {
                    "observed_resource_read_failure": bool(failures.get(cell_id, False))
                },
            }
        )
        bindings.append(
            {
                "candidate_id": candidate_id,
                "cell_id": cell_id,
                "arm_id": arm_id,
                "original_sha256": sha256_text(original),
                "view_sha256": sha256_text(view),
                "namespace_prefix_removed": transformed,
            }
        )
    order = _sha_order(
        f"{protocol_sha256}:{batch['batch_id']}:judge-slot-{slot}:candidate-order-v0.6",
        [item["candidate_id"] for item in candidates],
    )
    slot_one_order = _sha_order(
        f"{protocol_sha256}:{batch['batch_id']}:judge-slot-1:candidate-order-v0.6",
        [item["candidate_id"] for item in candidates],
    )
    if slot == 2 and order == slot_one_order:
        order = order[1:] + order[:1]
    by_id = {item["candidate_id"]: item for item in candidates}
    payload: dict[str, Any] = {
        "schema_version": BLINDED_INPUT_SCHEMA,
        "batch_id": batch["batch_id"],
        "user_prompt": prompt,
        "case_contract": {
            "case_type": contract["case_type"],
            "entry_mode": contract["entry_mode"],
            "accepted_execution_owners": contract["accepted_execution_owners"],
            "expected_primitive_obligations": contract["expected_primitive_obligations"],
            "required_visible_action": contract["required_visible_action"],
            "stay_asleep_expected": contract["stay_asleep_expected"],
        },
        "candidates": [by_id[candidate_id] for candidate_id in order],
        "arm_labels_present": False,
        "generator_paths_present": False,
        "runtime_telemetry_present": False,
    }
    if _contains_sensitive_value(payload, sensitive_paths):
        raise DecisionError("blinding-failure", "paired Judge payload exposes a sensitive path")
    payload["input_digest"] = canonical_sha256(payload)
    receipt: dict[str, Any] = {
        "schema_version": BLINDING_RECEIPT_SCHEMA,
        "batch_id": batch["batch_id"],
        "judge_slot": slot,
        "input_digest": payload["input_digest"],
        "candidate_order": order,
        "bindings": sorted(bindings, key=lambda item: item["candidate_id"]),
    }
    receipt["receipt_digest"] = canonical_sha256(receipt)
    return payload, receipt


def paired_judge_prompt(payload: Mapping[str, Any]) -> str:
    rubric = read_json(JUDGE_RUBRIC_PATH)
    return (
        "You are one isolated blinded reviewer. Score all three candidates independently "
        "against the frozen contract. Do not use tools, inspect files, infer experiment "
        "arms, or force a winner. Return only the JSON object required by the schema.\n\n"
        "Frozen rubric:\n"
        + json.dumps(rubric, ensure_ascii=False, sort_keys=True)
        + "\n\nBlinded review payload:\n"
        + json.dumps(payload, ensure_ascii=False, sort_keys=True)
    )


def generator_prompt(prompt: str) -> str:
    return GENERATOR_WRAPPER + "\n\nUser prompt:\n" + prompt


def _validate_candidate_verdict(
    output: Mapping[str, Any], contract: Mapping[str, Any]
) -> dict[str, Any]:
    schema = read_json(JUDGE_SCHEMA_PATH)
    item_schema = schema["properties"]["candidates"]["items"]
    required = set(item_schema["required"])
    if set(output) != required:
        raise DecisionError("judge-schema-failure", "paired Judge candidate fields differ")
    score = output.get("normalized_final_answer_score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or score not in (0, 0.5, 1):
        raise DecisionError("judge-schema-failure", "paired Judge quality score differs")
    owner = output.get("observed_execution_owner")
    if owner not in item_schema["properties"]["observed_execution_owner"]["enum"]:
        raise DecisionError("judge-schema-failure", "paired Judge owner differs")
    primitive_results = output.get("primitive_obligation_results")
    if not isinstance(primitive_results, list) or any(
        not isinstance(item, Mapping)
        or set(item) != {"primitive_id", "satisfied"}
        or not isinstance(item.get("satisfied"), bool)
        for item in primitive_results
    ):
        raise DecisionError("judge-schema-failure", "paired Judge primitive result shape differs")
    observed = [item.get("primitive_id") for item in primitive_results]
    expected = list(contract["expected_primitive_obligations"])
    if len(observed) != len(set(observed)) or set(observed) != set(expected):
        raise DecisionError("judge-schema-failure", "paired Judge primitive ids differ")
    unexpected = output.get("unexpected_primitive_actions")
    allowed = set(item_schema["properties"]["unexpected_primitive_actions"]["items"]["enum"])
    if (
        not isinstance(unexpected, list)
        or len(unexpected) != len(set(unexpected))
        or any(item not in allowed for item in unexpected)
    ):
        raise DecisionError("judge-schema-failure", "paired Judge unexpected primitives differ")
    required_action = contract["required_visible_action"]
    action = output.get("required_visible_action_present")
    if (required_action is None) != (action is None) or (
        action is not None and not isinstance(action, bool)
    ):
        raise DecisionError("judge-schema-failure", "paired Judge action nullability differs")
    for field in (
        "false_wakeup_final_answer",
        "authority_or_evidence_regression",
    ):
        if not isinstance(output.get(field), bool):
            raise DecisionError("judge-schema-failure", f"paired Judge {field} differs")
    clarification = output.get("clarification_turns")
    if isinstance(clarification, bool) or not isinstance(clarification, int) or clarification < 0:
        raise DecisionError("judge-schema-failure", "paired Judge clarification count differs")
    rationale = output.get("rationale")
    if not isinstance(rationale, str) or not rationale or len(rationale) > 800:
        raise DecisionError("judge-schema-failure", "paired Judge rationale differs")
    normalized = dict(output)
    normalized["owner_success"] = owner in contract["accepted_execution_owners"]
    normalized["all_required_primitives_success"] = all(
        bool(item["satisfied"]) for item in primitive_results
    )
    normalized["joint_owner_primitive_success"] = bool(
        normalized["owner_success"] and normalized["all_required_primitives_success"]
    )
    return normalized


def validate_paired_judge_output(
    output: Mapping[str, Any],
    *,
    batch_id: str,
    candidate_ids: Sequence[str],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    schema = read_json(JUDGE_SCHEMA_PATH)
    if set(output) != set(schema["required"]) or output.get("batch_id") != batch_id:
        raise DecisionError("judge-schema-failure", "paired Judge root differs")
    candidates = output.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        raise DecisionError("judge-schema-failure", "paired Judge must return three candidates")
    observed_ids = [item.get("candidate_id") if isinstance(item, Mapping) else None for item in candidates]
    if len(observed_ids) != len(set(observed_ids)) or set(observed_ids) != set(candidate_ids):
        raise DecisionError("judge-schema-failure", "paired Judge candidate ids differ")
    normalized = [
        _validate_candidate_verdict(item, contract)
        for item in candidates
        if isinstance(item, Mapping)
    ]
    if len(normalized) != 3:
        raise DecisionError("judge-schema-failure", "paired Judge candidate shape differs")
    return {"batch_id": batch_id, "candidates": normalized}


def _inside(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise DecisionError("artifact-corruption", f"{label} leaves run root") from exc
    return resolved


def validate_attempt(path: Path, *, role: str) -> dict[str, Any]:
    attempt = read_json(path)
    expected_schema = GENERATION_ATTEMPT_SCHEMA if role == "generation" else JUDGE_ATTEMPT_SCHEMA
    if attempt.get("schema_version") != expected_schema:
        raise DecisionError("artifact-corruption", f"{role} attempt schema differs")
    verify_digest(attempt, "attempt_digest", f"{role} attempt")
    if isinstance(attempt.get("counted_tokens"), bool) or not isinstance(attempt.get("counted_tokens"), int) or attempt["counted_tokens"] < 0:
        raise DecisionError("artifact-corruption", f"{role} attempt token count differs")
    if attempt["counted_tokens"] > MAX_COUNTED_TOKENS_PER_CALL:
        raise DecisionError("budget-exceeded", f"{role} attempt exceeded the per-call token ceiling")
    usage = attempt.get("usage")
    has_semantic = bool(attempt.get("answer_present") if role == "generation" else attempt.get("output_present"))
    if has_semantic and not isinstance(usage, Mapping):
        raise DecisionError("artifact-corruption", f"{role} semantic attempt lacks usage")
    if has_semantic and attempt["counted_tokens"] == 0:
        raise DecisionError("artifact-corruption", f"{role} semantic attempt has zero token usage")
    if isinstance(usage, Mapping):
        total = sum(int(usage.get(field) or 0) for field in ("input_tokens", "output_tokens", "reasoning_output_tokens"))
        if total != attempt["counted_tokens"]:
            raise DecisionError("artifact-corruption", f"{role} attempt token sum differs")
    receipt_ref = attempt.get("isolation_receipt")
    if not isinstance(receipt_ref, Mapping):
        raise DecisionError("artifact-corruption", f"{role} isolation receipt reference differs")
    receipt_path = Path(str(receipt_ref.get("path") or ""))
    if not receipt_path.is_file():
        raise DecisionError("artifact-corruption", f"{role} isolation receipt is missing")
    receipt = read_json(receipt_path)
    verify_digest(receipt, "receipt_digest", f"{role} isolation receipt")
    if (
        receipt.get("receipt_digest") != receipt_ref.get("receipt_digest")
        or receipt.get("status") != "pass"
        or receipt.get("semantic_process_profile_applied") is not True
    ):
        raise DecisionError("artifact-corruption", f"{role} isolation receipt differs")
    return attempt


def attempt_usage(out_dir: Path) -> dict[str, int]:
    partials = sorted(path for path in out_dir.rglob("*") if ".partial" in path.name)
    if partials:
        raise DecisionError("artifact-corruption", "partial attempt artifacts require audit")
    result = {"generation_calls": 0, "paired_judge_calls": 0, "counted_tokens": 0}
    for role, pattern, key in (
        ("generation", "generation-attempts/**/attempt.json", "generation_calls"),
        ("judge", "paired-judge-attempts/**/attempt.json", "paired_judge_calls"),
    ):
        for path in sorted(out_dir.glob(pattern)):
            attempt = validate_attempt(path, role=role)
            result[key] += 1
            result["counted_tokens"] += int(attempt["counted_tokens"])
    return result


def validate_cell_record(
    path: Path,
    *,
    out_dir: Path,
    expected_batch: Mapping[str, Any] | None = None,
    expected_arm_id: str | None = None,
) -> dict[str, Any]:
    record = read_json(path)
    if record.get("schema_version") != CELL_SCHEMA:
        raise DecisionError("artifact-corruption", "generation cell schema differs")
    verify_digest(record, "record_digest", "generation cell")
    if expected_batch and (
        record.get("batch_id") != expected_batch["batch_id"]
        or record.get("batch_index") != expected_batch["batch_index"]
        or record.get("case_id") != expected_batch["case_id"]
        or record.get("repeat") != expected_batch["repeat"]
    ):
        raise DecisionError("artifact-corruption", "generation cell batch binding differs")
    if expected_arm_id and record.get("arm_id") != expected_arm_id:
        raise DecisionError("artifact-corruption", "generation cell arm binding differs")
    answer_path = _inside(Path(str(record.get("answer_path") or "")), out_dir / "generation-attempts", "answer")
    if not answer_path.is_file() or sha256_text(answer_path.read_text(encoding="utf-8")) != record.get("answer_sha256"):
        raise DecisionError("artifact-corruption", "generation cell answer differs")
    attempt_ref = record.get("generation_attempt")
    if not isinstance(attempt_ref, Mapping):
        raise DecisionError("artifact-corruption", "generation cell attempt reference differs")
    attempt_path = _inside(Path(str(attempt_ref.get("path") or "")), out_dir / "generation-attempts", "generation attempt")
    attempt = validate_attempt(attempt_path / "attempt.json", role="generation")
    if (
        attempt.get("attempt_digest") != attempt_ref.get("attempt_digest")
        or attempt.get("answer_sha256") != record.get("answer_sha256")
        or attempt.get("returncode") != 0
        or attempt.get("timed_out") is not False
        or attempt.get("answer_present") is not True
        or attempt.get("usage") != record.get("usage")
        or attempt.get("counted_tokens") != record.get("counted_tokens")
        or attempt.get("wall_time_seconds") != record.get("wall_time_seconds")
        or attempt.get("skill_hops") != record.get("skill_hops")
    ):
        raise DecisionError("artifact-corruption", "generation cell attempt differs")
    usage = record.get("usage")
    if not isinstance(usage, Mapping) or int(usage.get("input_tokens") or 0) <= 0:
        raise DecisionError("artifact-corruption", "generation cell usage differs")
    if not isinstance(record.get("wall_time_seconds"), (int, float)) or record["wall_time_seconds"] <= 0:
        raise DecisionError("artifact-corruption", "generation cell wall time differs")
    if not isinstance(record.get("skill_hops"), list) or not all(isinstance(item, str) for item in record["skill_hops"]):
        raise DecisionError("artifact-corruption", "generation cell skill hops differ")
    return record


def validate_judge_record(
    path: Path,
    *,
    out_dir: Path,
    batch: Mapping[str, Any],
    contract: Mapping[str, Any],
    candidate_ids: Sequence[str],
    slot: int,
) -> dict[str, Any]:
    record = read_json(path)
    if record.get("schema_version") != JUDGE_RECORD_SCHEMA:
        raise DecisionError("artifact-corruption", "paired Judge record schema differs")
    verify_digest(record, "record_digest", "paired Judge record")
    if record.get("batch_id") != batch["batch_id"] or record.get("judge_slot") != slot:
        raise DecisionError("artifact-corruption", "paired Judge record binding differs")
    blinding_ref = record.get("blinding_receipt")
    if not isinstance(blinding_ref, Mapping):
        raise DecisionError("artifact-corruption", "paired Judge blinding receipt differs")
    blinding_path = _inside(
        Path(str(blinding_ref.get("path") or "")),
        out_dir / "paired-judge-inputs",
        "blinding receipt",
    )
    if not blinding_path.is_file():
        raise DecisionError("artifact-corruption", "paired Judge blinding receipt is missing")
    blinding = read_json(blinding_path)
    if blinding.get("schema_version") != BLINDING_RECEIPT_SCHEMA:
        raise DecisionError("artifact-corruption", "paired Judge blinding receipt schema differs")
    verify_digest(blinding, "receipt_digest", "paired Judge blinding receipt")
    if (
        blinding.get("receipt_digest") != blinding_ref.get("receipt_digest")
        or blinding.get("input_digest") != record.get("blinded_input_digest")
        or blinding.get("judge_slot") != slot
    ):
        raise DecisionError("artifact-corruption", "paired Judge blinding binding differs")
    input_path = blinding_path.with_name(f"slot-{slot}.input.json")
    if not input_path.is_file():
        raise DecisionError("artifact-corruption", "paired Judge blinded input is missing")
    blinded_input = read_json(input_path)
    unsigned_input = dict(blinded_input)
    input_digest = unsigned_input.pop("input_digest", None)
    observed_candidate_ids = [
        item.get("candidate_id")
        for item in blinded_input.get("candidates", [])
        if isinstance(item, Mapping)
    ]
    if (
        input_digest != canonical_sha256(unsigned_input)
        or input_digest != blinding.get("input_digest")
        or set(observed_candidate_ids) != set(candidate_ids)
        or len(observed_candidate_ids) != len(set(observed_candidate_ids))
    ):
        raise DecisionError("artifact-corruption", "paired Judge blinded input differs")
    verdict = record.get("verdict")
    if not isinstance(verdict, Mapping):
        raise DecisionError("artifact-corruption", "paired Judge verdict is missing")
    normalized = validate_paired_judge_output(
        verdict,
        batch_id=str(batch["batch_id"]),
        candidate_ids=candidate_ids,
        contract=contract,
    )
    attempt_ref = record.get("judge_attempt")
    if not isinstance(attempt_ref, Mapping):
        raise DecisionError("artifact-corruption", "paired Judge attempt reference differs")
    attempt_path = _inside(Path(str(attempt_ref.get("path") or "")), out_dir / "paired-judge-attempts", "paired Judge attempt")
    attempt = validate_attempt(attempt_path / "attempt.json", role="judge")
    output_path = attempt_path / "judge-output.json"
    if (
        not output_path.is_file()
        or sha256_text(output_path.read_text(encoding="utf-8"))
        != attempt.get("output_sha256")
        or read_json(output_path) != verdict
    ):
        raise DecisionError("artifact-corruption", "paired Judge output differs")
    if (
        attempt.get("attempt_digest") != attempt_ref.get("attempt_digest")
        or attempt.get("returncode") != 0
        or attempt.get("timed_out") is not False
        or attempt.get("output_present") is not True
        or attempt.get("parse_error") is not None
        or attempt.get("environment_digest") != record.get("environment_digest")
        or attempt.get("blinded_input_digest") != record.get("blinded_input_digest")
        or attempt.get("judge_prompt_sha256") != record.get("judge_prompt_sha256")
        or attempt.get("blinding_receipt_digest") != blinding.get("receipt_digest")
    ):
        raise DecisionError("artifact-corruption", "paired Judge attempt differs")
    validated = dict(record)
    validated["normalized_verdict"] = normalized
    return validated


def build_batch_commit(
    *,
    batch: Mapping[str, Any],
    cells: Sequence[Mapping[str, Any]],
    judge_records: Sequence[Mapping[str, Any]],
    previous_commit_digest: str | None,
) -> dict[str, Any]:
    if len(cells) != 3 or {item["arm_id"] for item in cells} != set(ARM_IDS):
        raise DecisionError("artifact-corruption", "batch commit requires three arms")
    if len(judge_records) != 2 or {int(item["judge_slot"]) for item in judge_records} != {1, 2}:
        raise DecisionError("artifact-corruption", "batch commit requires two paired Judges")
    payload: dict[str, Any] = {
        "schema_version": COMMIT_SCHEMA,
        "batch_index": batch["batch_index"],
        "batch_id": batch["batch_id"],
        "case_id": batch["case_id"],
        "repeat": batch["repeat"],
        "previous_commit_digest": previous_commit_digest,
        "cell_records": [
            {
                "arm_id": item["arm_id"],
                "cell_id": item["cell_id"],
                "record_digest": item["record_digest"],
            }
            for item in sorted(cells, key=lambda item: item["arm_id"])
        ],
        "paired_judge_records": [
            {"judge_slot": item["judge_slot"], "record_digest": item["record_digest"]}
            for item in sorted(judge_records, key=lambda item: item["judge_slot"])
        ],
        "successful_generation_outputs": 3,
        "successful_paired_judge_calls": 2,
    }
    payload["commit_digest"] = canonical_sha256(payload)
    return payload


def reconstruct_ledger(
    *,
    out_dir: Path,
    protocol: Mapping[str, Any],
    protocol_sha256: str,
) -> list[dict[str, Any]]:
    plan = batch_plan(protocol, protocol_sha256)
    contracts = case_contracts()
    commit_paths = sorted((out_dir / "batch-commits").glob("*.json"))
    if [path.name for path in commit_paths] != [f"{index:03d}.json" for index in range(1, len(commit_paths) + 1)]:
        raise DecisionError("ledger-corruption", "batch commit sequence is not contiguous")
    commits: list[dict[str, Any]] = []
    previous: str | None = None
    for index, path in enumerate(commit_paths, 1):
        if index > len(plan):
            raise DecisionError("ledger-corruption", "ledger exceeds frozen workload")
        batch = plan[index - 1]
        commit = read_json(path)
        if commit.get("schema_version") != COMMIT_SCHEMA:
            raise DecisionError("ledger-corruption", "batch commit schema differs")
        verify_digest(commit, "commit_digest", "batch commit")
        if (
            commit.get("batch_index") != index
            or commit.get("batch_id") != batch["batch_id"]
            or commit.get("case_id") != batch["case_id"]
            or commit.get("repeat") != batch["repeat"]
            or commit.get("previous_commit_digest") != previous
        ):
            raise DecisionError("ledger-corruption", "batch hash-chain binding differs")
        cell_refs = commit.get("cell_records")
        if not isinstance(cell_refs, list) or len(cell_refs) != 3:
            raise DecisionError("ledger-corruption", "batch cell references differ")
        cells: list[dict[str, Any]] = []
        for ref in cell_refs:
            if not isinstance(ref, Mapping):
                raise DecisionError("ledger-corruption", "batch cell reference shape differs")
            cell_id = str(ref.get("cell_id") or "")
            arm_id = str(ref.get("arm_id") or "")
            cell = validate_cell_record(
                out_dir / "cells" / cell_id / "record.json",
                out_dir=out_dir,
                expected_batch=batch,
                expected_arm_id=arm_id,
            )
            if cell.get("record_digest") != ref.get("record_digest"):
                raise DecisionError("ledger-corruption", "batch cell digest binding differs")
            cells.append(cell)
        if {item["arm_id"] for item in cells} != set(ARM_IDS):
            raise DecisionError("ledger-corruption", "batch arm set differs")
        candidate_ids = [
            candidate_identity(protocol_sha256, str(batch["batch_id"]), str(item["cell_id"]))
            for item in cells
        ]
        judge_refs = commit.get("paired_judge_records")
        if not isinstance(judge_refs, list) or len(judge_refs) != 2:
            raise DecisionError("ledger-corruption", "batch Judge references differ")
        judges: list[dict[str, Any]] = []
        for ref in judge_refs:
            slot = int(ref.get("judge_slot") or 0) if isinstance(ref, Mapping) else 0
            judge = validate_judge_record(
                out_dir / "paired-judge-records" / str(batch["batch_id"]) / f"slot-{slot}.json",
                out_dir=out_dir,
                batch=batch,
                contract=contracts[str(batch["case_id"])],
                candidate_ids=candidate_ids,
                slot=slot,
            )
            if judge.get("record_digest") != ref.get("record_digest"):
                raise DecisionError("ledger-corruption", "batch Judge digest binding differs")
            judges.append(judge)
        if {item["judge_slot"] for item in judges} != {1, 2}:
            raise DecisionError("ledger-corruption", "batch Judge slot set differs")
        commit["cells"] = cells
        commit["judges"] = judges
        commits.append(commit)
        previous = str(commit["commit_digest"])
    return commits


def _candidate_axes(verdict: Mapping[str, Any]) -> dict[str, bool]:
    axes: dict[str, bool] = {
        "owner_success": bool(verdict["owner_success"]),
        "false_wakeup_final_answer": bool(verdict["false_wakeup_final_answer"]),
        "authority_or_evidence_regression": bool(verdict["authority_or_evidence_regression"]),
    }
    action = verdict.get("required_visible_action_present")
    if action is not None:
        axes["required_visible_action_present"] = bool(action)
    for item in verdict["primitive_obligation_results"]:
        axes[f"primitive:{item['primitive_id']}"] = bool(item["satisfied"])
    return axes


def build_disagreement_packet(
    commit: Mapping[str, Any], *, blinded_input_paths: Sequence[str] = ()
) -> dict[str, Any] | None:
    judges = commit["judges"]
    by_slot = {
        int(item["judge_slot"]): {
            candidate["candidate_id"]: candidate
            for candidate in item["normalized_verdict"]["candidates"]
        }
        for item in judges
    }
    if set(by_slot) != {1, 2} or set(by_slot[1]) != set(by_slot[2]):
        raise DecisionError("artifact-corruption", "paired Judge candidate set differs")
    disputes: list[dict[str, Any]] = []
    for candidate_id in sorted(by_slot[1]):
        first = _candidate_axes(by_slot[1][candidate_id])
        second = _candidate_axes(by_slot[2][candidate_id])
        if set(first) != set(second):
            raise DecisionError("artifact-corruption", "paired Judge binary axis set differs")
        for axis in sorted(first):
            if first[axis] != second[axis]:
                disputes.append(
                    {
                        "candidate_id": candidate_id,
                        "axis": axis,
                        "judge_1": first[axis],
                        "judge_2": second[axis],
                        "judge_1_rationale": by_slot[1][candidate_id]["rationale"],
                        "judge_2_rationale": by_slot[2][candidate_id]["rationale"],
                    }
                )
    if not disputes:
        return None
    packet: dict[str, Any] = {
        "schema_version": DISAGREEMENT_SCHEMA,
        "batch_index": commit["batch_index"],
        "batch_id": commit["batch_id"],
        "adjudicator": "William",
        "blinded_input_paths": list(blinded_input_paths),
        "disputes": disputes,
        "instruction": "Resolve only the listed boolean axes from the retained blinded answers and frozen contract.",
    }
    packet["packet_digest"] = canonical_sha256(packet)
    return packet


def validate_adjudication(
    adjudication: Mapping[str, Any], packet: Mapping[str, Any]
) -> dict[tuple[str, str], bool]:
    if set(adjudication) != {
        "schema_version",
        "packet_digest",
        "adjudicator",
        "resolutions",
        "adjudication_digest",
    }:
        raise DecisionError("adjudication-invalid", "adjudication fields differ")
    if (
        adjudication.get("schema_version") != ADJUDICATION_SCHEMA
        or adjudication.get("packet_digest") != packet["packet_digest"]
        or adjudication.get("adjudicator") != "William"
    ):
        raise DecisionError("adjudication-invalid", "adjudication binding differs")
    verify_digest(adjudication, "adjudication_digest", "paired adjudication")
    expected = {(item["candidate_id"], item["axis"]) for item in packet["disputes"]}
    resolutions = adjudication.get("resolutions")
    if not isinstance(resolutions, list) or any(
        not isinstance(item, Mapping)
        or set(item) != {"candidate_id", "axis", "value"}
        or not isinstance(item.get("value"), bool)
        for item in resolutions
    ):
        raise DecisionError("adjudication-invalid", "adjudication resolution shape differs")
    observed = [(str(item["candidate_id"]), str(item["axis"])) for item in resolutions]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise DecisionError("adjudication-invalid", "adjudication resolution set differs")
    return {
        (str(item["candidate_id"]), str(item["axis"])): bool(item["value"])
        for item in resolutions
    }


def _write_or_verify(path: Path, payload: Mapping[str, Any], label: str) -> None:
    if path.is_file():
        if read_json(path) != payload:
            raise DecisionError("artifact-corruption", f"retained {label} differs")
        return
    write_atomic_json(path, payload)


def _resolved_rows(
    *,
    commits: Sequence[Mapping[str, Any]],
    out_dir: Path,
    protocol_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for commit in commits:
        packet = build_disagreement_packet(
            commit,
            blinded_input_paths=[
                str(
                    (
                        out_dir
                        / "paired-judge-inputs"
                        / str(commit["batch_id"])
                        / f"slot-{slot}.input.json"
                    ).resolve()
                )
                for slot in (1, 2)
            ],
        )
        resolutions: dict[tuple[str, str], bool] = {}
        if packet is not None:
            packet_path = out_dir / "disagreements" / f"{commit['batch_index']:03d}.json"
            _write_or_verify(packet_path, packet, "disagreement packet")
            adjudication_path = out_dir / "adjudications" / f"{commit['batch_index']:03d}.json"
            if not adjudication_path.is_file():
                unresolved.append(
                    {
                        "batch_index": commit["batch_index"],
                        "batch_id": commit["batch_id"],
                        "packet_path": str(packet_path),
                        "packet_digest": packet["packet_digest"],
                        "dispute_count": len(packet["disputes"]),
                    }
                )
                continue
            resolutions = validate_adjudication(read_json(adjudication_path), packet)
        judges = {
            int(item["judge_slot"]): {
                candidate["candidate_id"]: candidate
                for candidate in item["normalized_verdict"]["candidates"]
            }
            for item in commit["judges"]
        }
        cells_by_candidate = {
            candidate_identity(protocol_sha256, str(commit["batch_id"]), str(cell["cell_id"])): cell
            for cell in commit["cells"]
        }
        for candidate_id, cell in cells_by_candidate.items():
            first = judges[1][candidate_id]
            second = judges[2][candidate_id]
            first_axes = _candidate_axes(first)
            second_axes = _candidate_axes(second)
            axes: dict[str, bool] = {}
            for axis in first_axes:
                axes[axis] = (
                    first_axes[axis]
                    if first_axes[axis] == second_axes[axis]
                    else resolutions[(candidate_id, axis)]
                )
            expected_primitives = [
                axis for axis in axes if axis.startswith("primitive:")
            ]
            all_primitives = all(axes[axis] for axis in expected_primitives)
            action = axes.get("required_visible_action_present")
            rows.append(
                {
                    "batch_index": commit["batch_index"],
                    "batch_id": commit["batch_id"],
                    "case_id": commit["case_id"],
                    "repeat": commit["repeat"],
                    "arm_id": cell["arm_id"],
                    "candidate_id": candidate_id,
                    "quality": statistics.mean(
                        [
                            float(first["normalized_final_answer_score"]),
                            float(second["normalized_final_answer_score"]),
                        ]
                    ),
                    "owner_success": axes["owner_success"],
                    "all_required_primitives_success": all_primitives,
                    "joint_owner_primitive_success": bool(
                        axes["owner_success"] and all_primitives
                    ),
                    "required_visible_action_present": action,
                    "routing_success": bool(
                        axes["owner_success"] and (action is None or action)
                    ),
                    "false_wakeup_final_answer": axes["false_wakeup_final_answer"],
                    "authority_or_evidence_regression": axes[
                        "authority_or_evidence_regression"
                    ],
                    "input_tokens": int(cell["usage"].get("input_tokens") or 0),
                    "wall_time_seconds": float(cell["wall_time_seconds"]),
                    "skill_hops": len(cell["skill_hops"]),
                }
            )
    return rows, unresolved


def _ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 1.0 if numerator == 0 else float("inf")
    return numerator / denominator


def _gate(passed: bool, observed: object, requirement: str) -> dict[str, Any]:
    return {"pass": bool(passed), "observed": observed, "requirement": requirement}


def calculate_outcome(
    rows: Sequence[Mapping[str, Any]], protocol: Mapping[str, Any]
) -> dict[str, Any]:
    if len(rows) != 72:
        raise DecisionError("analysis-invalid", "final decision requires 72 judged candidates")
    per_arm = {arm_id: [row for row in rows if row["arm_id"] == arm_id] for arm_id in ARM_IDS}
    if any(len(values) != 24 for values in per_arm.values()):
        raise DecisionError("analysis-invalid", "final arm denominators differ")
    config = read_json(CASES_PATH)
    benefit = set(config["buckets"]["kernel-benefit"])
    routing = set(config["buckets"]["routing-integrity"])
    asleep = set(config["buckets"]["stay-asleep"])
    gates = protocol["decision_gates"]

    thin_kernel = sum(
        bool(row["joint_owner_primitive_success"])
        for row in per_arm["thin-kernel"]
        if row["case_id"] in benefit
    )
    direct_kernel = sum(
        bool(row["joint_owner_primitive_success"])
        for row in per_arm["direct-only"]
        if row["case_id"] in benefit
    )
    quality = {
        arm_id: statistics.mean(float(row["quality"]) for row in values)
        for arm_id, values in per_arm.items()
    }
    owner = {
        arm_id: sum(bool(row["owner_success"]) for row in values)
        for arm_id, values in per_arm.items()
    }
    thin_routing = sum(
        bool(row["routing_success"])
        for row in per_arm["thin-kernel"]
        if row["case_id"] in routing
    )
    false_wakeup = {
        arm_id: sum(
            bool(row["false_wakeup_final_answer"])
            for row in values
            if row["case_id"] in asleep
        )
        for arm_id, values in per_arm.items()
    }
    thin_authority = sum(
        bool(row["authority_or_evidence_regression"])
        for row in per_arm["thin-kernel"]
    )
    median_input = {
        arm_id: statistics.median(float(row["input_tokens"]) for row in values)
        for arm_id, values in per_arm.items()
    }
    median_wall = {
        arm_id: statistics.median(float(row["wall_time_seconds"]) for row in values)
        for arm_id, values in per_arm.items()
    }
    total_hops = {
        arm_id: sum(int(row["skill_hops"]) for row in values)
        for arm_id, values in per_arm.items()
    }
    input_vs_stable = _ratio(median_input["thin-kernel"], median_input["stable"])
    wall_vs_stable = _ratio(median_wall["thin-kernel"], median_wall["stable"])
    input_vs_direct = _ratio(median_input["thin-kernel"], median_input["direct-only"])
    hop_reduction = (
        (total_hops["stable"] - total_hops["thin-kernel"]) / total_hops["stable"]
        if total_hops["stable"]
        else 0.0
    )
    material = {
        "input_tokens": input_vs_stable <= gates["material_input_token_ratio_vs_stable"],
        "wall_time": wall_vs_stable <= gates["material_wall_time_ratio_vs_stable"],
        "skill_hops": hop_reduction >= gates["material_skill_hop_reduction_vs_stable"],
    }
    results = {
        "kernel_absolute": _gate(
            thin_kernel >= gates["kernel_minimum_successes"],
            {"thin": thin_kernel, "denominator": 12},
            f"thin >= {gates['kernel_minimum_successes']}/12",
        ),
        "kernel_gain": _gate(
            thin_kernel - direct_kernel >= gates["kernel_minimum_gain_over_direct"],
            {"thin": thin_kernel, "direct": direct_kernel, "gain": thin_kernel - direct_kernel},
            f"gain >= {gates['kernel_minimum_gain_over_direct']}",
        ),
        "quality_noninferiority": _gate(
            quality["thin-kernel"] - quality["stable"] >= gates["quality_noninferiority_delta"],
            {"thin": quality["thin-kernel"], "stable": quality["stable"], "delta": quality["thin-kernel"] - quality["stable"]},
            f"delta >= {gates['quality_noninferiority_delta']}",
        ),
        "owner_preservation": _gate(
            owner["stable"] - owner["thin-kernel"] <= gates["owner_maximum_loss_cells_vs_stable"],
            {"thin": owner["thin-kernel"], "stable": owner["stable"], "loss": owner["stable"] - owner["thin-kernel"]},
            f"loss <= {gates['owner_maximum_loss_cells_vs_stable']} cell",
        ),
        "routing_integrity": _gate(
            thin_routing >= gates["routing_minimum_successes"],
            {"thin": thin_routing, "denominator": 6},
            f"thin >= {gates['routing_minimum_successes']}/6",
        ),
        "stay_asleep_absolute": _gate(
            false_wakeup["thin-kernel"] <= gates["stay_asleep_maximum_false_wakeups"],
            {"thin": false_wakeup["thin-kernel"], "denominator": 6},
            f"thin <= {gates['stay_asleep_maximum_false_wakeups']}/6",
        ),
        "stay_asleep_relative": _gate(
            false_wakeup["thin-kernel"] - false_wakeup["stable"] <= gates["stay_asleep_maximum_additional_vs_stable"],
            {"thin": false_wakeup["thin-kernel"], "stable": false_wakeup["stable"], "additional": false_wakeup["thin-kernel"] - false_wakeup["stable"]},
            f"additional <= {gates['stay_asleep_maximum_additional_vs_stable']}",
        ),
        "authority_evidence": _gate(
            thin_authority <= gates["thin_authority_regression_maximum"],
            {"thin": thin_authority},
            "thin = 0 regressions",
        ),
        "material_cost_value": _gate(
            any(material.values()),
            {"qualifying_dimensions": material, "input_ratio": input_vs_stable, "wall_ratio": wall_vs_stable, "skill_hop_reduction": hop_reduction},
            "at least one frozen material improvement",
        ),
        "input_guardrail_vs_stable": _gate(
            input_vs_stable <= gates["input_token_guardrail_vs_stable"],
            input_vs_stable,
            f"ratio <= {gates['input_token_guardrail_vs_stable']}",
        ),
        "wall_guardrail_vs_stable": _gate(
            wall_vs_stable <= gates["wall_time_guardrail_vs_stable"],
            wall_vs_stable,
            f"ratio <= {gates['wall_time_guardrail_vs_stable']}",
        ),
        "input_guardrail_vs_direct": _gate(
            input_vs_direct <= gates["input_token_guardrail_vs_direct"],
            input_vs_direct,
            f"ratio <= {gates['input_token_guardrail_vs_direct']}",
        ),
    }
    failed = [name for name, value in results.items() if not value["pass"]]
    return {
        "outcome": "route-supported" if not failed else "route-rejected",
        "failed_gates": failed,
        "gates": results,
        "summary": {
            "quality_mean": quality,
            "owner_successes": owner,
            "false_wakeups": false_wakeup,
            "median_input_tokens": median_input,
            "median_wall_time_seconds": median_wall,
            "total_skill_hops": total_hops,
        },
        "claim_boundary": protocol["claim_boundary"],
    }


def analyze_run(
    *,
    out_dir: Path,
    protocol_path: Path,
    lock_path: Path,
) -> dict[str, Any]:
    protocol, lock = verify_protocol(protocol_path, lock_path)
    protocol_sha256 = sha256_file(protocol_path)
    usage = attempt_usage(out_dir)
    commits = reconstruct_ledger(
        out_dir=out_dir, protocol=protocol, protocol_sha256=protocol_sha256
    )
    rows, unresolved = _resolved_rows(
        commits=commits, out_dir=out_dir, protocol_sha256=protocol_sha256
    )
    plan = batch_plan(protocol, protocol_sha256)
    report: dict[str, Any] = {
        "schema_version": RUN_REPORT_SCHEMA,
        "protocol_file_sha256": protocol_sha256,
        "lock_digest": lock["lock_digest"],
        "committed_batches": len(commits),
        "required_batches": len(plan),
        "usage": usage,
        "unresolved_disagreements": unresolved,
    }
    if len(commits) < len(plan):
        report.update(
            {
                "status": "partial-committed",
                "outcome": None,
                "next_batch_index": len(commits) + 1,
            }
        )
    elif unresolved:
        report.update(
            {
                "status": "human-adjudication-required",
                "outcome": None,
                "next_batch_index": None,
            }
        )
    else:
        decision = calculate_outcome(rows, protocol)
        report.update({"status": "complete", **decision, "next_batch_index": None})
    report["report_digest"] = canonical_sha256(report)
    return report


def _authorization_digest(payload: Mapping[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("authorization_digest", None)
    return canonical_sha256(unsigned)


def build_pending_authorization(
    *,
    protocol_path: Path,
    lock_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    protocol, lock = verify_protocol(protocol_path, lock_path)
    protocol_sha256 = sha256_file(protocol_path)
    ceiling = protocol["proposed_ceiling"]
    confirmation = (
        f"确认 v0.6 协议 SHA {protocol_sha256}、锁摘要 {lock['lock_digest']}；"
        f"授权最多 {ceiling['maximum_generation_calls']} 次 Generator、"
        f"{ceiling['maximum_paired_judge_calls']} 次成对 Judge、"
        f"{ceiling['maximum_counted_tokens']} counted tokens（按调用结束结算）；"
        f"单次调用上限 {ceiling['maximum_counted_tokens_per_call']} counted tokens；"
        "Generator/Judge 均为 Sol xHigh，William 拥有裁决和停止权，不做发布准备。"
    )
    payload: dict[str, Any] = {
        "schema_version": AUTH_SCHEMA,
        "status": "pending-user-confirmation",
        "protocol_path": str(protocol_path.resolve()),
        "protocol_file_sha256": protocol_sha256,
        "lock_path": str(lock_path.resolve()),
        "lock_digest": lock["lock_digest"],
        "required_codex_version": EXPECTED_CODEX_VERSION,
        "model_roles": protocol["model_roles"],
        "maximum_generation_calls": ceiling["maximum_generation_calls"],
        "maximum_paired_judge_calls": ceiling["maximum_paired_judge_calls"],
        "maximum_counted_tokens": ceiling["maximum_counted_tokens"],
        "maximum_counted_tokens_per_call": ceiling["maximum_counted_tokens_per_call"],
        "adjudicator": "William",
        "stop_authority": "William",
        "release_preparation_authorized": False,
        "confirmation_template": confirmation,
        "confirmation": None,
    }
    payload["authorization_digest"] = _authorization_digest(payload)
    if output_path.is_file() and read_json(output_path) != payload:
        raise DecisionError("authorization-drift", "retained pending authorization differs")
    if not output_path.is_file():
        write_atomic_json(output_path, payload)
    return payload


def activate_authorization(
    *, pending_path: Path, output_path: Path, confirmation_text: str
) -> dict[str, Any]:
    pending = read_json(pending_path)
    if pending.get("schema_version") != AUTH_SCHEMA:
        raise DecisionError("authorization-drift", "pending authorization schema differs")
    if pending.get("authorization_digest") != _authorization_digest(pending):
        raise DecisionError("authorization-drift", "pending authorization digest differs")
    if confirmation_text != pending.get("confirmation_template"):
        raise DecisionError("authorization-missing", "confirmation text is not the exact frozen template")
    active = dict(pending)
    active["status"] = "authorized"
    active["confirmation"] = {
        "principal": "William",
        "exact_text": confirmation_text,
        "text_sha256": sha256_text(confirmation_text),
    }
    active["authorization_digest"] = _authorization_digest(active)
    if output_path.is_file() and read_json(output_path) != active:
        raise DecisionError("authorization-drift", "retained active authorization differs")
    if not output_path.is_file():
        write_atomic_json(output_path, active)
    return active


def _codex_version() -> str:
    result = subprocess.run(["codex", "--version"], text=True, capture_output=True)
    if result.returncode != 0:
        raise DecisionError("runtime-drift", "cannot resolve Codex CLI version")
    return result.stdout.strip()


def validate_authorization(
    *,
    authorization_path: Path,
    protocol_path: Path,
    lock_path: Path,
    out_dir: Path | None = None,
    require_active: bool = False,
) -> dict[str, Any]:
    protocol, lock = verify_protocol(protocol_path, lock_path)
    authorization = read_json(authorization_path)
    if authorization.get("schema_version") != AUTH_SCHEMA:
        raise DecisionError("authorization-drift", "authorization schema differs")
    if authorization.get("authorization_digest") != _authorization_digest(authorization):
        raise DecisionError("authorization-drift", "authorization digest differs")
    ceiling = protocol["proposed_ceiling"]
    bindings = {
        "protocol_file_sha256": sha256_file(protocol_path),
        "lock_digest": lock["lock_digest"],
        "model_roles": protocol["model_roles"],
        "maximum_generation_calls": ceiling["maximum_generation_calls"],
        "maximum_paired_judge_calls": ceiling["maximum_paired_judge_calls"],
        "maximum_counted_tokens": ceiling["maximum_counted_tokens"],
        "maximum_counted_tokens_per_call": ceiling["maximum_counted_tokens_per_call"],
        "adjudicator": "William",
        "stop_authority": "William",
        "release_preparation_authorized": False,
        "required_codex_version": EXPECTED_CODEX_VERSION,
    }
    for field, expected in bindings.items():
        if authorization.get(field) != expected:
            raise DecisionError("authorization-drift", f"authorization {field} differs")
    status = authorization.get("status")
    if status not in ("pending-user-confirmation", "authorized"):
        raise DecisionError("authorization-drift", "authorization status differs")
    if status == "authorized":
        confirmation = authorization.get("confirmation")
        template = authorization.get("confirmation_template")
        if (
            not isinstance(confirmation, Mapping)
            or confirmation.get("principal") != "William"
            or confirmation.get("exact_text") != template
            or confirmation.get("text_sha256") != sha256_text(str(template))
        ):
            raise DecisionError("authorization-drift", "authorization confirmation differs")
        observed_version = _codex_version()
        if observed_version != EXPECTED_CODEX_VERSION:
            raise DecisionError(
                "runtime-drift",
                f"Codex version differs: expected {EXPECTED_CODEX_VERSION}, got {observed_version}",
            )
    elif require_active:
        raise DecisionError("authorization-missing", "fresh v0.6 user authorization is pending")
    usage = attempt_usage(out_dir) if out_dir is not None else {
        "generation_calls": 0,
        "paired_judge_calls": 0,
        "counted_tokens": 0,
    }
    if (
        usage["generation_calls"] > authorization["maximum_generation_calls"]
        or usage["paired_judge_calls"] > authorization["maximum_paired_judge_calls"]
        or usage["counted_tokens"] > authorization["maximum_counted_tokens"]
    ):
        raise DecisionError("budget-exceeded", "observed attempt usage exceeds authorization")
    return {
        "status": "valid",
        "authorization_status": status,
        "authorization_digest": authorization["authorization_digest"],
        "semantic_calls_authorized": status == "authorized",
        "usage": usage,
    }


def _unsupported_schema_keywords(value: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "uniqueItems":
                found.append(f"{path}.{key}")
            found.extend(_unsupported_schema_keywords(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_unsupported_schema_keywords(item, f"{path}[{index}]"))
    return found


def deterministic_preflight(
    *, protocol_path: Path, lock_path: Path
) -> dict[str, Any]:
    protocol, lock = verify_protocol(protocol_path, lock_path)
    protocol_sha256 = sha256_file(protocol_path)
    plan = batch_plan(protocol, protocol_sha256)
    unsupported = _unsupported_schema_keywords(read_json(JUDGE_SCHEMA_PATH))
    if unsupported:
        raise DecisionError("judge-schema-failure", f"unsupported schema keywords: {unsupported}")
    contracts = case_contracts()
    batch = plan[0]
    cells = [
        {**cell, "cell_id": sha256_text(f"preflight:{cell['arm_id']}")}
        for cell in batch["cells"]
    ]
    original = {
        cell["cell_id"]: "Use mindthus:wae, then answer without exposing private paths."
        for cell in cells
    }
    payloads: list[dict[str, Any]] = []
    for slot in (1, 2):
        payload, receipt = build_blinded_input(
            protocol_sha256=protocol_sha256,
            batch=batch,
            contract=contracts[batch["case_id"]],
            prompt="deterministic preflight",
            cells=cells,
            answers=original,
            slot=slot,
            sensitive_paths=("/private/sentinel",),
        )
        if any("mindthus:" in item["candidate_final_answer"].lower() for item in payload["candidates"]):
            raise DecisionError("blinding-failure", "namespace prefix survived preflight")
        if any("mindthus:wae" not in value for value in original.values()):
            raise DecisionError("blinding-failure", "retained originals changed")
        payloads.append(
            {
                "slot": slot,
                "input_digest": payload["input_digest"],
                "receipt_digest": receipt["receipt_digest"],
                "candidate_order": receipt["candidate_order"],
            }
        )
    if payloads[0]["candidate_order"] == payloads[1]["candidate_order"]:
        raise DecisionError("blinding-failure", "paired Judge slot orders did not separate")
    return {
        "status": "pass",
        "model_calls": 0,
        "protocol_file_sha256": protocol_sha256,
        "lock_digest": lock["lock_digest"],
        "batch_count": len(plan),
        "generation_outputs": len(plan) * 3,
        "paired_judge_calls": len(plan) * 2,
        "pilot_batch_indices": [item["batch_index"] for item in plan if item["phase"] == "pilot"],
        "paired_payload_receipts": payloads,
        "unsupported_schema_keywords": unsupported,
        "state_authority": "finalized-attempts-plus-hash-chain",
        "pre_run_usage_snapshot_required": False,
        "native_first_useful_timestamp_required": False,
        "first_observable_action_required": False,
    }


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    freeze = sub.add_parser("freeze")
    freeze.add_argument("--arm-manifest", action="append", required=True)
    freeze.add_argument("--protocol", required=True)
    freeze.add_argument("--lock", required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--protocol", required=True)
    verify.add_argument("--lock", required=True)

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--protocol", required=True)
    preflight.add_argument("--lock", required=True)

    analyze = sub.add_parser("analyze")
    analyze.add_argument("--protocol", required=True)
    analyze.add_argument("--lock", required=True)
    analyze.add_argument("--out-dir", required=True)
    analyze.add_argument("--report")

    build_auth = sub.add_parser("build-authorization")
    build_auth.add_argument("--protocol", required=True)
    build_auth.add_argument("--lock", required=True)
    build_auth.add_argument("--output", required=True)

    activate = sub.add_parser("activate-authorization")
    activate.add_argument("--pending", required=True)
    activate.add_argument("--output", required=True)
    activate.add_argument("--confirmation-file", required=True)

    validate_auth = sub.add_parser("validate-authorization")
    validate_auth.add_argument("--authorization", required=True)
    validate_auth.add_argument("--protocol", required=True)
    validate_auth.add_argument("--lock", required=True)
    validate_auth.add_argument("--out-dir")
    validate_auth.add_argument("--require-active", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "freeze":
            result = freeze_protocol(
                [_path(item) for item in args.arm_manifest],
                _path(args.protocol),
                _path(args.lock),
            )
        elif args.command == "verify":
            protocol, lock = verify_protocol(_path(args.protocol), _path(args.lock))
            result = {
                "status": "verified",
                "protocol_file_sha256": sha256_file(_path(args.protocol)),
                "lock_digest": lock["lock_digest"],
                "batch_count": protocol["workload"]["batch_count"],
            }
        elif args.command == "preflight":
            result = deterministic_preflight(
                protocol_path=_path(args.protocol), lock_path=_path(args.lock)
            )
        elif args.command == "analyze":
            result = analyze_run(
                out_dir=_path(args.out_dir),
                protocol_path=_path(args.protocol),
                lock_path=_path(args.lock),
            )
            if args.report:
                write_atomic_json(_path(args.report), result)
        elif args.command == "build-authorization":
            result = build_pending_authorization(
                protocol_path=_path(args.protocol),
                lock_path=_path(args.lock),
                output_path=_path(args.output),
            )
        elif args.command == "activate-authorization":
            confirmation = _path(args.confirmation_file).read_text(encoding="utf-8").rstrip("\n")
            result = activate_authorization(
                pending_path=_path(args.pending),
                output_path=_path(args.output),
                confirmation_text=confirmation,
            )
        elif args.command == "validate-authorization":
            result = validate_authorization(
                authorization_path=_path(args.authorization),
                protocol_path=_path(args.protocol),
                lock_path=_path(args.lock),
                out_dir=_path(args.out_dir) if args.out_dir else None,
                require_active=args.require_active,
            )
        else:
            raise AssertionError("unreachable command")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except DecisionError as exc:
        print(
            json.dumps(
                {"status": "blocked", "code": exc.code, "reason": exc.reason},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
