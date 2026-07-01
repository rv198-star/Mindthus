#!/usr/bin/env python3
"""Shared support helpers for the cinematic colossal realism profile."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


SCRIPT_BOUNDARY = "support_only_agentic_audit_required"
PROFILE = "cinematic-colossal-realism"
ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "resources"
FIELD_PATTERN = re.compile(r"【[^】]+】")


def load_resource(name: str) -> dict[str, Any]:
    path = RESOURCES / name
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(payload: dict[str, Any], returncode: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(returncode)


def extract_fields(text: str) -> list[str]:
    return FIELD_PATTERN.findall(text)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def boundary_payload(**extra: Any) -> dict[str, Any]:
    return {
        "profile": PROFILE,
        "script_boundary": SCRIPT_BOUNDARY,
        **extra,
    }


def main_error(message: str, returncode: int = 2) -> None:
    sys.stderr.write(message + "\n")
    raise SystemExit(returncode)
