#!/usr/bin/env python3
"""Log Mindthus repo, marketplace, and Codex cache runtime fingerprints."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "1.4.1"
RELATIVE_FILES = (
    "skills/using-mindthus/SKILL.md",
    "docs/methodologies/shared-primitives.md",
)
REQUIRED_MARKERS = (
    "Original Prompt Contract / 原始有效提示词合同",
    "在回答前，先执行“输入审计”，不要顺着我的叙述直接推理",
    "First task: judge whether the user led you to the wrong level",
    "audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer",
    "leading_point",
    "Core Thesis Extraction / 主判断收束",
    "Object Anchor / 对象锚定",
    "keep asked object as subject",
    "Essence Wording Guard / 本质措辞护栏",
    "Composite Object Integrity / 复合对象完整性",
    "Executable Substrate Check / 可执行基底校准",
    "operative subcomponents move work from generation into execution/verification",
    "Auxiliary checks belong inside step 3",
    "Explanatory Authority Check / 解释权校准",
    "Dominant Carrier Check / 主导承载校准",
    "System Subject Check / 系统主体校准",
    "local correctness is not explanatory authority",
    "problem key over dialogue continuity",
    "professional tone is not proof",
    "common implementation is not essence",
    "first task is not answering",
)


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_marketplace_root(codex_home: Path) -> Path:
    return codex_home / "local-marketplaces" / f"mindthus-v{VERSION}" / "codex-plugin" / "mindthus"


def default_cache_root(codex_home: Path) -> Path:
    return codex_home / "plugins" / "cache" / "mindthus" / "mindthus" / VERSION


def sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def inspect_file(path: Path) -> dict[str, Any]:
    exists = path.is_file()
    info: dict[str, Any] = {"path": str(path), "exists": exists}
    if not exists:
        info["markers"] = {marker: False for marker in REQUIRED_MARKERS}
        return info

    text = path.read_text(encoding="utf-8")
    info.update(
        {
            "sha256": sha256_text(path),
            "bytes": path.stat().st_size,
            "mtime_utc": iso_mtime(path),
            "markers": {marker: marker in text for marker in REQUIRED_MARKERS},
        }
    )
    return info


def inspect_location(label: str, root: Path) -> dict[str, Any]:
    files = {rel: inspect_file(root / rel) for rel in RELATIVE_FILES}
    return {"label": label, "root": str(root), "exists": root.exists(), "files": files}


def compare_hashes(locations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for rel in RELATIVE_FILES:
        hashes = {
            label: location["files"][rel].get("sha256")
            for label, location in locations.items()
            if location["files"][rel].get("sha256")
        }
        unique_hashes = sorted(set(hashes.values()))
        comparisons[rel] = {
            "hashes": hashes,
            "all_available_match": len(unique_hashes) <= 1,
            "unique_hashes": unique_hashes,
        }
    return comparisons


def marker_presence(locations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    marker_report: dict[str, Any] = {}
    for marker in REQUIRED_MARKERS:
        marker_report[marker] = {
            label: any(file_info["markers"].get(marker, False) for file_info in location["files"].values())
            for label, location in locations.items()
        }
    return marker_report


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    codex_home = Path(args.codex_home).expanduser()
    locations = {
        "repo": inspect_location("repo", Path(args.repo_root).expanduser()),
        "marketplace": inspect_location("marketplace", Path(args.marketplace_root).expanduser()),
        "cache": inspect_location("cache", Path(args.cache_root).expanduser()),
    }
    comparisons = compare_hashes(locations)
    markers = marker_presence(locations)
    all_required_markers_present = all(
        all(location_present.values()) for location_present in markers.values()
    )
    all_available_hashes_match = all(
        comparison["all_available_match"] for comparison in comparisons.values()
    )
    status = "ok" if all_required_markers_present and all_available_hashes_match else "mismatch"
    return {
        "schema_version": "mindthus-runtime-log-v0.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "version": VERSION,
        "codex_home": str(codex_home),
        "locations": locations,
        "comparisons": comparisons,
        "markers": markers,
        "summary": {
            "status": status,
            "all_required_markers_present": all_required_markers_present,
            "all_available_hashes_match": all_available_hashes_match,
        },
    }


def print_human(report: dict[str, Any]) -> None:
    print("Mindthus runtime log")
    print(f"generated_at_utc: {report['generated_at_utc']}")
    print(f"version: {report['version']}")
    print(f"summary: {report['summary']['status']}")
    print()
    for label, location in report["locations"].items():
        print(f"[{label}] {location['root']}")
        for rel, info in location["files"].items():
            if not info["exists"]:
                print(f"  {rel}: MISSING")
                continue
            print(f"  {rel}: sha256={info['sha256']} bytes={info['bytes']} mtime_utc={info['mtime_utc']}")
        print()
    print("[hash comparisons]")
    for rel, comparison in report["comparisons"].items():
        status = "match" if comparison["all_available_match"] else "mismatch"
        print(f"  {rel}: {status}")
    print()
    print("[required markers]")
    for marker, presence in report["markers"].items():
        status = "OK" if all(presence.values()) else "MISSING"
        print(f"  {status} {marker}")


def main() -> int:
    codex_home = default_codex_home()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=repo_root(), type=Path, help="Mindthus repository root.")
    parser.add_argument(
        "--marketplace-root",
        default=default_marketplace_root(codex_home),
        type=Path,
        help="Installed local marketplace plugin root.",
    )
    parser.add_argument(
        "--cache-root",
        default=default_cache_root(codex_home),
        type=Path,
        help="Codex plugin cache root.",
    )
    parser.add_argument("--codex-home", default=codex_home, type=Path, help="Codex home directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on missing markers or hash mismatch.")
    args = parser.parse_args()

    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 1 if args.strict and report["summary"]["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
