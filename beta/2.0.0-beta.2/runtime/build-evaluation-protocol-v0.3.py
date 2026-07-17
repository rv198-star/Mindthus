#!/usr/bin/env python3
"""Build the visible-case Codex-only Beta.2 protocol v0.3."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
V02_BUILDER = BETA_ROOT / "runtime" / "build-evaluation-protocol-v0.2.py"
V02_VALIDATOR = BETA_ROOT / "runtime" / "freeze-evaluation-protocol-v0.2.py"
DEFAULT_OUT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.3.json"
SEALED_CASE_IDS = (
    "b2-shadow-owner-overlap",
    "b2-shadow-passive-intersection",
    "b2-shadow-anti-rename",
    "b2-shadow-near-negative",
)


def load_v02_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_protocol_v02_builder", V02_BUILDER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.2 protocol builder: {V02_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payload() -> dict[str, Any]:
    v02 = load_v02_builder()
    protocol = v02.payload()
    base = v02.load_base_builder()
    protocol["dependencies"].append(
        base.dependency(
            "codex_protocol_v02_validator",
            "beta/2.0.0-beta.2/runtime/freeze-evaluation-protocol-v0.2.py",
            117,
        )
    )
    protocol["protocol_version"] = "0.3"
    protocol["purpose"] = (
        "Compare Stable, direct-only, and thin-kernel behavior and cost on 25 "
        "implementation-visible Codex cases only. This exploratory evidence cannot "
        "establish hidden-set generalization, Claude behavior, cross-host behavior, "
        "or release readiness."
    )

    workload = protocol["workload"]
    workload["matched_case_ids"] = [
        case_id
        for case_id in workload["matched_case_ids"]
        if case_id not in SEALED_CASE_IDS
    ]
    workload["excluded_case_ids"] = [
        *SEALED_CASE_IDS,
        *workload["excluded_case_ids"],
    ]
    workload["evidence_visibility"] = "implementation-visible"
    workload["hidden_generalization_claim"] = "forbidden"

    design = protocol["execution_design"]
    design["order_seed_sha256"] = hashlib.sha256(
        b"mindthus-beta2-protocol-v0.3-codex-visible-only-preregistered-order"
    ).hexdigest()
    design["sealed_case_custodian_attestation_required"] = False
    design["sealed_receipt_binding_timing"] = (
        "not-applicable: all sealed-shadow cases are excluded"
    )
    design["visible_case_evidence_limitation"] = (
        "all 25 matched prompts and expected behavior are visible to implementation; "
        "results are exploratory and cannot support blindness or hidden-set claims"
    )

    authorization = protocol["authorization_parameters"]
    authorization["planned_generation_outputs"] = 225
    authorization["planned_judge_records"] = 450
    proposed = authorization["proposed_authorization"]
    proposed["maximum_generation_calls"] = 240
    proposed["maximum_judge_calls"] = 480
    proposed["token_or_cost_budget"]["maximum"] = 22000000
    authorization["delegated_digest_binding_allowed"] = True
    authorization["delegated_digest_binding_rule"] = (
        "The stop authority may authorize the exact experiment values before freeze "
        "and delegate binding to the first frozen v0.3 digest that validates against "
        "those values; any value drift requires new human authorization."
    )

    protocol["rejected_alternatives"].extend(
        [
            {
                "alternative": "retain empty sealed-shadow receipt slots without a custodian",
                "reason": (
                    "opaque receipts without prompt content cannot be executed and would "
                    "create a false blindness claim"
                ),
            },
            {
                "alternative": "treat the 25 visible cases as hidden evaluation evidence",
                "reason": (
                    "their prompts and expected behavior are available to implementation; "
                    "v0.3 supports exploratory visible-case claims only"
                ),
            },
        ]
    )
    protocol["freeze"]["source_parent_commit"] = base.git_head()
    return protocol


def main() -> int:
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT.write_text(
        json.dumps(payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(DEFAULT_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
