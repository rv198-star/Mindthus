"""Pure SRA decision normalization and typed comparison; no runtime file access."""
from __future__ import annotations
from typing import Any
from sra_domain import COMPARISON_FIELDS, COMPARISON_SCHEMA, canonical_bundle_key, normalize_resource_allocations
from sra_dependencies import normalized_dependency_resolutions
from sra_serialization import digest_data
from sra_criteria import normalized_reference, differing_paths


def _mapped_candidate(value: Any, mapping: dict[str, str]) -> Any:
    if value in {"reserve", "none", None}:
        return value
    return mapping.get(str(value), value)


def _normalize_candidate_assessments(
    judgment: dict[str, Any],
    *,
    id_field: str,
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    values = []
    for assessment in judgment.get("candidate_assessments", []):
        if not isinstance(assessment, dict):
            continue
        values.append({
            "candidate_id": _mapped_candidate(assessment.get(id_field), mapping),
            "feasibility": assessment.get("feasibility"),
            "candidate_role": assessment.get("candidate_role"),
            "contraction_result": assessment.get("contraction_result"),
        })
    return sorted(values, key=lambda item: str(item["candidate_id"]))


def _normalize_bundle_decision(
    judgment: dict[str, Any],
    *,
    mapping: dict[str, str],
) -> dict[str, Any]:
    decision = judgment.get("bundle_decision", {})
    if not isinstance(decision, dict):
        return {"status": "invalid", "bundle_assessments": [], "selected_bundle": "invalid"}
    local_to_key: dict[str, str] = {}
    raw_assessments = decision.get("bundle_assessments", [])
    if isinstance(raw_assessments, list):
        for bundle in raw_assessments:
            if not isinstance(bundle, dict):
                continue
            members = [
                str(_mapped_candidate(member, mapping))
                for member in bundle.get("member_ids", [])
            ]
            local_to_key[str(bundle.get("bundle_id"))] = canonical_bundle_key(members)
    assessments = []
    if isinstance(raw_assessments, list):
        for bundle in raw_assessments:
            if not isinstance(bundle, dict):
                continue
            members = sorted(
                str(_mapped_candidate(member, mapping))
                for member in bundle.get("member_ids", [])
            )
            assessments.append({
                "bundle": canonical_bundle_key(members),
                "member_ids": members,
                "feasibility": bundle.get("feasibility"),
                "dominance_status": bundle.get("dominance_status"),
                "dominated_by": sorted(
                    local_to_key.get(str(item), f"unknown:{item}")
                    for item in bundle.get("dominated_by", [])
                ),
                "resource_requirements": normalize_resource_allocations(
                    bundle.get("resource_requirements", [])
                ),
                "contraction_result": bundle.get("contraction_result"),
            })
    assessments.sort(key=lambda item: item["bundle"])
    selected_id = str(decision.get("selected_bundle_id", "none"))
    selected = "none" if selected_id == "none" else local_to_key.get(
        selected_id, f"unknown:{selected_id}"
    )
    return {
        "status": decision.get("status"),
        "bundle_assessments": assessments,
        "selected_bundle": selected,
    }


def normalized_decision_core(
    judgment: dict[str, Any],
    *,
    id_field: str,
    mapping: dict[str, str] | None = None,
) -> dict[str, Any]:
    mapping = mapping or {}
    ledger: list[dict[str, Any]] = []
    raw_ledger = judgment.get("allocation_ledger", [])
    if isinstance(raw_ledger, list):
        for entry in raw_ledger:
            if not isinstance(entry, dict):
                continue
            ledger.append({
                "candidate_id": _mapped_candidate(entry.get(id_field), mapping),
                "posture": entry.get("posture"),
                "current_allocations": normalize_resource_allocations(
                    entry.get("current_allocations", [])
                ),
            })
    ledger.sort(key=lambda item: str(item["candidate_id"]))
    next_tranche = judgment.get("next_tranche", {})
    if not isinstance(next_tranche, dict):
        next_tranche = {}
    reserve = judgment.get("reserve", {})
    if not isinstance(reserve, dict):
        reserve = {}
    missing = judgment.get("missing_information", [])
    return {
        "allocation_outcome": judgment.get("allocation_outcome"),
        "candidate_assessments": _normalize_candidate_assessments(
            judgment, id_field=id_field, mapping=mapping
        ),
        "bundle_decision": _normalize_bundle_decision(judgment, mapping=mapping),
        "allocation_ledger": ledger,
        "next_tranche": {
            "target_id": _mapped_candidate(
                next_tranche.get("target_id", "none"), mapping
            ),
            "resource_allocations": normalize_resource_allocations(
                next_tranche.get("resource_allocations", [])
            ),
            "window": next_tranche.get("window"),
            "completion_signal": next_tranche.get("completion_signal"),
            **({"completion_criterion_ref": normalized_reference(next_tranche["completion_criterion_ref"])}
               if "completion_criterion_ref" in next_tranche else {}),
            "start_condition": next_tranche.get("start_condition"),
        },
        "investment_ceiling": normalize_resource_allocations(
            judgment.get("investment_ceiling", [])
        ),
        "authorization_horizon": judgment.get("authorization_horizon"),
        "reserve": {
            "status": reserve.get("status"),
            "resource_allocations": normalize_resource_allocations(
                reserve.get("resource_allocations", [])
            ),
            "release_trigger": reserve.get("release_trigger"),
            "review_time": reserve.get("review_time"),
        },
        "missing_information": sorted(missing) if isinstance(missing, list) else [repr(missing)],
        **({"dependency_resolutions": normalized_dependency_resolutions(judgment, mapping)}
           if "dependency_resolutions" in judgment else {}),
    }


def compare_views(
    *,
    run_id: str,
    challenge_packet_hash: str,
    situated_packet_hash: str,
    challenge_judgment: dict[str, Any],
    situated_judgment: dict[str, Any],
    challenge_map: dict[str, str],
    detailed: bool = False,
) -> dict[str, Any]:
    challenge_core = normalized_decision_core(
        challenge_judgment,
        id_field="challenge_id",
        mapping=challenge_map,
    )
    situated_core = normalized_decision_core(
        situated_judgment,
        id_field="candidate_id",
    )
    conflicts: list[dict[str, Any]] = []
    for field in COMPARISON_FIELDS:
        if challenge_core.get(field) != situated_core.get(field):
            conflicts.append({
                "field": field,
                "challenge_value": challenge_core.get(field),
                "situated_value": situated_core.get(field),
            })
    base = {
        "schema_version": COMPARISON_SCHEMA,
        "run_id": run_id,
        "status": "agree" if not conflicts else "conflict",
        "challenge_packet_hash": challenge_packet_hash,
        "situated_packet_hash": situated_packet_hash,
        "challenge_judgment_hash": digest_data(challenge_judgment),
        "situated_judgment_hash": digest_data(situated_judgment),
        "challenge_core_mapped": challenge_core,
        "situated_core": situated_core,
        "conflict_fields": conflicts,
        "comparison_boundary": (
            "Workflow compares typed commitments and codes only. Agreement is "
            "corroboration, not proof; conflict chooses no winner."
        ),
    }
    if detailed or any("completion_criterion_ref" in core["next_tranche"] for core in (challenge_core, situated_core)):
        base["conflict_paths"] = differing_paths(challenge_core, situated_core)
    result = dict(base)
    result["comparison_hash"] = digest_data(base)
    return result
