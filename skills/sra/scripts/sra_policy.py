"""Version-bound calibration selection, independent of reasoning depth.

Absent policy retains v0.3 replay semantics. This module selects review effort; it
never certifies the caller's risk assessment or grants execution authority.
"""
from __future__ import annotations

from typing import Any

PROPORTIONATE_POLICY = "sra.proportionate.v1"
STRUCTURAL_SIGNALS = frozenset({
    "multiple_feasible_bundles", "multiple_contested_resources", "fixed_threshold",
})
RISK_LEVELS = frozenset({"ordinary_reversible", "consequential", "unknown"})
GOAL_GUIDANCE = """Protect the declared objective and non-negotiable constraints first.
Then compare the risk-adjusted marginal value of meaningful resource commitments over
the declared horizon. Direction tests, bottlenecks and windows are value sources, not
automatic priority labels. Unknown or delayed benefit is not zero. Consider maintenance,
learning, care, sustainable capacity and option value where relevant. SRA ranks work,
not human worth. A favorable expected return cannot buy a breach of a protected boundary.
Necessary support is sufficient, not unlimited. Stop analysis when its likely incremental
benefit no longer repays its cost. Do not invent numerical ROI or lower the target."""


def validate_execution_policy(data: dict[str, Any]) -> list[str]:
    if "execution_policy" not in data:
        return []
    policy = data["execution_policy"]
    if not isinstance(policy, dict):
        return ["execution_policy must be an object"]
    fields = {"version", "risk_level", "assessment_basis"}
    errors = []
    if set(policy) != fields:
        errors.append("execution_policy requires only version, risk_level and assessment_basis")
    if policy.get("version") != PROPORTIONATE_POLICY:
        errors.append("execution_policy.version must be " + PROPORTIONATE_POLICY)
    risk = policy.get("risk_level")
    if not isinstance(risk, str) or risk not in RISK_LEVELS:
        errors.append("execution_policy.risk_level must explicitly assess reversibility and consequence")
    basis = policy.get("assessment_basis")
    if not isinstance(basis, str) or not basis.strip():
        errors.append("execution_policy.assessment_basis must name the current source and rationale")
    return errors


def default_view_plan(data: dict[str, Any], mode: str) -> str:
    """Select insurance from declared consequence/contamination, not Full alone."""
    if "execution_policy" not in data:
        return "dual_view" if mode == "full" or data.get("contamination_signals") else "situated_only"
    policy = data.get("execution_policy")
    if validate_execution_policy(data):
        return "dual_view"  # Input validation separately rejects malformed policy.
    assert isinstance(policy, dict)
    explicit_risk = policy["risk_level"] != "ordinary_reversible"
    signals = data.get("escalation_signals", [])
    contexts = data.get("context_items", [])
    state = data.get("state_context", {})
    coverage = data.get("coverage_signals", [])
    if (not isinstance(signals, list) or not all(isinstance(s, str) for s in signals)
            or not isinstance(contexts, list) or not isinstance(state, dict)
            or not isinstance(coverage, list)):
        return "dual_view"
    consequential_signals = set(signals) - STRUCTURAL_SIGNALS
    contaminated_context = any(
        isinstance(item, dict) and item.get("kind") in {"previous_conclusion", "candidate_advocacy"}
        for item in contexts
    )
    historical_spend = bool(state.get("historical_spend"))
    high_impact = "high_impact" in coverage
    if (explicit_risk or consequential_signals or data.get("contamination_signals")
            or contaminated_context or historical_spend or high_impact):
        return "dual_view"
    return "situated_only"


def policy_packet_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Add only the new policy identity; legacy packet bytes remain unchanged."""
    policy = data.get("execution_policy")
    return {"execution_policy": dict(policy)} if isinstance(policy, dict) else {}


def policy_prompt(packet: dict[str, Any]) -> str:
    return "\n" + GOAL_GUIDANCE + "\n" if "execution_policy" in packet else ""
