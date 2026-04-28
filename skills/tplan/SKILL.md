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
7. Invoke the routed Mindthus skill named by the decision hook.
8. Apply or record the decision with `scripts/apply_decision.py`.

## Resource Files

- `resources/schema.md`: mission files, task fields, decision packet, hook output.
- `resources/lifecycle.md`: Mission completion, closure, task states, transitions.
- `resources/policy.md`: risk/resource policy and human-in-loop authority.
- `resources/hooks.md`: decision hook triggers, routed skills, input/output contract.

## Scripts

Run script help before use:

```bash
python3 skills/tplan/scripts/init_mission.py --help
python3 skills/tplan/scripts/check_mission.py --help
python3 skills/tplan/scripts/make_decision_packet.py --help
```

Script output validates bookkeeping only. Agentic judgment remains required.
