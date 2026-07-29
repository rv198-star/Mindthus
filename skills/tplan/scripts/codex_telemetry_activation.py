#!/usr/bin/env python3
"""Install, preflight, and clean up Codex telemetry hook activation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from codex_telemetry_adapter import (
    CODEX_SURFACES,
    _canonical_mission_dir,
    _read_state,
    _state_path,
    _validate_state_target,
    _validated_state_dir,
    coverage_path,
    hook_command,
    record_activation,
)
from codex_telemetry_dispatcher import (
    _read_registry_unlocked,
    _write_registry_unlocked,
    register_source_claim,
    registry_lock,
    registry_path,
)
from generate_codex_telemetry_hooks import hook_config
from tplan_runtime import (
    TplanError,
    _read_mission_unlocked,
    execution_trace_lock,
    read_mission,
)


HOOK_EVENT_NAMES = {
    "PreToolUse": "preToolUse",
    "PostToolUse": "postToolUse",
    "SubagentStart": "subagentStart",
    "SubagentStop": "subagentStop",
}
SOURCE_SCOPES = {"user", "project"}


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _source_hash(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _atomic_write_bytes(path: Path, value: bytes, *, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            temporary_path.chmod(mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _ensure_source_unchanged(path: Path, baseline: bytes | None) -> None:
    current = path.read_bytes() if path.exists() else None
    if current != baseline:
        raise TplanError(
            "Codex hook source changed during activation; retry instead of overwriting concurrent edits"
        )


def _validate_source_path(path: Path, scope: str) -> Path:
    if scope not in SOURCE_SCOPES:
        raise TplanError("Codex hook source scope must be user or project")
    resolved = path.resolve()
    if resolved.name != "hooks.json" or resolved.parent.name != ".codex":
        raise TplanError("Codex telemetry activation source must be a .codex/hooks.json file")
    return resolved


def _read_hook_source(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TplanError("Codex hook source is invalid JSON") from exc
    if not isinstance(value, dict):
        raise TplanError("Codex hook source must contain one JSON object")
    hooks = value.get("hooks", {})
    if not isinstance(hooks, dict):
        raise TplanError("Codex hook source hooks must be an object")
    for event, groups in hooks.items():
        if not isinstance(event, str) or not isinstance(groups, list):
            raise TplanError("Codex hook source contains an invalid event group")
    return value


def _merge_hook_source(
    source: dict[str, Any],
    mission_dir: Path,
    state_dir: Path,
    *,
    add_description: bool,
) -> tuple[dict[str, Any], int]:
    merged = copy.deepcopy(source)
    generated = hook_config(mission_dir, state_dir)
    if add_description and "description" not in merged:
        merged["description"] = generated["description"]
    hooks = merged.setdefault("hooks", {})
    expected_command = hook_command(mission_dir, state_dir)
    added = 0
    for event, groups in generated["hooks"].items():
        current_groups = hooks.setdefault(event, [])
        already_present = any(
            isinstance(group, dict)
            and isinstance(group.get("hooks"), list)
            and any(
                isinstance(handler, dict)
                and handler.get("type") == "command"
                and handler.get("command") == expected_command
                for handler in group["hooks"]
            )
            for group in current_groups
        )
        if not already_present:
            current_groups.extend(copy.deepcopy(groups))
            added += 1
    return merged, added


def _remove_hook_source(
    source: dict[str, Any], state_dir: Path
) -> tuple[dict[str, Any], int]:
    cleaned = copy.deepcopy(source)
    hooks = cleaned.get("hooks", {})
    expected_command = hook_command(Path("."), state_dir)
    removed = 0
    for event in list(hooks):
        retained_groups = []
        for group in hooks[event]:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                retained_groups.append(group)
                continue
            retained_handlers = []
            for handler in group["hooks"]:
                if (
                    isinstance(handler, dict)
                    and handler.get("type") == "command"
                    and handler.get("command") == expected_command
                ):
                    removed += 1
                else:
                    retained_handlers.append(handler)
            if retained_handlers:
                updated = copy.deepcopy(group)
                updated["hooks"] = retained_handlers
                retained_groups.append(updated)
        if retained_groups:
            hooks[event] = retained_groups
        else:
            hooks.pop(event, None)
    return cleaned, removed


def _source_record(
    *,
    scope: str,
    path: Path,
    sha256: str | None,
    enumerated: bool,
    handler_hashes: dict[str, str],
    trust_statuses: list[str],
    enabled: bool | None,
    created_by_tplan: bool,
) -> dict[str, Any]:
    return {
        "scope": scope,
        "path": str(path),
        "sha256": sha256,
        "enumerated": enumerated,
        "handler_hashes": handler_hashes,
        "trust_statuses": trust_statuses,
        "enabled": enabled,
        "created_by_tplan": created_by_tplan,
    }


def install_source(
    mission_dir: Path,
    state_dir: Path,
    *,
    surface: str,
    source_scope: str,
    source_path: Path,
) -> dict[str, Any]:
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    if surface not in CODEX_SURFACES:
        raise TplanError("Codex telemetry surface must be codex_app or codex_cli")
    source_path = _validate_source_path(source_path, source_scope)
    state = _read_state(_state_path(state_dir, mission_dir))
    _validate_state_target(state, mission_dir, read_mission(mission_dir))
    existed = source_path.exists()
    baseline = source_path.read_bytes() if existed else None
    baseline_mode = source_path.stat().st_mode & 0o777 if existed else None
    source = _read_hook_source(source_path)
    merged, added = _merge_hook_source(
        source,
        mission_dir,
        state_dir,
        add_description=not existed,
    )
    rendered = (json.dumps(merged, ensure_ascii=False, indent=2) + "\n").encode(
        "utf-8"
    )
    _ensure_source_unchanged(source_path, baseline)
    _atomic_write_bytes(source_path, rendered, mode=baseline_mode)
    source = _source_record(
        scope=source_scope,
        path=source_path,
        sha256=_source_hash(source_path),
        enumerated=False,
        handler_hashes={},
        trust_statuses=[],
        enabled=None,
        created_by_tplan=not existed,
    )
    try:
        activation = record_activation(
            mission_dir,
            state_dir,
            surface=surface,
            status="preflight_required",
            reason="hook source was installed or refreshed; host inventory preflight is required",
            host_build=None,
            codex_version=None,
            app_server_user_agent=None,
            platform_family=None,
            platform_os=None,
            source=source,
        )
    except Exception as exc:
        try:
            _ensure_source_unchanged(source_path, rendered)
        except TplanError:
            raise TplanError(
                "activation state write failed after the hook source changed; "
                "manual source reconciliation is required"
            ) from exc
        if baseline is None:
            source_path.unlink(missing_ok=True)
        else:
            _atomic_write_bytes(source_path, baseline, mode=baseline_mode)
        raise
    source_claim = register_source_claim(
        state_dir,
        source_path=source_path,
        scope=source_scope,
        created_by_tplan=not existed,
    )
    return {
        "status": "installed",
        "surface": surface,
        "source_path": str(source_path),
        "source_sha256": source["sha256"],
        "added_handler_groups": added,
        "dispatcher_source_claim": source_claim,
        "activation": activation,
    }


def _wait_for_response(
    messages: queue.Queue[dict[str, Any] | Exception | None],
    request_id: int,
    *,
    deadline: float,
) -> dict[str, Any]:
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TplanError("Codex app-server inventory request timed out")
        try:
            item = messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise TplanError("Codex app-server inventory request timed out") from exc
        if item is None:
            raise TplanError("Codex app-server closed before returning hook inventory")
        if isinstance(item, Exception):
            raise TplanError("Codex app-server returned invalid JSON") from item
        if item.get("id") != request_id:
            continue
        if isinstance(item.get("error"), dict):
            message = item["error"].get("message", "unknown app-server error")
            raise TplanError(f"Codex app-server request failed: {message}")
        result = item.get("result")
        if not isinstance(result, dict):
            raise TplanError("Codex app-server response has no object result")
        return result


def query_hook_inventory(
    codex_bin: str, cwd: Path, *, timeout_seconds: float = 15
) -> dict[str, Any]:
    try:
        process = subprocess.Popen(
            [codex_bin, "app-server"],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
    except OSError as exc:
        raise TplanError(f"could not start Codex app-server: {exc}") from exc
    if process.stdin is None or process.stdout is None:
        process.kill()
        raise TplanError("Codex app-server stdio is unavailable")
    messages: queue.Queue[dict[str, Any] | Exception | None] = queue.Queue()

    def read_messages() -> None:
        try:
            for line in process.stdout:
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    messages.put(exc)
                    return
                if isinstance(value, dict):
                    messages.put(value)
        finally:
            messages.put(None)

    reader = threading.Thread(target=read_messages, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout_seconds
    try:
        initialize = {
            "method": "initialize",
            "id": 0,
            "params": {
                "clientInfo": {
                    "name": "tplan_telemetry_preflight",
                    "title": "TPlan telemetry activation preflight",
                    "version": "0.2.0",
                }
            },
        }
        process.stdin.write(json.dumps(initialize, ensure_ascii=False) + "\n")
        process.stdin.flush()
        initialize_result = _wait_for_response(messages, 0, deadline=deadline)
        for message in (
            {"method": "initialized", "params": {}},
            {
                "method": "hooks/list",
                "id": 1,
                "params": {"cwds": [str(cwd.resolve())]},
            },
        ):
            process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
        process.stdin.flush()
        hooks_result = _wait_for_response(messages, 1, deadline=deadline)
    finally:
        try:
            process.stdin.close()
        except OSError:
            pass
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
        reader.join(timeout=1)
        process.stdout.close()
    try:
        version_result = subprocess.run(
            [codex_bin, "--version"],
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        codex_version = None
    else:
        codex_version = (
            version_result.stdout.strip()
            if version_result.returncode == 0 and version_result.stdout.strip()
            else None
        )
    return {
        "initialize": initialize_result,
        "hooks_list": hooks_result,
        "codex_version": codex_version,
    }


def query_codex_version(codex_bin: str, cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            [codex_bin, "--version"],
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def _load_inventory(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TplanError("Codex hook inventory file is invalid JSON") from exc
    if not isinstance(value, dict):
        raise TplanError("Codex hook inventory file must contain one object")
    if "hooks_list" in value:
        if not isinstance(value["hooks_list"], dict):
            raise TplanError("Codex hook inventory hooks_list must be an object")
        return value
    if "data" in value:
        return {
            "initialize": {},
            "hooks_list": value,
            "codex_version": None,
        }
    raise TplanError("Codex hook inventory file has no hooks_list or data")


def _inventory_rows(inventory: dict[str, Any], cwd: Path) -> list[dict[str, Any]]:
    hooks_list = inventory.get("hooks_list")
    data = hooks_list.get("data") if isinstance(hooks_list, dict) else None
    if not isinstance(data, list):
        raise TplanError("Codex hooks/list response data must be an array")
    resolved_cwd = str(cwd.resolve())
    for entry in data:
        if isinstance(entry, dict) and str(Path(str(entry.get("cwd"))).resolve()) == resolved_cwd:
            hooks = entry.get("hooks")
            if not isinstance(hooks, list):
                raise TplanError("Codex hooks/list entry hooks must be an array")
            return [row for row in hooks if isinstance(row, dict)]
    return []


def _existing_source_ownership(
    mission_dir: Path, state_dir: Path, surface: str, source_path: Path
) -> bool:
    state = _read_state(_state_path(state_dir, mission_dir))
    _validate_state_target(state, mission_dir, read_mission(mission_dir))
    activation = state.get("activation", {})
    surfaces = activation.get("surfaces", {}) if isinstance(activation, dict) else {}
    record = surfaces.get(surface, {}) if isinstance(surfaces, dict) else {}
    source = record.get("source") if isinstance(record, dict) else None
    return bool(
        isinstance(source, dict)
        and source.get("path") == str(source_path)
        and source.get("created_by_tplan")
    )


def evaluate_preflight(
    mission_dir: Path,
    state_dir: Path,
    *,
    surface: str,
    source_scope: str,
    source_path: Path,
    cwd: Path,
    inventory: dict[str, Any] | None,
    host_build: str | None,
    codex_bin: str,
) -> dict[str, Any]:
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    if surface not in CODEX_SURFACES:
        raise TplanError("Codex telemetry surface must be codex_app or codex_cli")
    source_path = _validate_source_path(source_path, source_scope)
    created_by_tplan = _existing_source_ownership(
        mission_dir, state_dir, surface, source_path
    )
    initialize: dict[str, Any] = {}
    codex_version: str | None = None
    app_server_user_agent: str | None = None
    platform_family: str | None = None
    platform_os: str | None = None
    status = "source_absent"
    reason = "the intended Codex hook source does not exist"
    source = _source_record(
        scope=source_scope,
        path=source_path,
        sha256=None,
        enumerated=False,
        handler_hashes={},
        trust_statuses=[],
        enabled=None,
        created_by_tplan=created_by_tplan,
    )
    source_baseline: bytes | None = None
    if surface == "codex_cli":
        codex_version = query_codex_version(codex_bin, cwd)

    if source_path.exists():
        source_baseline = source_path.read_bytes()
        source["sha256"] = _sha256_bytes(source_baseline)
        if inventory is None and surface == "codex_cli":
            try:
                inventory = query_hook_inventory(codex_bin, cwd)
            except TplanError as exc:
                status = "inventory_unavailable"
                reason = str(exc)
        elif inventory is None:
            status = "inventory_unavailable"
            reason = (
                "Codex App preflight requires hooks/list inventory exported by the "
                "App host; CLI app-server inventory is not App evidence"
            )
        if inventory is not None:
            initialize_value = inventory.get("initialize", {})
            initialize = initialize_value if isinstance(initialize_value, dict) else {}
            codex_version_value = inventory.get("codex_version")
            inventory_codex_version = (
                codex_version_value
                if isinstance(codex_version_value, str) and codex_version_value
                else None
            )
            codex_version = inventory_codex_version or codex_version
            app_server_user_agent = (
                initialize.get("userAgent")
                if isinstance(initialize.get("userAgent"), str)
                else None
            )
            platform_family = (
                initialize.get("platformFamily")
                if isinstance(initialize.get("platformFamily"), str)
                else None
            )
            platform_os = (
                initialize.get("platformOs")
                if isinstance(initialize.get("platformOs"), str)
                else None
            )
            rows = _inventory_rows(inventory, cwd)
            source_rows = [
                row
                for row in rows
                if row.get("sourcePath") == str(source_path)
                and row.get("source") == source_scope
            ]
            if not source_rows:
                status = "source_not_enumerated"
                reason = (
                    "the intended hook source exists but is absent from the host hooks/list inventory"
                )
            else:
                expected_command = hook_command(mission_dir, state_dir)
                bound_rows = [
                    row
                    for row in source_rows
                    if row.get("handlerType") == "command"
                    and row.get("command") == expected_command
                ]
                expected_rows: dict[str, dict[str, Any]] = {}
                duplicate_or_extra_bound_row = len(bound_rows) != len(
                    HOOK_EVENT_NAMES
                )
                for public_name, host_name in HOOK_EVENT_NAMES.items():
                    candidates = [
                        row
                        for row in bound_rows
                        if row.get("eventName") == host_name
                    ]
                    if len(candidates) == 1:
                        expected_rows[public_name] = candidates[0]
                    else:
                        duplicate_or_extra_bound_row = True
                if (
                    duplicate_or_extra_bound_row
                    or set(expected_rows) != set(HOOK_EVENT_NAMES)
                ):
                    status = "binding_mismatch"
                    reason = (
                        "the enumerated source does not contain exactly one of every "
                        "Mission/state-bound TPlan handler"
                    )
                elif any(
                    not isinstance(row.get("currentHash"), str)
                    or not row.get("currentHash")
                    or row.get("trustStatus")
                    not in {"managed", "untrusted", "trusted", "modified"}
                    or not isinstance(row.get("enabled"), bool)
                    for row in expected_rows.values()
                ):
                    status = "inventory_unavailable"
                    reason = (
                        "the host inventory omitted required hash, trust, or enabled metadata"
                    )
                else:
                    source["enumerated"] = True
                    source["handler_hashes"] = {
                        event: str(row.get("currentHash"))
                        for event, row in expected_rows.items()
                    }
                    source["trust_statuses"] = sorted(
                        {
                            str(row.get("trustStatus"))
                            for row in expected_rows.values()
                            if row.get("trustStatus")
                            in {"managed", "untrusted", "trusted", "modified"}
                        }
                    )
                    source["enabled"] = all(
                        row.get("enabled") is True for row in expected_rows.values()
                    )
                    if any(
                        row.get("trustStatus") in {"untrusted", "modified"}
                        for row in expected_rows.values()
                    ):
                        status = "needs_trust"
                        reason = (
                            "one or more required handlers are untrusted or their current hash differs from the trusted hash"
                        )
                    elif not source["enabled"]:
                        status = "disabled"
                        reason = "one or more required TPlan hook handlers are disabled"
                    else:
                        status = "ready"
                        reason = (
                            "the exact Mission-bound source is enumerated, trusted, and enabled"
                        )
        _ensure_source_unchanged(source_path, source_baseline)

    inventory_host_build = (
        inventory.get("host_build")
        if isinstance(inventory, dict)
        and isinstance(inventory.get("host_build"), str)
        and inventory.get("host_build")
        else None
    )
    effective_host_build = (
        host_build
        or inventory_host_build
        or (codex_version if surface == "codex_cli" else None)
    )
    if surface == "codex_app" and effective_host_build is None:
        raise TplanError(
            "Codex App preflight requires concrete --host-build or inventory host_build evidence"
        )
    activation = record_activation(
        mission_dir,
        state_dir,
        surface=surface,
        status=status,
        reason=reason,
        host_build=effective_host_build,
        codex_version=codex_version,
        app_server_user_agent=app_server_user_agent,
        platform_family=platform_family,
        platform_os=platform_os,
        source=source,
    )
    return {
        "status": status,
        "ready": status == "ready",
        "surface": surface,
        "reason": reason,
        "source": source,
        "host_build": effective_host_build,
        "codex_version": codex_version,
        "app_server_user_agent": app_server_user_agent,
        "activation": activation,
    }


def cleanup_activation(
    mission_dir: Path,
    state_dir: Path,
    *,
    remove_dispatcher: bool = False,
) -> dict[str, Any]:
    mission_dir = _canonical_mission_dir(mission_dir)
    state_dir = _validated_state_dir(state_dir, mission_dir)
    with execution_trace_lock(mission_dir):
        return _cleanup_activation_locked(
            mission_dir,
            state_dir,
            remove_dispatcher=remove_dispatcher,
        )


def _plan_dispatcher_source_cleanup(
    source_records: dict[str, dict[str, Any]],
    state_dir: Path,
) -> list[dict[str, Any]]:
    source_plans = []
    for source_path_text, source_record in source_records.items():
        source_path = Path(source_path_text)
        if not source_path.exists():
            source_plans.append(
                {
                    "path": source_path_text,
                    "status": "source_absent",
                    "removed_handlers": 0,
                    "action": "none",
                }
            )
            continue
        baseline = source_path.read_bytes()
        mode = source_path.stat().st_mode & 0o777
        source = _read_hook_source(source_path)
        cleaned, removed = _remove_hook_source(source, state_dir)
        hooks = cleaned.get("hooks")
        non_description_keys = set(cleaned) - {"description", "hooks"}
        can_remove_file = (
            source_record.get("created_by_tplan") is True
            and not hooks
            and not non_description_keys
        )
        if can_remove_file:
            source_status = "removed_owned_source"
            action = "remove"
            rendered = None
        elif removed:
            rendered = (
                json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8")
            source_status = "removed_tplan_handlers"
            action = "write"
        else:
            source_status = "no_tplan_handler_present"
            action = "none"
            rendered = None
        source_plans.append(
            {
                "path": source_path_text,
                "status": source_status,
                "removed_handlers": removed,
                "action": action,
                "baseline": baseline,
                "mode": mode,
                "rendered": rendered,
            }
        )
    return source_plans


def _rollback_source_plans(plans: list[dict[str, Any]]) -> bool:
    rollback_failed = False
    for plan in reversed(plans):
        source_path = Path(plan["path"])
        try:
            current = source_path.read_bytes() if source_path.exists() else None
            expected = None if plan["action"] == "remove" else plan["rendered"]
            if current != expected:
                rollback_failed = True
                continue
            _atomic_write_bytes(
                source_path,
                plan["baseline"],
                mode=plan["mode"],
            )
        except OSError:
            rollback_failed = True
    return not rollback_failed


def _apply_source_plans(source_plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    try:
        for plan in source_plans:
            if plan["action"] == "none":
                continue
            source_path = Path(plan["path"])
            _ensure_source_unchanged(source_path, plan["baseline"])
            if plan["action"] == "remove":
                source_path.unlink()
            else:
                _atomic_write_bytes(
                    source_path,
                    plan["rendered"],
                    mode=plan["mode"],
                )
            applied.append(plan)
    except Exception as exc:
        if not _rollback_source_plans(applied):
            raise TplanError(
                "Codex hook cleanup encountered concurrent edits; manual source "
                "reconciliation is required and the registry claim was retained"
            ) from exc
        raise
    return applied


def _source_results(source_plans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "path": plan["path"],
            "status": plan["status"],
            "removed_handlers": plan["removed_handlers"],
        }
        for plan in source_plans
    ]


def _cleanup_activation_locked(
    mission_dir: Path,
    state_dir: Path,
    *,
    remove_dispatcher: bool,
) -> dict[str, Any]:
    state_path = _state_path(state_dir, mission_dir)
    state = _read_state(state_path)
    _validate_state_target(state, mission_dir, _read_mission_unlocked(mission_dir))
    mission_path = str(mission_dir)
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        removed_binding_count = 0
        for session_id, binding in list(registry["bindings"].items()):
            if (
                isinstance(binding, dict)
                and binding.get("mission_path") == mission_path
            ):
                registry["bindings"].pop(session_id)
                removed_binding_count += 1
        active_binding_count = len(registry["bindings"])
        source_records = {
            path: {"path": path, **dict(source)}
            for path, source in registry["sources"].items()
        }
        should_remove_dispatcher = (
            remove_dispatcher and active_binding_count == 0
        )
        if should_remove_dispatcher:
            source_plans = _plan_dispatcher_source_cleanup(
                source_records,
                state_dir,
            )
            applied = _apply_source_plans(source_plans)
            registry["sources"] = {}
        else:
            applied = []
            source_plans = [
                {
                    "path": path,
                    "status": (
                        "retained_active_bindings"
                        if remove_dispatcher
                        else "retained_stable_dispatcher"
                    ),
                    "removed_handlers": 0,
                    "action": "none",
                }
                for path in sorted(source_records)
            ]
        try:
            if registry["bindings"] or registry["sources"]:
                _write_registry_unlocked(state_dir, registry)
                registry_removed = False
            else:
                path = registry_path(state_dir)
                path.unlink(missing_ok=True)
                registry_removed = not path.exists()
        except Exception as exc:
            if applied and not _rollback_source_plans(applied):
                raise TplanError(
                    "Codex dispatcher registry commit failed after source cleanup; "
                    "manual source reconciliation is required"
                ) from exc
            raise
    sidecar = coverage_path(mission_dir)
    sidecar.unlink(missing_ok=True)
    state_path.unlink(missing_ok=True)
    return {
        "status": "cleaned",
        "sources": _source_results(source_plans),
        "removed_binding_count": removed_binding_count,
        "active_binding_count": active_binding_count,
        "dispatcher_removed": bool(
            should_remove_dispatcher
            and all(plan["action"] in {"remove", "write", "none"} for plan in source_plans)
        ),
        "registry_removed": registry_removed,
        "binding_state_removed": not state_path.exists(),
        "coverage_claim_removed": not sidecar.exists(),
        "note": (
            "Mission routing and stale coverage were removed. The stable dispatcher "
            "remains trusted for reuse unless explicit removal was requested with no "
            "other active bindings."
        ),
    }


def uninstall_dispatcher(state_dir: Path) -> dict[str, Any]:
    state_dir = state_dir.resolve()
    with registry_lock(state_dir):
        registry = _read_registry_unlocked(state_dir)
        if registry["bindings"]:
            raise TplanError(
                "Codex telemetry dispatcher still has active Mission bindings; "
                "clean those Missions before uninstall"
            )
        source_records = {
            path: {"path": path, **dict(source)}
            for path, source in registry["sources"].items()
        }
        source_plans = _plan_dispatcher_source_cleanup(
            source_records,
            state_dir,
        )
        applied = _apply_source_plans(source_plans)
        try:
            path = registry_path(state_dir)
            path.unlink(missing_ok=True)
            registry_removed = not path.exists()
        except Exception as exc:
            if applied and not _rollback_source_plans(applied):
                raise TplanError(
                    "Codex dispatcher uninstall could not restore hook sources after "
                    "registry cleanup failed"
                ) from exc
            raise
    return {
        "status": "dispatcher_uninstalled",
        "sources": _source_results(source_plans),
        "dispatcher_removed": True,
        "registry_removed": registry_removed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage fail-closed Codex App/CLI telemetry hook activation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser(
        "install", help="Merge stable dispatcher handlers into one hooks.json source."
    )
    install.add_argument("mission_dir")
    install.add_argument("--state-dir", required=True)
    install.add_argument("--surface", required=True, choices=sorted(CODEX_SURFACES))
    install.add_argument("--source-scope", required=True, choices=sorted(SOURCE_SCOPES))
    install.add_argument("--source-path", required=True)

    preflight = subparsers.add_parser(
        "preflight", help="Fail closed unless hooks/list proves the source trusted and enabled."
    )
    preflight.add_argument("mission_dir")
    preflight.add_argument("--state-dir", required=True)
    preflight.add_argument("--surface", required=True, choices=sorted(CODEX_SURFACES))
    preflight.add_argument(
        "--source-scope", required=True, choices=sorted(SOURCE_SCOPES)
    )
    preflight.add_argument("--source-path", required=True)
    preflight.add_argument("--cwd")
    preflight.add_argument("--codex-bin", default="codex")
    preflight.add_argument("--inventory-json")
    preflight.add_argument("--host-build")

    cleanup = subparsers.add_parser(
        "cleanup",
        help=(
            "Unroute one Mission and remove stale coverage while retaining the "
            "stable dispatcher by default."
        ),
    )
    cleanup.add_argument("mission_dir")
    cleanup.add_argument("--state-dir", required=True)
    cleanup.add_argument(
        "--remove-dispatcher",
        action="store_true",
        help="Also remove dispatcher handlers when no other Mission bindings remain.",
    )
    uninstall = subparsers.add_parser(
        "uninstall",
        help="Remove the stable dispatcher after every Mission binding is cleaned.",
    )
    uninstall.add_argument("--state-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "install":
            result = install_source(
                Path(args.mission_dir),
                Path(args.state_dir),
                surface=args.surface,
                source_scope=args.source_scope,
                source_path=Path(args.source_path),
            )
        elif args.command == "preflight":
            inventory = (
                _load_inventory(Path(args.inventory_json))
                if args.inventory_json
                else None
            )
            result = evaluate_preflight(
                Path(args.mission_dir),
                Path(args.state_dir),
                surface=args.surface,
                source_scope=args.source_scope,
                source_path=Path(args.source_path),
                cwd=Path(args.cwd).resolve()
                if args.cwd
                else Path(args.mission_dir).resolve(),
                inventory=inventory,
                host_build=args.host_build,
                codex_bin=args.codex_bin,
            )
        elif args.command == "cleanup":
            result = cleanup_activation(
                Path(args.mission_dir),
                Path(args.state_dir),
                remove_dispatcher=args.remove_dispatcher,
            )
        else:
            result = uninstall_dispatcher(Path(args.state_dir))
    except (OSError, ValueError, TplanError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.command == "preflight" and not result["ready"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
