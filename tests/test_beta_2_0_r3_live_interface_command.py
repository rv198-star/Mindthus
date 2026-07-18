from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "beta/2.0.0-beta.2/runtime"
sys.path.insert(0, str(RUNTIME))
SPEC = importlib.util.spec_from_file_location("run_r3_live_interface_probe", RUNTIME / "run_r3_live_interface_probe.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_command_places_global_option_before_exec_and_binds_reasoning() -> None:
    auth = {"model": {"family": "gpt-5.6-sol", "reasoning_effort": "xhigh"}}
    command = MODULE.build_codex_command(auth, Path("/tmp/repo"), "PROBE")

    assert command[:4] == ["codex", "--ask-for-approval", "never", "exec"]
    assert "--no-alt-screen" not in command
    assert command[command.index("-m") + 1] == "gpt-5.6-sol"
    assert command[command.index("-c") + 1] == 'model_reasoning_effort="xhigh"'
    assert command[-1] == "PROBE"


def test_parser_check_replaces_prompt_with_help(monkeypatch, tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    class Result:
        returncode = 0
        stdout = "usage"
        stderr = ""

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return Result()

    monkeypatch.setattr(MODULE.subprocess, "run", fake_run)
    result = MODULE.validate_command_parser(["codex", "exec", "PROMPT"], tmp_path)

    assert observed["command"] == ["codex", "exec", "--help"]
    assert result["returncode"] == 0


def test_parse_codex_stdout_requires_final_and_terminal_usage() -> None:
    value = b"\n".join(
        [
            b'{"type":"thread.started","thread_id":"t1"}',
            b'{"type":"turn.started"}',
            b'{"type":"item.completed","item":{"type":"agent_message","text":"PROBE_OK"}}',
            b'{"type":"turn.completed","usage":{"input_tokens":12,"output_tokens":2}}',
        ]
    )
    parsed = MODULE.parse_codex_stdout(value)

    assert parsed["lifecycle_complete"] is True
    assert parsed["thread_ids"] == ["t1"]
    assert parsed["final_messages"] == ["PROBE_OK"]
    assert parsed["terminal_usage"] == {"input_tokens": 12, "output_tokens": 2}


def test_parse_codex_stdout_rejects_incomplete_or_invalid_jsonl() -> None:
    parsed = MODULE.parse_codex_stdout(b'{"type":"thread.started","thread_id":"t1"}\nnot-json\n')

    assert parsed["lifecycle_complete"] is False
    assert parsed["invalid_jsonl_lines"] == [2]
