"""Versioned, shape-only validation for observable Mindthus judgment traces.

A Judgment Trace records externally inspectable route, evidence, and decision-delta
facts. It must not contain private chain of thought, raw conversations, TPlan mission
state, or a claim that structural validation proves semantic correctness.

v1.1 adds three-state decision deltas, an explicit comparison basis, and field-level
source labels. The validator continues to accept v1 packages for backward compatibility.
"""

from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from _runtime.core.report import Finding, finding


LEGACY_JUDGMENT_TRACE_SCHEMA_VERSION = "mindthus.judgment-trace.v1"
JUDGMENT_TRACE_SCHEMA_VERSION = "mindthus.judgment-trace.v1.1"
SUPPORTED_JUDGMENT_TRACE_SCHEMA_VERSIONS = {
    LEGACY_JUDGMENT_TRACE_SCHEMA_VERSION,
    JUDGMENT_TRACE_SCHEMA_VERSION,
}
TRACE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
FIELD_PATH_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$")

JUDGMENT_OBJECTS = {
    "direct_task",
    "information_gap",
    "problem_definition",
    "scarce_resource_allocation",
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
    "sra",
    "edsp",
    "sela",
    "mpg",
    "wae",
    "tvg",
    "tplan",
    "human",
    "unknown",
}
METHODS = {"using-mindthus", "3l5s", "sra", "edsp", "sela", "mpg", "wae", "tvg", "tplan"}
LEGACY_JUDGMENT_OBJECTS = JUDGMENT_OBJECTS - {"scarce_resource_allocation"}
LEGACY_JUDGMENT_OWNERS = JUDGMENT_OWNERS - {"sra"}
LEGACY_METHODS = METHODS - {"sra"}
OUTCOME_STATUSES = {"not_evaluated", "accepted", "rejected", "inconclusive"}
SOURCE_TYPES = {"runtime_observation", "evaluator_label", "author_annotation", "mixed"}
FIELD_SOURCE_TYPES = {
    "runtime_observation",
    "evaluator_label",
    "author_annotation",
    "inferred",
    "unknown",
}
DELTA_BASES = {
    "runtime_observation",
    "single_output_evaluator",
    "baseline_comparison",
    "repair_sequence",
    "author_annotation",
    "not_assessed",
}
DELTA_UNKNOWN = "unknown"
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
LEGACY_SECTION_FIELDS = {
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
V11_SECTION_FIELDS = {
    **LEGACY_SECTION_FIELDS,
    "provenance": LEGACY_SECTION_FIELDS["provenance"] | {"field_sources"},
    "decision_delta": LEGACY_SECTION_FIELDS["decision_delta"] | {"basis", "comparison_ref"},
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
REQUIRED_V11_FIELD_SOURCES = {
    "input_shape.judgment_object",
    "input_shape.hard_judgment_point",
    "routing.judgment_owner",
    "routing.loaded_methods",
    "routing.routing_decision",
    "decision_delta.basis",
    "decision_delta.comparison_ref",
    *(f"decision_delta.{field}" for field in DECISION_DELTA_FIELDS),
    "outcome.status",
}
ALLOWED_FIELD_SOURCE_PATHS = {
    "timestamp_utc",
    "input_shape.judgment_object",
    "input_shape.hard_judgment_point",
    "input_shape.frame_status",
    "input_shape.active_constraints",
    "routing.judgment_owner",
    "routing.selected_method",
    "routing.loaded_methods",
    "routing.routing_decision",
    "routing.supporting_primitives",
    "evidence.available_evidence_classes",
    "evidence.missing_evidence_classes",
    "evidence.claim_ceiling",
    "decision_delta.basis",
    "decision_delta.comparison_ref",
    *(f"decision_delta.{field}" for field in DECISION_DELTA_FIELDS),
    "outcome.status",
    "outcome.validator_status",
    "outcome.benchmark_case_id",
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


def _require_object(
    data: dict[str, Any],
    field: str,
    findings: list[Finding],
    allowed_fields: set[str],
) -> dict[str, Any] | None:
    value = data.get(field)
    if not isinstance(value, dict):
        findings.append(finding("block", "invalid-field", f"{field} must be an object", field))
        return None
    findings.extend(_unknown_fields(value, allowed_fields, field))
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
    *,
    required: bool = False,
) -> None:
    if field not in data:
        if required:
            findings.append(finding("block", "missing-field", f"missing field: {field}", subject))
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


def _validate_field_sources(value: Any, findings: list[Finding]) -> None:
    if not isinstance(value, dict):
        findings.append(finding("block", "invalid-field", "field_sources must be an object", "provenance"))
        return
    for path, source_type in value.items():
        if not isinstance(path, str) or not FIELD_PATH_RE.fullmatch(path):
            findings.append(
                finding("block", "invalid-field-source-path", f"invalid field source path: {path!r}", "provenance")
            )
            continue
        if path not in ALLOWED_FIELD_SOURCE_PATHS:
            findings.append(
                finding("block", "unsupported-field-source-path", f"unsupported field source path: {path}", "provenance")
            )
        if source_type not in FIELD_SOURCE_TYPES:
            findings.append(
                finding(
                    "block",
                    "unsupported-field-source",
                    f"field source for {path} must be one of: {', '.join(sorted(FIELD_SOURCE_TYPES))}",
                    "provenance",
                )
            )
    for path in sorted(REQUIRED_V11_FIELD_SOURCES - set(value)):
        findings.append(
            finding("block", "missing-field-source", f"missing source label for {path}", "provenance")
        )


def _validate_v11_delta_value(value: Any, field: str, findings: list[Finding]) -> None:
    if value is True or value is False or value == DELTA_UNKNOWN:
        return
    findings.append(
        finding(
            "block",
            "invalid-delta-state",
            f"{field} must be true, false, or '{DELTA_UNKNOWN}'",
            "decision_delta",
        )
    )


def validate_judgment_trace(data: Any) -> list[Finding]:
    """Return shape findings without evaluating whether the judgment is true."""

    findings: list[Finding] = []
    if not isinstance(data, dict):
        return [finding("block", "invalid-root", "judgment trace root must be an object")]

    findings.extend(_unknown_fields(data, ROOT_FIELDS, "trace"))
    for field in sorted(REQUIRED_ROOT_FIELDS - set(data)):
        findings.append(finding("block", "missing-field", f"missing field: {field}", "trace"))

    schema_version = data.get("schema_version")
    if schema_version not in SUPPORTED_JUDGMENT_TRACE_SCHEMA_VERSIONS:
        findings.append(
            finding(
                "block",
                "unsupported-schema",
                "schema_version must be one of: "
                + ", ".join(sorted(SUPPORTED_JUDGMENT_TRACE_SCHEMA_VERSIONS)),
                "schema_version",
            )
        )
    is_v11 = schema_version == JUDGMENT_TRACE_SCHEMA_VERSION
    section_fields = V11_SECTION_FIELDS if is_v11 else LEGACY_SECTION_FIELDS
    judgment_objects = JUDGMENT_OBJECTS if is_v11 else LEGACY_JUDGMENT_OBJECTS
    judgment_owners = JUDGMENT_OWNERS if is_v11 else LEGACY_JUDGMENT_OWNERS
    methods = METHODS if is_v11 else LEGACY_METHODS

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

    field_sources: dict[str, Any] | None = None
    provenance = _require_object(data, "provenance", findings, section_fields["provenance"])
    if provenance is not None:
        _require_non_empty_string(provenance, "producer", findings, "provenance", required=True)
        _require_enum(provenance, "source_type", SOURCE_TYPES, findings, "provenance", required=True)
        _require_non_empty_string(provenance, "source_ref", findings, "provenance")
        if is_v11:
            if "field_sources" not in provenance:
                findings.append(finding("block", "missing-field", "missing field: field_sources", "provenance"))
            else:
                raw_field_sources = provenance.get("field_sources")
                _validate_field_sources(raw_field_sources, findings)
                if isinstance(raw_field_sources, dict):
                    field_sources = raw_field_sources

    input_shape = _require_object(data, "input_shape", findings, section_fields["input_shape"])
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
        _require_enum(
            input_shape,
            "judgment_object",
            judgment_objects,
            findings,
            "input_shape",
            required=is_v11,
        )
        _require_enum(input_shape, "frame_status", FRAME_STATUSES, findings, "input_shape")
        _validate_string_list(input_shape, "active_constraints", findings, "input_shape")

    routing = _require_object(data, "routing", findings, section_fields["routing"])
    if routing is not None:
        _require_enum(routing, "routing_decision", ROUTING_DECISIONS, findings, "routing", required=True)
        _require_enum(
            routing,
            "judgment_owner",
            judgment_owners,
            findings,
            "routing",
            required=is_v11,
        )
        _require_enum(routing, "selected_method", methods, findings, "routing")
        _validate_string_list(routing, "loaded_methods", findings, "routing", required=is_v11)
        if isinstance(routing.get("loaded_methods"), list):
            for method in routing["loaded_methods"]:
                if isinstance(method, str) and method not in methods:
                    findings.append(
                        finding(
                            "block",
                            "unsupported-enum",
                            f"loaded_methods contains unsupported method: {method}",
                            "routing",
                        )
                    )
        _validate_string_list(routing, "supporting_primitives", findings, "routing")

    evidence = _require_object(data, "evidence", findings, section_fields["evidence"])
    if evidence is not None:
        _validate_string_list(evidence, "available_evidence_classes", findings, "evidence")
        _validate_string_list(evidence, "missing_evidence_classes", findings, "evidence")
        _require_non_empty_string(evidence, "claim_ceiling", findings, "evidence")

    decision_delta = _require_object(data, "decision_delta", findings, section_fields["decision_delta"])
    if decision_delta is not None:
        if is_v11:
            basis = _require_enum(
                decision_delta,
                "basis",
                DELTA_BASES,
                findings,
                "decision_delta",
                required=True,
            )
            if "comparison_ref" not in decision_delta:
                findings.append(
                    finding("block", "missing-field", "missing field: comparison_ref", "decision_delta")
                )
                comparison_ref = None
            else:
                comparison_ref = decision_delta.get("comparison_ref")
                if comparison_ref is not None and (
                    not isinstance(comparison_ref, str) or not comparison_ref.strip()
                ):
                    findings.append(
                        finding(
                            "block",
                            "invalid-comparison-ref",
                            "comparison_ref must be null or a non-empty string",
                            "decision_delta",
                        )
                    )
            if basis in {"baseline_comparison", "repair_sequence"} and not (
                isinstance(comparison_ref, str) and comparison_ref.strip()
            ):
                findings.append(
                    finding(
                        "block",
                        "comparison-ref-required",
                        f"comparison_ref is required when basis is {basis}",
                        "decision_delta",
                    )
                )
            for field in DECISION_DELTA_FIELDS:
                if field not in decision_delta:
                    findings.append(finding("block", "missing-field", f"missing field: {field}", "decision_delta"))
                else:
                    value = decision_delta.get(field)
                    _validate_v11_delta_value(value, field, findings)
                    if (
                        value != DELTA_UNKNOWN
                        and field_sources is not None
                        and field_sources.get(f"decision_delta.{field}") == "unknown"
                    ):
                        findings.append(
                            finding(
                                "block",
                                "source-value-mismatch",
                                f"decision_delta.{field} is assessed but its field source is unknown",
                                "provenance",
                            )
                        )
            if (
                basis not in {None, "not_assessed"}
                and field_sources is not None
                and field_sources.get("decision_delta.basis") == "unknown"
            ):
                findings.append(
                    finding(
                        "block",
                        "source-value-mismatch",
                        "decision_delta.basis is set but its field source is unknown",
                        "provenance",
                    )
                )
            if (
                isinstance(comparison_ref, str)
                and comparison_ref.strip()
                and field_sources is not None
                and field_sources.get("decision_delta.comparison_ref") == "unknown"
            ):
                findings.append(
                    finding(
                        "block",
                        "source-value-mismatch",
                        "decision_delta.comparison_ref is set but its field source is unknown",
                        "provenance",
                    )
                )
        else:
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

    outcome = _require_object(data, "outcome", findings, section_fields["outcome"])
    if outcome is not None:
        _require_enum(outcome, "status", OUTCOME_STATUSES, findings, "outcome", required=True)
        _require_non_empty_string(outcome, "validator_status", findings, "outcome")
        _require_non_empty_string(outcome, "benchmark_case_id", findings, "outcome")

    prohibited = {
        "prompt",
        "raw_prompt",
        "answer",
        "raw_answer",
        "conversation",
        "chain_of_thought",
        "mission",
        "tasks",
    }
    for field in sorted(prohibited & set(data)):
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
