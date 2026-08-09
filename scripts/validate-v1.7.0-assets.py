#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

STABLE_VERSION = "1.7.0"
BETA_VERSION = "1.7.0-roi-beta"
STABLE_SHA = "71c8e8a2a2edb4b9c2ea7df24fb083a9e0a317d6"
STABLE_TREE = "fef11824fad710c6873d5f464c032cccc11e6cdd"
PRIOR_BETA_SHA = "76cb34ebf3e91eb16e0285776aa9207cb242bd61"
ROI_IMPL = "493f9520b75f582aa22f6c8647ec08eab3e122d3"
ROI_QUAL = "4ee3e034db6bf8d1e34002d7f162e2b008516490"


def run(*args: str, cwd: Path, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, text=True, capture_output=capture, check=False
    )


def checked(*args: str, cwd: Path) -> str:
    result = run(*args, cwd=cwd)
    if result.returncode != 0:
        raise SystemExit(result.stderr + result.stdout)
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def assert_clean(repo: Path) -> None:
    status = checked("git", "status", "--porcelain=v1", "--untracked-files=all", cwd=repo)
    assert_true(status == "", f"Beta source checkout is dirty:\n{status}")


def is_ancestor(repo: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    return run("git", "merge-base", "--is-ancestor", ancestor, descendant, cwd=repo).returncode == 0


def normalized(data: bytes) -> bytes:
    return data.replace(b"mindthus-beta:", b"mindthus:")


def reproducible_tar(source: Path, archive_path: Path, root_name: str) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with archive_path.open("wb") as raw, gzip.GzipFile(
        filename="", mode="wb", fileobj=raw, mtime=0
    ) as compressed, tarfile.open(fileobj=compressed, mode="w") as archive:
        for path in sorted(source.rglob("*"), key=lambda p: p.relative_to(source).as_posix()):
            relative = path.relative_to(source)
            info = archive.gettarinfo(str(path), arcname=f"{root_name}/{relative.as_posix()}")
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mtime = 0
            if info.isfile():
                info.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                with path.open("rb") as src:
                    archive.addfile(info, src)
            else:
                info.mode = 0o755
                archive.addfile(info)


def build_stable(repo: Path, root: Path) -> tuple[Path, Path]:
    plugin_out = root / "stable-plugins"
    skills_out = root / "stable-skills"
    for package, out in (("plugins", plugin_out), ("skills", skills_out)):
        result = run(
            sys.executable,
            str(repo / "scripts" / "build-release-pack.py"),
            "--package",
            package,
            "--out",
            str(out),
            cwd=repo,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr + result.stdout)
    return plugin_out, skills_out


def build_beta(repo: Path, root: Path, label: str) -> tuple[Path, Path]:
    out = root / f"beta-{label}"
    assets = root / f"beta-assets-{label}"
    archive = assets / f"mindthus-beta-{BETA_VERSION}.tar.gz"
    result = run(
        sys.executable,
        str(repo / "beta" / "2.0-beta" / "build-internal-beta.py"),
        "--out",
        str(out),
        "--archive",
        str(archive),
        cwd=repo,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    return out, archive


def validate_profile(repo: Path) -> tuple[dict, dict, str]:
    profile = json.loads((repo / "beta" / "2.0-beta" / "profile.json").read_text(encoding="utf-8"))
    register = json.loads((repo / "beta" / "2.0-beta" / "capability-register.json").read_text(encoding="utf-8"))
    head = checked("git", "rev-parse", "HEAD", cwd=repo)
    tree = checked("git", "rev-parse", f"{STABLE_SHA}^{{tree}}", cwd=repo)

    assert_true(profile["version"] == BETA_VERSION, "wrong Beta version")
    assert_true(profile["shared_core"]["version"] == STABLE_VERSION, "wrong Stable version in Beta profile")
    assert_true(profile["shared_core"]["ref"] == STABLE_SHA, "Beta does not pin exact Stable commit")
    assert_true(profile["shared_core"]["tree_oid"] == STABLE_TREE == tree, "Beta does not pin exact Stable tree")
    assert_true(profile["runtime_profile"]["implementation_ref"] == ROI_IMPL, "ROI.2 implementation ref moved")
    assert_true(profile["runtime_profile"]["qualification_ref"] == ROI_QUAL, "ROI.2 qualification ref moved")
    assert_true(profile["publication"]["source_tag"] == f"v{BETA_VERSION}", "wrong Beta source tag")
    assert_true(profile["publication"]["release_train"] == STABLE_VERSION, "wrong Beta release train")
    assert_true(profile["publication"]["marketplace"] is False, "Beta must not auto-publish marketplace")
    assert_true(profile["publication"]["automatic_migration"] is False, "Beta must not auto-migrate")
    assert_true(register["shared_core_ref"] == STABLE_SHA, "capability register Stable ref mismatch")
    assert_true(is_ancestor(repo, STABLE_SHA), "Stable commit is not an ancestor of Beta")
    assert_true(is_ancestor(repo, PRIOR_BETA_SHA), "previous qualified Beta lineage is not an ancestor")
    assert_true(is_ancestor(repo, ROI_QUAL), "ROI.2 qualification ref is not an ancestor")

    by_id = {item["id"]: item for item in register["capabilities"]}
    assert_true("wae-ownership-closure-v1" in by_id, "WAE Ownership Closure missing from Beta capability register")
    wae = by_id["wae-ownership-closure-v1"]
    assert_true(wae["ownership"] == "shared-product-core", "WAE Closure incorrectly owned by ROI overlay")
    assert_true(wae["release_1x"]["version"] == STABLE_VERSION, "WAE Stable version mismatch")
    assert_true(wae["release_roi_beta"]["version"] == BETA_VERSION, "WAE Beta version mismatch")
    for item in register["capabilities"]:
        assert_true(item["release_roi_beta"]["version"] == BETA_VERSION, f"Beta version mismatch: {item['id']}")
    return profile, register, head


def validate_composition(repo: Path, stable_out: Path, beta_out: Path, profile: dict, head: str) -> None:
    stable = stable_out / "codex-plugin" / "mindthus"
    beta = beta_out / "mindthus-beta"
    assert_true(stable.is_dir(), "Stable Codex plugin missing")
    assert_true(beta.is_dir(), "Beta Codex plugin missing")

    for owner in ("edsp", "sela", "mpg", "wae", "tvg", "tplan", "case-prep"):
        stable_tree = stable / "skills" / owner
        beta_tree = beta / "skills" / owner
        stable_files = sorted(p.relative_to(stable_tree) for p in stable_tree.rglob("*") if p.is_file())
        beta_files = sorted(p.relative_to(beta_tree) for p in beta_tree.rglob("*") if p.is_file())
        assert_true(stable_files == beta_files, f"shared owner file-set drift: {owner}")
        for relative in stable_files:
            assert_true(
                normalized((beta_tree / relative).read_bytes()) == (stable_tree / relative).read_bytes(),
                f"shared owner drift: {owner}/{relative}",
            )

    assert_true((beta / "skills" / "wae" / "resources" / "ownership-closure.md").is_file(), "Beta lost WAE Ownership Closure resource")

    stable_files = {p.relative_to(stable) for p in stable.rglob("*") if p.is_file()}
    beta_files = {p.relative_to(beta) for p in beta.rglob("*") if p.is_file()}
    assert_true(beta_files - stable_files == {Path("beta-profile.json"), Path("capability-register.json")}, "unexpected Beta-only files")
    assert_true(stable_files - beta_files == set(), "Beta dropped Stable files")
    actual_deltas = {rel for rel in stable_files if (stable / rel).read_bytes() != (beta / rel).read_bytes()}
    special = {
        Path(".codex-plugin/plugin.json"),
        Path("skills/using-mindthus/SKILL.md"),
        Path("skills/3l5s/SKILL.md"),
        Path("scripts/log-mindthus-runtime.py"),
    }
    assert_true(special.issubset(actual_deltas), "declared Beta runtime delta is incomplete")
    for relative in actual_deltas - special:
        stable_bytes = (stable / relative).read_bytes()
        beta_bytes = (beta / relative).read_bytes()
        assert_true(b"mindthus:" in stable_bytes, f"undeclared semantic delta: {relative}")
        assert_true(normalized(beta_bytes) == stable_bytes, f"non-namespace Beta drift: {relative}")

    historical = json.loads((repo / "beta" / "2.0-roi-thin-core" / "profile.json").read_text(encoding="utf-8"))
    correction = historical["package_time_contract_correction"]
    stable_text = (stable / correction["path"]).read_text(encoding="utf-8")
    beta_text = (beta / correction["path"]).read_text(encoding="utf-8")
    assert_true(stable_text.count(correction["before"]) == 1, "3L5S qualified correction no longer applies once")
    assert_true(beta_text == stable_text.replace(correction["before"], correction["after"]), "3L5S Beta correction drifted")

    manifest = json.loads((beta / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert_true(manifest["name"] == "mindthus-beta", "Beta plugin identity wrong")
    assert_true(manifest["version"] == BETA_VERSION, "Beta manifest version wrong")
    prompt = "\n".join(manifest["interface"]["defaultPrompt"])
    assert_true("mindthus-beta:using-mindthus" in prompt, "Beta default prompt namespace wrong")
    assert_true("mindthus:using-mindthus" not in prompt, "Stable namespace leaked into Beta prompt")
    assert_true(len(prompt.encode("utf-8")) <= 128, "Beta default prompt exceeds loader budget")
    for path in beta.rglob("*"):
        if path.is_file():
            assert_true(b"mindthus:" not in path.read_bytes(), f"Stable namespace leaked into Beta: {path}")

    packaged = json.loads((beta / "beta-profile.json").read_text(encoding="utf-8"))
    register_path = beta / "capability-register.json"
    assert_true(packaged["shared_core"] == profile["shared_core"], "packaged Beta profile Stable core mismatch")
    assert_true(packaged["assembly_source_ref"] == head, "Beta artifact was not assembled from exact branch head")
    assert_true(packaged["capability_register_sha256"] == sha256(register_path), "packaged capability digest mismatch")
    assert_true(len(packaged["assembly_inputs_sha256"]) == 5, "unexpected Beta assembly input count")

    with tempfile.TemporaryDirectory(prefix="mindthus-beta-diagnostic-") as tmp:
        codex_home = Path(tmp) / "home"
        cache = codex_home / "plugins" / "cache" / "mindthus-beta" / "mindthus-beta" / BETA_VERSION
        shutil.copytree(beta, cache)
        codex_home.mkdir(exist_ok=True)
        (codex_home / "config.toml").write_text(
            "[marketplaces.mindthus-beta]\nsource_type = \"local\"\n" + f"source = {json.dumps(str(beta_out))}\n",
            encoding="utf-8",
        )
        result = run(
            sys.executable,
            str(cache / "scripts" / "log-mindthus-runtime.py"),
            "--codex-home",
            str(codex_home),
            "--json",
            "--strict",
            cwd=repo,
        )
        assert_true(result.returncode == 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        assert_true(report["version"] == BETA_VERSION, "Beta diagnostic version mismatch")
        assert_true(report["summary"]["status"] == "ok", "Beta diagnostic strict check failed")


def make_assets(repo: Path, out_dir: Path) -> dict:
    assert_clean(repo)
    profile, register, head = validate_profile(repo)
    with tempfile.TemporaryDirectory(prefix="mindthus-v170-assets-") as tmp:
        work = Path(tmp)
        stable_plugins, stable_skills = build_stable(repo, work)
        beta_first, beta_archive_first = build_beta(repo, work, "first")
        beta_second, beta_archive_second = build_beta(repo, work, "second")
        validate_composition(repo, stable_plugins, beta_first, profile, head)
        assert_true(beta_archive_first.read_bytes() == beta_archive_second.read_bytes(), "Beta archive is not byte reproducible")

        out_dir.mkdir(parents=True, exist_ok=True)
        plugins_archive = out_dir / f"mindthus-plugins-{STABLE_VERSION}.tar.gz"
        skills_archive = out_dir / f"mindthus-skills-{STABLE_VERSION}.tar.gz"
        beta_archive = out_dir / f"mindthus-beta-{BETA_VERSION}.tar.gz"
        reproducible_tar(stable_plugins, plugins_archive, f"mindthus-plugins-{STABLE_VERSION}")
        reproducible_tar(stable_skills, skills_archive, f"mindthus-skills-{STABLE_VERSION}")
        shutil.copy2(beta_archive_first, beta_archive)

    assets = [plugins_archive, skills_archive, beta_archive]
    checksums = "".join(f"{sha256(path)}  {path.name}\n" for path in assets)
    (out_dir / "SHA256SUMS").write_text(checksums, encoding="utf-8")
    report = {
        "status": "valid",
        "stable_version": STABLE_VERSION,
        "stable_sha": STABLE_SHA,
        "stable_tree": STABLE_TREE,
        "beta_version": BETA_VERSION,
        "beta_sha": head,
        "prior_beta_lineage": PRIOR_BETA_SHA,
        "roi_implementation_ref": ROI_IMPL,
        "roi_qualification_ref": ROI_QUAL,
        "capability_count": len(register["capabilities"]),
        "wae_ownership_closure": "shared-product-core",
        "assets": [
            {"name": path.name, "sha256": sha256(path), "size": path.stat().st_size}
            for path in assets
        ],
    }
    (out_dir / "release-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = make_assets(args.repo.resolve(), args.out.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
