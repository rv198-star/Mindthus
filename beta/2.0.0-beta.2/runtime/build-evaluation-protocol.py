#!/usr/bin/env python3
"""Build the preregistered Beta.2 protocol from accepted local contracts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
DEFAULT_OUT = BETA_ROOT / "protocols" / "evaluation-protocol-v0.1.json"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def dependency(identifier: str, relative_path: str, issue: int) -> dict[str, Any]:
    path = REPO_ROOT / relative_path
    return {
        "id": identifier,
        "path": relative_path,
        "sha256": sha256_file(path),
        "acceptance_issue": issue,
    }


def evidence(endpoint: str, provenance: list[str], minimum: int = 1) -> dict[str, Any]:
    return {
        "endpoint": endpoint,
        "allowed_provenance": provenance,
        "minimum_per_cell": minimum,
    }


def primary(
    identifier: str,
    domain: str,
    metric: str,
    comparison: str,
    direction: str,
    margin_kind: str,
    margin_value: float,
    margin_unit: str,
    decision_rule: str,
    required_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": identifier,
        "domain": domain,
        "status": "resolved",
        "metric": metric,
        "comparison": comparison,
        "direction": direction,
        "margin": {
            "kind": margin_kind,
            "value": margin_value,
            "unit": margin_unit,
        },
        "decision_rule": decision_rule,
        "required_evidence": required_evidence,
        "missing_policy": "veto",
    }


def secondary(
    identifier: str,
    domain: str,
    metric: str,
    reporting_rule: str,
    required_evidence: list[dict[str, Any]],
    *,
    missing_policy: str = "block-endpoint",
) -> dict[str, Any]:
    return {
        "id": identifier,
        "domain": domain,
        "status": "resolved",
        "metric": metric,
        "reporting_rule": reporting_rule,
        "required_evidence": required_evidence,
        "missing_policy": missing_policy,
    }


def payload() -> dict[str, Any]:
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    matched = [
        case["case_id"]
        for case in matrix["cases"]
        if case["source"]["run_eligibility"] != "requires-user-authorization"
    ]
    excluded = [
        case["case_id"]
        for case in matrix["cases"]
        if case["source"]["run_eligibility"] == "requires-user-authorization"
    ]
    judge_pair = [evidence("judge.normalized_final_answer_score", ["judge-inferred"], 2)]
    owner_judge_pair = [evidence("judge.observed_execution_owner", ["judge-inferred"], 2)]
    primitive_judge_pair = [evidence("judge.primitive_obligation_results", ["judge-inferred"], 2)]
    return {
        "schema_version": "mindthus-beta2-evaluation-protocol-v0.1",
        "protocol_id": "mindthus-beta2-three-arm-evaluation",
        "protocol_version": "0.1",
        "status": "frozen",
        "purpose": (
            "Compare Stable, direct-only, and thin-kernel behavior and cost without "
            "turning skill loads into semantic success or turning repeat count into release proof."
        ),
        "dependencies": [
            dependency(
                "protocol_schema",
                "beta/2.0.0-beta.2/evaluation-protocol.schema.json",
                117,
            ),
            dependency(
                "protocol_lock_schema",
                "beta/2.0.0-beta.2/protocol-lock.schema.json",
                117,
            ),
            dependency(
                "arm_definitions",
                "beta/2.0.0-beta.2/arm-definitions.json",
                113,
            ),
            dependency(
                "arm_manifest_schema",
                "beta/2.0.0-beta.2/arm-manifest.schema.json",
                113,
            ),
            dependency(
                "scoring_case_schema",
                "beta/2.0.0-beta.2/evaluation-case.schema.json",
                114,
            ),
            dependency(
                "scoring_contract",
                "beta/2.0.0-beta.2/SCORING-CONTRACT.md",
                114,
            ),
            dependency(
                "telemetry_schema",
                "beta/2.0.0-beta.2/turn-telemetry.schema.json",
                115,
            ),
            dependency(
                "case_matrix_schema",
                "beta/2.0.0-beta.2/case-matrix.schema.json",
                116,
            ),
            dependency(
                "case_matrix_fixture",
                "beta/2.0.0-beta.2/fixtures/evaluation-case-matrix.json",
                116,
            ),
        ],
        "arms": [
            {
                "arm_id": arm_id,
                "identity_source": "sealed-arm-manifest.identity_digest",
                "mutable": False,
            }
            for arm_id in ("stable", "direct-only", "thin-kernel")
        ],
        "workload": {
            "matrix_dependency_id": "case_matrix_fixture",
            "matched_case_ids": matched,
            "smoke_case_ids": [
                "b2-dev-owner-3l5s",
                "b2-dev-arbitrator-overlap",
                "b2-dev-multi-primitive",
                "b2-dev-near-normal-debugging",
                "b2-dev-lifecycle-compact",
            ],
            "smoke_repeats": 1,
            "smoke_outputs_count_toward_matched": True,
            "excluded_case_ids": excluded,
            "case_type_weighting": "equal-positive-negative-mass",
            "host_surfaces": ["codex-plugin", "claude-plugin"],
            "entry_modes": [
                "owner-direct",
                "passive-kernel",
                "arbitrator",
                "stay-asleep",
                "evidence-first",
            ],
            "repeat_count_floor": 3,
            "planned_repeats": 3,
            "repeat_count_is_release_proof": False,
        },
        "execution_design": {
            "matched_cell_key": "protocol_digest/arm_digest/host/case_id/repeat",
            "paired_unit": "host/case_id/repeat",
            "arm_order": "sha256-fixed Latin rotation from preregistered order seed",
            "order_seed_sha256": hashlib.sha256(
                b"mindthus-beta2-protocol-v0.1-preregistered-order"
            ).hexdigest(),
            "generator_environment": "one isolated verified host home per arm",
            "judge_environment": "separate Mindthus-free and Superpowers-free home",
            "generator_judge_separated": True,
            "judge_count_per_output": 2,
            "judge_sessions_independent": True,
            "blinding": (
                "strip arm labels, paths, telemetry, order, and model-facing diagnostics; "
                "shuffle opaque output ids before judging"
            ),
            "adjudication": (
                "retain both scores; disagreement on binary primary axes requires a blinded "
                "human adjudicator, never generator self-report"
            ),
            "analysis_unit": "case-clustered paired delta with deterministic 95% bootstrap interval",
            "bootstrap_iterations": 10000,
            "sealed_case_custodian_attestation_required": True,
            "sealed_receipt_binding_timing": "after protocol freeze and before #119 authorization",
            "stratum_rule": (
                "report every host and entry mode separately; an overall equal-positive-negative "
                "weighted line cannot override a failing required stratum"
            ),
        },
        "primary_endpoints": [
            primary(
                "quality_noninferiority_vs_stable",
                "quality",
                "mean normalized blinded final-answer score",
                "thin-kernel minus stable",
                "higher-is-better",
                "noninferiority-delta",
                -0.05,
                "proportion",
                "lower 95% paired interval must be >= -0.05 in each host and overall",
                judge_pair,
            ),
            primary(
                "execution_owner_fidelity_vs_stable",
                "execution-owner-fidelity",
                "accepted execution-owner success rate",
                "thin-kernel minus stable",
                "higher-is-better",
                "noninferiority-delta",
                -0.05,
                "proportion",
                "lower 95% paired interval must be >= -0.05 in each host and overall",
                owner_judge_pair,
            ),
            primary(
                "primitive_recall_kernel_benefit",
                "primitive-recall",
                "required primitive action recall",
                "thin-kernel minus direct-only",
                "higher-is-better",
                "minimum-superiority-delta",
                0.10,
                "proportion",
                "lower 95% paired interval must be >= +0.10 in passive-obligation cases",
                primitive_judge_pair,
            ),
            primary(
                "joint_owner_primitive_kernel_benefit",
                "joint-owner-primitive",
                "joint accepted-owner and all-required-primitives success",
                "thin-kernel minus direct-only",
                "higher-is-better",
                "minimum-superiority-delta",
                0.08,
                "proportion",
                "lower 95% paired interval must be >= +0.08 in intersecting cases",
                [*owner_judge_pair, *primitive_judge_pair],
            ),
            primary(
                "false_wakeup_harm_vs_stable",
                "false-wakeup",
                "negative-control semantic or runtime false-wakeup rate",
                "thin-kernel minus stable",
                "lower-is-better",
                "maximum-harm-delta",
                0.03,
                "proportion",
                "upper 95% paired interval must be <= +0.03 and absolute rate <= 0.05",
                [
                    evidence("judge.false_wakeup_final_answer", ["judge-inferred"], 2),
                    evidence("skill_hops", ["deterministic"], 1),
                ],
            ),
            primary(
                "lifecycle_fidelity",
                "lifecycle",
                "required lifecycle event set fidelity",
                "thin-kernel absolute",
                "higher-is-better",
                "minimum-absolute-rate",
                1.0,
                "proportion",
                "every included thin-kernel cell must have native lifecycle fidelity",
                [evidence("lifecycle_event", ["native"], 1)],
            ),
            primary(
                "input_token_savings_vs_stable",
                "efficiency",
                "workload-weighted input token count",
                "thin-kernel relative to stable",
                "lower-is-better",
                "minimum-relative-reduction",
                0.15,
                "ratio-reduction",
                "upper 95% paired ratio interval must be <= 0.85 in each host and overall",
                [evidence("tokens.input", ["native"], 1)],
            ),
            primary(
                "kernel_token_overhead_vs_direct",
                "efficiency",
                "workload-weighted input token count",
                "thin-kernel relative to direct-only",
                "lower-is-better",
                "maximum-relative-overhead",
                0.08,
                "ratio-overhead",
                "upper 95% paired ratio interval must be <= 1.08",
                [evidence("tokens.input", ["native"], 1)],
            ),
            primary(
                "wall_time_savings_vs_stable",
                "efficiency",
                "wall time p50 and p95",
                "thin-kernel relative to stable",
                "lower-is-better",
                "minimum-relative-reduction",
                0.10,
                "ratio-reduction",
                "p50 ratio must be <= 0.90 and p95 ratio <= 0.95 in each host",
                [evidence("wall_time_seconds", ["native", "deterministic"], 1)],
            ),
            primary(
                "first_useful_action_latency",
                "user-visible-interaction-cost",
                "native first-useful-action latency p50 and p95",
                "thin-kernel relative to stable",
                "lower-is-better",
                "minimum-relative-reduction",
                0.10,
                "ratio-reduction",
                "p50 ratio must be <= 0.90 and p95 ratio <= 0.95 in each host",
                [evidence("first_useful_action_latency_seconds", ["native"], 1)],
            ),
        ],
        "secondary_endpoints": [
            secondary(
                "primitive_precision",
                "primitive-precision",
                "unexpected primitive action rate and per-primitive precision",
                "report by host, entry mode, primitive, arm, and provenance; no global pass",
                [evidence("judge.primitive_obligation_results", ["judge-inferred"], 2)],
            ),
            secondary(
                "token_breakdown",
                "efficiency",
                "cached input, output, and reasoning tokens",
                "report p50/p95 and missing denominators separately for every token component",
                [
                    evidence("tokens.cached_input", ["native"], 1),
                    evidence("tokens.output", ["native"], 1),
                    evidence("tokens.reasoning", ["native"], 1),
                ],
            ),
            secondary(
                "runtime_hops",
                "efficiency",
                "skill hops, tool hops, and retained resource reads",
                "report distributions by exact host/entry/arm strata",
                [
                    evidence("skill_hops", ["deterministic"], 1),
                    evidence("tool_hops", ["deterministic"], 1),
                    evidence("resource_reads", ["deterministic"], 1),
                ],
            ),
            secondary(
                "clarification_burden",
                "user-visible-interaction-cost",
                "clarification turns before useful action",
                "report paired counts; judge inference cannot satisfy native latency",
                [evidence("clarification_turns", ["judge-inferred", "native"], 1)],
            ),
            secondary(
                "visible_notices_and_jargon",
                "user-visible-interaction-cost",
                "visible notices and Mindthus terminology leakage",
                "report counts and any severe leakage verbatim only in restricted audit storage",
                [
                    evidence("visible_notices", ["deterministic"], 1),
                    evidence("mindthus_terminology_leakage", ["deterministic"], 1),
                ],
            ),
            secondary(
                "retry_and_failure_burden",
                "reliability",
                "retry count, timeout, and failure count",
                "report every retry and failure; never exclude it from efficiency denominators",
                [
                    evidence("retry_count", ["deterministic", "native"], 1),
                    evidence("failure_count", ["deterministic", "native"], 1),
                ],
            ),
            secondary(
                "load_contract",
                "runtime-load",
                "required/allowed skill-load contract and stay-asleep fidelity",
                "report separately from behavior and primitive success",
                [evidence("skill_hops", ["deterministic"], 1)],
            ),
            secondary(
                "source_provenance",
                "evidence-provenance",
                "public, development, sealed-shadow, and replay result lines",
                "never pool visible cases into a blind-evidence claim",
                [evidence("case.source_receipt", ["deterministic", "native"], 1)],
                missing_policy="veto",
            ),
        ],
        "missing_data_policy": {
            "zero_imputation": "forbidden",
            "pass_imputation": "forbidden",
            "primary_endpoint_missing": "fire missing-primary-native-evidence veto and stop",
            "secondary_endpoint_missing": "mark endpoint blocked/unknown with denominator; do not infer",
            "wrong_provenance": "treat as missing for that endpoint",
            "contradictory_evidence": "stop and retain both observations",
            "cross_host_substitution": "forbidden",
            "cross_entry_mode_substitution": "forbidden",
        },
        "vetoes": [
            {
                "id": "cross-arm-contamination",
                "stage": "preflight-or-run",
                "condition": "more than one Mindthus namespace or any arm artifact appears in another arm home",
                "action": "stop-run",
            },
            {
                "id": "protocol-or-arm-drift",
                "stage": "preflight-or-resume",
                "condition": "protocol, dependency, arm, package, hook, context, case, or tool digest differs",
                "action": "stop-run",
            },
            {
                "id": "untraceable-or-partial-artifact",
                "stage": "any",
                "condition": "a cell lacks an atomic receipt or cannot resolve to arm/protocol/case digests",
                "action": "stop-run",
            },
            {
                "id": "missing-primary-native-evidence",
                "stage": "smoke-or-matched",
                "condition": "any primary endpoint lacks its frozen native/deterministic minimum",
                "action": "stop-run",
            },
            {
                "id": "judge-environment-contamination",
                "stage": "judge",
                "condition": "judge sees arm labels, generator paths, Mindthus, Superpowers, or runtime telemetry",
                "action": "stop-run",
            },
            {
                "id": "systematic-critical-primitive-miss",
                "stage": "smoke-or-matched",
                "condition": "thin-kernel misses one required Frame, Whole, Decision Context, or Anti-Spiral action in all repeats of a case/host",
                "action": "stop-run",
            },
            {
                "id": "authority-or-evidence-regression",
                "stage": "smoke-or-matched",
                "condition": "any output overrides user authority or states an unsupported factual conclusion that its evidence gate forbids",
                "action": "stop-run",
            },
            {
                "id": "insufficient-kernel-benefit",
                "stage": "post-matched-decision",
                "condition": "primitive recall or joint owner+primitive benefit versus direct-only misses its frozen margin",
                "action": "recommend-stop",
            },
            {
                "id": "negligible-efficiency-savings",
                "stage": "post-matched-decision",
                "condition": "token or wall-time savings versus Stable miss a frozen primary threshold",
                "action": "recommend-stop",
            },
        ],
        "rerun_policy": {
            "infrastructure_failure_before_model_output": (
                "one same-cell retry is allowed after recording the failed attempt and proving no output"
            ),
            "model_output_exists": (
                "never discard or replace; only preregistered repeats may add observations"
            ),
            "judge_parse_failure": (
                "one retry over the identical blinded payload; retain both attempts, then human adjudication"
            ),
            "contamination_or_digest_failure": "no rerun under this protocol version; stop and version",
            "exclusions": (
                "only frozen eligibility or a fired veto; every exclusion remains in denominators and report"
            ),
            "threshold_or_workload_change": "requires a new protocol version before new model output",
        },
        "authorization_parameters": {
            "status": "required-before-issue-119",
            "must_name": [
                "protocol_digest",
                "generator_model_by_host",
                "judge_model_and_reasoning",
                "maximum_generation_calls",
                "maximum_judge_calls",
                "token_or_cost_budget",
                "stop_authority",
            ],
            "same_generator_configuration_across_arms": True,
            "model_name_routing": "forbidden",
            "budget_shortfall_action": "do not start; create a new protocol version rather than truncate cells",
        },
        "rejected_alternatives": [
            {
                "alternative": "identify arms with a free-text variant label",
                "reason": "labels do not prove package, host, hook, namespace, or context identity",
            },
            {
                "alternative": "route by model name or capability guess",
                "reason": "the architecture claim concerns behavior and cost, not a model allowlist",
            },
            {
                "alternative": "collapse quality, primitive benefit, and efficiency into one score",
                "reason": "a weighted composite can hide a quality regression or negligible Kernel value",
            },
            {
                "alternative": "choose workload weights or margins after smoke output",
                "reason": "result-aware choices invalidate the comparison",
            },
            {
                "alternative": "treat public or development cases as blind evidence",
                "reason": "their prompts and expected behavior are visible to implementation",
            },
            {
                "alternative": "infer native timing or hook evidence from answer text",
                "reason": "self-report and regex cannot establish host events",
            },
            {
                "alternative": "use one repeat as release evidence",
                "reason": "repeat count is only an exploration floor and never Stable release proof",
            },
        ],
        "freeze": {
            "immutable_after": "lock receipt creation and containing git commit",
            "amendment_policy": "new protocol version and new lock required",
            "semantic_model_output_generated_before_freeze": False,
            "source_parent_commit": git_head(),
        },
    }


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
