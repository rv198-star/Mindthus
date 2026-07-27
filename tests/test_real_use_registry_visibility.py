"""Contract tests for real-use registry visibility (issue #144, phase 1).

The failure this guards against is subtle: a validator that exits 0 on an empty log makes
a 0-record registry and a healthy 20-record registry indistinguishable in CI. These tests
pin the two properties that fix it without creating a new problem -- the count must be
*typed* (so evaluation and fixture records cannot stand in for real use), and the required
CI check must stay green at zero (so a strategic gap does not become a merge blocker that
gets routed around).
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
USAGE_LOGGER = REPO / "scripts" / "log-fidelity-usage.py"
WORKFLOW = REPO / ".github" / "workflows" / "python-validation.yml"
LEDGER = REPO / "docs" / "internal" / "tplan-feature-freeze-ledger.md"


def load_logger():
    spec = importlib.util.spec_from_file_location("log_fidelity_usage", USAGE_LOGGER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


logger = load_logger()


def record(**overrides):
    """Build a valid record. Only `real_use` may omit scores, so typed fixtures add them."""
    base = {
        "schema_version": logger.SCHEMA_VERSION,
        "logged_at": "2026-07-27T00:00:00Z",
        "observed_at": "2026-07-27T00:00:00Z",
        "collection_mode": "prospective",
        "record_type": "real_use",
        "scenario": "redacted task",
        "method": "SELA",
        "model": "fixture-model",
        "judge_model": "",
        "baseline_score": None,
        "constrained_score": None,
        "max_score": None,
        "score_delta": None,
        "constraint_helped": "yes",
        "source": "",
        "notes": "",
        "tags": [],
    }
    base.update(overrides)
    if base["record_type"] != "real_use" and base["max_score"] is None:
        base.update(
            {"baseline_score": None, "constrained_score": 8, "max_score": 10, "score_delta": None}
        )
    return base


def write_log(directory: Path, records) -> Path:
    path = directory / "usage.jsonl"
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8"
    )
    return path


class TypedCountTests(unittest.TestCase):
    def test_evaluation_and_fixture_records_do_not_count_as_real_use(self):
        counts = logger.count_by_type(
            [
                record(record_type="evaluation"),
                record(record_type="fixture"),
                record(record_type="evaluation"),
            ]
        )
        self.assertEqual(counts["real_use"], 0)
        self.assertEqual(counts["real_use_prospective"], 0)
        self.assertEqual(counts["evaluation"], 2)
        self.assertEqual(counts["fixture"], 1)

    def test_retrospective_real_use_does_not_count_toward_freeze_exit(self):
        counts = logger.count_by_type(
            [
                record(collection_mode="retrospective"),
                record(collection_mode="retrospective"),
                record(collection_mode="prospective"),
            ]
        )
        self.assertEqual(counts["real_use"], 3)
        self.assertEqual(counts["real_use_prospective"], 1)

    def test_validate_reports_counts_by_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_log(
                Path(tmp), [record(), record(record_type="evaluation"), record(record_type="fixture")]
            )
            result = subprocess.run(
                ["python3", str(USAGE_LOGGER), "--validate", "--log", str(path)],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("By type: real_use=1 evaluation=1 fixture=1", result.stdout)
            self.assertIn("Real-use prospective: 1", result.stdout)

    def test_min_real_use_is_record_type_aware(self):
        """An untyped threshold would pass here; this one must not."""
        with tempfile.TemporaryDirectory() as tmp:
            path = write_log(Path(tmp), [record(record_type="evaluation") for _ in range(10)])
            result = subprocess.run(
                ["python3", str(USAGE_LOGGER), "--validate", "--log", str(path), "--min-real-use", "5"],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("BELOW-THRESHOLD", result.stdout)


class SchemaTests(unittest.TestCase):
    def test_collection_mode_is_validated(self):
        findings = logger.validate_record(record(collection_mode="backfilled"), 1)
        self.assertIn("invalid-collection-mode", [item.code for item in findings])

    def test_observed_at_and_record_id_reject_empty_strings(self):
        """Empty is rejected for both; the code differs because the fields differ.

        `observed_at` is a timestamp, so an empty one is a missing timestamp.
        `record_id` is free text and stays an optional-field finding.
        """
        for field, expected in (
            ("observed_at", "missing-field"),
            ("record_id", "invalid-optional-field"),
        ):
            with self.subTest(field=field):
                findings = logger.validate_record(record(**{field: "  "}), 1)
                self.assertIn(expected, [item.code for item in findings])

    def test_existing_records_without_new_fields_still_validate(self):
        """The schema version is unchanged, so records written before this change must pass."""
        legacy = record()
        for field in ("observed_at", "collection_mode"):
            legacy.pop(field)
        self.assertEqual(logger.validate_record(legacy, 1), [])

    def test_record_id_is_derived_and_stable(self):
        first = logger.derive_record_id(record())
        self.assertEqual(first, logger.derive_record_id(record()))
        self.assertNotEqual(first, logger.derive_record_id(record(scenario="a different task")))
        self.assertTrue(first.startswith("mtu-"))

    def test_appended_record_carries_the_new_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "usage.jsonl"
            result = subprocess.run(
                [
                    "python3", str(USAGE_LOGGER),
                    "--log", str(path),
                    "--scenario", "redacted real task",
                    "--method", "SELA",
                    "--model", "fixture-model",
                    "--constraint-helped", "yes",
                    "--observed-at", "2026-07-20T00:00:00Z",
                    "--collection-mode", "retrospective",
                ],
                text=True,
                capture_output=True,
                cwd=REPO,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            written = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(written["observed_at"], "2026-07-20T00:00:00Z")
            self.assertEqual(written["collection_mode"], "retrospective")
            self.assertTrue(written["record_id"].startswith("mtu-"))
            self.assertNotEqual(written["observed_at"], written["logged_at"])


class TimestampValidationTests(unittest.TestCase):
    """Timestamps decide freeze exit, so an unvalidated one is a hole in the freeze.

    Before this, only `""` and non-strings were rejected. `not-a-date`, `2027-13-45`, and
    a date two years before the freeze opened all validated, and a record claiming to be
    a prospective observation of a task in 2024 counted toward opening the window.
    """

    def test_unparseable_timestamps_are_rejected(self):
        for field in ("logged_at", "observed_at"):
            for value in ("not-a-date", "2027-13-45", "yesterday", "07/27/2026"):
                with self.subTest(field=field, value=value):
                    findings = logger.validate_record(record(**{field: value}), 1)
                    self.assertIn("invalid-timestamp", [item.code for item in findings])

    def test_type_error_and_format_error_are_separate_codes(self):
        """Two different mistakes: a writer bug and a human typo."""
        typed = logger.validate_record(record(observed_at=1), 1)
        self.assertIn("invalid-field-type", [item.code for item in typed])
        malformed = logger.validate_record(record(observed_at="not-a-date"), 1)
        self.assertIn("invalid-timestamp", [item.code for item in malformed])

    def test_observation_cannot_postdate_the_log_entry(self):
        findings = logger.validate_record(
            record(observed_at="2026-07-28T00:00:00Z", logged_at="2026-07-27T00:00:00Z"), 1
        )
        self.assertIn("impossible-observation-order", [item.code for item in findings])

    def test_both_timestamps_go_through_the_same_validator(self):
        """`logged_at` was checked for presence only, `observed_at` for emptiness only."""
        for field in ("logged_at", "observed_at"):
            with self.subTest(field=field):
                findings = logger.validate_record(record(**{field: "2026-13-99"}), 1)
                self.assertTrue(
                    any(item.code == "invalid-timestamp" for item in findings),
                    f"{field} accepted an impossible date",
                )

    def test_valid_timestamps_produce_no_findings(self):
        for value in ("2026-07-27T00:00:00Z", "2026-07-27T00:00:00+00:00", "2026-07-27"):
            with self.subTest(value=value):
                self.assertEqual(logger.validate_record(record(observed_at=value), 1), [])


class FreezeEligibilityTests(unittest.TestCase):
    def test_freeze_opened_is_a_tz_aware_constant(self):
        """A naive constant raises TypeError on comparison the day someone moves it."""
        self.assertIsNotNone(logger.FREEZE_OPENED.tzinfo)

    def test_boundary_is_strictly_after_the_day_the_freeze_opened(self):
        """The prose says "observed after 2026-07-26" in two places. The code agrees.

        A record observed on the day #144 was filed would otherwise count toward opening
        the window it opened.
        """
        self.assertFalse(logger.freeze_eligible(record(observed_at="2026-07-26T23:59:59Z")))
        self.assertTrue(logger.freeze_eligible(record(observed_at="2026-07-27T00:00:00Z")))

    def test_backdated_prospective_record_does_not_count(self):
        """The defect in one line: self-declared prospective, observed years earlier."""
        backdated = record(observed_at="2024-01-01T00:00:00Z", collection_mode="prospective")
        self.assertEqual(logger.validate_record(backdated, 1), [], "record is well-formed")
        self.assertFalse(logger.freeze_eligible(backdated))
        self.assertEqual(logger.count_by_type([backdated])["freeze_eligible"], 0)

    def test_retrospective_records_never_count_however_recent(self):
        recent = record(observed_at="2026-07-30T00:00:00Z", collection_mode="retrospective")
        self.assertEqual(logger.count_by_type([recent])["freeze_eligible"], 0)

    def test_record_without_observed_at_is_not_eligible(self):
        legacy = record()
        legacy.pop("observed_at")
        self.assertFalse(logger.freeze_eligible(legacy))

    def test_prospective_count_and_eligible_count_are_reported_separately(self):
        """Collapsing them would hide exactly the records under discussion."""
        counts = logger.count_by_type(
            [record(observed_at="2024-01-01T00:00:00Z"), record(observed_at="2026-07-28T00:00:00Z")]
        )
        self.assertEqual(counts["real_use_prospective"], 2)
        self.assertEqual(counts["freeze_eligible"], 1)


class RecordIdTests(unittest.TestCase):
    def test_id_is_stable_across_when_the_record_was_written(self):
        """With an explicit observed_at, logging the same task later must not re-ID it.

        `logged_at` used to be in the seed, so the same task registered eight hours later
        produced a different ID -- and the record-10 review cites records by ID.
        """
        task = {
            "observed_at": "2026-07-27T02:00:00Z",
            "record_type": "real_use",
            "method": "SELA",
            "scenario": "a task",
            "model": "fixture-model",
        }
        first = logger.derive_record_id({**task, "logged_at": "2026-07-27T02:00:00Z"})
        for later in ("2026-07-27T10:00:00Z", "2026-07-28T09:00:00Z", "2026-08-01T00:00:00Z"):
            with self.subTest(logged_at=later):
                self.assertEqual(first, logger.derive_record_id({**task, "logged_at": later}))

    def test_logged_at_is_not_in_the_seed(self):
        source = USAGE_LOGGER.read_text(encoding="utf-8")
        seed_block = source.split("def derive_record_id")[1].split("hexdigest")[0]
        self.assertNotIn('"logged_at"', seed_block)

    def test_distinct_tasks_still_get_distinct_ids(self):
        base = record()
        for field, value in (
            ("scenario", "a different task"),
            ("method", "MPG"),
            ("model", "another-model"),
            ("observed_at", "2026-07-28T00:00:00Z"),
        ):
            with self.subTest(field=field):
                self.assertNotEqual(
                    logger.derive_record_id(base), logger.derive_record_id(record(**{field: value}))
                )

    def test_derivation_happens_only_on_the_write_path(self):
        """--validate must never recompute an ID; a stored ID is the record's identity."""
        source = USAGE_LOGGER.read_text(encoding="utf-8")
        self.assertEqual(source.count("derive_record_id("), 2, "expected def + one call site")

    def test_docstring_declares_the_stability_it_actually_provides(self):
        """C7: a docstring must not claim a property the code does not enforce.

        The old one said duplicates surface as a repeated ID. That is true only when the
        caller passes --observed-at; on the default path observed_at defaults to the
        logging time and two IDs result.
        """
        doc = logger.derive_record_id.__doc__
        self.assertIn("--observed-at", doc)
        self.assertIn("conditional", doc.lower())


class SourceFieldTests(unittest.TestCase):
    def test_absent_and_empty_source_behave_identically(self):
        """`--source ""` passed silently while omitting the key reported a finding.

        The more careless entry was the one that validated. Both mean "not provided".
        """
        empty = record(source="")
        absent = record()
        absent.pop("source")
        self.assertEqual(logger.validate_record(empty, 1), logger.validate_record(absent, 1))
        self.assertEqual(logger.validate_record(absent, 1), [])

    def test_source_stays_optional(self):
        """Mandating it would be new policy, and it would not make the field verifiable.

        `source` is free text: nothing checks that what it points at exists, is
        reachable, matches the record, or is redacted. Requiring non-empty turns "not
        filled in" into "filled in with anything".
        """
        self.assertIn("Optional artifact or issue reference", USAGE_LOGGER.read_text("utf-8"))

    def test_wrong_type_is_still_a_finding(self):
        findings = logger.validate_record(record(source=42), 1)
        self.assertIn("invalid-optional-field", [item.code for item in findings])


class StatusSurfaceTests(unittest.TestCase):
    def test_readme_renders_the_real_use_count(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn(logger.STATUS_BEGIN, readme)
        self.assertIn(logger.STATUS_END, readme)
        self.assertIn("真实使用记录：", readme)

    def test_readme_status_block_is_current(self):
        result = subprocess.run(
            ["python3", str(USAGE_LOGGER), "--check-status", "--log", "data/fidelity-usage-log.jsonl"],
            text=True,
            capture_output=True,
            cwd=REPO,
        )
        self.assertEqual(
            result.returncode,
            0,
            "README real-use status block is stale; run --render-status\n" + result.stdout,
        )

    def test_check_status_detects_a_hand_edited_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(
                f"intro\n\n{logger.STATUS_BEGIN}\n**真实使用记录：7/10**\n{logger.STATUS_END}\n",
                encoding="utf-8",
            )
            self.assertEqual(logger.sync_status(readme, [], check=True), 1)

    def test_status_block_counts_prospective_not_total(self):
        block = logger.render_status_block(
            [record(collection_mode="retrospective") for _ in range(9)] + [record()]
        )
        self.assertIn("1/10", block)
        self.assertNotIn("10/10", block)


class RequiredCiTests(unittest.TestCase):
    def test_required_ci_runs_the_freshness_check(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "python3 scripts/log-fidelity-usage.py --check-status "
            "--log data/fidelity-usage-log.jsonl",
            text,
        )

    def test_required_ci_does_not_gate_on_record_count(self):
        """A required job that fails at 0 records converts a strategic gap into noise.

        Checks executed lines rather than the whole file, since the workflow comment
        explains why --min-real-use is deliberately absent.
        """
        executed = [
            line
            for line in WORKFLOW.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertNotIn("--min-real-use", "\n".join(executed))

    def test_required_ci_checks_stay_green_on_an_empty_registry(self):
        for flags in (["--validate"], ["--check-status"]):
            with self.subTest(flags=flags):
                result = subprocess.run(
                    ["python3", str(USAGE_LOGGER), *flags, "--log", "data/fidelity-usage-log.jsonl"],
                    text=True,
                    capture_output=True,
                    cwd=REPO,
                )
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


class FreezeLedgerTests(unittest.TestCase):
    def test_ledger_exists_and_states_its_scope(self):
        self.assertTrue(LEDGER.is_file(), "freeze ledger is missing")
        text = LEDGER.read_text(encoding="utf-8")
        for phrase in ("| Date | PR / commit | Category | Why |", "Every merge during the window"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_ledger_records_defect_and_hygiene_merges_too(self):
        """A ledger of only the contested merges cannot show the window was respected."""
        text = LEDGER.read_text(encoding="utf-8")
        self.assertIn("not only the arguable ones", text)

    def test_ledger_does_not_claim_to_lift_the_freeze(self):
        text = LEDGER.read_text(encoding="utf-8")
        self.assertIn("does not lift the freeze", text)


if __name__ == "__main__":
    unittest.main()
