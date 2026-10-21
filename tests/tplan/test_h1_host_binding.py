"""Isolated Host bootstrap API contract, not proof of OS or Owner isolation.

Only synthetic trust is used. Unlike legacy H1 fixtures, these tests do not
patch the disabled trust seam: they exercise the explicit boot-bound writer.
"""
import base64
import copy
import hashlib
import hmac
import shutil
import unittest
from pathlib import Path

from tests.tplan import test_h1_kernel_gate as fixtures
from tests.tplan.h1_test_host import (
    TEST_TRUST, host_request, owner_receipt, acceptance_receipt)
from tplan_commands import canonical
import tplan_h1_commands as api
import tplan_runtime as runtime


class H1HostBindingTests(unittest.TestCase):
    def setUp(self):
        case = fixtures.H1KernelGateTests("test_explicit_new_mission_opt_in_only")
        case.setUp()
        self.addCleanup(case.doCleanups)
        case.create()
        self.root, self.mission = case.root, case.mission
        self.config = copy.deepcopy(TEST_TRUST)
        self.counter = 0

    def snapshot(self):
        return {name: (self.mission / name).read_bytes()
                for name in ("mission.json", "evidence.jsonl", "execution_trace.jsonl")}

    def request(self, action="candidate.submit", payload=None, **changes):
        self.counter += 1
        body = {"protocol": api.PROTOCOL, "action": action, "mission_id": "h1-case",
                "command_id": "bound-command-" + str(self.counter),
                "expected_build_hash": runtime.runtime_fingerprint()["build_hash"],
                "payload": payload or {"task_id": "A", "attempt_ref": "A-1",
                    "content_b64": base64.b64encode(b"actual source A").decode()}}
        body.update(changes)
        return host_request(body)

    def call(self, writer, action, payload):
        envelope, code = writer(self.request(action, payload))
        self.assertEqual(code, 0, envelope)
        self.assertEqual(envelope["status"], "committed", envelope)
        return envelope["data"]

    def test_01_explicit_binding_uses_canonical_writer_and_replay(self):
        writer = api.bind_host_writer(self.mission, self.config)
        request = self.request()
        result, code = writer(request)
        self.assertEqual((code, result["status"]), (0, "committed"), result)
        state = runtime.read_mission(self.mission)
        self.assertEqual(state["human_control"]["candidates"][result["data"]["candidate_id"]],
                         result["data"])
        before = self.snapshot()
        again, code = writer(request)
        self.assertEqual((code, again["status"]), (0, "replayed"), again)
        self.assertEqual(again["data"], result["data"])
        self.assertEqual(self.snapshot(), before)

    def test_02_binding_never_enables_ordinary_entry(self):
        before = self.snapshot()
        writer = api.bind_host_writer(self.mission, self.config)
        self.assertEqual(self.snapshot(), before)
        self.assertIsNone(api._trust_config())
        result, code = api.execute(self.mission, self.request())
        self.assertEqual((code, result["code"]), (2, "host_disabled"), result)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(writer(self.request())[1], 0)
        self.assertIsNone(api._trust_config())

    def test_03_original_configuration_cannot_change_bound_key_or_owner(self):
        writer = api.bind_host_writer(self.mission, self.config)
        self.config["mission_id"] = "other"
        self.config["issuer_id"] = "other-host"
        self.config["key_id"] = "other-key"
        self.config["key"] = b"different-secret-not-the-bound-key!"
        self.config["owner_subject_ref"] = "other-owner"
        self.config["origin_binding_ref"] = "other-binding"
        self.config["origin_session_ref"] = "other-session"
        candidate = self.call(writer, "candidate.submit", self.request()["payload"])
        self.call(writer, "decision.open", {"request_id": "HR1", "business_task_id": "A",
            "blocked_task_ids": ["B"], "candidate_id": candidate["candidate_id"]})
        result = self.call(writer, "decision.apply", {"receipt": owner_receipt("h1-case",
            candidate_sha256=candidate["content_sha256"])})
        self.assertTrue(result["owner_decision_committed"])
        request = self.request("command.get", {"command_id": "missing"})
        unsigned = {k: v for k, v in request["host_receipt"].items() if k != "signature"}
        request["host_receipt"]["signature"] = hmac.new(
            self.config["key"], canonical(unsigned).encode(), hashlib.sha256).hexdigest()
        before = self.snapshot()
        result, code = writer(request)
        self.assertEqual((code, result["code"]), (2, "unauthorized"), result)
        self.assertEqual(self.snapshot(), before)

    def test_04_nested_reviewer_scope_is_frozen_through_canonical_completion(self):
        writer = api.bind_host_writer(self.mission, self.config)
        self.config["acceptance_actors"]["B"]["actor_subject_ref"] = "worker"
        self.config["acceptance_actors"]["B"]["origin_binding_ref"] = "worker-binding"
        self.config["acceptance_actors"]["B"]["origin_session_ref"] = "worker-session"
        self.config["acceptance_actors"].clear()
        source = self.call(writer, "candidate.submit", self.request()["payload"])
        runtime.record_work_plan(self.mission, {"schema_version": "tplan.work_plan.v0.1",
            "coverage": "complete", "scope_note": "Bound writer synthetic A before B",
            "blocks": [{"task_id": "A", "depends_on": []},
                       {"task_id": "B", "depends_on": ["A"]},
                       {"task_id": "C", "depends_on": []}]})
        runtime.transition_task_status(self.mission, "A", "completed")
        runtime.append_event(self.mission, {"event_type": "acceptance_passed", "task_id": "A",
            "summary": "Synthetic acceptance of actual source bytes",
            "payload": {"acceptance_ids": ["A1"], "candidate_sha256": source["content_sha256"],
                        "attempt_ref": source["attempt_ref"]}})
        self.call(writer, "decision.open", {"request_id": "HR1", "business_task_id": "A",
            "blocked_task_ids": ["B"], "candidate_id": source["candidate_id"]})
        self.call(writer, "decision.apply", {"receipt": owner_receipt("h1-case",
            candidate_sha256=source["content_sha256"])})
        self.call(writer, "adoption.apply", {"request_id": "HR1", "candidate_id": source["candidate_id"]})
        slot = self.call(writer, "execution.claim", {"task_id": "B", "request_id": "HR1",
            "expected_revision": 2, "input_digest": "sha256:" + "a" * 64})
        self.call(writer, "result.record", {"slot_id": slot["slot_id"], "session_id": slot["session_id"],
            "native_request_id": slot["native_request_id"], "attempt_ref": slot["intent_id"],
            "receipt_ref": "bound-delivery", "content_b64": base64.b64encode(b"real B result").decode()})
        state = runtime.read_mission(self.mission)
        slot = state["human_control"]["execution_slots"][slot["slot_id"]]
        receipt = acceptance_receipt(state, slot)
        result = self.call(writer, "task.complete", {"receipt": receipt})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(runtime.find_task(runtime.read_mission(self.mission), "B")["status"], "completed")

    def test_05_invalid_configuration_never_mutates_mission(self):
        cases = [None, {}, {**self.config, "extra": "not-a-capability"}]
        for field in self.config:
            value = copy.deepcopy(self.config)
            del value[field]
            cases.append(value)
        for field in ("issuer_id", "key_id", "owner_subject_ref", "origin_binding_ref", "origin_session_ref"):
            for value in (None, "", " ", "bad\nref", "bad\x00ref", "x" * 2049, "\ud800"):
                cases.append({**self.config, field: value})
        for value in (b"short", "a" * 32, bytearray(b"a" * 32), b"a" * 129):
            cases.append({**self.config, "key": value})
        for value in ("wrong-mission", "../escape", False):
            cases.append({**self.config, "mission_id": value})
        for value in (None, [], {"missing-task": self.config["acceptance_actors"]["B"]},
                      {"B": {"actor_subject_ref": "reviewer"}},
                      {"B": {**self.config["acceptance_actors"]["B"], "extra": "no"}},
                      {"B": {**self.config["acceptance_actors"]["B"], "origin_session_ref": ""}}):
            cases.append({**self.config, "acceptance_actors": value})
        before = self.snapshot()
        for index, config in enumerate(cases):
            with self.subTest(index=index):
                with self.assertRaises(ValueError):
                    api.bind_host_writer(self.mission, config)
                self.assertEqual(self.snapshot(), before)

    def test_06_fixed_mission_and_request_only_callable(self):
        writer = api.bind_host_writer(self.mission, self.config)
        before = self.snapshot()
        result, code = writer(self.request(mission_id="other-mission"))
        self.assertEqual((code, result["code"]), (2, "unauthorized"), result)
        result, code = writer(self.request(directory=str(self.root / "other")))
        self.assertEqual((code, result["code"]), (2, "invalid_request"), result)
        with self.assertRaises(TypeError):
            writer(self.mission, self.request())
        with self.assertRaises(TypeError):
            writer(self.request(), config=self.config)
        self.assertEqual(self.snapshot(), before)

    def test_07_canonical_absolute_directory_required(self):
        link = self.root / "alias"
        link.symlink_to(self.mission, target_is_directory=True)
        parent_link = self.root / "parent-alias"
        parent_link.symlink_to(self.root, target_is_directory=True)
        before = self.snapshot()
        for directory in (Path("h1-case"), link, parent_link / "h1-case", self.root / "missing",
                          self.mission / ".." / "h1-case"):
            with self.subTest(directory=str(directory)):
                with self.assertRaises(ValueError):
                    api.bind_host_writer(directory, self.config)
                self.assertEqual(self.snapshot(), before)

    def test_08_replaced_directory_does_not_rebind(self):
        writer = api.bind_host_writer(self.mission, self.config)
        before = self.snapshot()
        moved = self.root / "original"
        self.mission.rename(moved)
        shutil.copytree(moved, self.mission)
        result, code = writer(self.request())
        self.assertEqual((code, result["code"]), (2, "mission_unavailable"), result)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual({name: (moved / name).read_bytes() for name in before}, before)


if __name__ == "__main__":
    unittest.main()
