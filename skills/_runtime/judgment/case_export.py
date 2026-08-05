"""Local-only, user-controlled Mindthus case export contract.

The exporter creates reviewable packages on local disk. It never uploads data and
never includes raw prompts, answers, attachments, or task logs by default.
"""

from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from _runtime.core.report import Finding, finding
from _runtime.judgment.trace import (
    load_judgment_trace,
    validate_judgment_trace,
    write_judgment_trace,
)


CASE_EXPORT_SCHEMA_VERSION = "mindthus.case-export.v1"
CASE_SUMMARY_SCHEMA_VERSION = "mindthus.case-summary.v1"
CASE_TYPES = {
    "judgment_failure",
    "judgment_repair",
    "value_delta",
    "routing_ambiguity",
    "test_regression_candidate",
}
SUMMARY_FIELDS = {
    "schema_version",
    "decision_context",
    "observed_failure_or_value_delta",
    "active_judgment_object",
    "selected_route_or_method",
    "signal",
    "evidence_available",
    "evidence_missing",
    "decision_delta",
    "learning_hypothesis",
    "uncertainty",
    "redaction_notes",
}
SUMMARY_REQUIRED_FIELDS = set(SUMMARY_FIELDS)
CASE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,63}$")
MAX_EXCERPT_BYTES = 1024 * 1024
ALLOWED_ROOT_FILES = {
    "manifest.json",
    "judgment-trace.json",
    "case.md",
    "README.md",
    "privacy-scan.json",
}

BLOCK_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "openai-style-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "bearer-token": re.compile(r"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE),
    "password-assignment": re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*[^\s]{6,}", re.IGNORECASE),
}
WARN_PATTERNS = {
    "email-address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "home-path": re.compile(r"/(?:home|Users)/[^/\s]+/"),
    "ipv4-address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


class CaseExportError(ValueError):
    """Raised when export inputs or a package violate the local contract."""

    def __init__(self, findings: Iterable[Finding]):
        self.findings = list(findings)
        message = "; ".join(item.message for item in self.findings) or "invalid case export"
        super().__init__(message)


def new_case_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{secrets.token_hex(4)}"


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list_findings(value: Any, field: str) -> list[Finding]:
    if not isinstance(value, list):
        return [finding("block", "invalid-field", f"{field} must be a list", "case-summary")]
    return [
        finding("block", "invalid-list-item", f"{field}[{index}] must be a non-empty string", "case-summary")
        for index, item in enumerate(value)
        if not _non_empty_string(item)
    ]


def validate_case_summary(data: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(data, dict):
        return [finding("block", "invalid-root", "case summary root must be an object")]
    for field in sorted(set(data) - SUMMARY_FIELDS):
        findings.append(finding("block", "unknown-field", f"unsupported summary field: {field}", "case-summary"))
    for field in sorted(SUMMARY_REQUIRED_FIELDS - set(data)):
        findings.append(finding("block", "missing-field", f"missing summary field: {field}", "case-summary"))
    if data.get("schema_version") != CASE_SUMMARY_SCHEMA_VERSION:
        findings.append(
            finding(
                "block",
                "unsupported-schema",
                f"summary schema_version must be {CASE_SUMMARY_SCHEMA_VERSION}",
                "case-summary",
            )
        )
    for field in (
        "decision_context",
        "observed_failure_or_value_delta",
        "active_judgment_object",
        "selected_route_or_method",
        "signal",
        "learning_hypothesis",
        "uncertainty",
        "redaction_notes",
    ):
        if not _non_empty_string(data.get(field)):
            findings.append(finding("block", "invalid-field", f"{field} must be a non-empty string", "case-summary"))
    for field in ("evidence_available", "evidence_missing", "decision_delta"):
        findings.extend(_string_list_findings(data.get(field), field))
    return findings


def load_case_summary(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CaseExportError([finding("block", "read-failed", f"failed to read {path}: {exc}")]) from exc
    except UnicodeDecodeError as exc:
        raise CaseExportError([finding("block", "decode-failed", f"failed to decode {path} as UTF-8: {exc}")]) from exc
    except json.JSONDecodeError as exc:
        raise CaseExportError(
            [finding("block", "invalid-json", f"invalid summary JSON at line {exc.lineno} column {exc.colno}: {exc.msg}")]
        ) from exc
    findings = validate_case_summary(data)
    if findings:
        raise CaseExportError(findings)
    assert isinstance(data, dict)
    return data


def scan_text(text: str, subject: str) -> list[Finding]:
    findings: list[Finding] = []
    for code, pattern in BLOCK_PATTERNS.items():
        if pattern.search(text):
            findings.append(
                finding(
                    "block",
                    f"sensitive-{code}",
                    f"possible high-risk secret detected in {subject}; redact it before export",
                    subject,
                )
            )
    for code, pattern in WARN_PATTERNS.items():
        if pattern.search(text):
            findings.append(
                finding(
                    "warn",
                    f"review-{code}",
                    f"possible identifying content detected in {subject}; review before sharing",
                    subject,
                )
            )
    return findings


def _safe_excerpt_name(label: str, source: Path, used: set[str]) -> str:
    base = label.strip() or source.stem
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-._") or "excerpt"
    suffix = source.suffix.lower() if source.suffix.lower() in {".md", ".txt", ".json"} else ".txt"
    if base.lower().endswith(suffix):
        name = base
    else:
        name = f"{base}{suffix}"
    candidate = name
    index = 2
    while candidate in used:
        candidate = f"{Path(name).stem}-{index}{Path(name).suffix}"
        index += 1
    used.add(candidate)
    return candidate


def _read_explicit_excerpt(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise CaseExportError([finding("block", "invalid-excerpt", f"excerpt must be a regular file: {path}")])
    size = path.stat().st_size
    if size > MAX_EXCERPT_BYTES:
        raise CaseExportError(
            [finding("block", "excerpt-too-large", f"excerpt exceeds {MAX_EXCERPT_BYTES} bytes: {path}")]
        )
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CaseExportError(
            [finding("block", "invalid-excerpt", f"excerpt must be UTF-8 text: {path}")]
        ) from exc


def _markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- None recorded."


def render_case_markdown(case_type: str, summary: dict[str, Any]) -> str:
    return f"""# Mindthus Case Summary

Case type: `{case_type}`

## Decision Context

{summary['decision_context']}

## Observed Failure Or Value Delta

{summary['observed_failure_or_value_delta']}

## Active Judgment Object

{summary['active_judgment_object']}

## Selected Route Or Method

{summary['selected_route_or_method']}

## Missed Or Correctly Detected Signal

{summary['signal']}

## Evidence Available

{_markdown_list(summary['evidence_available'])}

## Evidence Missing

{_markdown_list(summary['evidence_missing'])}

## Decision Delta

{_markdown_list(summary['decision_delta'])}

## Expected Repair Or Learning Hypothesis

{summary['learning_hypothesis']}

## Uncertainty

{summary['uncertainty']}

## Redaction Notes

{summary['redaction_notes']}
"""


def _package_readme() -> str:
    return """# Local Mindthus Case Export

This package was created locally at the user's request. It has not been uploaded.

Before sharing:

1. Read `manifest.json` and confirm every privacy flag is accurate.
2. Read `case.md`, `judgment-trace.json`, and every file under `excerpts/`.
3. Remove names, credentials, private paths, customer data, and unnecessary raw text.
4. Run `python3 scripts/validate-mindthus-case.py <package-directory>` again.
5. Share the package only through a separate, explicit user action.

The validator detects only a limited set of suspicious content patterns. A passing
report does not prove anonymity, consent, semantic correctness, or benchmark value.

Delete the package directory to remove this local export. No central copy is created
by the exporter.
"""


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_case_package(
    *,
    output_root: Path,
    trace_path: Path,
    summary_path: Path,
    case_type: str,
    case_id: str | None = None,
    source_client: str | None = None,
    source_method: str | None = None,
    benchmark_case_id: str | None = None,
    related_test_id: str | None = None,
    related_issue: str | None = None,
    excerpts: list[tuple[str, Path]] | None = None,
    excerpts_confirmed_redacted: bool = False,
) -> Path:
    """Create one local package. No network operation is performed."""

    if case_type not in CASE_TYPES:
        raise CaseExportError(
            [finding("block", "unsupported-case-type", f"case_type must be one of: {', '.join(sorted(CASE_TYPES))}")]
        )
    resolved_case_id = case_id or new_case_id()
    if not CASE_ID_RE.fullmatch(resolved_case_id):
        raise CaseExportError(
            [finding("block", "invalid-case-id", "case_id must use 3-64 letters, numbers, '.', '_', or '-'")]
        )

    trace = load_judgment_trace(trace_path)
    summary = load_case_summary(summary_path)
    case_markdown = render_case_markdown(case_type, summary)
    input_scan = scan_text(case_markdown, "case.md")
    metadata_for_scan = json.dumps(
        {
            "case_id": resolved_case_id,
            "source_client": source_client,
            "source_method": source_method,
            "benchmark_case_id": benchmark_case_id,
            "related_test_id": related_test_id,
            "related_issue": related_issue,
        },
        ensure_ascii=False,
    )
    input_scan.extend(scan_text(metadata_for_scan, "manifest metadata"))
    blocking = [item for item in input_scan if item.severity == "block"]
    if blocking:
        raise CaseExportError(blocking)

    explicit_excerpts = excerpts or []
    if explicit_excerpts and not excerpts_confirmed_redacted:
        raise CaseExportError(
            [
                finding(
                    "block",
                    "excerpt-confirmation-required",
                    "explicit excerpts require --confirm-excerpts-redacted",
                    "excerpts",
                )
            ]
        )

    prepared_excerpts: list[tuple[str, str]] = []
    scan_findings = list(input_scan)
    used_names: set[str] = set()
    for label, source in explicit_excerpts:
        text = _read_explicit_excerpt(source)
        name = _safe_excerpt_name(label, source, used_names)
        excerpt_findings = scan_text(text, f"excerpts/{name}")
        blocking = [item for item in excerpt_findings if item.severity == "block"]
        if blocking:
            raise CaseExportError(blocking)
        scan_findings.extend(excerpt_findings)
        prepared_excerpts.append((name, text))

    package_dir = output_root / f"mindthus-case-{resolved_case_id}"
    if package_dir.exists():
        raise CaseExportError(
            [finding("block", "output-exists", f"refusing to overwrite existing package: {package_dir}")]
        )
    package_dir.mkdir(parents=True, exist_ok=False)
    try:
        write_judgment_trace(package_dir / "judgment-trace.json", trace)
        (package_dir / "case.md").write_text(case_markdown, encoding="utf-8")
        (package_dir / "README.md").write_text(_package_readme(), encoding="utf-8")
        if prepared_excerpts:
            excerpt_dir = package_dir / "excerpts"
            excerpt_dir.mkdir()
            for name, text in prepared_excerpts:
                (excerpt_dir / name).write_text(text, encoding="utf-8")

        warning_codes = sorted({item.code for item in scan_findings if item.severity == "warn"})
        privacy_scan = {
            "schema_version": "mindthus.case-privacy-scan.v1",
            "status": "warnings" if warning_codes else "passed",
            "warning_codes": warning_codes,
            "note": "Pattern scan only; passing does not prove anonymity or adequate redaction.",
        }
        _write_json(package_dir / "privacy-scan.json", privacy_scan)

        manifest = {
            "schema_version": CASE_EXPORT_SCHEMA_VERSION,
            "case_id": resolved_case_id,
            "case_type": case_type,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_client": source_client,
            "source_method": source_method,
            "consent": {
                "export_requested_by_user": True,
                "review_required_before_share": True,
                "automatic_upload": False,
            },
            "privacy": {
                "contains_raw_prompt": False,
                "contains_raw_answer": False,
                "contains_attachments": False,
                "contains_user_selected_excerpts": bool(prepared_excerpts),
                "redaction_status": "review_required",
                "pattern_scan_status": privacy_scan["status"],
            },
            "links": {
                "benchmark_case_id": benchmark_case_id,
                "related_test_id": related_test_id,
                "related_issue": related_issue,
            },
            "files": {
                "judgment_trace": "judgment-trace.json",
                "case_summary": "case.md",
                "privacy_notice": "README.md",
                "privacy_scan": "privacy-scan.json",
                "excerpts": [f"excerpts/{name}" for name, _ in prepared_excerpts],
            },
        }
        _write_json(package_dir / "manifest.json", manifest)
    except Exception:
        for path in sorted(package_dir.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        package_dir.rmdir()
        raise

    findings = validate_case_package(package_dir)
    blocking = [item for item in findings if item.severity == "block"]
    if blocking:
        raise CaseExportError(blocking)
    return package_dir


def _validate_manifest(manifest: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(manifest, dict):
        return [finding("block", "invalid-manifest", "manifest root must be an object", "manifest.json")]
    expected_fields = {
        "schema_version",
        "case_id",
        "case_type",
        "created_at_utc",
        "source_client",
        "source_method",
        "consent",
        "privacy",
        "links",
        "files",
    }
    for field in sorted(set(manifest) - expected_fields):
        findings.append(finding("block", "unknown-field", f"unsupported manifest field: {field}", "manifest.json"))
    for field in sorted(expected_fields - set(manifest)):
        findings.append(finding("block", "missing-field", f"missing manifest field: {field}", "manifest.json"))
    if manifest.get("schema_version") != CASE_EXPORT_SCHEMA_VERSION:
        findings.append(
            finding(
                "block",
                "unsupported-schema",
                f"manifest schema_version must be {CASE_EXPORT_SCHEMA_VERSION}",
                "manifest.json",
            )
        )
    case_id = manifest.get("case_id")
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        findings.append(finding("block", "invalid-case-id", "manifest case_id is invalid", "manifest.json"))
    if manifest.get("case_type") not in CASE_TYPES:
        findings.append(finding("block", "unsupported-case-type", "manifest case_type is invalid", "manifest.json"))
    created_at = manifest.get("created_at_utc")
    if not isinstance(created_at, str):
        findings.append(finding("block", "invalid-created-at", "created_at_utc must be an ISO-8601 string", "manifest.json"))
    else:
        try:
            parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            findings.append(finding("block", "invalid-created-at", "created_at_utc must be ISO-8601", "manifest.json"))
        else:
            if parsed_created_at.tzinfo is None:
                findings.append(finding("block", "invalid-created-at", "created_at_utc must include a timezone", "manifest.json"))
    for field in ("source_client", "source_method"):
        if manifest.get(field) is not None and not _non_empty_string(manifest.get(field)):
            findings.append(finding("block", "invalid-source", f"{field} must be null or a non-empty string", "manifest.json"))

    consent = manifest.get("consent")
    if not isinstance(consent, dict):
        findings.append(finding("block", "invalid-consent", "consent must be an object", "manifest.json"))
    else:
        expected_consent_fields = {
            "export_requested_by_user",
            "review_required_before_share",
            "automatic_upload",
        }
        for field in sorted(set(consent) - expected_consent_fields):
            findings.append(finding("block", "unknown-field", f"unsupported consent field: {field}", "manifest.json"))
        if consent.get("export_requested_by_user") is not True:
            findings.append(finding("block", "consent-required", "export_requested_by_user must be true", "manifest.json"))
        if consent.get("review_required_before_share") is not True:
            findings.append(finding("block", "review-required", "review_required_before_share must be true", "manifest.json"))
        if consent.get("automatic_upload") is not False:
            findings.append(finding("block", "automatic-upload-forbidden", "automatic_upload must be false", "manifest.json"))
    privacy = manifest.get("privacy")
    if not isinstance(privacy, dict):
        findings.append(finding("block", "invalid-privacy", "privacy must be an object", "manifest.json"))
    else:
        expected_privacy_fields = {
            "contains_raw_prompt",
            "contains_raw_answer",
            "contains_attachments",
            "contains_user_selected_excerpts",
            "redaction_status",
            "pattern_scan_status",
        }
        for field in sorted(set(privacy) - expected_privacy_fields):
            findings.append(finding("block", "unknown-field", f"unsupported privacy field: {field}", "manifest.json"))
        for field in ("contains_raw_prompt", "contains_raw_answer", "contains_attachments"):
            if privacy.get(field) is not False:
                findings.append(
                    finding("block", "raw-content-forbidden", f"{field} must be false in v1 exports", "manifest.json")
                )
        if not isinstance(privacy.get("contains_user_selected_excerpts"), bool):
            findings.append(
                finding("block", "invalid-privacy", "contains_user_selected_excerpts must be a boolean", "manifest.json")
            )
        if privacy.get("redaction_status") != "review_required":
            findings.append(
                finding("block", "review-required", "redaction_status must remain review_required", "manifest.json")
            )
        if privacy.get("pattern_scan_status") not in {"passed", "warnings"}:
            findings.append(
                finding("block", "invalid-scan-status", "pattern_scan_status must be passed or warnings", "manifest.json")
            )

    links = manifest.get("links")
    expected_link_fields = {"benchmark_case_id", "related_test_id", "related_issue"}
    if not isinstance(links, dict):
        findings.append(finding("block", "invalid-links", "links must be an object", "manifest.json"))
    else:
        for field in sorted(set(links) - expected_link_fields):
            findings.append(finding("block", "unknown-field", f"unsupported links field: {field}", "manifest.json"))
        for field in expected_link_fields:
            if links.get(field) is not None and not _non_empty_string(links.get(field)):
                findings.append(finding("block", "invalid-link", f"{field} must be null or a non-empty string", "manifest.json"))

    files = manifest.get("files")
    expected_file_fields = {"judgment_trace", "case_summary", "privacy_notice", "privacy_scan", "excerpts"}
    if not isinstance(files, dict) or not isinstance(files.get("excerpts"), list):
        findings.append(finding("block", "invalid-files-index", "files.excerpts must be a list", "manifest.json"))
    else:
        for field in sorted(set(files) - expected_file_fields):
            findings.append(finding("block", "unknown-field", f"unsupported files field: {field}", "manifest.json"))
        expected_paths = {
            "judgment_trace": "judgment-trace.json",
            "case_summary": "case.md",
            "privacy_notice": "README.md",
            "privacy_scan": "privacy-scan.json",
        }
        for field, expected in expected_paths.items():
            if files.get(field) != expected:
                findings.append(finding("block", "invalid-files-index", f"{field} must be {expected}", "manifest.json"))
        for index, value in enumerate(files.get("excerpts", [])):
            safe_path = isinstance(value, str) and bool(
                re.fullmatch(r"excerpts/[A-Za-z0-9][A-Za-z0-9._-]*", value)
            )
            if safe_path and Path(value).name in {".", ".."}:
                safe_path = False
            if not safe_path:
                findings.append(
                    finding("block", "invalid-excerpt-path", f"files.excerpts[{index}] is not a safe excerpt path", "manifest.json")
                )
    return findings


def validate_case_package(package_dir: Path) -> list[Finding]:
    """Validate package shape and scan text. This does not prove anonymization."""

    findings: list[Finding] = []
    if not package_dir.is_dir() or package_dir.is_symlink():
        return [finding("block", "invalid-package", f"package must be a directory: {package_dir}")]

    for child in package_dir.iterdir():
        if child.is_symlink():
            findings.append(finding("block", "symlink-forbidden", f"symlink is not allowed: {child.name}", child.name))
        elif child.is_file() and child.name not in ALLOWED_ROOT_FILES:
            findings.append(finding("block", "unexpected-file", f"unexpected root file: {child.name}", child.name))
        elif child.is_dir() and child.name != "excerpts":
            findings.append(finding("block", "unexpected-directory", f"unexpected directory: {child.name}", child.name))

    for required in ("manifest.json", "judgment-trace.json", "case.md", "README.md", "privacy-scan.json"):
        if not (package_dir / required).is_file():
            findings.append(finding("block", "missing-file", f"missing required file: {required}", required))

    manifest: dict[str, Any] | None = None
    privacy_scan_data: dict[str, Any] | None = None
    manifest_path = package_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.append(finding("block", "invalid-manifest", f"failed to read manifest: {exc}", "manifest.json"))
        else:
            findings.extend(_validate_manifest(manifest))
            case_id = manifest.get("case_id")
            if isinstance(case_id, str) and package_dir.name != f"mindthus-case-{case_id}":
                findings.append(
                    finding(
                        "block",
                        "package-name-mismatch",
                        f"package directory must be named mindthus-case-{case_id}",
                        package_dir.name,
                    )
                )

    privacy_scan_path = package_dir / "privacy-scan.json"
    if privacy_scan_path.is_file():
        try:
            loaded_privacy_scan = json.loads(privacy_scan_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.append(
                finding(
                    "block",
                    "invalid-privacy-scan",
                    f"failed to read privacy scan: {exc}",
                    "privacy-scan.json",
                )
            )
        else:
            if not isinstance(loaded_privacy_scan, dict):
                findings.append(
                    finding(
                        "block",
                        "invalid-privacy-scan",
                        "privacy scan root must be an object",
                        "privacy-scan.json",
                    )
                )
            else:
                privacy_scan_data = loaded_privacy_scan
                expected_scan_fields = {"schema_version", "status", "warning_codes", "note"}
                for field in sorted(set(privacy_scan_data) - expected_scan_fields):
                    findings.append(
                        finding(
                            "block",
                            "unknown-field",
                            f"unsupported privacy scan field: {field}",
                            "privacy-scan.json",
                        )
                    )
                if privacy_scan_data.get("schema_version") != "mindthus.case-privacy-scan.v1":
                    findings.append(
                        finding(
                            "block",
                            "unsupported-schema",
                            "privacy scan schema_version must be mindthus.case-privacy-scan.v1",
                            "privacy-scan.json",
                        )
                    )
                if privacy_scan_data.get("status") not in {"passed", "warnings"}:
                    findings.append(
                        finding(
                            "block",
                            "invalid-scan-status",
                            "privacy scan status must be passed or warnings",
                            "privacy-scan.json",
                        )
                    )
                warning_codes = privacy_scan_data.get("warning_codes")
                if not isinstance(warning_codes, list) or any(
                    not isinstance(item, str) or not item.strip() for item in warning_codes
                ):
                    findings.append(
                        finding(
                            "block",
                            "invalid-warning-codes",
                            "privacy scan warning_codes must be a string list",
                            "privacy-scan.json",
                        )
                    )
                if not _non_empty_string(privacy_scan_data.get("note")):
                    findings.append(
                        finding(
                            "block",
                            "invalid-note",
                            "privacy scan note must be a non-empty string",
                            "privacy-scan.json",
                        )
                    )

    trace_path = package_dir / "judgment-trace.json"
    if trace_path.is_file():
        try:
            trace_data = json.loads(trace_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.append(finding("block", "invalid-trace", f"failed to read judgment trace: {exc}", "judgment-trace.json"))
        else:
            for item in validate_judgment_trace(trace_data):
                findings.append(
                    finding(item.severity, f"trace-{item.code}", item.message, "judgment-trace.json")
                )

    indexed_excerpts: set[str] = set()
    if manifest and isinstance(manifest.get("files"), dict):
        values = manifest["files"].get("excerpts")
        if isinstance(values, list):
            indexed_excerpts = {str(value) for value in values}
    actual_excerpts: set[str] = set()
    excerpt_dir = package_dir / "excerpts"
    if excerpt_dir.exists():
        if not excerpt_dir.is_dir() or excerpt_dir.is_symlink():
            findings.append(finding("block", "invalid-excerpts", "excerpts must be a regular directory", "excerpts"))
        else:
            for path in excerpt_dir.rglob("*"):
                if path.is_symlink() or not path.is_file():
                    findings.append(finding("block", "invalid-excerpt", f"invalid excerpt entry: {path}", "excerpts"))
                    continue
                rel = path.relative_to(package_dir).as_posix()
                actual_excerpts.add(rel)
                if path.stat().st_size > MAX_EXCERPT_BYTES:
                    findings.append(finding("block", "excerpt-too-large", f"excerpt exceeds size limit: {rel}", rel))
    if indexed_excerpts != actual_excerpts:
        findings.append(
            finding(
                "block",
                "excerpt-index-mismatch",
                f"manifest excerpts {sorted(indexed_excerpts)} do not match files {sorted(actual_excerpts)}",
                "manifest.json",
            )
        )
    if manifest and isinstance(manifest.get("privacy"), dict):
        declared = manifest["privacy"].get("contains_user_selected_excerpts")
        if declared is not bool(actual_excerpts):
            findings.append(
                finding(
                    "block",
                    "excerpt-privacy-mismatch",
                    "contains_user_selected_excerpts does not match package contents",
                    "manifest.json",
                )
            )

    for path in package_dir.rglob("*"):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in {".json", ".md", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(finding("block", "non-utf8-content", f"file must be UTF-8 text: {path.name}", path.name))
            continue
        findings.extend(scan_text(text, path.relative_to(package_dir).as_posix()))

    actual_warning_codes = sorted({item.code for item in findings if item.severity == "warn"})
    actual_scan_status = "warnings" if actual_warning_codes else "passed"
    if manifest and isinstance(manifest.get("privacy"), dict):
        declared_scan_status = manifest["privacy"].get("pattern_scan_status")
        if declared_scan_status in {"passed", "warnings"} and declared_scan_status != actual_scan_status:
            findings.append(
                finding(
                    "block",
                    "scan-status-mismatch",
                    f"pattern_scan_status is {declared_scan_status} but validator observed {actual_scan_status}",
                    "manifest.json",
                )
            )
    if privacy_scan_data is not None:
        declared_privacy_scan_status = privacy_scan_data.get("status")
        if declared_privacy_scan_status in {"passed", "warnings"} and declared_privacy_scan_status != actual_scan_status:
            findings.append(
                finding(
                    "block",
                    "scan-status-mismatch",
                    f"privacy scan status is {declared_privacy_scan_status} but validator observed {actual_scan_status}",
                    "privacy-scan.json",
                )
            )
        declared_warning_codes = privacy_scan_data.get("warning_codes")
        if isinstance(declared_warning_codes, list) and all(
            isinstance(item, str) and item.strip() for item in declared_warning_codes
        ):
            normalized_declared_codes = sorted(set(declared_warning_codes))
            if normalized_declared_codes != actual_warning_codes:
                findings.append(
                    finding(
                        "block",
                        "warning-code-mismatch",
                        (
                            f"privacy scan warning_codes {normalized_declared_codes} do not match "
                            f"validator warnings {actual_warning_codes}"
                        ),
                        "privacy-scan.json",
                    )
                )

    return findings
