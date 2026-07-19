# TPLAN Destination-First Discovery Trial Protocol

## Status

Locally pre-specified research protocol for Mindthus issue #109. This document fixes
the comparison and decision rule before the experiment result is interpreted.

The protocol was written before the local experiment was run, but it was not committed
or otherwise publicly timestamped beforehand. “Locally pre-specified” records the
owner-reported order of work; it is not independently timestamped preregistration.

This is not implementation approval and does not change `tplan.v0.1`.

## Question

Does TPLAN need an optional durable pre-Task discovery representation, or can the
same practical value be obtained by correctly using the existing Mission objective,
Mission Shared Context, a bounded discovery Task, and the `addition`, `selection`, and
`loopback` gates?

The tested object is the recoverable boundary between an in-scope but not-yet-precise
region and a materialized runtime Task. The tested object is not Wayfinder as a whole.

## Compared Variants

### A. Eager task materialization

Every in-scope region becomes a pending, blocked, or exploratory Task as soon as it is
noticed, even when its question or completion condition is not yet precise.

This is the pressure-case baseline, not a claim that current TPLAN requires this
behavior.

### B. Current TPLAN used correctly

- Mission objective and acceptance evidence remain canonical.
- A bounded discovery Task may investigate an uncertain area.
- Vague regions remain in Mission narrative/shared context.
- Once a region is precise enough, `addition` creates a Task.
- `selection` chooses among existing runtime nodes.
- `loopback` handles invalidated definitions.

### C. Destination-first discovery representation

- Destination is derived from Mission objective, acceptance evidence, and authority.
- A Fog record is durable but non-executable.
- Graduation creates a new Task with provenance; it does not turn the Fog object into a
  Task lifecycle state.
- Only materialized Tasks may enter the executable frontier or Mission completion.
- A read-only projection may expose structural eligibility but may not select.

## Core Fixture Requirements

The deterministic fixture must cover:

1. derived Destination;
2. initial Fog;
3. one Fog graduation into a new Task;
4. one resolved decision that exposes new Fog;
5. one decision that supersedes an earlier candidate;
6. a Task blocked by another decision;
7. multiple eligible Tasks routed to `selection`;
8. selected/active and resolved Tasks;
9. out-of-scope and superseded Fog history;
10. restart from identical canonical state with the same frontier;
11. a proof that Fog cannot enter the frontier or satisfy Mission completion.

## Real Mission Replays

### Replay 1: V5 targeted stabilization

Primary anchors:

- `.tplan/missions/mission-v5-targeted-stabilization/mission.json`
- `.tplan/shared_contexts/tplan_mission_shared_context-mission-v5-targeted-stabilization.md`
- `docs/benchmarks/v5-targeted-plan.md`
- GitHub issues #102-#108

Reason for selection: the destination stayed stable while issue #107, issue #108,
track 105a/105b, natural-activation requirements, and certification blockers emerged
after initial materialization.

### Replay 2: Issue #31 TVG value profiles and Shaw Brothers pilot

Primary anchors:

- `.tplan/missions/issue-31-tvg-value-profiles-run/mission.json`
- `.tplan/missions/issue-31-tvg-value-profiles-run/evidence.jsonl`
- `.tplan/missions/issue-31-tvg-value-profiles-run/logs/`
- GitHub issue #31

Reason for selection: three initial Tasks were well specified, but the pilot later
exposed a clean-room evidence requirement. The replay tests whether that requirement
is genuinely Fog or already precise enough for the existing `addition` gate.

### Negative control: MPG convergence

Primary anchors:

- `.tplan/missions/mainline-path-game-tvg-2026-06-08-run/mission.json`
- `.tplan/missions/mainline-path-game-tvg-2026-06-08-run/mainline-path-game-tvg-analysis.md`

Reason for selection: the initial Task sequence remained coherent through completion.
An optional discovery mode should stay off when no pre-Task uncertainty needs durable
representation.

## Evidence Provenance

The deterministic fixture and the replay coding are committed test inputs. The replay
classifications are owner-curated readings of the listed sources, rather than an
automated extraction of historical Mission state. The exact public links, local-source
paths, and SHA-256 identities of the local snapshots used during the research are in
[the source manifest](fixtures/issue_109_destination_first/source_manifest.md).

That manifest makes the inputs inspectable and the experiment mechanically rerunnable.
It does not independently establish that an untracked historical runtime snapshot was
the only or authoritative reading of a Mission.

## Observations

Fixture-local counts are allowed, but they are not universal performance measures.
For each replay, record:

- prematurely materialized nodes;
- stale or superseded-node churn;
- repeated semantic decisions;
- unresolved regions visible after restart;
- canonical surfaces needed to recover the next decision;
- human/authority interventions;
- whether handoff distinguishes Fog, Task, blocker, and completion;
- extra durable records introduced by the destination-first representation.

Also record whether the observed defect is actually caused by:

- missing pre-Task representation;
- failure to use existing `addition` or `loopback`;
- stale Mission Shared Context;
- insufficient Task materialization;
- external tracker state replacing canonical TPLAN state.

## Locally Pre-specified Decision Rule

Recommend a production TPLAN capability only if all of these hold:

1. The core fixture passes every control-boundary invariant.
2. Across both real Mission replays, destination-first discovery improves at least one
   tested recovery/decomposition outcome without worsening Task precision, authority,
   completion correctness, or auditability.
3. The improvement is unique relative to Variant B, not merely relative to eager task
   materialization.
4. At least one replay shows that a derived/narrative representation is insufficient
   even when it is correctly maintained; operator failure alone is not enough.
5. The design does not require Fog to become a Task state, does not add a competing
   objective, and does not let a script make a semantic decision.

If rules 1-2 pass but rules 3-4 fail, do not change the core runtime or Task schema.
Retain only a documentation/template finding or a bounded experimental helper.

If rule 1 fails, reject the capability shape.

## Claim Ceiling

The trial can establish only whether the representation is useful for these fixtures
and replays. It cannot establish general planning superiority, production concurrency
safety, semantic correctness, or independently verified historical replay facts.
