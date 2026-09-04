#!/usr/bin/env python3
"""Rebuild SRA v0.3 derived artifacts without changing Agentic judgments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sra_runtime import SraRuntimeError, repair_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild SRA v0.3 packets, surfaces, cache state, comparison, final copy, "
            "and trace from raw input plus valid recorded judgments."
        )
    )
    parser.add_argument("--dir", required=True, help="SRA v0.3 run directory.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = repair_run(Path(args.dir))
    except SraRuntimeError as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("SRA v0.3 derived artifacts rebuilt")
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0 if result.get("repaired") else 1


if __name__ == "__main__":
    raise SystemExit(main())
