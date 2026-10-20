"""H1-A contract tests: opt-in scoped pending decisions and legacy-writer vetoes.

Synthetic Missions only. No Owner authority or external dispatch is implemented.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tplan_runtime as runtime


def cli(script, *args):
    return subprocess.run([sys.executable, "-B", str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True, timeout=20)


class H1KernelGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mindthus-h1-gate-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mission = self.root / "h1-case"
        tasks = [
            {"id": i, "title": i, "role": "success-critical",
             "mission_contribution": "Synthetic task", "acceptance_evidence": ["A1"]}
            for i in ("A", "B", "C")
        ]
        task_path = self.root / "tasks.json"
        task_path.write_text(json.dumps(tasks))
        self.options = ["--dir", self.mission, "--mission-id", "h1-case",
                        "--title", "H1 gate fixture", "--objective", "Preserve business authority",
                        "--acceptance-evidence", "A1:H1 gate test", "--task-json", task_path]

    def create(self, scoped=True):
        r = cli("init_mission.py", *self.options,
                *(['--command-results', '--human-control'] if scoped else []))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return runtime.read_mission(self.mission)

    def put_pending(self):
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        after["human_control"]["requests"]["HR1"] = {
            "business_task_id": "A", "blocked_task_ids": ["B"], "status": "pending",
            "revision": 1, "required_actor": "owner",
            "allowed_choices": ["approve_current", "request_changes", "withdraw_change"],
            "current_candidate_id": None, "current_decision_id": None}
        # Internal test-only capability; no CLI/Worker/Host signing API in H1-A.
        with runtime.execution_trace_lock(self.mission):
            runtime._commit_mission_state_unlocked(
                self.mission, before, after,
                source={"kind": "runtime_script", "name": "h1-fixture-pending"},
                h1_control_authority=runtime._H1_CONTROL_AUTHORITY)
        return runtime.read_mission(self.mission)

    def test_explicit_new_mission_opt_in_only(self):
        state = self.create()
        self.assertEqual(state["human_control"]["schema_version"], "tplan.h1.v0.1")
        self.assertEqual(state["human_control"]["requests"], {})
        self.assertEqual(state["command_results"]["records"], {})
        self.assertIn("task_scoped_owner_gate", runtime.runtime_fingerprint()["capabilities"])

    def test_h1_requires_q2_opt_in_not_implicit_upgrade(self):
        response = cli("init_mission.py", *self.options, "--human-control")
        self.assertNotEqual(response.returncode, 0)
        self.assertFalse(self.mission.joinpath("mission.json").exists())
        self.assertIn("H1 requires", response.stderr)

    def test_h1_module_is_in_required_runtime_fingerprint(self):
        manifest = json.loads((SCRIPTS.parent / "resources/runtime-manifest.json").read_text())
        self.assertEqual(manifest["source_id"], "mindthus-tplan-h1a-candidate")
        self.assertIn("task_scoped_owner_gate", manifest["capabilities"])
        for field in ("required_scripts", "fingerprint_files"):
            self.assertIn("scripts/tplan_h1.py", manifest[field])

    def test_non_opt_in_uses_prior_shape(self):
        state = self.create(scoped=False)
        self.assertNotIn("human_control", state)
        self.assertNotIn("command_results", state)

    def test_pending_blocks_B_but_C_status_and_observation_continue(self):
        self.create(); self.put_pending()
        runtime.transition_task_status(self.mission, "C", "active")
        e = runtime.append_event(self.mission, {
            "event_type": "observation", "task_id": "C", "summary": "C independent"})
        self.assertEqual(e["task_id"], "C")
        self.assertEqual(runtime.read_mission(self.mission)["tasks"][2]["status"], "active")
        with self.assertRaisesRegex(runtime.TplanError, "H1|human"):
            runtime.transition_task_status(self.mission, "B", "active")

    def test_pending_parent_also_blocks_descendant_but_not_C(self):
        self.create()
        runtime.add_task_node(self.mission, {
            "id": "B.1", "parent_id": "B", "title": "Worker subtask",
            "role": "supporting", "parent_contribution": "Continue B only when approved",
            "parent_acceptance": "Parent approves this result", "mission_trace": "via B"})
        self.put_pending()
        with self.assertRaisesRegex(runtime.TplanError, "H1"):
            runtime.transition_task_status(self.mission, "B.1", "active")
        with self.assertRaisesRegex(runtime.TplanError, "H1"):
            runtime.append_event(self.mission, {
                "event_type": "acceptance_passed", "task_id": "B.1",
                "summary": "Faked subtask approval", "payload": {"acceptance_ids": ["A1"]}})
        self.assertIn("B.1", runtime.read_mission(self.mission)["tasks"][-1]["id"])
        runtime.transition_task_status(self.mission, "C", "active")

    def test_cannot_reparent_pending_subtask_outside_gate(self):
        self.create()
        runtime.add_task_node(self.mission, {
            "id": "B.1", "parent_id": "B", "title": "Subtask",
            "role": "supporting", "parent_contribution": "Follows B",
            "parent_acceptance": "Parent checks output", "mission_trace": "via B"})
        self.put_pending()
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        child = next(t for t in after["tasks"] if t["id"] == "B.1")
        child["parent_id"] = "C"
        child["status"] = "active"
        after["active_task_id"] = "B.1"
        with self.assertRaisesRegex(runtime.TplanError, "H1"):
            runtime.commit_mission_state(self.mission, before, after,
                source={"kind": "runtime_script", "name": "reparent-bypass"})
        self.assertEqual(runtime.read_mission(self.mission), before)

    def test_historical_acceptance_remains_readable_after_new_pending(self):
        self.create()
        original = runtime.append_event(self.mission, {
            "event_type": "acceptance_passed", "task_id": "B",
            "summary": "Historical before new request", "payload": {"acceptance_ids": ["A1"]}})
        self.put_pending()
        from query_runtime import query
        build = runtime.runtime_fingerprint()["build_hash"]
        request = {"protocol": "tplan.query.v1", "action": "snapshot.get",
                   "request_id": "h1-historical", "mission_id": "h1-case",
                   "expected_build_hash": build}
        before = self.mission.joinpath("evidence.jsonl").read_bytes()
        result, exit_code = query(self.mission, request)
        self.assertEqual(exit_code, 0, result)
        self.assertEqual(result["data"]["mission"]["id"], "h1-case")
        self.assertEqual(before, self.mission.joinpath("evidence.jsonl").read_bytes())
        with self.assertRaisesRegex(runtime.TplanError, "H1"):
            runtime.append_event(self.mission, {
                "event_type": "acceptance_passed", "task_id": "B",
                "summary": "New forged approval", "payload": {"acceptance_ids": ["A1"]}})
        self.assertEqual(original["event_type"], "acceptance_passed")

    def test_legacy_writer_cannot_point_active_focus_at_pending_B(self):
        self.create(); self.put_pending()
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        after["active_task_id"] = "B"
        with self.assertRaisesRegex(runtime.TplanError, "H1"):
            runtime.commit_mission_state(self.mission,before,after,
                source={"kind":"runtime_script","name":"focus-bypass"})
        self.assertEqual(runtime.read_mission(self.mission),before)

    def test_null_human_control_is_not_an_opt_in_and_cannot_close(self):
        self.create(scoped=False)
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        after["human_control"] = None
        self.assertTrue(runtime.validate_mission(after))
        with self.assertRaises(runtime.TplanError):
            runtime.commit_mission_state(self.mission,before,after,
                source={"kind":"runtime_script","name":"null-injection"})
        self.assertEqual(runtime.read_mission(self.mission),before)

    def test_non_h1_malformed_state_uses_prior_validator_without_h1_crash(self):
        self.create(scoped=False)
        before = runtime.read_mission(self.mission)
        for mutation in (
            lambda s: s.__setitem__("active_task_id", []),
            lambda s: s["tasks"][1].__setitem__("id", []),
        ):
            after = copy.deepcopy(before); mutation(after)
            with self.subTest(mutation=mutation):
                with self.assertRaises(runtime.TplanError):
                    runtime.commit_mission_state(self.mission, before, after,
                        source={"kind":"runtime_script","name":"malformed-snapshot"})
        self.assertEqual(runtime.read_mission(self.mission), before)

    def test_malformed_h1_request_is_invalid_without_crashing(self):
        self.create(); self.put_pending()
        base = runtime.read_mission(self.mission)
        cases = [
            ("business_task_id", []),
            ("blocked_task_ids", [{}]),
            ("status", {}),
            ("allowed_choices", [{}]),
            ("revision", True),
        ]
        for field, raw in cases:
            altered = copy.deepcopy(base)
            altered["human_control"]["requests"]["HR1"][field] = raw
            with self.subTest(field=field):
                self.assertTrue(runtime.validate_mission(altered))

    def test_untrusted_writer_cannot_remove_or_change_h1_objects(self):
        self.create(); self.put_pending()
        before = runtime.read_mission(self.mission)
        for mutate in (
            lambda x: x.pop("human_control"),
            lambda x: x["human_control"]["requests"].clear(),
            lambda x: x["tasks"].__setitem__(1, {**x["tasks"][1], "role": "normal"}),
            lambda x: x["tasks"].__delitem__(1),
            lambda x: x["mission"].__setitem__("status", "completed"),
        ):
            after = copy.deepcopy(before);mutate(after)
            with self.subTest(mutate=mutate):
                with self.assertRaises(runtime.TplanError):
                    runtime.commit_mission_state(self.mission,before,after,
                        source={"kind":"runtime_script","name":"untrusted-legacy"})
        self.assertEqual(runtime.read_mission(self.mission),before)

    def test_untrusted_qualified_acceptance_cannot_approve_B(self):
        self.create();self.put_pending()
        events_before = self.mission.joinpath("evidence.jsonl").read_bytes()
        with self.assertRaisesRegex(runtime.TplanError, "H1|human"):
            runtime.append_event(self.mission,{"event_type":"acceptance_passed",
                "task_id":"B","summary":"fake","payload":{"acceptance_ids":["A1"]}})
        self.assertEqual(events_before, self.mission.joinpath("evidence.jsonl").read_bytes())

    def test_legacy_task_approval_and_mission_complete_stay_blocked(self):
        self.create(); self.put_pending()
        before = runtime.read_mission(self.mission)
        after = copy.deepcopy(before)
        after["tasks"][1]["status"] = "completed"
        with self.assertRaises(runtime.TplanError):
            runtime.commit_mission_state(self.mission,before,after,source={"kind":"runtime_script","name":"fake"})
        after = copy.deepcopy(before)
        after["mission"]["status"] = "completed"
        with self.assertRaises(runtime.TplanError):
            runtime.commit_mission_state(self.mission,before,after,source={"kind":"runtime_script","name":"fake"})
        self.assertEqual(runtime.read_mission(self.mission),before)


if __name__ == "__main__":
    unittest.main()
