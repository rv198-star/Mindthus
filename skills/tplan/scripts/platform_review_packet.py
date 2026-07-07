#!/usr/bin/env python3
"""Create Claude Code / OpenCode review carrier artifacts for tplan role separation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tplan_runtime import build_decision_packet, build_mission_pulse, build_survey


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
ROLE_AGENT_NAMES = {
    "advise": "tplan-advisor",
    "grade": "tplan-grader",
    "dream": "tplan-dreamer",
}
VERDICTS = {
    "advise": ["continue", "switch", "escalate", "stop", "needs_human"],
    "grade": ["pass", "fail", "insufficient_evidence", "needs_human"],
    "dream": ["record_candidate", "risk_context_candidate", "issue_candidate", "discard"],
}
QUESTIONS = {
    "advise": [
        "Is the current route still aligned with Mission alignment and objective?",
        "Is the next gate appropriate for current risk and evidence state?",
        "Would continuing create weak evidence, authority drift, or review debt?",
    ],
    "grade": [
        "Which acceptance criteria are satisfied by inspectable evidence?",
        "Which claimed completions lack evidence links or rubric support?",
        "Is closure justified, blocked, or dependent on human authority?",
    ],
    "dream": [
        "What reusable lesson is visible without granting it acceptance authority?",
        "Should the lesson be Mission Shared Context, Shared Risk Context, issue, or regression candidate?",
        "What evidence boundary prevents this lesson from becoming doctrine too early?",
    ],
}
SKIP_RULES = [
    "Skip reviewer dispatch for low-risk lite Mission cases when review would not change action, evidence, risk handling, or closure.",
    "Skip dream review when no learning or memory candidate is being recorded.",
    "Skip advise review when route, continuation, and Mission alignment are already supported by fresh evidence.",
]
PLATFORMS = {
    "claude-code": {
        "schema_version": "tplan.claude_code_adapter.v0.1",
        "artifact_prefix": "claude-code",
        "agent_dir": ".claude/agents",
        "docs": "https://code.claude.com/docs/en/sub-agents",
        "permission_model": "custom subagent with fresh context, tool allowlist, and permissionMode: plan",
    },
    "opencode": {
        "schema_version": "tplan.opencode_adapter.v0.1",
        "artifact_prefix": "opencode",
        "agent_dir": ".opencode/agents",
        "docs": "https://open-code.ai/en/docs/agents",
        "permission_model": "custom subagent with native read/search allowed, edit/task/bash denied",
    },
}


def _orchestration_roles(mode: str) -> tuple[list[str], list[str]]:
    if mode == "recommended":
        return ["grade"], ["advise", "dream"]
    if mode == "strict":
        return ["advise", "grade"], ["dream"]
    raise ValueError(f"unsupported orchestration mode: {mode}")


def _compact_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _build_packet(mission_dir: Path, role: str, trigger: str, repo_root: Path, platform: str) -> dict[str, Any]:
    cfg = PLATFORMS[platform]
    survey = build_survey(mission_dir)
    pulse = build_mission_pulse(mission_dir, trigger=trigger)
    decision_context = build_decision_packet(mission_dir, HOOKS[role])
    return {
        "schema_version": cfg["schema_version"],
        "platform": platform,
        "role": role,
        "role_surface": ROLE_LABELS[role],
        "agent_name": ROLE_AGENT_NAMES[role],
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
            "agent_file": f"Install generated markdown under {cfg['agent_dir']}/ when real platform isolation is desired.",
            "delegation_prompt": "Use the generated prompt to invoke the reviewer carrier from the main agent.",
            "permission_model": cfg["permission_model"],
            "official_docs": cfg["docs"],
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


def _reviewer_body(packet: dict[str, Any]) -> str:
    role = packet["role"]
    return f"""You are a tplan `{packet['role_surface']}` reviewer.

Your output is a candidate finding for the main agent. You must not edit files,
Mission state, evidence, task tree, decisions, memory, or external systems.

Do not execute Mission work. Do not approve your own work. Do not write memory or risk
context directly. If reviewing learning, return candidate sinks only.

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
"""


def _agent_markdown(packet: dict[str, Any], platform: str) -> str:
    name = packet["agent_name"]
    role = packet["role"]
    description = f"tplan {packet['role_surface']} reviewer for candidate-only Mission review"
    if platform == "claude-code":
        return f"""---
name: {name}
description: {description}. Use proactively only at tplan Mission review boundaries.
tools: Read, Glob, Grep
permissionMode: plan
---

{_reviewer_body(packet)}
"""
    if platform == "opencode":
        return f"""---
description: {description}. Use only at tplan Mission review boundaries.
mode: subagent
permission:
  read: allow
  glob: allow
  grep: allow
  list: allow
  edit: deny
  task: deny
  bash: deny
---

{_reviewer_body(packet)}
"""
    raise ValueError(f"unsupported platform: {platform}")


def _delegation_prompt(packet: dict[str, Any], platform: str) -> str:
    agent_name = packet["agent_name"]
    mention = f"@agent-{agent_name}" if platform == "claude-code" else f"@{agent_name}"
    return f"""# tplan {packet['platform']} delegation prompt

Invoke `{mention}` with this packet. The reviewer returns candidate findings only; the
main agent must verify, merge, record evidence, apply decisions, and write the final
user-facing conclusion.

Review questions:

{chr(10).join(f"- {question}" for question in packet["review_questions"])}

Review packet:

```json
{_compact_json(packet)}
```
"""


def _config_snippet(packet: dict[str, Any], platform: str) -> dict[str, Any]:
    name = packet["agent_name"]
    if platform == "claude-code":
        return {
            "$schema": "https://json.schemastore.org/claude-code-settings.json",
            "hooks": {
                "SubagentStart": [
                    {
                        "matcher": f"^{name}$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": f"echo 'tplan reviewer {name} started' >&2",
                            }
                        ],
                    }
                ],
                "SubagentStop": [
                    {
                        "matcher": f"^{name}$",
                        "hooks": [
                            {
                                "type": "command",
                                "command": f"echo 'tplan reviewer {name} stopped; main agent must verify candidate findings' >&2",
                            }
                        ],
                    }
                ],
            },
        }
    if platform == "opencode":
        return {
            "$schema": "https://opencode.ai/config.json",
            "agent": {
                name: {
                    "description": f"tplan {packet['role_surface']} reviewer; candidate findings only",
                    "mode": "subagent",
                    "permission": {
                        "read": "allow",
                        "glob": "allow",
                        "grep": "allow",
                        "list": "allow",
                        "edit": "deny",
                        "task": "deny",
                        "bash": "deny",
                    },
                }
            },
        }
    raise ValueError(f"unsupported platform: {platform}")


def _install_notes(packet: dict[str, Any], platform: str) -> str:
    cfg = PLATFORMS[platform]
    agent_file = f"{cfg['agent_dir']}/{packet['agent_name']}.md"
    return f"""# {platform} tplan reviewer install note

Copy the generated agent markdown to `{agent_file}` only when this platform adapter is
worth the extra isolation cost.

Boundary:

- Reviewer output is candidate finding only.
- Main agent still verifies, records evidence, applies decisions, and writes the final answer.
- Do not use this as a mandatory four-agent runtime.
- Do not claim benchmark-level improvement from this adapter without evaluation.

Official capability reference: {cfg['docs']}
"""


def _write_outputs(packet: dict[str, Any], output_dir: Path, platform: str) -> dict[str, str]:
    cfg = PLATFORMS[platform]
    output_dir.mkdir(parents=True, exist_ok=True)
    role = packet["role"]
    prefix = cfg["artifact_prefix"]
    packet_path = output_dir / f"{prefix}-{role}-review-packet.json"
    agent_path = output_dir / f"{prefix}-{role}-reviewer-agent.md"
    prompt_path = output_dir / f"{prefix}-{role}-delegation-prompt.md"
    config_path = output_dir / f"{prefix}-{role}-config-snippet.json"
    notes_path = output_dir / f"{prefix}-{role}-install-notes.md"

    artifacts = {
        "packet_json": str(packet_path),
        "reviewer_agent": str(agent_path),
        "delegation_prompt": str(prompt_path),
        "config_snippet": str(config_path),
        "install_notes": str(notes_path),
    }
    packet_with_artifacts = dict(packet)
    packet_with_artifacts["artifacts"] = artifacts
    packet_path.write_text(_compact_json(packet_with_artifacts) + "\n", encoding="utf-8")
    agent_path.write_text(_agent_markdown(packet, platform), encoding="utf-8")
    prompt_path.write_text(_delegation_prompt(packet, platform), encoding="utf-8")
    config_path.write_text(_compact_json(_config_snippet(packet, platform)) + "\n", encoding="utf-8")
    notes_path.write_text(_install_notes(packet, platform), encoding="utf-8")
    return artifacts


def _role_activation_boundary(role: str, dispatch_requirement: str) -> str:
    if role == "grade":
        return "Dispatch before closure, release, handoff, method change, or meaningful acceptance claim."
    if role == "advise":
        prefix = "Dispatch" if dispatch_requirement == "required" else "Consider dispatching"
        return f"{prefix} before route changes, same-path continuation under uncertainty, or Mission alignment doubt."
    if role == "dream":
        return "Dispatch before recording reusable lessons, Mission Shared Context, Shared Risk Context, issue, or regression candidates."
    raise ValueError(f"unsupported role: {role}")


def _build_orchestration_plan(mode: str, mission_dir: Path, output_dir: Path, repo_root: Path, platform: str) -> dict[str, Any]:
    cfg = PLATFORMS[platform]
    required_roles, conditional_roles = _orchestration_roles(mode)
    role_artifacts: dict[str, dict[str, str]] = {}
    roles: dict[str, dict[str, Any]] = {}
    for role in ROLE_ORDER:
        packet = _build_packet(mission_dir, role, DEFAULT_TRIGGERS[role], repo_root, platform)
        artifacts = _write_outputs(packet, output_dir, platform)
        role_artifacts[role] = artifacts
        dispatch_requirement = "required" if role in required_roles else "conditional"
        roles[role] = {
            "dispatch_requirement": dispatch_requirement,
            "role_surface": ROLE_LABELS[role],
            "trigger": DEFAULT_TRIGGERS[role],
            "activation_boundary": _role_activation_boundary(role, dispatch_requirement),
            "artifacts": artifacts,
        }

    plan = {
        "schema_version": cfg["schema_version"],
        "platform": platform,
        "kind": f"{platform}_orchestration",
        "orchestration_policy": f"recommended_{platform}_tplan_path",
        "orchestration_mode": mode,
        "boundary": f"{platform} orchestration is not a mandatory four-agent runtime; reviewers are carriers that return candidate findings only.",
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
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_path = output_dir / f"{cfg['artifact_prefix']}-orchestration-plan.json"
    plan_path.write_text(_compact_json(plan) + "\n", encoding="utf-8")
    return {
        "plan": plan,
        "plan_path": str(plan_path),
        "role_artifacts": role_artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create platform role-separated review carrier artifacts.")
    parser.add_argument("mission_dir")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--role", choices=sorted(ROLES))
    mode.add_argument("--orchestration-mode", choices=sorted(ORCHESTRATION_MODES))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--trigger", help="Mission Pulse trigger. Defaults by role.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json", action="store_true", help="Print machine-readable manifest.")
    args = parser.parse_args()

    try:
        mission_dir = Path(args.mission_dir).resolve()
        output_dir = Path(args.output_dir).resolve()
        repo_root = Path(args.repo_root).resolve()
        if args.orchestration_mode:
            orchestration = _build_orchestration_plan(
                args.orchestration_mode,
                mission_dir,
                output_dir,
                repo_root,
                args.platform,
            )
            required_roles, conditional_roles = _orchestration_roles(args.orchestration_mode)
            manifest = {
                "schema_version": PLATFORMS[args.platform]["schema_version"],
                "platform": args.platform,
                "kind": f"{args.platform}_orchestration",
                "orchestration_mode": args.orchestration_mode,
                "required_roles": required_roles,
                "conditional_roles": conditional_roles,
                "skip_rules": SKIP_RULES,
                "artifacts": {"orchestration_plan": orchestration["plan_path"]},
                "role_artifacts": orchestration["role_artifacts"],
                "script_result": "generated_platform_carrier_artifacts_only",
            }
        else:
            role = args.role
            trigger = args.trigger or DEFAULT_TRIGGERS[role]
            packet = _build_packet(mission_dir, role, trigger, repo_root, args.platform)
            artifacts = _write_outputs(packet, output_dir, args.platform)
            manifest = {
                "schema_version": PLATFORMS[args.platform]["schema_version"],
                "platform": args.platform,
                "role": role,
                "trigger": trigger,
                "artifacts": artifacts,
                "script_result": "generated_platform_carrier_artifacts_only",
            }
        if args.json:
            print(_compact_json(manifest))
        else:
            print(f"Created {args.platform} tplan review carrier artifacts in {output_dir}")
        return 0
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
