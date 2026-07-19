"""Locate Mindthus shared Python runtime across supported package layouts."""

from __future__ import annotations

import sys
from pathlib import Path


def runtime_import_root(anchor: str | Path = __file__) -> Path:
    """Return the nearest ancestor that directly owns ``_runtime``."""

    resolved = Path(anchor).resolve()
    for candidate in (resolved.parent, *resolved.parents):
        if (candidate / "_runtime" / "__init__.py").is_file():
            return candidate
    raise ImportError(f"Cannot locate Mindthus _runtime from {resolved}")


def activate_runtime(anchor: str | Path = __file__) -> Path:
    root = runtime_import_root(anchor)
    value = str(root)
    sys.path[:] = [entry for entry in sys.path if entry != value]
    sys.path.insert(0, value)
    return root
