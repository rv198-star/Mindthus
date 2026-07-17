#!/usr/bin/env python3
"""Build and summarize redacted Mindthus Beta.2 per-turn telemetry.

This module never infers native host evidence from answer text.  Every endpoint
keeps its evidence provenance so callers can fail closed when a claim requires a
stronger source than the one available.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shlex
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "mindthus-beta2-turn-telemetry-v0.1"
SUMMARY_SCHEMA_VERSION = "mindthus-beta2-telemetry-summary-v0.1"
PROVENANCES = {
    "native",
    "deterministic",
    "judge-inferred",
    "self-reported",
    "unavailable",
}
MINDTHUS_SKILL_RE = re.compile(
    r"(?:mindthus(?:-beta)?:|skills/)(using-mindthus|3l5s|edsp|sela|mpg|wae|tvg|tplan)"
    r"(?:/SKILL\.md)?",
    re.IGNORECASE,
)
MINDTHUS_TERM_RE = re.compile(
    r"\b(?:Mindthus|SELA|MPG|EDSP|WAE|TVG|3L5S|tplan|using-mindthus)\b|"
    r"输入定框审计|整体趋势与局部优势|主线承载方案|极限推演|反螺旋",
    re.IGNORECASE,
)
NOTICE_RE = re.compile(
    r"(?:^|\n)\s*(?:注意|提示|warning|notice|caution)\s*[:：]",
    re.IGNORECASE,
)
RESOURCE_SUFFIXES = {
    ".md",
    ".json",
    ".jsonl",
    ".toml",
    ".yaml",
    ".yml",
    ".py",
    ".txt",
}

DEFAULT_REQUIRED_EVIDENCE: dict[str, tuple[str, ...]] = {
    "tokens.input": ("native",),
    "tokens.cached_input": ("native",),
    "tokens.output": ("native",),
    "tokens.reasoning": ("native",),
    "wall_time_seconds": ("deterministic", "native"),
    "first_useful_action_latency_seconds": ("native",),
    "arm_digest": ("native",),
    "host_plugin_inventory": ("native",),
    "hook_state": ("native",),
    "lifecycle_event": ("native",),
}


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _observation(
    value: Any = None,
    provenance: str = "unavailable",
    source: str | None = None,
    *,
    status: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    if provenance not in PROVENANCES:
        raise ValueError(f"unsupported telemetry provenance: {provenance}")
    if provenance == "unavailable":
        value = None
        status = status or "unavailable"
    else:
        status = status or "observed"
    result: dict[str, Any] = {
        "value": value,
        "provenance": provenance,
        "status": status,
    }
    if source:
        result["source"] = source
    if reason:
        result["reason"] = reason
    return result


def _native_value(
    raw: Mapping[str, Any],
    key: str,
    source: str,
) -> dict[str, Any]:
    if key not in raw or raw.get(key) is None:
        return _observation(reason=f"{source} was not emitted")
    return _observation(raw[key], "native", source)


def _path_is_within(path: Path, roots: Iterable[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _resource_receipts(
    commands: Iterable[str],
    *,
    base_dir: Path,
    allowed_roots: Iterable[Path],
) -> list[dict[str, Any]]:
    roots = [root.expanduser().resolve(strict=False) for root in allowed_roots]
    receipts: dict[str, dict[str, Any]] = {}
    for command in commands:
        try:
            tokens = shlex.split(command)
        except ValueError:
            tokens = command.split()
        for token in tokens:
            candidate = token.rstrip(",:;)]}")
            if "/" not in candidate:
                continue
            path = Path(candidate).expanduser()
            if path.name != "SKILL.md" and path.suffix.lower() not in RESOURCE_SUFFIXES:
                continue
            if not path.is_absolute():
                path = base_dir / path
            resolved = path.resolve(strict=False)
            key = str(resolved)
            if _path_is_within(resolved, roots):
                receipt: dict[str, Any] = {
                    "resolved_path": key,
                    "path_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
                    "kind": "skill" if resolved.name == "SKILL.md" else "resource",
                }
                if resolved.is_file():
                    receipt["content_sha256"] = hashlib.sha256(resolved.read_bytes()).hexdigest()
            else:
                receipt = {
                    "resolved_path": None,
                    "path_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
                    "kind": "external-redacted",
                }
            receipts[key] = receipt
    return [receipts[key] for key in sorted(receipts)]


def _skill_hops(commands: Iterable[str]) -> list[str]:
    owners: list[str] = []
    for command in commands:
        for match in MINDTHUS_SKILL_RE.finditer(command):
            owner = match.group(1).lower()
            if owner not in owners:
                owners.append(owner)
    return owners


def _tool_hops(commands: Iterable[str]) -> list[dict[str, str]]:
    return [
        {
            "tool": "command_execution",
            "event_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
        }
        for command in commands
    ]


def _manifest_measurements(
    manifest: Mapping[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, str | None]]:
    if not manifest:
        missing = {
            name: _observation(reason="sealed arm manifest was not supplied")
            for name in (
                "arm_digest",
                "carrier_digest",
                "host_plugin_inventory",
                "hook_trust",
                "hook_state",
            )
        }
        return missing, {
            "arm_id": None,
            "surface": None,
            "host_runtime": None,
        }

    host = manifest.get("host") if isinstance(manifest.get("host"), Mapping) else {}
    runtime = host.get("runtime") if isinstance(host.get("runtime"), Mapping) else {}
    plugin_list = (
        host.get("plugin_list") if isinstance(host.get("plugin_list"), Mapping) else {}
    )
    carrier = (
        manifest.get("carrier") if isinstance(manifest.get("carrier"), Mapping) else {}
    )
    ambient = (
        manifest.get("ambient_context")
        if isinstance(manifest.get("ambient_context"), Mapping)
        else {}
    )
    opaque = ambient.get("opaque") if isinstance(ambient.get("opaque"), list) else []
    hook_receipts = [
        item
        for item in opaque
        if isinstance(item, Mapping)
        and item.get("kind") == "host-hook-observation"
        and item.get("id") == "passive-kernel-session-start"
        and isinstance(item.get("sha256"), str)
    ]
    diagnostic = (
        manifest.get("runtime_diagnostic")
        if isinstance(manifest.get("runtime_diagnostic"), Mapping)
        else None
    )
    coordinates = plugin_list.get("active_mindthus_coordinates")
    inventory = list(coordinates) if isinstance(coordinates, list) else None
    hook_state = carrier.get("hook_state")
    hook_trust = (
        "carrier-verified"
        if diagnostic and diagnostic.get("integrity") == "ok"
        and diagnostic.get("carrier_status") == "verified"
        else "sealed-not-applicable"
        if manifest.get("arm_id") == "stable"
        else None
    )
    host_parts = [runtime.get("name"), runtime.get("version"), runtime.get("platform")]
    host_runtime = "/".join(str(item) for item in host_parts if item)

    values = {
        "arm_digest": _native_value(
            manifest,
            "identity_digest",
            "sealed-arm-manifest.identity_digest",
        ),
        "carrier_digest": _observation(
            _canonical_sha256(carrier),
            "deterministic",
            "sealed-arm-manifest.carrier",
        ),
        "host_plugin_inventory": (
            _observation(
                inventory,
                "native",
                "sealed-arm-manifest.host.plugin_list",
            )
            if inventory is not None
            else _observation(reason="active plugin inventory is absent")
        ),
        "hook_trust": (
            _observation(
                hook_trust,
                "native",
                "sealed-arm-manifest.runtime_diagnostic",
            )
            if hook_trust is not None
            else _observation(reason="runtime diagnostic cannot establish hook trust")
        ),
        "hook_state": (
            _observation(
                hook_state,
                "native",
                "sealed-arm-manifest.carrier.hook_state",
            )
            if hook_state is not None
            else _observation(reason="sealed hook state is absent")
        ),
    }
    if len(hook_receipts) == 1:
        values["arm.hook_observation_receipt"] = _observation(
            hook_receipts[0]["sha256"],
            "deterministic",
            "sealed-arm-manifest.ambient_context.opaque",
        )
    return values, {
        "arm_id": str(manifest.get("arm_id")) if manifest.get("arm_id") else None,
        "surface": str(manifest.get("surface")) if manifest.get("surface") else None,
        "host_runtime": host_runtime or None,
    }


def evaluate_required_evidence(
    measurements: Mapping[str, Mapping[str, Any]],
    requirements: Mapping[str, Iterable[str]],
) -> dict[str, Any]:
    endpoint_results: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    for endpoint, allowed_values in requirements.items():
        allowed = list(allowed_values)
        observed = measurements.get(endpoint)
        if not observed or observed.get("status") == "unavailable":
            status = "missing"
        elif observed.get("status") == "contradictory":
            status = "contradictory"
        elif observed.get("provenance") not in allowed:
            status = "provenance_mismatch"
        else:
            status = "satisfied"
        endpoint_results[endpoint] = {
            "status": status,
            "required_provenance": allowed,
            "observed_provenance": observed.get("provenance") if observed else "unavailable",
        }
        if status != "satisfied":
            reasons.append(f"{endpoint}:{status}")
    return {
        "status": "pass" if not reasons else "blocked",
        "reasons": reasons,
        "endpoint_results": endpoint_results,
    }


def _apply_contradictions(
    measurements: dict[str, dict[str, Any]],
    explicit: Mapping[str, str] | None,
) -> None:
    input_value = measurements["tokens.input"].get("value")
    cached_value = measurements["tokens.cached_input"].get("value")
    if isinstance(input_value, (int, float)) and isinstance(cached_value, (int, float)):
        if cached_value > input_value:
            measurements["tokens.cached_input"]["status"] = "contradictory"
            measurements["tokens.cached_input"]["reason"] = (
                "cached input tokens exceed total input tokens"
            )
    duration = measurements["wall_time_seconds"].get("value")
    for endpoint, label in (
        ("first_useful_action_latency_seconds", "first useful action"),
        ("first_observable_action_latency_seconds", "first observable action"),
    ):
        observation = measurements.get(endpoint)
        first_action = observation.get("value") if observation else None
        if isinstance(duration, (int, float)) and isinstance(first_action, (int, float)):
            if first_action > duration:
                observation["status"] = "contradictory"
                observation["reason"] = f"{label} occurs after turn wall time"
    for endpoint, reason in (explicit or {}).items():
        if endpoint in measurements:
            measurements[endpoint]["status"] = "contradictory"
            measurements[endpoint]["reason"] = str(reason)


def build_turn_telemetry(
    raw_turn: Mapping[str, Any],
    *,
    context: Mapping[str, Any] | None = None,
    required_evidence: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    """Create one redacted evidence record from a runner turn.

    `raw_turn` may contain sensitive prompt/answer/command content.  The returned
    record intentionally stores none of those raw values.
    """

    context = context or {}
    usage = raw_turn.get("usage") if isinstance(raw_turn.get("usage"), Mapping) else {}
    native = (
        raw_turn.get("native_telemetry")
        if isinstance(raw_turn.get("native_telemetry"), Mapping)
        else {}
    )
    commands = [str(value) for value in raw_turn.get("loaded_commands", [])]
    answer = str(raw_turn.get("answer", ""))
    agent_messages = [str(value) for value in raw_turn.get("agent_messages", [])]
    manifest = (
        context.get("arm_manifest")
        if isinstance(context.get("arm_manifest"), Mapping)
        else None
    )
    manifest_values, stratum = _manifest_measurements(manifest)

    base_dir = Path(str(context.get("execution_root") or ".")).expanduser().resolve(strict=False)
    allowed_roots = [Path(str(root)) for root in context.get("allowed_roots", [base_dir])]
    resources = _resource_receipts(
        commands,
        base_dir=base_dir,
        allowed_roots=allowed_roots,
    )
    skill_hops = _skill_hops(commands)
    tool_hops = _tool_hops(commands)

    judge = (
        context.get("judge_telemetry")
        if isinstance(context.get("judge_telemetry"), Mapping)
        else {}
    )
    clarification = (
        _observation(
            judge["clarification_turns"],
            "judge-inferred",
            "blinded-judge.clarification_turns",
        )
        if judge.get("clarification_turns") is not None
        else _observation(reason="clarification count was not judged")
    )
    lifecycle = (
        _observation(
            native["lifecycle_event"],
            "native",
            "host.lifecycle_event",
        )
        if native.get("lifecycle_event") is not None
        else _observation(reason="host lifecycle event was not emitted")
    )

    measurements: dict[str, dict[str, Any]] = {
        "tokens.input": _native_value(usage, "input_tokens", "turn.completed.usage.input_tokens"),
        "tokens.cached_input": _native_value(
            usage,
            "cached_input_tokens",
            "turn.completed.usage.cached_input_tokens",
        ),
        "tokens.output": _native_value(
            usage,
            "output_tokens",
            "turn.completed.usage.output_tokens",
        ),
        "tokens.reasoning": _native_value(
            usage,
            "reasoning_output_tokens",
            "turn.completed.usage.reasoning_output_tokens",
        ),
        "wall_time_seconds": (
            _observation(
                raw_turn["duration_seconds"],
                "deterministic",
                "runner.monotonic_wall_time",
            )
            if raw_turn.get("duration_seconds") is not None
            else _observation(reason="runner wall time is absent")
        ),
        "first_useful_action_latency_seconds": (
            _observation(
                native["first_useful_action_latency_seconds"],
                "native",
                "host.first_useful_action_event",
            )
            if native.get("first_useful_action_latency_seconds") is not None
            else _observation(
                reason="no native first-useful-action event; text inference is forbidden"
            )
        ),
        "skill_hops": _observation(skill_hops, "deterministic", "command-event classification"),
        "tool_hops": _observation(tool_hops, "deterministic", "command-event digests"),
        "resource_reads": _observation(
            resources,
            "deterministic",
            "command-event path classification",
        ),
        "retry_count": _observation(
            max(int(context.get("attempt", 1)) - 1, 0),
            "deterministic",
            "orchestrator.attempt",
        ),
        "failure_count": _observation(
            1 if raw_turn.get("timed_out") or raw_turn.get("returncode", 0) != 0 else 0,
            "deterministic",
            "runner.returncode_and_timeout",
        ),
        "clarification_turns": clarification,
        "visible_notices": _observation(
            {
                "count": sum(len(NOTICE_RE.findall(text)) for text in [answer, *agent_messages]),
            },
            "deterministic",
            "redacted visible-message classification",
        ),
        "mindthus_terminology_leakage": _observation(
            {
                "count": len(MINDTHUS_TERM_RE.findall(answer)),
                "observed": bool(MINDTHUS_TERM_RE.search(answer)),
            },
            "deterministic",
            "redacted final-answer classification",
        ),
        "lifecycle_event": lifecycle,
        **manifest_values,
    }
    if "first_observable_action_latency_seconds" in raw_turn:
        measurements["first_observable_action_latency_seconds"] = (
            _observation(
                raw_turn["first_observable_action_latency_seconds"],
                "deterministic",
                "runner.streaming_jsonl_arrival",
            )
            if raw_turn.get("first_observable_action_latency_seconds") is not None
            else _observation(
                reason="runner observed no eligible streaming JSONL action event"
            )
        )
    _apply_contradictions(
        measurements,
        context.get("contradictions")
        if isinstance(context.get("contradictions"), Mapping)
        else None,
    )

    requirements = {
        key: list(value)
        for key, value in (required_evidence or DEFAULT_REQUIRED_EVIDENCE).items()
    }
    gate = evaluate_required_evidence(measurements, requirements)
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": str(context.get("case_id") or "unknown"),
        "turn_index": int(context.get("turn_index") or 1),
        "stratum": {
            "host_runtime": stratum["host_runtime"] or "unknown",
            "surface": stratum["surface"] or "unknown",
            "entry_mode": str(context.get("entry_mode") or "unknown"),
            "arm_id": stratum["arm_id"] or "unknown",
        },
        "measurements": measurements,
        "required_evidence": requirements,
        "evidence_gate": gate,
        "retention": {
            "policy": "redacted-reproducibility-only",
            "raw_prompt_retained": False,
            "raw_answer_retained": False,
            "raw_commands_retained": False,
            "external_paths_retained": False,
        },
    }
    record["telemetry_digest"] = _canonical_sha256(record)
    return record


def _percentile(values: list[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(probability * len(ordered)))
    return round(float(ordered[rank - 1]), 6)


def summarize_telemetry(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate records without merging host, surface, entry mode, or arm strata."""

    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = {}
    for record in records:
        stratum = record.get("stratum") if isinstance(record.get("stratum"), Mapping) else {}
        key = tuple(
            str(stratum.get(name) or "unknown")
            for name in ("host_runtime", "surface", "entry_mode", "arm_id")
        )
        groups.setdefault(key, []).append(record)

    strata: list[dict[str, Any]] = []
    for key in sorted(groups):
        group = groups[key]
        endpoint_names = sorted(
            {
                name
                for record in group
                for name in (
                    record.get("measurements", {}).keys()
                    if isinstance(record.get("measurements"), Mapping)
                    else []
                )
            }
        )
        endpoints: dict[str, dict[str, Any]] = {}
        for name in endpoint_names:
            observations = [
                record.get("measurements", {}).get(name, {})
                for record in group
                if isinstance(record.get("measurements"), Mapping)
            ]
            observed = [item for item in observations if item.get("status") == "observed"]
            missing = [item for item in observations if item.get("status") == "unavailable"]
            contradictory = [
                item for item in observations if item.get("status") == "contradictory"
            ]
            numeric = [
                float(item["value"])
                for item in observed
                if isinstance(item.get("value"), (int, float))
                and not isinstance(item.get("value"), bool)
            ]
            endpoints[name] = {
                "denominator": len(group),
                "observed_count": len(observed),
                "missing_count": len(missing),
                "contradictory_count": len(contradictory),
                "numeric_count": len(numeric),
                "p50": _percentile(numeric, 0.50),
                "p95": _percentile(numeric, 0.95),
            }
        strata.append(
            {
                "stratum": dict(
                    zip(("host_runtime", "surface", "entry_mode", "arm_id"), key)
                ),
                "record_count": len(group),
                "gate_pass_count": sum(
                    1
                    for record in group
                    if record.get("evidence_gate", {}).get("status") == "pass"
                ),
                "gate_blocked_count": sum(
                    1
                    for record in group
                    if record.get("evidence_gate", {}).get("status") != "pass"
                ),
                "endpoints": endpoints,
            }
        )
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "record_count": sum(len(group) for group in groups.values()),
        "stratum_count": len(strata),
        "strata": strata,
        "percentile_method": "nearest-rank",
        "cross_stratum_rollup": None,
    }


def telemetry_records_from_responses(
    responses: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(telemetry)
        for response in responses
        for turn in response.get("turns", [])
        if isinstance(turn, Mapping)
        for telemetry in [turn.get("telemetry")]
        if isinstance(telemetry, Mapping)
    ]


def summarize_response_telemetry(
    responses: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    response_list = list(responses)
    expected_turn_count = sum(
        len(response.get("turns", []))
        for response in response_list
        if isinstance(response.get("turns"), list)
    )
    records = telemetry_records_from_responses(response_list)
    summary = summarize_telemetry(records)
    summary["expected_turn_count"] = expected_turn_count
    summary["missing_record_count"] = expected_turn_count - len(records)
    summary["record_completeness_gate"] = (
        "pass" if len(records) == expected_turn_count else "blocked"
    )
    return summary
