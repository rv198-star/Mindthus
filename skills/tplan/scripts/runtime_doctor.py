#!/usr/bin/env python3
"""Diagnose selected, installed, duplicate, and Mission-bound TPlan runtimes."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from tplan_runtime import (
    TplanError,
    load_runtime_manifest,
    read_json,
    runtime_fingerprint,
    runtime_fingerprint_compatibility,
    runtime_provenance_report,
    runtime_skill_root,
)


DOCTOR_SCHEMA_VERSION = "tplan.runtime_doctor.v0.1"
FALLBACK_REQUIRED_SCRIPTS = (
    "scripts/tplan_runtime.py",
    "scripts/execution_cost_tree.py",
    "scripts/render_execution_cost_tree.py",
    "scripts/runtime_doctor.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose TPlan runtime provenance, duplicates, and capabilities."
    )
    parser.add_argument("mission_dir", nargs="?", help="Optional Mission directory to compare.")
    parser.add_argument(
        "--selected-root",
        help="TPlan skill root, Mindthus skills root, or checkout selected for this run.",
    )
    parser.add_argument(
        "--installed-root",
        help="Expected installed/canonical TPlan or Mindthus skills root.",
    )
    parser.add_argument(
        "--candidate-root",
        action="append",
        default=[],
        help="Additional discovered TPlan or Mindthus skills root. Repeat as needed.",
    )
    parser.add_argument(
        "--selection-mode",
        choices=("explicit", "discovery"),
        default="explicit",
        help="Whether selection is known explicitly or unresolved discovery.",
    )
    parser.add_argument(
        "--no-default-discovery",
        action="store_true",
        help="Inspect only roots supplied on the command line.",
    )
    parser.add_argument("--format", choices=("json",), default="json")
    return parser.parse_args()


def normalize_tplan_root(path: Path) -> Path:
    expanded = path.expanduser()
    candidates = (expanded, expanded / "tplan", expanded / "skills" / "tplan")
    for candidate in candidates:
        if (candidate / "SKILL.md").is_file() or (
            candidate / "scripts" / "tplan_runtime.py"
        ).is_file():
            return candidate.resolve()
    return expanded.resolve()


def default_candidate_roots() -> list[Path]:
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    candidates = [
        runtime_skill_root(),
        codex_home / "mindthus" / "skills" / "tplan",
        codex_home / "skills" / "mindthus",
    ]
    plugin_cache = codex_home / "plugins" / "cache" / "mindthus" / "mindthus"
    if plugin_cache.is_dir():
        candidates.extend(sorted(plugin_cache.glob("*/skills/tplan")))
    configured = os.environ.get("MINDTHUS_TPLAN_ROOT")
    if configured:
        candidates.append(Path(configured))
    return candidates


def _diagnostic(
    diagnostics: list[dict[str, str]],
    severity: str,
    code: str,
    message: str,
) -> None:
    item = {"severity": severity, "code": code, "message": message}
    if item not in diagnostics:
        diagnostics.append(item)


def _legacy_version_from_path(skill_root: Path) -> str | None:
    for part in reversed(skill_root.parts):
        match = re.search(r"(?:^|[-_])v?(\d+\.\d+(?:\.\d+)?)$", part)
        if match is None:
            continue
        version = match.group(1)
        return version if version.count(".") == 2 else version + ".0"
    return None


def _legacy_version_from_git_describe(describe: str | None) -> str | None:
    if not describe:
        return None
    match = re.match(r"^v?(\d+\.\d+(?:\.\d+)?)", describe)
    if match is None:
        return None
    version = match.group(1)
    return version if version.count(".") == 2 else version + ".0"


def _git_output(skill_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(skill_root), *args],
            text=True,
            capture_output=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def _legacy_git_identity(skill_root: Path) -> dict[str, Any] | None:
    repo_root = _git_output(skill_root, "rev-parse", "--show-toplevel")
    commit = _git_output(skill_root, "rev-parse", "HEAD")
    if repo_root is None or commit is None or re.fullmatch(r"[0-9a-fA-F]{40,64}", commit) is None:
        return None
    describe = _git_output(skill_root, "describe", "--tags", "--always", "--dirty")
    dirty = bool(describe and describe.endswith("-dirty"))
    return {
        "repo_root": str(Path(repo_root).resolve()),
        "commit": commit.lower(),
        "describe": describe,
        "dirty": dirty,
        "package_version": _legacy_version_from_git_describe(describe),
        "source_id": f"git:{commit.lower()}" + (":dirty" if dirty else ""),
    }


def _legacy_capability_probe(skill_root: Path) -> tuple[list[str], dict[str, str]]:
    scripts = skill_root / "scripts"
    runtime_path = scripts / "tplan_runtime.py"
    try:
        runtime_source = runtime_path.read_text(encoding="utf-8")
    except OSError:
        runtime_source = ""
    capabilities: list[str] = []
    versions: dict[str, str] = {}
    if "EXECUTION_TRACE_SCHEMA_VERSION" in runtime_source:
        capabilities.append("execution_trace")
        versions["execution_trace"] = "detected_unversioned"
    if "commit_mission_state" in runtime_source:
        capabilities.append("atomic_mission_mutation")
    if (scripts / "render_execution_cost_tree.py").is_file():
        capabilities.append("execution_cost_renderer")
        versions["execution_cost_tree"] = "detected_unversioned"
    if (scripts / "runtime_doctor.py").is_file():
        capabilities.append("runtime_doctor")
        versions["runtime_doctor"] = "detected_unversioned"
    return sorted(capabilities), dict(sorted(versions.items()))


def inspect_runtime_root(configured_paths: Iterable[Path]) -> dict[str, Any]:
    configured = [str(path.expanduser()) for path in configured_paths]
    normalized = normalize_tplan_root(Path(configured[0]))
    manifest: dict[str, Any] | None = None
    manifest_error: str | None = None
    try:
        manifest = load_runtime_manifest(normalized)
    except (OSError, TplanError, ValueError) as exc:
        manifest_error = str(exc)
    required_scripts = sorted(
        set(FALLBACK_REQUIRED_SCRIPTS)
        | set(manifest["required_scripts"] if manifest is not None else [])
    )
    missing_scripts = [
        relative for relative in required_scripts if not (normalized / relative).is_file()
    ]
    fingerprint: dict[str, Any] | None = None
    fingerprint_error: str | None = None
    if manifest is not None and not missing_scripts:
        try:
            fingerprint = runtime_fingerprint(normalized)
        except (OSError, TplanError, ValueError) as exc:
            fingerprint_error = str(exc)
    git_identity = _legacy_git_identity(normalized) if manifest is None else None
    path_version = _legacy_version_from_path(normalized) if manifest is None else None
    legacy_version = (
        git_identity.get("package_version")
        if git_identity is not None and git_identity.get("package_version")
        else path_version
    )
    detected_capabilities, detected_versions = (
        _legacy_capability_probe(normalized) if manifest is None else ([], {})
    )
    if manifest is not None:
        identity_source = "manifest"
        source_id = manifest.get("source_id")
    elif git_identity is not None:
        identity_source = "git"
        source_id = git_identity["source_id"]
    elif path_version is not None:
        identity_source = "path_inference"
        source_id = f"mindthus-v{path_version}"
    else:
        identity_source = "unavailable"
        source_id = None
    return {
        "configured_paths": configured,
        "skill_root": str(normalized),
        "script_root": str((normalized / "scripts").resolve()),
        "exists": normalized.exists(),
        "manifest_path": str(normalized / "resources" / "runtime-manifest.json"),
        "manifest": manifest,
        "manifest_error": manifest_error,
        "package_version": (
            manifest.get("package_version") if manifest else legacy_version
        ),
        "source_id": source_id,
        "identity_source": identity_source,
        "git_identity": git_identity,
        "capability_source": "manifest" if manifest else "filesystem_probe",
        "capability_versions": (
            manifest.get("capability_versions", {}) if manifest else detected_versions
        ),
        "capabilities": (
            manifest.get("capabilities", []) if manifest else detected_capabilities
        ),
        "required_scripts": required_scripts,
        "missing_scripts": missing_scripts,
        "fingerprint": fingerprint,
        "fingerprint_error": fingerprint_error,
    }


def build_doctor_report(
    *,
    selected_root: Path | None,
    installed_root: Path | None,
    candidate_roots: Iterable[Path],
    selection_mode: str,
    mission_dir: Path | None,
    include_default_candidates: bool,
) -> dict[str, Any]:
    if selection_mode not in {"explicit", "discovery"}:
        raise TplanError("runtime doctor selection_mode unsupported")
    if selection_mode == "explicit" and selected_root is None:
        selected_root = runtime_skill_root()

    configured_roots = list(candidate_roots)
    if include_default_candidates:
        configured_roots.extend(default_candidate_roots())
    if selected_root is not None:
        configured_roots.append(selected_root)
    if installed_root is not None:
        configured_roots.append(installed_root)

    aliases_by_root: dict[str, list[Path]] = {}
    for configured in configured_roots:
        normalized = normalize_tplan_root(configured)
        if not normalized.exists():
            if configured in {selected_root, installed_root}:
                aliases_by_root.setdefault(str(normalized), []).append(configured)
            continue
        aliases_by_root.setdefault(str(normalized), []).append(configured)
    inspections = [
        inspect_runtime_root(aliases)
        for _, aliases in sorted(aliases_by_root.items())
    ]
    by_root = {item["skill_root"]: item for item in inspections}

    selected_path = (
        str(normalize_tplan_root(selected_root)) if selected_root is not None else None
    )
    installed_path = (
        str(normalize_tplan_root(installed_root)) if installed_root is not None else None
    )
    selected = by_root.get(selected_path) if selected_path else None
    installed = by_root.get(installed_path) if installed_path else None
    diagnostics: list[dict[str, str]] = []

    for candidate in inspections:
        candidate_is_selected = candidate is selected
        if not candidate_is_selected and candidate["manifest_error"]:
            _diagnostic(
                diagnostics,
                "warning",
                "candidate_runtime_manifest_invalid",
                candidate["manifest_error"],
            )
        if not candidate_is_selected and candidate["missing_scripts"]:
            _diagnostic(
                diagnostics,
                "warning",
                "candidate_runtime_missing_scripts",
                (
                    f"candidate runtime {candidate['skill_root']} is missing: "
                    + ", ".join(candidate["missing_scripts"])
                ),
            )
        if not candidate_is_selected and candidate["fingerprint_error"]:
            _diagnostic(
                diagnostics,
                "warning",
                "candidate_runtime_fingerprint_failed",
                candidate["fingerprint_error"],
            )
        if "scripts/render_execution_cost_tree.py" in candidate["missing_scripts"]:
            _diagnostic(
                diagnostics,
                "error" if candidate_is_selected else "warning",
                (
                    "selected_runtime_missing_renderer"
                    if candidate_is_selected
                    else "candidate_runtime_missing_renderer"
                ),
                f"TPlan runtime has no execution timeline renderer: {candidate['skill_root']}",
            )

    if selected_path and (selected is None or not selected["exists"]):
        _diagnostic(
            diagnostics,
            "error",
            "selected_runtime_missing",
            f"selected TPlan runtime does not exist: {selected_path}",
        )
    if selected is not None:
        if selected["manifest_error"]:
            _diagnostic(
                diagnostics,
                "error",
                "selected_runtime_manifest_invalid",
                selected["manifest_error"],
            )
        if selected["missing_scripts"]:
            _diagnostic(
                diagnostics,
                "error",
                "selected_runtime_missing_scripts",
                (
                    f"selected runtime {selected['skill_root']} is missing: "
                    + ", ".join(selected["missing_scripts"])
                ),
            )
        if selected["fingerprint_error"]:
            _diagnostic(
                diagnostics,
                "error",
                "selected_runtime_fingerprint_failed",
                selected["fingerprint_error"],
            )
    if installed_path and (installed is None or not installed["exists"]):
        _diagnostic(
            diagnostics,
            "error",
            "installed_runtime_missing",
            f"expected installed TPlan runtime does not exist: {installed_path}",
        )

    if len(inspections) > 1:
        severity = (
            "error"
            if selection_mode == "discovery" and selected_path is None
            else "warning"
        )
        code = (
            "ambiguous_duplicate_runtime"
            if severity == "error"
            else "duplicate_runtime_roots"
        )
        _diagnostic(
            diagnostics,
            severity,
            code,
            "multiple distinct TPlan runtime roots are configured: "
            + ", ".join(item["skill_root"] for item in inspections),
        )

    if selected is not None and installed is not None and selected_path != installed_path:
        selected_versions = selected["capability_versions"]
        installed_versions = installed["capability_versions"]
        incompatible_capabilities = {
            name: {
                "selected": selected_versions.get(name),
                "installed": installed_version,
            }
            for name, installed_version in installed_versions.items()
            if selected_versions.get(name) != installed_version
        }
        missing_capabilities = sorted(
            set(installed["capabilities"]) - set(selected["capabilities"])
        )
        if incompatible_capabilities or missing_capabilities:
            details = sorted(incompatible_capabilities)
            details.extend(f"capability:{name}" for name in missing_capabilities)
            _diagnostic(
                diagnostics,
                "error",
                "selected_runtime_incompatible_capabilities",
                (
                    "selected runtime has missing or incompatible installed capability "
                    "versions: "
                    + ", ".join(details)
                ),
            )
        if selected["fingerprint"] is not None and installed["fingerprint"] is not None:
            compatibility = runtime_fingerprint_compatibility(
                installed["fingerprint"],
                selected["fingerprint"],
            )
            _diagnostic(
                diagnostics,
                "warning" if compatibility["compatible"] else "error",
                (
                    "selected_runtime_relocated_from_installed"
                    if compatibility["compatible"]
                    else "selected_runtime_incompatible_with_installed"
                ),
                (
                    f"selected runtime {selected_path} differs from installed runtime "
                    f"{installed_path}; compatibility={compatibility['status']}"
                ),
            )
        else:
            _diagnostic(
                diagnostics,
                "error",
                "selected_runtime_incompatible_with_installed",
                (
                    f"selected runtime {selected_path} cannot be proven compatible "
                    f"with installed runtime {installed_path}"
                ),
            )

    mission_report: dict[str, Any] | None = None
    if mission_dir is not None:
        mission = read_json(mission_dir / "mission.json")
        if not isinstance(mission, dict):
            raise TplanError("Mission runtime state must be a JSON object")
        if selected is not None and selected["fingerprint"] is not None:
            mission_report = runtime_provenance_report(
                mission,
                current=selected["fingerprint"],
            )
            for item in mission_report["diagnostics"]:
                _diagnostic(
                    diagnostics,
                    mission_report["severity"],
                    item["code"],
                    item["message"],
                )
        else:
            _diagnostic(
                diagnostics,
                "error",
                "mission_runtime_comparison_unavailable",
                "Mission fingerprint cannot be compared because the selected runtime is invalid",
            )

    severity_rank = {"ok": 0, "warning": 1, "error": 2}
    highest = max(
        (severity_rank[item["severity"]] for item in diagnostics),
        default=0,
    )
    status = ("ok", "warning", "failed")[highest]
    remediation = [
        "Remove or disable stale duplicate TPlan skill paths from the active Codex profile.",
        "Explicitly validate and execute scripts from the intended installed TPlan root when duplicate discovery is intentional.",
        "Re-run runtime_doctor.py and require status ok or an understood compatible relocation before mutation or terminal handoff.",
    ]
    return {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "status": status,
        "selection_mode": selection_mode,
        "selected_root": selected_path,
        "installed_root": installed_path,
        "candidate_count": len(inspections),
        "candidates": inspections,
        "mission_dir": str(mission_dir.resolve()) if mission_dir is not None else None,
        "mission_runtime": mission_report,
        "diagnostics": diagnostics,
        "remediation": remediation,
        "boundary": (
            "diagnosis and supported-runtime rejection only; arbitrary filesystem writers "
            "require a host-enforced sole-writer boundary"
        ),
    }


def main() -> int:
    args = parse_args()
    try:
        report = build_doctor_report(
            selected_root=Path(args.selected_root) if args.selected_root else None,
            installed_root=Path(args.installed_root) if args.installed_root else None,
            candidate_roots=[Path(item) for item in args.candidate_root],
            selection_mode=args.selection_mode,
            mission_dir=Path(args.mission_dir) if args.mission_dir else None,
            include_default_candidates=not args.no_default_discovery,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["status"] == "failed" else 0
    except (OSError, TplanError, ValueError, json.JSONDecodeError) as exc:
        print(f"TPlan runtime doctor failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
