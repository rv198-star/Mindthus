#!/usr/bin/env python3
"""Record that a Mission Pulse candidate has already been handled."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tplan_runtime import consume_current_pulse_candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Consume a tplan Mission Pulse candidate.")
    parser.add_argument("mission_dir")
    parser.add_argument("--trigger", default="manual")
    parser.add_argument("--signal", help="Consume a specific observed signal instead of the winning candidate.")
    parser.add_argument("--note", help="Optional operator note for the consumption record.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    try:
        result = consume_current_pulse_candidate(
            Path(args.mission_dir),
            trigger=args.trigger,
            signal=args.signal,
            note=args.note,
        )
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        consumed = result["consumed_candidate"]
        print(
            "pulse_consumed:"
            f" signal={consumed['signal']} next_gate={consumed['candidate_next_gate']} trigger={consumed['trigger']}"
        )
        print("script_result: pulse candidate consumption recorded; later pulses may treat matching signals as stale")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
