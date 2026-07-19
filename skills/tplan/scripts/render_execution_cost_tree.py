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
        default=3,
        help="Compact only: include this many highest direct-cost real nodes (default: 3).",
    )
    parser.add_argument("--output", help="Write atomically to this path instead of stdout.")
    parser.add_argument(
        "--completion-handoff",
        action="store_true",
        help=(
            "Write the default Standard report and SVG under reports/, then print the "
            "Markdown links that must be included in the terminal user handoff."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        mission_dir = Path(args.mission_dir).resolve()
        if args.completion_handoff:
            if args.output or args.focus or args.view != "standard" or args.format != "markdown":
                raise TplanError(
                    "--completion-handoff requires the default Standard Markdown full-Mission view"
                )
            args.output = str(mission_dir / "reports" / "execution-cost-tree.md")
        report = build_execution_cost_tree(
            mission_dir,
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
            if args.completion_handoff:
                print("TPlan terminal handoff links (include both in the final user response):")
                print(f"- [TPlan 执行报告](<{output_path.resolve()}>)")
                print(f"- [TPlan 执行过程图](<{svg_path.resolve()}>)")
        else:
            print(rendered, end="")
        return 0
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
