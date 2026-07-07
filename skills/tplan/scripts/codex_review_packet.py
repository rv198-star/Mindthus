#!/usr/bin/env python3
"""Create Codex SubAgent / clean-CLI review packets for tplan role separation."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from tplan_runtime import build_decision_packet, build_mission_pulse, build_survey


SCHEMA_VERSION = "tplan.codex_adapter.v0.1"
ROLES = {"advise", "grade", "dream"}
ROLE_ORDER = ["advise", "grade", "dream"]
ORCHESTRATION_MODES = {"recommended", "strict"}
DEFAULT_TRIGGERS = {
    "advise": "before_continue",
    "grade": "before_freeze",
    "dream": "manual",
}
HOOKS = {
    "advise": "selection",
    "grade": "mission_review",
    "dream": "mission_review",
}
ROLE_LABELS = {
    "advise": "direction-checking",
    "grade": "acceptance-grading",
    "dream": "learning-candidate-review",
}
VERDICTS = {
    "advise": ["continue", "switch", "escalate", "stop", "needs_human"],
    "grade": ["pass", "fail", "insufficient_evidence", "needs_human"],
    "dream": ["record_candidate", "risk_context_candidate", "issue_candidate", "discard"],
}
QUESTIONS = {
    "advise": [
        "Is the current route still aligned with Mission alignment and the Mission objective?",
        "Is the next gate appropriate for the current risk and evidence state?",
        "Would continuing this path create weak evidence, authority drift, or review debt?",
        "What should the main agent inspect before applying any decision?",
    ],
    "grade": [
        "Which acceptance criteria are satisfied by inspectable evidence?",
        "Which claimed completions lack evidence links or rubric support?",
        "Is closure justified, blocked, or dependent on human authority?",
        "What is the smallest evidence gap that would change the closure decision?",
    ],
    "dream": [
        "What reusable lesson is visible without granting it acceptance authority?",
        "Should the lesson be a Mission Shared Context candidate, Shared Risk Context candidate, issue, or regression test?",
        "What evidence boundary prevents this lesson from becoming doctrine too early?",
        "What should the main agent verify before recording the lesson?",
    ],
}
SKIP_RULES = [
    "Skip reviewer dispatch for a low-risk lite Mission when direct evidence is obvious and review would not change action, evidence, risk handling, or closure.",
    "Skip dream review when no learning or memory candidate is being recorded.",
    "Skip advise review when route, continuation, and Mission alignment are already supported by fresh evidence and no switch/stop decision is pending.",
]


def _orchestration_roles(mode: str) -> tuple[list[str], list[str]]:
    if mode == "recommended":
        return ["grade"], ["advise", "dream"]
    if mode == "strict":
        return ["advise", "grade"], ["dream"]
    raise ValueError(f"unsupported orchestration mode: {mode}")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _compact_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _build_packet(mission_dir: Path, role: str, trigger: str, repo_root: Path) -> dict[str, Any]:
    survey = build_survey(mission_dir)
    pulse = build_mission_pulse(mission_dir, trigger=trigger)
    decision_context = build_decision_packet(mission_dir, HOOKS[role])
    return {
        "schema_version": SCHEMA_VERSION,
        "platform": "codex",
        "role": role,
        "role_surface": ROLE_LABELS[role],
        "mission_dir": str(mission_dir),
        "repo_root": str(repo_root),
        "adapter_boundary": {
            "candidate_findings_only": True,
            "read_only_reviewer": True,
            "must_not_mutate": [
                "files",
                "Mission state",
                "evidence",
                "task tree",
                "decisions",
                "memory",
                "external systems",
            ],
            "main_agent_owns": [
                "verification",
                "merge",
                "recording evidence",
                "Mission mutation",
                "final user-facing conclusion",
            ],
            "not_a_four_agent_runtime": True,
        },
        "carrier_options": {
            "subagent": "Spawn a read-only Codex explorer/reviewer with the generated prompt.",
            "clean_cli": "Run the generated ephemeral Codex CLI command when stronger context isolation is worth the cost.",
        },
        "review_contract": {
            "allowed_verdicts": VERDICTS[role],
            "required_output_fields": [
                "role",
                "verdict",
                "confidence",
                "findings",
                "evidence_refs",
                "authority_boundary",
                "state_mutation_attempted",
                "recommended_next_surface",
            ],
            "authority_boundary": "candidate_findings_only",
        },
        "review_questions": QUESTIONS[role],
        "survey": survey,
        "pulse": pulse,
        "decision_context": decision_context,
    }


def _prompt_for(packet: dict[str, Any], carrier: str) -> str:
    role = packet["role"]
    role_surface = packet["role_surface"]
    carrier_note = (
        "You are a read-only Codex SubAgent reviewer."
        if carrier == "subagent"
        else "You are running in an ephemeral Codex CLI review session."
    )
    return f"""# Codex tplan {role_surface} packet

{carrier_note}

You are reviewing a `tplan` Mission packet as the `{role}` surface. Your output is a
candidate finding for the main agent. You must not edit files, Mission state, evidence,
task tree, decisions, or external systems.

Do not execute the work yourself. Do not approve your own work. Do not write memory or
risk context directly. If you are reviewing learning, return candidate sinks only.

Return concise JSON with these fields:

```json
{{
  "role": "{role}",
  "verdict": "one of: {', '.join(packet['review_contract']['allowed_verdicts'])}",
  "confidence": 0,
  "findings": [
    {{
      "severity": "blocking|important|minor",
      "claim": "",
      "evidence_refs": [],
      "recommendation": ""
    }}
  ],
  "evidence_refs": [],
  "authority_boundary": "candidate_findings_only",
  "state_mutation_attempted": false,
  "recommended_next_surface": "",
  "learning_candidates": []
}}
```

Review questions:

{chr(10).join(f"- {question}" for question in packet["review_questions"])}

Review packet:

```json
{_compact_json(packet)}
```
"""


def _write_outputs(packet: dict[str, Any], output_dir: Path, repo_root: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    role = packet["role"]
    packet_path = output_dir / f"codex-{role}-review-packet.json"
    subagent_prompt_path = output_dir / f"codex-{role}-subagent-prompt.md"
    subagent_payload_path = output_dir / f"codex-{role}-subagent-dispatch.json"
    cli_prompt_path = output_dir / f"codex-{role}-cli-prompt.md"
    cli_command_path = output_dir / f"codex-{role}-cli-command.sh"
    cli_output_path = output_dir / f"codex-{role}-cli-review-output.md"

    subagent_prompt = _prompt_for(packet, "subagent")
    cli_prompt = _prompt_for(packet, "clean_cli")

    artifacts = {
        "packet_json": str(packet_path),
        "subagent_prompt": str(subagent_prompt_path),
        "subagent_dispatch": str(subagent_payload_path),
        "cli_prompt": str(cli_prompt_path),
        "cli_command": str(cli_command_path),
        "cli_output": str(cli_output_path),
    }
    packet_with_artifacts = dict(packet)
    packet_with_artifacts["artifacts"] = artifacts

    packet_path.write_text(_compact_json(packet_with_artifacts) + "\n", encoding="utf-8")
    subagent_prompt_path.write_text(subagent_prompt, encoding="utf-8")
    subagent_payload = {
        "tool": "multi_agent_v1.spawn_agent",
        "agent_type": "explorer",
        "fork_context": False,
        "message_file": str(subagent_prompt_path),
        "message": subagent_prompt,
        "authority_boundary": "candidate_findings_only",
    }
    subagent_payload_path.write_text(_compact_json(subagent_payload) + "\n", encoding="utf-8")
    cli_prompt_path.write_text(cli_prompt, encoding="utf-8")
    cli_command = "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "# read-only sandbox prevents model-generated shell commands from mutating the repo.",
            "# The Codex CLI still writes the final review output through -o outside the reviewer turn.",
            "codex -s read-only -a never exec --ephemeral "
            f"-C {shlex.quote(str(repo_root))} "
            f"-o {shlex.quote(str(cli_output_path))} "
            f"- < {shlex.quote(str(cli_prompt_path))}",
            "",
        ]
    )
    cli_command_path.write_text(cli_command, encoding="utf-8")
    return artifacts


def _build_orchestration_plan(
    *,
    mode: str,
    mission_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> dict[str, Any]:
    required_roles, conditional_roles = _orchestration_roles(mode)
    role_artifacts: dict[str, dict[str, str]] = {}
    roles: dict[str, dict[str, Any]] = {}
    for role in ROLE_ORDER:
        trigger = DEFAULT_TRIGGERS[role]
        packet = _build_packet(mission_dir, role, trigger, repo_root)
        artifacts = _write_outputs(packet, output_dir, repo_root)
        role_artifacts[role] = artifacts
        dispatch_requirement = "required" if role in required_roles else "conditional"
        roles[role] = {
            "dispatch_requirement": dispatch_requirement,
            "role_surface": ROLE_LABELS[role],
            "trigger": trigger,
            "activation_boundary": _role_activation_boundary(role, dispatch_requirement),
            "artifacts": artifacts,
        }

    plan = {
        "schema_version": SCHEMA_VERSION,
        "platform": "codex",
        "kind": "codex_orchestration",
        "orchestration_policy": "recommended_codex_tplan_path",
        "orchestration_mode": mode,
        "boundary": "Codex orchestration is not a mandatory four-agent runtime; reviewers are carriers that return candidate findings only.",
        "required_roles": required_roles,
        "conditional_roles": conditional_roles,
        "skip_rules": SKIP_RULES,
        "roles": roles,
        "main_agent_responsibilities": [
            "main_agent_execute_mission_work",
            "main_agent_verify_then_record",
            "main_agent_apply_tplan_decisions",
            "main_agent_write_final_user_conclusion",
        ],
    }
    plan_path = output_dir / "codex-orchestration-plan.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(_compact_json(plan) + "\n", encoding="utf-8")
    return {
        "plan": plan,
        "plan_path": str(plan_path),
        "role_artifacts": role_artifacts,
    }


def _role_activation_boundary(role: str, dispatch_requirement: str) -> str:
    if role == "grade":
        return (
            "Dispatch before closure, release, handoff, method change, authority-sensitive "
            "completion, or meaningful acceptance claim."
        )
    if role == "advise":
        prefix = "Dispatch" if dispatch_requirement == "required" else "Consider dispatching"
        return (
            f"{prefix} before route changes, same-path continuation under uncertainty, "
            "stop/switch decisions, repeated failure, or Mission alignment doubt."
        )
    if role == "dream":
        return (
            "Dispatch before recording reusable lessons, Mission Shared Context, Shared Risk "
            "Context, issue candidates, or regression candidates."
        )
    raise ValueError(f"unsupported role: {role}")


def _run_clean_cli(artifacts: dict[str, str], repo_root: Path, codex_bin: str) -> dict[str, Any]:
    prompt_path = Path(artifacts["cli_prompt"])
    output_path = Path(artifacts["cli_output"])
    stdout_path = output_path.with_suffix(".stdout.txt")
    stderr_path = output_path.with_suffix(".stderr.txt")
    command = [
        codex_bin,
        "-s",
        "read-only",
        "-a",
        "never",
        "exec",
        "--ephemeral",
        "-C",
        str(repo_root),
        "-o",
        str(output_path),
    ]
    result = subprocess.run(
        command,
        input=prompt_path.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
    )
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "output": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Codex role-separated review packet artifacts.")
    parser.add_argument("mission_dir")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--role", choices=sorted(ROLES))
    mode.add_argument("--orchestration-mode", choices=sorted(ORCHESTRATION_MODES))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--trigger", help="Mission Pulse trigger. Defaults by role.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--run-cli", action="store_true", help="Actually run the generated clean Codex CLI review.")
    parser.add_argument("--codex-bin", default="codex", help="Codex CLI binary used with --run-cli.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable manifest.")
    args = parser.parse_args()
    if args.orchestration_mode and args.run_cli:
        parser.error("--run-cli is only supported with --role; orchestration mode generates carrier artifacts")

    try:
        mission_dir = Path(args.mission_dir).resolve()
        output_dir = Path(args.output_dir).resolve()
        repo_root = Path(args.repo_root).resolve()
        if args.orchestration_mode:
            orchestration = _build_orchestration_plan(
                mode=args.orchestration_mode,
                mission_dir=mission_dir,
                output_dir=output_dir,
                repo_root=repo_root,
            )
            trigger = None
            artifacts = {"orchestration_plan": orchestration["plan_path"]}
            role_artifacts = orchestration["role_artifacts"]
            cli_run = None
        else:
            trigger = args.trigger or DEFAULT_TRIGGERS[args.role]
            packet = _build_packet(mission_dir, args.role, trigger, repo_root)
            artifacts = _write_outputs(packet, output_dir, repo_root)
            role_artifacts = None
            cli_run = _run_clean_cli(artifacts, repo_root, args.codex_bin) if args.run_cli else None
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.orchestration_mode:
        required_roles, conditional_roles = _orchestration_roles(args.orchestration_mode)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "platform": "codex",
            "kind": "codex_orchestration",
            "orchestration_mode": args.orchestration_mode,
            "required_roles": required_roles,
            "conditional_roles": conditional_roles,
            "skip_rules": SKIP_RULES,
            "artifacts": artifacts,
            "role_artifacts": role_artifacts,
            "cli_run": None,
            "script_result": "codex orchestration plan created; reviewer output remains candidate finding only",
        }
    else:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "platform": "codex",
            "kind": "single_role_packet",
            "role": args.role,
            "trigger": trigger,
            "artifacts": artifacts,
            "cli_run": cli_run,
            "script_result": "codex review packet created; reviewer output remains candidate finding only",
        }
    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        if args.orchestration_mode:
            print(f"codex_orchestration: mode={args.orchestration_mode}")
            print(f"required_roles: {','.join(manifest['required_roles'])}")
            print(f"conditional_roles: {','.join(manifest['conditional_roles'])}")
        else:
            print(f"codex_review_packet: role={args.role} trigger={trigger}")
        for label, path in artifacts.items():
            print(f"{label}: {path}")
        if cli_run is not None:
            print(f"cli_run_returncode: {cli_run['returncode']}")
            print(f"cli_run_output: {cli_run['output']}")
        print(manifest["script_result"])
    if cli_run is not None and cli_run["returncode"] != 0:
        return int(cli_run["returncode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
