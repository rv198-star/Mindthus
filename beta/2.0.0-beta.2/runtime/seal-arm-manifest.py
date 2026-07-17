#!/usr/bin/env python3
"""Seal and verify reproducible Mindthus Beta.2 evaluation-arm manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any


BETA_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEFINITIONS = BETA_ROOT / "arm-definitions.json"
DEFAULT_SCHEMA = BETA_ROOT / "arm-manifest.schema.json"
SPEC_SCHEMA = "mindthus-beta2-arm-spec-v0.1"
MANIFEST_SCHEMA = "mindthus-beta2-arm-manifest-v0.1"
SHA256_LENGTH = 64

SPEC_FIELDS = {
    "schema_version",
    "arm_id",
    "surface",
    "plugin_root",
    "host_home",
    "execution_root",
    "host_runtime",
    "host_cli",
    "host_config_files",
    "plugin_list_evidence",
    "runtime_diagnostic_evidence",
    "hook_state",
    "model",
    "tools",
    "ambient_context_files",
    "opaque_context",
}


class ManifestError(ValueError):
    """A fail-closed arm identity or evidence error."""


def load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"cannot read {label} at {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON in {label} at {path}: {exc}") from exc


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path, label: str) -> str:
    if not path.is_file() or path.is_symlink():
        raise ManifestError(f"{label} must be a regular non-symlink file: {path}")
    try:
        return sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise ManifestError(f"cannot hash {label} at {path}: {exc}") from exc


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def tree_sha256(root: Path) -> str:
    if not root.is_dir() or root.is_symlink():
        raise ManifestError(f"plugin_root must be a regular directory: {root}")
    digest = hashlib.sha256()
    file_count = 0
    for item in sorted(root.rglob("*"), key=lambda path: path.relative_to(root).as_posix()):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            raise ManifestError(f"plugin tree contains a symlink: {relative}")
        if not item.is_file():
            continue
        try:
            mode = stat.S_IMODE(item.stat().st_mode)
            content = item.read_bytes()
        except OSError as exc:
            raise ManifestError(f"cannot hash plugin tree item {item}: {exc}") from exc
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(f"{mode:04o}".encode("ascii"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
        file_count += 1
    if file_count == 0:
        raise ManifestError(f"plugin_root contains no files: {root}")
    return digest.hexdigest()


def resolve_path(value: Any, base: Path, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-empty path string")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    try:
        return path.resolve()
    except OSError as exc:
        raise ManifestError(f"cannot resolve {label} {value!r}: {exc}") from exc


def file_receipt(path: Path, label: str) -> dict[str, str]:
    return {"path": str(path), "sha256": sha256_file(path, label)}


def is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be an object")
    return value


def require_mapping_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ManifestError(f"{label} must be an array of objects")
    return value


def require_exact_fields(value: dict[str, Any], expected: set[str], label: str) -> None:
    missing = expected - set(value)
    extra = set(value) - expected
    if missing or extra:
        raise ManifestError(
            f"{label} fields mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )


def load_definitions(path: Path) -> tuple[dict[str, Any], str]:
    definitions = require_mapping(load_json(path, "arm definitions"), "arm definitions")
    if definitions.get("schema_version") != "mindthus-beta2-arm-definitions-v0.1":
        raise ManifestError("unsupported arm-definitions schema")
    arms = definitions.get("arms")
    surfaces = definitions.get("surfaces")
    if not isinstance(arms, dict) or set(arms) != {"stable", "direct-only", "thin-kernel"}:
        raise ManifestError("arm definitions must contain exactly stable, direct-only, thin-kernel")
    if not isinstance(surfaces, dict) or set(surfaces) != {"codex-plugin", "claude-plugin"}:
        raise ManifestError("arm definitions must contain exactly Codex and Claude surfaces")
    return definitions, sha256_file(path, "arm definitions")


def load_schema_digest(path: Path) -> str:
    schema = require_mapping(load_json(path, "arm manifest schema"), "arm manifest schema")
    declared = schema.get("properties", {}).get("schema_version", {}).get("const")
    if declared != MANIFEST_SCHEMA:
        raise ManifestError("arm manifest schema does not declare the active manifest version")
    return sha256_file(path, "arm manifest schema")


def plugin_manifest(
    plugin_root: Path,
    surface_definition: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    relative = surface_definition.get("plugin_manifest")
    if not isinstance(relative, str) or not relative:
        raise ManifestError("surface definition has no plugin_manifest")
    path = plugin_root / relative
    payload = require_mapping(load_json(path, "plugin manifest"), "plugin manifest")
    return path, payload


def default_prompt_from_manifest(payload: dict[str, Any]) -> Any:
    interface = payload.get("interface")
    if isinstance(interface, dict) and "defaultPrompt" in interface:
        return interface["defaultPrompt"]
    return payload.get("defaultPrompt")


def normalized_active_mindthus_coordinates(surface: str, payload: Any) -> list[str]:
    if surface == "codex-plugin" and isinstance(payload, dict):
        entries = payload.get("installed")
    elif surface == "claude-plugin" and isinstance(payload, list):
        entries = payload
    else:
        raise ManifestError(f"plugin-list evidence has the wrong {surface} JSON shape")
    if not isinstance(entries, list):
        raise ManifestError("plugin-list evidence entries must be an array")

    active: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        plugin_id = str(entry.get("pluginId") or entry.get("id") or "")
        name = str(entry.get("name") or plugin_id.split("@", 1)[0])
        if name not in {"mindthus", "mindthus-beta"} and not (
            plugin_id.startswith("mindthus@") or plugin_id.startswith("mindthus-beta@")
        ):
            continue
        if entry.get("enabled") is False:
            continue
        if plugin_id.startswith("mindthus-beta@") or name == "mindthus-beta":
            active.append(plugin_id or "mindthus-beta@mindthus-beta")
        else:
            active.append(plugin_id or "mindthus@mindthus")
    return sorted(active)


def native_plugin_observation(surface: str, payload: Any) -> str:
    if surface == "codex-plugin" and isinstance(payload, dict):
        entries = payload.get("installed")
    elif surface == "claude-plugin" and isinstance(payload, list):
        entries = payload
    else:
        raise ManifestError(f"plugin-list evidence has the wrong {surface} JSON shape")
    if not isinstance(entries, list):
        raise ManifestError("plugin-list evidence entries must be an array")
    observed_ids: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        plugin_id = str(entry.get("pluginId") or entry.get("id") or "")
        name = str(entry.get("name") or plugin_id.split("@", 1)[0])
        observed_ids.append(plugin_id or name)
    return f"observed plugins={observed_ids}"


def discover_agents_files(host_home: Path, execution_root: Path) -> list[Path]:
    discovered: set[Path] = set()
    global_agents = host_home / "AGENTS.md"
    if global_agents.is_file():
        discovered.add(global_agents.resolve())

    current = execution_root if execution_root.is_dir() else execution_root.parent
    current = current.resolve()
    while True:
        candidate = current / "AGENTS.md"
        if candidate.is_file():
            discovered.add(candidate.resolve())
        parent = current.parent
        if parent == current:
            break
        current = parent
    return sorted(discovered, key=str)


def context_file_receipts(
    entries: Any,
    base: Path,
    discovered_agents: list[Path],
) -> list[dict[str, str]]:
    if not isinstance(entries, list):
        raise ManifestError("ambient_context_files must be an array")
    receipts: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_paths: set[Path] = set()
    declared_agents: set[Path] = set()
    for index, raw in enumerate(entries):
        entry = require_mapping(raw, f"ambient_context_files[{index}]")
        require_exact_fields(entry, {"kind", "id", "path"}, f"ambient_context_files[{index}]")
        kind = entry.get("kind")
        context_id = entry.get("id")
        if not isinstance(kind, str) or not kind:
            raise ManifestError(f"ambient_context_files[{index}].kind must be non-empty")
        if not isinstance(context_id, str) or not context_id:
            raise ManifestError(f"ambient_context_files[{index}].id must be non-empty")
        if context_id in seen_ids:
            raise ManifestError(f"duplicate ambient context id: {context_id}")
        path = resolve_path(entry.get("path"), base, f"ambient_context_files[{index}].path")
        if path in seen_paths:
            raise ManifestError(f"duplicate ambient context path: {path}")
        receipt = file_receipt(path, f"ambient context {context_id}")
        receipts.append({"kind": kind, "id": context_id, **receipt})
        seen_ids.add(context_id)
        seen_paths.add(path)
        if kind == "agents-file":
            declared_agents.add(path)

    discovered_set = set(discovered_agents)
    if declared_agents != discovered_set:
        undeclared = sorted(str(path) for path in discovered_set - declared_agents)
        stale = sorted(str(path) for path in declared_agents - discovered_set)
        raise ManifestError(
            "AGENTS context ledger mismatch; "
            f"undeclared={undeclared}, declared-but-not-discovered={stale}"
        )
    return sorted(receipts, key=lambda item: (item["kind"], item["id"], item["path"]))


def opaque_context_receipts(entries: Any) -> list[dict[str, str]]:
    if not isinstance(entries, list):
        raise ManifestError("opaque_context must be an array")
    receipts: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(entries):
        entry = require_mapping(raw, f"opaque_context[{index}]")
        require_exact_fields(entry, {"kind", "id", "sha256"}, f"opaque_context[{index}]")
        kind = entry.get("kind")
        context_id = entry.get("id")
        digest = entry.get("sha256")
        if not isinstance(kind, str) or not kind:
            raise ManifestError(f"opaque_context[{index}].kind must be non-empty")
        if not isinstance(context_id, str) or not context_id:
            raise ManifestError(f"opaque_context[{index}].id must be non-empty")
        if not is_sha256(digest):
            raise ManifestError(f"opaque_context[{index}].sha256 must be lowercase SHA-256")
        identity = (kind, context_id)
        if identity in seen:
            raise ManifestError(f"duplicate opaque context identity: {identity}")
        seen.add(identity)
        receipts.append({"kind": kind, "id": context_id, "sha256": digest})
    return sorted(receipts, key=lambda item: (item["kind"], item["id"]))


def host_config_receipts(entries: Any, base: Path, host_home: Path) -> list[dict[str, str]]:
    if not isinstance(entries, list) or not entries:
        raise ManifestError("host_config_files must contain at least one file")
    receipts: list[dict[str, str]] = []
    seen: set[Path] = set()
    for index, value in enumerate(entries):
        path = resolve_path(value, base, f"host_config_files[{index}]")
        try:
            path.relative_to(host_home)
        except ValueError as exc:
            raise ManifestError(f"host config must be inside host_home: {path}") from exc
        if path in seen:
            raise ManifestError(f"duplicate host config path: {path}")
        receipts.append(file_receipt(path, f"host config {index}"))
        seen.add(path)
    return sorted(receipts, key=lambda item: item["path"])


def runtime_diagnostic_receipt(
    value: Any,
    base: Path,
    arm_definition: dict[str, Any],
    surface: str,
    hook_state: str,
    expected_host_observation: str,
) -> dict[str, str] | None:
    required = arm_definition.get("runtime_diagnostic_required") is True
    if not required:
        if value is not None:
            raise ManifestError("stable arm must not attach the Beta runtime diagnostic")
        return None
    path = resolve_path(value, base, "runtime_diagnostic_evidence")
    payload = require_mapping(load_json(path, "runtime diagnostic"), "runtime diagnostic")
    expected = {
        "schema_version": "mindthus-beta-runtime-diagnostic-v0.2",
        "plugin_name": arm_definition.get("plugin_name"),
        "surface": surface,
        "integrity": "ok",
        "carrier_status": "verified",
        "hook_state": hook_state,
        "runtime_isolation_evidence": "observed",
        "runtime_isolation_status": "isolated-observed",
        "passive_kernel_status": arm_definition.get("expected_passive_status"),
        "direct_owner_status": "packaged-verified",
    }
    mismatches = {
        key: {"expected": expected_value, "actual": payload.get(key)}
        for key, expected_value in expected.items()
        if payload.get(key) != expected_value
    }
    if mismatches:
        raise ManifestError(f"runtime diagnostic does not satisfy arm contract: {mismatches}")
    if payload.get("host_plugin_observation") != expected_host_observation:
        raise ManifestError(
            "runtime diagnostic host observation does not match plugin-list evidence; "
            f"expected={expected_host_observation!r}, "
            f"actual={payload.get('host_plugin_observation')!r}"
        )
    return {
        **file_receipt(path, "runtime diagnostic"),
        **{key: str(payload[key]) for key in (
            "schema_version",
            "integrity",
            "carrier_status",
            "hook_state",
            "runtime_isolation_status",
            "passive_kernel_status",
            "direct_owner_status",
        )},
    }


def normalized_model(value: Any) -> dict[str, str]:
    model = require_mapping(value, "model")
    require_exact_fields(model, {"id", "reasoning"}, "model")
    if not all(isinstance(model.get(key), str) and model[key] for key in ("id", "reasoning")):
        raise ManifestError("model.id and model.reasoning must be non-empty strings")
    return {"id": model["id"], "reasoning": model["reasoning"]}


def normalized_host_runtime(value: Any) -> dict[str, str]:
    runtime = require_mapping(value, "host_runtime")
    require_exact_fields(runtime, {"name", "version", "platform"}, "host_runtime")
    if not all(
        isinstance(runtime.get(key), str) and runtime[key]
        for key in ("name", "version", "platform")
    ):
        raise ManifestError(
            "host_runtime.name, host_runtime.version, and host_runtime.platform "
            "must be non-empty strings"
        )
    return {
        "name": runtime["name"],
        "version": runtime["version"],
        "platform": runtime["platform"],
    }


def normalized_tools(value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ManifestError("tools must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise ManifestError("tools must not contain duplicates")
    return sorted(value)


def build_manifest(
    spec: dict[str, Any],
    *,
    spec_base: Path,
    definitions: dict[str, Any],
    definition_sha256: str,
    schema_sha256: str,
) -> dict[str, Any]:
    require_exact_fields(spec, SPEC_FIELDS, "arm spec")
    if spec.get("schema_version") != SPEC_SCHEMA:
        raise ManifestError(f"arm spec schema must be {SPEC_SCHEMA}")
    arm_id = spec.get("arm_id")
    surface = spec.get("surface")
    if arm_id not in definitions["arms"]:
        raise ManifestError(f"unknown arm_id: {arm_id!r}")
    if surface not in definitions["surfaces"]:
        raise ManifestError(f"unknown surface: {surface!r}")
    arm_definition = require_mapping(definitions["arms"][arm_id], f"arm {arm_id}")
    surface_definition = require_mapping(definitions["surfaces"][surface], f"surface {surface}")

    plugin_root = resolve_path(spec.get("plugin_root"), spec_base, "plugin_root")
    host_home = resolve_path(spec.get("host_home"), spec_base, "host_home")
    execution_root = resolve_path(spec.get("execution_root"), spec_base, "execution_root")
    if not host_home.is_dir():
        raise ManifestError(f"host_home is not a directory: {host_home}")
    if not execution_root.exists():
        raise ManifestError(f"execution_root does not exist: {execution_root}")

    manifest_path, plugin_payload = plugin_manifest(plugin_root, surface_definition)
    expected_plugin_name = arm_definition.get("plugin_name")
    if plugin_payload.get("name") != expected_plugin_name:
        raise ManifestError(
            f"plugin manifest name {plugin_payload.get('name')!r} != {expected_plugin_name!r}"
        )
    version = plugin_payload.get("version")
    if not isinstance(version, str) or not version:
        raise ManifestError("plugin manifest version must be a non-empty string")
    default_prompt = default_prompt_from_manifest(plugin_payload)
    default_prompt_sha256 = canonical_sha256(default_prompt)

    hook_state = spec.get("hook_state")
    if hook_state not in arm_definition.get("allowed_hook_states", []):
        raise ManifestError(
            f"hook_state {hook_state!r} is invalid for {arm_id}; "
            f"expected one of {arm_definition.get('allowed_hook_states')}"
        )
    hook_config_path = plugin_root / "hooks" / "hooks.json"
    if arm_id in {"direct-only", "thin-kernel"} and not hook_config_path.is_file():
        raise ManifestError("Beta arms require the locked hook configuration in the package")
    hook_config = file_receipt(hook_config_path, "hook config") if hook_config_path.is_file() else None

    plugin_list_path = resolve_path(
        spec.get("plugin_list_evidence"), spec_base, "plugin_list_evidence"
    )
    plugin_list_payload = load_json(plugin_list_path, "plugin-list evidence")
    active_coordinates = normalized_active_mindthus_coordinates(surface, plugin_list_payload)
    host_observation = native_plugin_observation(surface, plugin_list_payload)
    expected_coordinate = arm_definition.get("plugin_coordinate")
    if active_coordinates != [expected_coordinate]:
        raise ManifestError(
            "host must expose exactly one active Mindthus namespace; "
            f"expected={[expected_coordinate]}, observed={active_coordinates}"
        )

    host_cli = require_mapping(spec.get("host_cli"), "host_cli")
    require_exact_fields(host_cli, {"name", "version"}, "host_cli")
    if host_cli.get("name") != surface_definition.get("host_cli"):
        raise ManifestError(
            f"host_cli.name {host_cli.get('name')!r} does not match surface {surface!r}"
        )
    if not isinstance(host_cli.get("version"), str) or not host_cli["version"]:
        raise ManifestError("host_cli.version must be a non-empty string")

    discovered_agents = discover_agents_files(host_home, execution_root)
    context_files = context_file_receipts(
        spec.get("ambient_context_files"), spec_base, discovered_agents
    )
    opaque_context = opaque_context_receipts(spec.get("opaque_context"))
    configs = host_config_receipts(spec.get("host_config_files"), spec_base, host_home)
    diagnostic = runtime_diagnostic_receipt(
        spec.get("runtime_diagnostic_evidence"),
        spec_base,
        arm_definition,
        surface,
        str(hook_state),
        host_observation,
    )

    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA,
        "arm_id": arm_id,
        "surface": surface,
        "definition_sha256": definition_sha256,
        "schema_sha256": schema_sha256,
        "package": {
            "root": str(plugin_root),
            "coordinate": expected_coordinate,
            "namespace_prefix": arm_definition.get("namespace_prefix"),
            "tree_sha256": tree_sha256(plugin_root),
            "manifest": {
                **file_receipt(manifest_path, "plugin manifest"),
                "name": plugin_payload["name"],
                "version": version,
                "default_prompt_sha256": default_prompt_sha256,
            },
        },
        "carrier": {
            "policy": arm_definition.get("carrier_policy"),
            "hook_state": hook_state,
            "config": hook_config,
        },
        "host": {
            "home": str(host_home),
            "execution_root": str(execution_root),
            "runtime": normalized_host_runtime(spec.get("host_runtime")),
            "cli": {"name": host_cli["name"], "version": host_cli["version"]},
            "config_files": configs,
            "plugin_list": {
                **file_receipt(plugin_list_path, "plugin-list evidence"),
                "source_command": surface_definition.get("plugin_list_command"),
                "active_mindthus_coordinates": active_coordinates,
            },
        },
        "runtime_diagnostic": diagnostic,
        "model": normalized_model(spec.get("model")),
        "tools": normalized_tools(spec.get("tools")),
        "ambient_context": {
            "files": context_files,
            "opaque": opaque_context,
            "discovered_agents_files": [str(path) for path in discovered_agents],
            "default_prompt_sha256": default_prompt_sha256,
        },
    }
    manifest["identity_digest"] = canonical_sha256(manifest)
    return manifest


def spec_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    package = require_mapping(manifest.get("package"), "manifest.package")
    host = require_mapping(manifest.get("host"), "manifest.host")
    carrier = require_mapping(manifest.get("carrier"), "manifest.carrier")
    ambient = require_mapping(manifest.get("ambient_context"), "manifest.ambient_context")
    plugin_list = require_mapping(host.get("plugin_list"), "manifest.host.plugin_list")
    context_files = require_mapping_list(
        ambient.get("files"), "manifest.ambient_context.files"
    )
    config_files = require_mapping_list(host.get("config_files"), "manifest.host.config_files")
    opaque_context = require_mapping_list(
        ambient.get("opaque"), "manifest.ambient_context.opaque"
    )
    return {
        "schema_version": SPEC_SCHEMA,
        "arm_id": manifest.get("arm_id"),
        "surface": manifest.get("surface"),
        "plugin_root": package.get("root"),
        "host_home": host.get("home"),
        "execution_root": host.get("execution_root"),
        "host_runtime": host.get("runtime"),
        "host_cli": host.get("cli"),
        "host_config_files": [item.get("path") for item in config_files],
        "plugin_list_evidence": plugin_list.get("path"),
        "runtime_diagnostic_evidence": (
            manifest["runtime_diagnostic"].get("path")
            if isinstance(manifest.get("runtime_diagnostic"), dict)
            else None
        ),
        "hook_state": carrier.get("hook_state"),
        "model": manifest.get("model"),
        "tools": manifest.get("tools"),
        "ambient_context_files": [
            {"kind": item.get("kind"), "id": item.get("id"), "path": item.get("path")}
            for item in context_files
        ],
        "opaque_context": opaque_context,
    }


def verify_manifest_payload(
    manifest: Any,
    *,
    definitions: dict[str, Any],
    definition_sha256: str,
    schema_sha256: str,
) -> dict[str, Any]:
    payload = require_mapping(manifest, "arm manifest")
    if payload.get("schema_version") != MANIFEST_SCHEMA:
        raise ManifestError(f"arm manifest schema must be {MANIFEST_SCHEMA}")
    identity_digest = payload.get("identity_digest")
    if not is_sha256(identity_digest):
        raise ManifestError("identity_digest must be a lowercase SHA-256")
    unsigned = dict(payload)
    unsigned.pop("identity_digest", None)
    actual_identity = canonical_sha256(unsigned)
    if identity_digest != actual_identity:
        raise ManifestError(
            f"identity digest mismatch: recorded={identity_digest}, actual={actual_identity}"
        )
    if payload.get("definition_sha256") != definition_sha256:
        raise ManifestError("arm definition changed after this manifest was sealed")
    if payload.get("schema_sha256") != schema_sha256:
        raise ManifestError("arm manifest schema changed after this manifest was sealed")

    rebuilt = build_manifest(
        spec_from_manifest(payload),
        spec_base=Path("/"),
        definitions=definitions,
        definition_sha256=definition_sha256,
        schema_sha256=schema_sha256,
    )
    if rebuilt != payload:
        changed = sorted(
            key for key in set(rebuilt) | set(payload) if rebuilt.get(key) != payload.get(key)
        )
        raise ManifestError(f"sealed environment no longer matches manifest fields: {changed}")
    return payload


def verify_manifest_file(
    path: Path,
    *,
    definitions: dict[str, Any],
    definition_sha256: str,
    schema_sha256: str,
) -> dict[str, Any]:
    return verify_manifest_payload(
        load_json(path, "arm manifest"),
        definitions=definitions,
        definition_sha256=definition_sha256,
        schema_sha256=schema_sha256,
    )


def verify_manifest_set(manifests: list[dict[str, Any]]) -> None:
    if not manifests:
        raise ManifestError("verify-set requires at least one manifest")
    identities: set[tuple[str, str]] = set()
    homes: dict[str, tuple[str, str]] = {}
    by_surface: dict[str, dict[str, dict[str, Any]]] = {}
    for manifest in manifests:
        identity = (str(manifest["surface"]), str(manifest["arm_id"]))
        if identity in identities:
            raise ManifestError(f"duplicate surface/arm manifest: {identity}")
        identities.add(identity)
        home = str(manifest["host"]["home"])
        if home in homes:
            raise ManifestError(
                f"host_home is shared by {homes[home]} and {identity}: {home}"
            )
        homes[home] = identity
        by_surface.setdefault(identity[0], {})[identity[1]] = manifest

    expected_arms = {"stable", "direct-only", "thin-kernel"}
    for surface, arms in by_surface.items():
        if set(arms) != expected_arms:
            raise ManifestError(
                f"{surface} manifest set must contain exactly {sorted(expected_arms)}; "
                f"observed={sorted(arms)}"
            )
        direct_tree = arms["direct-only"]["package"]["tree_sha256"]
        kernel_tree = arms["thin-kernel"]["package"]["tree_sha256"]
        if direct_tree != kernel_tree:
            raise ManifestError(
                f"{surface} direct-only and thin-kernel must use the same Beta package tree"
            )


def write_json_atomic(path: Path, payload: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise ManifestError(f"output already exists (use --force to replace): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def render_result(status: str, **fields: Any) -> str:
    return json.dumps({"status": status, **fields}, ensure_ascii=False, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--definitions", type=Path, default=DEFAULT_DEFINITIONS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    subparsers = parser.add_subparsers(dest="command", required=True)

    seal_parser = subparsers.add_parser("seal", help="Seal one arm spec into an immutable manifest.")
    seal_parser.add_argument("--spec", type=Path, required=True)
    seal_parser.add_argument("--out", type=Path, required=True)
    seal_parser.add_argument("--force", action="store_true")

    verify_parser = subparsers.add_parser("verify", help="Verify one sealed arm and live receipts.")
    verify_parser.add_argument("manifest", type=Path)

    set_parser = subparsers.add_parser(
        "verify-set",
        help="Verify complete three-arm sets and cross-arm host/package isolation.",
    )
    set_parser.add_argument("manifests", type=Path, nargs="+")

    args = parser.parse_args()
    try:
        definitions_path = args.definitions.resolve()
        definitions, definition_sha256 = load_definitions(definitions_path)
        schema_sha256 = load_schema_digest(args.schema.resolve())
        if args.command == "seal":
            spec_path = args.spec.resolve()
            spec = require_mapping(load_json(spec_path, "arm spec"), "arm spec")
            manifest = build_manifest(
                spec,
                spec_base=spec_path.parent,
                definitions=definitions,
                definition_sha256=definition_sha256,
                schema_sha256=schema_sha256,
            )
            output = args.out.resolve()
            plugin_root = Path(manifest["package"]["root"])
            try:
                output.relative_to(plugin_root)
            except ValueError:
                pass
            else:
                raise ManifestError("arm manifest output must be outside the measured plugin tree")
            write_json_atomic(output, manifest, args.force)
            print(
                render_result(
                    "sealed",
                    arm_id=manifest["arm_id"],
                    surface=manifest["surface"],
                    identity_digest=manifest["identity_digest"],
                    manifest=str(output),
                )
            )
            return 0

        if args.command == "verify":
            manifest_path = args.manifest.resolve()
            manifest = verify_manifest_file(
                manifest_path,
                definitions=definitions,
                definition_sha256=definition_sha256,
                schema_sha256=schema_sha256,
            )
            print(
                render_result(
                    "verified",
                    arm_id=manifest["arm_id"],
                    surface=manifest["surface"],
                    identity_digest=manifest["identity_digest"],
                    manifest=str(manifest_path),
                )
            )
            return 0

        manifest_paths = [path.resolve() for path in args.manifests]
        manifests = [
            verify_manifest_file(
                path,
                definitions=definitions,
                definition_sha256=definition_sha256,
                schema_sha256=schema_sha256,
            )
            for path in manifest_paths
        ]
        verify_manifest_set(manifests)
        print(
            render_result(
                "verified-set",
                manifests=[
                    {
                        "arm_id": manifest["arm_id"],
                        "surface": manifest["surface"],
                        "identity_digest": manifest["identity_digest"],
                        "manifest": str(path),
                    }
                    for path, manifest in zip(manifest_paths, manifests)
                ],
            )
        )
        return 0
    except ManifestError as exc:
        print(render_result("failed", error=str(exc)), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
