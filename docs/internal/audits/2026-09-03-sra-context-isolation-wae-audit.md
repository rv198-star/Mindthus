# SRA Context-Isolation WAE Audit

Date: 2026-09-03

Issue: #157

Branch: `feat/sra-context-isolated-runtime`

Audit focus: Workflow / Agentic / Evidence ownership

Verdict: **PASS WITH ISOLATION CLAIM CEILING**

## Audit Question

Does the SRA Phase 1.5 design put deterministic process control, semantic allocation
judgment, evidence constraints, and execution authority in the correct owners while
allowing SRA to make a relatively independent judgment?

This audit evaluates control ownership. Runtime tamper resistance and stage integrity
are evaluated separately in the companion runtime-integrity audit.

## Independence Boundary

SRA cannot be context-free. It needs the current objective, target threshold, risk
floor, decision owner, shared scarce resource, candidate cards, evidence, assumptions,
and current-state costs.

The required independence is narrower and operational:

> The context that created, defended, or prolonged the active task must not silently
> control the allocation judgment. Only explicitly admitted, typed, provenance-bearing
> decision context may enter the judge packet.

This is relative independence, not a claim that a model has no hidden platform context
or that the outer caller found every relevant candidate.

## WAE Classification

The SRA control surface has:

- high workflow certainty: admission, normalization, stage order, hashes, reference
  validation, carrier generation, and rendering are stable and repeatable;
- low semantic certainty: necessity, feasibility, contraction break points,
  replenishment value, switching-cost importance, and final allocation remain
  contextual judgments;
- evidence-sensitive claims: every factual or state-bearing reason must be bounded by
  evidence or an explicit assumption.

The correct quadrant is therefore:

```text
fixed Workflow shell
+ Agentic semantic owner
+ Evidence bridge
```

A pure prompt leaves deterministic order and isolation discipline to Agent memory. A
priority algorithm would move uncertain semantics into Workflow. Both are controller
mismatches.

## Confirmed Ownership

### Workflow owns

- context kind validation and admission policy;
- admitted, quarantined, and excluded ledgers;
- mandatory current-instruction anchor;
- protection against excluding current user constraints and authority;
- stable candidate IDs, anonymous aliases, and input-order-independent ordering;
- filtering state-only and unused evidence from judge packets;
- packet-specific JSON output schemas;
- raw input, admission, packet, judgment, and receipt hashes;
- the `prepared -> blind_recorded -> finalized` state machine;
- reference and stage validation;
- fresh-context carrier artifacts;
- final user-readable rendering.

### Agentic owns

- whether supplied context was classified semantically correctly;
- whether the candidate surface is sufficient;
- hard-gate applicability;
- target feasibility and necessity;
- contraction and the first break point;
- replenishment and next meaningful tranche;
- whether switching cost, reusable assets, remaining cost, commitments, or authority
  justify changing the blind result;
- the final allocation recommendation.

### Evidence owns

- source statements and observation time;
- claim ceilings;
- explicit assumptions and overturn conditions;
- evidence and assumption references on candidate and state records;
- observable carrier receipts when a host can provide them.

### Outer caller owns

- collection of raw candidate and source material;
- execution authority;
- project or TPlan mutation;
- final human-owned decisions when authority requires them.

## Findings And Root-Cause Repairs

### W1 — Stable Process Was Previously Left To Agent Memory

Before Phase 1.5, the Agent had to remember context admission, candidate symmetry,
contraction, blind separation, state reconciliation, authorization bounds, and final
rendering from method prose.

Repair:

- added a deterministic preparation command;
- added stage-bound judgment recording;
- added an integrity checker and renderer;
- kept semantic decisions outside the scripts.

Status: **FIXED**.

### W2 — Current Context Could Have Been Silently Reframed By The Collector

A generic exclusion lane could have allowed the outer caller to remove the current
instruction, current user constraint, or authority decision before judgment.

Repair:

- every applicable run requires at least one `current_instruction`;
- current instruction, current user constraint, and authority context cannot be
  explicitly excluded;
- user constraints remain constraints and do not become factual evidence;
- historical context requires explicit scoped admission plus evidence or assumption
  support;
- previous conclusions, candidate advocacy, and ambient inference remain quarantined.

Status: **FIXED**.

### W3 — Active-Path Context Had An Incumbency Advantage

The current task normally has richer text, stronger recency, known identity, and more
historical narrative than alternatives.

Repair:

- candidate cards use one common shape;
- blind aliases are generated from deterministic neutral content ordering;
- original IDs, titles, active identity, switching cost, remaining cost, reusable
  assets, commitments, authority state, and historical spend are withheld from the
  blind pass;
- context asymmetry produces a warning rather than a priority conclusion.

Status: **FIXED**.

### W4 — State Reconciliation Could Have Become A Second Unbounded Judgment

A state-aware Agent could otherwise discard the blind result by citing the active path,
historical effort, or unsupported state prose.

Repair:

- the blind result is recorded and hashed before the state packet exists;
- an unchanged result must preserve the blind floor and replenishment choice;
- a changed result must cite registered state IDs of the matching kind;
- a changed result requires non-identity, non-sunk substantive state references;
- every switching-cost, reusable-asset, remaining-cost, commitment, authority, and
  historical-spend state item is evidence- or assumption-bound;
- sunk cost is visible only through `sunk_cost_rejected` and cannot justify continuing.

Status: **FIXED**.

### W5 — Stronger Isolation Could Have Become A False Platform Claim

A same-context Agent cannot prove that it forgot the ambient conversation. A carrier
label also cannot prove that a host supplied no hidden context.

Repair:

- `packet_bound` is always labelled logical isolation;
- Full or contamination-pressure use of explicit `packet_bound` requires an
  `isolation_override_reason` and retains a degraded-isolation warning;
- fresh carriers without a persisted receipt remain declared, not verified;
- carrier receipts prove only an observable artifact was recorded;
- the final decision states that hidden host context remains outside the proof boundary;
- final isolation claims are recomputed from recorded carriers and receipts.

Status: **FIXED**.

### W6 — Workflow Was Prevented From Taking Semantic Authority

The new runtime does not contain a ranker, ROI engine, necessity classifier, or automatic
project mutation.

Scripts can reject malformed or unbound judgment artifacts, but they cannot decide that
a candidate is truly necessary, that a bundle is sufficient, or that an allocation is
correct.

Status: **PRESERVED**.

## Neighbor And Runtime Boundaries

- 3L5S still owns candidate definition and decomposition.
- EDSP still owns unstable proposition structure.
- SELA still owns long-term system-efficiency direction.
- MPG still owns carrier and path posture for one selected mainline.
- WAE owns this controller-boundary design, not allocation semantics.
- TVG still owns value gain inside one bounded artifact.
- Anti-Spiral supplies a brake; SRA allocates released resources once.
- TPlan still owns Mission state, Pulse arbitration, continuation, authority, recovery,
  and mutation.

No change was made to:

```text
skills/tplan/resources/hooks.md
skills/tplan/resources/schema.md
skills/tplan/scripts/tplan_runtime.py
```

## Evidence

```text
SRA context-isolation tests             28 PASS
Test Lifecycle executable coverage      72 / 72
full unittest suite                      920 PASS, 5 skipped
Python compileall                        PASS
release-pack all-platform build          PASS
SRA entry size                           9,983 / 10,240 bytes
TPlan runtime-control diff               EMPTY
```

A generated clean Codex carrier reached the model transport from an empty read-only
workspace and failed with HTTP 401 because the OCI node had no usable API credential.
No semantic judgment was produced. This is not counted as live isolation evidence.

## Claim Ceiling

Supported:

> SRA now has a deterministic Workflow shell that admits and normalizes context,
> separates blind and state-aware Agentic judgment, binds load-bearing state to evidence
> or assumptions, and prevents recorded carrier metadata from overstating isolation.

Unsupported:

- the outer caller supplied every relevant candidate or fact;
- the context kinds were semantically classified correctly;
- a fresh host had no hidden system context;
- the Agent selected the objectively correct priority;
- two-stage isolation guarantees unbiased judgment.

## Verdict

- Hybrid Workflow + Agentic + Evidence architecture: **PASS**.
- Relative-independence contract: **PASS**.
- Semantic allocation authority remains Agentic: **PASS**.
- TPlan ownership isolation: **PASS**.
- Live fresh-context semantic qualification: **PENDING due OCI authentication**.
