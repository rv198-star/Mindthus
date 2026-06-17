#!/usr/bin/env python3
"""Analyze scored Router Wake-Up A/B experiment records.

The runner does not call or judge models. It turns blinded human/LLM score records
into the certification metrics defined in tests/router_wakeup_ab_experiment_design.md.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus-router-wakeup-ab-v0.1"
VARIANTS = ("baseline", "treatment")
LOW_FREQUENCY_OWNERS = {"sela", "mpg", "edsp"}
CASE_TYPES = {
    "positive",
    "skip",
    "stress",
    "real_use",
    "direct",
    "missing_evidence",
    "deterministic",
    "tvg",
    "3l5s",
}


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    positive_lift_min: float
    alpha: float
    skip_margin: float = 0.05
    skip_min: float = 0.90
    method_lift_min: float | None = None
    require_mcnemar: bool = True
    baseline_ceiling: float | None = None


EXPERIMENTS = {
    "known": ExperimentConfig("known", positive_lift_min=0.25, alpha=0.05, baseline_ceiling=0.75),
    "holdout": ExperimentConfig(
        "holdout",
        positive_lift_min=0.20,
        alpha=0.05,
        method_lift_min=0.15,
        baseline_ceiling=0.80,
    ),
    "overuse": ExperimentConfig("overuse", positive_lift_min=0.0, alpha=0.05, require_mcnemar=False),
    "real_use": ExperimentConfig("real_use", positive_lift_min=0.15, alpha=0.05),
}


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def is_bool_or_none(value: Any) -> bool:
    return value is None or is_bool(value)


def validate_record(record: Any, line: int) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(record, dict):
        return [Finding(line, "invalid-record", "record must be a JSON object")]

    if record.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding(line, "invalid-schema-version", f"schema_version must be {SCHEMA_VERSION}")
        )

    for field in ("experiment", "scenario_id", "variant", "expected_owner", "selected_owner", "case_type"):
        if not non_empty_string(record.get(field)):
            findings.append(Finding(line, "missing-field", f"{field} must be a non-empty string"))

    if record.get("variant") not in VARIANTS:
        findings.append(Finding(line, "invalid-variant", "variant must be baseline or treatment"))
    if record.get("case_type") not in CASE_TYPES:
        findings.append(
            Finding(line, "invalid-case-type", f"case_type must be one of: {', '.join(sorted(CASE_TYPES))}")
        )
    if not isinstance(record.get("run_id"), int) or isinstance(record.get("run_id"), bool):
        findings.append(Finding(line, "invalid-run-id", "run_id must be an integer"))

    for field in ("correct_owner", "execution_impact", "evidence_ceiling_respected", "over_methodized"):
        if not is_bool(record.get(field)):
            findings.append(Finding(line, "invalid-boolean", f"{field} must be boolean"))

    for field in ("positive_wakeup", "skip_correct"):
        if not is_bool_or_none(record.get(field)):
            findings.append(Finding(line, "invalid-optional-boolean", f"{field} must be boolean or null"))

    if record.get("case_type") == "positive" and record.get("positive_wakeup") != record.get("correct_owner"):
        findings.append(
            Finding(
                line,
                "positive-wakeup-mismatch",
                "positive_wakeup must match correct_owner for positive cases",
            )
        )
    if record.get("case_type") != "positive" and record.get("positive_wakeup") is not None:
        findings.append(
            Finding(
                line,
                "positive-wakeup-mismatch",
                "positive_wakeup must be null outside positive cases",
            )
        )

    absorption = record.get("adjacent_absorption")
    if absorption not in ("none", "3l5s", "wae", "tvg", "other"):
        findings.append(
            Finding(line, "invalid-adjacent-absorption", "adjacent_absorption must be none, 3l5s, wae, tvg, or other")
        )
    if not isinstance(record.get("notes", ""), str):
        findings.append(Finding(line, "invalid-notes", "notes must be a string when present"))

    return findings


def load_records(path: Path) -> tuple[list[dict[str, Any]], list[Finding]]:
    records: list[dict[str, Any]] = []
    findings: list[Finding] = []
    if not path.exists():
        return records, [Finding(0, "missing-scores", f"scores file not found: {path}")]

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(Finding(line_number, "invalid-json", str(exc)))
            continue
        findings.extend(validate_record(record, line_number))
        if isinstance(record, dict):
            records.append(record)
    return records, findings


def pair_key(record: dict[str, Any]) -> tuple[str, str, int]:
    return (record["experiment"], record["scenario_id"], record["run_id"])


def validate_pairs(records: list[dict[str, Any]], experiment: str) -> list[Finding]:
    findings: list[Finding] = []
    groups: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        if record.get("experiment") != experiment:
            continue
        key = pair_key(record)
        variant = record["variant"]
        if variant in groups[key]:
            findings.append(
                Finding(0, "duplicate-pair", f"duplicate {variant} record for {key[1]} run {key[2]}")
            )
        groups[key][variant] = record

    if not groups:
        findings.append(Finding(0, "empty-experiment", f"no records for experiment: {experiment}"))

    for key, variants in sorted(groups.items()):
        missing = [variant for variant in VARIANTS if variant not in variants]
        if missing:
            findings.append(
                Finding(
                    0,
                    "missing-pair",
                    f"{key[1]} run {key[2]} missing variant(s): {', '.join(missing)}",
                )
            )
            continue
        baseline = variants["baseline"]
        treatment = variants["treatment"]
        for field in ("case_type", "expected_owner"):
            if baseline[field] != treatment[field]:
                findings.append(
                    Finding(0, "pair-mismatch", f"{key[1]} run {key[2]} mismatched {field}")
                )
    return findings


def primary_pass(record: dict[str, Any]) -> bool:
    return bool(record["correct_owner"] and record["execution_impact"])


def skip_pass(record: dict[str, Any]) -> bool:
    return bool(record.get("skip_correct") and record["evidence_ceiling_respected"])


def rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def exact_mcnemar_p(baseline_only: int, treatment_only: int) -> float:
    discordant = baseline_only + treatment_only
    if discordant == 0:
        return 1.0
    tail = min(baseline_only, treatment_only)
    probability = sum(math.comb(discordant, index) for index in range(tail + 1)) / (2**discordant)
    return min(1.0, 2 * probability)


def paired_pass_counts(
    records: list[dict[str, Any]], experiment: str, *, expected_owner: str | None = None
) -> tuple[int, int, int]:
    groups: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        if (
            record["experiment"] == experiment
            and record["case_type"] == "positive"
            and (expected_owner is None or record["expected_owner"] == expected_owner)
        ):
            groups[pair_key(record)][record["variant"]] = record

    baseline_only = 0
    treatment_only = 0
    pairs = 0
    for variants in groups.values():
        if set(variants) != set(VARIANTS):
            continue
        pairs += 1
        baseline = primary_pass(variants["baseline"])
        treatment = primary_pass(variants["treatment"])
        if baseline and not treatment:
            baseline_only += 1
        elif treatment and not baseline:
            treatment_only += 1
    return baseline_only, treatment_only, pairs


def paired_lift_ci(baseline_only: int, treatment_only: int, total_pairs: int) -> dict[str, float]:
    if total_pairs <= 0:
        return {"lower": 0.0, "upper": 0.0}
    difference = (treatment_only - baseline_only) / total_pairs
    discordant = baseline_only + treatment_only
    variance = (discordant / (total_pairs**2)) - ((treatment_only - baseline_only) ** 2 / (total_pairs**3))
    standard_error = math.sqrt(max(0.0, variance))
    lower = max(-1.0, difference - 1.96 * standard_error)
    upper = min(1.0, difference + 1.96 * standard_error)
    return {"lower": lower, "upper": upper}


def summarize_variant(records: list[dict[str, Any]], experiment: str, variant: str) -> dict[str, Any]:
    selected = [record for record in records if record["experiment"] == experiment and record["variant"] == variant]
    positive = [record for record in selected if record["case_type"] == "positive"]
    skips = [record for record in selected if record["case_type"] == "skip"]
    positive_passes = sum(1 for record in positive if primary_pass(record))
    skip_passes = sum(1 for record in skips if skip_pass(record))
    false_positives = sum(
        1
        for record in selected
        if record["case_type"] != "positive"
        and record["selected_owner"] in LOW_FREQUENCY_OWNERS
        and record["selected_owner"] != record["expected_owner"]
    )

    return {
        "records": len(selected),
        "positive_total": len(positive),
        "positive_passes": positive_passes,
        "positive_recall": rate(positive_passes, len(positive)),
        "skip_total": len(skips),
        "skip_passes": skip_passes,
        "skip_precision": rate(skip_passes, len(skips)),
        "execution_impact_passes": sum(1 for record in selected if record["execution_impact"]),
        "execution_impact_rate": rate(sum(1 for record in selected if record["execution_impact"]), len(selected)),
        "adjacent_absorption_rate": rate(
            sum(1 for record in selected if record["adjacent_absorption"] != "none"), len(selected)
        ),
        "over_methodized_rate": rate(sum(1 for record in selected if record["over_methodized"]), len(selected)),
        "low_frequency_false_positive_rate": rate(false_positives, len(selected)),
    }


def method_lifts(records: list[dict[str, Any]], experiment: str) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for method in sorted(LOW_FREQUENCY_OWNERS):
        method_records = [
            record
            for record in records
            if record["experiment"] == experiment
            and record["case_type"] == "positive"
            and record["expected_owner"] == method
        ]
        baseline = [record for record in method_records if record["variant"] == "baseline"]
        treatment = [record for record in method_records if record["variant"] == "treatment"]
        baseline_rate = rate(sum(1 for record in baseline if primary_pass(record)), len(baseline))
        treatment_rate = rate(sum(1 for record in treatment if primary_pass(record)), len(treatment))
        result[method] = {
            "baseline": baseline_rate,
            "treatment": treatment_rate,
            "lift": treatment_rate - baseline_rate,
        }
    return result


def method_mcnemar(records: list[dict[str, Any]], experiment: str) -> dict[str, dict[str, float]]:
    raw: list[tuple[str, float]] = []
    metrics: dict[str, dict[str, float]] = {}
    for method in sorted(LOW_FREQUENCY_OWNERS):
        baseline_only, treatment_only, pairs = paired_pass_counts(
            records, experiment, expected_owner=method
        )
        p_value = exact_mcnemar_p(baseline_only, treatment_only)
        raw.append((method, p_value))
        metrics[method] = {
            "mcnemar_p": p_value,
            "holm_adjusted_p": p_value,
            "baseline_only": baseline_only,
            "treatment_only": treatment_only,
            "pairs": pairs,
        }

    previous = 0.0
    total = len(raw)
    for rank, (method, p_value) in enumerate(sorted(raw, key=lambda item: item[1]), start=1):
        adjusted = min(1.0, p_value * (total - rank + 1))
        adjusted = max(previous, adjusted)
        metrics[method]["holm_adjusted_p"] = adjusted
        previous = adjusted
    return metrics


def case_correct_rate(records: list[dict[str, Any]], experiment: str, variant: str, case_type: str) -> float:
    selected = [
        record
        for record in records
        if record["experiment"] == experiment
        and record["variant"] == variant
        and record["case_type"] == case_type
    ]
    return rate(sum(1 for record in selected if primary_pass(record)), len(selected))


def analyze(records: list[dict[str, Any]], experiment: str) -> dict[str, Any]:
    config = EXPERIMENTS[experiment]
    baseline = summarize_variant(records, experiment, "baseline")
    treatment = summarize_variant(records, experiment, "treatment")
    baseline_only, treatment_only, positive_pairs = paired_pass_counts(records, experiment)
    mcnemar_p = exact_mcnemar_p(baseline_only, treatment_only)
    positive_lift = treatment["positive_recall"] - baseline["positive_recall"]
    skip_delta = treatment["skip_precision"] - baseline["skip_precision"]
    failed_checks: list[str] = []

    baseline_ceiling = (
        config.baseline_ceiling is not None
        and baseline["positive_total"] > 0
        and baseline["positive_recall"] > config.baseline_ceiling
    )
    if baseline_ceiling:
        failed_checks.append("baseline-ceiling")
    if positive_lift < config.positive_lift_min:
        failed_checks.append("positive-lift")
    if config.require_mcnemar and mcnemar_p > config.alpha:
        failed_checks.append("mcnemar")

    skip_noninferior = skip_delta >= -config.skip_margin and treatment["skip_precision"] >= config.skip_min
    if treatment["skip_total"] and not skip_noninferior:
        failed_checks.append("skip-noninferiority")

    execution_nondec = treatment["execution_impact_rate"] >= baseline["execution_impact_rate"]
    if not execution_nondec:
        failed_checks.append("execution-impact")

    lifts = method_lifts(records, experiment)
    method_p_values = method_mcnemar(records, experiment)
    if config.method_lift_min is not None:
        for method, metrics in lifts.items():
            if metrics["lift"] < config.method_lift_min:
                failed_checks.append(f"method-lift-{method}")
            if method_p_values[method]["holm_adjusted_p"] > config.alpha:
                failed_checks.append(f"method-mcnemar-{method}")

    false_positive_noninferior = True
    direct_route_preserved = True
    missing_evidence_route_preserved = True
    tvg_3l5s_noninferior = True

    if experiment == "overuse":
        fp_delta = treatment["low_frequency_false_positive_rate"] - baseline["low_frequency_false_positive_rate"]
        false_positive_noninferior = fp_delta <= 0.05
        direct_route_preserved = case_correct_rate(records, experiment, "treatment", "direct") >= 0.90
        missing_evidence_route_preserved = (
            case_correct_rate(records, experiment, "treatment", "missing_evidence") >= 0.90
        )
        tvg_delta = (
            case_correct_rate(records, experiment, "treatment", "tvg")
            - case_correct_rate(records, experiment, "baseline", "tvg")
        )
        three_l5s_delta = (
            case_correct_rate(records, experiment, "treatment", "3l5s")
            - case_correct_rate(records, experiment, "baseline", "3l5s")
        )
        tvg_3l5s_noninferior = tvg_delta >= -0.05 and three_l5s_delta >= -0.05

        if not false_positive_noninferior:
            failed_checks.append("low-frequency-false-positive")
        if not direct_route_preserved:
            failed_checks.append("direct-route-preservation")
        if not missing_evidence_route_preserved:
            failed_checks.append("missing-evidence-route-preservation")
        if not tvg_3l5s_noninferior:
            failed_checks.append("tvg-3l5s-noninferiority")

    if experiment == "real_use":
        if treatment["adjacent_absorption_rate"] > baseline["adjacent_absorption_rate"]:
            failed_checks.append("adjacent-absorption")
        if treatment["over_methodized_rate"] > baseline["over_methodized_rate"] + 0.05:
            failed_checks.append("over-methodization")

    return {
        "schema_version": SCHEMA_VERSION,
        "experiment": experiment,
        "certified": not failed_checks,
        "failed_checks": failed_checks,
        "variants": {"baseline": baseline, "treatment": treatment},
        "positive_wakeup": {
            "baseline": baseline["positive_recall"],
            "treatment": treatment["positive_recall"],
            "lift": positive_lift,
            "confidence_interval_95": paired_lift_ci(
                baseline_only, treatment_only, positive_pairs
            ),
            "mcnemar_p": mcnemar_p,
            "baseline_only": baseline_only,
            "treatment_only": treatment_only,
            "pairs": positive_pairs,
            "threshold": config.positive_lift_min,
        },
        "discriminability": {
            "baseline_ceiling": baseline_ceiling,
            "baseline_positive_recall": baseline["positive_recall"],
            "max_baseline_positive_recall": config.baseline_ceiling,
            "reason": (
                "baseline positive recall is too high for this experiment to prove the required lift"
                if baseline_ceiling
                else "baseline positive recall leaves enough headroom for the required lift"
            ),
        },
        "method_lifts": lifts,
        "method_mcnemar": method_p_values,
        "skip_precision": {
            "baseline": baseline["skip_precision"],
            "treatment": treatment["skip_precision"],
            "delta": skip_delta,
            "noninferior": skip_noninferior,
            "margin": config.skip_margin,
            "minimum_treatment": config.skip_min,
        },
        "execution_impact": {
            "baseline": baseline["execution_impact_rate"],
            "treatment": treatment["execution_impact_rate"],
            "nondecreasing": execution_nondec,
        },
        "overuse": {
            "baseline_false_positive": baseline["low_frequency_false_positive_rate"],
            "treatment_false_positive": treatment["low_frequency_false_positive_rate"],
            "false_positive_noninferior": false_positive_noninferior,
            "direct_route_preserved": direct_route_preserved,
            "missing_evidence_route_preserved": missing_evidence_route_preserved,
            "tvg_3l5s_noninferior": tvg_3l5s_noninferior,
            "baseline_over_methodized": baseline["over_methodized_rate"],
            "treatment_over_methodized": treatment["over_methodized_rate"],
            "baseline_adjacent_absorption": baseline["adjacent_absorption_rate"],
            "treatment_adjacent_absorption": treatment["adjacent_absorption_rate"],
        },
    }


def format_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def claim_ceiling(report: dict[str, Any]) -> str:
    experiment = report["experiment"]
    if not report["certified"]:
        return "No certification claim is allowed until failed checks are resolved."
    if experiment == "known":
        return "The router wake-up mechanism works on the designed acceptance scenarios."
    if experiment == "holdout":
        return (
            "The router wake-up mechanism generalizes across synthetic pressure scenarios, "
            "but real-use lift is not yet proven."
        )
    if experiment == "real_use":
        return "The router wake-up change significantly improved observed wake-up behavior."
    return "The overuse guardrail passed for this stress set."


def render_markdown(report: dict[str, Any]) -> str:
    positive = report["positive_wakeup"]
    skip = report["skip_precision"]
    execution = report["execution_impact"]
    max_baseline = report["discriminability"]["max_baseline_positive_recall"]
    max_baseline_text = "not_applicable" if max_baseline is None else format_pct(max_baseline)
    lines = [
        "# Router Wake-Up A/B Report",
        "",
        f"Experiment: `{report['experiment']}`",
        f"Certified: `{str(report['certified']).lower()}`",
        "",
        "## Primary Endpoint",
        "",
        f"- Baseline positive wake-up recall: {format_pct(positive['baseline'])}",
        f"- Treatment positive wake-up recall: {format_pct(positive['treatment'])}",
        f"- Lift: {format_pct(positive['lift'])}",
        f"- 95% CI: {format_pct(positive['confidence_interval_95']['lower'])} to "
        f"{format_pct(positive['confidence_interval_95']['upper'])}",
        f"- McNemar p: {positive['mcnemar_p']:.6f}",
        "",
        "## Discriminability",
        "",
        f"- Baseline ceiling triggered: `{str(report['discriminability']['baseline_ceiling']).lower()}`",
        f"- Max baseline positive recall: {max_baseline_text}",
        f"- Reason: {report['discriminability']['reason']}",
        "",
        "## Guardrails",
        "",
        f"- Skip precision delta: {format_pct(skip['delta'])}",
        f"- Skip non-inferior: `{str(skip['noninferior']).lower()}`",
        f"- Execution impact nondecreasing: `{str(execution['nondecreasing']).lower()}`",
        "",
        "## Method Lifts",
        "",
    ]
    for method, metrics in sorted(report["method_lifts"].items()):
        method_p = report["method_mcnemar"][method]
        lines.append(
            f"- `{method}`: baseline {format_pct(metrics['baseline'])}, "
            f"treatment {format_pct(metrics['treatment'])}, lift {format_pct(metrics['lift'])}, "
            f"Holm p {method_p['holm_adjusted_p']:.6f}"
        )
    lines.extend(
        [
            "",
            "## Overuse Guardrails",
            "",
            f"- False-positive non-inferior: `{str(report['overuse']['false_positive_noninferior']).lower()}`",
            f"- Direct route preserved: `{str(report['overuse']['direct_route_preserved']).lower()}`",
            f"- Missing-evidence route preserved: `{str(report['overuse']['missing_evidence_route_preserved']).lower()}`",
            f"- TVG/3L5S non-inferior: `{str(report['overuse']['tvg_3l5s_noninferior']).lower()}`",
        ]
    )
    lines.extend(
        [
            "",
            "## Claim Ceiling",
            "",
            claim_ceiling(report),
            "",
        ]
    )
    if report["failed_checks"]:
        lines.extend(["## Failed Checks", ""])
        lines.extend(f"- `{item}`" for item in report["failed_checks"])
        lines.append("")
    return "\n".join(lines)


def print_findings(findings: list[Finding]) -> None:
    print("Router Wake-Up A/B Validation Report")
    for finding in findings:
        line = f"line {finding.line}" if finding.line else "file"
        print(f"- BLOCK [{finding.code}] {line}: {finding.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", required=True, type=Path, help="JSONL scored A/B records.")
    parser.add_argument(
        "--experiment",
        required=True,
        choices=sorted(EXPERIMENTS),
        help="Experiment slice to analyze.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report.")
    parser.add_argument("--write-report", type=Path, help="Write a Markdown report.")
    parser.add_argument(
        "--fail-on-uncertified",
        action="store_true",
        help="Exit non-zero when the experiment does not meet its certification threshold.",
    )
    args = parser.parse_args()

    records, findings = load_records(args.scores)
    findings.extend(validate_pairs(records, args.experiment))
    if findings:
        print_findings(findings)
        return 1

    selected = [record for record in records if record["experiment"] == args.experiment]
    report = analyze(selected, args.experiment)

    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(render_markdown(report), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_markdown(report))

    if args.fail_on_uncertified and not report["certified"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
