#!/usr/bin/env python3
"""Inventory and verify immutable benchmark archives without modifying the checkout.

Full inventory prints one row per source blob. Recovery drills write only to a fresh
TemporaryDirectory, compare every byte to the recorded Git blob, then remove that temp
copy. This tool never deletes HEAD files, fetches history, or rewrites a source tag.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import tempfile
from typing import Any

ROOT = "docs/benchmarks/runs/"
KEEP = {
    "REPORT.md", "HUMAN_REVIEW_PACKET.md", "EXTERNAL_AUDIT_HANDOFF.md",
    "MANUAL_PROBLEM_CASE_AUDIT.md", "run-manifest.json", "summary.json",
    "runtime-fingerprint.json", "eval-home-runtime-fingerprint.json",
    "contamination-report.json", "CODEX_HOME_CONFIG_SNAPSHOT.md",
    "activation-summary.json", "summary-aggregate.json", "runtime-fingerprint-strict.json",
    "runtime-fingerprint-strict-rerun.json", "runtime-fingerprint-strict-safe.json",
    "issue-108-variant-cases.jsonl", "judge-output-schema.json",
}
RAW_DIRS = {"answers", "prompts", "events", "judge-answers", "judge-events", "judge-prompts", "judge-stderr", "stderr"}
RAW_NAMES = {"raw-responses.jsonl", "score-records.jsonl", "runner.stdout.log", "runner.stderr.log"}
REPORT_NAMES = {
    "REPORT.md", "HUMAN_REVIEW_PACKET.md", "EXTERNAL_AUDIT_HANDOFF.md",
    "MANUAL_PROBLEM_CASE_AUDIT.md",
}
ARCHIVE_POINTER = "Immutable archive base: `d735d11c14d92325607fe6b844eb29f7c426df62`"


KEEP_REASONS = {
    "REPORT.md": "decision-bearing campaign report",
    "HUMAN_REVIEW_PACKET.md": "human-review evidence and adjudication guide",
    "EXTERNAL_AUDIT_HANDOFF.md": "external-audit evidence handoff",
    "MANUAL_PROBLEM_CASE_AUDIT.md": "manual problem-case audit evidence",
    "run-manifest.json": "run configuration and lineage manifest",
    "summary.json": "decision-bearing run summary",
    "runtime-fingerprint.json": "runtime lineage fingerprint",
    "eval-home-runtime-fingerprint.json": "evaluation runtime lineage fingerprint",
    "contamination-report.json": "decision-bearing contamination evidence",
    "CODEX_HOME_CONFIG_SNAPSHOT.md": "configuration evidence required to interpret the run",
    "activation-summary.json": "activation aggregate required to interpret run behavior",
    "summary-aggregate.json": "cross-repeat decision-bearing aggregate",
    "runtime-fingerprint-strict.json": "strict runtime lineage fingerprint",
    "runtime-fingerprint-strict-rerun.json": "strict rerun lineage fingerprint",
    "runtime-fingerprint-strict-safe.json": "strict safe-run lineage fingerprint",
    "issue-108-variant-cases.jsonl": "bounded case corpus defining the retained diagnostic",
    "judge-output-schema.json": "judge output contract required to interpret scored results",
}


MIGRATE_REASONS = {
    "answers": "per-call answer; aggregate and decision evidence retained in HEAD",
    "prompts": "per-call prompt; run configuration and decision evidence retained in HEAD",
    "events": "per-call event stream; aggregate and decision evidence retained in HEAD",
    "judge-answers": "per-call judge output; summary and decision evidence retained in HEAD",
    "judge-events": "per-call judge event stream; summary and decision evidence retained in HEAD",
    "judge-prompts": "per-call judge prompt; judge contract and summary retained in HEAD",
    "judge-stderr": "per-call judge diagnostic log; decision evidence retained in HEAD",
    "stderr": "per-call diagnostic log; decision evidence retained in HEAD",
    "raw-responses.jsonl": "raw per-call responses; aggregate and decision evidence retained in HEAD",
    "score-records.jsonl": "per-case score records; aggregate and decision evidence retained in HEAD",
    "runner.stdout.log": "runner diagnostic log; decision evidence retained in HEAD",
    "runner.stderr.log": "runner diagnostic log; decision evidence retained in HEAD",
}


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    normalized = str(path)
    root = ROOT.rstrip("/")
    inside_root = normalized == root or normalized.startswith(ROOT)
    if not inside_root or path.is_absolute() or ".." in path.parts or "\\" in value or normalized != value.rstrip("/"):
        raise ValueError(f"archive path must be canonical and inside {ROOT}: {value}")
    return normalized


def git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def classify(path: str) -> tuple[str, str]:
    p = PurePosixPath(path)
    if path.endswith("discarded-initial-run/README.txt"):
        return "keep", "records why the initial run was discarded"
    if p.name in KEEP:
        return "keep", KEEP_REASONS[p.name]
    raw_parts = [part for part in p.parts[3:] if part in RAW_DIRS]
    if p.name in RAW_NAMES:
        return "candidate_migrate", MIGRATE_REASONS[p.name]
    if raw_parts:
        return "candidate_migrate", MIGRATE_REASONS[raw_parts[0]]
    return "keep", "unclassified: retain pending individual review"


def build_manifest(repo: Path, source: str, scope: str = ROOT.rstrip("/")) -> dict[str, Any]:
    """Build the reviewed full-stock contract without changing the checkout."""
    rows = inventory(repo, source, scope)
    files = []
    for row in rows:
        path = row["path"]
        files.append({
            "path": path,
            "blob_oid": row["blob_oid"],
            "bytes": row["bytes"],
            "disposition": "migrate" if row["disposition"] == "candidate_migrate" else "keep",
            "reason": row["reason"],
            "recovery_ref": f"{source}:{path}",
        })
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    return {
        "schema_version": "mindthus.benchmark-archive-manifest.v2",
        "generated_from_head": head,
        "generated_from_tree": git(repo, "rev-parse", f"{head}^{{tree}}").decode().strip(),
        "source_commit": source,
        "source_tag_hint": "v1.9.1",
        "scope": safe_path(scope),
        "recovery": (
            "Every recovery_ref is an immutable Git commit:path destination in the existing "
            "Mindthus history. The remote tag v1.9.1 is an availability hint, not the identity anchor."
        ),
        "classification": (
            "All original unclassified names are explicitly kept. Migrate rows are limited to "
            "the policy's per-call directories and raw/log filenames."
        ),
        "files": files,
    }


def inventory(repo: Path, source: str, scope: str = ROOT.rstrip("/")) -> list[dict[str, Any]]:
    if re.fullmatch(r"[0-9a-f]{40}", source) is None:
        raise ValueError("archive source must be a complete immutable commit SHA")
    scope = safe_path(scope + "/" if scope == ROOT.rstrip("/") else scope)
    rows = []
    for raw in git(repo, "ls-tree", "-r", "-l", "-z", source, "--", scope).split(b"\0"):
        if not raw:
            continue
        meta, name = raw.decode("utf-8").split("\t", 1)
        mode, kind, oid, size = meta.split()
        safe_path(name)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"archive requires regular tracked files: {name}")
        disposition, reason = classify(name)
        rows.append({"path": name, "blob_oid": oid, "bytes": int(size),
                     "disposition": disposition, "reason": reason,
                     "recovery_commit": source, "recovery_path": name})
    if not rows:
        raise ValueError("archive source scope is empty or unavailable; fetch the named source explicitly")
    return rows


def generated_index_plan(repo: Path, source: str, scope: str) -> dict[str, Any]:
    rows = inventory(repo, source, scope)
    source_by_path = {row["path"]: row for row in rows}
    indexed = {
        path.decode("utf-8")
        for path in git(repo, "ls-files", "-z", "--", safe_path(scope)).split(b"\0")
        if path
    }
    keep = {path for path, row in source_by_path.items() if row["disposition"] == "keep"}
    migrate = {
        path for path, row in source_by_path.items() if row["disposition"] == "candidate_migrate"
    }
    remove_paths = sorted(indexed & migrate)
    missing_keep = sorted(keep - indexed)
    unexpected = sorted(indexed - set(source_by_path))
    return {
        "status": (
            "complete"
            if not remove_paths and not missing_keep and not unexpected
            else "ready_to_migrate"
            if not missing_keep and not unexpected
            else "blocked"
        ),
        "source_commit": source,
        "scope": safe_path(scope),
        "source_files": len(rows),
        "keep_files": len(keep),
        "source_migrate_files": len(migrate),
        "remaining_migrate_files": len(remove_paths),
        "remaining_migrate_bytes": sum(source_by_path[path]["bytes"] for path in remove_paths),
        "remove_paths": remove_paths,
        "missing_keep_paths": missing_keep,
        "unexpected_tracked_paths": unexpected,
    }


def manifest_row_path(scope: str, value: str) -> str:
    """Accept legacy scope-relative rows and v2 repository-relative rows."""
    if value == scope or value.startswith(scope + "/"):
        return safe_path(value)
    return safe_path(scope + "/" + value)


def verify_manifest(repo: Path, manifest: dict[str, Any], *, check_index: bool = False) -> dict[str, Any]:
    source, scope = manifest["source_commit"], safe_path(manifest["scope"])
    actual = {r["path"]: r for r in inventory(repo, source, scope)}
    declared = manifest["files"]
    if not isinstance(declared, list):
        raise ValueError("manifest files must be a list")
    seen: dict[str, dict[str, Any]] = {}
    for row in declared:
        path = manifest_row_path(scope, row["path"])
        if path in seen or path not in actual:
            raise ValueError(f"duplicate or non-source archive entry: {path}")
        if row.get("disposition") not in {"keep", "migrate"}:
            raise ValueError(f"unreviewed disposition at {path}")
        if not isinstance(row.get("reason"), str) or not row["reason"]:
            raise ValueError(f"missing disposition reason at {path}")
        if row["blob_oid"] != actual[path]["blob_oid"] or row["bytes"] != actual[path]["bytes"]:
            raise ValueError(f"manifest does not match immutable source blob: {path}")
        if manifest.get("schema_version") == "mindthus.benchmark-archive-manifest.v2":
            expected_ref = f"{source}:{path}"
            if row.get("recovery_ref") != expected_ref:
                raise ValueError(f"invalid immutable recovery ref at {path}")
        seen[path] = row
    if set(seen) != set(actual):
        raise ValueError("manifest must cover the entire scoped source tree exactly once")
    if check_index:
        indexed = {p.decode("utf-8") for p in git(repo, "ls-files", "-z", "--", scope).split(b"\0") if p}
        wanted = {p for p, row in seen.items() if row["disposition"] == "keep"}
        if indexed != wanted:
            raise ValueError("index differs from the approved keep/migrate set")

    payload = git(repo, "archive", "--format=tar", source, "--", scope)
    restored = set()
    with tempfile.TemporaryDirectory(prefix="mindthus-archive-verify-") as tmp:
        root = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
            for member in archive.getmembers():
                if member.isdir():
                    directory = str(PurePosixPath(member.name))
                    if directory not in {str(parent) for parent in PurePosixPath(scope).parents}:
                        safe_path(directory)
                    continue
                path = safe_path(member.name)
                if not member.isfile() or path not in actual or path in restored:
                    raise ValueError(f"unexpected archive member: {path}")
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"unreadable archive member: {path}")
                contents = stream.read()
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(contents)
                recovered = destination.read_bytes()
                oid = hashlib.sha1(b"blob " + str(len(recovered)).encode("ascii") + b"\0" + recovered).hexdigest()
                if oid != actual[path]["blob_oid"] or len(recovered) != actual[path]["bytes"]:
                    raise ValueError(f"recovery digest mismatch at {path}")
                restored.add(path)
    if restored != set(actual):
        raise ValueError("recovery was incomplete")
    return {"status": "verified", "source_commit": source, "scope": scope,
            "files": len(actual), "restored_files": len(restored),
            "migrate_files": sum(r["disposition"] == "migrate" for r in declared),
            "migrate_bytes": sum(r["bytes"] for r in declared if r["disposition"] == "migrate"),
            "index_checked": check_index, "checkout_mutated": False}


def artifact_reference_tokens(text: str) -> list[str]:
    """Extract raw-artifact path tokens from prose, inline code and code blocks."""
    markers = tuple(sorted(RAW_DIRS, key=len, reverse=True)) + tuple(sorted(RAW_NAMES))
    tokens = []
    for token in re.findall(r"[A-Za-z0-9_./*<>{}-]+", text):
        token = token.strip(".,:;()[]{}")
        if token and ("/" in token or token in RAW_NAMES) and any(
            token == marker or token.endswith("/" + marker) or f"/{marker}/" in token
            or token.startswith(marker + "/")
            for marker in markers
        ):
            tokens.append(token)
    return list(dict.fromkeys(tokens))


def resolve_artifact_reference(report: str, token: str, migrate_paths: set[str]) -> list[str]:
    """Resolve a declared raw reference against the immutable source inventory."""
    report_dir = str(PurePosixPath(report).parent)
    pattern = token.replace("<case>", "*")
    if pattern.startswith(ROOT):
        patterns = [pattern]
    else:
        patterns = [f"{report_dir}/{pattern}", f"{report_dir}/*/{pattern}"]
    matches = set()
    for candidate in migrate_paths:
        for item in patterns:
            if item.endswith("/"):
                if candidate.startswith(item):
                    matches.add(candidate)
            elif fnmatch.fnmatchcase(candidate, item):
                matches.add(candidate)
    return sorted(matches)


def build_reference_map(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Verify retained reports' raw references and emit their immutable resolutions."""
    source = manifest["source_commit"]
    scope = safe_path(manifest["scope"])
    rows = {
        manifest_row_path(scope, row["path"]): row
        for row in manifest["files"]
    }
    reports = sorted(
        path for path, row in rows.items()
        if PurePosixPath(path).name in REPORT_NAMES and row["disposition"] == "keep"
    )
    migrate_paths = {path for path, row in rows.items() if row["disposition"] == "migrate"}
    mapped_reports = []
    for report in reports:
        report_path = repo / report
        if not report_path.is_file():
            raise ValueError(f"retained report missing from HEAD: {report}")
        text = report_path.read_text(encoding="utf-8")
        if ARCHIVE_POINTER not in text:
            raise ValueError(f"retained report lacks immutable archive base: {report}")
        references = []
        for token in artifact_reference_tokens(text):
            matches = resolve_artifact_reference(report, token, migrate_paths)
            if not matches:
                raise ValueError(f"artifact reference does not resolve in immutable archive: {report}: {token}")
            references.append({"declared_reference": token, "resolved_paths": matches})
        contents = report_path.read_bytes()
        blob_oid = hashlib.sha1(
            b"blob " + str(len(contents)).encode("ascii") + b"\0" + contents
        ).hexdigest()
        mapped_reports.append({
            "path": report,
            "head_blob_oid": blob_oid,
            "archive_base_commit": source,
            "references": references,
        })

    linked_run_paths = []
    indexed = {
        path.decode("utf-8")
        for path in git(repo, "ls-files", "-z", "--", "docs/benchmarks/runs").split(b"\0")
        if path
    }
    for document in ("docs/benchmarks/latest.md", "docs/benchmarks/v5-targeted-plan.md"):
        document_path = repo / document
        if not document_path.is_file():
            continue
        text = document_path.read_text(encoding="utf-8")
        for token in sorted(set(re.findall(r"docs/benchmarks/runs/[A-Za-z0-9_./-]+", text))):
            normalized = token.rstrip("/.,:;")
            resolves = normalized in indexed or any(path.startswith(normalized + "/") for path in indexed)
            if not resolves:
                raise ValueError(f"run-folder reference does not resolve in HEAD: {document}: {token}")
            linked_run_paths.append({"document": document, "declared_reference": token, "head_resolves": True})
    return {
        "schema_version": "mindthus.benchmark-archive-reference-map.v1",
        "source_commit": source,
        "inventory_scope": scope,
        "reports_checked": len(mapped_reports),
        "reports": mapped_reports,
        "run_folder_links": linked_run_paths,
        "status": "verified",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source")
    parser.add_argument("--scope", default=ROOT.rstrip("/"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--write-manifest", type=Path)
    parser.add_argument("--write-reference-map", type=Path)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--check-index", action="store_true")
    parser.add_argument("--index-plan", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    try:
        if args.write_manifest:
            result = build_manifest(repo, args.source or "", args.scope)
            args.write_manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = {"status": "written", "path": str(args.write_manifest), "files": len(result["files"])}
        elif args.write_reference_map:
            if not args.manifest:
                raise ValueError("--write-reference-map requires --manifest")
            manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
            result = build_reference_map(repo, manifest)
            args.write_reference_map.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = {"status": "written", "path": str(args.write_reference_map),
                      "reports_checked": result["reports_checked"]}
        elif args.manifest:
            result = verify_manifest(repo, json.loads(args.manifest.read_text(encoding="utf-8")), check_index=args.check_index)
        elif args.index_plan:
            result = generated_index_plan(repo, args.source or "", args.scope)
        else:
            rows = inventory(repo, args.source or "", args.scope)
            if args.summary:
                result = {"source_commit": args.source, "scope": args.scope, "files": len(rows),
                          "bytes": sum(r["bytes"] for r in rows),
                          "by_disposition": {d: {"files": sum(r["disposition"] == d for r in rows),
                                                "bytes": sum(r["bytes"] for r in rows if r["disposition"] == d)}
                                             for d in sorted({r["disposition"] for r in rows})}}
            else:
                result = rows
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (KeyError, TypeError, ValueError, OSError, tarfile.TarError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
