"""Locate the shared Mindthus ``_runtime`` package in supported release layouts."""

from __future__ import annotations

import sys
from pathlib import Path


def activate_shared_runtime(anchor: str | Path = __file__) -> Path:
    """Add the directory that directly owns ``_runtime`` to ``sys.path``.

    Supported layouts:

    - repository or Claude plugin: ``<root>/skills/_runtime``;
    - Codex skills pack: ``<root>/skills/mindthus/_runtime``;
    - OpenCode skills pack: ``<root>/.opencode/skills/mindthus/_runtime``.
    """

    script_path = Path(anchor).resolve()
    package_root = script_path.parent.parent
    candidates = (
        package_root / "skills",
        package_root / "skills" / "mindthus",
        package_root / ".opencode" / "skills" / "mindthus",
        package_root,
    )
    for candidate in candidates:
        if (candidate / "_runtime" / "__init__.py").is_file():
            value = str(candidate)
            sys.path[:] = [entry for entry in sys.path if entry != value]
            sys.path.insert(0, value)
            return candidate
    raise ImportError(f"Cannot locate Mindthus _runtime from {script_path}")
