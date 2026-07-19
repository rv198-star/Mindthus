#!/usr/bin/env python3
"""Compose the internal Mindthus 2.0 Beta from a frozen shared core and ROI.2."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = PROFILE_DIR / "profile.json"
REGISTER_PATH = PROFILE_DIR / "capability-register.json"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git_output(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def git_bytes(root: Path, ref: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=root, check=True, capture_output=True
    )
    return result.stdout


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def ensure_safe_output(path: Path, root: Path, force: bool) -> None:
    if path == root or root in path.parents or path in root.parents:
        raise SystemExit("internal Beta output must be outside the repository tree")
    if path.exists():
        if not path.is_dir():
            raise SystemExit(f"output exists and is not a directory: {path}")
        if any(path.iterdir()):
            if not force:
                raise SystemExit(f"output is not empty: {path}; pass --force to replace it")
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def require_commit(root: Path, ref: str) -> None:
    subprocess.run(
        ["git", "cat-file", "-e", f"{ref}^{{commit}}"],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def require_ancestor(root: Path, ancestor: str, descendant: str = "HEAD") -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant], cwd=root
    )
    if result.returncode != 0:
        raise SystemExit(f"required ancestry is absent: {ancestor} -> {descendant}")


def materialize_git_tree(root: Path, ref: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination.parent / "shared-core.tar"
    with archive_path.open("wb") as archive_file:
        subprocess.run(
            ["git", "archive", "--format=tar", ref],
            cwd=root,
            check=True,
            stdout=archive_file,
        )
    with tarfile.open(archive_path, "r") as archive:
        members = archive.getmembers()
        for member in members:
            parts = Path(member.name).parts
            if member.name.startswith("/") or ".." in parts:
                raise SystemExit(f"unsafe shared-core archive member: {member.name}")
            if member.issym() or member.islnk():
                raise SystemExit(f"shared-core archive contains a symlink: {member.name}")
        extract_kwargs = {}
        if "filter" in inspect.signature(archive.extractall).parameters:
            extract_kwargs["filter"] = "data"
        archive.extractall(destination, members=members, **extract_kwargs)


def rewrite_beta_identity(marketplace_root: Path, version: str) -> Path:
    stable_plugin_root = marketplace_root / "mindthus"
    plugin_root = marketplace_root / "mindthus-beta"
    stable_plugin_root.rename(plugin_root)

    marketplace_path = marketplace_root / ".agents" / "plugins" / "marketplace.json"
    marketplace = read_json(marketplace_path)
    marketplace["name"] = "mindthus-beta"
    marketplace["interface"]["displayName"] = "Mindthus 2.0 Beta"
    marketplace["plugins"][0]["name"] = "mindthus-beta"
    marketplace["plugins"][0]["source"]["path"] = "./mindthus-beta"
    write_json(marketplace_path, marketplace)

    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest = read_json(manifest_path)
    manifest["name"] = "mindthus-beta"
    manifest["version"] = version
    manifest["description"] = "Internal ROI.2-based Mindthus 2.0 Beta for Codex."
    interface = manifest["interface"]
    interface["displayName"] = "Mindthus 2.0 Beta"
    interface["shortDescription"] = "ROI.2 thin entry over the 1.5 shared core"
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not all(isinstance(item, str) for item in prompts):
        raise SystemExit("Codex defaultPrompt is not a string list")
    replacement_count = sum(item.count("mindthus:") for item in prompts)
    if replacement_count == 0:
        raise SystemExit("Codex defaultPrompt has no Stable namespace to rewrite")
    interface["defaultPrompt"] = [
        item.replace("mindthus:", "mindthus-beta:") for item in prompts
    ]
    write_json(manifest_path, manifest)
    return plugin_root


def build(output: Path, force: bool) -> Path:
    root = repo_root()
    profile = read_json(PROFILE_PATH)
    shared_ref = profile["shared_core"]["ref"]
    runtime = profile["runtime_profile"]
    implementation_ref = runtime["implementation_ref"]
    qualification_ref = runtime["qualification_ref"]
    convergence_ref = runtime["convergence_evidence_ref"]

    for ref in (shared_ref, implementation_ref, qualification_ref, convergence_ref):
        require_commit(root, ref)
    require_ancestor(root, shared_ref)
    require_ancestor(root, qualification_ref)
    require_ancestor(root, implementation_ref, qualification_ref)
    require_ancestor(root, qualification_ref, convergence_ref)
    actual_tree = git_output(root, "rev-parse", f"{shared_ref}^{{tree}}")
    if actual_tree != profile["shared_core"]["tree_oid"]:
        raise SystemExit("shared-core tree identity does not match profile")
    frozen_diff = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            qualification_ref,
            "--",
            "beta/2.0-roi-thin-core",
        ],
        cwd=root,
    )
    if frozen_diff.returncode != 0:
        raise SystemExit("historical ROI.2 qualification tree was modified")

    historical_profile_bytes = git_bytes(
        root, qualification_ref, runtime["historical_profile_path"]
    )
    historical_profile = json.loads(historical_profile_bytes.decode("utf-8"))
    if historical_profile.get("candidate") != "2.0.0-roi.2":
        raise SystemExit("runtime profile is not the qualified ROI.2 candidate")
    overlay_bytes = git_bytes(root, implementation_ref, runtime["overlay_path"])

    ensure_safe_output(output, root, force)
    with tempfile.TemporaryDirectory(prefix="mindthus-internal-beta-") as temporary:
        temp_root = Path(temporary)
        shared_source = temp_root / "shared-core"
        stable_out = temp_root / "stable-pack"
        materialize_git_tree(root, shared_ref, shared_source)
        subprocess.run(
            [
                sys.executable,
                str(shared_source / "scripts" / "build-release-pack.py"),
                "--package",
                "plugins",
                "--out",
                str(stable_out),
            ],
            cwd=shared_source,
            check=True,
        )
        shutil.copytree(stable_out / "codex-plugin", output, dirs_exist_ok=True)

    plugin_root = rewrite_beta_identity(output, profile["version"])
    using_target = plugin_root / "skills" / "using-mindthus" / "SKILL.md"
    using_target.write_bytes(overlay_bytes)

    correction = historical_profile["package_time_contract_correction"]
    correction_target = plugin_root / correction["path"]
    correction_text = correction_target.read_text(encoding="utf-8")
    before = correction["before"]
    after = correction["after"]
    if correction_text.count(before) != 1 or after in correction_text:
        raise SystemExit("qualified 3L5S guardrail replacement no longer applies exactly once")
    correction_target.write_text(correction_text.replace(before, after), encoding="utf-8")

    packaged_profile = dict(profile)
    packaged_profile["assembly_source_ref"] = git_output(root, "rev-parse", "HEAD")
    packaged_profile["runtime_overlay_sha256"] = sha256_bytes(overlay_bytes)
    packaged_profile["historical_profile_sha256"] = sha256_bytes(
        historical_profile_bytes
    )
    write_json(plugin_root / "beta-profile.json", packaged_profile)
    shutil.copy2(REGISTER_PATH, plugin_root / "capability-register.json")
    return plugin_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    plugin_root = build(args.out.resolve(), args.force)
    print(f"built internal Mindthus 2.0 Beta at {plugin_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
