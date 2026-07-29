#!/usr/bin/env python3
"""Route stable Codex hook callbacks to explicitly bound TPlan Missions."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:  # pragma: no cover - platform import
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback
    fcntl = None

try:  # pragma: no cover - platform import
    import msvcrt
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None

from codex_telemetry_adapter import (
    _canonical_mission_dir,
    _persist_state_and_coverage,
    _prepare_bind_session_state_unlocked,
    _read_state,
    _safe_id,
    _state_path,
    _validate_state_target,
    _validated_state_dir,
    coverage_path,
    handle_hook,
)
from tplan_runtime import (
    TplanError,
    _trace_mission_id,
    execution_trace_lock,
    now_iso,
    read_mission,
    write_json,
)


REGISTRY_SCHEMA_VERSION = "tplan.codex_telemetry_registry.v0.1"
DISPATCHER_VERSION = "tplan.codex_telemetry_dispatcher.v0.1"
REGISTRY_FILENAME = "tplan-codex-telemetry-registry.json"
REGISTRY_LOCK_FILENAME = ".tplan-codex-telemetry-registry.lock"
REGISTRY_THREAD_LOCK = threading.RLock()


def registry_path(state_dir: Path) -> Path:
    return state_dir.resolve() / REGISTRY_FILENAME


def _validated_registry_state_dir(state_dir: Path) -> Path:
    resolved = state_dir.resolve()
    if not resolved.is_dir():
        raise TplanError("--state-dir must be a pre-created host-controlled directory")
    return resolved


def _empty_registry() -> dict[str, Any]:
    timestamp = now_iso()
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "dispatcher_version": DISPATCHER_VERSION,
        "created_at": timestamp,
        "updated_at": timestamp,
        "bindings": {},
        "sources": {},
    }


def _validate_registry(registry: Any) -> dict[str, Any]:
    if not isinstance(registry, dict) or set(registry) != {
        "schema_version",
        "dispatcher_version",
        "created_at",
        "updated_at",
        "bindings",
        "sources",
    }:
        raise TplanError("Codex telemetry dispatcher registry has unsupported fields")
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise TplanError("Codex telemetry dispatcher registry has unsupported schema")
    if registry.get("dispatcher_version") != DISPATCHER_VERSION:
        raise TplanError("Codex telemetry dispatcher registry version does not match")
    for field in ("created_at", "updated_at"):
        value = registry.get(field)
        if not isinstance(value, str) or not value or len(value) > 100:
            raise TplanError(f"Codex telemetry dispatcher registry {field} is invalid")
    bindings = registry.get("bindings")
    if not isinstance(bindings, dict):
        raise TplanError("Codex telemetry dispatcher registry bindings must be an object")
    for session_id, binding in bindings.items():
        _safe_id(session_id, "session_id")
        if not isinstance(binding, dict) or set(binding) != {
            "mission_id",
            "mission_path",
            "binding_generation",
            "registered_at",
        }:
            raise TplanError("Codex telemetry dispatcher binding has unsupported fields")
        mission_path = binding.get("mission_path")
        if (
            not isinstance(mission_path, str)
            or not Path(mission_path).is_absolute()
            or len(mission_path) > 1000
            or "\n" in mission_path
            or "\r" in mission_path
        ):
            raise TplanError("Codex telemetry dispatcher Mission path is invalid")
        mission_id = binding.get("mission_id")
        if not isinstance(mission_id, str) or not mission_id or len(mission_id) > 300:
            raise TplanError("Codex telemetry dispatcher Mission id is invalid")
        generation = binding.get("binding_generation")
        if (
            isinstance(generation, bool)
            or not isinstance(generation, int)
            or generation < 1
        ):
            raise TplanError("Codex telemetry dispatcher binding generation is invalid")
        if (
            not isinstance(binding.get("registered_at"), str)
            or not binding["registered_at"]
            or len(binding["registered_at"]) > 100
        ):
            raise TplanError("Codex telemetry dispatcher registration time is invalid")
    sources = registry.get("sources")
    if not isinstance(sources, dict):
        raise TplanError("Codex telemetry dispatcher sources must be an object")
    for source_path, source in sources.items():
        source_file = Path(source_path)
        if (
            not isinstance(source_path, str)
            or not source_file.is_absolute()
            or source_file.name != "hooks.json"
            or source_file.parent.name != ".codex"
            or len(source_path) > 1000
            or "\n" in source_path
            or "\r" in source_path
        ):
            raise TplanError("Codex telemetry dispatcher source path is invalid")
        if not isinstance(source, dict) or set(source) != {
            "scope",
            "created_by_tplan",
            "registered_at",
        }:
            raise TplanError("Codex telemetry dispatcher source has unsupported fields")
        if source.get("scope") not in {"user", "project"}:
            raise TplanError("Codex telemetry dispatcher source scope is invalid")
        if not isinstance(source.get("created_by_tplan"), bool):
            raise TplanError("Codex telemetry dispatcher source ownership is invalid")
        if (
            not isinstance(source.get("registered_at"), str)
            or not source["registered_at"]
            or len(source["registered_at"]) > 100
        ):
            raise TplanError("Codex telemetry dispatcher source time is invalid")
    return registry


def _read_registry_unlocked(state_dir: Path) -> dict[str, Any]:
    path = registry_path(state_dir)
    if not path.exists():
        return _empty_registry()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TplanError("Codex telemetry dispatcher registry is invalid JSON") from exc
    return _validate_registry(value)


def _write_registry_unlocked(state_dir: Path, registry: dict[str, Any]) -> None:
    registry["updated_at"] = now_iso()
    _validate_registry(registry)
    path = registry_path(state_dir)
    write_json(path, registry, durable=True)
    try:
        path.chmod(0o600)
    except OSError:
        pass


@contextmanager
def registry_lock(state_dir: Path):
    state_dir = _validated_registry_state_dir(state_dir)
    lock_path = state_dir / REGISTRY_LOCK_FILENAME
    with REGISTRY_THREAD_LOCK, lock_path.open("a+b") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif msvcrt is not None:  # pragma: no cover - Windows fallback
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif msvcrt is not None:  # pragma: no cover - Windows fallback
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def _validate_registry_session_owner_unlocked(
    registry: dict[str, Any],
    mission_dir: Path,
    session_id: str,
) -> None:
    existing = registry["bindings"].get(session_id)
    if (
        isinstance(existing, dict)
        and existing.get("mission_path") != str(mission_dir)
    ):
        raise TplanError(
            "Codex telemetry session is already routed to another Mission; "
            "clean the previous Mission before reusing that session"
        )


def _apply_registry_binding_unlocked(
    registry: dict[str, Any],
    mission_dir: Path,
    mission: dict[str, Any],
    *,
    session_id: str,
    generation: int,
) -> None:
    _validate_registry_session_owner_unlocked(registry, mission_dir, session_id)
    for registered_session, registered in list(registry["bindings"].items()):
        if (
            isinstance(registered, dict)
            and registered.get("mission_path") == str(mission_dir)
            and registered_session != session_id
        ):
            registry["bindings"].pop(registered_session)
    registry["bindings"][session_id] = {
        "mission_id": _trace_mission_id(mission),
        "mission_path": str(mission_dir),
        "binding_generation": generation,
        "registered_at": now_iso(),
    }


def _file_bytes_or_none(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def _restore_file_bytes(path: Path, content: bytes | None, *, private: bool = False) -> None:
    if content is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    if private:
        try:
            path.chmod(0o600)
        except OSError:
            pass


def _binding_generation(state: dict[str, Any]) -> int:
    binding = state.get("binding", {})
    generation = binding.get("generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        raise TplanError("Codex telemetry binding generation is invalid")
    return generation


def bind_and_register_session(
    mission_dir: Path,
    state_dir: Path,
    *,
    session_id: str,
    thread_id: str | None = None,
    replace: bool = False,
    activation_required: bool = False,
) -> dict[str, Any]:
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    session_id = _safe_id(session_id, "session_id")
    if thread_id is not None:
        thread_id = _safe_id(thread_id, "thread_id")
    state_path = _state_path(state_dir, mission_dir)
    sidecar_path = coverage_path(mission_dir)
    previous_state: bytes | None = None
    previous_sidecar: bytes | None = None
    previous_registry: dict[str, Any] | None = None
    state_written = False
    registry_written = False
    try:
        with execution_trace_lock(mission_dir):
            previous_state = _file_bytes_or_none(state_path)
            previous_sidecar = _file_bytes_or_none(sidecar_path)
            path, state, mission = _prepare_bind_session_state_unlocked(
                mission_dir,
                state_dir,
                session_id=session_id,
                thread_id=thread_id,
                replace=replace,
                activation_required=activation_required,
            )
            generation = _binding_generation(state)
            with registry_lock(state_dir):
                registry = _read_registry_unlocked(state_dir)
                previous_registry = copy.deepcopy(registry)
                _validate_registry_session_owner_unlocked(
                    registry,
                    mission_dir,
                    session_id,
                )
                _persist_state_and_coverage(path, mission_dir, state)
                state_written = True
                _apply_registry_binding_unlocked(
                    registry,
                    mission_dir,
                    mission,
                    session_id=session_id,
                    generation=generation,
                )
                _write_registry_unlocked(state_dir, registry)
                registry_written = True
                binding_count = len(registry["bindings"])
    except Exception:
        if state_written or registry_written:
            _restore_file_bytes(state_path, previous_state, private=True)
            _restore_file_bytes(sidecar_path, previous_sidecar)
            if previous_registry is not None:
                with registry_lock(state_dir):
                    _write_registry_unlocked(state_dir, previous_registry)
        raise
    return {
        "status": "registered",
        "mission_id": _trace_mission_id(mission),
        "binding_scope": state["binding"]["scope"],
        "binding_generation": generation,
        "state_file": str(state_path),
        "coverage_file": str(sidecar_path),
        "active_binding_count": binding_count,
        "registry_file": str(registry_path(state_dir)),
    }


def register_binding(
    mission_dir: Path,
    state_dir: Path,
    *,
    session_id: str,
    replace: bool = False,
) -> dict[str, Any]:
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    session_id = _safe_id(session_id, "session_id")
    mission = read_mission(mission_dir)
    state = _read_state(_state_path(state_dir, mission_dir))
    _validate_state_target(state, mission_dir, mission)
    binding = state.get("binding", {})
    if binding.get("session_id") != session_id:
        raise TplanError(
            "Codex telemetry dispatcher registration does not match Mission binding"
        )
    generation = _binding_generation(state)
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        _apply_registry_binding_unlocked(
            registry,
            mission_dir,
            mission,
            session_id=session_id,
            generation=generation,
        )
        _write_registry_unlocked(state_dir, registry)
        binding_count = len(registry["bindings"])
    return {
        "status": "registered",
        "mission_id": _trace_mission_id(mission),
        "binding_generation": generation,
        "active_binding_count": binding_count,
        "registry_file": str(registry_path(state_dir)),
    }


def unregister_binding(mission_dir: Path, state_dir: Path) -> dict[str, Any]:
    mission_dir = mission_dir.resolve()
    state_dir = _validated_registry_state_dir(state_dir)
    removed = 0
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        for session_id, binding in list(registry["bindings"].items()):
            if (
                isinstance(binding, dict)
                and binding.get("mission_path") == str(mission_dir)
            ):
                registry["bindings"].pop(session_id)
                removed += 1
        _write_registry_unlocked(state_dir, registry)
        remaining = len(registry["bindings"])
    return {
        "status": "unregistered",
        "removed_binding_count": removed,
        "active_binding_count": remaining,
    }


def register_source_claim(
    state_dir: Path,
    *,
    source_path: Path,
    scope: str,
    created_by_tplan: bool,
) -> dict[str, Any]:
    state_dir = _validated_registry_state_dir(state_dir)
    source_path = source_path.resolve()
    if scope not in {"user", "project"}:
        raise TplanError("Codex telemetry dispatcher source scope is invalid")
    if source_path.name != "hooks.json" or source_path.parent.name != ".codex":
        raise TplanError(
            "Codex telemetry dispatcher source must be a .codex/hooks.json file"
        )
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        existing = registry["sources"].get(str(source_path))
        registry["sources"][str(source_path)] = {
            "scope": scope,
            "created_by_tplan": bool(
                created_by_tplan
                or (
                    isinstance(existing, dict)
                    and existing.get("created_by_tplan") is True
                )
            ),
            "registered_at": (
                existing.get("registered_at")
                if isinstance(existing, dict)
                and isinstance(existing.get("registered_at"), str)
                else now_iso()
            ),
        }
        _write_registry_unlocked(state_dir, registry)
        claim = dict(registry["sources"][str(source_path)])
    return {"path": str(source_path), **claim}


def registry_sources(state_dir: Path) -> list[dict[str, Any]]:
    state_dir = _validated_registry_state_dir(state_dir)
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        return [
            {"path": path, **dict(source)}
            for path, source in sorted(registry["sources"].items())
        ]


def remove_source_claims(state_dir: Path, source_paths: list[Path]) -> None:
    state_dir = _validated_registry_state_dir(state_dir)
    resolved_paths = {str(path.resolve()) for path in source_paths}
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        for source_path in resolved_paths:
            registry["sources"].pop(source_path, None)
        _write_registry_unlocked(state_dir, registry)


def prune_registry_if_empty(state_dir: Path) -> bool:
    state_dir = _validated_registry_state_dir(state_dir)
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        if registry["bindings"] or registry["sources"]:
            return False
        path = registry_path(state_dir)
        path.unlink(missing_ok=True)
        return not path.exists()


def dispatch_hook(
    state_dir: Path,
    event: Any,
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise TplanError("Codex telemetry dispatcher input must be an object")
    session_id = _safe_id(event.get("session_id"), "session_id")
    state_dir = _validated_registry_state_dir(state_dir)
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        binding = registry["bindings"].get(session_id)
        binding = dict(binding) if isinstance(binding, dict) else None
    if binding is None:
        return {
            "status": "not_reported",
            "reason": "dispatcher_session_not_registered",
            "attribution": "none",
        }
    mission_dir = Path(binding["mission_path"])
    state = _read_state(_state_path(state_dir, mission_dir))
    state_binding = state.get("binding", {})
    if (
        state_binding.get("session_id") != session_id
        or state_binding.get("generation") != binding.get("binding_generation")
    ):
        return {
            "status": "not_reported",
            "reason": "dispatcher_binding_generation_mismatch",
            "attribution": "none",
        }
    return handle_hook(
        mission_dir,
        state_dir,
        event,
        observed_at=observed_at,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Route stable Codex hook callbacks to bound TPlan Missions."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    hook = subparsers.add_parser("hook", help="Consume one Codex hook JSON object.")
    hook.add_argument("--state-dir", required=True)
    hook.add_argument("--print-result", action="store_true")
    return parser.parse_args()


def _read_stdin_object() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise TplanError(
            "Codex telemetry dispatcher stdin must contain one JSON object"
        ) from exc
    if not isinstance(value, dict):
        raise TplanError("Codex telemetry dispatcher stdin must contain one JSON object")
    return value


def main() -> int:
    args = parse_args()
    event_name: str | None = None
    try:
        event = _read_stdin_object()
        if isinstance(event.get("hook_event_name"), str):
            event_name = event["hook_event_name"]
        result = dispatch_hook(Path(args.state_dir), event)
        if not args.print_result:
            if event_name == "SubagentStop":
                print("{}")
            return 0
    except Exception:
        if args.print_result:
            print(
                json.dumps(
                    {
                        "status": "not_reported",
                        "reason": "dispatcher_input_or_binding_error",
                        "attribution": "none",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif event_name == "SubagentStop":
            print("{}")
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
