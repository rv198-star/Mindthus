#!/usr/bin/env python3
"""Assemble the unpublished Codex-only Mindthus 2.x ROI candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CANDIDATE_VERSION = "2.0.0-roi.1"
MARKETPLACE_NAME = "mindthus-roi"
OWNER_SKILLS = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def verify_owner_baseline(root: Path, baseline: str) -> None:
    paths = [f"skills/{name}" for name in OWNER_SKILLS]
    result = subprocess.run(
        ["git", "diff", "--quiet", baseline, "--", *paths],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit("owner Skill trees differ from the declared 1.4.6 baseline")


def build(output: Path, force: bool) -> Path:
    root = repo_root()
    candidate_root = root / "beta" / "2.0-roi-thin-core"
    profile_path = candidate_root / "profile.json"
    overlay = candidate_root / "skills" / "using-mindthus" / "SKILL.md"
    profile = read_json(profile_path)
    baseline = profile["baseline"]["commit"]

    ensure_safe_output(output, root, force)
    verify_owner_baseline(root, baseline)

    with tempfile.TemporaryDirectory(prefix="mindthus-roi-build-") as temporary:
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
    shutil.copy2(overlay, using_target)

    marketplace_path = output / ".agents" / "plugins" / "marketplace.json"
    marketplace = read_json(marketplace_path)
    marketplace["name"] = MARKETPLACE_NAME
    marketplace["interface"]["displayName"] = "Mindthus ROI Candidate"
    write_json(marketplace_path, marketplace)

    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest = read_json(manifest_path)
    manifest["version"] = CANDIDATE_VERSION
    manifest["description"] = "Unpublished ROI-first Mindthus 2.x Thin Core candidate."
    manifest["interface"]["displayName"] = "Mindthus ROI Candidate"
    manifest["interface"]["shortDescription"] = "Test a smaller judgment entry on Codex"
    write_json(manifest_path, manifest)

    packaged_profile = dict(profile)
    packaged_profile["overlay_sha256"] = sha256(using_target)
    write_json(plugin_root / "candidate-profile.json", packaged_profile)
    return plugin_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    plugin_root = build(args.out.resolve(), args.force)
    print(f"built {CANDIDATE_VERSION} Codex candidate at {plugin_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
