#!/usr/bin/env python3
"""Analyze frozen v0.4 smoke or matched Codex artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from run_real_codex_evaluation_v04 import (  # noqa: E402
    JUDGE_RUBRIC,
    EvaluationStop,
    canonical_sha256,
    completed_cell,
    expected_cells,
    existing_judge_record,
    judge_identity,
    judge_prompt,
    read_json,
    repo_path,
    source_cases,
    user_prompt,
    validate_judge_output,
    write_atomic_json,
)


DEFAULT_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
CRITICAL_PRIMITIVES = {
    "input_framing_audit",
    "whole_elephant",
    "decision_context_calibration",
    "anti_spiral",
}
BINARY_BASE_AXES = (
    "owner_success",
    "false_wakeup_final_answer",
    "required_visible_action_present",
    "authority_or_evidence_regression",
)


class AnalysisError(ValueError):
    pass


def validate_authorization(path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    authorization = read_json(path)
    try:
        validator = repo_path(
            authorization.get("authorization_validator_path"),
            "authorization_validator_path",
        )
    except EvaluationStop as exc:
        raise AnalysisError(exc.reason) from exc
    result = subprocess.run(
        ["python3", str(validator), "--authorization", str(path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise AnalysisError(result.stderr.strip() or result.stdout.strip())
    report = json.loads(result.stdout)
    try:
        protocol_path = repo_path(authorization["protocol"]["path"], "protocol.path")
    except EvaluationStop as exc:
        raise AnalysisError(exc.reason) from exc
    protocol = read_json(protocol_path)
    return report, authorization, protocol


def verify_digest(payload: Mapping[str, Any], field: str, label: str) -> None:
    unsigned = dict(payload)
    observed = unsigned.pop(field, None)
    if observed != canonical_sha256(unsigned):
        raise AnalysisError(f"{label} digest differs")


def load_cells(
    run_dir: Path,
    protocol: Mapping[str, Any],
    protocol_sha256: str,
    phase: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    expected = expected_cells(protocol, phase)
    expected_keys = {
        (cell["case_id"], cell["arm_id"], int(cell["repeat"])) for cell in expected
    }
    records: list[dict[str, Any]] = []
    by_tuple: dict[tuple[str, str, int], dict[str, Any]] = {}
    for path in sorted((run_dir / "cells").glob("*/record.json")):
        try:
            record = completed_cell(run_dir, path.parent.name)
        except EvaluationStop as exc:
            raise AnalysisError(exc.reason) from exc
        if record is None:
            raise AnalysisError(f"cell record disappeared: {path.parent.name}")
        if canonical_sha256(record["cell_key"]) != record["cell_id"]:
            raise AnalysisError("cell identity does not bind its key")
        if record["cell_key"].get("protocol_sha256") != protocol_sha256:
            raise AnalysisError("cell protocol digest differs")
        key = (
            str(record["cell_key"]["case_id"]),
            str(record["arm_id"]),
            int(record["cell_key"]["repeat"]),
        )
        if key not in expected_keys:
            raise AnalysisError(f"unexpected generation cell: {key}")
        if key in by_tuple:
            raise AnalysisError(f"duplicate logical cell: {key}")
        by_tuple[key] = record
        records.append(record)
    missing = sorted(expected_keys - set(by_tuple))
    if missing:
        raise AnalysisError(f"missing generation cells: {missing[:5]} (total={len(missing)})")
    return records, {record["cell_id"]: record for record in records}


def load_judges(
    run_dir: Path,
    protocol_sha256: str,
    cells: Iterable[Mapping[str, Any]],
    cases: Mapping[str, Mapping[str, Any]],
) -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    results: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    expected_record_paths: set[Path] = set()
    rubric = read_json(JUDGE_RUBRIC)
    for cell in cells:
        output_id = judge_identity(protocol_sha256, str(cell["cell_id"]))
        case_id = str(cell["cell_key"]["case_id"])
        case = cases[case_id]
        candidate = Path(str(cell["answer_path"])).read_text(encoding="utf-8")
        raw_prompt = user_prompt(case["source"])
        contract = case["contract"]
        input_base = {
            "schema_version": "mindthus-beta2-blinded-judge-input-v0.4",
            "blinded_output_id": output_id,
            "user_prompt": raw_prompt,
            "case_contract": {
                "case_type": contract["case_type"],
                "entry_mode": contract["entry_mode"],
                "accepted_execution_owners": contract["accepted_execution_owners"],
                "expected_primitive_obligations": contract[
                    "expected_primitive_obligations"
                ],
                "required_visible_action": contract["required_visible_action"],
                "stay_asleep_expected": contract["stay_asleep_expected"],
            },
            "candidate_final_answer": candidate,
            "arm_label_present": False,
            "generator_path_present": False,
            "runtime_telemetry_present": False,
        }
        expected_input = {**input_base, "input_digest": canonical_sha256(input_base)}
        input_path = run_dir / "judge-inputs" / f"{output_id}.json"
        if not input_path.is_file() or read_json(input_path) != expected_input:
            raise AnalysisError(f"blinded judge input differs: {output_id}")
        prompt_digest = hashlib.sha256(
            judge_prompt(
                rubric=rubric,
                case=case,
                prompt=raw_prompt,
                candidate=candidate,
                blinded_output_id=output_id,
            ).encode("utf-8")
        ).hexdigest()
        records: list[dict[str, Any]] = []
        for slot in (1, 2):
            path = run_dir / "judge-records" / output_id / f"judge-{slot}.json"
            expected_record_paths.add(path.resolve())
            try:
                record = existing_judge_record(run_dir, output_id, slot)
            except EvaluationStop as exc:
                raise AnalysisError(exc.reason) from exc
            if record is None:
                raise AnalysisError(f"missing judge record: {output_id}/slot-{slot}")
            if record.get("blinded_output_id") != output_id or record.get("judge_slot") != slot:
                raise AnalysisError("judge identity differs")
            environment_path = run_dir / "judge-homes" / f"slot-{slot}" / "environment.json"
            if not environment_path.is_file():
                raise AnalysisError(f"judge environment is missing: slot-{slot}")
            environment = read_json(environment_path)
            verify_digest(environment, "environment_digest", "judge environment")
            if (
                environment.get("slot") != slot
                or environment.get("active_forbidden_plugins") != []
                or environment.get("generator_home_access_granted") is not False
                or record.get("environment_digest") != environment.get("environment_digest")
            ):
                raise AnalysisError("judge environment binding differs")
            if (
                record.get("blinded_input_digest") != expected_input["input_digest"]
                or record.get("judge_prompt_sha256") != prompt_digest
            ):
                raise AnalysisError("judge prompt/input binding differs")
            attempt_number = int(record["attempt"])
            raw_output = read_json(
                run_dir
                / "judge-attempts"
                / output_id
                / f"slot-{slot}"
                / f"attempt-{attempt_number:02d}"
                / "judge-output.json"
            )
            if not isinstance(raw_output, Mapping) or validate_judge_output(
                raw_output, case
            ) != record.get("verdict"):
                raise AnalysisError("judge normalized verdict differs from retained output")
            records.append(record)
        results[str(cell["cell_id"])] = (records[0], records[1])
    observed_record_paths = {
        path.resolve() for path in (run_dir / "judge-records").glob("*/*.json")
    }
    if observed_record_paths != expected_record_paths:
        raise AnalysisError("judge record set contains missing or unexpected artifacts")
    return results


def binary_axes(verdict: Mapping[str, Any]) -> dict[str, bool | None]:
    axes: dict[str, bool | None] = {
        axis: verdict.get(axis) for axis in BINARY_BASE_AXES
    }
    for item in verdict["primitive_obligation_results"]:
        axes[f"primitive:{item['primitive_id']}"] = bool(item["satisfied"])
    return axes


def disagreement_rows(
    run_dir: Path,
    cells: Iterable[Mapping[str, Any]],
    judges: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
    cases: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in cells:
        first, second = judges[str(cell["cell_id"])]
        first_axes = binary_axes(first["verdict"])
        second_axes = binary_axes(second["verdict"])
        differing = {
            axis: [first_axes.get(axis), second_axes.get(axis)]
            for axis in sorted(set(first_axes) | set(second_axes))
            if first_axes.get(axis) != second_axes.get(axis)
        }
        if not differing:
            continue
        output_id = first["blinded_output_id"]
        blinded = read_json(run_dir / "judge-inputs" / f"{output_id}.json")
        rows.append(
            {
                "blinded_output_id": output_id,
                "user_prompt": blinded["user_prompt"],
                "case_contract": blinded["case_contract"],
                "candidate_final_answer": blinded["candidate_final_answer"],
                "disputed_axes": differing,
                "judge_1_rationale": first["verdict"]["rationale"],
                "judge_2_rationale": second["verdict"]["rationale"],
            }
        )
    return rows


def adjudication_map(
    run_dir: Path,
    packet: Mapping[str, Any],
    disagreements: Iterable[Mapping[str, Any]],
    phase: str,
) -> dict[str, dict[str, bool | None]] | None:
    path = run_dir / f"human-adjudication-{phase}.json"
    if not path.is_file():
        return None
    payload = read_json(path)
    verify_digest(payload, "adjudication_digest", "human adjudication")
    if payload.get("schema_version") != "mindthus-beta2-human-adjudication-v0.4":
        raise AnalysisError("human adjudication schema differs")
    if payload.get("adjudicator") != "William":
        raise AnalysisError("human adjudicator differs")
    if payload.get("packet_digest") != packet["packet_digest"]:
        raise AnalysisError("human adjudication packet digest differs")
    expected = {
        row["blinded_output_id"]: set(row["disputed_axes"])
        for row in disagreements
    }
    observed: dict[str, dict[str, bool | None]] = {}
    for decision in payload.get("decisions", []):
        output_id = str(decision.get("blinded_output_id") or "")
        axes = decision.get("axes")
        if output_id not in expected or not isinstance(axes, Mapping):
            raise AnalysisError("human adjudication contains an unexpected decision")
        if set(axes) != expected[output_id]:
            raise AnalysisError("human adjudication axes differ from disputed axes")
        if any(not isinstance(value, bool) for value in axes.values()):
            raise AnalysisError("human adjudication value is not boolean")
        observed[output_id] = dict(axes)
    if set(observed) != set(expected):
        raise AnalysisError("human adjudication is incomplete")
    return observed


def resolved_axes(
    cell: Mapping[str, Any],
    judges: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
    adjudications: Mapping[str, Mapping[str, bool | None]] | None,
) -> dict[str, bool | None]:
    first, second = judges[str(cell["cell_id"])]
    first_axes = binary_axes(first["verdict"])
    second_axes = binary_axes(second["verdict"])
    output_id = str(first["blinded_output_id"])
    result: dict[str, bool | None] = {}
    for axis in sorted(set(first_axes) | set(second_axes)):
        if first_axes.get(axis) == second_axes.get(axis):
            result[axis] = first_axes.get(axis)
        elif adjudications and output_id in adjudications:
            result[axis] = adjudications[output_id][axis]
        else:
            raise AnalysisError("unresolved binary judge disagreement")
    return result


def primitive_miss_veto(
    cells: Iterable[Mapping[str, Any]],
    judges: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
    adjudications: Mapping[str, Mapping[str, bool | None]] | None,
    cases: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    by_case_primitive: dict[tuple[str, str], list[bool]] = {}
    for cell in cells:
        if cell["arm_id"] != "thin-kernel":
            continue
        case_id = str(cell["cell_key"]["case_id"])
        expected = cases[case_id]["contract"]["expected_primitive_obligations"]
        axes = resolved_axes(cell, judges, adjudications)
        for primitive in expected:
            if primitive in CRITICAL_PRIMITIVES:
                by_case_primitive.setdefault((case_id, primitive), []).append(
                    bool(axes[f"primitive:{primitive}"])
                )
    return [
        {"case_id": case_id, "primitive_id": primitive}
        for (case_id, primitive), observations in sorted(by_case_primitive.items())
        if observations and not any(observations)
    ]


def percentile(values: Iterable[float], quantile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return math.nan
    index = (len(ordered) - 1) * quantile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def weighted_mean(rows: Iterable[Mapping[str, Any]], value: str) -> float:
    materialized = [row for row in rows if row.get(value) is not None]
    if not materialized:
        return math.nan
    types = sorted({str(row["case_type"]) for row in materialized})
    type_means = []
    for case_type in types:
        values = [float(row[value]) for row in materialized if row["case_type"] == case_type]
        type_means.append(statistics.fmean(values))
    return statistics.fmean(type_means)


def cluster_bootstrap(
    rows: list[dict[str, Any]],
    statistic: Callable[[list[dict[str, Any]]], float],
    *,
    seed: str,
    iterations: int,
) -> tuple[float, float]:
    by_type: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in rows:
        by_type.setdefault(str(row["case_type"]), {}).setdefault(
            str(row["case_id"]), []
        ).append(row)
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest(), 16))
    values: list[float] = []
    for _ in range(iterations):
        sample: list[dict[str, Any]] = []
        for clusters in by_type.values():
            ids = sorted(clusters)
            for _index in range(len(ids)):
                sample.extend(clusters[rng.choice(ids)])
        value = statistic(sample)
        if not math.isnan(value) and not math.isinf(value):
            values.append(value)
    if not values:
        return math.nan, math.nan
    return percentile(values, 0.025), percentile(values, 0.975)


def paired_rows(
    cells: Iterable[Mapping[str, Any]],
    judges: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
    adjudications: Mapping[str, Mapping[str, bool | None]] | None,
    cases: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_unit: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for cell in cells:
        case_id = str(cell["cell_key"]["case_id"])
        repeat = int(cell["cell_key"]["repeat"])
        first, second = judges[str(cell["cell_id"])]
        axes = resolved_axes(cell, judges, adjudications)
        quality = statistics.fmean(
            [
                float(first["verdict"]["normalized_final_answer_score"]),
                float(second["verdict"]["normalized_final_answer_score"]),
            ]
        )
        expected_primitives = cases[case_id]["contract"]["expected_primitive_obligations"]
        primitive_recall = (
            statistics.fmean(
                [float(bool(axes[f"primitive:{primitive}"])) for primitive in expected_primitives]
            )
            if expected_primitives
            else None
        )
        telemetry = cell["telemetry"]["measurements"]
        skill_hops = telemetry["skill_hops"]["value"]
        semantic_false_wakeup = bool(axes["false_wakeup_final_answer"])
        runtime_false_wakeup = bool(
            cases[case_id]["contract"]["stay_asleep_expected"] and skill_hops
        )
        row = {
            "case_id": case_id,
            "repeat": repeat,
            "case_type": cases[case_id]["contract"]["case_type"],
            "entry_mode": cases[case_id]["contract"]["entry_mode"],
            "quality": quality,
            "owner": float(bool(axes["owner_success"])),
            "primitive": primitive_recall,
            "joint": (
                float(bool(axes["owner_success"]) and bool(primitive_recall == 1.0))
                if primitive_recall is not None
                else None
            ),
            "false_wakeup": float(semantic_false_wakeup or runtime_false_wakeup),
            "input_tokens": float(telemetry["tokens.input"]["value"]),
            "wall_time": float(telemetry["wall_time_seconds"]["value"]),
            "first_observable": float(
                telemetry["first_observable_action_latency_seconds"]["value"]
            ),
        }
        by_unit.setdefault((case_id, repeat), {})[str(cell["arm_id"])] = row
    paired: list[dict[str, Any]] = []
    for (case_id, repeat), arms in sorted(by_unit.items()):
        if set(arms) != {"stable", "direct-only", "thin-kernel"}:
            raise AnalysisError(f"paired unit is incomplete: {case_id}/{repeat}")
        paired.append(
            {
                "case_id": case_id,
                "repeat": repeat,
                "case_type": arms["stable"]["case_type"],
                "entry_mode": arms["stable"]["entry_mode"],
                "stable": arms["stable"],
                "direct-only": arms["direct-only"],
                "thin-kernel": arms["thin-kernel"],
            }
        )
    return paired


def delta_stat(rows: list[dict[str, Any]], metric: str, left: str, right: str) -> float:
    usable = [
        {
            **row,
            "delta": row[left][metric] - row[right][metric],
        }
        for row in rows
        if row[left].get(metric) is not None and row[right].get(metric) is not None
    ]
    return weighted_mean(usable, "delta")


def ratio_stat(rows: list[dict[str, Any]], metric: str, left: str, right: str) -> float:
    left_mean = weighted_mean(
        [{**row, "value": row[left][metric]} for row in rows], "value"
    )
    right_mean = weighted_mean(
        [{**row, "value": row[right][metric]} for row in rows], "value"
    )
    return left_mean / right_mean if right_mean else math.nan


def endpoint_delta(
    rows: list[dict[str, Any]],
    *,
    endpoint_id: str,
    metric: str,
    left: str,
    right: str,
    direction: str,
    threshold: float,
    seed: str,
    iterations: int,
) -> dict[str, Any]:
    usable = [
        row
        for row in rows
        if row[left].get(metric) is not None and row[right].get(metric) is not None
    ]
    estimate = delta_stat(usable, metric, left, right)
    lower, upper = cluster_bootstrap(
        usable,
        lambda sample: delta_stat(sample, metric, left, right),
        seed=f"{seed}:{endpoint_id}",
        iterations=iterations,
    )
    passed = lower >= threshold if direction == "lower-bound" else upper <= threshold
    return {
        "id": endpoint_id,
        "estimate": estimate,
        "ci95": [lower, upper],
        "threshold": threshold,
        "decision": "pass" if passed else "fail",
        "paired_units": len(usable),
    }


def endpoint_ratio(
    rows: list[dict[str, Any]],
    *,
    endpoint_id: str,
    metric: str,
    left: str,
    right: str,
    upper_threshold: float,
    seed: str,
    iterations: int,
) -> dict[str, Any]:
    estimate = ratio_stat(rows, metric, left, right)
    lower, upper = cluster_bootstrap(
        rows,
        lambda sample: ratio_stat(sample, metric, left, right),
        seed=f"{seed}:{endpoint_id}",
        iterations=iterations,
    )
    return {
        "id": endpoint_id,
        "estimate": estimate,
        "ci95": [lower, upper],
        "threshold": upper_threshold,
        "decision": "pass" if upper <= upper_threshold else "fail",
        "paired_units": len(rows),
    }


def latency_endpoint(
    rows: list[dict[str, Any]],
    *,
    endpoint_id: str,
    metric: str,
    left: str,
    right: str,
) -> dict[str, Any]:
    left_values = [row[left][metric] for row in rows]
    right_values = [row[right][metric] for row in rows]
    p50_ratio = percentile(left_values, 0.5) / percentile(right_values, 0.5)
    p95_ratio = percentile(left_values, 0.95) / percentile(right_values, 0.95)
    return {
        "id": endpoint_id,
        "p50_ratio": p50_ratio,
        "p95_ratio": p95_ratio,
        "decision": "pass" if p50_ratio <= 0.90 and p95_ratio <= 0.95 else "fail",
        "paired_units": len(rows),
    }


def _with_required_entry_strata(
    overall: dict[str, Any],
    strata: list[dict[str, Any]],
) -> dict[str, Any]:
    overall_decision = str(overall["decision"])
    overall["overall_decision"] = overall_decision
    overall["entry_mode_results"] = strata
    overall["decision"] = (
        "pass"
        if overall_decision == "pass"
        and strata
        and all(item["decision"] == "pass" for item in strata)
        else "fail"
    )
    return overall


def stratified_delta(
    rows: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    overall = endpoint_delta(rows, **kwargs)
    strata: list[dict[str, Any]] = []
    for entry_mode in sorted({str(row["entry_mode"]) for row in rows}):
        subset = [row for row in rows if row["entry_mode"] == entry_mode]
        result = endpoint_delta(
            subset,
            **{
                **kwargs,
                "seed": f"{kwargs['seed']}:entry-mode:{entry_mode}",
            },
        )
        result["entry_mode"] = entry_mode
        strata.append(result)
    return _with_required_entry_strata(overall, strata)


def stratified_ratio(
    rows: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    overall = endpoint_ratio(rows, **kwargs)
    strata: list[dict[str, Any]] = []
    for entry_mode in sorted({str(row["entry_mode"]) for row in rows}):
        subset = [row for row in rows if row["entry_mode"] == entry_mode]
        result = endpoint_ratio(
            subset,
            **{
                **kwargs,
                "seed": f"{kwargs['seed']}:entry-mode:{entry_mode}",
            },
        )
        result["entry_mode"] = entry_mode
        strata.append(result)
    return _with_required_entry_strata(overall, strata)


def stratified_latency(
    rows: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    overall = latency_endpoint(rows, **kwargs)
    strata: list[dict[str, Any]] = []
    for entry_mode in sorted({str(row["entry_mode"]) for row in rows}):
        subset = [row for row in rows if row["entry_mode"] == entry_mode]
        result = latency_endpoint(subset, **kwargs)
        result["entry_mode"] = entry_mode
        strata.append(result)
    return _with_required_entry_strata(overall, strata)


def injection_fidelity(cells: Iterable[Mapping[str, Any]]) -> tuple[bool, int]:
    thin_cells = [cell for cell in cells if cell["arm_id"] == "thin-kernel"]
    receipt_digests = {
        cell["telemetry"]["measurements"]
        .get("arm.hook_observation_receipt", {})
        .get("value")
        for cell in thin_cells
    }
    receipts_valid = len(receipt_digests) == 1 and all(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
        for value in receipt_digests
    )
    passed = bool(thin_cells) and receipts_valid and all(
        cell["telemetry"]["measurements"]
        .get("arm.hook_observation_receipt", {})
        .get("provenance")
        == "deterministic"
        and cell["telemetry"]["measurements"]["hook_state"]["value"] == "fired"
        and "session-start"
        in cell["telemetry"]["measurements"]["lifecycle_event"]["value"]
        for cell in thin_cells
    )
    return passed, len(thin_cells)


def matched_report(
    *,
    cells: list[dict[str, Any]],
    judges: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
    adjudications: Mapping[str, Mapping[str, bool | None]] | None,
    cases: Mapping[str, Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    rows = paired_rows(cells, judges, adjudications, cases)
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    iterations = int(protocol["execution_design"]["bootstrap_iterations"])
    primitive_rows = [row for row in rows if row["thin-kernel"]["primitive"] is not None]
    negative_rows = [row for row in rows if row["case_type"] == "negative_control"]
    injection_pass, thin_cell_count = injection_fidelity(cells)
    thin_entry_modes = sorted(
        {
            str(cell["cell_key"]["entry_mode"])
            for cell in cells
            if cell["arm_id"] == "thin-kernel"
        }
    )
    injection_strata: list[dict[str, Any]] = []
    for entry_mode in thin_entry_modes:
        stratum_cells = [
            cell
            for cell in cells
            if cell["arm_id"] == "thin-kernel"
            and cell["cell_key"]["entry_mode"] == entry_mode
        ]
        passed, observed = injection_fidelity(stratum_cells)
        injection_strata.append(
            {
                "entry_mode": entry_mode,
                "observed_thin_cells": observed,
                "fidelity_rate": 1.0 if passed else 0.0,
                "threshold": 1.0,
                "decision": "pass" if passed else "fail",
            }
        )
    injection_endpoint = {
        "id": "passive_kernel_session_start_injection_fidelity",
        "observed_thin_cells": thin_cell_count,
        "fidelity_rate": 1.0 if injection_pass else 0.0,
        "threshold": 1.0,
        "overall_decision": "pass" if injection_pass else "fail",
        "entry_mode_results": injection_strata,
        "decision": (
            "pass"
            if injection_pass
            and injection_strata
            and all(item["decision"] == "pass" for item in injection_strata)
            else "fail"
        ),
    }
    endpoints = [
        stratified_delta(
            rows,
            endpoint_id="quality_noninferiority_vs_stable",
            metric="quality",
            left="thin-kernel",
            right="stable",
            direction="lower-bound",
            threshold=-0.05,
            seed=seed,
            iterations=iterations,
        ),
        stratified_delta(
            rows,
            endpoint_id="execution_owner_fidelity_vs_stable",
            metric="owner",
            left="thin-kernel",
            right="stable",
            direction="lower-bound",
            threshold=-0.05,
            seed=seed,
            iterations=iterations,
        ),
        stratified_delta(
            primitive_rows,
            endpoint_id="primitive_recall_kernel_benefit",
            metric="primitive",
            left="thin-kernel",
            right="direct-only",
            direction="lower-bound",
            threshold=0.10,
            seed=seed,
            iterations=iterations,
        ),
        stratified_delta(
            primitive_rows,
            endpoint_id="joint_owner_primitive_kernel_benefit",
            metric="joint",
            left="thin-kernel",
            right="direct-only",
            direction="lower-bound",
            threshold=0.08,
            seed=seed,
            iterations=iterations,
        ),
        stratified_delta(
            negative_rows,
            endpoint_id="false_wakeup_harm_vs_stable",
            metric="false_wakeup",
            left="thin-kernel",
            right="stable",
            direction="upper-bound",
            threshold=0.03,
            seed=seed,
            iterations=iterations,
        ),
        injection_endpoint,
        stratified_ratio(
            rows,
            endpoint_id="input_token_savings_vs_stable",
            metric="input_tokens",
            left="thin-kernel",
            right="stable",
            upper_threshold=0.85,
            seed=seed,
            iterations=iterations,
        ),
        stratified_ratio(
            rows,
            endpoint_id="kernel_token_overhead_vs_direct",
            metric="input_tokens",
            left="thin-kernel",
            right="direct-only",
            upper_threshold=1.08,
            seed=seed,
            iterations=iterations,
        ),
        stratified_latency(
            rows,
            endpoint_id="wall_time_savings_vs_stable",
            metric="wall_time",
            left="thin-kernel",
            right="stable",
        ),
        stratified_latency(
            rows,
            endpoint_id="first_observable_action_latency",
            metric="first_observable",
            left="thin-kernel",
            right="stable",
        ),
    ]
    false_wakeup = next(item for item in endpoints if item["id"] == "false_wakeup_harm_vs_stable")
    thin_negative_rate = weighted_mean(
        [{**row, "value": row["thin-kernel"]["false_wakeup"]} for row in negative_rows],
        "value",
    )
    false_wakeup["thin_absolute_rate"] = thin_negative_rate
    if thin_negative_rate > 0.05:
        false_wakeup["decision"] = "fail"
    for stratum in false_wakeup["entry_mode_results"]:
        stratum_rows = [
            row
            for row in negative_rows
            if row["entry_mode"] == stratum["entry_mode"]
        ]
        stratum_rate = weighted_mean(
            [
                {**row, "value": row["thin-kernel"]["false_wakeup"]}
                for row in stratum_rows
            ],
            "value",
        )
        stratum["thin_absolute_rate"] = stratum_rate
        if stratum_rate > 0.05:
            stratum["decision"] = "fail"
            false_wakeup["decision"] = "fail"
    failed = [item["id"] for item in endpoints if item["decision"] == "fail"]
    kernel_value_failures = {
        "primitive_recall_kernel_benefit",
        "joint_owner_primitive_kernel_benefit",
    } & set(failed)
    efficiency_failures = {
        "input_token_savings_vs_stable",
        "wall_time_savings_vs_stable",
        "first_observable_action_latency",
    } & set(failed)
    if not failed:
        conclusion = "visible-case evidence supports the thin Kernel under every frozen v0.4 threshold"
    elif kernel_value_failures:
        conclusion = "visible-case evidence does not establish sufficient thin-Kernel behavioral benefit"
    elif efficiency_failures:
        conclusion = "visible-case evidence does not establish the required thin-Kernel efficiency gain"
    else:
        conclusion = "visible-case evidence fails one or more safety/noninferiority thresholds"
    return {
        "status": "matched-complete",
        "conclusion": conclusion,
        "endpoint_results": endpoints,
        "failed_endpoints": failed,
        "recommend_stop_beta_direction": bool(kernel_value_failures or efficiency_failures),
        "claim_ceiling": (
            "25 implementation-visible cases on Codex CLI startup sessions only; "
            "no hidden-set, Claude, non-startup lifecycle, or release claim"
        ),
        "native_first_useful_action_endpoint": "unknown-unavailable",
    }


def analyze(phase: str, run_dir: Path, authorization_path: Path) -> dict[str, Any]:
    auth_report, _authorization, protocol = validate_authorization(authorization_path)
    matrix = read_json(MATRIX_PATH)
    cases = source_cases(matrix)
    cells, _by_id = load_cells(
        run_dir, protocol, auth_report["protocol_sha256"], phase
    )
    judges = load_judges(
        run_dir, auth_report["protocol_sha256"], cells, cases
    )
    disagreements = disagreement_rows(run_dir, cells, judges, cases)
    packet: dict[str, Any] = {
        "schema_version": "mindthus-beta2-human-adjudication-packet-v0.4",
        "protocol_sha256": auth_report["protocol_sha256"],
        "phase": phase,
        "adjudicator": "William",
        "blinding": "arm labels, generator paths, order, and runtime telemetry omitted",
        "decision_path": str(run_dir / f"human-adjudication-{phase}.json"),
        "decision_contract": (
            "one explicit boolean for every disputed axis; no arm inference and no "
            "undecided/null substitution"
        ),
        "items": disagreements,
    }
    packet["packet_digest"] = canonical_sha256(packet)
    packet_path = run_dir / f"human-adjudication-packet-{phase}.json"
    draft_path = run_dir / f"human-adjudication-draft-{phase}.json"
    if disagreements:
        write_atomic_json(packet_path, packet)
        if not draft_path.is_file():
            draft: dict[str, Any] = {
                "schema_version": "mindthus-beta2-human-adjudication-v0.4",
                "adjudicator": "William",
                "packet_digest": packet["packet_digest"],
                "decisions": [
                    {
                        "blinded_output_id": row["blinded_output_id"],
                        "axes": {axis: None for axis in row["disputed_axes"]},
                    }
                    for row in disagreements
                ],
            }
            draft["adjudication_digest"] = canonical_sha256(draft)
            write_atomic_json(draft_path, draft)
        elif read_json(draft_path).get("packet_digest") != packet["packet_digest"]:
            raise AnalysisError("human adjudication draft binds a different packet")
    adjudications = (
        adjudication_map(run_dir, packet, disagreements, phase)
        if disagreements
        else None
    )
    if disagreements and adjudications is None:
        return {
            "status": "human-adjudication-required",
            "reason": "two isolated judges disagree on one or more binary primary axes",
            "disputed_output_count": len(disagreements),
            "disputed_axis_count": sum(len(row["disputed_axes"]) for row in disagreements),
            "adjudicator": "William",
            "packet_path": str(packet_path),
            "packet_digest": packet["packet_digest"],
            "decision_path": packet["decision_path"],
            "draft_path": str(draft_path),
            "claim_available": False,
        }

    authority_regressions: list[str] = []
    for cell in cells:
        axes = resolved_axes(cell, judges, adjudications)
        if axes["authority_or_evidence_regression"]:
            authority_regressions.append(
                judges[str(cell["cell_id"])][0]["blinded_output_id"]
            )
    if authority_regressions:
        return {
            "status": "vetoed",
            "veto_id": "authority-or-evidence-regression",
            "reason": "a blinded final answer overrides authority or exceeds its evidence",
            "blinded_output_ids": authority_regressions,
            "claim_available": False,
        }
    critical_misses = primitive_miss_veto(cells, judges, adjudications, cases)
    if critical_misses:
        return {
            "status": "vetoed",
            "veto_id": "systematic-critical-primitive-miss",
            "reason": "thin-kernel missed a frozen critical primitive in every included repeat",
            "misses": critical_misses,
            "claim_available": False,
        }
    if phase == "smoke":
        return {
            "status": "passed",
            "generation_outputs": len(cells),
            "judge_records": len(cells) * 2,
            "binary_disagreements": 0,
            "frozen_vetoes_fired": [],
            "next_phase": "matched",
            "claim_available": False,
            "claim_boundary": "smoke validates execution only; it does not answer the architecture question",
        }
    return matched_report(
        cells=cells,
        judges=judges,
        adjudications=adjudications,
        cases=cases,
        protocol=protocol,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "matched"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    args = parser.parse_args()
    try:
        report = analyze(args.phase, args.run_dir.resolve(), args.authorization.resolve())
        code = 0
        write_atomic_json(args.run_dir.resolve() / f"{args.phase}-analysis.json", report)
    except (OSError, json.JSONDecodeError, AnalysisError, ValueError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
