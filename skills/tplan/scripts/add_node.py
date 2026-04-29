#!/usr/bin/env python3
"""Add a Task, SubTask, or Step node through runtime validation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tplan_runtime import TplanError, add_task_node


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add a tplan runtime node.")
    parser.add_argument("mission_dir")
    parser.add_argument("--id", required=True)
    parser.add_argument("--kind", required=True, choices=("task", "subtask", "step"))
    parser.add_argument("--title", required=True)
    parser.add_argument("--parent-id")
    parser.add_argument("--role")
    parser.add_argument("--status")
    parser.add_argument("--mission-contribution")
    parser.add_argument("--acceptance-evidence", action="append", default=[])
    parser.add_argument("--parent-contribution")
    parser.add_argument("--parent-acceptance")
    parser.add_argument("--mission-trace")
    parser.add_argument("--step-action")
    parser.add_argument("--done-condition")
    parser.add_argument("--evidence-link", action="append", default=[])
    return parser.parse_args()


def raw_node(args: argparse.Namespace) -> dict[str, object]:
    node: dict[str, object] = {
        "id": args.id,
        "kind": args.kind,
        "title": args.title,
        "evidence_links": args.evidence_link,
    }
    if args.parent_id is not None:
        node["parent_id"] = args.parent_id
    if args.role is not None:
        node["role"] = args.role
    if args.status is not None:
        node["status"] = args.status
    if args.mission_contribution is not None:
        node["mission_contribution"] = args.mission_contribution
    if args.acceptance_evidence:
        node["acceptance_evidence"] = args.acceptance_evidence
    if args.parent_contribution is not None:
        node["parent_contribution"] = args.parent_contribution
    if args.parent_acceptance is not None:
        node["parent_acceptance"] = args.parent_acceptance
    if args.mission_trace is not None:
        node["mission_trace"] = args.mission_trace
    if args.step_action is not None:
        node["step_action"] = args.step_action
    if args.done_condition is not None:
        node["done_condition"] = args.done_condition
    return node


def main() -> int:
    args = parse_args()
    try:
        node = add_task_node(Path(args.mission_dir), raw_node(args))
    except (OSError, TplanError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"added_node: {node['id']}")
    print("script_result: node added after runtime validation; semantic judgment remains agentic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
