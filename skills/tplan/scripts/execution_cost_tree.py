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


REPORT_SCHEMA_VERSION = "tplan.execution_cost_tree.v0.3"
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
) -> tuple[list[str], int]:
    by_id = {node["id"]: node for node in nodes}
    if focus_task_id is not None and focus_task_id not in by_id:
        raise TplanError(f"focus task {focus_task_id} does not exist")
    scope = (
        {focus_task_id, *_descendant_ids(focus_task_id, children)}
        if focus_task_id is not None
        else set(by_id)
    )
    roots = [focus_task_id] if focus_task_id else list(children.get(None, []))

    if view in {"standard", "audit"}:
        selected = set(scope)
    elif view == "compact":
        selected = set(roots)
        if focus_task_id is not None:
            selected.update(children.get(focus_task_id, []))

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
    return ordered, len(scope - selected)


def build_execution_cost_tree(
    mission_dir: Path,
    *,
    view: str = "standard",
    focus_task_id: str | None = None,
    top_cost: int = 5,
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

    visible_ids, hidden_count = _select_nodes(
        nodes,
        children,
        view=view,
        focus_task_id=focus_task_id,
        top_cost=top_cost,
    )
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
    report["tree_edges"] = _visible_edges(visible_nodes, visible_set, focus_task_id)
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


def _node_label(node: dict[str, Any], view: str) -> str:
    kind_label = {"task": "Task", "subtask": "SubTask", "step": "Step"}.get(
        node["kind"], str(node["kind"] or "Node")
    )
    dynamic = " · 动态新增" if node["dynamic"] else ""
    title = _shorten(node["title"], 48 if view != "audit" else 72)
    status = STATUS_LABELS.get(node["status"], node["status"])
    icon = STATUS_ICONS.get(node["status"], "•")
    elapsed = _fmt_covered_duration(
        node["elapsed_ms"], node["observed_elapsed_ms"], node["elapsed_coverage"]
    )
    order = f"#{node['execution_order']}" if node["execution_order"] is not None else "未运行"
    lines = [
        f"[{kind_label}] {title} · {node['id']}{dynamic}",
        f"{icon} {status} · {order}",
    ]
    if view == "compact":
        lines[1] += f" · 实际历时 {elapsed}"
        return "<br/>".join(_html(line) for line in lines)

    cost, elapsed_reconciliation, scope_label = _node_cost_view(node)
    status_details = [scope_label]
    if node["attempts"] > 1:
        status_details.append(f"执行次数 {node['attempts']}")
    if node["direct_cost"]["error_span_count"]:
        status_details.append(f"错误 {node['direct_cost']['error_span_count']}")
    open_span_count = (
        node["direct_open_span_count"]
        if node["kind"] == "step"
        else node["inclusive_open_span_count"]
    )
    if open_span_count:
        status_details.append(f"未结束调用 {open_span_count}")
    lines[1] += " · " + " · ".join(status_details)
    lines.extend(
        [
            f"实际历时 {elapsed} · 未被精确记录 {_fmt_not_exactly_recorded(elapsed_reconciliation)}",
            f"LLM调用累计 {_fmt_kind_duration(cost, LLM_KINDS, host_label='调用端实测')} · 脚本累计 {_fmt_kind_duration(cost, SCRIPT_KINDS)}",
            f"工具累计 {_fmt_kind_duration(cost, TOOL_KINDS)} · 等待累计 {_fmt_kind_duration(cost, WAIT_KINDS)} · Token {_fmt_tokens_compact(cost)}",
        ]
    )
    if node["outcome_summary"]:
        lines.append(f"结果：{_shorten(node['outcome_summary'], 64)}")
    return "<br/>".join(_html(line) for line in lines)


def render_mermaid(report: dict[str, Any]) -> str:
    mission = report["mission"]
    cost = mission["cost"]
    elapsed_reconciliation = mission["elapsed_reconciliation"]
    mission_status = STATUS_LABELS.get(mission["status"], mission["status"])
    mission_lines = [
        f"{_shorten(mission['title'], 68)}",
        f"Mission · {mission_status} · 实际历时 {_fmt_covered_duration(mission['elapsed_ms'], mission['observed_elapsed_ms'], mission['elapsed_coverage'])}",
        f"LLM调用累计 {_fmt_kind_duration(cost, LLM_KINDS, host_label='调用端实测')} · 脚本累计 {_fmt_kind_duration(cost, SCRIPT_KINDS)}",
        f"工具累计 {_fmt_kind_duration(cost, TOOL_KINDS)} · 等待累计 {_fmt_kind_duration(cost, WAIT_KINDS)}",
        f"未被精确记录 {_fmt_not_exactly_recorded(elapsed_reconciliation)} · Token {_fmt_tokens_compact(cost)}",
        f"覆盖 {report['trace']['coverage']} · {report['view']}",
    ]

    node_keys = {node["id"]: f"N{index}" for index, node in enumerate(report["nodes"], start=1)}
    lines = ["flowchart TB", f'  M["{"<br/>".join(_html(item) for item in mission_lines)}"]']
    for node in report["nodes"]:
        lines.append(f'  {node_keys[node["id"]]}["{_node_label(node, report["view"])}"]')
    for edge in report["tree_edges"]:
        source = "M" if edge["from"] == "mission" else node_keys[edge["from"]]
        lines.append(f"  {source} --> {node_keys[edge['to']]}")
    lines.extend(
        [
            "  classDef mission fill:#172554,color:#ffffff,stroke:#1d4ed8,stroke-width:2px;",
            "  classDef active fill:#dbeafe,color:#172554,stroke:#2563eb,stroke-width:2px;",
            "  classDef completed fill:#dcfce7,color:#14532d,stroke:#16a34a;",
            "  classDef blocked fill:#fee2e2,color:#7f1d1d,stroke:#dc2626,stroke-width:2px;",
            "  classDef paused fill:#fef3c7,color:#78350f,stroke:#d97706;",
            "  classDef pending fill:#f8fafc,color:#475569,stroke:#94a3b8,stroke-dasharray:4 3;",
            "  classDef closed fill:#f1f5f9,color:#334155,stroke:#64748b;",
            "  class M mission;",
        ]
    )
    classes: dict[str, list[str]] = defaultdict(list)
    for node in report["nodes"]:
        status = node["status"]
        style = status if status in {"active", "completed", "blocked", "paused", "pending"} else "closed"
        classes[style].append(node_keys[node["id"]])
    for style, keys in classes.items():
        lines.append(f"  class {','.join(keys)} {style};")
    return "\n".join(lines)


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _coverage_note(coverage: str) -> str:
    if coverage == "exact":
        return "生命周期追踪从 Mission 初始化开始；各类成本仍只包含宿主实际上报的 span。"
    if coverage == "partial":
        return "追踪晚于 Mission 创建，因此更早的执行路线与成本保持未知，不做猜测。"
    return "没有执行轨迹；当前仅展示 Mission 快照，时间与 Token 成本保持未知。"


def render_markdown(report: dict[str, Any]) -> str:
    mission = report["mission"]
    cost = mission["cost"]
    overhead = report["overhead"]["cost"]
    lines = [
        "# TPlan 实际执行与成本树",
        "",
        f"> {_coverage_note(report['trace']['coverage'])}",
        "",
        "```mermaid",
        render_mermaid(report),
        "```",
        "",
        f"视图：`{report['view']}`；真实节点：{report['trace']['visible_node_count']}/{report['trace']['total_node_count']}。",
    ]
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
