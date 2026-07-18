#!/usr/bin/env python3
"""Render a progressive actual-execution and cost tree from a TPlan Mission runtime."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from execution_cost_tree import build_execution_cost_tree, render_json, render_markdown
from tplan_runtime import TplanError, write_text_atomic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a tplan actual-execution and cost tree.")
    parser.add_argument("mission_dir")
    parser.add_argument("--view", choices=("compact", "standard", "audit"), default="standard")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--focus", help="Render only this task subtree.")
    parser.add_argument("--top-cost", type=int, default=5, help="High-cost descendants retained in standard view.")
    parser.add_argument("--output", help="Write atomically to this path instead of stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_execution_cost_tree(
            Path(args.mission_dir),
            view=args.view,
            focus_task_id=args.focus,
            top_cost=args.top_cost,
        )
        rendered = render_markdown(report) if args.format == "markdown" else render_json(report)
        if args.output:
            output_path = Path(args.output)
            write_text_atomic(output_path, rendered)
            print(f"rendered_execution_cost_tree: {output_path}")
        else:
            print(rendered, end="")
        return 0
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
