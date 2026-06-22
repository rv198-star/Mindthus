---
name: tplan
description: "Use when an AI agent needs an OKR-Runtime: a Mission needs script-driven task state, acceptance evidence, decision hooks, human-in-loop authority, or Mission-relative addition, subtraction, selection, closure, and recovery."
---

# tplan

## Core Claim / 核心判断

`tplan` is an OKR-Runtime for AI agents: it keeps a long-running Mission attached to
task state, acceptance evidence, decision hooks, and recovery authority.

Use OKR language as the primary public explanation: Mission maps to Objective,
acceptance criteria and acceptance evidence map to Key Results, and Task, SubTask, and Step map to initiatives and actions. It is not a human OKR management system. It keeps
current runtime terms unless a schema migration explicitly remaps them; the reason is runtime precision, not existing user familiarity.

Its cycle is shorter than ordinary OKR management: checkpoint, evidence, blocker,
feedback, or decision hook can update the active path while the Mission stays stable.
Treat it as a dynamic workflow runtime.

Scripts must not decide semantic truth. They validate shape, legality, references, and
authority. Semantic judgment routes to `3l5s`, `sela`, `edsp`, `wae`, or `tvg`.

## Mainline / 主路径

### Startup Policy

Mission startup records `human_in_loop`, `risk_tolerance`, and
`resource_sufficiency`. Default `human_in_loop` is `0` autonomous. Use
`scripts/init_lite.py` for low-risk checkpoint-first startup and `scripts/init_mission.py`
when expanded runtime state is needed.

### Adaptive Runtime Policy

Run as a thin Mission state machine by default. `runtime level may reduce recording density, but it must not weaken key risk triggers`.

- `lite`: reversible, short-path work. Lite mode minimum state is Mission objective,
  acceptance criteria, active node, latest state, and blocker/evidence/decision summary.
- `normal`: default Mission work with meaningful Task/SubTask/Step state.
- `strict`: high-risk, long-running, audit-heavy, or authority-sensitive work.

Lite Startup Default means checkpoint-first startup; Delayed Step Materialization means
ordinary actions become Steps only when they need recovery, acceptance, rollback,
evidence reference, or decomposition. Sparse Evidence means routine notes stay in logs;
only acceptance, blocker, feedback, decision, state-change, or key finding records
become evidence. Checkpoint Command means `scripts/checkpoint.py` may bundle a local log,
optional sparse evidence, and survey output, without bypassing gates.
Mission Pulse means `scripts/mission_pulse.py` may build a read-only Snapshot/Pulse/Gate
route note before continuation, freeze, handoff, stop, branch cleanup, or risk review.

### Runtime Loop

Use `3l5s` for success-critical Task proposal. Mutate structure through scripts, not
hand edits. Separate logs from evidence. Survey state, build a packet with
`scripts/make_decision_packet.py`, run the routed Mindthus hook, then apply only
validated decisions. Stop in Chinese when continuation is unsafe.

Lite Quickstart Recipe: Prefer these recipes over script-help exploration when inputs
are known. Start with `python3 skills/tplan/scripts/init_lite.py --dir ...`, checkpoint
with `scripts/checkpoint.py`, escalate through evidence, packet, hook, and
`scripts/apply_decision.py`.

### Shared Risk Context

Use Shared Risk Context when a local blocker, degraded condition, invalid evidence
risk, abnormal cost, or recovery signal may affect another unit's risk-adjusted value.
execution units do not read each other's task logs. Publish scoped signals to
Mission-level `shared_context.risk_signals`. `scripts/record_risk_context.py` writes
`risk_context_update`; recovery writes `risk_context_recovery`. High-impact decisions
with active shared risk must expose `risk_assessment`.

### Mission Shared Context Memory

Before starting a Mission, run Mission identity preflight with `preflight_mission.py`.
Project-level memory lives at
`.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md`. Continue only
when Mission identity is continuous; otherwise create a new Mission. `source_contexts`
are background memory for a new Mission, not a derived Mission status or inherited
acceptance authority.

### User-Facing Output Adapter

Internal IDs are for runtime stability. User-facing output should lead with meaning;
ordinary updates should not lead with raw IDs. Use `scripts/render_user_update.py` for
compact Chinese status updates.

### Read-only SubAgent Acceleration

SubAgents are scouts, not controllers. SubAgent outputs are candidate findings. The
main agent must verify, merge, decide, and write. SubAgents must not mutate files, Mission state, evidence, task tree, decisions, or external systems.

## Guardrails / 从属补漏

### Anti-Spiral Gate

Activate Anti-Spiral when local repair may be replacing Mission progress: third touches,
worsening feedback, additive layering, or weak evidence delta. This gate can route back
to `3l5s`, `wae`, subtraction, rollback, or a stop.

### Alignment Gate

Task alignment is hierarchical. Task faces Mission; SubTask faces Task; Step is the
execution leaf. Step never has children. Use `parent_alignment` for ordinary work and
`mission_alignment` / `mission_review` for high-impact Mission-facing changes.

### Linear Continuation Gate

Same-path continuation needs `path_assessment`: `marginal_roi`, `path_role`, and
`evidence_delta`. Elapsed time alone is not the criterion; Mission ROI and expected
evidence delta are.

#### Continuation Authorization

Mission-facing same-path `continue` decisions must expose `continuation_authorization`.
count-based reminders are triggers, not decisions. The record includes
`trigger_reasons`, `evidence_shape_lint`, `defect_classification`,
`expected_evidence_delta`, and `authorized_action`.

Use generic trigger reasons such as `repeated_same_path_attempt`,
`post_continuation_defect`, `high_cost_or_high_blast_radius_continuation`, and
`weak_or_unclear_evidence_delta`. Mechanical checks are shape-only evidence. Agentic
judgment decides whether a defect is `acceptance_blocking`, `batchable_detail`, or
`unclear`, and whether continuation still has Mission ROI.

### Graceful Stop

Stop cleanly when continuing would require inventing intent, authority, acceptance
criteria, or product judgment. `scripts/stop_report.py` records `stop_report` evidence,
marks the active node `blocked`, sets Mission to `requires_human`, and keeps resumption
context.

## Boundaries / 边界

- `tplan` is runtime governance, not a standalone reasoning engine.
- Scripts validate bookkeeping only; they do not prove semantic correctness.
- Evidence is not a process log.
- Shared Risk Context is not a cross-task transcript.
- Mission shared context Markdown is memory; `mission.json.shared_context` is the
  runtime index.
- Lite mode reduces ceremony only; it cannot bypass high-impact gates.
- Autonomous mode still stops when no authorized, ROI-defensible next action remains.

## Runtime Support / 支撑材料

- `resources/schema.md`: mission files, task fields, decision packet, hook output.
- `resources/lifecycle.md`: Mission completion, closure, task states, transitions.
- `resources/policy.md`: risk/resource policy and human-in-loop authority.
- `resources/hooks.md`: decision hooks, routed skills, path/risk/continuation contracts.
- `resources/user-output.md`: user-facing rendering rules.
- `resources/subagents.md`: read-only SubAgent acceleration and merge rules.
- `scripts/mission_pulse.py`: read-only Mission Pulse route note.
