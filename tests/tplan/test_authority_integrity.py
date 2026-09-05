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


def added_node(node_id="T3", *, status="pending", parent=None):
    value = {"id": node_id, "title": node_id, "status": status, "role": "supporting"}
    if parent is None:
        value.update(kind="task", mission_contribution="Supports existing work.", acceptance_evidence=[])
    else:
        value.update(kind="subtask", parent_id=parent,
                     parent_contribution="Supports the selected parent.",
                     parent_acceptance="Parent receives the result.", mission_trace="via parent")
    return value


def guarded_apply(root, proposed):
    """Prepare a genuinely bound receipt; return the final application operation."""
    guard = runtime.begin_interaction_guard(root, platform="test-host", message_ref="M1")
    runtime.resolve_interaction_guard(
        root, guard_id=guard["guard_id"], expected_revision=guard["revision"], message_refs=["M1"],
        disposition="await_clarification", proposal_id="P1", proposal_decision=proposed,
    )
    confirmed = runtime.begin_interaction_guard(root, platform="test-host", message_ref="M2")
    receipt = runtime.issue_authority_receipt(
        root, guard_id=confirmed["guard_id"], guard_revision=confirmed["revision"],
        proposal_id="P1", decision=proposed, confirmation_ref="M2", secret="test-only-secret",
    )
    return lambda: runtime.resolve_interaction_guard(
        root, guard_id=confirmed["guard_id"], expected_revision=confirmed["revision"],
        message_refs=["M2"], disposition="apply_authorized_change", decision=proposed,
        authority_receipt=receipt, receipt_secret="test-only-secret",
    )


class ContinuationConsequenceTests(AuthorityTestCase):
    def test_stop_and_review_ceiling_reject_execution_even_with_changed_recommendation(self):
        mutations = [
            {"type": "set_active_task", "task_id": "T1"},
            {"type": "transition_task", "task_id": "T1", "status": "active"},
            {"type": "transition_task", "task_id": "T1", "status": "pending"},
            {"type": "transition_task", "task_id": "T1", "status": "completed"},
            {"type": "set_mission_status", "status": "active"},
            {"type": "set_mission_status", "status": "completed"},
        ]
        for action in ("stop", "mission_review", "anti_spiral_audit"):
            for mutation in mutations:
                with self.subTest(action=action, mutation=mutation):
                    proposed = decision(recommendation="escalate", action=action, mutations=[mutation])
                    self.assertTrue(runtime.validate_hook_output(proposed))
                    self.assert_rejected_without_writes(
                        lambda: runtime.apply_decision(self.mission, proposed), "continuation.*consequence")

    def test_stop_cannot_authorize_continue_by_omitting_mutations(self):
        for recommendation in ("continue", "switch", "add"):
            with self.subTest(recommendation=recommendation):
                proposed = decision(recommendation=recommendation, action="stop")
                self.assert_rejected_without_writes(
                    lambda: runtime.apply_decision(self.mission, proposed), "continuation.*consequence")

    def test_consistent_continue_and_narrowing_dispositions_remain_usable(self):
        for action in ("continue_same_path", "targeted_fix", "batch_details"):
            with self.subTest(action=action):
                proposed = decision(recommendation="continue", action=action)
                proposed["path_assessment"]["marginal_roi"] = "weak"
                proposed["continuation_authorization"]["evidence_shape_lint"] = "fail"
                proposed["continuation_authorization"]["expected_evidence_delta"] = "unclear"
                self.assertEqual(runtime.apply_decision(self.mission, proposed), "applied_decision")
        proposed = decision(recommendation="escalate", action="stop", mutations=[
            {"type": "set_mission_status", "status": "requires_human"}])
        self.assertEqual(runtime.apply_decision(self.mission, proposed), "applied_decision")
        self.assertEqual(runtime.read_mission(self.mission)["mission"]["status"], "requires_human")

    def test_consistent_review_is_recordable_without_execution(self):
        for action in ("stop", "mission_review", "anti_spiral_audit"):
            with self.subTest(action=action):
                proposed = decision(recommendation="escalate", action=action)
                proposed["requires_human"] = True
                mission_before = runtime.mission_paths(self.mission)["mission"].read_bytes()
                self.assertEqual(runtime.apply_decision(self.mission, proposed), "recorded_recommendation")
                self.assertEqual(runtime.mission_paths(self.mission)["mission"].read_bytes(), mission_before)

    def test_real_guard_receipt_cannot_override_stop_contradiction(self):
        proposed = decision(recommendation="continue", action="stop", mutations=[
            {"type": "set_active_task", "task_id": "T1"}])
        apply = guarded_apply(self.mission, proposed)
        self.assert_rejected_without_writes(apply, "continuation.*consequence")
        self.assertIsNotNone(runtime.read_interaction_guard(self.mission))


class ActivePathAtomicityTests(AuthorityTestCase):
    def test_create_and_activate_updates_cursor_and_events_in_one_commit(self):
        runtime.transition_task_status(self.mission, "T1", "active")
        for node in (added_node("T3", status="active"), added_node("T3.1", status="active", parent="T3")):
            with self.subTest(node=node["id"]):
                runtime.add_task_node(self.mission, node)
                state = runtime.read_mission(self.mission)
                self.assertEqual(state["active_task_id"], node["id"])
                records = runtime.read_execution_trace(self.mission)
                added = next(r for r in records if r["event_type"] == "node_added" and r["task_id"] == node["id"])
                selected = next(r for r in records if r["event_type"] == "active_node_changed" and r["task_id"] == node["id"])
                self.assertEqual(added["commit_id"], selected["commit_id"])
                self.assertEqual(added["timestamp"], selected["timestamp"])
        self.assertEqual(runtime.find_task(state, "T3")["status"], "active")

    def test_pending_creation_preserves_selection_and_blocked_recovery_cursor(self):
        runtime.transition_task_status(self.mission, "T1", "active")
        runtime.add_task_node(self.mission, added_node())
        self.assertEqual(runtime.read_mission(self.mission)["active_task_id"], "T1")
        runtime.record_stop_report(self.mission, "T1", "Needs a decision.", {
            "current_goal": "Finish the Mission.", "attempts": ["Inspected evidence."],
            "blocking_issue": "Missing authority.", "why_cannot_continue_safely": "User decision is required.",
            "need_from_human": "Confirm the boundary.", "resume_condition": "Decision received.",
        })
        runtime.add_task_node(self.mission, added_node("T4"))
        state = runtime.read_mission(self.mission)
        self.assertEqual(state["active_task_id"], "T1")
        self.assertEqual(runtime.find_task(state, "T1")["status"], "blocked")

    def test_failed_create_and_activate_has_no_orphan_or_partial_cursor(self):
        before = snapshot(self.mission)
        with mock.patch.object(runtime, "write_json", side_effect=OSError("journal unavailable")):
            with self.assertRaisesRegex(OSError, "journal unavailable"):
                runtime.add_task_node(self.mission, added_node(status="active"))
        self.assertEqual(snapshot(self.mission), before)


def complete_tasks(root):
    for task_id in ("T1", "T2"):
        runtime.transition_task_status(root, task_id, "completed")


def pass_requirements(root):
    for task_id, acceptance_id in (("T1", "A1"), ("T2", "A2")):
        event(root, event_id="E-" + acceptance_id, event_type="acceptance_passed",
              task_id=task_id, payload={"acceptance_ids": [acceptance_id]})


def close_decision():
    return decision(recommendation="close", mutations=[{"type": "set_mission_status", "status": "completed"}])


class MissionCompletionIntegrityTests(AuthorityTestCase):
    def test_every_success_critical_status_other_than_completed_blocks_closure(self):
        for status in sorted(runtime.TASK_STATUSES - {"completed"}):
            with self.subTest(status=status):
                self.mission = create_mission(self.root / f"critical-{status}")
                pass_requirements(self.mission)
                before = runtime.read_mission(self.mission)
                after = copy.deepcopy(before)
                for task in after["tasks"]:
                    task["status"] = "completed"
                after["tasks"][0]["status"] = status
                after["mission"]["status"] = "completed"
                self.assert_rejected_without_writes(
                    lambda: runtime.commit_mission_state(
                        self.mission, before, after, source={"kind": "test", "name": "closure"}),
                    "Mission completion.*success-critical")

    def test_missing_acceptance_blocks_close_without_blocking_task_completion(self):
        complete_tasks(self.mission)
        self.assert_rejected_without_writes(
            lambda: runtime.apply_decision(self.mission, close_decision()), "Mission completion.*acceptance")
        self.assertTrue(all(t["status"] == "completed" for t in runtime.read_mission(self.mission)["tasks"]))

    def test_stream_order_controls_latest_qualified_acceptance(self):
        cases = [
            (("acceptance_passed", "acceptance_failed"), False),
            (("acceptance_failed", "acceptance_passed"), True),
            (("acceptance",), True),
        ]
        for i, (history, allowed) in enumerate(cases):
            with self.subTest(history=history):
                self.mission = create_mission(self.root / f"history-{i}")
                complete_tasks(self.mission)
                event(self.mission, event_id="E-A2", task_id="T2", event_type="acceptance_passed",
                      payload={"acceptance_ids": ["A2"]})
                for index, kind in enumerate(history):
                    runtime.append_event(self.mission, {
                        "id": f"E-{index}", "timestamp": f"2026-09-0{5-index}T12:00:00Z",
                        "event_type": kind, "task_id": "T1", "summary": "Observed acceptance.",
                        "payload": {"acceptance_ids": ["A1"]},
                    })
                if allowed:
                    self.assertEqual(runtime.apply_decision(self.mission, close_decision()), "applied_decision")
                    self.assertEqual(runtime.read_mission(self.mission)["mission"]["status"], "completed")
                else:
                    self.assert_rejected_without_writes(
                        lambda: runtime.apply_decision(self.mission, close_decision()), "Mission completion.*acceptance")

    def test_wrong_scope_incomplete_and_duplicate_acceptance_cannot_qualify(self):
        for variant in ("wrong_scope", "incomplete_legacy", "duplicate", "key_finding"):
            with self.subTest(variant=variant):
                self.mission = create_mission(self.root / variant)
                complete_tasks(self.mission)
                event(self.mission, event_id="E-A2", task_id="T2", event_type="acceptance_passed",
                      payload={"acceptance_ids": ["A2"]})
                raw = {"id": "E-A1", "timestamp": "2026-09-05T12:00:00Z", "summary": "Historical observation.",
                       "event_type": "acceptance_passed", "task_id": "T1", "payload": {"acceptance_ids": ["A1"]}}
                if variant == "wrong_scope":
                    raw["task_id"] = "T2"
                elif variant == "incomplete_legacy":
                    raw.update(event_type="acceptance", payload={})
                elif variant == "key_finding":
                    raw["event_type"] = "key_finding"
                path = runtime.mission_paths(self.mission)["evidence"]
                with path.open("a", encoding="utf-8") as stream:
                    stream.write((json.dumps(raw) + "\n") * (2 if variant == "duplicate" else 1))
                self.assert_rejected_without_writes(
                    lambda: runtime.apply_decision(self.mission, close_decision()), "Mission completion.*acceptance")

    def test_same_transaction_can_complete_tasks_and_supply_acceptance(self):
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        prepared = []
        for task_id, acceptance_id in (("T1", "A1"), ("T2", "A2")):
            runtime.set_task_status(after, task_id, "completed")
            prepared.append(runtime.prepare_event(self.mission, {
                "id": "E-" + acceptance_id, "event_type": "acceptance_passed", "task_id": task_id,
                "summary": "Reviewed acceptance.", "payload": {"acceptance_ids": [acceptance_id]},
            }))
        after["mission"]["status"] = "completed"
        runtime.commit_mission_state(
            self.mission, before, after, source={"kind": "test", "name": "atomic_closure"},
            refs={"evidence_ids": [e["id"] for e in prepared]}, prepared_evidence_events=prepared)
        self.assertEqual(runtime.read_mission(self.mission)["mission"]["status"], "completed")

    def test_adverse_evidence_arriving_after_candidate_build_blocks_close(self):
        complete_tasks(self.mission)
        pass_requirements(self.mission)
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        after["mission"]["status"] = "completed"
        event(self.mission, event_id="E-late-fail", event_type="acceptance_failed", payload={"acceptance_ids": ["A1"]})
        self.assert_rejected_without_writes(
            lambda: runtime.commit_mission_state(self.mission, before, after, source={"kind": "test", "name": "late"}),
            "Mission completion.*acceptance")

    def test_unfinished_supporting_work_is_not_a_mission_approval_gate(self):
        runtime.add_task_node(self.mission, added_node())
        complete_tasks(self.mission)
        pass_requirements(self.mission)
        runtime.apply_decision(self.mission, close_decision())
        state = runtime.read_mission(self.mission)
        self.assertEqual(state["mission"]["status"], "completed")
        self.assertEqual(runtime.find_task(state, "T3")["status"], "pending")

    def test_guarded_closure_uses_the_same_completion_boundary(self):
        apply = guarded_apply(self.mission, close_decision())
        self.assert_rejected_without_writes(apply, "Mission completion")
        self.assertIsNotNone(runtime.read_interaction_guard(self.mission))

    def test_advisory_closure_remains_a_recommendation(self):
        proposed = close_decision()
        proposed["requires_human"] = True
        before = runtime.mission_paths(self.mission)["mission"].read_bytes()
        self.assertEqual(runtime.apply_decision(self.mission, proposed), "recorded_recommendation")
        self.assertEqual(runtime.mission_paths(self.mission)["mission"].read_bytes(), before)

    def test_historical_completed_state_remains_readable_without_retroactive_acceptance(self):
        path = runtime.mission_paths(self.mission)["mission"]
        state = runtime.read_mission(self.mission)
        state["mission"]["status"] = "completed"
        path.write_text(json.dumps(state), encoding="utf-8")
        historic = path.read_bytes()
        self.assertEqual(runtime.read_mission(self.mission)["mission"]["status"], "completed")
        event(self.mission, event_id="E-history-note")
        self.assertEqual(path.read_bytes(), historic)


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
