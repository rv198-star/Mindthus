#!/usr/bin/env python3
"""Transactional CLI for optional A-side TPlan collaboration state."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import collaboration


def _check_paths(directory: Path) -> Path:
    if directory.is_symlink() or not directory.is_dir() or not (directory / "mission.json").is_file():
        raise collaboration.CollaborationError("mission_unavailable", "Select an existing Mission directory")
    for name in (
        "mission.json",
        "mission.md",
        "evidence.jsonl",
        "execution_trace.jsonl",
        ".execution_trace.lock",
        ".interaction-guard.json",
        ".mission-transaction.json",
    ):
        path = directory / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise collaboration.CollaborationError(
                "mission_unavailable", "Mission files must not redirect outside their directory"
            )
    return directory.resolve(strict=True)


def _load(runtime: Any, directory: Path, request: dict[str, Any]) -> dict[str, Any]:
    _check_paths(directory)
    for name in ("mission.json", "evidence.jsonl", "execution_trace.jsonl", ".interaction-guard.json"):
        path = directory / name
        if path.exists() and path.stat().st_size > collaboration.MAX_ARTIFACT:
            raise collaboration.CollaborationError("capacity_exceeded", "A canonical artifact exceeds 4 MiB")
    state = runtime._read_mission_unlocked(directory)
    if runtime.validate_mission(state) or state.get("mission", {}).get("id") != request["mission_id"]:
        raise collaboration.CollaborationError("invalid_state", "Mission shape or identity is invalid")
    if runtime.validate_mission_directory_identity(state, directory):
        raise collaboration.CollaborationError("invalid_state", "Mission directory does not match its identity")
    current = runtime.runtime_fingerprint()
    if current["build_hash"] != request["expected_build_hash"]:
        raise collaboration.CollaborationError("runtime_mismatch", "Selected runtime differs from the requested build")
    report = runtime.runtime_provenance_report(state, current=current)
    if report.get("compatible") is not True:
        raise collaboration.CollaborationError(
            "runtime_mismatch", "Use the Mission's recorded runtime; collaboration never adopts an old build"
        )
    if collaboration.CAPABILITY not in current.get("capabilities", []):
        raise collaboration.CollaborationError("unsupported_capability", "This runtime lacks collaboration support")
    return state


def _existing_evidence(runtime: Any, directory: Path, state: dict[str, Any]) -> list[dict[str, Any]]:
    events = runtime._read_events_unlocked(directory)
    if any(runtime.validate_evidence_event(state, event, compatibility=True, internal=True) for event in events):
        raise collaboration.CollaborationError("invalid_state", "Evidence records are invalid")
    trace = runtime._read_execution_trace_unlocked(directory)
    if any(runtime.validate_execution_trace_record(state, record) for record in trace):
        raise collaboration.CollaborationError("invalid_state", "Execution trace records are invalid")
    return events


def expected_snapshot(runtime: Any, directory: Path, state: dict[str, Any]) -> dict[str, str]:
    evidence = runtime.mission_paths(directory)["evidence"]
    return {
        "mission_digest": runtime.mission_control_digest(state),
        "evidence_digest": "sha256:" + hashlib.sha256(evidence.read_bytes() if evidence.exists() else b"").hexdigest(),
    }


def _normalized_new_tasks(runtime: Any, state: dict[str, Any], raw_tasks: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_tasks, list) or len(raw_tasks) > 64:
        raise collaboration.CollaborationError("invalid_request", "new_tasks must be a bounded list")
    temporary = copy.deepcopy(state)
    normalized: list[dict[str, Any]] = []
    for raw in raw_tasks:
        if not isinstance(raw, dict):
            raise collaboration.CollaborationError("invalid_request", "new_tasks entries must be objects")
        task = runtime.normalize_task_for_mission(temporary, raw)
        temporary["tasks"].append(task)
        normalized.append(task)
    return normalized


def _reject_h1_task_mutation(runtime: Any, state: dict[str, Any], payload: dict[str, Any]) -> None:
    control = state.get("human_control")
    if not isinstance(control, dict):
        return
    protected = {
        request.get("business_task_id")
        for request in control.get("requests", {}).values()
        if isinstance(request, dict)
    }
    changed = {item.get("task_id") for item in payload.get("task_changes", []) if isinstance(item, dict)}
    if changed & protected:
        raise collaboration.CollaborationError(
            "invalid_request", "H1-controlled task completion and status remain under the H1 writer"
        )


def _validate_recovery_request(runtime: Any, directory: Path, request: dict[str, Any]) -> None:
    """Verify request identity/build and prepared-state compatibility before any roll-forward write."""
    _check_paths(directory)
    state = runtime._read_mission_unlocked(directory)
    if not isinstance(state.get("mission"), dict) or state["mission"].get("id") != request["mission_id"]:
        raise collaboration.CollaborationError("invalid_state", "Recovery request mission_id does not match the Mission")
    if runtime.validate_mission_directory_identity(state, directory):
        raise collaboration.CollaborationError("invalid_state", "Mission directory does not match its identity")
    current = runtime.runtime_fingerprint()
    if current["build_hash"] != request["expected_build_hash"]:
        raise collaboration.CollaborationError("runtime_mismatch", "Recovery request build differs from the selected runtime")
    if runtime.runtime_provenance_report(state, current=current).get("compatible") is not True:
        raise collaboration.CollaborationError("runtime_mismatch", "Recovery requires the Mission's recorded compatible runtime")
    if collaboration.CAPABILITY not in current.get("capabilities", []):
        raise collaboration.CollaborationError("unsupported_capability", "This runtime lacks collaboration support")
    transaction_path = runtime.mission_paths(directory)["transaction"]
    if transaction_path.exists():
        transaction = runtime.read_json(transaction_path)
        prepared = transaction.get("mission")
        if not isinstance(prepared, dict) or prepared.get("mission", {}).get("id") != request["mission_id"]:
            raise collaboration.CollaborationError("invalid_state", "Prepared transaction belongs to a different Mission")
        if runtime.validate_mission(prepared):
            raise collaboration.CollaborationError("invalid_state", "Prepared transaction Mission shape is invalid")
        if runtime.runtime_provenance_report(prepared, current=current).get("compatible") is not True:
            raise collaboration.CollaborationError("runtime_mismatch", "Prepared transaction runtime differs from the selected build")


def _capacity_check(
    runtime: Any,
    directory: Path,
    before: dict[str, Any],
    after: dict[str, Any],
    events: list[dict[str, Any]],
) -> None:
    mission_bytes = len(json.dumps(after, ensure_ascii=False, indent=2).encode("utf-8")) + 1
    evidence_bytes = sum(len(json.dumps(event, ensure_ascii=False).encode("utf-8")) + 1 for event in events)
    trace = runtime.mission_paths(directory)["trace"]
    trace_size = trace.stat().st_size if trace.exists() else 0
    new_records = runtime._state_change_trace_records(
        before, after, source={"kind": "runtime_script", "name": "collaboration_runtime"}
    )
    appended_trace = sum(len(json.dumps(record, ensure_ascii=False).encode("utf-8")) + 1 for record in new_records)
    prospective_trace = trace_size + appended_trace
    if max(mission_bytes, evidence_bytes, prospective_trace) > collaboration.MAX_ARTIFACT:
        raise collaboration.CollaborationError("capacity_exceeded", "Prospective canonical artifacts exceed 4 MiB")
    if shutil.disk_usage(directory).free < max(
        collaboration.MIN_FREE, 2 * (mission_bytes + evidence_bytes + prospective_trace)
    ):
        raise collaboration.CollaborationError("capacity_exceeded", "Insufficient transaction headroom")


def _snapshot_data(runtime: Any, directory: Path, state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "mission_id": state["mission"]["id"],
        "survey": runtime.build_survey_from_state(state, events),
        "collaboration": copy.deepcopy(state.get("collaboration")),
        "resume": collaboration.build_resume_view(state, events),
        "expected_snapshot": expected_snapshot(runtime, directory, state),
        "capability": collaboration.CAPABILITY,
        "native_binding_capability": collaboration.BINDING_CAPABILITY,
    }


def execute(directory: Path, request: Any, *, principal: str) -> tuple[dict[str, Any], int]:
    commit_started = False
    runtime = None
    try:
        collaboration.validate_request(request)
        if not collaboration.valid_id(principal):
            raise collaboration.CollaborationError("invalid_request", "Principal must be a bounded identity")
        import tplan_runtime as runtime

        directory = _check_paths(Path(directory))
        with runtime.execution_trace_lock(directory):
            pending = runtime.mission_paths(directory)["transaction"].exists()
            if request["action"] == "runtime.recover":
                _validate_recovery_request(runtime, directory, request)
                commit_started = pending
                recovered = runtime._recover_pending_mission_transaction_unlocked(directory)
                state = _load(runtime, directory, request)
                events = _existing_evidence(runtime, directory, state)
                record = (
                    state.get("collaboration", {}).get("commands", {}).get(request["command_id"])
                    if isinstance(state.get("collaboration"), dict)
                    else None
                )
                return collaboration.envelope(
                    request,
                    status="recovered" if recovered else "read",
                    data={"recovered": recovered, "result": copy.deepcopy(record), "snapshot": _snapshot_data(runtime, directory, state, events)},
                    message="Recovered only already-prepared canonical transaction content",
                ), 0
            if pending:
                raise collaboration.CollaborationError(
                    "recovery_required", "Use the original writer's runtime.recover before another mutation"
                )
            state = _load(runtime, directory, request)
            events = _existing_evidence(runtime, directory, state)
            collab = state.get("collaboration") if isinstance(state.get("collaboration"), dict) else None
            existing_record = collab.get("commands", {}).get(request["command_id"]) if collab else None

            if request["action"] == "snapshot.get":
                return collaboration.envelope(
                    request,
                    status="read",
                    data=_snapshot_data(runtime, directory, state, events),
                    message="Read-only collaboration projection",
                ), 0
            if request["action"] == "command.get":
                if existing_record is None:
                    raise collaboration.CollaborationError(
                        "command_not_found", "No such command identity is recorded; this does not prove external non-execution"
                    )
                return collaboration.envelope(
                    request,
                    status="read",
                    data=copy.deepcopy(existing_record),
                    message="Historical command result only",
                ), 0

            request_digest = collaboration.digest({"request": request, "principal": principal})
            if existing_record is not None:
                if existing_record.get("request_digest") != request_digest:
                    raise collaboration.CollaborationError(
                        "command_conflict", "Command identity was already used with different content or principal"
                    )
                replay_data = copy.deepcopy(existing_record["data"])
                replay_data["expected_snapshot"] = expected_snapshot(runtime, directory, state)
                return collaboration.envelope(
                    request,
                    status="replayed",
                    data=replay_data,
                    message="Original committed result; no new business effect",
                ), 0
            if state.get("mission", {}).get("status") != "active":
                raise collaboration.CollaborationError(
                    "mission_closed",
                    "Mission is not active; its completed business boundary is preserved. Late facts require a follow-up Mission or legal continuation; reads, replay, and recovery remain available.",
                )
            if runtime._read_interaction_guard_unlocked(directory) is not None:
                raise collaboration.CollaborationError(
                    "guard_open", "Resolve the existing interaction guard through its authorized path"
                )
            current_snapshot = expected_snapshot(runtime, directory, state)
            if request["expected_snapshot"] != current_snapshot:
                raise collaboration.CollaborationError(
                    "stale_snapshot", "Mission or evidence changed; reload the collaboration snapshot"
                )
            _reject_h1_task_mutation(runtime, state, request["payload"])
            normalized_tasks = (
                _normalized_new_tasks(runtime, state, request["payload"].get("new_tasks"))
                if request["action"] == "feedback.resolve"
                else []
            )
            event_ids = {event.get("id") for event in events if isinstance(event.get("id"), str)}
            evidence_refs = request["payload"].get("evidence_refs", [])
            if not isinstance(evidence_refs, list) or any(ref not in event_ids for ref in evidence_refs):
                raise collaboration.CollaborationError("invalid_request", "evidence_refs must resolve to current events")
            after, data, command_status = collaboration.apply_command(
                state,
                action=request["action"],
                payload=request["payload"],
                command_id=request["command_id"],
                principal=principal,
                request_digest=request_digest,
                now=runtime.now_iso(),
                normalized_new_tasks=normalized_tasks,
                events=events,
            )
            transition_findings = collaboration.validate_transition(state, after)
            if transition_findings:
                raise collaboration.CollaborationError("invalid_state", "; ".join(transition_findings))
            state_findings = collaboration.validate_state(after)
            if state_findings:
                raise collaboration.CollaborationError("invalid_state", "; ".join(state_findings))
            mission_findings = runtime.validate_mission(after)
            if mission_findings:
                raise collaboration.CollaborationError("invalid_state", "; ".join(mission_findings))
            completion_findings = collaboration.task_completion_findings(state, after, events)
            if completion_findings:
                raise collaboration.CollaborationError("review_required", "; ".join(completion_findings))
            _capacity_check(runtime, directory, state, after, events)
            commit_started = True
            runtime._commit_mission_state_unlocked(
                directory,
                state,
                after,
                source={"kind": "runtime_script", "name": "collaboration_runtime"},
                latest_state=f"Collaboration {request['action']} committed.",
                collaboration_control_authority=runtime._COLLABORATION_CONTROL_AUTHORITY,
            )
            final_state = runtime._read_mission_unlocked(directory)
            response_data = copy.deepcopy(data)
            response_data["expected_snapshot"] = expected_snapshot(runtime, directory, final_state)
            return collaboration.envelope(
                request,
                status=command_status,
                data=response_data,
                message="Collaboration facts committed atomically",
            ), 0
    except collaboration.CollaborationError as exc:
        status = {
            "command_conflict": "conflict",
            "feedback_conflict": "conflict",
            "execution_in_flight": "conflict",
            "stale_snapshot": "conflict",
            "stale_generation": "conflict",
            "recovery_required": "recovery_required",
        }.get(exc.code, "rejected")
        return collaboration.envelope(request, status=status, code=exc.code, message=str(exc)), collaboration.EXITS[exc.code]
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        code = "outcome_unknown" if commit_started else "invalid_state"
        message = (
            "Inspect the original command and recover the prepared transaction; do not create a new identity"
            if commit_started
            else "Request or selected state is invalid"
        )
        return collaboration.envelope(request, status=code, code=code, message=message), collaboration.EXITS[code]
    except Exception as exc:
        code = "outcome_unknown" if commit_started else (
            "invalid_state" if runtime is not None and isinstance(exc, runtime.TplanError) else "runtime_unavailable"
        )
        return collaboration.envelope(
            request,
            status=code,
            code=code,
            message="Use the original runtime and command identity to inspect the outcome",
        ), collaboration.EXITS[code]


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise collaboration.CollaborationError(
            "invalid_request", "Expected --mission-dir, --principal, and --request-file"
        )


def main() -> int:
    parser = Parser(description=__doc__)
    parser.add_argument("--mission-dir", required=True, type=Path)
    parser.add_argument("--principal", required=True)
    parser.add_argument("--request-file", required=True, help="JSON request file, or - for stdin")
    try:
        args = parser.parse_args()
        raw = sys.stdin.read() if args.request_file == "-" else Path(args.request_file).read_text(encoding="utf-8")
        request = collaboration.parse_request(raw)
        result, status = execute(args.mission_dir, request, principal=args.principal)
    except (collaboration.CollaborationError, OSError) as exc:
        code = exc.code if isinstance(exc, collaboration.CollaborationError) else "invalid_request"
        result = collaboration.envelope({}, code=code, message=str(exc))
        status = collaboration.EXITS[code]
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
