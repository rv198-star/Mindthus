"""Adapter-neutral JSON loading helpers shared by Mindthus scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def load_json(
    path: Path,
    *,
    error_factory: Callable[[str], BaseException] = SystemExit,
) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise error_factory(f"failed to read JSON at {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise error_factory(f"failed to decode JSON at {path} as UTF-8: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        location = f"line {exc.lineno} column {exc.colno}"
        raise error_factory(f"invalid JSON at {path}: {exc.msg} ({location})") from exc
