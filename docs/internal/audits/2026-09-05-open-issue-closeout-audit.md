# Mindthus Open-Issue Closeout Audit

Date: 2026-09-05

Baseline:

- `main`: `d4db02f5e1a9d07b35273ee0010d0884d8cef121`
- current Stable: `v1.10.0`
- Stable source: `facc26ebac7004700881bd45f60e33960a197761`
- release verification: `docs/internal/audits/2026-09-05-v1.10.0-release-verification.md`

## Purpose

After the v1.10.0 SRA/maintenance release, distinguish real active work from historical
trackers, already-implemented TPlan defects, unaccepted design candidates, evidence work,
and host/platform extensions. This audit does not add product behavior.

The project now enters a feature-freeze/evidence phase: do not add methodology,
guardrails, or runtime behavior merely because an old proposal remains open. New core
engineering should require a reproducible defect, a material safety/authority gap, or
repeated real-use evidence showing a bounded value-gain opportunity.

## Verification used for closeout

Current implementation was inspected against the open issue acceptance surfaces. A
focused current-main regression run covered:

- `tests/tplan/test_render_user_update.py`
- `tests/tplan/test_execution_cost_tree.py`
- `tests/tplan/test_runtime_provenance.py`
- `tests/tplan/test_mission_shared_context.py`
- `tests/tplan/test_mission_pulse.py`
- `tests/tplan/test_codex_review_packet.py`
- `tests/tplan/test_stop_report.py`

Result: **141 tests passed**.

The same current product line was released as v1.10.0 only after the full repository
suite, Test Lifecycle, packaging, Stable/Beta composition, download and checksum gates
passed. Closeout below does not convert those deterministic tests into real-host or
real-task evidence.

## Close now — completed or absorbed

### #129 — v1.5.1 release tracker

Close as historical/obsolete. Its release train is long superseded by the published
v1.10.0 line. Keeping an old patch tracker open no longer represents active work.

### #135 — Quiet no-op / three-check heartbeat

Close as completed. The issue body itself records `implemented / acceptance verified`.
Current `render_user_update.py` implements the bounded quiet streak and heartbeat;
current tests cover automatic quiet/heartbeat, explicit status, Mission/evidence change,
Guard changes, invalid cursors and read-only failure boundaries.

### #139 — Projection is not a second source of truth

Close as absorbed in stronger current contracts. Current projection surfaces are
read-only or authority-bounded: Mission Pulse is read-only; user-update rendering does
not mutate Mission state; execution-cost rendering does not become a writer; Codex
review packets identify read-only reviewers; platform docs keep Mission/evidence
mutation and final authority with the main runtime/agent boundary. No separate writable
projection contract is needed.

This is an absorbed design rule, not a claim that arbitrary external prose cannot lie.

### #141 — truthful Standard completion timeline

Close as completed. Current regression coverage includes:

- every real node/declared edge preserved;
- vertical timeline/card rendering;
- incomplete terminal lifecycle downgraded to partial/snapshot coverage;
- exact lifecycle with zero cost spans kept separate from unavailable cost telemetry;
- missing active-path events downgrade coverage;
- unknown measurement remains unknown rather than zero;
- completion handoff and renderer failure/provenance boundaries.

### #142 — stale/duplicate runtime selection

Close as completed. `runtime_provenance`, runtime fingerprints and `runtime_doctor.py`
cover stale/duplicate roots, explicit versus ambiguous selection, missing renderer,
incompatible runtime mutation, terminal handoff and relocation compatibility. Tests
include the original stale-v1.1-versus-installed-v1.5.2 shape.

The host/filesystem bypass boundary remains correctly outside this issue and is owned by
#140.

### #147 — sparse telemetry presentation

Close as completed. Standard derives `presentation_density`, consolidates absent
channels, preserves observed channels and abnormal signals, does not render absent values
as zero, and distinguishes partial observed windows from exact lifecycle. Audit/JSON keep
the full coverage contract.

### #148 — explicit Mission re-entry decision

Close as completed. Current preflight separates discovery from authorization, uses
`needs_agentic_selection`, preserves current objective/acceptance continuity as an
assessment rather than execution authority, treats terminal/requires-human/provenance
conflicts fail-closed, and writes only after an explicit disposition/application step.
Current tests cover missing intent, match/mismatch, terminal state, requires-human,
stale state, multiple candidates, provenance conflict, tamper/freshness races and plain
language recovery output.

## Close now — design candidates not adopted under feature freeze

These are not marked implemented. They are closed because they never became accepted
product requirements and there is no current repeated real-use evidence justifying new
runtime surface. Reopen or create a new bounded issue if evidence later demonstrates the
failure mode.

### #133 — scoped Human Gate + safe fallback

Current canonical stop behavior remains a scoped blocked task plus Mission
`requires_human`; it does **not** implement the proposed `blocked_route`,
`safe_default_if_no_human`, `independent_work_still_allowed`, or automatic safe-bypass
model. The proposal would add meaningful control semantics and should not remain an
implicit P0 without current evidence. Close as not adopted.

### #137 — user/Agent dual-channel display

This proposal depends on the unadopted scoped-bypass semantics in #133. Current output
already distinguishes user-facing meaning, constraints and runtime state, but does not
promise an independent-work channel while the primary route waits for a human. Close as
not adopted; reopen only from a real communication/control failure.

### #138 — five-question stop/handoff schema

Current stop reports already provide current goal, attempts, blocker, why continuation
is unsafe, human need and resume condition. The proposed additional stable five-question
payload was never accepted as a required schema. Avoid adding duplicate handoff fields
without evidence that current recovery packets are insufficient. Close as not adopted.

### #67 — unified Mindthus CLI exploration

Close as deferred architecture exploration. Current script/runtime surfaces and release
packs are working; there is no current evidence that a new CLI layer pays for its
migration/compatibility cost. A future CLI should begin from a concrete developer/user
friction case, not from script-count growth alone.

## Close umbrella discussions

### #132 — LoopX absorption umbrella

Close after recording the final disposition:

- #134: accepted/implemented previously;
- #135: accepted/implemented, close now;
- #136: accepted/implemented previously;
- #139: compatible rule absorbed by stronger current read-only/authority boundaries;
- #133/#137/#138: not adopted under feature freeze; evidence required to reopen.

The umbrella has completed its decision role and should not remain an active roadmap.

### #183 — functional optimization discussion umbrella

Close after v1.10.0. Its SRA engineering decisions were executed (#188/#189/#190 and PR
#191), while remaining work has dedicated evidence/platform issues. Keeping the umbrella
open would make completed feature discussion look like active engineering.

## Keep open — evidence / effectiveness

### #144 — real-use evidence

Keep. This is the primary evidence backlog: real-use records are still empty and cannot
be fabricated. The next phase should collect natural tasks and aggregate repeated
mechanisms rather than use benchmark shape scores as product-value proof.

### #184 — end-to-end value/cost comparison

Keep. This asks whether Mindthus beats native Agent and a short generic-discipline
control on matched real tasks. It is central effectiveness evidence, not a missing
feature.

### #185 — SRA intake/card benefit observation

Keep. MVP is implemented; only real preparation cost, extra turns, total calls/tokens
and user usefulness remain unproven.

### #186 — SRA completion-reference benefit observation

Keep. MVP is implemented; actual false-conflict/reconciliation reduction and net cost
remain unproven.

### #187 — capability/evidence status view

Keep as evidence-governance support. If implemented, it must aggregate existing sources
without turning packaging/contract tests into host or behavior certification.

### #112 — 2.0/progressive-disclosure research

Keep HOLD. It should not restart until current entry/load cost is measured and a bounded
experiment is justified.

## Keep open — real platform extensions

### #140 — host-native authority / mutation-prevention certification

Keep. Current deterministic contracts do not provide the host-only signer/filesystem
boundary or per-platform real E2E required by this issue.

### #143 — Codex telemetry capture

Keep. The adapter and deterministic tests exist, but the issue explicitly requires real
Codex E2E capture and correlation. Tests alone do not satisfy that acceptance condition.

### #146 — Codex App/CLI hook activation reliability

Keep. This specifically requires separate App/CLI and user/project hook-source E2E.
Current docs intentionally keep those claims experimental.

## Resulting active backlog

After closeout, the intended open set is:

- Evidence/effectiveness: #112 (HOLD), #144, #184, #185, #186, #187
- Platform extensions: #140, #143, #146

Everything else listed above should be closed with a comment stating whether it was
completed/absorbed, historical/obsolete, or not adopted under feature freeze.

## Feature-freeze discipline

Until evidence changes the picture:

> Do not add a new Mindthus method, guardrail, schema family, runtime control path, or
> platform abstraction merely because it is conceptually attractive. Reopen engineering
> only for a reproducible correctness/safety defect, a concrete platform capability gap
> that has been explicitly prioritized, or repeated real-use evidence showing a bounded
> net-value opportunity.
