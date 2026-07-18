#!/usr/bin/env python3
"""Run the single authorized R3 LIVE_INTERFACE qualification probe.

This is deliberately a qualification adapter, not the formal evaluator.  It
starts one real Generator process, persists stream chunks as they arrive, and
never starts a Judge, formal arm, or release path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import selectors
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from decision_reset_kernel import DecisionRuntime, canonical_json, digest


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def git_commit_exists(repo_root: Path, commit: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def build_codex_command(auth: dict[str, Any], repo_root: Path, prompt: str) -> list[str]:
    """Build the exact command, keeping global options before the exec subcommand."""

    model = auth["model"]
    return [
        "codex",
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "-m",
        str(model["family"]),
        "-c",
        f'model_reasoning_effort="{model["reasoning_effort"]}"',
        "-C",
        str(repo_root),
        prompt,
    ]


def validate_command_parser(command: list[str], cwd: Path) -> dict[str, Any]:
    """Exercise the final argv through clap without starting a model turn."""

    check_command = command[:-1] + ["--help"]
    result = subprocess.run(check_command, cwd=cwd, text=True, capture_output=True, timeout=20)
    return {
        "command": check_command,
        "returncode": result.returncode,
        "stdout_sha256": sha256_bytes(result.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(result.stderr.encode("utf-8")),
        "stderr": result.stderr,
    }


def parse_codex_stdout(value: bytes) -> dict[str, Any]:
    """Extract only client-visible lifecycle facts from Codex JSONL stdout."""

    events: list[dict[str, Any]] = []
    invalid_lines: list[int] = []
    for line_number, raw_line in enumerate(value.decode("utf-8", errors="replace").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            invalid_lines.append(line_number)
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            invalid_lines.append(line_number)
    event_types = [str(event.get("type", "")) for event in events]
    thread_ids = [str(event["thread_id"]) for event in events if event.get("type") == "thread.started" and event.get("thread_id")]
    final_messages = [
        str(event["item"]["text"])
        for event in events
        if event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
        and isinstance(event["item"].get("text"), str)
    ]
    completed = [event for event in events if event.get("type") == "turn.completed"]
    terminal_usage = completed[-1].get("usage") if completed and isinstance(completed[-1].get("usage"), dict) else None
    lifecycle_complete = bool(
        thread_ids
        and "turn.started" in event_types
        and final_messages
        and completed
        and terminal_usage is not None
        and not invalid_lines
    )
    return {
        "event_types": event_types,
        "thread_ids": thread_ids,
        "final_messages": final_messages,
        "terminal_usage": terminal_usage,
        "invalid_jsonl_lines": invalid_lines,
        "lifecycle_complete": lifecycle_complete,
    }


def validate_authority(
    *, repo_root: Path, auth_path: Path, charter_path: Path, design_path: Path
) -> tuple[dict[str, Any], dict[str, Any], str, str]:
    auth = load_json(auth_path)
    charter = load_json(charter_path)
    design_sha = sha256_bytes(design_path.read_bytes())
    if auth.get("status") != "ACTIVE":
        raise ValueError("qualification authorization is not ACTIVE")
    if auth.get("program_id") != charter.get("program_id"):
        raise ValueError("authorization/charter program mismatch")
    if auth.get("design_sha256") != design_sha or charter.get("design_sha256") != design_sha:
        raise ValueError("design digest does not match authorization and charter")
    if auth.get("limits", {}).get("max_generator_calls") != 1:
        raise ValueError("this runner only accepts exactly one Generator call")
    if auth.get("limits", {}).get("max_paired_judge_calls") != 0 or auth.get("judge_calls") != 0:
        raise ValueError("Judge calls are not permitted by this runner")
    if auth.get("limits", {}).get("concurrency") != 1:
        raise ValueError("concurrency must be exactly one")
    if auth.get("limits", {}).get("authority_mode") != "TAIL_ACCEPTED":
        raise ValueError("authority mode must be explicit TAIL_ACCEPTED")
    if auth.get("model") != charter.get("model"):
        raise ValueError("authorization/charter model mismatch")
    charter_limits = charter.get("qualification", {})
    for key in (
        "max_generator_calls",
        "max_paired_judge_calls",
        "concurrency",
        "local_time_limit_seconds",
        "authority_mode",
    ):
        if auth.get("limits", {}).get(key) != charter_limits.get(key):
            raise ValueError(f"authorization/charter limit mismatch: {key}")
    if not auth.get("tail_acceptance", {}).get("accepted"):
        raise ValueError("tail acceptance is not explicit")
    if auth.get("formal_arm_sampling") or auth.get("release_publication"):
        raise ValueError("formal arm and release/publication must remain disabled")
    candidate = str(auth.get("candidate_commit", ""))
    if candidate != str(charter.get("candidate_commit", "")):
        raise ValueError("authorization/charter candidate mismatch")
    if not candidate or not git_commit_exists(repo_root, candidate):
        raise ValueError("candidate commit is not present in the repository")
    now = time.time()
    cutoff = datetime.fromisoformat(str(auth["cutoff_at"]).replace("Z", "+00:00")).timestamp()
    if cutoff <= now:
        raise ValueError("qualification authorization cutoff has expired")
    return auth, charter, design_sha, candidate


def append_chunk(
    runtime: DecisionRuntime,
    raw_handle: Any,
    *,
    stream: str,
    chunk_index: int,
    chunk: bytes,
) -> dict[str, Any]:
    raw_handle.write(chunk)
    raw_handle.flush()
    os.fsync(raw_handle.fileno())
    event_id = f"stream:{stream}:{chunk_index}"
    return runtime.append_source(
        "stream_chunk",
        {
            "stream": stream,
            "chunk_index": chunk_index,
            "byte_length": len(chunk),
            "sha256": sha256_bytes(chunk),
        },
        event_id=event_id,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--charter", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    auth_path = args.authorization.resolve()
    charter_path = args.charter.resolve()
    design_path = args.design.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    try:
        auth, charter, design_sha, candidate = validate_authority(
            repo_root=repo_root, auth_path=auth_path, charter_path=charter_path, design_path=design_path
        )
    except Exception as exc:
        receipt = {
            "schema_version": "mindthus-beta2-r3-live-interface-v0.1",
            "program_id": "unknown",
            "status": "BLOCKED_AUTHORITY",
            "started_at": started_at,
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "generator_calls": 0,
            "judge_calls": 0,
        }
        receipt["receipt_digest"] = digest(receipt)
        (out / "qualification-receipt.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(json.dumps(receipt, ensure_ascii=False))
        return 2

    runtime = DecisionRuntime(out)
    auth_digest = digest(auth)
    charter_digest = digest(charter)
    runtime.append_source(
        "authorization",
        {
            "program_id": auth["program_id"],
            "authorization_sha256": auth_digest,
            "charter_sha256": charter_digest,
            "design_sha256": design_sha,
            "candidate_commit": candidate,
            "authority_mode": auth["limits"]["authority_mode"],
            "max_generator_calls": auth["limits"]["max_generator_calls"],
            "max_paired_judge_calls": auth["limits"]["max_paired_judge_calls"],
            "formal_arm_sampling": auth["formal_arm_sampling"],
            "release_publication": auth["release_publication"],
        },
        event_id=f"authorization:{auth['program_id']}:{auth_digest}",
    )

    raw_path = out / "raw-stream.bin"
    prompt = (
        "This is a lifecycle qualification probe. Respond with exactly PROBE_OK. "
        "Do not inspect files, use tools, or make changes."
    )
    command = build_codex_command(auth, repo_root, prompt)
    parser_check = validate_command_parser(command, repo_root)
    runtime.append_source(
        "interface_precheck",
        {
            "command": parser_check["command"],
            "returncode": parser_check["returncode"],
            "stdout_sha256": parser_check["stdout_sha256"],
            "stderr_sha256": parser_check["stderr_sha256"],
        },
        event_id="interface-precheck:generator:1",
    )
    if parser_check["returncode"] != 0:
        runtime.append_source(
            "provider_terminal",
            {
                "infrastructure_receipt": True,
                "provider_code": "interface_precheck_failed",
                "stderr": parser_check["stderr"],
                "finished_at": utc_now(),
            },
            event_id="provider-terminal:precheck",
        )
        cut = runtime.seal_cut(reason="qualification_interface_precheck_failed")
        terminal = runtime.terminal_receipt()
        receipt = {
            "schema_version": "mindthus-beta2-r3-live-interface-v0.1",
            "program_id": auth["program_id"],
            "status": "BLOCKED_INTERFACE_PRECHECK",
            "started_at": started_at,
            "finished_at": utc_now(),
            "design_sha256": design_sha,
            "candidate_commit": candidate,
            "generator_calls": 0,
            "judge_calls": 0,
            "formal_arm_sampling": False,
            "release_publication": False,
            "decision_cut_digest": cut["digest"],
            "kernel_terminal": terminal,
            "parser_check": parser_check,
        }
        receipt["receipt_digest"] = digest(receipt)
        (out / "qualification-receipt.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(json.dumps({"status": receipt["status"], "generator_calls": 0, "digest": receipt["receipt_digest"]}, ensure_ascii=False))
        return 2

    cutoff = datetime.fromisoformat(str(auth["cutoff_at"]).replace("Z", "+00:00")).timestamp()
    if time.time() >= cutoff:
        runtime.append_source(
            "provider_terminal",
            {
                "infrastructure_receipt": True,
                "provider_code": "cutoff_before_request_start",
                "finished_at": utc_now(),
            },
            event_id="provider-terminal:prestart-cutoff",
        )
        cut = runtime.seal_cut(reason="qualification_cutoff_before_request_start")
        terminal = runtime.terminal_receipt()
        receipt = {
            "schema_version": "mindthus-beta2-r3-live-interface-v0.1",
            "program_id": auth["program_id"],
            "status": "BLOCKED_CUTOFF_BEFORE_REQUEST",
            "started_at": started_at,
            "finished_at": utc_now(),
            "generator_calls": 0,
            "judge_calls": 0,
            "decision_cut_digest": cut["digest"],
            "kernel_terminal": terminal,
        }
        receipt["receipt_digest"] = digest(receipt)
        (out / "qualification-receipt.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
        print(json.dumps({"status": receipt["status"], "generator_calls": 0, "digest": receipt["receipt_digest"]}, ensure_ascii=False))
        return 2

    runtime.append_source(
        "reservation",
        {"generator_slot": 1, "judge_slots": 0, "concurrency": 1, "reserved_at": started_at},
        event_id="reservation:generator:1",
    )
    runtime.append_source(
        "request_start",
        {"generator_slot": 1, "started_at": started_at, "model": auth["model"], "parser_check": "passed"},
        event_id="request-start:generator:1",
    )
    process: subprocess.Popen[bytes] | None = None
    chunks: list[dict[str, Any]] = []
    stdout_bytes = bytearray()
    stderr_bytes = bytearray()
    timed_out = False
    returncode: int | None = None
    try:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            start_new_session=True,
        )
        assert process.stdout is not None and process.stderr is not None
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        with raw_path.open("ab") as raw_handle:
            index = {"stdout": 0, "stderr": 0}
            while selector.get_map():
                if time.time() >= cutoff:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGTERM)
                    break
                for key, _ in selector.select(timeout=0.25):
                    chunk = os.read(key.fd, 4096)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    stream = str(key.data)
                    index[stream] += 1
                    chunks.append(append_chunk(runtime, raw_handle, stream=stream, chunk_index=index[stream], chunk=chunk))
                    (stdout_bytes if stream == "stdout" else stderr_bytes).extend(chunk)
            selector.close()
        if timed_out:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
        else:
            returncode = process.wait(timeout=max(1, int(cutoff - time.time())))
    except FileNotFoundError as exc:
        runtime.append_source("provider_terminal", {"infrastructure_receipt": True, "provider_code": "codex_missing", "message": str(exc)}, event_id="provider-terminal:missing")
    except subprocess.TimeoutExpired:
        timed_out = True
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)
    finally:
        if process is not None and returncode is None:
            returncode = process.returncode

    lifecycle = parse_codex_stdout(bytes(stdout_bytes))
    raw_file_sha256 = sha256_bytes(raw_path.read_bytes()) if raw_path.exists() else sha256_bytes(b"")
    infra = timed_out or returncode not in (0, None) or not stdout_bytes
    lifecycle_complete = bool(lifecycle["lifecycle_complete"] and not infra)
    provider_code = "timeout" if timed_out else ("exit_nonzero" if returncode not in (0, None) else "ok")
    runtime.append_source(
        "provider_terminal",
        {
            "returncode": returncode,
            "provider_code": provider_code,
            "infrastructure_receipt": infra,
            "stdout_sha256": sha256_bytes(bytes(stdout_bytes)),
            "stderr_sha256": sha256_bytes(bytes(stderr_bytes)),
            "raw_file_sha256": raw_file_sha256,
            "stream_chunks": len(chunks),
            "thread_ids": lifecycle["thread_ids"],
            "terminal_usage": lifecycle["terminal_usage"],
            "lifecycle_complete": lifecycle_complete,
            "finished_at": utc_now(),
        },
        event_id="provider-terminal:generator:1",
    )
    runtime.append_source(
        "attempt",
        {
            "attempt_id": "generator-1",
            "content": "final_nonempty" if lifecycle["final_messages"] and not infra else "unknown",
            "dependencies_valid": True,
            "claims": {},
            "usage": lifecycle["terminal_usage"],
        },
        event_id="attempt:generator:1",
    )
    cut = runtime.seal_cut(reason="qualification_probe_complete")
    terminal = runtime.terminal_receipt()
    receipt = {
        "schema_version": "mindthus-beta2-r3-live-interface-v0.1",
        "program_id": auth["program_id"],
        "status": (
            "LIVE_INTERFACE_LIFECYCLE_PASSED"
            if lifecycle_complete
            else ("LIVE_INTERFACE_INFRA_FAILURE" if infra else "LIVE_INTERFACE_INCOMPLETE")
        ),
        "started_at": started_at,
        "finished_at": utc_now(),
        "cutoff_at": auth["cutoff_at"],
        "design_sha256": design_sha,
        "candidate_commit": candidate,
        "model": auth["model"],
        "authority_mode": auth["limits"]["authority_mode"],
        "generator_calls": 1,
        "judge_calls": 0,
        "formal_arm_sampling": False,
        "release_publication": False,
        "command": command[:-1] + ["<probe-prompt>"],
        "returncode": returncode,
        "timed_out": timed_out,
        "stream_chunks": len(chunks),
        "raw_stream_sha256": raw_file_sha256,
        "raw_stream_layout": "ledger-order interleaved chunks",
        "client_lifecycle": lifecycle,
        "decision_cut_digest": cut["digest"],
        "kernel_terminal": terminal,
        "qualification_claim_boundary": "No product or route claim; lifecycle observation only.",
    }
    receipt["receipt_digest"] = digest(receipt)
    (out / "qualification-receipt.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "receipt": str(out / "qualification-receipt.json"), "digest": receipt["receipt_digest"], "returncode": returncode}, ensure_ascii=False))
    return 0 if lifecycle_complete else 3


if __name__ == "__main__":
    raise SystemExit(main())
