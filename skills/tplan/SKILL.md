---
name: tplan
description: Use when an AI agent needs an OKR-Runtime: a Mission needs script-driven task state, acceptance evidence, decision hooks, human-in-loop authority, or Mission-relative addition, subtraction, selection, closure, and recovery.
---

# tplan

## Core Claim / 核心判断

`tplan` is an OKR-Runtime for AI agents: a Mission-oriented task state and decision
control plane.

Use it when work needs to stay attached to a stable Mission, expose acceptance evidence,
avoid task-list drift, route semantic decisions to Mindthus skills, and preserve task
state in a resumable runtime.

If OKR helps a human team keep initiatives attached to objectives and key results,
`tplan` helps an AI agent keep long-running work attached to Mission, acceptance
evidence, task state, and decision authority. It is not a human OKR management system;
it is a runtime discipline for agents that otherwise drift inside long task lists.

Use OKR language as the primary public explanation. Keep current runtime schema and
scripts in `tplan` runtime terms unless a schema migration explicitly remaps them; the
reason is runtime precision, not existing user familiarity:

- Mission maps to Objective.
- acceptance criteria and acceptance evidence map to Key Results.
- Task, SubTask, and Step map to initiatives and actions.
- checkpoint, evidence event, blocker, feedback signal, and decision hook map to
  short-cycle check-ins or review signals.

Its cycle is shorter than ordinary OKR management: every checkpoint, evidence event,
blocker, feedback signal, or decision hook can update the active workflow while keeping
the Mission stable. Treat it as a dynamic workflow runtime, not a quarterly planning
sheet.

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

### Adaptive Runtime Policy

`tplan` should run as a thin Mission state machine by default and expand into a
control plane only when risk, recovery need, irreversibility, audit need, or judgment
pressure requires it.

Core rule:

```text
runtime level may reduce recording density, but it must not weaken key risk triggers.
```

Runtime levels change ceremony, not capability:

- `lite`: low-risk, short-path, reversible work with clear intent. Keep recovery state
  and sparse evidence; do not materialize every action as a Step.
- `normal`: default Mission work. Maintain task tree state, materialize meaningful
  SubTasks/Steps, record selective evidence, and use lightweight alignment for
  ordinary child work.
- `strict`: high-risk, long-running, multi-branch, human-authority-sensitive, or
  audit-heavy work. Use full decision packets, Mission Review, stronger evidence
  links, and triggered audit gates.

Lite mode minimum state:

- Mission objective
- acceptance criteria
- active node
- latest state
- blocker, evidence, or decision summary when present

All levels must preserve Mission anchoring, recoverable active state, task-tree
legality for materialized nodes, evidence/log separation, high-impact decision hooks,
and graceful stop behavior.

### Lite Startup Default

Use a checkpoint-first startup for low-risk, short-path, reversible Missions with clear
intent:

1. Initialize with `scripts/init_lite.py`.
2. Create exactly one active root Task that covers current acceptance evidence.
3. Record the latest recoverable state in the lite runtime narrative.
4. Use `scripts/checkpoint.py` for routine task-local notes or sparse evidence.
5. Do not create a Step until a promotion trigger appears.

This startup path preserves Mission objective, acceptance criteria, active node, latest
state, and recovery context without materializing a Step for the first ordinary action.

Escalate from lite to the expanded loop when the work becomes irreversible, needs
rollback, needs acceptance-level done checking, needs an evidence-linked action,
branches into multiple actions, hits a blocker, repeats failed attempts, or may change
Mission convergence.

### Delayed Step Materialization

Ordinary execution actions may start as task-local logs or notes. Promote an action into
a Step only when it needs recovery, acceptance, rollback, evidence reference, or has
grown into multi-action work.

This keeps the task tree from becoming a transcript of every micro-action while
preserving resumability when an action becomes important.

### Sparse Evidence

Evidence is intentionally sparse. Record evidence only when it constrains acceptance,
state change, blocker, user feedback, decision, or key finding claims. Routine process
notes stay in logs or archive summaries.

### Checkpoint Command

Use `scripts/checkpoint.py` when a lightweight runtime update needs to record an
optional task-local log, optional sparse evidence, and current survey in one call.

Checkpoint reduces script-call overhead only. It must not decide semantic truth,
choose runtime level, apply decision mutations, or bypass alignment, review, decision
hooks, or stop conditions.

### User-Facing Output Adapter

Internal IDs are for runtime stability. User-facing output should lead with meaning.

ordinary updates should not lead with raw IDs such as `T1`, `S2`, or `E3`. Translate
active nodes into task titles, evidence IDs into evidence summaries, and decision
packets into concise rationale plus next-action language. Keep raw IDs secondary, and
show them only for debug, audit, strict review, exact recovery, script failure, or an
explicit user request.

Use `scripts/render_user_update.py` when a Mission runtime needs a compact Chinese
status update for the user. Use `--include-internal` only when internal recovery
references are needed.

### Read-only SubAgent Acceleration

SubAgents are scouts, not controllers.

Use SubAgents for read-only parallel investigation when independent discovery branches
can reduce cost. SubAgent outputs are candidate findings. The main agent must verify,
merge, decide, and write any tplan runtime state.

Put another way: main agent must verify, merge, decide, and write; SubAgents only
investigate.

SubAgents may read files, search code or docs, inspect packages, compare options,
collect candidate evidence, and perform read-only review.

SubAgents must not mutate files, Mission state, evidence, task tree, decisions, or external systems.
They must not make final user-facing conclusions on behalf of the main agent.

Do not add a user-facing SubAgent mode switch. This is a guardrail for safe acceleration:
parallelize discovery when useful, but keep all writes, evidence records, task
mutations, decisions, and final conclusions under the main agent.

### Runtime Loop

The full loop below is the expanded `normal` / `strict` path. In `lite`, preserve the
minimum Mission state and use the same risk triggers without running every ceremony step.

1. Initialize Mission files with `scripts/init_lite.py` for lite startup or
   `scripts/init_mission.py` for expanded startup.
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

Use decision handling levels to avoid packet overuse:

- `inline alignment`: ordinary Step/SubTask choices; write a short parent-alignment
  note and continue.
- `light packet`: subpath switch, blocker, repeated failed attempt, or meaningful
  uncertainty that may affect parent convergence.
- `full mission review`: high-impact Mission-facing changes that can materially affect
  convergence.

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
- Lite mode is not a weaker `tplan`; it reduces runtime ceremony only. It cannot bypass
  high-impact alignment, review, decision hooks, or stop conditions.
- Autonomous mode still stops when no authorized, ROI-defensible next action remains.

## Runtime Support / 支撑材料

### Resource Files

- `resources/schema.md`: mission files, task fields, decision packet, hook output.
- `resources/lifecycle.md`: Mission completion, closure, task states, transitions.
- `resources/policy.md`: risk/resource policy and human-in-loop authority.
- `resources/hooks.md`: decision hook triggers, routed skills, input/output contract.
- `resources/user-output.md`: user-facing rendering rules for hiding internal IDs by default.
- `resources/subagents.md`: read-only SubAgent acceleration and merge rules.

### Runtime Scripts

Runtime scripts are added incrementally by implementation tasks. Until those scripts
exist, treat the script names in the Runtime Loop as planned interfaces rather than
executable commands.

Use `scripts/init_lite.py` for checkpoint-first startup: one active root Task, Mission
acceptance coverage, latest recoverable state, and no Step materialization until a
promotion trigger appears.

Use `scripts/checkpoint.py` for compact routine checkpoints: optional local log,
optional sparse evidence, and survey output. Use dedicated decision, transition, stop,
or review scripts when the runtime action changes authority, status, or Mission path.

Use `scripts/render_user_update.py` for ordinary user updates: it renders Mission
objective, active work, confirmed evidence summaries, and next action without leading
with internal IDs.

### Lite Quickstart Recipe

Prefer these recipes over script-help exploration when the required inputs are already
known. Use `--help` or source inspection only when arguments are missing, a command
fails, or behavior is unclear.

Lite startup:

```bash
python3 skills/tplan/scripts/init_lite.py --dir "$MISSION_DIR" \
  --mission-id "$MISSION_ID" \
  --title "$MISSION_TITLE" \
  --objective "$MISSION_OBJECTIVE" \
  --acceptance-evidence "A1:First acceptance condition." \
  --active-task-id T1 \
  --active-task-title "$ACTIVE_TASK_TITLE" \
  --active-task-contribution "$ACTIVE_TASK_CONTRIBUTION" \
  --latest-state "$LATEST_RECOVERABLE_STATE" \
  --human-in-loop 0 \
  --risk-tolerance "$RISK_TOLERANCE" \
  --resource-sufficiency "$RESOURCE_SUFFICIENCY"
```

Routine lite checkpoint:

```bash
python3 skills/tplan/scripts/checkpoint.py "$MISSION_DIR" \
  --task-id T1 \
  --log-summary "$ROUTINE_NOTE" \
  --log-payload-json '{"routine_note":true}' \
  --evidence-type acceptance \
  --evidence-summary "$ACCEPTANCE_OR_KEY_FINDING" \
  --evidence-task-id T1 \
  --evidence-payload-json '{"acceptance_ids":["A1"]}'
```

High-impact escalation:

```bash
python3 skills/tplan/scripts/record_evidence.py "$MISSION_DIR" \
  --event-type user_feedback \
  --summary "$HIGH_IMPACT_SIGNAL" \
  --task-id T1 \
  --payload-json '{"impact":"high"}'

python3 skills/tplan/scripts/make_decision_packet.py "$MISSION_DIR" \
  --hook subtraction \
  --output "$MISSION_DIR/decisions/subtraction-packet.json"

python3 skills/tplan/scripts/apply_decision.py "$MISSION_DIR" \
  --decision "$MISSION_DIR/decisions/subtraction-hook-output.json"
```

If the decision cannot be safely applied, record a graceful stop with
`scripts/stop_report.py` and keep the blocked node active for resumption.

Script output validates bookkeeping only. Agentic judgment remains required.
