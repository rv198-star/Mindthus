#!/usr/bin/env python3
"""Activate Mindthus shared primitives for a small set of runtime events.

The script validates activation shape and prints reminders. It does not judge semantic
truth, output quality, evidence sufficiency, Gate success, or whether work may exit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = SCRIPT_DIR / "manifest.json"
SCHEMA_VERSION = "mindthus-primitive-activation-v0.1"
ALLOWED_METHODS = {
    "using-mindthus",
    "3l5s",
    "edsp",
    "sela",
    "mpg",
    "wae",
    "tvg",
    "tplan",
    "unknown",
}


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_list_of_strings(findings: list[str], data: dict[str, Any], field: str, subject: str) -> None:
    value = data.get(field)
    if not isinstance(value, list) or any(not non_empty_string(item) for item in value):
        findings.append(f"{subject}.{field} must be a list of non-empty strings")


def validate_manifest(manifest: Any) -> list[str]:
    findings: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest root must be an object"]

    if manifest.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"schema_version must be {SCHEMA_VERSION}")
    if manifest.get("script_boundary") != "shape_only_reminder_not_semantic_judgment":
        findings.append("script_boundary must be shape_only_reminder_not_semantic_judgment")

    events = manifest.get("events")
    primitives = manifest.get("primitives")
    if not isinstance(events, dict) or not events:
        findings.append("events must be a non-empty object")
        events = {}
    if not isinstance(primitives, dict) or not primitives:
        findings.append("primitives must be a non-empty object")
        primitives = {}

    for primitive_id, primitive in primitives.items():
        subject = f"primitives.{primitive_id}"
        if not non_empty_string(primitive_id):
            findings.append("primitive id must be a non-empty string")
        if not isinstance(primitive, dict):
            findings.append(f"{subject} must be an object")
            continue
        for field in ("name", "short_rule", "owner"):
            if not non_empty_string(primitive.get(field)):
                findings.append(f"{subject}.{field} must be a non-empty string")
        for field in ("trigger", "action_effect", "not_a"):
            require_list_of_strings(findings, primitive, field, subject)

    for event_name, event in events.items():
        subject = f"events.{event_name}"
        if not non_empty_string(event_name):
            findings.append("event id must be a non-empty string")
        if not isinstance(event, dict):
            findings.append(f"{subject} must be an object")
            continue
        if not non_empty_string(event.get("description")):
            findings.append(f"{subject}.description must be a non-empty string")
        for field in ("active_primitives", "required_agent_checks"):
            require_list_of_strings(findings, event, field, subject)
        for primitive_id in event.get("active_primitives", []):
            if primitive_id not in primitives:
                findings.append(f"{subject}.active_primitives references unknown primitive {primitive_id!r}")
        conditional = event.get("conditional_primitives", [])
        if conditional is None:
            conditional = []
        if not isinstance(conditional, list):
            findings.append(f"{subject}.conditional_primitives must be a list when present")
            continue
        for index, item in enumerate(conditional):
            item_subject = f"{subject}.conditional_primitives[{index}]"
            if not isinstance(item, dict):
                findings.append(f"{item_subject} must be an object")
                continue
            primitive_id = item.get("primitive")
            method = item.get("method")
            if primitive_id not in primitives:
                findings.append(f"{item_subject}.primitive references unknown primitive {primitive_id!r}")
            if method not in ALLOWED_METHODS:
                findings.append(f"{item_subject}.method must be one of: {', '.join(sorted(ALLOWED_METHODS))}")

    return findings


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def activation_for(manifest: dict[str, Any], event_name: str, method: str) -> dict[str, Any]:
    events = manifest["events"]
    primitives = manifest["primitives"]
    event = events[event_name]
    active_ids = list(event["active_primitives"])
    for item in event.get("conditional_primitives", []):
        if item.get("method") == method:
            active_ids.append(item["primitive"])

    active_primitives = [
        {
            "id": primitive_id,
            "name": primitives[primitive_id]["name"],
            "short_rule": primitives[primitive_id]["short_rule"],
            "owner": primitives[primitive_id]["owner"],
            "action_effect": primitives[primitive_id]["action_effect"],
            "not_a": primitives[primitive_id]["not_a"],
        }
        for primitive_id in active_ids
    ]
    return {
        "schema_version": manifest["schema_version"],
        "event": event_name,
        "method": method,
        "active_primitives": active_primitives,
        "required_agent_checks": event["required_agent_checks"],
        "script_verdict": "shape_only",
        "agentic_judgment_required": True,
        "script_must_not_decide": [
            "semantic_truth",
            "evidence_sufficiency",
            "gate_success",
            "exit_state",
            "aesthetic_or_business_success",
            "user_authority",
        ],
    }


def print_text_report(report: dict[str, Any]) -> None:
    print("Primitive Activation Report")
    print(f"event: {report['event']}")
    print(f"method: {report['method']}")
    print()
    print("active_primitives:")
    for primitive in report["active_primitives"]:
        print(f"- {primitive['id']}: {primitive['short_rule']}")
    print()
    print("required_agent_checks:")
    for check in report["required_agent_checks"]:
        print(f"- {check}")
    print()
    print("script_verdict: shape_only")
    print("agentic_judgment_required: true")
    print(
        "Reminder: this script only activates reminders; it does not decide truth, value, Gate success, or exit."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Activate Mindthus shared primitives for a runtime event.")
    parser.add_argument("--event", required=True, help="Activation event, e.g. before-freeze.")
    parser.add_argument("--method", default="unknown", help="Mindthus method context.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Primitive activation manifest path.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    try:
        manifest = load_manifest(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        print("Primitive Activation Report")
        print(f"manifest: {manifest_path}")
        print(f"- BLOCK [manifest-read-failed]: {exc}")
        print("script_verdict: shape_only_failed")
        print("agentic_judgment_required: true")
        return 1

    findings = validate_manifest(manifest)
    if findings:
        print("Primitive Activation Report")
        print(f"manifest: {manifest_path}")
        for finding in findings:
            print(f"- BLOCK [invalid-manifest]: {finding}")
        print("script_verdict: shape_only_failed")
        print("agentic_judgment_required: true")
        return 1

    method = args.method.lower()
    if method not in ALLOWED_METHODS:
        print("Primitive Activation Report")
        print(f"- BLOCK [unsupported-method]: method must be one of: {', '.join(sorted(ALLOWED_METHODS))}")
        print("script_verdict: shape_only_failed")
        print("agentic_judgment_required: true")
        return 1
    if args.event not in manifest["events"]:
        print("Primitive Activation Report")
        print(f"- BLOCK [unsupported-event]: event must be one of: {', '.join(sorted(manifest['events']))}")
        print("script_verdict: shape_only_failed")
        print("agentic_judgment_required: true")
        return 1

    report = activation_for(manifest, args.event, method)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
