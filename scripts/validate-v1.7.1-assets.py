#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

STABLE_VERSION = "1.7.1"
STABLE_SHA = "dca73c1ff1710eca3d5b56216c374ce6c2240117"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=cwd, text=True, capture_output=True, check=False)


def checked(*args: str, cwd: Path) -> str:
    result = run(*args, cwd=cwd)
    if result.returncode != 0:
        raise AssertionError(result.stderr + result.stdout)
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reproducible_tar(source: Path, archive_path: Path, root_name: str) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with archive_path.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz, tarfile.open(fileobj=gz, mode="w") as archive:
        for path in sorted(source.rglob("*"), key=lambda p: p.relative_to(source).as_posix()):
            rel = path.relative_to(source)
            info = archive.gettarinfo(str(path), arcname=f"{root_name}/{rel.as_posix()}")
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            info.mode = 0o755 if path.is_dir() or (path.is_file() and path.stat().st_mode & 0o111) else 0o644
            if info.isfile():
                with path.open("rb") as src:
                    archive.addfile(info, src)
            else:
                archive.addfile(info)


def build(repo: Path, work: Path, label: str) -> tuple[Path, Path, Path, Path]:
    plugins = work / f"plugins-{label}"
    skills = work / f"skills-{label}"
    for package, out in (("plugins", plugins), ("skills", skills)):
        result = run(sys.executable, "scripts/build-release-pack.py", "--package", package, "--out", str(out), cwd=repo)
        if result.returncode != 0:
            raise AssertionError(result.stderr + result.stdout)
    plugin_archive = work / f"mindthus-plugins-{label}.tar.gz"
    skills_archive = work / f"mindthus-skills-{label}.tar.gz"
    reproducible_tar(plugins, plugin_archive, f"mindthus-plugins-{STABLE_VERSION}")
    reproducible_tar(skills, skills_archive, f"mindthus-skills-{STABLE_VERSION}")
    return plugins, skills, plugin_archive, skills_archive


def validate_packaged(plugins: Path, skills: Path) -> None:
    codex_manifest = json.loads((plugins / "codex-plugin/mindthus/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
    claude_manifest = json.loads((plugins / "claude-code/claude-plugin/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert codex_manifest["version"] == STABLE_VERSION
    assert claude_manifest["version"] == STABLE_VERSION

    pressure = (skills / "codex/skills/mindthus/using-mindthus/resources/primitives/expression-pressure-and-gates.md").read_text(encoding="utf-8")
    entry = (skills / "codex/skills/mindthus/using-mindthus/SKILL.md").read_text(encoding="utf-8")
    diagnostic = (skills / "codex/scripts/log-mindthus-runtime.py").read_text(encoding="utf-8")
    for marker in (
        "Competitive-frame convergence / 竞争框架收敛",
        "Competitive steelman / 竞争框架钢人",
        "Decisive discriminator / 决定性判别变量",
        "Visible Translation Boundary / 可见表达翻译边界",
    ):
        assert marker in pressure, marker
    assert "Pressure Surface Check / 施压面检查" in entry
    assert "expression-pressure-and-gates.md" in entry
    assert 'VERSION = "1.7.1"' in diagnostic


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()

    assert checked("git", "rev-parse", "HEAD", cwd=repo) == STABLE_SHA
    assert checked("git", "status", "--porcelain=v1", "--untracked-files=all", cwd=repo) == ""
    assert 'VERSION = "1.7.1"' in (repo / "scripts/build-release-pack.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.7.1"' in (repo / "scripts/log-mindthus-runtime.py").read_text(encoding="utf-8")
    manifest = json.loads((repo / "skills/tplan/resources/runtime-manifest.json").read_text(encoding="utf-8"))
    assert manifest["package_version"] == "1.5.4"
    assert manifest["source_id"] == "mindthus-v1.5.4"
    notes = (repo / "docs/releases/v1.7.1.md").read_text(encoding="utf-8")
    assert "protocol-debug evidence" in notes
    assert "TPlan runtime generation 继续保持 `1.5.4`" in notes

    with tempfile.TemporaryDirectory(prefix="mindthus-v171-assets-") as tmp:
        work = Path(tmp)
        p1, s1, pa1, sa1 = build(repo, work, "first")
        p2, s2, pa2, sa2 = build(repo, work, "second")
        validate_packaged(p1, s1)
        validate_packaged(p2, s2)
        assert pa1.read_bytes() == pa2.read_bytes(), "plugin archive is not reproducible"
        assert sa1.read_bytes() == sa2.read_bytes(), "skills archive is not reproducible"

        out.mkdir(parents=True, exist_ok=True)
        final_plugins = out / f"mindthus-plugins-{STABLE_VERSION}.tar.gz"
        final_skills = out / f"mindthus-skills-{STABLE_VERSION}.tar.gz"
        final_plugins.write_bytes(pa1.read_bytes())
        final_skills.write_bytes(sa1.read_bytes())

    assets = [final_plugins, final_skills]
    (out / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in assets), encoding="utf-8")
    report = {
        "status": "valid",
        "stable_version": STABLE_VERSION,
        "stable_sha": STABLE_SHA,
        "assets": [{"name": p.name, "sha256": sha256(p), "size": p.stat().st_size} for p in assets],
        "tplan_runtime_generation": "1.5.4",
        "reproducible_builds": 2,
    }
    (out / "release-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
