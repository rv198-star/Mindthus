#!/usr/bin/env python3
"""Build one unpublished Mindthus 2.x ROI-convergence route."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def candidate_root() -> Path:
    return Path(__file__).resolve().parent


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_safe_output(path: Path, root: Path, force: bool) -> None:
    if path == root or root in path.parents or path in root.parents:
        raise SystemExit("candidate output must be outside the repository tree")
    if path.exists():
        if not path.is_dir():
            raise SystemExit(f"output exists and is not a directory: {path}")
        if any(path.iterdir()):
            if not force:
                raise SystemExit(f"output is not empty: {path}; pass --force to replace it")
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def replace_exact(path: Path, before: str, after: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1 or after in text:
        raise SystemExit(f"{label} no longer matches exactly once: {path}")
    path.write_text(text.replace(before, after), encoding="utf-8")


def verify_source_owner_baseline(root: Path, baseline: str, owners: list[str]) -> None:
    result = subprocess.run(
        ["git", "diff", "--quiet", baseline, "--", *[f"skills/{x}" for x in owners]],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("source owner Skill trees differ from the frozen 1.4.6 baseline")


def skill_inventory(plugin_root: Path) -> list[str]:
    return sorted(
        path.relative_to(plugin_root).as_posix()
        for path in (plugin_root / "skills").rglob("SKILL.md")
    )


def build(route: str, output: Path, force: bool) -> Path:
    root = repo_root()
    base = candidate_root()
    profile = read_json(base / "profile.json")
    route_profile = profile["routes"][route]
    owners = profile["owner_skills"]
    stable_commit = profile["baseline"]["stable_commit"]

    ensure_safe_output(output, root, force)
    verify_source_owner_baseline(root, stable_commit, owners)

    with tempfile.TemporaryDirectory(prefix=f"mindthus-roi-{route}-build-") as temporary:
        stable_out = Path(temporary) / "stable-pack"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "build-release-pack.py"),
                "--package",
                "plugins",
                "--out",
                str(stable_out),
            ],
            cwd=root,
            check=True,
        )
        shutil.copytree(stable_out / "codex-plugin", output, dirs_exist_ok=True)

    plugin_root = output / "mindthus"
    using_target = plugin_root / "skills" / "using-mindthus" / "SKILL.md"
    if route_profile["remove_using"]:
        shutil.rmtree(using_target.parent)
    else:
        overlay = base / route_profile["using_overlay"]
        shutil.copy2(overlay, using_target)

    correction = profile["package_time_contract_correction"]
    replace_exact(
        plugin_root / correction["path"],
        correction["before"],
        correction["after"],
        "3L5S correction",
    )

    if "edsp" in route_profile["owner_metadata_overrides"]:
        override = profile["edsp_description_override"]
        replace_exact(
            plugin_root / "skills" / "edsp" / "SKILL.md",
            override["before"],
            override["after"],
            "EDSP description override",
        )

    marketplace_path = output / ".agents" / "plugins" / "marketplace.json"
    marketplace = read_json(marketplace_path)
    marketplace["name"] = route_profile["marketplace"]
    marketplace["interface"]["displayName"] = f"Mindthus ROI {route.upper()}"
    write_json(marketplace_path, marketplace)

    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest = read_json(manifest_path)
    manifest["version"] = route_profile["version"]
    manifest["description"] = f"Unpublished Mindthus ROI convergence route {route.upper()}."
    manifest["interface"]["displayName"] = f"Mindthus ROI {route.upper()}"
    manifest["interface"]["shortDescription"] = "Test recall-constrained ROI on Codex"
    write_json(manifest_path, manifest)

    inventory = skill_inventory(plugin_root)
    expected_count = len(owners) + (0 if route_profile["remove_using"] else 1)
    if len(inventory) != expected_count:
        raise SystemExit(
            f"unexpected discoverable Skill count for {route}: {len(inventory)} != {expected_count}"
        )
    if any("owner-index" in path for path in inventory):
        raise SystemExit("owner index unexpectedly entered Skill discovery")
    if (plugin_root / "hooks").exists() or (plugin_root / "AGENTS.md").exists():
        raise SystemExit("forbidden Hook or AGENTS carrier exists in candidate")
    if "defaultPrompt" in manifest:
        raise SystemExit("candidate manifest must not contain defaultPrompt")

    packaged_profile = {
        "schema_version": profile["schema_version"],
        "route": route,
        "version": route_profile["version"],
        "marketplace": route_profile["marketplace"],
        "stable_commit": stable_commit,
        "incumbent_commit": profile["baseline"]["incumbent_commit"],
        "discoverable_skills": inventory,
        "skill_sha256": {
            relative: sha256(plugin_root / relative) for relative in inventory
        },
        "using_bytes": using_target.stat().st_size if using_target.is_file() else 0,
        "route_definition": route_profile,
        "release_preparation": False,
    }
    write_json(plugin_root / "candidate-profile.json", packaged_profile)
    return plugin_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", required=True, choices=("r1", "r2", "r3"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    plugin_root = build(args.route, args.out.resolve(), args.force)
    print(f"built {args.route} candidate at {plugin_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
