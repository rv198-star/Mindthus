#!/usr/bin/env python3
"""Prove Codex injects the packaged Passive Kernel without calling a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import stat
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mindthus-beta2-host-hook-observation-v0.2"
PROBE_MODEL = "mindthus-no-model-hook-probe"
PROBE_PROMPT = "Mindthus Beta.2 infrastructure hook preflight only."
PROBE_PORT = 11434
KERNEL_OPEN = "<MINDTHUS_PASSIVE_KERNEL>"
KERNEL_CLOSE = "</MINDTHUS_PASSIVE_KERNEL>"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise RuntimeError(f"probe package tree contains a symlink: {relative}")
        if path.is_file():
            mode = stat.S_IMODE(path.stat().st_mode)
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(f"{mode:04o}".encode("ascii"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def canonical_kernel_text(value: str) -> str:
    """Normalize only transport-owned line endings and wrapper boundaries.

    The SessionStart shell hook uses command substitution, which removes the source
    file's trailing newline, then places the body between newline-delimited wrapper
    tags.  Comparing the normalized body proves content fidelity without pretending
    those transport boundary newlines are part of the authored kernel.
    """

    return value.replace("\r\n", "\n").replace("\r", "\n").strip("\n")


def wrapped_kernel_bodies(value: str) -> list[str]:
    bodies: list[str] = []
    offset = 0
    while True:
        start = value.find(KERNEL_OPEN, offset)
        if start < 0:
            return bodies
        body_start = start + len(KERNEL_OPEN)
        end = value.find(KERNEL_CLOSE, body_start)
        if end < 0:
            return bodies
        bodies.append(value[body_start:end])
        offset = end + len(KERNEL_CLOSE)


class ProbeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], kernel: str):
        super().__init__(address, ProbeHandler)
        self.kernel = kernel
        self.requests: list[dict[str, Any]] = []


class ProbeHandler(BaseHTTPRequestHandler):
    server: ProbeServer

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _json(self, status: int, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path.startswith("/v1/models") or self.path.startswith("/api/tags"):
            self._json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": PROBE_MODEL,
                            "object": "model",
                            "created": 0,
                            "owned_by": "local-no-model-probe",
                        }
                    ],
                    "models": [{"name": PROBE_MODEL, "model": PROBE_MODEL}],
                },
            )
        elif self.path.startswith("/api/version"):
            # Codex refuses Ollama versions older than its supported floor before it
            # sends a model request.  This endpoint is still a no-model loopback stub;
            # the version only permits transport preflight to reach request capture.
            self._json(200, {"version": "0.13.4"})
        else:
            self._json(404, {"error": "probe endpoint not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        text = body.decode("utf-8", "replace")
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError:
            decoded = None

        def strings(value: object) -> list[str]:
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [item for child in value for item in strings(child)]
            if isinstance(value, dict):
                return [item for child in value.values() for item in strings(child)]
            return []

        model_strings = strings(decoded)
        expected_kernel = canonical_kernel_text(self.server.kernel)
        wrapped_bodies = [
            body
            for value in model_strings
            for body in wrapped_kernel_bodies(value)
        ]
        matching_bodies = [
            body
            for body in wrapped_bodies
            if canonical_kernel_text(body) == expected_kernel
        ]
        self.server.requests.append(
            {
                "path": self.path,
                "request_bytes": len(body),
                "request_sha256": hashlib.sha256(body).hexdigest(),
                "kernel_wrapper_present": any(
                    KERNEL_OPEN in value and KERNEL_CLOSE in value
                    for value in model_strings
                ),
                "exact_kernel_present": bool(matching_bodies),
                "wrapped_kernel_count": len(wrapped_bodies),
                "matching_kernel_count": len(matching_bodies),
                "captured_kernel_canonical_sha256": (
                    hashlib.sha256(
                        canonical_kernel_text(matching_bodies[0]).encode("utf-8")
                    ).hexdigest()
                    if matching_bodies
                    else None
                ),
                "probe_prompt_present": any(
                    PROBE_PROMPT in value for value in model_strings
                ),
            }
        )
        # A 400 response is intentionally non-retryable: one captured request is
        # sufficient proof, and repeated transport retries add no evidence.
        self._json(
            400,
            {
                "error": {
                    "message": "intentional no-model hook probe stop",
                    "type": "mindthus_probe_stop",
                }
            },
        )


def probe_hook(
    *,
    package_root: Path,
    codex_home: Path,
    process_home: Path,
    execution_root: Path,
    expect_kernel: bool = True,
    bypass_hook_trust: bool = True,
    codex_version: str = "0.144.4",
    timeout: int = 75,
) -> dict[str, Any]:
    package_root = package_root.resolve()
    kernel_path = package_root / "runtime" / "passive-activation-kernel.md"
    if not kernel_path.is_file():
        raise RuntimeError("packaged Passive Kernel is unavailable")
    kernel = kernel_path.read_text(encoding="utf-8")
    try:
        server = ProbeServer(("127.0.0.1", PROBE_PORT), kernel)
    except OSError as exc:
        raise RuntimeError(
            f"no-model hook probe requires unused loopback port {PROBE_PORT}: {exc}"
        ) from exc
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    env = os.environ.copy()
    env.update(
        {
            "CODEX_HOME": str(codex_home.resolve()),
            "HOME": str(process_home.resolve()),
            "OTEL_SDK_DISABLED": "true",
            "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        }
    )
    command = [
        "codex",
        "exec",
        "--json",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--ephemeral",
        "--oss",
        "--local-provider",
        "ollama",
        "--model",
        PROBE_MODEL,
        "-s",
        "read-only",
        "-C",
        str(execution_root.resolve()),
        PROBE_PROMPT,
    ]
    if bypass_hook_trust:
        command.insert(command.index("-s"), "--dangerously-bypass-hook-trust")
    try:
        result = subprocess.run(
            command,
            cwd=execution_root,
            env=env,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
    matching = [
        request
        for request in server.requests
        if request["path"].startswith("/v1/responses")
        and request["probe_prompt_present"]
        and (
            request["kernel_wrapper_present"]
            and request["exact_kernel_present"]
            if expect_kernel
            else not request["kernel_wrapper_present"]
            and not request["exact_kernel_present"]
        )
    ]
    if result.returncode == 0:
        raise RuntimeError("no-model hook probe unexpectedly produced a successful turn")
    if not matching:
        wrapper_requests = sum(
            1 for request in server.requests if request["kernel_wrapper_present"]
        )
        exact_requests = sum(
            1 for request in server.requests if request["exact_kernel_present"]
        )
        prompt_requests = sum(
            1 for request in server.requests if request["probe_prompt_present"]
        )
        expectation = "contain the exact" if expect_kernel else "exclude the"
        raise RuntimeError(
            f"Codex model-visible request did not {expectation} Passive Kernel "
            f"(requests={len(server.requests)}, wrapper={wrapper_requests}, "
            f"exact={exact_requests}, prompt={prompt_requests})"
        )
    if "intentional no-model hook probe stop" not in (result.stdout + result.stderr):
        raise RuntimeError("Codex did not stop at the intentional local no-model endpoint")
    first = matching[0]
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": "observed-fired" if expect_kernel else "observed-absent",
        "expected_kernel_state": "present" if expect_kernel else "absent",
        "observed_kernel_state": "present" if expect_kernel else "absent",
        "observation_method": "loopback-no-model-request-capture",
        "model_execution_performed": False,
        "semantic_output_generated": False,
        "network_scope": "127.0.0.1-only model endpoint",
        "codex_cli_version": codex_version,
        "hook_trust_bypassed_for_vetted_package": bypass_hook_trust,
        "package_tree_sha256": tree_sha256(package_root),
        "kernel_sha256": hashlib.sha256(kernel.encode("utf-8")).hexdigest(),
        "kernel_canonical_sha256": hashlib.sha256(
            canonical_kernel_text(kernel).encode("utf-8")
        ).hexdigest(),
        "captured_kernel_canonical_sha256": first[
            "captured_kernel_canonical_sha256"
        ],
        "kernel_transport_normalization": (
            "line-endings-plus-wrapper-boundary-newlines-only"
        ),
        "request_path": first["path"],
        "request_sha256": first["request_sha256"],
        "request_bytes": first["request_bytes"],
        "captured_request_count": len(server.requests),
        "matching_request_count": len(matching),
        "request_content_retained": False,
        "expected_failure_returncode": result.returncode,
    }
    receipt["receipt_digest"] = canonical_sha256(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--codex-home", type=Path, required=True)
    parser.add_argument("--process-home", type=Path, required=True)
    parser.add_argument("--execution-root", type=Path, required=True)
    parser.add_argument("--expect-absent", action="store_true")
    parser.add_argument("--do-not-bypass-hook-trust", action="store_true")
    args = parser.parse_args()
    try:
        report = probe_hook(
            package_root=args.package_root,
            codex_home=args.codex_home,
            process_home=args.process_home,
            execution_root=args.execution_root,
            expect_kernel=not args.expect_absent,
            bypass_hook_trust=not args.do_not_bypass_hook_trust,
        )
        code = 0
    except (OSError, RuntimeError, subprocess.SubprocessError, socket.error) as exc:
        report = {"status": "blocked", "reason": str(exc)}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
