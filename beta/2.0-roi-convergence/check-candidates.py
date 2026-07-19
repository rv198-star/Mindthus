#!/usr/bin/env python3
"""Run bounded static checks for the three frozen ROI routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def body_after_frontmatter(path: Path) -> bytes:
    data = path.read_bytes()
    marker = b"\n---\n"
    end = data.find(marker, 4)
    if not data.startswith(b"---\n") or end < 0:
        raise RuntimeError(f"invalid Skill frontmatter: {path}")
    return data[end + len(marker) :]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    candidate_root = Path(__file__).resolve().parent
    results: dict[str, object] = {"schema_version": "roi-static-v0.1", "routes": {}}
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="mindthus-roi-static-") as temporary:
        temporary_root = Path(temporary)
        packs: dict[str, Path] = {}
        for route in ("r1", "r2", "r3"):
            output = temporary_root / route
            subprocess.run(
                [
                    sys.executable,
                    str(candidate_root / "build-candidate.py"),
                    "--route",
                    route,
                    "--out",
                    str(output),
                ],
                cwd=root,
                check=True,
            )
            packs[route] = output / "mindthus"

        stable_edsp = root / "skills" / "edsp" / "SKILL.md"
        stable_owner_bodies = {
            name: body_after_frontmatter(root / "skills" / name / "SKILL.md")
            for name in ("edsp", "sela", "mpg", "wae", "tvg", "tplan")
        }
        for route, plugin in packs.items():
            inventory = sorted(
                path.relative_to(plugin).as_posix()
                for path in (plugin / "skills").rglob("SKILL.md")
            )
            expected_count = 7 if route == "r3" else 8
            if len(inventory) != expected_count:
                failures.append(f"{route}: Skill count {len(inventory)} != {expected_count}")
            using = plugin / "skills" / "using-mindthus" / "SKILL.md"
            using_bytes = using.stat().st_size if using.is_file() else 0
            cap = {"r1": 1500, "r2": 900, "r3": 0}[route]
            if using_bytes > cap:
                failures.append(f"{route}: using bytes {using_bytes} > {cap}")
            for owner, stable_body in stable_owner_bodies.items():
                candidate_body = body_after_frontmatter(
                    plugin / "skills" / owner / "SKILL.md"
                )
                if candidate_body != stable_body:
                    failures.append(f"{route}: {owner} body changed")
            if route == "r1" and sha256(plugin / "skills" / "edsp" / "SKILL.md") != sha256(stable_edsp):
                failures.append("r1: EDSP metadata changed")
            if route in ("r2", "r3") and sha256(plugin / "skills" / "edsp" / "SKILL.md") == sha256(stable_edsp):
                failures.append(f"{route}: EDSP metadata override missing")
            profile = json.loads(
                (plugin / "candidate-profile.json").read_text(encoding="utf-8")
            )
            results["routes"][route] = {
                "discoverable_skills": inventory,
                "using_bytes": using_bytes,
                "profile_sha256": sha256(plugin / "candidate-profile.json"),
                "plugin_sha256": {
                    item: sha256(plugin / item) for item in inventory
                },
            }

    results["failures"] = failures
    results["status"] = "PASS" if not failures else "FAIL"
    output_text = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")
    print(output_text, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
