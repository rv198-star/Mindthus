"""Versioned, shape-only validation for observable Mindthus judgment traces.

A Judgment Trace records externally inspectable route, evidence, and decision-delta
facts. It must not contain private chain of thought, raw conversations, TPlan mission
state, or a claim that structural validation proves semantic correctness.
"""

from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from _runtime.core.report import Finding, finding


JUDGMENT_TRACE_SCHEMA_VERSION = "mindthus.judgment-trace.v1"
TRACE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")

JUDGMENT_OBJECTS = {
    "direct_task",
    "information_gap",
    "problem_definition",
    "structural_ambiguity",
    "whole_object_definition",
    "decision_context",
    "strategy_direction",
    "path_carrying",
    "controller_boundary",
    "artifact_value",
    "mission_runtime",
    "unknown",
}
FRAME_STATUSES = {"clean", "biased", "overloaded", "malformed", "not_assessed"}
ROUTING_DECISIONS = {"direct_execute", "acquire_information", "intervene", "block", "stop"}
JUDGMENT_OWNERS = {
    "direct_execution",
    "information_acquisition",
    "using-mindthus",
    "3l5s",
    "edsp",
    "sela",
    "mpg",
    "wae",
    "tvg",
    "tplan",
    "human",
    "unknown",
}
METHODS = {"using-mindthus", "3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan"}
OUTCOME_STATUSES = {"not_evaluated", "accepted", "rejected", "inconclusive"}
SOURCE_TYPES = {"runtime_observation", "evaluator_label", "author_annotation", "mixed"}
DECISION_DELTA_FIELDS = (
    "strategy_changed",
    "risk_handling_changed",
    "evidence_requirement_changed",
    "next_action_changed",
    "stopping_condition_changed",
    "handoff_changed",
)
ROOT_FIELDS = {
    "schema_version",
    "trace_id",
    "timestamp_utc",
    "provenance",
    "input_shape",
    "routing",
    "evidence",
    "decision_delta",
    "outcome",
}
SECTION_FIELDS = {
    "provenance": {"producer", "source_type", "source_ref"},
    "input_shape": {"judgment_object", "hard_judgment_point", "frame_status", "active_constraints"},
    "routing": {
        "judgment_owner",
        "selected_method",
        "loaded_methods",
        "routing_decision",
        "supporting_primitives",
    },
    "evidence": {"available_evidence_classes", "missing_evidence_classes", "claim_ceiling"},
    "decision_delta": set(DECISION_DELTA_FIELDS),
    "outcome": {"status", "validator_status", "benchmark_case_id"},
}
REQUIRED_ROOT_FIELDS = {
    "schema_version",
    "trace_id",
    "provenance",
    "input_shape",
    "routing",
    "evidence",
    "decision_delta",
    "outcome",
}


class TraceValidationError(ValueError):
    """Raised when a Judgment Trace fails shape validation."""

    def __init__(self, findings: Iterable[Finding]):
        self.findings = list(findings)
        message = "; ".join(item.message for item in self.findings) or "invalid judgment trace"
        super().__init__(message)


def new_trace_id(prefix: str = "trace") -> str:
    """Create a non-identifying local trace id."""

    safe_prefix = re.sub(r"[^A-Za-z0-9._:-]+", "-", prefix).strip("-._:") or "trace"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{safe_prefix}-{timestamp}-{secrets.token_hex(4)}"


def _unknown_fields(data: dict[str, Any], allowed: set[str], subject: str) -> list[Finding]:
    return [
        finding("block", "unknown-field", f"unsupported field: {key}", subject)
        for key in sorted(set(data) - allowed)
    ]


def _require_object(data: dict[str, Any], field: str, findings: list[Finding]) -> dict[str, Any] | None:
    value = data.get(field)
    if not isinstance(value, dict):
        findings.append(finding("block", "invalid-field", f"{field} must be an object", field))
        return None
    findings.extend(_unknown_fields(value, SECTION_FIELDS[field], field))
    return value


def _require_non_empty_string(
    data: dict[str, Any],
    field: str,
    findings: list[Finding],
    subject: str,
    *,
    required: bool = False,
) -> str | None:
    if field not in data:
        if required:
            findings.append(finding("block", "missing-field", f"missing field: {field}", subject))
        return None
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        findings.append(finding("block", "invalid-field", f"{field} must be a non-empty string", subject))
        return None
    return value


def _require_enum(
    data: dict[str, Any],
    field: str,
    allowed: set[str],
    findings: list[Finding],
    subject: str,
    *,
    required: bool = False,
) -> str | None:
    value = _require_non_empty_string(data, field, findings, subject, required=required)
    if value is not None and value not in allowed:
        findings.append(
            finding(
                "block",
                "unsupported-enum",
                f"{field} must be one of: {', '.join(sorted(allowed))}",
                subject,
            )
        )
        return None
    return value


def _validate_string_list(
    data: dict[str, Any],
    field: str,
    findings: list[Finding],
    subject: str,
) -> None:
    if field not in data:
        return
    value = data.get(field)
    if not isinstance(value, list):
        findings.append(finding("block", "invalid-field", f"{field} must be a list", subject))
        return
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            findings.append(
                finding(
                    "block",
                    "invalid-list-item",
                    f"{field}[{index}] must be a non-empty string",
                    subject,
                )
            )


def _validate_timestamp(value: Any, findings: list[Finding]) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        findings.append(finding("block", "invalid-field", "timestamp_utc must be a non-empty string", "timestamp_utc"))
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        findings.append(finding("block", "invalid-timestamp", "timestamp_utc must be ISO-8601", "timestamp_utc"))
        return
    if parsed.tzinfo is None:
        findings.append(finding("block", "invalid-timestamp", "timestamp_utc must include a timezone", "timestamp_utc"))


def validate_judgment_trace(data: Any) -> list[Finding]:
    """Return shape findings without evaluating whether the judgment is true."""

    findings: list[Finding] = []
    if not isinstance(data, dict):
        return [finding("block", "invalid-root", "judgment trace root must be an object")]

    findings.extend(_unknown_fields(data, ROOT_FIELDS, "trace"))
    for field in sorted(REQUIRED_ROOT_FIELDS - set(data)):
        findings.append(finding("block", "missing-field", f"missing field: {field}", "trace"))

    if data.get("schema_version") != JUDGMENT_TRACE_SCHEMA_VERSION:
        findings.append(
            finding(
                "block",
                "unsupported-schema",
                f"schema_version must be {JUDGMENT_TRACE_SCHEMA_VERSION}",
                "schema_version",
            )
        )

    trace_id = _require_non_empty_string(data, "trace_id", findings, "trace", required=True)
    if trace_id is not None and not TRACE_ID_RE.fullmatch(trace_id):
        findings.append(
            finding(
                "block",
                "invalid-trace-id",
                "trace_id must use 3-128 characters from letters, numbers, '.', '_', ':', or '-'",
                "trace_id",
            )
        )
    _validate_timestamp(data.get("timestamp_utc"), findings)

    provenance = _require_object(data, "provenance", findings)
    if provenance is not None:
        _require_non_empty_string(provenance, "producer", findings, "provenance", required=True)
        _require_enum(provenance, "source_type", SOURCE_TYPES, findings, "provenance", required=True)
        _require_non_empty_string(provenance, "source_ref", findings, "provenance")

    input_shape = _require_object(data, "input_shape", findings)
    if input_shape is not None:
        if not isinstance(input_shape.get("hard_judgment_point"), bool):
            findings.append(
                finding(
                    "block",
                    "invalid-field",
                    "hard_judgment_point must be a boolean",
                    "input_shape",
                )
            )
        _require_enum(input_shape, "judgment_object", JUDGMENT_OBJECTS, findings, "input_shape")
        _require_enum(input_shape, "frame_status", FRAME_STATUSES, findings, "input_shape")
        _validate_string_list(input_shape, "active_constraints", findings, "input_shape")

    routing = _require_object(data, "routing", findings)
    if routing is not None:
        _require_enum(routing, "routing_decision", ROUTING_DECISIONS, findings, "routing", required=True)
        _require_enum(routing, "judgment_owner", JUDGMENT_OWNERS, findings, "routing")
        _require_enum(routing, "selected_method", METHODS, findings, "routing")
        _validate_string_list(routing, "loaded_methods", findings, "routing")
        if isinstance(routing.get("loaded_methods"), list):
            for method in routing["loaded_methods"]:
                if isinstance(method, str) and method not in METHODS:
                    findings.append(
                        finding(
                            "block",
                            "unsupported-enum",
                            f"loaded_methods contains unsupported method: {method}",
                            "routing",
                        )
                    )
        _validate_string_list(routing, "supporting_primitives", findings, "routing")

    evidence = _require_object(data, "evidence", findings)
    if evidence is not None:
        _validate_string_list(evidence, "available_evidence_classes", findings, "evidence")
        _validate_string_list(evidence, "missing_evidence_classes", findings, "evidence")
        _require_non_empty_string(evidence, "claim_ceiling", findings, "evidence")

    decision_delta = _require_object(data, "decision_delta", findings)
    if decision_delta is not None:
        for field in DECISION_DELTA_FIELDS:
            if not isinstance(decision_delta.get(field), bool):
                findings.append(
                    finding(
                        "block",
                        "invalid-field",
                        f"{field} must be a boolean",
                        "decision_delta",
                    )
                )

    outcome = _require_object(data, "outcome", findings)
    if outcome is not None:
        _require_enum(outcome, "status", OUTCOME_STATUSES, findings, "outcome", required=True)
        _require_non_empty_string(outcome, "validator_status", findings, "outcome")
        _require_non_empty_string(outcome, "benchmark_case_id", findings, "outcome")

    prohibited = {"prompt", "raw_prompt", "answer", "raw_answer", "conversation", "chain_of_thought", "mission", "tasks"}
    found_prohibited = sorted(prohibited & set(data))
    for field in found_prohibited:
        findings.append(
            finding(
                "block",
                "prohibited-field",
                f"core Judgment Trace must not contain {field}",
                "trace",
            )
        )

    return findings


def validate_judgment_trace_or_raise(data: Any) -> dict[str, Any]:
    findings = validate_judgment_trace(data)
    if findings:
        raise TraceValidationError(findings)
    assert isinstance(data, dict)
    return data


def load_judgment_trace(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TraceValidationError([finding("block", "read-failed", f"failed to read {path}: {exc}")]) from exc
    except UnicodeDecodeError as exc:
        raise TraceValidationError([finding("block", "decode-failed", f"failed to decode {path} as UTF-8: {exc}")]) from exc
    except json.JSONDecodeError as exc:
        raise TraceValidationError(
            [finding("block", "invalid-json", f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}")]
        ) from exc
    return validate_judgment_trace_or_raise(data)


def write_judgment_trace(path: Path, data: dict[str, Any]) -> None:
    validate_judgment_trace_or_raise(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
