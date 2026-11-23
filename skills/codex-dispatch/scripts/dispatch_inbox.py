#!/usr/bin/env python3
"""Cross-chat delivery inbox for Codex Dispatch.

Stores delivery events under <git-common-dir>/dispatch-local/<task>/inbox/.
Operations:

- ``bind``: register the round's return obligation (task / round / worker /
  recipient). Recorded once at dispatch time; the Stop hook uses it — not
  reply text — to decide who owes what.
- ``discharge``: close an obligation once the delivery (or a blocker) for
  that round has been registered.
- ``put``: register a delivery event once, naming its ``recipient`` session.
  Re-putting the same event is a no-op (``duplicate`` / ``already_processed``).
- ``list``: show pending events (default) or all events.
- ``confirm``: record the sender-side receipt check — whether the
  recipient's turn actually started and did not fail. ``isError:false``
  from the send tool only means the message left.
- ``defer`` / ``resume``: A parks an event it is deliberately not handling
  yet (for example while waiting on the user) so it does not re-trigger
  the Stop hook every turn.
- ``done``: mark one pending event as processed, exactly once. Only the
  event's named recipient may do this unless ``--force`` is given;
  a refusal exits non-zero.
- ``takeover`` / ``release``: mark or clear a session the user has taken
  over; the Stop hook and heartbeat stand down for it until released.

An event's stable identity is task / round / sender / event / revision
(the attempt marker from the first brief).

The inbox lives under the repository's *common* git dir so all worktrees
share it, and it never enters the index. Because several sessions can
share one repo, every event names its ``recipient`` session id: only
that session is reminded of pending work and only it may ``done`` the
event. For non-git contexts pass ``--base-dir``.
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
SCHEMA_VERSION = "codex.dispatch_inbox.v0.2"
UNSAFE_KEY_RE = re.compile(r"[/\\\x00-\x1f\x7f]+")
MAX_KEY_LENGTH = 180
OBLIGATIONS_FILENAME = "obligations.json"


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


def dispatch_root(task: str | None, *, base_dir: str | None, cwd: Path) -> Path:
    if base_dir:
        root = Path(base_dir).resolve()
    else:
        git_dir = _git_common_dir(cwd)
        if git_dir is None:
            raise InboxError(
                "not inside a git work tree; pass --base-dir to place the inbox"
            )
        root = git_dir
    root = root / "dispatch-local"
    if task is None:
        return root
    task = _safe_key_part(task, "task")
    if "/" in task or task.startswith("."):
        raise InboxError("task must be a simple name without '/' or a leading '.'")
    return root / task


def inbox_root(task: str, *, base_dir: str | None, cwd: Path) -> Path:
    return dispatch_root(task, base_dir=base_dir, cwd=cwd) / "inbox"


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


# --- obligations -----------------------------------------------------------

def _obligations_path(dispatch_dir: Path) -> Path:
    return dispatch_dir / OBLIGATIONS_FILENAME


def _read_obligations(dispatch_dir: Path) -> dict:
    path = _obligations_path(dispatch_dir)
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InboxError("obligations file is unreadable") from exc
    if not isinstance(value, dict):
        raise InboxError("obligations file is not an object")
    return value


def _obligation_key(task: str, round_id: str, worker: str, recipient: str) -> str:
    return event_key(task, round_id, worker, "obligation", recipient)


def bind_obligation(dispatch_dir: Path, *, task, round_id, worker, recipient,
                    expected_kinds=None) -> dict:
    """Record the round's return obligation once at dispatch time."""
    obligations = _read_obligations(dispatch_dir)
    key = _obligation_key(task, round_id, worker, recipient)
    if key in obligations and obligations[key].get("status") == "open":
        return {"status": "duplicate", "key": key}
    record = {
        "key": key,
        "task": task,
        "round": round_id,
        "worker": worker,
        "recipient": recipient,
        "expected_kinds": expected_kinds or ["delivery", "blocker"],
        "status": "open",
        "bound_at": _now_iso(),
        "discharged_at": None,
    }
    obligations[key] = record
    _write_json(_obligations_path(dispatch_dir), obligations, exclusive=False)
    return {"status": "bound", "key": key, "obligation": record}


def discharge_obligation(dispatch_dir: Path, *, key: str, evidence: str) -> dict:
    obligations = _read_obligations(dispatch_dir)
    record = obligations.get(key)
    if record is None:
        return {"status": "not_found", "key": key}
    if record.get("status") == "discharged":
        return {"status": "duplicate", "key": key}
    record["status"] = "discharged"
    record["discharged_at"] = _now_iso()
    record["discharge_evidence"] = evidence
    _write_json(_obligations_path(dispatch_dir), obligations, exclusive=False)
    return {"status": "discharged", "key": key}


def list_obligations(dispatch_dir: Path, *, only_open: bool) -> list[dict]:
    obligations = _read_obligations(dispatch_dir)
    records = list(obligations.values())
    if only_open:
        records = [r for r in records if r.get("status") == "open"]
    records.sort(key=lambda r: r.get("bound_at", ""))
    return records


# --- events ----------------------------------------------------------------

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
        "deferred": False,
        "deferred_reason": None,
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


def _load_event_for_update(root: Path, key: str):
    pending, processed = _event_paths(root, key)
    if pending.exists():
        return pending, "pending"
    if processed.exists():
        return processed, "processed"
    return None, None


def done_event(root: Path, *, key: str, processor: str, force: bool) -> dict:
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
    recipient = event.get("recipient")
    if recipient and processor != recipient and not force:
        return {
            "status": "forbidden",
            "key": key,
            "reason": f"only recipient '{recipient}' may dispose this event "
                      f"(pass --force to override)",
        }
    event["processed_at"] = _now_iso()
    event["processor"] = processor
    _write_json(processed, event, exclusive=False)
    try:
        pending.unlink()
    except OSError:
        pass
    return {"status": "processed", "key": key, "processed_at": event["processed_at"]}


def defer_event(root: Path, *, key: str, deferred: bool, reason: str, actor: str) -> dict:
    path, state = _load_event_for_update(root, key)
    if path is None:
        return {"status": "not_found", "key": key}
    event = _read_event(path)
    event["deferred"] = deferred
    event["deferred_reason"] = reason if deferred else None
    event["deferred_by"] = actor if deferred else None
    _write_json(path, event, exclusive=False)
    return {"status": "deferred" if deferred else "resumed", "key": key}


def confirm_event(root: Path, *, key: str, outcome: str, evidence: str, checker: str) -> dict:
    """Attach the sender-side receipt check to an event."""
    if outcome not in CONFIRM_OUTCOMES:
        raise InboxError(
            "confirmation outcome must be one of " + ", ".join(sorted(CONFIRM_OUTCOMES))
        )
    path, _state = _load_event_for_update(root, key)
    if path is None:
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


# --- CLI -------------------------------------------------------------------

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

    bind = sub.add_parser(
        "bind",
        help="record the round's return obligation at dispatch time",
    )
    _add_common(bind)
    bind.add_argument("--round", dest="round_id", required=True)
    bind.add_argument("--worker", required=True, help="worker session id")
    bind.add_argument("--recipient", required=True, help="collecting session id")
    bind.add_argument(
        "--kinds",
        default="delivery,blocker",
        help="comma-separated event kinds that discharge this obligation",
    )

    discharge = sub.add_parser(
        "discharge",
        help="close an obligation after its delivery or blocker registered",
    )
    _add_common(discharge)
    discharge.add_argument("--key", required=True)
    discharge.add_argument("--evidence", default="")

    obligations = sub.add_parser(
        "obligations",
        help="list open (or all) return obligations for a task",
    )
    _add_common(obligations)
    obligations.add_argument("--all", action="store_true")
    obligations.add_argument("--json", action="store_true", dest="as_json")

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
    put.add_argument(
        "--recipient",
        required=True,
        help="session id that owns (and may dispose) this event",
    )
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
        help="session id doing the processing (default: CODEX_SESSION_ID or 'local')",
    )
    done.add_argument(
        "--force",
        action="store_true",
        help="override the recipient-only disposal check",
    )

    defer = sub.add_parser(
        "defer",
        help="park an event so the Stop hook stops reminding about it",
    )
    _add_common(defer)
    defer.add_argument("--key", required=True)
    defer.add_argument("--reason", default="")

    resume = sub.add_parser("resume", help="un-park a deferred event")
    _add_common(resume)
    resume.add_argument("--key", required=True)

    takeover = sub.add_parser(
        "takeover",
        help="mark a session as taken over by the user (hook/heartbeat stand down)",
    )
    takeover.add_argument("--task", required=False, default="-",
                          help="any task name; the marker is repo-wide")
    takeover.add_argument(
        "--base-dir", default=None,
        help="override the root that holds dispatch-local/ (default: git common dir)",
    )
    takeover.add_argument("--cwd", default=None)
    takeover.add_argument("--session", required=True, help="session id being taken over")
    takeover.add_argument("--note", default="")

    release = sub.add_parser(
        "release",
        help="clear a session's takeover marker so checks resume",
    )
    release.add_argument("--task", required=False, default="-",
                         help="any task name; the marker is repo-wide")
    release.add_argument("--base-dir", default=None)
    release.add_argument("--cwd", default=None)
    release.add_argument("--session", required=True)

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


TAKEOVER_FILENAME = "takeover.json"


def _takeover_path(dispatch_dir: Path) -> Path:
    # Repo-wide marker: lives at dispatch-local/takeover.json, one level
    # above per-task dirs.
    return dispatch_dir.parent / TAKEOVER_FILENAME


def _read_takeover(dispatch_dir: Path) -> dict:
    path = _takeover_path(dispatch_dir)
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def takeover_session(dispatch_dir: Path, *, session: str, note: str) -> dict:
    state = _read_takeover(dispatch_dir)
    state[session] = {"since": _now_iso(), "note": note}
    _write_json(_takeover_path(dispatch_dir), state, exclusive=False)
    return {"status": "taken_over", "session": session}


def release_session(dispatch_dir: Path, *, session: str) -> dict:
    state = _read_takeover(dispatch_dir)
    if session not in state:
        return {"status": "not_taken_over", "session": session}
    state.pop(session)
    _write_json(_takeover_path(dispatch_dir), state, exclusive=False)
    return {"status": "released", "session": session}


def _resolve_dispatch_dir(args) -> Path:
    cwd = Path(args.cwd).resolve() if args.cwd else Path.cwd()
    return dispatch_root(args.task, base_dir=args.base_dir, cwd=cwd)


def _emit(result, code: int = 0) -> int:
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return code


def _session_id() -> str:
    return os.environ.get("CODEX_SESSION_ID") or "local"


def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        dispatch_dir = _resolve_dispatch_dir(args)
        root = dispatch_dir / "inbox"
        if args.command == "bind":
            kinds = [k.strip() for k in args.kinds.split(",") if k.strip()]
            return _emit(
                bind_obligation(
                    dispatch_dir,
                    task=args.task,
                    round_id=args.round_id,
                    worker=args.worker,
                    recipient=args.recipient,
                    expected_kinds=kinds,
                )
            )
        if args.command == "discharge":
            return _emit(
                discharge_obligation(
                    dispatch_dir, key=args.key, evidence=args.evidence
                )
            )
        if args.command == "obligations":
            records = list_obligations(dispatch_dir, only_open=not args.all)
            if args.as_json:
                return _emit({"task": args.task, "obligations": records})
            for record in records:
                print(
                    f"[{record['status']}] {record['key']} "
                    f"worker={record['worker']} -> {record['recipient']} "
                    f"expects {','.join(record.get('expected_kinds', []))}"
                )
            if not records:
                print(f"(none) {dispatch_dir}")
            return 0
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
                "recipient": args.recipient,
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
                marker = ""
                if event.get("deferred"):
                    marker = " DEFERRED"
                line = (
                    f"[{event['_state']}{marker}] {event.get('key')} "
                    f"{event.get('event')}@{event.get('revision')} "
                    f"from {event.get('sender')} -> {event.get('recipient', '?')}"
                )
                if event.get("summary"):
                    line += f" — {event['summary']}"
                print(line)
            if not events:
                print(f"(empty) {root}")
            return 0
        if args.command == "done":
            processor = args.processor or _session_id()
            result = done_event(root, key=args.key, processor=processor, force=args.force)
            code = 0
            if result.get("status") in {"forbidden", "not_found"}:
                code = 3
            return _emit(result, code)
        if args.command == "defer":
            return _emit(
                defer_event(
                    root, key=args.key, deferred=True,
                    reason=args.reason, actor=_session_id(),
                )
            )
        if args.command == "resume":
            return _emit(
                defer_event(root, key=args.key, deferred=False, reason="",
                            actor=_session_id())
            )
        if args.command == "confirm":
            return _emit(
                confirm_event(
                    root,
                    key=args.key,
                    outcome=args.outcome,
                    evidence=args.evidence,
                    checker=_session_id(),
                )
            )
        if args.command == "takeover":
            return _emit(
                takeover_session(
                    dispatch_dir, session=args.session, note=args.note
                )
            )
        if args.command == "release":
            return _emit(
                release_session(dispatch_dir, session=args.session)
            )
    except InboxError as exc:
        print(f"dispatch_inbox: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
