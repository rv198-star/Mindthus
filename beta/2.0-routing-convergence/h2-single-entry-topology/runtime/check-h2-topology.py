#!/usr/bin/env python3
"""Fail-closed static verifier for the unpublished H2 single-entry candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


OWNERS = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")
EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".tplan", ".tvg", "artifacts", "logs", "test", "tests"}
EXCLUDED_SUFFIXES = {".gif", ".jpeg", ".jpg", ".log", ".mov", ".mp4", ".png", ".pyc", ".pyo", ".tmp", ".webp"}


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a non-empty string")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path escapes plugin root: {value}")
    return root / relative


def add(checks: list[dict], check_id: str, ok: bool, detail: str) -> None:
    checks.append({"id": check_id, "status": "ok" if ok else "failed", "detail": detail})


def normalized_owner_digest(owner_root: Path, name: str) -> str:
    digest = hashlib.sha256()
    for item in sorted(owner_root.rglob("*")):
        if not item.is_file():
            continue
        relative = item.relative_to(owner_root)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if item.suffix in EXCLUDED_SUFFIXES:
            continue
        if item.suffix == ".jsonl" and relative != Path("templates/evidence.jsonl"):
            continue
        normalized_relative = Path("SKILL.md") if relative == Path("OWNER.md") else relative
        payload = item.read_bytes()
        if item.suffix == ".md":
            text = payload.decode("utf-8")
            for owner in OWNERS:
                text = text.replace(
                    f"skills/using-mindthus/references/owners/{owner}/",
                    f"skills/{owner}/",
                )
            for companion in ("sela", "mpg"):
                if companion == name:
                    continue
                companion_path = Path(
                    os.path.relpath(
                        owner_root.parent / companion / "OWNER.md",
                        item.parent,
                    )
                ).as_posix()
                text = text.replace(companion_path, f"mindthus:{companion}")
            payload = text.encode("utf-8")
        digest.update(normalized_relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def plain_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        relative = item.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in relative.parts) or item.suffix in EXCLUDED_SUFFIXES:
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def diagnose(root: Path, stable_state: str, require_isolated: bool) -> dict:
    checks: list[dict] = []
    try:
        profile = json.loads((root / "beta" / "release-profile.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "mindthus-h2-diagnostic-v0.1",
            "integrity": "failed",
            "runtime_isolation_status": "unverified",
            "claim_ceiling": "candidate profile is unreadable",
            "checks": [{"id": "profile", "status": "failed", "detail": str(exc)}],
        }

    add(
        checks,
        "profile-contract",
        profile.get("schema_version") == "mindthus-release-profile-v0.5"
        and profile.get("release_line") == "2.0-routing-h2-single-entry"
        and profile.get("version") == "2.0.0-next.3"
        and profile.get("carrier_mode") == "single-entry-resource-owners"
        and profile.get("supported_surfaces") == ["codex-plugin"],
        "unpublished Codex-only H2 profile",
    )

    try:
        manifest = json.loads((root / ".codex-plugin" / "plugin.json").read_text())
        interface = manifest.get("interface", {})
        add(
            checks,
            "plugin-manifest",
            manifest.get("name") == "mindthus-beta"
            and manifest.get("version") == "2.0.0-next.3"
            and manifest.get("skills") == "./skills/"
            and "hooks" not in manifest
            and "defaultPrompt" not in interface,
            "one skills root, no Hook, no defaultPrompt",
        )
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        add(checks, "plugin-manifest", False, str(exc))

    skill_files = sorted(path.relative_to(root).as_posix() for path in (root / "skills").rglob("SKILL.md"))
    add(
        checks,
        "single-discoverable-skill",
        skill_files == ["skills/using-mindthus/SKILL.md"],
        str(skill_files),
    )
    reference_skills = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "reference").rglob("SKILL.md")
    )
    add(checks, "no-reference-skill-atlas", not reference_skills, str(reference_skills))
    add(
        checks,
        "no-reference-method-atlas",
        not (root / "reference" / "1.4.6" / "docs" / "methodologies").exists(),
        "reference/1.4.6/docs/methodologies",
    )

    owner_root = root / "skills" / "using-mindthus" / "references" / "owners"
    lock_records: dict[str, dict] = {}
    try:
        lock = json.loads(safe(root, profile.get("reference_lock")).read_text())
        lock_records = {
            str(record.get("id")): record
            for record in lock.get("trees", [])
            if isinstance(record, dict)
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        add(checks, "reference-lock", False, str(exc))
    for owner in OWNERS:
        try:
            built = owner_root / owner
            actual = normalized_owner_digest(built, owner)
            expected = lock_records[f"owner-{owner}"]["sha256"]
            add(
                checks,
                f"owner-lock:{owner}",
                (built / "OWNER.md").is_file()
                and not (built / "SKILL.md").exists()
                and actual == expected,
                actual,
            )
        except (OSError, KeyError, TypeError) as exc:
            add(checks, f"owner-lock:{owner}", False, str(exc))
    companion_paths: list[str] = []
    broken_companion_paths: list[str] = []
    for markdown in owner_root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        declaring_owner = markdown.relative_to(owner_root).parts[0]
        for companion in ("sela", "mpg"):
            if companion == declaring_owner:
                continue
            relative = Path(
                os.path.relpath(owner_root / companion / "OWNER.md", markdown.parent)
            ).as_posix()
            if relative in text:
                companion_paths.append(f"{markdown.relative_to(root)}:{relative}")
                if not (markdown.parent / relative).resolve().is_file():
                    broken_companion_paths.append(companion_paths[-1])
    add(
        checks,
        "owner-companion-paths",
        len(companion_paths) >= 2 and not broken_companion_paths,
        f"declared={len(companion_paths)} broken={broken_companion_paths}",
    )
    try:
        runtime_actual = plain_tree_digest(owner_root / "_runtime")
        runtime_expected = lock_records["owner-shared-runtime"]["sha256"]
        add(checks, "owner-lock:_runtime", runtime_actual == runtime_expected, runtime_actual)
    except (OSError, KeyError, TypeError) as exc:
        add(checks, "owner-lock:_runtime", False, str(exc))

    index = root / "skills" / "using-mindthus" / "references" / "owner-index.md"
    try:
        index_text = index.read_text()
        refs = [f"owners/{owner}/OWNER.md" for owner in OWNERS]
        add(
            checks,
            "owner-index",
            all(index_text.count(ref) == 1 for ref in refs),
            f"owner_refs={sum(index_text.count(ref) for ref in refs)}",
        )
    except OSError as exc:
        add(checks, "owner-index", False, str(exc))

    for relative in profile.get("forbidden_active_paths", []):
        try:
            add(checks, f"forbidden:{relative}", not safe(root, relative).exists(), relative)
        except ValueError as exc:
            add(checks, f"forbidden:{relative}", False, str(exc))
    for relative, expected in profile.get("artifact_sha256", {}).items():
        try:
            actual = sha(safe(root, relative).read_bytes())
            add(checks, f"artifact:{relative}", actual == expected, actual)
        except (OSError, ValueError) as exc:
            add(checks, f"artifact:{relative}", False, str(exc))
    for relative, expected in profile.get("generated_artifact_sha256", {}).get("codex-plugin", {}).items():
        try:
            actual = sha(safe(root, relative).read_bytes())
            add(checks, f"generated:{relative}", actual == expected, actual)
        except (OSError, ValueError) as exc:
            add(checks, f"generated:{relative}", False, str(exc))

    isolation = (
        "isolated-reported"
        if stable_state in {"disabled", "not-installed"}
        else "conflict" if stable_state == "enabled" else "unverified"
    )
    integrity = "ok" if all(item["status"] == "ok" for item in checks) else "failed"
    if require_isolated and isolation != "isolated-reported":
        integrity = "failed"
    ceiling = (
        "static package and reported isolation only; entry activation, on-demand owner reads, "
        "passive obligations, quality, tokens, and usability remain unproven"
        if integrity == "ok"
        else "H2 package integrity or isolation is not established"
    )
    return {
        "schema_version": "mindthus-h2-diagnostic-v0.1",
        "integrity": integrity,
        "runtime_isolation_status": isolation,
        "claim_ceiling": ceiling,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", required=True, type=Path)
    parser.add_argument(
        "--stable-state", choices=("unknown", "disabled", "not-installed", "enabled"), default="unknown"
    )
    parser.add_argument("--require-isolated", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = diagnose(args.plugin_root.resolve(), args.stable_state, args.require_isolated)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["claim_ceiling"])
    return 0 if result["integrity"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
