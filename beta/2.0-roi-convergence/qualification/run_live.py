#!/usr/bin/env python3
"""Run the frozen incumbent/R1/R2/R3 Codex ROI convergence panel."""

from __future__ import annotations

import argparse
import hashlib
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
PER_CALL_COUNTED_CAP = 200_000
MISSION_COUNTED_CAP = 5_000_000
MISSION_CALL_CAP = 51
ALL_ARMS = ("incumbent", "r1", "r2", "r3")
OWNER_NAMES = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")
PLUGIN_CACHE_RE = re.compile(r"/plugins/cache/[^/]+/[^/]+/[^/]+/([^'\"\s;]+)")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def qualification_root() -> Path:
    return Path(__file__).resolve().parent


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


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


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
    loaded_skills = sorted(
        {
            match.group(1)
            for relative in loaded_paths
            if (match := re.match(r"skills/([^/]+)/", relative))
        }
    )
    loaded_owners = sorted(name for name in loaded_skills if name in OWNER_NAMES)
    input_tokens = int(usage.get("input_tokens", 0))
    cached_tokens = int(usage.get("cached_input_tokens", 0))
    output_tokens = int(usage.get("output_tokens", 0))
    return {
        "usage": usage,
        "counted_tokens": input_tokens + output_tokens,
        "uncached_input_tokens": input_tokens - cached_tokens,
        "loaded_paths": loaded_paths,
        "loaded_skills": loaded_skills,
        "loaded_owners": loaded_owners,
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
    home.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    shutil.copy2(auth_source, home / "auth.json")
    env = dict(os.environ)
    env["CODEX_HOME"] = str(home)
    run_checked(
        [codex, "plugin", "marketplace", "add", str(marketplace), "--json"],
        cwd=workspace,
        env=env,
    )
    run_checked([codex, "plugin", "add", selector, "--json"], cwd=workspace, env=env)
    return env


def build_arms(root: Path, runtime_root: Path, arms: list[str]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for arm in arms:
        pack = runtime_root / f"{arm}-pack"
        if arm == "incumbent":
            run_checked(
                [
                    sys.executable,
                    str(root / "beta" / "2.0-roi-thin-core" / "build-candidate.py"),
                    "--out",
                    str(pack),
                ],
                cwd=root,
                env=dict(os.environ),
            )
            marketplace_name = "mindthus-roi"
        else:
            run_checked(
                [
                    sys.executable,
                    str(root / "beta" / "2.0-roi-convergence" / "build-candidate.py"),
                    "--route",
                    arm,
                    "--out",
                    str(pack),
                ],
                cwd=root,
                env=dict(os.environ),
            )
            profile = json.loads(
                (root / "beta" / "2.0-roi-convergence" / "profile.json").read_text(
                    encoding="utf-8"
                )
            )
            marketplace_name = profile["routes"][arm]["marketplace"]
        plugin_root = pack / "mindthus"
        result[arm] = {
            "marketplace": pack,
            "selector": f"mindthus@{marketplace_name}",
            "source_plugin": plugin_root,
            "plugin_tree_sha256": tree_sha256(plugin_root),
        }
    return result


def run_call(
    *,
    arm: str,
    case: dict,
    pack: dict,
    auth_source: Path,
    codex: str,
    runtime_root: Path,
    evidence_root: Path,
    fixtures_root: Path,
) -> dict:
    call_root = runtime_root / "calls" / arm / case["id"]
    home = call_root / "home"
    workspace = call_root / "workspace"
    fixture = fixtures_root / case["id"]
    if fixture.is_dir():
        shutil.copytree(fixture, workspace)
    else:
        workspace.mkdir(parents=True)

    env = prepare_home(
        home,
        workspace,
        pack["marketplace"],
        pack["selector"],
        auth_source,
        codex,
    )
    evidence = evidence_root / arm / case["id"]
    plugin_list = run_checked([codex, "plugin", "list", "--json"], cwd=workspace, env=env)
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
    timed_out = False
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            env=env,
            input=case["prompt"] + "\n",
            text=True,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        exit_code = 124
    duration = time.monotonic() - started
    write_text(evidence / "events.jsonl", stdout)
    write_text(evidence / "stderr.txt", stderr)
    parsed = parse_jsonl(stdout, pack["source_plugin"])
    write_text(evidence / "final.txt", parsed["final"] + "\n")
    summary = {
        "arm": arm,
        "case": case["id"],
        "group": case["group"],
        "expected": case["expected"],
        "required_owner": case["required_owner"],
        "passive_family": case["passive_family"],
        "model": MODEL,
        "effort": EFFORT,
        "started_at": started_at,
        "duration_seconds": round(duration, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "plugin_tree_sha256": pack["plugin_tree_sha256"],
        **parsed,
    }
    write_json(evidence / "summary.json", summary)
    return summary


def load_summaries(evidence_root: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(evidence_root.glob("*/*/summary.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def median_metrics(records: list[dict]) -> dict:
    return {
        "loaded_mindthus_bytes": statistics.median(
            record["loaded_mindthus_bytes"] for record in records
        ),
        "uncached_input_tokens": statistics.median(
            record["uncached_input_tokens"] for record in records
        ),
        "duration_seconds": statistics.median(record["duration_seconds"] for record in records),
    }


def reduction(baseline: float, candidate: float) -> float | None:
    return None if baseline == 0 else round((baseline - candidate) / baseline, 4)


def write_comparison(evidence_root: Path, cases: list[dict], arms: list[str]) -> dict:
    records = load_summaries(evidence_root)
    expected_case_ids = {case["id"] for case in cases}
    by_arm = {
        arm: [record for record in records if record["arm"] == arm and record["case"] in expected_case_ids]
        for arm in arms
    }
    medians: dict[str, dict] = {}
    hard_medians: dict[str, dict] = {}
    complete: dict[str, bool] = {}
    for arm, values in by_arm.items():
        complete[arm] = len(values) == len(cases) and all(item["exit_code"] == 0 for item in values)
        if values:
            medians[arm] = median_metrics(values)
        hard = [item for item in values if item["group"] == "hard_judgment"]
        if hard:
            hard_medians[arm] = median_metrics(hard)

    reductions: dict[str, dict] = {}
    if "incumbent" in medians:
        for arm, values in medians.items():
            if arm == "incumbent":
                continue
            reductions[arm] = {
                metric: reduction(medians["incumbent"][metric], values[metric])
                for metric in medians["incumbent"]
            }

    comparison = {
        "schema_version": "mindthus-roi-convergence-live-v0.1",
        "model": MODEL,
        "effort": EFFORT,
        "expected_cases": sorted(expected_case_ids),
        "arms": arms,
        "calls": len(records),
        "counted_tokens": sum(int(item.get("counted_tokens", 0)) for item in records),
        "complete": complete,
        "medians": medians,
        "hard_judgment_medians": hard_medians,
        "reductions_vs_incumbent": reductions,
        "records": records,
        "semantic_verdict": "agentic_review_required",
    }
    write_json(evidence_root / "comparison.json", comparison)
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--cases-file", type=Path)
    parser.add_argument("--arms", nargs="+", choices=ALL_ARMS, default=list(ALL_ARMS))
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--auth", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    qualification = qualification_root()
    cases_path = (args.cases_file or (qualification / "cases.json")).resolve()
    all_cases = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = [case for case in all_cases if not args.case or case["id"] in set(args.case)]
    if args.case and len(cases) != len(set(args.case)):
        known = {case["id"] for case in all_cases}
        raise SystemExit(f"unknown case id: {sorted(set(args.case) - known)}")

    evidence_root = args.evidence.resolve()
    if evidence_root.exists() and any(evidence_root.iterdir()) and not args.resume:
        raise SystemExit(f"evidence directory is not empty: {evidence_root}; use --resume")
    evidence_root.mkdir(parents=True, exist_ok=True)

    default_home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
    auth_source = (args.auth or (default_home / "auth.json")).resolve()
    if not auth_source.is_file():
        raise SystemExit(f"Codex auth file not found: {auth_source}")

    schedule: list[tuple[str, dict]] = []
    arms = list(dict.fromkeys(args.arms))
    for index, case in enumerate(cases):
        offset = index % len(arms)
        order = arms[offset:] + arms[:offset]
        schedule.extend((arm, case) for arm in order)
    write_json(
        evidence_root / "RUN-METADATA.json",
        {
            "model": MODEL,
            "effort": EFFORT,
            "arms": arms,
            "cases": [case["id"] for case in cases],
            "schedule": [{"arm": arm, "case": case["id"]} for arm, case in schedule],
            "per_call_counted_cap": PER_CALL_COUNTED_CAP,
            "mission_counted_cap": MISSION_COUNTED_CAP,
            "mission_call_cap": MISSION_CALL_CAP,
            "protocol": "beta/2.0-roi-convergence/PROTOCOL.md",
            "cases_file": str(cases_path),
        },
    )

    existing = load_summaries(evidence_root)
    if any(item["exit_code"] != 0 for item in existing):
        raise SystemExit("existing evidence contains a failed call; inspect before resuming")

    with tempfile.TemporaryDirectory(prefix="mindthus-roi-convergence-live-") as temporary:
        runtime_root = Path(temporary)
        packs = build_arms(root, runtime_root, arms)
        for arm, case in schedule:
            summary_path = evidence_root / arm / case["id"] / "summary.json"
            if summary_path.is_file():
                print(f"skip {arm}/{case['id']}: completed", flush=True)
                continue
            current = load_summaries(evidence_root)
            used_calls = len(current)
            used_tokens = sum(int(item.get("counted_tokens", 0)) for item in current)
            if used_calls >= MISSION_CALL_CAP or used_tokens >= MISSION_COUNTED_CAP:
                write_json(
                    evidence_root / "BUDGET-STOP.json",
                    {"used_calls": used_calls, "used_tokens": used_tokens},
                )
                return 2
            record = run_call(
                arm=arm,
                case=case,
                pack=packs[arm],
                auth_source=auth_source,
                codex=args.codex,
                runtime_root=runtime_root,
                evidence_root=evidence_root,
                fixtures_root=qualification / "fixtures",
            )
            print(
                f"{arm}/{case['id']}: exit={record['exit_code']} "
                f"counted={record['counted_tokens']} uncached={record['uncached_input_tokens']} "
                f"loaded={record['loaded_mindthus_bytes']} duration={record['duration_seconds']}s",
                flush=True,
            )
            comparison = write_comparison(evidence_root, cases, arms)
            if record["exit_code"] != 0:
                write_json(evidence_root / "RUN-FAILED.json", record)
                return 1
            if record["counted_tokens"] > PER_CALL_COUNTED_CAP:
                write_json(evidence_root / "PER-CALL-BUDGET-STOP.json", record)
                return 2
            if comparison["counted_tokens"] > MISSION_COUNTED_CAP:
                write_json(
                    evidence_root / "BUDGET-STOP.json",
                    {
                        "used_calls": comparison["calls"],
                        "used_tokens": comparison["counted_tokens"],
                    },
                )
                return 2

    comparison = write_comparison(evidence_root, cases, arms)
    print(json.dumps(comparison["reductions_vs_incumbent"], ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
