#!/usr/bin/env python3
"""Validate MPG fidelity output shape."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime_bootstrap import activate_runtime

activate_runtime(__file__)

from _runtime.core.io import load_json
from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


SPEC = FidelitySpec(
    schema_version="mpg-fidelity-v0.1",
    method="MPG",
    report_title="MPG Shape & Evidence Risk Report",
    required_moves=(
        "qualified_mainline",
        "carrier_vehicle_separation",
        "counter_force_map",
        "exposure_budget",
        "optionality_design",
        "trigger_conditions",
        "mainline_challenge",
        "aqm_boundary",
    ),
    action_postures=frozenset(
        {
            "commit",
            "stage",
            "hedge",
            "wait",
            "switch_vehicle",
            "probe",
            "hold",
            "exit",
            "transfer",
            "unclear",
        }
    ),
    truth_boundary="mainline truth",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MPG fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = load_json(path)
    findings = validate_fidelity_output(data, SPEC)
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
