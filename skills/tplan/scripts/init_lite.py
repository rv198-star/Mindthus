#!/usr/bin/env python3
"""Initialize a lightweight tplan Mission runtime.

This creates Mission state plus one active root Task. It does not materialize a
Step, and it does not decide semantic truth.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import (
    TplanError,
    attach_project_shared_context,
    build_mission,
    initialize_execution_trace,
    mission_paths,
    parse_acceptance_evidence,
    render_lite_runtime_state,
    render_mission_md,
    validate_mission,
    write_project_shared_context,
    write_json,
)


RUNTIME_FILES = ("mission", "narrative", "evidence", "trace", "logs", "archive", "reports")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a lite tplan Mission runtime.")
    parser.add_argument("--dir", required=True, help="Mission directory to create.")
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument(
        "--acceptance-evidence",
        action="append",
        default=[],
        help="Acceptance evidence as ID:description. Repeat for multiple items.",
    )
    parser.add_argument("--active-task-id", required=True)
    parser.add_argument("--active-task-title", required=True)
    parser.add_argument("--active-task-contribution", required=True)
    parser.add_argument("--latest-state", default="Not recorded yet.")
    parser.add_argument("--project-root", help="Project root used for .tplan/shared_contexts.")
    parser.add_argument("--source-context", action="append", default=[])
    parser.add_argument("--human-in-loop", type=int, default=0)
    parser.add_argument("--risk-tolerance", type=int, default=50)
    parser.add_argument("--resource-sufficiency", type=int, default=50)
    return parser.parse_args()


def refuse_existing_runtime(paths: dict[str, Path]) -> None:
    existing = [paths[name] for name in RUNTIME_FILES if paths[name].exists()]
    if existing:
        details = ", ".join(str(path) for path in existing)
        raise TplanError(f"mission runtime already exists: {details}")


def render_lite_mission_md(mission: dict[str, object], latest_state: str) -> str:
    return render_mission_md(mission) + "\n" + render_lite_runtime_state(mission, latest_state)


def main() -> int:
    args = parse_args()
    try:
        mission_dir = Path(args.dir)
        paths = mission_paths(mission_dir)
        refuse_existing_runtime(paths)

        acceptance_evidence = parse_acceptance_evidence(args.acceptance_evidence)
        task = {
            "id": args.active_task_id,
            "kind": "task",
            "title": args.active_task_title,
            "status": "active",
            "role": "success-critical",
            "mission_contribution": args.active_task_contribution,
            "acceptance_evidence": [item["id"] for item in acceptance_evidence],
            "evidence_links": [],
        }
        mission = build_mission(
            mission_id=args.mission_id,
            title=args.title,
            objective=args.objective,
            acceptance_evidence=acceptance_evidence,
            human_in_loop=args.human_in_loop,
            risk_tolerance=args.risk_tolerance,
            resource_sufficiency=args.resource_sufficiency,
            tasks=[task],
        )
        mission["active_task_id"] = args.active_task_id
        if args.project_root:
            attach_project_shared_context(
                mission,
                Path(args.project_root),
                mission_dir=mission_dir,
                source_contexts=[str(item) for item in args.source_context],
            )
        errors = validate_mission(mission)
        if errors:
            raise TplanError("; ".join(errors))

        paths["dir"].mkdir(parents=True, exist_ok=True)
        paths["logs"].mkdir(parents=True, exist_ok=True)
        paths["archive"].mkdir(parents=True, exist_ok=True)
        paths["reports"].mkdir(parents=True, exist_ok=True)
        write_json(paths["mission"], mission)
        paths["narrative"].write_text(
            render_lite_mission_md(mission, args.latest_state),
            encoding="utf-8",
        )
        paths["evidence"].write_text("", encoding="utf-8")
        initialize_execution_trace(mission_dir, mission)
        if args.project_root:
            write_project_shared_context(Path(args.project_root), mission)
        print(f"initialized_lite_mission: {mission_dir}")
        print("active_task_id: " + args.active_task_id)
        print("script_result: lite runtime files created; agentic Mission judgment is still required")
        return 0
    except (KeyError, OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
