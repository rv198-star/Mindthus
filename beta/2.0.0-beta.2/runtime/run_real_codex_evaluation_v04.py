#!/usr/bin/env python3
"""Run the frozen Mindthus Beta.2 Codex evaluation v0.4.

Generation homes are isolated by arm. Judge homes are separately isolated and never
receive arm labels, generator paths, runtime telemetry, or package diagnostics. All
semantic attempts are retained; an existing output is never replaced.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for import_root in (RUNTIME_ROOT, SCRIPTS_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from codex_stream_capture import StreamCapture, run_streamed  # noqa: E402
from mindthus_beta2_telemetry import build_turn_telemetry  # noqa: E402


DEFAULT_AUTHORIZATION = BETA_ROOT / "authorizations" / "issue-119-codex-v0.4.json"
MATRIX_PATH = BETA_ROOT / "fixtures" / "evaluation-case-matrix.json"
DEVELOPMENT_CASES = BETA_ROOT / "fixtures" / "development-cases.jsonl"
PUBLIC_CASES = REPO_ROOT / "tests" / "judgment_benchmark_50_cases.jsonl"
JUDGE_SCHEMA = BETA_ROOT / "fixtures" / "judge-output-v0.4.schema.json"
JUDGE_RUBRIC = BETA_ROOT / "fixtures" / "judge-rubric-v0.4.json"
ARM_SEALER = RUNTIME_ROOT / "seal-arm-manifest.py"
ANALYZER = RUNTIME_ROOT / "analyze_codex_evaluation_v04.py"
ARM_ORDER = ("stable", "direct-only", "thin-kernel")
FORBIDDEN_GENERATOR_COMMAND = re.compile(
    r"superpowers|judgment_benchmark|pass_criteria|fail_signal|docs/benchmarks|"
    r"evaluation-case-matrix|judge-rubric|judge-output",
    re.IGNORECASE,
)
FORBIDDEN_JUDGE_PLUGIN = re.compile(r"mindthus|superpowers", re.IGNORECASE)
FORBIDDEN_BLINDING_LABEL = re.compile(
    r"\b(?:direct-only|thin-kernel|stable\s+arm)\b|mindthus(?:-beta)?:",
    re.IGNORECASE,
)
V04_REQUIRED_EVIDENCE: dict[str, tuple[str, ...]] = {
    "tokens.input": ("native",),
    "wall_time_seconds": ("deterministic",),
    "first_observable_action_latency_seconds": ("deterministic",),
    "arm_digest": ("native",),
    "host_plugin_inventory": ("native",),
    "hook_state": ("native",),
    "lifecycle_event": ("native",),
}


class EvaluationStop(RuntimeError):
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def write_atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".partial", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run_json(
    command: list[str],
    *,
    cwd: Path = REPO_ROOT,
    env: Mapping[str, str] | None = None,
    label: str,
) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=dict(env) if env is not None else None,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise EvaluationStop("authority-or-evidence-regression", f"{label} failed: {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EvaluationStop(
            "authority-or-evidence-regression", f"{label} returned invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise EvaluationStop(
            "authority-or-evidence-regression", f"{label} returned a non-object"
        )
    return payload


def repo_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise EvaluationStop("authority-or-evidence-regression", f"{label} is missing")
    path = (REPO_ROOT / value).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise EvaluationStop(
            "authority-or-evidence-regression", f"{label} leaves repository"
        ) from exc
    return path


def authorized_context(
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    authorization = read_json(path)
    validator = repo_path(
        authorization.get("authorization_validator_path"),
        "authorization_validator_path",
    )
    report = run_json(
        ["python3", str(validator), "--authorization", str(path)],
        label="execution authorization",
    )
    if report.get("status") != "authorized":
        raise EvaluationStop("authority-or-evidence-regression", "authorization is inactive")
    protocol = read_json(repo_path(authorization["protocol"]["path"], "protocol.path"))
    return report, authorization, protocol


def latin_arm_order(seed: str, case_id: str, repeat: int) -> list[str]:
    offset = int(
        hashlib.sha256(f"{seed}:{case_id}:{repeat}".encode("utf-8")).hexdigest(),
        16,
    ) % len(ARM_ORDER)
    return [*ARM_ORDER[offset:], *ARM_ORDER[:offset]]


def expected_cells(protocol: Mapping[str, Any], phase: str) -> list[dict[str, Any]]:
    workload = protocol["workload"]
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    cells: list[dict[str, Any]] = []
    if phase == "smoke":
        case_ids = workload["smoke_case_ids"]
        repeats = (1,)
    else:
        case_ids = workload["matched_case_ids"]
        repeats = range(1, int(workload["planned_repeats"]) + 1)
    for repeat in repeats:
        for case_id in case_ids:
            for arm_id in latin_arm_order(seed, str(case_id), repeat):
                cells.append(
                    {"case_id": str(case_id), "arm_id": arm_id, "repeat": repeat}
                )
    expected_count = 15 if phase == "smoke" else 225
    if len(cells) != expected_count:
        raise EvaluationStop(
            "protocol-or-arm-drift",
            f"{phase} cardinality differs: expected={expected_count}, actual={len(cells)}",
        )
    return cells


def source_cases(matrix: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    development = {item["case_id"]: item for item in load_jsonl(DEVELOPMENT_CASES)}
    public = {item["case_id"]: item for item in load_jsonl(PUBLIC_CASES)}
    resolved: dict[str, dict[str, Any]] = {}
    for contract in matrix["cases"]:
        locator = str(contract["source"]["locator"])
        source_id = locator.rsplit("#", 1)[-1]
        source = (
            development.get(source_id)
            if contract["provenance"] == "development"
            else public.get(source_id)
            if contract["provenance"] == "public-regression"
            else None
        )
        if source is not None:
            resolved[str(contract["case_id"])] = {
                "contract": contract,
                "source": source,
            }
    return resolved


def user_prompt(source: Mapping[str, Any]) -> str:
    if source.get("prompt") is not None:
        return str(source["prompt"])
    turns = source.get("turns")
    if not isinstance(turns, list) or not turns:
        raise EvaluationStop("protocol-or-arm-drift", "case source has no executable prompt")
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
        raise EvaluationStop("protocol-or-arm-drift", "structured case has no user turn")
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


def event_evidence(stdout: str) -> dict[str, Any]:
    commands: list[str] = []
    messages: list[str] = []
    usage: dict[str, Any] | None = None
    event_types: list[str] = []
    thread_started = False
    first_native_timestamp: str | None = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, Mapping):
            continue
        event_type = str(event.get("type") or "unknown")
        event_types.append(event_type)
        if event_type == "thread.started":
            thread_started = True
        item = event.get("item") if isinstance(event.get("item"), Mapping) else {}
        if event_type == "item.completed" and item.get("type") == "command_execution":
            commands.append(str(item.get("command") or ""))
        if event_type == "item.completed" and item.get("type") == "agent_message":
            messages.append(str(item.get("text") or ""))
            timestamp = event.get("timestamp") or item.get("timestamp")
            if isinstance(timestamp, str) and timestamp and first_native_timestamp is None:
                first_native_timestamp = timestamp
        if event_type == "turn.completed" and isinstance(event.get("usage"), Mapping):
            usage = dict(event["usage"])
    native: dict[str, Any] = {}
    if thread_started:
        native["lifecycle_event"] = ["session-start"]
    return {
        "event_types": event_types,
        "loaded_commands": commands,
        "agent_messages": messages,
        "usage": usage,
        "native_telemetry": native,
        "first_native_timestamp": first_native_timestamp,
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
        raise EvaluationStop("protocol-or-arm-drift", f"arm is not verified: {path}")
    return read_json(path)


def verify_arm_set(paths: Iterable[Path], authorization: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    resolved = [path.resolve() for path in paths]
    run_json(
        ["python3", str(ARM_SEALER), "verify-set", *map(str, resolved)],
        label="three-arm manifest set",
    )
    manifests = {manifest["arm_id"]: manifest for manifest in map(verify_manifest, resolved)}
    if set(manifests) != set(ARM_ORDER):
        raise EvaluationStop("protocol-or-arm-drift", "three-arm set is incomplete")
    expected_model = authorization["generator_model_by_host"]["codex-plugin"]
    for arm_id, manifest in manifests.items():
        if manifest["model"] != {
            "id": expected_model["model_id"],
            "reasoning": expected_model["reasoning_effort"],
        }:
            raise EvaluationStop("protocol-or-arm-drift", f"{arm_id} model differs")
    thin = manifests["thin-kernel"]
    opaque = thin["ambient_context"]["opaque"]
    hook_receipts = [
        item
        for item in opaque
        if item.get("kind") == "host-hook-observation"
        and item.get("id") == "passive-kernel-session-start"
    ]
    path_by_arm = {str(read_json(path)["arm_id"]): path for path in resolved}
    receipt_path = (
        path_by_arm["thin-kernel"].parent / "evidence" / "hook-observation.json"
    )
    if len(hook_receipts) != 1 or not receipt_path.is_file():
        raise EvaluationStop("protocol-or-arm-drift", "thin arm lacks bound hook observation")
    receipt = read_json(receipt_path)
    unsigned = dict(receipt)
    digest = unsigned.pop("receipt_digest", None)
    if digest != canonical_sha256(unsigned) or digest != hook_receipts[0]["sha256"]:
        raise EvaluationStop("protocol-or-arm-drift", "thin hook observation digest differs")
    if receipt.get("status") != "observed-fired" or receipt.get("model_execution_performed") is not False:
        raise EvaluationStop("protocol-or-arm-drift", "thin hook observation is not evidence-honest")
    if receipt.get("semantic_output_generated") is not False:
        raise EvaluationStop("protocol-or-arm-drift", "thin hook probe produced semantic output")
    if receipt.get("package_tree_sha256") != thin["package"]["tree_sha256"]:
        raise EvaluationStop("protocol-or-arm-drift", "thin hook package receipt differs")
    if receipt.get("kernel_canonical_sha256") != receipt.get(
        "captured_kernel_canonical_sha256"
    ):
        raise EvaluationStop("protocol-or-arm-drift", "thin hook captured kernel differs")
    if receipt.get("network_scope") != "127.0.0.1-only model endpoint":
        raise EvaluationStop("protocol-or-arm-drift", "thin hook probe left loopback scope")
    if (
        receipt.get("expected_kernel_state") != "present"
        or receipt.get("observed_kernel_state") != "present"
        or receipt.get("hook_trust_bypassed_for_vetted_package") is not True
        or receipt.get("request_content_retained") is not False
        or int(receipt.get("matching_request_count") or 0) < 1
    ):
        raise EvaluationStop("protocol-or-arm-drift", "thin hook positive proof differs")

    direct = manifests["direct-only"]
    absence_entries = [
        item
        for item in direct["ambient_context"]["opaque"]
        if item.get("kind") == "host-hook-absence-observation"
        and item.get("id") == "passive-kernel-session-start-disabled"
    ]
    absence_path = (
        path_by_arm["direct-only"].parent
        / "evidence"
        / "hook-absence-observation.json"
    )
    if len(absence_entries) != 1 or not absence_path.is_file():
        raise EvaluationStop("protocol-or-arm-drift", "direct arm lacks hook absence proof")
    absence = read_json(absence_path)
    absence_unsigned = dict(absence)
    absence_digest = absence_unsigned.pop("receipt_digest", None)
    if (
        absence_digest != canonical_sha256(absence_unsigned)
        or absence_digest != absence_entries[0]["sha256"]
        or absence.get("status") != "observed-absent"
        or absence.get("expected_kernel_state") != "absent"
        or absence.get("observed_kernel_state") != "absent"
        or absence.get("hook_trust_bypassed_for_vetted_package") is not False
        or absence.get("model_execution_performed") is not False
        or absence.get("semantic_output_generated") is not False
        or absence.get("captured_kernel_canonical_sha256") is not None
        or absence.get("package_tree_sha256") != direct["package"]["tree_sha256"]
        or absence.get("network_scope") != "127.0.0.1-only model endpoint"
        or absence.get("request_content_retained") is not False
        or int(absence.get("matching_request_count") or 0) < 1
    ):
        raise EvaluationStop("protocol-or-arm-drift", "direct hook absence proof differs")
    return manifests


def cell_identity(
    cell: Mapping[str, Any],
    case: Mapping[str, Any],
    manifest: Mapping[str, Any],
    protocol_sha256: str,
) -> tuple[str, dict[str, Any]]:
    key = {
        "protocol_sha256": protocol_sha256,
        "arm_digest": manifest["identity_digest"],
        "surface": "codex-plugin",
        "case_id": cell["case_id"],
        "entry_mode": case["contract"]["entry_mode"],
        "scenario_lifecycle_path": case["contract"]["lifecycle_path"],
        "host_session_mode": "startup",
        "repeat": cell["repeat"],
        "executor": "codex-cli-0.144.4-v0.4",
    }
    return canonical_sha256(key), key


def scan_partial_artifacts(out_dir: Path) -> None:
    partials = sorted(path for path in out_dir.rglob("*") if ".partial" in path.name)
    if partials:
        raise EvaluationStop(
            "untraceable-or-partial-artifact",
            f"partial semantic artifacts require manual audit: {[str(path) for path in partials]}",
        )


def observed_attempt_usage(out_dir: Path) -> tuple[int, int, int]:
    generation_calls = 0
    judge_calls = 0
    counted_tokens = 0
    for kind, pattern in (
        ("generation", "generation-attempts/**/attempt.json"),
        ("judge", "judge-attempts/**/attempt.json"),
    ):
        for path in sorted(out_dir.glob(pattern)):
            attempt = read_json(path)
            unsigned = dict(attempt)
            digest = unsigned.pop("attempt_digest", None)
            if digest != canonical_sha256(unsigned):
                raise EvaluationStop(
                    "untraceable-or-partial-artifact", f"attempt digest differs: {path}"
                )
            if kind == "generation":
                generation_calls += 1
            else:
                judge_calls += 1
            counted_tokens += int(attempt.get("counted_tokens") or 0)
    return generation_calls, judge_calls, counted_tokens


def attempt_parent(out_dir: Path, kind: str, identifier: str) -> Path:
    path = out_dir / f"{kind}-attempts" / identifier
    path.mkdir(parents=True, exist_ok=True)
    return path


def finalize_attempt(temp_dir: Path, destination: Path) -> None:
    if destination.exists():
        raise EvaluationStop(
            "untraceable-or-partial-artifact", f"attempt already exists: {destination}"
        )
    os.replace(temp_dir, destination)


def completed_cell(out_dir: Path, cell_id: str) -> dict[str, Any] | None:
    path = out_dir / "cells" / cell_id / "record.json"
    if not path.is_file():
        return None
    record = read_json(path)
    unsigned = dict(record)
    digest = unsigned.pop("record_digest", None)
    if digest != canonical_sha256(unsigned):
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell digest differs: {cell_id}")
    if record.get("cell_id") != cell_id or record.get("schema_version") != (
        "mindthus-beta2-real-cell-v0.4"
    ):
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell identity differs: {cell_id}")
    answer_path = Path(str(record.get("answer_path") or "")).resolve()
    attempt_info = record.get("generation_attempt")
    if not isinstance(attempt_info, Mapping):
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell attempt is missing: {cell_id}")
    attempt_path = Path(str(attempt_info.get("path") or "")).resolve()
    try:
        answer_path.relative_to(out_dir.resolve())
        attempt_path.relative_to((out_dir / "generation-attempts").resolve())
    except ValueError as exc:
        raise EvaluationStop(
            "untraceable-or-partial-artifact", f"cell artifact leaves run root: {cell_id}"
        ) from exc
    if answer_path != attempt_path / "answer.txt" or not answer_path.is_file():
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell answer is missing: {cell_id}")
    answer = answer_path.read_text(encoding="utf-8")
    if hashlib.sha256(answer.encode("utf-8")).hexdigest() != record.get("answer_sha256"):
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell answer differs: {cell_id}")
    attempt_file = attempt_path / "attempt.json"
    if not attempt_file.is_file():
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell attempt is missing: {cell_id}")
    attempt = read_json(attempt_file)
    attempt_unsigned = dict(attempt)
    attempt_digest = attempt_unsigned.pop("attempt_digest", None)
    if (
        attempt_digest != canonical_sha256(attempt_unsigned)
        or attempt_digest != attempt_info.get("attempt_digest")
        or int(attempt.get("counted_tokens") or 0) != int(record.get("counted_tokens") or 0)
        or attempt.get("returncode") != 0
        or attempt.get("timed_out") is not False
        or attempt.get("answer_present") is not True
        or attempt.get("answer_sha256") != record.get("answer_sha256")
    ):
        raise EvaluationStop("untraceable-or-partial-artifact", f"cell attempt differs: {cell_id}")
    return record


def generator_command(
    *,
    manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    answer_path: Path,
) -> tuple[list[str], dict[str, str], Path]:
    model = authorization["generator_model_by_host"]["codex-plugin"]
    execution_root = Path(manifest["host"]["execution_root"])
    arm_root = Path(manifest["host"]["home"]).parent
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
    if manifest["arm_id"] == "thin-kernel":
        command.append("--dangerously-bypass-hook-trust")
    command.append("-")
    env = os.environ.copy()
    env.update(
        {
            "CODEX_HOME": str(manifest["host"]["home"]),
            "HOME": str(arm_root / "process-home"),
        }
    )
    return command, env, execution_root


def run_generator_attempt(
    *,
    cell_id: str,
    prompt: str,
    manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    out_dir: Path,
    attempt_number: int,
    timeout: int,
) -> tuple[dict[str, Any], StreamCapture, str, dict[str, Any]]:
    parent = attempt_parent(out_dir, "generation", cell_id)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"attempt-{attempt_number:02d}.partial-", dir=parent))
    answer_path = temp_dir / "answer.txt"
    command, env, execution_root = generator_command(
        manifest=manifest,
        authorization=authorization,
        answer_path=answer_path,
    )
    started_at = datetime.now(timezone.utc).isoformat()
    capture = run_streamed(
        command,
        input_text=prompt,
        cwd=execution_root,
        env=env,
        timeout=timeout,
    )
    (temp_dir / "events.jsonl").write_text(capture.stdout, encoding="utf-8")
    (temp_dir / "stderr.txt").write_text(capture.stderr, encoding="utf-8")
    evidence = event_evidence(capture.stdout)
    answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    if not answer and evidence["agent_messages"]:
        answer = str(evidence["agent_messages"][-1])
        answer_path.write_text(answer, encoding="utf-8")
    attempt = {
        "schema_version": "mindthus-beta2-generation-attempt-v0.4",
        "cell_id": cell_id,
        "attempt": attempt_number,
        "started_at_utc": started_at,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "returncode": capture.returncode,
        "timed_out": capture.timed_out,
        "wall_time_seconds": capture.wall_time_seconds,
        "first_observable_action": capture.first_observable_action,
        "answer_present": bool(answer),
        "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
        "events_sha256": hashlib.sha256(capture.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(capture.stderr.encode("utf-8")).hexdigest(),
        "usage": evidence["usage"],
        "counted_tokens": token_total(evidence["usage"]),
    }
    attempt["attempt_digest"] = canonical_sha256(attempt)
    (temp_dir / "attempt.json").write_text(
        json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    destination = parent / f"attempt-{attempt_number:02d}"
    finalize_attempt(temp_dir, destination)
    attempt["path"] = str(destination)
    return attempt, capture, answer, evidence


def execute_generator_cell(
    *,
    cell: Mapping[str, Any],
    case: Mapping[str, Any],
    manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    protocol_sha256: str,
    out_dir: Path,
    timeout: int,
    generation_calls_used: int,
    forbidden_path_fragments: Iterable[str],
) -> tuple[dict[str, Any], int, int]:
    cell_id, key = cell_identity(cell, case, manifest, protocol_sha256)
    existing = completed_cell(out_dir, cell_id)
    if existing:
        if existing.get("cell_key") != key:
            raise EvaluationStop("protocol-or-arm-drift", f"retained cell differs: {cell_id}")
        if existing.get("telemetry", {}).get("evidence_gate", {}).get("status") != "pass":
            raise EvaluationStop(
                "missing-primary-native-evidence",
                f"retained cell has a blocked evidence gate: {cell_id}",
            )
        return existing, 0, 0
    orphan_attempts = sorted(
        (out_dir / "generation-attempts" / cell_id).glob("attempt-*")
    )
    if orphan_attempts:
        raise EvaluationStop(
            "untraceable-or-partial-artifact",
            f"generation attempt exists without an atomic cell record: {cell_id}",
        )
    prompt = generator_prompt(user_prompt(case["source"]))
    attempts_used = 0
    counted_tokens = 0
    for attempt_number in (1, 2):
        if generation_calls_used + attempts_used >= authorization["maximum_generation_calls"]:
            raise EvaluationStop("authority-or-evidence-regression", "generation call ceiling reached")
        attempt, capture, answer, evidence = run_generator_attempt(
            cell_id=cell_id,
            prompt=prompt,
            manifest=manifest,
            authorization=authorization,
            out_dir=out_dir,
            attempt_number=attempt_number,
            timeout=timeout,
        )
        attempts_used += 1
        counted_tokens += int(attempt["counted_tokens"])
        failed = capture.returncode != 0 or capture.timed_out
        if failed and answer:
            raise EvaluationStop(
                "untraceable-or-partial-artifact",
                f"{cell_id} failed after semantic output; output retained and no retry allowed",
            )
        if failed and attempt_number == 1:
            continue
        if failed:
            raise EvaluationStop(
                "untraceable-or-partial-artifact", f"{cell_id} infrastructure retry failed"
            )
        contaminated = [
            command
            for command in evidence["loaded_commands"]
            if FORBIDDEN_GENERATOR_COMMAND.search(command)
            or "../" in command
            or any(fragment in command for fragment in forbidden_path_fragments)
        ]
        if contaminated:
            raise EvaluationStop(
                "cross-arm-contamination", f"{cell_id} loaded forbidden evaluation resources"
            )
        native = dict(evidence["native_telemetry"])
        raw_turn = {
            "usage": evidence["usage"],
            "duration_seconds": capture.wall_time_seconds,
            "first_observable_action_latency_seconds": (
                capture.first_observable_action["offset_seconds"]
                if capture.first_observable_action
                else None
            ),
            "native_telemetry": native,
            "loaded_commands": evidence["loaded_commands"],
            "answer": answer,
            "agent_messages": evidence["agent_messages"],
            "returncode": capture.returncode,
            "timed_out": capture.timed_out,
        }
        required_evidence = dict(V04_REQUIRED_EVIDENCE)
        if manifest["arm_id"] == "thin-kernel":
            required_evidence["arm.hook_observation_receipt"] = ("deterministic",)
        telemetry = build_turn_telemetry(
            raw_turn,
            context={
                "case_id": cell["case_id"],
                "turn_index": 1,
                "entry_mode": case["contract"]["entry_mode"],
                "execution_root": manifest["host"]["execution_root"],
                "allowed_roots": [
                    manifest["package"]["root"],
                    manifest["host"]["execution_root"],
                ],
                "arm_manifest": manifest,
                "attempt": attempt_number,
            },
            required_evidence=required_evidence,
        )
        record: dict[str, Any] = {
            "schema_version": "mindthus-beta2-real-cell-v0.4",
            "cell_id": cell_id,
            "cell_key": key,
            "arm_id": cell["arm_id"],
            "case_source_receipt": canonical_sha256(case["contract"]["source"]),
            "generation_attempt": {
                "attempt": attempt_number,
                "attempt_digest": attempt["attempt_digest"],
                "path": attempt["path"],
            },
            "answer_path": str(Path(attempt["path"]) / "answer.txt"),
            "answer_sha256": hashlib.sha256(answer.encode("utf-8")).hexdigest(),
            "event_types": evidence["event_types"],
            "transport_error_event_count": evidence["event_types"].count("error"),
            "usage": evidence["usage"],
            "counted_tokens": token_total(evidence["usage"]),
            "telemetry": telemetry,
            "native_first_useful_action_available": bool(evidence["first_native_timestamp"]),
            "host_lifecycle_claim": "startup-session-only",
            "scenario_lifecycle_path": case["contract"]["lifecycle_path"],
        }
        record["record_digest"] = canonical_sha256(record)
        write_atomic_json(out_dir / "cells" / cell_id / "record.json", record)
        if telemetry["evidence_gate"]["status"] != "pass":
            raise EvaluationStop(
                "missing-primary-native-evidence",
                f"{cell['case_id']}/{cell['arm_id']} evidence gate blocked: "
                f"{telemetry['evidence_gate']['reasons']}",
            )
        return record, attempts_used, counted_tokens
    raise AssertionError("unreachable generator attempt loop")


def judge_environment(
    *,
    out_dir: Path,
    runtime_root: Path,
    auth_source: Path,
    slot: int,
) -> dict[str, Any]:
    root = out_dir / "judge-homes" / f"slot-{slot}"
    codex_home = root / "codex-home"
    process_home = root / "process-home"
    execution_root = runtime_root / f"judge-{slot}" / "workspace"
    for path in (codex_home, process_home, execution_root):
        path.mkdir(parents=True, exist_ok=True)
    auth_target = codex_home / "auth.json"
    if not auth_target.exists():
        auth_target.symlink_to(auth_source.resolve())
    if not auth_target.is_symlink() or auth_target.resolve() != auth_source.resolve():
        raise EvaluationStop("judge-environment-contamination", "judge auth receipt differs")
    env = os.environ.copy()
    env.update({"CODEX_HOME": str(codex_home), "HOME": str(process_home)})
    inventory = run_json(
        ["codex", "plugin", "list", "--json"],
        cwd=execution_root,
        env=env,
        label=f"judge slot {slot} plugin inventory",
    )
    installed = inventory.get("installed", [])
    forbidden = [
        entry
        for entry in installed
        if FORBIDDEN_JUDGE_PLUGIN.search(
            str(entry.get("pluginId") or entry.get("id") or entry.get("name") or "")
        )
    ]
    if forbidden:
        raise EvaluationStop(
            "judge-environment-contamination", f"judge slot {slot} has forbidden plugin"
        )
    receipt = {
        "schema_version": "mindthus-beta2-judge-environment-v0.4",
        "slot": slot,
        "codex_home": str(codex_home),
        "process_home": str(process_home),
        "execution_root": str(execution_root),
        "plugin_inventory_sha256": canonical_sha256(inventory),
        "active_forbidden_plugins": [],
        "generator_home_access_granted": False,
        "auth_source_sha256": hashlib.sha256(str(auth_source.resolve()).encode()).hexdigest(),
    }
    receipt["environment_digest"] = canonical_sha256(receipt)
    write_atomic_json(root / "environment.json", receipt)
    return {**receipt, "env": env}


def judge_prompt(
    *,
    rubric: Mapping[str, Any],
    case: Mapping[str, Any],
    prompt: str,
    candidate: str,
    blinded_output_id: str,
) -> str:
    contract = case["contract"]
    payload = {
        "blinded_output_id": blinded_output_id,
        "user_prompt": prompt,
        "case_contract": {
            "case_type": contract["case_type"],
            "entry_mode": contract["entry_mode"],
            "accepted_execution_owners": contract["accepted_execution_owners"],
            "expected_primitive_obligations": contract["expected_primitive_obligations"],
            "required_visible_action": contract["required_visible_action"],
            "stay_asleep_expected": contract["stay_asleep_expected"],
        },
        "candidate_final_answer": candidate,
    }
    return (
        "You are one isolated blinded reviewer. Apply the frozen rubric exactly. "
        "Do not use tools, inspect files, infer the generator arm, or judge hidden reasoning. "
        "Return only the JSON object required by the output schema.\n\n"
        "Frozen rubric:\n"
        + json.dumps(rubric, ensure_ascii=False, sort_keys=True)
        + "\n\nBlinded review payload:\n"
        + json.dumps(payload, ensure_ascii=False, sort_keys=True)
    )


def validate_judge_output(output: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    schema = read_json(JUDGE_SCHEMA)
    required_fields = set(schema["required"])
    if set(output) != required_fields:
        raise ValueError(
            f"judge fields differ: missing={sorted(required_fields - set(output))}, "
            f"extra={sorted(set(output) - required_fields)}"
        )
    score = output["normalized_final_answer_score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)) or score not in (0, 0.5, 1):
        raise ValueError("judge quality score is outside frozen values")
    owner = output["observed_execution_owner"]
    if owner not in schema["properties"]["observed_execution_owner"]["enum"]:
        raise ValueError("judge execution owner is outside frozen values")
    contract = case["contract"]
    primitive_results = output["primitive_obligation_results"]
    if not isinstance(primitive_results, list):
        raise ValueError("primitive obligation results are not an array")
    if any(
        not isinstance(item, Mapping)
        or set(item) != {"primitive_id", "satisfied"}
        or not isinstance(item.get("satisfied"), bool)
        for item in primitive_results
    ):
        raise ValueError("judge primitive result shape differs")
    observed_ids = [item.get("primitive_id") for item in primitive_results]
    expected_ids = list(contract["expected_primitive_obligations"])
    if len(observed_ids) != len(set(observed_ids)) or set(observed_ids) != set(expected_ids):
        raise ValueError(
            f"judge primitive result ids differ: expected={expected_ids}, actual={observed_ids}"
        )
    required_action = contract["required_visible_action"]
    action_result = output["required_visible_action_present"]
    if (required_action is None) != (action_result is None):
        raise ValueError("judge required-visible-action nullability differs")
    if action_result is not None and not isinstance(action_result, bool):
        raise ValueError("judge required-visible-action result is not boolean/null")
    for field in ("false_wakeup_final_answer", "authority_or_evidence_regression"):
        if not isinstance(output[field], bool):
            raise ValueError(f"judge {field} is not boolean")
    unexpected = output["unexpected_primitive_actions"]
    allowed_primitives = set(
        schema["properties"]["unexpected_primitive_actions"]["items"]["enum"]
    )
    if (
        not isinstance(unexpected, list)
        or len(unexpected) != len(set(unexpected))
        or any(item not in allowed_primitives for item in unexpected)
    ):
        raise ValueError("judge unexpected primitive actions differ")
    clarification = output["clarification_turns"]
    if isinstance(clarification, bool) or not isinstance(clarification, int) or clarification < 0:
        raise ValueError("judge clarification count is invalid")
    rationale = output["rationale"]
    if not isinstance(rationale, str) or not rationale or len(rationale) > 800:
        raise ValueError("judge rationale length is invalid")
    normalized = dict(output)
    normalized["owner_success"] = output["observed_execution_owner"] in contract[
        "accepted_execution_owners"
    ]
    normalized["all_required_primitives_success"] = all(
        bool(item["satisfied"]) for item in primitive_results
    )
    normalized["joint_owner_primitive_success"] = (
        normalized["owner_success"] and normalized["all_required_primitives_success"]
    )
    return normalized


def judge_identity(protocol_sha256: str, cell_id: str) -> str:
    return hashlib.sha256(
        f"{protocol_sha256}:{cell_id}:blinded-output-v0.4".encode("utf-8")
    ).hexdigest()


def existing_judge_record(out_dir: Path, output_id: str, slot: int) -> dict[str, Any] | None:
    path = out_dir / "judge-records" / output_id / f"judge-{slot}.json"
    if not path.is_file():
        return None
    record = read_json(path)
    unsigned = dict(record)
    digest = unsigned.pop("record_digest", None)
    if digest != canonical_sha256(unsigned):
        raise EvaluationStop("untraceable-or-partial-artifact", "judge record digest differs")
    attempt_number = record.get("attempt")
    if not isinstance(attempt_number, int) or isinstance(attempt_number, bool):
        raise EvaluationStop("untraceable-or-partial-artifact", "judge attempt differs")
    attempt_path = (
        out_dir
        / "judge-attempts"
        / output_id
        / f"slot-{slot}"
        / f"attempt-{attempt_number:02d}"
    )
    attempt_file = attempt_path / "attempt.json"
    output_path = attempt_path / "judge-output.json"
    if not attempt_file.is_file() or not output_path.is_file():
        raise EvaluationStop("untraceable-or-partial-artifact", "judge attempt is missing")
    attempt = read_json(attempt_file)
    attempt_unsigned = dict(attempt)
    attempt_digest = attempt_unsigned.pop("attempt_digest", None)
    raw_output = output_path.read_text(encoding="utf-8")
    if (
        attempt_digest != canonical_sha256(attempt_unsigned)
        or attempt_digest != record.get("attempt_digest")
        or hashlib.sha256(raw_output.encode("utf-8")).hexdigest()
        != attempt.get("output_sha256")
        or int(attempt.get("counted_tokens") or 0) != int(record.get("counted_tokens") or 0)
        or attempt.get("returncode") != 0
        or attempt.get("timed_out") is not False
        or attempt.get("output_present") is not True
        or attempt.get("parse_error") is not None
    ):
        raise EvaluationStop("untraceable-or-partial-artifact", "judge attempt differs")
    return record


def run_judge_slot(
    *,
    slot: int,
    output_id: str,
    prompt: str,
    blinded_input_digest: str,
    case: Mapping[str, Any],
    environment: Mapping[str, Any],
    authorization: Mapping[str, Any],
    out_dir: Path,
    timeout: int,
) -> tuple[dict[str, Any], int, int]:
    prompt_digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    existing = existing_judge_record(out_dir, output_id, slot)
    if existing:
        if existing.get("blinded_input_digest") != blinded_input_digest or existing.get(
            "judge_prompt_sha256"
        ) != prompt_digest:
            raise EvaluationStop("judge-environment-contamination", "retained judge input differs")
        return existing, 0, 0
    parent = attempt_parent(out_dir, "judge", f"{output_id}/slot-{slot}")
    if any(parent.glob("attempt-*")):
        raise EvaluationStop(
            "untraceable-or-partial-artifact",
            f"judge attempt exists without an atomic judge record: {output_id}/slot-{slot}",
        )
    calls = 0
    counted_tokens = 0
    model = authorization["judge_model_and_reasoning"]
    for attempt_number in (1, 2):
        temp_dir = Path(
            tempfile.mkdtemp(prefix=f"attempt-{attempt_number:02d}.partial-", dir=parent)
        )
        answer_path = temp_dir / "judge-output.json"
        command = [
            "codex",
            "exec",
            "--json",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--ephemeral",
            "-s",
            "read-only",
            "-C",
            str(environment["execution_root"]),
            "--model",
            model["model_id"],
            "-c",
            f'model_reasoning_effort="{model["reasoning_effort"]}"',
            "--output-schema",
            str(JUDGE_SCHEMA),
            "-o",
            str(answer_path),
            "-",
        ]
        capture = run_streamed(
            command,
            input_text=prompt,
            cwd=Path(environment["execution_root"]),
            env=environment["env"],
            timeout=timeout,
        )
        calls += 1
        evidence = event_evidence(capture.stdout)
        tokens = token_total(evidence["usage"])
        counted_tokens += tokens
        raw_answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
        (temp_dir / "events.jsonl").write_text(capture.stdout, encoding="utf-8")
        (temp_dir / "stderr.txt").write_text(capture.stderr, encoding="utf-8")
        parse_error: str | None = None
        normalized: dict[str, Any] | None = None
        try:
            decoded = json.loads(raw_answer)
            if not isinstance(decoded, Mapping):
                raise ValueError("judge output is not an object")
            normalized = validate_judge_output(decoded, case)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            parse_error = str(exc)
        attempt = {
            "schema_version": "mindthus-beta2-judge-attempt-v0.4",
            "blinded_output_id": output_id,
            "judge_slot": slot,
            "attempt": attempt_number,
            "returncode": capture.returncode,
            "timed_out": capture.timed_out,
            "output_present": bool(raw_answer),
            "output_sha256": hashlib.sha256(raw_answer.encode("utf-8")).hexdigest(),
            "parse_error": parse_error,
            "usage": evidence["usage"],
            "counted_tokens": tokens,
            "environment_digest": environment["environment_digest"],
            "blinded_input_digest": blinded_input_digest,
            "judge_prompt_sha256": prompt_digest,
            "tool_call_count": len(evidence["loaded_commands"]),
            "tool_call_digests": [
                hashlib.sha256(command.encode("utf-8")).hexdigest()
                for command in evidence["loaded_commands"]
            ],
        }
        attempt["attempt_digest"] = canonical_sha256(attempt)
        (temp_dir / "attempt.json").write_text(
            json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        destination = parent / f"attempt-{attempt_number:02d}"
        finalize_attempt(temp_dir, destination)
        if evidence["loaded_commands"]:
            raise EvaluationStop(
                "judge-environment-contamination",
                f"judge slot {slot} used a tool for {output_id}",
            )
        if capture.returncode != 0 or capture.timed_out or normalized is None:
            if attempt_number == 1:
                continue
            attempts = [
                read_json(path)
                for path in sorted(parent.glob("attempt-*/attempt.json"))
            ]
            packet: dict[str, Any] = {
                "schema_version": "mindthus-beta2-judge-failure-packet-v0.4",
                "blinded_output_id": output_id,
                "failed_judge_slot": slot,
                "adjudicator": "William",
                "blinded_input_path": str(
                    out_dir / "judge-inputs" / f"{output_id}.json"
                ),
                "blinded_input_digest": blinded_input_digest,
                "judge_schema_sha256": sha256_file(JUDGE_SCHEMA),
                "judge_rubric_sha256": sha256_file(JUDGE_RUBRIC),
                "attempts": [
                    {
                        "attempt": item["attempt"],
                        "attempt_digest": item["attempt_digest"],
                        "returncode": item["returncode"],
                        "timed_out": item["timed_out"],
                        "output_present": item["output_present"],
                        "output_sha256": item["output_sha256"],
                        "parse_error": item["parse_error"],
                    }
                    for item in attempts
                ],
                "decision_required": (
                    "v0.4 cannot count fewer than two valid isolated Sol judge records; "
                    "William must stop or authorize a new protocol before any recovery run"
                ),
            }
            packet["packet_digest"] = canonical_sha256(packet)
            packet_path = (
                out_dir
                / "human-judge-failure-packets"
                / f"{output_id}-slot-{slot}.json"
            )
            write_atomic_json(packet_path, packet)
            raise EvaluationStop(
                "human-adjudication-required",
                f"judge slot {slot} could not produce a valid frozen-schema record; "
                f"decision packet: {packet_path}",
            )
        record: dict[str, Any] = {
            "schema_version": "mindthus-beta2-judge-record-v0.4",
            "blinded_output_id": output_id,
            "judge_slot": slot,
            "attempt": attempt_number,
            "attempt_digest": attempt["attempt_digest"],
            "environment_digest": environment["environment_digest"],
            "blinded_input_digest": blinded_input_digest,
            "judge_prompt_sha256": prompt_digest,
            "verdict": normalized,
            "usage": evidence["usage"],
            "counted_tokens": tokens,
        }
        record["record_digest"] = canonical_sha256(record)
        write_atomic_json(
            out_dir / "judge-records" / output_id / f"judge-{slot}.json", record
        )
        return record, calls, counted_tokens
    raise AssertionError("unreachable judge attempt loop")


def write_blinded_input(
    *,
    out_dir: Path,
    output_id: str,
    prompt: str,
    case: Mapping[str, Any],
    candidate: str,
) -> Path:
    contract = case["contract"]
    payload = {
        "schema_version": "mindthus-beta2-blinded-judge-input-v0.4",
        "blinded_output_id": output_id,
        "user_prompt": prompt,
        "case_contract": {
            "case_type": contract["case_type"],
            "entry_mode": contract["entry_mode"],
            "accepted_execution_owners": contract["accepted_execution_owners"],
            "expected_primitive_obligations": contract["expected_primitive_obligations"],
            "required_visible_action": contract["required_visible_action"],
            "stay_asleep_expected": contract["stay_asleep_expected"],
        },
        "candidate_final_answer": candidate,
        "arm_label_present": False,
        "generator_path_present": False,
        "runtime_telemetry_present": False,
    }
    payload["input_digest"] = canonical_sha256(payload)
    path = out_dir / "judge-inputs" / f"{output_id}.json"
    if path.is_file() and read_json(path) != payload:
        raise EvaluationStop("judge-environment-contamination", "blinded input changed")
    if not path.is_file():
        write_atomic_json(path, payload)
    return path


def judge_order(records: Iterable[Mapping[str, Any]], seed: str) -> list[Mapping[str, Any]]:
    return sorted(
        records,
        key=lambda record: hashlib.sha256(
            f"{seed}:{record['cell_id']}:judge-order-v0.4".encode("utf-8")
        ).hexdigest(),
    )


def state_payload(
    *,
    phase: str,
    status: str,
    authorization_report: Mapping[str, Any],
    generation_calls: int,
    judge_calls: int,
    counted_tokens: int,
    generation_outputs: int,
    judge_records: int,
    veto_id: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": "mindthus-beta2-real-evaluation-state-v0.4",
        "phase": phase,
        "status": status,
        "authorization_digest": authorization_report["authorization_digest"],
        "protocol_sha256": authorization_report["protocol_sha256"],
        "generation_calls": generation_calls,
        "judge_calls": judge_calls,
        "counted_tokens": counted_tokens,
        "completed_generation_outputs": generation_outputs,
        "completed_judge_records": judge_records,
        "veto_id": veto_id,
        "reason": reason,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    payload["state_digest"] = canonical_sha256(payload)
    return payload


def run_evaluation(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    scan_partial_artifacts(out_dir)
    auth_report, authorization, protocol = authorized_context(args.authorization.resolve())
    manifests = verify_arm_set(args.arm_manifest, authorization)
    matrix = read_json(MATRIX_PATH)
    cases = source_cases(matrix)
    cells = expected_cells(protocol, args.phase)
    if not set(cell["case_id"] for cell in cells).issubset(cases):
        raise EvaluationStop("protocol-or-arm-drift", "one or more case sources are unavailable")
    prior_state_path = out_dir / "run-state.json"
    generation_calls, judge_calls, counted_tokens = observed_attempt_usage(out_dir)
    completed_records: list[dict[str, Any]] = []
    for cell in cells:
        case = cases[cell["case_id"]]
        manifest = manifests[cell["arm_id"]]
        forbidden_paths = {
            str(out_dir),
            str(MATRIX_PATH.resolve()),
            str(DEVELOPMENT_CASES.resolve()),
            str(PUBLIC_CASES.resolve()),
            str(JUDGE_SCHEMA.resolve()),
            str(JUDGE_RUBRIC.resolve()),
        }
        for other_arm, other_manifest in manifests.items():
            if other_arm == cell["arm_id"]:
                continue
            forbidden_paths.update(
                {
                    str(Path(other_manifest["host"]["home"]).resolve()),
                    str(Path(other_manifest["host"]["execution_root"]).resolve()),
                    str(Path(other_manifest["package"]["root"]).resolve()),
                }
            )
        record, new_calls, new_tokens = execute_generator_cell(
            cell=cell,
            case=case,
            manifest=manifest,
            authorization=authorization,
            protocol_sha256=auth_report["protocol_sha256"],
            out_dir=out_dir,
            timeout=args.timeout,
            generation_calls_used=generation_calls,
            forbidden_path_fragments=sorted(forbidden_paths),
        )
        generation_calls += new_calls
        counted_tokens += new_tokens
        completed_records.append(record)
        if counted_tokens > authorization["token_or_cost_budget"]["maximum"]:
            raise EvaluationStop("authority-or-evidence-regression", "v0.4 token ceiling reached")
        write_atomic_json(
            prior_state_path,
            state_payload(
                phase=args.phase,
                status="generating",
                authorization_report=auth_report,
                generation_calls=generation_calls,
                judge_calls=judge_calls,
                counted_tokens=counted_tokens,
                generation_outputs=len(completed_records),
                judge_records=0,
            ),
        )

    auth_source = args.auth_source.resolve()
    if not auth_source.is_file():
        raise EvaluationStop("judge-environment-contamination", "Codex auth source is unavailable")
    environments = {
        slot: judge_environment(
            out_dir=out_dir,
            runtime_root=args.runtime_root.resolve(),
            auth_source=auth_source,
            slot=slot,
        )
        for slot in (1, 2)
    }
    rubric = read_json(JUDGE_RUBRIC)
    completed_judges = 0
    seed = str(protocol["execution_design"]["order_seed_sha256"])
    for record in judge_order(completed_records, seed):
        cell_id = str(record["cell_id"])
        key = record["cell_key"]
        case = cases[str(key["case_id"])]
        candidate = Path(record["answer_path"]).read_text(encoding="utf-8")
        sensitive_paths = {
            str(out_dir),
            *(
                str(Path(manifest[section][field]).resolve())
                for manifest in manifests.values()
                for section, field in (
                    ("host", "home"),
                    ("host", "execution_root"),
                    ("package", "root"),
                )
            ),
        }
        if FORBIDDEN_BLINDING_LABEL.search(candidate) or any(
            path in candidate for path in sensitive_paths
        ):
            raise EvaluationStop(
                "judge-environment-contamination",
                f"candidate {cell_id} exposes an arm label or generator path",
            )
        raw_prompt = user_prompt(case["source"])
        output_id = judge_identity(auth_report["protocol_sha256"], cell_id)
        blinded_input_path = write_blinded_input(
            out_dir=out_dir,
            output_id=output_id,
            prompt=raw_prompt,
            case=case,
            candidate=candidate,
        )
        blinded_input_digest = str(read_json(blinded_input_path)["input_digest"])
        prompt = judge_prompt(
            rubric=rubric,
            case=case,
            prompt=raw_prompt,
            candidate=candidate,
            blinded_output_id=output_id,
        )
        needed = sum(
            existing_judge_record(out_dir, output_id, slot) is None for slot in (1, 2)
        )
        if judge_calls + (2 * needed) > authorization["maximum_judge_calls"]:
            raise EvaluationStop("authority-or-evidence-regression", "judge call ceiling reached")
        futures: list[concurrent.futures.Future[tuple[dict[str, Any], int, int]]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            for slot in (1, 2):
                futures.append(
                    executor.submit(
                        run_judge_slot,
                        slot=slot,
                        output_id=output_id,
                        prompt=prompt,
                        blinded_input_digest=blinded_input_digest,
                        case=case,
                        environment=environments[slot],
                        authorization=authorization,
                        out_dir=out_dir,
                        timeout=args.timeout,
                    )
                )
            results = [future.result() for future in futures]
        for _judge_record, new_calls, new_tokens in results:
            judge_calls += new_calls
            counted_tokens += new_tokens
        completed_judges += 2
        if counted_tokens > authorization["token_or_cost_budget"]["maximum"]:
            raise EvaluationStop("authority-or-evidence-regression", "v0.4 token ceiling reached")
        write_atomic_json(
            prior_state_path,
            state_payload(
                phase=args.phase,
                status="judging",
                authorization_report=auth_report,
                generation_calls=generation_calls,
                judge_calls=judge_calls,
                counted_tokens=counted_tokens,
                generation_outputs=len(completed_records),
                judge_records=completed_judges,
            ),
        )

    analysis = run_json(
        [
            "python3",
            str(ANALYZER),
            "--phase",
            args.phase,
            "--run-dir",
            str(out_dir),
            "--authorization",
            str(args.authorization.resolve()),
        ],
        label=f"{args.phase} analysis",
    )
    status = str(analysis["status"])
    write_atomic_json(
        prior_state_path,
        state_payload(
            phase=args.phase,
            status=status,
            authorization_report=auth_report,
            generation_calls=generation_calls,
            judge_calls=judge_calls,
            counted_tokens=counted_tokens,
            generation_outputs=len(completed_records),
            judge_records=completed_judges,
            veto_id=analysis.get("veto_id"),
            reason=analysis.get("reason"),
        ),
    )
    return analysis, 0 if status in {"passed", "matched-complete"} else 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("smoke", "matched"), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--arm-manifest", type=Path, action="append", required=True)
    parser.add_argument("--authorization", type=Path, default=DEFAULT_AUTHORIZATION)
    parser.add_argument("--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json")
    parser.add_argument("--timeout", type=int, default=900)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, code = run_evaluation(args)
    except EvaluationStop as exc:
        report = {"status": "stopped", "veto_id": exc.veto_id, "reason": exc.reason}
        code = 2
        if args.out_dir.exists():
            write_atomic_json(args.out_dir / "stop-report.json", report)
    except (OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
