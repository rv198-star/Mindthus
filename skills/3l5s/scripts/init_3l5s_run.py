#!/usr/bin/env python3
"""Create a 3L5S working draft from a local template."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


TEMPLATE_BY_MODE = {
    "single-layer": "single-layer-btgsb.md",
    "three-layer": "three-layer-3l5s.md",
    "loopback": "loopback-record.md",
}


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def render_template(template_name: str, title: str, date: str) -> str:
    template_path = skill_root() / "templates" / template_name
    text = template_path.read_text(encoding="utf-8")
    return text.replace("{{title}}", title).replace("{{date}}", date)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a 3L5S markdown draft. This does not judge the problem."
    )
    parser.add_argument(
        "--mode",
        choices=sorted(TEMPLATE_BY_MODE),
        required=True,
        help="Draft type to generate.",
    )
    parser.add_argument("--title", required=True, help="Draft title.")
    parser.add_argument(
        "--date",
        default=dt.date.today().isoformat(),
        help="Draft date, default: today.",
    )
    parser.add_argument(
        "--output",
        help="Output markdown path. If omitted, print to stdout.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rendered = render_template(TEMPLATE_BY_MODE[args.mode], args.title, args.date)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"created: {output_path}")
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
