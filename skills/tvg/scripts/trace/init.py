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
        "prompt_self_audit_questions": [],
        "image_self_audit_questions": [],
        "source_notes": [],
        "profile_veto_constraints": [],
    }


def build_value_profile(args: argparse.Namespace) -> dict:
    profile = default_value_profile()
    if args.value_profile_mode:
        profile["mode"] = args.value_profile_mode
    if args.value_profile_name:
        profile["name"] = args.value_profile_name
    if args.value_profile_artifact_job:
        profile["artifact_job"] = args.value_profile_artifact_job
    if args.value_profile_good:
        profile["good_means"] = args.value_profile_good
    if args.value_profile_bad:
        profile["bad_means"] = args.value_profile_bad
    if args.value_profile_priority:
        profile["priority_order"] = args.value_profile_priority
    if args.value_profile_derived_axis:
        profile["derived_axes"] = args.value_profile_derived_axis
    if args.value_profile_evidence:
        profile["evidence_basis"] = args.value_profile_evidence
    if args.value_profile_prompt_audit_question:
        profile["prompt_self_audit_questions"] = args.value_profile_prompt_audit_question
    if args.value_profile_image_audit_question:
        profile["image_self_audit_questions"] = args.value_profile_image_audit_question
    if args.value_profile_source_note:
        profile["source_notes"] = args.value_profile_source_note
    if args.profile_veto_constraint:
        profile["profile_veto_constraints"] = args.profile_veto_constraint
    return profile


def build_trace(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "tvg-trace-v0.3",
        "method_version": "Thinking Value-Gain Methodology v0.3",
        "created_at": now,
        "updated_at": now,
        "module": {
            "id": args.module_id,
            "title": args.module_title,
            "type": args.module_type,
            "downstream_consumer": args.downstream_consumer,
            "freeze_granularity": args.freeze_granularity,
        },
        "value_profile": build_value_profile(args),
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
                "value_profile_truth",
                "aesthetic_success",
                "profile_completeness",
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
