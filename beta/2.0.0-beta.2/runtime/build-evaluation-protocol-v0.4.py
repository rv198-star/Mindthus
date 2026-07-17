#!/usr/bin/env python3
"""Build the evidence-honest visible-case Codex protocol v0.4."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
V03_BUILDER = BETA_ROOT / "runtime" / "build-evaluation-protocol-v0.3.py"
DEFAULT_OUT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.4.json"
PRIOR_PROTOCOL_SHA256 = "ce8c06eb0656e1023de9ff477ab7a0b5a3302194e9e5af952b916130a231b144"
PRIOR_CELL_RECORD_DIGEST = "c3f4964fb5eb992f867d781afac0a037409d4ce8708515479d820d2ee40d85ad"
PRIOR_GENERATION_CALLS = 1
PRIOR_JUDGE_CALLS = 0
PRIOR_COUNTED_TOKENS = 48256
CUMULATIVE_GENERATION_CEILING = 240
CUMULATIVE_JUDGE_CEILING = 480
CUMULATIVE_TOKEN_CEILING = 22000000


def load_v03_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "mindthus_beta2_protocol_v03_builder", V03_BUILDER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.3 builder: {V03_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dependency(identifier: str, relative: str) -> dict[str, Any]:
    path = REPO_ROOT / relative
    return {
        "id": identifier,
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "acceptance_issue": 117,
    }


def _replace_primary(protocol: dict[str, Any]) -> None:
    primary = protocol["primary_endpoints"]
    first_useful = next(
        item for item in primary if item["id"] == "first_useful_action_latency"
    )
    lifecycle = next(item for item in primary if item["id"] == "lifecycle_fidelity")
    first_useful_index = primary.index(first_useful)
    lifecycle_index = primary.index(lifecycle)
    primary[first_useful_index] = {
        **first_useful,
        "id": "first_observable_action_latency",
        "metric": "runner-observed first eligible Codex JSONL action latency p50 and p95",
        "required_evidence": [
            {
                "endpoint": "first_observable_action_latency_seconds",
                "allowed_provenance": ["deterministic"],
                "minimum_per_cell": 1,
            }
        ],
        "decision_rule": (
            "p50 ratio must be <= 0.90 and p95 ratio <= 0.95 on the Codex surface; "
            "this is runner-observed stream latency, not native first-useful-action timing"
        ),
    }
    primary[lifecycle_index] = {
        **lifecycle,
        "id": "passive_kernel_session_start_injection_fidelity",
        "metric": "sealed Passive Kernel SessionStart injection fidelity",
        "comparison": "thin-kernel absolute on startup sessions",
        "decision_rule": (
            "every thin-kernel cell must resolve to a sealed no-model hook observation, "
            "fired carrier state, and native thread.started event"
        ),
        "required_evidence": [
            {
                "endpoint": "arm.hook_observation_receipt",
                "allowed_provenance": ["deterministic"],
                "minimum_per_cell": 1,
            },
            {
                "endpoint": "hook_state",
                "allowed_provenance": ["native"],
                "minimum_per_cell": 1,
            },
            {
                "endpoint": "lifecycle_event",
                "allowed_provenance": ["native"],
                "minimum_per_cell": 1,
            },
        ],
    }
    protocol["secondary_endpoints"].extend(
        [
            {
                "id": "native_first_useful_action_latency",
                "domain": "user-visible-interaction-cost",
                "status": "resolved",
                "metric": "host-native first-useful-action latency availability and distribution",
                "reporting_rule": (
                    "report the endpoint as unknown when Codex emits no native timestamp; "
                    "runner arrival time must never substitute for it"
                ),
                "required_evidence": [
                    {
                        "endpoint": "first_useful_action_latency_seconds",
                        "allowed_provenance": ["native"],
                        "minimum_per_cell": 1,
                    }
                ],
                "missing_policy": "block-endpoint",
            },
            {
                "id": "nonstartup_lifecycle_scenario_behavior",
                "domain": "lifecycle",
                "status": "resolved",
                "metric": "visible response behavior on resume/clear/compact-labelled scenarios",
                "reporting_rule": (
                    "report as prompt-carried scenario behavior only; Codex CLI v0.4 calls are "
                    "fresh startup sessions and cannot establish real clear/compact/resume fidelity"
                ),
                "required_evidence": [
                    {
                        "endpoint": "judge.required_visible_action_present",
                        "allowed_provenance": ["judge-inferred"],
                        "minimum_per_cell": 2,
                    }
                ],
                "missing_policy": "block-endpoint",
            },
        ]
    )


def payload() -> dict[str, Any]:
    v03 = load_v03_builder()
    protocol = v03.payload()
    protocol["dependencies"].extend(
        [
            dependency(
                "visible_protocol_v03_validator",
                "beta/2.0.0-beta.2/runtime/freeze-evaluation-protocol-v0.3.py",
            ),
            dependency("telemetry_builder", "scripts/mindthus_beta2_telemetry.py"),
            dependency(
                "codex_stream_capture",
                "beta/2.0.0-beta.2/runtime/codex_stream_capture.py",
            ),
            dependency(
                "codex_hook_probe",
                "beta/2.0.0-beta.2/runtime/probe_codex_hook.py",
            ),
            dependency(
                "real_arm_materializer",
                "beta/2.0.0-beta.2/runtime/materialize-real-codex-arm.py",
            ),
            dependency(
                "real_evaluation_runner_v04",
                "beta/2.0.0-beta.2/runtime/run_real_codex_evaluation_v04.py",
            ),
            dependency(
                "real_evaluation_analyzer_v04",
                "beta/2.0.0-beta.2/runtime/analyze_codex_evaluation_v04.py",
            ),
            dependency(
                "judge_output_schema_v04",
                "beta/2.0.0-beta.2/fixtures/judge-output-v0.4.schema.json",
            ),
            dependency(
                "judge_rubric_v04",
                "beta/2.0.0-beta.2/fixtures/judge-rubric-v0.4.json",
            ),
            dependency(
                "dry_run_plan_schema_v04",
                "beta/2.0.0-beta.2/dry-run-plan-v0.4.schema.json",
            ),
            dependency(
                "dry_run_fixture_builder",
                "beta/2.0.0-beta.2/runtime/build-dry-run-fixture.py",
            ),
            dependency(
                "dry_run_orchestrator",
                "beta/2.0.0-beta.2/runtime/dry-run-orchestrator.py",
            ),
        ]
    )
    protocol["protocol_version"] = "0.4"
    protocol["purpose"] = (
        "Compare Stable, direct-only, and thin-kernel behavior and cost on 25 "
        "implementation-visible Codex startup-session cases using evidence the authorized "
        "Codex CLI can actually emit. Runner-observed action latency is separated from "
        "unavailable native first-useful-action timing, and non-startup lifecycle labels "
        "are scenario context rather than host-fidelity proof."
    )
    design = protocol["execution_design"]
    design["timing_contract"] = {
        "primary": "runner-observed first eligible item.started/item.completed event for agent_message or command_execution",
        "primary_provenance": "deterministic runner streaming arrival",
        "native_first_useful_action": "secondary unknown when the host emits no timestamp",
        "substitution": "forbidden",
    }
    design["host_lifecycle_scope"] = {
        "real_model_session_mode": "startup-only",
        "session_start_injection": "sealed no-model request capture plus fired carrier and thread.started",
        "direct_only_kernel_absence": (
            "sealed no-model request capture without hook-trust bypass; any Passive "
            "Kernel wrapper in direct-only is protocol-or-arm drift"
        ),
        "resume_clear_compact_labels": "prompt-carried scenario context only",
        "nonstartup_host_fidelity_claim": "forbidden",
    }
    design["prior_protocol_output_accounting"] = {
        "protocol_version": "0.3",
        "protocol_sha256": PRIOR_PROTOCOL_SHA256,
        "cell_record_digest": PRIOR_CELL_RECORD_DIGEST,
        "generation_calls": PRIOR_GENERATION_CALLS,
        "judge_calls": PRIOR_JUDGE_CALLS,
        "counted_tokens": PRIOR_COUNTED_TOKENS,
        "retention": "retained and excluded from v0.4 analysis",
        "same_case_new_cell_rule": (
            "allowed only under the distinct v0.4 protocol digest because the measurement "
            "contract changed; the v0.3 output is never replaced"
        ),
    }
    _replace_primary(protocol)
    protocol["missing_data_policy"]["primary_endpoint_missing"] = (
        "fire the frozen missing-primary-native-evidence veto id for any missing or "
        "wrong-provenance native/deterministic primary minimum and stop"
    )
    protocol["rerun_policy"]["prior_version_output"] = (
        "retain the v0.3 cell, exclude it from v0.4 estimates, and never present the "
        "v0.4 same-case cell as a replacement"
    )
    protocol["freeze"].update(
        {
            "semantic_model_output_generated_before_freeze": True,
            "semantic_model_output_generated_under_v0_4_before_freeze": False,
            "prior_semantic_output_scope": (
                "one retained v0.3 output, explicitly debited above; no semantic output "
                "was generated under the v0.4 protocol digest before its freeze"
            ),
        }
    )

    authorization = protocol["authorization_parameters"]
    proposed = authorization["proposed_authorization"]
    proposed["maximum_generation_calls"] = CUMULATIVE_GENERATION_CEILING - PRIOR_GENERATION_CALLS
    proposed["maximum_judge_calls"] = CUMULATIVE_JUDGE_CEILING - PRIOR_JUDGE_CALLS
    proposed["token_or_cost_budget"]["maximum"] = (
        CUMULATIVE_TOKEN_CEILING - PRIOR_COUNTED_TOKENS
    )
    authorization["cumulative_authority"] = {
        "maximum_generation_calls": CUMULATIVE_GENERATION_CEILING,
        "maximum_judge_calls": CUMULATIVE_JUDGE_CEILING,
        "aggregate_token_ceiling": CUMULATIVE_TOKEN_CEILING,
        "prior_consumption": {
            "protocol_version": "0.3",
            "generation_calls": PRIOR_GENERATION_CALLS,
            "judge_calls": PRIOR_JUDGE_CALLS,
            "counted_tokens": PRIOR_COUNTED_TOKENS,
        },
        "v04_available": {
            "maximum_generation_calls": proposed["maximum_generation_calls"],
            "maximum_judge_calls": proposed["maximum_judge_calls"],
            "aggregate_token_ceiling": proposed["token_or_cost_budget"]["maximum"],
        },
        "budget_expansion": False,
    }
    authorization["delegated_digest_binding_rule"] = (
        "The stop authority authorized autonomous bounded continuation after the v0.3 "
        "instrumentation stop. The first frozen v0.4 digest may bind only if Sol xHigh "
        "roles, 25 visible cases, two isolated judges, William adjudication/stop authority, "
        "the cumulative ceilings, no-release scope, and the tighter claim boundary remain exact."
    )
    protocol["rejected_alternatives"].extend(
        [
            {
                "alternative": "rename runner stream-arrival time as native first-useful-action latency",
                "reason": "Codex CLI 0.144.4 emits no event timestamp; the two evidence classes are not interchangeable",
            },
            {
                "alternative": "claim real resume, clear, or compact lifecycle coverage from labelled fixture prompts",
                "reason": "the noninteractive runner starts fresh Codex sessions and does not trigger those host transitions",
            },
            {
                "alternative": "discard or replace the retained v0.3 generation output",
                "reason": "a semantic output already exists and must remain visible in cumulative budget and audit accounting",
            },
            {
                "alternative": "treat direct-only hook disablement as a configuration assertion",
                "reason": "the causal control must prove the Passive Kernel wrapper is absent from the model-visible request",
            },
        ]
    )
    base = v03.load_v02_builder().load_base_builder()
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
