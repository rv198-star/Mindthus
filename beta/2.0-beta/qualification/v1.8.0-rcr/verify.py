#!/usr/bin/env python3
"""Deterministic v1.8.0 ROI Beta RCR compatibility qualification."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
PROFILE = REPO / "beta" / "2.0-beta" / "profile.json"
REGISTER = REPO / "beta" / "2.0-beta" / "capability-register.json"
OVERLAY = REPO / "beta" / "2.0-beta" / "overlays" / "using-mindthus-v1.8.0-rcr" / "SKILL.md"
HISTORICAL = REPO / "beta" / "2.0-roi-thin-core" / "profile.json"
MAX_BYTES = 2300
ALLOWED_DELTAS = {
    "skills/using-mindthus/SKILL.md",
    "skills/3l5s/SKILL.md",
    ".codex-plugin/plugin.json",
    "scripts/log-mindthus-runtime.py",
}
EXTRA_BETA_FILES = {"beta-profile.json", "capability-register.json"}
REQUIRED_OVERLAY_MARKERS = (
    "using-mindthus — Thin Core",
    "Pursue facts over agreement",
    "Frame and whole:",
    "Decision context:",
    "Evidence ceiling:",
    "Anti-Spiral:",
    "wrong canonical rule or owner",
    "remove obsolete exceptions",
    "intended mainline positively",
    "real vetoes stay explicit",
    "Clear local bugs stay local",
    "no method catalog",
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
    if b"mindthus-beta:" in raw:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            fail(f"Beta namespace appears in non-UTF-8 file: {path}")
        return text.replace("mindthus-beta:", "mindthus:").encode("utf-8")
    return raw


def verify(stable: Path, candidate: Path, archive_a: Path | None, archive_b: Path | None) -> None:
    profile = read_json(PROFILE)
    register = read_json(REGISTER)
    historical = read_json(HISTORICAL)
    overlay = OVERLAY.read_text(encoding="utf-8")
    overlay_compact = " ".join(overlay.split())

    if profile["version"] != "1.8.0-roi-beta":
        fail("composition version is not 1.8.0-roi-beta")
    if profile["shared_core"]["version"] != "1.8.0":
        fail("shared-core version is not 1.8.0")
    if profile["shared_core"]["ref"] != "42887387800806b08796c5972590272414c28c97":
        fail("shared-core ref is not the frozen v1.8.0 Stable tag commit")
    if OVERLAY.stat().st_size > MAX_BYTES:
        fail(f"Thin Core exceeds {MAX_BYTES} bytes: {OVERLAY.stat().st_size}")
    for marker in REQUIRED_OVERLAY_MARKERS:
        if " ".join(marker.split()) not in overlay_compact:
            fail(f"Thin Core missing marker: {marker}")

    if historical.get("candidate") != "2.0.0-roi.2":
        fail("historical runtime profile is not ROI.2")
    correction = historical["package_time_contract_correction"]
    if "hard brake" not in correction["after"] or "Clear failing tests" not in correction["after"]:
        fail("historical ROI.2 Anti-Spiral correction changed")

    if register["shared_core_ref"] != profile["shared_core"]["ref"]:
        fail("capability register shared_core_ref does not match profile")
    rcr = [item for item in register["capabilities"] if item["id"] == "root-cause-replacement-v1"]
    if len(rcr) != 1 or rcr[0]["release_roi_beta"]["version"] != "1.8.0-roi-beta":
        fail("RCR capability is not registered for v1.8.0 ROI Beta")

    manifest = read_json(candidate / ".codex-plugin" / "plugin.json")
    if manifest.get("name") != "mindthus-beta" or manifest.get("version") != "1.8.0-roi-beta":
        fail("Beta plugin identity/version mismatch")
    if (candidate / "skills" / "using-mindthus" / "SKILL.md").read_bytes() != OVERLAY.read_bytes():
        fail("packaged Thin Core differs from the frozen overlay")

    primitive_doc = candidate / "skills" / "using-mindthus" / "resources" / "primitives" / "root-cause-replacement.md"
    if not primitive_doc.is_file():
        fail("packaged RCR primitive document is missing")
    primitive_manifest = read_json(candidate / "scripts" / "primitives" / "manifest.json")
    rcr_runtime = primitive_manifest["primitives"].get("root_cause_replacement")
    if not rcr_runtime:
        fail("runtime manifest is missing root_cause_replacement")
    if "root-cause-finder" not in rcr_runtime.get("not_a", []) or "mandatory-refactor" not in rcr_runtime.get("not_a", []):
        fail("runtime RCR negative controls are incomplete")
    if "root_cause_replacement" not in primitive_manifest["events"]["before-continue"]["active_primitives"]:
        fail("before-continue does not activate the RCR reminder")
    for relative in ("skills/wae/SKILL.md", "skills/tvg/SKILL.md"):
        if "Root-Cause Replacement" not in (candidate / relative).read_text(encoding="utf-8"):
            fail(f"shared-core RCR handoff missing from {relative}")

    corrected_3l5s = (candidate / correction["path"]).read_text(encoding="utf-8")
    if correction["after"] not in corrected_3l5s or correction["before"] in corrected_3l5s:
        fail("qualified ROI.2 3L5S correction is not exact in the package")

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
        if beta_path is None:
            continue
        if stable_path.read_bytes() != normalized_beta_bytes(beta_path):
            fail(f"non-delta shared-core file diverged: {relative}")

    raw_namespace_hits = []
    for relative, path in beta_files.items():
        if b"mindthus:" in path.read_bytes():
            raw_namespace_hits.append(relative)
    if raw_namespace_hits:
        fail(f"Stable namespace leaked into Beta: {raw_namespace_hits[:5]}")

    if archive_a and archive_b:
        if sha256(archive_a) != sha256(archive_b):
            fail("two Beta archive builds are not byte-reproducible")

    print("PASS: v1.8.0 ROI Beta deterministic RCR compatibility qualification")
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
