#!/usr/bin/env python3
"""Check Mindthus 2.0 Beta package, carrier, and reported host isolation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


EXCLUDED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".tplan",
    ".tvg",
    "artifacts",
    "logs",
    "test",
    "tests",
}
EXCLUDED_SUFFIXES = {
    ".gif",
    ".jpeg",
    ".jpg",
    ".log",
    ".mov",
    ".mp4",
    ".png",
    ".pyc",
    ".pyo",
    ".tmp",
    ".webp",
}
EXCLUDED_NAME_SUBSTRINGS = ("ab_run", "pilot")
HOOK_STATES = ("unknown", "trusted", "fired", "untrusted", "disabled", "failed")
STABLE_RUNTIME_STATES = ("unknown", "not-installed", "disabled", "enabled")
ISOLATED_STABLE_STATES = {"not-installed", "disabled"}


def safe_path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a non-empty string")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path escapes plugin root: {value}")
    resolved = (root / relative).resolve()
    resolved.relative_to(root)
    return resolved


def tree_digest(
    source: Path,
    *,
    jsonl_allowlist: set[Path] | None = None,
    text_normalizations: dict[str, str] | None = None,
) -> str:
    jsonl_allowlist = jsonl_allowlist or set()
    text_normalizations = text_normalizations or {}
    digest = hashlib.sha256()
    for item in sorted(source.rglob("*")):
        if not item.is_file():
            continue
        relative = item.relative_to(source)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        lowered = relative.as_posix().lower()
        if any(token in lowered for token in EXCLUDED_NAME_SUBSTRINGS):
            continue
        if item.suffix in EXCLUDED_SUFFIXES:
            continue
        if item.suffix == ".jsonl" and relative not in jsonl_allowlist:
            continue
        content = item.read_bytes()
        if text_normalizations and item.suffix == ".md":
            text = content.decode("utf-8")
            for old, new in text_normalizations.items():
                text = text.replace(old, new)
            content = text.encode("utf-8")
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def add_check(checks: list[dict], check_id: str, ok: bool, detail: str) -> None:
    checks.append({"id": check_id, "status": "ok" if ok else "failed", "detail": detail})


def check_ok(checks: list[dict], check_id: str) -> bool:
    return any(check["id"] == check_id and check["status"] == "ok" for check in checks)


def expected_hook_config(surface: str) -> dict | None:
    root_variable = {
        "codex-plugin": "PLUGIN_ROOT",
        "claude-plugin": "CLAUDE_PLUGIN_ROOT",
    }.get(surface)
    if root_variable is None:
        return None
    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f'"${{{root_variable}}}/hooks/session-start"',
                            "async": False,
                        }
                    ],
                }
            ]
        }
    }


def detect_manifest(root: Path) -> tuple[str, Path | None, dict | None]:
    candidates = (
        ("codex-plugin", root / ".codex-plugin" / "plugin.json"),
        ("claude-plugin", root / ".claude-plugin" / "plugin.json"),
    )
    present = [(surface, path) for surface, path in candidates if path.is_file()]
    if len(present) != 1:
        return "unknown", None, None
    surface, path = present[0]
    try:
        return surface, path, json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return surface, path, None


def parse_host_plugins(surface: str, payload: object) -> tuple[str, bool, str]:
    if surface == "codex-plugin" and isinstance(payload, dict):
        entries = payload.get("installed", [])
    elif surface == "claude-plugin" and isinstance(payload, list):
        entries = payload
    else:
        raise ValueError(f"unexpected {surface} plugin-list payload")
    if not isinstance(entries, list):
        raise ValueError("plugin-list entries must be an array")

    stable_installed = False
    stable_enabled = False
    beta_enabled = False
    observed_ids: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        plugin_id = str(entry.get("pluginId") or entry.get("id") or "")
        name = str(entry.get("name") or plugin_id.split("@", 1)[0])
        enabled = entry.get("enabled") is not False
        observed_ids.append(plugin_id or name)
        if name == "mindthus" or plugin_id.startswith("mindthus@"):
            stable_installed = True
            stable_enabled = stable_enabled or enabled
        if name == "mindthus-beta" or plugin_id.startswith("mindthus-beta@"):
            beta_enabled = beta_enabled or enabled

    stable_state = (
        "enabled"
        if stable_enabled
        else "disabled"
        if stable_installed
        else "not-installed"
    )
    return stable_state, beta_enabled, f"observed plugins={observed_ids}"


def inspect_host_plugins(surface: str) -> tuple[str, bool, str]:
    command = {
        "codex-plugin": ["codex", "plugin", "list", "--json"],
        "claude-plugin": ["claude", "plugin", "list", "--json"],
    }.get(surface)
    if command is None:
        raise ValueError(f"cannot inspect an unknown plugin surface: {surface}")
    result = subprocess.run(command, text=True, capture_output=True, timeout=10)
    if result.returncode != 0:
        raise ValueError(
            f"host plugin inspection failed with {result.returncode}: {result.stderr.strip()}"
        )
    return parse_host_plugins(surface, json.loads(result.stdout))


def verify_manifest(
    checks: list[dict],
    surface: str,
    manifest: dict | None,
    profile: dict,
) -> None:
    identity = profile.get("plugin_identity", {})
    ok = (
        isinstance(manifest, dict)
        and manifest.get("name") == identity.get("name")
        and manifest.get("version") == profile.get("version")
    )
    if ok and surface == "codex-plugin":
        prompts = manifest.get("interface", {}).get("defaultPrompt", [])
        starter = prompts[0] if isinstance(prompts, list) and prompts else ""
        ok = (
            manifest.get("skills") == "./skills/"
            and "mindthus-beta:using-mindthus" in starter
            and "mindthus:using-mindthus" not in starter
        )
    add_check(
        checks,
        "plugin-manifest",
        ok,
        f"surface={surface}, expected name={identity.get('name')!r}, version={profile.get('version')!r}",
    )


def verify_generated_artifacts(
    root: Path,
    checks: list[dict],
    profile: dict,
    surface: str,
) -> bool:
    generated = profile.get("generated_artifact_sha256", {}).get(surface)
    if not isinstance(generated, dict) or not generated:
        add_check(checks, "generated-runtime-lock", False, f"missing lock for {surface}")
        return False
    all_ok = True
    for value, expected in generated.items():
        try:
            path = safe_path(root, value)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            ok = actual == expected
            detail = f"{value}: {actual}"
        except (ValueError, OSError) as exc:
            ok = False
            detail = f"{value!r}: {exc}"
        add_check(checks, f"generated-artifact:{value}", ok, detail)
        all_ok = all_ok and ok
    return all_ok


def verify_hook_carrier(
    root: Path,
    checks: list[dict],
    profile: dict,
    surface: str,
    generated_ok: bool,
) -> bool:
    hooks_path = root / "hooks" / "hooks.json"
    expected_config = expected_hook_config(surface)
    try:
        actual_config = json.loads(hooks_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        actual_config = None
    config_ok = expected_config is not None and actual_config == expected_config
    add_check(checks, "hook-config", config_ok, f"exact {surface} SessionStart contract")

    script = root / "hooks" / "session-start"
    executable_ok = script.is_file() and os.access(script, os.X_OK)
    add_check(checks, "hook-executable", executable_ok, "hooks/session-start is executable")

    if not (generated_ok and config_ok and executable_ok):
        add_check(
            checks,
            "hook-execution",
            False,
            "not executed because the locked carrier or its configuration failed verification",
        )
        return False

    root_variable = "PLUGIN_ROOT" if surface == "codex-plugin" else "CLAUDE_PLUGIN_ROOT"
    env = os.environ.copy()
    env.pop("PLUGIN_ROOT", None)
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    env[root_variable] = str(root)
    try:
        result = subprocess.run(
            [str(script)],
            text=True,
            capture_output=True,
            env=env,
            timeout=5,
        )
        payload = json.loads(result.stdout)
        kernel = (root / str(profile.get("passive_kernel"))).read_text(encoding="utf-8")
        expected_context = (
            f"<MINDTHUS_PASSIVE_KERNEL>\n{kernel.rstrip()}\n</MINDTHUS_PASSIVE_KERNEL>"
        )
        hook_output = payload.get("hookSpecificOutput", {})
        execution_ok = (
            result.returncode == 0
            and hook_output.get("hookEventName") == "SessionStart"
            and hook_output.get("additionalContext") == expected_context
        )
        detail = "locked hook emitted the exact packaged Passive Kernel"
        if not execution_ok:
            detail = f"returncode={result.returncode}; stderr={result.stderr.strip()!r}"
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError) as exc:
        execution_ok = False
        detail = str(exc)
    add_check(checks, "hook-execution", execution_ok, detail)
    return execution_ok


def failed_profile_result(
    hook_state: str,
    stable_state: str,
    checks: list[dict],
    isolation_evidence: str,
) -> dict:
    return {
        "schema_version": "mindthus-beta-runtime-diagnostic-v0.2",
        "integrity": "failed",
        "carrier_status": "failed",
        "hook_state": hook_state,
        "stable_runtime_state": stable_state,
        "runtime_isolation_evidence": isolation_evidence,
        "runtime_isolation_status": "unverified",
        "passive_kernel_status": "degraded",
        "direct_owner_status": "failed",
        "claim_ceiling": "package integrity is unknown",
        "checks": checks,
        "actions": ["rebuild or reinstall mindthus-beta from a verified Beta.1 artifact"],
    }


def diagnose(
    plugin_root: Path,
    hook_state: str,
    stable_state: str,
    *,
    isolation_evidence: str = "reported",
    beta_enabled: bool | None = None,
    host_observation: str | None = None,
) -> dict:
    root = plugin_root.resolve()
    checks: list[dict] = []
    actions: list[str] = []
    profile_path = root / "beta" / "release-profile.json"

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        add_check(checks, "release-profile", False, str(exc))
        return failed_profile_result(hook_state, stable_state, checks, isolation_evidence)

    add_check(
        checks,
        "profile-schema",
        profile.get("schema_version") == "mindthus-release-profile-v0.2"
        and profile.get("path_base") == "plugin-root",
        "profile schema and plugin-root path base",
    )
    add_check(
        checks,
        "beta1-phase-boundary",
        profile.get("release_preparation") == "not-started"
        and profile.get("behavioral_evaluation") == "deferred-to-beta.2",
        "Beta.1 is a functional prototype; release work and behavior evaluation are deferred",
    )
    identity = profile.get("plugin_identity", {})
    add_check(
        checks,
        "plugin-identity",
        identity.get("name") == "mindthus-beta"
        and identity.get("marketplace_name") == "mindthus-beta"
        and identity.get("coinstallable_with_stable") is True
        and identity.get("coenabled_with_stable") is False,
        "Beta is separately installable but must not be co-enabled with Stable",
    )
    adapter = profile.get("namespace_adapter", {})
    add_check(
        checks,
        "namespace-adapter-contract",
        adapter.get("mode") == "package-time-coordinate-only"
        and adapter.get("source_prefix") == "mindthus:"
        and adapter.get("runtime_prefix") == "mindthus-beta:",
        "Stable source coordinates normalize to the isolated Beta namespace",
    )

    surface, manifest_path, manifest = detect_manifest(root)
    verify_manifest(checks, surface, manifest, profile)

    active_paths = list(profile.get("active_runtime_paths", []))
    active_paths.extend(profile.get("active_runtime_paths_by_surface", {}).get(surface, []))
    for value in active_paths:
        try:
            path = safe_path(root, value)
            ok = path.exists()
            detail = value
        except (ValueError, OSError) as exc:
            ok = False
            detail = f"{value!r}: {exc}"
        add_check(checks, f"active:{value}", ok, detail)

    for value in profile.get("forbidden_active_paths", []):
        try:
            path = safe_path(root, value)
            ok = not path.exists()
            detail = value
        except (ValueError, OSError) as exc:
            ok = False
            detail = f"{value!r}: {exc}"
        add_check(checks, f"inactive:{value}", ok, detail)

    for value in profile.get("reference_only_paths", []):
        try:
            path = safe_path(root, value)
            ok = path.exists()
            detail = value
        except (ValueError, OSError) as exc:
            ok = False
            detail = f"{value!r}: {exc}"
        add_check(checks, f"reference:{value}", ok, detail)

    for value, expected in profile.get("artifact_sha256", {}).items():
        try:
            path = safe_path(root, value)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            ok = actual == expected
            detail = f"{value}: {actual}"
        except (ValueError, OSError) as exc:
            ok = False
            detail = f"{value!r}: {exc}"
        add_check(checks, f"artifact:{value}", ok, detail)

    generated_ok = verify_generated_artifacts(root, checks, profile, surface)

    try:
        lock_path = safe_path(root, profile.get("reference_lock"))
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        add_check(
            checks,
            "reference-lock-schema",
            lock.get("schema_version") == "mindthus-reference-lock-v0.1"
            and lock.get("stable_baseline") == profile.get("stable_baseline")
            and lock.get("baseline_commit") == profile.get("baseline_commit")
            and lock.get("source_path_base") == "repository-root"
            and lock.get("package_path_base") == "plugin-root",
            "reference lock schema, baseline commit, and path bases",
        )
        normalizations = {
            str(adapter.get("runtime_prefix")): str(adapter.get("source_prefix"))
        }
        for record in lock.get("trees", []):
            surface_paths = record.get("package_paths_by_surface")
            package_value = (
                surface_paths.get(surface)
                if isinstance(surface_paths, dict)
                else record.get("package_path")
            )
            package_path = safe_path(root, package_value)
            allowlist = {Path(value) for value in record.get("jsonl_allowlist", [])}
            normalize = (
                normalizations
                if str(record.get("id", "")).startswith("owner-")
                and record.get("id") != "owner-shared-runtime"
                else None
            )
            actual = tree_digest(
                package_path,
                jsonl_allowlist=allowlist,
                text_normalizations=normalize,
            )
            add_check(
                checks,
                f"locked-tree:{record.get('id')}",
                package_path.is_dir() and actual == record.get("sha256"),
                f"{package_value}: {actual}",
            )
        for record in lock.get("files", []):
            package_path = safe_path(root, record.get("package_path"))
            actual = hashlib.sha256(package_path.read_bytes()).hexdigest()
            add_check(
                checks,
                f"locked-file:{record.get('id')}",
                package_path.is_file() and actual == record.get("sha256"),
                f"{record.get('package_path')}: {actual}",
            )
    except (OSError, ValueError, json.JSONDecodeError, AttributeError) as exc:
        add_check(checks, "reference-lock", False, str(exc))

    owner_names = profile.get("owner_skills", [])
    owner_files_ok = all((root / "skills" / name / "SKILL.md").is_file() for name in owner_names)
    stable_prefix = str(adapter.get("source_prefix", "mindthus:"))
    stable_coordinate_hits: list[str] = []
    for name in (*owner_names, "using-mindthus"):
        skill_root = root / "skills" / name
        if not skill_root.is_dir():
            continue
        for path in sorted(skill_root.rglob("*.md")):
            if stable_prefix in path.read_text(encoding="utf-8"):
                stable_coordinate_hits.append(path.relative_to(root).as_posix())
    namespace_ok = not stable_coordinate_hits
    add_check(
        checks,
        "active-namespace-isolation",
        namespace_ok,
        "no Stable mindthus: coordinates in active Beta skills"
        if namespace_ok
        else f"Stable coordinates remain in {stable_coordinate_hits}",
    )

    carrier_ok = verify_hook_carrier(root, checks, profile, surface, generated_ok)
    owner_lock_ids = {f"locked-tree:owner-{name}" for name in owner_names}
    owner_lock_ids.add("locked-tree:owner-shared-runtime")
    owners_packaged = (
        owner_files_ok
        and namespace_ok
        and check_ok(checks, "plugin-manifest")
        and all(check_ok(checks, check_id) for check_id in owner_lock_ids)
    )
    add_check(
        checks,
        "direct-owner-package",
        owners_packaged,
        f"packaged Beta owners={owner_names}; host selection remains a model behavior claim",
    )

    integrity = "ok" if all(check["status"] == "ok" for check in checks) else "failed"
    if isolation_evidence == "observed" and beta_enabled is not True:
        isolation_status = "beta-inactive"
    elif stable_state in ISOLATED_STABLE_STATES:
        isolation_status = (
            "isolated-observed" if isolation_evidence == "observed" else "isolated-reported"
        )
    elif stable_state == "enabled":
        isolation_status = "conflict"
    else:
        isolation_status = "unverified"

    if hook_state == "fired" and integrity == "ok" and carrier_ok:
        passive_status = "reported-fired-carrier-verified"
    elif hook_state == "trusted" and integrity == "ok" and carrier_ok:
        passive_status = "carrier-verified-not-observed"
    else:
        passive_status = "degraded"

    if isolation_status == "conflict":
        claim_ceiling = "Stable and Beta are co-enabled; Beta behavior and cost are not isolated"
        actions.append("disable Stable mindthus before using or evaluating mindthus-beta")
    elif isolation_status == "beta-inactive":
        claim_ceiling = "mindthus-beta is not enabled in the inspected host environment"
        actions.append("enable mindthus-beta in the isolated host environment")
    elif isolation_status == "unverified":
        claim_ceiling = "package carrier may be verified, but Stable/Beta runtime isolation is unverified"
        actions.append("report --stable-state disabled or not-installed only after verifying the host")
    elif passive_status == "reported-fired-carrier-verified":
        claim_ceiling = (
            "the locked carrier output is verified and host firing was reported; "
            "owner choice and semantic behavior remain unproven until Beta.2"
        )
    else:
        claim_ceiling = "isolated direct-owner package only; passive host injection is not observed"

    if surface == "codex-plugin" and hook_state != "fired":
        actions.append("run /hooks, review and trust the mindthus-beta SessionStart hook, then start a session")
    if hook_state == "trusted":
        actions.append("observe a fresh SessionStart before reporting --hook-state fired")
    if hook_state in {"untrusted", "disabled", "failed"}:
        actions.append("repair or enable the SessionStart hook; otherwise keep the degraded claim ceiling")
    if integrity != "ok":
        actions.append("rebuild or reinstall mindthus-beta from a verified Beta.1 artifact")

    return {
        "schema_version": "mindthus-beta-runtime-diagnostic-v0.2",
        "release_line": profile.get("release_line"),
        "version": profile.get("version"),
        "plugin_name": identity.get("name"),
        "surface": surface,
        "integrity": integrity,
        "carrier_status": "verified" if carrier_ok else "failed",
        "hook_state": hook_state,
        "stable_runtime_state": stable_state,
        "runtime_isolation_evidence": isolation_evidence,
        "host_plugin_observation": host_observation,
        "runtime_isolation_status": isolation_status,
        "passive_kernel_status": passive_status,
        "direct_owner_status": "packaged-verified" if owners_packaged else "failed",
        "claim_ceiling": claim_ceiling,
        "checks": checks,
        "actions": actions,
    }


def render_text(result: dict) -> str:
    lines = [
        (
            f"Mindthus Beta runtime: integrity={result['integrity']} "
            f"carrier={result['carrier_status']} passive={result['passive_kernel_status']} "
            f"isolation={result['runtime_isolation_status']}"
        ),
        f"Claim ceiling: {result['claim_ceiling']}",
    ]
    for check in result["checks"]:
        if check["status"] != "ok":
            lines.append(f"FAIL {check['id']}: {check['detail']}")
    lines.extend(f"ACTION: {action}" for action in result["actions"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Installed mindthus-beta plugin root (defaults from this script)",
    )
    parser.add_argument("--hook-state", choices=HOOK_STATES, default="unknown")
    parser.add_argument(
        "--stable-state",
        choices=STABLE_RUNTIME_STATES,
        default="unknown",
        help="Observed Stable plugin state; this diagnostic does not inspect host plugin state",
    )
    host_group = parser.add_mutually_exclusive_group()
    host_group.add_argument(
        "--inspect-host",
        action="store_true",
        help="Read the current Codex or Claude plugin list and verify Beta/Stable isolation",
    )
    host_group.add_argument(
        "--host-plugins-json",
        type=Path,
        help="Parse saved output from `codex plugin list --json` or `claude plugin list --json`",
    )
    parser.add_argument(
        "--require-passive",
        action="store_true",
        help="Return non-zero unless the locked carrier is verified and host firing is reported",
    )
    parser.add_argument(
        "--require-isolated",
        action="store_true",
        help="Return non-zero unless Stable is reported disabled or not installed in this host environment",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    if (args.inspect_host or args.host_plugins_json) and args.stable_state != "unknown":
        parser.error("--stable-state cannot be combined with host plugin inspection")

    stable_state = args.stable_state
    isolation_evidence = "reported"
    beta_enabled: bool | None = None
    host_observation: str | None = None
    if args.inspect_host or args.host_plugins_json:
        surface, _, _ = detect_manifest(args.plugin_root.resolve())
        try:
            if args.host_plugins_json:
                payload = json.loads(args.host_plugins_json.read_text(encoding="utf-8"))
                stable_state, beta_enabled, host_observation = parse_host_plugins(surface, payload)
            else:
                stable_state, beta_enabled, host_observation = inspect_host_plugins(surface)
            isolation_evidence = "observed"
        except (OSError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            stable_state = "unknown"
            isolation_evidence = "inspection-failed"
            host_observation = str(exc)

    result = diagnose(
        args.plugin_root,
        args.hook_state,
        stable_state,
        isolation_evidence=isolation_evidence,
        beta_enabled=beta_enabled,
        host_observation=host_observation,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))

    if result["integrity"] != "ok":
        return 1
    if result["runtime_isolation_status"] in {"conflict", "beta-inactive"}:
        return 3
    if args.require_passive and result["passive_kernel_status"] != "reported-fired-carrier-verified":
        return 2
    if args.require_isolated and result["runtime_isolation_status"] not in {
        "isolated-observed",
        "isolated-reported",
    }:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
