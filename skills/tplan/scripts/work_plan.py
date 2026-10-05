#!/usr/bin/env python3
"""Optional planning metadata and a read-only view of declared Mission work.

The Mission owns state and acceptance. This module validates planning annotations
and computes only stated, comparable remaining-work quantities.
"""

from __future__ import annotations

import copy
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from tplan_errors import TplanError


WORK_PLAN_SCHEMA_VERSION = "tplan.work_plan.v0.1"
WORK_VIEW_SCHEMA_VERSION = "tplan.work_view.v0.1"
REMAINING_STATUSES = {"pending", "active", "blocked", "paused"}
PLAN_FIELDS = {
    "schema_version", "coverage", "scope_note", "blocks", "as_of", "source",
    "progress", "risks", "blockers",
}
BLOCK_FIELDS = {"task_id", "remaining", "depends_on", "parallel_conditions"}
RANGE_FIELDS = {"low", "high", "unit", "basis", "confidence"}
NOTE_FIELDS = {"summary", "task_ids", "impact", "source", "status"}
CONFIDENCES = {"low", "medium", "high", "unknown"}


def _tasks(mission: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values = mission.get("tasks")
    if not isinstance(values, list):
        return {}
    return {
        task["id"]: task for task in values
        if isinstance(task, dict) and isinstance(task.get("id"), str)
    }


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _fields(errors: list[str], value: dict[str, Any], allowed: set[str], label: str) -> None:
    extra = sorted(str(key) for key in value if key not in allowed)
    if extra:
        errors.append(f"{label} unsupported fields: {', '.join(extra)}")


def _strings(errors: list[str], value: Any, label: str) -> bool:
    if not isinstance(value, list) or not all(_text(item) for item in value):
        errors.append(f"{label} must be a list of non-empty strings")
        return False
    if len(value) != len(set(value)):
        errors.append(f"{label} must contain distinct values")
        return False
    return True


def _range(errors: list[str], value: Any, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object or null")
        return
    _fields(errors, value, RANGE_FIELDS, label)
    for key in ("low", "high"):
        if not _number(value.get(key)):
            errors.append(f"{label}.{key} must be a finite non-negative number")
    if _number(value.get("low")) and _number(value.get("high")) and value["low"] > value["high"]:
        errors.append(f"{label}.low must not exceed high")
    for key in ("unit", "basis"):
        if not _text(value.get(key)):
            errors.append(f"{label}.{key} must be a non-empty string")
    if "confidence" in value and (
        not isinstance(value["confidence"], str) or value["confidence"] not in CONFIDENCES
    ):
        errors.append(f"{label}.confidence must be low, medium, high, or unknown")


def _ancestors(task_id: str, tasks: dict[str, dict[str, Any]]) -> list[str]:
    ancestors: list[str] = []
    seen = {task_id}
    parent = tasks.get(task_id, {}).get("parent_id")
    while isinstance(parent, str) and parent in tasks and parent not in seen:
        ancestors.append(parent)
        seen.add(parent)
        parent = tasks[parent].get("parent_id")
    return ancestors


def validate_work_plan(mission: dict[str, Any], work_plan: Any) -> list[str]:
    """Validate shape and references, without judging estimates or changing state."""
    if not isinstance(work_plan, dict):
        return ["work_plan must be an object"]
    errors: list[str] = []
    _fields(errors, work_plan, PLAN_FIELDS, "work_plan")
    if work_plan.get("schema_version") != WORK_PLAN_SCHEMA_VERSION:
        errors.append(f"work_plan.schema_version must be {WORK_PLAN_SCHEMA_VERSION}")
    if not isinstance(work_plan.get("coverage"), str) or work_plan["coverage"] not in {"complete", "partial"}:
        errors.append("work_plan.coverage must be complete or partial")
    if not _text(work_plan.get("scope_note")):
        errors.append("work_plan.scope_note must be a non-empty string")
    if "source" in work_plan and not _text(work_plan["source"]):
        errors.append("work_plan.source must be a non-empty string")
    if "as_of" in work_plan:
        try:
            value = work_plan["as_of"]
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
            if parsed is None or parsed.tzinfo is None:
                raise ValueError
        except ValueError:
            errors.append("work_plan.as_of must be ISO-8601 with timezone")

    tasks = _tasks(mission)
    blocks = work_plan.get("blocks")
    block_ids: set[str] = set()
    dependencies: dict[str, list[str]] = {}
    if not isinstance(blocks, list):
        errors.append("work_plan.blocks must be a list")
        blocks = []
    for index, block in enumerate(blocks):
        label = f"work_plan.blocks[{index}]"
        if not isinstance(block, dict):
            errors.append(f"{label} must be an object")
            continue
        _fields(errors, block, BLOCK_FIELDS, label)
        task_id = block.get("task_id")
        valid_id = isinstance(task_id, str) and task_id in tasks
        if not valid_id:
            errors.append(f"{label}.task_id must reference an existing task")
        elif task_id in block_ids:
            errors.append(f"{label}.task_id duplicates {task_id}")
        else:
            block_ids.add(task_id)
        if "remaining" in block:
            _range(errors, block["remaining"], f"{label}.remaining")
        predecessor_ids = block.get("depends_on")
        if predecessor_ids is not None and _strings(errors, predecessor_ids, f"{label}.depends_on"):
            unknown = sorted(set(predecessor_ids) - set(tasks))
            if unknown:
                errors.append(f"{label}.depends_on references unknown tasks: {', '.join(unknown)}")
            if valid_id:
                if task_id in predecessor_ids:
                    errors.append(f"{label}.depends_on cannot reference itself")
                dependencies[task_id] = predecessor_ids
        conditions = block.get("parallel_conditions")
        if conditions is not None:
            _strings(errors, conditions, f"{label}.parallel_conditions")

    for task_id in sorted(block_ids):
        overlap = sorted(block_ids.intersection(_ancestors(task_id, tasks)))
        if overlap:
            errors.append(f"work_plan blocks overlap: {task_id} and ancestor {', '.join(overlap)}")

    graph_nodes = set(dependencies) | {
        predecessor for values in dependencies.values() for predecessor in values
    }
    incoming = {task_id: 0 for task_id in graph_nodes}
    for values in dependencies.values():
        for predecessor in values:
            incoming[predecessor] += 1
    queue = [task_id for task_id, count in incoming.items() if count == 0]
    visited = 0
    while queue:
        task_id = queue.pop()
        visited += 1
        for predecessor in dependencies.get(task_id, []):
            incoming[predecessor] -= 1
            if incoming[predecessor] == 0:
                queue.append(predecessor)
    if visited != len(graph_nodes):
        errors.append("work_plan depends_on contains a cycle")

    progress = work_plan.get("progress")
    if progress is not None:
        if not isinstance(progress, dict):
            errors.append("work_plan.progress must be an object or null")
        else:
            _fields(errors, progress, {"label", "value", "unit", "basis"}, "work_plan.progress")
            for key in ("label", "unit", "basis"):
                if not _text(progress.get(key)):
                    errors.append(f"work_plan.progress.{key} must be a non-empty string")
            if not _number(progress.get("value")):
                errors.append("work_plan.progress.value must be a finite non-negative number")
            elif isinstance(progress.get("unit"), str) and progress["unit"] in {"%", "percent", "percentage"} and progress["value"] > 100:
                errors.append("work_plan.progress percentage must not exceed 100")

    for field in ("risks", "blockers"):
        if field not in work_plan:
            continue
        notes = work_plan[field]
        if not isinstance(notes, list):
            errors.append(f"work_plan.{field} must be a list")
            continue
        for index, note in enumerate(notes):
            label = f"work_plan.{field}[{index}]"
            if not isinstance(note, dict):
                errors.append(f"{label} must be an object")
                continue
            allowed = NOTE_FIELDS | ({"release_condition"} if field == "blockers" else set())
            _fields(errors, note, allowed, label)
            if not _text(note.get("summary")):
                errors.append(f"{label}.summary must be a non-empty string")
            for key in ("impact", "source", "release_condition"):
                if key in note and not _text(note[key]):
                    errors.append(f"{label}.{key} must be a non-empty string")
            if "status" in note and (
                not isinstance(note["status"], str) or note["status"] not in {"active", "resolved"}
            ):
                errors.append(f"{label}.status must be active or resolved")
            if "task_ids" in note and _strings(errors, note["task_ids"], f"{label}.task_ids"):
                unknown = sorted(set(note["task_ids"]) - set(tasks))
                if unknown:
                    errors.append(f"{label}.task_ids references unknown tasks: {', '.join(unknown)}")
    return errors


def load_work_plan(path: Path | None) -> dict[str, Any] | None:
    """Read optional input JSON; validation needs its associated Mission."""
    if path is None:
        return None
    import json

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TplanError("work plan input must be an object")
    return value


def _frontier(tasks: dict[str, dict[str, Any]], planned_ids: set[str]) -> list[str]:
    """Project real nodes into non-overlapping blocks, retaining uncovered branches."""
    children: dict[str | None, list[str]] = defaultdict(list)
    for task_id, task in tasks.items():
        children[task.get("parent_id")].append(task_id)
    planned_ancestors = {ancestor for task_id in planned_ids for ancestor in _ancestors(task_id, tasks)}
    result: list[str] = []
    seen: set[str] = set()

    def append_branch(task_id: str) -> None:
        if task_id in seen:
            return
        seen.add(task_id)
        if task_id in planned_ids or task_id not in planned_ancestors:
            result.append(task_id)
        else:
            for child in children.get(task_id, []):
                append_branch(child)

    for task_id in children.get(None, []):
        append_branch(task_id)
    return result


def _current_notes(plan: dict[str, Any], field: str) -> list[dict[str, Any]]:
    return [
        copy.deepcopy(note) | {
            "source_kind": "work_plan",
            "source_path": f"work_plan.{field}[{index}]",
        }
        for index, note in enumerate(plan.get(field, []))
        if note.get("status", "active") == "active"
    ]


def _current_risks(mission: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    from tplan_runtime import active_risk_signals

    # Reuse the runtime's current-risk semantics. The source task is where a
    # signal arose, not a substitute for its shared scope or affected surfaces.
    shared = [
        copy.deepcopy(signal) | {
            "summary": signal.get("signal"),
            "impact": signal.get("value_effect"),
            "source_kind": "shared_risk_signal",
            "source_path": "shared_context.risk_signals",
            "source_ref": signal.get("id"),
        }
        for signal in active_risk_signals(mission)
    ]
    return [*shared, *_current_notes(plan, "risks")]


def _state_context_ids(
    tasks: dict[str, dict[str, Any]], frontier: list[str],
) -> list[str]:
    """Keep unfinished source state visible when the accounting frontier is closed.

    These nodes have no inherited estimate and are not new accounting blocks.
    """
    current_frontier = {
        task_id for task_id in frontier if tasks[task_id].get("status") in REMAINING_STATUSES
    }
    current_ancestors = {
        ancestor for task_id in current_frontier for ancestor in _ancestors(task_id, tasks)
    }
    candidates = {
        task_id for task_id, task in tasks.items()
        if task.get("status") in REMAINING_STATUSES
        and task_id not in frontier
        and task_id not in current_ancestors
        and not current_frontier.intersection(_ancestors(task_id, tasks))
    }
    return [
        task_id for task_id in tasks
        if task_id in candidates and not candidates.intersection(_ancestors(task_id, tasks))
    ]


def build_work_view(
    mission: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
    outcome_attribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an honest current-work projection without filesystem writes.

    Acceptance remains with the established outcome classifier. Callers with an
    atomic snapshot should pass its full attribution, including execution trace.
    Historical blocker events are not promoted into current planning constraints.
    """
    if outcome_attribution is None and evidence is not None:
        from outcome_attribution import build_outcome_attribution

        outcome_attribution = build_outcome_attribution(mission, evidence)
    attribution = (
        outcome_attribution.get("mission", outcome_attribution)
        if isinstance(outcome_attribution, dict) else None
    )
    completion_gaps = {
        warning.get("task_id")
        for warning in (attribution or {}).get("warnings", [])
        if warning.get("code") == "completion_without_progress_evidence"
    }
    tasks = _tasks(mission)
    supplied = "work_plan" in mission
    raw_plan = mission.get("work_plan")
    errors = validate_work_plan(mission, raw_plan) if supplied else []
    plan = raw_plan if supplied and not errors else {}
    diagnostics: list[dict[str, Any]] = []
    limitations: list[str] = []
    if errors:
        diagnostics.extend({"code": "invalid_work_plan", "message": error} for error in errors)
        limitations.append("规划元数据未通过校验；保留真实任务状态，不使用无效规划计算工作量或占比。")
    elif not supplied:
        limitations.append("未提供工作量规划；以下仅展示当前已登记工作，剩余量与工作量进度未知。")
    elif plan["coverage"] == "partial":
        limitations.append("规划只覆盖部分范围；已估计量不能代表整个 Mission 的剩余工作。")

    declared = {block["task_id"]: block for block in plan.get("blocks", [])}
    frontier = _frontier(tasks, set(declared))
    context_ids = _state_context_ids(tasks, frontier)
    rows: list[dict[str, Any]] = []
    for task_id in [*frontier, *context_ids]:
        task = tasks[task_id]
        block = declared.get(task_id, {})
        remaining = block.get("remaining")
        uncertainty_reasons: list[str] = []
        if task.get("status") == "completed":
            if remaining is not None and remaining["high"] > 0:
                uncertainty_reasons.append("任务状态为已完成，但源剩余估计仍大于零；两项声明需要核对。")
            if task_id in completion_gaps:
                uncertainty_reasons.append("既有结果归因提示完成声明缺少合格推进证据；剩余量不能据此视为零。")
            elif attribution is None:
                uncertainty_reasons.append("未提供完成证据的结果归因；保留完成声明，剩余量是否归零尚不明确。")
        if task_id in context_ids:
            uncertainty_reasons.append("规划前沿的结束状态未覆盖本节点的未完成状态；未分摊或复制父子估计。")
        predecessor_ids = block.get("depends_on")
        dependencies = None if predecessor_ids is None else [
            {
                "task_id": predecessor,
                "title": tasks[predecessor].get("title", predecessor),
                "status": tasks[predecessor].get("status"),
                "satisfied": tasks[predecessor].get("status") == "completed",
            }
            for predecessor in predecessor_ids
        ]
        dependency_status = (
            "unknown" if dependencies is None
            else "unmet" if any(not item["satisfied"] for item in dependencies)
            else "declared_clear"
        )
        rows.append({
            "task_id": task_id,
            "title": task.get("title", task_id),
            "parent_id": task.get("parent_id"),
            "kind": task.get("kind"),
            "role": task.get("role"),
            "status": task.get("status"),
            "is_remaining": task.get("status") in REMAINING_STATUSES,
            "remaining_uncertain": bool(uncertainty_reasons),
            "uncertainty_reasons": uncertainty_reasons,
            "accounting_role": "state_context" if task_id in context_ids else "block",
            "source": "work_plan" if task_id in declared else "mission_snapshot",
            "remaining": copy.deepcopy(remaining),
            "remaining_share": None,
            "depends_on": copy.deepcopy(predecessor_ids),
            "dependencies": dependencies,
            "dependency_status": dependency_status,
            "parallel_conditions": copy.deepcopy(block.get("parallel_conditions")),
        })

    remaining_rows = [row for row in rows if row["is_remaining"] or row["remaining_uncertain"]]
    unresolved_ids = [row["task_id"] for row in rows if row["remaining_uncertain"]]
    unknown_ids = [row["task_id"] for row in remaining_rows if row["remaining"] is None]
    uncovered_ids = [row["task_id"] for row in remaining_rows if row["source"] == "mission_snapshot"]
    conflicts = [
        row["task_id"] for row in rows
        if row["status"] == "completed" and row["remaining"] is not None and row["remaining"]["high"] > 0
    ]
    if conflicts:
        diagnostics.append({
            "code": "completion_remaining_conflict",
            "message": "完成状态与正剩余估计同时存在；保留源值待核对，不判断哪项已过时。",
            "task_ids": conflicts,
        })
        limitations.append("部分完成声明仍有正剩余估计；源声明待核对，不能生成完整剩余总量。")
    # Accounting blocks may cover descendants used as prerequisites elsewhere.
    # Their existing evidence warnings must survive that presentation boundary.
    gap_ids = [task_id for task_id in tasks if task_id in completion_gaps]
    if gap_ids:
        names = "、".join(f"{tasks[task_id].get('title', task_id)}（{task_id}）" for task_id in gap_ids)
        gap_message = (
            f"既有结果归因提示以下任务的完成声明缺少合格推进证据：{names}。"
            "前置项的“已满足”仅反映登记状态，不证明完成证据已通过；缺失的剩余估计没有按零处理。"
        )
        diagnostics.append({
            "code": "completion_without_progress_evidence",
            "message": gap_message,
            "task_ids": gap_ids,
        })
        limitations.append(gap_message)
    if attribution is None and any(row["status"] == "completed" for row in rows):
        limitations.append("未提供完成证据归因；已完成状态不会单独证明剩余量为零。")
    if context_ids:
        diagnostics.append({
            "code": "frontier_state_gap",
            "message": "已结束规划节点与父子层级的未完成状态并存；补充未计量状态节点，保留原状态和源估计。",
            "task_ids": context_ids,
        })
        limitations.append("规划前沿与部分父子节点的未完成状态不一致；已保留未计量状态节点，不能生成完整剩余总量。")

    by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in remaining_rows:
        if row["remaining"] is not None:
            by_unit[row["remaining"]["unit"]].append(row)
    totals = []
    overflow_units: set[str] = set()
    for unit, group in sorted(by_unit.items()):
        low = sum(row["remaining"]["low"] for row in group)
        high = sum(row["remaining"]["high"] for row in group)
        if not _number(low) or not _number(high):
            overflow_units.add(unit)
            diagnostics.append({
                "code": "remaining_aggregate_overflow",
                "message": "剩余量小计超出可表示范围；保留单块估计，不生成该单位的小计或占比。",
                "task_ids": [row["task_id"] for row in group],
            })
            continue
        totals.append({
            "unit": unit, "low": low, "high": high,
            "task_ids": [row["task_id"] for row in group],
        })
    complete = bool(
        plan and plan.get("coverage") == "complete"
        and remaining_rows and not unknown_ids and not unresolved_ids
        and len(totals) == 1 and not overflow_units
    )
    coverage = "complete" if complete else "partial" if totals else "unavailable"
    total = {key: totals[0][key] for key in ("low", "high", "unit")} if complete else None
    if unknown_ids and plan:
        limitations.append("部分当前工作或待核对声明没有剩余量估计；未知量未按零处理。")
    if uncovered_ids and plan:
        diagnostics.append({
            "code": "uncovered_work_blocks",
            "message": "当前已登记工作中有未被规划覆盖或未计量的状态节点。",
            "task_ids": uncovered_ids,
        })
    if len(by_unit) > 1:
        limitations.append("剩余量使用不同单位，分别列出已估计小计，不合并为整体总量。")
    if overflow_units:
        limitations.append("部分剩余量无法安全汇总；没有生成溢出的数值或占比。")
    for unit, group in by_unit.items():
        if unit in overflow_units:
            continue
        total_low = sum(row["remaining"]["low"] for row in group)
        total_high = sum(row["remaining"]["high"] for row in group)
        if total_high == 0:
            continue
        for row in group:
            low, high = row["remaining"]["low"], row["remaining"]["high"]
            low_denominator = (total_high - high) + low
            high_denominator = (total_low - low) + high
            share_low = (low / low_denominator) * 100 if low_denominator > 0 else 0
            share_high = (high / high_denominator) * 100 if high_denominator > 0 else 0
            row["remaining_share"] = {
                "low": max(0, min(100, share_low)),
                "high": max(0, min(100, share_high)),
                "unit": "percent",
                "denominator_unit": unit,
                "coverage": "complete" if complete else "partial",
                "basis": "同单位、互不重叠且已有估计的源剩余声明；含待核对声明时仅作部分小计，区间按其他块的上下界计算，不要求合计 100%。",
            }
    if any(row["remaining_share"] is not None for row in rows):
        limitations.append("工作量占比指已估计剩余声明的构成；各块区间不要求合计 100%，也不是整体完成率。")
    exited_ids = [
        row["task_id"] for row in rows
        if row["status"] in {"pruned", "abandoned", "superseded"}
        and row["remaining"] is not None and row["remaining"]["high"] > 0
    ]
    if exited_ids:
        diagnostics.append({
            "code": "exited_block_retains_estimate",
            "message": "已裁剪、放弃或替代的节点保留源估计；按原退出状态不计当前执行量，也不作为完成成果。",
            "task_ids": exited_ids,
        })
        limitations.append("退出范围的节点仍可保留源估计；其估计不计当前执行量，退出状态不代表完成成果。")
    if remaining_rows:
        limitations.append("前置关系仅表示已声明的任务要求与当前状态；并行条件不证明资源、权限或执行时机已满足。")

    return {
        "schema_version": WORK_VIEW_SCHEMA_VERSION,
        "mission": {
            key: copy.deepcopy(mission.get("mission", {}).get(key))
            for key in ("id", "title", "objective", "status")
        } | {"active_task_id": mission.get("active_task_id")},
        "planning": {
            "present": supplied,
            "coverage": plan.get("coverage", "unavailable"),
            "scope_note": plan.get("scope_note"),
            "as_of": plan.get("as_of"),
            "source": plan.get("source"),
        },
        "progress": copy.deepcopy(plan.get("progress")),
        "status_counts": dict(Counter(task.get("status", "unknown") for task in tasks.values())),
        "blocks": rows,
        "remaining": {
            "coverage": coverage,
            "total": total,
            "totals_by_unit": totals,
            "unknown_task_ids": unknown_ids,
            "uncovered_task_ids": uncovered_ids,
            "unresolved_task_ids": unresolved_ids,
        },
        "risks": _current_risks(mission, plan),
        "blockers": _current_notes(plan, "blockers"),
        "limitations": limitations,
        "diagnostics": diagnostics,
        "outcome_attribution": copy.deepcopy(attribution),
    }


def read_work_view_snapshot(mission_dir: Path) -> dict[str, Any]:
    """Reuse the existing locked no-write snapshot, including provenance diagnostics."""
    from outcome_attribution import build_outcome_attribution
    from tplan_runtime import read_outcome_attribution_snapshot

    snapshot = read_outcome_attribution_snapshot(mission_dir)
    attribution = build_outcome_attribution(snapshot["mission"], snapshot["events"], snapshot["trace"])
    snapshot["work_view"] = build_work_view(
        snapshot["mission"], snapshot["events"], attribution["mission"]
    )
    return snapshot
