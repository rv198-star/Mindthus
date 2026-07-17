#!/usr/bin/env python3
"""Build the Codex-only amendment of the preregistered Beta.2 protocol."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
BASE_BUILDER = BETA_ROOT / "runtime" / "build-evaluation-protocol.py"
DEFAULT_OUT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.2.json"


def load_base_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mindthus_beta2_protocol_v01_builder", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base protocol builder: {BASE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _replace_endpoint_language(protocol: dict[str, Any]) -> None:
    replacements = {
        "lower 95% paired interval must be >= -0.05 in each host and overall": (
            "lower 95% paired interval must be >= -0.05 on the Codex surface"
        ),
        "upper 95% paired ratio interval must be <= 0.85 in each host and overall": (
            "upper 95% paired ratio interval must be <= 0.85 on the Codex surface"
        ),
        "p50 ratio must be <= 0.90 and p95 ratio <= 0.95 in each host": (
            "p50 ratio must be <= 0.90 and p95 ratio <= 0.95 on the Codex surface"
        ),
        "report by host, entry mode, primitive, arm, and provenance; no global pass": (
            "report by Codex entry mode, primitive, arm, and provenance; no global pass"
        ),
        "report distributions by exact host/entry/arm strata": (
            "report distributions by exact Codex entry/arm strata"
        ),
    }
    for endpoint in [*protocol["primary_endpoints"], *protocol["secondary_endpoints"]]:
        for field in ("decision_rule", "reporting_rule"):
            value = endpoint.get(field)
            if value in replacements:
                endpoint[field] = replacements[value]


def payload() -> dict[str, Any]:
    base = load_base_builder()
    protocol = base.payload()
    protocol["dependencies"].append(
        base.dependency(
            "base_protocol_validator",
            "beta/2.0.0-beta.2/runtime/freeze-evaluation-protocol.py",
            117,
        )
    )
    protocol["protocol_version"] = "0.2"
    protocol["purpose"] = (
        "Compare Stable, direct-only, and thin-kernel behavior and cost on the Codex "
        "surface only, without turning skill loads into semantic success, repeat count "
        "into release proof, or a single-host result into a Claude/cross-host claim."
    )
    protocol["workload"]["host_surfaces"] = ["codex-plugin"]
    protocol["execution_design"]["order_seed_sha256"] = hashlib.sha256(
        b"mindthus-beta2-protocol-v0.2-codex-only-preregistered-order"
    ).hexdigest()
    protocol["execution_design"]["stratum_rule"] = (
        "report the Codex surface and every entry mode separately; an overall "
        "equal-positive-negative weighted line cannot override a failing required stratum"
    )
    protocol["execution_design"]["supported_result_surface"] = "codex-plugin"
    protocol["execution_design"]["cross_host_generalization"] = "forbidden"
    protocol["execution_design"]["same_model_judge_limitation"] = (
        "generator and judges use gpt-5.6-sol xhigh in isolated sessions; this is "
        "same-model blind review, not independent-model or cross-host validation"
    )
    _replace_endpoint_language(protocol)
    protocol["vetoes"][5]["condition"] = (
        "thin-kernel misses one required Frame, Whole, Decision Context, or Anti-Spiral "
        "action in all repeats of a Codex case"
    )

    protocol["authorization_parameters"].update(
        {
            "authorized_host_surface": "codex-plugin",
            "planned_generation_outputs": 261,
            "planned_judge_records": 522,
            "proposed_authorization": {
                "generator_model_by_host": {
                    "codex-plugin": {
                        "model_id": "gpt-5.6-sol",
                        "reasoning_effort": "xhigh",
                        "codex_cli_version": "0.144.4",
                    }
                },
                "judge_model_and_reasoning": {
                    "model_id": "gpt-5.6-sol",
                    "reasoning_effort": "xhigh",
                    "independent_sessions_per_output": 2,
                    "environment": "isolated Mindthus-free and Superpowers-free Codex home",
                },
                "maximum_generation_calls": 276,
                "maximum_judge_calls": 552,
                "token_or_cost_budget": {
                    "kind": "aggregate-token-ceiling",
                    "maximum": 25000000,
                    "counted_components": ["input", "output", "reasoning"],
                    "cached_input_double_counted": False,
                },
                "human_adjudicator": "William",
                "stop_authority": "William",
            },
        }
    )
    protocol["rejected_alternatives"].append(
        {
            "alternative": "infer Claude or cross-host behavior from the Codex-only run",
            "reason": "v0.2 contains no Claude execution stratum and supports only Codex claims",
        }
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
