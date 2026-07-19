#!/usr/bin/env python3
"""Redact bundled system-Skill bodies from the three invalid carrier traces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


EXPECTED = {
    "run-20260719-v1/r2/frame_whole/events.jsonl": "65f52ee347d73e2e9c8bf36a3f2c5fc79fa52c6cc2d9e1e8ba626c2fa9cda771",
    "run-20260719-v1-continuation/incumbent/frame_whole/events.jsonl": "eccdc6159ef1db01a9ca66b6cf5580bdfb0fb78ae007135d1aa0b13aa844e6f3",
    "run-20260719-v1-r1-frame/r1/frame_whole/events.jsonl": "93f0c17d3383edc90fd887b7b21a9d414b5f72710d49c32e7d74df041b96f7d1",
}
REDACTION = "[REDACTED: bundled system Skill body; command and lifecycle metadata retained]"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    evidence = Path(__file__).resolve().parent / "evidence"
    for relative, original_digest in EXPECTED.items():
        path = evidence / relative
        current = sha256(path)
        if current != original_digest:
            text = path.read_text(encoding="utf-8")
            if REDACTION in text:
                print(f"already sanitized: {relative}")
                continue
            raise SystemExit(f"unexpected source digest for {relative}: {current}")
        output: list[str] = []
        redactions = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "command_execution":
                command = str(item.get("command", ""))
                if "/skills/.system/" in command and item.get("aggregated_output"):
                    item["aggregated_output"] = REDACTION
                    redactions += 1
            output.append(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
        if redactions != 1:
            raise SystemExit(f"expected one completed system-Skill read in {relative}; got {redactions}")
        path.write_text("\n".join(output) + "\n", encoding="utf-8")
        print(f"sanitized: {relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
