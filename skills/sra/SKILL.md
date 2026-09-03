---
name: sra
description: Use when multiple valid actions or bundles compete for the same scarce resource and the next allocation must change; hold the target and risk floor fixed, contract credible bundles to their current floor, then replenish the next meaningful resource tranche. Do not use for one obvious action, independent resources, or undefined candidate problems.
---

# SRA / Scarce Resource Allocation / 稀缺资源分配

## Core Claim

SRA answers one question:

> When several valid actions or bundles compete for the same scarce resource, what is
> the smallest allocation that still makes the target achievable, and where should the
> next meaningful resource tranche go?

Chinese short form:

> 在目标、风险底线和资源约束不变的前提下，先收缩到刚好还能达标，再从这个底座回补下一份最值得投入的资源。

Execution short form:

> 收缩找底座，回补定增量。

SRA is a Judgment Kernel Skill. It owns semantic allocation under a shared scarce-resource
constraint. It does not own problem definition, structural truth, long-term direction,
path-carrying strategy, controller assignment, artifact quality, or Mission state.

## Mainline / 主路径

### When To Use

Use SRA when both are true:

1. at least two valid actions, bundles, continuation postures, or reserve choices compete
   for the same scarce resource; and
2. the judgment changes the next allocation, investment ceiling, maintenance line,
   reserve, defer/stop list, or reranking trigger.

Stay direct when there is one clear required action, resources are not actually
contested, tasks can proceed independently, or trying a reversible option is cheaper
than analysis.

### Operating Flow

1. **Lock the frame.** Name the objective, target threshold, time window, risk floor,
   decision owner, contested resource pools, and evidence ceiling.
2. **Scan the candidate horizon.** Include the active path, blockers, direction-changing
   unknowns, the strongest feasible alternative, and maintenance/reserve/defer/stop
   postures.
3. **Create bundle hypotheses.** Group complementary work into credible target-reaching
   bundles. Do not call a bundle minimum yet.
4. **Contract.** Remove, reduce, substitute, delay, parallelize, or replace work with a
   minimum decision-enabling validation until the next realistic change would break the
   unchanged target or risk floor.
5. **Name current floor bundles.** Record retained components, rejected work, the first
   break point, assumptions, and the dominant resource constraint.
6. **Qualify and compare.** Keep hard limits, dependency order, candidate roles, bundle
   selection, and marginal continuation as distinct logical layers. Preserve parallel,
   partial, conditional, or infeasible outcomes when appropriate.
7. **Replenish.** Starting from the selected floor bundle, compare the next meaningful
   resource tranches by bottleneck removal, direction or information value, window
   protection, downstream unlock, objective gain, and optionality.
8. **Allocate and bound.** Set main allocation, necessary support, maintenance, reserve,
   defer, stop, investment ceiling, authorization horizon, evidence ceiling, decision
   lifetime, and reranking triggers.

### Adaptive Depth

SRA has one semantic mainline. It does not use a lightweight mode that skips the core.

For an ordinary reversible decision, one contraction test and one replenishment
comparison may be enough. Expand the same loop only when bundles, multiple resource
channels, fixed thresholds, direction-changing uncertainty, switching cost, path
dependency, blast radius, or irreversibility can change the action.

Expansion adds candidates, evidence, resource detail, or pressure scenarios. It does
not replace contraction–replenishment with a generic priority discussion.

## Guardrails / 从属补漏

### Use The Core Every Time

Every applicable SRA judgment must show both:

- a `contraction result`; and
- a `replenishment result`.

A current-versus-alternative comparison without contraction is ordinary prioritization,
not SRA fidelity.

### Discover Before Naming Minimum

Before contraction, a bundle is only a `target-reaching bundle hypothesis`. It becomes a
`current floor bundle` only after the first evidence-bounded break point is found.

### Preserve The Target

Contraction changes resources and bundle composition while holding the target threshold
and risk floor fixed. Lowering the target is a separate owner-authorized decision.

### Keep Logical Types Separate

- hard limits and authority **qualify**;
- dependencies and fixed thresholds **sequence**;
- candidate roles **describe**;
- bundle comparison **selects**;
- replenishment **allocates the next tranche**.

Do not collapse these into one score or a fixed universal priority ladder.

### Judge Bundles Before Task Counts

Complementary work is compared as a bundle. Alternatives form separate bundles.
Splitting one candidate into more rows must not increase its resource claim.

### Keep Evidence And Value Separate

Use qualitative ordering and dominance unless real measurements support a numeric common
unit. A shape-valid artifact is not proof that the allocation is substantively correct.

### Bound Analysis Cost

Use the smallest pass whose cost is lower than the plausible loss from a wrong
allocation. Stop when the floor bundle, next tranche, authorization horizon, and rerank
trigger are clear enough to act.

### Outcomes And Allocation Lanes

Allowed outcomes:

- `direct`: no SRA allocation is needed;
- `allocate`: one current allocation is supported;
- `conditional`: the allocation depends on a named evidence state or trigger;
- `infeasible`: no bundle reaches the unchanged target within the risk floor;
- `blocked`: target, authority, evidence, candidate readiness, or resource boundaries are
  too incomplete.

The allocation separates:

- `main_allocation`;
- `necessary_support`;
- `maintenance`;
- `reserve` with a release trigger;
- `defer`;
- `stop`.

`maintain`, `reserve`, `defer`, and `stop` are lanes, not substitutes for the main
outcome.

### Default Visible Output

Keep the ordinary answer short and action-changing:

```text
Decision: direct | allocate | conditional | infeasible | blocked
Why now: objective-relevant reason
Current floor: smallest currently supported bundle
Next tranche: bounded resource allocation
Investment ceiling: maximum current commitment
Maintenance / reserve: explicit minimum or none
Defer / stop: displaced work
Rerank trigger: evidence, resource, risk, threshold, or window change
```

Use structured audit fields only when review, replay, validation, or handoff requires
them.

## Boundaries / 边界

- Undefined or unstable candidate problems belong to `3L5S` or `EDSP` before allocation.
- Long-term system-efficiency versus local-advantage direction belongs to `SELA`.
- Carrier, exposure, optionality, and path posture for a selected mainline belong to
  `MPG`.
- Agentic / Workflow / Evidence controller mismatch belongs to `WAE`.
- Another strengthening round inside one bounded artifact belongs to `TVG`; SRA enters
  only when that artifact competes with an external resource use.
- Anti-Spiral may brake repeated local repair and constrain the allowed action set; SRA
  decides where released resources go.
- TPlan owns Mission state, authority, evidence records, Pulse routing, recovery, and
  mutation. SRA owns only the semantic cross-candidate allocation judgment.

Do not create a fixed call chain. Route outward only when an uncertainty controls the
current allocation, then treat the returned result as a constraint.

## Runtime Support / 支撑材料

Read `resources/methodology.md` for the detailed contraction–replenishment procedure,
examples, failure modes, and method boundaries.

- `resources/fidelity-contract.md` — required SRA judgment moves and shape contract.
- `templates/fidelity-output.json` — structured example for review and replay.
- `scripts/validate_sra_output.py` — SRA shape and evidence-risk validator.

The validator reports shape and evidence risk only. A pass is not semantic priority,
ROI, bundle-feasibility, or allocation approval.
