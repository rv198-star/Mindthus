import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PULSE_SCHEMA_VERSION = "tplan.pulse.v0.2"
CANDIDATE_REQUIRED_FIELDS = {
    "signal",
    "candidate_next_gate",
    "scope",
    "source_kind",
    "source_ids",
    "priority_class",
    "severity",
    "freshness",
    "reason",
    "context",
}
CANDIDATE_SCOPES = {"active_node", "subpath", "mission"}
CANDIDATE_SOURCE_KINDS = {
    "trigger",
    "mission_state",
    "evidence_event",
    "step_log",
    "risk_signal",
    "task",
    "validation",
    "derived",
}
CANDIDATE_PRIORITIES = {
    "requires_human_or_stop",
    "mission_boundary",
    "runtime_integrity",
    "active_shared_risk",
    "current_blocker_or_feedback",
    "anti_spiral",
    "checkpoint_weak_evidence_delta",
    "branch_or_switch_cleanup",
    "same_path_continuation",
}
CANDIDATE_SEVERITIES = {"low", "medium", "high", "critical"}
CANDIDATE_FRESHNESS = {
    "current_trigger",
    "current_state",
    "current_path",
    "checkpoint_window",
    "recent_evidence",
    "historical",
    "unknown",
}


def run_script(script_name, *args):
    return subprocess.run(
        [sys.executable, str(REPO / "skills" / "tplan" / "scripts" / script_name), *args],
        text=True,
        capture_output=True,
    )


def create_mission(tmp):
    mission_dir = Path(tmp) / "mission"
    tasks = Path(tmp) / "tasks.json"
    tasks.write_text(
        json.dumps(
            [
                {
                    "id": "T1",
                    "title": "Validate pulse route",
                    "role": "success-critical",
                    "mission_contribution": "Keeps the Mission attached to the review route.",
                    "acceptance_evidence": ["A1"],
                },
                {
                    "id": "T2",
                    "title": "Run health gate",
                    "role": "supporting",
                    "mission_contribution": "Checks shared evidence health before rerun.",
                    "acceptance_evidence": [],
                },
                {
                    "id": "T3",
                    "title": "Explore alternate route",
                    "role": "exploratory",
                    "mission_contribution": "Provides an alternate path if the active route stops paying off.",
                    "acceptance_evidence": [],
                },
            ]
        ),
        encoding="utf-8",
    )
    result = run_script(
        "init_mission.py",
        "--dir",
        str(mission_dir),
        "--mission-id",
        "m1",
        "--title",
        "Mission Pulse",
        "--objective",
        "Route review signals without creating a new judgment center.",
        "--acceptance-evidence",
        "A1:Pulse routes observable signals to existing gates.",
        "--task-json",
        str(tasks),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    active = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "active")
    if active.returncode != 0:
        raise AssertionError(active.stderr)
    return mission_dir


def mission_files_snapshot(mission_dir):
    paths = [
        mission_dir / "mission.json",
        mission_dir / "evidence.jsonl",
        mission_dir / "mission.md",
    ]
    return {str(path.relative_to(mission_dir)): path.read_text(encoding="utf-8") for path in paths}


def mission_tree_snapshot(mission_dir):
    return {
        str(path.relative_to(mission_dir)): path.read_bytes()
        for path in sorted(mission_dir.rglob("*"))
        if path.is_file()
    }


def load_mission(mission_dir):
    return json.loads((mission_dir / "mission.json").read_text(encoding="utf-8"))


def save_mission(mission_dir, mission):
    (mission_dir / "mission.json").write_text(json.dumps(mission, indent=2), encoding="utf-8")


class MissionPulseTests(unittest.TestCase):
    def assert_pulse_read_only(self, mission_dir, *args):
        before = mission_tree_snapshot(mission_dir)
        result = run_script("mission_pulse.py", str(mission_dir), *args, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = mission_tree_snapshot(mission_dir)
        self.assertEqual(after, before)
        return json.loads(result.stdout)

    def assert_pulse_v2_contract(self, pulse):
        self.assertEqual(pulse["schema_version"], PULSE_SCHEMA_VERSION)
        self.assertEqual(pulse["mission_pulse"]["schema_version"], PULSE_SCHEMA_VERSION)
        self.assertIn("winning_candidate", pulse)
        self.assertIn("suppressed_candidates", pulse)
        self.assertIn("arbitration_trace", pulse)
        self.assertIsInstance(pulse["review_trigger_candidates"], list)
        self.assertIsInstance(pulse["suppressed_candidates"], list)
        self.assertIsInstance(pulse["arbitration_trace"], list)
        for candidate in pulse["review_trigger_candidates"]:
            self.assert_pulse_candidate_contract(candidate)

    def assert_pulse_candidate_contract(
        self,
        candidate,
        *,
        signal=None,
        candidate_next_gate=None,
        priority_class=None,
        source_kind=None,
        source_ids=None,
        freshness=None,
    ):
        self.assertTrue(CANDIDATE_REQUIRED_FIELDS.issubset(candidate), candidate)
        self.assertIn(candidate["scope"], CANDIDATE_SCOPES)
        self.assertIn(candidate["source_kind"], CANDIDATE_SOURCE_KINDS)
        self.assertIn(candidate["priority_class"], CANDIDATE_PRIORITIES)
        self.assertIn(candidate["severity"], CANDIDATE_SEVERITIES)
        self.assertIn(candidate["freshness"], CANDIDATE_FRESHNESS)
        self.assertIsInstance(candidate["source_ids"], list)
        self.assertIsInstance(candidate["context"], dict)
        if signal is not None:
            self.assertEqual(candidate["signal"], signal)
        if candidate_next_gate is not None:
            self.assertEqual(candidate["candidate_next_gate"], candidate_next_gate)
        if priority_class is not None:
            self.assertEqual(candidate["priority_class"], priority_class)
        if source_kind is not None:
            self.assertEqual(candidate["source_kind"], source_kind)
        if source_ids is not None:
            self.assertEqual(candidate["source_ids"], source_ids)
        if freshness is not None:
            self.assertEqual(candidate["freshness"], freshness)

    def candidate_by_signal(self, pulse, signal):
        matches = [candidate for candidate in pulse["review_trigger_candidates"] if candidate["signal"] == signal]
        self.assertEqual(len(matches), 1, pulse["review_trigger_candidates"])
        return matches[0]

    def assert_winning_signal(self, pulse, signal):
        self.assertIn("winning_candidate", pulse)
        self.assertIsNotNone(pulse["winning_candidate"])
        self.assertEqual(pulse["winning_candidate"]["signal"], signal)
        self.assertIn(pulse["winning_candidate"], pulse["review_trigger_candidates"])

    def assert_suppressed_signal(self, pulse, signal):
        self.assertIn("suppressed_candidates", pulse)
        suppressed = [candidate for candidate in pulse["suppressed_candidates"] if candidate["signal"] == signal]
        self.assertEqual(len(suppressed), 1, pulse["suppressed_candidates"])
        self.assertIn(suppressed[0], pulse["review_trigger_candidates"])

    def test_mission_pulse_is_read_only_and_routes_routine_checkpoint_to_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            before = mission_files_snapshot(mission_dir)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "checkpoint_batch", "--json")

            self.assertEqual(result.returncode, 0, result.stderr)
            after = mission_files_snapshot(mission_dir)
            self.assertEqual(after, before)
            pulse = json.loads(result.stdout)

        self.assertEqual(pulse["script_verdict"], "shape_only")
        self.assertTrue(pulse["agentic_judgment_required"])
        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continue")
        self.assertEqual(pulse["mission_pulse"]["trigger"], "checkpoint_batch")
        self.assertEqual(pulse["mission_pulse"]["scope"], "active_node")
        self.assertEqual(pulse["mission_pulse"]["signals"], [])
        self.assertIsNone(pulse["winning_candidate"])
        self.assertEqual(pulse["suppressed_candidates"], [])
        self.assertEqual(pulse["gate_owner"], "inline_alignment")
        self.assertNotIn("health_score", pulse)
        self.assertNotIn("health_verdict", pulse)
        self.assertFalse(pulse["review_trigger_candidates"])
        self.assertEqual(pulse["snapshot"]["active_task"]["id"], "T1")
        self.assertEqual(pulse["recent_evidence_summary"]["total_events"], 0)
        self.assertEqual(pulse["active_log_summary"]["task_id"], "T1")
        self.assertEqual(pulse["active_log_summary"]["log_count"], 0)
        self.assertFalse(pulse["pulse_shape_findings"])

    def test_mission_pulse_rejects_unknown_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "bogus_trigger", "--json")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported pulse trigger", result.stderr)

    def test_mission_pulse_rejects_user_feedback_trigger_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "user_feedback", "--json")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported pulse trigger", result.stderr)

    def test_mission_pulse_reports_evidence_link_lint_and_recent_summaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "key_finding",
                "--task-id",
                "T1",
                "--summary",
                "Observed a concrete route signal.",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            log = run_script(
                "record_step_log.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--step-id",
                "inspect",
                "--summary",
                "Inspected pulse output shape.",
                "--payload-json",
                '{"object_id": "pulse:shape"}',
            )
            self.assertEqual(log.returncode, 0, log.stderr)
            mission = load_mission(mission_dir)
            mission["tasks"][0]["evidence_links"] = ["E1", "E999"]
            save_mission(mission_dir, mission)

            result = run_script("mission_pulse.py", str(mission_dir), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["recent_evidence_summary"]["total_events"], 1)
        self.assertEqual(pulse["recent_evidence_summary"]["last_event_id"], "E1")
        self.assertEqual(pulse["recent_evidence_summary"]["counts_by_type"], {"key_finding": 1})
        self.assertEqual(pulse["recent_evidence_summary"]["recent_events"][0]["summary"], "Observed a concrete route signal.")
        self.assertEqual(pulse["active_log_summary"]["task_id"], "T1")
        self.assertEqual(pulse["active_log_summary"]["log_count"], 1)
        self.assertEqual(pulse["active_log_summary"]["last_log_id"], "L1")
        self.assertEqual(pulse["active_log_summary"]["object_touch_counts"], {"pulse:shape": 1})
        self.assertEqual(
            pulse["evidence_link_lint"]["unbound_evidence_links"],
            [{"task_id": "T1", "evidence_link": "E999"}],
        )
        self.assertFalse(pulse["evidence_link_lint"]["invalid_evidence_links"])
        self.assertFalse(pulse["pulse_shape_findings"])

    def test_mission_pulse_routes_active_shared_risk_to_health_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            risk = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_evidence_channel",
                "--signal",
                "evidence_channel_untrusted_until_smoke_check",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "evidence_persistence",
                "--value-effect",
                "Future acceptance evidence may be invalid until the channel is checked.",
                "--recommended-gate",
                "health_check",
                "--recovery-condition",
                "Evidence channel smoke check passes.",
            )
            self.assertEqual(risk.returncode, 0, risk.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "shared_risk")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["script_verdict"], "shape_only")
        self.assertTrue(pulse["agentic_judgment_required"])
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "health_check")
        self.assertEqual(pulse["gate_owner"], "shared_risk_mission_health_route")
        self.assertEqual(pulse["mission_pulse"]["scope"], "mission")
        self.assertIn("active_shared_risk", pulse["mission_pulse"]["signals"])
        self.assertIn("invalid_evidence_risk", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["systemic_probe"], "use_existing_structure")
        self.assertEqual(pulse["snapshot"]["shared_context"]["active_risk_signal_count"], 1)
        self.assertEqual(
            pulse["review_trigger_candidates"][0]["candidate_next_gate"],
            "health_check",
        )
        self.assert_winning_signal(pulse, "active_shared_risk")
        candidate = self.candidate_by_signal(pulse, "active_shared_risk")
        self.assert_pulse_candidate_contract(
            candidate,
            candidate_next_gate="health_check",
            priority_class="active_shared_risk",
            source_kind="risk_signal",
            source_ids=["E1"],
            freshness="current_state",
        )
        self.assertEqual(candidate["context"]["risk_signal_ids"], ["R1"])
        self.assertNotIn("risk_assessment", pulse)

    def test_mission_pulse_routes_before_continue_to_continuation_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "before_continue")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continuation_authorization")
        self.assertEqual(pulse["gate_owner"], "linear_continuation_gate")
        self.assertIn("same_path_continuation", pulse["mission_pulse"]["signals"])
        self.assertEqual(
            pulse["review_trigger_candidates"][0]["candidate_next_gate"],
            "continuation_authorization",
        )
        self.assert_winning_signal(pulse, "same_path_continuation")
        self.assert_pulse_candidate_contract(
            pulse["winning_candidate"],
            priority_class="same_path_continuation",
            source_kind="trigger",
            freshness="current_trigger",
        )

    def test_mission_pulse_routes_repeated_object_touch_to_anti_spiral(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            for index in range(3):
                result = run_script(
                    "record_step_log.py",
                    str(mission_dir),
                    "--task-id",
                    "T1",
                    "--step-id",
                    f"repair-{index + 1}",
                    "--summary",
                    f"Adjusted the same local prompt section {index + 1}.",
                    "--payload-json",
                    '{"object_id": "prompt:section-a", "change_kind": "add_layer"}',
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "before_continue", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "anti_spiral_audit")
        self.assertEqual(pulse["gate_owner"], "anti_spiral_runtime_gate")
        self.assertIn("third_touch", pulse["mission_pulse"]["signals"])
        self.assertIn("additive_layering", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["systemic_probe"], "needs_gate")
        self.assert_winning_signal(pulse, "third_touch")
        candidate = self.candidate_by_signal(pulse, "third_touch")
        self.assert_pulse_candidate_contract(
            candidate,
            candidate_next_gate="anti_spiral_audit",
            priority_class="anti_spiral",
            source_kind="step_log",
            source_ids=["L1", "L2", "L3"],
            freshness="current_path",
        )
        self.assertEqual(candidate["context"]["object_ids"], ["prompt:section-a"])
        self.assertEqual(pulse["active_log_summary"]["repeated_object_ids"], ["prompt:section-a"])

    def test_mission_pulse_routes_freeze_handoff_and_stop_checks_to_mission_review(self):
        for trigger in ("before_freeze", "before_handoff", "before_stop"):
            with self.subTest(trigger=trigger):
                with tempfile.TemporaryDirectory() as tmp:
                    mission_dir = create_mission(tmp)
                    pulse = self.assert_pulse_read_only(mission_dir, "--trigger", trigger)

                self.assert_pulse_v2_contract(pulse)
                self.assertEqual(pulse["mission_pulse"]["next_gate"], "mission_review")
                self.assertEqual(pulse["gate_owner"], "mission_review_gate")
                self.assertIn("mission_boundary_review", pulse["mission_pulse"]["signals"])
                self.assertEqual(
                    pulse["review_trigger_candidates"][0]["candidate_next_gate"],
                    "mission_review",
                )
                self.assert_winning_signal(pulse, "mission_boundary_review")
                self.assertEqual(pulse["winning_candidate"]["priority_class"], "mission_boundary")
                self.assertEqual(pulse["winning_candidate"]["context"]["trigger"], trigger)

    def test_mission_pulse_before_continue_without_active_task_routes_to_mission_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            transition = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")
            self.assertEqual(transition.returncode, 0, transition.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "before_continue")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["snapshot"]["active_task"], None)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "mission_review")
        self.assertIn("active_node_missing", pulse["mission_pulse"]["signals"])
        self.assert_winning_signal(pulse, "active_node_missing")
        self.assertEqual(pulse["winning_candidate"]["priority_class"], "runtime_integrity")

    def test_mission_pulse_manual_without_active_task_routes_to_mission_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            transition = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")
            self.assertEqual(transition.returncode, 0, transition.stderr)

            pulse = self.assert_pulse_read_only(mission_dir)

        self.assertEqual(pulse["snapshot"]["active_task"], None)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "mission_review")
        self.assert_pulse_v2_contract(pulse)
        self.assert_winning_signal(pulse, "active_node_missing")

    def test_mission_pulse_routes_feedback_trigger_to_loopback(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            feedback = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "feedback",
                "--task-id",
                "T1",
                "--summary",
                "User says the current definition missed the global review problem.",
            )
            self.assertEqual(feedback.returncode, 0, feedback.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "feedback", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "loopback")
        self.assertEqual(pulse["gate_owner"], "loopback_hook")
        self.assertIn("user_feedback", pulse["mission_pulse"]["signals"])
        self.assert_winning_signal(pulse, "user_feedback")
        candidate = self.candidate_by_signal(pulse, "user_feedback")
        self.assert_pulse_candidate_contract(
            candidate,
            candidate_next_gate="loopback",
            priority_class="current_blocker_or_feedback",
            source_kind="evidence_event",
            source_ids=["E1"],
            freshness="current_path",
        )

    def test_mission_pulse_routes_failure_interruption_and_surprise_to_mission_review(self):
        for event_type in ("failure", "interruption", "surprise"):
            with self.subTest(event_type=event_type):
                with tempfile.TemporaryDirectory() as tmp:
                    mission_dir = create_mission(tmp)
                    event = run_script(
                        "record_evidence.py",
                        str(mission_dir),
                        "--event-type",
                        event_type,
                        "--task-id",
                        "T1",
                        "--summary",
                        f"{event_type} changed the Mission path.",
                    )
                    self.assertEqual(event.returncode, 0, event.stderr)

                    pulse = self.assert_pulse_read_only(mission_dir)

                self.assert_pulse_v2_contract(pulse)
                self.assertEqual(pulse["mission_pulse"]["next_gate"], "mission_review")
                self.assertIn("blocker_or_surprise", pulse["mission_pulse"]["signals"])
                self.assert_winning_signal(pulse, "blocker_or_surprise")
                self.assertEqual(pulse["winning_candidate"]["source_ids"], ["E1"])
                self.assertEqual(pulse["winning_candidate"]["priority_class"], "current_blocker_or_feedback")

    def test_mission_pulse_routes_blocker_trigger_to_mission_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            blocker = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "blocker",
                "--task-id",
                "T1",
                "--summary",
                "Current path cannot resolve the acceptance boundary.",
            )
            self.assertEqual(blocker.returncode, 0, blocker.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "blocker", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "mission_review")
        self.assertEqual(pulse["gate_owner"], "mission_review_gate")
        self.assertIn("blocker_or_surprise", pulse["mission_pulse"]["signals"])
        self.assert_winning_signal(pulse, "blocker_or_surprise")
        self.assertEqual(pulse["winning_candidate"]["source_ids"], ["E1"])

    def test_mission_pulse_stale_completed_task_blocker_does_not_preempt_branch_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            blocker = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "blocker",
                "--task-id",
                "T1",
                "--summary",
                "Earlier task hit a blocker before completion.",
            )
            self.assertEqual(blocker.returncode, 0, blocker.stderr)
            transition = run_script("transition_task.py", str(mission_dir), "--task-id", "T1", "--status", "completed")
            self.assertEqual(transition.returncode, 0, transition.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "branch_cleanup")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "selection")
        self.assertEqual(pulse["gate_owner"], "selection_hook")
        self.assertIn("branch_cleanup_candidate", pulse["mission_pulse"]["signals"])
        self.assert_winning_signal(pulse, "branch_cleanup_candidate")

    def test_mission_pulse_routes_checkpoint_batch_without_evidence_movement(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            for index in range(3):
                checkpoint = run_script(
                    "checkpoint.py",
                    str(mission_dir),
                    "--task-id",
                    "T1",
                    "--step-id",
                    "checkpoint",
                    "--log-summary",
                    f"Checkpoint {index + 1} moved implementation details only.",
                )
                self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "checkpoint_batch", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continuation_authorization")
        self.assertIn("weak_evidence_delta", pulse["mission_pulse"]["signals"])
        self.assertIn("checkpoint_batch_without_acceptance_evidence", pulse["mission_pulse"]["signals"])
        self.assert_winning_signal(pulse, "checkpoint_batch_without_acceptance_evidence")
        self.assert_pulse_candidate_contract(
            pulse["winning_candidate"],
            priority_class="checkpoint_weak_evidence_delta",
            source_kind="step_log",
            source_ids=["L1", "L2", "L3"],
            freshness="checkpoint_window",
        )

    def test_mission_pulse_checkpoint_batch_ignores_prior_unlinked_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "key_finding",
                "--task-id",
                "T1",
                "--summary",
                "Earlier local finding did not satisfy acceptance evidence.",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            for index in range(3):
                checkpoint = run_script(
                    "checkpoint.py",
                    str(mission_dir),
                    "--task-id",
                    "T1",
                    "--step-id",
                    "checkpoint",
                    "--log-summary",
                    f"Later checkpoint {index + 1} still moved only implementation detail.",
                )
                self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "checkpoint_batch")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continuation_authorization")
        self.assertIn("checkpoint_batch_without_acceptance_evidence", pulse["mission_pulse"]["signals"])
        self.assert_winning_signal(pulse, "checkpoint_batch_without_acceptance_evidence")
        self.assertEqual(pulse["winning_candidate"]["source_ids"], ["L1", "L2", "L3"])

    def test_mission_pulse_checkpoint_batch_treats_stale_linked_evidence_as_no_fresh_movement(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "key_finding",
                "--task-id",
                "T1",
                "--summary",
                "Earlier linked finding existed before the checkpoint batch.",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            mission = load_mission(mission_dir)
            mission["tasks"][0]["evidence_links"] = ["E1"]
            save_mission(mission_dir, mission)
            for index in range(3):
                checkpoint = run_script(
                    "checkpoint.py",
                    str(mission_dir),
                    "--task-id",
                    "T1",
                    "--step-id",
                    "checkpoint",
                    "--log-summary",
                    f"Later checkpoint {index + 1} moved implementation details only.",
                )
                self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "checkpoint_batch")

        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continuation_authorization")
        self.assert_pulse_v2_contract(pulse)
        self.assert_winning_signal(pulse, "checkpoint_batch_without_acceptance_evidence")

    def test_mission_pulse_checkpoint_batch_respects_linked_acceptance_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            for index in range(3):
                checkpoint = run_script(
                    "checkpoint.py",
                    str(mission_dir),
                    "--task-id",
                    "T1",
                    "--step-id",
                    "checkpoint",
                    "--log-summary",
                    f"Later checkpoint {index + 1} after linked evidence.",
                )
                self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr)
            evidence = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "key_finding",
                "--task-id",
                "T1",
                "--summary",
                "Fresh linked finding satisfies the current acceptance evidence.",
            )
            self.assertEqual(evidence.returncode, 0, evidence.stderr)
            mission = load_mission(mission_dir)
            mission["tasks"][0]["evidence_links"] = ["E1"]
            save_mission(mission_dir, mission)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "checkpoint_batch")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "continue")
        self.assertIsNone(pulse["winning_candidate"])
        self.assertFalse(pulse["review_trigger_candidates"])

    def test_mission_pulse_routes_branch_cleanup_to_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "branch_cleanup", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "selection")
        self.assertEqual(pulse["gate_owner"], "selection_hook")
        self.assertIn("branch_cleanup_candidate", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["branch_disposition"], "unclear")
        self.assertEqual(
            pulse["review_trigger_candidates"][0]["candidate_next_gate"],
            "selection",
        )
        self.assert_winning_signal(pulse, "branch_cleanup_candidate")
        self.assertEqual(pulse["winning_candidate"]["source_kind"], "task")

    def test_mission_pulse_routes_active_switch_candidate_to_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "active_switch_candidate")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "selection")
        self.assertIn("branch_cleanup_candidate", pulse["mission_pulse"]["signals"])
        self.assert_winning_signal(pulse, "branch_cleanup_candidate")

    def test_mission_pulse_routes_requires_human_status_to_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            stop = run_script(
                "stop_report.py",
                str(mission_dir),
                "--task-id",
                "T1",
                "--summary",
                "Cannot continue without user authority.",
                "--current-goal",
                "Route an unclear authority boundary.",
                "--attempt",
                "Checked runtime state.",
                "--blocking-issue",
                "The acceptance authority is unclear.",
                "--why-cannot-continue-safely",
                "Continuing would invent acceptance criteria.",
                "--need-from-human",
                "Confirm the intended acceptance boundary.",
                "--resume-condition",
                "The user confirms the acceptance boundary.",
            )
            self.assertEqual(stop.returncode, 0, stop.stderr)

            result = run_script("mission_pulse.py", str(mission_dir), "--trigger", "before_freeze", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            pulse = json.loads(result.stdout)

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "stop")
        self.assertEqual(pulse["gate_owner"], "stop_report")
        self.assertIn("requires_human", pulse["mission_pulse"]["signals"])
        self.assertIn("authority_boundary_unclear", pulse["mission_pulse"]["signals"])
        self.assertEqual(pulse["mission_pulse"]["scope"], "mission")
        self.assert_winning_signal(pulse, "requires_human")
        self.assert_suppressed_signal(pulse, "mission_boundary_review")

    def test_mission_pulse_boundary_wins_over_shared_risk_but_preserves_suppressed_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            risk = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_evidence_channel",
                "--signal",
                "evidence_channel_untrusted_until_smoke_check",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "evidence_persistence",
                "--value-effect",
                "Future acceptance evidence may be invalid until the channel is checked.",
                "--recommended-gate",
                "health_check",
                "--recovery-condition",
                "Evidence channel smoke check passes.",
            )
            self.assertEqual(risk.returncode, 0, risk.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "before_freeze")

        self.assertEqual(pulse["mission_pulse"]["next_gate"], "mission_review")
        self.assert_pulse_v2_contract(pulse)
        self.assert_winning_signal(pulse, "mission_boundary_review")
        self.assert_suppressed_signal(pulse, "active_shared_risk")

    def test_mission_pulse_shared_risk_wins_over_before_continue_but_preserves_same_path_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            risk = run_script(
                "record_risk_context.py",
                str(mission_dir),
                "record",
                "--task-id",
                "T1",
                "--scope",
                "shared_evidence_channel",
                "--signal",
                "evidence_channel_untrusted_until_smoke_check",
                "--severity",
                "high",
                "--confidence",
                "high",
                "--affected-surface",
                "evidence_persistence",
                "--value-effect",
                "Future acceptance evidence may be invalid until the channel is checked.",
                "--recommended-gate",
                "health_check",
                "--recovery-condition",
                "Evidence channel smoke check passes.",
            )
            self.assertEqual(risk.returncode, 0, risk.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "before_continue")

        self.assert_pulse_v2_contract(pulse)
        self.assertEqual(pulse["mission_pulse"]["next_gate"], "health_check")
        self.assert_winning_signal(pulse, "active_shared_risk")
        self.assert_suppressed_signal(pulse, "same_path_continuation")

    def test_mission_pulse_feedback_wins_over_anti_spiral_but_preserves_anti_spiral_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir = create_mission(tmp)
            feedback = run_script(
                "record_evidence.py",
                str(mission_dir),
                "--event-type",
                "feedback",
                "--task-id",
                "T1",
                "--summary",
                "User says the current definition missed the global review problem.",
            )
            self.assertEqual(feedback.returncode, 0, feedback.stderr)
            for index in range(3):
                result = run_script(
                    "record_step_log.py",
                    str(mission_dir),
                    "--task-id",
                    "T1",
                    "--step-id",
                    f"repair-{index + 1}",
                    "--summary",
                    f"Adjusted the same local prompt section {index + 1}.",
                    "--payload-json",
                    '{"object_id": "prompt:section-a", "change_kind": "add_layer"}',
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            pulse = self.assert_pulse_read_only(mission_dir, "--trigger", "feedback")

        self.assertEqual(pulse["mission_pulse"]["next_gate"], "loopback")
        self.assert_pulse_v2_contract(pulse)
        self.assert_winning_signal(pulse, "user_feedback")
        self.assert_suppressed_signal(pulse, "third_touch")


if __name__ == "__main__":
    unittest.main()
