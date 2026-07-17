#!/usr/bin/env python3
"""Narrow generator-resource view correction for the frozen v0.4 run."""

from __future__ import annotations

import hashlib
import re
import shlex
from pathlib import Path
from typing import Any, Iterable, Mapping

import run_real_codex_evaluation_v04 as base


AMENDMENT_ID = "0.4-generator-view.1"


def _inner_shell_tokens(command: str) -> list[str]:
    """Return the script tokens carried by `zsh -lc`, or a safe fallback."""

    try:
        outer = shlex.split(command)
        if "-lc" in outer:
            index = outer.index("-lc")
            if index + 1 < len(outer):
                return shlex.split(outer[index + 1])
        return outer
    except ValueError:
        return [command]


def _keyword_scan_text(command: str) -> str:
    """Remove only selectors that explicitly exclude forbidden resources."""

    tokens = _inner_shell_tokens(command)
    separators = {"&&", "||", ";", "|", "&"}

    def segment_before(index: int) -> list[str]:
        start = 0
        for position in range(index - 1, -1, -1):
            if tokens[position] in separators:
                start = position + 1
                break
        return tokens[start:index]

    def is_negative_rg_glob(index: int, token: str) -> bool:
        previous = tokens[index - 1] if index else ""
        if previous not in {"-g", "--glob"} or not token.startswith("!"):
            return False
        return any(Path(item).name == "rg" for item in segment_before(index))

    def is_pruned_find_selector(index: int, token: str) -> bool:
        previous = tokens[index - 1] if index else ""
        if (
            not tokens
            or Path(tokens[0]).name != "find"
            or previous not in {"-name", "-iname", "-path", "-ipath"}
            or "superpowers" not in token.lower()
        ):
            return False
        if any(
            item in {"-delete", "-exec", "-execdir", "-ok", "-okdir"}
            for item in tokens
        ):
            return False
        try:
            prune_index = tokens.index("-prune", index + 1)
            tokens.index("-o", prune_index + 1)
        except ValueError:
            return False
        return True

    sanitized: list[str] = []
    for index, token in enumerate(tokens):
        if is_negative_rg_glob(index, token):
            sanitized.append("<negative-glob>")
            continue
        if is_pruned_find_selector(index, token):
            sanitized.append("<pruned-name>")
            continue
        sanitized.append(token)
    return " ".join(sanitized)


def _mask_allowed_root(command: str, root: str) -> str:
    """Mask an exact allowed path while rejecting lookalike path prefixes."""

    resolved = str(Path(root).resolve())
    pattern = re.compile(rf"(?<![\w./-]){re.escape(resolved)}(?![\w.-])")
    return pattern.sub("<ACTIVE_ARM_ALLOWED_ROOT>", command)


def command_violations(
    command: str,
    *,
    active_package_root: str,
    active_execution_root: str | None = None,
    forbidden_path_fragments: Iterable[str],
) -> list[str]:
    """Classify actual forbidden reads without treating exclusions as reads."""

    masked = _mask_allowed_root(command, active_package_root)
    if active_execution_root is not None:
        masked = _mask_allowed_root(masked, active_execution_root)
    violations: list[str] = []
    if base.FORBIDDEN_GENERATOR_COMMAND.search(_keyword_scan_text(masked)):
        violations.append("forbidden-resource-reference")
    if "../" in masked:
        violations.append("parent-traversal")
    if any(str(fragment) in masked for fragment in forbidden_path_fragments):
        violations.append("forbidden-path")
    return sorted(set(violations))


def contaminated_commands(
    commands: Iterable[str],
    *,
    active_package_root: str,
    active_execution_root: str | None = None,
    forbidden_path_fragments: Iterable[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for command in commands:
        violations = command_violations(
            command,
            active_package_root=active_package_root,
            active_execution_root=active_execution_root,
            forbidden_path_fragments=forbidden_path_fragments,
        )
        if violations:
            findings.append(
                {
                    "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
                    "violations": violations,
                }
            )
    return findings


def execute_generator_cell(
    *,
    cell: Mapping[str, Any],
    case: Mapping[str, Any],
    manifest: Mapping[str, Any],
    authorization: Mapping[str, Any],
    protocol_sha256: str,
    out_dir: Path,
    timeout: int,
    generation_calls_used: int,
    forbidden_path_fragments: Iterable[str],
) -> tuple[dict[str, Any], int, int]:
    """Execute one cell with the corrected, otherwise unchanged v0.4 gate."""

    cell_id, key = base.cell_identity(cell, case, manifest, protocol_sha256)
    existing = base.completed_cell(out_dir, cell_id)
    if existing:
        if existing.get("cell_key") != key:
            raise base.EvaluationStop(
                "protocol-or-arm-drift", f"retained cell differs: {cell_id}"
            )
        if existing.get("telemetry", {}).get("evidence_gate", {}).get("status") != "pass":
            raise base.EvaluationStop(
                "missing-primary-native-evidence",
                f"retained cell has a blocked evidence gate: {cell_id}",
            )
        return existing, 0, 0

    orphan_attempts = sorted(
        (out_dir / "generation-attempts" / cell_id).glob("attempt-*")
    )
    if orphan_attempts:
        raise base.EvaluationStop(
            "untraceable-or-partial-artifact",
            f"generation attempt exists without an atomic cell record: {cell_id}",
        )

    prompt = base.generator_prompt(base.user_prompt(case["source"]))
    attempts_used = 0
    counted_tokens = 0
    for attempt_number in (1, 2):
        if (
            generation_calls_used + attempts_used
            >= authorization["maximum_generation_calls"]
        ):
            raise base.EvaluationStop(
                "authority-or-evidence-regression", "generation call ceiling reached"
            )
        attempt, capture, answer, evidence = base.run_generator_attempt(
            cell_id=cell_id,
            prompt=prompt,
            manifest=manifest,
            authorization=authorization,
            out_dir=out_dir,
            attempt_number=attempt_number,
            timeout=timeout,
        )
        attempts_used += 1
        counted_tokens += int(attempt["counted_tokens"])
        failed = capture.returncode != 0 or capture.timed_out
        if failed and answer:
            raise base.EvaluationStop(
                "untraceable-or-partial-artifact",
                f"{cell_id} failed after semantic output; output retained and no retry allowed",
            )
        if failed and attempt_number == 1:
            continue
        if failed:
            raise base.EvaluationStop(
                "untraceable-or-partial-artifact",
                f"{cell_id} infrastructure retry failed",
            )

        contaminated = contaminated_commands(
            evidence["loaded_commands"],
            active_package_root=str(manifest["package"]["root"]),
            active_execution_root=str(manifest["host"]["execution_root"]),
            forbidden_path_fragments=forbidden_path_fragments,
        )
        if contaminated:
            raise base.EvaluationStop(
                "cross-arm-contamination",
                f"{cell_id} loaded forbidden evaluation resources",
            )

        native = dict(evidence["native_telemetry"])
        raw_turn = {
            "usage": evidence["usage"],
            "duration_seconds": capture.wall_time_seconds,
            "first_observable_action_latency_seconds": (
                capture.first_observable_action["offset_seconds"]
                if capture.first_observable_action
                else None
            ),
            "native_telemetry": native,
            "loaded_commands": evidence["loaded_commands"],
            "answer": answer,
            "agent_messages": evidence["agent_messages"],
            "returncode": capture.returncode,
            "timed_out": capture.timed_out,
        }
        required_evidence = dict(base.V04_REQUIRED_EVIDENCE)
        if manifest["arm_id"] == "thin-kernel":
            required_evidence["arm.hook_observation_receipt"] = ("deterministic",)
        telemetry = base.build_turn_telemetry(
            raw_turn,
            context={
                "case_id": cell["case_id"],
                "turn_index": 1,
                "entry_mode": case["contract"]["entry_mode"],
                "execution_root": manifest["host"]["execution_root"],
                "allowed_roots": [
                    manifest["package"]["root"],
                    manifest["host"]["execution_root"],
                ],
                "arm_manifest": manifest,
                "attempt": attempt_number,
            },
            required_evidence=required_evidence,
        )
        record: dict[str, Any] = {
            "schema_version": "mindthus-beta2-real-cell-v0.4",
            "cell_id": cell_id,
            "cell_key": key,
            "arm_id": cell["arm_id"],
            "case_source_receipt": base.canonical_sha256(case["contract"]["source"]),
            "generation_attempt": {
                "attempt": attempt_number,
                "attempt_digest": attempt["attempt_digest"],
                "path": attempt["path"],
            },
            "answer_path": str(Path(attempt["path"]) / "answer.txt"),
            "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
            "event_types": evidence["event_types"],
            "transport_error_event_count": evidence["event_types"].count("error"),
            "usage": evidence["usage"],
            "counted_tokens": base.token_total(evidence["usage"]),
            "telemetry": telemetry,
            "native_first_useful_action_available": bool(
                evidence["first_native_timestamp"]
            ),
            "host_lifecycle_claim": "startup-session-only",
            "scenario_lifecycle_path": case["contract"]["lifecycle_path"],
        }
        record["record_digest"] = base.canonical_sha256(record)
        base.write_atomic_json(out_dir / "cells" / cell_id / "record.json", record)
        if telemetry["evidence_gate"]["status"] != "pass":
            raise base.EvaluationStop(
                "missing-primary-native-evidence",
                f"{cell['case_id']}/{cell['arm_id']} evidence gate blocked: "
                f"{telemetry['evidence_gate']['reasons']}",
            )
        return record, attempts_used, counted_tokens
    raise AssertionError("unreachable generator attempt loop")
