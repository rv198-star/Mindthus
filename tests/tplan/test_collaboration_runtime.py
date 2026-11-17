"""Integration tests for the optional A-side collaboration transaction."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import collaboration
import collaboration_runtime
import tplan_runtime as runtime


class CollaborationRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tplan-collaboration-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mission = self.create_mission()
        self.principal = "coordinator-a"
        self.counter = 0

    def script(self, name, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / name), *args],
            text=True,
            capture_output=True,
            timeout=20,
        )

    def create_mission(self):
        directory = self.root / "collaboration-mission"
        tasks = self.root / "tasks.json"
        tasks.write_text(json.dumps([
            {"id": "T1", "title": "Implement the result", "role": "success-critical",
             "mission_contribution": "Delivers A1", "acceptance_evidence": ["A1"], "status": "active"},
            {"id": "T2", "title": "Protect the mainline", "role": "supporting",
             "mission_contribution": "Maintains acceptance coherence", "acceptance_evidence": []},
        ]), encoding="utf-8")
        result = self.script(
            "init_mission.py", "--dir", str(directory), "--mission-id", "collaboration-mission",
            "--title", "Collaboration mission", "--objective", "Deliver a verified collaboration runtime",
            "--acceptance-evidence", "A1:Verified collaboration runtime", "--task-json", str(tasks),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads((directory / "mission.json").read_text(encoding="utf-8"))
        state["active_task_id"] = "T1"
        (directory / "mission.json").write_text(json.dumps(state), encoding="utf-8")
        return directory

    def snapshot(self):
        response, code = collaboration_runtime.execute(
            self.mission,
            {
                "protocol": collaboration.PROTOCOL,
                "action": "snapshot.get",
                "mission_id": "collaboration-mission",
                "command_id": "snapshot-read",
                "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
                "expected_snapshot": None,
                "payload": {},
            },
            principal=self.principal,
        )
        self.assertEqual(code, 0, response)
        return response

    def mutate(self, action, payload, command_id=None, expected_snapshot="current"):
        self.counter += 1
        if expected_snapshot == "current":
            expected_snapshot = self.snapshot()["data"]["expected_snapshot"]
        request = {
            "protocol": collaboration.PROTOCOL,
            "action": action,
            "mission_id": "collaboration-mission",
            "command_id": command_id or f"command-{self.counter}",
            "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
            "expected_snapshot": expected_snapshot,
            "payload": payload,
        }
        return collaboration_runtime.execute(self.mission, request, principal=self.principal)

    def enable(self):
        response, code = self.mutate("enable", {
            "coordinator": {
                "thread_ref": "thread-a", "host_ref": "local",
                "responsibility": "Own the user objective, scope, and acceptance",
                "communication_authorization_refs": ["user-turn-1"],
            },
            "participants": [
                {"participant_id": "B", "thread_ref": "thread-b", "host_ref": "local",
                 "responsibility": "Implement and report bounded work",
                 "communication_authorization_refs": ["user-turn-1"]},
                {"participant_id": "C", "thread_ref": "thread-c", "host_ref": "local",
                 "responsibility": "Review current artifacts",
                 "communication_authorization_refs": ["user-turn-1"]},
            ],
            "policy": {"max_pending_feedback": 128, "processing_deadline_seconds": 900},
        })
        self.assertEqual(code, 0, response)
        return response

    def delegation_payload(self, task_id="T1", delegation_id="D1", intent_id="I1", round_no=1):
        return {
            "coordinator_generation": 1,
            "delegation_id": delegation_id,
            "intent_id": intent_id,
            "task_id": task_id,
            "round": round_no,
            "assignee_id": "B",
            "write_scope": f"workspace/{task_id}",
            "contract_version": f"contract-r{round_no}",
            "instruction_summary": f"Complete bounded work for {task_id}",
            "input_refs": [f"artifact://{task_id}/input"],
            "dependency_versions": {"design": f"v{round_no}"},
            "required_review": {"required": True, "reviewer_id": "C", "scope_refs": [f"scope://{task_id}"]},
        }

    def prepare(self, **kwargs):
        response, code = self.mutate("delegation.prepare", self.delegation_payload(**kwargs))
        self.assertEqual(code, 0, response)
        return response

    def dispatch(self, intent_id="I1", send_state="confirmed", execution_state="running", stop_requested=False):
        response, code = self.mutate("dispatch.record", {
            "coordinator_generation": 1,
            "intent_id": intent_id,
            "send_state": send_state,
            "execution_state": execution_state,
            "stop_requested": stop_requested,
            "native_refs": [f"thread://b/message/{intent_id}"] if send_state == "confirmed" else [],
            "observed_at": "2026-11-17T01:00:00+00:00",
            "reason": "Observed host dispatch fact",
        })
        self.assertEqual(code, 0, response)
        return response

    def feedback(self, source="msg-1", delegation_id="D1", artifact="h1", summary="Result ready", assert_ok=True, source_role="B", kind="result", round_no=1):
        digest = collaboration.digest({"source": source, "summary": summary})
        response, code = self.mutate("feedback.record", {
            "coordinator_generation": 1,
            "kind": kind,
            "source_event_ref": source,
            "source_thread_ref": ("thread-c" if source_role == "C" else "thread-b") if delegation_id else "thread-unknown",
            "source_host_ref": "local",
            "source_role_id": source_role if delegation_id else None,
            "delegation_id": delegation_id,
            "round": round_no if delegation_id else None,
            "contract_version": f"contract-r{round_no}" if delegation_id else None,
            "artifact_ref": f"artifact://{artifact}" if artifact else None,
            "artifact_digest": collaboration.digest({"artifact": artifact}) if artifact else None,
            "summary": summary,
            "original_ref": f"thread://source/{source}",
            "attachment_refs": [],
        })
        if assert_ok:
            self.assertEqual(code, 0, response)
        return response

    def coordination(self, focus="T2", state="working", next_action="Continue the next objective-relevant task"):
        return {
            "state": state,
            "focus_task_id": focus,
            "gap_summary": "A1 still needs a current reviewed artifact",
            "next_action": next_action,
            "resume_basis": [focus] if focus else [],
            "waiting_on": [] if state == "working" else [{"kind": "delegation", "ref": "D1", "condition": "B returns current evidence"}],
            "rationale": "Keep action aligned to the user objective",
        }

    def resolve(self, feedback_id="F1", disposition="adopted", artifact="h1", review=True, new_tasks=None, complete=True):
        payload = {
            "coordinator_generation": 1,
            "feedback_id": feedback_id,
            "disposition": disposition,
            "goal_relation": {
                "responsibility": "Own the user outcome and acceptance",
                "acceptance_ids": ["A1"],
                "rationale": "The result is relevant to the current acceptance gap",
            },
            "evidence_refs": [],
            "artifact_ref": {
                "ref": f"artifact://{artifact}", "digest": collaboration.digest({"artifact": artifact}),
                "contract_version": "contract-r1", "round": 1,
            } if disposition == "adopted" else None,
            "review": {
                "reviewer_id": "C", "delegation_id": "D1", "round": 1,
                "contract_version": "contract-r1", "artifact_ref": f"artifact://{artifact}",
                "artifact_digest": collaboration.digest({"artifact": artifact}),
                "scope_refs": ["scope://T1"], "verdict": "PASS",
                "rationale": "Current artifact and scope were reviewed",
            } if review else None,
            "task_changes": [{"task_id": "T1", "status": "completed"}] if disposition == "adopted" and complete else [],
            "new_tasks": new_tasks or [],
            "next_delegation": None,
            "coordination": self.coordination(),
        }
        return self.mutate("feedback.resolve", payload)

    def test_enable_preserves_objective_acceptance_tasks_and_focus(self):
        before = runtime.read_mission(self.mission)
        self.enable()
        after = runtime.read_mission(self.mission)
        self.assertEqual(after["mission"], before["mission"])
        self.assertEqual(after["tasks"], before["tasks"])
        self.assertEqual(after["active_task_id"], "T1")
        self.assertEqual(after["collaboration"]["schema_version"], collaboration.SCHEMA)
        self.assertEqual(collaboration.validate_state(after), [])

    def test_public_writer_cannot_add_or_modify_collaboration(self):
        before = runtime.read_mission(self.mission)
        bad = copy.deepcopy(before)
        bad["collaboration"] = {}
        with self.assertRaisesRegex(runtime.TplanError, "collaboration"):
            runtime.commit_mission_state(self.mission, before, bad, source={"kind": "runtime_script", "name": "fixture"})
        self.enable()
        before = runtime.read_mission(self.mission)
        with self.assertRaisesRegex(runtime.TplanError, "collaboration"):
            runtime.write_mission(self.root / "preloaded-collaboration", before)
        bad = copy.deepcopy(before)
        bad["collaboration"]["coordinator"]["responsibility"] = "Public rewrite"
        with self.assertRaisesRegex(runtime.TplanError, "collaboration"):
            runtime.commit_mission_state(self.mission, before, bad, source={"kind": "runtime_script", "name": "fixture"})

    def test_prepare_dispatch_unknown_and_same_scope_protection(self):
        self.enable()
        self.prepare()
        self.dispatch(send_state="unknown", execution_state="unknown")
        response, code = self.mutate("delegation.prepare", self.delegation_payload(delegation_id="D2", intent_id="I2"))
        self.assertEqual((code, response["code"]), (collaboration.EXITS["execution_in_flight"], "execution_in_flight"))
        reconciled, code = self.mutate("dispatch.record", {
            "coordinator_generation": 1, "intent_id": "I1", "send_state": "confirmed",
            "execution_state": "running", "stop_requested": True, "native_refs": ["thread://b/message/real"],
            "observed_at": "2026-11-17T01:01:00+00:00", "reason": "Original send found; stop requested but still running",
        })
        self.assertEqual(code, 0, reconciled)
        response, code = self.mutate("delegation.prepare", self.delegation_payload(delegation_id="D2", intent_id="I2"))
        self.assertEqual(code, collaboration.EXITS["execution_in_flight"], response)
        stopped, code = self.mutate("dispatch.record", {
            "coordinator_generation": 1, "intent_id": "I1", "send_state": "confirmed",
            "execution_state": "stopped", "stop_requested": True, "native_refs": ["thread://b/message/stopped"],
            "observed_at": "2026-11-17T01:02:00+00:00", "reason": "Original worker confirmed stopped",
        })
        self.assertEqual(code, 0, stopped)
        self.prepare(delegation_id="D2", intent_id="I2")

    def test_feedback_replay_conflict_and_pulse_cover_non_active_task(self):
        self.enable()
        self.prepare()
        checkpoint, code = self.mutate("coordination.checkpoint", {
            "coordinator_generation": 1, "state": "working", "focus_task_id": "T2",
            "gap_summary": "A remains on the objective-relevant task", "next_action": "Continue T2",
            "resume_basis": ["T2"], "waiting_on": [], "rationale": "A deliberately switched focus before T1 feedback arrived",
        })
        self.assertEqual(code, 0, checkpoint)
        first = self.feedback(source="msg-1", summary="T1 result")
        replay = self.feedback(source="msg-1", summary="T1 result")
        self.assertEqual(first["data"]["feedback_id"], replay["data"]["feedback_id"])
        # Different content for the same source is a conflict.
        different_payload = {
            "coordinator_generation": 1, "source_event_ref": "msg-1", "source_thread_ref": "thread-b",
            "source_host_ref": "local", "source_role_id": "B", "delegation_id": "D1", "round": 1,
            "contract_version": "contract-r1", "artifact_ref": "artifact://different",
            "artifact_digest": collaboration.digest({"artifact": "different"}), "summary": "Different",
            "original_ref": "thread://source/msg-1", "attachment_refs": [],
        }
        conflict, code = self.mutate("feedback.record", different_payload)
        self.assertEqual((code, conflict["code"]), (collaboration.EXITS["feedback_conflict"], "feedback_conflict"))
        pulse = runtime.build_mission_pulse(self.mission, trigger="manual")
        self.assertEqual(pulse["winning_candidate"]["signal"], "collaboration_feedback")
        self.assertEqual(pulse["winning_candidate"]["candidate_next_gate"], "continuation_authorization")
        self.assertIn(first["data"]["feedback_id"], pulse["winning_candidate"]["source_ids"])
        self.assertEqual(runtime.read_mission(self.mission)["active_task_id"], "T2")

    def test_unassociated_natural_language_feedback_waits_for_targeted_question(self):
        self.enable()
        response = self.feedback(source="msg-ambiguous", delegation_id=None, artifact=None, summary="The report is ready")
        state = runtime.read_mission(self.mission)
        record = state["collaboration"]["feedback"][response["data"]["feedback_id"]]
        self.assertEqual(record["association_status"], "needs_association")
        self.assertEqual(record["status"], "pending")
        self.assertEqual(state["tasks"][0]["status"], "active")
        resume = self.snapshot()["data"]["resume"]
        self.assertEqual(resume["needs_association_count"], 1)
        self.assertEqual(resume["pending_feedback"][0]["association_status"], "needs_association")
        self.assertEqual(resume["next_action"], state["collaboration"]["coordination"]["next_action"])

    def test_task_completion_requires_current_adoption_and_matching_review(self):
        self.enable()
        self.prepare()
        self.dispatch()
        feedback = self.feedback(source_role="C")
        missing_review, code = self.resolve(feedback_id=feedback["data"]["feedback_id"], review=False)
        self.assertEqual((code, missing_review["code"]), (collaboration.EXITS["review_required"], "review_required"))
        accepted, code = self.resolve(feedback_id=feedback["data"]["feedback_id"], review=True)
        self.assertEqual(code, 0, accepted)
        state = runtime.read_mission(self.mission)
        self.assertEqual(state["tasks"][0]["status"], "completed")
        self.assertEqual(state["active_task_id"], "T2")
        self.assertEqual(state["collaboration"]["adoptions"]["D1"]["artifact_ref"], "artifact://h1")

    def test_late_review_of_old_artifact_does_not_replace_current_adoption(self):
        self.enable()
        self.prepare()
        self.dispatch()
        old = self.feedback(source="msg-h1", artifact="h1", summary="Old result", source_role="C")
        current = self.feedback(source="msg-h2", artifact="h2", summary="Current result", source_role="C")
        accepted, code = self.resolve(feedback_id=current["data"]["feedback_id"], artifact="h2", review=True, complete=False)
        self.assertEqual(code, 0, accepted)
        late, code = self.resolve(feedback_id=old["data"]["feedback_id"], disposition="answered", artifact="h1", review=True)
        self.assertEqual(code, 0, late)
        runtime.transition_task_status(self.mission, "T1", "completed")
        adoption = runtime.read_mission(self.mission)["collaboration"]["adoptions"]["D1"]
        self.assertEqual(adoption["artifact_ref"], "artifact://h2")
        self.assertGreaterEqual(len(runtime.read_mission(self.mission)["collaboration"]["reviews"]), 2)

    def test_guard_and_stale_snapshot_reject_before_persistent_write(self):
        self.enable()
        stale = self.snapshot()["data"]["expected_snapshot"]
        self.prepare()
        guard_feedback = {
            "coordinator_generation": 1, "source_event_ref": "msg-guard", "source_thread_ref": "thread-b",
            "source_host_ref": "local", "source_role_id": "B", "delegation_id": "D1", "round": 1,
            "contract_version": "contract-r1", "artifact_ref": "artifact://h1",
            "artifact_digest": collaboration.digest({"artifact": "h1"}), "summary": "Guard input",
            "original_ref": "thread://source/msg-guard", "attachment_refs": [],
        }
        response, code = self.mutate("feedback.record", guard_feedback, expected_snapshot=stale)
        self.assertEqual((code, response["code"]), (collaboration.EXITS["stale_snapshot"], "stale_snapshot"))
        runtime.begin_interaction_guard(self.mission, platform="codex", binding_id="S1", message_ref="private")
        before = (self.mission / "mission.json").read_bytes()
        response, code = self.mutate("coordination.checkpoint", {
            "coordinator_generation": 1, "state": "waiting_external", "focus_task_id": "T1",
            "gap_summary": "Wait for B", "next_action": "Read B result after Guard resolution",
            "resume_basis": ["D1"], "waiting_on": [{"kind": "delegation", "ref": "D1", "condition": "B result"}],
            "rationale": "Guard remains open",
        })
        self.assertEqual((code, response["code"]), (collaboration.EXITS["guard_open"], "guard_open"))
        self.assertEqual(before, (self.mission / "mission.json").read_bytes())
        resolved = runtime.resolve_guard_at_turn_end(self.mission, platform="codex", binding_id="S1")
        self.assertEqual(resolved["disposition"], "resume_original")
        imported, code = self.mutate("feedback.record", guard_feedback)
        self.assertEqual((code, imported["status"]), (0, "committed"))
        duplicate, code = self.mutate("feedback.record", guard_feedback)
        self.assertEqual((code, duplicate["status"]), (0, "no_change"))
        self.assertEqual(imported["data"]["feedback_id"], duplicate["data"]["feedback_id"])

    def test_checkpoint_wait_resume_and_coordinator_handoff(self):
        self.enable()
        self.prepare()
        self.dispatch(send_state="confirmed", execution_state="running")
        waiting, code = self.mutate("coordination.checkpoint", {
            "coordinator_generation": 1, "state": "waiting_external", "focus_task_id": "T1",
            "gap_summary": "B is implementing the current result", "next_action": "Read B result and decide acceptance",
            "resume_basis": ["D1", "I1"],
            "waiting_on": [{"kind": "delegation", "ref": "D1", "condition": "B returns current evidence"}],
            "rationale": "All active work is external; Mission remains active",
        })
        self.assertEqual(code, 0, waiting)
        state = runtime.read_mission(self.mission)
        self.assertEqual(state["mission"]["status"], "active")
        self.assertEqual(state["collaboration"]["coordination"]["state"], "waiting_external")
        resume = self.snapshot()["data"]["resume"]
        self.assertEqual(resume["next_action"], "Read B result and decide acceptance")
        handoff, code = self.mutate("coordinator.handoff", {
            "coordinator_generation": 1,
            "coordinator": {"thread_ref": "thread-a2", "host_ref": "local", "responsibility": "Continue as A2",
                            "communication_authorization_refs": ["user-turn-2"]},
            "rationale": "A was replaced after interruption",
        })
        self.assertEqual(code, 0, handoff)
        stale, code = self.mutate("coordination.checkpoint", {
            "coordinator_generation": 1, "state": "working", "focus_task_id": "T1",
            "gap_summary": "stale", "next_action": "stale", "resume_basis": ["T1"],
            "waiting_on": [], "rationale": "old writer",
        })
        self.assertEqual((code, stale["code"]), (collaboration.EXITS["stale_generation"], "stale_generation"))

    def test_repair_of_completed_task_requires_bounded_new_success_critical_task(self):
        self.enable()
        self.prepare()
        self.dispatch()
        first = self.feedback(source="msg-1", artifact="h1", summary="Initial result", source_role="C")
        accepted, code = self.resolve(feedback_id=first["data"]["feedback_id"], artifact="h1", review=True)
        self.assertEqual(code, 0, accepted)
        failure = self.feedback(source="msg-2", artifact="h2", summary="Current result has a defect")
        payload = {
            "coordinator_generation": 1, "feedback_id": failure["data"]["feedback_id"], "disposition": "repair",
            "goal_relation": {"responsibility": "Own acceptance", "acceptance_ids": ["A1"],
                              "rationale": "The defect blocks the current acceptance claim"},
            "evidence_refs": [], "artifact_ref": None, "review": None,
            "task_changes": [], "new_tasks": [], "next_delegation": None,
            "coordination": self.coordination(focus="T2", next_action="Create a bounded repair task"),
        }
        missing, code = self.mutate("feedback.resolve", payload)
        self.assertEqual((code, missing["code"]), (collaboration.EXITS["repair_scope_required"], "repair_scope_required"))
        payload["new_tasks"] = [{
            "id": "T3", "title": "Repair current result", "role": "success-critical",
            "mission_contribution": "Restores A1", "acceptance_evidence": ["A1"], "status": "pending",
        }]
        payload["coordination"] = self.coordination(focus="T3", next_action="Execute the bounded repair task")
        repaired, code = self.mutate("feedback.resolve", payload)
        self.assertEqual(code, 0, repaired)
        state = runtime.read_mission(self.mission)
        self.assertIn("T3", {task["id"] for task in state["tasks"]})
        self.assertFalse(any("pending collaboration feedback" in item for item in collaboration.completion_findings(state)))

    def test_capacity_refuses_new_feedback_without_losing_existing_record(self):
        self.enable()
        self.prepare()
        self.feedback(source="msg-1", summary="First")
        before = runtime.read_mission(self.mission)
        with mock.patch.object(collaboration, "DEFAULT_MAX_PENDING_FEEDBACK", 1):
            response = self.feedback(source="msg-2", summary="Second", assert_ok=False)
        code = collaboration.EXITS[response["code"]]
        self.assertEqual((code, response["code"]), (collaboration.EXITS["capacity_exceeded"], "capacity_exceeded"))
        self.assertEqual(before, runtime.read_mission(self.mission))

    def test_manifest_and_installed_skill_documents_include_collaboration_recipe(self):
        manifest = json.loads((SCRIPTS.parent / "resources" / "runtime-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["capability_versions"]["collaboration"], "tplan.collaboration.v0.1")
        self.assertIn("tplan.collaboration.v0.1", manifest["capabilities"])
        for path in ("scripts/collaboration.py", "scripts/collaboration_runtime.py"):
            self.assertIn(path, manifest["required_scripts"])
            self.assertIn(path, manifest["fingerprint_files"])
        skill = (SCRIPTS.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("collaboration_runtime.py", skill)
        self.assertIn("B/C", skill)

    def test_command_replay_query_and_conflict(self):
        self.enable()
        snapshot = self.snapshot()["data"]["expected_snapshot"]
        request = {
            "protocol": collaboration.PROTOCOL,
            "action": "delegation.prepare",
            "mission_id": "collaboration-mission",
            "command_id": "stable-prepare",
            "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
            "expected_snapshot": snapshot,
            "payload": self.delegation_payload(),
        }
        first, code = collaboration_runtime.execute(self.mission, request, principal=self.principal)
        self.assertEqual((code, first["status"]), (0, "committed"), first)
        before = runtime.read_mission(self.mission)
        replay, code = collaboration_runtime.execute(self.mission, request, principal=self.principal)
        self.assertEqual((code, replay["status"]), (0, "replayed"), replay)
        self.assertEqual(before, runtime.read_mission(self.mission))
        changed = copy.deepcopy(request)
        changed["payload"]["instruction_summary"] = "Different content under the same command"
        conflict, code = collaboration_runtime.execute(self.mission, changed, principal=self.principal)
        self.assertEqual((code, conflict["code"]), (collaboration.EXITS["command_conflict"], "command_conflict"))
        read_request = {
            **{key: request[key] for key in ("protocol", "mission_id", "command_id", "expected_build_hash")},
            "action": "command.get",
            "expected_snapshot": None,
            "payload": {},
        }
        historical, code = collaboration_runtime.execute(self.mission, read_request, principal=self.principal)
        self.assertEqual(code, 0, historical)
        self.assertEqual(historical["data"]["request_digest"], first["data"].get("request_digest", historical["data"]["request_digest"]))
        self.assertEqual(historical["data"]["data"]["delegation_id"], "D1")

    def test_explicit_recovery_rolls_forward_once(self):
        self.enable()
        snapshot = self.snapshot()["data"]["expected_snapshot"]
        request = {
            "protocol": collaboration.PROTOCOL,
            "action": "delegation.prepare",
            "mission_id": "collaboration-mission",
            "command_id": "crash-prepare",
            "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
            "expected_snapshot": snapshot,
            "payload": self.delegation_payload(),
        }
        script = '''import json, os, sys\nfrom pathlib import Path\nsys.path.insert(0, sys.argv[1])\nimport tplan_runtime as runtime\nimport collaboration_runtime as collab\nruntime._recover_pending_mission_transaction_unlocked=lambda *a,**k: os._exit(91)\nrequest=json.loads(sys.argv[2])\ncollab.execute(Path(sys.argv[3]), request, principal="coordinator-a")\n'''
        crashed = subprocess.run(
            [sys.executable, "-B", "-c", script, str(SCRIPTS), json.dumps(request), str(self.mission)],
            text=True,
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(crashed.returncode, 91, crashed.stdout + crashed.stderr)
        self.assertTrue((self.mission / ".mission-transaction.json").exists())
        blocked, code = collaboration_runtime.execute(
            self.mission,
            {
                "protocol": collaboration.PROTOCOL, "action": "snapshot.get",
                "mission_id": "collaboration-mission", "command_id": "read-pending",
                "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
                "expected_snapshot": None, "payload": {},
            },
            principal=self.principal,
        )
        self.assertEqual((code, blocked["code"]), (collaboration.EXITS["recovery_required"], "recovery_required"))
        recovery = {**request, "action": "runtime.recover", "command_id": "crash-prepare", "expected_snapshot": None, "payload": {}}
        recovered, code = collaboration_runtime.execute(self.mission, recovery, principal=self.principal)
        self.assertEqual(code, 0, recovered)
        self.assertTrue(recovered["data"]["recovered"])
        self.assertEqual(recovered["data"]["result"]["data"]["delegation_id"], "D1")
        replay, code = collaboration_runtime.execute(self.mission, request, principal=self.principal)
        self.assertEqual((code, replay["status"]), (0, "replayed"))
        state = runtime.read_mission(self.mission)
        self.assertIn("D1", state["collaboration"]["delegations"])
        self.assertEqual(len(state["collaboration"]["delegations"]), 1)

    def test_review_identity_must_match_required_reviewer(self):
        self.enable()
        self.prepare()
        feedback = self.feedback()
        response, code = self.mutate("feedback.resolve", {
            "coordinator_generation": 1, "feedback_id": feedback["data"]["feedback_id"],
            "disposition": "adopted",
            "goal_relation": {"responsibility": "Own acceptance", "acceptance_ids": ["A1"],
                              "rationale": "The artifact is relevant"},
            "evidence_refs": [],
            "artifact_ref": {"ref": "artifact://h1", "digest": collaboration.digest({"artifact": "h1"}),
                             "contract_version": "contract-r1", "round": 1},
            "review": {"reviewer_id": "B", "delegation_id": "D1", "round": 1,
                       "contract_version": "contract-r1", "artifact_ref": "artifact://h1",
                       "artifact_digest": collaboration.digest({"artifact": "h1"}),
                       "scope_refs": ["scope://T1"], "verdict": "PASS", "rationale": "Self-review"},
            "task_changes": [{"task_id": "T1", "status": "completed"}],
            "new_tasks": [], "next_delegation": None, "coordination": self.coordination(),
        })
        self.assertEqual((code, response["code"]), (collaboration.EXITS["review_required"], "review_required"))
        self.assertEqual(runtime.read_mission(self.mission)["collaboration"]["adoptions"], {})

    def test_path_adjustment_and_next_delegation_commit_together(self):
        self.enable()
        self.prepare()
        feedback = self.feedback(artifact=None, summary="The current path cannot meet the acceptance contract")
        next_delegation = self.delegation_payload(task_id="T2", delegation_id="D2", intent_id="I2", round_no=2)
        next_delegation.pop("coordinator_generation")
        response, code = self.mutate("feedback.resolve", {
            "coordinator_generation": 1, "feedback_id": feedback["data"]["feedback_id"],
            "disposition": "path_adjusted",
            "goal_relation": {"responsibility": "Own the user outcome", "acceptance_ids": ["A1"],
                              "rationale": "The evidence invalidates the current implementation path"},
            "evidence_refs": [], "artifact_ref": None, "review": None,
            "task_changes": [{"task_id": "T1", "status": "paused"}],
            "new_tasks": [], "next_delegation": next_delegation,
            "coordination": self.coordination(focus="T2", next_action="Run the revised T2 path"),
        })
        self.assertEqual(code, 0, response)
        state = runtime.read_mission(self.mission)
        self.assertEqual(state["collaboration"]["feedback"][feedback["data"]["feedback_id"]]["status"], "resolved")
        self.assertIn("D2", state["collaboration"]["delegations"])
        self.assertIn("I2", state["collaboration"]["intents"])
        self.assertEqual(state["active_task_id"], "T2")

    def test_high_frequency_feedback_is_one_pulse_candidate(self):
        self.enable()
        self.prepare()
        first = self.feedback(source="msg-a", summary="Progress A")
        second = self.feedback(source="msg-b", summary="Progress B")
        third = self.feedback(source="msg-c", summary="Repeated review note")
        pulse = runtime.build_mission_pulse(self.mission, trigger="manual")
        candidates = [item for item in pulse["review_trigger_candidates"] if item["context"].get("source") == "collaboration"]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            set(candidates[0]["source_ids"]),
            {first["data"]["feedback_id"], second["data"]["feedback_id"], third["data"]["feedback_id"]},
        )

    def test_goal_preservation_scenario_spec_is_expectation_not_execution(self):
        path = Path(__file__).with_name("collaboration_behavior_replay.jsonl")
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual({item["case"] for item in records}, {"T26", "T27", "T28", "T29"})
        for item in records:
            self.assertEqual(item["evidence_class"], "scenario_expectation")
            self.assertFalse(item["real_host_e2e"])
            self.assertEqual(item["source_audit"], "pending")
            self.assertTrue(item["turns"])
            self.assertTrue(all(turn.get("a_decision") and turn.get("next_action") for turn in item["turns"]))

    def resolution(self, feedback_id, delegation="D1", round_no=1, artifact="h1", disposition="adopted",
                   verdict="PASS", complete=False, review_task="T1", new_tasks=None, next_delegation=None, focus="T2"):
        return {
            "coordinator_generation": 1, "feedback_id": feedback_id, "disposition": disposition,
            "goal_relation": {"responsibility": "Own acceptance", "acceptance_ids": ["A1"],
                              "rationale": "Scope and version checked for the original objective"},
            "evidence_refs": [],
            "artifact_ref": {"ref": f"artifact://{artifact}", "digest": collaboration.digest({"artifact": artifact}),
                             "contract_version": f"contract-r{round_no}", "round": round_no} if disposition == "adopted" else None,
            "review": {"reviewer_id": "C", "delegation_id": delegation, "round": round_no,
                       "contract_version": f"contract-r{round_no}", "artifact_ref": f"artifact://{artifact}",
                       "artifact_digest": collaboration.digest({"artifact": artifact}),
                       "scope_refs": [f"scope://{review_task}"], "verdict": verdict,
                       "rationale": "Observed review of this artifact"} if verdict else None,
            "task_changes": [{"task_id": review_task, "status": "completed"}] if complete else [],
            "new_tasks": new_tasks or [], "next_delegation": next_delegation,
            "coordination": self.coordination(focus=focus),
        }

    def test_r01_ordinary_progress_does_not_force_loopback_or_override_next_action(self):
        self.enable(); self.prepare()
        self.mutate("coordination.checkpoint", {"coordinator_generation": 1, **self.coordination(focus="T2", next_action="Continue T2")})
        self.feedback(source="progress-1", summary="B ordinary progress", kind="progress")
        pulse = runtime.build_mission_pulse(self.mission, trigger="manual")
        winner = pulse["winning_candidate"]
        self.assertEqual(winner["signal"], "collaboration_feedback")
        self.assertEqual(winner["candidate_next_gate"], "continuation_authorization")
        self.assertEqual(winner["severity"], "low")
        self.assertEqual(winner["priority_class"], "same_path_continuation")
        resume = self.snapshot()["data"]["resume"]
        self.assertEqual(resume["focus_task_id"], "T2")
        self.assertEqual(resume["next_action"], "Continue T2")

    def test_r01_blocker_feedback_routes_to_mission_review(self):
        self.enable(); self.prepare()
        self.feedback(source="block-1", summary="B reports a blocking defect", kind="blocker")
        pulse = runtime.build_mission_pulse(self.mission, trigger="manual")
        winner = pulse["winning_candidate"]
        self.assertEqual(winner["signal"], "collaboration_feedback")
        self.assertEqual(winner["candidate_next_gate"], "mission_review")
        self.assertEqual(winner["severity"], "high")
        self.assertEqual(winner["priority_class"], "current_blocker_or_feedback")

    def test_r03_later_fail_blocks_until_rereview_pass(self):
        self.enable(); self.prepare(); self.dispatch(execution_state="completed")
        f = self.feedback(source="review-pass", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], complete=True))
        self.assertEqual(k, 0, r)
        runtime.append_event(self.mission, {"event_type": "acceptance_passed", "summary": "A1", "task_id": "T1", "payload": {"acceptance_ids": ["A1"]}})
        f = self.feedback(source="later-review-fail", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], disposition="answered", verdict="FAIL"))
        self.assertEqual(k, 0, r)
        state = runtime.read_mission(self.mission)
        self.assertTrue(collaboration.completion_findings(state))
        state["mission"]["status"] = "completed"
        with self.assertRaises(runtime.TplanError):
            runtime.write_mission(self.mission, state)
        f = self.feedback(source="rereview-pass", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], disposition="answered", verdict="PASS"))
        self.assertEqual(k, 0, r)
        state = runtime.read_mission(self.mission)
        self.assertEqual(collaboration.completion_findings(state), [])
        state["mission"]["status"] = "completed"
        runtime.write_mission(self.mission, state)
        self.assertEqual(runtime.read_mission(self.mission)["mission"]["status"], "completed")

    def test_r03_old_version_fail_does_not_pollute_current_adoption(self):
        self.enable(); self.prepare(); self.dispatch(execution_state="completed")
        f = self.feedback(source="current-h2", artifact="h2", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], artifact="h2", complete=False))
        self.assertEqual(k, 0, r)
        f = self.feedback(source="old-h1-fail", artifact="h1", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], artifact="h1", disposition="answered", verdict="FAIL"))
        self.assertEqual(k, 0, r)
        runtime.transition_task_status(self.mission, "T1", "completed")
        self.assertEqual(runtime.find_task(runtime.read_mission(self.mission), "T1")["status"], "completed")

    def test_r04_review_cannot_transplant_across_delegations(self):
        self.enable(); self.prepare()
        self.prepare(task_id="T2", delegation_id="D2", intent_id="I2", round_no=2)
        f = self.feedback(source="review-about-D1", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], delegation="D2", round_no=2, disposition="answered", review_task="T2"))
        self.assertEqual((k, r["code"]), (collaboration.EXITS["review_required"], "review_required"))
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], delegation="D1", round_no=1, disposition="answered", review_task="T1"))
        self.assertEqual(k, 0, r)

    def test_r05_repair_or_adopt_cannot_release_running_scope(self):
        self.enable(); self.prepare(); self.dispatch(execution_state="running")
        f = self.feedback(source="defect-running", source_role="B", kind="blocker")
        nd = self.delegation_payload(delegation_id="D2", intent_id="I2", round_no=2); nd.pop("coordinator_generation")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], disposition="repair", verdict=None, next_delegation=nd))
        self.assertEqual((k, r["code"]), (collaboration.EXITS["execution_in_flight"], "execution_in_flight"))
        f2 = self.feedback(source="result-running", source_role="C")
        nd2 = self.delegation_payload(delegation_id="D3", intent_id="I3", round_no=2); nd2.pop("coordinator_generation")
        r, k = self.mutate("feedback.resolve", self.resolution(f2["data"]["feedback_id"], disposition="adopted", next_delegation=nd2))
        self.assertEqual((k, r["code"]), (collaboration.EXITS["execution_in_flight"], "execution_in_flight"))

    def test_r05_stopped_scope_allows_new_round_and_independent_scope_proceeds(self):
        self.enable(); self.prepare(); self.dispatch(execution_state="running")
        self.prepare(task_id="T2", delegation_id="DInd", intent_id="IInd", round_no=1)
        self.dispatch(intent_id="I1", execution_state="stopped", stop_requested=True)
        f = self.feedback(source="defect-stopped", source_role="B", kind="blocker")
        nd = self.delegation_payload(delegation_id="D2", intent_id="I2", round_no=2); nd.pop("coordinator_generation")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], disposition="repair", verdict=None, next_delegation=nd))
        self.assertEqual(k, 0, r)
        self.assertIn("D2", runtime.read_mission(self.mission)["collaboration"]["delegations"])

    def test_r06_not_sent_then_new_round_completes(self):
        self.enable(); self.prepare(); self.dispatch(send_state="not_sent", execution_state="not_started")
        self.prepare(delegation_id="D2", intent_id="I2", round_no=2)
        self.dispatch(intent_id="I2", execution_state="completed")
        f = self.feedback(source="new-round-reviewed", delegation_id="D2", artifact="h2", source_role="C", round_no=2)
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], delegation="D2", round_no=2, artifact="h2", complete=True))
        self.assertEqual(k, 0, r)
        self.assertEqual(runtime.find_task(runtime.read_mission(self.mission), "T1")["status"], "completed")

    def test_r06_stopped_then_new_round_completes(self):
        self.enable(); self.prepare(); self.dispatch(execution_state="running")
        self.dispatch(intent_id="I1", execution_state="stopped", stop_requested=True)
        self.prepare(delegation_id="D2", intent_id="I2", round_no=2)
        self.dispatch(intent_id="I2", execution_state="completed")
        f = self.feedback(source="stopped-new-round", delegation_id="D2", artifact="h2", source_role="C", round_no=2)
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], delegation="D2", round_no=2, artifact="h2", complete=True))
        self.assertEqual(k, 0, r)

    def test_r06_completed_task_defect_repair_rereview_mission_close(self):
        self.enable(); self.prepare(); self.dispatch(execution_state="completed")
        f = self.feedback(source="initial-pass", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], complete=True))
        self.assertEqual(k, 0, r)
        runtime.append_event(self.mission, {"event_type": "acceptance_passed", "summary": "A1 initial", "task_id": "T1", "payload": {"acceptance_ids": ["A1"]}})
        f = self.feedback(source="post-completion-defect", source_role="B", kind="blocker")
        repair_task = {"id": "T3", "title": "Repair current result", "role": "success-critical",
                       "mission_contribution": "Restores A1", "acceptance_evidence": ["A1"], "status": "pending"}
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], disposition="repair", verdict=None, new_tasks=[repair_task], focus="T3"))
        self.assertEqual(k, 0, r)
        self.prepare(task_id="T3", delegation_id="D3", intent_id="I3", round_no=1)
        self.dispatch(intent_id="I3", execution_state="completed")
        f = self.feedback(source="repair-reviewed", delegation_id="D3", artifact="h3", source_role="C")
        r, k = self.mutate("feedback.resolve", self.resolution(f["data"]["feedback_id"], delegation="D3", round_no=1, artifact="h3", complete=True, review_task="T3", focus=None))
        self.assertEqual(k, 0, r)
        runtime.append_event(self.mission, {"event_type": "acceptance_passed", "summary": "A1 repaired", "task_id": "T3", "payload": {"acceptance_ids": ["A1"]}})
        state = runtime.read_mission(self.mission)
        self.assertEqual(collaboration.completion_findings(state), [])
        state["mission"]["status"] = "completed"
        runtime.write_mission(self.mission, state)
        self.assertEqual(runtime.read_mission(self.mission)["mission"]["status"], "completed")

    def _prepared_crash(self, command_id="prepared-to-recover"):
        self.enable()
        with mock.patch.object(runtime, "_recover_pending_mission_transaction_unlocked", side_effect=OSError("prepared crash")):
            r, k = self.mutate("delegation.prepare", self.delegation_payload(), command_id=command_id)
        self.assertEqual(r["code"], "outcome_unknown", r)
        self.assertTrue((self.mission / ".mission-transaction.json").exists())

    def test_r07_recovery_rejects_wrong_identity_before_write(self):
        self._prepared_crash()
        before = (self.mission / "mission.json").read_bytes()
        for change in ({"mission_id": "wrong-mission"}, {"expected_build_hash": "sha256:" + "0" * 64}):
            req = {"protocol": collaboration.PROTOCOL, "action": "runtime.recover", "mission_id": "collaboration-mission",
                   "command_id": "prepared-to-recover", "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
                   "expected_snapshot": None, "payload": {}}
            req.update(change)
            r, k = collaboration_runtime.execute(self.mission, req, principal=self.principal)
            self.assertNotEqual(k, 0, r)
            self.assertEqual((self.mission / "mission.json").read_bytes(), before)
            self.assertTrue((self.mission / ".mission-transaction.json").exists())
        req = {"protocol": collaboration.PROTOCOL, "action": "runtime.recover", "mission_id": "collaboration-mission",
               "command_id": "prepared-to-recover", "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
               "expected_snapshot": None, "payload": {}}
        r, k = collaboration_runtime.execute(self.mission, req, principal=self.principal)
        self.assertEqual(k, 0, r)
        self.assertTrue(r["data"]["recovered"])
        self.assertIn("D1", runtime.read_mission(self.mission)["collaboration"]["delegations"])

    def test_r08_write_response_snapshot_is_current_and_usable(self):
        r = self.enable()
        advertised = r["data"]["expected_snapshot"]
        actual = self.snapshot()["data"]["expected_snapshot"]
        self.assertEqual(advertised, actual)
        response, k = self.mutate("delegation.prepare", self.delegation_payload(), expected_snapshot=advertised)
        self.assertEqual(k, 0, response)
        replay, k = collaboration_runtime.execute(self.mission, {
            "protocol": collaboration.PROTOCOL, "action": "delegation.prepare", "mission_id": "collaboration-mission",
            "command_id": "command-2", "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
            "expected_snapshot": advertised, "payload": self.delegation_payload()}, principal=self.principal)
        self.assertEqual((k, replay["status"]), (0, "replayed"))
        self.assertEqual(replay["data"]["expected_snapshot"], self.snapshot()["data"]["expected_snapshot"])

    def test_r09_trace_capacity_includes_this_append(self):
        self.enable()
        trace = self.mission / "execution_trace.jsonl"
        data = trace.read_bytes().rstrip(b"\n")
        target = collaboration.MAX_ARTIFACT - 100
        trace.write_bytes(data + b" " * (target - len(data) - 1) + b"\n")
        before = trace.stat().st_size
        r, k = self.mutate("coordination.checkpoint", {"coordinator_generation": 1, **self.coordination()})
        self.assertEqual((k, r["code"]), (collaboration.EXITS["capacity_exceeded"], "capacity_exceeded"))
        self.assertEqual(trace.stat().st_size, before)
        read, read_code = collaboration_runtime.execute(self.mission, {
            "protocol": collaboration.PROTOCOL, "action": "snapshot.get", "mission_id": "collaboration-mission",
            "command_id": "post-capacity", "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
            "expected_snapshot": None, "payload": {}}, principal=self.principal)
        self.assertEqual(read_code, 0, read)


if __name__ == "__main__":
    unittest.main()
