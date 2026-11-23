#!/usr/bin/env python3
"""Cross-chat delivery inbox for Codex Dispatch.

Stores delivery events under <git-common-dir>/dispatch-local/<task>/inbox/.
Four operations:

- ``put``: register a delivery event once. Re-putting the same event is a
  no-op (status ``duplicate`` or ``already_processed``); an event is never
  processed twice.
- ``list``: show pending events (default) or all events.
- ``confirm``: record the sender-side receipt check — whether the
  recipient's turn actually started and did not fail. ``isError:false``
  from the send tool only means the message left; confirmation is what
  turns a sent event into a received one.
- ``done``: mark one pending event as processed, exactly once.

An event is identified by the stable dispatch identity: task / round /
sender / event / revision (the attempt marker from the first brief).

The inbox directory lives under the repository's *common* git dir so all
worktrees of one repository share it, and it never enters the index
(``.git`` is not tracked). For non-git contexts pass ``--base-dir``.
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
from datetime import datetime, timezone
from pathlib import Path

EVENT_KINDS = {"milestone", "blocker", "delivery", "review"}
CONFIRM_OUTCOMES = {"received", "unexecuted", "unknown"}
SCHEMA_VERSION = "codex.dispatch_inbox.v0.1"
UNSAFE_KEY_RE = re.compile(r"[/\\\x00-\x1f\x7f]+")
MAX_KEY_LENGTH = 180


class InboxError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_key_part(value, field):
    if not isinstance(value, str) or not value.strip():
        raise InboxError(f"{field} must be a non-empty string")
    text_value = value.strip()
    if len(text_value) > 200:
        raise InboxError(f"{field} must be 200 characters or fewer")
    return text_value


def _git_common_dir(cwd: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    text_value = result.stdout.strip()
    if not text_value:
        return None
    path = Path(text_value)
    if not path.is_absolute():
        path = (cwd / path).resolve()
    return path if path.is_dir() else None


def inbox_root(task: str, *, base_dir: str | None, cwd: Path) -> Path:
    task = _safe_key_part(task, "task")
    if "/" in task or task.startswith("."):
        raise InboxError("task must be a simple name without '/' or a leading '.'")
    if base_dir:
        root = Path(base_dir).resolve()
    else:
        git_dir = _git_common_dir(cwd)
        if git_dir is None:
            raise InboxError(
                "not inside a git work tree; pass --base-dir to place the inbox"
            )
        root = git_dir
    return root / "dispatch-local" / task / "inbox"


def event_key(task: str, round_id: str, sender: str, kind: str, revision: str) -> str:
    parts = [
        _safe_key_part(task, "task"),
        _safe_key_part(round_id, "round"),
        _safe_key_part(sender, "sender"),
        _safe_key_part(kind, "event"),
        _safe_key_part(revision, "revision"),
    ]
    canonical = "__".join(parts)
    sanitized = UNSAFE_KEY_RE.sub("-", canonical).strip("-")
    if len(sanitized) <= MAX_KEY_LENGTH:
        return sanitized
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{sanitized[:MAX_KEY_LENGTH - 17]}-{digest}"


def _write_json(path: Path, payload: dict, *, exclusive: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".event-", suffix=".tmp", dir=str(path.parent)
    )
    tmp = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive:
            os.link(tmp, path)
            tmp.unlink()
        else:
            os.replace(tmp, path)
    except FileExistsError:
        if tmp.exists():
            tmp.unlink()
        raise
    finally:
        if tmp.exists():
            tmp.unlink()


def _event_paths(root: Path, key: str):
    return (
        root / "pending" / f"{key}.json",
        root / "processed" / f"{key}.json",
    )


def _read_event(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InboxError(f"inbox event file is unreadable: {path.name}") from exc
    if not isinstance(value, dict):
        raise InboxError(f"inbox event file is not an object: {path.name}")
    return value


def put_event(root: Path, *, key: str, fields: dict) -> dict:
    pending, processed = _event_paths(root, key)
    if processed.exists():
        return {"status": "already_processed", "key": key, "path": str(processed)}
    if pending.exists():
        existing = _read_event(pending)
        return {
            "status": "duplicate",
            "key": key,
            "path": str(pending),
            "registered_at": existing.get("registered_at"),
        }
    event = {
        "schema_version": SCHEMA_VERSION,
        "key": key,
        "registered_at": _now_iso(),
        "confirmation": None,
        "processed_at": None,
        "processor": None,
        **fields,
    }
    try:
        _write_json(pending, event, exclusive=True)
    except FileExistsError:
        return {"status": "duplicate", "key": key, "path": str(pending)}
    return {"status": "registered", "key": key, "path": str(pending)}


def list_events(root: Path, *, include_processed: bool) -> list[dict]:
    events = []
    for state, subdir in (("pending", "pending"), ("processed", "processed")):
        directory = root / subdir
        if not directory.is_dir():
            continue
        if state == "processed" and not include_processed:
            continue
        for path in sorted(directory.glob("*.json")):
            event = _read_event(path)
            event["_state"] = state
            events.append(event)
    events.sort(key=lambda e: e.get("registered_at", ""))
    return events


def done_event(root: Path, *, key: str, processor: str) -> dict:
    pending, processed = _event_paths(root, key)
    if processed.exists():
        event = _read_event(processed)
        return {
            "status": "already_processed",
            "key": key,
            "processed_at": event.get("processed_at"),
        }
    if not pending.exists():
        return {"status": "not_found", "key": key}
    event = _read_event(pending)
    event["processed_at"] = _now_iso()
    event["processor"] = processor
    _write_json(processed, event, exclusive=False)
    try:
        pending.unlink()
    except OSError:
        pass
    return {"status": "processed", "key": key, "processed_at": event["processed_at"]}


def confirm_event(root: Path, *, key: str, outcome: str, evidence: str, checker: str) -> dict:
    """Attach the sender-side receipt check to an event.

    ``outcome`` is ``received`` (the target turn ran and did not fail),
    ``unexecuted`` (the target session errored or its turn failed — the
    dispatch must not count as delivered) or ``unknown``.
    """
    if outcome not in CONFIRM_OUTCOMES:
        raise InboxError(
            "confirmation outcome must be one of " + ", ".join(sorted(CONFIRM_OUTCOMES))
        )
    pending, processed = _event_paths(root, key)
    if pending.exists():
        path = pending
    elif processed.exists():
        path = processed
    else:
        return {"status": "not_found", "key": key}
    event = _read_event(path)
    if event.get("confirmation") and event["confirmation"].get("outcome") == outcome:
        return {"status": "duplicate_confirmation", "key": key, "outcome": outcome}
    event["confirmation"] = {
        "outcome": outcome,
        "checked_at": _now_iso(),
        "checker": checker,
        "evidence": evidence,
    }
    _write_json(path, event, exclusive=False)
    return {"status": "confirmed", "key": key, "outcome": outcome}


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--task", required=True, help="dispatch task name")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="override the root that holds dispatch-local/ (default: git common dir)",
    )
    parser.add_argument(
        "--cwd",
        default=None,
        help="directory used to resolve the git common dir (default: pwd)",
    )


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register and dispose cross-chat delivery events once each.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    put = sub.add_parser("put", help="register one delivery event (idempotent)")
    _add_common(put)
    put.add_argument("--round", dest="round_id", required=True)
    put.add_argument("--sender", required=True, help="sending chat name or thread ref")
    put.add_argument(
        "--event",
        dest="kind",
        required=True,
        choices=sorted(EVENT_KINDS),
        help="event kind: milestone, blocker, delivery or review",
    )
    put.add_argument("--revision", required=True, help="fixed revision being reported")
    put.add_argument("--summary", default="", help="what the sender asks the reader to do")
    put.add_argument(
        "--payload-file",
        default=None,
        help="optional JSON file merged into the event as 'payload'",
    )

    listing = sub.add_parser("list", help="list pending events (or all with --all)")
    _add_common(listing)
    listing.add_argument("--all", action="store_true", help="include processed events")
    listing.add_argument("--json", action="store_true", dest="as_json")

    done = sub.add_parser("done", help="mark one pending event as processed, once")
    _add_common(done)
    done.add_argument("--key", required=True, help="event key from put/list")
    done.add_argument(
        "--processor",
        default=None,
        help="who processed it (default: session id or 'local')",
    )

    confirm = sub.add_parser(
        "confirm",
        help="record the sender-side receipt check on an event",
    )
    _add_common(confirm)
    confirm.add_argument("--key", required=True)
    confirm.add_argument(
        "--outcome", required=True, choices=sorted(CONFIRM_OUTCOMES),
        help="received | unexecuted | unknown",
    )
    confirm.add_argument(
        "--evidence", default="",
        help="what was checked, e.g. wait_threads snapshot or read_thread result",
    )

    return parser.parse_args(argv)


def _resolve_root(args) -> Path:
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    return inbox_root(args.task, base_dir=args.base_dir, cwd=cwd)


def _emit(result, code: int = 0) -> int:
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        root = _resolve_root(args)
        if args.command == "put":
            key = event_key(
                args.task, args.round_id, args.sender, args.kind, args.revision
            )
            fields = {
                "task": args.task,
                "round": args.round_id,
                "sender": args.sender,
                "event": args.kind,
                "revision": args.revision,
                "summary": args.summary,
            }
            if args.payload_file:
                try:
                    payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise InboxError(f"--payload-file is not readable JSON: {exc}")
                fields["payload"] = payload
            return _emit(put_event(root, key=key, fields=fields))
        if args.command == "list":
            events = list_events(root, include_processed=args.all)
            if args.as_json:
                return _emit({"task": args.task, "inbox": str(root), "events": events})
            for event in events:
                line = (
                    f"[{event['_state']}] {event.get('key')} "
                    f"{event.get('event')}@{event.get('revision')} "
                    f"from {event.get('sender')}"
                )
                if event.get("summary"):
                    line += f" — {event['summary']}"
                print(line)
            if not events:
                print(f"(empty) {root}")
            return 0
        if args.command == "done":
            processor = args.processor or os.environ.get("CODEX_SESSION_ID") or "local"
            return _emit(done_event(root, key=args.key, processor=processor))
        if args.command == "confirm":
            checker = os.environ.get("CODEX_SESSION_ID") or "local"
            return _emit(
                confirm_event(
                    root,
                    key=args.key,
                    outcome=args.outcome,
                    evidence=args.evidence,
                    checker=checker,
                )
            )
    except InboxError as exc:
        print(f"dispatch_inbox: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
