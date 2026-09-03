#!/usr/bin/env python3
"""Deterministic runtime helpers for context-isolated SRA judgment.

The runtime owns packet construction, context admission mechanics, stable identifiers,
hashes, stage transitions, and reference checks. It never decides semantic priority.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


INPUT_SCHEMA = "sra.context-input.v0.1"
RUN_SCHEMA = "sra.run.v0.1"
ADMISSION_SCHEMA = "sra.context-admission.v0.1"
SEALED_PACKET_SCHEMA = "sra.sealed-packet.v0.1"
BLIND_PACKET_SCHEMA = "sra.blind-packet.v0.1"
STATE_PACKET_SCHEMA = "sra.state-packet.v0.1"
BLIND_JUDGMENT_SCHEMA = "sra.blind-judgment.v0.1"
STATE_JUDGMENT_SCHEMA = "sra.state-judgment.v0.1"
CHECK_REPORT_SCHEMA = "sra.run-check.v0.1"
TRACE_SCHEMA = "sra.runtime-event.v0.1"

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$")
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

MODES = {"auto", "lite", "full"}
ISOLATION_PROFILES = {"auto", "packet_bound", "fresh_context", "blind_then_state"}
CARRIERS = {"packet_bound", "fresh_subagent", "ephemeral_cli"}
FULL_ESCALATION_SIGNALS = {
    "direction_changing_uncertainty",
    "multiple_feasible_bundles",
    "major_commitment",
    "irreversible_exposure",
    "multiple_contested_resources",
    "fixed_threshold",
    "material_switching_cost",
    "path_dependency",
    "incomparable_candidate",
    "more_than_one_tranche",
}
CONTAMINATION_SIGNALS = {
    "active_task_richness",
    "prior_agent_conclusion",
    "candidate_advocacy_asymmetry",
    "cross_project_context",
    "sunk_cost_narrative",
    "presentation_order_bias",
    "user_factual_frame_without_evidence",
    "explicit_independent_judgment_request",
}
CONTEXT_KINDS = {
    "current_instruction",
    "user_constraint",
    "authority_decision",
    "observed_fact",
    "runtime_evidence",
    "assumption",
    "historical_context",
    "candidate_advocacy",
    "previous_conclusion",
    "ambient_inference",
}
ADMISSION_BY_KIND = {
    "current_instruction": ("admitted", "current_authority"),
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
    "parent_objective",
    "target_threshold",
    "time_window",
    "risk_floor",
    "decision_owner",
    "evidence_ceiling",
)
CANDIDATE_STRING_FIELDS = (
    "candidate_id",
    "title",
    "objective_contribution",
    "dependency_or_bundle_role",
    "delay_cost_or_opportunity_window",
    "irreversibility_or_downside",
)
BLIND_FEASIBILITY = {"feasible", "conditional", "infeasible", "unclear"}
CANDIDATE_ROLES = {
    "hard_gate",
    "threshold_essential",
    "enabler_or_bottleneck",
    "value_expanding",
    "maintenance_or_option",
    "defer_or_stop",
    "unclear",
}
CONTRACTION_RESULTS = {
    "retained",
    "capped",
    "downgraded",
    "substituted",
    "removed",
    "unclear",
}
FINAL_DECISIONS = {
    "continue",
    "switch",
    "maintain",
    "defer",
    "stop",
    "reserve",
    "allocate",
    "conditional",
    "infeasible",
    "blocked",
}
AUTHORIZATION_HORIZONS = {
    "one_action",
    "one_tranche",
    "until_named_checkpoint",
    "bounded_full",
}
STATE_ADJUSTMENT_KINDS = {
    "active_path_identity",
    "switching_cost",
    "reusable_asset",
    "remaining_cost",
    "current_commitment",
    "authority_boundary",
    "sunk_cost_rejected",
    "none",
}
STATE_ITEM_KIND_BY_COLLECTION = {
    "switching_costs": "switching_cost",
    "reusable_assets": "reusable_asset",
    "remaining_costs": "remaining_cost",
    "historical_spend": "sunk_cost",
    "commitments": "current_commitment",
    "authority_boundaries": "authority_boundary",
}
STATE_REF_KINDS_BY_ADJUSTMENT = {
    "active_path_identity": {"active_candidate"},
    "switching_cost": {"switching_cost"},
    "reusable_asset": {"reusable_asset"},
    "remaining_cost": {"remaining_cost"},
    "current_commitment": {"current_commitment"},
    "authority_boundary": {"authority_boundary"},
    "sunk_cost_rejected": {"sunk_cost"},
    "none": set(),
}


class SraRuntimeError(ValueError):
    """Raised when deterministic SRA runtime contracts are violated."""


class SraValidationError(SraRuntimeError):
    """Raised when structured input or judgment fails validation."""

    def __init__(self, findings: Iterable[str]):
        self.findings = list(findings)
        super().__init__("; ".join(self.findings))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_data(data: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def _walk_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _walk_strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_strings(item, f"{path}[{index}]")


def hidden_candidate_identity_findings(
    judgment: Any, candidates: Iterable[dict[str, Any]]
) -> list[str]:
    """Detect direct leakage of original candidate IDs or full titles into blind output."""

    findings: list[str] = []
    strings = list(_walk_strings(judgment))
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        title = candidate.get("title")
        if isinstance(candidate_id, str) and candidate_id:
            token = re.compile(
                rf"(?<![A-Za-z0-9._-]){re.escape(candidate_id)}(?![A-Za-z0-9._-])"
            )
            for path, text in strings:
                if token.search(text):
                    findings.append(
                        f"blind judgment contains hidden original candidate candidate_id at {path}: {candidate_id}"
                    )
        if isinstance(title, str) and title:
            folded_title = " ".join(title.casefold().split())
            if len(folded_title) < 6:
                continue
            for path, text in strings:
                folded_text = " ".join(text.casefold().split())
                if folded_title in folded_text:
                    findings.append(
                        f"blind judgment contains hidden original candidate title at {path}: {title}"
                    )
    return sorted(set(findings))


def load_json(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SraRuntimeError(f"failed to read JSON at {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise SraRuntimeError(f"failed to decode JSON at {path} as UTF-8: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SraRuntimeError(
            f"invalid JSON at {path}: {exc.msg} (line {exc.lineno} column {exc.colno})"
        ) from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SraRuntimeError(f"failed to read JSONL at {path}: {exc}") from exc
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SraRuntimeError(
                f"invalid JSONL at {path}, line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise SraRuntimeError(
                f"JSONL record at {path}, line {line_number} must be an object"
            )
        records.append(value)
    return records


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_is_non_empty_string(item) for item in value)


def _validate_id(value: Any, path: str, findings: list[str]) -> None:
    if not _is_non_empty_string(value) or not ID_RE.fullmatch(str(value)):
        findings.append(f"{path} must use 2-64 letters, numbers, '.', '_', or '-'")


def _validate_unique_ids(
    items: Any,
    *,
    collection_path: str,
    id_field: str,
    findings: list[str],
    required: bool = True,
) -> set[str]:
    if not isinstance(items, list):
        findings.append(f"{collection_path} must be a list")
        return set()
    if required and not items:
        findings.append(f"{collection_path} must not be empty")
    values: set[str] = set()
    for index, item in enumerate(items):
        path = f"{collection_path}[{index}]"
        if not isinstance(item, dict):
            findings.append(f"{path} must be an object")
            continue
        value = item.get(id_field)
        _validate_id(value, f"{path}.{id_field}", findings)
        if _is_non_empty_string(value):
            text = str(value)
            if text in values:
                findings.append(f"duplicate {id_field}: {text}")
            values.add(text)
    return values


def validate_context_input(data: Any) -> list[str]:
    findings: list[str] = []
    if not isinstance(data, dict):
        return ["SRA context input must be an object"]
    if data.get("schema_version") != INPUT_SCHEMA:
        findings.append(f"schema_version must be {INPUT_SCHEMA}")
    run_id = data.get("run_id")
    if not _is_non_empty_string(run_id) or not RUN_ID_RE.fullmatch(str(run_id)):
        findings.append("run_id must use 3-64 letters, numbers, '.', '_', or '-'")
    mode = data.get("mode", "auto")
    if mode not in MODES:
        findings.append(f"mode must be one of: {', '.join(sorted(MODES))}")
    profile = data.get("isolation_profile", "auto")
    if profile not in ISOLATION_PROFILES:
        findings.append(
            f"isolation_profile must be one of: {', '.join(sorted(ISOLATION_PROFILES))}"
        )

    signals = data.get("escalation_signals", [])
    if not _string_list(signals):
        findings.append("escalation_signals must be a list of strings")
    elif any(item not in FULL_ESCALATION_SIGNALS for item in signals):
        unknown = sorted(set(signals) - FULL_ESCALATION_SIGNALS)
        findings.append(f"unsupported escalation_signals: {unknown}")
    contamination = data.get("contamination_signals", [])
    if not _string_list(contamination):
        findings.append("contamination_signals must be a list of strings")
    elif any(item not in CONTAMINATION_SIGNALS for item in contamination):
        unknown = sorted(set(contamination) - CONTAMINATION_SIGNALS)
        findings.append(f"unsupported contamination_signals: {unknown}")
    override_reason = data.get("isolation_override_reason")
    if override_reason is not None and not _is_non_empty_string(override_reason):
        findings.append("isolation_override_reason must be a non-empty string when supplied")
    packet_bound_needs_override = profile == "packet_bound" and (
        mode == "full" or bool(signals) or bool(contamination)
    )
    if packet_bound_needs_override and not _is_non_empty_string(override_reason):
        findings.append(
            "packet_bound isolation under Full or contamination pressure requires isolation_override_reason"
        )

    frame = data.get("allocation_frame")
    if not isinstance(frame, dict):
        findings.append("allocation_frame must be an object")
    else:
        for field in FRAME_STRING_FIELDS:
            if not _is_non_empty_string(frame.get(field)):
                findings.append(f"allocation_frame.{field} must be a non-empty string")
        resources = frame.get("contested_resources")
        if not _string_list(resources) or not resources:
            findings.append("allocation_frame.contested_resources must be a non-empty list")

    candidate_ids = _validate_unique_ids(
        data.get("candidates"),
        collection_path="candidates",
        id_field="candidate_id",
        findings=findings,
    )
    candidates = data.get("candidates")
    if isinstance(candidates, list):
        if len(candidates) < 2:
            findings.append("candidates must contain at least two candidates or postures")
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                continue
            path = f"candidates[{index}]"
            for field in CANDIDATE_STRING_FIELDS:
                if not _is_non_empty_string(candidate.get(field)):
                    findings.append(f"{path}.{field} must be a non-empty string")
            resource_demand = candidate.get("resource_demand")
            if not isinstance(resource_demand, list) or not resource_demand:
                findings.append(f"{path}.resource_demand must be a non-empty list")
            else:
                for demand_index, demand in enumerate(resource_demand):
                    dpath = f"{path}.resource_demand[{demand_index}]"
                    if not isinstance(demand, dict):
                        findings.append(f"{dpath} must be an object")
                        continue
                    for field in ("resource", "amount"):
                        if not _is_non_empty_string(demand.get(field)):
                            findings.append(f"{dpath}.{field} must be a non-empty string")
            for field in ("evidence_refs", "assumption_refs"):
                if not _string_list(candidate.get(field, [])):
                    findings.append(f"{path}.{field} must be a list of strings")

    evidence_ids = _validate_unique_ids(
        data.get("evidence", []),
        collection_path="evidence",
        id_field="evidence_id",
        findings=findings,
        required=False,
    )
    evidence = data.get("evidence", [])
    if isinstance(evidence, list):
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                continue
            path = f"evidence[{index}]"
            for field in ("kind", "source", "statement", "claim_ceiling"):
                if not _is_non_empty_string(item.get(field)):
                    findings.append(f"{path}.{field} must be a non-empty string")
            if "observed_at" in item and not _is_non_empty_string(item.get("observed_at")):
                findings.append(f"{path}.observed_at must be a non-empty string when present")

    assumption_ids = _validate_unique_ids(
        data.get("assumptions", []),
        collection_path="assumptions",
        id_field="assumption_id",
        findings=findings,
        required=False,
    )
    assumptions = data.get("assumptions", [])
    if isinstance(assumptions, list):
        for index, item in enumerate(assumptions):
            if not isinstance(item, dict):
                continue
            path = f"assumptions[{index}]"
            for field in ("statement", "overturn_condition"):
                if not _is_non_empty_string(item.get(field)):
                    findings.append(f"{path}.{field} must be a non-empty string")

    context_ids = _validate_unique_ids(
        data.get("context_items", []),
        collection_path="context_items",
        id_field="context_id",
        findings=findings,
        required=False,
    )
    namespaces = {
        "candidate": candidate_ids,
        "evidence": evidence_ids,
        "assumption": assumption_ids,
        "context": context_ids,
    }
    namespace_names = list(namespaces)
    for index, left_name in enumerate(namespace_names):
        for right_name in namespace_names[index + 1 :]:
            overlap = sorted(namespaces[left_name] & namespaces[right_name])
            if overlap:
                findings.append(
                    f"IDs must be globally unambiguous; {left_name}/{right_name} overlap: {overlap}"
                )
    context_items = data.get("context_items", [])
    if isinstance(context_items, list):
        current_instruction_count = sum(
            1
            for item in context_items
            if isinstance(item, dict) and item.get("kind") == "current_instruction"
        )
        if current_instruction_count == 0:
            findings.append(
                "context_items must include at least one current_instruction anchoring the present allocation request"
            )
        for index, item in enumerate(context_items):
            if not isinstance(item, dict):
                continue
            path = f"context_items[{index}]"
            kind = item.get("kind")
            if kind not in CONTEXT_KINDS:
                findings.append(
                    f"{path}.kind must be one of: {', '.join(sorted(CONTEXT_KINDS))}"
                )
            for field in ("statement", "source", "decision_relevance"):
                if not _is_non_empty_string(item.get(field)):
                    findings.append(f"{path}.{field} must be a non-empty string")
            requested_disposition = item.get("requested_disposition", "consider")
            if requested_disposition not in {"consider", "admit", "exclude"}:
                findings.append(
                    f"{path}.requested_disposition must be consider, admit, or exclude"
                )
            if kind in {"current_instruction", "user_constraint", "authority_decision"} and requested_disposition == "exclude":
                findings.append(
                    f"{path} cannot exclude current instruction, current user constraint, or authority context"
                )
            for field, allowed in (
                ("candidate_ids", candidate_ids),
                ("evidence_refs", evidence_ids),
                ("assumption_refs", assumption_ids),
            ):
                refs = item.get(field, [])
                if not _string_list(refs):
                    findings.append(f"{path}.{field} must be a list of strings")
                elif allowed or refs:
                    unknown = sorted(set(refs) - allowed)
                    if unknown:
                        findings.append(f"{path}.{field} contains unknown IDs: {unknown}")
            evidence_refs = item.get("evidence_refs", [])
            assumption_refs = item.get("assumption_refs", [])
            if kind == "authority_decision":
                for authority_field in ("authority_scope", "authority_expiry"):
                    if not _is_non_empty_string(item.get(authority_field)):
                        findings.append(
                            f"{path}.{authority_field} must be a non-empty string for authority_decision"
                        )
            if kind in {"observed_fact", "runtime_evidence"} and not evidence_refs:
                findings.append(f"{path}.evidence_refs must bind evidence-bearing context")
            if kind == "assumption" and not assumption_refs:
                findings.append(f"{path}.assumption_refs must bind assumption context")
            if kind == "historical_context" and not (evidence_refs or assumption_refs):
                findings.append(
                    f"{path} historical context must cite evidence or an explicit assumption"
                )

    for index, candidate in enumerate(candidates if isinstance(candidates, list) else []):
        if not isinstance(candidate, dict):
            continue
        unknown_evidence = sorted(set(candidate.get("evidence_refs", [])) - evidence_ids)
        unknown_assumptions = sorted(set(candidate.get("assumption_refs", [])) - assumption_ids)
        if unknown_evidence:
            findings.append(
                f"candidates[{index}].evidence_refs contains unknown IDs: {unknown_evidence}"
            )
        if unknown_assumptions:
            findings.append(
                f"candidates[{index}].assumption_refs contains unknown IDs: {unknown_assumptions}"
            )

    active_candidate = data.get("active_candidate_id")
    if active_candidate is not None and active_candidate not in candidate_ids:
        findings.append("active_candidate_id must reference a candidate or be null")

    state_context = data.get("state_context", {})
    if not isinstance(state_context, dict):
        findings.append("state_context must be an object")
    else:
        for field in (
            "switching_costs",
            "reusable_assets",
            "remaining_costs",
            "historical_spend",
            "commitments",
            "authority_boundaries",
        ):
            values = state_context.get(field, [])
            if not isinstance(values, list):
                findings.append(f"state_context.{field} must be a list")
                continue
            for index, item in enumerate(values):
                path = f"state_context.{field}[{index}]"
                if not isinstance(item, dict):
                    findings.append(f"{path} must be an object")
                    continue
                for key, value in item.items():
                    if key.endswith("candidate_id") and value not in candidate_ids:
                        findings.append(f"{path}.{key} contains unknown candidate ID: {value}")
                state_evidence_refs = item.get("evidence_refs", [])
                state_assumption_refs = item.get("assumption_refs", [])
                for ref_field, allowed in (
                    ("evidence_refs", evidence_ids),
                    ("assumption_refs", assumption_ids),
                ):
                    refs = item.get(ref_field, [])
                    if not _string_list(refs):
                        findings.append(f"{path}.{ref_field} must be a list of strings")
                        continue
                    unknown = sorted(set(refs) - allowed)
                    if unknown:
                        findings.append(f"{path}.{ref_field} contains unknown IDs: {unknown}")
                if not state_evidence_refs and not state_assumption_refs:
                    findings.append(
                        f"{path} must cite evidence_refs or assumption_refs before it can influence state reconciliation"
                    )

    known_omissions = data.get("known_omissions", [])
    if not _string_list(known_omissions):
        findings.append("known_omissions must be a list of strings")

    return findings


def selected_mode(data: dict[str, Any]) -> str:
    requested = str(data.get("mode", "auto"))
    if requested in {"lite", "full"}:
        return requested
    return "full" if data.get("escalation_signals") else "lite"


def selected_isolation(data: dict[str, Any], mode: str) -> str:
    requested = str(data.get("isolation_profile", "auto"))
    if requested != "auto":
        return requested
    if mode == "full":
        return "blind_then_state"
    if data.get("contamination_signals"):
        return "fresh_context"
    return "packet_bound"


def apply_context_admission(data: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    admitted_ids: list[str] = []
    quarantined_ids: list[str] = []
    excluded_ids: list[str] = []
    for item in data.get("context_items", []):
        value = dict(item)
        context_id = str(value["context_id"])
        if value.get("requested_disposition", "consider") == "exclude":
            admission, admitted_as = "excluded", "caller_excluded"
            excluded_ids.append(context_id)
        elif value["kind"] == "historical_context":
            if value.get("requested_disposition") == "admit":
                admission, admitted_as = "admitted", "scoped_history"
                admitted_ids.append(context_id)
            else:
                admission, admitted_as = "quarantined", "history_requires_explicit_admission"
                quarantined_ids.append(context_id)
        else:
            admission, admitted_as = ADMISSION_BY_KIND[value["kind"]]
            if admission == "admitted":
                admitted_ids.append(context_id)
            else:
                quarantined_ids.append(context_id)
        value["admission"] = admission
        value["admitted_as"] = admitted_as
        value["admission_reason"] = _admission_reason(value["kind"], admission, admitted_as)
        items.append(value)
    return {
        "schema_version": ADMISSION_SCHEMA,
        "run_id": data["run_id"],
        "policy": "kind-based deterministic admission; semantic relevance remains Agentic",
        "items": items,
        "admitted_ids": admitted_ids,
        "quarantined_ids": quarantined_ids,
        "excluded_ids": excluded_ids,
    }


def _admission_reason(kind: str, admission: str, admitted_as: str) -> str:
    if admission == "excluded":
        return "The caller explicitly excluded this item; the ledger preserves the exclusion."
    if kind == "user_constraint":
        return "Current user values and constraints may shape the decision but do not prove factual claims."
    if kind in {"observed_fact", "runtime_evidence"}:
        return "Evidence-bearing context is admitted only inside its source and claim ceiling."
    if kind == "assumption":
        return "The item remains an explicit assumption and cannot be upgraded to evidence."
    if kind == "historical_context":
        return "Historical context is admitted only as scoped background and inherits no current authority."
    if kind in {"candidate_advocacy", "previous_conclusion", "ambient_inference"}:
        return "This item is quarantined as a claim and cannot silently control the allocation."
    return f"The item is admitted as {admitted_as} inside its declared scope."


def candidate_context_weights(data: dict[str, Any], admission: dict[str, Any]) -> dict[str, int]:
    evidence_by_id = {item["evidence_id"]: item for item in data.get("evidence", [])}
    assumption_by_id = {item["assumption_id"]: item for item in data.get("assumptions", [])}
    admitted_items = [item for item in admission["items"] if item["admission"] == "admitted"]
    weights: dict[str, int] = {}
    for candidate in data["candidates"]:
        candidate_id = candidate["candidate_id"]
        text = " ".join(
            str(candidate.get(field, ""))
            for field in (
                "objective_contribution",
                "dependency_or_bundle_role",
                "delay_cost_or_opportunity_window",
                "irreversibility_or_downside",
            )
        )
        for evidence_id in candidate.get("evidence_refs", []):
            item = evidence_by_id.get(evidence_id, {})
            text += " " + str(item.get("statement", "")) + " " + str(item.get("claim_ceiling", ""))
        for assumption_id in candidate.get("assumption_refs", []):
            item = assumption_by_id.get(assumption_id, {})
            text += " " + str(item.get("statement", "")) + " " + str(item.get("overturn_condition", ""))
        for item in admitted_items:
            scoped = item.get("candidate_ids", [])
            if not scoped or candidate_id in scoped:
                text += " " + str(item.get("statement", ""))
        weights[candidate_id] = len(text.strip())
    return weights


def context_asymmetry_warnings(weights: dict[str, int]) -> list[str]:
    if len(weights) < 2:
        return []
    values = list(weights.values())
    smallest, largest = min(values), max(values)
    if largest <= 200:
        return []
    if smallest == 0 or largest > max(3 * smallest, smallest + 300):
        richest = max(weights, key=weights.get)
        thinnest = min(weights, key=weights.get)
        return [
            f"candidate context asymmetry: {richest} weight={largest}, {thinnest} weight={smallest}; Agentic review must not treat descriptive richness as priority"
        ]
    return []


def _blind_sort_key(candidate: dict[str, Any]) -> tuple[str, str]:
    neutral = {
        "objective_contribution": candidate["objective_contribution"],
        "resource_demand": candidate["resource_demand"],
        "dependency_or_bundle_role": candidate["dependency_or_bundle_role"],
        "delay_cost_or_opportunity_window": candidate["delay_cost_or_opportunity_window"],
        "irreversibility_or_downside": candidate["irreversibility_or_downside"],
        "evidence_refs": sorted(candidate.get("evidence_refs", [])),
        "assumption_refs": sorted(candidate.get("assumption_refs", [])),
    }
    return digest_data(neutral), str(candidate["candidate_id"])


def build_packets(data: dict[str, Any]) -> dict[str, Any]:
    findings = validate_context_input(data)
    if findings:
        raise SraValidationError(findings)

    mode = selected_mode(data)
    isolation = selected_isolation(data, mode)
    admission = apply_context_admission(data)
    context_manifest_hash = digest_data(admission)
    raw_input_hash = digest_data(data)
    weights = candidate_context_weights(data, admission)
    warnings = context_asymmetry_warnings(weights)
    if isolation == "packet_bound" and _is_non_empty_string(data.get("isolation_override_reason")):
        warnings.append(
            "packet-bound isolation was explicitly retained under contamination or Full pressure; fresh-context independence is degraded"
        )

    admitted_context = [
        {
            "context_id": item["context_id"],
            "kind": item["kind"],
            "statement": item["statement"],
            "source": item["source"],
            "decision_relevance": item["decision_relevance"],
            "candidate_ids": item.get("candidate_ids", []),
            "evidence_refs": item.get("evidence_refs", []),
            "assumption_refs": item.get("assumption_refs", []),
            "authority_scope": item.get("authority_scope"),
            "authority_expiry": item.get("authority_expiry"),
            "admitted_as": item["admitted_as"],
        }
        for item in admission["items"]
        if item["admission"] == "admitted"
    ]
    sealed_base = {
        "schema_version": SEALED_PACKET_SCHEMA,
        "run_id": data["run_id"],
        "mode": mode,
        "isolation_profile": isolation,
        "isolation_override_reason": data.get("isolation_override_reason"),
        "raw_input_hash": raw_input_hash,
        "context_manifest_hash": context_manifest_hash,
        "allocation_frame": data["allocation_frame"],
        "candidates": data["candidates"],
        "evidence": data.get("evidence", []),
        "assumptions": data.get("assumptions", []),
        "admitted_context": admitted_context,
        "context_admission_summary": {
            "admitted_ids": admission["admitted_ids"],
            "quarantined_ids": admission["quarantined_ids"],
            "excluded_ids": admission["excluded_ids"],
        },
        "contamination_signals": data.get("contamination_signals", []),
        "known_omissions": data.get("known_omissions", []),
        "escalation_signals": data.get("escalation_signals", []),
        "warnings": warnings,
    }
    sealed_packet = dict(sealed_base)
    sealed_packet["packet_hash"] = digest_data(sealed_base)

    ordered = sorted(data["candidates"], key=_blind_sort_key)
    candidate_map: dict[str, str] = {}
    blind_candidates: list[dict[str, Any]] = []
    for index, candidate in enumerate(ordered, 1):
        blind_id = f"B{index:02d}"
        candidate_map[blind_id] = candidate["candidate_id"]
        blind_candidates.append(
            {
                "blind_id": blind_id,
                "objective_contribution": candidate["objective_contribution"],
                "resource_demand": candidate["resource_demand"],
                "dependency_or_bundle_role": candidate["dependency_or_bundle_role"],
                "delay_cost_or_opportunity_window": candidate["delay_cost_or_opportunity_window"],
                "irreversibility_or_downside": candidate["irreversibility_or_downside"],
                "evidence_refs": candidate.get("evidence_refs", []),
                "assumption_refs": candidate.get("assumption_refs", []),
            }
        )

    blind_context = []
    blind_evidence_ids = {
        evidence_id
        for candidate in data["candidates"]
        for evidence_id in candidate.get("evidence_refs", [])
    }
    blind_assumption_ids = {
        assumption_id
        for candidate in data["candidates"]
        for assumption_id in candidate.get("assumption_refs", [])
    }
    for item in admitted_context:
        mapped_candidates = [
            blind_id
            for blind_id, candidate_id in candidate_map.items()
            if candidate_id in item.get("candidate_ids", [])
        ]
        value = dict(item)
        value.pop("candidate_ids", None)
        value["blind_candidate_ids"] = mapped_candidates
        blind_context.append(value)
        blind_evidence_ids.update(item.get("evidence_refs", []))
        blind_assumption_ids.update(item.get("assumption_refs", []))

    blind_evidence = [
        item for item in data.get("evidence", []) if item["evidence_id"] in blind_evidence_ids
    ]
    blind_assumptions = [
        item
        for item in data.get("assumptions", [])
        if item["assumption_id"] in blind_assumption_ids
    ]

    blind_base = {
        "schema_version": BLIND_PACKET_SCHEMA,
        "run_id": data["run_id"],
        "mode": mode,
        "sealed_packet_hash": sealed_packet["packet_hash"],
        "context_manifest_hash": context_manifest_hash,
        "allocation_frame": data["allocation_frame"],
        "candidates": blind_candidates,
        "evidence": blind_evidence,
        "assumptions": blind_assumptions,
        "admitted_context": blind_context,
        "known_omissions": data.get("known_omissions", []),
        "contamination_signals": data.get("contamination_signals", []),
        "warnings": warnings,
        "blind_boundary": {
            "omitted": [
                "original candidate titles",
                "original candidate IDs",
                "active candidate identity",
                "switching costs",
                "reusable assets",
                "remaining costs",
                "historical spend",
                "current commitments and authority state",
                "evidence and assumptions used only by state records",
                "quarantined context statements",
            ],
            "external_context_forbidden": True,
        },
    }
    blind_packet = dict(blind_base)
    blind_packet["packet_hash"] = digest_data(blind_base)

    return {
        "mode": mode,
        "isolation_profile": isolation,
        "admission": admission,
        "sealed_packet": sealed_packet,
        "blind_packet": blind_packet,
        "candidate_map": candidate_map,
        "raw_input_hash": raw_input_hash,
        "context_manifest_hash": context_manifest_hash,
        "context_weights": weights,
        "warnings": warnings,
    }


def _string_array_schema(
    allowed: Iterable[str] | None = None, *, min_items: int = 0
) -> dict[str, Any]:
    values = list(allowed or [])
    schema: dict[str, Any] = {"type": "array", "minItems": min_items}
    if values:
        schema["items"] = {"type": "string", "enum": values}
    else:
        schema["items"] = {"type": "string"}
        schema["maxItems"] = 0
    return schema


def blind_output_schema(packet: dict[str, Any]) -> dict[str, Any]:
    blind_ids = [item["blind_id"] for item in packet.get("candidates", [])]
    evidence_ids = [item["evidence_id"] for item in packet.get("evidence", [])]
    assumption_ids = [item["assumption_id"] for item in packet.get("assumptions", [])]
    assessment = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "blind_id",
            "feasibility",
            "candidate_role",
            "contraction_result",
            "first_break_point",
            "evidence_refs",
            "assumption_refs",
        ],
        "properties": {
            "blind_id": {"type": "string", "enum": blind_ids},
            "feasibility": {"type": "string", "enum": sorted(BLIND_FEASIBILITY)},
            "candidate_role": {"type": "string", "enum": sorted(CANDIDATE_ROLES)},
            "contraction_result": {
                "type": "string",
                "enum": sorted(CONTRACTION_RESULTS),
            },
            "first_break_point": {"type": "string", "minLength": 1},
            "evidence_refs": _string_array_schema(evidence_ids),
            "assumption_refs": _string_array_schema(assumption_ids),
        },
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SRA Blind Judgment",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "stage",
            "packet_hash",
            "mode",
            "candidate_assessments",
            "current_floor",
            "provisional_next_tranche",
            "missing_information",
            "claim_ceiling",
        ],
        "properties": {
            "schema_version": {"type": "string", "const": BLIND_JUDGMENT_SCHEMA},
            "stage": {"type": "string", "const": "blind"},
            "packet_hash": {"type": "string", "const": packet["packet_hash"]},
            "mode": {"type": "string", "const": packet["mode"]},
            "candidate_assessments": {
                "type": "array",
                "minItems": len(blind_ids),
                "maxItems": len(blind_ids),
                "items": assessment,
            },
            "current_floor": _string_array_schema(blind_ids),
            "provisional_next_tranche": {
                "type": "object",
                "additionalProperties": False,
                "required": ["blind_id", "description", "reason"],
                "properties": {
                    "blind_id": {
                        "type": "string",
                        "enum": blind_ids + ["reserve", "none"],
                    },
                    "description": {"type": "string", "minLength": 1},
                    "reason": {"type": "string", "minLength": 1},
                },
            },
            "missing_information": {
                "type": "array",
                "items": {"type": "string"},
            },
            "claim_ceiling": {"type": "string", "minLength": 1},
        },
    }


def state_output_schema(packet: dict[str, Any]) -> dict[str, Any]:
    candidate_ids = [item["candidate_id"] for item in packet.get("candidate_mapping", [])]
    evidence_ids = [item["evidence_id"] for item in packet.get("evidence", [])]
    assumption_ids = [item["assumption_id"] for item in packet.get("assumptions", [])]
    state_ids = [item["state_id"] for item in packet.get("state_items", [])]
    adjustment = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "kind",
            "finding",
            "state_refs",
            "evidence_refs",
            "assumption_refs",
        ],
        "properties": {
            "kind": {"type": "string", "enum": sorted(STATE_ADJUSTMENT_KINDS)},
            "finding": {"type": "string", "minLength": 1},
            "state_refs": _string_array_schema(state_ids),
            "evidence_refs": _string_array_schema(evidence_ids),
            "assumption_refs": _string_array_schema(assumption_ids),
        },
    }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "SRA State-Aware Judgment",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "stage",
            "packet_hash",
            "blind_judgment_hash",
            "decision",
            "blind_result_changed",
            "change_reason",
            "sunk_cost_used_as_reason",
            "state_adjustments",
            "current_floor",
            "next_tranche",
            "investment_ceiling",
            "authorization_horizon",
            "maintenance",
            "reserve",
            "defer",
            "stop",
            "rerank_triggers",
            "state_refs",
            "evidence_refs",
            "assumption_refs",
            "claim_ceiling",
        ],
        "properties": {
            "schema_version": {"type": "string", "const": STATE_JUDGMENT_SCHEMA},
            "stage": {"type": "string", "const": "state_aware"},
            "packet_hash": {"type": "string", "const": packet["packet_hash"]},
            "blind_judgment_hash": {
                "type": "string",
                "const": packet["blind_judgment_hash"],
            },
            "decision": {"type": "string", "enum": sorted(FINAL_DECISIONS)},
            "blind_result_changed": {"type": "boolean"},
            "change_reason": {"type": "string", "minLength": 1},
            "sunk_cost_used_as_reason": {"type": "boolean", "const": False},
            "state_adjustments": {"type": "array", "items": adjustment},
            "current_floor": _string_array_schema(candidate_ids),
            "next_tranche": {
                "type": "object",
                "additionalProperties": False,
                "required": ["candidate_id", "description", "reason"],
                "properties": {
                    "candidate_id": {
                        "type": "string",
                        "enum": candidate_ids + ["reserve", "none"],
                    },
                    "description": {"type": "string", "minLength": 1},
                    "reason": {"type": "string", "minLength": 1},
                },
            },
            "investment_ceiling": {"type": "string", "minLength": 1},
            "authorization_horizon": {
                "type": "string",
                "enum": sorted(AUTHORIZATION_HORIZONS),
            },
            "maintenance": {"type": "array", "items": {"type": "string"}},
            "reserve": {
                "type": "object",
                "additionalProperties": False,
                "required": ["status", "reason", "release_trigger", "review_time"],
                "properties": {
                    "status": {"type": "string", "enum": ["none", "reserved"]},
                    "reason": {"type": "string", "minLength": 1},
                    "release_trigger": {"type": "string", "minLength": 1},
                    "review_time": {"type": "string", "minLength": 1},
                },
            },
            "defer": {"type": "array", "items": {"type": "string"}},
            "stop": {"type": "array", "items": {"type": "string"}},
            "rerank_triggers": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string"},
            },
            "state_refs": _string_array_schema(state_ids),
            "evidence_refs": _string_array_schema(evidence_ids),
            "assumption_refs": _string_array_schema(assumption_ids),
            "claim_ceiling": {"type": "string", "minLength": 1},
        },
    }


def make_runtime_event(run_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": TRACE_SCHEMA,
        "event_id": f"EV-{hashlib.sha256((run_id + event_type + now_iso()).encode()).hexdigest()[:12]}",
        "run_id": run_id,
        "event_type": event_type,
        "recorded_at": now_iso(),
        "payload": payload,
    }


def save_run_state(path: Path, state: dict[str, Any]) -> None:
    state = dict(state)
    state["updated_at"] = now_iso()
    write_json(path, state)


def load_run(run_dir: Path) -> dict[str, Any]:
    state = load_json(run_dir / "run.json")
    if not isinstance(state, dict) or state.get("schema_version") != RUN_SCHEMA:
        raise SraRuntimeError(f"invalid SRA run state at {run_dir / 'run.json'}")
    return state


def validate_blind_judgment(judgment: Any, blind_packet: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if not isinstance(judgment, dict):
        return ["blind judgment must be an object"]
    if judgment.get("schema_version") != BLIND_JUDGMENT_SCHEMA:
        findings.append(f"schema_version must be {BLIND_JUDGMENT_SCHEMA}")
    if judgment.get("stage") != "blind":
        findings.append("stage must be blind")
    if judgment.get("packet_hash") != blind_packet.get("packet_hash"):
        findings.append("packet_hash does not match blind-packet.json")
    if judgment.get("mode") != blind_packet.get("mode"):
        findings.append("mode does not match blind packet")

    allowed_candidates = {item["blind_id"] for item in blind_packet.get("candidates", [])}
    allowed_evidence = {item["evidence_id"] for item in blind_packet.get("evidence", [])}
    allowed_assumptions = {item["assumption_id"] for item in blind_packet.get("assumptions", [])}
    assessments = judgment.get("candidate_assessments")
    if not isinstance(assessments, list):
        findings.append("candidate_assessments must be a list")
        assessments = []
    seen: set[str] = set()
    for index, assessment in enumerate(assessments):
        path = f"candidate_assessments[{index}]"
        if not isinstance(assessment, dict):
            findings.append(f"{path} must be an object")
            continue
        blind_id = assessment.get("blind_id")
        if blind_id not in allowed_candidates:
            findings.append(f"{path}.blind_id must reference the blind packet")
        elif blind_id in seen:
            findings.append(f"duplicate blind candidate assessment: {blind_id}")
        else:
            seen.add(str(blind_id))
        if assessment.get("feasibility") not in BLIND_FEASIBILITY:
            findings.append(f"{path}.feasibility is unsupported")
        if assessment.get("candidate_role") not in CANDIDATE_ROLES:
            findings.append(f"{path}.candidate_role is unsupported")
        if assessment.get("contraction_result") not in CONTRACTION_RESULTS:
            findings.append(f"{path}.contraction_result is unsupported")
        if not _is_non_empty_string(assessment.get("first_break_point")):
            findings.append(f"{path}.first_break_point must be a non-empty string")
        findings.extend(
            _validate_refs(
                assessment,
                path,
                allowed_evidence=allowed_evidence,
                allowed_assumptions=allowed_assumptions,
            )
        )
    if seen != allowed_candidates:
        findings.append("candidate_assessments must cover every blind candidate exactly once")

    current_floor = judgment.get("current_floor")
    if not _string_list(current_floor):
        findings.append("current_floor must be a list of blind IDs")
    else:
        unknown = sorted(set(current_floor) - allowed_candidates)
        if unknown:
            findings.append(f"current_floor contains unknown blind IDs: {unknown}")
        feasible_ids = {
            assessment.get("blind_id")
            for assessment in assessments
            if isinstance(assessment, dict)
            and assessment.get("feasibility") in {"feasible", "conditional"}
        }
        if not current_floor and feasible_ids:
            findings.append(
                "current_floor may be empty only when no blind candidate is feasible or conditional"
            )
    next_tranche = judgment.get("provisional_next_tranche")
    if not isinstance(next_tranche, dict):
        findings.append("provisional_next_tranche must be an object")
    else:
        candidate = next_tranche.get("blind_id")
        if candidate not in {"reserve", "none"} and candidate not in allowed_candidates:
            findings.append(
                "provisional_next_tranche.blind_id must be a blind ID, reserve, or none"
            )
        for field in ("description", "reason"):
            if not _is_non_empty_string(next_tranche.get(field)):
                findings.append(f"provisional_next_tranche.{field} must be a non-empty string")
    if not isinstance(judgment.get("missing_information", []), list):
        findings.append("missing_information must be a list")
    if not _is_non_empty_string(judgment.get("claim_ceiling")):
        findings.append("claim_ceiling must be a non-empty string")
    return findings


def _validate_refs(
    value: dict[str, Any],
    path: str,
    *,
    allowed_evidence: set[str],
    allowed_assumptions: set[str],
) -> list[str]:
    findings: list[str] = []
    for field, allowed in (
        ("evidence_refs", allowed_evidence),
        ("assumption_refs", allowed_assumptions),
    ):
        refs = value.get(field, [])
        if not _string_list(refs):
            findings.append(f"{path}.{field} must be a list of strings")
            continue
        unknown = sorted(set(refs) - allowed)
        if unknown:
            findings.append(f"{path}.{field} contains unknown IDs: {unknown}")
    return findings


def _normalized_state_items(raw_input: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    active_candidate = raw_input.get("active_candidate_id")
    if active_candidate:
        items.append(
            {
                "state_id": "S-active-candidate",
                "kind": "active_candidate",
                "data": {"candidate_id": active_candidate},
                "policy": "Current-path identity may affect switching analysis but not blind feasibility.",
            }
        )
    state_context = raw_input.get("state_context", {})
    for collection, kind in STATE_ITEM_KIND_BY_COLLECTION.items():
        values = state_context.get(collection, [])
        for value in sorted(values, key=digest_data):
            digest = digest_data({"kind": kind, "data": value}).split(":", 1)[1][:10]
            policy = "May adjust the blind result only when explicitly cited."
            if kind == "sunk_cost":
                policy = "Sunk-cost-only: visible for rejection and never a continuation reason."
            items.append(
                {
                    "state_id": f"S-{kind.replace('_', '-')}-{digest}",
                    "kind": kind,
                    "data": value,
                    "policy": policy,
                }
            )
    return items


def build_state_packet(
    *,
    raw_input: dict[str, Any],
    sealed_packet: dict[str, Any],
    blind_packet: dict[str, Any],
    candidate_map: dict[str, str],
    blind_judgment: dict[str, Any],
) -> dict[str, Any]:
    candidate_by_id = {item["candidate_id"]: item for item in raw_input["candidates"]}
    mapping = [
        {
            "blind_id": blind_id,
            "candidate_id": candidate_id,
            "title": candidate_by_id[candidate_id]["title"],
        }
        for blind_id, candidate_id in sorted(candidate_map.items())
    ]
    state_items = _normalized_state_items(raw_input)
    state_evidence_ids = {
        item["evidence_id"] for item in blind_packet.get("evidence", [])
    }
    state_assumption_ids = {
        item["assumption_id"] for item in blind_packet.get("assumptions", [])
    }
    for item in state_items:
        data = item.get("data", {})
        state_evidence_ids.update(data.get("evidence_refs", []))
        state_assumption_ids.update(data.get("assumption_refs", []))
    state_evidence = [
        item
        for item in raw_input.get("evidence", [])
        if item["evidence_id"] in state_evidence_ids
    ]
    state_assumptions = [
        item
        for item in raw_input.get("assumptions", [])
        if item["assumption_id"] in state_assumption_ids
    ]
    base = {
        "schema_version": STATE_PACKET_SCHEMA,
        "run_id": raw_input["run_id"],
        "mode": sealed_packet["mode"],
        "sealed_packet_hash": sealed_packet["packet_hash"],
        "blind_packet_hash": blind_packet["packet_hash"],
        "blind_judgment_hash": digest_data(blind_judgment),
        "allocation_frame": raw_input["allocation_frame"],
        "candidate_mapping": mapping,
        "active_candidate_id": raw_input.get("active_candidate_id"),
        "state_items": state_items,
        "historical_spend_policy": (
            "historical spend is sunk-cost-only and cannot justify continuation"
        ),
        "evidence": state_evidence,
        "assumptions": state_assumptions,
        "blind_judgment": blind_judgment,
        "state_boundary": {
            "allowed_adjustments": sorted(STATE_ADJUSTMENT_KINDS),
            "allowed_state_refs": [item["state_id"] for item in state_items],
            "sunk_cost_may_justify_continuation": False,
            "external_context_forbidden": True,
        },
    }
    packet = dict(base)
    packet["packet_hash"] = digest_data(base)
    return packet


def validate_state_judgment(judgment: Any, state_packet: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if not isinstance(judgment, dict):
        return ["state-aware judgment must be an object"]
    if judgment.get("schema_version") != STATE_JUDGMENT_SCHEMA:
        findings.append(f"schema_version must be {STATE_JUDGMENT_SCHEMA}")
    if judgment.get("stage") != "state_aware":
        findings.append("stage must be state_aware")
    if judgment.get("packet_hash") != state_packet.get("packet_hash"):
        findings.append("packet_hash does not match state-packet.json")
    if judgment.get("blind_judgment_hash") != state_packet.get("blind_judgment_hash"):
        findings.append("blind_judgment_hash does not match the locked blind judgment")
    if judgment.get("decision") not in FINAL_DECISIONS:
        findings.append("decision is unsupported")
    if not isinstance(judgment.get("blind_result_changed"), bool):
        findings.append("blind_result_changed must be boolean")
    if not _is_non_empty_string(judgment.get("change_reason")):
        findings.append("change_reason must be a non-empty string")
    if judgment.get("sunk_cost_used_as_reason") is not False:
        findings.append("sunk_cost_used_as_reason must be false")

    allowed_candidates = {
        item["candidate_id"] for item in state_packet.get("candidate_mapping", [])
    }
    allowed_evidence = {item["evidence_id"] for item in state_packet.get("evidence", [])}
    allowed_assumptions = {
        item["assumption_id"] for item in state_packet.get("assumptions", [])
    }
    state_kind_by_id = {
        item["state_id"]: item["kind"] for item in state_packet.get("state_items", [])
    }
    allowed_state = set(state_kind_by_id)
    adjustments = judgment.get("state_adjustments")
    if not isinstance(adjustments, list):
        findings.append("state_adjustments must be a list")
        adjustments = []
    substantive_adjustment_refs: set[str] = set()
    for index, adjustment in enumerate(adjustments):
        path = f"state_adjustments[{index}]"
        if not isinstance(adjustment, dict):
            findings.append(f"{path} must be an object")
            continue
        if adjustment.get("kind") not in STATE_ADJUSTMENT_KINDS:
            findings.append(f"{path}.kind is unsupported")
        if not _is_non_empty_string(adjustment.get("finding")):
            findings.append(f"{path}.finding must be a non-empty string")
        state_refs = adjustment.get("state_refs", [])
        if not _string_list(state_refs):
            findings.append(f"{path}.state_refs must be a list of strings")
        else:
            unknown_state = sorted(set(state_refs) - allowed_state)
            if unknown_state:
                findings.append(f"{path}.state_refs contains unknown IDs: {unknown_state}")
            adjustment_kind = adjustment.get("kind")
            if adjustment_kind != "none" and not state_refs:
                findings.append(f"{path}.state_refs must cite admitted state information")
            expected_kinds = STATE_REF_KINDS_BY_ADJUSTMENT.get(str(adjustment_kind), set())
            mismatched = [
                state_ref
                for state_ref in state_refs
                if state_ref in state_kind_by_id
                and state_kind_by_id[state_ref] not in expected_kinds
            ]
            if mismatched:
                findings.append(
                    f"{path}.state_refs do not match adjustment kind {adjustment_kind}: {mismatched}"
                )
            if adjustment_kind not in {"none", "sunk_cost_rejected"}:
                substantive_adjustment_refs.update(
                    state_ref
                    for state_ref in state_refs
                    if state_ref in state_kind_by_id
                    and state_kind_by_id[state_ref] not in {"active_candidate", "sunk_cost"}
                )
        findings.extend(
            _validate_refs(
                adjustment,
                path,
                allowed_evidence=allowed_evidence,
                allowed_assumptions=allowed_assumptions,
            )
        )

    current_floor = judgment.get("current_floor")
    if not _string_list(current_floor):
        findings.append("current_floor must be a list of candidate IDs")
    else:
        unknown = sorted(set(current_floor) - allowed_candidates)
        if unknown:
            findings.append(f"current_floor contains unknown candidate IDs: {unknown}")
        if judgment.get("decision") not in {"infeasible", "blocked"} and not current_floor:
            findings.append("current_floor must not be empty for an actionable allocation")
    next_tranche = judgment.get("next_tranche")
    if not isinstance(next_tranche, dict):
        findings.append("next_tranche must be an object")
    else:
        candidate = next_tranche.get("candidate_id")
        if candidate not in {"reserve", "none"} and candidate not in allowed_candidates:
            findings.append(
                "next_tranche.candidate_id must reference a candidate, reserve, or none"
            )
        if judgment.get("decision") not in {"infeasible", "blocked"} and candidate == "none":
            findings.append("an actionable allocation cannot use next_tranche.candidate_id=none")
        for field in ("description", "reason"):
            if not _is_non_empty_string(next_tranche.get(field)):
                findings.append(f"next_tranche.{field} must be a non-empty string")
    for field in ("investment_ceiling", "claim_ceiling"):
        if not _is_non_empty_string(judgment.get(field)):
            findings.append(f"{field} must be a non-empty string")
    if judgment.get("authorization_horizon") not in AUTHORIZATION_HORIZONS:
        findings.append("authorization_horizon is unsupported")
    for field in ("maintenance", "defer", "stop", "rerank_triggers"):
        if not _string_list(judgment.get(field, [])):
            findings.append(f"{field} must be a list of strings")
    if not judgment.get("rerank_triggers"):
        findings.append("rerank_triggers must not be empty")
    reserve = judgment.get("reserve")
    if not isinstance(reserve, dict):
        findings.append("reserve must be an object")
    else:
        if reserve.get("status") not in {"none", "reserved"}:
            findings.append("reserve.status must be none or reserved")
        for field in ("reason", "release_trigger", "review_time"):
            if not _is_non_empty_string(reserve.get(field)):
                findings.append(f"reserve.{field} must be a non-empty string")
    top_state_refs = judgment.get("state_refs", [])
    if not _string_list(top_state_refs):
        findings.append("state_judgment.state_refs must be a list of strings")
    else:
        unknown_state = sorted(set(top_state_refs) - allowed_state)
        if unknown_state:
            findings.append(f"state_judgment.state_refs contains unknown IDs: {unknown_state}")
    mapping_by_blind = {
        item["blind_id"]: item["candidate_id"]
        for item in state_packet.get("candidate_mapping", [])
    }
    blind_judgment = state_packet.get("blind_judgment", {})
    blind_floor = [
        mapping_by_blind.get(blind_id, blind_id)
        for blind_id in blind_judgment.get("current_floor", [])
    ]
    blind_next = blind_judgment.get("provisional_next_tranche", {}).get("blind_id")
    mapped_blind_next = mapping_by_blind.get(blind_next, blind_next)
    final_next = next_tranche.get("candidate_id") if isinstance(next_tranche, dict) else None
    changed = judgment.get("blind_result_changed") is True
    if not changed:
        if current_floor != blind_floor:
            findings.append(
                "blind_result_changed=false requires current_floor to preserve the locked blind floor"
            )
        if final_next != mapped_blind_next:
            findings.append(
                "blind_result_changed=false requires next_tranche to preserve the locked blind replenishment choice"
            )
    else:
        if not top_state_refs:
            findings.append("a changed blind result must cite state_judgment.state_refs")
        substantive_top_refs = {
            state_ref
            for state_ref in top_state_refs
            if state_ref in state_kind_by_id
            and state_kind_by_id[state_ref] not in {"active_candidate", "sunk_cost"}
        }
        if not substantive_top_refs:
            findings.append(
                "a changed blind result requires non-sunk, non-identity state references"
            )
        if not substantive_adjustment_refs:
            findings.append(
                "a changed blind result requires a substantive state adjustment with matching state references"
            )
    findings.extend(
        _validate_refs(
            judgment,
            "state_judgment",
            allowed_evidence=allowed_evidence,
            allowed_assumptions=allowed_assumptions,
        )
    )
    return findings


def prompt_for_blind(packet: dict[str, Any]) -> str:
    return f"""# SRA packet-bound blind allocation judgment

You are the semantic SRA allocation owner. Judge only from the sealed packet below.
Do not import ambient conversation, previous conclusions, project memory, or unstated
facts. Cite only packet evidence IDs and assumption IDs. If the candidate surface is
insufficient, return missing information rather than inventing priority.

This is the blind pass. You do not know which candidate is active. Run contraction
before naming the current floor, then choose a provisional replenishment tranche.
Do not mutate files, tasks, Mission state, memory, or external systems.

Return JSON matching `sra.blind-judgment.v0.1` with:

- `schema_version`, `stage=blind`, `packet_hash`, `mode`;
- one `candidate_assessments` entry per blind candidate containing `blind_id`,
  `feasibility`, `candidate_role`, `contraction_result`, `first_break_point`,
  `evidence_refs`, and `assumption_refs`;
- `current_floor` as blind IDs;
- `provisional_next_tranche` with `blind_id`, `description`, and `reason`;
- `missing_information` and `claim_ceiling`.

Blind packet:

```json
{json.dumps(packet, ensure_ascii=False, indent=2)}
```
"""


def prompt_for_state(packet: dict[str, Any]) -> str:
    return f"""# SRA packet-bound state-aware reconciliation

You are the semantic SRA allocation owner. Reconcile the locked blind judgment with the
state packet below. Use only packet candidate, evidence, and assumption IDs. Do not
import ambient context or repeat a previous conclusion as proof.

Switching cost, reusable assets, remaining cost, commitments, and authority may adjust
the blind result. Historical spend is sunk cost and cannot justify continuation.
State whether the blind result changed and cite the admitted state information that
caused the change. Do not mutate files, tasks, Mission state, memory, or external systems.

Return JSON matching `sra.state-judgment.v0.1` with:

- `schema_version`, `stage=state_aware`, `packet_hash`, `blind_judgment_hash`;
- `decision`, `blind_result_changed`, `change_reason`,
  `sunk_cost_used_as_reason=false`;
- `state_adjustments` entries containing `kind`, `finding`, `state_refs`,
  `evidence_refs`, and `assumption_refs`;
- `current_floor`, `next_tranche`, `investment_ceiling`, `authorization_horizon`;
- `maintenance`, `reserve`, `defer`, `stop`, `rerank_triggers`;
- top-level `state_refs`, `evidence_refs`, `assumption_refs`, and `claim_ceiling`.

State packet:

```json
{json.dumps(packet, ensure_ascii=False, indent=2)}
```
"""


def effective_isolation_claim(
    carriers: dict[str, str], receipts: dict[str, dict[str, Any]] | None = None
) -> str:
    """Report only the observable packet/carrier boundary; never assert hidden-context absence."""

    blind = carriers.get("blind")
    state = carriers.get("state_aware")
    receipts = receipts or {}
    fresh = {"fresh_subagent", "ephemeral_cli"}
    if blind in fresh and state in fresh:
        if "blind" in receipts and "state_aware" in receipts:
            return "fresh_two_pass_with_receipts"
        return "fresh_two_pass_declared"
    if blind in fresh or state in fresh:
        if (blind in fresh and "blind" in receipts) or (
            state in fresh and "state_aware" in receipts
        ):
            return "fresh_partial_with_receipt"
        return "fresh_partial_declared"
    return "logical_packet_only"


def carrier_dispatch(
    prompt_path: Path,
    *,
    stage: str,
    output_path: Path,
    output_schema_path: Path,
) -> dict[str, Any]:
    return {
        "tool": "multi_agent_v1.spawn_agent",
        "agent_type": "explorer",
        "fork_context": False,
        "message_file": str(prompt_path),
        "output_schema_file": str(output_schema_path),
        "tool_policy": "no_tools",
        "authority_boundary": "sra_semantic_allocation_only",
        "read_only": True,
        "must_not_mutate": [
            "files",
            "Mission state",
            "task state",
            "evidence records",
            "memory",
            "external systems",
        ],
        "expected_output_file": str(output_path),
        "stage": stage,
    }


def carrier_command(
    *,
    prompt_path: Path,
    output_path: Path,
    output_schema_path: Path,
    workspace_path: Path,
) -> str:
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "PROMPT=" + shlex.quote(str(prompt_path)),
            "OUTPUT=" + shlex.quote(str(output_path)),
            "OUTPUT_SCHEMA=" + shlex.quote(str(output_schema_path)),
            "WORKSPACE=" + shlex.quote(str(workspace_path)),
            "mkdir -p \"$WORKSPACE\"",
            "codex exec --ephemeral --ignore-rules --ignore-user-config \\",
            "  --skip-git-repo-check -s read-only -C \"$WORKSPACE\" \\",
            "  --output-schema \"$OUTPUT_SCHEMA\" -o \"$OUTPUT\" - < \"$PROMPT\"",
            "",
        ]
    )


def run_check(run_dir: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    try:
        state = load_run(run_dir)
    except SraRuntimeError as exc:
        return {
            "schema_version": CHECK_REPORT_SCHEMA,
            "run_dir": str(run_dir),
            "status": "blocked",
            "findings": [{"severity": "block", "code": "run-state", "message": str(exc)}],
        }

    def add(severity: str, code: str, message: str) -> None:
        findings.append({"severity": severity, "code": code, "message": message})

    required_files = {
        "prepared": [
            "raw-input.json",
            "context-admission.json",
            "sealed-packet.json",
            "blind-packet.json",
            "blind-agent-prompt.md",
            "blind-output-schema.json",
            "blind-subagent-dispatch.json",
            "blind-codex-command.sh",
            "trace.jsonl",
        ],
        "blind_recorded": [
            "judgments/blind.json",
            "state-packet.json",
            "state-aware-agent-prompt.md",
            "state-aware-output-schema.json",
            "state-aware-subagent-dispatch.json",
            "state-aware-codex-command.sh",
        ],
        "finalized": ["judgments/state-aware.json", "final-decision.json"],
    }
    stage = state.get("stage")
    if stage not in {"prepared", "blind_recorded", "finalized"}:
        add("block", "stage", f"unsupported stage: {stage!r}")
    stages = ["prepared"]
    if stage in {"blind_recorded", "finalized"}:
        stages.append("blind_recorded")
    if stage == "finalized":
        stages.append("finalized")
    for current in stages:
        for rel in required_files[current]:
            if not (run_dir / rel).is_file():
                add("block", "missing-file", f"missing required run file: {rel}")

    try:
        raw_input = load_json(run_dir / "raw-input.json")
        admission = load_json(run_dir / "context-admission.json")
        sealed = load_json(run_dir / "sealed-packet.json")
        blind = load_json(run_dir / "blind-packet.json")
        rebuilt = build_packets(raw_input)
        if rebuilt["admission"] != admission:
            add("block", "admission-rebuild", "context admission does not match deterministic rebuild")
        if rebuilt["candidate_map"] != state.get("candidate_map"):
            add("block", "candidate-map", "run candidate_map does not match deterministic blind mapping")
        if rebuilt["sealed_packet"] != sealed:
            add("block", "sealed-rebuild", "sealed packet does not match deterministic rebuild")
        if rebuilt["blind_packet"] != blind:
            add("block", "blind-rebuild", "blind packet does not match deterministic rebuild")
        blind_schema = load_json(run_dir / "blind-output-schema.json")
        if blind_schema != blind_output_schema(blind):
            add("block", "blind-output-schema", "blind output schema does not match the packet")
        if digest_data(raw_input) != state.get("raw_input_hash"):
            add("block", "raw-input-hash", "raw-input.json does not match the locked run hash")
        if digest_data(admission) != state.get("context_manifest_hash"):
            add("block", "context-manifest-hash", "context-admission.json does not match the locked run hash")
        if sealed.get("raw_input_hash") != state.get("raw_input_hash"):
            add("block", "sealed-raw-input-hash", "sealed packet does not bind the current raw input")
        if sealed.get("context_manifest_hash") != state.get("context_manifest_hash"):
            add("block", "sealed-context-hash", "sealed packet does not bind the admission ledger")
        if blind.get("context_manifest_hash") != state.get("context_manifest_hash"):
            add("block", "blind-context-hash", "blind packet does not bind the admission ledger")
        if sealed.get("packet_hash") != state.get("sealed_packet_hash"):
            add("block", "sealed-hash", "run state sealed_packet_hash does not match packet")
        if blind.get("packet_hash") != state.get("blind_packet_hash"):
            add("block", "blind-hash", "run state blind_packet_hash does not match packet")
        sealed_base = dict(sealed)
        sealed_hash = sealed_base.pop("packet_hash", None)
        if sealed_hash != digest_data(sealed_base):
            add("block", "sealed-content-hash", "sealed packet content hash is invalid")
        blind_base = dict(blind)
        blind_hash = blind_base.pop("packet_hash", None)
        if blind_hash != digest_data(blind_base):
            add("block", "blind-content-hash", "blind packet content hash is invalid")
    except (SraRuntimeError, SraValidationError, AttributeError) as exc:
        add("block", "packet-read", str(exc))

    carriers = state.get("carriers", {})
    receipts = state.get("carrier_receipts", {})
    requested = state.get("isolation_profile")
    override_reason = state.get("isolation_override_reason")
    if requested == "packet_bound" and _is_non_empty_string(override_reason):
        add(
            "warn",
            "degraded-isolation-override",
            "packet-bound isolation was explicitly retained under Full or contamination pressure; fresh-context independence remains unavailable",
        )
    if requested in {"fresh_context", "blind_then_state"}:
        used = set(carriers.values())
        if not used:
            add(
                "warn",
                "isolation-not-yet-observed",
                "fresh isolation was requested but no judgment carrier has been recorded",
            )
        elif used == {"packet_bound"}:
            add(
                "warn",
                "logical-isolation-only",
                "the run requested fresh isolation but only packet-bound same-context carriers were recorded",
            )
    for carrier_stage, carrier in carriers.items():
        if carrier not in {"fresh_subagent", "ephemeral_cli"}:
            continue
        receipt = receipts.get(carrier_stage)
        if not isinstance(receipt, dict):
            add(
                "warn",
                "fresh-carrier-without-receipt",
                f"{carrier_stage} declares {carrier} but has no persisted observable receipt",
            )
            continue
        stored_path = receipt.get("stored_path")
        expected_hash = receipt.get("sha256")
        stored = Path(stored_path) if isinstance(stored_path, str) else Path("")
        if not stored.is_absolute():
            stored = run_dir / stored
        if not isinstance(stored_path, str) or not stored.is_file():
            add(
                "block",
                "carrier-receipt-missing",
                f"{carrier_stage} carrier receipt is not recoverable",
            )
            continue
        actual_hash = "sha256:" + hashlib.sha256(stored.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            add(
                "block",
                "carrier-receipt-hash",
                f"{carrier_stage} carrier receipt hash does not match",
            )

    if stage in {"blind_recorded", "finalized"}:
        blind_judgment = load_json(run_dir / "judgments" / "blind.json")
        errors = validate_blind_judgment(blind_judgment, load_json(run_dir / "blind-packet.json"))
        raw_for_identity = load_json(run_dir / "raw-input.json")
        errors.extend(
            hidden_candidate_identity_findings(
                blind_judgment, raw_for_identity.get("candidates", [])
            )
        )
        for message in errors:
            add("block", "blind-judgment", message)
        state_packet = load_json(run_dir / "state-packet.json")
        state_schema = load_json(run_dir / "state-aware-output-schema.json")
        if state_schema != state_output_schema(state_packet):
            add("block", "state-output-schema", "state-aware output schema does not match the packet")
        state_base = dict(state_packet)
        state_hash = state_base.pop("packet_hash", None)
        if state_hash != digest_data(state_base):
            add("block", "state-content-hash", "state packet content hash is invalid")
        if state_hash != state.get("state_packet_hash"):
            add("block", "state-hash", "run state state_packet_hash does not match packet")
        if digest_data(blind_judgment) != state.get("blind_judgment_hash"):
            add("block", "blind-judgment-hash", "recorded blind judgment does not match run state")
    if stage == "finalized":
        state_packet = load_json(run_dir / "state-packet.json")
        state_judgment = load_json(run_dir / "judgments" / "state-aware.json")
        errors = validate_state_judgment(state_judgment, state_packet)
        for message in errors:
            add("block", "state-judgment", message)
        if digest_data(state_judgment) != state.get("state_judgment_hash"):
            add("block", "state-judgment-hash", "recorded state judgment does not match run state")
        try:
            final = load_json(run_dir / "final-decision.json")
            if final.get("schema_version") != "sra.final-decision.v0.1":
                add("block", "final-schema", "final-decision.json has an unsupported schema")
            for field in (
                "sealed_packet_hash",
                "blind_packet_hash",
                "blind_judgment_hash",
                "state_packet_hash",
                "state_judgment_hash",
            ):
                if final.get(field) != state.get(field):
                    add("block", "final-hash", f"final-decision.json {field} does not match run state")
            if final.get("decision") != state_judgment:
                add("block", "final-decision-copy", "final decision does not match the recorded state judgment")
            if final.get("carriers") != carriers:
                add("block", "final-carriers", "final decision carrier record does not match run state")
            if final.get("carrier_receipts") != receipts:
                add("block", "final-carrier-receipts", "final decision carrier receipts do not match run state")
            expected_isolation = effective_isolation_claim(carriers, receipts)
            if final.get("effective_isolation_claim") != expected_isolation:
                add(
                    "block",
                    "final-isolation-claim",
                    "final decision isolation claim exceeds or contradicts recorded carriers",
                )
            if state.get("effective_isolation_claim") != expected_isolation:
                add(
                    "block",
                    "state-isolation-claim",
                    "run state isolation claim exceeds or contradicts recorded carriers",
                )
            if final.get("requested_isolation_profile") != state.get("isolation_profile"):
                add(
                    "block",
                    "final-isolation-profile",
                    "final decision requested isolation profile does not match run state",
                )
            if final.get("isolation_override_reason") != state.get("isolation_override_reason"):
                add(
                    "block",
                    "final-isolation-override",
                    "final decision isolation override reason does not match run state",
                )
            if not _is_non_empty_string(final.get("isolation_boundary")):
                add("block", "final-isolation-boundary", "final decision must state its isolation boundary")
        except (SraRuntimeError, AttributeError) as exc:
            add("block", "final-read", str(exc))

    try:
        trace = load_jsonl(run_dir / "trace.jsonl")
        event_types = [item.get("event_type") for item in trace]
        expected_events = ["run_prepared"]
        if stage in {"blind_recorded", "finalized"}:
            expected_events.append("blind_judgment_recorded")
        if stage == "finalized":
            expected_events.append("state_judgment_recorded")
        if event_types != expected_events:
            add(
                "block",
                "trace-order",
                f"trace events must be exactly {expected_events}; found {event_types}",
            )
        for index, event in enumerate(trace):
            if event.get("schema_version") != TRACE_SCHEMA:
                add("block", "trace-schema", f"trace event {index} has an unsupported schema")
            if event.get("run_id") != state.get("run_id"):
                add("block", "trace-run-id", f"trace event {index} has the wrong run_id")
    except SraRuntimeError as exc:
        add("block", "trace-read", str(exc))

    status = "blocked" if any(item["severity"] == "block" for item in findings) else (
        "warning" if findings else "ok"
    )
    return {
        "schema_version": CHECK_REPORT_SCHEMA,
        "run_dir": str(run_dir),
        "run_id": state.get("run_id"),
        "stage": stage,
        "isolation_profile": requested,
        "recorded_carriers": carriers,
        "status": status,
        "findings": findings,
        "truth_boundary": (
            "This report checks packet, workflow, hashes, references, stage order, and observable carrier claims only; it does not validate semantic priority, complete context, or host-level isolation."
        ),
    }
