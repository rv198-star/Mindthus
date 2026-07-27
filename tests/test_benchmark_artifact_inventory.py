"""Contract tests for the benchmark run artifact inventory.

The inventory decides which historical run artifacts leave HEAD. Its dangerous failure
mode is not crashing -- it is silently classifying a decision-bearing file as `migrate`,
or silently reporting a retained report as safe when its evidence references are about to
break. These tests pin the safety-relevant behaviour, not the totals: totals move
whenever a new campaign lands, but "unknown files are kept" and "this tool never deletes"
must not move.
"""

import csv
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


def committed_inventory_entries():
    summary = json.loads(
        (REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json").read_text(
            encoding="utf-8"
        )
    )
    return inventory.build_inventory(
        REPO,
        revision=summary["baseline_commit"],
        migrate_destination=summary["destination"],
    )


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
        entries = committed_inventory_entries()
        references = inventory.scan_references(REPO, entries)
        flagged = {item["report"] for item in references["details"]}
        self.assertIn(
            "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/"
            "HUMAN_REVIEW_PACKET.md",
            flagged,
        )
        self.assertEqual(references["reports_with_dangling_references"], len(flagged))

    def test_all_required_report_types_require_archive_pointers(self):
        entries = committed_inventory_entries()
        references = inventory.scan_references(REPO, entries)
        expected = [
            item
            for item in entries
            if item.disposition == "keep"
            and Path(item.path).name in inventory.ARCHIVE_POINTER_REPORTS
        ]
        self.assertEqual(references["reports_requiring_archive_pointer"], len(expected))
        self.assertEqual(references["retained_reports"], len(expected))
        self.assertGreater(
            references["reports_requiring_archive_pointer"],
            references["reports_with_dangling_references"],
            "direct-risk reports are only a subset of the pointer obligation",
        )
        self.assertEqual(references["reports_missing_pointer_syntax"], [])
        self.assertEqual(
            references["reports_with_verified_archive_pointer"],
            references["reports_requiring_archive_pointer"],
        )
        self.assertTrue(references["semantic_pointer_coverage_ok"])

    def test_baseline_and_workspace_pointer_coverage_are_separate_populations(self):
        summary = json.loads(
            (REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json").read_text(
                encoding="utf-8"
            )
        )
        entries = inventory.build_inventory(
            REPO,
            revision=summary["baseline_commit"],
            migrate_destination=summary["destination"],
        )
        baseline = inventory.scan_references(
            REPO, entries, content_revision=summary["baseline_commit"]
        )
        workspace = inventory.scan_references(REPO, entries)

        self.assertEqual(baseline["scan_source"]["kind"], "git-revision")
        self.assertEqual(baseline["reports_with_pointer_syntax"], 0)
        self.assertEqual(baseline["reports_with_verified_archive_pointer"], 0)
        self.assertFalse(baseline["semantic_pointer_coverage_ok"])

        self.assertEqual(workspace["scan_source"]["kind"], "workspace")
        self.assertEqual(workspace["reports_with_pointer_syntax"], 14)
        self.assertEqual(workspace["reports_with_verified_archive_pointer"], 14)
        self.assertTrue(workspace["semantic_pointer_coverage_ok"])

        report = (
            "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/"
            "REPORT.md"
        )
        baseline_oid = subprocess.run(
            ["git", "rev-parse", f"{summary['baseline_commit']}:{report}"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        head_oid = subprocess.run(
            ["git", "rev-parse", f"HEAD:{report}"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertNotEqual(
            baseline_oid,
            head_oid,
            "the fixture must prove baseline and workspace report bytes differ",
        )

    def test_forged_40_hex_pointer_fails_semantic_verification(self):
        summary = json.loads(
            (REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json").read_text(
                encoding="utf-8"
            )
        )
        entries = inventory.build_inventory(
            REPO,
            revision=summary["baseline_commit"],
            migrate_destination=summary["destination"],
        )
        report = (
            "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/"
            "REPORT.md"
        )
        forged = "0" * 40
        forged_text = (REPO / report).read_text(encoding="utf-8").replace(
            summary["destination"].removeprefix("git:"), forged
        )
        references = inventory.scan_references(
            REPO, entries, report_text_overrides={report: forged_text}
        )

        self.assertEqual(references["reports_with_pointer_syntax"], 14)
        self.assertEqual(references["reports_with_verified_archive_pointer"], 13)
        self.assertFalse(references["semantic_pointer_coverage_ok"])
        failed = {
            item["report"]: item
            for item in references["reports_failed_semantic_pointer_verification"]
        }
        self.assertIn(report, failed)
        self.assertIn("pointer-commit-unresolvable", failed[report]["errors"])
        self.assertIsNone(inventory.try_resolve_commit(REPO, forged))

    def test_archive_dependent_references_resolve_to_verified_inventory_oids(self):
        entries = committed_inventory_entries()
        references = inventory.scan_references(REPO, entries)
        self.assertGreater(len(references["archive_reference_details"]), 0)
        self.assertTrue(
            all(
                item["archive_verified"]
                for item in references["archive_reference_details"]
            )
        )
        archive = references["archive_destination_verification"]
        self.assertTrue(archive["commit_exists"])
        self.assertTrue(archive["valid"])
        self.assertEqual(
            archive["verified_migrate_files"], archive["expected_migrate_files"]
        )


class ReferenceAccountingTests(unittest.TestCase):
    """Every extracted reference must land in exactly one category.

    The first pass of this scanner dropped 73 references without incrementing any
    counter: a reference that matched no branch fell off the loop. A scan that examined
    nothing then reported the same clean result as a scan that examined everything. These
    tests make that failure mode arithmetic rather than a matter of reading the code.
    """

    @classmethod
    def setUpClass(cls):
        cls.entries = committed_inventory_entries()
        cls.references = inventory.scan_references(REPO, cls.entries)

    def test_categories_sum_to_the_number_extracted(self):
        by_category = self.references["by_category"]
        self.assertEqual(
            sum(by_category.values()),
            self.references["total_extracted"],
            "references were dropped between extraction and classification",
        )
        self.assertTrue(self.references["accounting_ok"])

    def test_every_category_is_present_even_at_zero(self):
        """A sparse dict lets a category that stopped being reached look absent."""
        self.assertEqual(
            set(self.references["by_category"]), set(inventory.REFERENCE_CATEGORIES)
        )

    def test_scan_scope_is_reported_not_implied(self):
        """`accounting_ok` covers the files scanned, not the repository.

        Without these two numbers next to it, `accounting_ok: True` reads as a much
        stronger claim than it is -- 14 of 159 kept files are actually read.
        """
        kept = len([item for item in self.entries if item.disposition == "keep"])
        self.assertEqual(
            self.references["scanned_files"] + self.references["skipped_files"], kept
        )
        self.assertGreater(self.references["skipped_files"], 0)

    def test_return_contract_uses_unambiguous_names(self):
        """Policy obligation, direct risk, syntax, and verification are separate."""
        self.assertLessEqual(
            inventory.REFERENCES_REQUIRED_KEYS, set(self.references)
        )
        for key in (
            "retained_reports",
            "reports_requiring_archive_pointer",
            "reports_with_dangling_references",
            "details",
        ):
            with self.subTest(key=key):
                self.assertIn(key, self.references)
        for misleading in (
            "reports_needing_archive_pointer",
            "reports_with_archive_pointer",
        ):
            with self.subTest(misleading=misleading):
                self.assertNotIn(misleading, self.references)

    def test_broken_accounting_fails_the_run(self):
        """The gate must be an exit code, not a printed line nobody reads."""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("BROKEN-ACCOUNTING", source)
        self.assertIn('if references["accounting_ok"]', source)

    def test_report_does_not_assert_cleanliness_when_accounting_is_broken(self):
        """C7 on generated prose: the report must not claim what the numbers deny.

        An unconditional "nothing was dropped" sentence is the same defect the reference
        scan was rejected for, one layer up -- a document asserting a property of a scan
        that did not hold.
        """
        summary = inventory.summarize(self.entries)
        broken = {**self.references, "accounting_ok": False, "total_extracted": 999}
        text = inventory.render_report(
            summary,
            self.entries,
            "abc1234",
            self.references,
            broken,
            "git:abc1234",
        )
        self.assertNotIn("nothing was dropped", text)
        self.assertIn("floor, not a total", text)

        clean = inventory.render_report(
            summary,
            self.entries,
            "abc1234",
            self.references,
            self.references,
            "git:abc1234",
        )
        self.assertIn("nothing was dropped", clean)

    def test_numeric_ratios_are_rejected_by_shape_not_by_failed_resolution(self):
        """`0/12` and `1.5 / 2` are scores. The slash makes PATH_LIKE accept them."""
        for ratio in ("0/12", "1.5 / 2", "0.467 / 0.600 / 0.667"):
            with self.subTest(ratio=ratio):
                self.assertTrue(inventory.PATH_LIKE.search(ratio))
                self.assertTrue(inventory.NUMERIC_RATIO.match(ratio))
        self.assertGreater(self.references["by_category"]["rejected_numeric_ratio"], 0)

    def test_numeric_ratio_filter_matches_no_real_tracked_path(self):
        """A filter that started swallowing filenames would be the original defect again."""
        for item in self.entries:
            self.assertIsNone(inventory.NUMERIC_RATIO.match(item.path))
            self.assertIsNone(
                inventory.NUMERIC_RATIO.match(Path(item.path).name)
            )

    def test_migrate_basename_index_is_derived_not_a_literal(self):
        """`judge-output-schema.json` is cited bare by a report and has 50 migrate copies.

        The hand-written MIGRATE_NAMES literal holds 4 names, so the reference resolved
        to nothing, matched no branch, and vanished. Deriving the index from the
        classification result is what makes that structurally impossible.
        """
        derived = inventory.migrate_only_basenames(self.entries)
        self.assertIn("judge-output-schema.json", derived)
        self.assertGreater(len(derived), len(inventory.MIGRATE_NAMES) * 10)

    def test_report_citing_a_bare_migrated_basename_needs_an_archive_pointer(self):
        flagged = {item["report"] for item in self.references["details"]}
        self.assertIn(
            "docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/REPORT.md",
            flagged,
            "a report citing a migrated artifact by bare basename was reported safe",
        )

    def test_references_to_files_outside_runs_are_not_reported_as_at_risk(self):
        """Migration touches only RUNS_ROOT. Flagging `scripts/foo.py` is a false positive.

        35 of the originally dropped references are ordinary repo files. A scanner that
        cries wolf 35 times to catch one real risk gets ignored, and then the one real
        risk is missed too.
        """
        tracked = {"scripts/log-mindthus-runtime.py", "docs/benchmarks/latest.md"}
        for ref in tracked:
            with self.subTest(ref=ref):
                self.assertTrue(inventory.resolves_outside_runs(ref, tracked))
        self.assertFalse(
            inventory.resolves_outside_runs(
                f"{inventory.RUNS_ROOT}/c/answers/a.txt",
                {f"{inventory.RUNS_ROOT}/c/answers/a.txt"},
            ),
            "a path under RUNS_ROOT is exactly what migration acts on",
        )

    def test_unresolved_references_stay_visible_rather_than_being_explained_away(self):
        """The remainder is prose and env-var names caught by the regex.

        No exemption rule is written for them. A "looks like prose, skip it" heuristic
        would be another filter a reviewer cannot independently check -- the same defect
        class being repaired here. A constant, countable, irritating remainder is safer.
        """
        self.assertGreater(self.references["by_category"]["unresolved"], 0)


class CsvContractTests(unittest.TestCase):
    COMMITTED = REPO / "docs" / "benchmarks" / "artifact-inventory.csv"

    def test_committed_csv_has_no_carriage_returns(self):
        """Read as bytes.

        Text mode and `subprocess.run(text=True)` apply universal newlines, which
        translate CRLF to LF before any assertion sees it -- a check written that way
        passes against the very file it is supposed to reject.
        """
        data = self.COMMITTED.read_bytes()
        self.assertNotIn(b"\r", data)

    def test_committed_csv_header_is_exact_and_ordered(self):
        header = self.COMMITTED.read_bytes().split(b"\n", 1)[0].decode("utf-8")
        self.assertEqual(header.split(","), list(inventory.CSV_COLUMNS))

    def test_csv_columns_match_the_entry_dataclass(self):
        """Pinning the header is only safe if it is checked against the row source."""
        from dataclasses import fields

        self.assertEqual(
            list(inventory.CSV_COLUMNS), [field.name for field in fields(inventory.Entry)]
        )

    def test_csv_eol_is_pinned_by_gitattributes(self):
        """Otherwise a Windows checkout rewrites the bytes and the evidence stops matching."""
        result = subprocess.run(
            ["git", "ls-files", "--eol", "--", "*.csv"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertTrue(result.stdout.strip(), "no CSV is tracked")
        for line in result.stdout.splitlines():
            with self.subTest(line=line):
                self.assertIn("i/lf", line)
                self.assertIn("eol=lf", line)

    def test_schema_version_moved_with_the_row_bytes(self):
        """v0.4 separates evidence populations and verifies pointer semantics."""
        self.assertTrue(inventory.INVENTORY_SCHEMA_VERSION.endswith("v0.4"))

    def test_every_committed_row_carries_reason_and_destination(self):
        with self.COMMITTED.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(path=row["path"]):
                self.assertEqual(row["reason"], inventory.RULE_REASONS[row["rule"]])
                if row["disposition"] == "keep":
                    self.assertEqual(row["destination"], "HEAD")
                else:
                    self.assertRegex(row["destination"], r"^git:[0-9a-f]{40}$")

    def test_report_pointers_name_the_committed_inventory_destination(self):
        summary = json.loads(
            (REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json").read_text(
                encoding="utf-8"
            )
        )
        marker = f"`{summary['destination']}`"
        reports = [
            item
            for item in inventory.build_inventory(
                REPO,
                revision=summary["baseline_commit"],
                migrate_destination=summary["destination"],
            )
            if item.disposition == "keep"
            and Path(item.path).name in inventory.ARCHIVE_POINTER_REPORTS
        ]
        self.assertEqual(len(reports), 14)
        for item in reports:
            with self.subTest(path=item.path):
                text = (REPO / item.path).read_text(encoding="utf-8")
                self.assertIn(inventory.ARCHIVE_POINTER_MARKER, text)
                self.assertIn(marker, text)


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
    def test_committed_summary_matches_its_pinned_baseline(self):
        summary_path = REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json"
        self.assertTrue(summary_path.is_file(), "committed inventory summary is missing")
        committed = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(committed["schema_version"], inventory.INVENTORY_SCHEMA_VERSION)
        self.assertRegex(committed["baseline_commit"], r"^[0-9a-f]{40}$")
        self.assertEqual(committed["destination"], f"git:{committed['baseline_commit']}")

        fresh = inventory.summarize(
            inventory.build_inventory(
                REPO,
                revision=committed["baseline_commit"],
                migrate_destination=committed["destination"],
            )
        )
        self.assertEqual(
            committed["summary"],
            fresh,
            "committed inventory disagrees with its immutable baseline",
        )

    def test_committed_inventory_resolves_every_unmatched_path(self):
        summary_path = REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json"
        committed = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(
            committed["summary"]["unmatched_files"],
            0,
            "unmatched paths must be classified explicitly before deletion is considered",
        )

    def test_committed_summary_separates_baseline_and_workspace_semantics(self):
        committed = json.loads(
            (REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("references", committed)
        self.assertEqual(set(committed["reference_scans"]), {"baseline", "workspace"})
        baseline = committed["reference_scans"]["baseline"]
        workspace = committed["reference_scans"]["workspace"]
        self.assertEqual(baseline["reports_with_pointer_syntax"], 0)
        self.assertEqual(baseline["reports_with_verified_archive_pointer"], 0)
        self.assertFalse(baseline["semantic_pointer_coverage_ok"])
        self.assertEqual(workspace["reports_with_pointer_syntax"], 14)
        self.assertEqual(workspace["reports_with_verified_archive_pointer"], 14)
        self.assertTrue(workspace["semantic_pointer_coverage_ok"])
        self.assertEqual(
            workspace["archive_destination_verification"]["verified_migrate_files"],
            committed["summary"]["migrate_files"],
        )

    def test_committed_rows_match_every_blob_in_the_pinned_tree(self):
        summary = json.loads(
            (REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            item.path: item
            for item in inventory.build_inventory(
                REPO,
                revision=summary["baseline_commit"],
                migrate_destination=summary["destination"],
            )
        }
        with (
            REPO / "docs" / "benchmarks" / "artifact-inventory.csv"
        ).open(encoding="utf-8", newline="") as handle:
            committed = {row["path"]: row for row in csv.DictReader(handle)}
        self.assertEqual(set(committed), set(expected))
        for path, item in expected.items():
            with self.subTest(path=path):
                row = committed[path]
                self.assertEqual(row["blob_oid"], item.blob_oid)
                self.assertEqual(int(row["size_bytes"]), item.size_bytes)
                self.assertEqual(row["disposition"], item.disposition)
                self.assertEqual(row["reason"], item.reason)
                self.assertEqual(row["destination"], item.destination)

    def test_migration_verifier_uses_pinned_archive_and_current_head_separately(self):
        """Before deletion it must prove archive OIDs yet refuse a completion claim.

        After deletion the same test continues to use the immutable inventory rather
        than comparing the committed pre-migration summary with the changed live tree.
        """
        summary = json.loads(
            (REPO / "docs" / "benchmarks" / "artifact-inventory-summary.json").read_text(
                encoding="utf-8"
            )
        )
        entries = inventory.build_inventory(
            REPO,
            revision=summary["baseline_commit"],
            migrate_destination=summary["destination"],
        )
        verification = inventory.verify_migration(
            REPO, entries, summary["destination"].removeprefix("git:")
        )
        self.assertEqual(
            verification["archive_verified_files"],
            summary["summary"]["migrate_files"],
        )
        self.assertEqual(verification["archive_missing_files"], 0)
        self.assertEqual(verification["archive_oid_mismatches"], 0)

        # Phase 1 is deliberately not a completion claim: no deletion is authorized yet.
        if verification["remaining_migrate_files"]:
            self.assertFalse(verification["complete"])
            self.assertEqual(
                verification["remaining_migrate_files"],
                summary["summary"]["migrate_files"],
            )


if __name__ == "__main__":
    unittest.main()
