"""Optional Q2 ordinary-observation commands over the canonical TPlan transaction.

This is not an Owner signer, scheduler, or separate result database. Principal is
an ordinary caller identity for replay matching, never an authorization claim.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

PROTOCOL = "tplan.command.v1"
STORE_SCHEMA = "tplan.command_results.v0.1"
CAPABILITY = "atomic_command_results"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
HASH = re.compile(r"sha256:[a-f0-9]{64}\Z")
MAX_REQUEST = 16 * 1024
MAX_RECORDS = 1024
MAX_STORE = 1024 * 1024
MAX_ARTIFACT = 4 * 1024 * 1024
MIN_FREE = 16 * 1024 * 1024
EXITS = {"invalid_request": 2, "unsupported_capability": 3, "recovery_required": 4,
         "runtime_mismatch": 5, "mission_unavailable": 6, "invalid_state": 7,
         "runtime_unavailable": 8, "query_failed": 9, "capacity_exceeded": 10,
         "command_not_found": 11, "guard_open": 12, "command_conflict": 13,
         "outcome_unknown": 14}
RESULT_KEYS = {"command_id", "action", "principal", "request_digest", "commit_id",
               "evidence_id", "evidence_digest", "committed_at"}


class CommandError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and ID.fullmatch(value) is not None


def validate_store(value: Any) -> list[str]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "records"}:
        return ["command_results shape is invalid"]
    if value["schema_version"] != STORE_SCHEMA or not isinstance(value["records"], dict):
        return ["command_results schema is unsupported"]
    errors = []
    for key, result in value["records"].items():
        if not valid_id(key) or not isinstance(result, dict) or set(result) != RESULT_KEYS:
            errors.append("command result record shape is invalid")
            continue
        if result["command_id"] != key or result["action"] != "evidence.record":
            errors.append("command result identity is invalid")
        if not all(valid_id(result[x]) for x in ("principal", "commit_id", "evidence_id")):
            errors.append("command result references are invalid")
        for field in ("request_digest", "evidence_digest"):
            if not isinstance(result[field], str) or not HASH.fullmatch(result[field]):
                errors.append("command result digest is invalid")
        try:
            dt = datetime.fromisoformat(result["committed_at"].replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError("timezone required")
        except (ValueError, TypeError, AttributeError):
            errors.append("command result time is invalid")
    return errors


def validate_request(request: Any, principal: str) -> None:
    required = {"protocol", "action", "mission_id", "command_id", "expected_build_hash"}
    if not isinstance(request, dict) or not valid_id(principal):
        raise CommandError("invalid_request", "Request and ordinary caller identity are required")
    expected = required | ({"payload"} if request.get("action") == "evidence.record" else set())
    if set(request) != expected or request.get("protocol") != PROTOCOL:
        raise CommandError("invalid_request", "Select the exact tplan.command.v1 fields")
    if request["action"] not in ("evidence.record", "command.get", "runtime.recover"):
        raise CommandError("invalid_request", "Unsupported Q2 action")
    if not all(valid_id(request[x]) for x in ("mission_id", "command_id")):
        raise CommandError("invalid_request", "Invalid request identity")
    if not isinstance(request["expected_build_hash"], str) or not HASH.fullmatch(request["expected_build_hash"]):
        raise CommandError("invalid_request", "An exact Host-selected runtime build is required")
    try:
        encoded = canonical(request).encode()
    except (ValueError, TypeError, RecursionError) as exc:
        raise CommandError("invalid_request", "Request must contain finite JSON values") from exc
    if len(encoded) > MAX_REQUEST:
        raise CommandError("invalid_request", "Request exceeds 16 KiB")
    if request["action"] == "evidence.record":
        value = request["payload"]
        if not isinstance(value, dict) or set(value) != {"summary", "task_id", "data"}:
            raise CommandError("invalid_request", "Observation payload fields are invalid")
        summary = value["summary"]
        if not isinstance(summary, str) or not summary.strip() or len(summary) > 2048 or any(c in summary for c in "\n\r"):
            raise CommandError("invalid_request", "Observation summary must be one nonempty line")
        if value["task_id"] is not None and not valid_id(value["task_id"]):
            raise CommandError("invalid_request", "Invalid task reference")
        if not isinstance(value["data"], dict):
            raise CommandError("invalid_request", "Observation data must be a JSON object")


def parse_request(raw: str) -> dict[str, Any]:
    if len(raw.encode()) > MAX_REQUEST:
        raise CommandError("invalid_request", "Request exceeds 16 KiB")
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise CommandError("invalid_request", "Duplicate JSON keys")
            result[k] = v
        return result
    def constant(value):
        raise CommandError("invalid_request", "Non-finite JSON values")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, RecursionError) as exc:
        raise CommandError("invalid_request", "Invalid request JSON") from exc


def envelope(request: Any, *, status="rejected", code=None, data=None, message="") -> dict:
    req = request if isinstance(request, dict) else {}
    return {"protocol": PROTOCOL, "mission_id": req.get("mission_id"),
            "command_id": req.get("command_id"), "action": req.get("action"),
            "ok": code is None, "status": status, "code": code, "message": message, "data": data}


def _check_paths(directory: Path) -> Path:
    if directory.is_symlink() or not directory.is_dir() or not (directory / "mission.json").is_file():
        raise CommandError("mission_unavailable", "Select an existing ordinary Mission directory")
    for name in ("mission.json", "mission.md", "evidence.jsonl", "execution_trace.jsonl",
                 ".execution_trace.lock", ".interaction-guard.json", ".mission-transaction.json"):
        p = directory / name
        if p.is_symlink() or (p.exists() and not p.is_file()):
            raise CommandError("mission_unavailable", "Mission files must not redirect outside their directory")
    return directory.resolve(strict=True)


def _load(runtime, directory: Path, request: dict) -> dict:
    _check_paths(directory)
    for name in ("mission.json", "evidence.jsonl", "execution_trace.jsonl", ".interaction-guard.json"):
        p = directory / name
        if p.exists() and p.stat().st_size > MAX_ARTIFACT:
            raise CommandError("capacity_exceeded", "Q2 source exceeds its bounded Mission scope")
    state = runtime._read_mission_unlocked(directory)
    if runtime.validate_mission(state) or state["mission"]["id"] != request["mission_id"]:
        raise CommandError("invalid_state", "Mission shape or identity is invalid")
    current = runtime.runtime_fingerprint()
    if current["build_hash"] != request["expected_build_hash"]:
        raise CommandError("runtime_mismatch", "Selected runtime differs from the requested build")
    report = runtime.runtime_provenance_report(state, current=current)
    if report["compatible"] is not True:
        raise CommandError("runtime_mismatch", "Use the original writer; Q2 never adopts legacy Missions")
    if CAPABILITY not in current["capabilities"] or "command_results" not in state:
        raise CommandError("unsupported_capability", "This Mission did not explicitly enable command results")
    return state


def _existing_evidence(runtime, directory: Path, state: dict) -> list:
    events = runtime._read_events_unlocked(directory)
    if any(runtime.validate_evidence_event(state, e, compatibility=True, internal=True) for e in events):
        raise CommandError("invalid_state", "Evidence records are invalid")
    by_id = {e["id"]: e for e in events}
    if len(by_id) != len(events):
        raise CommandError("invalid_state", "Evidence identities are duplicated")
    for result in state["command_results"]["records"].values():
        event = by_id.get(result["evidence_id"])
        if not event or event["event_type"] != "observation" or digest(event) != result["evidence_digest"]:
            raise CommandError("invalid_state", "Persisted command result has no matching observation")
    trace = runtime._read_execution_trace_unlocked(directory)
    if any(runtime.validate_execution_trace_record(state, record) for record in trace):
        raise CommandError("invalid_state", "Execution trace records are invalid")
    return events


def execute(directory: Path, request: Any, *, principal: str) -> tuple[dict, int]:
    """Apply one ordinary local action; never authenticate Owner or call external tools."""
    commit_started = False
    runtime = None
    try:
        validate_request(request, principal)
        import tplan_runtime as runtime
        directory = _check_paths(directory)
        with runtime.execution_trace_lock(directory):
            state = _load(runtime, directory, request)
            pending = runtime.mission_paths(directory)["transaction"].exists()
            if pending and request["action"] != "runtime.recover":
                raise CommandError("recovery_required", "Explicit recovery with the original writer is required")
            if request["action"] == "runtime.recover":
                commit_started = pending
                recovered = runtime._recover_pending_mission_transaction_unlocked(directory)
                state = _load(runtime, directory, request)
                _existing_evidence(runtime, directory, state)
                result = state["command_results"]["records"].get(request["command_id"])
                return envelope(request, status="recovered" if recovered else "read",
                                data={"recovered": recovered, "found": result is not None, "result": result},
                                message="Local recovery only; no external action was sent"), 0
            events = _existing_evidence(runtime, directory, state)
            records = state["command_results"]["records"]
            result = records.get(request["command_id"])
            if request["action"] == "command.get":
                if result is None:
                    raise CommandError("command_not_found", "No recorded local result; this does not prove external non-execution")
                return envelope(request, status="read", data=result, message="Historical command result only"), 0
            request_digest = digest({"request": request, "principal": principal})
            if result is not None:
                if result["request_digest"] != request_digest:
                    raise CommandError("command_conflict", "Command identity was already used with different content or caller")
                return envelope(request, status="replayed", data=result, message="Original committed result; no new write"), 0
            if runtime._read_interaction_guard_unlocked(directory) is not None:
                raise CommandError("guard_open", "Resolve the existing guard through its authorized path")
            value = request["payload"]
            event = runtime.prepare_event(directory, {"event_type": "observation", "summary": value["summary"],
                                                     "task_id": value["task_id"], "payload": value["data"]})
            if runtime.validate_evidence_event(state, event):
                raise CommandError("invalid_request", "Observation does not satisfy the existing evidence contract")
            result = {"command_id": request["command_id"], "action": "evidence.record", "principal": principal,
                      "request_digest": request_digest, "commit_id": "CQ" + uuid.uuid4().hex,
                      "evidence_id": event["id"], "evidence_digest": digest(event), "committed_at": runtime.now_iso()}
            after = copy.deepcopy(state)
            after["command_results"]["records"][request["command_id"]] = result
            store_bytes = len(canonical(after["command_results"]).encode())
            if len(records) >= MAX_RECORDS or store_bytes > MAX_STORE:
                raise CommandError("capacity_exceeded", "Command retention budget exhausted; retain facts and review capacity")
            mission_bytes = len(json.dumps(after, ensure_ascii=False, indent=2).encode()) + 1
            evidence_bytes = sum(len(json.dumps(e, ensure_ascii=False).encode()) + 1 for e in events + [event])
            if max(mission_bytes, evidence_bytes) > MAX_ARTIFACT:
                raise CommandError("capacity_exceeded", "Prospective canonical artifacts exceed the Q2 budget")
            trace_size = runtime.mission_paths(directory)["trace"].stat().st_size
            if shutil.disk_usage(directory).free < max(MIN_FREE, 2 * (mission_bytes + evidence_bytes + trace_size)):
                raise CommandError("capacity_exceeded", "Insufficient transaction headroom; no data was removed")
            commit_started = True
            runtime._commit_mission_state_unlocked(
                directory, state, after, source={"kind": "runtime_script", "name": "command_runtime"},
                prepared_evidence_events=[event], command_result_authority=runtime._COMMAND_RESULT_AUTHORITY)
            return envelope(request, status="committed", data=result, message="Observation and result committed together"), 0
    except CommandError as exc:
        status = "conflict" if exc.code == "command_conflict" else "recovery_required" if exc.code == "recovery_required" else "rejected"
        return envelope(request, status=status, code=exc.code, message=str(exc)), EXITS[exc.code]
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        code = "outcome_unknown" if commit_started else "invalid_state"
        return envelope(request, status=code if commit_started else "rejected", code=code,
                        message="Inspect the original command and pending transaction; do not create a new identity" if commit_started else "Request or selected state is invalid"), EXITS[code]
    except Exception as exc:
        code = "outcome_unknown" if commit_started else (
            "invalid_state" if runtime is not None and isinstance(exc, runtime.TplanError) else "runtime_unavailable")
        return envelope(request, status=code if commit_started else "rejected", code=code,
                        message="Use the original runtime and command identity to inspect the outcome"), EXITS[code]
