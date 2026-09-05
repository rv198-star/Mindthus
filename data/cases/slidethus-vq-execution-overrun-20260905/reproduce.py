#!/usr/bin/env python3
"""Read-only-on-repository probes derived from one bounded real-use incident.

All Missions and artifacts are synthetic and live in TemporaryDirectory. This is an
incident diagnostic, not a regression gate that expects bugs to persist. Each probe
reports the observed boundary; a later fix should change the observation. Exit 0 means
the probes ran, not that the runtime is correct. No original Mission is reconstructed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "skills/tplan/scripts"))
import tplan_runtime as runtime
from tests.tplan.test_apply_decision import create_mission, valid_path_assessment


def digest_files(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def evidence_and_trace(mission: Path) -> tuple[list[dict], list[dict]]:
    def load(name: str) -> list[dict]:
        path = mission / name
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    return load("evidence.jsonl"), load("execution_trace.jsonl")


def add_evidence(mission: Path, event_type: str = "key_finding") -> str:
    event = runtime.append_event(mission, {
        "event_type": event_type, "task_id": "T1",
        "summary": "Synthetic diagnostic evidence; not real task acceptance.",
        "payload": {"acceptance_ids": ["A1"]} if event_type.startswith("acceptance_") else {},
    })
    return event["id"]


def transition_reference(kind: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mindthus-case-ref-") as tmp:
        mission = create_mission(tmp, human_in_loop=0)
        runtime.transition_task_status(mission, "T1", "active")
        kwargs: dict[str, Any] = {}
        if kind == "existing_evidence":
            kwargs["evidence_refs"] = [add_evidence(mission)]
        elif kind == "missing_evidence":
            kwargs["evidence_refs"] = ["EPLACEHOLDER"]
        else:
            artifact = Path(tmp) / "inspected.txt"
            artifact.write_text("Synthetic artifact; no product or private content.\n")
            kwargs["artifact_refs" if kind == "artifact_as_artifact" else "evidence_refs"] = [str(artifact)]
        before = digest_files(mission)
        try:
            runtime.transition_task_status(mission, "T1", "completed", **kwargs)
            disposition, error = "accepted", None
        except (runtime.TplanError, ValueError) as exc:
            disposition, error = "rejected", str(exc)
        evidence, trace = evidence_and_trace(mission)
        ids = {item["id"] for item in evidence}
        completion = [e for e in trace if e.get("event_type") == "task_status_changed"
                      and e.get("task_id") == "T1" and e.get("payload", {}).get("to_status") == "completed"]
        refs = completion[-1].get("refs", {}).get("evidence_ids", []) if completion else []
        state = runtime.read_mission(mission)
        return {
            "kind": kind, "disposition": disposition, "error": error,
            "task_status": runtime.find_task(state, "T1")["status"],
            "unresolved_evidence_ref_count": sum(ref not in ids for ref in refs),
            "writes_if_rejected": digest_files(mission) != before if disposition == "rejected" else None,
        }


def addition(status: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mindthus-case-cursor-") as tmp:
        mission = create_mission(tmp, human_in_loop=0)
        before = digest_files(mission)
        try:
            runtime.add_task_node(mission, {
                "id": "T6", "kind": "task", "title": "Synthetic repair task",
                "role": "supporting", "status": status,
                "mission_contribution": "Supports the existing objective.",
                "acceptance_evidence": [],
            })
            disposition, error = "accepted", None
        except (runtime.TplanError, ValueError) as exc:
            disposition, error = "rejected", str(exc)
        state = runtime.read_mission(mission)
        _, trace = evidence_and_trace(mission)
        task = next((t for t in state["tasks"] if t["id"] == "T6"), None)
        return {
            "requested_status": status, "disposition": disposition, "error": error,
            "created_status": task["status"] if task else None,
            "active_task_id": state["active_task_id"],
            "matching_active_node_event": any(e.get("event_type") == "active_node_changed"
                                               and e.get("task_id") == "T6" for e in trace),
            "shape_findings": runtime.validate_mission(state),
            "writes_if_rejected": digest_files(mission) != before if disposition == "rejected" else None,
        }


def ordinary_activation() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mindthus-case-activation-") as tmp:
        mission = create_mission(tmp, human_in_loop=0)
        runtime.transition_task_status(mission, "T1", "active")
        state = runtime.read_mission(mission)
        _, trace = evidence_and_trace(mission)
        return {"task_status": runtime.find_task(state, "T1")["status"],
                "active_task_id": state["active_task_id"],
                "active_node_changed_events": sum(e["event_type"] == "active_node_changed" for e in trace)}


def decision(recommendation: str, mutations: list[dict]) -> dict[str, Any]:
    return {
        "recommendation": recommendation, "rationale": "Synthetic boundary probe, not a true acceptance claim.",
        "confidence": 50, "evidence_links": [], "proposed_mutations": mutations,
        "requires_human": False, "mission_alignment": "Tests the declared runtime boundary.",
        "path_assessment": valid_path_assessment(),
    }


def mission_completion(failed_evidence: bool = False) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mindthus-case-close-") as tmp:
        mission = create_mission(tmp, human_in_loop=0)
        if failed_evidence:
            add_evidence(mission, "acceptance_failed")
        value = decision("close", [{"type": "set_mission_status", "status": "completed"}])
        before = digest_files(mission)
        try:
            result, error = runtime.apply_decision(mission, value), None
        except (runtime.TplanError, ValueError) as exc:
            result, error = "rejected", str(exc)
        state = runtime.read_mission(mission)
        evidence, _ = evidence_and_trace(mission)
        return {
            "with_failed_acceptance": failed_evidence, "result": result, "error": error,
            "mission_status": state["mission"]["status"],
            "success_critical_statuses": {t["id"]: t["status"] for t in state["tasks"] if t["role"] == "success-critical"},
            "passed_acceptance_events": sum(e["event_type"] == "acceptance_passed" for e in evidence),
            "failed_acceptance_events": sum(e["event_type"] == "acceptance_failed" for e in evidence),
            "shape_findings": runtime.validate_mission(state),
            "writes_if_rejected": digest_files(mission) != before if result == "rejected" else None,
        }


def continuation_contradiction() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="mindthus-case-continue-") as tmp:
        mission = create_mission(tmp, human_in_loop=0)
        value = decision("continue", [{"type": "set_active_task", "task_id": "T1"}])
        value["continuation_authorization"] = {
            "trigger_reasons": ["repeated_same_path_attempt"], "evidence_shape_lint": "fail",
            "defect_classification": "acceptance_blocking", "expected_evidence_delta": "no_new_evidence_expected",
            "authorized_action": "stop",
        }
        findings = runtime.validate_hook_output(value)
        before = digest_files(mission)
        try:
            result, error = runtime.apply_decision(mission, value), None
        except (runtime.TplanError, ValueError) as exc:
            result, error = "rejected", str(exc)
        state = runtime.read_mission(mission)
        return {
            "authorized_action": "stop", "recommendation": "continue", "validation_findings": findings,
            "result": result, "error": error, "active_task_id": state["active_task_id"],
            "task_status": runtime.find_task(state, "T1")["status"],
            "writes_if_rejected": digest_files(mission) != before if result == "rejected" else None,
        }


def verify_packet_copy() -> dict[str, Any]:
    case = Path(__file__).resolve().parent
    admission = json.loads((case / "admission.json").read_text(encoding="utf-8"))
    expected = {row["path"]: row for row in admission["source"]["files"]}
    source = case / "packet"
    actual = {p.relative_to(source).as_posix(): p for p in source.rglob("*") if p.is_file()}
    if set(actual) != set(expected):
        raise RuntimeError("stored packet inventory differs from the uploaded packet")
    for name, path in actual.items():
        raw = path.read_bytes()
        if len(raw) != expected[name]["bytes"] or hashlib.sha256(raw).hexdigest() != expected[name]["sha256"]:
            raise RuntimeError("uploaded packet bytes changed: " + name)
    # The exporter validator checks the original directory name. Materialize only
    # this exact reviewed packet in a fresh temporary directory, not in the repo.
    with tempfile.TemporaryDirectory(prefix="mindthus-case-packet-check-") as tmp:
        target = Path(tmp) / admission["source"]["original_directory"]
        shutil.copytree(source, target)
        check = subprocess.run([sys.executable, str(REPO / "skills/case-prep/scripts/validate_case_packet.py"),
                                str(target), "--json"], text=True, capture_output=True)
        if check.returncode:
            raise RuntimeError(check.stdout + check.stderr)
        report = json.loads(check.stdout)
    return {"source_file_hashes_matched": len(actual), "packet_status": report["status"],
            "block_count": report["block_count"], "warning_count": report["warning_count"],
            "validation_location": "fresh temporary copy with original export directory name",
            "repository_packet_modified": False, "source_consent_flags_preserved": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-only", action="store_true")
    args = parser.parse_args()
    packet_check = verify_packet_copy()
    if args.packet_only:
        print(json.dumps(packet_check, ensure_ascii=False, indent=2))
        return
    git = lambda *a: subprocess.check_output(["git", "-C", str(REPO), *a], text=True).strip()
    result = {
        "packet_validation": packet_check,
        "case_id": "slidethus-vq-execution-overrun-20260905",
        "probe_kind": "synthetic_current_runtime_boundary_check",
        "product_base_commit": git("rev-parse", "HEAD"), "python": sys.version.split()[0],
        "claim_ceiling": "Only current supported API behavior; not original run replay, model behavior or causal ROI.",
        "reference_probes": [transition_reference(k) for k in (
            "missing_evidence", "artifact_as_evidence", "existing_evidence", "artifact_as_artifact")],
        "node_addition": [addition("active"), addition("pending")],
        "ordinary_activation": ordinary_activation(),
        "completion": [mission_completion(False), mission_completion(True)],
        "continuation_consistency": continuation_contradiction(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
