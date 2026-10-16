"""Completion gate: superseded critical work needs one qualified replacement.

This is an in-memory structural contract test, not a model acceptance probe.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "tplan" / "scripts"))
from tplan_runtime import _mission_completion_findings  # noqa: E402


def mission():
    return {
        "schema_version": "tplan.v0.1",
        "mission": {
            "id": "mission-supersession-fixture",
            "status": "active",
            "acceptance_evidence": [{"id": "AC_GOAL", "description": "Verified outcome"}],
        },
        "tasks": [
            {"id": "T0", "role": "success-critical", "status": "completed",
             "acceptance_evidence": ["AC_GOAL"]},
            {"id": "T1", "role": "success-critical", "status": "superseded",
             "acceptance_evidence": ["AC_GOAL"]},
            {"id": "T2", "role": "success-critical", "status": "completed",
             "acceptance_evidence": ["AC_GOAL"]},
        ],
    }


def evidence(task="T2", kind="acceptance_passed", event_id="E-1"):
    return {
        "id": event_id,
        "timestamp": "2026-10-16T00:00:00+00:00",
        "event_type": kind,
        "summary": "Artifact checked and accepted",
        "task_id": task,
        "payload": {"acceptance_ids": ["AC_GOAL"]},
    }


def test_superseded_critical_with_unique_accepted_successor_closes():
    assert _mission_completion_findings(mission(), [evidence()]) == []


def test_superseded_without_qualified_successor_stays_blocked():
    result = _mission_completion_findings(mission(), [])
    assert any("T1" in item for item in result)
    assert any("AC_GOAL" in item for item in result)


def test_pending_active_blocked_and_abandoned_still_block():
    for status in ("pending", "active", "blocked", "abandoned", "pruned"):
        state = mission()
        state["tasks"][1]["status"] = status
        result = _mission_completion_findings(state, [evidence()])
        assert any("T1" in item for item in result), status


def test_successor_must_be_complete_and_cover_same_criterion():
    for variant in ("pending", "no_criteria", "supporting"):
        state = mission()
        target = state["tasks"][2]
        if variant == "pending":
            target["status"] = "pending"
        elif variant == "no_criteria":
            target["acceptance_evidence"] = []
        else:
            target["role"] = "supporting"
        assert any("T1" in x for x in _mission_completion_findings(state, [evidence()])), variant


def test_superseded_requires_one_unambiguous_positive_successor():
    state = mission()
    state["tasks"].append({**copy.deepcopy(state["tasks"][2]), "id": "T3"})
    assert _mission_completion_findings(state, [evidence()]) == []
    both = [evidence(), evidence(task="T3", event_id="E-2")]
    assert any("T1" in x for x in _mission_completion_findings(state, both))


def test_newer_failure_invalidates_successor_acceptance():
    event1 = evidence()
    event2 = evidence(kind="acceptance_failed", event_id="E-2")
    result = _mission_completion_findings(mission(), [event1, event2])
    assert any("T1" in x for x in result)
    assert any("AC_GOAL" in x for x in result)


def test_acceptance_by_original_superseded_task_is_not_substitute():
    result = _mission_completion_findings(mission(), [evidence(task="T1")])
    assert any("T1" in x for x in result)
