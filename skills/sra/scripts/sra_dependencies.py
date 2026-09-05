"""SRA dependency evidence and deterministic authorization consequences.

The packet owns the graph. Agentic judgments assess its edges; this module checks
those declarations, not the semantic truth of evidence or the best allocation.
"""
from __future__ import annotations
from typing import Any


def dependency_edges(packet: dict[str, Any], id_field: str) -> set[tuple[str, str]]:
    return {(str(c[id_field]), str(p)) for c in packet.get("candidates", [])
            for p in c.get("depends_on", [])}


def dependency_resolution_schema(packet: dict[str, Any], id_field: str) -> dict[str, Any]:
    ids = [c[id_field] for c in packet.get("candidates", [])]
    evidence = [e["evidence_id"] for e in packet.get("evidence", [])]
    return {
        "type": "array", "minItems": len(dependency_edges(packet, id_field)),
        "maxItems": len(dependency_edges(packet, id_field)),
        "description": (
            "Resolve every packet depends_on edge once. satisfied cites evidence bound to "
            "the prerequisite; unmet/unknown prevents immediate current or next allocation "
            "to its dependent. Inclusion in a bundle is not completion."
        ),
        "items": {
            "type": "object", "additionalProperties": False,
            "required": ["dependent_id", "prerequisite_id", "status", "evidence_refs", "reason"],
            "properties": {
                "dependent_id": {"type": "string", "enum": ids},
                "prerequisite_id": {"type": "string", "enum": ids},
                "status": {"type": "string", "enum": ["satisfied", "unmet", "unknown"]},
                "evidence_refs": {"type": "array", "uniqueItems": True,
                                  "items": {"type": "string", "enum": evidence}},
                "reason": {"type": "string", "minLength": 1},
            },
        },
    }


def validate_dependencies(judgment: dict[str, Any], packet: dict[str, Any], id_field: str) -> list[str]:
    """Run after structural validation; return domain errors without mutations."""
    edges = dependency_edges(packet, id_field)
    if not edges:
        return []
    errors: list[str] = []
    candidates = {str(c[id_field]): c for c in packet["candidates"]}
    resolutions: dict[tuple[str, str], dict[str, Any]] = {}
    for record in judgment["dependency_resolutions"]:
        edge = (record["dependent_id"], record["prerequisite_id"])
        if edge not in edges:
            errors.append(f"dependency resolution {edge} does not reference a packet edge")
        if edge in resolutions:
            errors.append(f"duplicate dependency resolution {edge}")
        resolutions[edge] = record
        bound_evidence = set(candidates.get(edge[1], {}).get("evidence_refs", []))
        cited = set(record["evidence_refs"])
        if not cited <= bound_evidence:
            errors.append(f"dependency {edge} evidence must be bound to its prerequisite candidate")
        if record["status"] == "satisfied" and not cited:
            errors.append(f"satisfied dependency {edge} requires prerequisite evidence")
    if set(resolutions) != edges:
        errors.append("dependency_resolutions must cover every packet dependency exactly once")
    if errors:
        return errors

    active = {str(row[id_field]) for row in judgment["allocation_ledger"] if row["current_allocations"]}
    target = judgment["next_tranche"]["target_id"]
    outcome = judgment["allocation_outcome"]
    if outcome == "allocate" and target in candidates:
        active.add(target)
    unresolved: dict[str, list[str]] = {}
    for (dependent, prerequisite), record in resolutions.items():
        if record["status"] != "satisfied":
            unresolved.setdefault(dependent, []).append(prerequisite)
            if dependent in active:
                errors.append(
                    f"candidate {dependent} has {record['status']} dependency {prerequisite}; "
                    "immediate allocation requires satisfied prerequisites"
                )

    bundle = judgment.get("bundle_decision", {})
    selected = next((b for b in bundle.get("bundle_assessments", [])
                     if b["bundle_id"] == bundle.get("selected_bundle_id")), None)
    members = set(selected["member_ids"]) if selected else set()
    if outcome == "allocate":
        for dependent in members:
            for prerequisite in unresolved.get(dependent, []):
                if prerequisite not in members:
                    errors.append(
                        f"selected bundle omits unresolved dependency {prerequisite} of {dependent}"
                    )

    # Completed edges stop traversal: historical cycles are not current deadlocks.
    def cycle_from(node: str, stack: tuple[str, ...], done: set[str]) -> bool:
        if node in stack:
            return True
        if node in done:
            return False
        if any(cycle_from(p, stack + (node,), done) for p in unresolved.get(node, [])):
            return True
        done.add(node)
        return False

    if outcome in {"allocate", "conditional"}:
        roots = active | members | ({target} if target in candidates else set())
        if any(cycle_from(root, (), set()) for root in roots):
            errors.append("unresolved dependency cycle prevents an executable selected path")
    return errors


def normalized_dependency_resolutions(judgment: dict[str, Any], mapping: dict[str, str]) -> list[dict[str, Any]]:
    values = [{"dependent_id": mapping.get(r["dependent_id"], r["dependent_id"]),
               "prerequisite_id": mapping.get(r["prerequisite_id"], r["prerequisite_id"]),
               "status": r["status"], "evidence_refs": sorted(r["evidence_refs"])}
              for r in judgment.get("dependency_resolutions", [])]
    return sorted(values, key=lambda r: (r["dependent_id"], r["prerequisite_id"]))
