---
name: tplan
description: Use when a Mission needs a script-driven task runtime, task tree state, decision hooks, human-in-loop authority, or Mission-relative addition, subtraction, selection, closure, and evidence tracking.
---

# tplan

`tplan` is a Mission-oriented project manager and control plane.

Use it when work needs to stay attached to a stable Mission, avoid task-list drift,
route semantic decisions to Mindthus skills, and preserve task state in a resumable
runtime.

## Core Boundary

`tplan` owns runtime state, order, authority, validation, and decision hook contracts.

Scripts must not decide semantic truth. They may validate shape, state legality, parent
links, evidence references, and human-in-loop authority.

Semantic judgment is delegated:

- `3l5s`: problem definition, decomposition, loopback
- `sela`: subtraction and Mission-level ROI pressure
- `edsp`: fuzzy structural choices
- `wae`: control boundaries, evidence bridges, and log/evidence separation
- `tvg`: artifact depth audit

## Startup Policy

Mission startup uses three numeric inputs:

- `human_in_loop`: `0` autonomous, `100` advisory; mixed modes are reserved.
- `risk_tolerance`: `0-33` low, `34-66` normal, `67-100` high.
- `resource_sufficiency`: `0-33` poor, `34-66` normal, `67-100` rich.

Default `human_in_loop` is `0`.

## Runtime Loop

1. Initialize Mission files with `scripts/init_mission.py`.
2. Use `3l5s` to propose success-critical Task nodes.
3. Add Task, SubTask, and Step nodes through `scripts/add_node.py`; do not hand-edit
   `mission.json` for structure changes.
4. Validate the tree with `scripts/check_mission.py`.
5. Record task-local step logs with `scripts/record_step_log.py` while executing.
6. Record only acceptance, state-change, blocker, feedback, or decision evidence with
   `scripts/record_evidence.py`.
7. Archive completed task logs with `scripts/archive_task_logs.py` and promote only the
   summary or key findings to evidence when they support a claim.
8. Survey state with `scripts/survey.py`.
9. Generate a decision packet with `scripts/make_decision_packet.py`.
10. Run the parent-alignment or Mission Review Gate for the decision weight.
11. Invoke the routed Mindthus skill named by the decision hook.
12. Ensure the hook output states the required alignment before mutation.
13. Apply or record the decision with `scripts/apply_decision.py`.

## Alignment Gate

Task alignment is hierarchical by default:

- Task nodes are strongly responsible to the Mission.
- SubTask nodes are strongly responsible to their parent Task.
- Step nodes are execution leaves responsible to their parent Task or SubTask.
- SubTasks and Steps carry a lightweight `mission_trace` through the parent chain, but do not
  repeat a full Mission justification during ordinary execution.

Mission is not counted as a task level. Runtime `v0.1` supports:

- `task`: level 1 control node, Mission-facing.
- `subtask`: level 2 control node, Task-facing.
- `step`: level 2 or 3 execution leaf.

Simple work may use `Mission -> Task -> Step`. Complex work may use
`Mission -> Task -> SubTask -> Step`. Step never has children. If a Step needs
meaningful decomposition, it should raise a split signal and its parent control node
should replace or upgrade it into a SubTask.

Future expansion may add deeper Task/SubTask control layers, but Step remains the
stable execution leaf.

## Logs, Evidence, And Summary

Evidence is not a process log.

- `logs/`: step-local records used while doing work. They are allowed to be noisy and
  should stay below the active execution boundary.
- `evidence.jsonl`: acceptance, state-change, blocker, feedback, decision, or key
  finding records that constrain claims.
- `archive/`: compressed task history. When a task or milestone closes, archive its
  logs and keep a summary plus only the evidence needed by the parent.

Decision packets should consume evidence and recent blockers, not raw step logs unless
a specific investigation needs them.

Use a lightweight gate for ordinary SubTask/Step decisions:

- `parent_alignment`: how the recommendation advances the parent task.
- `mission_trace`: the parent-chain path back to Mission acceptance evidence.

Use `mission_alignment` and, for high-impact decisions, a full `mission_review` when
the decision can materially affect Mission convergence:

- adding or removing a `success-critical` task
- pausing, pruning, abandoning, or superseding a `success-critical` task
- switching the active task
- closing the Mission
- making subtraction decisions after resource pressure changes
- looping back because feedback challenges the current problem definition
- expanding the same supporting or exploratory branch more than once

The full review must identify the current Mission objective, remaining acceptance gap,
task contribution, Mission ROI effect, and risk of not taking the decision. This is a
judgment prompt, not proof that the judgment is correct.

## Resource Files

- `resources/schema.md`: mission files, task fields, decision packet, hook output.
- `resources/lifecycle.md`: Mission completion, closure, task states, transitions.
- `resources/policy.md`: risk/resource policy and human-in-loop authority.
- `resources/hooks.md`: decision hook triggers, routed skills, input/output contract.

## Runtime Scripts

Runtime scripts are added incrementally by implementation tasks. Until those scripts
exist, treat the script names in the Runtime Loop as planned interfaces rather than
executable commands.

Script output validates bookkeeping only. Agentic judgment remains required.
