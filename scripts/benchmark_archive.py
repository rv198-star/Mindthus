#!/usr/bin/env python3
"""Inventory and verify immutable benchmark archives without modifying the checkout.

Full inventory prints one row per source blob. Recovery drills write only to a fresh
TemporaryDirectory, compare every byte to the recorded Git blob, then remove that temp
copy. This tool never deletes HEAD files, fetches history, or rewrites a source tag.
"""
from __future__ import annotations

import argparse
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
    if p.name in KEEP or path.endswith("discarded-initial-run/README.txt"):
        return "keep", "decision-bearing report, summary, lineage or schema"
    if p.name in RAW_NAMES or set(p.parts[3:]) & RAW_DIRS:
        return "candidate_migrate", "per-call artifact; requires scoped approval and recoverability"
    return "keep", "unclassified: retain pending individual review"


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


def verify_manifest(repo: Path, manifest: dict[str, Any], *, check_index: bool = False) -> dict[str, Any]:
    source, scope = manifest["source_commit"], safe_path(manifest["scope"])
    actual = {r["path"]: r for r in inventory(repo, source, scope)}
    declared = manifest["files"]
    if not isinstance(declared, list):
        raise ValueError("manifest files must be a list")
    seen: dict[str, dict[str, Any]] = {}
    for row in declared:
        path = safe_path(scope + "/" + row["path"])
        if path in seen or path not in actual:
            raise ValueError(f"duplicate or non-source archive entry: {path}")
        if row.get("disposition") not in {"keep", "migrate"}:
            raise ValueError(f"unreviewed disposition at {path}")
        if not isinstance(row.get("reason"), str) or not row["reason"]:
            raise ValueError(f"missing disposition reason at {path}")
        if row["blob_oid"] != actual[path]["blob_oid"] or row["bytes"] != actual[path]["bytes"]:
            raise ValueError(f"manifest does not match immutable source blob: {path}")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source")
    parser.add_argument("--scope", default=ROOT.rstrip("/"))
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--check-index", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    try:
        if args.manifest:
            result = verify_manifest(repo, json.loads(args.manifest.read_text(encoding="utf-8")), check_index=args.check_index)
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
