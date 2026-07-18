#!/usr/bin/env python3
"""Replay and audit an existing R3 LIVE_INTERFACE artifact without model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from decision_reset_kernel import EventLedger, canonical_json, digest
from run_r3_live_interface_probe import parse_codex_stdout


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact.resolve()
    source_receipt = json.loads((root / "qualification-receipt.json").read_text(encoding="utf-8"))
    records = EventLedger(root / "events.jsonl").records()
    raw = (root / "raw-stream.bin").read_bytes()
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    offset = 0
    verified_chunks = 0
    for record in records:
        if record["event_type"] != "stream_chunk":
            continue
        payload = record["payload"]
        length = int(payload["byte_length"])
        chunk = raw[offset : offset + length]
        offset += length
        if len(chunk) != length or sha256_bytes(chunk) != payload["sha256"]:
            raise ValueError(f"raw chunk mismatch at ledger seq {record['seq']}")
        stream = str(payload["stream"])
        if stream not in streams:
            raise ValueError(f"unknown stream at ledger seq {record['seq']}: {stream}")
        streams[stream].extend(chunk)
        verified_chunks += 1
    if offset != len(raw):
        raise ValueError("raw file contains bytes not bound by stream_chunk events")
    lifecycle = parse_codex_stdout(bytes(streams["stdout"]))
    provider = [record["payload"] for record in records if record["event_type"] == "provider_terminal"][-1]
    stream_digests_match = (
        provider.get("stdout_sha256") == sha256_bytes(bytes(streams["stdout"]))
        and provider.get("stderr_sha256") == sha256_bytes(bytes(streams["stderr"]))
    )
    actual_raw_sha = sha256_bytes(raw)
    audit: dict[str, Any] = {
        "schema_version": "mindthus-beta2-r3-live-interface-audit-v0.1",
        "program_id": source_receipt.get("program_id"),
        "source_receipt_digest": source_receipt.get("receipt_digest"),
        "ledger_verified": True,
        "verified_chunks": verified_chunks,
        "raw_bytes": len(raw),
        "raw_file_sha256": actual_raw_sha,
        "source_receipt_raw_digest_matches": source_receipt.get("raw_stream_sha256") == actual_raw_sha,
        "provider_stream_digests_match": stream_digests_match,
        "client_lifecycle": lifecycle,
        "generator_calls": source_receipt.get("generator_calls"),
        "judge_calls": source_receipt.get("judge_calls"),
        "lifecycle_probe_status": "PASS" if lifecycle["lifecycle_complete"] and stream_digests_match else "FAIL",
        "full_live_interface_bundle_status": "PARTIAL",
        "unmet_full_bundle_items": [
            "accepted Judge schema was not authorized or sampled",
            "full enabled tool/event envelope and arm identity were not qualified by this lifecycle-only probe"
        ],
        "audit_disposition": "SOURCE_EVIDENCE_RECOVERED; ORIGINAL_TOP_LEVEL_RAW_DIGEST_DEFECT",
    }
    audit["audit_digest"] = digest(audit)
    (root / "qualification-audit.json").write_text(canonical_json(audit) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["lifecycle_probe_status"], "audit": str(root / "qualification-audit.json"), "digest": audit["audit_digest"]}, ensure_ascii=False))
    return 0 if audit["lifecycle_probe_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
