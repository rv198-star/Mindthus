#!/usr/bin/env python3
"""Run the frozen five-case Stable/Candidate Codex qualification."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


MODEL = "gpt-5.6-sol"
EFFORT = "xhigh"
TIMEOUT_SECONDS = 900
PLUGIN_CACHE_RE = re.compile(
    r"/plugins/cache/[^/]+/[^/]+/[^/]+/([^'\"\s;]+)"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def run_checked(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def parse_jsonl(stdout: str, source_plugin: Path) -> dict:
    usage: dict = {}
    final_messages: list[str] = []
    command_items: list[dict] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {})
        if event.get("type") != "item.completed":
            continue
        item = event.get("item", {})
        if item.get("type") == "agent_message":
            final_messages.append(str(item.get("text", "")))
        if item.get("type") == "command_execution":
            command_items.append(item)

    loaded_relatives: set[str] = set()
    for item in command_items:
        command = str(item.get("command", ""))
        for relative in PLUGIN_CACHE_RE.findall(command):
            candidate = source_plugin / relative
            if candidate.is_file():
                loaded_relatives.add(relative)

    loaded_paths = sorted(loaded_relatives)
    loaded_bytes = sum((source_plugin / relative).stat().st_size for relative in loaded_paths)
    input_tokens = int(usage.get("input_tokens", 0))
    cached_tokens = int(usage.get("cached_input_tokens", 0))
    return {
        "usage": usage,
        "uncached_input_tokens": input_tokens - cached_tokens,
        "loaded_paths": loaded_paths,
        "loaded_mindthus_bytes": loaded_bytes,
        "final": final_messages[-1] if final_messages else "",
    }


def prepare_home(
    home: Path,
    workspace: Path,
    marketplace: Path,
    selector: str,
    auth_source: Path,
    codex: str,
) -> dict[str, str]:
    home.mkdir(parents=True)
    workspace.mkdir(parents=True)
    shutil.copy2(auth_source, home / "auth.json")
    env = dict(os.environ)
    env["CODEX_HOME"] = str(home)
    run_checked(
        [codex, "plugin", "marketplace", "add", str(marketplace), "--json"],
        cwd=workspace,
        env=env,
    )
    run_checked(
        [codex, "plugin", "add", selector, "--json"],
        cwd=workspace,
        env=env,
    )
    return env


def run_call(
    *,
    arm: str,
    case: dict,
    marketplace: Path,
    selector: str,
    source_plugin: Path,
    auth_source: Path,
    codex: str,
    runtime_root: Path,
    evidence_root: Path,
    fixtures_root: Path,
) -> dict:
    call_root = runtime_root / arm / case["id"]
    home = call_root / "home"
    workspace = call_root / "workspace"
    fixture = fixtures_root / case["id"]
    if fixture.is_dir():
        shutil.copytree(fixture, workspace)
    else:
        workspace.mkdir(parents=True)

    env = prepare_home(home, workspace, marketplace, selector, auth_source, codex)
    evidence = evidence_root / arm / case["id"]
    plugin_list = run_checked(
        [codex, "plugin", "list", "--json"], cwd=workspace, env=env
    )
    write_text(evidence / "plugin-list.json", plugin_list.stdout)
    config = home / "config.toml"
    if config.is_file():
        shutil.copy2(config, evidence / "config.toml")

    command = [
        codex,
        "exec",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "--ignore-rules",
        "--color",
        "never",
        "-m",
        MODEL,
        "-c",
        f'model_reasoning_effort="{EFFORT}"',
        "-c",
        'approval_policy="never"',
        "-s",
        "read-only",
        "-C",
        str(workspace),
        "-",
    ]
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=workspace,
        env=env,
        input=case["prompt"] + "\n",
        text=True,
        capture_output=True,
        timeout=TIMEOUT_SECONDS,
    )
    duration = time.monotonic() - started
    write_text(evidence / "events.jsonl", result.stdout)
    write_text(evidence / "stderr.txt", result.stderr)
    parsed = parse_jsonl(result.stdout, source_plugin)
    write_text(evidence / "final.txt", parsed["final"] + "\n")
    summary = {
        "arm": arm,
        "case": case["id"],
        "expected": case["expected"],
        "model": MODEL,
        "effort": EFFORT,
        "started_at": started_at,
        "duration_seconds": round(duration, 3),
        "exit_code": result.returncode,
        **parsed,
    }
    write_json(evidence / "summary.json", summary)
    return summary


def median_metrics(records: list[dict]) -> dict:
    return {
        "loaded_mindthus_bytes": statistics.median(
            record["loaded_mindthus_bytes"] for record in records
        ),
        "uncached_input_tokens": statistics.median(
            record["uncached_input_tokens"] for record in records
        ),
        "duration_seconds": statistics.median(
            record["duration_seconds"] for record in records
        ),
    }


def reduction(stable: float, candidate: float) -> float | None:
    return None if stable == 0 else round((stable - candidate) / stable, 4)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--auth", type=Path)
    args = parser.parse_args()

    root = repo_root()
    qualification = Path(__file__).resolve().parent
    candidate_root = qualification.parent
    cases = json.loads((qualification / "cases.json").read_text(encoding="utf-8"))
    evidence_root = args.evidence.resolve()
    if evidence_root.exists() and any(evidence_root.iterdir()):
        raise SystemExit(f"evidence directory is not empty: {evidence_root}")
    evidence_root.mkdir(parents=True, exist_ok=True)

    default_home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    auth_source = (args.auth or (default_home / "auth.json")).resolve()
    if not auth_source.is_file():
        raise SystemExit(f"Codex auth file not found: {auth_source}")

    with tempfile.TemporaryDirectory(prefix="mindthus-roi-live-") as temporary:
        runtime_root = Path(temporary)
        stable_pack = runtime_root / "stable-pack"
        candidate_pack = runtime_root / "candidate-pack"
        run_checked(
            [
                sys.executable,
                str(root / "scripts" / "build-release-pack.py"),
                "--package",
                "plugins",
                "--out",
                str(stable_pack),
            ],
            cwd=root,
            env=dict(os.environ),
        )
        run_checked(
            [
                sys.executable,
                str(candidate_root / "build-candidate.py"),
                "--out",
                str(candidate_pack),
            ],
            cwd=root,
            env=dict(os.environ),
        )

        arms = {
            "stable": {
                "marketplace": stable_pack / "codex-plugin",
                "selector": "mindthus@mindthus",
                "source_plugin": stable_pack / "codex-plugin" / "mindthus",
            },
            "candidate": {
                "marketplace": candidate_pack,
                "selector": "mindthus@mindthus-roi",
                "source_plugin": candidate_pack / "mindthus",
            },
        }
        records: list[dict] = []
        for case in cases:
            for arm in case["arm_order"]:
                record = run_call(
                    arm=arm,
                    case=case,
                    auth_source=auth_source,
                    codex=args.codex,
                    runtime_root=runtime_root,
                    evidence_root=evidence_root,
                    fixtures_root=qualification / "fixtures",
                    **arms[arm],
                )
                records.append(record)
                print(
                    f"{arm}/{case['id']}: exit={record['exit_code']} "
                    f"uncached={record['uncached_input_tokens']} "
                    f"loaded={record['loaded_mindthus_bytes']} "
                    f"duration={record['duration_seconds']}s",
                    flush=True,
                )
                if record["exit_code"] != 0:
                    write_json(evidence_root / "RUN-FAILED.json", record)
                    return 1

    by_arm = {
        arm: [record for record in records if record["arm"] == arm]
        for arm in ("stable", "candidate")
    }
    medians = {arm: median_metrics(values) for arm, values in by_arm.items()}
    comparison = {
        "schema_version": "mindthus-roi-live-result-v0.1",
        "calls": len(records),
        "model": MODEL,
        "effort": EFFORT,
        "medians": medians,
        "reductions": {
            metric: reduction(medians["stable"][metric], medians["candidate"][metric])
            for metric in medians["stable"]
        },
        "records": records,
    }
    write_json(evidence_root / "comparison.json", comparison)
    print(json.dumps(comparison["reductions"], ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
