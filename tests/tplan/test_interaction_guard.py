import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"

import sys

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tplan_runtime


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    mission = tplan_runtime.build_mission(
        mission_id="interaction-guard",
        title="Interaction Guard Mission",
        objective="Keep Plan state stable across user interruptions.",
        acceptance_evidence=[{"id": "A1", "description": "Guard behavior is verified."}],
        human_in_loop=0,
        risk_tolerance=50,
        resource_sufficiency=50,
        tasks=[
            {
                "id": "T1",
                "title": "Protect the active path",
                "role": "success-critical",
                "mission_contribution": "Protects TPlan runtime state.",
                "acceptance_evidence": ["A1"],
            },
            {
                "id": "T2",
                "title": "Apply reviewed change",
                "role": "success-critical",
                "mission_contribution": "Applies authorized runtime changes.",
                "acceptance_evidence": ["A1"],
            },
        ],
    )
    mission_dir.mkdir()
    tplan_runtime.write_mission(mission_dir, mission)
    tplan_runtime.initialize_execution_trace(mission_dir, mission)
    tplan_runtime.transition_task_status(mission_dir, "T1", "active")
    return mission_dir


def decision_to_t2():
    return {
        "recommendation": "switch",
        "rationale": "The reviewed change selects T2.",
        "confidence": 90,
        "evidence_links": [],
        "proposed_mutations": [{"type": "set_active_task", "task_id": "T2"}],
        "requires_human": False,
        "mission_alignment": "T2 is the approved next Mission path.",
        "path_assessment": {
            "marginal_roi": "positive",
            "path_role": "dominant_path",
            "evidence_delta": "new_evidence_expected",
        },
    }


class InteractionGuardTests(unittest.TestCase):
    def test_guard_blocks_trace_and_log_artifact_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            tplan_runtime.append_step_log(mission_dir, {"task_id": "T1", "summary": "before guard"})
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            with self.assertRaisesRegex(tplan_runtime.TplanError, "append_step_log"):
                tplan_runtime.append_step_log(mission_dir, {"task_id": "T1", "summary": "must remain blocked"})
            with self.assertRaisesRegex(tplan_runtime.TplanError, "append_execution_trace_record"):
                tplan_runtime.start_execution_span(
                    mission_dir,
                    {
                        "task_id": "T1",
                        "span": {
                            "kind": "tool",
                            "label": "blocked guarded telemetry",
                            "measurement_source": "host_measured",
                            "attribution": "exact",
                        },
                    },
                )
            with self.assertRaisesRegex(tplan_runtime.TplanError, "archive_task_logs"):
                tplan_runtime.archive_task_logs(mission_dir, "T1", "must remain blocked")
            self.assertEqual(tplan_runtime.read_interaction_guard(mission_dir)["guard_id"], guard["guard_id"])

    def test_expired_or_legacy_guard_never_auto_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            guard = tplan_runtime.begin_interaction_guard(
                mission_dir, platform="codex-desktop", binding_id="S1", message_ref="M1"
            )
            expired = dict(guard)
            expired["lease"] = dict(guard["lease"])
            expired["lease"]["deadline_at"] = "2000-01-01T00:00:00+00:00"
            tplan_runtime._write_interaction_guard_unlocked(mission_dir, expired)
            orphaned = tplan_runtime.orphan_expired_interaction_guard(mission_dir)
            self.assertEqual(orphaned["phase"], "orphaned")
            self.assertEqual(orphaned["recovery"]["reason"], "lease_expired")
            self.assertEqual(
                tplan_runtime.resolve_guard_at_turn_end(mission_dir, platform="codex-desktop", binding_id="S1")["disposition"],
                "pending_recovery",
            )

            legacy = dict(guard)
            legacy["schema_version"] = tplan_runtime.LEGACY_INTERACTION_GUARD_SCHEMA_VERSION
            legacy["phase"] = "open"
            legacy.pop("platform_profile_id")
            legacy.pop("lease")
            legacy.pop("recovery")
            tplan_runtime.write_json(tplan_runtime.interaction_guard_path(mission_dir), legacy, durable=True)
            self.assertEqual(tplan_runtime.read_interaction_guard(mission_dir)["phase"], "orphaned")
            self.assertEqual(
                tplan_runtime.resolve_guard_at_turn_end(mission_dir, platform="codex-desktop", binding_id="S1")["disposition"],
                "pending_recovery",
            )

    def test_first_turn_end_resolves_all_pending_messages_without_continuation(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            first = tplan_runtime.begin_interaction_guard(
                mission_dir,
                platform="codex-desktop",
                platform_profile_id="codex-desktop@test",
                binding_id="S1",
                message_ref="M1",
                owner_turn_id="turn-2",
            )
            current = tplan_runtime.begin_interaction_guard(
                mission_dir,
                platform="codex-desktop",
                platform_profile_id="codex-desktop@test",
                binding_id="S1",
                message_ref="M2",
                owner_turn_id="turn-2",
            )
            self.assertGreater(current["revision"], first["revision"])
            result = tplan_runtime.resolve_guard_at_turn_end(
                mission_dir,
                platform="codex-desktop",
                binding_id="S1",
            )
            self.assertEqual(result["disposition"], "resume_original")
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))

    def test_orphaned_guard_keeps_writers_closed_but_operator_resume_is_recoverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            orphaned = tplan_runtime.orphan_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                reason="turn_end_resolution_failed",
            )
            self.assertEqual(orphaned["phase"], "orphaned")
            with self.assertRaisesRegex(tplan_runtime.TplanError, "interaction guard is open"):
                tplan_runtime.transition_task_status(mission_dir, "T2", "active")
            result = tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=orphaned["guard_id"],
                expected_revision=orphaned["revision"],
                message_refs=["M1"],
                disposition="resume_original",
            )
            self.assertEqual(result["resumed_task_id"], "T1")
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))

    def test_guard_blocks_supported_state_and_evidence_writers_then_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = tplan_runtime.read_mission(mission_dir)
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")

            with self.assertRaisesRegex(tplan_runtime.TplanError, "interaction guard is open"):
                tplan_runtime.transition_task_status(mission_dir, "T2", "active")
            with self.assertRaisesRegex(tplan_runtime.TplanError, "interaction guard is open"):
                tplan_runtime.add_task_node(
                    mission_dir,
                    {
                        "id": "T3",
                        "title": "Unauthorized node",
                        "role": "supporting",
                        "mission_contribution": "Must not be added.",
                        "acceptance_evidence": [],
                    },
                )
            with self.assertRaisesRegex(tplan_runtime.TplanError, "interaction guard is open"):
                tplan_runtime.append_event(
                    mission_dir,
                    {"event_type": "user_feedback", "summary": "A status inquiry is not feedback."},
                )
            with self.assertRaisesRegex(tplan_runtime.TplanError, "interaction guard is open"):
                tplan_runtime.record_risk_signal(
                    mission_dir,
                    "T1",
                    {
                        "scope": "shared_environment",
                        "signal": "unauthorized-route",
                        "severity": "high",
                        "confidence": "high",
                        "affected_surfaces": ["runtime"],
                        "value_effect": "Would alter route.",
                        "recommended_gate": "review",
                        "recovery_condition": "Do not write during guard.",
                    },
                )
            changed = tplan_runtime.read_mission(mission_dir)
            changed["active_task_id"] = "T2"
            with self.assertRaisesRegex(tplan_runtime.TplanError, "write_mission cannot bypass"):
                tplan_runtime.write_mission(mission_dir, changed)
            with self.assertRaises(TypeError):
                tplan_runtime.commit_mission_state(
                    mission_dir,
                    before,
                    changed,
                    source={"kind": "test", "name": "unauthorized_guard_close"},
                    guard_after=None,
                )

            self.assertEqual(tplan_runtime.read_mission(mission_dir), before)
            self.assertEqual(tplan_runtime.read_events(mission_dir), [])
            result = tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                message_refs=["M1"],
                disposition="resume_original",
            )
            self.assertEqual(result["resumed_task_id"], "T1")
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))

    def test_nested_message_stale_resolve_cannot_close_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            first = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            second = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M2")
            self.assertEqual(second["revision"], first["revision"] + 1)
            with self.assertRaisesRegex(tplan_runtime.TplanError, "stale"):
                tplan_runtime.resolve_interaction_guard(
                    mission_dir,
                    guard_id=first["guard_id"],
                    expected_revision=first["revision"],
                    message_refs=["M1"],
                    disposition="resume_original",
                )
            awaiting = tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=second["guard_id"],
                expected_revision=second["revision"],
                message_refs=["M1"],
                disposition="await_clarification",
            )
            self.assertEqual(awaiting["pending_messages"], ["M2"])
            self.assertTrue(tplan_runtime.interaction_guard_path(mission_dir).exists())

    def test_receipt_binds_exact_mutation_and_cannot_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            first = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            decision = decision_to_t2()
            awaiting = tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=first["guard_id"],
                expected_revision=first["revision"],
                message_refs=["M1"],
                disposition="await_clarification",
                proposal_id="P1",
                proposal_decision=decision,
            )
            with self.assertRaisesRegex(tplan_runtime.TplanError, "pending confirmation message"):
                tplan_runtime.issue_authority_receipt(
                    mission_dir,
                    guard_id=awaiting["guard_id"],
                    guard_revision=awaiting["revision"],
                    proposal_id="P1",
                    decision=decision,
                    confirmation_ref="M1",
                    secret="host-secret",
                )
            confirmation = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M2")
            receipt = tplan_runtime.issue_authority_receipt(
                mission_dir,
                guard_id=confirmation["guard_id"],
                guard_revision=confirmation["revision"],
                proposal_id="P1",
                decision=decision,
                confirmation_ref="M2",
                secret="host-secret",
            )
            tampered_decision = {**decision, "rationale": "Different prose was not what the user confirmed."}
            with self.assertRaisesRegex(tplan_runtime.TplanError, "decision mismatch"):
                tplan_runtime.resolve_interaction_guard(
                    mission_dir,
                    guard_id=confirmation["guard_id"],
                    expected_revision=confirmation["revision"],
                    message_refs=["M2"],
                    disposition="apply_authorized_change",
                    decision=tampered_decision,
                    authority_receipt=receipt,
                    receipt_secret="host-secret",
                )
            result = tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=confirmation["guard_id"],
                expected_revision=confirmation["revision"],
                message_refs=["M2"],
                disposition="apply_authorized_change",
                decision=decision,
                authority_receipt=receipt,
                receipt_secret="host-secret",
            )
            self.assertEqual(result["receipt_id"], receipt["receipt_id"])
            self.assertEqual(tplan_runtime.read_mission(mission_dir)["active_task_id"], "T2")
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))

            replay_guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M3")
            with self.assertRaisesRegex(tplan_runtime.TplanError, "guard identity or revision mismatch"):
                tplan_runtime.resolve_interaction_guard(
                    mission_dir,
                    guard_id=replay_guard["guard_id"],
                    expected_revision=replay_guard["revision"],
                    message_refs=["M3"],
                    disposition="apply_authorized_change",
                    decision=decision,
                    authority_receipt=receipt,
                    receipt_secret="host-secret",
                )

    def test_receipt_rejects_a_pending_message_that_arrived_before_the_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            first = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            second = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M2")
            decision = decision_to_t2()
            awaiting = tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=second["guard_id"],
                expected_revision=second["revision"],
                message_refs=["M1"],
                disposition="await_clarification",
                proposal_id="P1",
                proposal_decision=decision,
            )
            current = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M3")
            self.assertGreater(current["revision"], awaiting["revision"])
            with self.assertRaisesRegex(tplan_runtime.TplanError, "received after the proposal"):
                tplan_runtime.issue_authority_receipt(
                    mission_dir,
                    guard_id=current["guard_id"],
                    guard_revision=current["revision"],
                    proposal_id="P1",
                    decision=decision,
                    confirmation_ref="M2",
                    secret="host-secret",
                )

    def test_resume_recovery_keeps_guard_fail_closed_until_transaction_rolls_forward(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            original_write_guard = tplan_runtime._write_interaction_guard_unlocked

            def fail_guard_close(path, value):
                if value is None:
                    raise OSError("simulated guard close interruption")
                return original_write_guard(path, value)

            with mock.patch.object(tplan_runtime, "_write_interaction_guard_unlocked", side_effect=fail_guard_close):
                with self.assertRaisesRegex(OSError, "simulated guard close interruption"):
                    tplan_runtime.resolve_interaction_guard(
                        mission_dir,
                        guard_id=guard["guard_id"],
                        expected_revision=guard["revision"],
                        message_refs=["M1"],
                        disposition="resume_original",
                    )

            self.assertTrue(tplan_runtime.interaction_guard_path(mission_dir).exists())
            tplan_runtime.read_mission(mission_dir)
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))

    def test_authorized_change_recovery_rolls_mission_evidence_and_guard_forward_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            first = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            decision = decision_to_t2()
            awaiting = tplan_runtime.resolve_interaction_guard(
                mission_dir,
                guard_id=first["guard_id"],
                expected_revision=first["revision"],
                message_refs=["M1"],
                disposition="await_clarification",
                proposal_id="P1",
                proposal_decision=decision,
            )
            confirmation = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M2")
            receipt = tplan_runtime.issue_authority_receipt(
                mission_dir,
                guard_id=confirmation["guard_id"],
                guard_revision=confirmation["revision"],
                proposal_id="P1",
                decision=decision,
                confirmation_ref="M2",
                secret="host-secret",
            )
            original_write_guard = tplan_runtime._write_interaction_guard_unlocked

            def fail_guard_close(path, value):
                if value is None:
                    raise OSError("simulated guard close interruption")
                return original_write_guard(path, value)

            with mock.patch.object(tplan_runtime, "_write_interaction_guard_unlocked", side_effect=fail_guard_close):
                with self.assertRaisesRegex(OSError, "simulated guard close interruption"):
                    tplan_runtime.resolve_interaction_guard(
                        mission_dir,
                        guard_id=awaiting["guard_id"],
                        expected_revision=confirmation["revision"],
                        message_refs=["M2"],
                        disposition="apply_authorized_change",
                        decision=decision,
                        authority_receipt=receipt,
                        receipt_secret="host-secret",
                    )

            self.assertTrue(tplan_runtime.interaction_guard_path(mission_dir).exists())
            recovered = tplan_runtime.read_mission(mission_dir)
            self.assertEqual(recovered["active_task_id"], "T2")
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            events = tplan_runtime.read_events(mission_dir)
            self.assertEqual([event["event_type"] for event in events], ["decision_applied"])

    def test_stop_recovery_rolls_mission_evidence_and_guard_forward_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            payload = {
                "current_goal": "Preserve user authority.",
                "attempts": ["Opened an interaction guard."],
                "blocking_issue": "Need a user decision.",
                "why_cannot_continue_safely": "Changing paths would invent authority.",
                "need_from_human": "Confirm the next path.",
                "resume_condition": "A confirmed decision is received.",
            }
            original_write_guard = tplan_runtime._write_interaction_guard_unlocked

            def fail_guard_close(path, value):
                if value is None:
                    raise OSError("simulated guard close interruption")
                return original_write_guard(path, value)

            with mock.patch.object(tplan_runtime, "_write_interaction_guard_unlocked", side_effect=fail_guard_close):
                with self.assertRaisesRegex(OSError, "simulated guard close interruption"):
                    tplan_runtime.stop_interaction_guard(
                        mission_dir,
                        guard_id=guard["guard_id"],
                        expected_revision=guard["revision"],
                        message_refs=["M1"],
                        task_id="T1",
                        summary="Stop safely.",
                        payload=payload,
                    )

            self.assertTrue(tplan_runtime.interaction_guard_path(mission_dir).exists())
            recovered = tplan_runtime.read_mission(mission_dir)
            self.assertEqual(recovered["mission"]["status"], "requires_human")
            self.assertIsNone(tplan_runtime.read_interaction_guard(mission_dir))
            events = tplan_runtime.read_events(mission_dir)
            self.assertEqual([event["event_type"] for event in events], ["stop_report"])

    def test_stop_can_only_block_the_baseline_active_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            guard = tplan_runtime.begin_interaction_guard(mission_dir, platform="test-host", message_ref="M1")
            payload = {
                "current_goal": "Preserve user authority.",
                "attempts": ["Opened an interaction guard."],
                "blocking_issue": "Need a user decision.",
                "why_cannot_continue_safely": "Changing paths would invent authority.",
                "need_from_human": "Confirm the next path.",
                "resume_condition": "A confirmed decision is received.",
            }
            with self.assertRaisesRegex(tplan_runtime.TplanError, "baseline active task"):
                tplan_runtime.stop_interaction_guard(
                    mission_dir,
                    guard_id=guard["guard_id"],
                    expected_revision=guard["revision"],
                    message_refs=["M1"],
                    task_id="T2",
                    summary="Stop safely.",
                    payload=payload,
                )
            result = tplan_runtime.stop_interaction_guard(
                mission_dir,
                guard_id=guard["guard_id"],
                expected_revision=guard["revision"],
                message_refs=["M1"],
                task_id="T1",
                summary="Stop safely.",
                payload=payload,
            )
            self.assertEqual(result["task_id"], "T1")
            mission = tplan_runtime.read_mission(mission_dir)
            self.assertEqual(mission["mission"]["status"], "requires_human")
            self.assertEqual(mission["active_task_id"], "T1")
