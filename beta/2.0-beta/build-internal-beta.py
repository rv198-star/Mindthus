#!/usr/bin/env python3
"""Compose the internal Mindthus 2.0 Beta from a frozen shared core and ROI.2."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = PROFILE_DIR / "profile.json"
REGISTER_PATH = PROFILE_DIR / "capability-register.json"
PROFILE_REPO_PATH = "beta/2.0-beta/profile.json"
REGISTER_REPO_PATH = "beta/2.0-beta/capability-register.json"
BUILDER_REPO_PATH = "beta/2.0-beta/build-internal-beta.py"
BETA_DIAGNOSTIC_MARKERS = (
    "using-mindthus — Thin Core",
    "Pursue facts over agreement",
    "Frame and whole:",
    "Decision context:",
    "Evidence ceiling:",
    "Anti-Spiral:",
    "no method catalog",
    "Anti-Spiral hard brake",
    "same local repair count >= 3",
)


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


def require_clean_checkout(root: Path) -> None:
    status = git_output(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise SystemExit(
            "Beta assembly requires a clean checkout; commit or remove all tracked and "
            "untracked inputs before building"
        )


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


def ensure_safe_archive(path: Path, root: Path, output: Path, force: bool) -> None:
    if path == root or root in path.parents or path in root.parents:
        raise SystemExit("Beta archive must be outside the repository tree")
    if path == output or output in path.parents or path in output.parents:
        raise SystemExit("Beta archive must be outside the assembly output tree")
    if path.exists():
        if not path.is_file():
            raise SystemExit(f"Beta archive path exists and is not a file: {path}")
        if not force:
            raise SystemExit(f"Beta archive already exists: {path}; pass --force to replace it")


def ensure_safe_checksum(path: Path, root: Path, output: Path, force: bool) -> None:
    ensure_safe_archive(path, root, output, force)


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
    manifest["description"] = "ROI.2-based Mindthus 2.0 Beta prerelease for Codex."
    interface = manifest["interface"]
    interface["displayName"] = "Mindthus 2.0 Beta"
    interface["shortDescription"] = "ROI.2 thin entry over the 1.5 shared core"
    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not all(isinstance(item, str) for item in prompts):
        raise SystemExit("Codex defaultPrompt is not a string list")
    replacement_count = sum(item.count("mindthus:") for item in prompts)
    if replacement_count == 0:
        raise SystemExit("Codex defaultPrompt has no Stable namespace to rewrite")
    rewritten_prompts = [
        item.replace("mindthus:", "mindthus-beta:") for item in prompts
    ]
    for item in rewritten_prompts:
        if len(item.encode("utf-8")) > 128:
            raise SystemExit("Beta Codex defaultPrompt exceeds the proven 128-byte loader limit")
    interface["defaultPrompt"] = rewritten_prompts
    write_json(manifest_path, manifest)
    return plugin_root


def rewrite_namespace(plugin_root: Path) -> dict[str, int]:
    rewrites: dict[str, int] = {}
    for path in sorted(candidate for candidate in plugin_root.rglob("*") if candidate.is_file()):
        raw = path.read_bytes()
        count = raw.count(b"mindthus:")
        if count == 0:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SystemExit(f"Stable namespace appears in non-UTF-8 artifact: {path}") from error
        path.write_text(text.replace("mindthus:", "mindthus-beta:"), encoding="utf-8")
        rewrites[path.relative_to(plugin_root).as_posix()] = count
    return rewrites


def rewrite_runtime_diagnostics(plugin_root: Path, stable_version: str, beta_version: str) -> None:
    path = plugin_root / "scripts" / "log-mindthus-runtime.py"
    text = path.read_text(encoding="utf-8")
    replacements = {
        f'VERSION = "{stable_version}"': f'VERSION = "{beta_version}"',
        'PACKAGE_IDENTITY = "mindthus"': 'PACKAGE_IDENTITY = "mindthus-beta"',
        'MARKETPLACE_IDENTITY = "mindthus"': 'MARKETPLACE_IDENTITY = "mindthus-beta"',
        'f"mindthus-v{VERSION}" / "codex-plugin" / "mindthus"': (
            'f"mindthus-beta-v{VERSION}" / "mindthus-beta"'
        ),
    }
    for before, after in replacements.items():
        if text.count(before) != 1:
            raise SystemExit(f"Beta runtime diagnostic rewrite no longer applies once: {before}")
        text = text.replace(before, after)
    marker_start = text.index("REQUIRED_MARKERS = (")
    marker_end = text.index("\n)\n\n\ndef default_codex_home", marker_start) + 2
    marker_literal = "REQUIRED_MARKERS = (\n" + "".join(
        f"    {marker!r},\n" for marker in BETA_DIAGNOSTIC_MARKERS
    ) + ")"
    text = text[:marker_start] + marker_literal + text[marker_end:]
    path.write_text(text, encoding="utf-8")


def write_reproducible_archive(source: Path, archive_path: Path, version: str) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    root_name = f"mindthus-beta-{version}"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{archive_path.name}.", suffix=".tmp", dir=archive_path.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with temporary_path.open("wb") as raw, gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, mtime=0
        ) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
            for path in sorted(
                source.rglob("*"), key=lambda item: item.relative_to(source).as_posix()
            ):
                relative = path.relative_to(source)
                info = archive.gettarinfo(
                    str(path), arcname=f"{root_name}/{relative.as_posix()}"
                )
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.mtime = 0
                if info.isfile():
                    info.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                    with path.open("rb") as source_file:
                        archive.addfile(info, source_file)
                else:
                    info.mode = 0o755
                    archive.addfile(info)
        temporary_path.replace(archive_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def write_checksum(archive_path: Path, checksum_path: Path) -> None:
    digest = sha256_bytes(archive_path.read_bytes())
    value = f"{digest}  {archive_path.name}\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{checksum_path.name}.", suffix=".tmp", dir=checksum_path.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        temporary_path.write_text(value, encoding="utf-8")
        temporary_path.replace(checksum_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def build(output: Path, force: bool) -> Path:
    root = repo_root()
    require_clean_checkout(root)
    source_ref = git_output(root, "rev-parse", "HEAD")
    profile_bytes = git_bytes(root, source_ref, PROFILE_REPO_PATH)
    register_bytes = git_bytes(root, source_ref, REGISTER_REPO_PATH)
    builder_bytes = git_bytes(root, source_ref, BUILDER_REPO_PATH)
    profile = json.loads(profile_bytes.decode("utf-8"))
    shared_ref = profile["shared_core"]["ref"]
    runtime = profile["runtime_profile"]
    implementation_ref = runtime["implementation_ref"]
    qualification_ref = runtime["qualification_ref"]

    for ref in (shared_ref, implementation_ref, qualification_ref):
        require_commit(root, ref)
    require_ancestor(root, shared_ref)
    require_ancestor(root, qualification_ref)
    require_ancestor(root, implementation_ref, qualification_ref)
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

    rewrite_runtime_diagnostics(
        plugin_root, profile["shared_core"]["version"], profile["version"]
    )
    namespace_rewrites = rewrite_namespace(plugin_root)
    if not namespace_rewrites:
        raise SystemExit("Beta artifact contained no Stable namespace references to isolate")

    packaged_profile = dict(profile)
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    register_target = plugin_root / profile["capability_register"]["artifact_path"]
    register_target.write_bytes(register_bytes)
    packaged_profile["assembly_source_ref"] = source_ref
    packaged_profile["assembly_inputs_sha256"] = {
        BUILDER_REPO_PATH: sha256_bytes(builder_bytes),
        PROFILE_REPO_PATH: sha256_bytes(profile_bytes),
        REGISTER_REPO_PATH: sha256_bytes(register_bytes),
        runtime["overlay_path"]: sha256_bytes(overlay_bytes),
        runtime["historical_profile_path"]: sha256_bytes(historical_profile_bytes),
    }
    packaged_profile["artifact_manifest_sha256"] = sha256_bytes(manifest_path.read_bytes())
    packaged_profile["capability_register_sha256"] = sha256_bytes(register_bytes)
    packaged_profile["namespace_rewrites"] = namespace_rewrites
    write_json(plugin_root / "beta-profile.json", packaged_profile)
    return plugin_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = repo_root()
    output = args.out.resolve()
    archive_path = args.archive.resolve() if args.archive else None
    checksum_path = archive_path.parent / "SHA256SUMS" if archive_path else None
    if archive_path is not None and checksum_path is not None:
        ensure_safe_archive(archive_path, root, output, args.force)
        ensure_safe_checksum(checksum_path, root, output, args.force)
    plugin_root = build(output, args.force)
    if args.archive:
        profile = read_json(plugin_root / "beta-profile.json")
        write_reproducible_archive(output, archive_path, profile["version"])
        write_checksum(archive_path, checksum_path)
        print(f"built reproducible Beta archive at {archive_path}")
        print(f"wrote Beta archive checksum at {checksum_path}")
    print(f"built Mindthus 2.0 Beta prerelease at {plugin_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
