# SRA Scarce Resource Allocation — Contraction–Replenishment Core Design

Status: root-cause realigned / implementation-ready
Date: 2026-09-03
Issue: https://github.com/rv198-star/Mindthus/issues/156
Supersedes: `78c2eb23` design logic

## Decision

Create `SRA / Scarce Resource Allocation / 稀缺资源分配` as an independent
Mindthus Judgment Kernel Skill.

SRA owns one judgment:

> When several valid actions or action bundles compete for the same scarce resource,
> what is the smallest allocation that still makes the target achievable, and where
> should the next meaningful resource tranche go?

Chinese short form:

> 在目标、风险底线和资源约束不变的前提下，先收缩到刚好还能达标，再从这个底座回补下一份最值得投入的资源。

Execution short form:

> 收缩找底座，回补定增量。

SRA remains usable by itself. `3L5S`, `EDSP`, `SELA`, `MPG`, `WAE`, `TVG`,
Anti-Spiral, and TPlan may supply candidates, constraints, or runtime support, but none
is a mandatory pre-hop.

## Root-Cause Realignment

The previous design did not merely contain too much detail. Its canonical sequence was
wrong in three ways:

1. The default `Lite` path did not execute contraction and replenishment, so ordinary
   use bypassed the method's defining mechanism.
2. The expanded path constructed a `minimum sufficient bundle` before contraction,
   even though contraction is the operation that should discover the current minimum
   sufficient bundle.
3. One fixed `Priority Order` mixed five different logical types: qualification gates,
   candidate roles, dependency order, bundle selection, and marginal continuation.
   Treating them as one ranking made the method look precise while leaving the actual
   allocation judgment unstable.

This design replaces those rules rather than adding exceptions around them.

Every SRA judgment now uses the same contraction–replenishment core. Depth adapts by
expanding the candidate horizon, resource channels, pressure scenarios, or evidence
work—not by switching to a different method that omits the core.

## Problem

Mindthus can already define problems, expose structural ambiguity, calibrate strategic
direction, design a path-carrying strategy, assign agentic control, strengthen bounded
artifacts, and govern long Missions.

A separate judgment remains under-owned:

> Several things are valid and useful, but they compete for the same limited time,
> money, specialist capacity, attention, risk budget, or opportunity window. What gets
> the resource now, what receives only maintenance, and what is deferred or stopped?

A normal priority list often fails because it:

- ranks isolated tasks whose value exists only as a bundle;
- lets the active task monopolize attention merely because work has already started;
- lowers the target silently when resources tighten;
- treats hard limits, necessities, bottlenecks, enhancements, and options as one score;
- ignores fixed thresholds and indivisible resource blocks;
- confuses sunk cost with future switching cost;
- collapses different resource pools into one fictional currency;
- allocates everything and leaves no explicit maintenance, reserve, defer, or stop lane;
- remains static after evidence, constraints, risks, or opportunity windows change.

## Core Claim

> Fix the target and risk floor. Contract each credible target-reaching bundle until the
> next realistic removal, reduction, substitution, or delay would make the target no
> longer sufficiently supported. Then replenish from the surviving floor bundles by
> choosing the next meaningful tranche with the strongest objective-relevant marginal
> contribution under current evidence.

This produces a current allocation, not a timeless global optimum.

The word `minimum` is evidence-bounded. It means the lowest currently defensible bundle
for the declared target, window, and risk floor—not the mathematically smallest or most
fragile plan.

## Canonical Logic

SRA separates four logical layers. They must not be flattened into one priority score or
one universal ranking.

### 1. Frame And Qualification Constraints

Lock the smallest frame required for a responsible allocation:

- `parent_objective`: the result the allocation serves;
- `target_threshold`: what counts as success in this allocation window;
- `time_window`: how long the decision remains relevant;
- `risk_floor`: safety, compliance, ethics, authority, survival, or another hard limit;
- `decision_owner`: who can authorize allocation, stop, reserve, or target change;
- `contested_resources`: the actually shared scarce resource pools;
- `evidence_ceiling`: what current evidence can and cannot support.

Hard limits and authority qualify an allocation. They are not ordinary candidates and
must not be traded against value through a score.

Resource pressure does not silently lower the target. Lowering the target is a new
owner-authorized decision.

### 2. Contraction

Build one or more credible `target-reaching bundle hypotheses`. Do not label them
minimum yet.

For each bundle, apply realistic pressure using these operations:

- remove a component;
- reduce its scope, quality, frequency, or redundancy;
- substitute a cheaper component;
- move it later without missing the window;
- parallelize it onto a non-contested resource pool;
- replace a full action with the minimum decision-enabling validation.

After each change, ask:

- Does the bundle still support the unchanged target threshold?
- Does it still satisfy the risk floor and authority boundary?
- Did a hidden dependency or fixed threshold appear?
- Did the dominant resource constraint change?
- Is this component genuinely necessary now, or merely useful?

Contraction stops at the first evidence-bounded break point. The surviving bundle is the
`current floor bundle`.

A contraction result records:

- retained components and why they remain load-bearing;
- removed, downgraded, substituted, delayed, or parallelized components;
- the first change that would break target support or the risk floor;
- assumptions and evidence behind each necessity claim;
- what would make a necessity claim obsolete.

If no bundle survives the unchanged target and risk floor, the result is `infeasible`.

### 3. Sequencing And Bundle Selection

Only after contraction has exposed floor bundles does SRA compare them.

The comparison follows distinct rules rather than one mixed priority list:

- `qualification`: discard bundles that violate hard limits, authority, or the target;
- `dependency`: honor predecessors, fixed thresholds, and indivisible commitments;
- `direction/bottleneck`: surface a small action or validation that can reverse the
  path, unlock many downstream actions, remove the dominant constraint, or protect a
  closing window;
- `dominance`: discard a bundle when another uses no more of every contested resource
  and is strictly better on at least one load-bearing dimension;
- `conditionality`: preserve partial, parallel, or state-dependent choices when no
  bundle dominates across plausible states.

These rules constrain selection. They are not candidate roles and they do not create a
numeric total order.

### 4. Replenishment

Start from the selected current floor bundle, not from zero and not from the historical
plan.

Add one `meaningful resource tranche` at a time. A tranche is the smallest allocation
that can produce an observable decision-relevant result, such as:

- one complete validation experiment;
- one engineer-day;
- one review cycle;
- one deliverable work package;
- the smallest team or budget block that crosses a fixed threshold.

Compare possible next tranches by asking which one most strongly:

- removes the current bottleneck;
- changes or validates the direction;
- unlocks downstream options;
- protects a valuable closing window or prevents irreversible loss;
- produces decision-relevant information;
- expands target attainment, resilience, quality, or optionality beyond the floor.

Use evidence-linked qualitative comparison and Pareto dominance by default. Use numeric
ROI only when real measurements and a defensible common unit already exist. SRA does not
invent one.

When contraction removal order and replenishment addition order differ, inspect
threshold effects, complementarity, switching cost, path dependency, or unresolved
uncertainty. Preserve the difference; do not force symmetry.

## Adaptive Depth

SRA has one semantic mainline. It uses the minimum sufficient reasoning depth.

For an ordinary reversible decision, one pass may be enough:

1. name the target, risk floor, and contested resource;
2. test one realistic contraction against the active bundle;
3. compare the strongest alternative next tranche;
4. authorize one bounded allocation and one reranking trigger.

Expand the same loop when any load-bearing condition appears:

- several target-reaching bundle hypotheses;
- multiple constrained resource pools;
- fixed thresholds or indivisible commitments;
- material switching cost or path dependency;
- direction-changing uncertainty;
- high blast radius or hard-to-reverse exposure;
- a credible candidate that cannot yet be compared;
- no stable choice after one contraction–replenishment pass.

The expansion adds evidence, candidates, scenarios, or resource detail. It does not
replace contraction–replenishment with a generic priority discussion.

## Entry And Outcomes

Use SRA when both are true:

1. at least two valid actions, bundles, continuation postures, or reserve choices compete
   for a shared scarce resource; and
2. the judgment changes the next allocation, investment ceiling, maintenance line,
   reserve, defer/stop list, or reranking trigger.

Stay direct when there is only one clear required action, resources are not actually
contested, tasks can proceed independently, or trying the reversible option costs less
than analysis.

Allowed outcomes:

- `direct`: no SRA allocation is needed;
- `allocate`: one current allocation and next tranche are supported;
- `conditional`: the allocation depends on a named evidence state or trigger;
- `infeasible`: no bundle reaches the unchanged target within the risk floor;
- `blocked`: target, authority, evidence, candidate readiness, or resource boundary is
  too incomplete to allocate responsibly.

`maintain`, `reserve`, `defer`, and `stop` are allocation lanes, not substitutes for the
main outcome.

## Candidate Horizon

Before contraction, scan beyond the active task so the current path does not own the
candidate set by default.

The bounded horizon includes:

1. the current bundle;
2. a hard blocker or threshold-essential predecessor;
3. a direction-changing unknown, irreversible risk, or closing window;
4. the strongest feasible alternative contribution to the same objective;
5. maintenance, reserve, defer, and stop postures.

Keep candidates at comparable granularity. Splitting one item into five subtasks must
not increase its apparent claim on resources.

A minimally comparable candidate states:

```text
candidate_id
objective_contribution
resource_demand_vector
dependency_or_bundle_role
evidence_state
delay_cost_or_window
irreversibility_or_downside
```

If a load-bearing field is unknown, request only the minimum evidence needed for the
current allocation.

## Resource Model

Keep scarce resources as a vector:

- time;
- money;
- specialist capacity;
- general labor;
- management attention;
- risk or exposure budget;
- opportunity window;
- another explicitly named constrained resource.

Identify which pool is actually contested, which constraint dominates now, which pools
are substitutable, and which actions can proceed in parallel.

A task that consumes a different non-contested pool is not automatically a competitor.

## Allocation Lanes

The final allocation separates:

- `main_allocation`: the selected floor bundle and current attack;
- `necessary_support`: support required by the floor bundle;
- `maintenance`: minimum resource that preserves operation or reversibility;
- `reserve`: intentionally uncommitted capacity with a release trigger;
- `defer`: useful work receiving no current growth allocation;
- `stop`: work whose future allocation is no longer justified under the current frame.

Candidate roles are contextual. A component can move from necessary support to value
expansion after the target threshold is reached.

## Switching Cost And Sunk Cost

Compare future consequences from the current state:

- `sunk_cost`: already spent and unrecoverable; it does not justify continuation;
- `switching_cost`: new cost required to move to an alternative;
- `reusable_asset`: completed work that retains future value;
- `remaining_cost`: additional resource required to finish the current path.

Historical effort can affect reusable assets or switching cost, but it is not a vote for
continuing the current path.

## Reserve

Reserve is a deliberate allocation when uncommitted capacity has higher option value
than immediate use.

A reserve decision names:

```text
reserved_resource
reserve_reason
release_trigger
expiry_or_review_time
```

Reserve may protect incident response, rollback capacity, survival, a likely opportunity
window, or optionality while direction evidence arrives.

## Mainline / 主路径

1. Decide whether a real shared-resource competition exists; otherwise execute directly.
2. Lock objective, target threshold, window, risk floor, owner, resources, and evidence
   ceiling.
3. Run the bounded Candidate Horizon and create comparable bundle hypotheses.
4. Contract each credible target-reaching bundle until the next change breaks support.
5. Qualify and compare the surviving floor bundles using dependency, bottleneck,
   dominance, and conditionality rules.
6. Replenish from the selected floor bundle and choose the next meaningful tranche.
7. Allocate across main, support, maintenance, reserve, defer, and stop lanes.
8. Set the authorization horizon, evidence ceiling, decision lifetime, and reranking
   triggers.

## Output Contract

The default user-visible answer should stay short and action-changing:

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

A structured audit artifact may additionally include:

```text
allocation_frame
candidate_horizon
bundle_hypotheses
contraction_trace
floor_bundles
qualification_and_dependency_findings
replenishment_options
selected_allocation_lanes
authorization_horizon
evidence_ceiling
reranking_triggers
```

The structured artifact supports review. It must not become the default visible
methodology wall.

## Stop Conditions

Stop the current SRA judgment when:

1. the current floor bundle is stable under the adjacent realistic contraction;
2. the next meaningful tranche is clear or conditionally tied to one named validation;
3. remaining uncertainty is insufficient to change the current action;
4. another analysis round has no named positive-value hypothesis;
5. execution evidence and reranking triggers can handle the residual uncertainty.

SRA authorizes only the declared horizon. It does not continue searching for a timeless
perfect allocation.

## Guardrails

### Preserve The Target

Contraction changes resources and bundle composition while holding the declared target
and risk floor fixed. Only the authorized owner can change the target.

### Use The Core Every Time

Every non-direct SRA judgment must show both a contraction result and a replenishment
result. A generic current-versus-alternative comparison is not SRA fidelity.

### Discover Before Naming Minimum

A bundle may be a target-reaching hypothesis before contraction. It becomes a current
floor bundle only after contraction identifies the first break point.

### Compare Bundles Before Isolated Tasks

Complementary work is judged as a bundle. Alternatives form separate bundles. A large
bundle cannot hide weak components because contraction tests each load-bearing role.

### Keep Logical Types Separate

Hard limits qualify. Dependencies sequence. Roles describe. Bundle comparison selects.
Replenishment allocates the next tranche. Do not collapse these into one score or fixed
priority ladder.

### Bound Analysis Cost

Use the smallest pass whose cost is lower than the plausible loss from a wrong
allocation. Expand only when named conditions can change the action.

### Keep Evidence And Value Separate

A complete shape, passing validator, or fluent explanation does not prove that the
allocation is substantively correct. Claim strength stays below the evidence ceiling.

## Method Ownership

- `3L5S` defines or decomposes unclear problems; SRA allocates among minimally comparable
  candidates.
- `EDSP` owns an unstable proposition or false binary that can change the bundle set.
- `SELA` owns long-term system-efficiency versus local-advantage direction pressure.
- `MPG` owns carrier, exposure, optionality, and path posture for a selected mainline.
- `WAE` owns Agentic / Workflow / Evidence controller mismatch.
- `TVG` owns another bounded strengthening round inside one artifact; SRA enters only
  when that artifact competes with an external resource use.
- Anti-Spiral can brake repeated local repair and constrain the allowed action set; SRA
  decides where the released resource goes.
- TPlan owns Mission state, authority, evidence records, recovery, Pulse routing, and
  mutations. SRA owns only the semantic cross-candidate allocation judgment.

Route an uncertainty outward only when it controls the current allocation. The returned
result becomes a constraint; it does not create a fixed call chain.

The first implementation does not replace TPlan `selection`, `subtraction`, or
continuation logic. Any `allocation_review` integration remains a separate follow-up.

## Pressure Tests

### Positive Cases

1. A release threshold is met, visual polish can continue, and payment validation still
   blocks launch.
2. Product defects, compliance work, technical debt, and features compete for one Sprint
   and several specialist pools.
3. A startup can fund either a platform build or a smaller customer-validation bundle.
4. A research delivery needs more evidence while the deadline is closing.
5. One person has several long-term projects competing for attention and recovery
   capacity.

Expected behavior:

- locks the target and risk floor;
- considers bundles rather than isolated task counts;
- performs contraction before calling a bundle minimum;
- performs replenishment in every non-direct case;
- names a bounded next tranche and investment ceiling;
- returns maintenance, reserve, defer, stop, and rerank decisions when relevant;
- returns `infeasible` rather than silently lowering the target.

### Boundary Cases

| Case | Expected owner or action |
|---|---|
| One known blocker and no competing use of the same resource | direct execution |
| Candidate problems are not defined | 3L5S |
| The proposition or comparison dimensions are unstable | EDSP |
| Long-term system efficiency versus local advantage | SELA |
| A selected mainline needs carrier and exposure strategy | MPG |
| One bounded artifact may benefit from another internal strengthening round | TVG |
| Scripts and agent judgment control the wrong layer | WAE |
| TPlan Pulse selects a runtime Gate | TPlan workflow |
| Tasks use different non-contested resources | direct or parallel execution |

### Adversarial Cases

1. `active-task capture`: a critical blocker sits outside the immediate frame.
2. `granularity manipulation`: one candidate is split into many rows.
3. `sunk-cost capture`: historical spend is used as the reason to continue.
4. `fixed threshold`: value appears only after a multi-day or multi-person tranche.
5. `multiple resource channels`: money is available but the specialist is not.
6. `no feasible bundle`: every bundle violates the unchanged target or risk floor.
7. `contraction/replenishment asymmetry`: removal and addition orders differ.
8. `hard-limit low ROI`: compliance or safety work has no direct revenue.
9. `analysis overkill`: a reversible ten-minute decision stays direct.
10. `reserve option`: full allocation would destroy required response capacity.

### Root-Cause Regression Cases

1. An ordinary SRA answer that only compares current and alternative work must fail
   fidelity because it has no contraction result.
2. A design or output that names a `minimum sufficient bundle` before contraction must
   fail fidelity.
3. A validator or test must not require the former mixed seven-step `Priority Order`.
4. Candidate splitting must not create more allocation weight.
5. A passing shape validator must not be reported as semantic priority approval.

## Validation Contract

Separate four claims:

1. `shape`: required fields and allowed outcomes are present;
2. `routing`: positive and boundary cases wake the correct owner;
3. `action_change`: the decision changes allocation, ceiling, maintenance, reserve,
   defer/stop, or reranking behavior;
4. `allocation_quality`: the substantive allocation is better under the case evidence.

Scripts may validate shape, enums, references, and explicit evidence-risk surfaces. They
must not compute semantic priority, ROI, bundle truth, or allocation correctness.

Allowed first-release claim:

> SRA provides an evidence-bounded contraction–replenishment contract for making
> scarce-resource allocation explicit and action-changing, with tested boundaries
> against neighboring Mindthus methods.

It must not claim universal priority accuracy, optimal ROI, mathematical optimization,
or semantic approval from a shape pass.

## Implementation Scope

### Phase 1: Standalone Contract

Create:

- `skills/sra/SKILL.md`;
- `skills/sra/resources/methodology.md`;
- `skills/sra/resources/fidelity-contract.md`;
- `skills/sra/templates/fidelity-output.json`;
- `skills/sra/scripts/validate_sra_output.py` as a shape-only validator;
- `docs/methodologies/sra.md`;
- `tests/test_sra_contract.py`;
- `tests/sra_pressure_tests.md`.

Phase 1 must prove the same contraction–replenishment core at ordinary and expanded
reasoning depth, including the root-cause regression cases.

### Phase 2: Routing And Packaging

Only after Phase 1 passes:

- route SRA in `skills/using-mindthus/SKILL.md` by semantic shape;
- add SRA to `AGENTS.md` and public methodology navigation;
- update `docs/internal/skill-design-patterns.md`;
- update packaging and method-layering tests;
- register executable tests in the Test Lifecycle registry;
- verify Stable and ROI Beta packaging implications.

### Phase 3: Separate Integration Follow-Up

Only after standalone behavior is validated:

- evaluate a narrow TPlan `allocation_review` hook;
- compare it with existing selection, subtraction, and continuation ownership;
- preserve Pulse arbitration, Mission identity, authority, and mutation ownership;
- validate real TPlan cases before changing runtime ownership.

Phase 3 is not required for SRA to be independently useful.

## Acceptance Criteria

- [ ] SRA is an independent Judgment Kernel Skill for shared scarce-resource allocation.
- [ ] Every non-direct judgment executes contraction and replenishment.
- [ ] Contraction discovers the current floor bundle before it is named minimum.
- [ ] Qualification, dependency, roles, bundle selection, and marginal allocation remain
      distinct logical layers.
- [ ] The target and risk floor remain fixed unless the decision owner explicitly changes
      them.
- [ ] Bundles, fixed thresholds, multiple resource channels, switching cost, reserve,
      conditionality, parallelism, infeasibility, defer, and stop are representable.
- [ ] The default visible answer remains short and action-changing.
- [ ] Validators remain shape-only and make no semantic priority claim.
- [ ] Positive, boundary, adversarial, and root-cause regression cases pass review.
- [ ] Phase 2 begins only after the standalone contract passes.
- [ ] TPlan integration remains outside the initial implementation.

## Release And Governance

This design authorizes implementation through issue `#156` on an isolated branch or
worktree. It does not authorize a release.

Any active project-level feature freeze or real-use evidence gate must still be resolved
before merge. Release work must preserve the Stable plus ROI Beta synchronization rule.
