#!/usr/bin/env python3
"""Render an integrity-checked SRA v0.3 decision without recomputing semantics."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from sra_runtime import FINAL_DECISION_SCHEMA, SraRuntimeError, load_json, run_check
from sra_criteria import resolved_completion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render an SRA v0.3 terminal decision.")
    parser.add_argument("--dir", required=True, help="Terminal SRA run directory.")
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--output", help="Optional Markdown output path.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--view", choices=("card", "full"), help="Defaults to card for proportionate runs; full for legacy runs.")
    return parser.parse_args()


def _raw_input(run_dir: Path) -> dict[str, Any]:
    raw = load_json(run_dir / "raw-input.json")
    if not isinstance(raw, dict):
        raise SraRuntimeError("raw-input.json must contain an object")
    return raw


def _candidate_labels(raw: dict[str, Any]) -> dict[str, str]:
    return {
        str(item["candidate_id"]): str(item.get("action_statement", item["candidate_id"]))
        for item in raw.get("candidates", [])
        if isinstance(item, dict) and "candidate_id" in item
    }


def _resource_labels(raw: dict[str, Any]) -> dict[str, str]:
    return {
        str(item["resource_id"]): str(item.get("label", item["resource_id"]))
        for item in raw.get("allocation_frame", {}).get("resource_pools", [])
        if isinstance(item, dict) and "resource_id" in item
    }


def _candidate_label(value: Any, labels: dict[str, str], language: str) -> str:
    text = str(value)
    if text == "none":
        return "无" if language == "zh" else "none"
    if text == "reserve":
        return "机动资源" if language == "zh" else "reserve"
    return labels.get(text, text)


def _number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _quantity_text(quantity: Any, language: str) -> str:
    if not isinstance(quantity, dict):
        return "未记录" if language == "zh" else "not recorded"
    kind = quantity.get("quantity_kind")
    if kind == "exact":
        return f"{_number(quantity.get('amount'))} {quantity.get('unit')}"
    if kind == "bounded":
        return (
            f"{_number(quantity.get('lower_bound'))}–"
            f"{_number(quantity.get('upper_bound'))} {quantity.get('unit')}"
        )
    if kind == "ordinal":
        return str(quantity.get("level"))
    if kind == "indivisible":
        blocks = quantity.get("blocks", [])
        separator = "、" if language == "zh" else ", "
        return separator.join(str(item) for item in blocks)
    return "未记录" if language == "zh" else "not recorded"


def _allocations_text(
    allocations: Any,
    resource_labels: dict[str, str],
    language: str,
    *,
    empty: str,
) -> str:
    if not isinstance(allocations, list) or not allocations:
        return empty
    parts: list[str] = []
    for item in allocations:
        if not isinstance(item, dict):
            continue
        resource_id = str(item.get("resource_id", ""))
        label = resource_labels.get(resource_id, resource_id)
        parts.append(f"{label}: {_quantity_text(item.get('quantity'), language)}")
    separator = "；" if language == "zh" else "; "
    return separator.join(parts) if parts else empty


def _ledger_rows(
    decision: dict[str, Any], postures: set[str] | None = None
) -> list[dict[str, Any]]:
    rows = [
        item
        for item in decision.get("allocation_ledger", [])
        if isinstance(item, dict)
    ]
    if postures is not None:
        rows = [item for item in rows if item.get("posture") in postures]
    return rows


def _ledger_text(
    decision: dict[str, Any],
    candidate_labels: dict[str, str],
    resource_labels: dict[str, str],
    language: str,
    *,
    postures: set[str] | None = None,
    require_allocation: bool = False,
    empty: str,
) -> str:
    rows = _ledger_rows(decision, postures)
    if require_allocation:
        rows = [item for item in rows if item.get("current_allocations")]
    parts = []
    for item in rows:
        candidate_id = item.get("candidate_id", item.get("challenge_id", "none"))
        label = _candidate_label(candidate_id, candidate_labels, language)
        allocation_text = _allocations_text(
            item.get("current_allocations"),
            resource_labels,
            language,
            empty="零" if language == "zh" else "zero",
        )
        parts.append(f"{label} [{item.get('posture')}] — {allocation_text}")
    separator = "；" if language == "zh" else "; "
    return separator.join(parts) if parts else empty


def _items(values: Any, language: str, empty: str) -> str:
    if not isinstance(values, list) or not values:
        return empty
    separator = "；" if language == "zh" else "; "
    return separator.join(str(item) for item in values)


def _authorization_text(decision: dict[str, Any], language: str) -> str:
    outcome = decision.get("allocation_outcome")
    next_tranche = decision.get("next_tranche", {})
    start_condition = (
        next_tranche.get("start_condition") if isinstance(next_tranche, dict) else None
    )
    if outcome == "allocate":
        return str(start_condition or ("可立即开始" if language == "zh" else "may start now"))
    if outcome == "conditional" and start_condition:
        prefix = "满足条件后启动：" if language == "zh" else "start only after: "
        return prefix + str(start_condition)
    if outcome == "infeasible":
        return "无可执行分配" if language == "zh" else "no feasible allocation"
    return "当前未授权启动" if language == "zh" else "no action is authorized now"


def _bundle_text(
    decision: dict[str, Any],
    candidate_labels: dict[str, str],
    language: str,
) -> str:
    bundle_decision = decision.get("bundle_decision", {})
    if not isinstance(bundle_decision, dict):
        return "未记录" if language == "zh" else "not recorded"
    status = bundle_decision.get("status")
    if status in {"not_applicable", "not_assessed"}:
        return "不适用" if status == "not_applicable" and language == "zh" else (
            "未评估" if language == "zh" else str(status).replace("_", " ")
        )
    selected_id = bundle_decision.get("selected_bundle_id", "none")
    selected = next(
        (
            item
            for item in bundle_decision.get("bundle_assessments", [])
            if isinstance(item, dict) and item.get("bundle_id") == selected_id
        ),
        None,
    )
    if not isinstance(selected, dict):
        return "无" if language == "zh" else "none"
    members = [
        _candidate_label(item, candidate_labels, language)
        for item in selected.get("member_ids", [])
    ]
    separator = "、" if language == "zh" else ", "
    return (
        f"{selected_id}: {separator.join(members)} "
        f"[{selected.get('feasibility')}/{selected.get('dominance_status')}]"
    )


def _override_text(overrides: Any, language: str) -> str:
    if not isinstance(overrides, dict) or not overrides:
        return "无" if language == "zh" else "none"
    parts = []
    for key in sorted(overrides):
        value = overrides[key]
        if not isinstance(value, dict):
            continue
        if language == "zh":
            parts.append(
                f"{key}: {value.get('approved_by')} 批准；{value.get('override_reason')}；"
                f"风险范围：{value.get('risk_acceptance_scope')}；到期：{value.get('expiry')}"
            )
        else:
            parts.append(
                f"{key}: approved by {value.get('approved_by')}; "
                f"{value.get('override_reason')}; risk scope: "
                f"{value.get('risk_acceptance_scope')}; expiry: {value.get('expiry')}"
            )
    separator = "；" if language == "zh" else "; "
    return separator.join(parts) if parts else ("无" if language == "zh" else "none")


def _render(
    final: dict[str, Any],
    candidate_labels: dict[str, str],
    resource_labels: dict[str, str],
    language: str,
) -> str:
    decision = final["decision"]
    next_tranche = decision.get("next_tranche", {})
    if not isinstance(next_tranche, dict):
        next_tranche = {}
    reserve = decision.get("reserve", {})
    if not isinstance(reserve, dict):
        reserve = {}
    is_zh = language == "zh"
    none = "无" if is_zh else "none"
    reserve_text = none
    if reserve.get("status") == "reserved":
        reserve_text = (
            f"{_allocations_text(reserve.get('resource_allocations'), resource_labels, language, empty=none)}; "
            f"{reserve.get('reason')}; "
            f"{'释放条件' if is_zh else 'release'}: {reserve.get('release_trigger')}; "
            f"{'复核' if is_zh else 'review'}: {reserve.get('review_time')}"
        )
    labels = {
        "title": "SRA 决策" if is_zh else "SRA Decision",
        "runtime": "运行状态" if is_zh else "Runtime status",
        "bundle": "选中组合" if is_zh else "Selected bundle",
        "floor": "当前底座" if is_zh else "Current floor",
        "next_target": "下一投入对象" if is_zh else "Next target",
        "next": "下一投入批次" if is_zh else "Next tranche",
        "signal": "完成信号" if is_zh else "Completion signal",
        "start": "授权状态" if is_zh else "Authorization state",
        "why": "判断理由" if is_zh else "Why",
        "ceiling": "投入上限" if is_zh else "Investment ceiling",
        "horizon": "授权边界" if is_zh else "Authorization horizon",
        "maintenance": "最低维护" if is_zh else "Maintenance",
        "reserve": "机动资源" if is_zh else "Reserve",
        "defer": "明确延后" if is_zh else "Defer",
        "stop": "明确停止" if is_zh else "Stop",
        "rerank": "重排触发" if is_zh else "Rerank triggers",
        "missing": "缺失信息" if is_zh else "Missing information",
        "overrides": "治理覆盖" if is_zh else "Governance overrides",
        "source": "最终来源" if is_zh else "Final source",
        "view": "判断视角" if is_zh else "View plan",
        "context": "上下文边界" if is_zh else "Context boundary",
        "claim": "证据上限" if is_zh else "Claim ceiling",
    }
    return "\n".join(
        [
            f"# {labels['title']}：{decision.get('allocation_outcome', '未记录' if is_zh else 'not recorded')}",
            "",
            f"- {labels['runtime']}：{final.get('finalization_status', none)}",
            f"- {labels['bundle']}：{_bundle_text(decision, candidate_labels, language)}",
            f"- {labels['floor']}：{_ledger_text(decision, candidate_labels, resource_labels, language, require_allocation=True, empty=none)}",
            f"- {labels['next_target']}：{_candidate_label(next_tranche.get('target_id', 'none'), candidate_labels, language)}",
            f"- {labels['next']}：{_allocations_text(next_tranche.get('resource_allocations'), resource_labels, language, empty=none)}",
            f"- {labels['signal']}：{next_tranche.get('completion_signal', none)}",
            f"- {labels['start']}：{_authorization_text(decision, language)}",
            f"- {labels['why']}：{next_tranche.get('reason', none)}",
            f"- {labels['ceiling']}：{_allocations_text(decision.get('investment_ceiling'), resource_labels, language, empty=none)}",
            f"- {labels['horizon']}：{decision.get('authorization_horizon', none)}",
            f"- {labels['maintenance']}：{_ledger_text(decision, candidate_labels, resource_labels, language, postures={'maintenance'}, empty=none)}",
            f"- {labels['reserve']}：{reserve_text}",
            f"- {labels['defer']}：{_ledger_text(decision, candidate_labels, resource_labels, language, postures={'defer'}, empty=none)}",
            f"- {labels['stop']}：{_ledger_text(decision, candidate_labels, resource_labels, language, postures={'stop'}, empty=none)}",
            f"- {labels['rerank']}：{_items(decision.get('rerank_triggers'), language, none)}",
            f"- {labels['missing']}：{_items(decision.get('missing_information'), language, none)}",
            f"- {labels['overrides']}：{_override_text(final.get('governance_overrides'), language)}",
            f"- {labels['source']}：{final.get('final_source', none)}",
            f"- {labels['view']}：{final.get('view_plan', none)}",
            f"- {labels['context']}：{final.get('observed_context_boundary', none)}",
            f"- {labels['claim']}：{decision.get('claim_ceiling', none)}",
            "",
        ]
    )


def _render_card(final: dict[str, Any], raw: dict[str, Any], language: str) -> str:
    """Project one checked decision; never decide or hide authorization boundaries."""
    zh = language == "zh"
    label = lambda cn, en: cn if zh else en
    decision = final["decision"]
    frame = raw["allocation_frame"]
    candidate_labels, resource_labels = _candidate_labels(raw), _resource_labels(raw)
    next_tranche = decision["next_tranche"]
    none = label("无", "none")
    allocations = lambda values: _allocations_text(values, resource_labels, language, empty=none)
    outcome = decision["allocation_outcome"]
    ledger_summary = []
    for title, postures in ((label('当前已分配', 'Current commitments'), {'floor', 'maintenance'}),
                            (label('延后', 'Deferred'), {'defer'}), (label('停止', 'Stopped'), {'stop'})):
        if _ledger_rows(decision, postures):
            ledger_summary.append(f"{title}：{_ledger_text(decision, candidate_labels, resource_labels, language, postures=postures, empty=none)}")
    if decision.get('bundle_decision', {}).get('status') == 'assessed':
        ledger_summary.insert(0, f"{label('选中组合', 'Selected bundle')}：{_bundle_text(decision, candidate_labels, language)}")
    constraints = [c['statement'] for c in raw.get('context_items', []) if c.get('kind') in {'user_constraint', 'authority_decision'}]
    status = {
        "allocate": label("本轮投入", "Current allocation"),
        "conditional": label("有条件计划，当前未授权启动", "Conditional plan; no start now"),
        "infeasible": label("当前资源下不可行", "Infeasible under current resources"),
        "blocked": label("已阻断，当前未授权启动", "Blocked; no start authorized"),
        "request_missing_context": label("需补信息，当前未授权启动", "Missing context; no start authorized"),
    }[outcome]
    lines = [
        f"# SRA — {status}", "",
        f"**{label('目标', 'Objective')}**：{frame['parent_objective']}",
        f"{label('达标条件', 'Threshold')}：{frame['target_threshold']}",
        f"{label('保护底线', 'Protected boundary')}：{frame['risk_floor']}",
        *([f"{label('当前约束', 'Current constraints')}：{_items(constraints, language, none)}"] if constraints else []), "",
        f"## {label('当前决定', 'Decision')}",
        f"{_candidate_label(next_tranche['target_id'], candidate_labels, language)} — {allocations(next_tranche['resource_allocations'])}",
        f"{label('判断理由', 'Why')}：{next_tranche['reason']}",
        *ledger_summary, "",
        f"## {label('执行边界', 'Execution boundary')}",
        f"{label('授权状态', 'Authorization')}：{_authorization_text(decision, language)}",
        f"{label('本轮窗口', 'Decision window')}：{frame['time_window']}",
        f"{label('下一批窗口', 'Tranche window')}：{next_tranche['window']}",
        f"{label('投入上限', 'Investment ceiling')}：{allocations(decision['investment_ceiling'])}",
        f"{label('授权边界', 'Authorization horizon')}：{decision['authorization_horizon']}",
        f"{label('完成条件', 'Completion')}：{next_tranche.get('completion_signal', none)}",
    ]
    used_resources = {r['resource_id'] for row in decision['allocation_ledger'] for r in row['current_allocations']}
    used_resources.update(r['resource_id'] for r in next_tranche['resource_allocations'])
    reserve = decision['reserve']
    used_resources.update(r['resource_id'] for r in reserve['resource_allocations'])
    for pool in frame['resource_pools']:
        if pool['resource_id'] in used_resources:
            lines.append(f"{label('资源窗口', 'Resource window')} {pool['resource_id']}：{pool['window']}")
    for resolution in decision.get('dependency_resolutions', []):
        dependent = _candidate_label(resolution['dependent_id'], candidate_labels, language)
        prerequisite = _candidate_label(resolution['prerequisite_id'], candidate_labels, language)
        lines.append(f"{label('前置', 'Prerequisite')} {dependent} ← {prerequisite}：{resolution['status']} [{', '.join(resolution['evidence_refs'])}]")
    if reserve['status'] == 'reserved':
        lines.append(f"{label('保留资源', 'Reserve')}：{allocations(reserve['resource_allocations'])}；{reserve['reason']}；{reserve['release_trigger']}；{reserve['review_time']}")
    if final.get('governance_overrides'):
        lines.append(f"{label('降级授权', 'Governance override')}：{_override_text(final['governance_overrides'], language)}")
    lines.extend([
        "", f"## {label('重新判断', 'Reconsider')}",
        _items(decision.get('rerank_triggers'), language, none),
    ])
    if decision.get('missing_information'):
        lines.append(f"**{label('尚缺', 'Missing')}**：{_items(decision['missing_information'], language, none)}")
    lines.extend([
        "", f"{label('证据上限', 'Claim ceiling')}：{decision.get('claim_ceiling', frame['evidence_ceiling'])}",
        f"{label('判断视角', 'View plan')}：{final['view_plan']} / {final['observed_context_boundary']}",
        f"{label('详情', 'Details')}：run `{final['run_id']}` / `final-decision.json`；`--view full`",
        label("SRA 分配结论不替代实际执行权限。", "An SRA allocation does not replace execution authority."), "",
    ])
    return '\n'.join(lines)


def render(run_dir: Path, language: str, view: str = "full") -> tuple[dict[str, Any], str]:
    report = run_check(run_dir)
    blocking = [
        item["message"]
        for item in report.get("findings", [])
        if item.get("severity") == "block"
    ]
    if blocking:
        raise SraRuntimeError("run integrity failed: " + "; ".join(blocking))
    final_path = run_dir / "final-decision.json"
    if not final_path.is_file():
        raise SraRuntimeError(f"terminal decision does not exist: {final_path}")
    final = load_json(final_path)
    if not isinstance(final, dict) or final.get("schema_version") != FINAL_DECISION_SCHEMA:
        raise SraRuntimeError(f"invalid terminal decision: {final_path}")
    if not isinstance(final.get("decision"), dict):
        raise SraRuntimeError("terminal decision has no decision object")
    raw = _raw_input(run_dir)
    if view not in {"card", "full"}:
        raise SraRuntimeError("unsupported result view")
    display = copy.deepcopy(final)
    if "completion_criterion_ref" in display["decision"]["next_tranche"]:
        display["decision"]["next_tranche"]["completion_signal"] = resolved_completion(final["decision"], raw)
    text = _render_card(display, raw, language) if view == "card" else _render(
        display, _candidate_labels(raw), _resource_labels(raw), language,
    )
    return final, text


def main() -> int:
    args = parse_args()
    try:
        run_dir = Path(args.dir)
        view = args.view or ("card" if "execution_policy" in _raw_input(run_dir) else "full")
        final, text = render(run_dir, args.language, view)
    except SraRuntimeError as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(final, ensure_ascii=False, indent=2))
    elif args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"rendered: {output_path}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
