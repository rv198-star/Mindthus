#!/usr/bin/env python3
"""Validate EDSP fidelity output shape."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


SPEC = FidelitySpec(
    schema_version="edsp-fidelity-v0.1",
    method="EDSP",
    report_title="EDSP Shape & Evidence Risk Report",
    required_moves=(
        "uncertainty_type",
        "extreme_variables",
        "coordinate_system",
        "multi_role_pressure",
        "scenario_projection_gate",
        "overturn_conditions",
    ),
    action_postures=frozenset(
        {
            "structural_position",
            "scenario_project",
            "reject_binary",
            "gather_evidence",
            "transfer",
            "stop",
            "unclear",
        }
    ),
    truth_boundary="structural truth",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EDSP fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = validate_fidelity_output(data, SPEC)
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
