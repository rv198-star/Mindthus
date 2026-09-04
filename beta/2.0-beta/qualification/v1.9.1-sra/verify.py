#!/usr/bin/env python3
"""Deterministic v1.9.1 ROI Beta SRA compatibility qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
PROFILE = REPO / "beta" / "2.0-beta" / "profile.json"
REGISTER = REPO / "beta" / "2.0-beta" / "capability-register.json"
OVERLAY = REPO / "beta" / "2.0-beta" / "overlays" / "using-mindthus-v1.9.0-sra" / "SKILL.md"
HISTORICAL = REPO / "beta" / "2.0-roi-thin-core" / "profile.json"
STABLE_REF = "d735d11c14d92325607fe6b844eb29f7c426df62"
STABLE_TREE = "9c301753689d5ceb5f9fa2019ca41b4425f583bd"
MAX_BYTES = 2300
ALLOWED_DELTAS = {
    "skills/using-mindthus/SKILL.md",
    "skills/3l5s/SKILL.md",
    ".codex-plugin/plugin.json",
    "scripts/log-mindthus-runtime.py",
}
EXTRA_BETA_FILES = {"beta-profile.json", "capability-register.json"}
REQUIRED_SRA_SURFACES = (
    "skills/sra/SKILL.md",
    "skills/sra/resources/methodology.md",
    "skills/sra/resources/context-isolation.md",
    "skills/sra/resources/fidelity-contract.md",
    "skills/sra/scripts/sra_domain.py",
    "skills/sra/scripts/sra_runtime_core.py",
    "skills/sra/scripts/sra_runtime_integrity.py",
    "skills/sra/scripts/repair_sra_run.py",
    "skills/sra/templates/full-context-input.json",
    "skills/sra/templates/full-challenge-judgment.json",
    "skills/sra/templates/full-situated-judgment.json",
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def files(root: Path) -> dict[str, Path]:
    return {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file()
    }


def normalized_beta_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if b"mindthus-beta:" not in raw:
        return raw
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail(f"Beta namespace appears in non-UTF-8 file: {path}")
    return text.replace("mindthus-beta:", "mindthus:").encode("utf-8")


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO, check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


def verify(stable: Path, candidate: Path, archive_a: Path | None, archive_b: Path | None) -> None:
    profile = read_json(PROFILE)
    register = read_json(REGISTER)
    historical = read_json(HISTORICAL)

    if profile["version"] != "1.9.1-roi-beta":
        fail("composition version is not 1.9.1-roi-beta")
    if profile["shared_core"] != {
        "version": "1.9.1",
        "ref": STABLE_REF,
        "tree_oid": STABLE_TREE,
    }:
        fail("shared-core identity is not the frozen v1.9.1 Stable source")
    if git_output("rev-parse", f"{STABLE_REF}^{{tree}}") != STABLE_TREE:
        fail("frozen Stable commit does not resolve to the declared tree")
    if not git_output("merge-base", "--is-ancestor", STABLE_REF, "HEAD") == "":
        fail("unexpected merge-base output")

    if OVERLAY.stat().st_size > MAX_BYTES:
        fail(f"Thin Core exceeds {MAX_BYTES} bytes: {OVERLAY.stat().st_size}")
    overlay = OVERLAY.read_text(encoding="utf-8")
    overlay_compact = " ".join(overlay.split())
    for marker in (
        "using-mindthus — Thin Core",
        "Pursue facts over agreement",
        "Multiple judgeable candidates sharing one scarce resource belong to SRA",
    ):
        if " ".join(marker.split()) not in overlay_compact:
            fail(f"Thin Core missing marker: {marker}")

    if register["shared_core_ref"] != STABLE_REF:
        fail("capability register shared_core_ref mismatch")
    for capability in register["capabilities"]:
        if capability["release_1x"]["version"] != "1.9.1":
            fail(f"Stable capability version mismatch: {capability['id']}")
        if capability["release_roi_beta"]["version"] != "1.9.1-roi-beta":
            fail(f"Beta capability version mismatch: {capability['id']}")

    manifest = read_json(candidate / ".codex-plugin" / "plugin.json")
    if manifest.get("name") != "mindthus-beta" or manifest.get("version") != "1.9.1-roi-beta":
        fail("Beta plugin identity/version mismatch")
    packaged_profile = read_json(candidate / "beta-profile.json")
    if packaged_profile.get("shared_core") != profile["shared_core"]:
        fail("packaged profile shared-core identity mismatch")
    if (candidate / "skills" / "using-mindthus" / "SKILL.md").read_bytes() != OVERLAY.read_bytes():
        fail("packaged Thin Core differs from the qualified overlay")
    correction = historical["package_time_contract_correction"]
    corrected_3l5s = (candidate / correction["path"]).read_text(encoding="utf-8")
    if correction["after"] not in corrected_3l5s or correction["before"] in corrected_3l5s:
        fail("qualified ROI.2 3L5S Anti-Spiral correction is not exact")

    for relative in REQUIRED_SRA_SURFACES:
        if not (candidate / relative).is_file():
            fail(f"packaged SRA v0.3 surface is missing: {relative}")
    domain = (candidate / "skills/sra/scripts/sra_domain.py").read_text(encoding="utf-8")
    integrity = (candidate / "skills/sra/scripts/sra_runtime_integrity.py").read_text(encoding="utf-8")
    if "validate_cumulative_allocations_against_demand" not in domain:
        fail("cumulative Demand validator is missing")
    if "cannot repair without a complete prepared-input anchor" not in integrity:
        fail("prepared-input anchor Repair blocker is missing")

    stable_files = files(stable)
    beta_files = files(candidate)
    for extra in EXTRA_BETA_FILES:
        if extra not in beta_files:
            fail(f"Beta metadata file missing: {extra}")
    missing = sorted(set(stable_files) - set(beta_files) - ALLOWED_DELTAS)
    if missing:
        fail(f"Beta dropped shared-core files: {missing[:5]}")
    for relative, stable_path in stable_files.items():
        if relative in ALLOWED_DELTAS:
            continue
        beta_path = beta_files.get(relative)
        if beta_path is not None and stable_path.read_bytes() != normalized_beta_bytes(beta_path):
            fail(f"non-delta shared-core file diverged: {relative}")

    namespace_leaks = [
        relative for relative, path in beta_files.items() if b"mindthus:" in path.read_bytes()
    ]
    if namespace_leaks:
        fail(f"Stable namespace leaked into Beta: {namespace_leaks[:5]}")

    stable_contract = (REPO / "tests/test_sra_v03_runtime_contract.py").read_text(encoding="utf-8")
    stable_lifecycle = (REPO / "tests/test_sra_v03_runtime_lifecycle.py").read_text(encoding="utf-8")
    if "test_lite_cumulative_candidate_commitment_cannot_exceed_demand" not in stable_contract:
        fail("cumulative Demand regression is absent from the inherited source")
    if 'assertRaisesRegex(SraRuntimeError, "prepared-input anchor")' not in stable_lifecycle:
        fail("prepared-input anchor regression is absent from the inherited source")

    if archive_a and archive_b and sha256(archive_a) != sha256(archive_b):
        fail("two Beta archive builds are not byte-reproducible")

    print("PASS: v1.9.1 ROI Beta deterministic SRA compatibility qualification")
    print(f"thin_core_bytes={OVERLAY.stat().st_size}")
    if archive_a:
        print(f"archive_sha256={sha256(archive_a)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stable-plugin-root", required=True, type=Path)
    parser.add_argument("--candidate-plugin-root", required=True, type=Path)
    parser.add_argument("--archive-a", type=Path)
    parser.add_argument("--archive-b", type=Path)
    args = parser.parse_args()
    verify(
        args.stable_plugin_root.resolve(),
        args.candidate_plugin_root.resolve(),
        args.archive_a.resolve() if args.archive_a else None,
        args.archive_b.resolve() if args.archive_b else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
