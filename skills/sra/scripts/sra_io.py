#!/usr/bin/env python3
"""Shared errors, JSON persistence, run-state loading, and trace event identity for SRA."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from sra_domain import RUN_SCHEMA, TRACE_SCHEMA
from sra_serialization import canonical_json


class SraRuntimeError(ValueError):
    pass


class SraValidationError(SraRuntimeError):
    def __init__(self, findings: Iterable[str]):
        self.findings = list(findings)
        super().__init__("; ".join(self.findings))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SraRuntimeError(f"failed to read JSON at {path}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SraRuntimeError(
            f"invalid JSON at {path}: {exc.msg} (line {exc.lineno} column {exc.colno})"
        ) from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SraRuntimeError(f"failed to read JSONL at {path}: {exc}") from exc
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SraRuntimeError(
                f"invalid JSONL at {path}, line {line_number}: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise SraRuntimeError(
                f"JSONL record at {path}, line {line_number} must be an object"
            )
        records.append(value)
    return records


def save_run_state(path: Path, state: dict[str, Any]) -> None:
    value = dict(state)
    value["updated_at"] = now_iso()
    write_json(path, value)


def load_run(run_dir: Path) -> dict[str, Any]:
    state = load_json(run_dir / "run.json")
    if not isinstance(state, dict):
        raise SraRuntimeError(f"invalid SRA run state at {run_dir / 'run.json'}")
    schema_version = state.get("schema_version")
    if schema_version != RUN_SCHEMA:
        if isinstance(schema_version, str) and schema_version.startswith(
            "sra.context-calibrated-run.v0."
        ):
            raise SraRuntimeError(
                f"SRA run uses {schema_version}; the {RUN_SCHEMA} writer cannot resume it. "
                "Prepare a new version-bound run from the source decision context."
            )
        raise SraRuntimeError(f"invalid SRA run state at {run_dir / 'run.json'}")
    return state


def make_runtime_event(run_id: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    recorded_at = now_iso()
    seed = canonical_json([run_id, event_type, recorded_at, payload])
    return {
        "schema_version": TRACE_SCHEMA,
        "event_id": "EV-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12],
        "run_id": run_id,
        "event_type": event_type,
        "recorded_at": recorded_at,
        "payload": payload,
    }


def expected_runtime_event_id(event: dict[str, Any]) -> str:
    seed = canonical_json([
        event.get("run_id"), event.get("event_type"),
        event.get("recorded_at"), event.get("payload"),
    ])
    return "EV-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
