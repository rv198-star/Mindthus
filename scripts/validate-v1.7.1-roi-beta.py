#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STABLE_VERSION = "1.7.1"
BETA_VERSION = "1.7.1-roi-beta"
STABLE_SHA = "dca73c1ff1710eca3d5b56216c374ce6c2240117"
STABLE_TREE = "13e034c687041b5aa90e5baebc8f1158b7c5dcba"
BETA_SHA = "0a73dbdfbeec7b1b9dfb78ad63ca1eb3f3ad6f4b"
PRIOR_BETA_SHA = "a55c8bde3d10f0eb1825b9897e45a7fe92f03044"
ROI_IMPL = "493f9520b75f582aa22f6c8647ec08eab3e122d3"
ROI_QUAL = "4ee3e034db6bf8d1e34002d7f162e2b008516490"
EXPECTED_STABLE_PLUGINS = "2cfbaad7909706f27a85a7a5e662952a2860e995ea902149a644b44d54598cdc"
EXPECTED_STABLE_SKILLS = "9f0fe49c08c341e4cfc31ce0c573e05004d80fb5e7184af54bf79c07e137b98d"


def run(*args: str, cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(args), cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    return result


def git(root: Path, *args: str) -> str:
    return run("git", *args, cwd=root, check=True).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def normalize(value: bytes) -> bytes:
    return value.replace(b"mindthus-beta:", b"mindthus:")


def assert_clean(root: Path) -> None:
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    assert_true(status == "", f"dirty source checkout:\n{status}")


def assert_ancestor(root: Path, ancestor: str, descendant: str = "HEAD") -> None:
    result = run("git", "merge-base", "--is-ancestor", ancestor, descendant, cwd=root)
    assert_true(result.returncode == 0, f"missing ancestry: {ancestor} -> {descendant}")


def build_stable(stable_src: Path, out: Path) -> Path:
    result = run(
        sys.executable,
        str(stable_src / "scripts" / "build-release-pack.py"),
        "--package",
        "plugins",
        "--out",
        str(out),
        cwd=stable_src,
    )
    assert_true(result.returncode == 0, result.stderr + result.stdout)
    return out / "codex-plugin" / "mindthus"


def build_beta(beta_src: Path, out: Path, archive: Path) -> Path:
    result = run(
        sys.executable,
        str(beta_src / "beta" / "2.0-beta" / "build-internal-beta.py"),
        "--out",
        str(out),
        "--archive",
        str(archive),
        cwd=beta_src,
    )
    assert_true(result.returncode == 0, result.stderr + result.stdout)
    return out / "mindthus-beta"


def validate_profile(beta_src: Path) -> tuple[dict, dict]:
    profile = json.loads((beta_src / "beta" / "2.0-beta" / "profile.json").read_text(encoding="utf-8"))
    register = json.loads((beta_src / "beta" / "2.0-beta" / "capability-register.json").read_text(encoding="utf-8"))
    assert_true(git(beta_src, "rev-parse", "HEAD") == BETA_SHA, "unexpected Beta source head")
    assert_true(profile["version"] == BETA_VERSION, "wrong Beta version")
    assert_true(profile["shared_core"] == {
        "version": STABLE_VERSION,
        "ref": STABLE_SHA,
        "tree_oid": STABLE_TREE,
    }, "wrong Stable shared-core pin")
    runtime = profile["runtime_profile"]
    assert_true(runtime["implementation_ref"] == ROI_IMPL, "ROI implementation ref drift")
    assert_true(runtime["qualification_ref"] == ROI_QUAL, "ROI qualification ref drift")
    assert_true(profile["rollback"]["tag"] == "v1.7.1", "wrong rollback tag")
    assert_true(profile["publication"]["source_tag"] == "v1.7.1-roi-beta", "wrong source tag")
    assert_true(profile["publication"]["release_train"] == STABLE_VERSION, "wrong release train")
    assert_true(profile["publication"]["marketplace"] is False, "Beta marketplace must stay disabled")
    assert_true(profile["publication"]["automatic_migration"] is False, "Beta auto-migration must stay disabled")
    assert_true(register["shared_core_ref"] == STABLE_SHA, "register shared-core ref mismatch")

    by_id = {item["id"]: item for item in register["capabilities"]}
    assert_true("competitive-frame-convergence-v1" in by_id, "v1.7.1 bugfix capability missing")
    assert_true(by_id["competitive-frame-convergence-v1"]["ownership"] == "shared-product-core", "C-lite fix must be shared-core owned")
    assert_true(by_id["wae-ownership-closure-v1"]["ownership"] == "shared-product-core", "WAE Closure ownership drift")
    for item in register["capabilities"]:
        assert_true(item["release_1x"]["version"] == STABLE_VERSION, f"Stable version mismatch: {item['id']}")
        assert_true(item["release_roi_beta"]["version"] == BETA_VERSION, f"Beta version mismatch: {item['id']}")

    assert_ancestor(beta_src, STABLE_SHA)
    assert_ancestor(beta_src, PRIOR_BETA_SHA)
    assert_ancestor(beta_src, ROI_QUAL)
    assert_ancestor(beta_src, ROI_IMPL, ROI_QUAL)
    assert_true(git(beta_src, "rev-parse", f"{STABLE_SHA}^{{tree}}") == STABLE_TREE, "Stable tree pin mismatch")
    return profile, register


def validate_composition(stable: Path, beta: Path, beta_src: Path, profile: dict) -> None:
    shared_owners = ("edsp", "sela", "mpg", "wae", "tvg", "tplan", "case-prep")
    for owner in shared_owners:
        stable_tree = stable / "skills" / owner
        beta_tree = beta / "skills" / owner
        stable_files = sorted(p.relative_to(stable_tree) for p in stable_tree.rglob("*") if p.is_file())
        beta_files = sorted(p.relative_to(beta_tree) for p in beta_tree.rglob("*") if p.is_file())
        assert_true(stable_files == beta_files, f"shared owner file-set drift: {owner}")
        for rel in stable_files:
            assert_true(normalize((beta_tree / rel).read_bytes()) == (stable_tree / rel).read_bytes(), f"shared owner drift: {owner}/{rel}")

    pressure_rel = Path("skills/using-mindthus/resources/primitives/expression-pressure-and-gates.md")
    stable_pressure = stable / pressure_rel
    beta_pressure = beta / pressure_rel
    assert_true(normalize(beta_pressure.read_bytes()) == stable_pressure.read_bytes(), "pressure resource drifted from Stable")
    pressure_text = beta_pressure.read_text(encoding="utf-8")
    for marker in (
        "Competitive-frame convergence / 竞争框架收敛",
        "Competitive steelman / 竞争框架钢人",
        "Decisive discriminator / 决定性判别变量",
        "Visible Translation Boundary / 可见表达翻译边界",
        "5K 多花的钱，值不值得换更锐的文字？",
    ):
        assert_true(marker in pressure_text, f"missing v1.7.1 pressure marker: {marker}")

    stable_files = {p.relative_to(stable) for p in stable.rglob("*") if p.is_file()}
    beta_files = {p.relative_to(beta) for p in beta.rglob("*") if p.is_file()}
    assert_true(beta_files - stable_files == {Path("beta-profile.json"), Path("capability-register.json")}, "unexpected Beta-only files")
    assert_true(stable_files - beta_files == set(), "Beta dropped Stable files")
    actual_deltas = {rel for rel in stable_files if (stable / rel).read_bytes() != (beta / rel).read_bytes()}
    declared_special = {
        Path(".codex-plugin/plugin.json"),
        Path("skills/using-mindthus/SKILL.md"),
        Path("skills/3l5s/SKILL.md"),
        Path("scripts/log-mindthus-runtime.py"),
    }
    assert_true(declared_special.issubset(actual_deltas), "declared Beta runtime delta incomplete")
    for rel in actual_deltas - declared_special:
        stable_bytes = (stable / rel).read_bytes()
        beta_bytes = (beta / rel).read_bytes()
        assert_true(b"mindthus:" in stable_bytes, f"undeclared semantic delta: {rel}")
        assert_true(normalize(beta_bytes) == stable_bytes, f"non-namespace Beta drift: {rel}")

    manifest = json.loads((beta / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert_true(manifest["name"] == "mindthus-beta", "wrong Beta plugin identity")
    assert_true(manifest["version"] == BETA_VERSION, "wrong Beta manifest version")
    prompt = "\n".join(manifest["interface"]["defaultPrompt"])
    assert_true("mindthus-beta:using-mindthus" in prompt, "Beta default prompt namespace wrong")
    assert_true("mindthus:using-mindthus" not in prompt, "Stable namespace leaked into Beta prompt")
    assert_true(len(prompt.encode("utf-8")) <= 128, "Beta default prompt exceeds loader budget")

    for path in beta.rglob("*"):
        if path.is_file():
            assert_true(b"mindthus:" not in path.read_bytes(), f"Stable namespace leaked into Beta: {path}")

    packaged_profile = json.loads((beta / "beta-profile.json").read_text(encoding="utf-8"))
    assert_true(packaged_profile["shared_core"] == profile["shared_core"], "packaged shared core mismatch")
    assert_true(packaged_profile["assembly_source_ref"] == BETA_SHA, "artifact not assembled from exact Beta source")
    packaged_register = json.loads((beta / "capability-register.json").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in packaged_register["capabilities"]}
    assert_true(by_id["competitive-frame-convergence-v1"]["ownership"] == "shared-product-core", "packaged C-lite ownership drift")

    with tempfile.TemporaryDirectory(prefix="mindthus-v171-beta-diagnostic-") as tmp:
        codex_home = Path(tmp) / "home"
        cache = codex_home / "plugins" / "cache" / "mindthus-beta" / "mindthus-beta" / BETA_VERSION
        shutil.copytree(beta, cache)
        codex_home.mkdir(exist_ok=True)
        marketplace_root = beta.parent
        (codex_home / "config.toml").write_text(
            "[marketplaces.mindthus-beta]\nsource_type = \"local\"\n" + f"source = {json.dumps(str(marketplace_root))}\n",
            encoding="utf-8",
        )
        result = run(
            sys.executable,
            str(cache / "scripts" / "log-mindthus-runtime.py"),
            "--codex-home",
            str(codex_home),
            "--json",
            "--strict",
            cwd=beta_src,
        )
        assert_true(result.returncode == 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        assert_true(payload["version"] == BETA_VERSION, "Beta diagnostic version mismatch")
        assert_true(payload["summary"]["status"] == "ok", "Beta diagnostic strict check failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--beta-src", required=True, type=Path)
    parser.add_argument("--stable-src", required=True, type=Path)
    parser.add_argument("--dist", required=True, type=Path)
    args = parser.parse_args()
    beta_src = args.beta_src.resolve()
    stable_src = args.stable_src.resolve()
    dist = args.dist.resolve()
    dist.mkdir(parents=True, exist_ok=True)

    assert_clean(beta_src)
    assert_clean(stable_src)
    assert_true(git(stable_src, "rev-parse", "HEAD") == STABLE_SHA, "unexpected Stable source head")
    profile, register = validate_profile(beta_src)

    with tempfile.TemporaryDirectory(prefix="mindthus-v171-roi-beta-") as tmp:
        work = Path(tmp)
        stable = build_stable(stable_src, work / "stable-plugins")
        beta_first_archive = dist / f"mindthus-beta-{BETA_VERSION}.tar.gz"
        beta_first = build_beta(beta_src, work / "beta-first", beta_first_archive)
        second_dist = work / "second-dist"
        second_dist.mkdir()
        beta_second_archive = second_dist / f"mindthus-beta-{BETA_VERSION}.tar.gz"
        beta_second = build_beta(beta_src, work / "beta-second", beta_second_archive)
        assert_true(beta_first_archive.read_bytes() == beta_second_archive.read_bytes(), "Beta archive is not byte reproducible")
        validate_composition(stable, beta_first, beta_src, profile)
        validate_composition(stable, beta_second, beta_src, profile)

    beta_digest = sha256(dist / f"mindthus-beta-{BETA_VERSION}.tar.gz")
    report = {
        "schema_version": "mindthus-v1.7.1-roi-beta-validation-v0.1",
        "status": "valid",
        "stable_version": STABLE_VERSION,
        "stable_sha": STABLE_SHA,
        "stable_tree": STABLE_TREE,
        "beta_version": BETA_VERSION,
        "beta_sha": BETA_SHA,
        "prior_beta_sha": PRIOR_BETA_SHA,
        "roi_implementation_ref": ROI_IMPL,
        "roi_qualification_ref": ROI_QUAL,
        "capability_count": len(register["capabilities"]),
        "competitive_frame_convergence": "shared-product-core",
        "beta_archive_sha256": beta_digest,
        "beta_archive_size": (dist / f"mindthus-beta-{BETA_VERSION}.tar.gz").stat().st_size,
        "expected_stable_plugins_sha256": EXPECTED_STABLE_PLUGINS,
        "expected_stable_skills_sha256": EXPECTED_STABLE_SKILLS,
    }
    (dist / "roi-beta-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
