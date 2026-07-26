"""Contract tests for the benchmark run artifact inventory.

The inventory decides which historical run artifacts leave HEAD. Its dangerous failure
mode is not crashing -- it is silently classifying a decision-bearing file as `migrate`,
or silently reporting a retained report as safe when its evidence references are about to
break. These tests pin the safety-relevant behaviour, not the totals: totals move
whenever a new campaign lands, but "unknown files are kept" and "this tool never deletes"
must not move.
"""

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "benchmark-artifact-inventory.py"


def load_module():
    spec = importlib.util.spec_from_file_location("benchmark_artifact_inventory", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


inventory = load_module()


class ClassificationContractTests(unittest.TestCase):
    def test_unknown_paths_are_kept_not_deleted(self):
        """A shape no rule anticipated must never be migrated by silent default."""
        disposition, rule = inventory.classify(
            "docs/benchmarks/runs/2099-01-01-future-campaign/something-nobody-planned.json"
        )
        self.assertEqual(disposition, "keep")
        self.assertEqual(rule, "unmatched")

    def test_per_call_artifacts_are_migrated(self):
        base = "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/treatment-cli-clean"
        for path in (
            f"{base}/answers/mtj-001-turn-1.txt",
            f"{base}/prompts/mtj-001.prompt.txt",
            f"{base}/events/mtj-001-turn-1.jsonl",
            f"{base}/judge-answers/mtj-001.record.json",
            f"{base}/score-records.jsonl",
            f"{base}/raw-responses.jsonl",
        ):
            with self.subTest(path=path):
                self.assertEqual(inventory.classify(path)[0], "migrate")

    def test_decision_bearing_artifacts_are_kept(self):
        base = "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1"
        for path in (
            f"{base}/REPORT.md",
            f"{base}/HUMAN_REVIEW_PACKET.md",
            f"{base}/EXTERNAL_AUDIT_HANDOFF.md",
            f"{base}/MANUAL_PROBLEM_CASE_AUDIT.md",
            f"{base}/run-manifest.json",
            f"{base}/contamination-report.json",
            f"{base}/summary.json",
            f"{base}/summary-aggregate.json",
            f"{base}/runtime-fingerprint-strict.json",
            f"{base}/discarded-initial-run/README.txt",
        ):
            with self.subTest(path=path):
                self.assertEqual(inventory.classify(path)[0], "keep")

    def test_duplicated_telemetry_is_migrated_because_the_original_is_kept(self):
        """activation-summary.json duplicates summary.json['activation'] exactly.

        Verified equal in 43/43 tracked cases. Migrating it loses no information; the
        sibling summary.json carries the same object and is kept.
        """
        base = "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/treatment-cli-clean"
        self.assertEqual(inventory.classify(f"{base}/activation-summary.json")[0], "migrate")
        self.assertEqual(inventory.classify(f"{base}/summary.json")[0], "keep")

    def test_case_register_is_kept_because_report_claims_depend_on_it(self):
        path = (
            "docs/benchmarks/runs/2026-07-09-issue-108-generalized-probes/"
            "issue-108-variant-cases.jsonl"
        )
        self.assertEqual(inventory.classify(path), ("keep", "policy:case-register"))

    def test_every_rule_has_a_stated_reason(self):
        """Rows reference a reason by key; a missing key would raise at render time."""
        for name in dir(inventory):
            if not name.startswith(("KEEP_", "MIGRATE_")):
                continue
            values = getattr(inventory, name)
            if not isinstance(values, (set, frozenset)):
                continue
            for member in values:
                path = f"docs/benchmarks/runs/campaign/sub/{member}"
                if name == "MIGRATE_DIRS":
                    path = f"docs/benchmarks/runs/campaign/{member}/file.txt"
                _, rule = inventory.classify(path)
                self.assertIn(rule, inventory.RULE_REASONS)


class ReferenceResolutionTests(unittest.TestCase):
    def test_directory_reference_survives_when_anything_under_it_is_kept(self):
        tracked = {
            "docs/benchmarks/runs/c/repeat-1/summary.json": "keep",
            "docs/benchmarks/runs/c/repeat-1/answers/a.txt": "migrate",
        }
        self.assertTrue(
            inventory.reference_survives("repeat-1/", "docs/benchmarks/runs/c/REPORT.md", tracked)
        )

    def test_directory_reference_breaks_when_everything_under_it_migrates(self):
        tracked = {"docs/benchmarks/runs/c/answers/a.txt": "migrate"}
        self.assertFalse(
            inventory.reference_survives("answers/", "docs/benchmarks/runs/c/REPORT.md", tracked)
        )

    def test_file_reference_to_migrated_artifact_breaks(self):
        tracked = {"docs/benchmarks/runs/c/score-records.jsonl": "migrate"}
        self.assertFalse(
            inventory.reference_survives(
                "score-records.jsonl", "docs/benchmarks/runs/c/REPORT.md", tracked
            )
        )

    def test_unresolvable_reference_is_reported_not_skipped(self):
        """Glob templates and variant-relative paths resolve to nothing today.

        `answers/<case>.record.json` matches no tracked file, and the review packets write
        `answers/mtj-032-turn-1.txt` relative to a variant subdirectory rather than the
        report's own. Treating either as safe would hide the reports that most need an
        archive pointer, so scan_references counts them.
        """
        self.assertIsNone(
            inventory.reference_survives(
                "answers/<case>.record.json", "docs/benchmarks/runs/c/REPORT.md", {}
            )
        )
        self.assertTrue("answers/<case>.record.json".startswith(inventory.MIGRATED_REF_PREFIXES))

    def test_live_scan_flags_the_review_packet_whose_evidence_column_dies(self):
        entries = inventory.build_inventory(REPO)
        references = inventory.scan_references(REPO, entries)
        flagged = {item["report"] for item in references["details"]}
        self.assertIn(
            "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/"
            "HUMAN_REVIEW_PACKET.md",
            flagged,
        )
        self.assertLessEqual(references["reports_needing_archive_pointer"], len(flagged) + 1)


class DryRunSafetyTests(unittest.TestCase):
    def test_script_declares_itself_a_dry_run_and_never_deletes(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("never deletes, moves, or rewrites", source)
        for destructive in ("os.remove", "shutil.rmtree", "unlink(", "git rm", "filter-repo"):
            with self.subTest(call=destructive):
                self.assertNotIn(destructive, source)

    def test_running_the_tool_leaves_the_working_tree_unchanged(self):
        before = subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout
        result = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=REPO, capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        after = subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout
        self.assertEqual(before, after, "inventory run modified the working tree")


class CommittedInventoryTests(unittest.TestCase):
    def test_committed_summary_matches_a_fresh_run(self):
        summary_path = REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json"
        self.assertTrue(summary_path.is_file(), "committed inventory summary is missing")
        committed = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(committed["schema_version"], inventory.INVENTORY_SCHEMA_VERSION)

        fresh = inventory.summarize(inventory.build_inventory(REPO))
        self.assertEqual(
            committed["summary"],
            fresh,
            "committed inventory is stale; regenerate it before review",
        )

    def test_committed_inventory_resolves_every_unmatched_path(self):
        summary_path = REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json"
        committed = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(
            committed["summary"]["unmatched_files"],
            0,
            "unmatched paths must be classified explicitly before deletion is considered",
        )


if __name__ == "__main__":
    unittest.main()
