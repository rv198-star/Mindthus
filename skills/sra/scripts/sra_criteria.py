"""Completion-only shared criteria; identity binding is not semantic approval."""
from __future__ import annotations

import copy
import re
from typing import Any

from sra_serialization import digest_data

CATALOG_VERSION = "sra.completion-criteria.v1"
FIELDS = {"criterion_id", "revision", "subject", "observable_result", "evidence_requirement", "window", "source", "content_hash"}


def criterion_hash(criterion: dict[str, Any]) -> str:
    return digest_data({k: v for k, v in criterion.items() if k != "content_hash"})


def criteria_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = data.get("completion_criteria")
    return catalog.get("items", []) if isinstance(catalog, dict) else []


def validate_criteria_input(data: dict[str, Any]) -> list[str]:
    catalog = data.get("completion_criteria")
    candidate_values = data.get("candidates", [])
    candidates = candidate_values if isinstance(candidate_values, list) else []
    if "completion_criteria" not in data:
        return ["candidate completion_criterion_ids requires a completion_criteria catalog"] if any(
            isinstance(c, dict) and "completion_criterion_ids" in c for c in candidates
        ) else []
    if not isinstance(catalog, dict) or set(catalog) != {"version", "items"} or catalog.get("version") != CATALOG_VERSION:
        return ["completion_criteria requires the supported version and items only"]
    if not isinstance(catalog["items"], list) or not catalog["items"]:
        return ["completion_criteria.items must be a non-empty list"]
    errors, known = [], set()
    candidate_ids = [c.get("candidate_id") for c in candidates if isinstance(c, dict)]
    for index, item in enumerate(catalog["items"]):
        path = f"completion_criteria.items[{index}]"
        if not isinstance(item, dict) or set(item) != FIELDS:
            errors.append(path + " must contain exactly the criterion identity, semantics, source and hash")
            continue
        if any(not isinstance(item[k], str) or not item[k].strip() for k in FIELDS):
            errors.append(path + " fields must be non-empty strings")
            continue
        identifier = item["criterion_id"]
        if not re.fullmatch(r"CR-[A-Za-z0-9._-]{1,48}", identifier) or identifier in known:
            errors.append(path + " criterion_id must be unique and use a neutral CR- identifier")
        known.add(identifier)
        if item["content_hash"] != criterion_hash(item):
            errors.append(path + " content_hash does not match the declared criterion")
        text = " ".join(item[k] for k in FIELDS if k != "content_hash")
        for candidate_id in candidate_ids:
            if isinstance(candidate_id, str) and re.search(r"(?<![A-Za-z0-9._-])" + re.escape(candidate_id) + r"(?![A-Za-z0-9._-])", text):
                errors.append(path + " must use neutral wording, without original candidate identifiers")
    used = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        ids = candidate.get("completion_criterion_ids", [])
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            errors.append("completion_criterion_ids must be a list of criterion identifiers")
            continue
        if len(ids) != len(set(ids)) or set(ids) - known:
            errors.append("completion_criterion_ids contains duplicate or unknown criteria")
        used.update(ids)
    if known - used:
        errors.append("completion_criteria contains unbound criteria; bind them to eligible candidates")
    return errors


def criteria_packet_fields(data: dict[str, Any]) -> dict[str, Any]:
    return {"completion_criteria": copy.deepcopy(data["completion_criteria"])} if "completion_criteria" in data else {}


def completion_reference(packet: dict[str, Any], criterion_id: str) -> dict[str, str]:
    item = next((c for c in criteria_items(packet) if c["criterion_id"] == criterion_id), None)
    if item is None:
        raise ValueError("unknown completion criterion")
    return {k: item[k] for k in ("criterion_id", "revision", "content_hash")} | {"packet_hash": packet["packet_hash"]}


def tranche_schema(base: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    """Free text remains conservative; referenced criteria replace, not shadow, it."""
    if not criteria_items(packet):
        return base
    referenced = copy.deepcopy(base)
    referenced["required"].remove("completion_signal")
    referenced["properties"].pop("completion_signal")
    referenced["required"].append("completion_criterion_ref")
    referenced["properties"]["completion_criterion_ref"] = {"oneOf": [
        {"type": "object", "additionalProperties": False,
         "required": list(reference),
         "properties": {k: {"type": "string", "const": v} for k, v in reference.items()}}
        for reference in (completion_reference(packet, c["criterion_id"]) for c in criteria_items(packet))
    ]}
    return {"oneOf": [base, referenced]}


def validate_completion_reference(judgment: dict[str, Any], packet: dict[str, Any], id_field: str) -> list[str]:
    tranche = judgment["next_tranche"]
    reference = tranche.get("completion_criterion_ref")
    if reference is None:
        return []
    candidate = next((c for c in packet["candidates"] if c[id_field] == tranche["target_id"]), None)
    if candidate is None or reference["criterion_id"] not in candidate.get("completion_criterion_ids", []):
        return ["next_tranche completion criterion is not bound to its target candidate"]
    item = next(c for c in criteria_items(packet) if c["criterion_id"] == reference["criterion_id"])
    if tranche["window"] != item["window"]:
        return ["next_tranche.window must match the referenced completion criterion window"]
    return []


def normalized_reference(reference: dict[str, Any]) -> dict[str, Any]:
    # The validator binds each view's packet hash; comparison uses the shared identity.
    return {k: reference[k] for k in ("criterion_id", "revision", "content_hash")}


def resolved_completion(decision: dict[str, Any], raw: dict[str, Any]) -> str:
    tranche = decision["next_tranche"]
    reference = tranche.get("completion_criterion_ref")
    if reference is None:
        return str(tranche.get("completion_signal", ""))
    item = next(c for c in criteria_items(raw) if c["criterion_id"] == reference["criterion_id"])
    return f"{item['subject']}: {item['observable_result']}; {item['evidence_requirement']}; {item['window']} [{item['criterion_id']}@{item['revision']}]"


def differing_paths(left: Any, right: Any, path: str = "") -> list[str]:
    """Diagnostic field paths only; the existing disagreement still controls closure."""
    if left == right:
        return []
    if isinstance(left, dict) and isinstance(right, dict):
        paths = []
        for key in sorted(set(left) | set(right)):
            child = path + "/" + str(key).replace("~", "~0").replace("/", "~1")
            paths.extend(differing_paths(left[key], right[key], child) if key in left and key in right else [child])
        return paths
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return [p for index, pair in enumerate(zip(left, right)) for p in differing_paths(*pair, path + f"/{index}")]
    return [path or "/"]
