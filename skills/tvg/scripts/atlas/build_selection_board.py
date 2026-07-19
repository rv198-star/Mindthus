#!/usr/bin/env python3
"""Build a deterministic strip of selected atlas candidates without choosing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_BOUNDARY = "support_only_agentic_audit_required"
LABEL_SCHEMA_VERSION = "tvg-atlas-labels-v1"
LAYOUTS = {"2x2": (2, 2), "3x3": (3, 3)}


class SelectionBoardError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pillow() -> tuple[Any, Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except ImportError as exc:
        raise SelectionBoardError("Pillow is required; install scripts/atlas/requirements.txt") from exc
    return Image, ImageDraw, ImageFont, ImageOps


def _font(size: int) -> Any:
    _, _, ImageFont, _ = _pillow()
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def _load_regions(
    path: Path,
    source: Path,
    decoded_width: int,
    decoded_height: int,
) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SelectionBoardError(f"cannot read labels JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != LABEL_SCHEMA_VERSION:
        raise SelectionBoardError(f"labels JSON schema_version must be {LABEL_SCHEMA_VERSION!r}")
    source_record = payload.get("source")
    if not isinstance(source_record, dict):
        raise SelectionBoardError("labels JSON must contain source identity")
    try:
        actual_digest = _sha256(source)
    except OSError as exc:
        raise SelectionBoardError(f"cannot read input image bytes: {exc}") from exc
    if source_record.get("sha256") != actual_digest:
        raise SelectionBoardError("labels JSON source digest does not match input image")
    if source_record.get("decoded_width") != decoded_width or source_record.get(
        "decoded_height"
    ) != decoded_height:
        raise SelectionBoardError("labels JSON decoded dimensions do not match input image")
    layout = payload.get("layout")
    if layout not in LAYOUTS:
        raise SelectionBoardError(f"labels JSON layout must be one of {sorted(LAYOUTS)}")
    columns, rows = LAYOUTS[layout]
    regions = payload.get("regions")
    if not isinstance(regions, list):
        raise SelectionBoardError("labels JSON must contain a regions list")
    if len(regions) != columns * rows:
        raise SelectionBoardError("labels JSON region count does not match layout")
    result: dict[str, dict[str, Any]] = {}
    for index, region in enumerate(regions):
        if not isinstance(region, dict) or not isinstance(region.get("id"), str):
            raise SelectionBoardError(f"invalid region at index {index}")
        expected_row = index // columns + 1
        expected_column = index % columns + 1
        if region.get("row") != expected_row or region.get("column") != expected_column:
            raise SelectionBoardError("labels JSON regions must be in row-major order")
        expected_box = [
            decoded_width * (expected_column - 1) // columns,
            decoded_height * (expected_row - 1) // rows,
            decoded_width * expected_column // columns,
            decoded_height * expected_row // rows,
        ]
        if region.get("pixel_box") != expected_box:
            raise SelectionBoardError(f"region {region['id']} pixel box is outside the declared layout")
        if region["id"] in result:
            raise SelectionBoardError(f"duplicate region ID: {region['id']}")
        result[region["id"]] = region
    return result


def build_board(source: Path, labels: Path, selected: list[str], output: Path) -> list[dict[str, Any]]:
    if len(selected) != 3 or len(set(selected)) != 3:
        raise SelectionBoardError("exactly three distinct selected IDs are required")
    if not source.is_file():
        raise SelectionBoardError(f"input image not found: {source}")
    Image, ImageDraw, _, ImageOps = _pillow()
    try:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except (OSError, ValueError) as exc:
        raise SelectionBoardError(f"cannot read input image: {exc}") from exc
    regions = _load_regions(labels, source, image.width, image.height)
    unknown = [candidate_id for candidate_id in selected if candidate_id not in regions]
    if unknown:
        raise SelectionBoardError(f"unknown selected IDs: {unknown}")
    panel_width = 500
    panel_height = 333
    gap = 12
    footer = 64
    canvas = Image.new("RGB", (panel_width * 3 + gap * 4, panel_height + footer + gap * 2), "#111111")
    draw = ImageDraw.Draw(canvas)
    title_font = _font(26)
    lineage_font = _font(16)
    records: list[dict[str, Any]] = []
    for index, candidate_id in enumerate(selected):
        region = regions[candidate_id]
        box = region.get("pixel_box")
        if not isinstance(box, list) or len(box) != 4 or not all(isinstance(value, int) for value in box):
            raise SelectionBoardError(f"invalid pixel box for {candidate_id}")
        panel = image.crop(tuple(box)).resize((panel_width, panel_height), Image.Resampling.LANCZOS)
        x = gap + index * (panel_width + gap)
        canvas.paste(panel, (x, gap))
        draw.rectangle((x, gap, x + panel_width - 1, gap + panel_height - 1), outline="#75c9a7", width=5)
        draw.text((x + 8, gap + panel_height + 8), candidate_id, font=title_font, fill="white")
        parents = region.get("parent_candidate_ids") or []
        if parents:
            draw.text(
                (x + 170, gap + panel_height + 14),
                f"from {' + '.join(parents)}",
                font=lineage_font,
                fill="#beded2",
            )
        records.append({"id": candidate_id, "parent_candidate_ids": parents, "source_pixel_box": box})
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a selected-candidate strip from deterministic regions.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--labels-json", type=Path, required=True)
    parser.add_argument("--selected", nargs=3, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        records = build_board(args.input, args.labels_json, args.selected, args.output)
    except SelectionBoardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {
                    "output_path": str(args.output),
                    "selected": records,
                    "script_boundary": SCRIPT_BOUNDARY,
                    "boundary_note": "The script cropped supplied IDs only; it did not choose or rank candidates.",
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
