---
name: tplan
description: Use only when the user explicitly asks for tplan or a workflow routes work into the Mission runtime; not for passive activation from long-term goal wording, durable task state, task trees, resumption, autonomous progress, ordinary plans, or todo lists.
---

# tplan

`tplan` is a Mission-oriented project manager and control plane.

Use it when work needs to stay attached to a stable Mission, avoid task-list drift,
route semantic decisions through decision hooks to Mindthus skills, and preserve task
state in a resumable runtime.

## Activation Boundary

tplan is manual or workflow-routed. Use it only when the user explicitly asks for
tplan, asks to run a Mission runtime, or an existing workflow routes the work into
tplan.

Workflow routing must be explicit: an external process, script, upstream hook, or user
instruction names tplan or Mission runtime. Do not infer workflow routing from a
request that merely looks suitable for tplan.

长期目标、复杂项目、计划、todo、plan、保留任务状态、任务树、恢复现场、几十步、切换任务、记录证据、后续轮次、自动推进、状态持久化等自然语言需求，可以提示任务可能需要拆解或确认运行方式，但不被长期目标表述被动唤起 tplan。普通执行先用当前最小合适方法处理；需要 tplan 时先向用户确认，而不是自行初始化 Mission 文件和运行时脚本。只有用户显式要求使用 tplan，或 workflow 明确路由到 Mission runtime，才进入 tplan。

For activation-only routing, choose `null` for tplan-shaped natural-language requests
unless the user explicitly names tplan/Mission runtime or an external workflow names
tplan. Do not select tplan just because the request mentions many steps, task
switching, evidence recording, resumable context, or persistent state.

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
7. If execution cannot safely continue, write a concise Chinese stop report with
   `scripts/stop_report.py` and request human intervention.
8. Archive completed task logs with `scripts/archive_task_logs.py` and promote only the
   summary or key findings to evidence when they support a claim.
9. Survey state with `scripts/survey.py`.
10. Generate a decision packet with `scripts/make_decision_packet.py`.
11. Run the parent-alignment or Mission Review Gate for the decision weight.
12. Invoke the routed Mindthus skill named by the decision hook.
13. Validate LLM-produced hook output with `scripts/validate_decision.py`.
14. If validation fails once, repair the decision JSON shape; if it fails twice, use
    `scripts/stop_report.py`.
15. Apply or record the valid decision with `scripts/apply_decision.py`.

For simple state transitions after judgment has already happened, use narrow commands:
`scripts/set_active_task.py`, `scripts/complete_task.py`, `scripts/block_task.py`, and
`scripts/pause_task.py`. These commands do not decide whether the transition is wise;
they only enforce deterministic runtime state changes.

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

## Graceful Stop

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

## Contract Failure Policy

Strict runtime scripts should not be the first contact point for loose LLM output.

Before `apply_decision.py`, use `scripts/validate_decision.py` when the decision JSON
was produced by an LLM or copied from a hook response.

Failure policy:

1. First contract failure: read the validation errors and repair template, then ask the
   agent to repair the decision JSON shape.
2. Second contract failure: stop cleanly with `scripts/stop_report.py`, explain the
   contract blocker in Chinese, and request human intervention.

This repairs shape only. It does not prove the recommendation is semantically correct.

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
