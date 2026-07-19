#!/usr/bin/env python3
"""Add deterministic candidate IDs and optional parent lineage to an image atlas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_BOUNDARY = "support_only_agentic_audit_required"
LAYOUTS = {"2x2": (2, 2), "3x3": (3, 3)}
PREFIX_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,23}$")


class AtlasLabelError(ValueError):
    """Raised when deterministic atlas labeling cannot proceed."""


def _pillow() -> tuple[Any, Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise AtlasLabelError("Pillow is required; install scripts/atlas/requirements.txt") from exc
    return Image, ImageDraw, ImageFont, ImageOps


def _load_font(size: int) -> Any:
    _, _, ImageFont, _ = _pillow()
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size=size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


def _draw_label(
    image: Any,
    label: str,
    parent_text: str | None,
    x: int,
    y: int,
    edge: int,
    font_size: int | None,
) -> None:
    _, ImageDraw, _, _ = _pillow()
    resolved_size = font_size or max(18, round(edge * 0.055))
    font = _load_font(resolved_size)
    lineage_font = _load_font(max(10, round(resolved_size * 0.58)))
    padding_x = max(10, round(resolved_size * 0.55))
    padding_y = max(7, round(resolved_size * 0.35))
    margin = max(10, round(edge * 0.025))
    draw = ImageDraw.Draw(image, "RGBA")
    left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
    label_width = right - left
    label_height = bottom - top
    lineage_width = 0
    lineage_height = 0
    if parent_text:
        p_left, p_top, p_right, p_bottom = draw.textbbox((0, 0), parent_text, font=lineage_font)
        lineage_width = p_right - p_left
        lineage_height = p_bottom - p_top
    box = (
        x + margin,
        y + margin,
        x + margin + max(label_width, lineage_width) + padding_x * 2,
        y + margin + label_height + lineage_height + padding_y * (3 if parent_text else 2),
    )
    draw.rounded_rectangle(
        box, radius=max(6, round(resolved_size * 0.3)), fill=(12, 12, 12, 210)
    )
    draw.text(
        (box[0] + padding_x - left, box[1] + padding_y - top),
        label,
        font=font,
        fill=(255, 255, 255, 255),
    )
    if parent_text:
        draw.text(
            (box[0] + padding_x, box[1] + padding_y * 2 + label_height),
            parent_text,
            font=lineage_font,
            fill=(190, 222, 210, 255),
        )


def _load_lineage(path: Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AtlasLabelError(f"cannot read lineage JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise AtlasLabelError("lineage JSON must be an object mapping candidate IDs to parent IDs")
    lineage: dict[str, list[str]] = {}
    for candidate_id, parents in payload.items():
        if isinstance(parents, str) and parents.strip():
            lineage[candidate_id] = [parents]
        elif isinstance(parents, list) and parents and all(isinstance(item, str) and item.strip() for item in parents):
            lineage[candidate_id] = parents
        elif parents is not None:
            raise AtlasLabelError(f"invalid lineage value for {candidate_id!r}")
    return lineage


def label_atlas(
    source: Path,
    output: Path,
    layout: str,
    id_prefix: str,
    font_size: int | None,
    lineage: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    if layout not in LAYOUTS:
        raise AtlasLabelError(f"unsupported layout {layout!r}")
    if not PREFIX_PATTERN.fullmatch(id_prefix):
        raise AtlasLabelError(
            "id prefix must start with a letter and use at most 24 letters, numbers, '_' or '-'"
        )
    if font_size is not None and font_size <= 0:
        raise AtlasLabelError("font size must be positive")
    if not source.is_file():
        raise AtlasLabelError(f"input image not found: {source}")

    Image, _, _, ImageOps = _pillow()
    try:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGBA")
    except (OSError, ValueError) as exc:
        raise AtlasLabelError(f"cannot read atlas: {exc}") from exc

    columns, rows = LAYOUTS[layout]
    lineage = lineage or {}
    regions: list[dict[str, Any]] = []
    for index in range(columns * rows):
        column = index % columns
        row = index // columns
        x0 = image.width * column // columns
        x1 = image.width * (column + 1) // columns
        y0 = image.height * row // rows
        y1 = image.height * (row + 1) // rows
        candidate_id = f"{id_prefix}{index + 1:02d}"
        parents = lineage.get(candidate_id, [])
        parent_text = f"from {' + '.join(parents)}" if parents else None
        _draw_label(image, candidate_id, parent_text, x0, y0, min(x1 - x0, y1 - y0), font_size)
        regions.append(
            {
                "id": candidate_id,
                "row": row + 1,
                "column": column + 1,
                "pixel_box": [x0, y0, x1, y1],
                "parent_candidate_ids": parents,
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        image.convert("RGB").save(output, format="PNG")
    except OSError as exc:
        raise AtlasLabelError(f"cannot write labeled atlas: {exc}") from exc
    return regions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Label equal atlas regions and optional parent lineage without judging image quality."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layout", choices=sorted(LAYOUTS), required=True)
    parser.add_argument("--id-prefix", required=True)
    parser.add_argument("--lineage-json", type=Path)
    parser.add_argument("--font-size", type=int)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        regions = label_atlas(
            args.input,
            args.output,
            args.layout,
            args.id_prefix,
            args.font_size,
            _load_lineage(args.lineage_json),
        )
    except AtlasLabelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {
                    "input_path": str(args.input),
                    "output_path": str(args.output),
                    "layout": args.layout,
                    "regions": regions,
                    "script_boundary": SCRIPT_BOUNDARY,
                    "boundary_note": (
                        "Equal theoretical regions, IDs, and supplied lineage were rendered mechanically; "
                        "atlas legibility and candidate value still require agentic audit."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
