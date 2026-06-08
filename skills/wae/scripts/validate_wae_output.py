#!/usr/bin/env python3
"""Validate WAE fidelity output shape."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


SPEC = FidelitySpec(
    schema_version="wae-fidelity-v0.1",
    method="WAE",
    report_title="WAE Shape & Evidence Risk Report",
    required_moves=(
        "uncertainty_classification",
        "controlling_layer",
        "risk_modulators",
        "evidence_bridges",
        "schema_judgment_boundary",
    ),
    action_postures=frozenset(
        {
            "workflow_control",
            "agentic_control",
            "evidence_gate",
            "human_escalation",
            "hybrid",
            "transfer",
            "stop",
            "unclear",
        }
    ),
    truth_boundary="control-boundary truth",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate WAE fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = validate_fidelity_output(data, SPEC)
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
