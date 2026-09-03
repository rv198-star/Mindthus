#!/usr/bin/env python3
"""Render a finalized SRA decision without recomputing allocation semantics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sra_runtime import SraRuntimeError, load_json, run_check


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a finalized SRA decision in concise Chinese or English."
    )
    parser.add_argument("--dir", required=True, help="Finalized SRA run directory.")
    parser.add_argument("--language", choices=("zh", "en"), default="zh")
    parser.add_argument("--output", help="Optional output Markdown path.")
    parser.add_argument("--json", action="store_true", help="Emit normalized JSON instead.")
    return parser.parse_args()


def _items(values: Any, empty: str, separator: str = "；") -> str:
    if not isinstance(values, list) or not values:
        return empty
    return separator.join(str(item) for item in values)


def _render_zh(final: dict[str, Any]) -> str:
    decision = final["decision"]
    reserve = decision.get("reserve", {})
    reserve_text = "无"
    if reserve.get("status") == "reserved":
        reserve_text = (
            f"{reserve.get('reason')}；释放条件：{reserve.get('release_trigger')}；"
            f"复核时间：{reserve.get('review_time')}"
        )
    next_tranche = decision.get("next_tranche", {})
    return "\n".join(
        [
            f"# SRA 决策：{decision.get('decision')}",
            "",
            f"- 当前底座：{_items(decision.get('current_floor'), '未记录')}",
            f"- 下一投入批次：{next_tranche.get('description', '未记录')}",
            f"- 为什么：{next_tranche.get('reason', '未记录')}",
            f"- 投入上限：{decision.get('investment_ceiling', '未记录')}",
            f"- 授权边界：{decision.get('authorization_horizon', '未记录')}",
            f"- 最低维护：{_items(decision.get('maintenance'), '无')}",
            f"- 机动资源：{reserve_text}",
            f"- 明确延后：{_items(decision.get('defer'), '无')}",
            f"- 明确停止：{_items(decision.get('stop'), '无')}",
            f"- 重排触发：{_items(decision.get('rerank_triggers'), '未记录')}",
            f"- 盲评结论是否被状态信息改变：{'是' if decision.get('blind_result_changed') else '否'}",
            f"- 调整理由：{decision.get('change_reason', '未记录')}",
            f"- 隔离口径：{final.get('effective_isolation_claim', '未记录')}",
            f"- 证据上限：{decision.get('claim_ceiling', '未记录')}",
            "",
        ]
    )


def _render_en(final: dict[str, Any]) -> str:
    decision = final["decision"]
    reserve = decision.get("reserve", {})
    reserve_text = "none"
    if reserve.get("status") == "reserved":
        reserve_text = (
            f"{reserve.get('reason')}; release: {reserve.get('release_trigger')}; "
            f"review: {reserve.get('review_time')}"
        )
    next_tranche = decision.get("next_tranche", {})
    return "\n".join(
        [
            f"# SRA Decision: {decision.get('decision')}",
            "",
            f"- Current floor: {_items(decision.get('current_floor'), 'not recorded', '; ')}",
            f"- Next tranche: {next_tranche.get('description', 'not recorded')}",
            f"- Why: {next_tranche.get('reason', 'not recorded')}",
            f"- Investment ceiling: {decision.get('investment_ceiling', 'not recorded')}",
            f"- Authorization horizon: {decision.get('authorization_horizon', 'not recorded')}",
            f"- Maintenance: {_items(decision.get('maintenance'), 'none', '; ')}",
            f"- Reserve: {reserve_text}",
            f"- Defer: {_items(decision.get('defer'), 'none', '; ')}",
            f"- Stop: {_items(decision.get('stop'), 'none', '; ')}",
            f"- Rerank triggers: {_items(decision.get('rerank_triggers'), 'not recorded', '; ')}",
            f"- Blind result changed: {decision.get('blind_result_changed')}",
            f"- Adjustment reason: {decision.get('change_reason', 'not recorded')}",
            f"- Isolation claim: {final.get('effective_isolation_claim', 'not recorded')}",
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
        raise SraRuntimeError(f"finalized decision does not exist: {final_path}")
    final = load_json(final_path)
    if not isinstance(final, dict) or final.get("schema_version") != "sra.final-decision.v0.1":
        raise SraRuntimeError(f"invalid finalized decision: {final_path}")
    decision = final.get("decision")
    if not isinstance(decision, dict):
        raise SraRuntimeError("final decision has no state-aware judgment object")
    text = _render_zh(final) if language == "zh" else _render_en(final)
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
        return 0
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"rendered: {output_path}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
