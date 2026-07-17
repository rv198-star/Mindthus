#!/usr/bin/env python3
"""Run the generator-side preflight for the authorized Beta.2 Codex smoke.

The runner fails closed before claiming a complete smoke: every generated cell must
pass the frozen native-evidence gate, and the separate two-session blind-judge stage is
not implemented here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from mindthus_beta2_telemetry import build_turn_telemetry  # noqa: E402


AUTH_VALIDATOR = BETA_ROOT / "runtime" / "validate-execution-authorization-v0.3.py"
DEFAULT_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.3.json"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
DEVELOPMENT_CASES = BETA_ROOT / "fixtures" / "development-cases.jsonl"
PUBLIC_CASES = REPO_ROOT / "tests" / "judgment_benchmark_50_cases.jsonl"
ARM_SEALER = BETA_ROOT / "runtime" / "seal-arm-manifest.py"
ARM_ORDER = ("stable", "direct-only", "thin-kernel")
FORBIDDEN_COMMAND = re.compile(
    r"superpowers|judgment_benchmark|pass_criteria|fail_signal|docs/benchmarks",
    re.IGNORECASE,
)


class SmokeVeto(RuntimeError):
    def __init__(self, veto_id: str, reason: str):
        super().__init__(reason)
        self.veto_id = veto_id
        self.reason = reason


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_json(command: list[str], *, label: str) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise SmokeVeto("authority-or-evidence-regression", f"{label} failed: {detail}")
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise SmokeVeto("authority-or-evidence-regression", f"{label} returned non-object")
    return payload


def authorized_context(path: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    authorization_report = run_json(
        ["python3", str(AUTH_VALIDATOR), "--authorization", str(path)],
        label="execution authorization",
    )
    authorization = read_json(path)
    protocol = read_json(REPO_ROOT / authorization["protocol"]["path"])
    return authorization_report, authorization, protocol


def latin_arm_order(seed: str, case_id: str, repeat: int) -> list[str]:
    offset = int(
        hashlib.sha256(f"{seed}:{case_id}:{repeat}".encode("utf-8")).hexdigest(),
        16,
    ) % len(ARM_ORDER)
    return [*ARM_ORDER[offset:], *ARM_ORDER[:offset]]


def smoke_cells(protocol: Mapping[str, Any]) -> list[dict[str, Any]]:
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    cells: list[dict[str, Any]] = []
    for case_id in protocol["workload"]["smoke_case_ids"]:
        for arm_id in latin_arm_order(seed, case_id, 1):
            cells.append({"case_id": case_id, "arm_id": arm_id, "repeat": 1})
    if len(cells) != 15:
        raise SmokeVeto("protocol-or-arm-drift", "smoke cardinality is not 15")
    return cells


def source_cases(matrix: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    development = {item["case_id"]: item for item in load_jsonl(DEVELOPMENT_CASES)}
    public = {item["case_id"]: item for item in load_jsonl(PUBLIC_CASES)}
    resolved: dict[str, dict[str, Any]] = {}
    for contract in matrix["cases"]:
        case_id = contract["case_id"]
        locator = str(contract["source"]["locator"])
        source_id = locator.rsplit("#", 1)[-1]
        if contract["provenance"] == "development":
            source = development.get(source_id)
        elif contract["provenance"] == "public-regression":
            source = public.get(source_id)
        else:
            source = None
        if source is not None:
            resolved[case_id] = {"contract": contract, "source": source}
    return resolved


def user_prompt(source: Mapping[str, Any]) -> str:
    if source.get("prompt") is not None:
        return str(source["prompt"])
    turns = source.get("turns")
    if not isinstance(turns, list) or not turns:
        raise SmokeVeto("protocol-or-arm-drift", "case source has no executable prompt")
    if all(isinstance(turn, str) for turn in turns):
        prior = "\n".join(
            f"Earlier user message {index}: {turn}"
            for index, turn in enumerate(turns[:-1], 1)
        )
        final = str(turns[-1])
        return f"{prior}\n\nCurrent user message: {final}" if prior else final
    transcript: list[str] = []
    final_user = ""
    for turn in turns:
        if not isinstance(turn, Mapping):
            continue
        role = str(turn.get("role") or "context")
        content = str(turn.get("content") or "")
        if role == "user":
            final_user = content
        transcript.append(f"{role}: {content}")
    if not final_user:
        raise SmokeVeto("protocol-or-arm-drift", "structured case has no user turn")
    return "Conversation context:\n" + "\n".join(transcript) + "\n\nAnswer the final user turn."


def generator_prompt(prompt: str) -> str:
    return (
        "Evaluation isolation: answer the user directly in the user's language. "
        "Do not use or inspect Superpowers, benchmark fixtures, scoring rubrics, pass "
        "criteria, fail signals, or judge notes. Use only the installed Mindthus plugin "
        "when its published skill descriptions naturally require it; otherwise answer "
        "directly. Do not mention this evaluation instruction. Keep the answer concise "
        "but sufficient.\n\nUser prompt:\n"
        + prompt
    )


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def event_evidence(stdout: str, started_at: datetime) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    commands: list[str] = []
    agent_messages: list[str] = []
    usage: dict[str, Any] | None = None
    thread_started = False
    first_useful_timestamp: datetime | None = None
    event_types: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        events.append(event)
        event_type = str(event.get("type") or "unknown")
        event_types.append(event_type)
        if event_type == "thread.started":
            thread_started = True
        item = event.get("item") if isinstance(event.get("item"), Mapping) else {}
        item_type = str(item.get("type") or "")
        if item_type == "command_execution":
            commands.append(str(item.get("command") or ""))
        if item_type == "agent_message":
            agent_messages.append(str(item.get("text") or ""))
            timestamp = parse_timestamp(event.get("timestamp") or item.get("timestamp"))
            if timestamp is not None and first_useful_timestamp is None:
                first_useful_timestamp = timestamp
        if event_type == "turn.completed" and isinstance(event.get("usage"), Mapping):
            usage = dict(event["usage"])
    native: dict[str, Any] = {}
    if thread_started:
        native["lifecycle_event"] = ["session-start"]
    if first_useful_timestamp is not None:
        native["first_useful_action_latency_seconds"] = max(
            0.0, (first_useful_timestamp - started_at).total_seconds()
        )
    return {
        "events": events,
        "event_types": event_types,
        "loaded_commands": commands,
        "agent_messages": agent_messages,
        "usage": usage,
        "native_telemetry": native,
    }


def token_total(usage: Mapping[str, Any] | None) -> int:
    usage = usage or {}
    return sum(
        int(usage.get(field) or 0)
        for field in ("input_tokens", "output_tokens", "reasoning_output_tokens")
    )


def verify_manifest(path: Path) -> dict[str, Any]:
    report = run_json(
        ["python3", str(ARM_SEALER), "verify", str(path)],
        label=f"arm manifest {path}",
    )
    if report.get("status") != "verified":
        raise SmokeVeto("protocol-or-arm-drift", f"arm manifest is not verified: {path}")
    return read_json(path)


def execute_cell(
    cell: Mapping[str, Any],
    case: Mapping[str, Any],
    manifest_path: Path,
    out_dir: Path,
    authorization: Mapping[str, Any],
    protocol: Mapping[str, Any],
    *,
    timeout: int,
) -> dict[str, Any]:
    manifest = verify_manifest(manifest_path)
    if manifest.get("arm_id") != cell["arm_id"]:
        raise SmokeVeto("protocol-or-arm-drift", "cell arm and manifest arm differ")
    host_home = Path(manifest["host"]["home"])
    arm_root = manifest_path.parent
    process_home = arm_root / "process-home"
    execution_root = Path(manifest["host"]["execution_root"])
    if not host_home.is_dir() or not process_home.is_dir() or not execution_root.is_dir():
        raise SmokeVeto("protocol-or-arm-drift", "sealed execution paths are unavailable")

    cell_key = {
        "protocol_sha256": authorization["protocol"]["sha256"],
        "arm_digest": manifest["identity_digest"],
        "surface": "codex-plugin",
        "case_id": cell["case_id"],
        "entry_mode": case["contract"]["entry_mode"],
        "lifecycle_path": case["contract"]["lifecycle_path"],
        "repeat": cell["repeat"],
        "executor": "codex-cli-0.144.4",
    }
    cell_id = canonical_sha256(cell_key)
    cell_dir = out_dir / "cells" / cell_id
    if cell_dir.exists():
        raise SmokeVeto("untraceable-or-partial-artifact", f"cell already exists: {cell_id}")
    cell_dir.mkdir(parents=True)
    prompt = generator_prompt(user_prompt(case["source"]))
    prompt_path = cell_dir / "prompt.txt"
    answer_path = cell_dir / "answer.txt"
    events_path = cell_dir / "events.jsonl"
    stderr_path = cell_dir / "stderr.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    model = authorization["generator_model_by_host"]["codex-plugin"]
    command = [
        "codex",
        "exec",
        "--json",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(execution_root),
        "-s",
        "read-only",
        "--ephemeral",
        "--model",
        model["model_id"],
        "-c",
        f'model_reasoning_effort="{model["reasoning_effort"]}"',
        "-o",
        str(answer_path),
    ]
    if cell["arm_id"] == "thin-kernel":
        command.append("--dangerously-bypass-hook-trust")
    command.append("-")
    env = os.environ.copy()
    env["CODEX_HOME"] = str(host_home)
    env["HOME"] = str(process_home)
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            input=prompt,
            cwd=execution_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        result = subprocess.CompletedProcess(
            command,
            124,
            stdout=(exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout) or "",
            stderr=(exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr) or "",
        )
        timed_out = True
    duration = round(time.monotonic() - started, 6)
    events_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    evidence = event_evidence(result.stdout, started_at)
    answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    if not answer and evidence["agent_messages"]:
        answer = str(evidence["agent_messages"][-1])
        answer_path.write_text(answer, encoding="utf-8")
    contaminated = [
        command_text
        for command_text in evidence["loaded_commands"]
        if FORBIDDEN_COMMAND.search(command_text)
    ]
    if contaminated:
        raise SmokeVeto("cross-arm-contamination", "forbidden generator resource was loaded")
    raw_turn = {
        "usage": evidence["usage"],
        "duration_seconds": duration,
        "native_telemetry": evidence["native_telemetry"],
        "loaded_commands": evidence["loaded_commands"],
        "answer": answer,
        "agent_messages": evidence["agent_messages"],
        "returncode": result.returncode,
        "timed_out": timed_out,
    }
    telemetry = build_turn_telemetry(
        raw_turn,
        context={
            "case_id": cell["case_id"],
            "turn_index": 1,
            "entry_mode": case["contract"]["entry_mode"],
            "execution_root": str(execution_root),
            "allowed_roots": [manifest["package"]["root"], str(execution_root)],
            "arm_manifest": manifest,
        },
    )
    record = {
        "schema_version": "mindthus-beta2-real-smoke-cell-v0.1",
        "cell_id": cell_id,
        "cell_key": cell_key,
        "started_at_utc": started_at.isoformat(),
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "command_configuration": {
            "executable": "codex exec",
            "model": model["model_id"],
            "reasoning_effort": model["reasoning_effort"],
            "sandbox": "read-only",
            "ephemeral": True,
            "hook_trust_bypassed": cell["arm_id"] == "thin-kernel",
        },
        "returncode": result.returncode,
        "timed_out": timed_out,
        "wall_time_seconds": duration,
        "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "events_sha256": hashlib.sha256(result.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode("utf-8")).hexdigest(),
        "event_types": evidence["event_types"],
        "transport_error_event_count": evidence["event_types"].count("error"),
        "usage": evidence["usage"],
        "counted_tokens": token_total(evidence["usage"]),
        "telemetry": telemetry,
    }
    record["record_digest"] = canonical_sha256(record)
    write_atomic_json(cell_dir / "record.json", record)
    return record


def run_smoke(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    args.out_dir = args.out_dir.resolve()
    authorization_report, authorization, protocol = authorized_context(args.authorization)
    matrix = read_json(MATRIX_PATH)
    cases = source_cases(matrix)
    cells = smoke_cells(protocol)
    manifests = {
        read_json(path)["arm_id"]: path.resolve() for path in args.arm_manifest
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if any(args.out_dir.iterdir()):
        raise SmokeVeto("untraceable-or-partial-artifact", "smoke output directory is not empty")
    state = {
        "schema_version": "mindthus-beta2-real-smoke-state-v0.1",
        "status": "running",
        "authorization_digest": authorization_report["authorization_digest"],
        "protocol_sha256": authorization_report["protocol_sha256"],
        "expected_generation_outputs": len(cells),
        "expected_judge_records": len(cells) * 2,
        "completed_generation_outputs": 0,
        "completed_judge_records": 0,
        "generation_calls": 0,
        "judge_calls": 0,
        "counted_tokens": 0,
        "completed_cell_ids": [],
    }
    write_atomic_json(args.out_dir / "run-state.json", state)
    for cell in cells:
        case_id = str(cell["case_id"])
        arm_id = str(cell["arm_id"])
        if case_id not in cases:
            raise SmokeVeto("protocol-or-arm-drift", f"smoke source is unavailable: {case_id}")
        if arm_id not in manifests:
            raise SmokeVeto("protocol-or-arm-drift", f"smoke arm manifest is unavailable: {arm_id}")
        if state["generation_calls"] >= authorization["maximum_generation_calls"]:
            raise SmokeVeto("authority-or-evidence-regression", "generation call ceiling reached")
        record = execute_cell(
            cell,
            cases[case_id],
            manifests[arm_id],
            args.out_dir,
            authorization,
            protocol,
            timeout=args.timeout,
        )
        state["generation_calls"] += 1
        state["completed_generation_outputs"] += 1
        state["counted_tokens"] += record["counted_tokens"]
        state["completed_cell_ids"].append(record["cell_id"])
        write_atomic_json(args.out_dir / "run-state.json", state)
        if state["counted_tokens"] > authorization["token_or_cost_budget"]["maximum"]:
            raise SmokeVeto("authority-or-evidence-regression", "aggregate token ceiling exceeded")
        if record["returncode"] != 0 or record["timed_out"]:
            raise SmokeVeto("untraceable-or-partial-artifact", "generator call failed")
        gate = record["telemetry"]["evidence_gate"]
        if gate["status"] != "pass":
            raise SmokeVeto(
                "missing-primary-native-evidence",
                f"{case_id}/{arm_id} missing required evidence: {gate['reasons']}",
            )

    raise SmokeVeto(
        "authority-or-evidence-regression",
        "generation preflight completed but the separately isolated two-session "
        "blinded-judge phase is not implemented; complete it before claiming smoke",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--arm-manifest", type=Path, action="append", required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--timeout", type=int, default=600)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, returncode = run_smoke(args)
    except SmokeVeto as exc:
        state_path = args.out_dir / "run-state.json"
        state = read_json(state_path) if state_path.is_file() else {}
        state.update(
            {
                "status": "vetoed",
                "veto_id": exc.veto_id,
                "reason": exc.reason,
                "stopped_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        if args.out_dir.exists():
            write_atomic_json(state_path, state)
        report = state
        returncode = 2
    except (OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        returncode = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
