#!/usr/bin/env python3
"""CLI wrapper for the shared Whole Elephant Protocol audit validator."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills"))

from scripts.primitives.whole_elephant_validator import main


if __name__ == "__main__":
    raise SystemExit(main())
