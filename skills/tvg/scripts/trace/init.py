#!/usr/bin/env python3
"""Initialize a Thinking Value-Gain trace record.

This script creates bookkeeping scaffolding only. It does not perform audit judgment.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def default_value_profile() -> dict:
    return {
        "mode": "default",
        "name": "default practical-value profile",
        "artifact_job": "increase practical thinking value for the module's actual downstream use",
        "value_semantics": {
            "good_means": [
                "clearer decision / action leverage",
                "better evidence honesty",
                "stronger handoff usability",
                "risk reduction without false confidence",
                "reuse without overfitting",
                "execution readiness",
            ],
            "bad_means": [
                "length, polish, or ornamental structure without practical value",
                "generic completeness that leaves downstream invention",
                "confidence that exceeds evidence or hides review-bound uncertainty",
            ],
            "priority_order": [
                "evidence honesty and explicit constraints",
                "downstream usability",
                "decision / action leverage",
                "risk reduction",
                "reuse and execution readiness",
                "value density",
            ],
            "derived_axes": [],
            "evidence_basis": [
                "TVG default practical-value model",
            ],
            "profile_veto_constraints": [],
        },
        "prompt_self_audit_questions": [],
        "image_self_audit_questions": [],
        "source_notes": [],
    }


def build_value_profile(args: argparse.Namespace) -> dict:
    profile = default_value_profile()
    if args.value_profile_mode:
        profile["mode"] = args.value_profile_mode
    if args.value_profile_name:
        profile["name"] = args.value_profile_name
    if args.value_profile_artifact_job:
        profile["artifact_job"] = args.value_profile_artifact_job
    semantics = profile["value_semantics"]
    if args.value_profile_good:
        semantics["good_means"] = args.value_profile_good
    if args.value_profile_bad:
        semantics["bad_means"] = args.value_profile_bad
    if args.value_profile_priority:
        semantics["priority_order"] = args.value_profile_priority
    if args.value_profile_derived_axis:
        semantics["derived_axes"] = args.value_profile_derived_axis
    if args.value_profile_evidence:
        semantics["evidence_basis"] = args.value_profile_evidence
    if args.value_profile_prompt_audit_question:
        profile["prompt_self_audit_questions"] = args.value_profile_prompt_audit_question
    if args.value_profile_image_audit_question:
        profile["image_self_audit_questions"] = args.value_profile_image_audit_question
    if args.value_profile_source_note:
        profile["source_notes"] = args.value_profile_source_note
    if args.profile_veto_constraint:
        semantics["profile_veto_constraints"] = args.profile_veto_constraint
    surface = {}
    if args.value_profile_surface_artifact_role:
        surface["artifact_role"] = args.value_profile_surface_artifact_role
    if args.value_profile_surface_downstream_use:
        surface["downstream_use"] = args.value_profile_surface_downstream_use
    if args.value_profile_surface_observable_unit:
        surface["observable_units"] = args.value_profile_surface_observable_unit
    if args.value_profile_surface_granularity_pressure:
        surface["granularity_pressure"] = args.value_profile_surface_granularity_pressure
    if args.value_profile_surface_review_handle:
        surface["review_handles"] = args.value_profile_surface_review_handle
    if surface:
        profile["realization_surface"] = surface
    gain_policy = {}
    if args.value_profile_gain_preferred_move:
        gain_policy["preferred_moves"] = args.value_profile_gain_preferred_move
    if args.value_profile_gain_discouraged_move:
        gain_policy["discouraged_moves"] = args.value_profile_gain_discouraged_move
    if args.value_profile_gain_split_rule:
        gain_policy["split_rules"] = args.value_profile_gain_split_rule
    if args.value_profile_gain_merge_rule:
        gain_policy["merge_rules"] = args.value_profile_gain_merge_rule
    if args.value_profile_gain_density_guidance:
        gain_policy["density_guidance"] = args.value_profile_gain_density_guidance
    if gain_policy:
        profile["gain_policy"] = gain_policy
    return profile


def build_expected_value(args: argparse.Namespace, value_profile: dict) -> dict:
    unresolved_items = list(args.expected_value_unresolved_item)
    if not args.downstream_consumer:
        unresolved_items.append("downstream_consumer is not specified")
    if not args.freeze_granularity:
        unresolved_items.append("freeze_granularity is not specified")
    hard_constraints = list(args.expected_value_hard_constraint)
    hard_constraints.extend(args.veto_constraint)
    hard_constraints.extend(value_profile.get("value_semantics", {}).get("profile_veto_constraints", []))
    if not hard_constraints:
        hard_constraints = [
            "do not override evidence honesty, claim ceilings, user constraints, safety boundaries, or veto constraints",
        ]
    useful_when = list(args.expected_value_useful_when)
    if not useful_when:
        useful_when = [
            "downstream user can act, review, decide, implement, render, or hand off without inventing critical missing truth",
        ]
    evidence_boundary = list(args.expected_value_evidence_boundary)
    if not evidence_boundary:
        evidence_boundary = [
            "separate supported claims from assumptions and review-bound uncertainty",
        ]
    return {
        "mode": args.expected_value_mode or "provisional-default",
        "target_artifact": args.expected_value_target_artifact or args.module_title,
        "artifact_job": args.expected_value_artifact_job or value_profile["artifact_job"],
        "useful_when": useful_when,
        "hard_constraints": hard_constraints,
        "evidence_boundary": evidence_boundary,
        "output_bias": args.expected_value_output_bias or "balanced",
        "source": args.expected_value_source or (
            "derived from module metadata, downstream consumer, active value_profile, "
            "and supplied constraints; agentic judgment must refine it when context is thin"
        ),
        "unresolved_expected_value_items": unresolved_items,
    }


def build_exit_gate(args: argparse.Namespace, value_profile: dict, expected_value: dict) -> dict:
    mode = args.exit_gate_mode or "provisional-default"
    source = args.exit_gate_source or (
        "internal stop condition compiled from expected_value, TVG fixed bottom lines, "
        "active value_profile, and any supplied veto constraints; agentic audit must judge it"
    )
    unresolved_gate_items = list(args.exit_gate_unresolved_item)
    unresolved_gate_items.extend(expected_value["unresolved_expected_value_items"])
    if not args.downstream_consumer:
        unresolved_gate_items.append("downstream_consumer is not specified")
    if not args.freeze_granularity:
        unresolved_gate_items.append("freeze_granularity is not specified")

    semantics = value_profile.get("value_semantics", {})
    profile_fit_checks = list(args.exit_gate_value_profile_fit_check)
    if not profile_fit_checks:
        profile_fit_checks = [
            "artifact expresses the active value_profile or default practical-value standard for its actual job",
            "longer output is not treated as value by itself",
        ]
        for priority in semantics.get("priority_order", [])[:3]:
            profile_fit_checks.append(f"profile priority preserved: {priority}")

    hard_veto_checks = list(args.exit_gate_hard_veto_check)
    hard_veto_checks.extend(expected_value["hard_constraints"])
    hard_veto_checks.extend(args.veto_constraint)
    hard_veto_checks.extend(semantics.get("profile_veto_constraints", []))
    if not hard_veto_checks:
        hard_veto_checks = [
            "evidence honesty, claim ceilings, user constraints, safety boundaries, and veto constraints remain non-overridable",
        ]

    downstream_use_checks = list(args.exit_gate_downstream_use_check)
    if not downstream_use_checks:
        downstream_use_checks = list(expected_value["useful_when"])

    evidence_boundary_checks = list(args.exit_gate_evidence_boundary_check)
    if not evidence_boundary_checks:
        evidence_boundary_checks = list(expected_value["evidence_boundary"])

    return {
        "mode": mode,
        "source": source,
        "module_responsibility": args.exit_gate_module_responsibility or args.module_type,
        "downstream_use": args.exit_gate_downstream_use or args.downstream_consumer,
        "hard_veto_checks": hard_veto_checks,
        "value_profile_fit_checks": profile_fit_checks,
        "downstream_use_checks": downstream_use_checks,
        "evidence_boundary_checks": evidence_boundary_checks,
        "exit_blockers": args.exit_gate_exit_blocker,
        "next_round_positive_value_check": args.exit_gate_next_round_positive_value_check
        or "another round requires a named positive-value hypothesis, not only more polish, compliance, or thickness",
        "unresolved_gate_items": unresolved_gate_items,
    }


def build_debug_log(args: argparse.Namespace) -> dict:
    return {
        "enabled": bool(args.debug_log),
        "round_entries": [],
        "script_note": (
            "debug_log is default-off and observation-only. It records candidate pools, gate checks, "
            "veto checks, positive-value hypotheses, and agent decisions when enabled; scripts validate "
            "shape only and never decide candidate quality or exit."
        ),
    }


def build_value_gain_scoring_reference() -> dict:
    return {
        "enabled": True,
        "scale": {
            "min": 0,
            "max": 5,
            "meaning": (
                "0-5 ordinal anchors are a reference, not measurement; scores help compare rounds, "
                "not compute decisions."
            ),
        },
        "dimensions": [
            {
                "id": "thinking_thickness",
                "label": "Thinking Thickness",
                "question": "Does the artifact now have enough constraints, alternatives, failure paths, and evidence boundaries?",
                "low_anchor": "thin structure or fluent summary without usable substrate",
                "mid_anchor": "some real constraints and trade-offs, but downstream still repairs missing judgment",
                "high_anchor": "enough thought substrate for review, action, reuse, or handoff",
            },
            {
                "id": "grounded_insight_yield",
                "label": "Grounded Insight Yield",
                "question": "Does the artifact create non-obvious but anchored understanding or action leverage?",
                "low_anchor": "mostly obvious restatement, polish, or generic best practice",
                "mid_anchor": "one or two useful insights but weak grounding or limited transfer",
                "high_anchor": "changes judgment while staying inside evidence and user constraints",
            },
            {
                "id": "value_density",
                "label": "Value Density",
                "question": "Does each added unit carry enough value relative to reading or execution burden?",
                "low_anchor": "longer, smoother, or more complete-looking without higher utility",
                "mid_anchor": "useful but still padded, repetitive, or uneven",
                "high_anchor": "dense, reviewable, and easy to use without losing necessary context",
            },
        ],
        "round_scores": [],
        "script_note": (
            "value_gain_scoring_reference is enabled by default as an always-on reference. Scripts validate "
            "shape and 0-5 range only; agentic judgment decides score meaning, improvement, sufficiency, and exit."
        ),
    }


def build_pressure(args: argparse.Namespace) -> dict:
    value = args.pressure_value or 2
    presets = {
        1: {
            "typical_rounds": "1",
            "exploration_passes": ["single focused value pass"],
        },
        2: {
            "typical_rounds": "2",
            "exploration_passes": ["core value pass", "exit audit"],
        },
        3: {
            "typical_rounds": "3",
            "exploration_passes": ["core value pass", "candidate comparison", "exit audit"],
        },
        4: {
            "typical_rounds": "4-5",
            "exploration_passes": [
                "candidate comparison",
                "failure pressure",
                "downstream-use audit",
                "compression audit",
            ],
        },
        5: {
            "typical_rounds": "5-7",
            "exploration_passes": [
                "candidate comparison",
                "sentence-function repair",
                "confusion audit",
                "adversarial audit",
                "compression audit",
                "benchmark or human-preference check when available",
            ],
        },
    }
    preset = presets[value]
    return {
        "value": value,
        "mode": "explicit" if args.pressure_value else "default",
        "meaning": (
            "resource investment pressure, not quality score; it guides how much effort the Agent should "
            "spend searching for positive value before exit, but it does not guarantee quality."
        ),
        "typical_rounds": preset["typical_rounds"],
        "exploration_passes": preset["exploration_passes"],
        "script_note": (
            "Scripts record pressure shape only. They cannot decide pressure correctness, required round count, "
            "Gate success, score sufficiency, or whether to exit."
        ),
    }


def build_trace(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    value_profile = build_value_profile(args)
    expected_value = build_expected_value(args, value_profile)
    return {
        "schema_version": "tvg-trace-v0.4",
        "method_version": "Thinking Value-Gain Methodology v0.4",
        "created_at": now,
        "updated_at": now,
        "module": {
            "id": args.module_id,
            "title": args.module_title,
            "type": args.module_type,
            "downstream_consumer": args.downstream_consumer,
            "freeze_granularity": args.freeze_granularity,
        },
        "expected_value": expected_value,
        "value_profile": value_profile,
        "exit_gate": build_exit_gate(args, value_profile, expected_value),
        "debug_log": build_debug_log(args),
        "value_gain_scoring_reference": build_value_gain_scoring_reference(),
        "pressure": build_pressure(args),
        "value_gain": {
            "claimed_value_gain": "",
            "value_gain_types": [],
            "selected_axes": [],
            "veto_constraints": args.veto_constraint,
            "evidence_support": "",
            "remaining_review_bound": [],
        },
        "rounds": [],
        "agentic_exit_audit": {
            "audit_role": "",
            "auditor_independence": "",
            "disagreements": [],
            "veto_constraint_result": "",
            "demo_false_positive_risk": "",
            "overfitting_risk": "",
            "downstream_usability": "",
            "exit_state": "",
            "why_not_another_round": "",
        },
        "script_support": {
            "trace_initialized_by_script": True,
            "script_verdict": "No schema violations were detected only after validation; agentic audit is still required.",
            "script_cannot_decide": [
                "value_gain",
                "veto_constraints",
                "expected_value_correctness",
                "value_profile_truth",
                "default_gate_correctness",
                "exit_gate_success",
                "realization_surface_fit",
                "gain_policy_success",
                "prompt_thickness_success",
                "aesthetic_success",
                "profile_completeness",
                "value_gain_score_correctness",
                "score_improvement",
                "score_sufficiency",
                "score_based_exit",
                "pressure_correctness",
                "round_budget_sufficiency",
                "pressure_based_exit",
                "auditor_independence_requirement",
                "demo_false_positive_risk",
                "overfitting_risk",
                "another_round_value",
                "exit_state",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a TVG trace record.")
    parser.add_argument("--module-id", required=True)
    parser.add_argument("--module-title", required=True)
    parser.add_argument("--module-type", required=True)
    parser.add_argument("--downstream-consumer", default="")
    parser.add_argument("--freeze-granularity", default="")
    parser.add_argument("--veto-constraint", action="append", default=[])
    parser.add_argument("--expected-value-mode", choices=("explicit", "provisional-default", "inferred-with-warning"))
    parser.add_argument("--expected-value-target-artifact")
    parser.add_argument("--expected-value-artifact-job")
    parser.add_argument("--expected-value-useful-when", action="append", default=[])
    parser.add_argument("--expected-value-hard-constraint", action="append", default=[])
    parser.add_argument("--expected-value-evidence-boundary", action="append", default=[])
    parser.add_argument("--expected-value-output-bias")
    parser.add_argument("--expected-value-source")
    parser.add_argument("--expected-value-unresolved-item", action="append", default=[])
    parser.add_argument("--exit-gate-mode", choices=("explicit", "provisional-default", "inferred-with-warning"))
    parser.add_argument("--exit-gate-source")
    parser.add_argument("--exit-gate-module-responsibility")
    parser.add_argument("--exit-gate-downstream-use")
    parser.add_argument("--exit-gate-hard-veto-check", action="append", default=[])
    parser.add_argument("--exit-gate-value-profile-fit-check", action="append", default=[])
    parser.add_argument("--exit-gate-downstream-use-check", action="append", default=[])
    parser.add_argument("--exit-gate-evidence-boundary-check", action="append", default=[])
    parser.add_argument("--exit-gate-exit-blocker", action="append", default=[])
    parser.add_argument("--exit-gate-next-round-positive-value-check")
    parser.add_argument("--exit-gate-unresolved-item", action="append", default=[])
    parser.add_argument("--debug-log", action="store_true")
    parser.add_argument("--pressure-value", type=int, choices=range(1, 6))
    parser.add_argument("--value-profile-mode", choices=("default", "supplied", "inferred-with-warning"))
    parser.add_argument("--value-profile-name")
    parser.add_argument("--value-profile-artifact-job")
    parser.add_argument("--value-profile-good", action="append", default=[])
    parser.add_argument("--value-profile-bad", action="append", default=[])
    parser.add_argument("--value-profile-priority", action="append", default=[])
    parser.add_argument("--value-profile-derived-axis", action="append", default=[])
    parser.add_argument("--value-profile-evidence", action="append", default=[])
    parser.add_argument("--value-profile-prompt-audit-question", action="append", default=[])
    parser.add_argument("--value-profile-image-audit-question", action="append", default=[])
    parser.add_argument("--value-profile-source-note", action="append", default=[])
    parser.add_argument("--profile-veto-constraint", action="append", default=[])
    parser.add_argument("--value-profile-surface-artifact-role")
    parser.add_argument("--value-profile-surface-downstream-use")
    parser.add_argument("--value-profile-surface-observable-unit", action="append", default=[])
    parser.add_argument("--value-profile-surface-granularity-pressure", action="append", default=[])
    parser.add_argument("--value-profile-surface-review-handle", action="append", default=[])
    parser.add_argument("--value-profile-gain-preferred-move", action="append", default=[])
    parser.add_argument("--value-profile-gain-discouraged-move", action="append", default=[])
    parser.add_argument("--value-profile-gain-split-rule", action="append", default=[])
    parser.add_argument("--value-profile-gain-merge-rule", action="append", default=[])
    parser.add_argument("--value-profile-gain-density-guidance", action="append", default=[])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_trace(args), ensure_ascii=False, indent=2) + "\n")
    print(f"initialized_trace: {output}")
    print("script_result: bookkeeping scaffold created; agentic audit is still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
