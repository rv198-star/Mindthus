#!/usr/bin/env python3
"""Build platform-specific Mindthus release packs."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


VERSION = "1.4.3"
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
EXCLUDED_NAME_SUBSTRINGS = ("ab_run", "pilot")
JSONL_ALLOWLIST = {Path("tplan/templates/evidence.jsonl")}
TEXT_REWRITE_SUFFIXES = {".md"}
SKILL_NAMES = ("3l5s", "sela", "mpg", "edsp", "wae", "tvg", "tplan", "using-mindthus")
LICENSE_FILES = ("LICENSE", "COMMERCIAL-LICENSE.md")
RELEASE_SCRIPT_PATHS = (
    Path("run-fidelity-judge.py"),
    Path("log-fidelity-usage.py"),
    Path("log-mindthus-runtime.py"),
    Path("primitives/check.py"),
    Path("primitives/validate_whole_elephant.py"),
    Path("primitives/whole_elephant_validator.py"),
    Path("primitives/manifest.json"),
)
CLAUDE_ACTIVATION_ROUTER_PROMPT = (
    "遇事不要慌，先搞清楚情况再说。This is a light Mindthus activation router, not a mandatory workflow. "
    "Use mindthus:using-mindthus only at hard judgment points: problem definition, structural ambiguity, "
    "strategic trend/local-advantage tradeoff, path-carrying risk, workflow/agent/evidence control boundary, "
    "thin artifact value, mission drift, or repeated local repair. Clear, low-risk, fact-sufficient tasks "
    "should be done directly; when facts, files, runtime behavior, or platform rules are missing, acquire "
    "evidence first. If an upstream brainstorming/design workflow such as Superpowers Brainstorm is active "
    "or clearly applicable, let it control design discovery and approval; Mindthus should not repeat "
    "brainstorming and should intervene only at remaining hard judgment points."
)
CODEX_ACTIVATION_ROUTER_PROMPT = (
    "Mindthus: hard judgment point -> mindthus:using-mindthus; simple direct; "
    "evidence first; defer to Superpowers Brainstorm."
)


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
    jsonl_allowlist: set[Path] | None = None,
) -> None:
    binary_asset_allowlist = binary_asset_allowlist or set()
    jsonl_allowlist = JSONL_ALLOWLIST if jsonl_allowlist is None else jsonl_allowlist
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
        if item.suffix == ".jsonl" and rel not in jsonl_allowlist:
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
    for rel_path in RELEASE_SCRIPT_PATHS:
        copy_file_filtered(root / "scripts" / rel_path, target / "scripts" / rel_path)


def write_claude_activation_hook(plugin_root: Path) -> None:
    write_json(
        plugin_root / "hooks" / "hooks.json",
        {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup|clear|compact",
                        "hooks": [
                            {
                                "type": "command",
                                "command": '"${CLAUDE_PLUGIN_ROOT}/hooks/session-start"',
                                "async": False,
                            }
                        ],
                    }
                ]
            }
        },
    )
    script = f"""#!/usr/bin/env bash
set -euo pipefail

context='<MINDTHUS_ROUTER_CONTEXT>
{CLAUDE_ACTIVATION_ROUTER_PROMPT}
</MINDTHUS_ROUTER_CONTEXT>'

escape_for_json() {{
  local s="$1"
  s="${{s//\\\\/\\\\\\\\}}"
  s="${{s//\\"/\\\\\\"}}"
  s="${{s//$'\\n'/\\\\n}}"
  s="${{s//$'\\r'/\\\\r}}"
  s="${{s//$'\\t'/\\\\t}}"
  printf '%s' "$s"
}}

printf '{{\\n  "hookSpecificOutput": {{\\n    "hookEventName": "SessionStart",\\n    "additionalContext": "%s"\\n  }}\\n}}\\n' "$(escape_for_json "$context")"
"""
    script_path = plugin_root / "hooks" / "session-start"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(script, encoding="utf-8")
    script_path.chmod(0o755)


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
    copy_tree_filtered(methodologies_dir, plugin_root / "docs" / "methodologies")
    copy_license_files(repo, plugin_root)
    copy_release_scripts(repo, plugin_root)
    write_claude_activation_hook(plugin_root)


def build_claude_code_skills(root: Path, repo: Path, skills_dir: Path, methodologies_dir: Path) -> None:
    platform_root = root / "claude-code"
    copy_tree_filtered(skills_dir, platform_root / "skills")
    copy_tree_filtered(methodologies_dir, platform_root / "docs" / "methodologies")
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def build_codex(root: Path, repo: Path, skills_dir: Path, agents_file: Path, methodologies_dir: Path) -> None:
    platform_root = root / "codex"
    replacements = skill_path_replacements("skills/mindthus")
    copy_tree_filtered(skills_dir, platform_root / "skills" / "mindthus", replacements)
    copy_tree_filtered(
        methodologies_dir,
        platform_root / "docs" / "methodologies",
        replacements,
    )
    copy_file_filtered(agents_file, platform_root / "AGENTS.md", replacements)
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def build_codex_plugin(root: Path, repo: Path, skills_dir: Path, methodologies_dir: Path) -> None:
    marketplace_root = root / "codex-plugin"
    plugin_root = root / "codex-plugin" / "mindthus"
    write_json(
        marketplace_root / ".agents" / "plugins" / "marketplace.json",
        {
            "name": "mindthus",
            "interface": {"displayName": "Mindthus"},
            "plugins": [
                {
                    "name": "mindthus",
                    "source": {"source": "local", "path": "./mindthus"},
                    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                    "category": "Engineering",
                }
            ],
        },
    )
    write_json(
        plugin_root / ".codex-plugin" / "plugin.json",
        {
            "name": "mindthus",
            "version": VERSION,
            "description": "Judgment framework skills that help agents choose the right method before acting.",
            "author": {"name": "Mindthus"},
            "homepage": "https://github.com/rv198-star/Mindthus",
            "repository": "https://github.com/rv198-star/Mindthus",
            "license": "AGPL-3.0-only",
            "keywords": [
                "judgment",
                "agent-workflow",
                "skills",
                "decision-making",
                "tplan",
                "sela",
                "mpg",
            ],
            "skills": "./skills/",
            "interface": {
                "displayName": "Mindthus",
                "shortDescription": "Choose the right judgment lens before acting",
                "longDescription": (
                    "Mindthus is a judgment framework for AI agents. It helps Codex route "
                    "unclear, strategic, path-dependent, evidence-bound, or artifact-quality "
                    "problems to the smallest sufficient method instead of adding process everywhere. "
                    "The release-pack manifest uses SPDX AGPL-3.0-only for the open-source lane; "
                    "separate commercial licensing is documented in the repository license materials."
                ),
                "developerName": "Mindthus",
                "category": "Engineering",
                "capabilities": ["Interactive", "Read"],
                "websiteURL": "https://github.com/rv198-star/Mindthus",
                "privacyPolicyURL": "https://github.com/rv198-star/Mindthus",
                "termsOfServiceURL": "https://github.com/rv198-star/Mindthus",
                "defaultPrompt": [CODEX_ACTIVATION_ROUTER_PROMPT],
            },
        },
    )
    for skill_name in SKILL_NAMES:
        jsonl_allowlist = {Path("templates/evidence.jsonl")} if skill_name == "tplan" else set()
        copy_tree_filtered(skills_dir / skill_name, plugin_root / "skills" / skill_name, jsonl_allowlist=jsonl_allowlist)
    copy_tree_filtered(skills_dir / "_runtime", plugin_root / "_runtime")
    copy_tree_filtered(
        methodologies_dir,
        plugin_root / "docs" / "methodologies",
    )
    copy_license_files(repo, plugin_root)
    copy_release_scripts(repo, plugin_root)


def build_opencode(root: Path, repo: Path, skills_dir: Path, agents_file: Path, methodologies_dir: Path) -> None:
    platform_root = root / "opencode"
    replacements = skill_path_replacements(".opencode/skills/mindthus")
    copy_tree_filtered(skills_dir, platform_root / ".opencode" / "skills" / "mindthus", replacements)
    copy_tree_filtered(
        methodologies_dir,
        platform_root / "docs" / "methodologies",
        replacements,
    )
    copy_file_filtered(agents_file, platform_root / "AGENTS.md", replacements)
    copy_license_files(repo, platform_root)
    copy_release_scripts(repo, platform_root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Output directory for the release pack.")
    parser.add_argument(
        "--package",
        choices=("all", "plugins", "skills"),
        default="all",
        help="Package surface to build. Release assets use plugins and skills; all is for local inspection.",
    )
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
    for rel_path in RELEASE_SCRIPT_PATHS:
        if not (root / "scripts" / rel_path).is_file():
            raise SystemExit(f"{rel_path} not found: {root / 'scripts' / rel_path}")

    output = args.out.resolve()
    ensure_safe_output_dir(output, root)
    ensure_output_dir(output, args.force)
    if args.package in ("all", "plugins"):
        build_claude_code(output, root, skills_dir, methodologies_dir)
        build_codex_plugin(output, root, skills_dir, methodologies_dir)
    if args.package in ("all", "skills"):
        build_claude_code_skills(output, root, skills_dir, methodologies_dir)
        build_codex(output, root, skills_dir, agents_file, methodologies_dir)
        build_opencode(output, root, skills_dir, agents_file, methodologies_dir)
    print(f"built Mindthus {args.package} release pack at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
