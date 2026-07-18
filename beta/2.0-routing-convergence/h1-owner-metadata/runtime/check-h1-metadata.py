#!/usr/bin/env python3
"""Fail-closed static verifier for the unpublished H1 metadata candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


OWNERS = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")


def frontmatter_and_body(path: Path) -> tuple[dict[str, str], bytes]:
    payload = path.read_bytes()
    marker = b"---\n"
    if not payload.startswith(marker):
        raise ValueError("missing frontmatter start")
    end = payload.find(marker, len(marker))
    if end < 0:
        raise ValueError("missing frontmatter end")
    data: dict[str, str] = {}
    for raw in payload[len(marker) : end].decode("utf-8").splitlines():
        key, value = raw.split(":", 1)
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        data[key.strip()] = value
    return data, payload[end + len(marker) :]


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("path must be a non-empty string")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path escapes plugin root: {value}")
    return root / relative


def check(checks: list[dict], check_id: str, ok: bool, detail: str) -> None:
    checks.append({"id": check_id, "status": "ok" if ok else "failed", "detail": detail})


def diagnose(root: Path, stable_state: str, require_isolated: bool) -> dict:
    checks: list[dict] = []
    try:
        profile = json.loads((root / "beta" / "release-profile.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "mindthus-h1-diagnostic-v0.1",
            "integrity": "failed",
            "runtime_isolation_status": "unverified",
            "claim_ceiling": "candidate package profile is unreadable",
            "checks": [{"id": "profile", "status": "failed", "detail": str(exc)}],
        }

    check(
        checks,
        "profile-contract",
        profile.get("schema_version") == "mindthus-release-profile-v0.4"
        and profile.get("release_line") == "2.0-routing-h1-metadata"
        and profile.get("version") == "2.0.0-next.2"
        and profile.get("carrier_mode") == "native-skill-description"
        and profile.get("supported_surfaces") == ["codex-plugin"],
        "distinct unpublished Codex-only H1 profile",
    )

    try:
        manifest = json.loads((root / ".codex-plugin" / "plugin.json").read_text())
        prompts = manifest.get("interface", {}).get("defaultPrompt", [])
        prompt = prompts[0] if len(prompts) == 1 else ""
        check(
            checks,
            "plugin-manifest",
            manifest.get("name") == "mindthus-beta"
            and manifest.get("version") == "2.0.0-next.2"
            and manifest.get("skills") == "./skills/"
            and "hooks" not in manifest
            and prompt == profile.get("default_prompt")
            and not any(
                token in prompt.lower()
                for token in ("route", "owner", "using-mindthus", "mindthus-beta", "sessionstart")
            ),
            "neutral default prompt and no Hook",
        )
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        check(checks, "plugin-manifest", False, str(exc))

    for relative in profile.get("forbidden_active_paths", []):
        try:
            check(checks, f"forbidden:{relative}", not safe(root, relative).exists(), relative)
        except ValueError as exc:
            check(checks, f"forbidden:{relative}", False, str(exc))

    for relative, expected in profile.get("artifact_sha256", {}).items():
        try:
            actual = sha(safe(root, relative).read_bytes())
            check(checks, f"artifact:{relative}", actual == expected, actual)
        except (OSError, ValueError) as exc:
            check(checks, f"artifact:{relative}", False, str(exc))
    for relative, expected in profile.get("generated_artifact_sha256", {}).get(
        "codex-plugin", {}
    ).items():
        try:
            actual = sha(safe(root, relative).read_bytes())
            check(checks, f"generated:{relative}", actual == expected, actual)
        except (OSError, ValueError) as exc:
            check(checks, f"generated:{relative}", False, str(exc))

    expected_entry = profile.get("thin_entry_sha256")
    try:
        entry = root / "skills" / "using-mindthus" / "SKILL.md"
        check(checks, "thin-entry-lock", sha(entry.read_bytes()) == expected_entry, sha(entry.read_bytes()))
    except OSError as exc:
        check(checks, "thin-entry-lock", False, str(exc))

    overrides = profile.get("owner_description_overrides", {})
    body_hashes = profile.get("owner_body_sha256", {})
    source_descriptions = profile.get("unchanged_owner_descriptions", {})
    packaged_names: list[str] = []
    for owner in OWNERS:
        try:
            skill = root / "skills" / owner / "SKILL.md"
            metadata, body = frontmatter_and_body(skill)
            packaged_names.append(metadata.get("name", ""))
            expected_description = overrides.get(owner, source_descriptions.get(owner))
            normalized_body = body.replace(b"mindthus-beta:", b"mindthus:")
            check(
                checks,
                f"owner:{owner}",
                set(metadata) == {"name", "description"}
                and metadata.get("name") == owner
                and metadata.get("description") == expected_description
                and sha(normalized_body) == body_hashes.get(owner),
                f"body={sha(normalized_body)}; description_bytes={len(metadata.get('description', '').encode('utf-8'))}",
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            check(checks, f"owner:{owner}", False, str(exc))
    check(checks, "owner-inventory", packaged_names == list(OWNERS), str(packaged_names))

    stable_hits: list[str] = []
    for owner in (*OWNERS, "using-mindthus"):
        skill_root = root / "skills" / owner
        for path in sorted(skill_root.rglob("*.md")) if skill_root.is_dir() else []:
            if "mindthus:" in path.read_text(encoding="utf-8"):
                stable_hits.append(path.relative_to(root).as_posix())
    check(checks, "namespace-isolation", not stable_hits, str(stable_hits))

    isolation = (
        "isolated-reported"
        if stable_state in {"disabled", "not-installed"}
        else "conflict" if stable_state == "enabled" else "unverified"
    )
    integrity = "ok" if all(item["status"] == "ok" for item in checks) else "failed"
    if require_isolated and isolation != "isolated-reported":
        integrity = "failed"
    if integrity != "ok":
        ceiling = "H1 package integrity or isolation is not established"
    else:
        ceiling = (
            "static package and reported isolation only; activation, owner selection, passive recall, "
            "answer quality, tokens, and latency remain unproven"
        )
    return {
        "schema_version": "mindthus-h1-diagnostic-v0.1",
        "integrity": integrity,
        "runtime_isolation_status": isolation,
        "claim_ceiling": ceiling,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", required=True, type=Path)
    parser.add_argument(
        "--stable-state", choices=("unknown", "disabled", "not-installed", "enabled"), default="unknown"
    )
    parser.add_argument("--require-isolated", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = diagnose(args.plugin_root.resolve(), args.stable_state, args.require_isolated)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result["claim_ceiling"])
    return 0 if result["integrity"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
