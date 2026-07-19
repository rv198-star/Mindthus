#!/usr/bin/env python3
"""Append and validate lightweight Method Fidelity usage logs.

This script records whether method-fidelity constraints helped in real or evaluation
use. It validates the record shape only; it does not judge method value.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus-fidelity-usage-log-v0.1"
DEFAULT_LOG = Path("data/fidelity-usage-log.jsonl")
METHODS = ("3L5S", "SELA", "MPG", "EDSP", "WAE", "TVG", "tplan", "using-mindthus")
RECORD_TYPES = ("real_use", "evaluation", "fixture")
HELPED_VALUES = ("yes", "no", "mixed", "unknown")
INVOCATION_MODES = ("explicit_router", "explicit_skill", "automatic_best_effort", "unknown")
OVERHEAD_LEVELS = ("none", "low", "moderate", "high", "unknown")


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    message: str


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_tags(raw: str) -> list[str]:
    if not raw.strip():
        return []
    tags = [item.strip() for item in raw.split(",")]
    return [item for item in tags if item]


def optional_text(value: str | None) -> str:
    return value.strip() if value else ""


def validate_score(
    record: dict[str, Any], field: str, max_score: int, findings: list[Finding], line: int
) -> None:
    value = record.get(field)
    if value is None and field == "baseline_score":
        return
    if not is_int(value) or not 0 <= value <= max_score:
        findings.append(
            Finding(line, "invalid-score", f"{field} must be an integer from 0 to max_score")
        )


def validate_record(record: Any, line: int) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(record, dict):
        return [Finding(line, "invalid-record", "record must be a JSON object")]

    if record.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding(line, "invalid-schema-version", f"schema_version must be {SCHEMA_VERSION}")
        )

    for field in ("logged_at", "scenario", "model"):
        if not non_empty_string(record.get(field)):
            findings.append(Finding(line, "missing-field", f"{field} must be a non-empty string"))

    if record.get("method") not in METHODS:
        findings.append(Finding(line, "invalid-method", f"method must be one of: {', '.join(METHODS)}"))
    if record.get("record_type") not in RECORD_TYPES:
        findings.append(
            Finding(line, "invalid-record-type", f"record_type must be one of: {', '.join(RECORD_TYPES)}")
        )
    if record.get("constraint_helped") not in HELPED_VALUES:
        findings.append(
            Finding(
                line,
                "invalid-helped-value",
                f"constraint_helped must be one of: {', '.join(HELPED_VALUES)}",
            )
        )

    invocation_mode = record.get("invocation_mode")
    if invocation_mode is not None and invocation_mode not in INVOCATION_MODES:
        findings.append(
            Finding(
                line,
                "invalid-invocation-mode",
                f"invocation_mode must be one of: {', '.join(INVOCATION_MODES)}",
            )
        )
    for field in ("decision_changed", "rework_reduced", "harm_observed"):
        value = record.get(field)
        if value is not None and value not in HELPED_VALUES:
            findings.append(
                Finding(
                    line,
                    "invalid-outcome-value",
                    f"{field} must be one of: {', '.join(HELPED_VALUES)}",
                )
            )
    overhead_level = record.get("overhead_level")
    if overhead_level is not None and overhead_level not in OVERHEAD_LEVELS:
        findings.append(
            Finding(
                line,
                "invalid-overhead-level",
                f"overhead_level must be one of: {', '.join(OVERHEAD_LEVELS)}",
            )
        )
    if "mechanism" in record and not isinstance(record.get("mechanism"), str):
        findings.append(Finding(line, "invalid-optional-field", "mechanism must be a string"))

    max_score = record.get("max_score")
    baseline = record.get("baseline_score")
    constrained = record.get("constrained_score")
    if max_score is None and record.get("record_type") == "real_use":
        if baseline is not None or constrained is not None:
            findings.append(
                Finding(
                    line,
                    "incomplete-score-set",
                    "real_use scores require constrained_score and a positive max_score",
                )
            )
    elif not is_int(max_score) or max_score <= 0:
        findings.append(Finding(line, "invalid-max-score", "max_score must be a positive integer"))
        max_score = 0
    else:
        validate_score(record, "baseline_score", max_score, findings, line)
        validate_score(record, "constrained_score", max_score, findings, line)

    expected_delta = constrained - baseline if is_int(baseline) and is_int(constrained) else None
    if record.get("score_delta") != expected_delta:
        findings.append(
            Finding(line, "invalid-score-delta", "score_delta must equal constrained_score - baseline_score")
        )

    tags = record.get("tags")
    if not isinstance(tags, list) or any(not non_empty_string(item) for item in tags):
        findings.append(Finding(line, "invalid-tags", "tags must be a list of non-empty strings"))

    for field in ("judge_model", "source", "notes"):
        if not isinstance(record.get(field), str):
            findings.append(Finding(line, "invalid-optional-field", f"{field} must be a string"))

    return findings


def build_record(args: argparse.Namespace) -> dict[str, Any]:
    baseline = args.baseline_score
    constrained = args.constrained_score
    return {
        "schema_version": SCHEMA_VERSION,
        "logged_at": args.logged_at or now_utc(),
        "record_type": args.record_type,
        "scenario": args.scenario.strip(),
        "method": args.method,
        "model": args.model.strip(),
        "judge_model": optional_text(args.judge_model),
        "baseline_score": baseline,
        "constrained_score": constrained,
        "max_score": args.max_score,
        "score_delta": constrained - baseline if baseline is not None else None,
        "constraint_helped": args.constraint_helped,
        "invocation_mode": args.invocation_mode,
        "decision_changed": args.decision_changed,
        "rework_reduced": args.rework_reduced,
        "overhead_level": args.overhead_level,
        "harm_observed": args.harm_observed,
        "mechanism": optional_text(args.mechanism),
        "source": optional_text(args.source),
        "notes": optional_text(args.notes),
        "tags": parse_tags(args.tags),
    }


def is_default_log_path(path: Path) -> bool:
    return path.resolve(strict=False) == (Path.cwd() / DEFAULT_LOG).resolve(strict=False)


def read_jsonl(path: Path, *, allow_missing_empty: bool = False) -> tuple[list[dict[str, Any]], list[Finding]]:
    records: list[dict[str, Any]] = []
    findings: list[Finding] = []
    if not path.exists():
        if allow_missing_empty:
            return records, findings
        findings.append(Finding(0, "missing-log", f"usage log not found: {path}"))
        return records, findings

    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(Finding(index, "invalid-json", f"invalid JSON: {exc}"))
            continue
        records.append(record)
        findings.extend(validate_record(record, index))
    return records, findings


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        line = f"line {finding.line}" if finding.line else "file"
        print(f"- BLOCK [{finding.code}] {line}: {finding.message}")


def validate_log(path: Path) -> int:
    missing_default_log = not path.exists() and is_default_log_path(path)
    records, findings = read_jsonl(path, allow_missing_empty=missing_default_log)
    if findings:
        print("Fidelity Usage Log Report")
        print(f"Log file: {path}")
        print_findings(findings)
        return 1
    print("Fidelity Usage Log Report")
    print(f"Log file: {path}")
    print(f"Records: {len(records)}")
    if missing_default_log:
        print("No usage-log data yet; the default log is optional until the first record is appended.")
    print("No usage-log shape risks detected.")
    return 0


def append_record(path: Path, record: dict[str, Any]) -> int:
    findings = validate_record(record, 1)
    if findings:
        print("Fidelity Usage Log Report")
        print_findings(findings)
        return 1

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"appended fidelity usage log record to {path}")
    if record["max_score"] is None:
        score_summary = "score=not_recorded"
    else:
        baseline = record["baseline_score"]
        delta = record["score_delta"]
        baseline_text = "none" if baseline is None else str(baseline)
        delta_text = "none" if delta is None else f"{delta:+d}"
        score_summary = (
            f"baseline={baseline_text}/{record['max_score']} "
            f"constrained={record['constrained_score']}/{record['max_score']} "
            f"delta={delta_text}"
        )
    print(
        "summary: "
        f"method={record['method']} model={record['model']} {score_summary} "
        f"helped={record['constraint_helped']} invocation={record['invocation_mode']}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="JSONL usage log path.")
    parser.add_argument("--validate", action="store_true", help="Validate an existing usage log.")
    parser.add_argument("--scenario", help="Redacted scenario summary.")
    parser.add_argument("--method", choices=METHODS, help="Mindthus method or skill used.")
    parser.add_argument("--model", help="Model that produced the method output.")
    parser.add_argument("--judge-model", help="Human or LLM judge identifier.")
    parser.add_argument("--baseline-score", type=int, help="Optional baseline score.")
    parser.add_argument("--constrained-score", type=int, help="Constrained or real-use judge score.")
    parser.add_argument("--max-score", type=int, help="Maximum judge score for this rubric.")
    parser.add_argument("--constraint-helped", choices=HELPED_VALUES, help="Whether constraints helped.")
    parser.add_argument(
        "--invocation-mode",
        default="unknown",
        choices=INVOCATION_MODES,
        help="How Mindthus entered the task.",
    )
    parser.add_argument(
        "--decision-changed",
        default="unknown",
        choices=HELPED_VALUES,
        help="Whether Mindthus materially changed the judgment or action.",
    )
    parser.add_argument(
        "--rework-reduced",
        default="unknown",
        choices=HELPED_VALUES,
        help="Whether Mindthus reduced downstream rework.",
    )
    parser.add_argument(
        "--overhead-level",
        default="unknown",
        choices=OVERHEAD_LEVELS,
        help="Observed extra process or attention cost.",
    )
    parser.add_argument(
        "--harm-observed",
        default="unknown",
        choices=HELPED_VALUES,
        help="Whether Mindthus caused a worse decision, delay, or avoidable burden.",
    )
    parser.add_argument("--mechanism", help="Redacted recurring success or failure mechanism.")
    parser.add_argument("--record-type", default="real_use", choices=RECORD_TYPES, help="Usage record type.")
    parser.add_argument("--logged-at", help="Override timestamp, preferably ISO-8601.")
    parser.add_argument("--source", help="Optional artifact or issue reference.")
    parser.add_argument("--notes", help="Optional short note.")
    parser.add_argument("--tags", default="", help="Comma-separated tags.")
    args = parser.parse_args()

    if args.validate:
        return validate_log(args.log)

    required = {
        "scenario": args.scenario,
        "method": args.method,
        "model": args.model,
        "constraint_helped": args.constraint_helped,
    }
    if args.record_type != "real_use":
        required.update(
            {
                "constrained_score": args.constrained_score,
                "max_score": args.max_score,
            }
        )
    missing = [name for name, value in required.items() if value is None or value == ""]
    if missing:
        raise SystemExit(f"missing required arguments for append: {', '.join(missing)}")

    score_values = (args.baseline_score, args.constrained_score, args.max_score)
    if any(value is not None for value in score_values) and (
        args.constrained_score is None or args.max_score is None
    ):
        raise SystemExit("partial scores are invalid: provide constrained_score and max_score together")

    return append_record(args.log, build_record(args))


if __name__ == "__main__":
    raise SystemExit(main())
