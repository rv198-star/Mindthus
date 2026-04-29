#!/usr/bin/env python3
"""Score Mindthus skill activation benchmark results."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SKILLS = {"3l5s", "edsp", "sela", "wae", "tvg", "tplan"}
NONE_LABEL = "none"


class BenchmarkError(ValueError):
    """Benchmark input contract violation."""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BenchmarkError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise BenchmarkError(f"{path}:{line_number}: record must be an object")
        records.append(record)
    return records


def normalize_skill(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise BenchmarkError(f"selected skill must be a string or null: {value!r}")
    normalized = value.strip().lower()
    if normalized in {"", "none", "no_skill", "no-skill", "no_trigger", "no-trigger", "null"}:
        return None
    if normalized not in SKILLS:
        raise BenchmarkError(f"unsupported skill: {value!r}")
    return normalized


def selected_skill(result: dict[str, Any]) -> str | None:
    ranked = result.get("ranked_skills")
    if ranked is not None:
        if not isinstance(ranked, list):
            raise BenchmarkError("ranked_skills must be a list when provided")
        if ranked:
            return normalize_skill(ranked[0])
    return normalize_skill(result.get("selected_skill"))


def validate_case(case: dict[str, Any]) -> None:
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        raise BenchmarkError("case id must be a non-empty string")
    if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
        raise BenchmarkError(f"case {case_id} prompt must be a non-empty string")
    if not isinstance(case.get("should_trigger"), bool):
        raise BenchmarkError(f"case {case_id} should_trigger must be a boolean")
    acceptable = case.get("acceptable_skills")
    if not isinstance(acceptable, list):
        raise BenchmarkError(f"case {case_id} acceptable_skills must be a list")
    normalized_acceptable = [normalize_skill(skill) for skill in acceptable]
    if any(skill is None for skill in normalized_acceptable):
        raise BenchmarkError(f"case {case_id} acceptable_skills cannot include none")
    expected = normalize_skill(case.get("expected_skill"))
    if case["should_trigger"]:
        if expected is None:
            raise BenchmarkError(f"case {case_id} expected_skill is required")
        if expected not in normalized_acceptable:
            raise BenchmarkError(f"case {case_id} expected_skill must be acceptable")
    else:
        if expected is not None or normalized_acceptable:
            raise BenchmarkError(f"case {case_id} negative cases must not expect a skill")


def keyed_records(records: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    for record in records:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise BenchmarkError(f"{label} record missing string {key}")
        if value in keyed:
            raise BenchmarkError(f"duplicate {label} id: {value}")
        keyed[value] = record
    return keyed


def score(cases: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    for case in cases:
        validate_case(case)
    cases_by_id = keyed_records(cases, "id", "case")
    results_by_id = keyed_records(results, "case_id", "result")

    unknown_results = sorted(set(results_by_id) - set(cases_by_id))
    if unknown_results:
        raise BenchmarkError(f"unknown result case id: {unknown_results[0]}")
    for case_id in sorted(cases_by_id):
        if case_id not in results_by_id:
            raise BenchmarkError(f"missing result for case {case_id}")

    trigger_total = 0
    negative_total = 0
    acceptable_hits = 0
    primary_hits = 0
    selected_total = 0
    false_triggers = 0
    per_skill_total: Counter[str] = Counter()
    per_skill_hits: Counter[str] = Counter()
    confusion: dict[str, Counter[str]] = defaultdict(Counter)

    for case_id, case in cases_by_id.items():
        result = results_by_id[case_id]
        selected = selected_skill(result)
        selected_label = selected or NONE_LABEL
        expected = normalize_skill(case.get("expected_skill"))
        expected_label = expected or NONE_LABEL
        confusion[expected_label][selected_label] += 1

        if selected is not None:
            selected_total += 1

        if case["should_trigger"]:
            trigger_total += 1
            assert expected is not None
            per_skill_total[expected] += 1
            acceptable = set(case["acceptable_skills"])
            if selected in acceptable:
                acceptable_hits += 1
                per_skill_hits[expected] += 1
            if selected == expected:
                primary_hits += 1
        else:
            negative_total += 1
            if selected is not None:
                false_triggers += 1

    precision = acceptable_hits / selected_total if selected_total else 0.0
    recall = acceptable_hits / trigger_total if trigger_total else 0.0
    route_at_1 = primary_hits / trigger_total if trigger_total else 0.0
    over_trigger_rate = false_triggers / negative_total if negative_total else 0.0

    return {
        "counts": {
            "cases": len(cases),
            "trigger_cases": trigger_total,
            "negative_cases": negative_total,
            "selected_skills": selected_total,
            "acceptable_hits": acceptable_hits,
            "primary_hits": primary_hits,
            "false_triggers": false_triggers,
        },
        "metrics": {
            "recall": recall,
            "precision": precision,
            "route_at_1": route_at_1,
            "over_trigger_rate": over_trigger_rate,
        },
        "per_skill_recall": {
            skill: (per_skill_hits[skill] / per_skill_total[skill] if per_skill_total[skill] else 0.0)
            for skill in sorted(SKILLS)
        },
        "confusion_matrix": {
            expected: dict(sorted(counter.items()))
            for expected, counter in sorted(confusion.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Mindthus activation benchmark results.")
    parser.add_argument("--cases", default=str(Path(__file__).with_name("cases.jsonl")))
    parser.add_argument("--results", required=True)
    args = parser.parse_args()

    try:
        report = score(load_jsonl(Path(args.cases)), load_jsonl(Path(args.results)))
    except (OSError, BenchmarkError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
