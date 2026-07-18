#!/usr/bin/env python3
"""Render an actual-execution and cost tree from a TPlan Mission runtime."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from execution_cost_tree import (
    build_execution_cost_tree,
    render_compact_text,
    render_json,
    render_markdown,
    render_svg,
)
from tplan_runtime import TplanError, write_text_atomic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a tplan actual-execution and cost tree.")
    parser.add_argument("mission_dir")
    parser.add_argument("--view", choices=("compact", "standard", "audit"), default="standard")
    parser.add_argument("--format", choices=("markdown", "text", "svg", "json"), default="markdown")
    parser.add_argument("--focus", help="Render only this task subtree.")
    parser.add_argument(
        "--top-cost",
        type=int,
        default=5,
        help="Compact only: include this many highest direct-cost real nodes (default: 5).",
    )
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
        if args.format == "text":
            rendered = render_compact_text(report)
        elif args.format == "svg":
            rendered = render_svg(report)
        elif args.format == "json":
            rendered = render_json(report)
        else:
            rendered = render_markdown(report)
        if args.output:
            output_path = Path(args.output)
            if args.format == "markdown" and args.view != "compact":
                svg_path = output_path.with_suffix(".svg")
                rendered = render_markdown(report, timeline_svg_ref=svg_path.name)
                write_text_atomic(svg_path, render_svg(report))
            write_text_atomic(output_path, rendered)
            print(f"rendered_execution_cost_tree: {output_path}")
            if args.format == "markdown" and args.view != "compact":
                print(f"rendered_execution_cost_tree_svg: {svg_path}")
        else:
            print(rendered, end="")
        return 0
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
