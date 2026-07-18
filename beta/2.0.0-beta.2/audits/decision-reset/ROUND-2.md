# Decision Completeness Reset — round 2 audit record

## Frozen input

- Revision: `R1`
- Design SHA-256:
  `34f8736d48c1d6ecfd43381dfe77c338fa6112870b3e1a5a50ec5b34ac50c4fd`
- Independence: six read-only reviews of the same frozen R1; two isolated waves of
  three; no R1 edit occurred until all six final reports were returned. Reviewers were
  told not to read same-round reports or modify files.
- Platform limitation: the environment permits only a bounded cumulative set of child
  sessions. R2-A6 therefore reused one completed round-1 session for a new, isolated
  audit turn. It did not receive other round-2 reports. Its judgment is independent of
  same-round findings, but it is not a fresh reviewer identity; this limitation is part
  of the evidence record rather than silently relabeled as stronger independence.
- Semantic Generator/Judge calls: `0`

## Reviewer verdicts

| Reviewer | Independent focus | Verdict | Confidence |
| --- | --- | --- | ---: |
| R2-A1 | state-machine fault injection and event-order replay | BLOCK | 0.94 |
| R2-A2 | product behavior versus infrastructure failure | BLOCK | 0.95 |
| R2-A3 | denominators, estimand, and evidence sufficiency | BLOCK | 0.94 |
| R2-A4 | current Codex operational feasibility | BLOCK | 0.94 |
| R2-A5 | authority, deadline, and terminal governance | BLOCK | 0.94 |
| R2-A6 | anti-spiral deletion and minimal control surface | PASS-WITH-MAJORS | 0.92 |

Round result: `BLOCK / materially redesign before round 3`.

## Finding dispositions

Audits are union-based. Every blocker and major finding below changed R2 or narrowed
its claim. None was dismissed by majority vote.

### R2-A1 — event and state fault injection

| Finding | Level | Disposition | R2 change |
| --- | --- | --- | --- |
| R2-A1-F1 | BLOCKER | accepted-fixed | added an order-independent fold over orthogonal local, provider, parse, and output-stage dimensions; later provider facts refine rather than overwrite earlier lifecycle facts |
| R2-A1-F2 | BLOCKER | accepted-fixed | defined a fixed ledger cutoff, terminal compare-and-set, crash recovery, and the terminal receipt itself as the single atomic program action |

### R2-A2 — product/infrastructure boundary

| Finding | Level | Disposition | R2 change |
| --- | --- | --- | --- |
| R2-A2-B1 | BLOCKER | accepted-fixed | added a closed event-combination × axis matrix distinguishing refusal, progress-only, normal empty output, provider fault, client fault, and local timeout |
| R2-A2-B2 | BLOCKER | accepted-fixed | made the product handoff explicit and split every tool hop into `arm_request` versus `execution/result` dependencies |
| R2-A2-M1 | MAJOR | accepted-fixed | declared the live-alias service-window estimand and made cache/service-regime facts scoped dependencies rather than invisible nuisance assumptions |

### R2-A3 — denominators and evidence

| Finding | Level | Disposition | R2 change |
| --- | --- | --- | --- |
| R2-A3-01 | BLOCKER | accepted-fixed | froze a closed universe containing all planned future slots; an unrun slot is retained as missing rather than disappearing from the denominator |
| R2-A3-02 | BLOCKER | accepted-fixed | replaced final-only quality analysis with joint delivered outcome, `completion × final_quality`, so completion selection cannot create a favorable quality subset |
| R2-A3-03 | BLOCKER | accepted-fixed | defined one joint uncertainty world set and changed C4 to `exists one metric m such that for every admissible world omega` the bound passes |
| R2-A3-04 | BLOCKER | accepted-fixed | replaced a three-call triplet with a counterbalanced superblock in which every arm occupies every serial position once; checkpoints occur only after a complete superblock |
| R2-A3-05 | BLOCKER | accepted-fixed | made `PASS`, `REFUTED`, and `UNRESOLVED` disjoint, added tie behavior and monotonic endpoint rules, and required pre-call satisfiability witnesses |

### R2-A4 — current Codex feasibility

| Finding | Level | Disposition | R2 change |
| --- | --- | --- | --- |
| R2-A4-F1 | BLOCKER | accepted-boundary | current Codex cannot prove provider request identity, cancellation, exact settlement, or a finite post-timeout cumulative-token bound; R2 now permits only `STRICT_BOUNDED` with finite exposed bounds or explicitly authorized `TAIL_ACCEPTED`, and forbids a hard-cap claim in the latter |
| R2-A4-F2 | BLOCKER | accepted-fixed | split real `LIVE_INTERFACE` qualification from `DETERMINISTIC_FAULT` injection; fixtures prove adapter behavior, never provider behavior |
| R2-A4-F3 | BLOCKER | accepted-fixed | required pre-send durable reservation and streaming WAL chunks rather than retaining evidence only in parent memory until child completion |
| R2-A4-F4 | BLOCKER | accepted-fixed | changed reservation, scheduling, and analysis from triplets to complete counterbalanced superblocks |
| R2-A4-F5 | BLOCKER | accepted-boundary | removed runtime human semantic adjudication from the minimal program; outer authorization and stop receipts still require a trusted conversation principal and cannot be synthesized by the runner |

### R2-A5 — governance and authority

| Finding | Level | Disposition | R2 change |
| --- | --- | --- | --- |
| R2-A5-01 | BLOCKER | accepted-fixed | qualification now requires its own prior authorization; qualification evidence cannot retroactively create call authority |
| R2-A5-02 | BLOCKER | accepted-fixed | separated mechanical calibration validity, policy choice, qualification exposure, and formal exposure into non-substitutable receipt capabilities |
| R2-A5-03 | BLOCKER | accepted-fixed | fixed the program cutoff before calls and made terminal action an atomic compare-and-set over one ledger prefix; late facts are archival only |
| R2-A5-04 | BLOCKER | accepted-fixed | every decisive certificate carries authority lineage to the exact trusted receipt and cannot inherit authority from an unauthenticated event or runner-created record |
| R2-A5-05 | BLOCKER | accepted-fixed | added a successor-admission rule: the same estimand, workload, failure, or evidence gap cannot restart under a renamed program without a new falsifiable information-gain claim and separate authorization |

### R2-A6 — anti-spiral deletion

| Finding | Level | Disposition | R2 change |
| --- | --- | --- | --- |
| R2-A6-01 | MAJOR | accepted-fixed | collapsed authority, lifecycle, and evidence history into one append-only event ledger; no parallel authority ledger remains |
| R2-A6-02 | MAJOR | accepted-fixed | made typed states, eligibility, exposure, and run status disposable projections; replaced a mutable dependency graph with one static matrix |
| R2-A6-03 | MAJOR | accepted-fixed | removed human semantic repair, disagreement adjudication, and runtime amendment branches; non-invariant Judge worlds remain unresolved |
| R2-A6-04 | MAJOR | accepted-fixed | replaced a scalar budget gate with resource-specific call, time, concurrency, token, and outstanding-tail guards; one resource cannot silently authorize another |

## Novel scenarios added to the replay set

- local timeout followed by a valid provider final and then an unknown event;
- crash between terminal eligibility and durable terminal receipt;
- refusal, progress-only, normal-empty, provider-fault, client-fault, and timeout
  combinations scored on different axes;
- provider final quality observed only for the easiest completions;
- an arm permanently occupying the service-throttled third serial position;
- locally injected provider-like faults being mislabeled as live-provider evidence;
- parent death after sampling while raw chunks exist only in memory;
- a user-input event without a trusted William principal being treated as authority;
- a qualification call made before any exposure authorization; and
- the same failed program restarted under a new version label without new information.

## Material R2 changes

R2 is a control-model simplification despite being more explicit at the boundary:

1. one source ledger replaces competing runtime truth stores;
2. an orthogonal event fold replaces named-error precedence patches;
3. a static dependency matrix replaces causal guessing;
4. five coherent qualification bundles separate live facts from deterministic fixtures;
5. a closed slot universe and counterbalanced superblock prevent denominator and order
   selection;
6. one joint uncertainty set and delivered-outcome metric prevent Judge and completion
   cherry-picking;
7. resource-specific authority modes state what current Codex can and cannot bound; and
8. no human semantic repair or version-amendment center remains inside runtime.

## Round output

- Revision: `R2`
- Design SHA-256:
  `b9d55d5faee7bf3e4ec6c399f34bd9e31ebd6f3b1614a0734ae01be2c8590b2f`
- Next allowed action: freeze this exact R2 and obtain six round-3 adversarial audits.
  No Generator, Judge, A/B, release, or implementation work is authorized.
