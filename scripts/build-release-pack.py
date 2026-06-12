#!/usr/bin/env python3
"""Build platform-specific Mindthus release packs."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


VERSION = "1.1.0"
EXCLUDED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".tplan",
    ".tvg",
    "artifacts",
    "logs",
    "test",
    "tests",
}
EXCLUDED_SUFFIXES = {".gif", ".jpeg", ".jpg", ".log", ".mov", ".mp4", ".png", ".pyc", ".pyo", ".tmp", ".webp"}
METHODOLOGY_BINARY_ASSET_ALLOWLIST = {
    Path("assets/tplan-okr-runtime.png"),
    Path("assets/tvg-architecture.png"),
}
EXCLUDED_NAME_SUBSTRINGS = ("ab_run", "pilot")
JSONL_ALLOWLIST = {Path("tplan/templates/evidence.jsonl")}
TEXT_REWRITE_SUFFIXES = {".md"}
SKILL_NAMES = ("3l5s", "sela", "mpg", "edsp", "wae", "tvg", "tplan", "using-mindthus")
LICENSE_FILES = ("LICENSE", "COMMERCIAL-LICENSE.md")
RELEASE_SCRIPTS = ("run-fidelity-judge.py", "log-fidelity-usage.py")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_output_dir(path: Path, force: bool) -> None:
    if path.exists() and not path.is_dir():
        raise SystemExit(f"output path exists and is not a directory: {path}")
    if path.exists():
        if any(path.iterdir()):
            if not force:
                raise SystemExit(f"output directory is not empty: {path}")
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def ensure_safe_output_dir(path: Path, root: Path) -> None:
    protected_sources = [
        root,
        root / "skills",
        root / "docs",
        root / "scripts",
        root / "tests",
        root / ".git",
    ]
    if len(path.parts) <= 2:
        raise SystemExit(f"refusing broad output directory: {path}")
    if path in root.parents:
        raise SystemExit(f"refusing repository parent output directory: {path}")
    if any(path == protected or protected in path.parents for protected in protected_sources):
        raise SystemExit(f"refusing output directory inside protected source tree: {path}")


def rewrite_text(text: str, replacements: dict[str, str]) -> str:
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def copy_file_filtered(source: Path, target: Path, replacements: dict[str, str] | None = None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if replacements and source.suffix in TEXT_REWRITE_SUFFIXES:
        text = source.read_text(encoding="utf-8")
        target.write_text(rewrite_text(text, replacements), encoding="utf-8")
        return
    shutil.copy2(source, target)


def copy_tree_filtered(
    source: Path,
    target: Path,
    replacements: dict[str, str] | None = None,
    binary_asset_allowlist: set[Path] | None = None,
) -> None:
    binary_asset_allowlist = binary_asset_allowlist or set()
    for item in sorted(source.rglob("*")):
        rel = item.relative_to(source)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        lowered = rel.as_posix().lower()
        if any(token in lowered for token in EXCLUDED_NAME_SUBSTRINGS):
            continue
        dest = target / rel
        if item.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        if item.suffix in EXCLUDED_SUFFIXES and rel not in binary_asset_allowlist:
            continue
        if item.suffix == ".jsonl" and rel not in JSONL_ALLOWLIST:
            continue
        copy_file_filtered(item, dest, replacements)


def skill_path_replacements(platform_skill_root: str) -> dict[str, str]:
    return {f"skills/{name}/": f"{platform_skill_root}/{name}/" for name in SKILL_NAMES}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_license_files(root: Path, target: Path) -> None:
    for filename in LICENSE_FILES:
        copy_file_filtered(root / filename, target / filename)


def copy_release_scripts(root: Path, target: Path) -> None:
    for filename in RELEASE_SCRIPTS:
        copy_file_filtered(root / "scripts" / filename, target / "scripts" / filename)


def build_claude_code(root: Path, repo: Path, skills_dir: Path, methodologies_dir: Path) -> None:
    platform_root = root / "claude-code"
    plugin_root = platform_root / "claude-plugin"

    write_json(
        platform_root / ".claude-plugin" / "marketplace.json",
        {
            "name": "mindthus",
            "description": "Mindthus public skills marketplace",
            "owner": {"name": "Mindthus"},
            "plugins": [
                {
                    "name": "mindthus",
                    "source": "./claude-plugin",
                }
            ],
        },
    )
    write_json(
        plugin_root / ".claude-plugin" / "plugin.json",
        {
            "name": "mindthus",
            "version": VERSION,
            "description": "Mindthus cognitive judgment skills pack",
            "author": {"name": "Mindthus"},
        },
    )
    copy_tree_filtered(skills_dir, plugin_root / "skills")
    copy_tree_filtered(
        methodologies_dir,
        plugin_root / "docs" / "methodologies",
        binary_asset_allowlist=METHODOLOGY_BINARY_ASSET_ALLOWLIST,
    )
    copy_license_files(repo, plugin_root)
    copy_release_scripts(repo, plugin_root)


def build_codex(root: Path, repo: Path, skills_dir: Path, agents_file: Path, methodologies_dir: Path) -> None:
    platform_root = root / "codex"
    replacements = skill_path_replacements("skills/mindthus")
    copy_tree_filtered(skills_dir, platform_root / "skills" / "mindthus", replacements)
    copy_tree_filtered(
        methodologies_dir,
        platform_root / "docs" / "methodologies",
        replacements,
        binary_asset_allowlist=METHODOLOGY_BINARY_ASSET_ALLOWLIST,
    )
    copy_file_filtered(agents_file, platform_root / "AGENTS.md", replacements)
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def build_opencode(root: Path, repo: Path, skills_dir: Path, agents_file: Path, methodologies_dir: Path) -> None:
    platform_root = root / "opencode"
    replacements = skill_path_replacements(".opencode/skills/mindthus")
    copy_tree_filtered(skills_dir, platform_root / ".opencode" / "skills" / "mindthus", replacements)
    copy_tree_filtered(
        methodologies_dir,
        platform_root / "docs" / "methodologies",
        replacements,
        binary_asset_allowlist=METHODOLOGY_BINARY_ASSET_ALLOWLIST,
    )
    copy_file_filtered(agents_file, platform_root / "AGENTS.md", replacements)
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Output directory for the release pack.")
    parser.add_argument("--force", action="store_true", help="Replace a non-empty output directory.")
    args = parser.parse_args()

    root = repo_root()
    skills_dir = root / "skills"
    methodologies_dir = root / "docs" / "methodologies"
    agents_file = root / "AGENTS.md"
    if not skills_dir.is_dir():
        raise SystemExit(f"skills directory not found: {skills_dir}")
    if not methodologies_dir.is_dir():
        raise SystemExit(f"methodologies directory not found: {methodologies_dir}")
    if not agents_file.is_file():
        raise SystemExit(f"AGENTS.md not found: {agents_file}")
    for filename in LICENSE_FILES:
        if not (root / filename).is_file():
            raise SystemExit(f"{filename} not found: {root / filename}")
    for filename in RELEASE_SCRIPTS:
        if not (root / "scripts" / filename).is_file():
            raise SystemExit(f"{filename} not found: {root / 'scripts' / filename}")

    output = args.out.resolve()
    ensure_safe_output_dir(output, root)
    ensure_output_dir(output, args.force)
    build_claude_code(output, root, skills_dir, methodologies_dir)
    build_codex(output, root, skills_dir, agents_file, methodologies_dir)
    build_opencode(output, root, skills_dir, agents_file, methodologies_dir)
    print(f"built Mindthus release pack at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
