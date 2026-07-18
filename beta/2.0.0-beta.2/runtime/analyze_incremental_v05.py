#!/usr/bin/env python3
"""Analyze only hash-chained, Judge-backed v0.5 batch commits."""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
RUNNER_PATH = RUNTIME_ROOT / "run_real_codex_evaluation_v05.py"
V04_ANALYZER_PATH = RUNTIME_ROOT / "analyze_codex_evaluation_v04.py"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = _load("mindthus_beta2_v05_runner_for_analysis", RUNNER_PATH)
V04A = _load("mindthus_beta2_v04_analyzer_for_v05", V04_ANALYZER_PATH)


class AnalysisError(RuntimeError):
    pass


def canonical_sha256(value: object) -> str:
    return RUNNER.canonical_sha256(value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_digest(payload: Mapping[str, Any], field: str, label: str) -> None:
    unsigned = dict(payload)
    digest = unsigned.pop(field, None)
    if digest != canonical_sha256(unsigned):
        raise AnalysisError(f"{label} digest differs")


def committed_evidence(
    run_dir: Path,
    protocol: Mapping[str, Any],
    protocol_sha256: str,
) -> tuple[
    list[dict[str, Any]],
    dict[str, tuple[dict[str, Any], dict[str, Any]]],
    list[dict[str, Any]],
]:
    batches = RUNNER.batch_plan(protocol, protocol_sha256)
    previous: str | None = None
    cells: list[dict[str, Any]] = []
    judges: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    commits: list[dict[str, Any]] = []
    for batch in batches:
        commit = RUNNER.validate_batch_commit(run_dir, batch, previous)
        if commit is None:
            break
        commits.append(commit)
        if commit.get("protocol_sha256") != protocol_sha256:
            raise AnalysisError("committed batch protocol digest differs")
        previous = commit["commit_digest"]
        batch_cells: list[dict[str, Any]] = []
        for item in commit["generation_records"]:
            record = RUNNER.completed_cell(run_dir, str(item["cell_id"]))
            if record is None:
                raise AnalysisError("committed cell disappeared")
            batch_cells.append(record)
            cells.append(record)
        for cell in batch_cells:
            output_id = RUNNER.judge_identity(protocol_sha256, str(cell["cell_id"]))
            first = RUNNER.V04.existing_judge_record(run_dir, output_id, 1)
            second = RUNNER.V04.existing_judge_record(run_dir, output_id, 2)
            if first is None or second is None:
                raise AnalysisError("committed Judge record disappeared")
            judges[str(cell["cell_id"])] = (first, second)
    return cells, judges, commits


def disagreement_packet(
    run_dir: Path,
    commit: Mapping[str, Any],
    cells: Iterable[Mapping[str, Any]],
    judges: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> dict[str, Any] | None:
    entries: list[dict[str, Any]] = []
    for cell in cells:
        if cell.get("batch_id") != commit["batch_id"]:
            continue
        first, second = judges[str(cell["cell_id"])]
        first_axes = V04A.binary_axes(first["verdict"])
        second_axes = V04A.binary_axes(second["verdict"])
        differing = {
            axis: [first_axes.get(axis), second_axes.get(axis)]
            for axis in sorted(set(first_axes) | set(second_axes))
            if first_axes.get(axis) != second_axes.get(axis)
        }
        if differing:
            entries.append(
                {
                    "blinded_output_id": first["blinded_output_id"],
                    "disputed_axes": differing,
                    "blinded_input_path": str(
                        run_dir
                        / "judge-inputs"
                        / f"{first['blinded_output_id']}.json"
                    ),
                    "judge_1_rationale": first["verdict"]["rationale"],
                    "judge_2_rationale": second["verdict"]["rationale"],
                }
            )
    if not entries:
        return None
    packet: dict[str, Any] = {
        "schema_version": "mindthus-beta2-batch-adjudication-packet-v0.5",
        "batch_id": commit["batch_id"],
        "batch_index": commit["batch_index"],
        "adjudicator": "William",
        "entries": entries,
    }
    packet["packet_digest"] = canonical_sha256(packet)
    return packet


def adjudication_for_packet(
    run_dir: Path, packet: Mapping[str, Any]
) -> dict[str, dict[str, bool]] | None:
    path = run_dir / "human-adjudications-v0.5" / f"{packet['batch_id']}.json"
    if not path.is_file():
        return None
    decision = read_json(path)
    verify_digest(decision, "adjudication_digest", "v0.5 adjudication")
    if (
        decision.get("schema_version")
        != "mindthus-beta2-batch-adjudication-v0.5"
        or decision.get("batch_id") != packet["batch_id"]
        or decision.get("packet_digest") != packet["packet_digest"]
        or decision.get("adjudicator") != "William"
    ):
        raise AnalysisError("v0.5 adjudication identity differs")
    expected = {
        item["blinded_output_id"]: set(item["disputed_axes"])
        for item in packet["entries"]
    }
    resolved: dict[str, dict[str, bool]] = {}
    for item in decision.get("decisions", []):
        output_id = str(item.get("blinded_output_id") or "")
        axes = item.get("axes")
        if (
            output_id not in expected
            or not isinstance(axes, Mapping)
            or set(axes) != expected[output_id]
            or any(not isinstance(value, bool) for value in axes.values())
        ):
            raise AnalysisError("v0.5 adjudication axes differ")
        resolved[output_id] = dict(axes)
    if set(resolved) != set(expected):
        raise AnalysisError("v0.5 adjudication is incomplete")
    return resolved


def _mean(values: Iterable[float | None]) -> float | None:
    materialized = [float(value) for value in values if value is not None]
    return statistics.fmean(materialized) if materialized else None


def descriptive_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "quality",
        "owner",
        "primitive",
        "joint",
        "false_wakeup",
        "input_tokens",
        "wall_time",
        "first_observable",
    )
    arms: dict[str, dict[str, Any]] = {}
    for arm in RUNNER.ARM_ORDER:
        arms[arm] = {
            field: _mean(row[arm].get(field) for row in rows) for field in fields
        }
    return {
        "paired_triplets": len(rows),
        "arm_descriptive_means": arms,
        "threshold_decisions_available": False,
    }


def analyze(
    run_dir: Path, authorization_path: Path
) -> dict[str, Any]:
    auth_report, _authorization, protocol = RUNNER.V04.authorized_context(
        authorization_path.resolve()
    )
    if protocol.get("protocol_version") != "0.5":
        raise AnalysisError("incremental analyzer received another protocol")
    cases = RUNNER.V04.source_cases(read_json(MATRIX_PATH))
    cells, judges, commits = committed_evidence(
        run_dir, protocol, auth_report["protocol_sha256"]
    )
    adjudications: dict[str, dict[str, bool]] = {}
    unresolved_packets: list[dict[str, Any]] = []
    for commit in commits:
        packet = disagreement_packet(run_dir, commit, cells, judges)
        if packet is None:
            continue
        packet_path = (
            run_dir
            / "human-adjudication-packets-v0.5"
            / f"{commit['batch_id']}.json"
        )
        RUNNER.write_atomic_json(packet_path, packet)
        resolution = adjudication_for_packet(run_dir, packet)
        if resolution is None:
            unresolved_packets.append(
                {
                    "batch_id": commit["batch_id"],
                    "packet_path": str(packet_path),
                    "packet_digest": packet["packet_digest"],
                }
            )
        else:
            adjudications.update(resolution)
    base: dict[str, Any] = {
        "schema_version": "mindthus-beta2-incremental-analysis-v0.5",
        "protocol_sha256": auth_report["protocol_sha256"],
        "committed_batches": len(commits),
        "committed_generation_outputs": len(cells),
        "committed_judge_records": len(cells) * 2,
        "unresolved_adjudication_packets": unresolved_packets,
    }
    if unresolved_packets:
        return {
            **base,
            "status": "human-adjudication-required",
            "claim_boundary": "raw Judge-backed committed evidence only until binary disagreements resolve",
        }
    rows = V04A.paired_rows(cells, judges, adjudications or None, cases) if cells else []
    if len(commits) < 75:
        return {
            **base,
            "status": "partial-committed",
            "descriptive": descriptive_rows(rows),
            "claim_boundary": "descriptive Judge-backed committed triplets only; no frozen threshold or architecture conclusion",
        }
    matched = V04A.matched_report(
        cells=cells,
        judges=judges,
        adjudications=adjudications or None,
        cases=cases,
        protocol=protocol,
    )
    matched["conclusion"] = matched["conclusion"].replace("v0.4", "v0.5")
    matched["claim_ceiling"] = (
        "75 filesystem-isolated, hash-chained, Judge-backed visible-case Codex triplets; "
        "no hidden-set, Claude, non-startup lifecycle, or release claim"
    )
    return {**base, **matched}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = analyze(args.run_dir.resolve(), args.authorization.resolve())
        RUNNER.write_atomic_json(
            args.run_dir.resolve() / "incremental-analysis-v0.5.json", report
        )
        code = 0 if report["status"] != "human-adjudication-required" else 3
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
