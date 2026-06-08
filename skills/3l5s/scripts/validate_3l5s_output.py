#!/usr/bin/env python3
"""Validate 3L5S fidelity output shape."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _runtime.fidelity.core import FidelitySpec, print_text_report, validate_fidelity_output


SPEC = FidelitySpec(
    schema_version="3l5s-fidelity-v0.1",
    method="3L5S",
    report_title="3L5S Shape & Evidence Risk Report",
    required_moves=(
        "form_choice",
        "layer_separation",
        "btgsb_fields",
        "acceptance_evidence_surface",
        "loopback_trigger",
    ),
    action_postures=frozenset(
        {
            "define_problem",
            "decompose",
            "loopback",
            "direct_execute",
            "transfer",
            "stop",
            "unclear",
        }
    ),
    truth_boundary="problem truth",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate 3L5S fidelity output shape.")
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = validate_fidelity_output(data, SPEC)
    print_text_report(path, data, findings, SPEC)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
