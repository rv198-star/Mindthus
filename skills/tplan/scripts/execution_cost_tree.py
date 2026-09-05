#!/usr/bin/env python3
"""Build and render a progressive TPlan observed-execution and cost tree."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from outcome_attribution import (
    attribution_audit_lines,
    attribution_audit_text,
    attribution_text,
    build_outcome_attribution,
    short_attribution_label,
)
from tplan_runtime import (
    TplanError,
    read_outcome_attribution_snapshot,
    task_map,
    validate_execution_trace,
    validate_mission,
)


from execution_time_metrics import (
    RECONCILABLE_KINDS, EXACT_MEASUREMENT_SOURCES,
    _parse_timestamp, _timestamp_ms, _iso_from_ms, _union_duration_ms,
    _record_interval, _is_reconcilable, _clip_interval, _elapsed_reconciliation,
    _counted_tokens,
)

REPORT_SCHEMA_VERSION = "tplan.execution_cost_tree.v0.9"
CODEX_TELEMETRY_COVERAGE_SCHEMA_VERSION = "tplan.codex_telemetry_coverage.v0.2"
VIEWS = {"compact", "standard", "audit"}
TERMINAL_MISSION_STATUSES = {
    "completed",
    "blocked",
    "budget_exhausted",
    "abandoned",
    "superseded",
    "requires_human",
}
ABNORMAL_TASK_STATUSES = {"blocked", "paused", "pruned", "abandoned", "superseded"}
LLM_KINDS = {"model"}
SCRIPT_KINDS = {"script"}
TOOL_KINDS = {"tool"}
WAIT_KINDS = {"wait"}
STANDARD_DURATION_CHANNELS = (
    ("model_duration", "LLM调用", "LLM调用累计", LLM_KINDS),
    ("script_duration", "脚本时长", "脚本累计", SCRIPT_KINDS),
    ("tool_duration", "工具时长", "工具累计", TOOL_KINDS),
    ("wait_duration", "等待时长", "等待累计", WAIT_KINDS),
)
STATUS_LABELS = {
    "active": "执行中",
    "completed": "成功",
    "blocked": "受阻",
    "paused": "已暂停",
    "pending": "未执行",
    "pruned": "已裁剪",
    "abandoned": "已撤回",
    "superseded": "已替代",
}
STATUS_ICONS = {
    "active": "▶",
    "completed": "✓",
    "blocked": "!",
    "paused": "Ⅱ",
    "pending": "○",
    "pruned": "−",
    "abandoned": "×",
    "superseded": "↪",
}
COMPACT_KIND_TAGS = {
    "task": "[T]",
    "subtask": "[ST]",
    "step": "[P]",
}
LIFECYCLE_STATE_EVENT_TYPES = {
    "mission_initialized",
    "node_added",
    "task_status_changed",
    "active_node_changed",
    "mission_status_changed",
    "interaction_guard_state",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_telemetry_capture(reason: str, *, diagnostic: str | None = None) -> dict[str, Any]:
    channels = {
        name: {
            "status": "not_reported",
            "observed_span_count": 0,
            "reason": reason,
        }
        for name in (
            "local_tools",
            "hosted_tools",
            "model_turns",
            "tokens",
            "waits",
            "subagents",
        )
    }
    return {
        "schema_version": CODEX_TELEMETRY_COVERAGE_SCHEMA_VERSION,
        "adapter_version": None,
        "generated_at": None,
        "binding": {
            "status": "not_configured",
            "scope": None,
            "mission_id": None,
            "generation": None,
        },
        "activation": {
            "required": False,
            "active_surface": None,
            "status": "not_tested",
            "reason": reason,
            "surfaces": {
                surface: {
                    "status": "not_tested",
                    "reason": reason,
                    "checked_at": None,
                    "host_build": None,
                    "codex_version": None,
                    "app_server_user_agent": None,
                    "platform_family": None,
                    "platform_os": None,
                    "binding_generation": None,
                    "source": None,
                }
                for surface in ("codex_app", "codex_cli")
            },
        },
        "channels": channels,
        "deduplication": {
            "hook_preferred_for_tools": True,
            "deduplicated_event_count": 0,
            "agent_turn_is_non_additive_envelope": True,
        },
        "privacy": {
            "raw_prompts": "not_collected",
            "raw_model_responses": "not_collected",
            "command_arguments": "not_collected",
            "tool_inputs_and_outputs": "not_collected",
            "connector_payloads": "not_collected",
            "stable_ids": "not_collected",
        },
        "diagnostics": {
            "binding_failure_count": 0,
            "unpaired_event_count": 0,
            "trace_write_failure_count": 0,
            "last_code": diagnostic,
        },
    }


def _safe_optional_telemetry_text(
    value: Any, *, limit: int = 500
) -> bool:
    return value is None or (
        isinstance(value, str)
        and value
        and len(value) <= limit
        and "\n" not in value
        and "\r" not in value
    )


def _valid_telemetry_activation(activation: Any) -> bool:
    if (
        not isinstance(activation, dict)
        or set(activation)
        != {"required", "active_surface", "status", "reason", "surfaces"}
        or not isinstance(activation.get("required"), bool)
        or activation.get("active_surface") not in {None, "codex_app", "codex_cli"}
        or activation.get("status")
        not in {
            "not_tested",
            "preflight_required",
            "source_absent",
            "source_not_enumerated",
            "needs_trust",
            "disabled",
            "binding_mismatch",
            "inventory_unavailable",
            "callback_unpaired",
            "ready",
            "observed",
        }
        or not _safe_optional_telemetry_text(activation.get("reason"))
        or not isinstance(activation.get("surfaces"), dict)
        or set(activation["surfaces"]) != {"codex_app", "codex_cli"}
    ):
        return False
    for record in activation["surfaces"].values():
        if (
            not isinstance(record, dict)
            or set(record)
            != {
                "status",
                "reason",
                "checked_at",
                "host_build",
                "codex_version",
                "app_server_user_agent",
                "platform_family",
                "platform_os",
                "binding_generation",
                "source",
            }
            or record.get("status")
            not in {
                "not_tested",
                "preflight_required",
                "source_absent",
                "source_not_enumerated",
                "needs_trust",
                "disabled",
                "binding_mismatch",
                "inventory_unavailable",
                "callback_unpaired",
                "ready",
                "observed",
            }
            or not _safe_optional_telemetry_text(record.get("reason"))
            or not all(
                _safe_optional_telemetry_text(record.get(field), limit=1000)
                for field in (
                    "checked_at",
                    "host_build",
                    "codex_version",
                    "app_server_user_agent",
                    "platform_family",
                    "platform_os",
                )
            )
            or (
                record.get("binding_generation") is not None
                and (
                    isinstance(record.get("binding_generation"), bool)
                    or not isinstance(record.get("binding_generation"), int)
                    or record["binding_generation"] < 1
                )
            )
        ):
            return False
        source = record.get("source")
        if source is None:
            continue
        if (
            not isinstance(source, dict)
            or set(source)
            != {
                "scope",
                "path",
                "sha256",
                "enumerated",
                "handler_hashes",
                "trust_statuses",
                "enabled",
                "created_by_tplan",
            }
            or source.get("scope") not in {"user", "project"}
            or not isinstance(source.get("path"), str)
            or not Path(source["path"]).is_absolute()
            or not _safe_optional_telemetry_text(source.get("path"), limit=1000)
            or (
                source.get("sha256") is not None
                and (
                    not isinstance(source.get("sha256"), str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", source["sha256"])
                    is None
                )
            )
            or not isinstance(source.get("enumerated"), bool)
            or (
                source.get("enabled") is not None
                and not isinstance(source.get("enabled"), bool)
            )
            or not isinstance(source.get("created_by_tplan"), bool)
            or not isinstance(source.get("handler_hashes"), dict)
            or any(
                not isinstance(key, str)
                or not isinstance(value, str)
                or not value
                or len(value) > 200
                or any(ord(character) < 32 for character in value)
                for key, value in source["handler_hashes"].items()
            )
            or not isinstance(source.get("trust_statuses"), list)
            or any(
                status not in {"managed", "untrusted", "trusted", "modified"}
                for status in source["trust_statuses"]
            )
        ):
            return False
    return True


def _read_telemetry_capture(mission_dir: Path, mission_id: str | None) -> dict[str, Any]:
    path = mission_dir / "reports" / "codex-telemetry-coverage.json"
    if not path.exists():
        return _default_telemetry_capture(
            "optional Codex telemetry adapter is not configured for this Mission"
        )
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default_telemetry_capture(
            "Codex telemetry coverage sidecar is unreadable",
            diagnostic="coverage_sidecar_unreadable",
        )
    required_channels = {
        "local_tools",
        "hosted_tools",
        "model_turns",
        "tokens",
        "waits",
        "subagents",
    }
    binding = report.get("binding") if isinstance(report, dict) else None
    activation = report.get("activation") if isinstance(report, dict) else None
    channels = report.get("channels") if isinstance(report, dict) else None
    deduplication = report.get("deduplication") if isinstance(report, dict) else None
    privacy = report.get("privacy") if isinstance(report, dict) else None
    diagnostics = report.get("diagnostics") if isinstance(report, dict) else None
    if (
        not isinstance(report, dict)
        or set(report)
        != {
            "schema_version",
            "adapter_version",
            "generated_at",
            "binding",
            "activation",
            "channels",
            "deduplication",
            "privacy",
            "diagnostics",
        }
        or report.get("schema_version") != CODEX_TELEMETRY_COVERAGE_SCHEMA_VERSION
        or not isinstance(report.get("adapter_version"), str)
        or not isinstance(report.get("generated_at"), str)
        or not isinstance(binding, dict)
        or set(binding) != {"status", "scope", "mission_id", "generation"}
        or binding.get("status") != "exact"
        or binding.get("scope") not in {"session", "session_and_thread"}
        or binding.get("mission_id") != mission_id
        or isinstance(binding.get("generation"), bool)
        or not isinstance(binding.get("generation"), int)
        or binding["generation"] < 1
        or not _valid_telemetry_activation(activation)
        or not isinstance(channels, dict)
        or set(channels) != required_channels
        or not isinstance(deduplication, dict)
        or set(deduplication)
        != {
            "hook_preferred_for_tools",
            "deduplicated_event_count",
            "agent_turn_is_non_additive_envelope",
        }
        or deduplication.get("hook_preferred_for_tools") is not True
        or deduplication.get("agent_turn_is_non_additive_envelope") is not True
        or isinstance(deduplication.get("deduplicated_event_count"), bool)
        or not isinstance(deduplication.get("deduplicated_event_count"), int)
        or deduplication["deduplicated_event_count"] < 0
        or not isinstance(privacy, dict)
        or set(privacy)
        != {
            "raw_prompts",
            "raw_model_responses",
            "command_arguments",
            "tool_inputs_and_outputs",
            "connector_payloads",
            "stable_ids",
        }
        or not all(
            isinstance(value, str)
            and value
            and len(value) <= 80
            and "\n" not in value
            and "\r" not in value
            for value in privacy.values()
        )
        or not isinstance(diagnostics, dict)
        or set(diagnostics)
        != {
            "binding_failure_count",
            "unpaired_event_count",
            "trace_write_failure_count",
            "last_code",
        }
        or not all(
            not isinstance(diagnostics.get(field), bool)
            and isinstance(diagnostics.get(field), int)
            and diagnostics[field] >= 0
            for field in (
                "binding_failure_count",
                "unpaired_event_count",
                "trace_write_failure_count",
            )
        )
        or (
            diagnostics.get("last_code") is not None
            and (
                not isinstance(diagnostics.get("last_code"), str)
                or len(diagnostics["last_code"]) > 100
                or "\n" in diagnostics["last_code"]
                or "\r" in diagnostics["last_code"]
            )
        )
    ):
        return _default_telemetry_capture(
            "Codex telemetry coverage sidecar does not match this Mission or schema",
            diagnostic="coverage_sidecar_binding_invalid",
        )
    for channel in channels.values():
        if (
            not isinstance(channel, dict)
            or channel.get("status")
            not in {"observed", "available_not_observed", "not_reported"}
            or isinstance(channel.get("observed_span_count"), bool)
            or not isinstance(channel.get("observed_span_count"), int)
            or channel["observed_span_count"] < 0
            or not isinstance(channel.get("reason"), str)
            or not channel["reason"]
            or len(channel["reason"]) > 500
            or "\n" in channel["reason"]
            or "\r" in channel["reason"]
        ):
            return _default_telemetry_capture(
                "Codex telemetry coverage sidecar contains invalid channel data",
                diagnostic="coverage_sidecar_channels_invalid",
            )
    return report


def _unique_strings(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _usage_owner_event_ids(records: Iterable[dict[str, Any]]) -> set[str]:
    """Choose leaf-most explicit model/agent-turn usage owners from the full span graph."""

    records = list(records)
    token_records = [
        record
        for record in records
        if record["span"]["kind"] == "model"
        or (record["span"]["kind"] == "agent_turn" and record.get("usage"))
    ]
    by_span_id = {
        record["span"].get("span_id"): record
        for record in records
        if isinstance(record["span"].get("span_id"), str)
    }
    excluded_agent_span_ids: set[str] = set()
    for record in token_records:
        parent_span_id = record["span"].get("parent_span_id")
        visited: set[str] = set()
        while isinstance(parent_span_id, str) and parent_span_id not in visited:
            visited.add(parent_span_id)
            parent = by_span_id.get(parent_span_id)
            if parent is None:
                break
            if parent["span"]["kind"] == "agent_turn":
                excluded_agent_span_ids.add(parent_span_id)
            parent_span_id = parent["span"].get("parent_span_id")
    return {
        record["event_id"]
        for record in token_records
        if record["span"]["kind"] == "model"
        or record["span"].get("span_id") not in excluded_agent_span_ids
    }


def _span_cost(
    records: Iterable[dict[str, Any]],
    *,
    usage_owner_event_ids: set[str] | None = None,
) -> dict[str, Any]:
    records = list(records)
    intervals: list[tuple[int, int]] = []
    kind_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
    kind_sources: dict[str, Counter[str]] = defaultdict(Counter)
    by_kind_resource_ms: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    for record in records:
        span = record["span"]
        interval = _record_interval(record)
        intervals.append(interval)
        kind = span["kind"]
        kind_intervals[kind].append(interval)
        by_kind_resource_ms[kind] += span["duration_ms"]
        sources[span["measurement_source"]] += 1
        kind_sources[kind][span["measurement_source"]] += 1
        statuses[span["status"]] += 1
    resolved_usage_owners = (
        _usage_owner_event_ids(records)
        if usage_owner_event_ids is None
        else usage_owner_event_ids
    )
    token_records = [record for record in records if record.get("event_id") in resolved_usage_owners]
    usage: Counter[str] = Counter()
    usage_fields: set[str] = set()
    usage_sources: Counter[str] = Counter()
    for record in token_records:
        usage_source = record.get("usage_source")
        if isinstance(usage_source, str):
            usage_sources[usage_source] += 1
        for field, value in record.get("usage", {}).items():
            usage_fields.add(field)
            usage[field] += value
    if not token_records:
        usage_coverage = "not_reported"
    elif all(
        {"input_tokens", "output_tokens"}.issubset(record.get("usage", {}))
        for record in token_records
    ):
        usage_coverage = "complete"
    elif any(record.get("usage") for record in token_records):
        usage_coverage = "partial"
    else:
        usage_coverage = "unavailable"
    return {
        "span_count": len(records),
        "observed_interval_union_ms": _union_duration_ms(intervals),
        "resource_time_ms": sum(by_kind_resource_ms.values()),
        "additive_resource_time_ms": sum(
            value for kind, value in by_kind_resource_ms.items() if kind != "agent_turn"
        ),
        "envelope_span_count": sum(
            1 for record in records if record["span"]["kind"] == "agent_turn"
        ),
        "by_kind_resource_ms": dict(sorted(by_kind_resource_ms.items())),
        "by_kind_interval_union_ms": {
            kind: _union_duration_ms(kind_intervals[kind]) for kind in sorted(kind_intervals)
        },
        "by_kind_measurement_sources": {
            kind: dict(sorted(kind_sources[kind].items())) for kind in sorted(kind_sources)
        },
        "usage": {field: usage[field] for field in sorted(usage_fields)},
        "usage_fields": sorted(usage_fields),
        "usage_coverage": usage_coverage,
        "usage_sources": dict(sorted(usage_sources.items())),
        "usage_record_count": len(token_records),
        "excluded_usage_envelope_count": sum(
            1
            for record in records
            if record["span"]["kind"] == "agent_turn"
            and record.get("event_id") not in resolved_usage_owners
        ),
        "measurement_sources": dict(sorted(sources.items())),
        "span_statuses": dict(sorted(statuses.items())),
        "error_span_count": statuses["error"],
    }


def _duration_channel_status(cost: dict[str, Any], kinds: set[str]) -> str:
    present = [kind for kind in kinds if kind in cost["by_kind_resource_ms"]]
    if not present:
        return "not_reported"
    sources: Counter[str] = Counter()
    for kind in present:
        sources.update(cost["by_kind_measurement_sources"].get(kind, {}))
    observed_count = sum(
        count for source, count in sources.items() if source != "unavailable"
    )
    if observed_count and sources.get("unavailable"):
        return "partial"
    if observed_count:
        return "observed"
    return "unavailable"


def _presentation_density_profile(
    *,
    lifecycle_coverage: str,
    cost: dict[str, Any],
) -> dict[str, Any]:
    channels: dict[str, dict[str, str]] = {}
    for name, label, _render_label, kinds in STANDARD_DURATION_CHANNELS:
        channels[name] = {
            "label": label,
            "status": _duration_channel_status(cost, kinds),
        }
    token_status = {
        "complete": "observed",
        "partial": "partial",
        "unavailable": "unavailable",
        "not_reported": "not_reported",
    }[cost["usage_coverage"]]
    channels["tokens"] = {"label": "Token", "status": token_status}

    observed = [
        channel["label"]
        for channel in channels.values()
        if channel["status"] in {"observed", "partial"}
    ]
    explicitly_unavailable = [
        channel["label"]
        for channel in channels.values()
        if channel["status"] == "unavailable"
    ]
    omitted = [
        channel["label"]
        for channel in channels.values()
        if channel["status"] == "not_reported"
    ]
    present_count = len(observed) + len(explicitly_unavailable)
    has_partial_channel = any(
        channel["status"] == "partial" for channel in channels.values()
    )
    if not omitted:
        mode = "dense"
    elif present_count <= 2:
        mode = "sparse"
    else:
        mode = "mixed"
    if not present_count:
        telemetry_coverage = "not_reported"
    elif not omitted and not explicitly_unavailable and not has_partial_channel:
        telemetry_coverage = "complete"
    else:
        telemetry_coverage = "partial"

    if observed:
        if len(observed) == 1 and omitted:
            note = f"遥测覆盖：部分，仅采集{observed[0]}"
        else:
            coverage_label = {
                "complete": "完整",
                "partial": "部分",
                "not_reported": "未采集",
            }[telemetry_coverage]
            note = f"遥测覆盖：{coverage_label}，已采集{'、'.join(observed)}"
    elif explicitly_unavailable:
        note = "遥测覆盖：无可用数值"
    else:
        note = "遥测覆盖：未采集成本通道"
    if explicitly_unavailable:
        note += f"；明确不可用：{'、'.join(explicitly_unavailable)}"
    if omitted:
        note += f"；未采集：{'、'.join(omitted)}"
    note += "；未显示字段不代表 0。"

    return {
        "mode": mode,
        "source": "actual_trace_and_cost_coverage",
        "lifecycle_coverage": lifecycle_coverage,
        "telemetry_coverage": telemetry_coverage,
        "channels": channels,
        "observed_channels": observed,
        "explicitly_unavailable_channels": explicitly_unavailable,
        "omitted_standard_channels": omitted,
        "standard_note": note,
    }


def _record_time_ms(record: dict[str, Any]) -> int:
    if record.get("event_type") == "span_completed":
        return _timestamp_ms(record["span"]["finished_at"])
    return _timestamp_ms(record["timestamp"])


def _record_bounds_ms(record: dict[str, Any]) -> tuple[int, int]:
    if record.get("event_type") == "span_completed":
        return (
            _timestamp_ms(record["span"]["started_at"]),
            _timestamp_ms(record["span"]["finished_at"]),
        )
    observed_at = _timestamp_ms(record["timestamp"])
    return observed_at, observed_at


def _validate_trace(mission: dict[str, Any], trace: list[dict[str, Any]]) -> None:
    errors = validate_execution_trace(mission, trace)
    if errors:
        raise TplanError("; ".join(errors))


def _add_coverage_diagnostic(
    diagnostics: list[dict[str, str]],
    code: str,
    message: str,
) -> None:
    diagnostic = {"code": code, "message": message}
    if diagnostic not in diagnostics:
        diagnostics.append(diagnostic)


def _validate_lifecycle_commit_integrity(
    trace: list[dict[str, Any]],
    *,
    initialization_index: int,
    initial_active_task_id: str | None,
    diagnostics: list[dict[str, str]],
) -> str | None:
    """Validate ordering and the runtime-owned active-path part of lifecycle commits."""

    lifecycle_records = [
        (index, record)
        for index, record in enumerate(trace)
        if record.get("event_type") in LIFECYCLE_STATE_EVENT_TYPES
    ]
    previous_timestamp_ms: int | None = None
    previous_event_type: str | None = None
    for _, record in lifecycle_records:
        timestamp_ms = _timestamp_ms(record["timestamp"])
        if previous_timestamp_ms is not None and timestamp_ms < previous_timestamp_ms:
            _add_coverage_diagnostic(
                diagnostics,
                "trace_lifecycle_timestamp_non_monotonic",
                (
                    f"{record['event_type']} timestamp precedes the earlier "
                    f"{previous_event_type} lifecycle record"
                ),
            )
        previous_timestamp_ms = timestamp_ms
        previous_event_type = record["event_type"]

    commit_records: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    commit_order: list[str] = []
    for index, record in lifecycle_records:
        if index <= initialization_index or record.get("event_type") == "mission_initialized":
            continue
        commit_id = record.get("commit_id")
        if not isinstance(commit_id, str):
            continue
        if commit_id not in commit_records:
            commit_records[commit_id] = []
            commit_order.append(commit_id)
        commit_records[commit_id].append((index, record))

    replay_active_task_id = initial_active_task_id
    recovery_cursor_task_id: str | None = None
    for commit_id in commit_order:
        records = commit_records[commit_id]
        timestamps = {record["timestamp"] for _, record in records}
        if len(timestamps) != 1:
            _add_coverage_diagnostic(
                diagnostics,
                "trace_commit_timestamp_mismatch",
                f"lifecycle commit {commit_id} contains more than one timestamp",
            )

        active_records = [
            record for _, record in records if record.get("event_type") == "active_node_changed"
        ]
        if len(active_records) > 1:
            _add_coverage_diagnostic(
                diagnostics,
                "trace_active_commit_ambiguous",
                (
                    f"lifecycle commit {commit_id} contains more than one "
                    "active_node_changed record"
                ),
            )
        activated_task_ids: list[str] = []
        task_state_records: list[dict[str, Any]] = []
        current_active_deactivated = False
        for _, record in records:
            event_type = record.get("event_type")
            task_id = record.get("task_id")
            payload = record.get("payload", {})
            if event_type == "node_added" and isinstance(task_id, str):
                task_state_records.append(record)
                if payload.get("status") == "active":
                    activated_task_ids.append(task_id)
            elif event_type == "task_status_changed" and isinstance(task_id, str):
                task_state_records.append(record)
                if payload.get("to_status") == "active":
                    activated_task_ids.append(task_id)
                if (
                    task_id == replay_active_task_id
                    and payload.get("from_status") == "active"
                    and payload.get("to_status") != "active"
                ):
                    current_active_deactivated = True

        distinct_activated = list(dict.fromkeys(activated_task_ids))
        commit_sources = {
            (
                record.get("source", {}).get("kind"),
                record.get("source", {}).get("name"),
            )
            for _, record in records
            if isinstance(record.get("source"), dict)
        }
        authorized_recovery_source = (
            commit_sources == {("runtime_script", "stop_report")}
            or commit_sources == {("interaction_guard", "stop")}
        )
        retains_blocked_recovery_cursor = (
            current_active_deactivated
            and authorized_recovery_source
            and any(
                record.get("event_type") == "task_status_changed"
                and record.get("task_id") == replay_active_task_id
                and record.get("payload", {}).get("to_status") == "blocked"
                for _, record in records
            )
            and any(
                record.get("event_type") == "mission_status_changed"
                and record.get("payload", {}).get("to_status") == "requires_human"
                for _, record in records
            )
        )
        if active_records:
            recovery_cursor_task_id = None
        if retains_blocked_recovery_cursor:
            recovery_cursor_task_id = replay_active_task_id
        if (
            not active_records
            and current_active_deactivated
            and not retains_blocked_recovery_cursor
        ):
            _add_coverage_diagnostic(
                diagnostics,
                "trace_active_commit_incomplete",
                (
                    f"lifecycle commit {commit_id} deactivates current task "
                    f"{replay_active_task_id} without the matching "
                    "active_node_changed record"
                ),
            )
        elif (
            not active_records
            and len(distinct_activated) == 1
            and len(task_state_records) == 1
        ):
            activated_task_id = distinct_activated[0]
            if replay_active_task_id != activated_task_id:
                _add_coverage_diagnostic(
                    diagnostics,
                    "trace_active_commit_incomplete",
                    (
                        f"lifecycle commit {commit_id} activates task {activated_task_id} "
                        "without the matching active_node_changed record"
                    ),
                )

        for record in active_records:
            payload = record.get("payload", {})
            from_task_id = payload.get("from_task_id")
            if from_task_id != replay_active_task_id:
                _add_coverage_diagnostic(
                    diagnostics,
                    "trace_active_transition_mismatch",
                    (
                        f"active-node trace expects {from_task_id} "
                        f"but replay state is {replay_active_task_id}"
                    ),
                )
            replay_active_task_id = payload.get("to_task_id")
    return recovery_cursor_task_id


def _trace_coverage(
    mission: dict[str, Any],
    trace: list[dict[str, Any]],
) -> dict[str, Any]:
    if not trace:
        return {
            "coverage": "snapshot_only",
            "diagnostics": [],
            "initialized_at": None,
            "terminal_at": None,
            "snapshot_consistent": False,
        }

    diagnostics: list[dict[str, str]] = []
    initialization_records = [
        (index, record)
        for index, record in enumerate(trace)
        if record.get("event_type") == "mission_initialized"
    ]
    if not initialization_records:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_missing_initialization",
            "execution trace does not contain mission_initialized",
        )
        return {
            "coverage": "partial",
            "diagnostics": diagnostics,
            "initialized_at": None,
            "terminal_at": None,
            "snapshot_consistent": False,
        }

    initialization_index, initialization = initialization_records[0]
    if initialization_index != 0:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_initialization_not_first",
            "mission_initialized is not the first trace record",
        )
    if len(initialization_records) != 1:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_duplicate_initialization",
            "execution trace contains more than one mission_initialized record",
        )

    initialized_at = initialization["timestamp"]
    initialized_ms = _timestamp_ms(initialized_at)
    if any(_record_bounds_ms(record)[0] < initialized_ms for record in trace):
        _add_coverage_diagnostic(
            diagnostics,
            "trace_event_precedes_initialization",
            "an observed trace interval precedes mission_initialized",
        )

    payload = initialization.get("payload", {})
    replay_mission_status = payload.get("mission_status")
    replay_active_task_id = payload.get("active_task_id")
    replay_tasks: dict[str, dict[str, Any]] = {}
    for task_snapshot in payload.get("tasks", []):
        task_id = task_snapshot.get("id")
        if task_id in replay_tasks:
            _add_coverage_diagnostic(
                diagnostics,
                "trace_duplicate_initial_task",
                f"mission_initialized repeats task {task_id}",
            )
            continue
        replay_tasks[task_id] = {
            "status": task_snapshot.get("status"),
            "parent_id": task_snapshot.get("parent_id"),
            "kind": task_snapshot.get("kind"),
        }

    recovery_cursor_task_id = _validate_lifecycle_commit_integrity(
        trace,
        initialization_index=initialization_index,
        initial_active_task_id=replay_active_task_id,
        diagnostics=diagnostics,
    )

    terminal_at: str | None = None
    terminal_record_index: int | None = None
    last_state_change_index: int | None = None
    snapshot_mission_status = mission.get("mission", {}).get("status")
    for record_index, record in enumerate(
        trace[initialization_index + 1 :],
        start=initialization_index + 1,
    ):
        event_type = record.get("event_type")
        if event_type == "mission_initialized":
            continue
        task_id = record.get("task_id")
        event_payload = record.get("payload", {})
        if event_type == "node_added":
            last_state_change_index = record_index
            if task_id in replay_tasks:
                _add_coverage_diagnostic(
                    diagnostics,
                    "trace_duplicate_node_addition",
                    f"node_added repeats task {task_id}",
                )
            else:
                replay_tasks[task_id] = {
                    "status": event_payload.get("status"),
                    "parent_id": event_payload.get("parent_id"),
                    "kind": event_payload.get("kind"),
                }
            continue
        if event_type == "task_status_changed":
            last_state_change_index = record_index
            if task_id not in replay_tasks:
                _add_coverage_diagnostic(
                    diagnostics,
                    "trace_task_transition_without_node",
                    f"task_status_changed references uninitialized task {task_id}",
                )
                replay_tasks[task_id] = {
                    "status": event_payload.get("from_status"),
                    "parent_id": None,
                    "kind": None,
                }
            replay_status = replay_tasks[task_id].get("status")
            from_status = event_payload.get("from_status")
            if replay_status != from_status:
                _add_coverage_diagnostic(
                    diagnostics,
                    "trace_task_transition_mismatch",
                    (
                        f"task {task_id} trace expects {from_status} "
                        f"but replay state is {replay_status}"
                    ),
                )
            replay_tasks[task_id]["status"] = event_payload.get("to_status")
            continue
        if event_type == "active_node_changed":
            last_state_change_index = record_index
            from_task_id = event_payload.get("from_task_id")
            replay_active_task_id = event_payload.get("to_task_id")
            continue
        if event_type == "mission_status_changed":
            last_state_change_index = record_index
            from_status = event_payload.get("from_status")
            if replay_mission_status != from_status:
                _add_coverage_diagnostic(
                    diagnostics,
                    "trace_mission_transition_mismatch",
                    (
                        f"Mission trace expects {from_status} "
                        f"but replay state is {replay_mission_status}"
                    ),
                )
            replay_mission_status = event_payload.get("to_status")
            if replay_mission_status == snapshot_mission_status:
                terminal_at = record["timestamp"]
                terminal_record_index = record_index

    snapshot_tasks = task_map(mission)
    missing_task_ids = sorted(set(snapshot_tasks) - set(replay_tasks))
    unexpected_task_ids = sorted(set(replay_tasks) - set(snapshot_tasks))
    if missing_task_ids:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_missing_task_lifecycle",
            f"snapshot tasks missing from lifecycle trace: {', '.join(missing_task_ids)}",
        )
    if unexpected_task_ids:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_unknown_task_lifecycle",
            f"trace tasks missing from snapshot: {', '.join(unexpected_task_ids)}",
        )
    for task_id in sorted(set(snapshot_tasks) & set(replay_tasks)):
        snapshot_status = snapshot_tasks[task_id].get("status")
        replay_status = replay_tasks[task_id].get("status")
        if replay_status != snapshot_status:
            _add_coverage_diagnostic(
                diagnostics,
                "trace_task_status_mismatch",
                (
                    f"task {task_id} snapshot status is {snapshot_status} "
                    f"but trace replays to {replay_status}"
                ),
            )
        snapshot_parent_id = snapshot_tasks[task_id].get("parent_id")
        replay_parent_id = replay_tasks[task_id].get("parent_id")
        snapshot_kind = snapshot_tasks[task_id].get("kind")
        replay_kind = replay_tasks[task_id].get("kind")
        if replay_parent_id != snapshot_parent_id or replay_kind != snapshot_kind:
            _add_coverage_diagnostic(
                diagnostics,
                "trace_task_structure_mismatch",
                (
                    f"task {task_id} snapshot structure is "
                    f"parent={snapshot_parent_id}, kind={snapshot_kind} but trace replays to "
                    f"parent={replay_parent_id}, kind={replay_kind}"
                ),
            )

    snapshot_active_task_id = mission.get("active_task_id")
    if snapshot_active_task_id is not None:
        snapshot_active_task = snapshot_tasks.get(snapshot_active_task_id)
        snapshot_active_status = (
            snapshot_active_task.get("status")
            if snapshot_active_task is not None
            else None
        )
        valid_recovery_cursor = (
            snapshot_mission_status == "requires_human"
            and snapshot_active_status == "blocked"
            and snapshot_active_task_id == recovery_cursor_task_id
        )
        if (
            snapshot_active_task is None
            or (
                snapshot_active_status != "active"
                and not valid_recovery_cursor
            )
        ):
            _add_coverage_diagnostic(
                diagnostics,
                "snapshot_active_task_not_active",
                (
                    f"snapshot active_task_id {snapshot_active_task_id} does not "
                    "reference an active task"
                ),
            )
    if replay_active_task_id != snapshot_active_task_id:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_active_task_mismatch",
            (
                f"snapshot active_task_id is {snapshot_active_task_id} "
                f"but trace replays to {replay_active_task_id}"
            ),
        )
    if replay_mission_status != snapshot_mission_status:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_mission_status_mismatch",
            (
                f"Mission snapshot status is {snapshot_mission_status} "
                f"but trace replays to {replay_mission_status}"
            ),
        )
    if snapshot_mission_status in TERMINAL_MISSION_STATUSES and terminal_at is None:
        _add_coverage_diagnostic(
            diagnostics,
            "trace_missing_terminal_event",
            (
                "terminal Mission snapshot has no matching "
                "mission_status_changed lifecycle event"
            ),
        )
    elif (
        snapshot_mission_status in TERMINAL_MISSION_STATUSES
        and terminal_record_index != last_state_change_index
    ):
        _add_coverage_diagnostic(
            diagnostics,
            "trace_lifecycle_after_terminal",
            "task or Mission lifecycle changes occur after the matching terminal event",
        )

    return {
        "coverage": "exact" if not diagnostics else "partial",
        "diagnostics": diagnostics,
        "initialized_at": initialized_at,
        "terminal_at": terminal_at,
        "snapshot_consistent": not diagnostics,
    }


def _new_lifecycle_state() -> dict[str, Any]:
    return {
        "active_started_ms": None,
        "active_intervals": [],
        "activation_attempts": 0,
        "attempts": 0,
        "dynamic": False,
        "execution_order": None,
        "first_observed_at": None,
        "last_observed_at": None,
        "outcome_summary": None,
        "evidence_refs": [],
        "artifact_refs": [],
        "status_history": [],
        "visited": False,
    }


def _observe_node(state: dict[str, Any], timestamp: str, next_order: list[int]) -> None:
    state["visited"] = True
    if state["first_observed_at"] is None or _timestamp_ms(timestamp) < _timestamp_ms(
        state["first_observed_at"]
    ):
        state["first_observed_at"] = timestamp
    if state["last_observed_at"] is None or _timestamp_ms(timestamp) > _timestamp_ms(
        state["last_observed_at"]
    ):
        state["last_observed_at"] = timestamp
    if state["execution_order"] is None:
        state["execution_order"] = next_order[0]
        next_order[0] += 1


def _build_lifecycle(
    mission: dict[str, Any],
    trace: list[dict[str, Any]],
    coverage: str,
    generated_at: str,
) -> dict[str, dict[str, Any]]:
    states = {task_id: _new_lifecycle_state() for task_id in task_map(mission)}
    next_order = [1]
    open_span_tasks: dict[str, str] = {}
    ordered_trace = sorted(enumerate(trace), key=lambda item: (_record_time_ms(item[1]), item[0]))

    for _, record in ordered_trace:
        event_type = record["event_type"]
        timestamp = record["timestamp"]
        timestamp_ms = _timestamp_ms(timestamp)
        if event_type == "mission_initialized":
            for task_snapshot in record.get("payload", {}).get("tasks", []):
                if not isinstance(task_snapshot, dict):
                    continue
                task_id = task_snapshot.get("id")
                if task_id not in states:
                    continue
                state = states[task_id]
                status = task_snapshot.get("status")
                state["status_history"].append(
                    {"timestamp": timestamp, "from_status": None, "to_status": status, "source": "initial"}
                )
                if status == "active":
                    state["active_started_ms"] = timestamp_ms
                    state["activation_attempts"] = 1
                    _observe_node(state, timestamp, next_order)
            continue

        task_id = record.get("task_id")
        state = states.get(task_id) if isinstance(task_id, str) else None
        if event_type == "node_added" and state is not None:
            state["dynamic"] = True
            status = record.get("payload", {}).get("status")
            state["status_history"].append(
                {"timestamp": timestamp, "from_status": None, "to_status": status, "source": "node_added"}
            )
            if status == "active":
                state["active_started_ms"] = timestamp_ms
                state["activation_attempts"] = max(1, state["activation_attempts"])
                _observe_node(state, timestamp, next_order)
            continue

        if event_type == "task_status_changed" and state is not None:
            payload = record.get("payload", {})
            previous_status = payload.get("from_status")
            next_status = payload.get("to_status")
            if previous_status == "active" and state["active_started_ms"] is not None:
                state["active_intervals"].append((state["active_started_ms"], timestamp_ms))
                state["active_started_ms"] = None
            if next_status == "active":
                state["active_started_ms"] = timestamp_ms
                state["activation_attempts"] += 1
            state["status_history"].append(
                {
                    "timestamp": timestamp,
                    "from_status": previous_status,
                    "to_status": next_status,
                    "source": record.get("source", {}).get("name"),
                }
            )
            _observe_node(state, timestamp, next_order)
            outcome = payload.get("outcome_summary")
            if isinstance(outcome, str) and outcome:
                state["outcome_summary"] = outcome
            refs = record.get("refs", {})
            state["evidence_refs"] = _unique_strings(
                [*state["evidence_refs"], *refs.get("evidence_ids", []), *refs.get("evidence_links", [])]
            )
            state["artifact_refs"] = _unique_strings(
                [*state["artifact_refs"], *refs.get("artifact_refs", []), *payload.get("artifact_refs", [])]
            )
            continue

        if event_type == "span_started" and state is not None:
            _observe_node(state, timestamp, next_order)
            state["attempts"] = max(state["attempts"], record["span"]["attempt"])
            open_span_tasks[record["span"]["span_id"]] = task_id
            continue

        if event_type == "span_completed" and state is not None:
            open_span_tasks.pop(record["span"]["span_id"], None)
            _observe_node(state, record["span"]["started_at"], next_order)
            _observe_node(state, record["span"]["finished_at"], next_order)
            state["attempts"] = max(state["attempts"], record["span"]["attempt"])

    if trace:
        trace_finish_ms = max(_record_time_ms(record) for record in trace)
    else:
        trace_finish_ms = _timestamp_ms(generated_at)
    mission_status = mission.get("mission", {}).get("status")
    active_finish_ms = trace_finish_ms if mission_status in TERMINAL_MISSION_STATUSES else _timestamp_ms(generated_at)
    for task_id in set(open_span_tasks.values()):
        _observe_node(states[task_id], _iso_from_ms(active_finish_ms), next_order)
    for state in states.values():
        was_active = state["active_started_ms"] is not None
        if state["active_started_ms"] is not None:
            state["active_intervals"].append((state["active_started_ms"], active_finish_ms))
            state["active_started_ms"] = None
        if was_active:
            _observe_node(state, _iso_from_ms(active_finish_ms), next_order)
        observed_active_ms = (
            _union_duration_ms(state["active_intervals"]) if coverage != "snapshot_only" else None
        )
        duration_coverage = coverage
        state["observed_active_duration_ms"] = observed_active_ms
        state["active_duration_ms"] = observed_active_ms if duration_coverage == "exact" else None
        state["active_duration_source"] = duration_coverage
        observed_elapsed_ms = None
        if coverage != "snapshot_only" and state["first_observed_at"] and state["last_observed_at"]:
            observed_elapsed_ms = max(
                0,
                _timestamp_ms(state["last_observed_at"])
                - _timestamp_ms(state["first_observed_at"]),
            )
        state["observed_elapsed_ms"] = observed_elapsed_ms
        state["elapsed_ms"] = observed_elapsed_ms if duration_coverage == "exact" else None
        state["elapsed_coverage"] = duration_coverage
        state["attempts"] = max(state["attempts"], state["activation_attempts"])
        del state["active_intervals"]
        del state["active_started_ms"]
        del state["activation_attempts"]
    return states


def _descendant_ids(task_id: str, children: dict[str | None, list[str]]) -> list[str]:
    output: list[str] = []
    for child_id in children.get(task_id, []):
        output.append(child_id)
        output.extend(_descendant_ids(child_id, children))
    return output


def _mission_timing(
    mission: dict[str, Any],
    trace: list[dict[str, Any]],
    coverage_analysis: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    coverage = coverage_analysis["coverage"]
    if coverage == "snapshot_only":
        return {
            "elapsed_ms": None,
            "observed_elapsed_ms": None,
            "started_at": None,
            "finished_at": None,
            "observed_started_at": None,
            "observed_finished_at": None,
        }

    observed_bounds = [_record_bounds_ms(record) for record in trace]
    observed_start_ms = min(start for start, _ in observed_bounds)
    observed_finish_ms = max(finish for _, finish in observed_bounds)
    observed_started_at = _iso_from_ms(observed_start_ms)
    observed_finished_at = _iso_from_ms(observed_finish_ms)
    started_at = coverage_analysis.get("initialized_at")
    finished_at: str | None = None
    elapsed_ms: int | None = None
    if coverage == "exact":
        mission_status = mission.get("mission", {}).get("status")
        finished_at = (
            coverage_analysis.get("terminal_at")
            if mission_status in TERMINAL_MISSION_STATUSES
            else generated_at
        )
        if started_at is not None and finished_at is not None:
            elapsed_ms = max(0, _timestamp_ms(finished_at) - _timestamp_ms(started_at))
            observed_started_at = started_at
            observed_finished_at = finished_at
            observed_start_ms = _timestamp_ms(started_at)
            observed_finish_ms = _timestamp_ms(finished_at)
    return {
        "elapsed_ms": elapsed_ms,
        "observed_elapsed_ms": max(0, observed_finish_ms - observed_start_ms),
        "started_at": started_at,
        "finished_at": finished_at,
        "observed_started_at": observed_started_at,
        "observed_finished_at": observed_finished_at,
    }


def _node_actual_state(status: str, visited: bool) -> str:
    if status == "pending" and not visited:
        return "not_run"
    return status


def _select_nodes(
    nodes: list[dict[str, Any]],
    children: dict[str | None, list[str]],
    *,
    view: str,
    focus_task_id: str | None,
    top_cost: int,
) -> tuple[list[str], int, dict[str, list[str]]]:
    by_id = {node["id"]: node for node in nodes}
    if focus_task_id is not None and focus_task_id not in by_id:
        raise TplanError(f"focus task {focus_task_id} does not exist")
    scope = (
        {focus_task_id, *_descendant_ids(focus_task_id, children)}
        if focus_task_id is not None
        else set(by_id)
    )
    roots = [focus_task_id] if focus_task_id else list(children.get(None, []))

    reasons: dict[str, set[str]] = defaultdict(set)
    if view in {"standard", "audit"}:
        selected = set(scope)
        for task_id in selected:
            reasons[task_id].add("full_view")
    elif view == "compact":
        selected = {task_id for task_id in roots if task_id is not None}
        for task_id in selected:
            reasons[task_id].add("root")

        for task_id in scope:
            node = by_id[task_id]
            signal_reasons: list[str] = []
            if node["status"] == "active" or node["status"] in ABNORMAL_TASK_STATUSES:
                signal_reasons.append("status_signal")
            if node["attempts"] > 1:
                signal_reasons.append("retry")
            if node["direct_cost"]["error_span_count"]:
                signal_reasons.append("error")
            if node["direct_open_span_count"]:
                signal_reasons.append("open_span")
            if node["dynamic"]:
                signal_reasons.append("dynamic")
            if signal_reasons:
                selected.add(task_id)
                reasons[task_id].update(signal_reasons)

        def direct_cost_key(task_id: str) -> tuple[int, int, int, int]:
            node = by_id[task_id]
            direct_cost = node["direct_cost"]
            token_total = _counted_tokens(direct_cost["usage"])
            execution_order = node["execution_order"]
            return (
                direct_cost["additive_resource_time_ms"],
                token_total,
                -(execution_order if isinstance(execution_order, int) else 1_000_000),
                -node["plan_index"],
            )

        cost_candidates = [
            task_id
            for task_id in scope
            if task_id not in selected
            and (
                by_id[task_id]["direct_cost"]["additive_resource_time_ms"] > 0
                or any(by_id[task_id]["direct_cost"]["usage"].values())
            )
        ]
        for task_id in sorted(cost_candidates, key=direct_cost_key, reverse=True)[:top_cost]:
            selected.add(task_id)
            reasons[task_id].add("top_direct_cost")

        for task_id in list(selected):
            parent_id = by_id[task_id].get("parent_id")
            while parent_id in scope:
                selected.add(parent_id)
                reasons[parent_id].add("selected_path")
                parent_id = by_id[parent_id].get("parent_id")

    def sibling_key(task_id: str) -> tuple[int, int]:
        order = by_id[task_id]["execution_order"]
        return (order if isinstance(order, int) else 1_000_000, by_id[task_id]["plan_index"])

    ordered: list[str] = []

    def visit(task_id: str) -> None:
        if task_id in selected:
            ordered.append(task_id)
        for child_id in sorted(children.get(task_id, []), key=sibling_key):
            if child_id in scope and (
                child_id in selected
                or any(item in selected for item in _descendant_ids(child_id, children))
            ):
                visit(child_id)

    for root_id in sorted([item for item in roots if item is not None], key=sibling_key):
        visit(root_id)
    return (
        ordered,
        len(scope - selected),
        {task_id: sorted(reasons[task_id]) for task_id in ordered},
    )


def _duration_hotspots(nodes: list[dict[str, Any]], *, view: str) -> dict[str, Any]:
    """Rank comparable executed Task nodes by exact actual elapsed time."""

    eligible = [
        node
        for node in nodes
        if view == "standard"
        and node["kind"] == "task"
        and node["visited"]
        and node["elapsed_ms"] is not None
    ]
    eligible.sort(
        key=lambda node: (
            -node["elapsed_ms"],
            node["execution_order"] if node["execution_order"] is not None else 1_000_000,
            node["plan_index"],
        )
    )
    eligible_count = len(eligible)
    selected_count = (
        min(3, max(1, (eligible_count * 3) // 10)) if eligible_count >= 2 else 0
    )
    return {
        "enabled": view == "standard",
        "metric": "actual_elapsed_ms",
        "scope": "executed_task_nodes_with_exact_elapsed",
        "quota_rule": "min(3,max(1,floor(N*0.30))) when N>=2",
        "eligible_task_count": eligible_count,
        "selected_count": selected_count,
        "tasks": [
            {
                "task_id": node["id"],
                "rank": rank,
                "elapsed_ms": node["elapsed_ms"],
            }
            for rank, node in enumerate(eligible[:selected_count], start=1)
        ],
    }


def _timeline_metadata(
    mission: dict[str, Any],
    nodes: list[dict[str, Any]],
    *,
    focus_task_id: str | None,
) -> dict[str, Any]:
    """Build semantic layout data for the vertical execution timeline.

    Row spacing is deliberately ordinal so a long idle period cannot make the SVG
    unboundedly tall. Exact relative time remains visible in each row, while the
    per-node range bar uses one shared linear Mission scale.
    """

    elapsed_coverage = mission.get("elapsed_coverage")
    exact_coverage = elapsed_coverage == "exact"
    window_start = (
        mission.get("started_at") if exact_coverage else mission.get("observed_started_at")
    )
    window_finish = (
        mission.get("finished_at") if exact_coverage else mission.get("observed_finished_at")
    )
    window_elapsed = (
        mission.get("elapsed_ms") if exact_coverage else mission.get("observed_elapsed_ms")
    )
    origin_ms = _timestamp_ms(window_start) if window_start else None
    parent_by_id = {node["id"]: node.get("parent_id") for node in nodes}

    def depth_for(task_id: str) -> int:
        depth = 0
        current = parent_by_id.get(task_id)
        seen = {task_id}
        while current in parent_by_id and current not in seen:
            if current == focus_task_id:
                break
            seen.add(current)
            depth += 1
            current = parent_by_id.get(current)
        return depth

    rows: list[dict[str, Any]] = []
    for tree_index, node in enumerate(nodes):
        started_at = node.get("first_observed_at")
        finished_at = node.get("last_observed_at")
        start_offset_ms = (
            max(0, _timestamp_ms(started_at) - origin_ms)
            if origin_ms is not None and started_at is not None
            else None
        )
        finish_offset_ms = (
            max(start_offset_ms or 0, _timestamp_ms(finished_at) - origin_ms)
            if origin_ms is not None and finished_at is not None
            else None
        )
        rows.append(
            {
                "node_id": node["id"],
                "depth": depth_for(node["id"]),
                "tree_index": tree_index,
                "execution_order": node.get("execution_order"),
                "start_offset_ms": start_offset_ms,
                "finish_offset_ms": finish_offset_ms,
            }
        )

    rows.sort(
        key=lambda row: (
            row["start_offset_ms"] is None,
            row["start_offset_ms"] if row["start_offset_ms"] is not None else 0,
            row["execution_order"] if row["execution_order"] is not None else 1_000_000,
            row["tree_index"],
        )
    )
    return {
        "axis": "vertical",
        "row_positioning": (
            "first_observed_chronological"
            if elapsed_coverage != "snapshot_only"
            else "declared_tree_order"
        ),
        "row_spacing": "ordinal_not_duration_proportional",
        "range_bar_scale": (
            "linear_mission_elapsed"
            if exact_coverage
            else "linear_observed_window"
            if elapsed_coverage == "partial"
            else "not_available"
        ),
        "offset_coverage": elapsed_coverage,
        "offset_origin": (
            "mission_initialized"
            if exact_coverage
            else "first_observed_trace"
            if elapsed_coverage == "partial"
            else None
        ),
        "window_kind": (
            "mission_lifecycle"
            if exact_coverage
            else "observed_trace"
            if elapsed_coverage == "partial"
            else "snapshot_only"
        ),
        "window_started_at": window_start,
        "window_finished_at": window_finish,
        "window_elapsed_ms": window_elapsed,
        "rows": rows,
    }


def build_execution_cost_tree(
    mission_dir: Path,
    *,
    view: str = "standard",
    focus_task_id: str | None = None,
    top_cost: int = 3,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if view not in VIEWS:
        raise TplanError(f"execution cost tree view unsupported: {view}")
    if top_cost < 0:
        raise TplanError("top_cost must be non-negative")
    generated_at = generated_at or _now_iso()
    try:
        _parse_timestamp(generated_at)
    except ValueError as exc:
        raise TplanError("generated_at must be ISO-8601 with timezone") from exc

    snapshot = read_outcome_attribution_snapshot(mission_dir)
    mission = snapshot["mission"]
    runtime_provenance = snapshot["runtime_provenance"]
    mission_errors = validate_mission(mission)
    if mission_errors:
        raise TplanError("; ".join(mission_errors))
    trace = snapshot["trace"]
    _validate_trace(mission, trace)
    outcome_attribution = build_outcome_attribution(mission, snapshot["events"], trace)
    coverage_analysis = _trace_coverage(mission, trace)
    coverage = coverage_analysis["coverage"]
    lifecycle = _build_lifecycle(mission, trace, coverage, generated_at)
    tasks = mission.get("tasks", [])
    by_id = task_map(mission)
    plan_index = {task["id"]: index for index, task in enumerate(tasks) if isinstance(task, dict)}
    children: dict[str | None, list[str]] = defaultdict(list)
    for task_id, task in by_id.items():
        children[task.get("parent_id")].append(task_id)
    for parent_id in children:
        children[parent_id].sort(key=lambda task_id: plan_index[task_id])

    exact_spans: dict[str, list[dict[str, Any]]] = defaultdict(list)
    overhead_spans: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_spans: list[dict[str, Any]] = []
    started_spans = [record for record in trace if record["event_type"] == "span_started"]
    completed_span_ids = {
        record["span"]["span_id"]
        for record in trace
        if record["event_type"] == "span_completed"
    }
    open_spans = [
        record
        for record in started_spans
        if record["span"]["span_id"] not in completed_span_ids
    ]
    for record in trace:
        if record["event_type"] != "span_completed":
            continue
        all_spans.append(record)
        attribution = record["span"]["attribution"]
        if attribution == "exact":
            exact_spans[record["task_id"]].append(record)
        else:
            overhead_spans[attribution].append(record)

    usage_owner_event_ids = _usage_owner_event_ids(all_spans)

    mission_timing = _mission_timing(mission, trace, coverage_analysis, generated_at)
    observed_elapsed_ms = mission_timing["observed_elapsed_ms"]
    started_at = mission_timing["started_at"]
    finished_at = mission_timing["finished_at"]
    mission_elapsed_ms = mission_timing["elapsed_ms"]
    mission_cost = _span_cost(all_spans, usage_owner_event_ids=usage_owner_event_ids)
    presentation_density = _presentation_density_profile(
        lifecycle_coverage=coverage,
        cost=mission_cost,
    )
    mission_elapsed_reconciliation = _elapsed_reconciliation(
        all_spans,
        elapsed_ms=mission_elapsed_ms,
        observed_elapsed_ms=observed_elapsed_ms,
        coverage=coverage,
        started_at=started_at,
        finished_at=finished_at,
    )

    active_task_id = mission.get("active_task_id")
    nodes: list[dict[str, Any]] = []
    for task_id, task in by_id.items():
        state = lifecycle[task_id]
        descendant_ids = _descendant_ids(task_id, children)
        inclusive_records = [
            record
            for descendant_id in [task_id, *descendant_ids]
            for record in exact_spans.get(descendant_id, [])
        ]
        direct_records = exact_spans.get(task_id, [])
        direct_open_spans = [
            record
            for record in open_spans
            if record["span"]["attribution"] == "exact" and record.get("task_id") == task_id
        ]
        inclusive_open_spans = [
            record
            for record in open_spans
            if record["span"]["attribution"] == "exact"
            and record.get("task_id") in {task_id, *descendant_ids}
        ]
        direct_cost = _span_cost(direct_records, usage_owner_event_ids=usage_owner_event_ids)
        inclusive_cost = _span_cost(inclusive_records, usage_owner_event_ids=usage_owner_event_ids)
        elapsed_ms = state["elapsed_ms"]
        observed_node_elapsed_ms = state["observed_elapsed_ms"]
        elapsed_coverage = state["elapsed_coverage"]
        node = {
            "id": task_id,
            "parent_id": task.get("parent_id"),
            "kind": task.get("kind"),
            "level": task.get("level"),
            "title": task.get("title"),
            "status": task.get("status"),
            "actual_state": _node_actual_state(str(task.get("status")), state["visited"]),
            "role": task.get("role"),
            "dynamic": state["dynamic"],
            "visited": state["visited"],
            "execution_order": state["execution_order"],
            "attempts": state["attempts"],
            "first_observed_at": state["first_observed_at"],
            "last_observed_at": state["last_observed_at"],
            "elapsed_ms": elapsed_ms,
            "observed_elapsed_ms": observed_node_elapsed_ms,
            "elapsed_coverage": elapsed_coverage,
            "active_duration_ms": state["active_duration_ms"],
            "observed_active_duration_ms": state["observed_active_duration_ms"],
            "active_duration_source": state["active_duration_source"],
            "outcome_summary": state["outcome_summary"],
            "evidence_refs": state["evidence_refs"],
            "artifact_refs": state["artifact_refs"],
            "outcome_attribution": outcome_attribution["tasks"][task_id],
            "status_history": state["status_history"],
            "direct_cost": direct_cost,
            "inclusive_cost": inclusive_cost,
            "direct_open_span_count": len(direct_open_spans),
            "inclusive_open_span_count": len(inclusive_open_spans),
            "direct_elapsed_reconciliation": _elapsed_reconciliation(
                direct_records,
                elapsed_ms=elapsed_ms,
                observed_elapsed_ms=observed_node_elapsed_ms,
                coverage=elapsed_coverage,
                started_at=state["first_observed_at"],
                finished_at=state["last_observed_at"],
            ),
            "subtree_elapsed_reconciliation": _elapsed_reconciliation(
                inclusive_records,
                elapsed_ms=elapsed_ms,
                observed_elapsed_ms=observed_node_elapsed_ms,
                coverage=elapsed_coverage,
                started_at=state["first_observed_at"],
                finished_at=state["last_observed_at"],
            ),
            "plan_index": plan_index[task_id],
            "active_task_id": active_task_id,
        }
        nodes.append(node)

    visible_ids, hidden_count, selection_reasons = _select_nodes(
        nodes,
        children,
        view=view,
        focus_task_id=focus_task_id,
        top_cost=top_cost,
    )
    duration_hotspots = _duration_hotspots(nodes, view=view)
    visible_set = set(visible_ids)
    visible_nodes = [next(node for node in nodes if node["id"] == task_id) for task_id in visible_ids]
    for node in visible_nodes:
        node.pop("plan_index", None)
        node.pop("active_task_id", None)
    outcome_attribution["mission"]["node_yield_counts"] = dict(
        Counter(node["outcome_attribution"]["yield_class"] for node in nodes)
    )
    overhead_by_attribution = {
        attribution: _span_cost(records, usage_owner_event_ids=usage_owner_event_ids)
        for attribution, records in sorted(overhead_spans.items())
    }
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "view": view,
        "presentation": "unicode_text_tree" if view == "compact" else "vertical_timeline_svg",
        "focus_task_id": focus_task_id,
        "top_cost": top_cost,
        "runtime": runtime_provenance,
        "telemetry_capture": _read_telemetry_capture(
            mission_dir, mission.get("mission", {}).get("id")
        ),
        "presentation_density": presentation_density,
        "mission": {
            "id": mission.get("mission", {}).get("id"),
            "title": mission.get("mission", {}).get("title"),
            "status": mission.get("mission", {}).get("status"),
            "active_task_id": active_task_id,
            "elapsed_ms": mission_elapsed_ms,
            "observed_elapsed_ms": observed_elapsed_ms,
            "elapsed_coverage": coverage,
            "started_at": started_at,
            "finished_at": finished_at,
            "observed_started_at": mission_timing["observed_started_at"],
            "observed_finished_at": mission_timing["observed_finished_at"],
            "cost": mission_cost,
            "elapsed_reconciliation": mission_elapsed_reconciliation,
            "outcome_attribution": outcome_attribution["mission"],
        },
        "trace": {
            "coverage": coverage,
            "coverage_diagnostics": coverage_analysis["diagnostics"],
            "snapshot_consistent": coverage_analysis["snapshot_consistent"],
            "record_count": len(trace),
            "span_count": len(all_spans),
            "started_span_count": len(started_spans),
            "completed_span_count": len(all_spans),
            "open_span_count": len(open_spans),
            "open_spans": [
                {
                    "span_id": record["span"]["span_id"],
                    "task_id": record.get("task_id"),
                    "kind": record["span"]["kind"],
                    "label": record["span"].get("label"),
                    "entry_observed_at": record["timestamp"],
                }
                for record in open_spans
            ],
            "cost_scope": "reported_spans_only",
            "hidden_node_count": hidden_count,
            "visible_node_count": len(visible_nodes),
            "total_node_count": len(nodes),
            "structure_fidelity": "one_to_one",
            "projection": view == "compact" or focus_task_id is not None,
            "selection_reasons": selection_reasons if view == "compact" else {},
        },
        "overhead": {
            "cost": _span_cost(
                [record for records in overhead_spans.values() for record in records],
                usage_owner_event_ids=usage_owner_event_ids,
            ),
            "by_attribution": overhead_by_attribution,
        },
        "metric_semantics": {
            "actual_elapsed_ms": (
                "exact natural elapsed time between replay-consistent lifecycle boundaries"
            ),
            "model_resource_time_ms": (
                "sum of completed model-call durations; host_measured is caller-visible request "
                "elapsed, not provider-internal inference time"
            ),
            "exact_interval_coverage_ms": (
                "union of completed exact-time model, script, tool, wait, and runtime intervals"
            ),
            "not_exactly_recorded_elapsed_ms": (
                "actual elapsed minus exact interval coverage; not a claim that the remainder is model or script time"
            ),
            "observed_trace_window": (
                "first-to-last observed trace interval; never promoted to exact Mission completion time"
            ),
        },
        "nodes": visible_nodes,
        "visible_node_ids": visible_ids,
    }
    if view == "standard":
        report["duration_hotspots"] = duration_hotspots
    report["tree_edges"] = _visible_edges(visible_nodes, visible_set, focus_task_id)
    if view == "compact":
        report["compact_projection"] = {
            "policy": "roots_plus_signals_and_top_direct_cost",
            "top_direct_cost_count": top_cost,
            "signal_rules": ["active_or_abnormal", "retry", "error", "open_span", "dynamic"],
            "selected_paths_preserved": True,
        }
    else:
        report["timeline"] = _timeline_metadata(
            report["mission"],
            visible_nodes,
            focus_task_id=focus_task_id,
        )
    return report


def _visible_edges(
    nodes: list[dict[str, Any]],
    visible_ids: set[str],
    focus_task_id: str | None,
) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for node in nodes:
        task_id = node["id"]
        parent_id = node["parent_id"]
        if task_id == focus_task_id or parent_id is None:
            edges.append({"from": "mission", "to": task_id})
        elif parent_id in visible_ids:
            edges.append({"from": parent_id, "to": task_id})
    return edges


def _fmt_duration(value: int | None) -> str:
    if value is None:
        return "未知"
    if value < 1000:
        return f"{value}ms"
    seconds = value / 1000
    if seconds < 60:
        return f"{seconds:.1f}s" if seconds < 10 else f"{seconds:.0f}s"
    minutes, remaining = divmod(round(seconds), 60)
    if minutes < 60:
        return f"{minutes}m{remaining:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m"


def _fmt_covered_duration(exact_value: int | None, observed_value: int | None, coverage: str) -> str:
    if coverage == "exact":
        return _fmt_duration(exact_value)
    if coverage == "partial" and observed_value is not None:
        return f"≥{_fmt_duration(observed_value)}"
    return "未知"


def _elapsed_scope_label(coverage: str, *, mission: bool = False) -> str:
    if coverage == "partial":
        return "已观测窗口" if mission else "已观测区间"
    return "实际历时"


def _fmt_token_number(value: int) -> str:
    if value < 1000:
        return str(value)
    if value < 1_000_000:
        return f"{value / 1000:.1f}k"
    return f"{value / 1_000_000:.1f}m"


def _fmt_tokens(cost: dict[str, Any]) -> str:
    usage = cost["usage"]
    fields = set(cost["usage_fields"])
    coverage = cost["usage_coverage"]
    if coverage == "not_reported":
        return "未采集"
    if coverage == "unavailable" or not ({"input_tokens", "output_tokens"} & fields):
        return "未知"
    lower_bound = "≥" if coverage == "partial" else ""
    input_value = (
        lower_bound + _fmt_token_number(usage.get("input_tokens", 0))
        if "input_tokens" in fields
        else "?"
    )
    output_value = (
        lower_bound + _fmt_token_number(usage.get("output_tokens", 0))
        if "output_tokens" in fields
        else "?"
    )
    suffix: list[str] = []
    if "cached_input_tokens" in fields:
        suffix.append(f"缓存 {_fmt_token_number(usage.get('cached_input_tokens', 0))}")
    if "reasoning_output_tokens" in fields:
        suffix.append(f"推理 {_fmt_token_number(usage.get('reasoning_output_tokens', 0))}")
    estimate_prefix = "≈" if cost["usage_sources"].get("inferred") else ""
    return f"{estimate_prefix}输入 {input_value} / 输出 {output_value}" + (
        f" ({', '.join(suffix)})" if suffix else ""
    )


def _fmt_tokens_compact(cost: dict[str, Any]) -> str:
    usage = cost["usage"]
    fields = set(cost["usage_fields"])
    coverage = cost["usage_coverage"]
    if coverage == "not_reported":
        return "未采集"
    if coverage == "unavailable" or not ({"input_tokens", "output_tokens"} & fields):
        return "未知"
    lower_bound = "≥" if coverage == "partial" else ""
    input_value = (
        lower_bound + _fmt_token_number(usage.get("input_tokens", 0))
        if "input_tokens" in fields
        else "?"
    )
    output_value = (
        lower_bound + _fmt_token_number(usage.get("output_tokens", 0))
        if "output_tokens" in fields
        else "?"
    )
    estimate_prefix = "≈" if cost["usage_sources"].get("inferred") else ""
    return f"{estimate_prefix}入 {input_value} / 出 {output_value}"


def _kind_time(cost: dict[str, Any], kinds: set[str]) -> int:
    return sum(cost["by_kind_resource_ms"].get(kind, 0) for kind in kinds)


def _fmt_kind_duration(
    cost: dict[str, Any],
    kinds: set[str],
    *,
    host_label: str = "宿主实测",
) -> str:
    present = [kind for kind in kinds if kind in cost["by_kind_resource_ms"]]
    if not present:
        return "未采集"
    sources: Counter[str] = Counter()
    for kind in present:
        sources.update(cost["by_kind_measurement_sources"].get(kind, {}))
    value = _kind_time(cost, kinds)
    if sources and set(sources) == {"unavailable"}:
        return "未知"
    rendered = _fmt_duration(value)
    if sources.get("unavailable"):
        return f"≥{rendered}（部分未知）" if value else "未知"
    if sources.get("inferred"):
        estimate_label = "估算" if set(sources) == {"inferred"} else "含估算"
        return f"≈{rendered}（{estimate_label}）"
    exact_sources = set(sources)
    if exact_sources == {"host_measured"}:
        source_label = host_label
    elif exact_sources == {"platform_reported"}:
        source_label = "平台上报"
    elif exact_sources:
        source_label = "混合实测"
    else:
        return rendered
    return f"{rendered}（{source_label}）"


def _fmt_resource_duration(cost: dict[str, Any]) -> str:
    if cost["span_count"] == cost["envelope_span_count"]:
        return "未采集"
    sources = Counter(cost["measurement_sources"])
    for source, count in cost["by_kind_measurement_sources"].get("agent_turn", {}).items():
        sources[source] -= count
        if sources[source] <= 0:
            del sources[source]
    value = cost["additive_resource_time_ms"]
    if sources and set(sources) == {"unavailable"}:
        return "未知"
    rendered = _fmt_duration(value)
    if sources.get("unavailable"):
        return f"≥{rendered}" if value else "未知"
    if sources.get("inferred"):
        return f"≈{rendered}"
    return rendered


def _shorten(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _html(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _fmt_not_exactly_recorded(elapsed_reconciliation: dict[str, Any]) -> str:
    if elapsed_reconciliation["coverage"] != "exact":
        return "未知"
    return _fmt_duration(elapsed_reconciliation["not_exactly_recorded_elapsed_ms"])


def _node_cost_view(node: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    if node["kind"] == "step":
        return node["direct_cost"], node["direct_elapsed_reconciliation"], "直接成本"
    return node["inclusive_cost"], node["subtree_elapsed_reconciliation"], "子树汇总"


def _standard_cost_metric_fragments(cost: dict[str, Any]) -> list[str]:
    fragments: list[str] = []
    for name, _label, render_label, kinds in STANDARD_DURATION_CHANNELS:
        if _duration_channel_status(cost, kinds) == "not_reported":
            continue
        host_label = "调用端实测" if name == "model_duration" else "宿主实测"
        fragments.append(
            f"{render_label} "
            f"{_fmt_kind_duration(cost, kinds, host_label=host_label)}"
        )
    if cost["usage_coverage"] != "not_reported":
        fragments.append(f"Token {_fmt_tokens_compact(cost)}")
    return fragments


def _chunk_metric_fragments(
    fragments: list[str],
    *,
    size: int = 2,
) -> list[str]:
    return [
        " · ".join(fragments[index : index + size])
        for index in range(0, len(fragments), size)
    ]


def _execution_presentation_title(report: dict[str, Any]) -> str:
    coverage = report["trace"]["coverage"]
    if coverage == "exact":
        return "TPlan 纵向实际执行时间轴"
    if coverage == "partial":
        return "TPlan 已观测执行窗口"
    return "TPlan Mission 结构快照"


def _standard_node_content_lines(
    node: dict[str, Any],
    row: dict[str, Any],
    *,
    time_coverage: str,
) -> list[tuple[str, str]]:
    cost, reconciliation, scope_label = _node_cost_view(node)
    lines: list[tuple[str, str]] = [
        (_svg_node_status_details(node, scope_label), "node-meta")
    ]
    elapsed = _fmt_covered_duration(
        node["elapsed_ms"],
        node["observed_elapsed_ms"],
        node["elapsed_coverage"],
    )
    if elapsed != "未知":
        time_parts: list[str] = []
        if (
            row.get("start_offset_ms") is not None
            and row.get("finish_offset_ms") is not None
        ):
            time_parts.append(
                "时间 "
                f"{_fmt_timeline_offset(row['start_offset_ms'], time_coverage)} → "
                f"{_fmt_timeline_offset(row['finish_offset_ms'], time_coverage)}"
            )
        time_parts.append(
            f"{_elapsed_scope_label(node['elapsed_coverage'])} {elapsed}"
        )
        not_exact = _fmt_not_exactly_recorded(reconciliation)
        if not_exact != "未知":
            time_parts.append(f"未被精确记录 {not_exact}")
        lines.append((" · ".join(time_parts), "node-metric"))
    lines.extend(
        (fragment_line, "node-metric")
        for fragment_line in _chunk_metric_fragments(
            _standard_cost_metric_fragments(cost)
        )
    )
    lines.extend(
        [
            (
                "结果："
                + (
                    _shorten(node["outcome_summary"], 82)
                    if node["outcome_summary"]
                    else "未记录"
                ),
                "node-result",
            ),
            (
                "产出归因："
                + _shorten(
                    attribution_text(node["outcome_attribution"]),
                    74,
                ),
                "node-result",
            ),
        ]
    )
    return lines


def _standard_mission_header_lines(report: dict[str, Any]) -> list[str]:
    mission = report["mission"]
    mission_status = STATUS_LABELS.get(mission["status"], mission["status"])
    elapsed = _fmt_covered_duration(
        mission["elapsed_ms"],
        mission["observed_elapsed_ms"],
        mission["elapsed_coverage"],
    )
    status_line = f"Mission · {mission_status}"
    if elapsed != "未知":
        status_line += (
            f" · {_elapsed_scope_label(mission['elapsed_coverage'], mission=True)} "
            f"{elapsed}"
        )
    metric_fragments = _standard_cost_metric_fragments(mission["cost"])
    not_exact = _fmt_not_exactly_recorded(mission["elapsed_reconciliation"])
    if not_exact != "未知":
        metric_fragments.append(f"未被精确记录 {not_exact}")
    mission_attribution = mission["outcome_attribution"]
    visible_node_label = (
        "可见真实节点" if report["trace"]["projection"] else "真实节点"
    )
    return [
        status_line,
        report["presentation_density"]["standard_note"],
        *_chunk_metric_fragments(metric_fragments),
        (
            f"{visible_node_label} "
            f"{report['trace']['visible_node_count']}/{report['trace']['total_node_count']}"
            f" · 产出归因 P{len(mission_attribution['countable_progress'])}"
            f"/C{len(mission_attribution['constraint_deltas'])}"
            f" · 生命周期 {report['trace']['coverage']}"
            + (
                f" · 生命周期告警 {len(report['trace'].get('coverage_diagnostics', []))}"
                if report["trace"].get("coverage_diagnostics")
                else ""
            )
            + f" · 运行时 {report['runtime']['status']}"
            + " · standard"
        ),
    ]


def _fmt_timeline_offset(value: int | None, coverage: str = "exact") -> str:
    if value is None:
        return "未观测"
    sign = "+" if coverage == "exact" and value >= 0 else "≥" if value >= 0 else "−"
    value = abs(value)
    hours, remainder = divmod(value, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    if hours:
        return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    return f"{sign}{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _svg_status_palette(status: str) -> tuple[str, str, str]:
    return {
        "active": ("#eff6ff", "#2563eb", "#1e3a8a"),
        "completed": ("#f0fdf4", "#16a34a", "#14532d"),
        "blocked": ("#fef2f2", "#dc2626", "#7f1d1d"),
        "paused": ("#fffbeb", "#d97706", "#78350f"),
        "pending": ("#f8fafc", "#94a3b8", "#475569"),
        "pruned": ("#f8fafc", "#64748b", "#334155"),
        "abandoned": ("#fff1f2", "#e11d48", "#881337"),
        "superseded": ("#f8fafc", "#64748b", "#334155"),
    }.get(status, ("#f8fafc", "#64748b", "#334155"))


def _svg_text(
    x: int | float,
    y: int | float,
    value: Any,
    class_name: str,
    *,
    anchor: str | None = None,
) -> str:
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x}" y="{y}" class="{class_name}"{anchor_attr}>{_html(value)}</text>'


def _svg_node_status_details(node: dict[str, Any], scope_label: str) -> str:
    details = [
        f"#{node['execution_order']}" if node["execution_order"] is not None else "未运行",
        scope_label,
    ]
    if node["dynamic"]:
        details.append("动态新增")
    if node["attempts"] > 1:
        details.append(f"执行次数 {node['attempts']}")
    if node["direct_cost"]["error_span_count"]:
        details.append(f"错误 {node['direct_cost']['error_span_count']}")
    open_span_count = (
        node["direct_open_span_count"]
        if node["kind"] == "step"
        else node["inclusive_open_span_count"]
    )
    if open_span_count:
        details.append(f"未结束调用 {open_span_count}")
    return " · ".join(details)


def _compact_status(status: str, actual_state: str | None = None) -> str:
    if actual_state == "not_run":
        return "○ 未执行"
    return {
        "active": "▶️ 执行中",
        "completed": "✅",
        "blocked": "⛔ 受阻",
        "paused": "⏸ 已暂停",
        "pending": "○ 待执行",
        "pruned": "✂ 已裁剪",
        "abandoned": "↩ 已撤回",
        "superseded": "↪ 已替代",
        "budget_exhausted": "⛔ 预算耗尽",
        "requires_human": "⛔ 等待人工",
    }.get(status, STATUS_LABELS.get(status, status))


def _compact_cost_summary(cost: dict[str, Any]) -> str:
    parts = [
        f"LLM {_fmt_kind_duration_compact(cost, LLM_KINDS)}",
        f"脚本 {_fmt_kind_duration_compact(cost, SCRIPT_KINDS)}",
    ]
    optional = [
        ("工具", _fmt_kind_duration_compact(cost, TOOL_KINDS)),
        ("等待", _fmt_kind_duration_compact(cost, WAIT_KINDS)),
    ]
    parts.extend(f"{label} {value}" for label, value in optional if value != "—")
    return " / ".join(parts)


def _fmt_kind_duration_compact(cost: dict[str, Any], kinds: set[str]) -> str:
    present = [kind for kind in kinds if kind in cost["by_kind_resource_ms"]]
    if not present:
        return "—"
    sources: Counter[str] = Counter()
    for kind in present:
        sources.update(cost["by_kind_measurement_sources"].get(kind, {}))
    value = _kind_time(cost, kinds)
    if sources and set(sources) == {"unavailable"}:
        return "?"
    rendered = _fmt_duration(value)
    if sources.get("unavailable"):
        return f"≥{rendered}" if value else "?"
    if sources.get("inferred"):
        return f"≈{rendered}"
    return rendered


def _fmt_tokens_inline(cost: dict[str, Any]) -> str:
    usage = cost["usage"]
    fields = set(cost["usage_fields"])
    coverage = cost["usage_coverage"]
    if coverage == "not_reported":
        return "—"
    if coverage == "unavailable" or not ({"input_tokens", "output_tokens"} & fields):
        return "?"
    input_value = _fmt_token_number(usage.get("input_tokens", 0)) if "input_tokens" in fields else "?"
    output_value = _fmt_token_number(usage.get("output_tokens", 0)) if "output_tokens" in fields else "?"
    prefix = "≈" if cost["usage_sources"].get("inferred") else ""
    if coverage == "partial":
        prefix += "≥"
    return f"{prefix}{input_value}/{output_value}"


def _compact_kind_source(
    cost: dict[str, Any],
    kinds: set[str],
    *,
    host_label: str,
) -> str | None:
    present = [kind for kind in kinds if kind in cost["by_kind_resource_ms"]]
    if not present:
        return None
    sources: Counter[str] = Counter()
    for kind in present:
        sources.update(cost["by_kind_measurement_sources"].get(kind, {}))
    labels = [
        label
        for source, label in (
            ("platform_reported", "平台上报"),
            ("host_measured", host_label),
            ("inferred", "估算"),
            ("unavailable", "未知"),
        )
        if sources.get(source)
    ]
    return "/".join(labels) if labels else "来源未标注"


def _compact_source_legend(cost: dict[str, Any]) -> str:
    source_groups: dict[str, list[str]] = defaultdict(list)
    for label, kinds, host_label in (
        ("LLM", LLM_KINDS, "调用端实测"),
        ("脚本", SCRIPT_KINDS, "宿主实测"),
        ("工具", TOOL_KINDS, "宿主实测"),
        ("等待", WAIT_KINDS, "宿主实测"),
    ):
        source = _compact_kind_source(cost, kinds, host_label=host_label)
        if source is not None:
            source_groups[source].append(label)
    if not source_groups:
        rendered = "本次未采集资源时长"
    else:
        rendered = " · ".join(
            f"{'/'.join(labels)} {source}" for source, labels in source_groups.items()
        )
    return f"来源：{rendered}"


def _compact_signal_reasons(node: dict[str, Any], reasons: set[str]) -> set[str]:
    signal_reasons = reasons & {
        "status_signal",
        "retry",
        "error",
        "open_span",
        "dynamic",
    }
    if node["status"] != "completed" and node["actual_state"] != "not_run":
        signal_reasons.add("non_routine_status")
    return signal_reasons


def _compact_node_summary(node: dict[str, Any], reasons: set[str]) -> str:
    cost, _, _ = _node_cost_view(node)
    elapsed = _fmt_covered_duration(
        node["elapsed_ms"], node["observed_elapsed_ms"], node["elapsed_coverage"]
    )
    if node["elapsed_coverage"] == "partial":
        elapsed = f"观测 {elapsed}"
    kind_tag = COMPACT_KIND_TAGS.get(node["kind"], "[?]")
    parts = [
        f"{kind_tag} {_shorten(node['title'], 40)} "
        f"{_compact_status(node['status'], node['actual_state'])} {elapsed}",
        _compact_cost_summary(cost),
    ]
    signal_reasons = _compact_signal_reasons(node, reasons)
    token_value = _fmt_tokens_inline(cost)
    if token_value != "—" and ("top_direct_cost" in reasons or signal_reasons):
        parts.append(f"Tok {token_value}")
    if node["dynamic"]:
        parts.append("动态")
    if node["attempts"] > 1:
        parts.append(f"↻{node['attempts']}")
    if node["direct_cost"]["error_span_count"]:
        parts.append(f"✕{node['direct_cost']['error_span_count']}")
    if node["direct_open_span_count"]:
        parts.append(f"未结束 {node['direct_open_span_count']}")
    if node["outcome_summary"] and signal_reasons:
        parts.append(f"→ {_shorten(node['outcome_summary'], 52)}")
    parts.append(short_attribution_label(node["outcome_attribution"]))
    return " · ".join(parts)


def render_compact_text(report: dict[str, Any]) -> str:
    if report["view"] != "compact":
        raise TplanError("text tree is only available for compact view")
    mission = report["mission"]
    mission_elapsed = _fmt_covered_duration(
        mission["elapsed_ms"], mission["observed_elapsed_ms"], mission["elapsed_coverage"]
    )
    if mission["elapsed_coverage"] == "partial":
        mission_elapsed = f"观测 {mission_elapsed}"
    mission_token = _fmt_tokens_inline(mission["cost"])
    mission_line = (
        f"Mission · {_shorten(mission['title'], 60)} "
        f"{_compact_status(mission['status'])} {mission_elapsed}"
        f" · {_compact_cost_summary(mission['cost'])}"
    )
    if mission_token != "—":
        mission_line += f" · Tok {mission_token}"
    mission_line += f" · {short_attribution_label(mission['outcome_attribution'])}"
    lines = [mission_line, "层级：[T] Task · [ST] SubTask · [P] Step"]
    node_by_id = {node["id"]: node for node in report["nodes"]}
    selection_reasons = {
        task_id: set(reasons)
        for task_id, reasons in report["trace"]["selection_reasons"].items()
    }
    order = {node["id"]: index for index, node in enumerate(report["nodes"])}
    children: dict[str, list[str]] = defaultdict(list)
    roots: list[str] = []
    for node in report["nodes"]:
        parent_id = node.get("parent_id")
        if parent_id in node_by_id:
            children[parent_id].append(node["id"])
        else:
            roots.append(node["id"])
    for parent_id in children:
        children[parent_id].sort(key=lambda task_id: order[task_id])
    roots.sort(key=lambda task_id: order[task_id])

    def visit(task_id: str, prefix: str, is_last: bool) -> None:
        connector = "└─ " if is_last else "├─ "
        lines.append(
            prefix
            + connector
            + _compact_node_summary(node_by_id[task_id], selection_reasons.get(task_id, set()))
        )
        next_prefix = prefix + ("   " if is_last else "│  ")
        child_ids = children.get(task_id, [])
        for index, child_id in enumerate(child_ids):
            visit(child_id, next_prefix, index == len(child_ids) - 1)

    for index, task_id in enumerate(roots):
        visit(task_id, "", index == len(roots) - 1)
    lines.extend(
        [
            "",
            (
                f"显示 {report['trace']['visible_node_count']}/{report['trace']['total_node_count']}；"
                f"省略 {report['trace']['hidden_node_count']}"
            ),
            (
                f"{_compact_source_legend(mission['cost'])}；"
                f"未精确记录 {_fmt_not_exactly_recorded(mission['elapsed_reconciliation'])}；"
                "— 未采集 · ? 未知 · ≈ 估算 · ≥ 部分采集"
            ),
        ]
    )
    runtime_text = _runtime_diagnostic_text(report)
    if runtime_text:
        lines.extend(["", f"运行时告警：{runtime_text}"])
    return "\n".join(lines) + "\n"


def render_svg(report: dict[str, Any]) -> str:
    """Render a portrait SVG: chronological rows plus the real hierarchy overlay.

    Vertical spacing follows event order, not elapsed duration. Every row therefore
    remains readable even when the Mission contains long idle gaps. Exact relative
    offsets are printed beside the axis, and each card has a linearly scaled range bar
    against the same Mission duration.
    """

    if report["view"] == "compact":
        raise TplanError("compact view uses a Unicode text tree; SVG is only available for standard/audit")
    mission = report["mission"]
    timeline = report["timeline"]
    node_by_id = {node["id"]: node for node in report["nodes"]}
    rows = timeline["rows"]
    view = report["view"]
    hotspot_by_id = {
        item["task_id"]: item for item in report.get("duration_hotspots", {}).get("tasks", [])
    }
    time_coverage = timeline.get("offset_coverage") or report["trace"]["coverage"]
    standard_node_lines = (
        {
            row["node_id"]: _standard_node_content_lines(
                node_by_id[row["node_id"]],
                row,
                time_coverage=time_coverage,
            )
            for row in rows
        }
        if view == "standard"
        else {}
    )
    standard_header_lines = (
        _standard_mission_header_lines(report) if view == "standard" else []
    )
    width = 1180
    header_x = 32
    header_y = 24
    header_width = width - 64
    header_height = (
        288
        if view == "audit"
        else max(168, 120 + 24 * len(standard_header_lines))
    )
    axis_x = 112
    card_base_x = 270
    depth_indent = 42
    right_margin = 34
    legend_y = header_y + header_height + 30
    row_top = legend_y + 22
    card_height = (
        296
        if view == "audit"
        else max(
            154,
            54 + 25 * max(
                (len(lines) for lines in standard_node_lines.values()),
                default=4,
            ),
        )
    )
    row_gap_by_kind = {"task": 30, "subtask": 18, "step": 12}
    row_ys: list[float] = []
    row_cursor = float(row_top)
    for index, row in enumerate(rows):
        if index:
            row_kind = node_by_id[row["node_id"]]["kind"]
            row_cursor += row_gap_by_kind.get(row_kind, 16)
        row_ys.append(row_cursor)
        row_cursor += card_height
    footer_height = 70
    content_bottom = row_cursor if rows else row_top + card_height
    height = content_bottom + footer_height
    axis_start_y = row_ys[0] + card_height / 2 if rows else row_top + card_height / 2
    axis_end_y = row_ys[-1] + card_height / 2 if rows else axis_start_y
    mission_elapsed = timeline.get("window_elapsed_ms")
    time_label = (
        "实际相对时间"
        if time_coverage == "exact"
        else "已观测相对时间"
        if time_coverage == "partial"
        else "无执行时间刻度"
    )
    mission_status = STATUS_LABELS.get(mission["status"], mission["status"])
    mission_cost = mission["cost"]
    mission_reconciliation = mission["elapsed_reconciliation"]
    report_title = _execution_presentation_title(report)
    visible_node_label = "可见真实节点" if report["trace"]["projection"] else "真实节点"
    coverage_warning_count = len(report["trace"].get("coverage_diagnostics", []))
    runtime = report["runtime"]
    time_domain_description = (
        "左侧刻度显示 Mission 生命周期相对时间，时间条按同一 Mission 历时等比例显示"
        if time_coverage == "exact"
        else "左侧刻度只显示已观测窗口相对时间，时间条不代表完整 Mission 历时"
        if time_coverage == "partial"
        else "没有执行时间观测，卡片按声明拓扑顺序排列且不显示时间条"
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="tplan-title tplan-desc" '
            f'data-layout="vertical-execution-timeline" '
            f'data-view="{_html(view)}" '
            f'data-schema-version="{_html(report["schema_version"])}">'
        ),
        f'<title id="tplan-title">{_html(mission["title"])} · {_html(report_title)}</title>',
        (
            '<desc id="tplan-desc">纵向排列真实任务节点；'
            f'{time_domain_description}；弱配色折线保留真实父子关系；'
            '缩进、6/4/2px 主干与分支结构线、短层级标记、类型牌及标题字重共同区分 Task、SubTask 与 Step；'
            'Task 主干与分支全线不透明以保持同色；父子线共享接头由父级等效色不透明覆盖，'
            '避免子级颜色透出混色；'
            '状态颜色集中在状态标签，异常节点才使用状态底色；中性耗时排名标签不表示失败。</desc>'
        ),
        "<style>",
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif}",
        ".report-title{font-size:22px;font-weight:700;fill:#ffffff}",
        ".mission-title{font-size:18px;font-weight:650;fill:#dbeafe}",
        ".mission-meta{font-size:14px;fill:#dbeafe}",
        ".legend{font-size:13px;fill:#475569}",
        ".time-label{font-size:12px;font-variant-numeric:tabular-nums;fill:#475569}",
        ".node-title-task{font-size:16px;font-weight:700;fill:#0f172a}",
        ".node-title-subtask{font-size:15px;font-weight:650;fill:#0f172a}",
        ".node-title-step{font-size:14px;font-weight:600;fill:#0f172a}",
        ".kind-label{font-size:11px;font-weight:750;letter-spacing:.35px}",
        ".node-meta{font-size:12.5px;fill:#475569}",
        ".node-metric{font-size:13px;fill:#1e293b}",
        ".node-result{font-size:12.5px;fill:#334155}",
        ".status-label{font-size:12px;font-weight:650}",
        ".duration-hotspot-label{font-size:12px;font-weight:650;fill:#475569}",
        ".tree-edge{fill:none;stroke-linecap:round;stroke-linejoin:round}",
        ".time-guide{stroke:#cbd5e1;stroke-width:1;stroke-dasharray:3 5}",
        ".axis{stroke:#64748b;stroke-width:2}",
        ".range-track{fill:#e8edf3}",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
        (
            f'<rect x="{header_x}" y="{header_y}" width="{header_width}" height="{header_height}" '
            'rx="16" fill="#172554" stroke="#3b82f6" stroke-width="1.5"/>'
        ),
        _svg_text(58, 58, report_title, "report-title"),
        _svg_text(58, 88, _shorten(mission["title"], 72), "mission-title"),
        *(
            [
                _svg_text(
                    58,
                    116 + index * 24,
                    _shorten(part, 135),
                    "mission-meta",
                )
                for index, part in enumerate(standard_header_lines)
            ]
            if view == "standard"
            else [
                _svg_text(
                    58,
                    116,
                    (
                        f"Mission · {mission_status} · "
                        f"{_elapsed_scope_label(mission['elapsed_coverage'], mission=True)} "
                        f"{_fmt_covered_duration(mission['elapsed_ms'], mission['observed_elapsed_ms'], mission['elapsed_coverage'])}"
                    ),
                    "mission-meta",
                ),
                _svg_text(
                    58,
                    140,
                    (
                        f"LLM调用累计 {_fmt_kind_duration(mission_cost, LLM_KINDS, host_label='调用端实测')}"
                        f" · 脚本累计 {_fmt_kind_duration(mission_cost, SCRIPT_KINDS)}"
                    ),
                    "mission-meta",
                ),
                _svg_text(
                    58,
                    164,
                    (
                        f"工具累计 {_fmt_kind_duration(mission_cost, TOOL_KINDS)}"
                        f" · 等待累计 {_fmt_kind_duration(mission_cost, WAIT_KINDS)}"
                        f" · 未被精确记录 {_fmt_not_exactly_recorded(mission_reconciliation)}"
                    ),
                    "mission-meta",
                ),
                _svg_text(
                    58,
                    188,
                    (
                        f"Token {_fmt_tokens_compact(mission_cost)}"
                        f" · {visible_node_label} {report['trace']['visible_node_count']}/{report['trace']['total_node_count']}"
                        f" · 产出归因 P{len(mission['outcome_attribution']['countable_progress'])}"
                        f"/C{len(mission['outcome_attribution']['constraint_deltas'])}"
                        f" · 覆盖 {report['trace']['coverage']}"
                        + (
                            f" · 生命周期告警 {coverage_warning_count}"
                            if coverage_warning_count
                            else ""
                        )
                        + f" · 运行时 {runtime['status']}"
                        + f" · {view}"
                    ),
                    "mission-meta",
                ),
                *[
                    _svg_text(
                        58,
                        212 + index * 24,
                        ("Mission 审计：" if index == 0 else "")
                        + _shorten(part, 135),
                        "mission-meta",
                    )
                    for index, part in enumerate(
                        attribution_audit_lines(mission["outcome_attribution"])
                    )
                ],
            ]
        ),
        _svg_text(
            32,
            legend_y,
            (
                f"纵向=首次执行；左侧是{time_label}；蓝灰条=起止/持续；"
                "层级线=Task 主干 6 / SubTask 分支 4 / Step 末梢 2px；中性标签=Task 耗时排名。"
            ),
            "legend",
        ),
    ]

    if rows:
        lines.append(
            f'<line x1="{axis_x}" y1="{axis_start_y}" x2="{axis_x}" y2="{axis_end_y}" class="axis"/>'
        )

    positions: dict[str, dict[str, float]] = {}
    for index, row in enumerate(rows):
        node = node_by_id[row["node_id"]]
        card_x = card_base_x + row["depth"] * depth_indent
        card_y = row_ys[index]
        card_width = width - right_margin - card_x
        center_y = card_y + card_height / 2
        positions[node["id"]] = {
            "x": card_x,
            "y": card_y,
            "width": card_width,
            "height": card_height,
            "center_y": center_y,
            "kind": node["kind"],
        }
        lines.extend(
            [
                f'<line x1="{axis_x + 8}" y1="{center_y}" x2="{card_x - 10}" y2="{center_y}" class="time-guide"/>',
                f'<circle cx="{axis_x}" cy="{center_y}" r="5" fill="#ffffff" stroke="#475569" stroke-width="2"/>',
                _svg_text(
                    axis_x - 12,
                    center_y + 4,
                    _fmt_timeline_offset(row["start_offset_ms"], time_coverage),
                    "time-label",
                    anchor="end",
                ),
            ]
        )

    # SVG uses painter's order. Paint thinner child branches first so the thicker
    # parent edge owns their shared junction instead of being visibly cut by it.
    edge_paint_order = {"step": 0, "subtask": 1, "task": 2}
    edge_styles = {
        "task": {
            "width": 6.0,
            "color": "#64748b",
            "opacity": 1.0,
            "opaque_equivalent": "#64748b",
        },
        "subtask": {
            "width": 4.0,
            "color": "#8b5cf6",
            "opacity": 0.72,
            "opaque_equivalent": "#aa88f8",
        },
        "step": {
            "width": 2.0,
            "color": "#60a5fa",
            "opacity": 0.84,
            "opaque_equivalent": "#78b3fa",
        },
    }
    painted_edges = sorted(
        report["tree_edges"],
        key=lambda edge: edge_paint_order.get(
            positions.get(edge["to"], {}).get("kind", ""), -1
        ),
    )
    junction_caps: dict[tuple[str, float, float, float], dict[str, Any]] = {}
    for edge in painted_edges:
        child_position = positions.get(edge["to"])
        if child_position is None:
            continue
        child_x = child_position["x"]
        child_y = child_position["center_y"]
        edge_style = edge_styles.get(
            child_position["kind"],
            {
                "width": 2.0,
                "color": "#94a3b8",
                "opacity": 0.72,
                "opaque_equivalent": "#a7b0bd",
            },
        )
        if edge["from"] == "mission":
            branch_x = card_base_x - 28
            path = f"M {branch_x} {header_y + header_height} V {child_y} H {child_x}"
        else:
            parent_position = positions.get(edge["from"])
            if parent_position is None:
                continue
            parent_x = parent_position["x"]
            parent_y = parent_position["center_y"]
            branch_x = min(parent_x, child_x) - 18
            path = f"M {parent_x} {parent_y} H {branch_x} V {child_y} H {child_x}"
            parent_kind = parent_position["kind"]
            parent_style = edge_styles.get(parent_kind)
            if parent_style is not None:
                junction_caps[(edge["from"], parent_x, parent_y, branch_x)] = {
                    "parent_id": edge["from"],
                    "kind": parent_kind,
                    "x1": branch_x,
                    "x2": parent_x,
                    "y": parent_y,
                    "style": parent_style,
                }
        lines.append(
            (
                f'<path d="{path}" class="tree-edge" stroke="{edge_style["color"]}" '
                f'stroke-width="{edge_style["width"]}" opacity="{edge_style["opacity"]}" '
                f'data-tree-from="{_html(edge["from"])}" data-tree-to="{_html(edge["to"])}" '
                f'data-child-kind="{_html(child_position["kind"])}"/>'
            )
        )

    for cap in sorted(
        junction_caps.values(),
        key=lambda item: edge_paint_order.get(item["kind"], -1),
    ):
        cap_style = cap["style"]
        lines.append(
            (
                f'<line x1="{cap["x1"]}" y1="{cap["y"]}" x2="{cap["x2"]}" y2="{cap["y"]}" '
                f'class="tree-edge junction-cap" stroke="{cap_style["opaque_equivalent"]}" '
                f'stroke-width="{cap_style["width"]}" opacity="1" '
                f'data-junction-parent="{_html(cap["parent_id"])}" '
                f'data-parent-kind="{_html(cap["kind"])}"/>'
            )
        )

    for row in rows:
        node = node_by_id[row["node_id"]]
        hotspot = hotspot_by_id.get(node["id"])
        position = positions[node["id"]]
        card_x = position["x"]
        card_y = position["y"]
        card_width = position["width"]
        status_fill, status_stroke, text_color = _svg_status_palette(node["status"])
        if node["status"] == "completed":
            card_fill = "#ffffff"
            card_stroke = "#d8e0ea"
            card_stroke_width = 1.2
        else:
            card_fill = status_fill
            card_stroke = status_stroke
            card_stroke_width = 1.5
        cost, reconciliation, scope_label = _node_cost_view(node)
        kind_label = {"task": "Task", "subtask": "SubTask", "step": "Step"}.get(
            node["kind"], str(node["kind"] or "Node")
        )
        kind_style = {
            "task": {
                "label": "TASK",
                "fill": "#475569",
                "stroke": "#475569",
                "text": "#ffffff",
            },
            "subtask": {
                "label": "SUBTASK",
                "fill": "#f3e8ff",
                "stroke": "#8b5cf6",
                "text": "#6d28d9",
            },
            "step": {
                "label": "STEP",
                "fill": "#eff6ff",
                "stroke": "#3b82f6",
                "text": "#1d4ed8",
            },
        }.get(
            node["kind"],
            {
                "label": kind_label.upper(),
                "fill": "#f8fafc",
                "stroke": "#94a3b8",
                "text": "#475569",
            },
        )
        hierarchy_accent = {
            "task": {"color": "#64748b", "width": 6},
            "subtask": {"color": "#8b5cf6", "width": 4},
            "step": {"color": "#60a5fa", "width": 2},
        }.get(node["kind"], {"color": "#94a3b8", "width": 2})
        title_class = {
            "task": "node-title-task",
            "subtask": "node-title-subtask",
            "step": "node-title-step",
        }.get(node["kind"], "node-title-subtask")
        status = STATUS_LABELS.get(node["status"], node["status"])
        icon = STATUS_ICONS.get(node["status"], "•")
        title_limit = 32 if view != "audit" else 46
        title = f"{_shorten(node['title'], title_limit)} · {node['id']}"
        elapsed = _fmt_covered_duration(
            node["elapsed_ms"], node["observed_elapsed_ms"], node["elapsed_coverage"]
        )
        range_text = (
            f"{_fmt_timeline_offset(row['start_offset_ms'], time_coverage)} → "
            f"{_fmt_timeline_offset(row['finish_offset_ms'], time_coverage)}"
        )
        hotspot_rank_attr = f' data-duration-hotspot-rank="{hotspot["rank"]}"' if hotspot else ""
        lines.extend(
            [
                (
                    f'<g id="node-{_html(node["id"])}" class="task-card" '
                    f'data-task-id="{_html(node["id"])}" data-depth="{row["depth"]}" '
                    f'data-start-offset-ms="{row["start_offset_ms"] if row["start_offset_ms"] is not None else ""}" '
                    f'data-finish-offset-ms="{row["finish_offset_ms"] if row["finish_offset_ms"] is not None else ""}"'
                    f'{hotspot_rank_attr}>'
                ),
                (
                    f'<rect x="{card_x}" y="{card_y}" width="{card_width}" height="{card_height}" '
                    f'rx="10" fill="{card_fill}" stroke="{card_stroke}" stroke-width="{card_stroke_width}"/>'
                ),
                (
                    f'<rect x="{card_x + 3}" y="{card_y + 13}" width="{hierarchy_accent["width"]}" '
                    f'height="28" rx="{hierarchy_accent["width"] / 2}" fill="{hierarchy_accent["color"]}" '
                    f'class="hierarchy-accent" data-node-kind="{_html(node["kind"])}"/>'
                ),
                (
                    f'<rect x="{card_x + 18}" y="{card_y + 13}" width="72" height="24" rx="6" '
                    f'fill="{kind_style["fill"]}" stroke="{kind_style["stroke"]}" stroke-width="1.25"/>'
                ),
                (
                    f'<text x="{card_x + 54}" y="{card_y + 30}" class="kind-label" text-anchor="middle" '
                    f'fill="{kind_style["text"]}">{_html(kind_style["label"])}</text>'
                ),
                _svg_text(card_x + 104, card_y + 29, title, title_class),
                (
                    f'<rect x="{card_x + card_width - 94}" y="{card_y + 13}" width="76" height="24" '
                    f'rx="12" fill="{status_stroke}" opacity=".13"/>'
                ),
                (
                    f'<text x="{card_x + card_width - 56}" y="{card_y + 30}" class="status-label" '
                    f'text-anchor="middle" fill="{text_color}">{_html(icon + " " + status)}</text>'
                ),
            ]
        )
        if hotspot:
            hotspot_badge_x = card_x + card_width - 224
            lines.extend(
                [
                    (
                        f'<rect x="{hotspot_badge_x}" y="{card_y + 13}" width="118" height="24" '
                        'rx="12" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.25"/>'
                    ),
                    (
                        f'<text x="{hotspot_badge_x + 59}" y="{card_y + 30}" '
                        'class="duration-hotspot-label" text-anchor="middle">'
                        f'耗时排名 #{hotspot["rank"]}</text>'
                    ),
                ]
            )
        if view == "standard":
            lines.extend(
                _svg_text(
                    card_x + 18,
                    card_y + 54 + index * 25,
                    text,
                    class_name,
                )
                for index, (text, class_name) in enumerate(
                    standard_node_lines[node["id"]]
                )
            )
            range_y = card_y + card_height - 14
        else:
            time_metric = _svg_text(
                card_x + 18,
                card_y + 79,
                (
                    f"时间 {range_text} · "
                    f"{_elapsed_scope_label(node['elapsed_coverage'])} {elapsed}"
                    f" · 未被精确记录 {_fmt_not_exactly_recorded(reconciliation)}"
                ),
                "node-metric",
            )
            lines.extend(
                [
                    _svg_text(
                        card_x + 18,
                        card_y + 54,
                        _svg_node_status_details(node, scope_label),
                        "node-meta",
                    ),
                    time_metric,
                    _svg_text(
                        card_x + 18,
                        card_y + 104,
                        (
                            f"LLM调用累计 {_fmt_kind_duration(cost, LLM_KINDS, host_label='调用端实测')}"
                            f" · 脚本累计 {_fmt_kind_duration(cost, SCRIPT_KINDS)}"
                        ),
                        "node-metric",
                    ),
                    _svg_text(
                        card_x + 18,
                        card_y + 129,
                        (
                            f"工具累计 {_fmt_kind_duration(cost, TOOL_KINDS)}"
                            f" · 等待累计 {_fmt_kind_duration(cost, WAIT_KINDS)}"
                            f" · Token {_fmt_tokens_compact(cost)}"
                        ),
                        "node-metric",
                    ),
                    _svg_text(
                        card_x + 18,
                        card_y + 151,
                        f"结果：{_shorten(node['outcome_summary'], 82) if node['outcome_summary'] else '未记录'}",
                        "node-result",
                    ),
                    _svg_text(
                        card_x + 18,
                        card_y + 174,
                        f"产出归因：{_shorten(attribution_text(node['outcome_attribution']), 74)}",
                        "node-result",
                    ),
                ]
            )
            lines.extend(
                _svg_text(
                    card_x + 18,
                    card_y + 197 + index * 23,
                    ("审计：" if index == 0 else "") + _shorten(part, 105),
                    "node-meta",
                )
                for index, part in enumerate(
                    attribution_audit_lines(node["outcome_attribution"])
                )
            )
            range_y = card_y + 282

        track_x = card_x + 18
        track_width = card_width - 36
        lines.append(
            f'<rect x="{track_x}" y="{range_y}" width="{track_width}" height="6" rx="3" class="range-track"/>'
        )
        start_offset = row["start_offset_ms"]
        finish_offset = row["finish_offset_ms"]
        if mission_elapsed and start_offset is not None and finish_offset is not None:
            start_fraction = min(1.0, max(0.0, start_offset / mission_elapsed))
            finish_fraction = min(1.0, max(start_fraction, finish_offset / mission_elapsed))
            range_x = min(track_x + track_width - 4.0, track_x + start_fraction * track_width)
            range_width = max(4.0, (finish_fraction - start_fraction) * track_width)
            range_width = min(range_width, track_x + track_width - range_x)
            range_y_rendered = range_y
            range_height = 6
            range_fill = "#64748b"
            range_class = "node-range"
            lines.append(
                (
                    f'<rect x="{range_x:.2f}" y="{range_y_rendered}" width="{range_width:.2f}" '
                    f'height="{range_height}" rx="4" fill="{range_fill}" class="{range_class}" '
                    f'data-task-id="{_html(node["id"])}"/>'
                )
            )
        lines.append("</g>")

    footer_y = content_bottom + 40
    if time_coverage == "exact":
        footer_text = (
            f"Mission 结束 {_fmt_timeline_offset(mission_elapsed, time_coverage)}"
            " · 纵向行距不代表持续时间；"
            "精确时间由刻度、节点起止值及统一比例时间条表达。"
        )
    elif time_coverage == "partial":
        footer_text = (
            f"观测窗口结束 {_fmt_timeline_offset(mission_elapsed, time_coverage)}"
            " · 纵向行距不代表持续时间；"
            "刻度和时间条仅表达已观测事件的相对位置，不代表完整 Mission 历时。"
        )
    else:
        footer_text = (
            "没有执行时间观测；纵向行距不代表持续时间；"
            "卡片仅保留声明拓扑、状态和异常信号，未显示成本不按零处理。"
        )
    lines.extend(
        [
            f'<line x1="32" y1="{footer_y - 24}" x2="{width - 32}" y2="{footer_y - 24}" stroke="#e2e8f0"/>',
            _svg_text(
                32,
                footer_y,
                footer_text,
                "legend",
            ),
        ]
    )
    if report["trace"]["hidden_node_count"]:
        lines.append(
            _svg_text(
                32,
                footer_y + 24,
                f"投影视图省略 {report['trace']['hidden_node_count']} 个真实节点；Standard/Audit 可查看完整拓扑。",
                "legend",
            )
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _coverage_note(report: dict[str, Any]) -> str:
    coverage = report["trace"]["coverage"]
    if coverage == "exact":
        return (
            "生命周期追踪可从 Mission 初始化完整回放到当前快照；"
            "各类成本仍只包含宿主实际上报的 span。"
        )
    if coverage == "partial":
        return (
            "生命周期追踪不完整或与当前快照不一致；这里只显示已观测窗口，"
            "不把最后一条事件当作 Mission 完成时间。"
        )
    return "没有执行轨迹；当前仅展示 Mission 快照，时间与 Token 成本保持未知。"


def _coverage_diagnostic_text(report: dict[str, Any]) -> str | None:
    diagnostics = report["trace"].get("coverage_diagnostics", [])
    if not diagnostics:
        return None
    return "；".join(
        f"{item['code']}: {item['message']}" for item in diagnostics
    )


def _runtime_diagnostic_text(report: dict[str, Any]) -> str | None:
    diagnostics = report["runtime"].get("diagnostics", [])
    if not diagnostics:
        return None
    return "；".join(
        f"{item['code']}: {item['message']}" for item in diagnostics
    )


def _append_telemetry_capture_markdown(
    lines: list[str], report: dict[str, Any]
) -> None:
    capture = report["telemetry_capture"]
    activation = capture["activation"]
    labels = {
        "local_tools": "本地工具/脚本",
        "hosted_tools": "托管工具",
        "model_turns": "模型/Turn",
        "tokens": "Token",
        "waits": "等待",
        "subagents": "SubAgent",
    }
    lines.extend(
        [
            "",
            "## Codex 遥测覆盖",
            "",
            (
                f"绑定：`{capture['binding']['status']}`；范围："
                f"`{capture['binding'].get('scope') or 'none'}`；generation："
                f"`{capture['binding'].get('generation') or 'none'}`。"
                "没有观测值的类别保持 `not_reported`，不会按零处理。"
            ),
            "",
            (
                f"激活：`{activation['status']}`；当前 surface："
                f"`{activation.get('active_surface') or 'none'}`；"
                f"原因：{activation['reason']}。"
            ),
            "",
            "| Surface | 激活状态 | Codex build/version | Hook source | 原因 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for surface_name, surface in activation["surfaces"].items():
        source = surface.get("source")
        source_text = "none"
        if isinstance(source, dict):
            source_text = (
                f"{source['scope']}:{source['path']}；"
                f"hash={source.get('sha256') or 'absent'}；"
                f"enumerated={str(source['enumerated']).lower()}；"
                f"trust={','.join(source['trust_statuses']) or 'none'}；"
                f"enabled={source.get('enabled')}"
            )
        build = surface.get("host_build") or surface.get("codex_version") or "none"
        lines.append(
            "| "
            + " | ".join(
                (
                    _markdown_cell(surface_name),
                    _markdown_cell(surface["status"]),
                    _markdown_cell(build),
                    _markdown_cell(source_text),
                    _markdown_cell(surface["reason"]),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| 通道 | 状态 | 已完成 span | 原因 |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for name, channel in capture["channels"].items():
        lines.append(
            "| "
            + " | ".join(
                (
                    labels[name],
                    _markdown_cell(channel["status"]),
                    str(channel["observed_span_count"]),
                    _markdown_cell(channel["reason"]),
                )
            )
            + " |"
        )


def render_markdown(report: dict[str, Any], *, timeline_svg_ref: str | None = None) -> str:
    if report["view"] == "compact":
        if timeline_svg_ref is not None:
            raise TplanError("compact Markdown is a Unicode text tree and has no SVG sidecar")
        lines = [
            "# TPlan 执行摘要",
            "",
            f"> {_coverage_note(report)}",
            "",
            "```text",
            render_compact_text(report).rstrip(),
            "```",
            "",
            "Task/SubTask 成本为其真实子树累计；Step 为直接成本。没有出现的下级节点只是被省略，没有被合并。",
            "",
            "LLM、脚本、工具和等待是累计资源时间，可能相互重叠；逐节点详情见 Standard/Audit。",
        ]
        diagnostic_text = _coverage_diagnostic_text(report)
        if diagnostic_text:
            lines[3:3] = [f"> 覆盖告警：{diagnostic_text}", ""]
        runtime_text = _runtime_diagnostic_text(report)
        if runtime_text:
            lines[3:3] = [f"> 运行时告警：{runtime_text}", ""]
        return "\n".join(lines).rstrip() + "\n"

    mission = report["mission"]
    cost = mission["cost"]
    overhead = report["overhead"]["cost"]
    presentation_title = _execution_presentation_title(report)
    markdown_title = {
        "exact": "# TPlan 实际执行与成本树",
        "partial": "# TPlan 已观测执行窗口与成本树",
        "snapshot_only": "# TPlan Mission 结构快照与成本边界",
    }[report["trace"]["coverage"]]
    lines = [
        markdown_title,
        "",
        f"> {_coverage_note(report)}",
        "",
    ]
    diagnostic_text = _coverage_diagnostic_text(report)
    if diagnostic_text:
        lines.extend([f"> 覆盖告警：{diagnostic_text}", ""])
    runtime_text = _runtime_diagnostic_text(report)
    if runtime_text:
        lines.extend([f"> 运行时告警：{runtime_text}", ""])
    if timeline_svg_ref:
        lines.extend(
            [
                f"![{presentation_title}](<{timeline_svg_ref}>)",
                "",
            ]
        )
    else:
        inline_svg = render_svg(report).split("\n", 1)[1].rstrip()
        lines.extend([inline_svg, ""])
    if report["view"] == "audit":
        _append_telemetry_capture_markdown(lines, report)
    lines.append("")
    visible_node_label = "可见真实节点" if report["trace"]["projection"] else "真实节点"
    lines.append(
        f"视图：`{report['view']}`；布局：`vertical_execution_timeline`；"
        f"{visible_node_label}：{report['trace']['visible_node_count']}/{report['trace']['total_node_count']}。"
    )
    if report["trace"]["hidden_node_count"]:
        lines.append(
            f"这是投影视图，省略了 {report['trace']['hidden_node_count']} 个真实节点；"
            "使用 `--view standard` 或 `--view audit` 查看完整拓扑。"
        )
    mission_attribution = mission["outcome_attribution"]
    node_yield_counts = mission_attribution.get("node_yield_counts", {})
    writeback_only_nodes = node_yield_counts.get("writeback_only", 0)
    telemetry_only_nodes = node_yield_counts.get("telemetry_only", 0)
    lines.append(
        "产出归因："
        f"{len(mission_attribution['countable_progress'])} 项可计推进 · "
        f"{len(mission_attribution['constraint_deltas'])} 项关键约束 · "
        f"{writeback_only_nodes} 个仅状态写回节点 · {telemetry_only_nodes} 个仅遥测节点。"
    )
    lines.extend(
        [
            "",
            "口径：覆盖 exact 时，实际历时按可回放生命周期的开始到结束计算；覆盖 partial 时，"
            "这里只显示已观测窗口，不把它当作 Mission 完成时间。LLM 调用、脚本、工具和等待显示的是"
            "各自累计资源时间，嵌套或并行时不可直接相加。调用端实测覆盖完整模型请求，可能包含"
            "排队、网络和流式传输，不等于平台内部纯推理时间。未被精确记录 = 实际历时减去已完成且"
            "时间来源精确的区间并集；它不自动属于 LLM、脚本或其他类别。已缓存输入包含在输入 Token 中，"
            "不会重复累计。",
        ]
    )
    if report["trace"]["open_span_count"]:
        lines.append(
            f"未结束调用：{report['trace']['open_span_count']} 个；已有入口记录但没有配对结束记录，"
            "因此不计入累计成本。"
        )
    if report["view"] == "audit" and cost["envelope_span_count"]:
        lines.append(
            f"Agent turn 包络：{cost['envelope_span_count']} 个 span，"
            f"{_fmt_kind_duration(cost, {'agent_turn'})}；仅用于审计，不计入 LLM 调用累计或可加资源时间。"
        )
    if report["view"] == "audit" and overhead["span_count"]:
        lines.append(
            f"Mission 级共享/未归属 span：{_fmt_duration(overhead['additive_resource_time_ms'])} 可加资源时间，"
            f"{_fmt_tokens(overhead)} Token；这些成本不分摊到任务节点。"
        )

    notable = [
        node
        for node in report["nodes"]
        if node["outcome_summary"]
        or node["status"] in ABNORMAL_TASK_STATUSES
        or node["attempts"] > 1
        or node["direct_cost"]["error_span_count"]
        or node["direct_open_span_count"]
    ]
    if notable and report["view"] == "audit":
        lines.extend(["", "## 结果与异常", ""])
        for node in notable:
            details: list[str] = []
            if node["outcome_summary"]:
                details.append(_shorten(node["outcome_summary"], 180))
            if node["attempts"] > 1:
                details.append(f"执行 {node['attempts']} 次")
            if node["direct_cost"]["error_span_count"]:
                details.append(f"{node['direct_cost']['error_span_count']} 个错误 span")
            if node["direct_open_span_count"]:
                details.append(f"{node['direct_open_span_count']} 个未结束调用")
            if not details:
                details.append(STATUS_LABELS.get(node["status"], node["status"]))
            lines.append(f"- {node['title']} (`{node['id']}`): {'; '.join(details)}")

    if report["view"] == "audit":
        mission_audit_relevant = any(
            mission_attribution[field]
            for field in (
                "countable_progress",
                "constraint_deltas",
                "state_writebacks",
                "unclassified_writebacks",
                "warnings",
            )
        )
        audit_nodes = [
            node
            for node in report["nodes"]
            if node["outcome_attribution"]["unclassified_writebacks"]
            or node["outcome_attribution"]["warnings"]
            or node["outcome_attribution"]["countable_progress"]
            or node["outcome_attribution"]["constraint_deltas"]
        ]
        if mission_audit_relevant or audit_nodes:
            lines.extend(["", "## 产出归因审计", ""])
            if mission_audit_relevant:
                lines.append(
                    f"- Mission (`{mission['id']}`): {attribution_text(mission_attribution)}；"
                    f"{attribution_audit_text(mission_attribution)}。"
                )
            for node in audit_nodes:
                attribution = node["outcome_attribution"]
                evidence_ids = sorted(
                    {
                        evidence_id
                        for bucket in (
                            "countable_progress",
                            "constraint_deltas",
                            "unclassified_writebacks",
                        )
                        for item in attribution[bucket]
                        for evidence_id in item.get("evidence_ids", [])
                    }
                )
                commit_ids = sorted(
                    {
                        commit_id
                        for bucket in (
                            "countable_progress",
                            "constraint_deltas",
                            "state_writebacks",
                            "unclassified_writebacks",
                        )
                        for item in attribution[bucket]
                        for commit_id in item.get("commit_ids", [])
                    }
                )
                reasons = [
                    item.get("reason")
                    for item in attribution["unclassified_writebacks"]
                    if isinstance(item.get("reason"), str)
                ]
                warning_codes = [item["code"] for item in attribution["warnings"]]
                lines.append(
                    f"- {node['title']} (`{node['id']}`): {attribution_text(attribution)}；"
                    f"evidence={evidence_ids or ['none']}；commit={commit_ids or ['none']}；"
                    f"unclassified={reasons or ['none']}；warnings={warning_codes or ['none']}。"
                )
        lines.extend(
            [
                "",
                "## 审计明细",
                "",
                (
                    "| 顺序 | 节点 | 状态 | 产出归因 | "
                    f"{_elapsed_scope_label(report['trace']['coverage'])} | 活跃时间 | 次数 | "
                    "直接资源 | 子树资源 | 子树未精确记录 | 证据 | 产物 |"
                ),
                "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for node in report["nodes"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(node["execution_order"] or "—"),
                        _markdown_cell(f"{node['title']} ({node['id']})"),
                        _markdown_cell(node["actual_state"]),
                        _markdown_cell(attribution_text(node["outcome_attribution"])),
                        _fmt_covered_duration(
                            node["elapsed_ms"], node["observed_elapsed_ms"], node["elapsed_coverage"]
                        ),
                        _fmt_covered_duration(
                            node["active_duration_ms"],
                            node["observed_active_duration_ms"],
                            node["active_duration_source"],
                        ),
                        str(node["attempts"]),
                        _fmt_resource_duration(node["direct_cost"]),
                        _fmt_resource_duration(node["inclusive_cost"]),
                        _fmt_not_exactly_recorded(node["subtree_elapsed_reconciliation"]),
                        str(len(node["evidence_refs"])),
                        str(len(node["artifact_refs"])),
                    ]
                )
                + " |"
            )
    return "\n".join(lines).rstrip() + "\n"


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
