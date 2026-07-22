#!/usr/bin/env python3
"""Pure, read-only outcome attribution for TPlan runtime snapshots.

The module classifies validated writeback and telemetry. It never decides whether
an acceptance claim is semantically true, and never attributes cost causally.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from tplan_runtime import (
    CONTINUATION_AUTHORIZATION_FIELDS,
    CONTINUATION_TRIGGER_REASONS,
    OUTCOME_ATTRIBUTION_SCHEMA_VERSION,
    classify_evidence_outcome,
    parent_chain,
    task_map,
)


LIFECYCLE_WRITEBACK_TYPES = {
    "node_added",
    "task_status_changed",
    "active_node_changed",
    "mission_status_changed",
}


def _blank_scope(kind: str, scope_id: str) -> dict[str, Any]:
    return {
        "schema_version": OUTCOME_ATTRIBUTION_SCHEMA_VERSION,
        "scope": {"kind": kind, "id": scope_id},
        "yield_class": "no_activity",
        "countable_progress": [],
        "constraint_deltas": [],
        "state_writebacks": [],
        "unclassified_writebacks": [],
        "telemetry": {"span_count": 0, "cost_present": False},
        "warnings": [],
    }


def _event_entry(event: dict[str, Any], kind: str, **extra: Any) -> dict[str, Any]:
    entry = {
        "kind": kind,
        "summary": str(event.get("summary", "")).strip(),
        "evidence_ids": [event["id"]] if isinstance(event.get("id"), str) else [],
        "commit_ids": [],
    }
    entry.update(extra)
    return entry


def _refs(record: dict[str, Any], field: str) -> list[str]:
    refs = record.get("refs")
    values = refs.get(field) if isinstance(refs, dict) else None
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, str)]


def _commit_index(trace: list[dict[str, Any]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    for record in trace:
        if record.get("event_type") not in LIFECYCLE_WRITEBACK_TYPES:
            continue
        commit_id = record.get("commit_id")
        if not isinstance(commit_id, str) or not commit_id:
            continue
        for evidence_id in _refs(record, "evidence_ids"):
            index[evidence_id].add(commit_id)
    return index


def _valid_continuation_authorization(payload: dict[str, Any]) -> bool:
    authorization = payload.get("continuation_authorization")
    if not isinstance(authorization, dict):
        return False
    reasons = authorization.get("trigger_reasons")
    if (
        not isinstance(reasons, list)
        or not all(isinstance(reason, str) and reason in CONTINUATION_TRIGGER_REASONS for reason in reasons)
    ):
        return False
    return all(
        isinstance(authorization.get(field), str)
        and authorization[field] in allowed
        for field, allowed in CONTINUATION_AUTHORIZATION_FIELDS.items()
    ) and authorization.get("authorized_action") in {"continue_same_path", "targeted_fix", "batch_details"}


def _path_delta(
    event: dict[str, Any], commit_ids: list[str]
) -> tuple[dict[str, Any] | None, str | None]:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return None, "decision_applied payload is not an object"
    mutations = payload.get("proposed_mutations")
    recommendation = payload.get("recommendation")
    if isinstance(mutations, list) and mutations and commit_ids:
        return _event_entry(event, "path_delta", commit_ids=commit_ids), None
    if (
        recommendation == "continue"
        and isinstance(mutations, list)
        and not mutations
        and _valid_continuation_authorization(payload)
    ):
        return _event_entry(event, "path_delta", commit_ids=commit_ids), None
    return None, "decision_applied has neither committed mutations nor valid continuation authorization"


def _scope_ids(mission: dict[str, Any], task_id: Any) -> list[str]:
    if not isinstance(task_id, str) or task_id not in task_map(mission):
        return []
    return [str(task["id"]) for task in parent_chain(mission, task_id)]


def _add_unique(bucket: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    if entry not in bucket:
        bucket.append(entry)


def _add_warning(scope: dict[str, Any], code: str, **details: Any) -> None:
    warning = {"code": code, **details}
    if warning not in scope["warnings"]:
        scope["warnings"].append(warning)


def _finish(scope: dict[str, Any]) -> None:
    progress = bool(scope["countable_progress"])
    constraints = bool(scope["constraint_deltas"])
    writebacks = bool(scope["state_writebacks"] or scope["unclassified_writebacks"])
    telemetry = bool(scope["telemetry"]["cost_present"])
    if progress and constraints:
        scope["yield_class"] = "progress_and_constraint"
    elif progress:
        scope["yield_class"] = "countable_progress"
    elif constraints:
        scope["yield_class"] = "constraint_delta"
    elif scope["unclassified_writebacks"]:
        scope["yield_class"] = "unclassified"
    elif writebacks:
        scope["yield_class"] = "writeback_only"
    elif telemetry:
        scope["yield_class"] = "telemetry_only"
    else:
        scope["yield_class"] = "no_activity"


def build_outcome_attribution(
    mission: dict[str, Any],
    events: list[dict[str, Any]],
    trace: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build Mission and task/ancestor attribution from an immutable snapshot."""

    trace = trace or []
    mission_id = str(mission.get("mission", {}).get("id", "mission"))
    mission_scope = _blank_scope("mission", mission_id)
    task_scopes = {
        task_id: _blank_scope(str(task.get("kind", "task")), task_id)
        for task_id, task in task_map(mission).items()
    }
    commits_by_evidence = _commit_index(trace)
    evidence_id_counts = Counter(
        event.get("id")
        for event in events
        if isinstance(event, dict) and isinstance(event.get("id"), str)
    )
    qualified_by_evidence: dict[str, tuple[str, dict[str, Any]]] = {}

    for event in events:
        result = classify_evidence_outcome(mission, event)
        classification = result["classification"]
        event_id = event.get("id")
        commit_ids = sorted(commits_by_evidence.get(event_id, set())) if isinstance(event_id, str) else []
        scopes = [mission_scope, *[task_scopes[task_id] for task_id in _scope_ids(mission, event.get("task_id"))]]
        if isinstance(event_id, str) and evidence_id_counts[event_id] > 1:
            for scope in scopes:
                _add_warning(scope, "duplicate_evidence_id", evidence_id=event_id)
            entry = _event_entry(
                event,
                "unclassified_writeback",
                reason="duplicate evidence id cannot support outcome attribution",
                commit_ids=[],
            )
            for scope in scopes:
                _add_unique(scope["unclassified_writebacks"], entry)
            continue
        if classification == "acceptance_delta":
            payload = event.get("payload", {})
            entry = _event_entry(
                event,
                "acceptance_delta",
                acceptance_ids=list(payload.get("acceptance_ids", [])),
                commit_ids=commit_ids,
            )
            target = "countable_progress"
        elif classification == "constraint_delta":
            payload = event.get("payload", {})
            extra = {}
            if event.get("event_type") == "acceptance_failed":
                extra["acceptance_ids"] = list(payload.get("acceptance_ids", []))
            entry = _event_entry(event, "constraint_delta", commit_ids=commit_ids, **extra)
            target = "constraint_deltas"
        elif classification == "decision_applied_candidate":
            entry, reason = _path_delta(event, commit_ids)
            if entry is not None:
                target = "countable_progress"
            else:
                entry = _event_entry(event, "unclassified_writeback", reason=reason, commit_ids=commit_ids)
                target = "unclassified_writebacks"
                for scope in scopes:
                    _add_warning(
                        scope,
                        "unclassified_decision_applied",
                        evidence_id=event_id,
                        reason=reason,
                    )
        else:
            warnings = result.get("warnings", [])
            reason = "; ".join(warnings) if warnings else "event type does not imply countable progress"
            entry = _event_entry(event, "unclassified_writeback", reason=reason, commit_ids=commit_ids)
            target = "unclassified_writebacks"
            if warnings:
                for scope in scopes:
                    _add_warning(
                        scope,
                        "legacy_or_invalid_evidence",
                        evidence_id=event_id,
                        findings=list(warnings),
                    )
        for scope in scopes:
            _add_unique(scope[target], entry)
        if (
            target in {"countable_progress", "constraint_deltas"}
            and isinstance(event_id, str)
            and evidence_id_counts[event_id] == 1
        ):
            qualified_by_evidence[event_id] = (target, entry)

    for record in trace:
        event_type = record.get("event_type")
        if event_type in LIFECYCLE_WRITEBACK_TYPES:
            entry = {
                "kind": "state_writeback",
                "event_type": event_type,
                "task_id": record.get("task_id"),
                "summary": record.get("payload", {}).get("outcome_summary")
                if isinstance(record.get("payload"), dict)
                else None,
                "evidence_ids": _refs(record, "evidence_ids"),
                "artifact_refs": _refs(record, "artifact_refs"),
                "commit_ids": [record["commit_id"]] if isinstance(record.get("commit_id"), str) else [],
            }
            scopes = [mission_scope, *[task_scopes[task_id] for task_id in _scope_ids(mission, record.get("task_id"))]]
            for scope in scopes:
                _add_unique(scope["state_writebacks"], entry)
            for evidence_id in entry["evidence_ids"]:
                qualified = qualified_by_evidence.get(evidence_id)
                if qualified is None:
                    continue
                target, outcome_entry = qualified
                for scope in scopes:
                    _add_unique(scope[target], outcome_entry)

        if event_type == "span_completed":
            mission_scope["telemetry"]["span_count"] += 1
            span = record.get("span")
            if isinstance(span, dict) and span.get("attribution") == "exact":
                for task_id in _scope_ids(mission, record.get("task_id")):
                    task_scopes[task_id]["telemetry"]["span_count"] += 1

    mission_scope["telemetry"]["cost_present"] = mission_scope["telemetry"]["span_count"] > 0
    for scope in task_scopes.values():
        scope["telemetry"]["cost_present"] = scope["telemetry"]["span_count"] > 0

    for task_id, task in task_map(mission).items():
        scope = task_scopes[task_id]
        if task.get("status") == "completed" and not any(
            item.get("event_type") == "task_status_changed" and item.get("task_id") == task_id
            for item in scope["state_writebacks"]
        ):
            snapshot_entry = {
                "kind": "state_writeback",
                "event_type": "mission_snapshot_status",
                "task_id": task_id,
                "summary": "Current Mission snapshot records this task as completed.",
                "evidence_ids": [],
                "artifact_refs": [],
                "commit_ids": [],
            }
            for ancestor_id in _scope_ids(mission, task_id):
                _add_unique(task_scopes[ancestor_id]["state_writebacks"], snapshot_entry)
            _add_unique(mission_scope["state_writebacks"], snapshot_entry)
        if task.get("status") == "completed" and not scope["countable_progress"]:
            _add_warning(scope, "completion_without_progress_evidence", task_id=task_id)
            _add_warning(mission_scope, "completion_without_progress_evidence", task_id=task_id)

    _finish(mission_scope)
    for scope in task_scopes.values():
        _finish(scope)
    return {
        "schema_version": OUTCOME_ATTRIBUTION_SCHEMA_VERSION,
        "mission": mission_scope,
        "tasks": task_scopes,
    }


def short_attribution_label(attribution: dict[str, Any]) -> str:
    labels = {
        "progress_and_constraint": "推进+约束",
        "countable_progress": "推进",
        "constraint_delta": "约束",
        "writeback_only": "仅写回",
        "telemetry_only": "仅遥测",
        "unclassified": "未分类",
        "no_activity": "无活动",
    }
    return labels.get(str(attribution.get("yield_class")), "未分类")


def attribution_text(attribution: dict[str, Any]) -> str:
    progress = attribution.get("countable_progress", [])
    constraints = attribution.get("constraint_deltas", [])
    if progress:
        acceptance_ids = sorted(
            {
                acceptance_id
                for item in progress
                for acceptance_id in item.get("acceptance_ids", [])
                if isinstance(acceptance_id, str)
            }
        )
        detail = f"（acceptance {', '.join(acceptance_ids)}）" if acceptance_ids else ""
        suffix = f"，另有 {len(constraints)} 项关键约束" if constraints else ""
        rendered = f"可计推进{detail}{suffix}"
    elif constraints:
        rendered = f"{len(constraints)} 项关键约束，无可计推进"
    elif attribution.get("unclassified_writebacks"):
        rendered = "存在未分类写回，暂无可计推进"
    elif attribution.get("state_writebacks"):
        rendered = "状态已写回，但没有可计推进 evidence"
    elif attribution.get("telemetry", {}).get("cost_present"):
        rendered = "仅遥测，暂无 Mission/evidence 写回"
    else:
        rendered = "无遥测或结果写回"
    if any(
        warning.get("code") == "completion_without_progress_evidence"
        for warning in attribution.get("warnings", [])
    ):
        return f"completion_without_progress_evidence；{rendered}"
    return rendered


def attribution_audit_lines(attribution: dict[str, Any]) -> list[str]:
    buckets = (
        "countable_progress",
        "constraint_deltas",
        "state_writebacks",
        "unclassified_writebacks",
    )
    evidence_ids = sorted(
        {
            value
            for bucket in buckets
            for item in attribution.get(bucket, [])
            for value in item.get("evidence_ids", [])
            if isinstance(value, str)
        }
    )
    commit_ids = sorted(
        {
            value
            for bucket in buckets
            for item in attribution.get(bucket, [])
            for value in item.get("commit_ids", [])
            if isinstance(value, str)
        }
    )
    reasons = [
        item["reason"]
        for item in attribution.get("unclassified_writebacks", [])
        if isinstance(item.get("reason"), str)
    ]
    warning_codes = [
        item["code"]
        for item in attribution.get("warnings", [])
        if isinstance(item.get("code"), str)
    ]
    return [
        f"evidence {','.join(evidence_ids) or 'none'}",
        f"commit {','.join(commit_ids) or 'none'}",
        f"unclassified {','.join(reasons) or 'none'}",
        f"warnings {','.join(warning_codes) or 'none'}",
    ]


def attribution_audit_text(attribution: dict[str, Any]) -> str:
    return " · ".join(attribution_audit_lines(attribution))
