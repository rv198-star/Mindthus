#!/usr/bin/env python3
"""Generate Mission-scoped native-hook configuration for supported CLI hosts."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from interaction_host import PROFILES, profile_for
from tplan_runtime import TplanError, read_mission


SUPPORTED_PLATFORMS = tuple(PROFILES)


def _hook_command(platform: str, mission_dir: Path, state_dir: Path, *, turn_end: bool = False) -> str:
    adapter = Path(__file__).resolve().with_name("platform_interaction_hook.py")
    supervisor = adapter.with_name("hook_supervisor.py")
    command = " ".join(
        shlex.quote(item)
        for item in (
            sys.executable,
            str(supervisor),
            "--timeout",
            "5",
            "--",
            sys.executable,
            str(adapter),
            "--platform",
            platform,
            "--mission-dir",
            str(mission_dir),
            "--state-dir",
            str(state_dir),
        )
    )
    if turn_end:
        # Codex treats a non-zero Stop hook as a request to continue.  A crashed or
        # timed-out adapter must therefore end normally and leave recovery to the
        # orphan/lease path, never manufacture another guarded continuation.
        return (
            f'{command}; tplan_hook_status=$?; '
            "if [ \"$tplan_hook_status\" -ne 0 ]; then "
            "printf '{\"systemMessage\":\"TPlan turn-end hook failed safely; Mission remains locked for recovery.\"}\\n'; exit 0; fi"
        )
    return (
        f'{command}; tplan_hook_status=$?; '
        "if [ \"$tplan_hook_status\" -ne 0 ]; then "
        "printf 'TPlan hook supervisor failed (status %s)\\n' \"$tplan_hook_status\" >&2; exit 2; fi"
    )


def hook_config(platform: str, mission_dir: Path, *, state_dir: Path, experimental: bool = False) -> dict[str, Any]:
    try:
        profile = profile_for(platform)
    except ValueError as exc:
        raise TplanError(str(exc)) from exc
    if not profile.certified and not experimental:
        raise TplanError(
            f"{platform} has no certified real-host interaction profile; pass --experimental only for E2E validation"
        )
    resolved_state_dir = state_dir.resolve()
    if not resolved_state_dir.is_dir():
        raise TplanError("--state-dir must be a pre-created host-controlled directory")
    try:
        resolved_state_dir.relative_to(mission_dir.resolve())
    except ValueError:
        pass
    else:
        raise TplanError("--state-dir must be outside the Mission directory")
    command = _hook_command(platform, mission_dir, resolved_state_dir)
    turn_end_command = _hook_command(platform, mission_dir, resolved_state_dir, turn_end=True)
    timeout = 30_000 if platform == "gemini-cli" else 30
    hook = {"type": "command", "command": command, "timeout": timeout}
    message_hook = hook if platform != "gemini-cli" else {**hook, "description": "Protect the active TPlan path across mid-turn user messages."}
    before_matcher = ".*" if platform == "gemini-cli" else "*"
    hooks = {
        profile.message_event: [{"hooks": [message_hook]}],
        profile.before_tool_event: [{"matcher": before_matcher, "hooks": [hook]}],
        profile.turn_end_event: [{"hooks": [{**hook, "command": turn_end_command}]}],
    }
    if profile.session_start_event is not None:
        hooks[profile.session_start_event] = [{"hooks": [hook]}]
    return {
        "description": f"Mission-scoped TPlan interaction guard ({profile.profile_id}).",
        "hooks": hooks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a TPlan interaction-hook config snippet.")
    parser.add_argument("mission_dir")
    parser.add_argument("--platform", required=True, choices=SUPPORTED_PLATFORMS)
    parser.add_argument("--output")
    parser.add_argument(
        "--state-dir",
        required=True,
        help="Host-controlled state directory outside agent write authority.",
    )
    parser.add_argument(
        "--experimental",
        action="store_true",
        help="Generate an unverified profile only for a documented real-host E2E run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mission_dir = Path(args.mission_dir).resolve()
    try:
        read_mission(mission_dir)
        config = hook_config(
            args.platform,
            mission_dir,
            state_dir=Path(args.state_dir),
            experimental=args.experimental,
        )
    except (OSError, ValueError, TplanError) as exc:
        raise SystemExit(str(exc)) from exc
    rendered = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
