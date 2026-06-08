#!/usr/bin/env python3
"""Validate using-mindthus fidelity output shape."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


SPEC = FidelitySpec(
    schema_version="using-mindthus-fidelity-v0.1",
    method="using-mindthus",
    report_title="using-mindthus Shape & Evidence Risk Report",
    required_moves=(
        "intervention_boundary",
        "premise_calibration",
        "constraint_separation",
        "judgment_object_routing",
        "method_arbitration",
        "execution_impact",
    ),
    action_postures=frozenset(
        {
            "direct_execute",
            "acquire_information",
            "route",
            "arbitrate",
            "transfer",
            "stop",
            "unclear",
        }
    ),
    truth_boundary="router judgment truth",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate using-mindthus fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = validate_fidelity_output(data, SPEC)
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
