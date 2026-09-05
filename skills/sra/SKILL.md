---
name: sra
description: "Use directly when multiple already-judgeable actions or bundles compete for one named scarce resource; choose the current floor and next meaningful tranche. Default Lite; use Full for explicit bundles, multiple resource constraints, fixed thresholds, or major commitments. Do not use with missing comparison facts/resource, or for one selected mainline's carrier, exposure, timing, or exit."
---

# SRA / Scarce Resource Allocation / 稀缺资源优先分配

## Core Claim

> 以足够低的判断成本，先保护目标成立所必需的投入，
> 再把下一份资源分给当前风险调整后边际价值最高的用途。

“先生存、再图强” means viability before optional improvement, under the user's real
goal, time horizon and protected constraints. SRA ranks work, not the worth of people.

Execution shorthand:

> 收缩找出不能删的；回补决定下一份值得加的。

SRA allocates a shared scarce resource among sufficiently judgeable work. It is an
evidence-bounded judgment, not a universal score or optimizer.

## Mainline

### Entry And Analysis-Cost Gate

Choose one entry outcome:

- `direct`: one required next action exists, no credible competing use of the same
  resource exists, or direct trial is cheaper than analysis;
- `lite`: one bounded action, resource tranche, or named checkpoint is enough;
- `full`: explicit candidate bundles, multiple constrained resources, fixed thresholds,
  direction-changing uncertainty, or a major/hard-to-reverse commitment is load-bearing;
- `blocked`: allocation would require inventing a target, authority, shared resource,
  candidate contribution, evidence, question projection, or risk boundary.

`auto` starts from Lite and expands only under named escalation conditions. It is a mode
selector, not a third reasoning mode.

Use a depth whose cost is lower than the plausible avoidable loss from a wrong allocation.
Stop when more analysis is unlikely to change the next action enough to repay its cost.
A seconds-long irreversible action can warrant more review than a long reversible task.

### Allocation Frame

Lock the smallest sufficient frame:

```text
parent_objective
target_threshold
time_window
risk_floor
decision_owner
resource_pools[]
evidence_ceiling
```

Each resource pool has a stable `resource_id`, a decision window, capacity, and one
quantity contract:

- `measured`: exact or bounded amount with additive `sum`;
- `ordinal`: one ordered level with `exclusive` allocation;
- `indivisible`: named blocks with block-set allocation.

Do not translate unlike resources into one synthetic score.

### Candidate Horizon Probe

Scan only far enough to avoid active-task capture:

1. current path;
2. hard gate, blocker, or threshold-essential predecessor;
3. direction-changing unknown, irreversible risk, or closing opportunity;
4. strongest feasible alternative serving the same objective;
5. maintenance, reserve, defer, and stop postures.

Lite normally keeps two to four actionable candidates. Full expands only when bundle or
resource-channel structure requires it.

Candidate cards carry observable action, effect, demand, dependency, window, downside,
reversibility, evidence, and assumptions. Inputs do not pre-label priority, ROI,
hard-gate status, necessity, or another SRA role.

### Priority Order

1. Protect the minimum sufficient support for the declared target, authority and risk
   floor. Test necessity by what would break if that support were removed.
2. Compare risk-adjusted bundle value and the marginal value of meaningful additional
   resource commitments among feasible alternatives. Dependencies constrain executable
   order; direction tests, bottlenecks and windows are sources of value, not automatic
   priority labels.
3. Commit only worthwhile tranches. Keep justified maintenance or reserve, and explicitly
   defer or stop displaced work. Reconsider when relevant evidence or resources change.

Compare fixed or indivisible thresholds as complete meaningful tranches. Unknown value is
not zero; delayed benefits, learning, care, reliability and options count under the chosen
horizon. No universal numeric ROI score or mandatory utilization target is required.

### Lite

Lite runs the shared method core once: lock the frame, probe candidates, run one
`micro-contraction` to expose the current floor, then one `micro-replenishment` to choose
the next meaningful tranche. Separate future switching cost from sunk cost and set the
ceiling, horizon, displaced-work posture, and rerank trigger.

Lite uses:

```text
one_action | one_tranche | until_named_checkpoint
```

A Lite result without both contraction and replenishment is ordinary prioritization, not
complete SRA fidelity.

### Full

Full expands the same logic across explicit bundles and resource channels. It records
bundle assessments, removes infeasible or dominated bundles, runs Resource Contraction
and Resource Replenishment, selects one feasible or conditional non-dominated bundle,
and records the ledger, tranche, reserve, ceiling, and authorization boundary.

Full may use `bounded_decision_window` in addition to Lite horizons. It must not merely
produce a longer Lite explanation: explicit bundle members and bundle assessments are
required.

### Allocation Ledger And Outcome

Every candidate receives exactly one posture in the current window:

```text
floor | maintenance | candidate | defer | stop
```

`floor` and `maintenance` carry nonzero current allocation. `candidate`, `defer`, and
`stop` carry zero. The next tranche is separate from current allocation.

`allocate` authorizes the typed tranche; `conditional` waits for its named condition;
`infeasible`, `blocked`, and `request_missing_context` authorize no target-reaching work.

### Stop

Lite stops after one bounded allocation and rerank trigger. Full stops when the selected
bundle is stable across adjacent realistic pressure, the first tranche is clear,
remaining uncertainty cannot change the current action, and another analysis round has
no named positive-value hypothesis.

## Guardrails

### Protect The Target Threshold

Keep the requested target and risk floor fixed during contraction. A cheaper survival
state becomes valid only through an explicit authorized target change. Necessary work
receives sufficient support, not unlimited investment. If resources cannot support the
floor, expose the infeasibility and the decision needed; do not silently lower the target.

### Preserve The Real Objective

This guardrail prevents short-term, measurable gains from replacing the user's goal.
Use the declared horizon and affected-party constraints; protect safety, dignity, care,
commitments and sustainable capacity where they bind the decision. High expected gain
cannot buy a breach of a hard boundary. Low-confidence benefits may justify a bounded
probe, not automatic rejection or unlimited speculative spending.

### Protect Small But Decisive Actions

Keep direction tests, bottleneck removal, irreversible-risk prevention, and option
creation visible. This does not make every small task critical.

### Judge Bundles Before Isolated Tasks

Preserve complementarity and fixed thresholds, then test every claimed member through
contraction. A weak component cannot hide inside a large bundle.

### Preserve Partial Orders

Dependency, parallel resources, threshold effects, and uncertainty may justify parallel
or conditional allocation. Do not force a total ranking.

### Separate Switching And Sunk Cost

Compare future consequences from the current state. Historical spend never proves that
continuation is best.

### Keep Workflow Deterministic

Workflow validates references, resource contracts, each candidate's cumulative current
plus next-tranche demand, bundle membership, posture consistency, capacity, ceilings,
state transitions, and typed disagreement. It
does not decide semantic necessity, risk acceptance, bundle sufficiency, strongest
alternative, or priority.

## Boundaries

- `3L5S` defines or decomposes candidates that are not yet judgeable.
- `EDSP` owns an unstable proposition, false binary, or structural coordinate system.
- `SELA` owns long-term system-efficiency versus local-advantage direction pressure.
- `MPG` owns carrier, exposure, timing, optionality, and path posture for one selected
  mainline.
- `WAE` owns an Agentic/Workflow/Evidence controller mismatch.
- `TVG` owns another value-gain round inside one bounded artifact.
- Anti-Spiral supplies the brake when repeated repair replaces objective progress; SRA
  allocates the released resource.
- `TPlan` owns Mission state, Pulse arbitration, continuation, recovery, authority, and
  mutation. SRA returns semantic allocation; it does not mutate the Mission.

Do not use SRA when there is no real shared resource contention. Do not treat the words
“priority”, “important”, “ROI”, or “resource” as sufficient wake-up evidence.

## Runtime Support

Conversational Lite may give bounded advice without creating a run. Controlled
allocations use the sole v0.3 contract and `prepare_sra_run.py`, `record_sra_judgment.py`,
`check_sra_run.py`, `repair_sra_run.py` and `render_sra_decision.py`.

Read `resources/proportionate-runtime.md` for draft intake, checked cards, completion
references and explicit re-ranking. Helpers generate structure, not facts or permission.
Legacy inputs retain conservative calibration; the named proportionate policy admits
single-view structural Full only after an explicit ordinary/reversible assessment.
Uncertain, consequential or contaminated cases retain mutually hidden dual views.

`run.json` is a cache. Raw input and Agentic judgments own the decision; Repair only
rebuilds derived artifacts. Changed inputs require a new run. Prepared v0.2 runs are not
resumed under v0.3. Detailed contracts live in `resources/context-isolation.md`.

Integrity checks prove neither complete context nor correct priority, optimal ROI or
real-world value. A short card is a projection of the checked decision, not new authority.
