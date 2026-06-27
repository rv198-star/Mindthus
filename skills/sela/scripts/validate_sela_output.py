#!/usr/bin/env python3
"""Validate SELA fidelity output shape."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _runtime.core.io import load_json
from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


SPEC = FidelitySpec(
    schema_version="sela-fidelity-v0.1",
    method="SELA",
    report_title="SELA Shape & Evidence Risk Report",
    required_moves=(
        "fair_comparison_check",
        "local_advantage_scalability",
        "system_efficiency_trajectory",
        "hard_boundary_check",
        "timing_action_posture",
        "misuse_challenge",
    ),
    action_postures=frozenset(
        {
            "commit",
            "trial",
            "hold",
            "wait",
            "stage",
            "dual_track",
            "reject",
            "transfer",
            "unclear",
        }
    ),
    truth_boundary="strategic truth",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SELA fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = load_json(path)
    findings = validate_fidelity_output(data, SPEC)
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
