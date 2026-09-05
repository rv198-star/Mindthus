#!/usr/bin/env python3
"""Canonical SRA v0.3 domain vocabulary and deterministic invariants."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import math
from typing import Any, Iterable

INPUT_SCHEMA = "sra.decision-context-input.v0.3"
RUN_SCHEMA = "sra.context-calibrated-run.v0.3"
ADMISSION_SCHEMA = "sra.context-admission.v0.3"
BASE_PACKET_SCHEMA = "sra.decision-base-packet.v0.3"
COVERAGE_PACKET_SCHEMA = "sra.coverage-packet.v0.3"
CHALLENGE_PACKET_SCHEMA = "sra.challenge-packet.v0.3"
SITUATED_PACKET_SCHEMA = "sra.situated-packet.v0.3"
COVERAGE_JUDGMENT_SCHEMA = "sra.coverage-judgment.v0.3"
CHALLENGE_JUDGMENT_SCHEMA = "sra.challenge-judgment.v0.3"
SITUATED_JUDGMENT_SCHEMA = "sra.situated-judgment.v0.3"
COMPARISON_SCHEMA = "sra.view-comparison.v0.3"
RECONCILIATION_PACKET_SCHEMA = "sra.reconciliation-packet.v0.3"
RECONCILIATION_JUDGMENT_SCHEMA = "sra.reconciliation-judgment.v0.3"
FINAL_DECISION_SCHEMA = "sra.final-decision.v0.3"
CHECK_REPORT_SCHEMA = "sra.run-check.v0.3"
TRACE_SCHEMA = "sra.runtime-event.v0.3"
WORKFLOW_BLOCKED_SCHEMA = "sra.workflow-blocked-decision.v0.3"
FIDELITY_SCHEMA = "sra-fidelity-v0.2"

MODES = {"auto", "lite", "full"}
VIEW_PLANS = {"auto", "situated_only", "dual_view"}
COVERAGE_PLANS = {"auto", "skip", "required"}
CARRIERS = {"packet_bound", "fresh_subagent", "ephemeral_cli"}

FULL_ESCALATION_SIGNALS = {
    "direction_changing_uncertainty", "multiple_feasible_bundles",
    "major_commitment", "irreversible_exposure", "multiple_contested_resources",
    "fixed_threshold", "material_switching_cost", "path_dependency",
    "incomparable_candidate", "more_than_one_tranche",
}
CONTAMINATION_SIGNALS = {
    "active_task_richness", "prior_agent_conclusion",
    "candidate_advocacy_asymmetry", "cross_project_context",
    "sunk_cost_narrative", "presentation_order_bias",
    "user_factual_frame_without_evidence", "explicit_independent_judgment_request",
    "major_redirection_of_invested_work",
}
COVERAGE_SIGNALS = {
    "candidate_surface_uncertain", "source_inventory_incomplete",
    "cross_project_scope", "major_omission_risk", "high_impact",
}

CONTEXT_KINDS = {
    "user_constraint", "authority_decision", "observed_fact", "runtime_evidence",
    "assumption", "historical_context", "candidate_advocacy",
    "previous_conclusion", "ambient_inference",
}
PROTECTED_CONTEXT_KINDS = {"user_constraint", "authority_decision"}
ADMISSION_BY_KIND = {
    "user_constraint": ("admitted", "decision_constraint"),
    "authority_decision": ("admitted", "scoped_authority"),
    "observed_fact": ("admitted", "evidence_claim"),
    "runtime_evidence": ("admitted", "evidence_claim"),
    "assumption": ("admitted", "explicit_assumption"),
    "candidate_advocacy": ("quarantined", "candidate_claim_only"),
    "previous_conclusion": ("quarantined", "prior_conclusion_only"),
    "ambient_inference": ("quarantined", "ambient_inference_only"),
}
FRAME_STRING_FIELDS = (
    "parent_objective", "target_threshold", "time_window", "risk_floor",
    "decision_owner", "evidence_ceiling",
)
CANDIDATE_STRING_FIELDS = (
    "candidate_id", "action_statement", "expected_target_effect",
    "deadline_or_window", "downside", "reversibility",
)
CANDIDATE_LIST_FIELDS = (
    "depends_on", "unlocks", "substitutes_for", "evidence_refs", "assumption_refs",
)
FORBIDDEN_CANDIDATE_FIELDS = {
    "candidate_role", "dependency_or_bundle_role", "hard_gate",
    "threshold_essential", "enabler_or_bottleneck", "value_expanding",
    "maintenance_or_option", "defer_or_stop", "priority", "priority_score",
    "roi_score",
}
QUANTITY_KINDS = {"exact", "bounded", "ordinal", "indivisible"}
RESOURCE_FAMILIES = {"measured", "ordinal", "indivisible"}
FEASIBILITY = {"feasible", "conditional", "infeasible", "unclear"}
CANDIDATE_ROLES = {
    "hard_gate", "threshold_essential", "enabler_or_bottleneck",
    "value_expanding", "maintenance_or_option", "defer_or_stop", "unclear",
}
CONTRACTION_RESULTS = {
    "retained", "capped", "downgraded", "substituted", "removed", "unclear",
}
ALLOCATION_POSTURES = {"floor", "maintenance", "candidate", "defer", "stop"}
RESERVED_CANDIDATE_IDS = {"none", "reserve"}
RESERVED_BUNDLE_IDS = {"none"}
ALLOCATION_OUTCOMES = {"allocate", "conditional", "infeasible", "blocked"}
RECONCILIATION_OUTCOMES = ALLOCATION_OUTCOMES | {"request_missing_context"}
BUNDLE_FEASIBILITY = FEASIBILITY
DOMINANCE_STATUSES = {
    "non_dominated", "dominated", "infeasible", "conditional", "unclear",
}
AUTHORIZATION_HORIZONS = {
    "one_action", "one_tranche", "until_named_checkpoint",
    "bounded_decision_window",
}
LITE_AUTHORIZATION_HORIZONS = {
    "one_action", "one_tranche", "until_named_checkpoint",
}
COVERAGE_OUTCOMES = {
    "packet_ready", "packet_ready_with_warning", "packet_incomplete",
}
FINALIZATION_STATUSES = {"pending", "finalized", "conditional", "blocked"}
STATE_ITEM_KIND_BY_COLLECTION = {
    "switching_costs": "switching_cost", "reusable_assets": "reusable_asset",
    "remaining_costs": "remaining_cost", "historical_spend": "sunk_cost",
    "commitments": "current_commitment",
}
STATE_CONSIDERATION_KINDS = {
    "active_path_identity", "switching_cost", "reusable_asset", "remaining_cost",
    "current_commitment", "authority_boundary", "sunk_cost_rejected", "none",
}
STATE_REF_KINDS_BY_CONSIDERATION = {
    "active_path_identity": {"active_candidate"},
    "switching_cost": {"switching_cost"},
    "reusable_asset": {"reusable_asset"},
    "remaining_cost": {"remaining_cost"},
    "current_commitment": {"current_commitment"},
    "authority_boundary": {"current_commitment"},
    "sunk_cost_rejected": {"sunk_cost"},
    "none": set(),
}
COMPARISON_FIELDS = (
    "allocation_outcome", "candidate_assessments", "bundle_decision", "allocation_ledger",
    "next_tranche", "investment_ceiling", "authorization_horizon", "reserve",
    "missing_information", "dependency_resolutions",
)
OVERRIDE_FIELDS = (
    "override_reason", "approved_by", "authority_ref", "risk_acceptance_scope",
    "expiry",
)


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(is_non_empty_string(item) for item in value)


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _positive_number(value: Any) -> bool:
    return is_number(value) and value > 0


def is_utc_timestamp_or_timeless(value: Any) -> bool:
    if value == "timeless":
        return True
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def validate_quantity_contract(value: Any, path: str, findings: list[str]) -> None:
    if not isinstance(value, dict):
        findings.append(f"{path} must be a quantity-contract object")
        return
    family = value.get("family")
    if family not in RESOURCE_FAMILIES:
        findings.append(
            f"{path}.family must be one of: {', '.join(sorted(RESOURCE_FAMILIES))}"
        )
        return
    allowed = {
        "measured": {"family", "aggregation", "unit"},
        "ordinal": {"family", "aggregation", "scale"},
        "indivisible": {"family", "aggregation", "blocks"},
    }[str(family)]
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        findings.append(f"{path} contains unsupported fields for {family}: {unexpected}")
    required_aggregation = {
        "measured": "sum",
        "ordinal": "exclusive",
        "indivisible": "set",
    }[str(family)]
    if value.get("aggregation") != required_aggregation:
        findings.append(
            f"{path}.aggregation must be {required_aggregation!r} for {family} resources"
        )
    if family == "measured":
        if not is_non_empty_string(value.get("unit")):
            findings.append(f"{path}.unit must be a non-empty string for measured resources")
    elif family == "ordinal":
        scale = value.get("scale")
        if not is_string_list(scale) or len(scale) < 2:
            findings.append(f"{path}.scale must contain at least two ordered labels")
        elif len(set(scale)) != len(scale):
            findings.append(f"{path}.scale must not contain duplicate labels")
    else:
        blocks = value.get("blocks")
        if not is_string_list(blocks) or not blocks:
            findings.append(f"{path}.blocks must be a non-empty list")
        elif len(set(blocks)) != len(blocks):
            findings.append(f"{path}.blocks must not contain duplicate block IDs")


def validate_quantity(
    value: Any,
    path: str,
    findings: list[str],
    *,
    allow_zero: bool = False,
) -> None:
    if not isinstance(value, dict):
        findings.append(f"{path} must be a quantity object")
        return
    kind = value.get("quantity_kind")
    if kind not in QUANTITY_KINDS:
        findings.append(
            f"{path}.quantity_kind must be one of: {', '.join(sorted(QUANTITY_KINDS))}"
        )
        return
    allowed_by_kind = {
        "exact": {"quantity_kind", "amount", "unit"},
        "bounded": {"quantity_kind", "lower_bound", "upper_bound", "unit"},
        "ordinal": {"quantity_kind", "level"},
        "indivisible": {"quantity_kind", "blocks"},
    }
    unexpected = sorted(set(value) - allowed_by_kind[str(kind)])
    if unexpected:
        findings.append(f"{path} contains unsupported fields for {kind}: {unexpected}")
    if kind == "exact":
        amount = value.get("amount")
        if (
            isinstance(amount, (int, float))
            and not isinstance(amount, bool)
            and not math.isfinite(float(amount))
        ):
            findings.append(f"{path}.amount must be finite")
        elif allow_zero:
            if not is_number(amount) or amount < 0:
                findings.append(
                    f"{path}.amount must be a non-negative number for exact quantity"
                )
        elif not _positive_number(amount):
            findings.append(f"{path}.amount must be a positive number for exact quantity")
        if not is_non_empty_string(value.get("unit")):
            findings.append(f"{path}.unit must be a non-empty string for exact quantity")
    elif kind == "bounded":
        lower, upper = value.get("lower_bound"), value.get("upper_bound")
        if (
            isinstance(lower, (int, float))
            and not isinstance(lower, bool)
            and not math.isfinite(float(lower))
        ):
            findings.append(f"{path}.lower_bound must be finite")
        elif not is_number(lower) or lower < 0:
            findings.append(f"{path}.lower_bound must be a non-negative number")
        if (
            isinstance(upper, (int, float))
            and not isinstance(upper, bool)
            and not math.isfinite(float(upper))
        ):
            findings.append(f"{path}.upper_bound must be finite")
        elif not _positive_number(upper):
            findings.append(f"{path}.upper_bound must be a positive number")
        if is_number(lower) and is_number(upper) and lower > upper:
            findings.append(f"{path}.lower_bound must not exceed upper_bound")
        if not is_non_empty_string(value.get("unit")):
            findings.append(f"{path}.unit must be a non-empty string for bounded quantity")
    elif kind == "ordinal":
        if not is_non_empty_string(value.get("level")):
            findings.append(f"{path}.level must be a non-empty string")
    else:
        blocks = value.get("blocks")
        if not is_string_list(blocks) or not blocks:
            findings.append(f"{path}.blocks must be a non-empty list")
        elif len(set(blocks)) != len(blocks):
            findings.append(f"{path}.blocks must not contain duplicates")


def validate_quantity_for_contract(
    value: Any,
    contract: Any,
    path: str,
    findings: list[str],
    *,
    allow_zero: bool = False,
) -> None:
    before = len(findings)
    validate_quantity(value, path, findings, allow_zero=allow_zero)
    validate_quantity_contract(contract, f"{path}.contract", findings)
    if len(findings) != before or not isinstance(value, dict) or not isinstance(contract, dict):
        return
    kind = value.get("quantity_kind")
    family = contract.get("family")
    if family == "measured":
        if kind not in {"exact", "bounded"}:
            findings.append(f"{path} must use exact or bounded quantity for measured resource")
        elif value.get("unit") != contract.get("unit"):
            findings.append(
                f"{path}.unit must match measured resource unit {contract.get('unit')!r}"
            )
    elif family == "ordinal":
        if kind != "ordinal":
            findings.append(f"{path} must use ordinal quantity for ordinal resource")
        elif value.get("level") not in contract.get("scale", []):
            findings.append(f"{path}.level must use the declared ordinal scale")
    elif family == "indivisible":
        if kind != "indivisible":
            findings.append(f"{path} must use indivisible quantity for indivisible resource")
        else:
            unknown = sorted(set(value.get("blocks", [])) - set(contract.get("blocks", [])))
            if unknown:
                findings.append(f"{path}.blocks contains unknown block IDs: {unknown}")


def _exact_schema(unit: str | None = None) -> dict[str, Any]:
    unit_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    if unit is not None:
        unit_schema = {"type": "string", "const": unit}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["quantity_kind", "amount", "unit"],
        "properties": {
            "quantity_kind": {"type": "string", "const": "exact"},
            "amount": {"type": "number", "exclusiveMinimum": 0},
            "unit": unit_schema,
        },
    }


def _bounded_schema(unit: str | None = None) -> dict[str, Any]:
    unit_schema: dict[str, Any] = {"type": "string", "minLength": 1}
    if unit is not None:
        unit_schema = {"type": "string", "const": unit}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["quantity_kind", "lower_bound", "upper_bound", "unit"],
        "properties": {
            "quantity_kind": {"type": "string", "const": "bounded"},
            "lower_bound": {"type": "number", "minimum": 0},
            "upper_bound": {"type": "number", "exclusiveMinimum": 0},
            "unit": unit_schema,
        },
    }


def quantity_schema(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    if contract is None:
        return {
            "oneOf": [
                _exact_schema(),
                _bounded_schema(),
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["quantity_kind", "level"],
                    "properties": {
                        "quantity_kind": {"type": "string", "const": "ordinal"},
                        "level": {"type": "string", "minLength": 1},
                    },
                },
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["quantity_kind", "blocks"],
                    "properties": {
                        "quantity_kind": {"type": "string", "const": "indivisible"},
                        "blocks": {
                            "type": "array", "minItems": 1, "uniqueItems": True,
                            "items": {"type": "string", "minLength": 1},
                        },
                    },
                },
            ]
        }
    family = contract.get("family")
    if family == "measured":
        unit = str(contract.get("unit", ""))
        return {"oneOf": [_exact_schema(unit), _bounded_schema(unit)]}
    if family == "ordinal":
        return {
            "type": "object", "additionalProperties": False,
            "required": ["quantity_kind", "level"],
            "properties": {
                "quantity_kind": {"type": "string", "const": "ordinal"},
                "level": {"type": "string", "enum": list(contract.get("scale", []))},
            },
        }
    return {
        "type": "object", "additionalProperties": False,
        "required": ["quantity_kind", "blocks"],
        "properties": {
            "quantity_kind": {"type": "string", "const": "indivisible"},
            "blocks": {
                "type": "array", "minItems": 1, "uniqueItems": True,
                "items": {"type": "string", "enum": list(contract.get("blocks", []))},
            },
        },
    }


def resource_contracts(resource_pools: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(pool["resource_id"]): dict(pool.get("quantity_contract", {}))
        for pool in resource_pools
        if isinstance(pool, dict) and is_non_empty_string(pool.get("resource_id"))
    }


def resource_allocation_schema(
    resource_pools: Iterable[dict[str, Any]], *, min_items: int = 0
) -> dict[str, Any]:
    pools = [pool for pool in resource_pools if isinstance(pool, dict)]
    variants = []
    for pool in pools:
        variants.append({
            "type": "object",
            "additionalProperties": False,
            "required": ["resource_id", "quantity"],
            "properties": {
                "resource_id": {"type": "string", "const": pool.get("resource_id")},
                "quantity": quantity_schema(pool.get("quantity_contract", {})),
            },
        })
    return {
        "type": "array", "minItems": min_items, "uniqueItems": True,
        "items": {"oneOf": variants},
    }


def validate_resource_allocations(
    value: Any,
    path: str,
    *,
    resource_pools: Iterable[dict[str, Any]],
    findings: list[str],
    require_non_empty: bool = False,
) -> None:
    pools = [pool for pool in resource_pools if isinstance(pool, dict)]
    contracts = resource_contracts(pools)
    if not isinstance(value, list):
        findings.append(f"{path} must be a list")
        return
    if require_non_empty and not value:
        findings.append(f"{path} must not be empty")
    seen: set[str] = set()
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            findings.append(f"{item_path} must be an object")
            continue
        unexpected = sorted(set(item) - {"resource_id", "quantity"})
        if unexpected:
            findings.append(f"{item_path} contains unsupported fields: {unexpected}")
        resource_id = item.get("resource_id")
        if resource_id not in contracts:
            findings.append(f"{item_path}.resource_id must reference a declared resource pool")
            continue
        if resource_id in seen:
            findings.append(f"{path} contains duplicate resource_id: {resource_id}")
        seen.add(str(resource_id))
        validate_quantity_for_contract(
            item.get("quantity"), contracts[str(resource_id)],
            f"{item_path}.quantity", findings,
        )


def normalize_quantity(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"quantity_kind": "invalid", "value": repr(value)}
    kind = value.get("quantity_kind")
    if kind == "exact":
        return {"quantity_kind": "exact", "amount": value.get("amount"), "unit": value.get("unit")}
    if kind == "bounded":
        return {
            "quantity_kind": "bounded", "lower_bound": value.get("lower_bound"),
            "upper_bound": value.get("upper_bound"), "unit": value.get("unit"),
        }
    if kind == "ordinal":
        return {"quantity_kind": "ordinal", "level": value.get("level")}
    if kind == "indivisible":
        blocks = value.get("blocks") if isinstance(value.get("blocks"), list) else []
        return {"quantity_kind": "indivisible", "blocks": sorted(blocks)}
    return {"quantity_kind": "invalid", "value": repr(value)}


def normalize_resource_allocations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return [{"resource_id": "__invalid__", "quantity": normalize_quantity(value)}]
    normalized = []
    for item in value:
        if not isinstance(item, dict):
            normalized.append({"resource_id": "__invalid__", "quantity": normalize_quantity(item)})
            continue
        normalized.append({
            "resource_id": item.get("resource_id"),
            "quantity": normalize_quantity(item.get("quantity")),
        })
    return sorted(normalized, key=lambda item: str(item.get("resource_id")))


def _quantity_upper(value: Any) -> float | None:
    if not isinstance(value, dict):
        return None
    if value.get("quantity_kind") == "exact" and is_number(value.get("amount")):
        return float(value["amount"])
    if value.get("quantity_kind") == "bounded" and is_number(value.get("upper_bound")):
        return float(value["upper_bound"])
    return None


def _ordinal_rank(value: Any, contract: dict[str, Any]) -> int | None:
    if not isinstance(value, dict) or value.get("quantity_kind") != "ordinal":
        return None
    try:
        return list(contract.get("scale", [])).index(value.get("level"))
    except ValueError:
        return None


def _block_set(value: Any) -> set[str] | None:
    if not isinstance(value, dict) or value.get("quantity_kind") != "indivisible":
        return None
    blocks = value.get("blocks")
    return set(blocks) if is_string_list(blocks) else None


def _allocation_map(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        return {}
    return {
        str(item.get("resource_id")): item.get("quantity")
        for item in value
        if isinstance(item, dict) and is_non_empty_string(item.get("resource_id"))
    }


def quantity_within(value: Any, limit: Any, contract: dict[str, Any]) -> bool:
    family = contract.get("family")
    if family == "measured":
        value_upper = _quantity_upper(value)
        limit_upper = _quantity_upper(limit)
        return (
            value_upper is not None and limit_upper is not None
            and value_upper <= limit_upper + 1e-12
            and isinstance(value, dict) and isinstance(limit, dict)
            and value.get("unit") == limit.get("unit") == contract.get("unit")
        )
    if family == "ordinal":
        value_rank = _ordinal_rank(value, contract)
        limit_rank = _ordinal_rank(limit, contract)
        return value_rank is not None and limit_rank is not None and value_rank <= limit_rank
    if family == "indivisible":
        value_blocks = _block_set(value)
        limit_blocks = _block_set(limit)
        return value_blocks is not None and limit_blocks is not None and value_blocks <= limit_blocks
    return False


def validate_allocations_against_demand(
    allocations: Any,
    demands: Any,
    path: str,
    *,
    resource_pools: Iterable[dict[str, Any]],
    findings: list[str],
) -> None:
    contracts = resource_contracts(resource_pools)
    demand_by_resource = _allocation_map(demands)
    if not isinstance(allocations, list):
        return
    for index, item in enumerate(allocations):
        if not isinstance(item, dict):
            continue
        resource_id = str(item.get("resource_id"))
        if resource_id not in demand_by_resource:
            findings.append(
                f"{path}[{index}].resource_id is not declared in the candidate resource demand"
            )
            continue
        contract = contracts.get(resource_id)
        if contract is not None and not quantity_within(
            item.get("quantity"), demand_by_resource[resource_id], contract
        ):
            findings.append(
                f"{path}[{index}].quantity exceeds or conflicts with the candidate resource demand"
            )


def validate_cumulative_allocations_against_demand(
    *allocation_groups: Any,
    demands: Any,
    path: str,
    resource_pools: Iterable[dict[str, Any]],
    findings: list[str],
) -> None:
    """Validate one candidate's total current-window commitment against its demand."""
    contracts = resource_contracts(resource_pools)
    demand_by_resource = _allocation_map(demands)
    cumulative = _quantities_by_resource(*allocation_groups)
    for resource_id, quantities in cumulative.items():
        demand = demand_by_resource.get(resource_id)
        contract = contracts.get(resource_id)
        if demand is None:
            findings.append(
                f"{path}.{resource_id} is not declared in the candidate resource demand"
            )
            continue
        if contract is None:
            continue
        family = contract.get("family")
        if family == "measured":
            total = _combined_measured_upper(quantities)
            limit = _quantity_upper(demand)
            if total is None or limit is None or total > limit + 1e-12:
                findings.append(
                    f"{path}.{resource_id} cumulative allocation exceeds or conflicts "
                    "with the candidate resource demand"
                )
        elif family == "ordinal":
            if len(quantities) != 1 or not quantity_within(
                quantities[0], demand, contract
            ):
                findings.append(
                    f"{path}.{resource_id} cumulative allocation exceeds or conflicts "
                    "with the candidate resource demand"
                )
        elif family == "indivisible":
            blocks = [
                block for quantity in quantities for block in (_block_set(quantity) or set())
            ]
            demand_blocks = _block_set(demand) or set()
            duplicates = any(count > 1 for count in Counter(blocks).values())
            if duplicates or not set(blocks) <= demand_blocks:
                findings.append(
                    f"{path}.{resource_id} cumulative allocation exceeds or conflicts "
                    "with the candidate resource demand"
                )


def _quantities_by_resource(*allocation_groups: Any) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for group in allocation_groups:
        if not isinstance(group, list):
            continue
        for item in group:
            if not isinstance(item, dict) or not is_non_empty_string(item.get("resource_id")):
                continue
            quantity = item.get("quantity")
            if isinstance(quantity, dict):
                result.setdefault(str(item["resource_id"]), []).append(quantity)
    return result


def _combined_measured_upper(values: Iterable[dict[str, Any]]) -> float | None:
    total = 0.0
    for value in values:
        upper = _quantity_upper(value)
        if upper is None:
            return None
        total += upper
    return total


def _combined_ordinal_max(
    values: Iterable[dict[str, Any]], contract: dict[str, Any]
) -> int | None:
    ranks = [_ordinal_rank(value, contract) for value in values]
    if any(rank is None for rank in ranks):
        return None
    return max((rank for rank in ranks if rank is not None), default=-1)


def validate_resource_envelope(
    *,
    resource_pools: Iterable[dict[str, Any]],
    current_allocations: Any,
    next_allocations: Any,
    reserve_allocations: Any,
    investment_ceiling: Any,
    outcome: Any,
    findings: list[str],
) -> None:
    pools = [pool for pool in resource_pools if isinstance(pool, dict)]
    contracts = resource_contracts(pools)
    capacity_by_resource = {
        str(pool.get("resource_id")): pool.get("capacity") for pool in pools
    }
    ceiling_by_resource = _allocation_map(investment_ceiling)
    active_by_resource = _quantities_by_resource(
        current_allocations, next_allocations, reserve_allocations
    )
    committed_by_resource = _quantities_by_resource(
        current_allocations, next_allocations
    )

    for resource_id, quantities in active_by_resource.items():
        contract = contracts.get(resource_id)
        capacity = capacity_by_resource.get(resource_id)
        if contract is None or capacity is None:
            continue
        family = contract.get("family")
        if family == "measured":
            total = _combined_measured_upper(quantities)
            limit = _quantity_upper(capacity)
            if total is not None and limit is not None and total > limit + 1e-12:
                findings.append(
                    f"resource {resource_id} allocation {total:g} exceeds declared capacity {limit:g}"
                )
        elif family == "ordinal":
            if len(quantities) > 1:
                findings.append(
                    f"resource {resource_id} uses exclusive ordinal aggregation and cannot be allocated more than once"
                )
            used_rank = _combined_ordinal_max(quantities, contract)
            capacity_rank = _ordinal_rank(capacity, contract)
            if used_rank is not None and capacity_rank is not None and used_rank > capacity_rank:
                findings.append(
                    f"resource {resource_id} allocation exceeds declared ordinal capacity"
                )
        elif family == "indivisible":
            blocks = [
                block for value in quantities for block in (_block_set(value) or set())
            ]
            duplicates = sorted(
                block for block, count in Counter(blocks).items() if count > 1
            )
            if duplicates:
                findings.append(
                    f"resource {resource_id} blocks allocated more than once: {duplicates}"
                )
            capacity_blocks = _block_set(capacity) or set()
            unknown = sorted(set(blocks) - capacity_blocks)
            if unknown:
                findings.append(
                    f"resource {resource_id} allocation exceeds available blocks: {unknown}"
                )

    if outcome not in {"allocate", "conditional"}:
        return
    for resource_id, quantities in committed_by_resource.items():
        contract = contracts.get(resource_id)
        ceiling = ceiling_by_resource.get(resource_id)
        if contract is None:
            continue
        if ceiling is None:
            findings.append(f"investment_ceiling must cover committed resource {resource_id}")
            continue
        family = contract.get("family")
        if family == "measured":
            total = _combined_measured_upper(quantities)
            limit = _quantity_upper(ceiling)
            if total is None or limit is None or total > limit + 1e-12:
                findings.append(
                    f"resource {resource_id} commitment exceeds investment ceiling"
                )
        elif family == "ordinal":
            used_rank = _combined_ordinal_max(quantities, contract)
            ceiling_rank = _ordinal_rank(ceiling, contract)
            if used_rank is None or ceiling_rank is None or used_rank > ceiling_rank:
                findings.append(
                    f"resource {resource_id} commitment exceeds ordinal investment ceiling"
                )
        elif family == "indivisible":
            used_blocks = {
                block for value in quantities for block in (_block_set(value) or set())
            }
            ceiling_blocks = _block_set(ceiling) or set()
            if not used_blocks <= ceiling_blocks:
                findings.append(
                    f"resource {resource_id} commitment exceeds block investment ceiling"
                )


def validate_override_record(value: Any, path: str, findings: list[str]) -> None:
    if not isinstance(value, dict):
        findings.append(f"{path} must be an object")
        return
    unexpected = sorted(set(value) - set(OVERRIDE_FIELDS))
    if unexpected:
        findings.append(f"{path} contains unsupported fields: {unexpected}")
    for field in OVERRIDE_FIELDS:
        if not is_non_empty_string(value.get(field)):
            findings.append(f"{path}.{field} must be a non-empty string")


def override_is_present(data: dict[str, Any], key: str) -> bool:
    return isinstance(data.get("overrides"), dict) and isinstance(
        data["overrides"].get(key), dict
    )


def selected_mode(data: dict[str, Any]) -> str:
    requested = str(data.get("mode", "auto"))
    if requested == "full":
        return "full"
    if requested == "lite":
        return "lite"
    return "full" if data.get("escalation_signals") else "lite"


def selected_view_plan(data: dict[str, Any], mode: str) -> tuple[str, list[str]]:
    requested = str(data.get("view_plan", "auto"))
    default = (
        "dual_view" if mode == "full" or data.get("contamination_signals") else "situated_only"
    )
    plan = requested if requested in {"situated_only", "dual_view"} else default
    warnings: list[str] = []
    if plan != default:
        warnings.append(f"governed view-plan override: {default} -> {plan}")
    return plan, warnings


def selected_coverage_plan(data: dict[str, Any], mode: str) -> tuple[str, list[str]]:
    requested = str(data.get("coverage_review", "auto"))
    default = (
        "required"
        if data.get("coverage_signals") or (mode == "full" and data.get("known_omissions"))
        else "skip"
    )
    plan = requested if requested in {"required", "skip"} else default
    warnings: list[str] = []
    if plan != default:
        warnings.append(f"governed coverage override: {default} -> {plan}")
    return plan, warnings


def initial_statuses(view_plan: str, coverage_plan: str) -> dict[str, str]:
    return {
        "coverage": "pending" if coverage_plan == "required" else "not_required",
        "challenge": "pending" if view_plan == "dual_view" else "not_required",
        "situated": "pending",
        "comparison": "pending" if view_plan == "dual_view" else "not_required",
        "reconciliation": "not_required",
        "finalization": "pending",
    }


def finalization_status_for_outcome(outcome: str) -> str:
    mapping = {
        "allocate": "finalized",
        "conditional": "conditional",
        "infeasible": "finalized",
        "blocked": "blocked",
        "request_missing_context": "blocked",
    }
    if outcome not in mapping:
        raise ValueError(f"unsupported allocation outcome: {outcome}")
    return mapping[outcome]


def outcome_authorizes_now(outcome: str) -> bool:
    return outcome == "allocate"


def canonical_bundle_key(member_ids: Iterable[str]) -> str:
    members = sorted(set(str(member_id) for member_id in member_ids))
    return "bundle:" + ",".join(members)
