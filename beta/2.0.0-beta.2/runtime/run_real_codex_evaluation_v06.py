#!/usr/bin/env python3
"""Run the fresh, bounded Mindthus Beta route-decision evaluation v0.6.

One batch generates the three frozen arms, sends all three opaque candidates to two
independent paired Judges, and appends one hash-chained commit.  Finalized attempts are
promoted before any new model call, so interruption and adjudication resume from
artifacts rather than from a mutable usage snapshot.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence


BETA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BETA_ROOT.parents[1]
RUNTIME_ROOT = BETA_ROOT / "runtime"
CORE_PATH = RUNTIME_ROOT / "decision_evaluation_v06.py"
V04_PATH = RUNTIME_ROOT / "run_real_codex_evaluation_v04.py"
ISOLATION_PATH = RUNTIME_ROOT / "filesystem_isolation_v05.py"
ARM_LABEL = re.compile(
    r"\b(?:direct-only|thin-kernel|stable\s+arm|mindthus\s+beta)\b|"
    r"mindthus-beta@mindthus-beta|mindthus@mindthus|2\.0\.0-beta\.1|"
    r"(?<![\d.])1\.4\.6(?![\d.])",
    re.IGNORECASE,
)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CORE = _load("mindthus_beta2_decision_v06", CORE_PATH)
V04 = _load("mindthus_beta2_runner_v04_low_level", V04_PATH)
ISO = _load("mindthus_beta2_isolation_v05_low_level", ISOLATION_PATH)


class RunStop(RuntimeError):
    def __init__(self, code: str, reason: str):
        super().__init__(reason)
        self.code = code
        self.reason = reason


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    CORE.write_atomic_json(path, payload)


def _verify_or_write(path: Path, payload: Mapping[str, Any], label: str) -> None:
    if path.is_file():
        if _read(path) != payload:
            raise RunStop("artifact-corruption", f"retained {label} differs")
    else:
        _write(path, payload)


def _existing_file(root: Path) -> Path:
    if root.is_file():
        return root.resolve()
    for path in sorted(root.rglob("*"), key=str):
        if path.is_file() and not path.is_symlink():
            return path.resolve()
    raise RunStop("arm-drift", f"probe root contains no regular file: {root}")


def _case_prompt(contract: Mapping[str, Any]) -> str:
    prompt = contract["prompt"]
    return V04.user_prompt({"prompt": prompt}) if isinstance(prompt, str) else V04.user_prompt({"turns": prompt})


def _generator_prompt(prompt: str) -> str:
    return CORE.generator_prompt(prompt)


def _manifests(protocol: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for receipt in protocol["arms"]:
        manifest = _read(Path(receipt["path"]))
        if (
            manifest.get("arm_id") != receipt["arm_id"]
            or manifest.get("identity_digest") != receipt["identity_digest"]
            or manifest.get("model") != {"id": "gpt-5.6-sol", "reasoning": "xhigh"}
        ):
            raise RunStop("arm-drift", f"sealed arm differs: {receipt['arm_id']}")
        result[str(receipt["arm_id"])] = manifest
    if set(result) != set(CORE.ARM_IDS):
        raise RunStop("arm-drift", "sealed arm set is incomplete")
    return result


def _judge_environment(out_dir: Path, runtime_root: Path, auth_source: Path, slot: int) -> dict[str, Any]:
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
        raise RunStop("judge-environment-contamination", "Judge auth binding differs")
    env = os.environ.copy()
    env.update({"CODEX_HOME": str(codex_home), "HOME": str(process_home)})
    probe = subprocess.run(
        ["codex", "plugin", "list", "--json"],
        cwd=execution_root,
        env=env,
        text=True,
        capture_output=True,
    )
    if probe.returncode != 0:
        raise RunStop("judge-environment-contamination", "cannot inspect Judge plugin inventory")
    try:
        inventory = json.loads(probe.stdout)
    except json.JSONDecodeError as exc:
        raise RunStop("judge-environment-contamination", "Judge plugin inventory is invalid") from exc
    serialized = json.dumps(inventory, ensure_ascii=False).lower()
    if "mindthus" in serialized or "superpowers" in serialized:
        raise RunStop("judge-environment-contamination", "Judge has a forbidden plugin")
    receipt: dict[str, Any] = {
        "schema_version": "mindthus-beta2-paired-judge-environment-v0.6",
        "judge_slot": slot,
        "codex_home": str(codex_home.resolve()),
        "execution_root": str(execution_root.resolve()),
        "plugin_inventory_sha256": CORE.canonical_sha256(inventory),
        "active_forbidden_plugins": [],
        "generator_home_access_granted": False,
        "auth_source_path_sha256": CORE.sha256_text(str(auth_source.resolve())),
    }
    receipt["environment_digest"] = CORE.canonical_sha256(receipt)
    _verify_or_write(root / "environment.json", receipt, "Judge environment")
    return {**receipt, "env": env}


def _semantic_profile(
    *,
    role: str,
    identifier: str,
    attempt: int,
    slot: int | None,
    answer_path: Path,
    cwd: Path,
    env: Mapping[str, str],
    command: Sequence[str],
    out_dir: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    auth_source: Path,
) -> tuple[list[str], dict[str, Any]]:
    suffix = f"slot-{slot}/" if slot is not None else ""
    receipt_path = out_dir / "isolation-receipts" / role / identifier / suffix / f"attempt-{attempt:02d}.json"
    profile_path = receipt_path.with_suffix(".sb")
    codex_home = Path(str(env["CODEX_HOME"])).resolve()
    process_home = Path(str(env["HOME"])).resolve()
    answer_root = answer_path.parent.resolve()
    answer_root.mkdir(parents=True, exist_ok=True)
    own_manifest = next(
        (
            manifest
            for manifest in manifests.values()
            if Path(manifest["host"]["home"]).resolve() == codex_home
        ),
        None,
    )
    allowed_read = [cwd.resolve(), codex_home, process_home, answer_root]
    allowed_write = [codex_home, process_home, answer_root]
    if own_manifest is not None:
        allowed_read.append(Path(own_manifest["package"]["root"]).resolve())
    allowed_files = [auth_source.resolve()]
    if role == "judge":
        allowed_files.append(CORE.JUDGE_SCHEMA_PATH.resolve())

    control = out_dir / "control" / "semantic-access-denied.txt"
    control.parent.mkdir(parents=True, exist_ok=True)
    if not control.is_file():
        control.write_text("semantic model access forbidden\n", encoding="utf-8")
    forbidden = [
        CORE.MATRIX_PATH.resolve(),
        CORE.JUDGE_RUBRIC_PATH.resolve(),
        control.resolve(),
    ]
    forbidden.extend(_existing_file(Path(item["package"]["root"])) for item in manifests.values())
    forbidden = [
        path
        for path in forbidden
        if path not in allowed_files
        and not any(path.is_relative_to(root) for root in allowed_read)
    ]
    sentinel = answer_root / ".v06-positive-probe"
    sentinel.write_text("v0.6 isolation positive probe\n", encoding="utf-8")
    positives = [sentinel]
    if own_manifest is not None:
        positives.append(_existing_file(Path(own_manifest["package"]["root"])))
    try:
        base = ISO.prepare_verified_profile(
            profile_path=profile_path,
            receipt_path=receipt_path,
            protected_roots=[
                Path("/Volumes/Data"),
                Path.home().resolve(),
                out_dir.resolve(),
                *[
                    Path(item["host"]["home"]).resolve().parent
                    for item in manifests.values()
                ],
            ],
            allowed_read_roots=allowed_read,
            allowed_write_roots=allowed_write,
            allowed_read_files=allowed_files,
            probe_root=answer_root,
            allowed_targets=positives,
            forbidden_targets=forbidden,
        )
    except ISO.IsolationError as exc:
        raise RunStop("isolation-failure", str(exc)) from exc
    runtime_probe = subprocess.run(
        ISO.sandboxed_command(profile_path, ["codex", "--version"]),
        cwd=cwd,
        env=dict(env),
        text=True,
        capture_output=True,
    )
    if runtime_probe.returncode != 0 or runtime_probe.stdout.strip() != CORE.EXPECTED_CODEX_VERSION:
        raise RunStop("isolation-failure", "Codex cannot start under the exact sandbox profile")
    bound = ISO.sandboxed_command(profile_path, command)
    receipt = {
        **{key: value for key, value in base.items() if key != "receipt_digest"},
        "role": role,
        "execution_identifier": identifier,
        "attempt": attempt,
        "judge_slot": slot,
        "sandboxed_command_sha256": CORE.canonical_sha256(list(map(str, bound))),
        "sandboxed_runtime_probe": {
            "returncode": runtime_probe.returncode,
            "stdout_sha256": CORE.sha256_text(runtime_probe.stdout),
            "stderr_sha256": CORE.sha256_text(runtime_probe.stderr),
            "model_execution_performed": False,
        },
        "semantic_process_profile_applied": True,
    }
    receipt["receipt_digest"] = CORE.canonical_sha256(receipt)
    _write(receipt_path, receipt)
    return bound, {
        "path": str(receipt_path.resolve()),
        "receipt_digest": receipt["receipt_digest"],
    }


def _observed_read_failure(stdout: str) -> bool:
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") if isinstance(event, Mapping) else None
        if not isinstance(item, Mapping) or item.get("type") != "command_execution":
            continue
        command = str(item.get("command") or "").lower()
        status = str(item.get("status") or event.get("status") or "").lower()
        if "skill.md" in command and status in {"failed", "error"}:
            return True
    return False


def _usage_total(usage: Mapping[str, Any] | None) -> int:
    return V04.token_total(usage)


def _budget_check(
    authorization: Mapping[str, Any], out_dir: Path, *, reserve_calls: int = 0
) -> dict[str, int]:
    usage = CORE.attempt_usage(out_dir)
    if (
        usage["generation_calls"] > authorization["maximum_generation_calls"]
        or usage["paired_judge_calls"] > authorization["maximum_paired_judge_calls"]
        or usage["counted_tokens"] > authorization["maximum_counted_tokens"]
    ):
        raise RunStop("budget-exceeded", "v0.6 authorization ceiling reached")
    if (
        usage["counted_tokens"]
        + reserve_calls * int(authorization["maximum_counted_tokens_per_call"])
        > authorization["maximum_counted_tokens"]
    ):
        raise RunStop(
            "budget-exceeded",
            "remaining token budget cannot cover the frozen per-call maximum",
        )
    return usage


def _next_attempt(parent: Path, role: str) -> int:
    attempts = sorted(parent.glob("attempt-*/attempt.json"))
    for index, path in enumerate(attempts, 1):
        if path.parent.name != f"attempt-{index:02d}":
            raise RunStop("artifact-corruption", f"{role} attempt sequence differs")
        attempt = CORE.validate_attempt(path, role=role)
        semantic = bool(attempt.get("answer_present") if role == "generation" else attempt.get("output_present"))
        successful = (
            attempt.get("returncode") == 0
            and attempt.get("timed_out") is False
            and semantic
            and (role == "generation" or attempt.get("parse_error") is None)
        )
        if successful:
            if index != len(attempts):
                raise RunStop("artifact-corruption", f"{role} has attempts after success")
            return 0
        if semantic or int(attempt.get("counted_tokens") or 0) != 0:
            raise RunStop("experiment-invalid", f"{role} failed after semantic output or token use")
    if len(attempts) >= 2:
        raise RunStop("experiment-invalid", f"{role} zero-token infrastructure retry failed")
    return len(attempts) + 1


def _generator_command(
    manifest: Mapping[str, Any], answer_path: Path
) -> tuple[list[str], dict[str, str], Path]:
    execution_root = Path(manifest["host"]["execution_root"]).resolve()
    codex_home = Path(manifest["host"]["home"]).resolve()
    process_home = codex_home.parent / "process-home"
    process_home.mkdir(parents=True, exist_ok=True)
    command = [
        "codex",
        "exec",
        "--json",
        "--strict-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(execution_root),
        "-s",
        "read-only",
        "--ephemeral",
        "--model",
        "gpt-5.6-sol",
        "-c",
        'model_reasoning_effort="xhigh"',
        "-c",
        f"model_context_window={CORE.MAX_COUNTED_TOKENS_PER_CALL}",
        "-o",
        str(answer_path),
    ]
    if manifest["arm_id"] == "thin-kernel":
        command.append("--dangerously-bypass-hook-trust")
    command.append("-")
    env = os.environ.copy()
    env.update({"CODEX_HOME": str(codex_home), "HOME": str(process_home)})
    return command, env, execution_root


def _run_generation_attempt(
    *,
    protocol_sha256: str,
    batch: Mapping[str, Any],
    cell: Mapping[str, Any],
    arm_receipt: Mapping[str, Any],
    manifest: Mapping[str, Any],
    contract: Mapping[str, Any],
    out_dir: Path,
    auth_source: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    attempt_number: int,
    timeout: int,
) -> None:
    cell_id, key = CORE.cell_identity(
        protocol_sha256=protocol_sha256,
        batch=batch,
        arm=arm_receipt,
        contract=contract,
    )
    parent = out_dir / "generation-attempts" / cell_id
    parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f"attempt-{attempt_number:02d}.partial-", dir=parent))
    answer_path = temp / "answer.txt"
    command, env, cwd = _generator_command(manifest, answer_path)
    bound, isolation = _semantic_profile(
        role="generation",
        identifier=cell_id,
        attempt=attempt_number,
        slot=None,
        answer_path=answer_path,
        cwd=cwd,
        env=env,
        command=command,
        out_dir=out_dir,
        manifests=manifests,
        auth_source=auth_source,
    )
    prompt = _generator_prompt(_case_prompt(contract))
    started = _now()
    capture = V04.run_streamed(bound, input_text=prompt, cwd=cwd, env=env, timeout=timeout)
    evidence = V04.event_evidence(capture.stdout)
    answer = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    if not answer and evidence["agent_messages"]:
        answer = str(evidence["agent_messages"][-1])
        answer_path.write_text(answer, encoding="utf-8")
    (temp / "events.jsonl").write_text(capture.stdout, encoding="utf-8")
    (temp / "stderr.txt").write_text(capture.stderr, encoding="utf-8")
    telemetry: dict[str, Any] | None = None
    telemetry_error: str | None = None
    skill_hops: list[str] = []
    if capture.returncode == 0 and not capture.timed_out and answer:
        raw_turn = {
            "usage": evidence["usage"],
            "duration_seconds": capture.wall_time_seconds,
            "first_observable_action_latency_seconds": (
                capture.first_observable_action["offset_seconds"]
                if capture.first_observable_action
                else None
            ),
            "native_telemetry": dict(evidence["native_telemetry"]),
            "loaded_commands": evidence["loaded_commands"],
            "answer": answer,
            "agent_messages": evidence["agent_messages"],
            "returncode": capture.returncode,
            "timed_out": capture.timed_out,
        }
        required = dict(V04.V04_REQUIRED_EVIDENCE)
        required.pop("first_observable_action_latency_seconds", None)
        if manifest["arm_id"] == "thin-kernel":
            required["arm.hook_observation_receipt"] = ("deterministic",)
        try:
            telemetry = V04.build_turn_telemetry(
                raw_turn,
                context={
                    "case_id": batch["case_id"],
                    "turn_index": 1,
                    "entry_mode": contract["entry_mode"],
                    "execution_root": manifest["host"]["execution_root"],
                    "allowed_roots": [
                        manifest["package"]["root"],
                        manifest["host"]["execution_root"],
                    ],
                    "arm_manifest": manifest,
                    "attempt": attempt_number,
                },
                required_evidence=required,
            )
            skill_hops = list(telemetry["measurements"]["skill_hops"]["value"])
        except (KeyError, TypeError, ValueError, RuntimeError) as exc:
            telemetry_error = str(exc)
    usage = evidence["usage"]
    attempt: dict[str, Any] = {
        "schema_version": CORE.GENERATION_ATTEMPT_SCHEMA,
        "batch_id": batch["batch_id"],
        "cell_id": cell_id,
        "cell_key": key,
        "arm_id": cell["arm_id"],
        "attempt": attempt_number,
        "started_at_utc": started,
        "completed_at_utc": _now(),
        "returncode": capture.returncode,
        "timed_out": capture.timed_out,
        "wall_time_seconds": capture.wall_time_seconds,
        "first_observable_action": capture.first_observable_action,
        "answer_present": bool(answer),
        "answer_sha256": CORE.sha256_text(answer),
        "events_sha256": CORE.sha256_text(capture.stdout),
        "stderr_sha256": CORE.sha256_text(capture.stderr),
        "usage": usage,
        "counted_tokens": _usage_total(usage),
        "skill_hops": skill_hops,
        "observed_resource_read_failure": _observed_read_failure(capture.stdout),
        "telemetry": telemetry,
        "telemetry_error": telemetry_error,
        "isolation_receipt": isolation,
    }
    attempt["attempt_digest"] = CORE.canonical_sha256(attempt)
    (temp / "attempt.json").write_text(json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    destination = parent / f"attempt-{attempt_number:02d}"
    if destination.exists():
        raise RunStop("artifact-corruption", "generation attempt destination exists")
    os.replace(temp, destination)


def _promote_generation(
    *,
    protocol_sha256: str,
    batch: Mapping[str, Any],
    cell: Mapping[str, Any],
    arm_receipt: Mapping[str, Any],
    contract: Mapping[str, Any],
    out_dir: Path,
) -> dict[str, Any] | None:
    cell_id, key = CORE.cell_identity(
        protocol_sha256=protocol_sha256,
        batch=batch,
        arm=arm_receipt,
        contract=contract,
    )
    record_path = out_dir / "cells" / cell_id / "record.json"
    if record_path.is_file():
        record = CORE.validate_cell_record(
            record_path,
            out_dir=out_dir,
            expected_batch=batch,
            expected_arm_id=str(cell["arm_id"]),
        )
        if record.get("cell_key") != key:
            raise RunStop("artifact-corruption", "retained generation identity differs")
        return record
    parent = out_dir / "generation-attempts" / cell_id
    next_number = _next_attempt(parent, "generation") if parent.exists() else 1
    if next_number != 0:
        return None
    attempt_path = sorted(parent.glob("attempt-*/attempt.json"))[-1]
    attempt = CORE.validate_attempt(attempt_path, role="generation")
    answer_path = attempt_path.parent / "answer.txt"
    if not answer_path.is_file() or CORE.sha256_text(answer_path.read_text(encoding="utf-8")) != attempt["answer_sha256"]:
        raise RunStop("artifact-corruption", "promotable generation answer differs")
    telemetry = attempt.get("telemetry")
    if not isinstance(telemetry, Mapping) or telemetry.get("evidence_gate", {}).get("status") != "pass":
        raise RunStop("experiment-invalid", "promotable Generator evidence differs")
    record: dict[str, Any] = {
        "schema_version": CORE.CELL_SCHEMA,
        "cell_id": cell_id,
        "cell_key": key,
        "batch_id": batch["batch_id"],
        "batch_index": batch["batch_index"],
        "case_id": batch["case_id"],
        "repeat": batch["repeat"],
        "arm_id": cell["arm_id"],
        "case_contract_digest": CORE.canonical_sha256(contract),
        "generation_attempt": {
            "attempt": attempt["attempt"],
            "attempt_digest": attempt["attempt_digest"],
            "path": str(attempt_path.parent.resolve()),
        },
        "answer_path": str(answer_path.resolve()),
        "answer_sha256": attempt["answer_sha256"],
        "usage": attempt["usage"],
        "counted_tokens": attempt["counted_tokens"],
        "wall_time_seconds": attempt["wall_time_seconds"],
        "first_observable_action": attempt["first_observable_action"],
        "skill_hops": attempt["skill_hops"],
        "observed_resource_read_failure": attempt["observed_resource_read_failure"],
        "telemetry_digest": CORE.canonical_sha256(telemetry),
    }
    record["record_digest"] = CORE.canonical_sha256(record)
    _write(record_path, record)
    return CORE.validate_cell_record(
        record_path,
        out_dir=out_dir,
        expected_batch=batch,
        expected_arm_id=str(cell["arm_id"]),
    )


def _judge_command(answer_path: Path, environment: Mapping[str, Any]) -> list[str]:
    return [
        "codex",
        "exec",
        "--json",
        "--strict-config",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--ephemeral",
        "-s",
        "read-only",
        "-C",
        str(environment["execution_root"]),
        "--model",
        "gpt-5.6-sol",
        "-c",
        'model_reasoning_effort="xhigh"',
        "-c",
        f"model_context_window={CORE.MAX_COUNTED_TOKENS_PER_CALL}",
        "--output-schema",
        str(CORE.JUDGE_SCHEMA_PATH.resolve()),
        "-o",
        str(answer_path),
        "-",
    ]


def _judge_input(
    *,
    protocol_sha256: str,
    batch: Mapping[str, Any],
    contract: Mapping[str, Any],
    cells: Sequence[Mapping[str, Any]],
    out_dir: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    slot: int,
) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    answers = {
        str(cell["cell_id"]): Path(cell["answer_path"]).read_text(encoding="utf-8")
        for cell in cells
    }
    if any(ARM_LABEL.search(answer) for answer in answers.values()):
        raise RunStop("blinding-failure", "candidate answer exposes an experiment arm label")
    sensitive = sorted(
        {
            str(Path(manifest[section][field]).resolve())
            for manifest in manifests.values()
            for section, field in (
                ("host", "home"),
                ("host", "execution_root"),
                ("package", "root"),
            )
        }
    )
    payload, receipt = CORE.build_blinded_input(
        protocol_sha256=protocol_sha256,
        batch=batch,
        contract=contract,
        prompt=_case_prompt(contract),
        cells=cells,
        answers=answers,
        slot=slot,
        sensitive_paths=sensitive,
        observed_read_failures={
            str(cell["cell_id"]): bool(cell["observed_resource_read_failure"])
            for cell in cells
        },
    )
    root = out_dir / "paired-judge-inputs" / str(batch["batch_id"])
    input_path = root / f"slot-{slot}.input.json"
    receipt_path = root / f"slot-{slot}.receipt.json"
    _verify_or_write(input_path, payload, "paired Judge input")
    _verify_or_write(receipt_path, receipt, "paired Judge blinding receipt")
    return payload, receipt, input_path, receipt_path


def _run_judge_attempt(
    *,
    batch: Mapping[str, Any],
    contract: Mapping[str, Any],
    payload: Mapping[str, Any],
    receipt: Mapping[str, Any],
    receipt_path: Path,
    environment: Mapping[str, Any],
    out_dir: Path,
    auth_source: Path,
    manifests: Mapping[str, Mapping[str, Any]],
    slot: int,
    attempt_number: int,
    timeout: int,
) -> None:
    parent = out_dir / "paired-judge-attempts" / str(batch["batch_id"]) / f"slot-{slot}"
    parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f"attempt-{attempt_number:02d}.partial-", dir=parent))
    answer_path = temp / "judge-output.json"
    command = _judge_command(answer_path, environment)
    bound, isolation = _semantic_profile(
        role="judge",
        identifier=str(batch["batch_id"]),
        attempt=attempt_number,
        slot=slot,
        answer_path=answer_path,
        cwd=Path(environment["execution_root"]),
        env=environment["env"],
        command=command,
        out_dir=out_dir,
        manifests=manifests,
        auth_source=auth_source,
    )
    prompt = CORE.paired_judge_prompt(payload)
    started = _now()
    capture = V04.run_streamed(
        bound,
        input_text=prompt,
        cwd=Path(environment["execution_root"]),
        env=environment["env"],
        timeout=timeout,
    )
    evidence = V04.event_evidence(capture.stdout)
    raw = answer_path.read_text(encoding="utf-8") if answer_path.is_file() else ""
    (temp / "events.jsonl").write_text(capture.stdout, encoding="utf-8")
    (temp / "stderr.txt").write_text(capture.stderr, encoding="utf-8")
    parse_error: str | None = None
    if raw:
        try:
            decoded = json.loads(raw)
            if not isinstance(decoded, Mapping):
                raise CORE.DecisionError("judge-schema-failure", "paired Judge output is not an object")
            CORE.validate_paired_judge_output(
                decoded,
                batch_id=str(batch["batch_id"]),
                candidate_ids=[item["candidate_id"] for item in payload["candidates"]],
                contract=contract,
            )
        except (json.JSONDecodeError, CORE.DecisionError) as exc:
            parse_error = str(exc)
    if evidence["loaded_commands"]:
        parse_error = "paired Judge used a forbidden tool"
    usage = evidence["usage"]
    attempt: dict[str, Any] = {
        "schema_version": CORE.JUDGE_ATTEMPT_SCHEMA,
        "batch_id": batch["batch_id"],
        "judge_slot": slot,
        "attempt": attempt_number,
        "started_at_utc": started,
        "completed_at_utc": _now(),
        "returncode": capture.returncode,
        "timed_out": capture.timed_out,
        "output_present": bool(raw),
        "output_sha256": CORE.sha256_text(raw),
        "parse_error": parse_error,
        "usage": usage,
        "counted_tokens": _usage_total(usage),
        "environment_digest": environment["environment_digest"],
        "blinded_input_digest": payload["input_digest"],
        "blinding_receipt_digest": receipt["receipt_digest"],
        "judge_prompt_sha256": CORE.sha256_text(prompt),
        "tool_call_count": len(evidence["loaded_commands"]),
        "isolation_receipt": isolation,
    }
    attempt["attempt_digest"] = CORE.canonical_sha256(attempt)
    (temp / "attempt.json").write_text(json.dumps(attempt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    destination = parent / f"attempt-{attempt_number:02d}"
    if destination.exists():
        raise RunStop("artifact-corruption", "paired Judge attempt destination exists")
    os.replace(temp, destination)


def _promote_judge(
    *,
    batch: Mapping[str, Any],
    contract: Mapping[str, Any],
    payload: Mapping[str, Any],
    receipt: Mapping[str, Any],
    receipt_path: Path,
    environment: Mapping[str, Any],
    out_dir: Path,
    slot: int,
) -> dict[str, Any] | None:
    record_path = out_dir / "paired-judge-records" / str(batch["batch_id"]) / f"slot-{slot}.json"
    candidate_ids = [item["candidate_id"] for item in payload["candidates"]]
    if record_path.is_file():
        return CORE.validate_judge_record(
            record_path,
            out_dir=out_dir,
            batch=batch,
            contract=contract,
            candidate_ids=candidate_ids,
            slot=slot,
        )
    parent = out_dir / "paired-judge-attempts" / str(batch["batch_id"]) / f"slot-{slot}"
    next_number = _next_attempt(parent, "judge") if parent.exists() else 1
    if next_number != 0:
        return None
    attempt_path = sorted(parent.glob("attempt-*/attempt.json"))[-1]
    attempt = CORE.validate_attempt(attempt_path, role="judge")
    output_path = attempt_path.parent / "judge-output.json"
    if not output_path.is_file() or CORE.sha256_text(output_path.read_text(encoding="utf-8")) != attempt["output_sha256"]:
        raise RunStop("artifact-corruption", "promotable paired Judge output differs")
    decoded = _read(output_path)
    normalized = CORE.validate_paired_judge_output(
        decoded,
        batch_id=str(batch["batch_id"]),
        candidate_ids=candidate_ids,
        contract=contract,
    )
    if normalized["batch_id"] != decoded["batch_id"]:
        raise RunStop("artifact-corruption", "promotable paired Judge batch differs")
    record: dict[str, Any] = {
        "schema_version": CORE.JUDGE_RECORD_SCHEMA,
        "batch_id": batch["batch_id"],
        "judge_slot": slot,
        "judge_attempt": {
            "attempt": attempt["attempt"],
            "attempt_digest": attempt["attempt_digest"],
            "path": str(attempt_path.parent.resolve()),
        },
        "environment_digest": environment["environment_digest"],
        "blinded_input_digest": payload["input_digest"],
        "judge_prompt_sha256": attempt["judge_prompt_sha256"],
        "blinding_receipt": {
            "path": str(receipt_path.resolve()),
            "receipt_digest": receipt["receipt_digest"],
        },
        "verdict": decoded,
        "usage": attempt["usage"],
        "counted_tokens": attempt["counted_tokens"],
    }
    record["record_digest"] = CORE.canonical_sha256(record)
    _write(record_path, record)
    return CORE.validate_judge_record(
        record_path,
        out_dir=out_dir,
        batch=batch,
        contract=contract,
        candidate_ids=candidate_ids,
        slot=slot,
    )


def _run_missing_generators(
    *,
    authorization: Mapping[str, Any],
    protocol: Mapping[str, Any],
    protocol_sha256: str,
    batch: Mapping[str, Any],
    contract: Mapping[str, Any],
    manifests: Mapping[str, Mapping[str, Any]],
    out_dir: Path,
    auth_source: Path,
    timeout: int,
) -> list[dict[str, Any]]:
    arm_receipts = {item["arm_id"]: item for item in protocol["arms"]}
    records: dict[str, dict[str, Any]] = {}
    pending: list[tuple[Mapping[str, Any], int]] = []
    for cell in batch["cells"]:
        record = _promote_generation(
            protocol_sha256=protocol_sha256,
            batch=batch,
            cell=cell,
            arm_receipt=arm_receipts[cell["arm_id"]],
            contract=contract,
            out_dir=out_dir,
        )
        if record is not None:
            records[str(cell["arm_id"])] = record
            continue
        cell_id, _ = CORE.cell_identity(
            protocol_sha256=protocol_sha256,
            batch=batch,
            arm=arm_receipts[cell["arm_id"]],
            contract=contract,
        )
        parent = out_dir / "generation-attempts" / cell_id
        pending.append((cell, _next_attempt(parent, "generation") if parent.exists() else 1))
    usage = _budget_check(authorization, out_dir, reserve_calls=len(pending))
    if usage["generation_calls"] + len(pending) > authorization["maximum_generation_calls"]:
        raise RunStop("budget-exceeded", "insufficient Generator call budget for next batch")
    if pending:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(pending)) as executor:
            futures = [
                executor.submit(
                    _run_generation_attempt,
                    protocol_sha256=protocol_sha256,
                    batch=batch,
                    cell=cell,
                    arm_receipt=arm_receipts[cell["arm_id"]],
                    manifest=manifests[cell["arm_id"]],
                    contract=contract,
                    out_dir=out_dir,
                    auth_source=auth_source,
                    manifests=manifests,
                    attempt_number=attempt_number,
                    timeout=timeout,
                )
                for cell, attempt_number in pending
            ]
            for future in futures:
                future.result()
    # Promotion is zero-model.  Only proven zero-output/zero-token failures may retry.
    for cell in batch["cells"]:
        arm_id = str(cell["arm_id"])
        if arm_id in records:
            continue
        record = _promote_generation(
            protocol_sha256=protocol_sha256,
            batch=batch,
            cell=cell,
            arm_receipt=arm_receipts[arm_id],
            contract=contract,
            out_dir=out_dir,
        )
        if record is None:
            usage = _budget_check(authorization, out_dir, reserve_calls=1)
            if usage["generation_calls"] >= authorization["maximum_generation_calls"]:
                raise RunStop("budget-exceeded", "Generator retry headroom is exhausted")
            cell_id, _ = CORE.cell_identity(
                protocol_sha256=protocol_sha256,
                batch=batch,
                arm=arm_receipts[arm_id],
                contract=contract,
            )
            attempt_number = _next_attempt(out_dir / "generation-attempts" / cell_id, "generation")
            _run_generation_attempt(
                protocol_sha256=protocol_sha256,
                batch=batch,
                cell=cell,
                arm_receipt=arm_receipts[arm_id],
                manifest=manifests[arm_id],
                contract=contract,
                out_dir=out_dir,
                auth_source=auth_source,
                manifests=manifests,
                attempt_number=attempt_number,
                timeout=timeout,
            )
            record = _promote_generation(
                protocol_sha256=protocol_sha256,
                batch=batch,
                cell=cell,
                arm_receipt=arm_receipts[arm_id],
                contract=contract,
                out_dir=out_dir,
            )
        if record is None:
            raise RunStop("experiment-invalid", "Generator retry did not produce promotable output")
        records[arm_id] = record
    _budget_check(authorization, out_dir)
    return [records[str(cell["arm_id"])] for cell in batch["cells"]]


def _run_paired_judges(
    *,
    authorization: Mapping[str, Any],
    batch: Mapping[str, Any],
    contract: Mapping[str, Any],
    protocol_sha256: str,
    cells: Sequence[Mapping[str, Any]],
    manifests: Mapping[str, Mapping[str, Any]],
    environments: Mapping[int, Mapping[str, Any]],
    out_dir: Path,
    auth_source: Path,
    timeout: int,
) -> list[dict[str, Any]]:
    inputs = {
        slot: _judge_input(
            protocol_sha256=protocol_sha256,
            batch=batch,
            contract=contract,
            cells=cells,
            out_dir=out_dir,
            manifests=manifests,
            slot=slot,
        )
        for slot in (1, 2)
    }
    records: dict[int, dict[str, Any]] = {}
    pending: list[tuple[int, int]] = []
    for slot in (1, 2):
        payload, receipt, _, receipt_path = inputs[slot]
        record = _promote_judge(
            batch=batch,
            contract=contract,
            payload=payload,
            receipt=receipt,
            receipt_path=receipt_path,
            environment=environments[slot],
            out_dir=out_dir,
            slot=slot,
        )
        if record is not None:
            records[slot] = record
            continue
        parent = out_dir / "paired-judge-attempts" / str(batch["batch_id"]) / f"slot-{slot}"
        pending.append((slot, _next_attempt(parent, "judge") if parent.exists() else 1))
    usage = _budget_check(authorization, out_dir, reserve_calls=len(pending))
    if usage["paired_judge_calls"] + len(pending) > authorization["maximum_paired_judge_calls"]:
        raise RunStop("budget-exceeded", "insufficient paired Judge budget for next batch")
    if pending:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(pending)) as executor:
            futures = []
            for slot, attempt_number in pending:
                payload, receipt, _, receipt_path = inputs[slot]
                futures.append(
                    executor.submit(
                        _run_judge_attempt,
                        batch=batch,
                        contract=contract,
                        payload=payload,
                        receipt=receipt,
                        receipt_path=receipt_path,
                        environment=environments[slot],
                        out_dir=out_dir,
                        auth_source=auth_source,
                        manifests=manifests,
                        slot=slot,
                        attempt_number=attempt_number,
                        timeout=timeout,
                    )
                )
            for future in futures:
                future.result()
    for slot in (1, 2):
        if slot in records:
            continue
        payload, receipt, _, receipt_path = inputs[slot]
        record = _promote_judge(
            batch=batch,
            contract=contract,
            payload=payload,
            receipt=receipt,
            receipt_path=receipt_path,
            environment=environments[slot],
            out_dir=out_dir,
            slot=slot,
        )
        if record is None:
            usage = _budget_check(authorization, out_dir, reserve_calls=1)
            if usage["paired_judge_calls"] >= authorization["maximum_paired_judge_calls"]:
                raise RunStop("budget-exceeded", "paired Judge retry headroom is exhausted")
            parent = out_dir / "paired-judge-attempts" / str(batch["batch_id"]) / f"slot-{slot}"
            attempt_number = _next_attempt(parent, "judge")
            _run_judge_attempt(
                batch=batch,
                contract=contract,
                payload=payload,
                receipt=receipt,
                receipt_path=receipt_path,
                environment=environments[slot],
                out_dir=out_dir,
                auth_source=auth_source,
                manifests=manifests,
                slot=slot,
                attempt_number=attempt_number,
                timeout=timeout,
            )
            record = _promote_judge(
                batch=batch,
                contract=contract,
                payload=payload,
                receipt=receipt,
                receipt_path=receipt_path,
                environment=environments[slot],
                out_dir=out_dir,
                slot=slot,
            )
        if record is None:
            raise RunStop("experiment-invalid", "paired Judge retry did not produce promotable output")
        records[slot] = record
    _budget_check(authorization, out_dir)
    return [records[1], records[2]]


def _projection(out_dir: Path, status: str, committed: int, active: Mapping[str, Any] | None) -> None:
    payload: dict[str, Any] = {
        "schema_version": "mindthus-beta2-route-decision-projection-v0.6",
        "status": status,
        "committed_batches": committed,
        "active_batch_index": active.get("batch_index") if active else None,
        "active_batch_id": active.get("batch_id") if active else None,
        "usage": CORE.attempt_usage(out_dir),
        "authority": "disposable projection; rebuild from attempts and batch commits",
        "updated_at_utc": _now(),
    }
    payload["projection_digest"] = CORE.canonical_sha256(payload)
    _write(out_dir / "run-state.json", payload)


def run(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    protocol, lock = CORE.verify_protocol(args.protocol.resolve(), args.lock.resolve())
    protocol_sha256 = CORE.sha256_file(args.protocol.resolve())
    deterministic = CORE.deterministic_preflight(
        protocol_path=args.protocol.resolve(), lock_path=args.lock.resolve()
    )
    manifests = _manifests(protocol)
    for manifest in manifests.values():
        staging = Path(manifest["host"]["execution_root"]).resolve().parent / "package"
        if staging.exists():
            raise RunStop(
                "isolation-failure",
                f"builder staging still exists beside arm {manifest['arm_id']}",
            )
        for field in ("home", "execution_root"):
            if not Path(manifest["host"][field]).is_dir():
                raise RunStop("arm-drift", f"arm {field} is unavailable: {manifest['arm_id']}")
        if not Path(manifest["package"]["root"]).is_dir():
            raise RunStop("arm-drift", f"arm package is unavailable: {manifest['arm_id']}")
    auth_source = args.auth_source.resolve()
    if not auth_source.is_file():
        raise RunStop("authorization-missing", "Codex auth source is unavailable")
    auth_report = CORE.validate_authorization(
        authorization_path=args.authorization.resolve(),
        protocol_path=args.protocol.resolve(),
        lock_path=args.lock.resolve(),
        out_dir=out_dir,
        require_active=not args.preflight_only,
    )
    environments = {
        slot: _judge_environment(
            out_dir, args.runtime_root.resolve(), auth_source, slot
        )
        for slot in (1, 2)
    }
    if args.preflight_only:
        return {
            **deterministic,
            "authorization": auth_report,
            "arm_ids": sorted(manifests),
            "judge_environment_digests": {
                str(slot): environment["environment_digest"]
                for slot, environment in environments.items()
            },
            "semantic_calls_performed": 0,
        }, 0
    authorization = _read(args.authorization.resolve())
    contracts = CORE.case_contracts()
    plan = CORE.batch_plan(protocol, protocol_sha256)
    commits = CORE.reconstruct_ledger(
        out_dir=out_dir, protocol=protocol, protocol_sha256=protocol_sha256
    )
    analysis = CORE.analyze_run(
        out_dir=out_dir,
        protocol_path=args.protocol.resolve(),
        lock_path=args.lock.resolve(),
    )
    if analysis["status"] in {"human-adjudication-required", "complete"}:
        return analysis, 3 if analysis["status"] == "human-adjudication-required" else 0
    previous = commits[-1]["commit_digest"] if commits else None
    committed = len(commits)
    limit = min(len(plan), committed + args.max_new_batches) if args.max_new_batches else len(plan)
    for batch in plan[committed:limit]:
        _projection(out_dir, "generating", committed, batch)
        cells = _run_missing_generators(
            authorization=authorization,
            protocol=protocol,
            protocol_sha256=protocol_sha256,
            batch=batch,
            contract=contracts[batch["case_id"]],
            manifests=manifests,
            out_dir=out_dir,
            auth_source=auth_source,
            timeout=args.timeout,
        )
        _projection(out_dir, "judging", committed, batch)
        judges = _run_paired_judges(
            authorization=authorization,
            batch=batch,
            contract=contracts[batch["case_id"]],
            protocol_sha256=protocol_sha256,
            cells=cells,
            manifests=manifests,
            environments=environments,
            out_dir=out_dir,
            auth_source=auth_source,
            timeout=args.timeout,
        )
        commit = CORE.build_batch_commit(
            batch=batch,
            cells=cells,
            judge_records=judges,
            previous_commit_digest=previous,
        )
        commit_path = out_dir / "batch-commits" / f"{batch['batch_index']:03d}.json"
        _verify_or_write(commit_path, commit, "batch commit")
        previous = commit["commit_digest"]
        committed += 1
        _projection(out_dir, "batch-committed", committed, batch)
        analysis = CORE.analyze_run(
            out_dir=out_dir,
            protocol_path=args.protocol.resolve(),
            lock_path=args.lock.resolve(),
        )
        _write(out_dir / "decision-report.json", analysis)
        if analysis["status"] == "human-adjudication-required":
            return analysis, 3
        if analysis["status"] == "complete":
            return analysis, 0
    analysis = CORE.analyze_run(
        out_dir=out_dir,
        protocol_path=args.protocol.resolve(),
        lock_path=args.lock.resolve(),
    )
    _write(out_dir / "decision-report.json", analysis)
    return analysis, 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--auth-source", type=Path, default=Path.home() / ".codex" / "auth.json")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--max-new-batches", type=int, default=0)
    parser.add_argument("--preflight-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report, code = run(args)
    except (CORE.DecisionError, RunStop, ISO.IsolationError, OSError, json.JSONDecodeError) as exc:
        error_code = getattr(exc, "code", "experiment-invalid")
        status = "blocked" if error_code in {"authorization-missing", "authorization-drift", "runtime-drift"} else "experiment-invalid"
        report = {"status": status, "outcome": None, "code": error_code, "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
