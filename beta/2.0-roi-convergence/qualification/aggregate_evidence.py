#!/usr/bin/env python3
"""Aggregate the frozen ROI convergence artifacts without semantic grading."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


ARMS = ("incumbent", "r1", "r2", "r3")
VALID_CASES = (
    "direct",
    "evidence",
    "frame_whole_v11",
    "decision_context",
    "anti_spiral",
    "anti_spiral_near_negative",
    "clear_sela",
    "clear_mpg",
    "clear_wae",
)
HARD_CASES = {
    "frame_whole_v11",
    "decision_context",
    "anti_spiral",
    "clear_sela",
    "clear_mpg",
    "clear_wae",
}
EXPLICIT_CASES = {"clear_sela": "sela", "clear_mpg": "mpg", "clear_wae": "wae"}
PASSIVE_CASES = {
    "frame_whole_v11": "frame_whole",
    "decision_context": "decision_context",
    "anti_spiral": "anti_spiral",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def metric_medians(records: list[dict]) -> dict:
    return {
        "loaded_mindthus_bytes": statistics.median(
            item["loaded_mindthus_bytes"] for item in records
        ),
        "uncached_input_tokens": statistics.median(
            item["uncached_input_tokens"] for item in records
        ),
        "duration_seconds": statistics.median(item["duration_seconds"] for item in records),
    }


def reduction(baseline: float, candidate: float) -> float | None:
    return None if baseline == 0 else round((baseline - candidate) / baseline, 4)


def valid_summary_path(evidence: Path, arm: str, case: str) -> Path:
    if case in {"direct", "evidence"}:
        run = "run-20260719-v1"
    elif case == "frame_whole_v11":
        run = "run-20260719-v11-frame"
    else:
        run = "run-20260719-v11-main"
    return evidence / run / arm / case / "summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    qualification = Path(__file__).resolve().parent
    evidence = qualification / "evidence"
    by_arm: dict[str, list[dict]] = {arm: [] for arm in ARMS}
    source_paths: dict[str, dict[str, str]] = {arm: {} for arm in ARMS}
    for arm in ARMS:
        for case in VALID_CASES:
            path = valid_summary_path(evidence, arm, case)
            record = load(path)
            by_arm[arm].append(record)
            source_paths[arm][case] = path.relative_to(qualification.parent).as_posix()

    medians = {arm: metric_medians(records) for arm, records in by_arm.items()}
    hard_medians = {
        arm: metric_medians([item for item in records if item["case"] in HARD_CASES])
        for arm, records in by_arm.items()
    }
    reductions: dict[str, dict] = {}
    for arm in ARMS[1:]:
        reductions[arm] = {
            metric: reduction(medians["incumbent"][metric], medians[arm][metric])
            for metric in medians["incumbent"]
        }

    activation: dict[str, dict] = {}
    for arm, records in by_arm.items():
        by_case = {item["case"]: item for item in records}
        explicit = {
            case: {
                "required": owner,
                "loaded_owners": by_case[case]["loaded_owners"],
                "hit": owner in by_case[case]["loaded_owners"],
            }
            for case, owner in EXPLICIT_CASES.items()
        }
        passive = {
            family: {
                "case": case,
                "loaded_skills": by_case[case]["loaded_skills"],
                "hit": bool(by_case[case]["loaded_skills"]),
            }
            for case, family in PASSIVE_CASES.items()
        }
        activation[arm] = {
            "explicit": explicit,
            "explicit_hits": sum(item["hit"] for item in explicit.values()),
            "passive": passive,
            "passive_hits": sum(item["hit"] for item in passive.values()),
        }

    invalid_paths = [
        evidence / "run-20260719-v1" / "r2" / "frame_whole" / "summary.json",
        evidence
        / "run-20260719-v1-continuation"
        / "incumbent"
        / "frame_whole"
        / "summary.json",
        evidence / "run-20260719-v1-r1-frame" / "r1" / "frame_whole" / "summary.json",
    ]
    invalid_records = [load(path) for path in invalid_paths]
    targeted_paths = [
        evidence / "run-20260719-r21-targeted" / "r2" / "decision_context" / "summary.json",
        evidence / "run-20260719-r21-targeted" / "r2" / "clear_mpg" / "summary.json",
    ]
    targeted = [load(path) for path in targeted_paths]

    all_summaries = [load(path) for path in sorted(evidence.glob("*/*/*/summary.json"))]
    result = {
        "schema_version": "mindthus-roi-convergence-aggregate-v0.1",
        "script_verdict": "arithmetic_and_activation_shape_only",
        "semantic_review": "qualification/SEMANTIC-VERDICTS.json",
        "valid_initial_panel": {
            "calls": sum(len(items) for items in by_arm.values()),
            "cases_per_arm": len(VALID_CASES),
            "source_paths": source_paths,
            "medians": medians,
            "hard_judgment_medians": hard_medians,
            "reductions_vs_incumbent": reductions,
            "activation": activation,
            "counted_tokens_by_arm": {
                arm: sum(item["counted_tokens"] for item in records)
                for arm, records in by_arm.items()
            },
        },
        "invalidated_v1_frame_carrier": {
            "calls": len(invalid_records),
            "counted_tokens": sum(item["counted_tokens"] for item in invalid_records),
            "records": invalid_records,
            "verdict_use": False,
            "mission_budget_use": True,
        },
        "r2_1_targeted_pair": {
            "calls": len(targeted),
            "counted_tokens": sum(item["counted_tokens"] for item in targeted),
            "records": targeted,
        },
        "mission_usage": {
            "generator_calls": len(all_summaries),
            "judge_calls": 0,
            "counted_tokens": sum(item["counted_tokens"] for item in all_summaries),
            "input_tokens": sum(int(item["usage"].get("input_tokens", 0)) for item in all_summaries),
            "output_tokens": sum(int(item["usage"].get("output_tokens", 0)) for item in all_summaries),
            "cached_input_tokens_is_input_subset": True,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["mission_usage"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
