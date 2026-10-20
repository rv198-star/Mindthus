"""Q1 uses the real pinned runtime, only with disposable synthetic Missions."""
import concurrent.futures
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "tplan" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from query_runtime import (PROTOCOL, MAX_SOURCE_BYTES, QueryError, parse_request, query)
from tplan_runtime import begin_interaction_guard, runtime_fingerprint


def files(directory):
    return {str(p.relative_to(directory)): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in directory.rglob("*") if p.is_file() and p.name != ".execution_trace.lock"}


class QueryRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="tplan-query-q1-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mission = self.root / "q1-fixture"
        tasks = self.root / "tasks.json"
        tasks.write_text(json.dumps([{"id": "T1", "title": "Observe fixture",
            "role": "success-critical", "mission_contribution": "Verify the Q1 contract",
            "acceptance_evidence": ["A1"]}]))
        result = self.script("init_mission.py", "--dir", str(self.mission),
                             "--mission-id", "q1-fixture", "--title", "Synthetic Q1",
                             "--objective", "Verify observation-only queries",
                             "--acceptance-evidence", "A1:Snapshot stays read-only",
                             "--task-json", str(tasks))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.request = {"protocol": PROTOCOL, "action": "snapshot.get",
                        "request_id": "query-1", "mission_id": "q1-fixture"}

    def script(self, name, *args):
        return subprocess.run([sys.executable, "-B", str(SCRIPTS / name), *args],
                              capture_output=True, text=True, timeout=15)

    def cli(self, request=None):
        raw = json.dumps(request or self.request)
        return subprocess.run([sys.executable, "-B", "-I", str(SCRIPTS / "query_runtime.py"),
                               "--mission-dir", str(self.mission), "--request-json", raw],
                              capture_output=True, text=True, timeout=15)

    def assert_readonly(self, operation):
        before = files(self.mission)
        result = operation()
        self.assertEqual(before, files(self.mission))
        return result

    def test_real_cli_and_function_return_identical_observation(self):
        value, status = self.assert_readonly(lambda: query(self.mission, self.request))
        result = self.assert_readonly(self.cli)
        self.assertEqual(status, 0)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(value, json.loads(result.stdout))
        self.assertEqual(value["data"]["authority"], "observation_only")
        self.assertFalse(value["data"]["command_result_store"])
        self.assertNotIn("skill_root", value["data"]["runtime"])
        self.assertNotIn("events", value["data"])

    def test_pending_transaction_is_not_recovered_or_parsed(self):
        transaction = self.mission / ".mission-transaction.json"
        transaction.write_text('{"prepared":"not a real transaction"}')
        result = self.assert_readonly(self.cli)
        self.assertEqual(result.returncode, 4)
        self.assertEqual(json.loads(result.stdout)["code"], "recovery_required")
        self.assertTrue(transaction.exists())

    def test_guard_is_observed_without_removal_or_message_exposure(self):
        begin_interaction_guard(self.mission, platform="codex", message_ref="private-message-ref")
        result = self.assert_readonly(self.cli)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(json.loads(result.stdout)["data"]["interaction_guard"]["present"])
        self.assertNotIn("private-message-ref", result.stdout)

    def test_missing_directory_is_not_created(self):
        missing = self.root / "does-not-exist"
        result, status = query(missing, self.request)
        self.assertEqual(status, 6)
        self.assertEqual(result["code"], "mission_unavailable")
        self.assertFalse(missing.exists())

    def test_missing_mission_does_not_create_lock(self):
        empty = self.root / "empty"
        empty.mkdir()
        _, status = query(empty, self.request)
        self.assertEqual(status, 6)
        self.assertEqual(list(empty.iterdir()), [])

    def test_runtime_mismatch_refuses_without_repinning(self):
        path = self.mission / "mission.json"
        state = json.loads(path.read_text())
        state["runtime_provenance"]["fingerprint"]["build_hash"] = "sha256:" + "0" * 64
        path.write_text(json.dumps(state))
        result = self.assert_readonly(self.cli)
        self.assertEqual(result.returncode, 5)
        self.assertEqual(json.loads(result.stdout)["code"], "runtime_mismatch")

    def test_host_expected_build_hash_is_checked(self):
        bad = {**self.request, "expected_build_hash": "sha256:" + "0" * 64}
        value, status = self.assert_readonly(lambda: query(self.mission, bad))
        self.assertEqual((status, value["code"]), (5, "runtime_mismatch"))
        good = {**self.request, "expected_build_hash": runtime_fingerprint()["build_hash"]}
        self.assertEqual(query(self.mission, good)[1], 0)

    def test_legacy_unpinned_remains_unpinned(self):
        path = self.mission / "mission.json"
        state = json.loads(path.read_text())
        state.pop("runtime_provenance")
        path.write_text(json.dumps(state))
        result = self.assert_readonly(self.cli)
        self.assertEqual(result.returncode, 0, result.stdout)
        current = json.loads(result.stdout)["data"]["runtime"]
        self.assertEqual(current["compatibility"], "legacy_unpinned")
        self.assertIsNone(current["compatible"])
        self.assertNotIn("runtime_provenance", json.loads(path.read_text()))

    def test_command_get_unsupported_does_not_create_result_store(self):
        request = {**self.request, "action": "command.get", "command_id": "cmd-1"}
        value, status = self.assert_readonly(lambda: query(self.mission, request))
        self.assertEqual((status, value["code"]), (3, "unsupported_capability"))
        self.assertIsNone(value["data"])

    def test_invalid_request_shapes_and_duplicate_json_keys(self):
        variants = [[], {**self.request, "protocol": "wrong"},
                    {**self.request, "action": "decision.apply"},
                    {**self.request, "extra": "ignored?"},
                    {**self.request, "mission_id": "../escape"},
                    {**self.request, "command_id": "not-valid-for-snapshot"},
                    {**self.request, "expected_build_hash": 42}]
        for value in variants:
            with self.subTest(value=value):
                with self.assertRaises(QueryError):
                    parse_request(json.dumps(value))
        for raw in ['{"protocol":"a","protocol":"b"}', 'NaN', '{broken', '"' + 'x'*17000 + '"']:
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(QueryError):
                    parse_request(raw)

    def test_mismatched_id_and_corrupt_state_are_not_success(self):
        value, status = query(self.mission, {**self.request, "mission_id": "another"})
        self.assertEqual((status, value["code"]), (7, "invalid_state"))
        (self.mission / "mission.json").write_text('{broken')
        result = self.assert_readonly(self.cli)
        self.assertEqual(result.returncode, 7)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_symlink_mission_and_state_are_rejected(self):
        alias = self.root / "alias"
        alias.symlink_to(self.mission, target_is_directory=True)
        self.assertEqual(query(alias, self.request)[1], 6)
        evidence = self.mission / "evidence.jsonl"
        saved = self.root / "evidence-saved"
        evidence.rename(saved)
        evidence.symlink_to(saved)
        self.assertEqual(query(self.mission, self.request)[1], 6)

    def test_response_and_source_bounds_return_explicit_error(self):
        with patch("query_runtime.MAX_RESPONSE_BYTES", 100):
            value, status = query(self.mission, self.request)
        self.assertEqual((status, value["code"]), (10, "snapshot_too_large"))
        with (self.mission / "evidence.jsonl").open("wb") as handle:
            handle.truncate(MAX_SOURCE_BYTES + 1)
        result = self.assert_readonly(self.cli)
        self.assertEqual(result.returncode, 10)

    def test_parallel_real_queries_and_official_evidence_writer(self):
        # Concurrency here uses the official writer, not an independent JSON writer.
        def write_event(i):
            result = self.script("record_evidence.py", str(self.mission),
                                 "--event-type", "observation", "--summary", f"Synthetic {i}")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("recorded_evidence:", result.stdout)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(write_event, i) if i % 3 == 0 else pool.submit(self.cli)
                       for i in range(9)]
            for future in futures:
                result = future.result()
                if result is not None:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    data = json.loads(result.stdout)["data"]
                    self.assertEqual(data["mission"]["id"], "q1-fixture")
        final = json.loads(self.cli().stdout)["data"]
        self.assertEqual(final["evidence_count"], 3)

    def test_new_facade_does_not_change_legacy_runtime_fingerprint(self):
        manifest = json.loads((SCRIPTS.parent / "resources" / "runtime-manifest.json").read_text())
        self.assertNotIn("scripts/query_runtime.py", manifest["fingerprint_files"])
        # Existing CLI and unchanged manifest remain the writer contract.
        self.assertEqual(runtime_fingerprint()["package_version"], "1.5.4")


if __name__ == "__main__":
    unittest.main()
