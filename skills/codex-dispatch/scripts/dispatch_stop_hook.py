#!/usr/bin/env python3
"""Codex Stop hook for Dispatch cross-chat handoffs.

Installed at user scope (~/.codex/hooks.json). On every turn stop it:

1. Writes a liveness timestamp under <git-common-dir>/dispatch-local/
   (or a fallback location outside git when the session is not in a repo).
   Dispatch reads that timestamp — not config — to decide whether the hook
   is actually running.
2. Lets the turn end immediately when ``stop_hook_active`` is already true
   (the hook may interrupt a turn only once).
3. Blocks once with a reminder when either check applies to this repo:

   - Coordinator side: ``dispatch-local/*/inbox/pending`` is non-empty —
     there are delivered events waiting for the local A to dispose.
   - Worker side: this repo has a ``dispatch-local`` tree (so it takes part
     in dispatch) and ``last_assistant_message`` neither looks like a
     delivery report nor records a blocker — the worker may have finished
     without sending its authorized return.

Codex Stop contract: exit 0 with a JSON object on stdout. ``decision:
"block"`` plus ``reason`` makes Codex continue the turn with that reason as
a new prompt; ``{}`` lets the turn end. Non-JSON stdout is invalid, and any
matching hook returning ``continue: false`` takes precedence — this hook
never emits it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LIVENESS_FILENAME = "hook-last-run.json"
SCHEMA_VERSION = "codex.dispatch_stop_hook.v0.1"

# Markers in last_assistant_message that already close the loop.
DELIVERY_MARKERS = (
    "：",  # sender-colon message form used for deliveries
    "交付",
    "回发",
    "请复审",
    "送审",
    "send_message_to_thread",
    "send_message",
    "delivery",
    "delivered",
    "sent",
)
BLOCKER_MARKERS = (
    "阻塞",
    "无法",
    "受阻",
    "暂停",
    "block",
    "blocked",
    "blocker",
    "cannot",
    "unable",
    "waiting",
    "等待",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git_common_dir(cwd: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    if not text:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = (cwd / path).resolve()
    return path if path.is_dir() else None


def _write_liveness(event: dict) -> str | None:
    """Record that the hook ran; return where it was written, or None."""
    cwd_text = event.get("cwd")
    cwd = Path(cwd_text).resolve() if isinstance(cwd_text, str) and cwd_text else Path.cwd()
    record = {
        "schema_version": SCHEMA_VERSION,
        "ran_at": _now_iso(),
        "session_id": event.get("session_id"),
        "hook_event_name": event.get("hook_event_name"),
        "cwd": str(cwd),
    }
    targets = []
    git_dir = _git_common_dir(cwd)
    if git_dir is not None:
        targets.append(git_dir / "dispatch-local" / LIVENESS_FILENAME)
    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        targets.append(Path(cache_home) / "codex-dispatch" / LIVENESS_FILENAME)
    targets.append(Path.home() / ".codex" / "dispatch-local" / LIVENESS_FILENAME)
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return str(target)
        except OSError:
            continue
    return None


def _pending_inbox_entries(dispatch_local: Path) -> list[dict]:
    pending = []
    if not dispatch_local.is_dir():
        return pending
    for task_dir in sorted(dispatch_local.iterdir()):
        inbox_pending = task_dir / "inbox" / "pending"
        if not inbox_pending.is_dir():
            continue
        for event_path in sorted(inbox_pending.glob("*.json")):
            try:
                event = json.loads(event_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                event = {"key": event_path.stem}
            pending.append({"task": task_dir.name, "event": event})
    return pending


def _repo_uses_dispatch(dispatch_local: Path) -> bool:
    """True when a real inbox exists — not merely the hook's own liveness file."""
    if not dispatch_local.is_dir():
        return False
    for child in dispatch_local.iterdir():
        if child.is_dir() and (child / "inbox").is_dir():
            return True
    return False


def _looks_delivered(message: str) -> bool:
    text = message or ""
    return any(marker in text for marker in DELIVERY_MARKERS)


def _looks_blocked(message: str) -> bool:
    text = message or ""
    return any(marker in text for marker in BLOCKER_MARKERS)


def evaluate(event: dict) -> dict:
    """Return the stdout JSON for this Stop event."""
    liveness_path = _write_liveness(event)
    if event.get("stop_hook_active") is True:
        return {}
    cwd_text = event.get("cwd")
    cwd = Path(cwd_text).resolve() if isinstance(cwd_text, str) and cwd_text else None
    git_dir = _git_common_dir(cwd) if cwd is not None else None
    if git_dir is None:
        return {}
    dispatch_local = git_dir / "dispatch-local"
    if not dispatch_local.is_dir():
        return {}
    pending = _pending_inbox_entries(dispatch_local)
    if pending:
        lines = []
        for item in pending[:5]:
            event_info = item["event"]
            lines.append(
                f"- {item['task']}: {event_info.get('key', '(unreadable)')} "
                f"{event_info.get('event', '?')}@{event_info.get('revision', '?')} "
                f"from {event_info.get('sender', '?')}"
            )
        return {
            "decision": "block",
            "reason": (
                "Dispatch 收件箱还有未处理的交付事件，先调用 dispatch_inbox.py "
                "list 查看并用 done 处理：\n" + "\n".join(lines)
            ),
        }
    if not _repo_uses_dispatch(dispatch_local):
        return {}
    message = event.get("last_assistant_message")
    if isinstance(message, str) and message.strip():
        if _looks_delivered(message) or _looks_blocked(message):
            return {}
        return {
            "decision": "block",
            "reason": (
                "这一轮结束时既没有交付记录也没有阻塞说明。若你手里有待回发的"
                "已固定成果，请按派工单沿已授权的回程发一次；若确实没有待交付"
                "事项，在回复里写明状态即可。"
            ),
        }
    return {}


def main() -> int:
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}
    if not isinstance(event, dict):
        event = {}
    try:
        result = evaluate(event)
    except Exception:
        result = {}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
