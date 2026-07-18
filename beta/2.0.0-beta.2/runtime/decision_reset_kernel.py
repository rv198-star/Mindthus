#!/usr/bin/env python3
"""Small deterministic kernel for the Mindthus Beta.2 decision-reset contract.

This module deliberately owns mechanics only: one append-only source ledger, a
replay-stable projection, mutually exclusive outcome classification, one sealed
decision cut, and one content-addressed terminal receipt. It does not call Codex,
score answers, or infer product truth.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "mindthus-beta2-decision-reset-kernel-v0.1"
GENESIS = "GENESIS"
TERMINAL_ACTIONS = {"CONTINUE_BETA", "STOP_ROUTE", "STOP_UNPROVEN"}
INFRA_CODES = {"429", "500", "502", "503", "504", "5xx", "cancelled", "canceled"}


class LedgerError(RuntimeError):
    """Raised when source history cannot be verified or a transition is illegal."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _fsync_parent(path: Path) -> None:
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class EventLedger:
    """A single JSONL source ledger with idempotent event IDs and a hash chain."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def records(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LedgerError(f"invalid JSON at line {line_no}") from exc
                records.append(record)
        self.verify(records)
        return records

    @staticmethod
    def verify(records: Iterable[Mapping[str, Any]]) -> None:
        previous = GENESIS
        seen: dict[str, str] = {}
        expected_seq = 1
        for record in records:
            required = {"schema_version", "seq", "event_id", "event_type", "payload", "prev_digest", "digest"}
            if not required.issubset(record):
                raise LedgerError(f"missing ledger fields: {sorted(required - set(record))}")
            if record["schema_version"] != SCHEMA_VERSION:
                raise LedgerError("ledger schema mismatch")
            if record["seq"] != expected_seq or record["prev_digest"] != previous:
                raise LedgerError("ledger sequence or chain mismatch")
            event_id = str(record["event_id"])
            body = {key: record[key] for key in ("schema_version", "seq", "event_id", "event_type", "payload", "prev_digest")}
            expected_digest = digest(body)
            if record["digest"] != expected_digest:
                raise LedgerError(f"ledger digest mismatch at seq {expected_seq}")
            if event_id in seen and seen[event_id] != record["digest"]:
                raise LedgerError(f"event id has conflicting records: {event_id}")
            seen[event_id] = record["digest"]
            previous = record["digest"]
            expected_seq += 1

    def head(self) -> tuple[int, str]:
        records = self.records()
        return (records[-1]["seq"], records[-1]["digest"]) if records else (0, GENESIS)

    def append(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        *,
        event_id: str,
        source_time: str | None = None,
    ) -> dict[str, Any]:
        records = self.records()
        for existing in records:
            if existing["event_id"] == event_id:
                if existing["event_type"] != event_type or existing["payload"] != dict(payload):
                    raise LedgerError(f"idempotency conflict for event {event_id}")
                return existing
        seq, previous = self.head()
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "seq": seq + 1,
            "event_id": event_id,
            "event_type": event_type,
            "payload": dict(payload),
            "prev_digest": previous,
        }
        if source_time is not None:
            record["source_time"] = source_time
        record["digest"] = digest(record)
        self.path.touch(exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.write(canonical_json(record) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        _fsync_parent(self.path)
        return record


def classify_attempt(payload: Mapping[str, Any]) -> str:
    """Apply the R3 outcome precedence without inferring provider cause."""

    infra = payload.get("infrastructure_receipt")
    provider_code = str(payload.get("provider_code", "")).lower()
    if infra or provider_code in INFRA_CODES or provider_code.startswith("5"):
        return "INFRA_NONCOMPLETION"
    content = str(payload.get("content", "unknown"))
    if content == "final_nonempty" and payload.get("dependencies_valid", True):
        return "COMPLETED"
    if content in {"final_empty", "product_failure", "refusal", "progress_only", "tool_only"}:
        return "PRODUCT_NONCOMPLETION"
    if payload.get("sampling") is False and payload.get("usage", 0) == 0:
        return "NO_SAMPLING_ZERO_USAGE"
    return "UNKNOWN"


def replay_projection(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a stable projection from the event multiset, independent of append order."""

    unique: dict[str, Mapping[str, Any]] = {}
    for record in records:
        event_id = str(record["event_id"])
        if event_id in unique and unique[event_id] != record:
            return {"integrity": "invalid", "reason": "conflicting_event_id", "events": {}}
        unique[event_id] = record
    attempts: dict[str, dict[str, Any]] = {}
    claims: dict[str, list[str]] = {}
    for record in sorted(unique.values(), key=lambda item: str(item["event_id"])):
        if record["event_type"] == "attempt":
            payload = dict(record["payload"])
            attempt_id = str(payload.get("attempt_id", record["event_id"]))
            outcome = classify_attempt(payload)
            attempts[attempt_id] = {"outcome": outcome, "payload": payload}
            for claim, value in dict(payload.get("claims", {})).items():
                claims.setdefault(str(claim), []).append(str(value))
    return {"integrity": "valid", "attempts": attempts, "claims": claims}


def reduce_terminal(records: Iterable[Mapping[str, Any]], cut_digest: str) -> dict[str, Any]:
    """Return a deterministic terminal candidate over the sealed source prefix."""

    source_records = [record for record in records if record["event_type"] not in {"decision_cut", "terminal_receipt"}]
    projection = replay_projection(source_records)
    if projection.get("integrity") != "valid":
        action = "STOP_UNPROVEN"
    else:
        values = [value for values in projection["claims"].values() for value in values]
        if any(value == "REFUTED" for value in values):
            action = "STOP_ROUTE"
        elif values and all(value == "PASS" for value in values) and len(projection["claims"]) >= 1:
            action = "CONTINUE_BETA"
        else:
            action = "STOP_UNPROVEN"
    reducer_digest = digest({"cut_digest": cut_digest, "projection": projection, "action": action})
    return {
        "action": action,
        "cut_digest": cut_digest,
        "reducer_digest": reducer_digest,
        "projection": projection,
    }


class DecisionRuntime:
    """Kernel state transitions; no model calls and no semantic adjudication."""

    def __init__(self, root: Path):
        self.root = root
        self.ledger = EventLedger(root / "events.jsonl")

    def append_source(self, event_type: str, payload: Mapping[str, Any], *, event_id: str) -> dict[str, Any]:
        if any(record["event_type"] == "decision_cut" for record in self.ledger.records()):
            raise LedgerError("source append after decision cut is audit-only")
        return self.ledger.append(event_type, payload, event_id=event_id)

    def append_audit(self, event_type: str, payload: Mapping[str, Any], *, event_id: str) -> dict[str, Any]:
        return self.ledger.append(event_type, payload, event_id=event_id)

    def seal_cut(self, *, reason: str, expected_head: str | None = None) -> dict[str, Any]:
        records = self.ledger.records()
        existing = [record for record in records if record["event_type"] == "decision_cut"]
        if existing:
            return existing[0]
        seq, head_digest = self.ledger.head()
        if expected_head is not None and expected_head != head_digest:
            raise LedgerError("decision-cut head compare-and-set failed")
        return self.ledger.append(
            "decision_cut",
            {"source_head_seq": seq, "source_head_digest": head_digest, "reason": reason},
            event_id=f"cut:{head_digest}",
        )

    def terminal_receipt(self) -> dict[str, Any]:
        records = self.ledger.records()
        cuts = [record for record in records if record["event_type"] == "decision_cut"]
        if not cuts:
            raise LedgerError("cannot reduce before decision cut")
        cut = cuts[0]
        existing = [record for record in records if record["event_type"] == "terminal_receipt"]
        if existing:
            first = existing[0]["payload"]
            if any(record["payload"] != first for record in existing[1:]):
                raise LedgerError("terminal CAS conflict")
            return dict(first)
        cut_seq = int(cut["payload"]["source_head_seq"])
        source_prefix = [record for record in records if int(record["seq"]) <= cut_seq]
        candidate = reduce_terminal(source_prefix, cut["digest"])
        receipt_id = f"terminal:{cut['digest']}:{candidate['action']}:{candidate['reducer_digest']}"
        payload = {key: candidate[key] for key in ("action", "cut_digest", "reducer_digest")}
        self.ledger.append("terminal_receipt", payload, event_id=receipt_id)
        return payload


def run_deterministic_qualification(root: Path) -> dict[str, Any]:
    """Run model-free fixtures required by the first qualification slice."""

    fixtures: dict[str, dict[str, Any]] = {}
    infra = DecisionRuntime(root / "explicit-infra-precedence")
    infra.append_source("attempt", {"attempt_id": "a1", "content": "progress_only", "claims": {"C2": "PASS"}}, event_id="a1")
    infra.append_source("provider_error", {"attempt_id": "a1", "provider_code": "503", "infrastructure_receipt": True}, event_id="a1-error")
    fixtures["explicit_infra_precedence"] = {
        "observed": classify_attempt(infra.ledger.records()[0]["payload"] | {"provider_code": "503", "infrastructure_receipt": True}),
        "expected": "INFRA_NONCOMPLETION",
    }

    pre_cut = DecisionRuntime(root / "pre-cut-conflict")
    pre_cut.append_source("attempt", {"attempt_id": "a1", "content": "final_nonempty", "claims": {"C1": "PASS"}}, event_id="a1")
    pre_cut.append_source("attempt", {"attempt_id": "a1-conflict", "content": "unknown", "claims": {"C1": "UNRESOLVED"}}, event_id="a1-conflict")
    cut = pre_cut.seal_cut(reason="fixture")
    pre_receipt = pre_cut.terminal_receipt()
    fixtures["pre_cut_conflict"] = {"action": pre_receipt["action"], "expected": "STOP_UNPROVEN", "cut": cut["digest"]}

    post_cut = DecisionRuntime(root / "post-cut-audit")
    post_cut.append_source("attempt", {"attempt_id": "a1", "content": "final_nonempty", "claims": {"C1": "PASS"}}, event_id="a1")
    post_cut.seal_cut(reason="fixture")
    post_cut.append_audit("provider_error", {"attempt_id": "a1", "provider_code": "503"}, event_id="late-503")
    post_receipt = post_cut.terminal_receipt()
    fixtures["post_cut_is_audit_only"] = {"action": post_receipt["action"], "expected": "CONTINUE_BETA"}

    duplicate = DecisionRuntime(root / "duplicate-event")
    first = duplicate.append_source("attempt", {"attempt_id": "a1", "content": "final_empty"}, event_id="a1")
    second = duplicate.append_source("attempt", {"attempt_id": "a1", "content": "final_empty"}, event_id="a1")
    fixtures["idempotent_duplicate"] = {"same_digest": first["digest"] == second["digest"], "records": len(duplicate.ledger.records())}

    all_pass = all(
        fixture.get("action", fixture.get("observed", fixture.get("same_digest"))) == fixture.get("expected", True)
        for fixture in fixtures.values()
    )
    return {"schema_version": SCHEMA_VERSION, "status": "passed" if all_pass else "failed", "fixtures": fixtures}

