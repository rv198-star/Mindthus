#!/usr/bin/env python3
"""Create a no-model R3 capability/preflight receipt.

This command never starts a Codex turn. It validates the local kernel fixtures and
records the current CLI/plugin surface so a later trusted qualification authorization
can bind exact digests and choose STRICT_BOUNDED or TAIL_ACCEPTED explicitly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from decision_reset_kernel import canonical_json, digest, run_deterministic_qualification


def probe(command: list[str], cwd: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=20)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--design", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    fixture = run_deterministic_qualification(args.out / "deterministic-fault")
    probes = [probe(["codex", "--version"], args.repo_root), probe(["codex", "--help"], args.repo_root)]
    try:
        probes.append(probe(["codex", "plugin", "list", "--json"], args.repo_root))
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        probes.append({"command": ["codex", "plugin", "list", "--json"], "error": type(exc).__name__})
    receipt = {
        "schema_version": "mindthus-beta2-r3-preflight-v0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "program_status": "READY_FOR_QUALIFICATION_AUTHORIZATION",
        "semantic_calls": 0,
        "design_sha256": hashlib.sha256(args.design.read_bytes()).hexdigest(),
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "bundles": {
            "DETERMINISTIC_FAULT": {"status": fixture["status"], "receipt": fixture},
            "RECOVERY_AUTHORITY": {"status": "PARTIAL", "note": "Kernel cut/terminal recovery is covered by deterministic fixtures; crash injection remains implementation qualification."},
            "INTEGRITY": {"status": "PARTIAL", "note": "This preflight records local surface only; native arm isolation is not yet qualified."},
            "LIVE_INTERFACE": {"status": "NOT_RUN", "reason": "qualification authorization absent"},
            "JUDGE_CALIBRATION": {"status": "NOT_RUN", "reason": "qualification authorization absent"},
        },
        "authority": {
            "strict_bounded": False,
            "tail_accepted": False,
            "reason": "No trusted qualification receipt has selected an authority mode.",
        },
        "probes": probes,
    }
    receipt["receipt_digest"] = digest(receipt)
    (args.out / "preflight-receipt.json").write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["program_status"], "receipt": str(args.out / "preflight-receipt.json"), "digest": receipt["receipt_digest"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
