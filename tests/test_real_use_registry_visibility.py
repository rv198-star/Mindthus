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
        for field in ("observed_at", "record_id"):
            with self.subTest(field=field):
                findings = logger.validate_record(record(**{field: "  "}), 1)
                self.assertIn("invalid-optional-field", [item.code for item in findings])

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
