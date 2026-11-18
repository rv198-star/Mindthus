#!/usr/bin/env python3
"""Read the visible model catalog from a selected Codex App Server."""

import argparse
import json
import queue
import stat
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class InventoryError(Exception):
    pass


def required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise InventoryError(f"Invalid {field} in model/list")
    return value


def project_model(row):
    if not isinstance(row, dict) or not isinstance(row.get("supportedReasoningEfforts"), list):
        raise InventoryError("Invalid model or reasoning efforts in model/list")
    efforts = [
        required_text(option.get("reasoningEffort") if isinstance(option, dict) else None,
                      "reasoningEffort")
        for option in row["supportedReasoningEfforts"]
    ]
    return {
        "id": required_text(row.get("id"), "id"),
        "model": required_text(row.get("model"), "model"),
        "displayName": required_text(row.get("displayName"), "displayName"),
        "supportedReasoningEfforts": efforts,
        "defaultReasoningEffort": required_text(row.get("defaultReasoningEffort"),
                                                "defaultReasoningEffort"),
    }


@contextmanager
def stdio_transport(command):
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL) as process:
        lines = queue.Queue()

        def read_lines():
            try:
                for line in process.stdout:
                    lines.put(line)
            finally:
                lines.put(None)

        reader = threading.Thread(target=read_lines, daemon=True)
        reader.start()

        def send(body):
            process.stdin.write(json.dumps(body).encode() + b"\n")
            process.stdin.flush()

        def receive(remaining):
            try:
                return lines.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError from None

        try:
            yield send, receive
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            reader.join(timeout=1)


@contextmanager
def socket_transport(path, deadline):
    try:
        from websockets.exceptions import WebSocketException
        from websockets.sync.client import unix_connect
    except ImportError:
        raise InventoryError("--socket requires websockets>=12; see host operations") from None
    if not stat.S_ISSOCK(path.stat().st_mode):
        raise InventoryError("The supplied path is not an App Server socket")
    try:
        with unix_connect(str(path), uri="ws://localhost", close_timeout=1,
                          open_timeout=max(0, deadline - time.monotonic())) as ws:
            yield lambda body: ws.send(json.dumps(body)), lambda remaining: ws.recv(timeout=remaining)
    except TimeoutError:
        raise InventoryError("Timed out opening the target App Server socket") from None
    except WebSocketException:
        raise InventoryError("The target App Server WebSocket connection failed") from None


def read_catalog(send, receive, provider, deadline, page_size):
    request_id = 0

    def request(method, params):
        nonlocal request_id
        request_id += 1
        send({"id": request_id, "method": method, "params": params})
        while True:
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError
                message = receive(remaining)
            except TimeoutError:
                raise InventoryError(f"Timed out waiting for {method}") from None
            if message is None:
                raise InventoryError(f"App Server closed before returning {method}")
            try:
                response = json.loads(message)
            except (UnicodeError, ValueError):
                raise InventoryError("App Server returned invalid JSON") from None
            if not isinstance(response, dict):
                raise InventoryError("App Server returned a non-object message")
            if response.get("id") != request_id:
                continue
            if "error" in response:
                error = response["error"]
                code = error.get("code") if isinstance(error, dict) else None
                suffix = f" (RPC error {code})" if type(code) is int else ""
                raise InventoryError(f"App Server rejected {method}{suffix}")
            result = response.get("result")
            if not isinstance(result, dict):
                raise InventoryError(f"Invalid result from {method}")
            return result

    request("initialize", {"clientInfo": {"name": "mindthus_codex_dispatch", "version": "0.1.0"}})
    send({"method": "initialized"})
    params = {"includeHidden": False, "limit": page_size}
    if provider is not None:
        params["modelProvider"] = provider
    rows, ids, cursors = [], set(), set()
    while True:
        result = request("model/list", params)
        if not isinstance(result.get("data"), list) or "nextCursor" not in result:
            raise InventoryError("Invalid catalog page from model/list")
        for row in result["data"]:
            if isinstance(row, dict) and row.get("hidden") is True:
                continue
            model = project_model(row)
            if model["id"] in ids:
                raise InventoryError("Duplicate model ID across catalog rows")
            ids.add(model["id"])
            rows.append(model)
        cursor = result["nextCursor"]
        if cursor is None:
            return rows
        if not isinstance(cursor, str) or not cursor or cursor in cursors:
            raise InventoryError("Invalid or repeated model/list cursor")
        cursors.add(cursor)
        params["cursor"] = cursor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="Target host label for the inventory")
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument("--socket", type=Path, help="Socket of the running target server")
    transport.add_argument("--cli", action="store_true", help="CLI target using current working context")
    parser.add_argument("--codex-bin", help="Codex executable for --cli (default: codex)")
    parser.add_argument("--provider", help="Exact provider ID; omit for the target default scope")
    parser.add_argument("--timeout", type=int, default=15, help="Seconds for the full read")
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    if args.timeout < 1 or args.page_size < 1:
        parser.error("--timeout and --page-size must be positive")
    if not args.host.strip() or (args.provider is not None and not args.provider.strip()):
        parser.error("--host and any supplied --provider must be nonempty")
    if args.socket is not None and args.codex_bin is not None:
        parser.error("--codex-bin is only for --cli")

    deadline = time.monotonic() + args.timeout
    connection = (socket_transport(args.socket, deadline) if args.socket is not None
                  else stdio_transport([args.codex_bin or "codex", "app-server"]))
    try:
        with connection as (send, receive):
            models = read_catalog(send, receive, args.provider, deadline, args.page_size)
    except (InventoryError, OSError) as exc:
        # Do not print raw RPC errors, endpoint paths, or child logs.
        reason = str(exc) if isinstance(exc, InventoryError) else (exc.strerror or "I/O error")
        print(f"Model inventory unavailable: {reason}", file=sys.stderr)
        return 1

    print(json.dumps({
        "source": "model/list",
        "transport": "existing_socket" if args.socket else "cli_stdio",
        "host": args.host,
        "modelProvider": args.provider,
        "observedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "models": models,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
