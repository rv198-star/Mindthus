#!/usr/bin/env python3
"""Prepare the actual HTML for a host's previewable code block, without rendering it.

The download stays the original file. This helper emits its exact UTF-8 source;
only the host or user can establish whether the preview is visible and interactive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


def prepare_html_delivery(path: Path) -> dict[str, str]:
    artifact = path.expanduser().resolve(strict=True)
    if artifact.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("An existing .html or .htm artifact is required")
    raw = artifact.read_bytes()
    source = raw.decode("utf-8")
    if not source.strip() or "\x00" in source:
        raise ValueError("HTML must be nonempty UTF-8 text without NUL characters")
    # A longer fence keeps HTML containing Markdown examples inside one block.
    fence = "`" * max(3, 1 + max((len(run) for run in re.findall(r"`+", source)), default=0))
    separator = "" if source.endswith("\n") else "\n"
    return {
        "artifact_path": str(artifact),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mime_type": "text/html",
        "html": source,
        "preview_block": f"{fence}html\n{source}{separator}{fence}\n",
        "status": "prepared_not_verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()
    try:
        delivery = prepare_html_delivery(args.html_file)
        if args.format == "json":
            print(json.dumps(delivery, ensure_ascii=False, indent=2))
        else:
            sys.stdout.write(delivery["preview_block"])
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"HTML delivery preparation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
