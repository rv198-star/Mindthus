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


REPORT_SCHEMA_VERSION = "tplan.execution_cost_tree.v0.1"
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
AI_KINDS = {"model"}
SCRIPT_TOOL_KINDS = {"script", "tool"}
STATUS_LABELS = {
    "active": "running",
    "completed": "completed",
    "blocked": "blocked",
    "paused": "paused",
    "pending": "not run",
    "pruned": "pruned",
    "abandoned": "abandoned",
    "superseded": "superseded",
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


def _span_cost(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = list(records)
    intervals: list[tuple[int, int]] = []
    kind_intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
    kind_sources: dict[str, Counter[str]] = defaultdict(Counter)
    by_kind_resource_ms: Counter[str] = Counter()
    usage: Counter[str] = Counter()
    usage_fields: set[str] = set()
    sources: Counter[str] = Counter()
    usage_sources: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    for record in records:
        span = record["span"]
        start = _timestamp_ms(span["started_at"])
        finish = _timestamp_ms(span["finished_at"])
        interval = (start, finish)
        intervals.append(interval)
        kind = span["kind"]
        kind_intervals[kind].append(interval)
        by_kind_resource_ms[kind] += span["duration_ms"]
        sources[span["measurement_source"]] += 1
        kind_sources[kind][span["measurement_source"]] += 1
        statuses[span["status"]] += 1
        usage_source = record.get("usage_source")
        if isinstance(usage_source, str):
            usage_sources[usage_source] += 1
        for field, value in record.get("usage", {}).items():
            usage_fields.add(field)
            usage[field] += value
    token_records = [record for record in records if record["span"]["kind"] == "model"]
    if not token_records:
        token_records = [record for record in records if record["span"]["kind"] == "agent_turn"]
    if not token_records:
        usage_coverage = "not_applicable"
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
        "observed_wall_ms": _union_duration_ms(intervals),
        "resource_time_ms": sum(by_kind_resource_ms.values()),
        "by_kind_resource_ms": dict(sorted(by_kind_resource_ms.items())),
        "by_kind_wall_ms": {
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
    state["first_observed_at"] = state["first_observed_at"] or timestamp
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

        if event_type == "span_completed" and state is not None:
            _observe_node(state, record["span"]["started_at"], next_order)
            state["last_observed_at"] = record["span"]["finished_at"]
            state["attempts"] = max(state["attempts"], record["span"]["attempt"])

    if trace:
        trace_finish_ms = max(_record_time_ms(record) for record in trace)
    else:
        trace_finish_ms = _timestamp_ms(generated_at)
    mission_status = mission.get("mission", {}).get("status")
    active_finish_ms = trace_finish_ms if mission_status in TERMINAL_MISSION_STATUSES else _timestamp_ms(generated_at)
    for state in states.values():
        if state["active_started_ms"] is not None:
            state["active_intervals"].append((state["active_started_ms"], active_finish_ms))
            state["active_started_ms"] = None
        state["active_duration_ms"] = (
            _union_duration_ms(state["active_intervals"]) if coverage != "snapshot_only" else None
        )
        state["active_duration_source"] = coverage
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


def _cost_rank(node: dict[str, Any]) -> tuple[int, int, int, int]:
    cost = node["direct_cost"]
    usage = cost["usage"]
    return (
        cost["resource_time_ms"],
        usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        cost["span_count"],
        -node["plan_index"],
    )


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

    if view == "audit":
        selected = set(scope)
    elif view == "compact":
        selected = set(roots)
        if focus_task_id is not None:
            selected.update(children.get(focus_task_id, []))
    else:
        selected = set(roots)
        candidates = [node for node in nodes if node["id"] in scope and node["id"] not in selected]
        for node in candidates:
            if (
                node["status"] in ABNORMAL_TASK_STATUSES
                or node["attempts"] > 1
                or node["dynamic"]
                or node["outcome_summary"]
                or node["direct_cost"]["error_span_count"] > 0
                or node["direct_cost"]["measurement_sources"].get("unavailable", 0) > 0
                or node["id"] == node.get("active_task_id")
            ):
                selected.add(node["id"])
        ranked = sorted(candidates, key=_cost_rank, reverse=True)
        selected.update(node["id"] for node in ranked[:top_cost] if _cost_rank(node)[:3] != (0, 0, 0))

        for task_id in list(selected):
            parent_id = by_id[task_id]["parent_id"]
            while parent_id is not None and parent_id in scope:
                selected.add(parent_id)
                parent_id = by_id[parent_id]["parent_id"]

    def sibling_key(task_id: str) -> tuple[int, int]:
        order = by_id[task_id]["execution_order"]
        return (order if isinstance(order, int) else 1_000_000, by_id[task_id]["plan_index"])

    ordered: list[str] = []

    def visit(task_id: str) -> None:
        if task_id in selected:
            ordered.append(task_id)
        for child_id in sorted(children.get(task_id, []), key=sibling_key):
            if child_id in scope and (child_id in selected or any(item in selected for item in _descendant_ids(child_id, children))):
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
    for record in trace:
        if record["event_type"] != "span_completed":
            continue
        all_spans.append(record)
        attribution = record["span"]["attribution"]
        if attribution == "exact":
            exact_spans[record["task_id"]].append(record)
        else:
            overhead_spans[attribution].append(record)

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
            "active_duration_ms": state["active_duration_ms"],
            "active_duration_source": state["active_duration_source"],
            "outcome_summary": state["outcome_summary"],
            "evidence_refs": state["evidence_refs"],
            "artifact_refs": state["artifact_refs"],
            "status_history": state["status_history"],
            "direct_cost": _span_cost(exact_spans.get(task_id, [])),
            "inclusive_cost": _span_cost(inclusive_records),
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
    elapsed_ms, started_at, finished_at = _mission_elapsed(mission, trace, coverage, generated_at)
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
            "elapsed_ms": elapsed_ms,
            "started_at": started_at,
            "finished_at": finished_at,
            "cost": _span_cost(all_spans),
        },
        "trace": {
            "coverage": coverage,
            "record_count": len(trace),
            "span_count": len(all_spans),
            "cost_scope": "reported_spans_only",
            "hidden_node_count": hidden_count,
            "visible_node_count": len(visible_nodes),
            "total_node_count": len(nodes),
        },
        "overhead": {
            "cost": _span_cost([record for records in overhead_spans.values() for record in records]),
            "by_attribution": overhead_by_attribution,
        },
        "nodes": visible_nodes,
        "visible_node_ids": visible_ids,
    }
    report["tree_edges"] = _visible_edges(visible_nodes, visible_set, by_id, focus_task_id)
    return report


def _visible_edges(
    nodes: list[dict[str, Any]],
    visible_ids: set[str],
    all_tasks: dict[str, dict[str, Any]],
    focus_task_id: str | None,
) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for node in nodes:
        task_id = node["id"]
        parent_id = node["parent_id"]
        while parent_id is not None and parent_id not in visible_ids:
            parent = all_tasks.get(parent_id)
            parent_id = parent.get("parent_id") if parent else None
        if task_id == focus_task_id or parent_id is None:
            edges.append({"from": "mission", "to": task_id})
        else:
            edges.append({"from": parent_id, "to": task_id})
    return edges


def _fmt_duration(value: int | None) -> str:
    if value is None:
        return "unknown"
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
    if coverage == "not_applicable":
        return "n/a"
    if coverage == "unavailable" or not ({"input_tokens", "output_tokens"} & fields):
        return "unknown"
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
        suffix.append(f"cached {_fmt_token_number(usage.get('cached_input_tokens', 0))}")
    if "reasoning_output_tokens" in fields:
        suffix.append(f"reasoning {_fmt_token_number(usage.get('reasoning_output_tokens', 0))}")
    return f"{input_value} in / {output_value} out" + (f" ({', '.join(suffix)})" if suffix else "")


def _kind_time(cost: dict[str, Any], kinds: set[str]) -> int:
    return sum(cost["by_kind_resource_ms"].get(kind, 0) for kind in kinds)


def _fmt_kind_duration(cost: dict[str, Any], kinds: set[str]) -> str:
    present = [kind for kind in kinds if kind in cost["by_kind_resource_ms"]]
    if not present:
        return "n/a"
    sources: Counter[str] = Counter()
    for kind in present:
        sources.update(cost["by_kind_measurement_sources"].get(kind, {}))
    value = _kind_time(cost, kinds)
    if sources and set(sources) == {"unavailable"}:
        return "unknown"
    rendered = _fmt_duration(value)
    if sources.get("unavailable"):
        return f"≥{rendered}" if value else "unknown"
    if sources.get("inferred"):
        return f"~{rendered}"
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


def _node_label(node: dict[str, Any], view: str) -> str:
    order = f"#{node['execution_order']} " if node["execution_order"] is not None else ""
    dynamic = " +dynamic" if node["dynamic"] else ""
    title = _shorten(node["title"], 54 if view != "audit" else 80)
    status = STATUS_LABELS.get(node["status"], node["status"])
    icon = STATUS_ICONS.get(node["status"], "•")
    lines = [f"{order}{title} · {node['id']}{dynamic}", f"{icon} {status} · active {_fmt_duration(node['active_duration_ms'])}"]
    if view != "compact":
        cost = node["inclusive_cost"]
        cost_parts: list[str] = []
        if any(kind in cost["by_kind_resource_ms"] for kind in AI_KINDS):
            cost_parts.append(f"AI {_fmt_kind_duration(cost, AI_KINDS)}")
        if any(kind in cost["by_kind_resource_ms"] for kind in SCRIPT_TOOL_KINDS):
            cost_parts.append(f"script/tool {_fmt_kind_duration(cost, SCRIPT_TOOL_KINDS)}")
        if "agent_turn" in cost["by_kind_resource_ms"]:
            cost_parts.append(f"turn {_fmt_kind_duration(cost, {'agent_turn'})}")
        if cost_parts:
            lines.append(" · ".join(cost_parts))
        tokens = _fmt_tokens(cost)
        if tokens != "n/a":
            lines.append(f"tokens {tokens}")
        if node["attempts"] > 1:
            lines.append(f"attempts {node['attempts']}")
        if node["outcome_summary"]:
            lines.append(f"result: {_shorten(node['outcome_summary'], 72)}")
    return "<br/>".join(_html(line) for line in lines)


def render_mermaid(report: dict[str, Any]) -> str:
    mission = report["mission"]
    cost = mission["cost"]
    mission_lines = [
        f"{_shorten(mission['title'], 68)}",
        f"Mission · {mission['status']} · elapsed {_fmt_duration(mission['elapsed_ms'])}",
    ]
    cost_parts: list[str] = []
    if any(kind in cost["by_kind_resource_ms"] for kind in AI_KINDS):
        cost_parts.append(f"AI {_fmt_kind_duration(cost, AI_KINDS)}")
    if any(kind in cost["by_kind_resource_ms"] for kind in SCRIPT_TOOL_KINDS):
        cost_parts.append(f"script/tool {_fmt_kind_duration(cost, SCRIPT_TOOL_KINDS)}")
    if cost_parts:
        mission_lines.append(" · ".join(cost_parts))
    tokens = _fmt_tokens(cost)
    if tokens != "n/a":
        mission_lines.append(f"tokens {tokens}")
    mission_lines.append(f"coverage {report['trace']['coverage']} · {report['view']}")

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
        return "Lifecycle tracing started with Mission initialization; costs still include only spans actually reported by their hosts."
    if coverage == "partial":
        return "Tracing began after Mission creation, so earlier route and cost are unknown rather than estimated."
    return "No execution trace is available; the tree shows the current Mission snapshot and leaves time/Token cost unknown."


def render_markdown(report: dict[str, Any]) -> str:
    mission = report["mission"]
    cost = mission["cost"]
    overhead = report["overhead"]["cost"]
    lines = [
        "# TPlan Actual Execution & Cost Tree",
        "",
        f"> {_coverage_note(report['trace']['coverage'])}",
        "",
        "| Scope | State | End-to-end elapsed | AI/model time | Script/tool time | Tokens |",
        "| --- | --- | ---: | ---: | ---: | --- |",
        "| "
        + " | ".join(
            [
                _markdown_cell(mission["title"]),
                _markdown_cell(mission["status"]),
                _fmt_duration(mission["elapsed_ms"]),
                _fmt_kind_duration(cost, AI_KINDS),
                _fmt_kind_duration(cost, SCRIPT_TOOL_KINDS),
                _markdown_cell(_fmt_tokens(cost)),
            ]
        )
        + " |",
        "",
        "```mermaid",
        render_mermaid(report),
        "```",
        "",
        f"View: `{report['view']}`. Visible nodes: {report['trace']['visible_node_count']}/{report['trace']['total_node_count']}.",
    ]
    if report["trace"]["hidden_node_count"]:
        lines.append(
            f"{report['trace']['hidden_node_count']} lower-signal nodes are hidden; use `--view audit` or `--focus TASK_ID` to expand."
        )
    lines.extend(
        [
            "",
            "Cost reading: end-to-end elapsed is wall time; per-kind durations are resource time and may overlap when spans are nested or parallel. "
            "Cached input is already part of input Tokens and is never added again.",
        ]
    )
    if overhead["span_count"]:
        lines.append(
            f"Mission overhead/shared/unattributed spans: {_fmt_duration(overhead['resource_time_ms'])} resource time, "
            f"{_fmt_tokens(overhead)} Tokens. These costs are not divided across task nodes."
        )

    notable = [
        node
        for node in report["nodes"]
        if node["outcome_summary"]
        or node["status"] in ABNORMAL_TASK_STATUSES
        or node["attempts"] > 1
        or node["direct_cost"]["error_span_count"]
    ]
    if notable and report["view"] != "compact":
        lines.extend(["", "## Outcomes and exceptions", ""])
        for node in notable:
            details: list[str] = []
            if node["outcome_summary"]:
                details.append(_shorten(node["outcome_summary"], 180))
            if node["attempts"] > 1:
                details.append(f"{node['attempts']} attempts")
            if node["direct_cost"]["error_span_count"]:
                details.append(f"{node['direct_cost']['error_span_count']} error span(s)")
            if not details:
                details.append(STATUS_LABELS.get(node["status"], node["status"]))
            lines.append(f"- {node['title']} (`{node['id']}`): {'; '.join(details)}")

    if report["view"] == "audit":
        lines.extend(
            [
                "",
                "## Audit detail",
                "",
                "| Order | Node | State | Active | Attempts | Direct resource | Subtree resource | Evidence refs | Artifact refs |",
                "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
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
                        _fmt_duration(node["active_duration_ms"]),
                        str(node["attempts"]),
                        _fmt_duration(node["direct_cost"]["resource_time_ms"]),
                        _fmt_duration(node["inclusive_cost"]["resource_time_ms"]),
                        str(len(node["evidence_refs"])),
                        str(len(node["artifact_refs"])),
                    ]
                )
                + " |"
            )
    return "\n".join(lines).rstrip() + "\n"


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
