#!/usr/bin/env python3
"""Persist a Thinking Value-Gain trace record into a local trace store.

This script stores evidence for later calibration. It does not approve the trace.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "unnamed-module"


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist a TVG trace record.")
    parser.add_argument("trace")
    parser.add_argument("--store", default=".tvg/traces")
    args = parser.parse_args()

    source = Path(args.trace)
    trace = json.loads(source.read_text())
    module = trace.get("module", {}) if isinstance(trace, dict) else {}
    module_id = slugify(str(module.get("id", "unnamed-module")))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    store = Path(args.store)
    store.mkdir(parents=True, exist_ok=True)
    target = store / f"{timestamp}-{module_id}.json"
    shutil.copyfile(source, target)
    print(f"persisted_trace: {target}")
    print("script_result: trace stored for calibration/search; agentic audit remains authoritative")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
