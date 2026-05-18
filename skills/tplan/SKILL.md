---
name: tplan
description: Use when a Mission needs a script-driven task runtime, task tree state, decision hooks, human-in-loop authority, or Mission-relative addition, subtraction, selection, closure, and evidence tracking.
---

# tplan

## Core Claim / 核心判断

`tplan` is a Mission-oriented project manager and control plane.

Use it when work needs to stay attached to a stable Mission, avoid task-list drift,
route semantic decisions to Mindthus skills, and preserve task state in a resumable
runtime.

### Core Boundary

`tplan` owns runtime state, order, authority, validation, and decision hook contracts.

Scripts must not decide semantic truth. They may validate shape, state legality, parent
links, evidence references, and human-in-loop authority.

Semantic judgment is delegated:

- `3l5s`: problem definition, decomposition, loopback
- `sela`: subtraction and Mission-level ROI pressure
- `edsp`: fuzzy structural choices
- `wae`: control boundaries, evidence bridges, and log/evidence separation
- `tvg`: artifact depth audit

## Mainline / 主路径

### Startup Policy

Mission startup uses three numeric inputs:

- `human_in_loop`: `0` autonomous, `100` advisory; mixed modes are reserved.
- `risk_tolerance`: `0-33` low, `34-66` normal, `67-100` high.
- `resource_sufficiency`: `0-33` poor, `34-66` normal, `67-100` rich.

Default `human_in_loop` is `0`.

### Runtime Loop

1. Initialize Mission files with `scripts/init_mission.py`.
2. Use `3l5s` to propose success-critical Task nodes.
3. Add Task, SubTask, and Step nodes through `scripts/add_node.py`; do not hand-edit
   `mission.json` for structure changes.
4. Validate the tree with `scripts/check_mission.py`.
5. Record task-local step logs with `scripts/record_step_log.py` while executing.
6. Record only acceptance, state-change, blocker, feedback, or decision evidence with
   `scripts/record_evidence.py`.
7. If execution cannot safely continue, write a concise Chinese stop report with
   `scripts/stop_report.py` and request human intervention.
8. Archive completed task logs with `scripts/archive_task_logs.py` and promote only the
   summary or key findings to evidence when they support a claim.
9. Survey state with `scripts/survey.py`.
10. Generate a decision packet with `scripts/make_decision_packet.py`.
11. Run the parent-alignment or Mission Review Gate for the decision weight.
12. Invoke the routed Mindthus skill named by the decision hook.
13. Ensure the hook output states the required alignment before mutation.
14. Apply or record the decision with `scripts/apply_decision.py`.

## Guardrails / 从属补漏

### Anti-Spiral Gate

Long-running Missions should activate Anti-Spiral Self-Audit when observable traces
suggest local repair may be replacing Mission progress: repeated third touches of the
same object, user feedback that the result worsened or remains insufficient, additive
layering, or weak evidence delta on same-path continuation.

This gate is not a separate skill. It is a runtime brake that can route back to `3l5s`
for problem loopback, `wae` for control-boundary repair, or subtraction/rollback inside
the active Mission. Full text lives in `docs/methodologies/anti-spiral-self-audit.md`.

### Alignment Gate

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

### Logs, Evidence, And Summary

Evidence is not a process log.

- `logs/`: step-local records used while doing work. They are allowed to be noisy and
  should stay below the active execution boundary.
- `evidence.jsonl`: acceptance, state-change, blocker, feedback, decision, or key
  finding records that constrain claims.
- `archive/`: compressed task history. When a task or milestone closes, archive its
  logs and keep a summary plus only the evidence needed by the parent.

Decision packets should consume evidence and recent blockers, not raw step logs unless
a specific investigation needs them.

### Graceful Stop

tplan should stop cleanly when continuing would require inventing missing intent,
authority, acceptance criteria, or product judgment. A stop is not a generic failure:
it is a handoff to a human with the smallest useful context.

Default user-facing stop reports are Chinese:

```text
停止报告

当前目标：
...

已尝试：
1. ...
2. ...
3. ...

阻碍：
...

为何不能安全继续：
...

需要人类提供：
...

恢复条件：
...
```

Use `scripts/stop_report.py` to record the report. It writes a `stop_report` evidence
event, marks the current node `blocked`, sets the Mission to `requires_human`, and
keeps the blocked node active for resumption.

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

### Linear Continuation Gate

`tplan` does not stop because work has taken too long. It challenges same-path
continuation when marginal Mission ROI, path dominance, or expected evidence delta is
weak or unclear.

For high-impact selection, subtraction, loopback, chain-role, active-task switch,
Mission closure, escalation, or continuation decisions, hook output should expose
`path_assessment`:

- `marginal_roi`: expected incremental Mission value of another same-path action.
- `path_role`: whether the path is a unique blocker, dominant path, one of many, or unclear.
- `evidence_delta`: whether the next action is expected to produce decision-constraining evidence.

Scripts validate this structure only. Agentic judgment decides whether the assessment
is true, and evidence links should constrain the confidence of the recommendation.

## Boundaries / 边界

- `tplan` must not become a standalone semantic reasoning engine; route semantic judgment to the appropriate Mindthus skill.
- Scripts must not decide semantic truth. They validate shape, state legality, authority, and evidence references.
- Evidence is not a process log; promote only acceptance, blocker, feedback, decision, state-change, or key finding records.
- Autonomous mode still stops when no authorized, ROI-defensible next action remains.

## Runtime Support / 支撑材料

### Resource Files

- `resources/schema.md`: mission files, task fields, decision packet, hook output.
- `resources/lifecycle.md`: Mission completion, closure, task states, transitions.
- `resources/policy.md`: risk/resource policy and human-in-loop authority.
- `resources/hooks.md`: decision hook triggers, routed skills, input/output contract.

### Runtime Scripts

Runtime scripts are added incrementally by implementation tasks. Until those scripts
exist, treat the script names in the Runtime Loop as planned interfaces rather than
executable commands.

Script output validates bookkeeping only. Agentic judgment remains required.
