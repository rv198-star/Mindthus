#!/usr/bin/env python3
"""Generate the scoped keep/migrate inventory for historical benchmark run artifacts.

This script classifies every tracked file under `docs/benchmarks/runs/` against
`docs/benchmarks/run-artifact-retention-policy.md` and emits a machine-readable
inventory: one CSV row per path (`path / blob_oid / size_bytes / disposition / rule`)
plus a JSON summary holding the totals and the rule dictionary those rows key into.

It is an inventory and dry-run tool only. It never deletes, moves, or rewrites
anything. Deletion is a separate, separately reviewed step.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath


# v0.2: CSV rows are written with LF line terminators (v0.1 emitted CRLF via the csv
# module's default) and the column order below is pinned. Both change the bytes of every
# row, so the version moves with them -- a consumer that pinned v0.1 must be told the
# file it validated is not the file it now reads.
INVENTORY_SCHEMA_VERSION = "mindthus-benchmark-artifact-inventory-v0.2"
RUNS_ROOT = "docs/benchmarks/runs"

# Pinned explicitly rather than read off `asdict(entries[0])`. Deriving the header from
# the first row makes the schema a function of whichever file sorts first and of dataclass
# field order, so a reordered field silently rewrites 6493 rows with no version change.
CSV_COLUMNS = ("path", "blob_oid", "size_bytes", "disposition", "rule")

# Reports and decision records. Policy: "the campaign report and decision boundary",
# "compact human-review or disagreement records".
KEEP_REPORTS = {
    "REPORT.md",
    "HUMAN_REVIEW_PACKET.md",
    "EXTERNAL_AUDIT_HANDOFF.md",
    "MANUAL_PROBLEM_CASE_AUDIT.md",
    "CODEX_HOME_CONFIG_SNAPSHOT.md",
}

# Policy: "run and contamination manifests", "aggregate scores and pre-registered gate
# results", "fingerprints needed to identify runner, fixture, prompt, model, and code
# lineage".
KEEP_MANIFESTS = {
    "run-manifest.json",
    "contamination-report.json",
}
KEEP_AGGREGATES = {
    "summary.json",
    "summary-aggregate.json",
}

# The case register defining what a campaign actually tested. Policy keeps "fingerprints
# needed to identify runner, fixture, prompt, model, and code lineage" — this file *is*
# the fixture. It also meets the Exception Test: the issue-108 report claims the variants
# differ in surface wording, domain, and role direction, and that claim cannot be checked
# without the variant text. It is cited under that report's Artifacts list and exists
# nowhere else outside the migrate set.
KEEP_CASE_REGISTERS = {
    "issue-108-variant-cases.jsonl",
}
KEEP_FINGERPRINTS = {
    "runtime-fingerprint.json",
    "eval-home-runtime-fingerprint.json",
    "runtime-fingerprint-strict.json",
    "runtime-fingerprint-strict-rerun.json",
    "runtime-fingerprint-strict-safe.json",
}

# Policy: "per-call prompts and full answers", "event streams, stderr, and last-message
# files", "generator, triage, action, and judge intermediate records".
MIGRATE_DIRS = {
    "answers",
    "prompts",
    "events",
    "judge-answers",
    "judge-events",
    "judge-prompts",
    "judge-stderr",
    "stderr",
}
MIGRATE_NAMES = {
    "raw-responses.jsonl",
    "score-records.jsonl",
    "runner.stdout.log",
    "runner.stderr.log",
}

# Policy: "duplicated schemas and telemetry".
#
# judge-output-schema.json: all 50 copies are one blob, byte-for-byte regenerable from
# judge_schema() in scripts/run-judgment-benchmark-cli.py. Contains no run-specific data.
#
# activation-summary.json: verified equal to the `activation` object already embedded in
# the sibling summary.json in 43/43 cases — both are written by the same
# activation_summary() call — and cited by no report. Retaining summary.json retains the
# data; this file is the duplicate.
MIGRATE_DUPLICATED = {
    "judge-output-schema.json",
    "activation-summary.json",
}


# Per-rule constants. `reason` and `destination` are properties of the rule, not of the
# individual path, so they are stored once here and referenced by key from each row.
# Repeating them on all 6493 rows would add ~0.9 MiB of duplicated strings to an
# inventory whose purpose is to reduce tracked weight.
RULE_REASONS = {
    "policy:campaign-report": "campaign report or decision boundary record",
    "policy:decision-boundary": "records why a run was discarded",
    "policy:manifest": "run or contamination manifest supporting a stated claim",
    "policy:aggregate": "aggregate scores or pre-registered gate results",
    "policy:fingerprint": (
        "fingerprint identifying runner, fixture, prompt, model, or code lineage"
    ),
    "policy:case-register": (
        "case register defining what the campaign tested; report claims are unverifiable "
        "without it"
    ),
    "policy:per-call": (
        "per-call prompt, answer, event stream, stderr, or judge intermediate record"
    ),
    "policy:duplicated": (
        "duplicated schema or telemetry; the same content is retained elsewhere or is "
        "regenerable from tracked code"
    ),
    "unmatched": "no rule matched; kept by default and requires explicit human classification",
}


@dataclass(frozen=True)
class Entry:
    path: str
    blob_oid: str
    size_bytes: int
    disposition: str
    rule: str

    @property
    def reason(self) -> str:
        return RULE_REASONS[self.rule]


def run_git(args: list[str], repo: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def tracked_files(repo: Path) -> list[tuple[str, str, int]]:
    """Return (path, blob_oid, size_bytes) for every tracked file under RUNS_ROOT."""
    raw = run_git(["ls-files", "-s", "-z", RUNS_ROOT], repo)
    paths: list[tuple[str, str]] = []
    for record in raw.split("\0"):
        if not record.strip():
            continue
        meta, _, path = record.partition("\t")
        fields = meta.split()
        if len(fields) < 2:
            raise SystemExit(f"unexpected git ls-files output: {record!r}")
        paths.append((path, fields[1]))

    if not paths:
        return []

    # Batch the object sizes so a 6000-file inventory stays a single git call.
    batch_input = "".join(f"{oid}\n" for _, oid in paths)
    sizes_raw = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectsize)"],
        cwd=repo,
        input=batch_input,
        text=True,
        capture_output=True,
        check=False,
    )
    if sizes_raw.returncode != 0:
        raise SystemExit(f"git cat-file failed: {sizes_raw.stderr.strip()}")
    sizes = [int(line) for line in sizes_raw.stdout.splitlines() if line.strip()]
    if len(sizes) != len(paths):
        raise SystemExit(f"size lookup mismatch: {len(sizes)} sizes for {len(paths)} paths")

    return [(path, oid, size) for (path, oid), size in zip(paths, sizes)]


def classify(path: str) -> tuple[str, str]:
    """Return (disposition, rule) for one tracked path.

    Unmatched paths are deliberately classified `keep` with an `unmatched` rule so a
    new artifact shape can never be deleted by silent default.
    """
    name = Path(path).name
    parts = set(Path(path).parts)

    if name in KEEP_REPORTS:
        return "keep", "policy:campaign-report"
    if name == "README.txt" and "discarded-initial-run" in parts:
        return "keep", "policy:decision-boundary"
    if name in KEEP_MANIFESTS:
        return "keep", "policy:manifest"
    if name in KEEP_AGGREGATES:
        return "keep", "policy:aggregate"
    if name in KEEP_FINGERPRINTS:
        return "keep", "policy:fingerprint"
    if name in KEEP_CASE_REGISTERS:
        return "keep", "policy:case-register"

    if parts & MIGRATE_DIRS:
        return "migrate", "policy:per-call"
    if name in MIGRATE_NAMES:
        return "migrate", "policy:per-call"
    if name in MIGRATE_DUPLICATED:
        return "migrate", "policy:duplicated"

    return "keep", "unmatched"


def build_inventory(repo: Path) -> list[Entry]:
    entries: list[Entry] = []
    for path, oid, size in tracked_files(repo):
        disposition, rule = classify(path)
        entries.append(
            Entry(path=path, blob_oid=oid, size_bytes=size, disposition=disposition, rule=rule)
        )
    return sorted(entries, key=lambda item: item.path)


# Backticked path references inside retained reports, e.g. `answers/mtj-032-turn-1.txt`.
BACKTICK_REF = re.compile(r"`([^`\n]+)`")

# A referenced token is only a path worth resolving if it looks like one: it carries a
# directory separator or a known artifact extension. This keeps ordinary prose in
# backticks (`ok`, `summary`) out of the dangling-reference count.
PATH_LIKE = re.compile(r"(/|\.(json|jsonl|txt|log|md))")

# Scores and ratios written in backticks -- `0/12`, `1.5 / 2`, `0.467 / 0.600 / 0.667`.
# The slash makes PATH_LIKE accept them, so they must be rejected by shape rather than
# left to fail resolution and be counted as unresolved references. The pattern is
# deliberately anchored and digits-only: it matches none of the 6493 tracked paths, and a
# looser rule that started swallowing real filenames would be the same class of defect
# this scan is being repaired for.
NUMERIC_RATIO = re.compile(r"^\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)+$")

# Leading path segments that name a migrated artifact class. A reference that starts with
# one of these is aimed at migrated content even when it resolves to no tracked path --
# because it is a glob template (`answers/<case>.record.json`) or is written relative to a
# variant subdirectory rather than the report's own directory. Both shapes appear in the
# retained review packets, and both must count: a reference that resolves nowhere today is
# not evidence of safety.
MIGRATED_REF_PREFIXES = tuple(f"{name}/" for name in sorted(MIGRATE_DIRS))

# Every extracted reference lands in exactly one of these. The point is the accounting
# identity below: `sum(by_category.values()) == total_extracted`. Without it a reference
# that matches no branch simply falls off the loop, and a scan that examined nothing
# reports the same "clean" result as a scan that examined everything. That is how the
# first pass of this tool dropped 73 references without a single counter moving.
#
# A category is never omitted when its count is zero. A sparse dict lets a disappearing
# category masquerade as an absent one.
REFERENCE_CATEGORIES = (
    "rejected_empty",
    "rejected_not_path_like",
    "rejected_numeric_ratio",
    "rejected_url",
    "resolved_survives",
    "resolved_outside_migration_scope",
    "breaks_after_migration",
    "unresolved_migrate_class",
    "unresolved_absolute_external",
    "unresolved",
)

# The return contract of scan_references(). Three of these have live consumers (main(),
# render_report(), tests/test_benchmark_artifact_inventory.py), so the contract is
# additive only: keys may be added, never removed or repurposed.
REFERENCES_REQUIRED_KEYS = frozenset(
    {
        "retained_reports",
        "reports_needing_archive_pointer",
        "details",
        "scanned_files",
        "skipped_files",
        "total_extracted",
        "by_category",
        "accounting_ok",
    }
)


def reference_survives(ref: str, report: str, tracked: dict[str, str]) -> bool | None:
    """Return whether a reference still resolves after migration, or None if unresolved.

    References inside run reports are written relative to the report's own directory, but
    some are repo-rooted. Both are tried.

    A file reference survives only if that file is kept. A *directory* reference survives
    if anything under it is kept — `repeat-1/` still resolves after migration because
    `repeat-1/summary.json` stays. Treating a directory as broken because one file
    beneath it moves would flag most reports in the corpus and bury the three that are
    genuinely affected.
    """
    for base in (f"{PurePosixPath(report).parent}/{ref.rstrip('/')}", ref.rstrip("/")):
        normalized = str(PurePosixPath(base))
        if normalized in tracked:
            return tracked[normalized] == "keep"
        prefix = normalized + "/"
        beneath = [disposition for path, disposition in tracked.items() if path.startswith(prefix)]
        if beneath:
            return "keep" in beneath
    return None


def migrate_only_basenames(entries: list[Entry]) -> set[str]:
    """Basenames whose every tracked copy is classified `migrate`.

    Derived from the classification result rather than hand-listed. A bare basename in a
    report (`judge-output-schema.json`) carries no directory to resolve against, so the
    only honest answer to "does this reference survive migration?" is: it survives iff
    some copy of that name survives.

    The literal `MIGRATE_NAMES` is a classification rule -- an input stating what policy
    migrates. This is an output, and the two are not interchangeable: the literal holds 4
    names, the derived index holds several hundred, and the gap between them is where a
    reference to a migrated artifact hid.
    """
    dispositions: dict[str, set[str]] = {}
    for item in entries:
        dispositions.setdefault(PurePosixPath(item.path).name, set()).add(item.disposition)
    return {name for name, seen in dispositions.items() if seen == {"migrate"}}


def resolves_outside_runs(ref: str, repo_tracked: set[str]) -> bool:
    """Whether a reference names a tracked file that migration cannot touch.

    Membership in the git index, not filesystem existence: an untracked file on this
    working copy tells us nothing about what a reviewer or CI will see. Paths under
    RUNS_ROOT are excluded because those are exactly the paths migration acts on --
    resolving one here would answer the wrong question.
    """
    normalized = str(PurePosixPath(ref.rstrip("/")))
    return normalized in repo_tracked and not normalized.startswith(f"{RUNS_ROOT}/")


def scan_references(repo: Path, entries: list[Entry]) -> dict:
    """Report which references inside retained reports break once migration happens.

    Read-only. A reference is `dangling_after_migration` when migration would leave it
    pointing at nothing: either it resolves today but only to files marked `migrate`
    (`breaks_after_migration`), or it resolves to no tracked path and is aimed at a
    migrated artifact class (`unresolved_migrate_class`). Both go in the same list because
    both mean the same thing for the reader of the report — those reports need an archive
    base pointer before deletion is safe.

    Every extracted reference is counted into exactly one `REFERENCE_CATEGORIES` bucket,
    including the ones this scan decides to ignore. `accounting_ok` states whether the
    buckets sum to the number extracted; when it is False the scan dropped something and
    the "N reports need a pointer" line below it cannot be trusted.

    Scope: only files named in `KEEP_REPORTS` are read. `scanned_files` and
    `skipped_files` report that boundary, because `accounting_ok` is a claim about the
    references this scan saw, not about the repository.
    """
    tracked = {item.path: item.disposition for item in entries}
    reports = [
        item.path
        for item in entries
        if item.disposition == "keep" and PurePosixPath(item.path).name in KEEP_REPORTS
    ]
    kept = [item.path for item in entries if item.disposition == "keep"]
    repo_tracked = {line for line in run_git(["ls-files"], repo).splitlines() if line}
    migrate_only = migrate_only_basenames(entries)

    by_category = {category: 0 for category in REFERENCE_CATEGORIES}
    total_extracted = 0
    affected: list[dict] = []
    for report in sorted(reports):
        broken: set[str] = set()
        text = (repo / report).read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for raw_ref in BACKTICK_REF.findall(line):
                total_extracted += 1
                ref = raw_ref.strip()
                if not ref:
                    by_category["rejected_empty"] += 1
                    continue
                if ref.startswith(("http://", "https://")):
                    by_category["rejected_url"] += 1
                    continue
                if not PATH_LIKE.search(ref):
                    by_category["rejected_not_path_like"] += 1
                    continue
                if NUMERIC_RATIO.match(ref):
                    by_category["rejected_numeric_ratio"] += 1
                    continue
                survives = reference_survives(ref, report, tracked)
                if survives is True:
                    by_category["resolved_survives"] += 1
                elif survives is False:
                    by_category["breaks_after_migration"] += 1
                    broken.add(f"{line_number}:{ref}")
                elif ref.startswith(MIGRATED_REF_PREFIXES) or PurePosixPath(ref).name in migrate_only:
                    # Unresolvable, but aimed squarely at a migrated artifact class.
                    by_category["unresolved_migrate_class"] += 1
                    broken.add(f"{line_number}:{ref}")
                elif resolves_outside_runs(ref, repo_tracked):
                    # A real tracked file, just not under RUNS_ROOT. Migration cannot
                    # touch it, so it is resolved rather than dangling. Reporting these
                    # as at-risk was the loudest part of the first pass's noise.
                    by_category["resolved_outside_migration_scope"] += 1
                elif ref.startswith("/"):
                    # Absolute paths on whoever's machine ran the campaign (`/tmp/...`).
                    # Nothing in this repository can make them resolve or break.
                    by_category["unresolved_absolute_external"] += 1
                else:
                    by_category["unresolved"] += 1
        if broken:
            affected.append({"report": report, "dangling_after_migration": sorted(broken)})

    return {
        "retained_reports": len(reports),
        "reports_needing_archive_pointer": len(affected),
        "details": affected,
        "scanned_files": len(reports),
        "skipped_files": len(kept) - len(reports),
        "total_extracted": total_extracted,
        "by_category": by_category,
        "accounting_ok": sum(by_category.values()) == total_extracted,
    }


def summarize(entries: list[Entry]) -> dict:
    keep = [item for item in entries if item.disposition == "keep"]
    migrate = [item for item in entries if item.disposition == "migrate"]
    unmatched = [item for item in entries if item.rule == "unmatched"]
    by_rule: dict[str, dict[str, int]] = {}
    for item in entries:
        bucket = by_rule.setdefault(item.rule, {"files": 0, "bytes": 0})
        bucket["files"] += 1
        bucket["bytes"] += item.size_bytes
    return {
        "total_files": len(entries),
        "total_bytes": sum(item.size_bytes for item in entries),
        "keep_files": len(keep),
        "keep_bytes": sum(item.size_bytes for item in keep),
        "migrate_files": len(migrate),
        "migrate_bytes": sum(item.size_bytes for item in migrate),
        "unmatched_files": len(unmatched),
        "by_rule": dict(sorted(by_rule.items())),
    }


def render_report(
    summary: dict, entries: list[Entry], baseline_commit: str, references: dict
) -> str:
    mib = 1024 * 1024
    lines = [
        "# Benchmark Run Artifact Inventory",
        "",
        f"Schema: `{INVENTORY_SCHEMA_VERSION}`",
        f"Baseline commit: `{baseline_commit}`",
        "",
        "Generated by `scripts/benchmark-artifact-inventory.py`. This is a dry-run",
        "classification only. No file is deleted, moved, or rewritten by this tool.",
        "",
        "## Totals",
        "",
        "| Set | Files | Size |",
        "| --- | ---: | ---: |",
        f"| Tracked under `{RUNS_ROOT}/` | {summary['total_files']} | "
        f"{summary['total_bytes'] / mib:.3f} MiB |",
        f"| Keep | {summary['keep_files']} | {summary['keep_bytes'] / mib:.3f} MiB |",
        f"| Migrate | {summary['migrate_files']} | {summary['migrate_bytes'] / mib:.3f} MiB |",
        "",
        "## By Rule",
        "",
        "| Rule | Files | Size |",
        "| --- | ---: | ---: |",
    ]
    for rule, bucket in summary["by_rule"].items():
        lines.append(f"| `{rule}` | {bucket['files']} | {bucket['bytes'] / mib:.3f} MiB |")

    lines += [
        "",
        "## Unmatched",
        "",
    ]
    unmatched = [item for item in entries if item.rule == "unmatched"]
    if not unmatched:
        lines.append("None. Every tracked path matched an explicit policy rule.")
    else:
        lines.append(
            f"{len(unmatched)} path(s) matched no rule. They are classified `keep` by "
            "default and must be resolved individually before any deletion step."
        )
        lines.append("")
        for item in unmatched:
            lines.append(f"- `{item.path}`")

    lines += [
        "",
        "## Reference Resolution",
        "",
        f"{references['retained_reports']} retained report(s) scanned for backticked path",
        "references that migration would leave pointing at nothing — either resolving today",
        "only to files marked `migrate`, or resolving nowhere while naming a migrated",
        "artifact class. Each such report needs an archive base pointer before deletion, or",
        "its evidence column goes dead.",
        "",
        f"Scope: {references['scanned_files']} file(s) scanned, "
        f"{references['skipped_files']} kept file(s) not scanned. The accounting below is a",
        "claim about the references this scan read, not about the repository.",
        "",
        f"{references['total_extracted']} reference(s) extracted, each counted into exactly one",
        f"category. `accounting_ok` is `{references['accounting_ok']}`: "
        + (
            "the categories sum to the number extracted, so nothing was dropped between "
            "extraction and classification."
            if references["accounting_ok"]
            else f"the categories sum to {sum(references['by_category'].values())}, not "
            f"{references['total_extracted']}. References were dropped between extraction "
            "and classification, so every count below is a floor, not a total."
        ),
        "",
        "| Category | Count |",
        "| --- | ---: |",
        *[
            f"| `{category}` | {references['by_category'][category]} |"
            for category in REFERENCE_CATEGORIES
        ],
        "",
    ]
    if not references["details"]:
        lines.append("None. No retained report references a migrated artifact.")
    else:
        lines.append(
            f"**{references['reports_needing_archive_pointer']} report(s) need an archive "
            "base pointer:**"
        )
        lines.append("")
        lines.append("| Report | Dangling refs |")
        lines.append("| --- | ---: |")
        for item in references["details"]:
            lines.append(f"| `{item['report']}` | {len(item['dangling_after_migration'])} |")

    lines += [
        "",
        "## Net Accounting",
        "",
        "Migration removes the migrate set from HEAD. This inventory itself adds tracked",
        "files. Both are reported separately so a correct migration is never judged a",
        "failure because its own evidence offset the reduction.",
        "",
        "| Term | Files | Size |",
        "| --- | ---: | ---: |",
        f"| Removed from HEAD (migrate set) | {summary['migrate_files']} | "
        f"{summary['migrate_bytes'] / mib:.3f} MiB |",
        "| Added by this inventory (support) | see below | see below |",
        "",
        "Support additions are listed explicitly at migration time and subtracted when",
        "net tracked size is reported. Net size is a reported quantity, not a pass/fail",
        "line. The pass/fail criteria are: every `migrate` row absent from HEAD, deleted",
        f"blob sizes summing to {summary['migrate_bytes']} bytes, and `{RUNS_ROOT}/`",
        f"reduced to approximately {summary['keep_bytes'] / mib:.3f} MiB.",
        "",
        "## Boundary",
        "",
        "- This inventory does not authorize deletion.",
        "- Migration may begin only after this classification, archive reachability, and",
        "  reference resolution are independently reviewed.",
        "- No history rewrite. All pre-existing commit SHAs and preregistered evidence",
        "  pointers remain valid.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1], help="Repository root."
    )
    parser.add_argument("--csv", type=Path, help="Write the inventory rows to this CSV path.")
    parser.add_argument(
        "--summary",
        type=Path,
        help="Write totals and the rule dictionary to this JSON path (no per-row duplication).",
    )
    parser.add_argument("--report", type=Path, help="Write a human-readable summary to this path.")
    parser.add_argument(
        "--destination",
        default="benchmark-archive (pinned commit/tag recorded at migration time)",
        help="Recorded destination for migrated artifacts.",
    )
    parser.add_argument(
        "--fail-on-unmatched",
        action="store_true",
        help="Exit non-zero when any tracked path matches no explicit rule.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    entries = build_inventory(repo)
    if not entries:
        print(f"no tracked files under {RUNS_ROOT}/")
        return 0

    summary = summarize(entries)
    references = scan_references(repo, entries)
    baseline_commit = run_git(["rev-parse", "HEAD"], repo).strip()

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", encoding="utf-8", newline="") as handle:
            # newline="" keeps Python from translating; lineterminator="\n" stops the csv
            # module writing its RFC-4180 default CRLF. Without the second one this is the
            # only CRLF file in the repository.
            writer = csv.DictWriter(
                handle, fieldnames=list(CSV_COLUMNS), lineterminator="\n"
            )
            writer.writeheader()
            for item in entries:
                writer.writerow(asdict(item))
        print(f"wrote {len(entries)} rows to {args.csv}")

    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": INVENTORY_SCHEMA_VERSION,
            "baseline_commit": baseline_commit,
            "runs_root": RUNS_ROOT,
            "destination": args.destination,
            "rows": str(args.csv) if args.csv else None,
            "rule_reasons": RULE_REASONS,
            "summary": summary,
            "references": references,
        }
        args.summary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"wrote inventory summary to {args.summary}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            render_report(summary, entries, baseline_commit, references), encoding="utf-8"
        )
        print(f"wrote inventory report to {args.report}")

    mib = 1024 * 1024
    print(f"baseline commit : {baseline_commit}")
    print(f"total    {summary['total_files']:5d} files  {summary['total_bytes'] / mib:8.3f} MiB")
    print(f"keep     {summary['keep_files']:5d} files  {summary['keep_bytes'] / mib:8.3f} MiB")
    print(f"migrate  {summary['migrate_files']:5d} files  {summary['migrate_bytes'] / mib:8.3f} MiB")
    print(
        f"reports  {references['retained_reports']:5d} retained, "
        f"{references['reports_needing_archive_pointer']} need an archive base pointer"
    )
    print(
        f"refs     {references['total_extracted']:5d} extracted from "
        f"{references['scanned_files']} scanned file(s); "
        f"{references['skipped_files']} kept file(s) not scanned"
    )
    for category in REFERENCE_CATEGORIES:
        print(f"           {category:26s} {references['by_category'][category]:5d}")
    print(f"           accounting_ok = {references['accounting_ok']}")

    exit_code = 0
    if not references["accounting_ok"]:
        # The scan lost references between extraction and classification, so every count
        # above it is a floor rather than a total. Fail regardless of --fail-on-unmatched:
        # this is not a policy question a caller opts into, it is a broken scan.
        print(
            "- BROKEN-ACCOUNTING extracted "
            f"{references['total_extracted']} but categorized "
            f"{sum(references['by_category'].values())}; reference counts are not trustworthy"
        )
        exit_code = 1

    if summary["unmatched_files"]:
        print(f"unmatched {summary['unmatched_files']} file(s) kept by default; resolve before deletion")
        if args.fail_on_unmatched:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
