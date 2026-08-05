import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills"))

from _runtime.judgment.case_export import (  # noqa: E402
    CaseExportError,
    create_case_package,
    validate_case_package,
)


RUNTIME_FIXTURES = REPO / "skills" / "_runtime" / "judgment" / "fixtures"
TRACES = RUNTIME_FIXTURES / "traces"
SUMMARIES = RUNTIME_FIXTURES / "case-summaries"
EXCERPTS = RUNTIME_FIXTURES / "excerpts"
EXPORTER = REPO / "scripts" / "export-mindthus-case.py"
VALIDATOR = REPO / "scripts" / "validate-mindthus-case.py"


class CaseExportTests(unittest.TestCase):
    def test_three_canonical_case_intents_export_and_validate(self):
        fixtures = (
            ("judgment_failure", "direct-execution.json", "judgment-failure.json", "failure-fixture"),
            ("value_delta", "intervention.json", "value-delta.json", "value-delta-fixture"),
            ("routing_ambiguity", "information-acquisition.json", "minimal-redacted.json", "redacted-fixture"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            for case_type, trace_name, summary_name, case_id in fixtures:
                with self.subTest(case_type=case_type):
                    package = create_case_package(
                        output_root=output_root,
                        trace_path=TRACES / trace_name,
                        summary_path=SUMMARIES / summary_name,
                        case_type=case_type,
                        case_id=case_id,
                    )
                    findings = validate_case_package(package)
                    self.assertFalse([item for item in findings if item.severity == "block"])
                    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
                    self.assertTrue(manifest["consent"]["export_requested_by_user"])
                    self.assertTrue(manifest["consent"]["review_required_before_share"])
                    self.assertFalse(manifest["consent"]["automatic_upload"])
                    self.assertFalse(manifest["privacy"]["contains_raw_prompt"])
                    self.assertFalse(manifest["privacy"]["contains_raw_answer"])
                    self.assertFalse(manifest["privacy"]["contains_attachments"])

    def test_excerpt_requires_explicit_redaction_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(CaseExportError) as caught:
                create_case_package(
                    output_root=Path(tmp),
                    trace_path=TRACES / "intervention.json",
                    summary_path=SUMMARIES / "value-delta.json",
                    case_type="value_delta",
                    case_id="excerpt-without-confirmation",
                    excerpts=[("observation", EXCERPTS / "redacted-example.txt")],
                )

        self.assertTrue(
            any(item.code == "excerpt-confirmation-required" for item in caught.exception.findings)
        )

    def test_confirmed_redacted_excerpt_is_indexed_and_review_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = create_case_package(
                output_root=Path(tmp),
                trace_path=TRACES / "intervention.json",
                summary_path=SUMMARIES / "value-delta.json",
                case_type="value_delta",
                case_id="confirmed-redacted-excerpt",
                excerpts=[("observation", EXCERPTS / "redacted-example.txt")],
                excerpts_confirmed_redacted=True,
            )
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["files"]["excerpts"], ["excerpts/observation.txt"])
            self.assertTrue(manifest["privacy"]["contains_user_selected_excerpts"])
            self.assertEqual(manifest["privacy"]["redaction_status"], "review_required")
            self.assertTrue((package / "excerpts" / "observation.txt").is_file())

    def test_secret_pattern_blocks_explicit_excerpt(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / "secret.txt"
            secret.write_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")

            with self.assertRaises(CaseExportError) as caught:
                create_case_package(
                    output_root=Path(tmp),
                    trace_path=TRACES / "intervention.json",
                    summary_path=SUMMARIES / "value-delta.json",
                    case_type="value_delta",
                    case_id="secret-excerpt",
                    excerpts=[("secret", secret)],
                    excerpts_confirmed_redacted=True,
                )

        self.assertTrue(any(item.code == "sensitive-bearer-token" for item in caught.exception.findings))

    def test_validator_blocks_manifest_that_enables_automatic_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = create_case_package(
                output_root=Path(tmp),
                trace_path=TRACES / "direct-execution.json",
                summary_path=SUMMARIES / "judgment-failure.json",
                case_type="judgment_failure",
                case_id="tampered-manifest",
            )
            manifest_path = package / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["consent"]["automatic_upload"] = True
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            findings = validate_case_package(package)

        self.assertTrue(any(item.code == "automatic-upload-forbidden" for item in findings))

    def test_identifier_warning_is_disclosed_without_blocking_local_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = create_case_package(
                output_root=Path(tmp),
                trace_path=TRACES / "direct-execution.json",
                summary_path=SUMMARIES / "minimal-redacted.json",
                case_type="routing_ambiguity",
                case_id="warning-disclosure",
                source_client="reviewer@example.com",
            )
            findings = validate_case_package(package)
            manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
            privacy_scan = json.loads((package / "privacy-scan.json").read_text(encoding="utf-8"))

        self.assertFalse([item for item in findings if item.severity == "block"])
        self.assertTrue(any(item.code == "review-email-address" for item in findings))
        self.assertEqual(manifest["privacy"]["pattern_scan_status"], "warnings")
        self.assertEqual(privacy_scan["status"], "warnings")

    def test_validator_rejects_tampered_privacy_scan_status_and_warning_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = create_case_package(
                output_root=Path(tmp),
                trace_path=TRACES / "direct-execution.json",
                summary_path=SUMMARIES / "minimal-redacted.json",
                case_type="routing_ambiguity",
                case_id="tampered-privacy-scan",
                source_client="reviewer@example.com",
            )
            privacy_scan_path = package / "privacy-scan.json"
            privacy_scan = json.loads(privacy_scan_path.read_text(encoding="utf-8"))
            privacy_scan["status"] = "passed"
            privacy_scan["warning_codes"] = []
            privacy_scan_path.write_text(
                json.dumps(privacy_scan, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            findings = validate_case_package(package)

        self.assertTrue(
            any(item.code == "scan-status-mismatch" and item.subject == "privacy-scan.json" for item in findings)
        )
        self.assertTrue(any(item.code == "warning-code-mismatch" for item in findings))

    def test_validator_rejects_missing_manifest_contract_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = create_case_package(
                output_root=Path(tmp),
                trace_path=TRACES / "direct-execution.json",
                summary_path=SUMMARIES / "judgment-failure.json",
                case_type="judgment_failure",
                case_id="missing-manifest-field",
            )
            manifest_path = package / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["source_client"]
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            findings = validate_case_package(package)

        self.assertTrue(
            any(item.code == "missing-field" and "source_client" in item.message for item in findings)
        )

    def test_cli_creates_local_package_and_validator_requires_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            export = subprocess.run(
                [
                    "python3",
                    str(EXPORTER),
                    "--trace",
                    str(TRACES / "intervention.json"),
                    "--summary",
                    str(SUMMARIES / "value-delta.json"),
                    "--case-type",
                    "value_delta",
                    "--out-dir",
                    tmp,
                    "--case-id",
                    "cli-case-export",
                ],
                cwd=REPO,
                text=True,
                capture_output=True,
            )
            package = Path(tmp) / "mindthus-case-cli-case-export"
            validate = subprocess.run(
                ["python3", str(VALIDATOR), str(package), "--json"],
                cwd=REPO,
                text=True,
                capture_output=True,
            )

        self.assertEqual(export.returncode, 0, export.stderr + export.stdout)
        self.assertIn("automatic_upload: false", export.stdout)
        self.assertEqual(validate.returncode, 0, validate.stderr + validate.stdout)
        report = json.loads(validate.stdout)
        self.assertEqual(report["status"], "review_required")
        self.assertIn("separate user action", report["sharing_boundary"])


if __name__ == "__main__":
    unittest.main()
