#!/usr/bin/env python3
"""Render a finalized SRA decision without recomputing allocation semantics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sra_runtime import FINAL_DECISION_SCHEMA, SraRuntimeError, load_json, run_check


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a finalized SRA decision.")
    parser.add_argument("--dir", required=True, help="Finalized SRA run directory.")
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--output", help="Optional Markdown output path.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def _candidate_labels(run_dir: Path) -> dict[str, str]:
    raw = load_json(run_dir / "raw-input.json")
    return {
        str(item["candidate_id"]): str(item.get("action_statement", item["candidate_id"]))
        for item in raw.get("candidates", [])
        if isinstance(item, dict) and "candidate_id" in item
    }


def _label(value: Any, labels: dict[str, str]) -> str:
    text = str(value)
    if text in {"none", "reserve"}:
        return {"none": "无", "reserve": "保留资源"}[text]
    return labels.get(text, text)


def _items(values: Any, labels: dict[str, str], empty: str) -> str:
    if not isinstance(values, list) or not values:
        return empty
    return "；".join(_label(item, labels) for item in values)


def _render_zh(final: dict[str, Any], labels: dict[str, str]) -> str:
    decision = final["decision"]
    next_tranche = decision.get("next_tranche", {})
    candidate_id = next_tranche.get("candidate_id", next_tranche.get("challenge_id", "none"))
    reserve = decision.get("reserve", {})
    reserve_text = "无"
    if reserve.get("status") == "reserved":
        reserve_candidate = reserve.get("candidate_id", reserve.get("challenge_id", "none"))
        reserve_text = (
            f"{_label(reserve_candidate, labels)}；{reserve.get('reason')}；"
            f"释放条件：{reserve.get('release_trigger')}；复核：{reserve.get('review_time')}"
        )
    missing = decision.get("missing_information", [])
    return "\n".join(
        [
            f"# SRA 决策：{decision.get('allocation_outcome', '未记录')}",
            "",
            f"- 当前底座：{_items(decision.get('current_floor'), labels, '无')}",
            f"- 下一投入对象：{_label(candidate_id, labels)}",
            f"- 下一投入批次：{next_tranche.get('description', '未记录')}",
            f"- 判断理由：{next_tranche.get('reason', '未记录')}",
            f"- 投入上限：{decision.get('investment_ceiling', '未记录')}",
            f"- 授权边界：{decision.get('authorization_horizon', '未记录')}",
            f"- 最低维护：{_items(decision.get('maintenance'), labels, '无')}",
            f"- 机动资源：{reserve_text}",
            f"- 明确延后：{_items(decision.get('defer'), labels, '无')}",
            f"- 明确停止：{_items(decision.get('stop'), labels, '无')}",
            f"- 重排触发：{_items(decision.get('rerank_triggers'), {}, '未记录')}",
            f"- 缺失信息：{_items(missing, {}, '无')}",
            f"- 最终来源：{final.get('final_source', '未记录')}",
            f"- 判断视角：{final.get('view_plan', '未记录')}",
            f"- 上下文边界：{final.get('observed_context_boundary', '未记录')}",
            f"- 证据上限：{decision.get('claim_ceiling', '未记录')}",
            "",
        ]
    )


def _render_en(final: dict[str, Any], labels: dict[str, str]) -> str:
    decision = final["decision"]
    next_tranche = decision.get("next_tranche", {})
    candidate_id = next_tranche.get("candidate_id", next_tranche.get("challenge_id", "none"))
    return "\n".join(
        [
            f"# SRA Decision: {decision.get('allocation_outcome', 'not recorded')}",
            "",
            f"- Current floor: {_items(decision.get('current_floor'), labels, 'none')}",
            f"- Next target: {_label(candidate_id, labels)}",
            f"- Next tranche: {next_tranche.get('description', 'not recorded')}",
            f"- Why: {next_tranche.get('reason', 'not recorded')}",
            f"- Investment ceiling: {decision.get('investment_ceiling', 'not recorded')}",
            f"- Authorization horizon: {decision.get('authorization_horizon', 'not recorded')}",
            f"- Maintenance: {_items(decision.get('maintenance'), labels, 'none')}",
            f"- Defer: {_items(decision.get('defer'), labels, 'none')}",
            f"- Stop: {_items(decision.get('stop'), labels, 'none')}",
            f"- Rerank triggers: {_items(decision.get('rerank_triggers'), {}, 'not recorded')}",
            f"- Final source: {final.get('final_source', 'not recorded')}",
            f"- View plan: {final.get('view_plan', 'not recorded')}",
            f"- Context boundary: {final.get('observed_context_boundary', 'not recorded')}",
            f"- Claim ceiling: {decision.get('claim_ceiling', 'not recorded')}",
            "",
        ]
    )


def render(run_dir: Path, language: str) -> tuple[dict[str, Any], str]:
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
        raise SraRuntimeError(f"final decision does not exist: {final_path}")
    final = load_json(final_path)
    if not isinstance(final, dict) or final.get("schema_version") != FINAL_DECISION_SCHEMA:
        raise SraRuntimeError(f"invalid finalized decision: {final_path}")
    if not isinstance(final.get("decision"), dict):
        raise SraRuntimeError("final decision has no decision object")
    labels = _candidate_labels(run_dir)
    text = _render_zh(final, labels) if language == "zh" else _render_en(final, labels)
    return final, text


def main() -> int:
    args = parse_args()
    try:
        final, text = render(Path(args.dir), args.language)
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
