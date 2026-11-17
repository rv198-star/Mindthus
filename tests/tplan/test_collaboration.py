"""Pure contract tests for optional A-side TPlan collaboration state."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import collaboration


class CollaborationContractTests(unittest.TestCase):
    def base_state(self):
        return {
            "schema_version": collaboration.SCHEMA,
            "enabled_at": "2026-11-17T00:00:00+00:00",
            "coordinator": {
                "generation": 1,
                "thread_ref": "thread-a",
                "host_ref": "local",
                "responsibility": "Own the user outcome and acceptance",
                "communication_authorization_refs": ["user-turn-1"],
            },
            "participants": {
                "B": {
                    "thread_ref": "thread-b",
                    "host_ref": "local",
                    "responsibility": "Implement the bounded work",
                    "communication_authorization_refs": ["user-turn-1"],
                }
            },
            "policy": {"max_pending_feedback": 128, "processing_deadline_seconds": 900},
            "delegations": {},
            "intents": {},
            "feedback": {},
            "adoptions": {},
            "reviews": {},
            "repair_obligations": {},
            "coordination": {
                "state": "working",
                "focus_task_id": "T1",
                "gap_summary": "Finish the current acceptance gap",
                "next_action": "Continue T1",
                "resume_basis": ["T1"],
                "waiting_on": [],
                "updated_at": "2026-11-17T00:00:00+00:00",
            },
            "commands": {},
        }

    def mission(self):
        return {
            "mission": {"id": "m1", "objective": "Ship a verified result", "acceptance_evidence": [{"id": "A1"}]},
            "tasks": [
                {"id": "T1", "kind": "task", "role": "success-critical", "status": "active", "acceptance_evidence": ["A1"]},
                {"id": "T2", "kind": "task", "role": "supporting", "status": "pending", "acceptance_evidence": []},
            ],
            "active_task_id": "T1",
            "collaboration": self.base_state(),
        }

    def test_state_shape_accepts_the_frozen_minimum(self):
        self.assertEqual(collaboration.validate_state(self.mission()), [])

    def test_state_shape_rejects_unknown_fields_bad_refs_and_duplicate_active_scope(self):
        state = self.mission()
        state["collaboration"]["extra"] = True
        self.assertTrue(collaboration.validate_state(state))

        state = self.mission()
        delegation = {
            "delegation_id": "D1",
            "task_id": "missing",
            "round": 1,
            "assignee_id": "missing",
            "write_scope": "src/a",
            "contract_version": "contract-1",
            "instruction_summary": "Exercise a missing task",
            "instruction_digest": "sha256:" + "1" * 64,
            "input_refs": [],
            "dependency_versions": {},
            "required_review": {"required": False, "reviewer_id": None, "scope_refs": []},
            "intent_id": "I1",
            "status": "prepared",
            "created_at": "2026-11-17T00:00:00+00:00",
            "disposition": None,
        }
        state["collaboration"]["delegations"]["D1"] = delegation
        findings = collaboration.validate_state(state)
        self.assertTrue(any("task" in item and "does not exist" in item for item in findings))
        self.assertTrue(any("assignee" in item for item in findings))

    def test_resume_view_keeps_objective_responsibility_and_pending_feedback(self):
        state = self.mission()
        state["collaboration"]["feedback"]["F1"] = {
            "feedback_id": "F1",
            "kind": "result",
            "source_event_ref": "msg-1",
            "source_thread_ref": "thread-b",
            "source_host_ref": "local",
            "source_role_id": "B",
            "delegation_id": None,
            "round": None,
            "contract_version": None,
            "artifact_ref": None,
            "artifact_digest": None,
            "content_digest": "sha256:" + "2" * 64,
            "summary": "I found a result but did not name the task.",
            "original_ref": "thread://b/message/1",
            "attachment_refs": [],
            "association_status": "needs_association",
            "association_gap": "task/delegation round and contract version are required",
            "status": "pending",
            "recorded_at": "2026-11-17T00:00:00+00:00",
            "resolution": None,
        }
        view = collaboration.build_resume_view(state)
        self.assertEqual(view["objective"], "Ship a verified result")
        self.assertEqual(view["coordinator_responsibility"], "Own the user outcome and acceptance")
        self.assertEqual(view["focus_task_id"], "T1")
        self.assertEqual(view["pending_feedback"][0]["association_status"], "needs_association")
        self.assertEqual(view["needs_association_count"], 1)
        self.assertEqual(view["next_action"], "Continue T1")

    def test_completion_findings_block_pending_feedback_and_required_review(self):
        state = self.mission()
        state["collaboration"]["feedback"]["F1"] = {
            "feedback_id": "F1", "kind": "blocker", "source_event_ref": "msg-1", "source_thread_ref": "thread-b",
            "source_host_ref": "local", "source_role_id": "B", "delegation_id": "D1",
            "round": 1, "contract_version": "contract-1", "artifact_ref": "artifact://h1",
            "artifact_digest": "sha256:" + "2" * 64, "content_digest": "sha256:" + "3" * 64,
            "summary": "A current failure", "original_ref": "thread://b/message/1", "attachment_refs": [],
            "association_status": "linked", "association_gap": None, "status": "pending",
            "recorded_at": "2026-11-17T00:00:00+00:00", "resolution": None,
        }
        findings = collaboration.completion_findings(state)
        self.assertTrue(any("pending collaboration feedback" in item for item in findings))

    def test_request_parser_rejects_duplicate_and_nonfinite_values(self):
        with self.assertRaises(collaboration.CollaborationError):
            collaboration.parse_request('{"protocol":"a","protocol":"b"}')
        with self.assertRaises(collaboration.CollaborationError):
            collaboration.parse_request('{"value":NaN}')

    def test_validator_does_not_mutate_input(self):
        state = self.mission()
        before = copy.deepcopy(state)
        collaboration.validate_state(state)
        self.assertEqual(state, before)
        json.dumps(state, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
