#!/usr/bin/env python3
"""Deterministically materialize the Beta.2 case metadata matrix.

Prompt content is kept in provenance-specific stores.  This builder emits only the
case contract and source receipt, so sealed and replay content cannot leak into the
implementation repository through the matrix.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"

SEALED_RECEIPTS = {
    "b2-shadow-owner-overlap": "7f0894121c8764ce91e1431017cd64b99b9dccaaa5b45c96b0fb712149784cf7",
    "b2-shadow-passive-intersection": "6b984ddaf50f36e11671c46f7e158819a8da2e2fe24f58f483bbda145abbc944",
    "b2-shadow-anti-rename": "62467e8636ac30f104fbd6b664bcc712a2dc64329d80f0c7646f2d6a622c682d",
    "b2-shadow-near-negative": "7a2336cf7a28d4b2a6abdb277b0c6ef2f02bf126ba8130fba3f31f49c0d4da8a",
}
REPLAY_RECEIPTS = {
    "b2-replay-architecture-review": "06cae09f78d92a92bea840f360d06c23d7fda7ff37100366597e7c87ee69edda",
    "b2-replay-debugging-session": "44f2b66ba1805a6e17f7cc0f2d9178bb4337277d19817d95289b355bf123c551",
}
LIFECYCLE_EVENTS = {
    "startup": ["session-start", "before-route", "before-answer"],
    "resume": ["session-start", "before-continue", "before-answer"],
    "clear": ["session-start", "before-route", "before-answer"],
    "compact": ["session-start", "before-continue", "before-answer"],
}


def source_for(case_id: str, provenance: str) -> dict[str, Any]:
    if provenance == "public-regression":
        return {
            "locator": f"tests/judgment_benchmark_50_cases.jsonl#{case_id}",
            "receipt_sha256": None,
            "implementation_visible": True,
            "run_eligibility": "eligible",
        }
    if provenance == "development":
        return {
            "locator": f"fixtures/development-cases.jsonl#{case_id}",
            "receipt_sha256": None,
            "implementation_visible": True,
            "run_eligibility": "eligible",
        }
    if provenance == "sealed-shadow":
        return {
            "locator": f"fixtures/sealed-shadow-index.json#{case_id}",
            "receipt_sha256": SEALED_RECEIPTS[case_id],
            "implementation_visible": False,
            "run_eligibility": "requires-custodian-attestation",
        }
    if provenance == "real-task-replay":
        return {
            "locator": f"fixtures/real-task-replay-index.json#{case_id}",
            "receipt_sha256": REPLAY_RECEIPTS[case_id],
            "implementation_visible": False,
            "run_eligibility": "requires-user-authorization",
        }
    raise ValueError(f"unsupported provenance: {provenance}")


def matrix_case(
    case_id: str,
    title: str,
    *,
    provenance: str = "development",
    source_case_id: str | None = None,
    case_type: str = "positive",
    entry_mode: str = "owner-direct",
    lifecycle_path: str = "startup",
    owner: str,
    accepted_owners: list[str] | None = None,
    primitives: list[str] | None = None,
    visible_action: str | None = None,
    required_loads: list[str] | None = None,
    allowed_loads: list[str] | None = None,
    stay_asleep: bool = False,
    evidence_first: bool = False,
    risk: str = "medium",
    risk_reason: str = "development-visible wording can tune implementation behavior",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    source_id = source_case_id or case_id
    obligations = primitives or []
    loads = required_loads or []
    allowed = allowed_loads if allowed_loads is not None else list(loads)
    coverage_tags = [
        f"provenance:{provenance}",
        f"entry:{entry_mode}",
        f"lifecycle:{lifecycle_path}",
        *[f"primitive:{primitive}" for primitive in obligations],
        *(tags or []),
    ]
    return {
        "case_id": case_id,
        "title": title,
        "case_type": case_type,
        "provenance": provenance,
        "source": source_for(source_id, provenance),
        "entry_mode": entry_mode,
        "lifecycle_path": lifecycle_path,
        "expected_execution_owner": owner,
        "accepted_execution_owners": accepted_owners or [owner],
        "expected_primitive_obligations": obligations,
        "required_visible_action": visible_action,
        "required_skill_loads": loads,
        "allowed_skill_loads": allowed,
        "stay_asleep_expected": stay_asleep,
        "expected_lifecycle_events": LIFECYCLE_EVENTS[lifecycle_path],
        "evidence_first_expected": evidence_first,
        "contamination_risk": {"level": risk, "reason": risk_reason},
        "coverage_tags": coverage_tags,
    }


def cases() -> list[dict[str, Any]]:
    return [
        matrix_case(
            "b2-public-frame",
            "Public regression: local diagnosis must not capture the whole incident",
            provenance="public-regression",
            source_case_id="mtj-001",
            entry_mode="passive-kernel",
            owner="direct_answer",
            primitives=["input_framing_audit"],
            visible_action="Bound the indexing hypothesis before proposing changes.",
            required_loads=[],
            allowed_loads=[],
            risk="high",
            risk_reason="public expected behavior is visible to implementers",
        ),
        matrix_case(
            "b2-public-whole",
            "Public regression: a local mechanism cannot claim whole-agent essence",
            provenance="public-regression",
            source_case_id="mtj-012",
            entry_mode="passive-kernel",
            owner="direct_answer",
            primitives=["whole_elephant"],
            visible_action="Separate the local mechanism from the whole-object definition.",
            required_loads=[],
            allowed_loads=[],
            risk="high",
            risk_reason="public expected behavior is visible to implementers",
        ),
        matrix_case(
            "b2-public-edsp",
            "Public regression: reconstruct a malformed binary",
            provenance="public-regression",
            source_case_id="mtj-017",
            owner="edsp",
            required_loads=["edsp"],
            allowed_loads=["edsp"],
            risk="high",
            risk_reason="public rubric and historical outputs are visible",
            tags=["owner:edsp"],
        ),
        matrix_case(
            "b2-public-anti-spiral",
            "Public regression: stop a third same-object prompt patch",
            provenance="public-regression",
            source_case_id="mtj-033",
            entry_mode="passive-kernel",
            owner="direct_judgment",
            accepted_owners=["direct_judgment", "3l5s", "tplan"],
            primitives=["anti_spiral"],
            visible_action="Pause the next local patch and inspect the upstream cause.",
            required_loads=[],
            allowed_loads=["3l5s", "tplan"],
            risk="high",
            risk_reason="public Anti-Spiral trigger is known to implementers",
            tags=["anti-spiral:same-object-third-touch"],
        ),
        matrix_case(
            "b2-dev-owner-3l5s",
            "3L5S owns an undefined repeated-failure problem",
            owner="3l5s",
            primitives=["input_framing_audit"],
            visible_action="Define a falsifiable problem before task breakdown.",
            required_loads=["3l5s"],
            allowed_loads=["3l5s"],
            tags=["owner:3l5s", "direct-owner-passive-intersection"],
        ),
        matrix_case(
            "b2-dev-owner-edsp",
            "EDSP owns structural ambiguity with situated decision pressure",
            owner="edsp",
            primitives=["decision_context_calibration"],
            visible_action="Reconstruct the decision axes before selecting a scenario.",
            required_loads=["edsp"],
            allowed_loads=["edsp"],
            tags=["owner:edsp", "direct-owner-passive-intersection"],
        ),
        matrix_case(
            "b2-dev-owner-sela",
            "SELA owns system-efficiency versus local-advantage direction",
            owner="sela",
            primitives=["whole_elephant"],
            visible_action="Separate local excellence from system-level direction pressure.",
            required_loads=["sela"],
            allowed_loads=["sela"],
            tags=["owner:sela", "direct-owner-passive-intersection"],
        ),
        matrix_case(
            "b2-dev-owner-mpg",
            "MPG owns path carrying after direction is fixed",
            owner="mpg",
            primitives=["decision_context_calibration"],
            visible_action="Name carrier exposure and decision-changing triggers.",
            required_loads=["mpg"],
            allowed_loads=["mpg"],
            tags=["owner:mpg", "direct-owner-passive-intersection"],
        ),
        matrix_case(
            "b2-dev-owner-wae",
            "WAE owns an agentic controller mismatch",
            owner="wae",
            primitives=["input_framing_audit"],
            visible_action="Reassign control among agent judgment, workflow, and evidence.",
            required_loads=["wae"],
            allowed_loads=["wae"],
            tags=["owner:wae", "direct-owner-passive-intersection"],
        ),
        matrix_case(
            "b2-dev-owner-tvg",
            "TVG owns bounded value strengthening",
            owner="tvg",
            visible_action="Strengthen evidence, trade-offs, and handoff without reopening scope.",
            required_loads=["tvg"],
            allowed_loads=["tvg"],
            tags=["owner:tvg"],
        ),
        matrix_case(
            "b2-dev-owner-tplan",
            "tplan owns Mission runtime and authority",
            owner="tplan",
            primitives=["anti_spiral"],
            visible_action="Create evidence-linked runtime state and an explicit authority gate.",
            required_loads=["tplan"],
            allowed_loads=["tplan"],
            tags=["owner:tplan", "direct-owner-passive-intersection"],
        ),
        matrix_case(
            "b2-dev-arbitrator-overlap",
            "Genuine owner overlap reaches the thin arbitrator",
            entry_mode="arbitrator",
            owner="using-mindthus",
            accepted_owners=["using-mindthus"],
            visible_action="Choose one execution owner and preserve remaining obligations.",
            required_loads=["using-mindthus"],
            allowed_loads=["using-mindthus", "sela", "mpg", "wae"],
            tags=["owner-overlap:genuine"],
        ),
        matrix_case(
            "b2-dev-evidence-first",
            "Unknown incident requires facts before a method",
            entry_mode="evidence-first",
            owner="information_acquisition",
            primitives=["evidence_first"],
            visible_action="Request or inspect the decision-changing logs before diagnosing.",
            required_loads=[],
            allowed_loads=[],
            evidence_first=True,
        ),
        matrix_case(
            "b2-dev-multi-primitive",
            "One direct answer carries Frame, Whole, and Decision Context",
            entry_mode="passive-kernel",
            owner="direct_judgment",
            primitives=[
                "input_framing_audit",
                "whole_elephant",
                "decision_context_calibration",
            ],
            visible_action="Preserve one thesis while satisfying all three constraints.",
            required_loads=[],
            allowed_loads=[],
            tags=["multi-obligation"],
        ),
        matrix_case(
            "b2-dev-anti-third-touch",
            "Anti-Spiral fires on the third same-object local repair",
            entry_mode="passive-kernel",
            lifecycle_path="resume",
            owner="direct_judgment",
            primitives=["anti_spiral"],
            visible_action="Stop the next local addition and move upstream.",
            required_loads=[],
            allowed_loads=["3l5s", "tplan"],
            tags=["anti-spiral:same-object-third-touch"],
        ),
        matrix_case(
            "b2-dev-anti-renamed-object",
            "Anti-Spiral tracks object identity across renaming",
            entry_mode="passive-kernel",
            lifecycle_path="resume",
            owner="direct_judgment",
            primitives=["anti_spiral"],
            visible_action="Treat the renamed carrier as the same underlying object and pause.",
            required_loads=[],
            allowed_loads=["3l5s", "tplan"],
            tags=["anti-spiral:renamed-same-object"],
        ),
        matrix_case(
            "b2-dev-anti-distinct-objects",
            "Anti-Spiral stays asleep across distinct work objects",
            case_type="negative_control",
            entry_mode="stay-asleep",
            lifecycle_path="resume",
            owner="direct_execution",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            tags=["anti-spiral:distinct-objects", "near-negative:normal-iterative-debugging"],
        ),
        matrix_case(
            "b2-dev-anti-new-evidence",
            "Anti-Spiral stays asleep when each repeat has decision-changing evidence",
            case_type="negative_control",
            entry_mode="stay-asleep",
            lifecycle_path="resume",
            owner="direct_debugging",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            tags=["anti-spiral:repeated-with-new-evidence", "near-negative:sufficient-evidence"],
        ),
        matrix_case(
            "b2-dev-near-local-scope",
            "Legitimate local scope does not trigger whole-object reconstruction",
            case_type="negative_control",
            entry_mode="stay-asleep",
            owner="direct_answer",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            tags=["near-negative:legitimate-local-scope"],
        ),
        matrix_case(
            "b2-dev-near-sufficient-evidence",
            "Sufficient evidence goes directly to repair",
            case_type="negative_control",
            entry_mode="stay-asleep",
            owner="direct_debugging",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            tags=["near-negative:sufficient-evidence"],
        ),
        matrix_case(
            "b2-dev-near-user-tradeoff",
            "Explicit user-owned reversible trade-off remains authoritative",
            case_type="negative_control",
            entry_mode="stay-asleep",
            owner="direct_execution",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            tags=["near-negative:explicit-user-owned-tradeoff"],
        ),
        matrix_case(
            "b2-dev-near-normal-debugging",
            "Independent debugging defects are not a same-object spiral",
            case_type="negative_control",
            entry_mode="stay-asleep",
            lifecycle_path="resume",
            owner="direct_debugging",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            tags=["near-negative:normal-iterative-debugging", "anti-spiral:distinct-objects"],
        ),
        matrix_case(
            "b2-dev-lifecycle-resume",
            "Resume restores Mission state before continuation",
            lifecycle_path="resume",
            owner="tplan",
            visible_action="Recover active task, evidence, and authority before continuing.",
            required_loads=["tplan"],
            allowed_loads=["tplan"],
            tags=["owner:tplan"],
        ),
        matrix_case(
            "b2-dev-lifecycle-clear",
            "Clear reinjects Kernel obligations without stale conclusions",
            entry_mode="passive-kernel",
            lifecycle_path="clear",
            owner="direct_answer",
            primitives=["input_framing_audit"],
            visible_action="Re-evaluate the current frame after clear.",
            required_loads=[],
            allowed_loads=[],
        ),
        matrix_case(
            "b2-dev-lifecycle-compact",
            "Compact preserves active constraints and stop conditions",
            entry_mode="passive-kernel",
            lifecycle_path="compact",
            owner="direct_execution",
            primitives=["decision_context_calibration"],
            visible_action="Carry the active decision context across compaction.",
            required_loads=[],
            allowed_loads=[],
        ),
        matrix_case(
            "b2-shadow-owner-overlap",
            "Sealed owner-overlap shadow receipt",
            provenance="sealed-shadow",
            entry_mode="arbitrator",
            owner="using-mindthus",
            visible_action="Resolve genuine ambiguity without becoming a mandatory router.",
            required_loads=["using-mindthus"],
            allowed_loads=["using-mindthus", "sela", "mpg"],
            risk="low",
            risk_reason="prompt content is absent from the implementation repository",
            tags=["owner-overlap:genuine"],
        ),
        matrix_case(
            "b2-shadow-passive-intersection",
            "Sealed direct-owner and multiple-passive intersection receipt",
            provenance="sealed-shadow",
            entry_mode="passive-kernel",
            owner="mpg",
            primitives=["whole_elephant", "decision_context_calibration"],
            visible_action="Keep owner judgment distinct from both passive constraints.",
            required_loads=["mpg"],
            allowed_loads=["mpg"],
            risk="low",
            risk_reason="prompt content is absent from the implementation repository",
            tags=["owner:mpg", "multi-obligation", "direct-owner-passive-intersection"],
        ),
        matrix_case(
            "b2-shadow-anti-rename",
            "Sealed renamed-object Anti-Spiral receipt",
            provenance="sealed-shadow",
            entry_mode="passive-kernel",
            lifecycle_path="compact",
            owner="direct_judgment",
            primitives=["anti_spiral"],
            visible_action="Detect same-object continuity without keyword matching.",
            required_loads=[],
            allowed_loads=["3l5s", "tplan"],
            risk="low",
            risk_reason="prompt content is absent from the implementation repository",
            tags=["anti-spiral:renamed-same-object"],
        ),
        matrix_case(
            "b2-shadow-near-negative",
            "Sealed false-wakeup near-negative receipt",
            provenance="sealed-shadow",
            case_type="negative_control",
            entry_mode="stay-asleep",
            owner="direct_execution",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            risk="low",
            risk_reason="prompt content is absent from the implementation repository",
            tags=["near-negative:explicit-user-owned-tradeoff"],
        ),
        matrix_case(
            "b2-replay-architecture-review",
            "Restricted real-task architecture review replay receipt",
            provenance="real-task-replay",
            entry_mode="arbitrator",
            lifecycle_path="compact",
            owner="using-mindthus",
            primitives=["input_framing_audit", "whole_elephant"],
            visible_action="Preserve the real task's authority and evidence boundaries.",
            required_loads=["using-mindthus"],
            allowed_loads=["using-mindthus", "edsp", "wae"],
            risk="low",
            risk_reason="task content is external and requires user authorization",
            tags=["owner-overlap:genuine", "multi-obligation"],
        ),
        matrix_case(
            "b2-replay-debugging-session",
            "Restricted real-task debugging replay receipt",
            provenance="real-task-replay",
            case_type="negative_control",
            entry_mode="stay-asleep",
            lifecycle_path="resume",
            owner="direct_debugging",
            required_loads=[],
            allowed_loads=[],
            stay_asleep=True,
            risk="low",
            risk_reason="task content is external and requires user authorization",
            tags=["near-negative:normal-iterative-debugging", "anti-spiral:repeated-with-new-evidence"],
        ),
    ]


def payload() -> dict[str, Any]:
    return {
        "schema_version": "mindthus-beta2-case-matrix-v0.1",
        "coverage_requirements": {
            "owners": ["3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan"],
            "primitives": [
                "input_framing_audit",
                "whole_elephant",
                "decision_context_calibration",
                "anti_spiral",
                "evidence_first",
            ],
            "lifecycle_paths": ["startup", "resume", "clear", "compact"],
            "near_negatives": [
                "legitimate-local-scope",
                "sufficient-evidence",
                "explicit-user-owned-tradeoff",
                "normal-iterative-debugging",
            ],
            "anti_spiral_sequences": [
                "same-object-third-touch",
                "renamed-same-object",
                "distinct-objects",
                "repeated-with-new-evidence",
            ],
            "provenance_classes": [
                "public-regression",
                "development",
                "sealed-shadow",
                "real-task-replay",
            ],
            "entry_modes": [
                "owner-direct",
                "passive-kernel",
                "arbitrator",
                "stay-asleep",
                "evidence-first",
            ],
        },
        "cases": cases(),
    }


def main() -> int:
    DEFAULT_OUT.write_text(
        json.dumps(payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(DEFAULT_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
