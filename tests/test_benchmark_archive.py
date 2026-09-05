"""Archive invariants use tiny local Git fixtures; CI never fetches historical runs."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from benchmark_archive import git, inventory, safe_path, verify_manifest


class BenchmarkArchiveTests(unittest.TestCase):
    def setUp(self):
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.repo = Path(holder.name)
        self.scope = "docs/benchmarks/runs/fixture/repeat-1"
        root = self.repo / self.scope
        (root / "events").mkdir(parents=True)
        (root / "summary.json").write_text('{"status":"diagnostic"}\n', encoding="utf-8")
        (root / "events" / "case.jsonl").write_text('{"record":"historical"}\n', encoding="utf-8")
        git(self.repo, "init", "-q")
        git(self.repo, "add", ".")
        git(self.repo, "-c", "user.name=Archive Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-qm", "source")
        self.source = git(self.repo, "rev-parse", "HEAD").decode().strip()
        self.manifest = {"source_commit": self.source, "scope": self.scope, "files": [
            {"path": row["path"][len(self.scope)+1:], "blob_oid": row["blob_oid"], "bytes": row["bytes"],
             "disposition": "migrate" if "/events/" in row["path"] else "keep", "reason": "Fixture classification"}
            for row in inventory(self.repo, self.source, self.scope)]}

    def test_recovery_verifies_all_bytes_without_mutating_checkout(self):
        before = {str(p.relative_to(self.repo)): p.read_bytes() for p in (self.repo / self.scope).rglob("*") if p.is_file()}
        result = verify_manifest(self.repo, self.manifest)
        self.assertEqual(result["restored_files"], 2)
        self.assertEqual(result["migrate_files"], 1)
        self.assertEqual(result["migrate_bytes"], len(b'{"record":"historical"}\n'))
        self.assertFalse(result["checkout_mutated"])
        self.assertEqual(before, {str(p.relative_to(self.repo)): p.read_bytes() for p in (self.repo / self.scope).rglob("*") if p.is_file()})

    def test_incomplete_duplicate_or_corrupt_manifest_is_rejected(self):
        mutations = [lambda m: m["files"].pop(),
                     lambda m: m["files"].append(copy.deepcopy(m["files"][0])),
                     lambda m: m["files"][0].update(blob_oid="0" * 40),
                     lambda m: m["files"][0].update(bytes=999),
                     lambda m: m["files"][0].update(path="../../outside"),
                     lambda m: m.update(source_commit="main")]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                manifest = copy.deepcopy(self.manifest)
                mutate(manifest)
                with self.assertRaises(ValueError):
                    verify_manifest(self.repo, manifest)

    def test_index_must_match_reviewed_migration_exactly(self):
        with self.assertRaisesRegex(ValueError, "index differs"):
            verify_manifest(self.repo, self.manifest, check_index=True)
        git(self.repo, "rm", "--cached", "--", self.scope + "/events/case.jsonl")
        self.assertTrue(verify_manifest(self.repo, self.manifest, check_index=True)["index_checked"])
        git(self.repo, "rm", "--cached", "--", self.scope + "/summary.json")
        with self.assertRaisesRegex(ValueError, "index differs"):
            verify_manifest(self.repo, self.manifest, check_index=True)

    def test_scopes_are_bounded_and_committed_pilot_has_a_complete_reference(self):
        self.assertEqual(safe_path("docs/benchmarks/runs"), "docs/benchmarks/runs")
        self.assertEqual(safe_path("docs/benchmarks/runs/"), "docs/benchmarks/runs")
        for path in ("/tmp/escape", "docs/benchmarks/runs/../../secrets", "docs/benchmarks/runs-other/fixture", "docs/benchmarks/runs/x\\y"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                safe_path(path)
        pilot = json.loads((REPO / "docs/benchmarks/archive-pilot-20260905.json").read_text(encoding="utf-8"))
        self.assertRegex(pilot["source_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(len(pilot["files"]), 37)
        self.assertEqual(len({r["path"] for r in pilot["files"]}), 37)
        self.assertEqual(sum(r["disposition"] == "migrate" for r in pilot["files"]), 32)
        self.assertTrue(all(r["reason"] for r in pilot["files"]))


if __name__ == "__main__":
    unittest.main()
