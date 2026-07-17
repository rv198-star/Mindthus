#!/usr/bin/env python3
"""Run the deterministic, model-free Mindthus Beta.2 orchestration rehearsal."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from mindthus_beta2_telemetry import build_turn_telemetry  # noqa: E402


SEALER = BETA_ROOT / "runtime" / "seal-arm-manifest.py"
PROTOCOL_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol.py"
PROTOCOL_VALIDATORS = {
    "0.1": PROTOCOL_VALIDATOR,
    "0.2": BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.2.py",
}
MATRIX_LINTER = BETA_ROOT / "runtime" / "lint-case-matrix.py"
REQUIRED_ARMS = {"stable", "direct-only", "thin-kernel"}
KNOWN_SURFACES = {"codex-plugin", "claude-plugin"}
CLAIMS_UNAVAILABLE = [
    "real-model final-answer quality or noninferiority",
    "real execution-owner fidelity",
    "real primitive recall, precision, or Kernel benefit",
    "real token, wall-time, or first-useful-action distributions",
    "real host hook behavior outside the deterministic fixture",
    "sealed-case blindness until independent custodian attestation",
    "matched-evaluation Hold/Stop/continue recommendation",
    "release readiness or Stable promotion",
]


class DryRunVeto(RuntimeError):
    def __init__(self, veto_id: str, reason: str):
        super().__init__(reason)
        self.veto_id = veto_id
        self.reason = reason


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


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


def with_digest(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    result = dict(payload)
    result[field] = canonical_sha256(result)
    return result


def verify_embedded_digest(payload: Mapping[str, Any], field: str, label: str) -> None:
    unsigned = dict(payload)
    observed = unsigned.pop(field, None)
    if observed != canonical_sha256(unsigned):
        raise DryRunVeto("protocol-or-arm-drift", f"{label} digest mismatch")


def run_check(command: list[str], *, veto_id: str, label: str) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise DryRunVeto(veto_id, f"{label} failed: {detail}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"status": "ok", "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest()}


def load_plan(plan_path: Path) -> dict[str, Any]:
    plan = read_json(plan_path)
    if plan.get("schema_version") not in {
        "mindthus-beta2-dry-run-plan-v0.1",
        "mindthus-beta2-dry-run-plan-v0.2",
    }:
        raise DryRunVeto("protocol-or-arm-drift", "unsupported dry-run plan schema")
    verify_embedded_digest(plan, "plan_digest", "dry-run plan")
    if plan.get("executor") != "deterministic-mock-only" or plan.get("model_execution_allowed") is not False:
        raise DryRunVeto("protocol-or-arm-drift", "plan does not forbid model execution")
    return plan


def verify_protocol_and_matrix(plan: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    protocol_path = Path(str(plan["protocol_path"]))
    lock_path = Path(str(plan["protocol_lock_path"]))
    matrix_path = Path(str(plan["case_matrix_path"]))
    if not protocol_path.is_file() or sha256_file(protocol_path) != plan.get("protocol_sha256"):
        raise DryRunVeto("protocol-or-arm-drift", "frozen protocol path or digest differs")
    if not matrix_path.is_file() or sha256_file(matrix_path) != plan.get("case_matrix_sha256"):
        raise DryRunVeto("protocol-or-arm-drift", "case matrix path or digest differs")
    protocol = read_json(protocol_path)
    protocol_version = str(protocol.get("protocol_version") or "")
    validator_path = PROTOCOL_VALIDATORS.get(protocol_version)
    if validator_path is None:
        raise DryRunVeto("protocol-or-arm-drift", "protocol version has no dry-run validator")
    if protocol_version == "0.2":
        planned_validator = Path(str(plan.get("protocol_validator_path") or ""))
        if planned_validator.resolve(strict=False) != validator_path.resolve(strict=False):
            raise DryRunVeto("protocol-or-arm-drift", "v0.2 protocol validator path differs")
        if not planned_validator.is_file() or sha256_file(planned_validator) != plan.get(
            "protocol_validator_sha256"
        ):
            raise DryRunVeto("protocol-or-arm-drift", "v0.2 protocol validator digest differs")
        expected_plan_schema = "mindthus-beta2-dry-run-plan-v0.2"
    else:
        expected_plan_schema = "mindthus-beta2-dry-run-plan-v0.1"
    if plan.get("schema_version") != expected_plan_schema:
        raise DryRunVeto("protocol-or-arm-drift", "dry-run plan/protocol versions differ")
    protocol_surfaces = list(protocol.get("workload", {}).get("host_surfaces", []))
    if list(plan.get("supported_surfaces", [])) != protocol_surfaces:
        raise DryRunVeto("protocol-or-arm-drift", "dry-run surfaces differ from frozen workload")
    protocol_report = run_check(
        [
            "python3",
            str(validator_path),
            "validate",
            "--protocol",
            str(protocol_path),
            "--lock",
            str(lock_path),
        ],
        veto_id="protocol-or-arm-drift",
        label="frozen protocol validation",
    )
    run_check(
        ["python3", str(MATRIX_LINTER), "--matrix", str(matrix_path)],
        veto_id="protocol-or-arm-drift",
        label="case matrix validation",
    )
    matrix = read_json(matrix_path)
    lock = read_json(lock_path)
    if protocol_report.get("protocol_sha256") != plan.get("protocol_sha256"):
        raise DryRunVeto("protocol-or-arm-drift", "lock does not resolve the plan protocol digest")
    return protocol, matrix, lock


def apply_observation_faults(
    observations: list[dict[str, Any]],
    fault: str | None,
) -> list[dict[str, Any]]:
    changed = copy.deepcopy(observations)
    if not changed:
        return changed
    if fault == "co-enable-contamination":
        changed[0]["active_mindthus_coordinates"] = [
            "mindthus@mindthus",
            "mindthus-beta@mindthus-beta",
        ]
    elif fault == "wrong-artifact-hash":
        changed[0]["package_tree_sha256"] = "0" * 64
    elif fault == "wrong-hook-state":
        changed[0]["hook_state"] = (
            "disabled" if changed[0]["hook_state"] != "disabled" else "fired"
        )
    elif fault == "path-resource-failure":
        changed[0]["resource_probe_path"] = "/definitely/missing/beta2-resource"
    return changed


def verify_arm_set(
    plan: Mapping[str, Any],
    *,
    fault: str | None,
) -> list[dict[str, Any]]:
    manifest_paths = [Path(str(value)) for value in plan.get("arm_manifests", [])]
    required_surfaces = set(plan.get("supported_surfaces", []))
    if not required_surfaces or not required_surfaces.issubset(KNOWN_SURFACES):
        raise DryRunVeto("protocol-or-arm-drift", "dry-run surfaces are missing or unsupported")
    expected_manifest_count = len(required_surfaces) * len(REQUIRED_ARMS)
    if len(manifest_paths) != expected_manifest_count or len(
        {str(path.resolve()) for path in manifest_paths}
    ) != expected_manifest_count:
        raise DryRunVeto(
            "cross-arm-contamination",
            f"dry-run requires {expected_manifest_count} distinct arm manifests",
        )
    run_check(
        ["python3", str(SEALER), "verify-set", *[str(path) for path in manifest_paths]],
        veto_id="protocol-or-arm-drift",
        label="sealed arm set verification",
    )
    manifests = [read_json(path) for path in manifest_paths]
    observed_pairs = {(item.get("surface"), item.get("arm_id")) for item in manifests}
    required_pairs = {
        (surface, arm) for surface in required_surfaces for arm in REQUIRED_ARMS
    }
    if observed_pairs != required_pairs:
        raise DryRunVeto("cross-arm-contamination", "arm/surface matrix is incomplete or duplicated")
    homes = [str(item.get("host", {}).get("home")) for item in manifests]
    if len(homes) != len(set(homes)):
        raise DryRunVeto("cross-arm-contamination", "source host home is shared across arms")
    for manifest in manifests:
        if manifest.get("model") != {"id": "deterministic-mock", "reasoning": "none"}:
            raise DryRunVeto("protocol-or-arm-drift", "dry-run arm permits a non-mock model")
        if manifest.get("tools") != ["deterministic-mock"]:
            raise DryRunVeto("protocol-or-arm-drift", "dry-run arm permits non-mock tools")

    observations = apply_observation_faults(
        [dict(item) for item in plan.get("host_observations", [])],
        fault,
    )
    by_path = {str(Path(item["manifest_path"]).resolve()): item for item in observations}
    if set(by_path) != {str(path.resolve()) for path in manifest_paths}:
        raise DryRunVeto("protocol-or-arm-drift", "host observations do not match arm manifests")
    for path, manifest in zip(manifest_paths, manifests):
        observation = by_path[str(path.resolve())]
        coordinates = observation.get("active_mindthus_coordinates", [])
        if len(coordinates) != 1:
            raise DryRunVeto(
                "cross-arm-contamination",
                f"co-enable contamination in {manifest['surface']}/{manifest['arm_id']}",
            )
        expected_coordinates = manifest["host"]["plugin_list"]["active_mindthus_coordinates"]
        if coordinates != expected_coordinates:
            raise DryRunVeto("cross-arm-contamination", "observed namespace differs from sealed arm")
        checks = {
            "identity_digest": manifest["identity_digest"],
            "hook_state": manifest["carrier"]["hook_state"],
            "package_tree_sha256": manifest["package"]["tree_sha256"],
            "ambient_context_sha256": canonical_sha256(manifest["ambient_context"]),
        }
        for field, expected in checks.items():
            if observation.get(field) != expected:
                raise DryRunVeto(
                    "protocol-or-arm-drift",
                    f"{field} differs for {manifest['surface']}/{manifest['arm_id']}",
                )
        resource_path = Path(str(observation.get("resource_probe_path")))
        if not resource_path.is_file():
            raise DryRunVeto("protocol-or-arm-drift", f"resource path is unavailable: {resource_path}")
    return manifests


def verify_judge_environment(
    plan: Mapping[str, Any],
    manifests: Iterable[Mapping[str, Any]],
    *,
    fault: str | None,
) -> dict[str, Any]:
    path = Path(str(plan["judge_environment_path"]))
    if not path.is_file() or sha256_file(path) != plan.get("judge_environment_sha256"):
        raise DryRunVeto("judge-environment-contamination", "judge environment receipt differs")
    environment = read_json(path)
    unsigned = dict(environment)
    digest = unsigned.pop("environment_digest", None)
    if digest != canonical_sha256(unsigned):
        raise DryRunVeto("judge-environment-contamination", "judge environment digest mismatch")
    if fault == "judge-environment-contamination":
        environment = dict(environment)
        environment["active_mindthus_coordinates"] = ["mindthus@mindthus"]
    if environment.get("executor") != "deterministic-mock-judge":
        raise DryRunVeto("judge-environment-contamination", "judge executor is not deterministic")
    if environment.get("active_mindthus_coordinates") or environment.get("superpowers_enabled") is not False:
        raise DryRunVeto("judge-environment-contamination", "judge environment contains forbidden skills")
    if environment.get("generator_home_access") is not False:
        raise DryRunVeto("judge-environment-contamination", "judge can access generator homes")
    judge_home = str(Path(str(environment.get("home"))).resolve())
    generator_homes = {
        str(Path(str(item["host"]["home"])).resolve()) for item in manifests
    }
    if judge_home in generator_homes:
        raise DryRunVeto("judge-environment-contamination", "judge home overlaps a generator home")
    return environment


def verify_fault_catalog(plan: Mapping[str, Any], fault: str | None) -> dict[str, str]:
    catalog_path = Path(str(plan.get("negative_fixture_catalog")))
    if not catalog_path.is_file():
        raise DryRunVeto("protocol-or-arm-drift", "negative fixture catalog is missing")
    catalog = read_json(catalog_path)
    faults = {item["fault"]: item["expected_veto"] for item in catalog.get("faults", [])}
    if fault and fault not in faults:
        raise DryRunVeto("protocol-or-arm-drift", f"unknown deterministic fault: {fault}")
    return faults


def case_map_for_plan(
    plan: Mapping[str, Any],
    protocol: Mapping[str, Any],
    matrix: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    all_cases = {case["case_id"]: case for case in matrix.get("cases", [])}
    selected = list(plan.get("dry_run_case_ids", []))
    if len(selected) != len(set(selected)):
        raise DryRunVeto("untraceable-or-partial-artifact", "dry-run case list contains a duplicate")
    if not set(selected).issubset(set(protocol["workload"]["matched_case_ids"])):
        raise DryRunVeto("protocol-or-arm-drift", "dry-run case lies outside frozen matched workload")
    if not set(selected).issubset(all_cases):
        raise DryRunVeto("protocol-or-arm-drift", "dry-run case is absent from frozen matrix")
    cases = {case_id: all_cases[case_id] for case_id in selected}
    lifecycles = {case["lifecycle_path"] for case in cases.values()}
    if lifecycles != set(plan.get("required_lifecycle_paths", [])):
        raise DryRunVeto("protocol-or-arm-drift", "startup/resume/clear/compact plumbing is incomplete")
    return cases


def expected_cells(
    manifests: Iterable[Mapping[str, Any]],
    cases: Mapping[str, Mapping[str, Any]],
    protocol_digest: str,
    *,
    fault: str | None,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for manifest in sorted(manifests, key=lambda item: (item["surface"], item["arm_id"])):
        for case_id in sorted(cases):
            case = cases[case_id]
            key = {
                "protocol_sha256": protocol_digest,
                "arm_digest": manifest["identity_digest"],
                "surface": manifest["surface"],
                "case_id": case_id,
                "entry_mode": case["entry_mode"],
                "lifecycle_path": case["lifecycle_path"],
                "repeat": 1,
                "executor": "deterministic-mock-only",
            }
            digest = canonical_sha256(key)
            cells.append(
                {
                    "cell_id": digest,
                    "cell_key": key,
                    "cell_key_digest": digest,
                    "manifest": manifest,
                    "case": case,
                }
            )
    if fault == "duplicate-cell" and cells:
        cells.append(copy.deepcopy(cells[0]))
    digests = [cell["cell_key_digest"] for cell in cells]
    if len(digests) != len(set(digests)):
        raise DryRunVeto("untraceable-or-partial-artifact", "duplicate logical cell detected")
    return cells


def materialized_home_payload(
    manifest: Mapping[str, Any],
    target: Path,
) -> tuple[dict[str, Any], list[tuple[Path, Path]]]:
    copies: list[tuple[Path, Path]] = []
    config_receipts: list[dict[str, Any]] = []
    for index, receipt in enumerate(manifest["host"]["config_files"], 1):
        source = Path(receipt["path"])
        destination = target / "config" / f"{index:02d}-{source.name}"
        copies.append((source, destination))
        config_receipts.append(
            {"path": str(destination), "sha256": receipt["sha256"], "kind": "host-config"}
        )
    context_receipts: list[dict[str, Any]] = []
    for index, receipt in enumerate(manifest["ambient_context"]["files"], 1):
        source = Path(receipt["path"])
        destination = target / "context" / f"{index:02d}-{receipt['id']}-{source.name}"
        copies.append((source, destination))
        context_receipts.append(
            {
                "path": str(destination),
                "sha256": receipt["sha256"],
                "kind": receipt["kind"],
                "id": receipt["id"],
            }
        )
    base = {
        "schema_version": "mindthus-beta2-materialized-home-v0.1",
        "surface": manifest["surface"],
        "arm_id": manifest["arm_id"],
        "arm_digest": manifest["identity_digest"],
        "source_home_path_sha256": hashlib.sha256(
            str(manifest["host"]["home"]).encode("utf-8")
        ).hexdigest(),
        "package_coordinate": manifest["package"]["coordinate"],
        "package_tree_sha256": manifest["package"]["tree_sha256"],
        "active_mindthus_coordinates": manifest["host"]["plugin_list"][
            "active_mindthus_coordinates"
        ],
        "hook_state": manifest["carrier"]["hook_state"],
        "config_receipts": config_receipts,
        "context_receipts": context_receipts,
        "model_execution_allowed": False,
    }
    return with_digest(base, "home_receipt_digest"), copies


def materialize_homes(
    manifests: Iterable[Mapping[str, Any]],
    out_dir: Path,
    *,
    resume: bool,
) -> dict[str, str]:
    manifest_list = list(manifests)
    receipts: dict[str, str] = {}
    for manifest in manifest_list:
        target = out_dir / "materialized-homes" / manifest["surface"] / manifest["arm_id"]
        receipt_path = target / "home-receipt.json"
        expected, copies = materialized_home_payload(manifest, target)
        if receipt_path.is_file():
            if not resume:
                raise DryRunVeto("untraceable-or-partial-artifact", "materialized home already exists")
            observed = read_json(receipt_path)
            if observed != expected:
                raise DryRunVeto("protocol-or-arm-drift", "materialized home receipt changed")
            verify_embedded_digest(observed, "home_receipt_digest", "materialized home")
            for receipt in [*observed["config_receipts"], *observed["context_receipts"]]:
                path = Path(receipt["path"])
                if not path.is_file() or sha256_file(path) != receipt["sha256"]:
                    raise DryRunVeto("protocol-or-arm-drift", "materialized home file changed")
        else:
            if target.exists() and any(target.iterdir()):
                raise DryRunVeto("untraceable-or-partial-artifact", "partial materialized home")
            for source, destination in copies:
                if not source.is_file():
                    raise DryRunVeto("protocol-or-arm-drift", f"home source file is missing: {source}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            write_atomic_json(receipt_path, expected)
        receipts[manifest["identity_digest"]] = expected["home_receipt_digest"]
    if len(receipts) != len(manifest_list):
        raise DryRunVeto("cross-arm-contamination", "materialized home identities are not unique")
    return receipts


def scan_partial_writes(out_dir: Path) -> None:
    partials = sorted(out_dir.rglob("*.partial")) if out_dir.exists() else []
    if partials:
        raise DryRunVeto(
            "untraceable-or-partial-artifact",
            f"partial writes are present: {[str(path) for path in partials]}",
        )


def state_payload(base: Mapping[str, Any], completed: Mapping[str, str], status: str) -> dict[str, Any]:
    return with_digest(
        {
            **base,
            "status": status,
            "completed_cells": dict(sorted(completed.items())),
        },
        "state_digest",
    )


def verify_cell_record(record: Mapping[str, Any]) -> None:
    verify_embedded_digest(record, "record_digest", "cell record")
    if record.get("schema_version") != "mindthus-beta2-dry-run-cell-v0.1":
        raise DryRunVeto("untraceable-or-partial-artifact", "cell schema differs")
    telemetry = record.get("telemetry", {})
    if telemetry.get("evidence_gate", {}).get("status") != "pass":
        raise DryRunVeto("missing-primary-native-evidence", "retained cell telemetry is blocked")


def existing_cells(
    out_dir: Path,
    expected: Mapping[str, Mapping[str, Any]],
    *,
    resume: bool,
) -> dict[str, str]:
    completed: dict[str, str] = {}
    logical: dict[str, Path] = {}
    for record_path in sorted((out_dir / "cells").glob("*/record.json")):
        record = read_json(record_path)
        verify_cell_record(record)
        cell_id = str(record.get("cell_id"))
        key_digest = str(record.get("cell_key_digest"))
        if cell_id not in expected:
            raise DryRunVeto("untraceable-or-partial-artifact", f"unexpected cell artifact: {cell_id}")
        if key_digest in logical:
            raise DryRunVeto("untraceable-or-partial-artifact", "duplicate completed logical cell")
        logical[key_digest] = record_path
        if record.get("cell_key") != expected[cell_id]["cell_key"]:
            raise DryRunVeto("protocol-or-arm-drift", "completed cell key differs")
        completed[cell_id] = str(record["record_digest"])
    if completed and not resume:
        raise DryRunVeto("untraceable-or-partial-artifact", "completed cells require --resume")
    return completed


def deterministic_raw_turn(cell: Mapping[str, Any], *, omit_native_latency: bool) -> dict[str, Any]:
    digest = cell["cell_key_digest"]
    seed = int(digest[:8], 16)
    duration = round(0.4 + (seed % 400) / 1000, 3)
    first_latency = round(duration * 0.4, 3)
    case = cell["case"]
    package_root = Path(cell["manifest"]["package"]["root"])
    commands = [
        f"Read {package_root / 'skills' / skill / 'SKILL.md'}"
        for skill in case.get("required_skill_loads", [])
    ]
    native = {"lifecycle_event": case["expected_lifecycle_events"]}
    if not omit_native_latency:
        native["first_useful_action_latency_seconds"] = first_latency
    return {
        "usage": {
            "input_tokens": 200 + seed % 80,
            "cached_input_tokens": 20 + seed % 20,
            "output_tokens": 40 + seed % 30,
            "reasoning_output_tokens": 10 + seed % 15,
        },
        "duration_seconds": duration,
        "native_telemetry": native,
        "loaded_commands": commands,
        "answer": "Deterministic fixture candidate; no semantic model output.",
        "agent_messages": [],
        "returncode": 0,
        "timed_out": False,
    }


def write_once(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists():
        if read_json(path) != payload:
            raise DryRunVeto("untraceable-or-partial-artifact", f"existing artifact differs: {path}")
        return
    write_atomic_json(path, payload)


def execute_cell(
    cell: Mapping[str, Any],
    out_dir: Path,
    home_receipts: Mapping[str, str],
    judge_environment: Mapping[str, Any],
    *,
    omit_native_latency: bool,
) -> dict[str, Any]:
    manifest = cell["manifest"]
    case = cell["case"]
    raw_turn = deterministic_raw_turn(cell, omit_native_latency=omit_native_latency)
    telemetry = build_turn_telemetry(
        raw_turn,
        context={
            "case_id": case["case_id"],
            "turn_index": 1,
            "entry_mode": case["entry_mode"],
            "execution_root": manifest["host"]["execution_root"],
            "allowed_roots": [manifest["package"]["root"], manifest["host"]["execution_root"]],
            "arm_manifest": manifest,
            "judge_telemetry": {"clarification_turns": 0},
        },
    )
    if telemetry["evidence_gate"]["status"] != "pass":
        raise DryRunVeto(
            "missing-primary-native-evidence",
            f"synthetic telemetry gate blocked {cell['cell_id']}: {telemetry['evidence_gate']['reasons']}",
        )

    blinded_output_id = hashlib.sha256(
        f"{cell['cell_key_digest']}:blinded-output".encode("utf-8")
    ).hexdigest()
    candidate_output = "Deterministic fixture candidate; semantic quality is unavailable."
    judge_input = with_digest(
        {
            "schema_version": "mindthus-beta2-dry-run-judge-input-v0.1",
            "blinded_output_id": blinded_output_id,
            "case_contract": {
                "case_id": case["case_id"],
                "case_type": case["case_type"],
                "accepted_execution_owners": case["accepted_execution_owners"],
                "expected_primitive_obligations": case["expected_primitive_obligations"],
                "required_visible_action": case["required_visible_action"],
                "stay_asleep_expected": case["stay_asleep_expected"],
            },
            "candidate_output": candidate_output,
            "contains_arm_label": False,
            "contains_runtime_telemetry": False,
            "contains_generator_path": False,
            "judge_environment_digest": judge_environment["environment_digest"],
            "semantic_judgment_allowed": False,
        },
        "judge_input_digest",
    )
    judge_input_path = out_dir / "judge-inputs" / f"{blinded_output_id}.json"
    write_once(judge_input_path, judge_input)
    judge_receipts: list[dict[str, Any]] = []
    for index in (1, 2):
        judge_record = with_digest(
            {
                "schema_version": "mindthus-beta2-dry-run-judge-record-v0.1",
                "blinded_output_id": blinded_output_id,
                "judge_slot": index,
                "executor": "deterministic-mock-judge",
                "status": "plumbing-only",
                "semantic_score": None,
                "provenance": "deterministic-fixture",
                "model_call_performed": False,
            },
            "judge_record_digest",
        )
        judge_path = out_dir / "judge-records" / blinded_output_id / f"judge-{index}.json"
        write_once(judge_path, judge_record)
        judge_receipts.append(
            {
                "judge_slot": index,
                "path": str(judge_path),
                "sha256": sha256_file(judge_path),
                "record_digest": judge_record["judge_record_digest"],
            }
        )

    source_receipt = canonical_sha256(case["source"])
    record = with_digest(
        {
            "schema_version": "mindthus-beta2-dry-run-cell-v0.1",
            "cell_id": cell["cell_id"],
            "cell_key": cell["cell_key"],
            "cell_key_digest": cell["cell_key_digest"],
            "plan_executor": "deterministic-mock-only",
            "protocol_sha256": cell["cell_key"]["protocol_sha256"],
            "arm_digest": manifest["identity_digest"],
            "materialized_home_receipt_digest": home_receipts[manifest["identity_digest"]],
            "case_source_receipt": source_receipt,
            "synthetic_generation": {
                "candidate_output_sha256": hashlib.sha256(candidate_output.encode("utf-8")).hexdigest(),
                "model_call_performed": False,
                "semantic_output": False,
            },
            "telemetry": telemetry,
            "judge_input": {
                "path": str(judge_input_path),
                "sha256": sha256_file(judge_input_path),
                "judge_input_digest": judge_input["judge_input_digest"],
            },
            "judge_records": judge_receipts,
            "semantic_claims_available": [],
        },
        "record_digest",
    )
    record_path = out_dir / "cells" / cell["cell_id"] / "record.json"
    if record_path.exists():
        raise DryRunVeto("untraceable-or-partial-artifact", "completed cell would be overwritten")
    write_atomic_json(record_path, record)
    return record


def report_payload(
    *,
    status: str,
    plan: Mapping[str, Any] | None,
    protocol_digest: str | None,
    lock_digest: str | None,
    expected_count: int,
    completed_count: int,
    new_count: int,
    skipped_count: int,
    surfaces: Iterable[str] = (),
    arms: Iterable[str] = (),
    lifecycles: Iterable[str] = (),
    fault: str | None = None,
    veto_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-dry-run-report-v0.1",
        "status": status,
        "executor": "deterministic-mock-only",
        "plan_digest": plan.get("plan_digest") if plan else None,
        "protocol_sha256": protocol_digest,
        "protocol_lock_digest": lock_digest,
        "expected_cell_count": expected_count,
        "completed_cell_count": completed_count,
        "new_cell_count": new_count,
        "skipped_completed_cell_count": skipped_count,
        "surfaces": sorted(set(surfaces)),
        "arms": sorted(set(arms)),
        "lifecycle_paths": sorted(set(lifecycles)),
        "model_calls": 0,
        "judge_model_calls": 0,
        "semantic_model_output_count": 0,
        "semantic_claims_available": [],
        "orchestration_claims_available": [
            "sealed identity and isolation preflight mechanics",
            "deterministic lifecycle event plumbing",
            "provenance-aware telemetry and missing-data veto mechanics",
            "atomic cell artifacts and non-overwriting resume",
            "blinded judge-envelope and contamination checks",
        ] if status == "passed" else [],
        "claims_unavailable_until_real_model_execution": CLAIMS_UNAVAILABLE,
        "release_readiness": "not-assessed",
        "fault": fault,
        "veto_id": veto_id,
        "reason": reason,
    }
    return with_digest(payload, "report_digest")


def run_dry_run(
    plan_path: Path,
    out_dir: Path,
    *,
    resume: bool,
    interrupt_after: int | None,
    fault: str | None,
) -> tuple[dict[str, Any], int]:
    plan = load_plan(plan_path)
    fault_catalog = verify_fault_catalog(plan, fault)
    out_dir.mkdir(parents=True, exist_ok=True)
    if fault == "partial-write":
        partial = out_dir / "cells" / "orphan" / "record.json.partial"
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_text("partial", encoding="utf-8")
    scan_partial_writes(out_dir)
    protocol, matrix, lock = verify_protocol_and_matrix(plan)
    manifests = verify_arm_set(plan, fault=fault)
    judge_environment = verify_judge_environment(plan, manifests, fault=fault)
    cases = case_map_for_plan(plan, protocol, matrix)
    cells = expected_cells(
        manifests,
        cases,
        str(plan["protocol_sha256"]),
        fault=fault,
    )
    expected = {cell["cell_id"]: cell for cell in cells}
    state_path = out_dir / "run-manifest.json"
    state_base = {
        "schema_version": "mindthus-beta2-dry-run-state-v0.1",
        "plan_digest": plan["plan_digest"],
        "protocol_sha256": plan["protocol_sha256"],
        "protocol_lock_digest": lock["lock_digest"],
        "expected_cell_ids": sorted(expected),
        "model_execution_allowed": False,
    }
    if state_path.exists():
        if not resume:
            raise DryRunVeto("untraceable-or-partial-artifact", "existing run state requires --resume")
        observed_state = read_json(state_path)
        verify_embedded_digest(observed_state, "state_digest", "dry-run state")
        for field, value in state_base.items():
            if observed_state.get(field) != value:
                raise DryRunVeto("protocol-or-arm-drift", f"resume state changed at {field}")
    elif resume:
        raise DryRunVeto("untraceable-or-partial-artifact", "--resume requested without run state")

    completed = existing_cells(out_dir, expected, resume=resume)
    home_receipts = materialize_homes(manifests, out_dir, resume=resume)
    write_atomic_json(state_path, state_payload(state_base, completed, "running"))
    new_count = 0
    skipped_count = len(completed)
    for cell in cells:
        if cell["cell_id"] in completed:
            continue
        record = execute_cell(
            cell,
            out_dir,
            home_receipts,
            judge_environment,
            omit_native_latency=(fault == "missing-telemetry" and new_count == 0),
        )
        completed[cell["cell_id"]] = record["record_digest"]
        new_count += 1
        write_atomic_json(state_path, state_payload(state_base, completed, "running"))
        if interrupt_after is not None and new_count >= interrupt_after:
            write_atomic_json(state_path, state_payload(state_base, completed, "interrupted"))
            report = report_payload(
                status="interrupted",
                plan=plan,
                protocol_digest=plan["protocol_sha256"],
                lock_digest=lock["lock_digest"],
                expected_count=len(cells),
                completed_count=len(completed),
                new_count=new_count,
                skipped_count=skipped_count,
                surfaces=(item["surface"] for item in manifests),
                arms=(item["arm_id"] for item in manifests),
                lifecycles=(case["lifecycle_path"] for case in cases.values()),
            )
            return report, 75
    write_atomic_json(state_path, state_payload(state_base, completed, "completed"))
    scan_partial_writes(out_dir)
    report = report_payload(
        status="passed",
        plan=plan,
        protocol_digest=plan["protocol_sha256"],
        lock_digest=lock["lock_digest"],
        expected_count=len(cells),
        completed_count=len(completed),
        new_count=new_count,
        skipped_count=skipped_count,
        surfaces=(item["surface"] for item in manifests),
        arms=(item["arm_id"] for item in manifests),
        lifecycles=(case["lifecycle_path"] for case in cases.values()),
    )
    if fault and fault_catalog.get(fault):
        raise DryRunVeto(
            fault_catalog[fault],
            f"fault {fault} did not fire its expected veto",
        )
    return report, 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--interrupt-after", type=int, default=None)
    parser.add_argument("--fault", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan: dict[str, Any] | None = None
    try:
        if args.interrupt_after is not None and args.interrupt_after < 1:
            raise DryRunVeto("protocol-or-arm-drift", "--interrupt-after must be positive")
        plan = load_plan(args.plan)
        report, returncode = run_dry_run(
            args.plan,
            args.out_dir,
            resume=args.resume,
            interrupt_after=args.interrupt_after,
            fault=args.fault,
        )
    except (OSError, json.JSONDecodeError, subprocess.SubprocessError, DryRunVeto) as exc:
        if isinstance(exc, DryRunVeto):
            veto_id = exc.veto_id
            reason = exc.reason
        else:
            veto_id = "untraceable-or-partial-artifact"
            reason = str(exc)
        report = report_payload(
            status="vetoed",
            plan=plan,
            protocol_digest=plan.get("protocol_sha256") if plan else None,
            lock_digest=None,
            expected_count=0,
            completed_count=0,
            new_count=0,
            skipped_count=0,
            fault=args.fault,
            veto_id=veto_id,
            reason=reason,
        )
        returncode = 2
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_atomic_json(args.out_dir / "dry-run-report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
