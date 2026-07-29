#!/usr/bin/env python3
"""Bind a Codex session and generate stable dispatcher hook configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from codex_telemetry_adapter import hook_command
from codex_telemetry_dispatcher import bind_and_register_session
from tplan_runtime import TplanError


def hook_config(mission_dir: Path, state_dir: Path) -> dict[str, Any]:
    hook = {
        "type": "command",
        "command": hook_command(mission_dir, state_dir),
        "timeout": 10,
    }
    return {
        "description": "Optional privacy-minimized TPlan Codex telemetry adapter.",
        "hooks": {
            "PreToolUse": [{"matcher": "*", "hooks": [hook]}],
            "PostToolUse": [{"matcher": "*", "hooks": [hook]}],
            "SubagentStart": [{"hooks": [hook]}],
            "SubagentStop": [{"hooks": [hook]}],
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bind a Codex session and generate optional TPlan telemetry hooks."
    )
    parser.add_argument("mission_dir")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--thread-id")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mission_dir = Path(args.mission_dir).resolve()
    state_dir = Path(args.state_dir).resolve()
    try:
        bind_and_register_session(
            mission_dir,
            state_dir,
            session_id=args.session_id,
            thread_id=args.thread_id,
            replace=args.replace,
            activation_required=True,
        )
        config = hook_config(mission_dir, state_dir)
    except (OSError, ValueError, TplanError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    rendered = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
