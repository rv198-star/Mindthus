#!/usr/bin/env python3
"""Apply the frozen v0.4 recovery censoring rule to the untouched v0.4 analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

import analyze_codex_evaluation_v04 as base  # noqa: E402
import run_real_codex_evaluation_v04 as runner  # noqa: E402


DEFAULT_AUTHORIZATION = (
    BETA_ROOT / "authorizations" / "issue-119-codex-v0.4-recovery.1.json"
)
RECOVERY_ID = "0.4-recovery.1"
RECOVERY_CELL_ID = (
    "6721d94969c4893b4d5b7ffcc6b12fb38d334fd551f929114e2e7d1688a39dd5"
)
EFFICIENCY_ENDPOINT_IDS = {
    "input_token_savings_vs_stable",
    "kernel_token_overhead_vs_direct",
    "wall_time_savings_vs_stable",
    "first_observable_action_latency",
}


class RecoveryAnalysisError(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RecoveryAnalysisError(reason)


def recovery_cell(run_dir: Path) -> dict[str, Any]:
    try:
        record = runner.completed_cell(run_dir, RECOVERY_CELL_ID)
    except runner.EvaluationStop as exc:
        raise RecoveryAnalysisError(exc.reason) from exc
    require(record is not None, "the recovered v0.4 cell is missing")
    recovery = record.get("recovery_amendment")
    require(isinstance(recovery, Mapping), "the recovered cell lacks amendment metadata")
    require(recovery.get("amendment_id") == RECOVERY_ID, "the recovered cell amendment differs")
    cost = record.get("recovery_cost_evidence")
    require(isinstance(cost, Mapping), "the recovered cell lacks cost evidence")
    require(
        cost.get("efficiency_evidence_status")
        == "right-censored-exclude-paired-unit",
        "the recovered cell is not marked as right-censored",
    )
    return record


def filtered_efficiency_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    censored = [
        row
        for row in rows
        if row["case_id"] == "b2-dev-near-normal-debugging" and int(row["repeat"]) == 1
    ]
    require(len(censored) == 1, "the frozen censored paired unit is missing or duplicated")
    usable = [row for row in rows if row not in censored]
    return usable, censored


def resolved_rows(
    run_dir: Path,
    authorization_path: Path,
) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
    auth_report, _authorization, protocol = base.validate_authorization(authorization_path)
    matrix = runner.read_json(base.MATRIX_PATH)
    cases = runner.source_cases(matrix)
    cells, _ = base.load_cells(run_dir, protocol, auth_report["protocol_sha256"], "matched")
    judges = base.load_judges(run_dir, auth_report["protocol_sha256"], cells, cases)
    disagreements = base.disagreement_rows(run_dir, cells, judges, cases)
    adjudications = None
    if disagreements:
        packet_path = run_dir / "human-adjudication-packet-matched.json"
        require(packet_path.is_file(), "human adjudication packet is missing")
        packet = runner.read_json(packet_path)
        adjudications = base.adjudication_map(
            run_dir, packet, disagreements, "matched"
        )
        require(adjudications is not None, "human adjudication is incomplete")
    return base.paired_rows(cells, judges, adjudications, cases), protocol


def recompute_efficiency_endpoints(
    rows: list[dict[str, Any]], protocol: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    iterations = int(protocol["execution_design"]["bootstrap_iterations"])
    endpoints = [
        base.stratified_ratio(
            rows,
            endpoint_id="input_token_savings_vs_stable",
            metric="input_tokens",
            left="thin-kernel",
            right="stable",
            upper_threshold=0.85,
            seed=seed,
            iterations=iterations,
        ),
        base.stratified_ratio(
            rows,
            endpoint_id="kernel_token_overhead_vs_direct",
            metric="input_tokens",
            left="thin-kernel",
            right="direct-only",
            upper_threshold=1.08,
            seed=seed,
            iterations=iterations,
        ),
        base.stratified_latency(
            rows,
            endpoint_id="wall_time_savings_vs_stable",
            metric="wall_time",
            left="thin-kernel",
            right="stable",
        ),
        base.stratified_latency(
            rows,
            endpoint_id="first_observable_action_latency",
            metric="first_observable",
            left="thin-kernel",
            right="stable",
        ),
    ]
    for endpoint in endpoints:
        endpoint["right_censored_paired_units"] = 1
        endpoint["censoring_rule"] = (
            "b2-dev-near-normal-debugging/repeat-1 excluded because the direct-only "
            "attempt-01 terminal usage and completion cost are unknown"
        )
    return {item["id"]: item for item in endpoints}


def amended_conclusion(report: dict[str, Any]) -> None:
    failed = [
        item["id"] for item in report["endpoint_results"] if item["decision"] == "fail"
    ]
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
        conclusion = (
            "visible-case evidence supports the thin Kernel under every frozen v0.4 "
            "threshold after the preregistered one-unit efficiency censoring"
        )
    elif kernel_value_failures:
        conclusion = "visible-case evidence does not establish sufficient thin-Kernel behavioral benefit"
    elif efficiency_failures:
        conclusion = "visible-case evidence does not establish the required thin-Kernel efficiency gain"
    else:
        conclusion = "visible-case evidence fails one or more safety/noninferiority thresholds"
    report["failed_endpoints"] = failed
    report["conclusion"] = conclusion
    report["recommend_stop_beta_direction"] = bool(
        kernel_value_failures or efficiency_failures
    )


def analyze(phase: str, run_dir: Path, authorization_path: Path) -> dict[str, Any]:
    recovered = recovery_cell(run_dir)
    base_report = base.analyze(phase, run_dir, authorization_path)
    generation_calls, judge_calls, measured_tokens = runner.observed_attempt_usage(run_dir)
    report = dict(base_report)
    report.update(
        {
            "amendment_id": RECOVERY_ID,
            "base_protocol_version": "0.4",
            "recovered_cell_id": RECOVERY_CELL_ID,
            "recovered_final_answer_judged": report.get("status")
            not in {"blocked", "human-adjudication-required"},
            "budget_accounting": {
                "generation_calls": generation_calls,
                "judge_calls": judge_calls,
                "measured_counted_tokens": measured_tokens,
                "unknown_usage_reserved_tokens": recovered["recovery_cost_evidence"][
                    "unknown_usage_reserved_tokens"
                ],
                "conservative_total_for_authority": measured_tokens
                + recovered["recovery_cost_evidence"]["unknown_usage_reserved_tokens"],
                "unknown_attempt_usage_claim": "unknown-unavailable",
            },
            "evidence_preservation": {
                "attempt_1_retained": True,
                "attempt_2_appended": True,
                "original_stop_snapshot_retained": (
                    run_dir
                    / "recovery"
                    / RECOVERY_ID
                    / "pre-amendment"
                    / "stop-report.json"
                ).is_file(),
            },
        }
    )
    if phase == "matched" and report.get("status") == "matched-complete":
        all_rows, protocol = resolved_rows(run_dir, authorization_path)
        usable_rows, censored_rows = filtered_efficiency_rows(all_rows)
        replacements = recompute_efficiency_endpoints(usable_rows, protocol)
        report["endpoint_results"] = [
            replacements.get(item["id"], item) for item in report["endpoint_results"]
        ]
        report["efficiency_pairing"] = {
            "total_paired_units": len(all_rows),
            "usable_paired_units": len(usable_rows),
            "right_censored_paired_units": len(censored_rows),
            "censored_units": [
                {"case_id": row["case_id"], "repeat": row["repeat"]}
                for row in censored_rows
            ],
            "affected_endpoints": sorted(EFFICIENCY_ENDPOINT_IDS),
            "behavioral_and_safety_endpoints_use_all_units": True,
        }
        amended_conclusion(report)
        report["claim_ceiling"] = (
            "25 implementation-visible cases on Codex CLI startup sessions only, with "
            "one preregistered right-censored paired unit on four efficiency endpoints; "
            "no hidden-set, Claude, non-startup lifecycle, or release claim"
        )
    elif phase == "smoke":
        report["efficiency_pairing"] = {
            "status": "not-estimated-in-smoke",
            "future_matched_censoring": "one paired unit on four efficiency endpoints",
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "matched"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    args = parser.parse_args()
    try:
        report = analyze(
            args.phase, args.run_dir.resolve(), args.authorization.resolve()
        )
        runner.write_atomic_json(
            args.run_dir.resolve() / f"{args.phase}-analysis.json", report
        )
        code = 0
    except (
        OSError,
        json.JSONDecodeError,
        RecoveryAnalysisError,
        base.AnalysisError,
        ValueError,
    ) as exc:
        report = {"status": "blocked", "amendment_id": RECOVERY_ID, "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
