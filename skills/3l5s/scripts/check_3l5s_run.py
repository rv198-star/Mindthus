#!/usr/bin/env python3
"""Produce a 3L5S Shape & Evidence Risk Report for a markdown draft."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


STEPS = ("Baseline", "Target", "Gap", "Strategy", "Breakdown")
LAYERS = ("Discovery", "Definition", "Resolution")

VAGUE_VERBS = (
    "optimize",
    "improve",
    "handle",
    "research",
    "follow up",
    "think about",
    "process",
    "fix stuff",
    "优化",
    "改进",
    "处理",
    "研究",
    "跟进",
    "完善",
    "梳理",
    "推进",
)

EVIDENCE_PATTERN = re.compile(
    r"evidence|acceptance|accepted|done when|artifact|changed state|proof|"
    r"证据|验收|产物|完成标准|可验证|观察|日志|测试|文件",
    re.IGNORECASE,
)
STRATEGY_REASON_PATTERN = re.compile(
    r"why|because|trade-?off|alternative|reject|choose|chosen|"
    r"为什么|因为|取舍|替代|放弃|选择|权衡",
    re.IGNORECASE,
)
DEFINITION_PATTERN = re.compile(
    r"falsif|measure|metric|scope|impact|cause|证伪|衡量|测量|范围|影响|原因",
    re.IGNORECASE,
)
SOLUTION_PATTERN = re.compile(
    r"\bfix\b|\bimplement\b|\bship\b|\bdeploy\b|solution|解决|修复|实现|上线|交付"
)


@dataclass
class Finding:
    level: str
    code: str
    message: str


def heading_block(text: str, heading_name: str, level: int) -> str:
    hashes = "#" * level
    pattern = re.compile(
        rf"(?ms)^{hashes}\s+[^\n]*{re.escape(heading_name)}[^\n]*\n"
        rf"(?P<body>.*?)(?=^#{{1,{level}}}\s+|\Z)"
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group("body")


def has_heading(text: str, heading_name: str) -> bool:
    return bool(re.search(rf"(?mi)^#+\s+.*{re.escape(heading_name)}\b", text))


def placeholder_like(block: str) -> bool:
    stripped = re.sub(r"[\s#:\-/`>*]+", "", block)
    return not stripped or "待填写" in block or "TODO" in block or "TBD" in block


def task_lines(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line)
    ]


def detect_mode(text: str) -> str:
    if "Mode: three-layer" in text or all(has_heading(text, layer) for layer in LAYERS):
        return "three-layer"
    if "Mode: single-layer" in text:
        return "single-layer"
    if "Loopback Record" in text or "Loopback Target" in text:
        return "loopback"
    return "unknown"


def check_required_steps(text: str, findings: list[Finding]) -> None:
    for step in STEPS:
        if not has_heading(text, step):
            findings.append(
                Finding("risk", "missing-step", f"Missing step heading: {step}.")
            )


def check_three_layer(text: str, findings: list[Finding]) -> None:
    for layer in LAYERS:
        layer_block = heading_block(text, layer, 2)
        if not layer_block:
            findings.append(
                Finding("risk", "missing-layer", f"Missing layer heading: {layer}.")
            )
            continue

        for step in STEPS:
            if not has_heading(layer_block, step):
                findings.append(
                    Finding(
                        "risk",
                        "missing-layer-step",
                        f"{layer} is missing step heading: {step}.",
                    )
                )

        if layer == "Discovery" and SOLUTION_PATTERN.search(layer_block):
            findings.append(
                Finding(
                    "warn",
                    "possible-layer-collapse",
                    "Discovery contains solution/action language; check whether signal and solution were collapsed.",
                )
            )
        if layer == "Definition" and not DEFINITION_PATTERN.search(layer_block):
            findings.append(
                Finding(
                    "warn",
                    "definition-thin",
                    "Definition lacks falsification, measurement, scope, cause, or impact language.",
                )
            )
        if layer == "Resolution" and not EVIDENCE_PATTERN.search(layer_block):
            findings.append(
                Finding(
                    "warn",
                    "resolution-evidence-thin",
                    "Resolution lacks visible acceptance or evidence language.",
                )
            )


def check_placeholders(text: str, findings: list[Finding]) -> None:
    if "待填写" in text or "TODO" in text or "TBD" in text:
        findings.append(
            Finding(
                "info",
                "placeholder-present",
                "Draft still contains placeholder language.",
            )
        )

    for step in STEPS:
        block = heading_block(text, step, 2) or heading_block(text, step, 3)
        if block and placeholder_like(block):
            findings.append(
                Finding(
                    "warn",
                    "step-placeholder",
                    f"{step} appears empty or placeholder-only.",
                )
            )


def check_vague_actions(text: str, findings: list[Finding]) -> None:
    vague_pattern = re.compile("|".join(re.escape(v) for v in VAGUE_VERBS), re.IGNORECASE)
    for line in task_lines(text):
        if vague_pattern.search(line):
            findings.append(
                Finding(
                    "warn",
                    "vague-action",
                    f"Vague action language may need another BTGSB loop: {line}",
                )
            )


def check_evidence_and_strategy(text: str, findings: list[Finding]) -> None:
    if not EVIDENCE_PATTERN.search(text):
        findings.append(
            Finding(
                "risk",
                "missing-evidence-surface",
                "No evidence or acceptance surface detected.",
            )
        )

    strategy_blocks = [
        block
        for block in (
            heading_block(text, "Strategy", 2),
            heading_block(text, "Strategy", 3),
        )
        if block
    ]
    if strategy_blocks and not any(
        STRATEGY_REASON_PATTERN.search(block) for block in strategy_blocks
    ):
        findings.append(
            Finding(
                "warn",
                "strategy-reason-thin",
                "Strategy is present but lacks visible reason, trade-off, or rejected alternatives.",
            )
        )


def check_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    findings: list[Finding] = []
    mode = detect_mode(text)

    if mode == "three-layer":
        check_three_layer(text, findings)
    elif mode == "single-layer":
        check_required_steps(text, findings)
    elif mode == "loopback":
        for heading in ("Trigger", "Previous Claim", "New Evidence", "Loopback Target", "Next Action"):
            if not has_heading(text, heading):
                findings.append(
                    Finding("risk", "missing-loopback-field", f"Missing loopback field: {heading}.")
                )
    else:
        findings.append(
            Finding(
                "warn",
                "mode-unknown",
                "Could not detect single-layer, three-layer, or loopback mode.",
            )
        )
        check_required_steps(text, findings)

    check_placeholders(text, findings)
    check_vague_actions(text, findings)
    check_evidence_and_strategy(text, findings)

    return {
        "path": str(path),
        "mode": mode,
        "report_name": "3L5S Shape & Evidence Risk Report",
        "findings": [asdict(f) for f in findings],
    }


def print_text_report(report: dict) -> None:
    print("3L5S Shape & Evidence Risk Report")
    print(f"Path: {report['path']}")
    print(f"Mode: {report['mode']}")
    print()

    findings = report["findings"]
    if not findings:
        print("No obvious shape or evidence risks detected.")
        print("This is not proof that the judgment is correct.")
        return

    for finding in findings:
        print(f"- {finding['level'].upper()} [{finding['code']}]: {finding['message']}")

    print()
    print("Reminder: this report exposes review risks; it does not validate truth.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check 3L5S markdown shape and evidence risks. This does not judge truth."
    )
    parser.add_argument("path", help="Markdown draft to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = check_file(Path(args.path))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
