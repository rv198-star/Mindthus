#!/usr/bin/env python3
"""Build and render a progressive TPlan actual-execution and cost tree."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from tplan_runtime import (
    TplanError,
    read_execution_trace,
    read_mission,
    task_map,
    validate_execution_trace,
    validate_mission,
)


REPORT_SCHEMA_VERSION = "tplan.execution_cost_tree.v0.5"
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
RECONCILABLE_KINDS = {"model", "script", "tool", "wait", "runtime"}
EXACT_MEASUREMENT_SOURCES = {"platform_reported", "host_measured"}
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


def _parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def _timestamp_ms(value: str) -> int:
    return round(_parse_timestamp(value).timestamp() * 1000)


def _iso_from_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _unique_strings(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, str) and value and value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _union_duration_ms(intervals: Iterable[tuple[int, int]]) -> int:
    ordered = sorted((start, finish) for start, finish in intervals if finish >= start)
    if not ordered:
        return 0
    total = 0
    current_start, current_finish = ordered[0]
    for start, finish in ordered[1:]:
        if start <= current_finish:
            current_finish = max(current_finish, finish)
            continue
        total += current_finish - current_start
        current_start, current_finish = start, finish
    return total + current_finish - current_start


def _record_interval(record: dict[str, Any]) -> tuple[int, int]:
    span = record["span"]
    return _timestamp_ms(span["started_at"]), _timestamp_ms(span["finished_at"])


def _is_reconcilable(record: dict[str, Any]) -> bool:
    span = record["span"]
    return (
        span["kind"] in RECONCILABLE_KINDS
        and span["measurement_source"] in EXACT_MEASUREMENT_SOURCES
    )


def _clip_interval(
    interval: tuple[int, int],
    started_at: str | None,
    finished_at: str | None,
) -> tuple[int, int] | None:
    start, finish = interval
    if started_at is not None:
        start = max(start, _timestamp_ms(started_at))
    if finished_at is not None:
        finish = min(finish, _timestamp_ms(finished_at))
    if finish < start:
        return None
    return start, finish


def _elapsed_reconciliation(
    records: Iterable[dict[str, Any]],
    *,
    elapsed_ms: int | None,
    observed_elapsed_ms: int | None,
    coverage: str,
    started_at: str | None,
    finished_at: str | None,
) -> dict[str, Any]:
    records = list(records)
    intervals = []
    for record in records:
        if not _is_reconcilable(record):
            continue
        clipped = _clip_interval(_record_interval(record), started_at, finished_at)
        if clipped is not None:
            intervals.append(clipped)
    exact_interval_coverage_ms = _union_duration_ms(intervals)
    if observed_elapsed_ms is not None:
        exact_interval_coverage_ms = min(exact_interval_coverage_ms, observed_elapsed_ms)
    exact_partition = coverage == "exact" and elapsed_ms is not None
    not_exactly_recorded_elapsed_ms = (
        max(0, elapsed_ms - exact_interval_coverage_ms) if exact_partition else None
    )
    exact_interval_coverage_ratio = None
    if exact_partition:
        exact_interval_coverage_ratio = 1.0 if elapsed_ms == 0 and exact_interval_coverage_ms == 0 else (
            exact_interval_coverage_ms / elapsed_ms if elapsed_ms else 0.0
        )
    return {
        "coverage": coverage,
        "elapsed_ms": elapsed_ms,
        "observed_elapsed_ms": observed_elapsed_ms,
        "exact_interval_coverage_ms": (
            exact_interval_coverage_ms if observed_elapsed_ms is not None else None
        ),
        "not_exactly_recorded_elapsed_ms": not_exactly_recorded_elapsed_ms,
        "exact_interval_coverage_ratio": exact_interval_coverage_ratio,
        "included_exact_interval_count": len(intervals),
        "excluded_envelope_span_count": sum(
            1 for record in records if record["span"]["kind"] == "agent_turn"
        ),
    }


def _span_cost(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
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
    token_records = [record for record in records if record["span"]["kind"] == "model"]
    if not token_records:
        token_records = [record for record in records if record["span"]["kind"] == "agent_turn"]
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
        "measurement_sources": dict(sorted(sources.items())),
        "span_statuses": dict(sorted(statuses.items())),
        "error_span_count": statuses["error"],
    }


def _record_time_ms(record: dict[str, Any]) -> int:
    if record.get("event_type") == "span_completed":
        return _timestamp_ms(record["span"]["finished_at"])
    return _timestamp_ms(record["timestamp"])


def _validate_trace(mission: dict[str, Any], trace: list[dict[str, Any]]) -> None:
    errors = validate_execution_trace(mission, trace)
    if errors:
        raise TplanError("; ".join(errors))


def _trace_coverage(trace: list[dict[str, Any]]) -> str:
    if not trace:
        return "snapshot_only"
    if trace[0].get("event_type") == "mission_initialized":
        return "exact"
    return "partial"


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
        duration_coverage = "exact" if coverage == "exact" or state["dynamic"] else coverage
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


def _mission_elapsed(
    mission: dict[str, Any], trace: list[dict[str, Any]], coverage: str, generated_at: str
) -> tuple[int | None, str | None, str | None]:
    if coverage == "snapshot_only":
        return None, None, None
    start_record = next((record for record in trace if record["event_type"] == "mission_initialized"), trace[0])
    started_at = start_record["timestamp"]
    mission_status = mission.get("mission", {}).get("status")
    finished_at = (
        max(trace, key=_record_time_ms)["timestamp"]
        if mission_status in TERMINAL_MISSION_STATUSES
        else generated_at
    )
    if mission_status in TERMINAL_MISSION_STATUSES:
        latest = max(trace, key=_record_time_ms)
        if latest["event_type"] == "span_completed":
            finished_at = latest["span"]["finished_at"]
    return max(0, _timestamp_ms(finished_at) - _timestamp_ms(started_at)), started_at, finished_at


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
            token_total = sum(direct_cost["usage"].values())
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

    mission_start = mission.get("started_at")
    mission_finish = mission.get("finished_at")
    mission_elapsed = mission.get("elapsed_ms")
    if mission_elapsed is None:
        mission_elapsed = mission.get("observed_elapsed_ms")
    origin_ms = _timestamp_ms(mission_start) if mission_start else None
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
        "row_positioning": "first_observed_chronological",
        "row_spacing": "ordinal_not_duration_proportional",
        "range_bar_scale": (
            "linear_mission_elapsed"
            if mission.get("elapsed_coverage") == "exact"
            else "linear_observed_window"
        ),
        "offset_coverage": mission.get("elapsed_coverage"),
        "offset_origin": (
            "mission_initialized"
            if mission.get("elapsed_coverage") == "exact"
            else "first_observed_trace"
        ),
        "started_at": mission_start,
        "finished_at": mission_finish,
        "elapsed_ms": mission_elapsed,
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

    mission = read_mission(mission_dir)
    mission_errors = validate_mission(mission)
    if mission_errors:
        raise TplanError("; ".join(mission_errors))
    trace = read_execution_trace(mission_dir)
    _validate_trace(mission, trace)
    coverage = _trace_coverage(trace)
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

    observed_elapsed_ms, started_at, finished_at = _mission_elapsed(
        mission, trace, coverage, generated_at
    )
    mission_elapsed_ms = observed_elapsed_ms if coverage == "exact" else None
    mission_cost = _span_cost(all_spans)
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
        direct_cost = _span_cost(direct_records)
        inclusive_cost = _span_cost(inclusive_records)
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
    overhead_by_attribution = {
        attribution: _span_cost(records) for attribution, records in sorted(overhead_spans.items())
    }
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "view": view,
        "presentation": "unicode_text_tree" if view == "compact" else "vertical_timeline_svg",
        "focus_task_id": focus_task_id,
        "top_cost": top_cost,
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
            "cost": mission_cost,
            "elapsed_reconciliation": mission_elapsed_reconciliation,
        },
        "trace": {
            "coverage": coverage,
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
            "cost": _span_cost([record for records in overhead_spans.values() for record in records]),
            "by_attribution": overhead_by_attribution,
        },
        "metric_semantics": {
            "actual_elapsed_ms": "natural elapsed time between observed lifecycle boundaries",
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
    if coverage == "partial" and observed_value:
        return f"≥{_fmt_duration(observed_value)}"
    return "未知"


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
    return " · ".join(parts)


def render_compact_text(report: dict[str, Any]) -> str:
    if report["view"] != "compact":
        raise TplanError("text tree is only available for compact view")
    mission = report["mission"]
    mission_elapsed = _fmt_covered_duration(
        mission["elapsed_ms"], mission["observed_elapsed_ms"], mission["elapsed_coverage"]
    )
    mission_token = _fmt_tokens_inline(mission["cost"])
    mission_line = (
        f"Mission · {_shorten(mission['title'], 60)} "
        f"{_compact_status(mission['status'])} {mission_elapsed}"
        f" · {_compact_cost_summary(mission['cost'])}"
    )
    if mission_token != "—":
        mission_line += f" · Tok {mission_token}"
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
    width = 1180
    header_x = 32
    header_y = 24
    header_width = width - 64
    header_height = 192
    axis_x = 112
    card_base_x = 270
    depth_indent = 42
    right_margin = 34
    row_top = 268
    card_height = {"compact": 164, "standard": 178, "audit": 204}[view]
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
    mission_elapsed = timeline.get("elapsed_ms")
    time_coverage = timeline.get("offset_coverage") or report["trace"]["coverage"]
    time_label = "实际相对时间" if time_coverage == "exact" else "已观测相对时间"
    mission_status = STATUS_LABELS.get(mission["status"], mission["status"])
    mission_cost = mission["cost"]
    mission_reconciliation = mission["elapsed_reconciliation"]
    report_title = "TPlan 执行时间轴摘要" if view == "compact" else "TPlan 纵向实际执行时间轴"
    visible_node_label = "可见真实节点" if report["trace"]["projection"] else "真实节点"

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
            '<desc id="tplan-desc">纵向按首次观测时间排列真实任务节点；左侧刻度显示相对追踪起点的'
            '时间，卡片底部中性时间条按统一观测窗口等比例显示节点起止范围，弱配色折线保留真实父子关系；'
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
        _svg_text(
            58,
            116,
            (
                f"Mission · {mission_status} · 实际历时 "
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
                f" · 覆盖 {report['trace']['coverage']} · {view}"
            ),
            "mission-meta",
        ),
        _svg_text(
            32,
            246,
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
        if view == "compact":
            lines.extend(
                [
                    _svg_text(
                        card_x + 18,
                        card_y + 54,
                        f"{_svg_node_status_details(node, scope_label)} · {range_text} · 实际历时 {elapsed}",
                        "node-meta",
                    ),
                    _svg_text(
                        card_x + 18,
                        card_y + 80,
                        (
                            f"LLM调用累计 {_fmt_kind_duration(cost, LLM_KINDS, host_label='调用端实测')}"
                            f" · 脚本累计 {_fmt_kind_duration(cost, SCRIPT_KINDS)}"
                        ),
                        "node-metric",
                    ),
                    _svg_text(
                        card_x + 18,
                        card_y + 105,
                        (
                            f"工具累计 {_fmt_kind_duration(cost, TOOL_KINDS)}"
                            f" · 等待累计 {_fmt_kind_duration(cost, WAIT_KINDS)}"
                            f" · Token {_fmt_tokens_compact(cost)}"
                        ),
                        "node-metric",
                    ),
                    _svg_text(
                        card_x + 18,
                        card_y + 128,
                        f"结果：{_shorten(node['outcome_summary'], 82) if node['outcome_summary'] else '未记录'}",
                        "node-result",
                    ),
                ]
            )
            range_y = card_y + 150
        else:
            time_metric = _svg_text(
                card_x + 18,
                card_y + 79,
                (
                    f"时间 {range_text} · 实际历时 {elapsed}"
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
                ]
            )
            if view == "audit":
                lines.append(
                    _svg_text(
                        card_x + 18,
                        card_y + 174,
                        (
                            f"审计：直接 span {node['direct_cost']['span_count']} · 子树 span {node['inclusive_cost']['span_count']}"
                            f" · 证据 {len(node['evidence_refs'])} · 产物 {len(node['artifact_refs'])}"
                        ),
                        "node-meta",
                    )
                )
                range_y = card_y + 190
            else:
                range_y = card_y + 164

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
    lines.extend(
        [
            f'<line x1="32" y1="{footer_y - 24}" x2="{width - 32}" y2="{footer_y - 24}" stroke="#e2e8f0"/>',
            _svg_text(
                32,
                footer_y,
                (
                    f"{'Mission 结束' if time_coverage == 'exact' else '观测窗口结束'} "
                    f"{_fmt_timeline_offset(mission_elapsed, time_coverage)} · 纵向行距不代表持续时间；"
                    "精确时间由刻度、节点起止值及统一比例时间条表达。"
                ),
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


def _coverage_note(coverage: str) -> str:
    if coverage == "exact":
        return "生命周期追踪从 Mission 初始化开始；各类成本仍只包含宿主实际上报的 span。"
    if coverage == "partial":
        return "追踪晚于 Mission 创建，因此更早的执行路线与成本保持未知，不做猜测。"
    return "没有执行轨迹；当前仅展示 Mission 快照，时间与 Token 成本保持未知。"


def render_markdown(report: dict[str, Any], *, timeline_svg_ref: str | None = None) -> str:
    if report["view"] == "compact":
        if timeline_svg_ref is not None:
            raise TplanError("compact Markdown is a Unicode text tree and has no SVG sidecar")
        lines = [
            "# TPlan 执行摘要",
            "",
            f"> {_coverage_note(report['trace']['coverage'])}",
            "",
            "```text",
            render_compact_text(report).rstrip(),
            "```",
            "",
            "Task/SubTask 成本为其真实子树累计；Step 为直接成本。没有出现的下级节点只是被省略，没有被合并。",
            "",
            "LLM、脚本、工具和等待是累计资源时间，可能相互重叠；逐节点详情见 Standard/Audit。",
        ]
        return "\n".join(lines).rstrip() + "\n"

    mission = report["mission"]
    cost = mission["cost"]
    overhead = report["overhead"]["cost"]
    lines = [
        "# TPlan 实际执行与成本树",
        "",
        f"> {_coverage_note(report['trace']['coverage'])}",
        "",
    ]
    if timeline_svg_ref:
        lines.extend(
            [
                f"![TPlan 纵向实际执行时间轴](<{timeline_svg_ref}>)",
                "",
            ]
        )
    else:
        inline_svg = render_svg(report).split("\n", 1)[1].rstrip()
        lines.extend([inline_svg, ""])
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
    lines.extend(
        [
            "",
            "口径：实际历时按开始到结束的自然经过时间计算；LLM 调用、脚本、工具和等待显示的是"
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
        lines.extend(
            [
                "",
                "## 审计明细",
                "",
                "| 顺序 | 节点 | 状态 | 实际历时 | 活跃时间 | 次数 | 直接资源 | 子树资源 | 子树未精确记录 | 证据 | 产物 |",
                "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
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
