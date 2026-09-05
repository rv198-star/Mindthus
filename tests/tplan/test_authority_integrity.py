"""Cross-entry regressions for #196-#199; assertions cover effects, not field presence."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tplan_runtime as runtime


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def create_mission(root, *, human_in_loop=0):
    root.mkdir(parents=True)
    mission = runtime.build_mission(
        mission_id=root.name,
        title="Authority integrity",
        objective="Keep declared authority and committed consequences consistent.",
        acceptance_evidence=[
            {"id": "A1", "description": "First requirement is met."},
            {"id": "A2", "description": "Second requirement is met."},
        ],
        human_in_loop=human_in_loop, risk_tolerance=50, resource_sufficiency=50,
        tasks=[
            {"id": task_id, "title": task_id, "role": "success-critical",
             "mission_contribution": "Satisfies the declared requirement.",
             "acceptance_evidence": [acceptance_id]}
            for task_id, acceptance_id in (("T1", "A1"), ("T2", "A2"))
        ],
    )
    runtime.write_mission(root, mission)
    runtime.initialize_execution_trace(root, mission)
    return root


def event(root, *, event_id="E-valid", event_type="key_finding", task_id="T1", payload=None):
    return runtime.append_event(root, {
        "id": event_id, "event_type": event_type, "summary": "An observed result.",
        "task_id": task_id, "payload": {} if payload is None else payload,
    })


def decision(*, recommendation="switch", mutations=None, action=None):
    value = {
        "recommendation": recommendation, "rationale": "Apply the reviewed disposition.",
        "confidence": 80, "evidence_links": [], "requires_human": False,
        "mission_alignment": "The requested state matches the declared Mission boundary.",
        "path_assessment": {"marginal_roi": "positive", "path_role": "dominant_path",
                            "evidence_delta": "new_evidence_expected"},
        "proposed_mutations": [] if mutations is None else mutations,
    }
    if action is not None:
        value["continuation_authorization"] = {
            "trigger_reasons": ["manual_authorization"], "evidence_shape_lint": "pass",
            "defect_classification": "none", "expected_evidence_delta": "new_evidence_expected",
            "authorized_action": action,
        }
    return value


class AuthorityTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mission = create_mission(self.root / "mission")

    def assert_rejected_without_writes(self, operation, pattern):
        before = snapshot(self.mission)
        with self.assertRaisesRegex(runtime.TplanError, pattern):
            operation()
        self.assertEqual(snapshot(self.mission), before)


class EvidenceReferenceIntegrityTests(AuthorityTestCase):
    def test_missing_path_and_cross_mission_ids_are_rejected_atomically(self):
        other = create_mission(self.root / "other")
        event(other, event_id="E-other")
        artifact = self.mission / "result.txt"
        artifact.write_text("real artifact", encoding="utf-8")
        for ref in ("EPLACEHOLDER", str(artifact), "E-other"):
            with self.subTest(ref=ref):
                self.assert_rejected_without_writes(
                    lambda: runtime.transition_task_status(
                        self.mission, "T1", "completed", evidence_refs=[ref]),
                    "evidence.*reference",
                )

    def test_existing_and_same_transaction_evidence_are_resolvable(self):
        existing = event(self.mission)
        runtime.transition_task_status(self.mission, "T1", "completed", evidence_refs=[existing["id"]])
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        runtime.set_task_status(after, "T2", "active")
        prepared = runtime.prepare_event(self.mission, {
            "id": "E-prepared", "event_type": "key_finding", "summary": "Atomic evidence.",
            "task_id": "T2", "payload": {},
        })
        runtime.commit_mission_state(
            self.mission, before, after, source={"kind": "test", "name": "prepared"},
            refs={"evidence_ids": [existing["id"], prepared["id"]]},
            prepared_evidence_events=[prepared],
        )
        self.assertEqual(runtime.read_mission(self.mission)["active_task_id"], "T2")
        self.assertEqual(sum(e["id"] == "E-prepared" for e in runtime.read_events(self.mission)), 1)
        # Correctly typed artifact references need no fabricated evidence event.
        runtime.transition_task_status(self.mission, "T2", "completed", artifact_refs=["result.txt"])

    def test_ambiguous_historical_id_blocks_only_new_uses_of_that_id(self):
        entry = event(self.mission)
        path = runtime.mission_paths(self.mission)["evidence"]
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry) + "\n")
        history = path.read_bytes()
        self.assert_rejected_without_writes(
            lambda: runtime.transition_task_status(self.mission, "T1", "completed", evidence_refs=[entry["id"]]),
            "evidence.*reference",
        )
        unique = event(self.mission, event_id="E-unique")
        runtime.transition_task_status(self.mission, "T2", "active", evidence_refs=[unique["id"]])
        self.assertTrue(path.read_bytes().startswith(history))
        self.assertEqual(runtime.read_mission(self.mission)["active_task_id"], "T2")

    def test_reference_rejection_discards_prepared_evidence_before_journal(self):
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        runtime.set_task_status(after, "T1", "active")
        prepared = runtime.prepare_event(self.mission, {
            "id": "E-uncommitted", "event_type": "key_finding", "summary": "Candidate only.",
            "task_id": "T1", "payload": {},
        })
        self.assert_rejected_without_writes(
            lambda: runtime.commit_mission_state(
                self.mission, before, after, source={"kind": "test", "name": "invalid_ref"},
                refs={"evidence_ids": [prepared["id"], "E-missing"]}, prepared_evidence_events=[prepared]),
            "evidence.*reference",
        )

    def test_extra_lifecycle_records_cannot_bypass_reference_resolution(self):
        before = runtime.read_mission(self.mission)
        extra = runtime._new_trace_record(
            before, "active_node_changed", task_id="T1",
            payload={"from_task_id": None, "to_task_id": "T1"},
            refs={"evidence_ids": ["E-missing"]},
            source={"kind": "test", "name": "extra"}, commit_id="C-extra",
        )
        with runtime.execution_trace_lock(self.mission):
            self.assert_rejected_without_writes(
                lambda: runtime._commit_mission_state_unlocked(
                    self.mission, before, before, source={"kind": "test", "name": "extra"},
                    extra_trace_records=[extra]), "evidence.*reference")
