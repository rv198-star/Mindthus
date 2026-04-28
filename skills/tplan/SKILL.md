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
- `wae`: control boundaries and evidence bridges
- `tvg`: artifact depth audit

## Startup Policy

Mission startup uses three numeric inputs:

- `human_in_loop`: `0` autonomous, `100` advisory; mixed modes are reserved.
- `risk_tolerance`: `0-33` low, `34-66` normal, `67-100` high.
- `resource_sufficiency`: `0-33` poor, `34-66` normal, `67-100` rich.

Default `human_in_loop` is `0`.

## Runtime Loop

1. Initialize Mission files with `scripts/init_mission.py`.
2. Use `3l5s` to propose success-critical level-2 Plan Tasks.
3. Validate the tree with `scripts/check_mission.py`.
4. Record execution evidence with `scripts/record_evidence.py`.
5. Survey state with `scripts/survey.py`.
6. Generate a decision packet with `scripts/make_decision_packet.py`.
7. Run the Mission Review Gate for the decision weight.
8. Invoke the routed Mindthus skill named by the decision hook.
9. Ensure the hook output states Mission alignment before mutation.
10. Apply or record the decision with `scripts/apply_decision.py`.

## Mission Review Gate

Every addition, subtraction, selection, loopback, and closure decision must stay
Mission-relative without turning every small step into ceremony.

Use a lightweight gate for ordinary decisions: state `mission_alignment` in one or two
sentences before applying or recording the decision.

Use a full `mission_review` for high-impact decisions:

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
