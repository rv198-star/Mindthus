import importlib.util
import json
import subprocess
import unittest
from copy import deepcopy
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check-test-lifecycle.py"
REGISTRY = REPO / "tests" / "test-lifecycle-registry.json"
POLICY = REPO / "docs" / "internal" / "test-lifecycle-policy.md"
REVIEW = REPO / "docs" / "internal" / "test-lifecycle-review-2026-08-06.md"
CLEANUP = REPO / "docs" / "internal" / "test-lifecycle-cleanup-wave-1-2026-08-06.md"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_test_lifecycle", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestLifecycleTests(unittest.TestCase):
    def test_registry_covers_every_executable_test_once(self):
        checker = load_checker()
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))

        report = checker.validate_registry(data, REPO)

        self.assertEqual(report["status"], "valid", report["findings"])
        self.assertEqual(
            report["registered_executable_test_file_count"],
            report["executable_test_file_count"],
        )
        self.assertEqual(report["review_candidate_count"], 0)
        self.assertIn("historical_guard", report["gating_states"])

    def test_registry_validator_rejects_unregistered_test(self):
        checker = load_checker()
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        mutated = deepcopy(data)
        target = "tests/test_case_export.py"
        for entry in mutated["entries"]:
            if target in entry.get("paths", []):
                entry["paths"].remove(target)

        report = checker.validate_registry(mutated, REPO)

        self.assertEqual(report["status"], "invalid")
        self.assertTrue(
            any(item["code"] == "unregistered-test" and target in item["message"] for item in report["findings"])
        )

    def test_cli_reports_valid_registry(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--json"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["registered_executable_test_file_count"], report["executable_test_file_count"])

    def test_policy_names_gating_and_new_test_contract(self):
        policy = POLICY.read_text(encoding="utf-8")
        review = REVIEW.read_text(encoding="utf-8")
        cleanup = CLEANUP.read_text(encoding="utf-8")

        for phrase in (
            "active_gate",
            "active_regression",
            "historical_guard",
            "operationally gating today",
            "must update the registry in the same change",
            "protected invariant or failure class",
        ):
            self.assertIn(phrase, policy)
        for phrase in (
            "tests/test_v0_9_acceptance.py",
            "candidate_archive",
            "keep it as `historical_guard` for now",
            "No executable test was safely archived in this initial review",
        ):
            self.assertIn(phrase, review)
        for phrase in (
            "Test Lifecycle Cleanup Wave 1",
            "test_public_docs_preserve_v0_9_history_and_name_v1_0_release_surface",
            "Replacement Ownership",
            "remains `historical_guard`",
            "No test file is deleted in Wave 1",
        ):
            self.assertIn(phrase, cleanup)


if __name__ == "__main__":
    unittest.main()
