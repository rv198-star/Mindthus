#!/usr/bin/env python3
"""Verify the static Codex-native thin-router package and isolation claim ceiling."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


OWNER_NAMES = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")
STABLE_STATES = ("unknown", "disabled", "not-installed", "enabled")
EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".tplan", ".tvg", "artifacts", "logs", "test", "tests"}
EXCLUDED_SUFFIXES = {".gif", ".jpeg", ".jpg", ".log", ".mov", ".mp4", ".png", ".pyc", ".pyo", ".tmp", ".webp"}
EXCLUDED_NAME_SUBSTRINGS = ("ab_run", "pilot")


def safe_path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a non-empty string")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path escapes plugin root: {value}")
    return root / relative


def add_check(checks: list[dict], check_id: str, ok: bool, detail: str) -> None:
    checks.append({"id": check_id, "status": "ok" if ok else "failed", "detail": detail})


def check_ok(checks: list[dict], check_id: str) -> bool:
    return any(check["id"] == check_id and check["status"] == "ok" for check in checks)


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing frontmatter start")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("missing frontmatter end") from exc
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        if key in data or not isinstance(value, str) or not value:
            raise ValueError(f"invalid frontmatter key: {key}")
        data[key] = value
    return data


def tree_digest(
    source: Path,
    *,
    jsonl_allowlist: set[Path] | None = None,
    replacements: dict[str, str] | None = None,
) -> str:
    jsonl_allowlist = jsonl_allowlist or set()
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
        payload = item.read_bytes()
        if replacements and item.suffix == ".md":
            text = payload.decode("utf-8")
            for old, new in replacements.items():
                text = text.replace(old, new)
            payload = text.encode("utf-8")
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest()


def parse_host_plugins(payload: object) -> tuple[str, bool | None, str]:
    entries: list[dict] = []
    if isinstance(payload, list):
        entries = [item for item in payload if isinstance(item, dict)]
    elif isinstance(payload, dict):
        for key in ("plugins", "items", "installed"):
            value = payload.get(key)
            if isinstance(value, list):
                entries = [item for item in value if isinstance(item, dict)]
                break
    if not entries:
        raise ValueError("host plugin inventory contains no plugin entries")

    stable_enabled = False
    beta_enabled = False
    stable_seen = False
    beta_seen = False
    for entry in entries:
        identity = " ".join(
            str(entry.get(key, "")) for key in ("name", "id", "pluginId", "plugin_id")
        ).lower()
        raw_status = str(entry.get("status", "")).lower()
        enabled = entry.get("enabled")
        if not isinstance(enabled, bool):
            enabled = raw_status not in {"disabled", "not-installed", "uninstalled"}
        if "mindthus-beta" in identity:
            beta_seen = True
            beta_enabled = beta_enabled or enabled
        elif "mindthus" in identity:
            stable_seen = True
            stable_enabled = stable_enabled or enabled

    stable_state = "enabled" if stable_enabled else ("disabled" if stable_seen else "not-installed")
    beta_state: bool | None = beta_enabled if beta_seen else False
    return stable_state, beta_state, f"entries={len(entries)}"


def diagnose(
    plugin_root: Path,
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
        return {
            "schema_version": "mindthus-native-router-diagnostic-v0.1",
            "integrity": "failed",
            "native_entry_status": "package-unverified",
            "runtime_isolation_status": "unverified",
            "claim_ceiling": "package integrity is unknown",
            "checks": checks,
            "actions": ["rebuild the unpublished successor candidate"],
        }

    add_check(
        checks,
        "profile-contract",
        profile.get("schema_version") == "mindthus-release-profile-v0.3"
        and profile.get("release_line") == "2.0-next-native-thin-router"
        and profile.get("version") == "2.0.0-next.1"
        and profile.get("carrier_mode") == "native-skill-description"
        and profile.get("supported_surfaces") == ["codex-plugin"],
        "unpublished Codex-only native Skill carrier",
    )
    identity = profile.get("plugin_identity", {})
    add_check(
        checks,
        "plugin-identity",
        identity.get("name") == "mindthus-beta"
        and identity.get("marketplace_name") == "mindthus-beta"
        and identity.get("coinstallable_with_stable") is True
        and identity.get("coenabled_with_stable") is False,
        "candidate is separately installable but not co-enabled with Stable",
    )
    adapter = profile.get("namespace_adapter", {})
    add_check(
        checks,
        "namespace-adapter",
        adapter.get("mode") == "package-time-coordinate-only"
        and adapter.get("source_prefix") == "mindthus:"
        and adapter.get("runtime_prefix") == "mindthus-beta:",
        "coordinate-only owner adaptation",
    )

    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        default_prompts = manifest.get("interface", {}).get("defaultPrompt", [])
        default_prompt = default_prompts[0] if len(default_prompts) == 1 else ""
        expected_prompt = profile.get("default_prompt")
        prompt_bytes = len(default_prompt.encode("utf-8"))
        prompt_budget = int(profile.get("budgets", {}).get("default_prompt_max_bytes", 0))
        prompt_policy_free = not any(
            token in default_prompt.lower()
            for token in ("route", "owner", "using-mindthus", "mindthus-beta", "sessionstart")
        )
        manifest_ok = (
            manifest.get("name") == "mindthus-beta"
            and manifest.get("version") == "2.0.0-next.1"
            and manifest.get("skills") == "./skills/"
            and "hooks" not in manifest
            and default_prompt == expected_prompt
            and 0 < prompt_bytes <= prompt_budget
            and prompt_policy_free
        )
        add_check(checks, "plugin-manifest", manifest_ok, f"default_prompt_bytes={prompt_bytes}")
    except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError) as exc:
        add_check(checks, "plugin-manifest", False, str(exc))

    for value in profile.get("active_runtime_paths", []):
        try:
            path = safe_path(root, value)
            add_check(checks, f"active:{value}", path.exists(), value)
        except (OSError, ValueError) as exc:
            add_check(checks, f"active:{value}", False, str(exc))
    for value in profile.get("forbidden_active_paths", []):
        try:
            path = safe_path(root, value)
            add_check(checks, f"forbidden:{value}", not path.exists(), value)
        except (OSError, ValueError) as exc:
            add_check(checks, f"forbidden:{value}", False, str(exc))
    for value in profile.get("reference_only_paths", []):
        try:
            path = safe_path(root, value)
            add_check(checks, f"reference:{value}", path.exists(), value)
        except (OSError, ValueError) as exc:
            add_check(checks, f"reference:{value}", False, str(exc))

    for value, expected in profile.get("artifact_sha256", {}).items():
        try:
            path = safe_path(root, value)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            add_check(checks, f"artifact:{value}", actual == expected, f"{value}: {actual}")
        except (OSError, ValueError) as exc:
            add_check(checks, f"artifact:{value}", False, str(exc))
    generated = profile.get("generated_artifact_sha256", {}).get("codex-plugin", {})
    for value, expected in generated.items():
        try:
            path = safe_path(root, value)
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            add_check(checks, f"generated:{value}", actual == expected, f"{value}: {actual}")
        except (OSError, ValueError) as exc:
            add_check(checks, f"generated:{value}", False, str(exc))

    using_path = root / "skills" / "using-mindthus" / "SKILL.md"
    try:
        using_text = using_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(using_path)
        budgets = profile.get("budgets", {})
        entry_bytes = len(using_text.encode("utf-8"))
        entry_words = len(using_text.split())
        description_bytes = len(frontmatter.get("description", "").encode("utf-8"))
        required_phrases = (
            "Mandatory thin Mindthus entry for every conversation",
            "**Direct:**",
            "**Evidence first:**",
            "**Hard judgment:**",
            "**Frame:**",
            "**Whole:**",
            "**Decision context:**",
            "**Anti-Spiral:**",
        )
        forbidden_entry_tokens = (
            "gpt-5",
            "sol",
            "sessionstart",
            "3l5s",
            "edsp",
            "sela",
            "mpg",
            "wae",
            "tvg",
            "tplan",
        )
        entry_ok = (
            set(frontmatter) == {"name", "description"}
            and frontmatter.get("name") == "using-mindthus"
            and entry_bytes <= int(budgets.get("using_mindthus_max_bytes", 0))
            and entry_words <= int(budgets.get("using_mindthus_max_words", 0))
            and description_bytes <= int(budgets.get("description_max_bytes", 0))
            and all(phrase in using_text for phrase in required_phrases)
            and not any(token in using_text.lower() for token in forbidden_entry_tokens)
        )
        add_check(
            checks,
            "thin-entry-contract",
            entry_ok,
            f"words={entry_words}; bytes={entry_bytes}; description_bytes={description_bytes}",
        )
    except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
        add_check(checks, "thin-entry-contract", False, str(exc))

    try:
        lock_path = safe_path(root, profile.get("reference_lock"))
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        owner_records = {
            record.get("id"): record
            for record in lock.get("trees", [])
            if isinstance(record, dict) and str(record.get("id", "")).startswith("owner-")
        }
        for name in OWNER_NAMES:
            record = owner_records.get(f"owner-{name}", {})
            package_path = safe_path(root, record.get("package_path"))
            allowlist = {Path(value) for value in record.get("jsonl_allowlist", [])}
            actual = tree_digest(
                package_path,
                jsonl_allowlist=allowlist,
                replacements={"mindthus-beta:": "mindthus:"},
            )
            add_check(
                checks,
                f"owner-lock:{name}",
                package_path.is_dir() and actual == record.get("sha256"),
                f"skills/{name}: {actual}",
            )
        shared = owner_records.get("owner-shared-runtime", {})
        shared_path = safe_path(root, shared.get("package_paths_by_surface", {}).get("codex-plugin"))
        shared_digest = tree_digest(shared_path)
        add_check(
            checks,
            "owner-lock:shared-runtime",
            shared_path.is_dir() and shared_digest == shared.get("sha256"),
            f"_runtime: {shared_digest}",
        )
    except (OSError, ValueError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        add_check(checks, "owner-lock", False, str(exc))

    stable_hits: list[str] = []
    for name in (*OWNER_NAMES, "using-mindthus"):
        skill_root = root / "skills" / name
        for path in sorted(skill_root.rglob("*.md")) if skill_root.is_dir() else []:
            if "mindthus:" in path.read_text(encoding="utf-8"):
                stable_hits.append(path.relative_to(root).as_posix())
    add_check(
        checks,
        "active-namespace-isolation",
        not stable_hits,
        "no Stable coordinates in active Skills" if not stable_hits else str(stable_hits),
    )

    integrity = "ok" if all(check["status"] == "ok" for check in checks) else "failed"
    if isolation_evidence == "observed" and beta_enabled is not True:
        isolation_status = "candidate-inactive"
    elif stable_state == "enabled":
        isolation_status = "conflict"
    elif stable_state in {"disabled", "not-installed"}:
        isolation_status = "isolated-observed" if isolation_evidence == "observed" else "isolated-reported"
    else:
        isolation_status = "unverified"

    if integrity != "ok":
        claim_ceiling = "candidate package integrity is not established"
        actions.append("rebuild the unpublished successor candidate from locked sources")
    elif isolation_status == "conflict":
        claim_ceiling = "Stable and candidate are co-enabled; behavior and cost are not isolated"
        actions.append("disable Stable before any successor qualification")
    elif isolation_status == "candidate-inactive":
        claim_ceiling = "the candidate is not enabled in the observed host inventory"
        actions.append("enable only mindthus-beta in a fresh isolated CODEX_HOME")
    elif isolation_status == "unverified":
        claim_ceiling = "static package verified; runtime isolation is unverified"
        actions.append("verify Stable is disabled or not installed before qualification")
    else:
        claim_ceiling = (
            "static native-entry package and isolation are verified; activation, passive recall, "
            "owner selection, quality, tokens, and latency remain unproven"
        )

    return {
        "schema_version": "mindthus-native-router-diagnostic-v0.1",
        "release_line": profile.get("release_line"),
        "version": profile.get("version"),
        "plugin_name": identity.get("name"),
        "surface": "codex-plugin",
        "integrity": integrity,
        "native_entry_status": "packaged-unproven" if integrity == "ok" else "package-unverified",
        "direct_owner_status": (
            "packaged-verified"
            if all(check_ok(checks, f"owner-lock:{name}") for name in OWNER_NAMES)
            else "failed"
        ),
        "stable_runtime_state": stable_state,
        "runtime_isolation_evidence": isolation_evidence,
        "host_plugin_observation": host_observation,
        "runtime_isolation_status": isolation_status,
        "claim_ceiling": claim_ceiling,
        "checks": checks,
        "actions": actions,
    }


def render_text(result: dict) -> str:
    lines = [
        (
            f"Mindthus native thin router: integrity={result['integrity']} "
            f"entry={result['native_entry_status']} "
            f"isolation={result['runtime_isolation_status']}"
        ),
        f"Claim ceiling: {result['claim_ceiling']}",
    ]
    lines.extend(
        f"FAIL {check['id']}: {check['detail']}"
        for check in result["checks"]
        if check["status"] != "ok"
    )
    lines.extend(f"ACTION: {action}" for action in result["actions"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Built or installed mindthus-beta plugin root",
    )
    isolation = parser.add_mutually_exclusive_group()
    isolation.add_argument("--stable-state", choices=STABLE_STATES, default="unknown")
    isolation.add_argument("--host-plugins-json", type=Path)
    parser.add_argument("--require-isolated", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    stable_state = args.stable_state
    isolation_evidence = "reported"
    beta_enabled: bool | None = None
    host_observation: str | None = None
    if args.host_plugins_json:
        try:
            payload = json.loads(args.host_plugins_json.read_text(encoding="utf-8"))
            stable_state, beta_enabled, host_observation = parse_host_plugins(payload)
            isolation_evidence = "observed"
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            stable_state = "unknown"
            isolation_evidence = "inspection-failed"
            host_observation = str(exc)

    result = diagnose(
        args.plugin_root,
        stable_state,
        isolation_evidence=isolation_evidence,
        beta_enabled=beta_enabled,
        host_observation=host_observation,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result))

    if result["integrity"] != "ok":
        return 1
    if result["runtime_isolation_status"] in {"conflict", "candidate-inactive"}:
        return 3
    if args.require_isolated and result["runtime_isolation_status"] not in {
        "isolated-observed",
        "isolated-reported",
    }:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
