#!/usr/bin/env python3
"""Log Mindthus repo, marketplace, and Codex cache runtime fingerprints."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


VERSION = "1.5.2"
PACKAGE_IDENTITY = "mindthus"
MARKETPLACE_IDENTITY = "mindthus"
RELATIVE_FILES = (
    "skills/using-mindthus/SKILL.md",
    "skills/using-mindthus/resources/calibration-pairs.yaml",
    "docs/methodologies/shared-primitives.md",
    "docs/methodologies/primitives/aspect-ownership.md",
    "docs/methodologies/primitives/decision-context-calibration.md",
    "docs/methodologies/primitives/entry-triage.md",
    "docs/methodologies/primitives/expression-pressure-and-gates.md",
    "docs/methodologies/primitives/frame-fitness-check.md",
    "docs/methodologies/primitives/mpg-scalar-commitment-unpack.md",
    "docs/methodologies/primitives/whole-elephant-protocol.md",
    "scripts/primitives/check.py",
    "scripts/primitives/manifest.json",
    "scripts/primitives/validate_whole_elephant.py",
    "scripts/primitives/whole_elephant_validator.py",
    "skills/using-mindthus/scripts/validate_using_mindthus_output.py",
    "skills/_runtime/__init__.py",
    "skills/_runtime/core/__init__.py",
    "skills/_runtime/core/io.py",
    "skills/_runtime/core/report.py",
    "skills/_runtime/core/shape.py",
    "skills/_runtime/fidelity/__init__.py",
    "skills/_runtime/fidelity/core.py",
)

RUNTIME_TOP_LEVEL_ALIASES = {
    "skills/_runtime/__init__.py": "_runtime/__init__.py",
    "skills/_runtime/core/__init__.py": "_runtime/core/__init__.py",
    "skills/_runtime/core/io.py": "_runtime/core/io.py",
    "skills/_runtime/core/report.py": "_runtime/core/report.py",
    "skills/_runtime/core/shape.py": "_runtime/core/shape.py",
    "skills/_runtime/fidelity/__init__.py": "_runtime/fidelity/__init__.py",
    "skills/_runtime/fidelity/core.py": "_runtime/fidelity/core.py",
}
REQUIRED_MARKERS = (
    "Original Prompt Contract / 原始有效提示词合同",
    "在回答前，先执行“输入审计”，不要顺着我的叙述直接推理",
    "Truth Orientation / 真相优先",
    "pursue facts and truth over agreement",
    "audit order: true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer",
    "Entry Triage / 入口分诊",
    "definition authority contest",
    "green tests imply release readiness",
    "negative and shadow controls",
    "Root-cause evidence gate",
    "same local repair count >= 3",
    "Visible consequence probe",
    "leading_point",
    "Partial Truth Capture / 局部真相捕获",
    "A locally true observation must not own the whole explanation",
    "Whole Object Reconstruction / 整体对象还原",
    "reconstruct the whole object before essence judgment",
    "Whole Elephant Protocol / 全象流程",
    "Compact Semantic Triad / 三根硬支柱",
    "misdirection_if_local_wins",
    "Contrastive Consequence Probe / 后果对比探针",
    "better_direction_for_target",
    "start by naming the complete object before summarizing local truths",
    "local_success_points",
    "coverage_weight",
    "weighted_synthesis",
    "whole_first_re_evaluation",
    "strategy_choice",
    "definition_owner",
    "result_controller",
    "decision_consequence",
    "mindthus-whole-elephant-audit-v0.1",
    "When Partial Truth Capture triggers, the formal answer is incomplete without",
    "target job",
    "main use cases",
    "primary value carrier",
    "local interface role",
    "authority_weight",
    "overreach_risk",
    "corrected_thesis",
    "grant authority only when the local frame carries the target result",
    "would change the decision if removed",
    "predicts outcomes or failures better than competing frames",
    "blocked_by_missing_evidence when the whole-object carrier is unknown",
    "definition consequence",
    "optimization direction",
    "Non-Mirror Correction / 非镜像纠错",
    "Failure Channel / 失败通道",
    "Anti-Sycophancy / 反谄媚",
    "Core Thesis Extraction / 主判断收束",
    "Essence Wording Guard / 本质措辞护栏",
    "Auxiliary checks belong inside step 3",
    "Explanatory Authority Check / 解释权校准",
    "Dominant Carrier Check / 主导承载校准",
    "System Subject Check / 系统主体校准",
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


def configured_marketplace_root(codex_home: Path) -> Path:
    fallback = default_marketplace_root(codex_home)
    config_path = codex_home / "config.toml"
    if not config_path.is_file():
        return fallback
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        marketplace = config["marketplaces"][MARKETPLACE_IDENTITY]
        if marketplace.get("source_type") != "local":
            return fallback
        source_root = Path(marketplace["source"]).expanduser().resolve()
        manifest = json.loads(
            (source_root / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        plugin = next(
            item for item in manifest["plugins"] if item.get("name") == PACKAGE_IDENTITY
        )
        plugin_source = plugin["source"]
        if plugin_source.get("source") != "local":
            return fallback
        return (source_root / plugin_source["path"]).resolve()
    except (KeyError, StopIteration, OSError, tomllib.TOMLDecodeError, TypeError, ValueError):
        return fallback


def default_cache_root(codex_home: Path) -> Path:
    return codex_home / "plugins" / "cache" / MARKETPLACE_IDENTITY / PACKAGE_IDENTITY / VERSION


def sha256_text(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def inspect_file(root: Path, rel: str) -> dict[str, Any]:
    candidates = [root / rel]
    if rel in RUNTIME_TOP_LEVEL_ALIASES:
        candidates.append(root / RUNTIME_TOP_LEVEL_ALIASES[rel])
    path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    exists = path.is_file()
    info: dict[str, Any] = {
        "path": str(path),
        "canonical_relative_path": rel,
        "exists": exists,
    }
    if path != candidates[0]:
        info["resolved_relative_path"] = RUNTIME_TOP_LEVEL_ALIASES[rel]
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
    files = {rel: inspect_file(root, rel) for rel in RELATIVE_FILES}
    return {"label": label, "root": str(root), "exists": root.exists(), "files": files}


def compare_hashes(locations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for rel in RELATIVE_FILES:
        presence = {
            label: bool(location["files"][rel].get("exists"))
            for label, location in locations.items()
        }
        hashes = {
            label: location["files"][rel].get("sha256")
            for label, location in locations.items()
            if location["files"][rel].get("sha256")
        }
        unique_hashes = sorted(set(hashes.values()))
        comparisons[rel] = {
            "hashes": hashes,
            "presence": presence,
            "all_present": all(presence.values()),
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
    all_tracked_files_present = all(
        comparison["all_present"] for comparison in comparisons.values()
    )
    status = (
        "ok"
        if all_required_markers_present and all_available_hashes_match and all_tracked_files_present
        else "mismatch"
    )
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
            "all_tracked_files_present": all_tracked_files_present,
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    codex_home = default_codex_home()
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Runtime boundary: status=ok verifies installed files, hashes, and marker "
            "presence only. It does not prove model behavior, semantic judgment quality, "
            "or runtime activation correctness."
        ),
    )
    parser.add_argument("--repo-root", default=repo_root(), type=Path, help="Mindthus repository root.")
    parser.add_argument(
        "--marketplace-root",
        default=None,
        type=Path,
        help="Installed local marketplace plugin root.",
    )
    parser.add_argument(
        "--cache-root",
        default=None,
        type=Path,
        help="Codex plugin cache root.",
    )
    parser.add_argument("--codex-home", default=codex_home, type=Path, help="Codex home directory.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on missing tracked files, missing markers, or hash mismatch.",
    )
    args = parser.parse_args(argv)
    args.codex_home = Path(args.codex_home).expanduser()
    if args.marketplace_root is None:
        args.marketplace_root = configured_marketplace_root(args.codex_home)
    else:
        args.marketplace_root = Path(args.marketplace_root).expanduser()
    if args.cache_root is None:
        args.cache_root = default_cache_root(args.codex_home)
    else:
        args.cache_root = Path(args.cache_root).expanduser()
    return args


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 1 if args.strict and report["summary"]["status"] != "ok" else 0


if __name__ == "__main__":
    raise SystemExit(main())
