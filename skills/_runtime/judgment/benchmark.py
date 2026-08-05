"""Narrow adapter from the existing judgment benchmark to Judgment Trace v1.

The adapter intentionally records conservative evaluator-visible deltas. It does
not infer a full reasoning path from answer text.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from _runtime.judgment.trace import (
    JUDGMENT_TRACE_SCHEMA_VERSION,
    METHODS,
    validate_judgment_trace_or_raise,
    write_judgment_trace,
)


DIRECT_EXPECTED_OWNERS = {
    "clarification",
    "direct_answer",
    "direct_debugging",
    "direct_execution",
    "direct_judgment",
    "evidence_review",
    "release_review",
}
OWNER_OBJECT_MAP = {
    "input_framing_audit": "whole_object_definition",
    "whole_elephant": "whole_object_definition",
    "edsp": "structural_ambiguity",
    "sela": "strategy_direction",
    "sela_boundary": "strategy_direction",
    "mpg": "path_carrying",
    "wae": "controller_boundary",
    "tvg": "artifact_value",
    "anti_spiral": "problem_definition",
    "decision_context_calibration": "decision_context",
    "aspect_arbitration": "structural_ambiguity",
    "expression_discipline": "whole_object_definition",
    "approximate_quantified_mapping": "information_gap",
    "information_acquisition": "information_gap",
    "clarification": "information_gap",
}
OWNER_NORMALIZATION = {
    "input_framing_audit": "using-mindthus",
    "whole_elephant": "using-mindthus",
    "sela_boundary": "sela",
    "anti_spiral": "using-mindthus",
    "decision_context_calibration": "using-mindthus",
    "aspect_arbitration": "using-mindthus",
    "expression_discipline": "using-mindthus",
    "approximate_quantified_mapping": "using-mindthus",
}


def _stable_trace_id(case_id: str, variant: str, timestamp: str) -> str:
    digest = hashlib.sha256(f"{case_id}\n{variant}\n{timestamp}".encode("utf-8")).hexdigest()[:12]
    safe_variant = "".join(char if char.isalnum() or char in "._-" else "-" for char in variant)[:40]
    return f"benchmark-{case_id}-{safe_variant or 'run'}-{digest}"


def _loaded_methods(score: dict[str, Any]) -> list[str]:
    value = score.get("loaded_owner") or []
    if isinstance(value, str):
        value = [value]
    return [str(item) for item in value if str(item) in METHODS]


def _outcome_status(score: dict[str, Any]) -> str:
    value = score.get("score")
    if value == 2:
        return "accepted"
    if value == 0:
        return "rejected"
    if value == 1:
        return "inconclusive"
    return "not_evaluated"


def judgment_trace_from_benchmark(
    case: dict[str, Any],
    response: dict[str, Any],
    score: dict[str, Any],
) -> dict[str, Any]:
    """Build a conservative, evaluator-labeled trace for one benchmark case."""

    expected_owner = str(case.get("expected_owner") or "unknown")
    stay_asleep = bool(case.get("stay_asleep_expected"))
    loaded_methods = _loaded_methods(score)
    timestamp = str(score.get("judged_at_utc") or response.get("generated_at_utc") or "")
    variant = str(score.get("variant") or response.get("variant") or "benchmark")

    if expected_owner == "information_acquisition":
        routing_decision = "acquire_information"
        judgment_owner = "information_acquisition"
    elif stay_asleep or expected_owner in DIRECT_EXPECTED_OWNERS:
        routing_decision = "direct_execute"
        judgment_owner = "direct_execution"
    else:
        routing_decision = "intervene"
        judgment_owner = loaded_methods[0] if loaded_methods else OWNER_NORMALIZATION.get(expected_owner, expected_owner)
        if judgment_owner not in METHODS:
            judgment_owner = "unknown"

    visible_delta = score.get("required_visible_action_present") is True
    trace: dict[str, Any] = {
        "schema_version": JUDGMENT_TRACE_SCHEMA_VERSION,
        "trace_id": _stable_trace_id(str(case.get("case_id") or "unknown"), variant, timestamp),
        "provenance": {
            "producer": "run-judgment-benchmark-cli",
            "source_type": "mixed",
            "source_ref": str(case.get("case_id") or "unknown"),
        },
        "input_shape": {
            "judgment_object": OWNER_OBJECT_MAP.get(expected_owner, "direct_task" if stay_asleep else "unknown"),
            "hard_judgment_point": (
                not stay_asleep
                and expected_owner not in DIRECT_EXPECTED_OWNERS
                and expected_owner != "information_acquisition"
            ),
            "active_constraints": [
                f"case_type:{case.get('case_type', 'unknown')}",
                f"expected_owner:{expected_owner}",
            ],
        },
        "routing": {
            "judgment_owner": judgment_owner,
            "routing_decision": routing_decision,
            "loaded_methods": loaded_methods,
        },
        "evidence": {
            "available_evidence_classes": ["benchmark_case", "generator_response", "judge_score"],
            "missing_evidence_classes": ["real_world_outcome"],
            "claim_ceiling": "Benchmark evaluator label; not proof of semantic truth or real-world outcome.",
        },
        "decision_delta": {
            "strategy_changed": visible_delta and expected_owner in {"sela", "sela_boundary", "mpg"},
            "risk_handling_changed": visible_delta and expected_owner in {"wae", "mpg"},
            "evidence_requirement_changed": visible_delta and expected_owner in {
                "information_acquisition",
                "input_framing_audit",
                "whole_elephant",
                "approximate_quantified_mapping",
            },
            "next_action_changed": visible_delta,
            "stopping_condition_changed": visible_delta and expected_owner == "anti_spiral",
            "handoff_changed": False,
        },
        "outcome": {
            "status": _outcome_status(score),
            "validator_status": f"benchmark_judge_score:{score.get('score', 'not_evaluated')}",
            "benchmark_case_id": str(case.get("case_id") or "unknown"),
        },
    }
    if timestamp:
        trace["timestamp_utc"] = timestamp
    if loaded_methods:
        trace["routing"]["selected_method"] = loaded_methods[0]
    validate_judgment_trace_or_raise(trace)
    return trace


def write_benchmark_judgment_traces(
    out_dir: Path,
    cases: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    scores: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Write one JSON trace per judged case plus a JSONL index."""

    case_by_id = {str(case.get("case_id")): case for case in cases}
    response_by_id = {str(response.get("case_id")): response for response in responses}
    trace_dir = out_dir / "judgment-traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    traces: list[dict[str, Any]] = []
    for score in scores:
        case_id = str(score.get("case_id"))
        case = case_by_id.get(case_id)
        response = response_by_id.get(case_id)
        if case is None or response is None:
            continue
        trace = judgment_trace_from_benchmark(case, response, score)
        write_judgment_trace(trace_dir / f"{case_id}.json", trace)
        traces.append(trace)
    (out_dir / "judgment-traces.jsonl").write_text(
        "".join(json.dumps(trace, ensure_ascii=False, sort_keys=True) + "\n" for trace in traces),
        encoding="utf-8",
    )
    return traces
