"""Do not infer lifecycle semantics from an event name shared by two products."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HostProfile:
    platform: str
    profile_id: str
    message_event: str
    before_tool_event: str
    turn_end_event: str
    session_start_event: str | None
    read_only_tools: frozenset[str]
    safe_control_tools: frozenset[str]
    native_turn_id: bool
    stable_message_identity: bool = False
    release_strategy: str = "first_owned_end"
    resume_strategy: str = "none"
    certified: bool = False


_SAFE_CONTROL_TOOLS = frozenset(
    {
        "mcp__tplan_guard__inspect",
        "mcp__tplan_guard__await_proposal",
        "mcp__tplan_guard__stop_fixed",
    }
)


PROFILES = {
    "codex-desktop": HostProfile(
        platform="codex-desktop",
        profile_id="codex-desktop@v0.2-unverified",
        message_event="UserPromptSubmit",
        before_tool_event="PreToolUse",
        turn_end_event="Stop",
        session_start_event="SessionStart",
        read_only_tools=frozenset({"view_image"}),
        safe_control_tools=_SAFE_CONTROL_TOOLS,
        native_turn_id=True,
        stable_message_identity=False,
    ),
    "codex-cli": HostProfile(
        platform="codex-cli",
        profile_id="codex-cli@v0.2-unverified",
        message_event="UserPromptSubmit",
        before_tool_event="PreToolUse",
        turn_end_event="Stop",
        session_start_event="SessionStart",
        read_only_tools=frozenset({"view_image"}),
        safe_control_tools=_SAFE_CONTROL_TOOLS,
        native_turn_id=True,
        stable_message_identity=False,
    ),
    "claude-code": HostProfile(
        platform="claude-code",
        profile_id="claude-code@v0.2-unverified",
        message_event="UserPromptSubmit",
        before_tool_event="PreToolUse",
        turn_end_event="Stop",
        session_start_event=None,
        read_only_tools=frozenset({"Read", "Glob", "Grep", "WebFetch", "WebSearch"}),
        safe_control_tools=_SAFE_CONTROL_TOOLS,
        native_turn_id=False,
        stable_message_identity=False,
    ),
    "gemini-cli": HostProfile(
        platform="gemini-cli",
        profile_id="gemini-cli@v0.2-unverified",
        message_event="BeforeAgent",
        before_tool_event="BeforeTool",
        turn_end_event="AfterAgent",
        session_start_event=None,
        read_only_tools=frozenset({"read_file", "read_many_files", "list_directory", "search_file_content", "glob"}),
        safe_control_tools=_SAFE_CONTROL_TOOLS,
        native_turn_id=False,
        stable_message_identity=False,
    ),
}


def profile_for(platform: str) -> HostProfile:
    try:
        return PROFILES[platform]
    except KeyError as exc:
        raise ValueError(f"unsupported interaction hook platform: {platform}") from exc
