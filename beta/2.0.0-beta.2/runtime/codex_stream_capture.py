#!/usr/bin/env python3
"""Capture Codex JSONL with monotonic line-arrival receipts.

The timing produced here is runner-observed. It is deliberately not called native
host timing and never substitutes for a missing host timestamp.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


ELIGIBLE_ITEM_TYPES = frozenset({"agent_message", "command_execution"})
ELIGIBLE_EVENT_TYPES = frozenset({"item.started", "item.completed"})


@dataclass(frozen=True)
class StreamCapture:
    returncode: int
    stdout: str
    stderr: str
    wall_time_seconds: float
    timed_out: bool
    first_observable_action: dict[str, Any] | None


def observable_action_receipt(
    line: str,
    *,
    arrived_at: float,
    started_at: float,
    stdout_sequence: int,
) -> dict[str, Any] | None:
    """Return a redacted receipt for one eligible event, otherwise ``None``."""

    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(event, Mapping):
        return None
    event_type = str(event.get("type") or "")
    item = event.get("item") if isinstance(event.get("item"), Mapping) else {}
    item_type = str(item.get("type") or "")
    if event_type not in ELIGIBLE_EVENT_TYPES or item_type not in ELIGIBLE_ITEM_TYPES:
        return None
    return {
        "event_type": event_type,
        "item_type": item_type,
        "stdout_sequence": stdout_sequence,
        "offset_seconds": round(max(0.0, arrived_at - started_at), 6),
        "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
        "provenance": "runner-stream-arrival",
        "content_retained": False,
    }


def _reader(
    stream: Any,
    stream_name: str,
    output: "queue.Queue[tuple[str, float, str] | tuple[str, None, None]]",
) -> None:
    try:
        for line in iter(stream.readline, ""):
            output.put((stream_name, time.monotonic(), line))
    finally:
        output.put((stream_name, None, None))


def run_streamed(
    command: Sequence[str],
    *,
    input_text: str,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    timeout: float,
) -> StreamCapture:
    """Run a process and timestamp stdout lines at reader arrival.

    Stdout and stderr are drained concurrently. On timeout the child is terminated,
    then killed if it does not exit promptly. The returned receipt contains no event
    content, only type, sequence, offset, and the line digest.
    """

    # Include process creation in the user's runner-visible wait.
    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    events: "queue.Queue[tuple[str, float, str] | tuple[str, None, None]]" = queue.Queue()
    threads = [
        threading.Thread(target=_reader, args=(process.stdout, "stdout", events), daemon=True),
        threading.Thread(target=_reader, args=(process.stderr, "stderr", events), daemon=True),
    ]
    for thread in threads:
        thread.start()
    try:
        process.stdin.write(input_text)
        process.stdin.close()
    except BrokenPipeError:
        pass

    stdout: list[str] = []
    stderr: list[str] = []
    closed: set[str] = set()
    first_receipt: dict[str, Any] | None = None
    stdout_sequence = 0
    timed_out = False
    deadline = started + timeout
    while len(closed) < 2:
        remaining = deadline - time.monotonic()
        if remaining <= 0 and process.poll() is None:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            deadline = time.monotonic() + 5
        try:
            stream_name, arrived_at, line = events.get(timeout=max(0.01, min(0.1, remaining)))
        except queue.Empty:
            if process.poll() is not None and all(not thread.is_alive() for thread in threads):
                break
            continue
        if arrived_at is None:
            closed.add(stream_name)
            continue
        assert line is not None
        if stream_name == "stdout":
            stdout.append(line)
            stdout_sequence += 1
            if first_receipt is None:
                first_receipt = observable_action_receipt(
                    line,
                    arrived_at=arrived_at,
                    started_at=started,
                    stdout_sequence=stdout_sequence,
                )
        else:
            stderr.append(line)

    for thread in threads:
        thread.join(timeout=1)
    if process.poll() is None:
        process.kill()
    returncode = process.wait()
    process.stdout.close()
    process.stderr.close()
    return StreamCapture(
        returncode=returncode,
        stdout="".join(stdout),
        stderr="".join(stderr),
        wall_time_seconds=round(time.monotonic() - started, 6),
        timed_out=timed_out,
        first_observable_action=first_receipt,
    )


__all__ = [
    "ELIGIBLE_EVENT_TYPES",
    "ELIGIBLE_ITEM_TYPES",
    "StreamCapture",
    "observable_action_receipt",
    "run_streamed",
]
