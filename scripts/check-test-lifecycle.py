#!/usr/bin/env python3
"""Validate the Mindthus test lifecycle registry against executable test files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "tests" / "test-lifecycle-registry.json"
SCHEMA_VERSION = "mindthus.test-lifecycle.v1"
LIFECYCLE_STATES = {
    "active_gate",
    "active_regression",
    "historical_guard",
    "candidate_consolidate",
    "candidate_archive",
    "obsolete",
}
SUITE_ROLES = {"unit", "contract", "fidelity", "pressure", "acceptance", "fixture", "historical_report", "mixed"}
RUNTIME_COSTS = {"low", "medium", "high", "unknown"}
OWNERS = {"router", "primitive", "skill", "tplan", "packaging", "release", "benchmark", "runtime", "shared"}


def finding(severity: str, code: str, message: str, subject: str = "") -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message, "subject": subject}


def load_registry(path: Path) -> tuple[Any, list[dict[str, str]]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except OSError as exc:
        return None, [finding("block", "read-failed", f"failed to read registry: {exc}", str(path))]
    except UnicodeDecodeError as exc:
        return None, [finding("block", "decode-failed", f"registry must be UTF-8: {exc}", str(path))]
    except json.JSONDecodeError as exc:
        return None, [
            finding(
                "block",
                "invalid-json",
                f"invalid registry JSON at line {exc.lineno} column {exc.colno}: {exc.msg}",
                str(path),
            )
        ]


def _expand_entry_paths(entry: dict[str, Any], root: Path) -> tuple[set[str], list[dict[str, str]]]:
    paths: set[str] = set()
    findings: list[dict[str, str]] = []
    test_id = str(entry.get("test_id") or "unknown")
    raw_paths = entry.get("paths") or []
    raw_globs = entry.get("path_globs") or []
    if not isinstance(raw_paths, list) or not isinstance(raw_globs, list):
        return set(), [finding("block", "invalid-path-index", "paths and path_globs must be lists", test_id)]
    if not raw_paths and not raw_globs:
        findings.append(finding("block", "missing-path-index", "entry needs paths or path_globs", test_id))
    for raw in raw_paths:
        if not isinstance(raw, str) or not raw.strip():
            findings.append(finding("block", "invalid-path", "paths entries must be non-empty strings", test_id))
            continue
        path = root / raw
        if not path.is_file():
            findings.append(finding("block", "missing-path", f"registered test path does not exist: {raw}", test_id))
        paths.add(Path(raw).as_posix())
    for raw in raw_globs:
        if not isinstance(raw, str) or not raw.strip():
            findings.append(finding("block", "invalid-glob", "path_globs entries must be non-empty strings", test_id))
            continue
        matches = [path for path in root.glob(raw) if path.is_file()]
        if not matches:
            findings.append(finding("block", "empty-glob", f"registered glob matched no files: {raw}", test_id))
        for path in matches:
            paths.add(path.relative_to(root).as_posix())
    return paths, findings


def validate_registry(data: Any, root: Path = ROOT) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if not isinstance(data, dict):
        return {
            "schema_version": "mindthus.test-lifecycle-report.v1",
            "status": "invalid",
            "findings": [finding("block", "invalid-root", "registry root must be an object")],
        }
    if data.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            finding("block", "unsupported-schema", f"schema_version must be {SCHEMA_VERSION}", "registry")
        )
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        findings.append(finding("block", "invalid-entries", "entries must be a non-empty list", "registry"))
        entries = []
    gating_states = data.get("gating_states")
    if not isinstance(gating_states, list) or not gating_states:
        findings.append(finding("block", "invalid-gating-states", "gating_states must be a non-empty list", "registry"))
        gating_states = []
    for state in gating_states:
        if state not in LIFECYCLE_STATES:
            findings.append(finding("block", "unsupported-state", f"unsupported gating state: {state}", "registry"))

    coverage: dict[str, list[str]] = {}
    seen_ids: set[str] = set()
    status_counts: dict[str, int] = {state: 0 for state in sorted(LIFECYCLE_STATES)}
    for entry in entries:
        if not isinstance(entry, dict):
            findings.append(finding("block", "invalid-entry", "each entry must be an object", "registry"))
            continue
        test_id = entry.get("test_id")
        if not isinstance(test_id, str) or not test_id.strip():
            findings.append(finding("block", "invalid-test-id", "test_id must be a non-empty string", "registry"))
            test_id = "unknown"
        elif test_id in seen_ids:
            findings.append(finding("block", "duplicate-test-id", f"duplicate test_id: {test_id}", test_id))
        seen_ids.add(str(test_id))

        owner = entry.get("owner")
        if owner not in OWNERS:
            findings.append(finding("block", "invalid-owner", f"unsupported owner: {owner}", str(test_id)))
        protects = entry.get("protects")
        if not isinstance(protects, list) or not protects or any(not isinstance(item, str) or not item.strip() for item in protects):
            findings.append(finding("block", "invalid-protects", "protects must be a non-empty string list", str(test_id)))
        status = entry.get("lifecycle_status")
        if status not in LIFECYCLE_STATES:
            findings.append(finding("block", "invalid-lifecycle-status", f"unsupported lifecycle_status: {status}", str(test_id)))
        else:
            status_counts[str(status)] += 1
        if entry.get("suite_role") not in SUITE_ROLES:
            findings.append(finding("block", "invalid-suite-role", f"unsupported suite_role: {entry.get('suite_role')}", str(test_id)))
        if entry.get("runtime_cost") not in RUNTIME_COSTS:
            findings.append(finding("block", "invalid-runtime-cost", f"unsupported runtime_cost: {entry.get('runtime_cost')}", str(test_id)))
        if status in {"candidate_consolidate", "candidate_archive", "obsolete"}:
            replacement = entry.get("replacement")
            notes = entry.get("notes")
            if not replacement and (not isinstance(notes, str) or not notes.strip()):
                findings.append(
                    finding(
                        "block",
                        "retirement-evidence-required",
                        "candidate or obsolete entries need replacement or residual-risk notes",
                        str(test_id),
                    )
                )
        paths, path_findings = _expand_entry_paths(entry, root)
        findings.extend(path_findings)
        for path in paths:
            coverage.setdefault(path, []).append(str(test_id))

    executable = {
        path.relative_to(root).as_posix()
        for path in (root / "tests").rglob("test_*.py")
        if path.is_file()
    }
    uncovered = sorted(executable - set(coverage))
    overcovered = {path: owners for path, owners in coverage.items() if len(owners) > 1 and path in executable}
    unexpected = sorted(set(coverage) - executable)
    for path in uncovered:
        findings.append(finding("block", "unregistered-test", f"executable test is not registered: {path}", path))
    for path, owners in sorted(overcovered.items()):
        findings.append(
            finding("block", "duplicate-coverage", f"test is covered by multiple entries: {', '.join(owners)}", path)
        )
    for path in unexpected:
        findings.append(finding("warn", "non-executable-registration", f"registered path is not test_*.py: {path}", path))

    candidates = data.get("review_candidates") or []
    if not isinstance(candidates, list):
        findings.append(finding("block", "invalid-review-candidates", "review_candidates must be a list", "registry"))
        candidates = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            findings.append(finding("block", "invalid-review-candidate", "review candidate must be an object", "registry"))
            continue
        for field in ("test_id", "proposed_status", "evidence", "current_blocker"):
            if not isinstance(candidate.get(field), str) or not candidate[field].strip():
                findings.append(
                    finding("block", "incomplete-review-candidate", f"review candidate missing {field}", "registry")
                )
        if candidate.get("proposed_status") not in {"candidate_consolidate", "candidate_archive", "obsolete"}:
            findings.append(
                finding("block", "invalid-proposed-status", "review candidate proposed_status is invalid", "registry")
            )

    blocks = [item for item in findings if item["severity"] == "block"]
    return {
        "schema_version": "mindthus.test-lifecycle-report.v1",
        "status": "valid" if not blocks else "invalid",
        "executable_test_file_count": len(executable),
        "registered_executable_test_file_count": len(executable & set(coverage)),
        "entry_count": len(entries),
        "status_counts": status_counts,
        "gating_states": gating_states,
        "review_candidate_count": len(candidates),
        "findings": findings,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    data, load_findings = load_registry(args.registry)
    if load_findings:
        report = {
            "schema_version": "mindthus.test-lifecycle-report.v1",
            "status": "invalid",
            "findings": load_findings,
        }
    else:
        report = validate_registry(data)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Mindthus Test Lifecycle Registry")
        print(f"Registry: {args.registry}")
        print(f"Status: {report['status']}")
        if "executable_test_file_count" in report:
            print(f"Executable test files: {report['executable_test_file_count']}")
            print(f"Registered executable test files: {report['registered_executable_test_file_count']}")
            print(f"Registry entries: {report['entry_count']}")
        print()
        if not report.get("findings"):
            print("Registry covers every executable test file exactly once.")
        else:
            for item in report["findings"]:
                subject = f" [{item['subject']}]" if item.get("subject") else ""
                print(f"- {item['severity'].upper()} [{item['code']}]{subject}: {item['message']}")
    return 1 if report["status"] != "valid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
