#!/usr/bin/env python3
"""Create a decision packet for a tplan decision hook."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import build_decision_packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a tplan decision packet.")
    parser.add_argument("mission_dir")
    parser.add_argument("--hook", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    try:
        packet = build_decision_packet(Path(args.mission_dir), args.hook)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"decision_packet: {args.output}")
    print("script_result: packet created; semantic judgment remains with the routed skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
