# Mindthus 2.0 Beta.2 — Decision Completeness Reset

Status: `R3-candidate / design-only / round-3 remediation pending confirmation`

This is not `v0.7`, not an execution protocol, and not authorization for Generator,
Judge, A/B, release, publication, or Stable migration work. R3-candidate applies the
two root fixes found by the third and final six-audit round; only targeted confirmation
of those fixes may change its status.

## Core — what this design guarantees

The old program repeatedly confused three different questions:

1. Did an event or artifact exist?
2. Is it eligible to support this particular claim?
3. Does eligible product evidence prove or refute the Thin-Kernel route?

This reset keeps them separate:

- one append-only event ledger retains raw facts;
- one frozen dependency matrix determines claim-local eligibility; and
- one reducer issues `PASS`, `REFUTED`, or `UNRESOLVED` certificates over a closed
  workload and its full uncertainty set.

Every terminal state produces exactly one absorbing program action:

1. `CONTINUE_BETA` — every critical claim has an eligible `PASS` certificate;
2. `STOP_ROUTE` — at least one critical claim has an eligible product-evidence
   `REFUTED` certificate; or
3. `STOP_UNPROVEN` — no legal path to a decisive certificate remains inside the frozen
   scope, deadline, evidence, or authority.

There is no terminal Hold, live amendment, semantic-resampling branch, or human
semantic adjudication in the minimal core. Judge disagreement is an uncertainty set;
if the route action is not invariant across it, the claim remains unresolved. William
retains policy, exposure, stop, and successor-program authority, not a runtime role that
repairs missing semantic evidence.

Decision completeness is a reduction guarantee over a recoverable ledger, not a claim
that software can emit an action while the host and all storage are permanently
unavailable. On first recovery after the deadline, the same frozen ledger prefix must
reduce to the same terminal receipt.

## Discovery — evidence-backed reset premise

The v0.3–v0.6 runs settled `9,111,203` counted tokens but retained only four committed,
Judge-backed triplets—two from v0.5 and two from v0.6—with no route-wide result.

The reusable failures were:

- real scope or external dependencies were frozen before they were available;
- known Codex/API omissions were made global vetoes;
- partial, expensive, or tool-heavy product behavior was relabeled infrastructure;
- shared isolation and Judge-evidence defects were localized to observed symptoms;
- projections competed with the immutable event history;
- model context size was mistaken for cumulative call usage; and
- each new fact produced another protocol/amendment instead of a terminal decision.

The detailed v0.1–v0.6 reconstruction and round-1 dispositions are preserved in
`audits/decision-reset/ROUND-1.md`. This reset does not rewrite those historical
contracts.

## Definition — the falsifiable design problem

The architecture is not decision-complete if any of the following is possible:

- a retained fact disappears from every applicable claim without a mechanical
  eligibility reason;
- missingness, corrupted lineage, or an unrun future slot produces `STOP_ROUTE`;
- a real product regression is hidden by an over-broad infrastructure `unknown`;
- event order, late settlement, fixed arm position, or complete-case selection changes
  the terminal action;
- qualification uses capabilities or authority the current Codex surface does not
  expose;
- two sources of truth disagree about reservation, settlement, or eligibility; or
- a reachable state requires a new runtime branch, version, or budget expansion.

Resolution requires a deterministic replay of every historical and audited novel fault,
one closed authority calculation, and one unique terminal action from every recoverable
ledger prefix.

## Mainline — the minimal sufficient program

### 1. Authority exists before calls, not after them

Before `QUALIFYING`, there is no active program and no model-call authority.

The user must first provide a trusted **qualification authorization** that binds:

- program and draft-charter digests;
- model alias, reasoning effort, Codex surface, and claim ceiling;
- candidate A plus at most one aggregate correction B;
- A+B combined call, local-time, concurrency, and accepted tail-exposure limits;
- the allowlist of surfaces B may change;
- the program cutoff; and
- no formal arm sampling, release, or publication authority.

Qualification calls use the same reservation rules as later calls. A ledger records
authority; it does not create or retroactively expand it.

After qualification and calibration, formal execution requires a separate trusted
**formal authorization**. It binds the final adapter and charter digests, closed slot
universe, superblocks, reducer/threshold digest, remaining cumulative exposure, model
configuration, cutoff, and stop authority. Qualification consumption is never reset or
retrospectively approved.

Calibration has two distinct outputs:

- a mechanical validity receipt proving the closed workload, discrete thresholds,
  uncertainty rules, and satisfiability checks are internally coherent; and
- a policy receipt recording William's chosen burden of proof and trade-offs.

Neither output is empirical evidence. Formal exposure approval is a separate capability;
one receipt type cannot substitute for another.

### 2. Keep five phases and one event ledger

```text
QUALIFYING
  -> CALIBRATING
  -> READY_FOR_AUTHORITY
  -> FORMAL_RUNNING
  -> TERMINAL
```

Any phase may become quiescent when its legal work, deadline, or authority is exhausted.
It enters `TERMINAL` only after the single decision prefix is sealed. `FORMAL_RUNNING`
may then end `STOP_ROUTE` or `CONTINUE_BETA` when the corresponding certificate exists;
otherwise it ends `STOP_UNPROVEN`.

There is exactly one durable, append-only event ledger/WAL. It stores only source facts:

- authorization and policy receipts;
- reservation and request-start records;
- raw stream chunks and event IDs;
- local lifecycle and client-visible provider lifecycle events;
- dependency, isolation, cache, and environment receipts;
- cancellations and settlements when actually exposed;
- original Generator outputs and derived Judge-view source bindings;
- Judge replica outputs; and
- decision-cut seals and terminal receipts.

Typed attempts, usage intervals, eligibility, claim states, exposure totals, and run
state are deterministic disposable projections. They are never parallel ledgers or
persisted sources of truth. Only the terminal receipt is a durable derived certificate,
and it binds the exact ledger-prefix and reducer digests.

### 3. Replace a generic dependency graph with a static matrix

The frozen matrix has rows of:

```text
claim/subclaim × dependency node × scope × required status
```

Scopes are closed: `program/common`, `case`, `superblock`, `cell`, and `event`.
Corrupt or unknown shared facts propagate to all and only dependent axes at that scope.

Required nodes include charter/stimulus identity, adapter/event grammar, live-service
regime facts, arm realization, wrapper/tool inventory, native isolation, capture and
settlement, Judge transform/schema/runtime, and axis-specific evidence capsules.

The product handoff is explicit:

- **before handoff:** canonical prompt, case digest, cwd/project snapshot, offered-tool
  inventory, cache seed, and carrier/config receipts are shared infrastructure;
- **after handoff:** arm-selected owners, methods, tool/path requests, retries, and
  answer choices are product behavior; and
- every tool hop has separate `arm_request` and `execution/result` nodes.

A carrier correctly denying a forbidden arm request is not carrier corruption. The
request remains owner/authority evidence; repeated arm requests through the cutoff can
be completion and cost evidence. A wrong project snapshot or offered-tool inventory
caps downstream axes only at its actual scope; it does not erase earlier arm requests
or every historical epoch.

Retention is unconditional. Eligibility is per matrix row. If a dependency fact cannot
be proven, it is `unknown`; workflow and reducer do not guess causal scope.

### 4. Qualify one coherent adapter through five bundles

Every qualification receipt binds one candidate digest covering the client binary,
configuration, event grammar, capture/WAL implementation, tool inventory, schemas,
cache seed, view/capsule rules, isolation, scheduler, and reducers.

The single qualification manifest contains five bundles:

| Bundle | What it proves |
| --- | --- |
| `LIVE_INTERFACE` | actual successful Generator lifecycle, enabled tool/event envelope, terminal reported usage, accepted Judge schema, and client-visible identities |
| `DETERMINISTIC_FAULT` | adapter handling of empty/failure shapes, half-lines, duplicates, out-of-order and unknown events, local timeout, parent crash, late final/settlement, and conflicting records |
| `INTEGRITY` | native isolation, canonical cache seed/write-set, label-deidentified view trace, fixed evidence-capsule coverage, and no online Judge tools/discovery |
| `RECOVERY_AUTHORITY` | replay-confluent folds, reservation/release rules, complete-superblock guard, decision-cut seal, terminal compare-and-set, and crash recovery |
| `JUDGE_CALIBRATION` | the correlated Judge family handles preregistered historical counterexamples, including shared missing evidence and equivalent claims, within the declared ceiling |

`LIVE_INTERFACE` is real service evidence. Deterministic adapter faults prove how the
adapter handles a state if observed; they do not pretend the provider was forced to
produce it. Real success plus deterministic failure injection is required; neither
substitutes for the other.

There are at most two candidates. A runs the full manifest. After all A failures are
known, B may make one aggregate correction limited to preauthorized transport,
capture, parser, durability, or scheduler surfaces. Changing an arm, task prompt,
estimand, product claim, threshold policy, evidence policy, or workload is not B; it
ends `STOP_UNPROVEN`. B reruns the full manifest under one digest. No A pass is spliced
into B.

If the final adapter cannot expose a required capability, the design either lowers the
claim before formal freeze or stops unproven. A missing provider ability is never filled
by a green local fixture.

### 5. Define the estimand, slot universe, and superblock before sampling

The estimand is behavior of the frozen arms on the named live Codex model alias and
reasoning effort during one bounded, recorded service window. It is not behavior under
one cryptographically pinned backend build; current Codex does not expose that proof.

This is a **fixed-cohort exploratory policy decision**, not population inference. It
does not claim p-values, power, or generalization beyond the frozen visible workload.

Calibration freezes:

- every case, repeat, arm, Judge slot, workload stratum, and analysis weight;
- a positive minimum planned denominator for every axis;
- the full allowed outcome domain of each slot before the first call;
- the randomization seed and service-regime policy; and
- complete counterbalance superblocks.

One superblock contains the three repeats needed for each arm to occupy each serial
position once within the same workload stratum. Triplets are judged as they finish, but
route projections are evaluated only after a complete superblock. They remain
provisional until the decision cut. An incomplete superblock retains every raw
observation and cost but keeps position-dependent comparisons unresolved.

All future, unrun, interrupted, and ineligible slots remain in the closed universe with
their full allowed domains. They never disappear from a complete-case denominator.
Before the decision cut, even an all-world `PASS` or `REFUTED` projection is not a
certificate and cannot emit a terminal action. Sampling follows the frozen slot schedule
until it is complete or a frozen authority, stop, or cutoff guard prevents the next
start; it never resumes through an amendment.

Detectable client, alias, config, tool/catalog, adapter, or declared service-regime
change makes only the affected superblock ineligible unless the static matrix proves a
wider scope. Unobservable backend rollout remains an explicit live-service limitation
mitigated by counterbalanced order, not a claim of immutable-build causality.

Total observed cost and native uncached-input cost are separate surfaces. Uncached cost
is eligible only when the cache receipt is complete. The charter freezes whether a
detectable regime change is part of the estimator; this cannot be selected after seeing
arm results.

### 6. Fold events monotonically and replay-confluently

Before request send, workflow fsyncs the reservation. The qualified outbound primitive
then performs one linearized transition: recheck authorization and the unsealed cutoff,
append/fsync `request_start` against the current ledger head, and invoke the transport.
No later process may consume an old start intent. A crash after the durable start but
before provable sampling remains a conservative started/unknown attempt; only exact
proof of no sampling and zero usage permits the frozen retry. Raw binary chunks are
appended durably as received; parsing does not decide whether bytes deserve storage.

The fold keeps local and client-visible provider lifecycle orthogonal:

- local: started / running / timed-out / crashed / exited;
- provider-visible: unknown / running / terminal / interrupted / cancelled;
- user outcome: completed / noncompleted / unknown;
- content: final-nonempty / final-empty / progress-only / tool-only / none / unknown;
- per-resource exposure: a joint allowed set derived from reservations and settlements.

The ledger is fact-retentive and its fold is replay-confluent for the same event
multiset. Before the decision cut, derived eligibility and `Ω` may narrow or widen as
new facts arrive:

- exact duplicate event IDs are idempotent;
- later provider final may refine earlier progress and local timeout without deleting
  those facts;
- reconnect/error events do not override a later valid final and terminal usage;
- exact settlement intersects/narrows the reserved exposure set;
- incompatible exact events, empty interval intersections, or conflicting identities
  invalidate the affected scope mechanically; and
- after the decision prefix is sealed, late events are audit-only and cannot change a
  certificate.

Unknown event types are retained. Their conservative fanout is fixed by source
envelope: an unknown event in one attempt caps every axis that depends on that attempt;
an unknown shared adapter-grammar event closes new calls and caps the current
superblock; it does not automatically rewrite prior eligible superblocks.

Qualification must show that event reordering, duplication, crash recovery, and replay
produce the same projection and terminal candidate.

### 7. Use a frozen outcome matrix, not runtime causal stories

The complete implementation table is runtime support, but the main semantics are fixed:

| Observed state by decision cut | User outcome | Product axes | Comparison eligibility |
| --- | --- | --- | --- |
| final nonempty + valid dependencies | completed | delivered quality, owner/action, completion, cost | eligible for dependent axes |
| provider-terminal final empty or explicit product refusal/failure on an answer-required task, with no explicit infrastructure receipt | noncompleted | delivered quality `0`, completion `0`, cost | eligible for dependent product axes |
| progress/tool only, no final, valid handoff, no explicit shared/provider failure receipt | noncompleted | delivered quality `0`, arm requests/actions, completion `0`, cost | eligible as end-to-end product behavior in its balanced superblock |
| explicit provider 429/5xx/cancellation or shared capture/tool-service failure receipt, with or without prior progress/tool events | observed noncompletion/UX and cost retained | arm requests before the failure may remain eligible | downstream arm-completion contrast is ineligible |
| proven no sampling + zero usage | no product outcome | transport fact only | one frozen retry; exhausted slot remains unresolved |
| parent/capture crash or unknown sampling | raw bytes/cost interval retained | independently proven pre-crash arm requests may survive | downstream semantic/completion axes unresolved; no retry |
| final nonempty + unknown usage | completed semantic outcome | C1–C3 may proceed; cost set includes unknown tail | C4 unresolved unless bounded |
| Judge empty/refusal/failure | Generator facts unchanged | affected Judge axes unresolved | never converted to Generator failure |

Current Codex does not expose a stable, deterministically triggerable native refusal
type. Qualification therefore proves only the event shapes actually exposed; refusal
handling in fault fixtures proves reducer behavior, not provider capability.

The rows are mutually exclusive. An explicit frozen infrastructure receipt takes
precedence over generic terminal-empty/product-failure and progress-only predicates;
the complete event×axis table must prove exactly one base outcome per axis. The matrix
never asks workflow to infer why a service failed. Direct provider/shared receipts
determine infrastructure ineligibility. Otherwise the fixed live-service estimand,
handoff boundary, and balanced design determine end-to-end eligibility.

### 8. Reduce a joint uncertainty world, not separate convenient denominators

Each planned slot contributes an allowed set of joint values. The global uncertainty
set `Ω` preserves completion, delivered quality, owner/action axes, tokens, wall time,
tool hops, service regime, and Judge replica value sets together. Calibration may use a
conservative Cartesian envelope, but must say so before formal sampling.

Critical claims are:

| ID | Claim |
| --- | --- |
| C1 | Thin adds action-changing passive primitive recall beyond Direct-only |
| C2 | Thin preserves Stable delivered answer quality, completion, owner fidelity, and authority/evidence behavior |
| C3 | Thin stays asleep on near-negatives and arbitrates overlap correctly |
| C4 | Thin provides material user-cost value without unacceptable guardrail regression |

Delivered quality uses the fixed planned-slot denominator:

```text
delivered_quality = completion × final_quality
```

A noncompletion has delivered quality `0`; an ineligible/unknown slot retains the full
allowed domain. Final-only quality may be reported descriptively but is not a route
gate. This prevents completion-conditioned selection and Simpson reversals from making
C2 pass.

C4 uses a frozen per-slot cost vector and planned-slot aggregation. It does not divide
by completed answers. Let `C4_policy(ω)` include all guardrails and the material-benefit
rule in one possible world `ω`:

- material benefit requires one predeclared metric that satisfies its margin in every
  allowed world: `exists metric m, for every ω: benefit(m, ω)`;
- every mandatory guardrail must hold in every allowed world; and
- metric units, directions, ratios, zero/infinite rules, aggregation, and correlations
  are frozen in calibration.

For any critical claim `C`:

- `PASS` iff `C` is true in every `ω ∈ Ω`;
- `REFUTED` iff eligible product evidence makes `C` false in every `ω ∈ Ω`;
- otherwise `UNRESOLVED`.

Missingness, corruption, ineligible slots, and unrun future slots expand `Ω`; they never
create `REFUTED`.

Before formal authorization, the discrete real outcome domain must prove:

- `PASS ∩ REFUTED = empty`, with a frozen tie convention;
- exactly one of PASS/REFUTED/UNRESOLVED is emitted per claim;
- a joint all-pass witness and at least one reachable product-refutation witness exist;
- minimum denominators and full superblocks fit the closed slot capacity;
- pre-cut projections are replay-confluent for the same event multiset, while the one
  terminal certificate is computed only from a sealed prefix; and
- the initial empty ledger cannot emit a route action.

Unsatisfiable or resolution-insufficient parameters end `STOP_UNPROVEN` before formal
sampling.

### 9. Treat Judges as correlated replicas with no human repair path

Two Sol/xHigh sessions are two replicas of one scoring family, not independent truth
sources. Their outputs produce value sets:

- booleans become the returned allowed set;
- ordinal values become the returned closed set/interval;
- enums become the returned label set; and
- a missing replica contributes the full allowed domain.

No default averaging occurs. If the program action is invariant across the resulting
worlds, it may proceed. Otherwise the claim remains unresolved and eventually ends
`STOP_UNPROVEN`. There is no runtime human semantic packet or adjudication resume.

Each axis has a predeclared evidence-capsule contract bound to exact cell, epoch, source,
time, command/result coverage, and digest. Missing coverage makes the axis unknown even
when replicas agree. Verdicts cannot select an active evidence view.

Views are **label-deidentified**, not claimed fully blind. Only frozen, traceable,
semantics-preserving identifier transforms are allowed. Terminology leakage and
residual arm inference are separate observations. Judge tools, online discovery, and
evaluated plugins are removed at the transport/config layer.

### 10. Choose one honest authority mode

All authority events live in the single ledger. Guards are per resource dimension, not
one invalid scalar sum:

```text
for every hard resource r:
    settled[r] + outstanding[r] + next_superblock[r] <= limit[r]
```

Hard resources may include call starts, concurrency, and local wall time. Token/cost may
be hard only if the provider exposes a finite enforceable upper debit `U` and a trusted
settlement/cancellation path.

Current Codex exposes no proven provider request ID, billing lookup, cancellation
receipt, or cumulative per-turn token cap. Therefore calibration must choose one mode:

1. `STRICT_BOUNDED`: finite token/cost `U` is mandatory; absent that capability, end
   `STOP_UNPROVEN` before formal sampling.
2. `TAIL_ACCEPTED`: William explicitly accepts that a single started turn has no proven
   finite token tail. Calls, concurrency, and local time remain hard controls; tokens
   are a post-settlement stop target, not a hard ceiling. An unsettled/interrupted turn
   prevents another call and leaves its superblock unresolved through the cutoff.

No document may call mode 2 “hard token bounded.” Transparent WebSocket/HTTP fallback
and provider-attempt count remain unknown unless the interface exposes proof.

Before the first call of a superblock, every hard dimension reserves all nine Generator
positions, six Judge calls, and frozen retry allowance for the three counterbalanced
triplets. A target crossing cannot truncate a reserved superblock. If a call becomes
unsettled or an external stop interrupts the superblock, remaining calls do not start;
the partial superblock is retained but comparative claims remain unresolved.

A reservation is released only by the exact evidence supported by the chosen authority
mode. Killing the local client is not provider cancellation. Every decisive certificate
depends on valid qualification/formal authorization, start reservation, and applicable
settlement/tail-acceptance lineage.

### 11. Seal one decision prefix before producing one program action

The program cutoff is an absolute value in the authorized charter. There are exactly two
ways to seal the decision prefix:

1. the workflow reaches that absolute cutoff; or
2. a trusted William stop receipt explicitly closes it earlier.

A complete-superblock checkpoint cannot seal the prefix or emit a program action. At a
normal cutoff, workflow appends one decision-cut record with a compare-and-set against
`cut_absent + exact current source-head digest`. A source-event commit racing with that
cut is therefore linearized wholly before or wholly after it.

If the host was unavailable and the normal cut record is absent, first recovery seals
the greatest ledger prefix whose durable local commit receipt proves it was committed
no later than the authorized absolute cutoff. Any later or unprovably timed record is
audit-only; ambiguous commit-order integrity forces `STOP_UNPROVEN`. Remote timestamps
never move an event across the cut. Qualification must fault-test both normal and
recovery sealing.

Only source facts in the sealed prefix belong to the decision. No request may start
after the cut. This favors a local, testable boundary over unknowable network timing.

On the cut, or on first recovery when the cut should already exist, reduce exactly once:

```text
validate the decision cut, its sealed source prefix, and terminal slot

if a valid linearized terminal receipt exists:
    return that first receipt unchanged
else if a committed terminal conflict predates any valid terminal CAS
        or cut/prefix/reducer integrity is invalid
        or contract is unsatisfiable:
    candidate = STOP_UNPROVEN
else if any critical claim has REFUTED:
    candidate = STOP_ROUTE
else if every critical claim has PASS:
    candidate = CONTINUE_BETA
else:
    candidate = STOP_UNPROVEN

CAS the canonical candidate against:
    terminal_absent + exact decision-cut digest
```

The atomic, fsynced, compare-and-set terminal receipt is itself the program action.
User-visible display is an idempotent projection keyed by its content-derived receipt
ID; there is no separate “sent” phase. A torn or uncommitted terminal write is absent
and replays. Once a valid terminal CAS exists, later terminal-shaped or conflicting
bytes are audit incidents only and can never create a second action. If the receipt
bytes are damaged but the cut, sealed prefix, and successful linearization proof remain
recoverable, reconstruct the same content-derived receipt. Losing those recovery facts
with the durable store is outside the stated recoverable-ledger guarantee, not a reason
to append a second terminal action.

Qualification injects source events on both sides of the cut, crashes before/after the
cut and terminal CAS, torn writes, duplicates, conflicts, and damaged projections. A
committed terminal conflict that exists before any valid terminal CAS can only produce
the single canonical `STOP_UNPROVEN`; it can never yield a route claim.

Late settlement can narrow historical accounting and create an authority-incident
record, but cannot issue a second route action. This is allowed only when the original
call already had valid authority lineage under the chosen mode; otherwise the decisive
certificate was never eligible.

## Controller assignment

| Surface | Owner | Boundary |
| --- | --- | --- |
| source facts, order, WAL, reservations, isolation, cutoff, terminal CAS | Workflow | records and enforces mechanics; never judges semantics or provider cause |
| arm-selected answer/owner/tool behavior | Generator | product behavior after the frozen handoff |
| semantic scoring | correlated Judge replicas | frozen label-deidentified views and capsules; no tools or active-evidence choice |
| scientific shape and validity | charter + mechanical calibration checks | fixes closed cohort, estimand, domains, weights, predicates, and satisfiability; never uses formal outcomes |
| policy burden and exposure | William | approves target trade-offs, tail mode, calls/time, and stop; approval is not empirical proof |
| eligibility | static dependency matrix | propagates valid/corrupt/unknown facts at fixed scope; never guesses causality |
| claims and action | deterministic reducer | computes `Ω`, certificates, and one terminal receipt; never invents evidence |

## Guardrails and boundaries

- One ledger prevents reservation/settlement source drift.
- Derived truth remains disposable; stale projections cannot control decisions.
- Full superblocks prevent serial position from becoming the arm effect.
- A fixed slot universe prevents complete-case and future-slot omission bias.
- Delivered quality prevents conditional-final selection from hiding noncompletion.
- Joint uncertainty quantifiers prevent metric switching across possible worlds.
- Fixed evidence capsules prevent two agreeing replicas from sharing an invisible
  post-outcome repair.
- Strict versus tail-accepted authority makes unsupported token bounds explicit.
- A sealed decision cut plus terminal receipt is absorbing; no compatibility amendment or renamed continuation
  exists inside the program.

Claim ceiling:

- visible, fixed-cohort Codex/live-alias/same-Judge-family exploratory evidence only;
- no immutable-backend, hidden-set, Claude, cross-host, statistical-population,
  universal, release, migration, or production-readiness claim; and
- no implementation or semantic execution authority from this document.

## Successor-program boundary

An agent may never infer a successor from `STOP_ROUTE`, `STOP_UNPROVEN`, an open issue,
or “continue” language that does not explicitly authorize a new charter.

A successor requires a new trusted user receipt that references the prior terminal
receipt and a new charter digest. No budget, authority, adjudication, or evidence
eligibility transfers automatically.

- after `STOP_UNPROVEN`, the receipt must name the external fact that removed the exact
  blocker;
- after `STOP_ROUTE`, it must name a materially new route hypothesis/design delta and
  retain the old refutation as prior evidence; and
- more budget, a later deadline, a new seed, or a renamed program alone is not a
  material delta.

## Final replay acceptance before implementation discussion

The frozen replay manifest must cover at least:

- v0.1 valid-but-unused scope change; v0.2 absent custodian; v0.3 missing endpoint;
- v0.4 progress-only timeout, shared isolation failure, and shared Judge-evidence
  omission;
- v0.5 schema rejection, namespace view, and stale resume snapshot;
- v0.6 successful 265,154-token Stable tool loop;
- normal empty/failure output, explicit provider 5xx after progress, and a valid carrier
  denying an arm-selected sibling read loop;
- wrong workload at each scope and a valid-hash but insufficient evidence capsule;
- candidate A/B pass splicing and pre-qualification self-authorization;
- third-position throttling across a full counterbalance superblock;
- future-slot omission, completion-composition swap, and C4 metric switching;
- local timeout followed by late provider final, duplicate/out-of-order/unknown events,
  parent crash, and zombie settlement;
- request-start/cutoff races, decision-cut/terminal crash windows, terminal conflicts
  before and after valid CAS, and late facts;
- explicit provider 429/5xx after progress versus product-terminal empty/failure
  precedence; and
- strict-bounded capability absence plus tail-accepted lineage.

For every fixture, the test asserts raw retention, matrix eligibility, uncertainty-set
effect, legal next transition, authority effect, and unique terminal candidate. The
fixture manifest and full event×axis table are runtime support, not a second methodology
in the main design.

## Resolution — final audit only

The six round-3 audit tasks found two root defects: premature terminal absorption before
the decision prefix was sealed, and overlapping outcome predicates for explicit
infrastructure failures. R3-candidate removes the early terminal path, linearizes the
cut before reduction, fixes terminal-conflict priority, and makes outcome predicates
mutually exclusive. These are local reductions, not a new protocol layer.

Round 3 closes only after the reviewers who raised those blockers confirm that every
submitted fault now has a deterministic treatment, the worst-case authority calculation
still closes under the selected mode, and no path requires a live version, amendment,
or implicit successor.

If the design passes, the result is still a reviewed design—not permission to implement
or run it. William decides separately whether the expected information value justifies
the remaining complexity and exposure.
