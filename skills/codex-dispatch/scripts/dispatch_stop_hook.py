#!/usr/bin/env python3
"""Codex Stop hook for Dispatch cross-chat handoffs.

Installed at user scope (~/.codex/hooks.json). On every turn stop it:

1. Writes a liveness timestamp under <git-common-dir>/dispatch-local/
   (or a cache/home fallback outside a repo). Dispatch reads that
   timestamp — not config — to decide whether the hook is running.
2. Lets the turn end when ``stop_hook_active`` is already true (the hook
   may interrupt a turn only once).
3. Otherwise checks the repo's ``dispatch-local`` state for work bound
   to *this* session, never to reply text:

   - Coordinator check: any pending, non-deferred inbox event whose
     ``recipient`` equals this ``session_id`` — A still owes disposal.
   - Worker check: any open obligation whose ``worker`` equals this
     ``session_id`` and for which no expected event kind (delivery or
     blocker) has been registered for its round — B may have finished
     without its return send.

   Sessions unrelated to either check are never interrupted, even in a
   repo that takes part in dispatch.

   A session the user has taken over (recorded in
   ``dispatch-local/takeover.json`` by ``dispatch_inbox.py takeover``)
   is skipped entirely until ``release`` clears the marker.

Codex Stop contract: exit 0 with a JSON object on stdout. ``decision:
"block"`` plus ``reason`` makes Codex continue the turn with that
reason as a new prompt; ``{}`` lets the turn end.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LIVENESS_FILENAME = "hook-last-run.json"
SCHEMA_VERSION = "codex.dispatch_stop_hook.v0.2"
OBLIGATIONS_FILENAME = "obligations.json"
TAKEOVER_FILENAME = "takeover.json"
# Every block reason starts with this marker so hosts (and the
# interjection rules) can tell hook-injected prompts from messages a
# human actually typed.
HOOK_REASON_PREFIX = "[dispatch-hook]"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hook_dir() -> Path:
    return Path(__file__).resolve().parent


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
    # Only a real Stop-hook run proves liveness. Records without a
    # session_id (unit tests, manual probes) or for other hook events
    # must not make the hook look alive.
    if event.get("hook_event_name") != "Stop":
        return None
    session = event.get("session_id")
    if not isinstance(session, str) or not session:
        return None
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


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _iter_task_dirs(dispatch_local: Path):
    if not dispatch_local.is_dir():
        return
    for child in sorted(dispatch_local.iterdir()):
        if child.is_dir() and child.name != ".tmp":
            yield child


def _pending_events_for(task_dir: Path, session_id: str) -> list[dict]:
    """Pending, non-deferred events addressed to this session."""
    pending_dir = task_dir / "inbox" / "pending"
    out = []
    if not pending_dir.is_dir():
        return out
    for path in sorted(pending_dir.glob("*.json")):
        event = _read_json(path)
        if not isinstance(event, dict):
            continue
        if event.get("deferred"):
            continue
        if event.get("recipient") != session_id:
            continue
        out.append(event)
    return out


def _inbox_has_event(task_dir: Path, round_id: str, kinds) -> bool:
    """Whether any event for ``round_id`` with one of ``kinds`` was ever registered."""
    for state in ("pending", "processed"):
        directory = task_dir / "inbox" / state
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            event = _read_json(path)
            if not isinstance(event, dict):
                continue
            if event.get("round") != round_id:
                continue
            if event.get("event") in kinds:
                return True
    return False


def _open_obligations_for(task_dir: Path, session_id: str) -> list[dict]:
    """Open obligations where this session is the worker."""
    obligations_path = task_dir / OBLIGATIONS_FILENAME
    obligations = _read_json(obligations_path)
    if not isinstance(obligations, dict):
        return []
    out = []
    for record in obligations.values():
        if not isinstance(record, dict):
            continue
        if record.get("status") != "open":
            continue
        if record.get("worker") != session_id:
            continue
        out.append(record)
    return out


def _inbox_cli() -> str:
    """Absolute path to dispatch_inbox.py for use in reminders."""
    return str(_hook_dir() / "dispatch_inbox.py")


def _is_taken_over(dispatch_local: Path, session_id: str) -> bool:
    """Whether the user currently holds this session.

    The marker is repo-wide (one level above the per-task dirs) and is
    written by dispatch_inbox.py takeover.
    """
    state = _read_json(dispatch_local / TAKEOVER_FILENAME)
    return isinstance(state, dict) and session_id in state


def evaluate(event: dict) -> dict:
    liveness_path = _write_liveness(event)
    if event.get("stop_hook_active") is True:
        return {}
    session_id = event.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return {}
    cwd_text = event.get("cwd")
    cwd = Path(cwd_text).resolve() if isinstance(cwd_text, str) and cwd_text else None
    if cwd is None:
        return {}
    git_dir = _git_common_dir(cwd)
    if git_dir is None:
        return {}
    dispatch_local = git_dir / "dispatch-local"
    if not dispatch_local.is_dir():
        return {}
    if _is_taken_over(dispatch_local, session_id):
        return {}
    inbox_cli = _inbox_cli()

    # Coordinator check: pending events addressed to me.
    pending_lines = []
    for task_dir in _iter_task_dirs(dispatch_local):
        for event in _pending_events_for(task_dir, session_id):
            pending_lines.append(
                f"- {event.get('task', task_dir.name)}: {event.get('key')} "
                f"{event.get('event')}@{event.get('revision')} from {event.get('sender', '?')}"
            )
    if pending_lines:
        return {
            "decision": "block",
            "reason": (
                HOOK_REASON_PREFIX + " "
                "Dispatch 收件箱里还有未处理的交付事件（指名给你这个会话）。"
                f"先运行 `{inbox_cli} list --task <任务>` 查看，"
                "再用 `done --key <key>` 逐项处置；"
                "确实需要暂缓的事件用 `defer --key <key> --reason <原因>` 挂起。\n"
                + "\n".join(pending_lines[:8])
            ),
        }

    # Worker check: open obligations where I owe a return event.
    owe_lines = []
    for task_dir in _iter_task_dirs(dispatch_local):
        for record in _open_obligations_for(task_dir, session_id):
            kinds = record.get("expected_kinds") or ["delivery", "blocker"]
            if _inbox_has_event(task_dir, record["round"], kinds):
                continue
            owe_lines.append(
                f"- {record.get('task', task_dir.name)} round {record['round']}: "
                f"应向 {record.get('recipient')} 交付 {','.join(kinds)}，"
                "尚未在收件箱登记"
            )
    if owe_lines:
        return {
            "decision": "block",
            "reason": (
                HOOK_REASON_PREFIX + " "
                "你有尚未完成的交付义务。把固定成果写入收件箱"
                f"（`{inbox_cli} put ...`）后沿已授权的回程发一次；"
                "若确实受阻，写一条 blocker 事件再说明状态。\n"
                + "\n".join(owe_lines[:8])
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
