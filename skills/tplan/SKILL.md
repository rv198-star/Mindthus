---
name: tplan
description: "Use when an AI agent needs an OKR-Runtime: a Mission needs script-driven task state, acceptance evidence, decision hooks, human-in-loop authority, or Mission-relative addition, subtraction, selection, closure, and recovery."
---

# tplan

## Core Claim / 核心判断

`tplan` is an OKR-Runtime for AI agents: it keeps a long-running Mission attached to
task state, acceptance evidence, decision hooks, and recovery authority.

Use OKR language as the primary public explanation: Mission maps to Objective;
acceptance criteria and acceptance evidence map to Key Results; Task, SubTask, and Step map to initiatives and actions. It is not a human OKR management system. Keep runtime
terms unless a schema migration explicitly remaps them: the reason is runtime precision,
not existing user familiarity.

Its cycle is shorter than ordinary OKR management: checkpoint, evidence, blocker,
feedback, or decision hook can update the active path while the Mission stays stable.
Treat it as a dynamic workflow runtime.

Scripts must not decide semantic truth: validate shape, legality, references and
authority. Route semantic judgment to `3l5s`, `sra`, `sela`, `edsp`, `wae`, or `tvg`.

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

Lite Startup Default is checkpoint-first startup. Delayed Step Materialization creates
Steps only for recovery, acceptance, rollback, evidence reference, or decomposition.
Sparse Evidence keeps routine notes in logs; only acceptance, blockers, feedback,
decisions, state changes and key findings become evidence. Checkpoint Command (`scripts/checkpoint.py`)
bundles log, optional evidence and survey without bypassing gates. Mission Pulse
(`scripts/mission_pulse.py`) builds a read-only Snapshot/Pulse/Gate before continuation,
freeze, handoff, stop, cleanup or risk review. Role-Separated Review Policy separates
doing, direction-checking, acceptance and learning: responsibility separation, not a new role model.

### Runtime Loop

For a known, bounded Task, reuse its objective and acceptance. Use `3l5s` only for
unclear or oversized proposals. Mutate structure through scripts, not hand edits;
separate logs from evidence. Consequential structure/authority changes, new blockers,
unknown recovery or same-path continuation triggers require survey,
`scripts/make_decision_packet.py` and a routed hook. Apply only validated decisions;
stop in Chinese when continuation is unsafe.

Lite Quickstart Recipe: Prefer these recipes over script-help exploration:
`python3 skills/tplan/scripts/init_lite.py --dir ...`, then `scripts/checkpoint.py`.
Use evidence, packet, hook and `scripts/apply_decision.py` when the triggers above apply.

### Shared Risk Context

execution units do not read each other's task logs. For blockers, degradation, evidence risk,
abnormal cost or recovery affecting another unit's risk-adjusted value, publish
`shared_context.risk_signals` via `scripts/record_risk_context.py`:
`risk_context_update` or `risk_context_recovery`. High-impact decisions with active
shared risk must expose `risk_assessment`.

### Mission Shared Context Memory

Run Mission identity preflight with `preflight_mission.py` at
`.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md`. `source_contexts`
are background only and never inherit acceptance authority.

Re-entry: a residual Mission is a candidate; require `--disposition`, `--rationale` and
a receipt before mutation. Active-Mission continuation is separate.

### User-Facing Output Adapter

Internal IDs are for runtime stability. User-facing output should lead with meaning;
ordinary updates should not lead with raw IDs. Use `scripts/render_user_update.py`:
`--progress` for text; `--visualization` for ChatGPT; `--html PATH` saves it.
Maintain optional `work_plan` from known context at planning, scope changes, major
blockers or re-estimation; leave gaps unknown without per-block questions.

Terminal handoff: `render_execution_cost_tree.py "$MISSION_DIR" --completion-handoff`;
include both emitted links or error. See `resources/user-output.md`.

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
- SRA may judge cross-task resource allocation; TPlan retains state, Pulse, continuation, authority, recovery, and mutation.
- Scripts validate bookkeeping only; they do not prove semantic correctness.
- Evidence is not a process log.
- Execution trace is cost/lifecycle telemetry, not evidence or a raw transcript.
- Shared Risk Context is not a cross-task transcript.
- Mission shared context Markdown is memory; `mission.json.shared_context` is the
  runtime index.
- Lite reduces ceremony; it cannot bypass high-impact gates.
- Autonomous mode stops when no authorized, ROI-defensible action remains.

## Runtime Support / 支撑材料

- Core contracts: `resources/schema.md`, `lifecycle.md`, `policy.md`, and `hooks.md`.
- Output contracts: `resources/user-output.md` and `execution-trace.md`.
- Review carriers: `resources/subagents.md`, `resources/platforms/*.md`, and
  `scripts/*review_packet.py`.
- Runtime views: `scripts/mission_pulse.py`, `render_user_update.py`, and
  `render_progress_view.py`, `render_execution_cost_tree.py`.
