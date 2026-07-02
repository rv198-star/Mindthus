#!/usr/bin/env python3
"""Mindthus CLI: Unified runtime/workflow/evidence surface.

WAE Boundary:
- Workflow & Evidence: CLI validates shape, references, and logs.
- Agentic Judgment: Should remain in skills / agent reasoning / human review.
  CLI does not decide semantic truth.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

COMMAND_MAP = {
    "install": "scripts/install-skills.sh",
    "router-ab": "scripts/router-wakeup-ab.py",
    "primitives": {
        "check": "scripts/primitives/check.py",
    },
    "pack": {
        "build": "scripts/build-release-pack.py",
    },
    "fidelity": {
        "judge": "scripts/run-fidelity-judge.py",
        "log": "scripts/log-fidelity-usage.py",
    },
    "tplan": {
        "init": "skills/tplan/scripts/init_mission.py",
        "init-lite": "skills/tplan/scripts/init_lite.py",
        "preflight": "skills/tplan/scripts/preflight_mission.py",
        "check": "skills/tplan/scripts/check_mission.py",
        "checkpoint": "skills/tplan/scripts/checkpoint.py",
        "pulse": "skills/tplan/scripts/mission_pulse.py",
        "survey": "skills/tplan/scripts/survey.py",
        "evidence": "skills/tplan/scripts/record_evidence.py",
        "risk": "skills/tplan/scripts/record_risk_context.py",
        "stop-report": "skills/tplan/scripts/stop_report.py",
        "decision-packet": "skills/tplan/scripts/make_decision_packet.py",
        "add-node": "skills/tplan/scripts/add_node.py",
        "apply-decision": "skills/tplan/scripts/apply_decision.py",
        "transition-task": "skills/tplan/scripts/transition_task.py",
        "record-step-log": "skills/tplan/scripts/record_step_log.py",
        "render-user-update": "skills/tplan/scripts/render_user_update.py",
        "archive-task-logs": "skills/tplan/scripts/archive_task_logs.py",
    }
}


def print_main_help() -> None:
    help_text = """Mindthus CLI: Unified runtime/workflow/evidence surface.

WAE Boundary:
- Workflow & Evidence: CLI validates shape, references, and logs.
- Agentic Judgment: Should remain in skills / agent reasoning / human review.
  CLI does not decide semantic truth.

Usage:
  mindthus <command> [<subcommand>] [options]

Commands:
  install                      Install Mindthus skills
  doctor                       Run environment diagnostics
  router-ab                    Wake-up analyzer & primitive checks
  primitives check             Verify primitive check constraints
  pack build                   Build platform-specific release packs
  fidelity judge               Run fidelity evaluation judges
  fidelity log                 Log fidelity usage events

  tplan <subcommand>           TPlan Mission runtime operations
    init                       Initialize a tplan Mission directory
    init-lite                  Initialize a lightweight tplan Mission
    preflight                  Preflight Mission identity & shared context
    check                      Validate TPlan Mission runtime state
    checkpoint                 Commit evidence checkpoint
    pulse                      Create a health assessment pulse
    survey                     Survey tasks status & evidence
    evidence                   Record task evidence
    risk                       Record shared risk signal
    stop-report                Generate mission stop report
    decision-packet            Create decision packet
    add-node                   Add a node to task tree
    apply-decision             Apply a decision packet to mission state
    transition-task            Transition a task status
    record-step-log            Record a step log entry
    render-user-update         Render user-facing progress updates
    archive-task-logs          Archive completed task logs

Run 'mindthus <command> --help' or 'mindthus <command> <subcommand> --help' for details on options.
"""
    print(help_text)


def print_tplan_help() -> None:
    help_text = """Usage: mindthus tplan <subcommand> [options]

TPlan Mission runtime operations.

Subcommands:
    init                       Initialize a tplan Mission directory
    init-lite                  Initialize a lightweight tplan Mission
    preflight                  Preflight Mission identity & shared context
    check                      Validate TPlan Mission runtime state
    checkpoint                 Commit evidence checkpoint
    pulse                      Create a health assessment pulse
    survey                     Survey tasks status & evidence
    evidence                   Record task evidence
    risk                       Record shared risk signal
    stop-report                Generate mission stop report
    decision-packet            Create decision packet
    add-node                   Add a node to task tree
    apply-decision             Apply a decision packet to mission state
    transition-task            Transition a task status
    record-step-log            Record a step log entry
    render-user-update         Render user-facing progress updates
    archive-task-logs          Archive completed task logs

Run 'mindthus tplan <subcommand> --help' for details on options.
"""
    print(help_text)


def run_doctor() -> int:
    print("Running Mindthus environment diagnostics...")
    errors = []
    
    # 1. Check Python version
    py_ver = sys.version_info
    print(f"- Python version: {py_ver.major}.{py_ver.minor}.{py_ver.micro} ... OK")
    
    # 2. Check root directory structures
    for folder in ["skills", "scripts"]:
        path = ROOT_DIR / folder
        if path.is_dir():
            print(f"- Directory '{folder}' found at {path} ... OK")
        else:
            errors.append(f"Directory '{folder}' not found at {path}")
            
    # 3. Check for git repository or release package mode
    if (ROOT_DIR / ".git").is_dir():
         print("- Git repository detected ... OK")
    else:
         print("- No local .git folder detected (release pack mode)")

    if errors:
        print("\nDiagnostics: FAILED")
        for err in errors:
            print(f"  [ERROR] {err}")
        return 1
    
    print("\nDiagnostics: OK")
    return 0


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print_main_help()
        sys.exit(0)
        
    cmd = args[0]
    if cmd == "doctor":
        sys.exit(run_doctor())
        
    if cmd not in COMMAND_MAP:
        print(f"Error: unknown command '{cmd}'", file=sys.stderr)
        print_main_help()
        sys.exit(1)
        
    mapping = COMMAND_MAP[cmd]
    if isinstance(mapping, dict):
        if len(args) < 2 or args[1] in ("-h", "--help", "help"):
            if cmd == "tplan":
                print_tplan_help()
            else:
                print(f"Usage: mindthus {cmd} <subcommand> [options]")
                print(f"Subcommands: {', '.join(mapping.keys())}")
            sys.exit(0)
            
        subcmd = args[1]
        if subcmd not in mapping:
            print(f"Error: unknown subcommand '{subcmd}' for command '{cmd}'", file=sys.stderr)
            sys.exit(1)
            
        target_script = mapping[subcmd]
        remaining_args = args[2:]
    else:
        target_script = mapping
        remaining_args = args[1:]
        
    script_path = ROOT_DIR / target_script
    if not script_path.exists():
        print(f"Error: target script '{target_script}' not found at {script_path}", file=sys.stderr)
        sys.exit(1)
        
    if script_path.suffix == ".sh":
        cmd_to_run = ["bash", str(script_path)] + remaining_args
    else:
        cmd_to_run = [sys.executable, str(script_path)] + remaining_args
        
    res = subprocess.run(cmd_to_run)
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
