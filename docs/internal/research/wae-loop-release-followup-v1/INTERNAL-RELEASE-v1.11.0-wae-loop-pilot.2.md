# Internal Pilot Release: v1.11.0-wae-loop-pilot.2

Date: 2026-09-07
Status: INTERNAL PILOT / NOT STABLE / NOT ROI BETA
Issue: #207
Research PR: #208
Supersedes for new pilots: `v1.11.0-wae-loop-pilot.1`

## Purpose

`pilot.2` is the first integrity-hardened WAE Loop pilot package for real-project admission. It responds directly to the WFF deterministic audit of `pilot.1` at commit `bbf55dd98672dab1deaa023252cbe96e05e91764`.

Mindthus accepts both WFF blockers as runtime defects and includes both proposed hardening items in the same root-cause repair. New WFF / EKRI / Slidethus pilots should use `pilot.2`; `pilot.1` remains immutable historical evidence and should not be newly admitted.

## Root-cause repair

The `pilot.1` runtime accidentally treated `summary.json` as both sequence authority and a derived view while `trace.jsonl` was also persisted. `guard-handoff` then consumed the latest trace checkpoint without first proving the persisted run was coherent.

`pilot.2` establishes one authority model:

> immutable activation agreement + valid fsynced hash-chain trace are authoritative; summary and portable bundle are derived and recoverable.

### BLOCKER 1 — guard-handoff on invalid trace: CLOSED

`guard-handoff` now validates the authoritative activation/trace state before consuming a handoff checkpoint. Broken sequence/hash chain, invalid persisted event shape, invalid lifecycle relationship, or activation binding causes fail-closed behavior. Stale but derivable `summary.json` / `wae-loop-run.json` may be reconstructed from a valid authoritative trace.

### BLOCKER 2 — interrupted append duplicate sequence: CLOSED

A new append no longer allocates sequence from `summary.json`. It validates the existing activation/trace, derives the current state from the last valid trace event, repairs stale derived views, and then allocates `sequence = len(valid_trace) + 1` with the previous event hash.

If a process stops after trace append + fsync but before summary/bundle advancement, the next append recovers from the valid trace rather than producing `1 -> 2 -> 2`. If the trace itself is malformed or its integrity cannot be established, append fails closed.

### HARDENING 1 — immutable activation agreement binding: INCLUDED

`activation.json` now carries `activation_sha256`. Every persisted trace event binds that digest. Post-enable mutation of Owner, scope, reserved decisions, handoff purpose or other activation fields invalidates the run even if derived files are regenerated.

### HARDENING 2 — complete persisted event validation: INCLUDED

Trace schema version is now `mindthus.wae-loop-trace.v0.2`. Runtime validation checks required fields, decision/enumeration domains, artifact/cost/coverage shapes, decision-specific invariants, sequence/hash chain and basic event lifecycle relationships. A hash-correct event with an invalid checkpoint decision or missing required semantics is rejected.

## Host responsibilities unchanged

The WFF audit correctly identified two host responsibilities; they remain outside the Mindthus runtime defect set:

1. A qualifying WFF handoff should always call `guard-handoff` with the actual artifact/ref/hash. Omitting artifact binding intentionally weakens live-artifact protection.
2. `need_input` / `stop` finish removes the active WAE pointer by design. WFF owns durable phase/task status and must not interpret later `disabled` pass-through as prior phase qualification.

## Pilot behavior retained

- WAE Loop remains OFF by default.
- Activation is explicit and bounded.
- Active responsibility handoffs require `handoff | refine | need_input | stop` checkpoints.
- Loop depth is semantic handoff depth, not request count.
- One-pass handoff remains valid.
- Mechanical and authorized Agentic downstream owners are both valid closure boundaries.
- Project-local trace root remains `.mindthus/wae-loop/`.
- `wae-loop-run.json` remains the convenient retrieval artifact; `trace.jsonl` is the authoritative event log together with immutable activation agreement.
- TPlan/host continues to own Mission/task lifecycle and recovery.

## Validation

Before freezing the internal package candidate:

- full repository unittest: **1104 passed, 5 skipped**;
- WAE delegation-loop + WAE contract targeted tests: **37 passed**;
- WFF audit regressions added for invalid-trace guard, post-fsync recovery, activation mutation and hash-correct invalid event shape;
- release-pack inclusion remains covered by WAE runtime tests;
- no model calls were used to qualify these deterministic runtime repairs.

These checks validate runtime integrity and packaging contracts only. They do not prove WAE Loop semantic value in WFF / EKRI / Slidethus.

## Consumer rule

New real-project pilots should pin the exact `pilot.2` ZIP + SHA256 and must not continue from `pilot.1` as if the runtime contracts were identical. Existing `pilot.1` audit evidence remains useful as predecessor evidence; no `pilot.1` run should be rewritten to `pilot.2`.
