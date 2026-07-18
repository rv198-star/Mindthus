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
