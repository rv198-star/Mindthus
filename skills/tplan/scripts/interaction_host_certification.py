#!/usr/bin/env python3
"""Record and validate bounded interaction-host certification artifacts.

The artifact is intentionally a claim ledger, not a self-certification shortcut.
``certified`` is accepted only when every stated host precondition is evidenced.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from tplan_runtime import TplanError, read_interaction_guard, read_mission, write_json


SCHEMA_VERSION = "tplan.interaction_host_certification.v0.2"
LEGACY_SCHEMA_VERSION = "tplan.interaction_host_certification.v0.1"
CHECK_FIELDS = {
    "message_arrival",
    "native_tool_gate",
    "direct_release",
    "no_continuation",
    "safe_stop",
    "operator_recovery",
    "overlap",
    "restart_or_timeout",
    "stable_message_identity",
}
ENFORCEMENT_LEVELS = {"advisory_only", "checkpoint_detection", "mutation_prevention"}
EVENT_ORIGINS = {"none", "host_signed", "host_managed_unforgeable"}
STATE_WRITERS = {"same_principal", "host_only"}
RECEIPT_SIGNERS = {"none", "host_only"}


def _safe_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value or len(value) > 500:
        raise TplanError(f"certification {label} must be a safe non-empty single-line string")
    return value


def _parse_time(value: Any) -> None:
    text = _safe_string(value, "recorded_at")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TplanError("certification recorded_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise TplanError("certification recorded_at must include timezone")


def validate_certification(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TplanError("certification artifact must be an object")
    required = {
        "schema_version", "status", "platform", "profile_id", "recorded_at", "host", "hook_sources",
        "state_directory", "checks", "capability", "limitations",
    }
    schema_version = value.get("schema_version")
    if schema_version == SCHEMA_VERSION:
        required.add("authority_boundary")
    if set(value) != required or schema_version not in {SCHEMA_VERSION, LEGACY_SCHEMA_VERSION}:
        raise TplanError("certification artifact schema is invalid")
    if value.get("status") not in {"partial", "certified", "failed"}:
        raise TplanError("certification status must be partial, certified, or failed")
    _safe_string(value.get("platform"), "platform")
    _safe_string(value.get("profile_id"), "profile_id")
    _parse_time(value.get("recorded_at"))
    host = value.get("host")
    if not isinstance(host, dict) or set(host) != {"product", "version", "os"}:
        raise TplanError("certification host must contain product, version, and os")
    for key, item in host.items():
        _safe_string(item, f"host {key}")
    sources = value.get("hook_sources")
    if not isinstance(sources, list) or not sources:
        raise TplanError("certification hook_sources must be a non-empty list")
    for source in sources:
        if not isinstance(source, dict) or set(source) != {"source", "source_hash", "trusted", "enabled"}:
            raise TplanError("certification hook source is malformed")
        _safe_string(source.get("source"), "hook source")
        _safe_string(source.get("source_hash"), "hook source_hash")
        if not isinstance(source.get("trusted"), bool) or not isinstance(source.get("enabled"), bool):
            raise TplanError("certification hook source trusted/enabled must be boolean")
    state = value.get("state_directory")
    if not isinstance(state, dict) or set(state) != {"agent_write_protected", "evidence"}:
        raise TplanError("certification state_directory is malformed")
    if not isinstance(state.get("agent_write_protected"), bool):
        raise TplanError("certification state_directory agent_write_protected must be boolean")
    _safe_string(state.get("evidence"), "state_directory evidence")
    authority = None
    if schema_version == SCHEMA_VERSION:
        authority = value.get("authority_boundary")
        if not isinstance(authority, dict) or set(authority) != {"event_origin", "state_writer", "receipt_signer", "evidence"}:
            raise TplanError("certification authority_boundary is malformed")
        if authority.get("event_origin") not in EVENT_ORIGINS:
            raise TplanError("certification authority_boundary event_origin is unsupported")
        if authority.get("state_writer") not in STATE_WRITERS:
            raise TplanError("certification authority_boundary state_writer is unsupported")
        if authority.get("receipt_signer") not in RECEIPT_SIGNERS:
            raise TplanError("certification authority_boundary receipt_signer is unsupported")
        _safe_string(authority.get("evidence"), "authority_boundary evidence")
    checks = value.get("checks")
    if not isinstance(checks, dict) or set(checks) != CHECK_FIELDS or not all(isinstance(item, bool) for item in checks.values()):
        raise TplanError("certification checks are malformed")
    capability = value.get("capability")
    if not isinstance(capability, dict) or set(capability) != {"enforcement_level", "scope"}:
        raise TplanError("certification capability is malformed")
    if capability.get("enforcement_level") not in ENFORCEMENT_LEVELS:
        raise TplanError("certification enforcement_level is unsupported")
    _safe_string(capability.get("scope"), "capability scope")
    limitations = value.get("limitations")
    if not isinstance(limitations, list) or any(not isinstance(item, str) for item in limitations):
        raise TplanError("certification limitations must be a list of strings")
    for item in limitations:
        _safe_string(item, "limitation")
    if value["status"] == "certified" or capability["enforcement_level"] == "mutation_prevention":
        if schema_version == LEGACY_SCHEMA_VERSION:
            raise TplanError("legacy certification artifacts cannot claim certified mutation prevention")
        if value["profile_id"].endswith("@v0.2-unverified"):
            raise TplanError("an unverified interaction-host profile cannot claim certified mutation prevention")
        if not all(checks.values()) or not state["agent_write_protected"] or not all(
            source["trusted"] and source["enabled"] for source in sources
        ):
            raise TplanError("certification claim lacks required host evidence")
        if authority is None or authority["event_origin"] == "none" or authority["state_writer"] != "host_only" or authority["receipt_signer"] != "host_only":
            raise TplanError("certification claim lacks an unforgeable host authority boundary")
    return value


def default_output_path(mission_dir: Path, platform: str, profile_id: str) -> Path:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", f"{platform}-{profile_id}").strip("-")
    return mission_dir / "reports" / f"interaction-host-certification-{slug}.json"


def record_certification(mission_dir: Path, artifact: Any, *, output: Path | None = None) -> Path:
    read_mission(mission_dir)
    if read_interaction_guard(mission_dir) is not None:
        raise TplanError("interaction guard is open; certification artifact write is blocked")
    artifact = validate_certification(artifact)
    target = (
        output.resolve()
        if output is not None
        else default_output_path(mission_dir.resolve(), artifact["platform"], artifact["profile_id"])
    )
    reports = (mission_dir / "reports").resolve()
    try:
        target.relative_to(reports)
    except ValueError as exc:
        raise TplanError("certification output must remain under Mission reports") from exc
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, artifact, durable=True)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record or validate a TPlan interaction-host certification artifact.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("record", "validate"):
        command = sub.add_parser(name)
        command.add_argument("mission_dir")
        command.add_argument("--input", required=True)
    sub.choices["record"].add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        artifact = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if args.command == "validate":
            validate_certification(artifact)
            print("certification_valid: true")
        else:
            target = record_certification(Path(args.mission_dir).resolve(), artifact, output=Path(args.output) if args.output else None)
            print(f"recorded_certification: {target}")
    except (OSError, ValueError, json.JSONDecodeError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
