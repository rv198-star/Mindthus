# SRA Scarce Resource Allocation / 稀缺资源优先分配 Design

Status: approved design / implementation-ready after issue registration
Date: 2026-09-03
Issue: https://github.com/rv198-star/Mindthus/issues/156

## Decision

Create `SRA / Scarce Resource Allocation / 稀缺资源优先分配` as an independent Mindthus
Judgment Kernel Skill.

SRA owns this judgment:

> When multiple valid problems, tasks, branches, projects, or continuation choices
> compete for the same scarce resource, which combination receives the current
> allocation, which items stay on a minimum maintenance line, and which items are
> deferred or stopped?

SRA is usable by itself. `3L5S`, `TPlan`, Anti-Spiral, SELA, MPG, EDSP, WAE, and TVG
may provide inputs, constraints, or runtime support, but none is a prerequisite for a
standalone SRA judgment.

SRA uses two reasoning depths:

- `Lite`: the default fast decision for the next meaningful resource tranche during
  ordinary execution.
- `Full`: the expanded allocation judgment for high-impact portfolios, minimum
  sufficient bundles, multiple resource constraints, direction-changing uncertainty,
  fixed commitment thresholds, or irreversible decisions.

`auto` is the default selector. It starts from `Lite` and expands to `Full` only when an
explicit escalation condition is present.

Both depths preserve one semantic identity: Lite runs one bounded micro-contraction and
one micro-replenishment; Full expands the same contraction–replenishment logic across
bundles, resource channels, pressure scenarios, and decision lifetimes.

## Goal

Make scarce-resource allocation an explicit, action-changing judgment without turning
ordinary work into a planning ceremony.

SRA should help an agent or person:

- protect hard gates and threshold-essential work;
- identify small actions that change direction, remove a bottleneck, or avoid an
  irreversible loss;
- prevent current detail work from monopolizing attention by default;
- choose a minimum sufficient bundle rather than rank isolated tasks that only work
  together;
- decide the next meaningful resource tranche;
- name what receives only maintenance, what is deferred, and what stops;
- preserve reserve capacity when uncertainty or opportunity windows justify it;
- rerun the allocation when goals, evidence, constraints, risks, or available resources
  change.

The first release should prove method shape, routing boundaries, and action-changing
pressure-test behavior. It should not claim universal priority accuracy, optimal
business ROI, or mathematically optimal resource allocation.

## Problem

Mindthus can already define problems, expose structural ambiguity, calibrate strategic
direction, design a path-carrying strategy, assign agentic control, strengthen bounded
artifacts, and govern long Missions.

A separate judgment remains under-owned:

> Several things are valid and useful, but they compete for the same limited time,
> money, specialist capacity, attention, risk budget, or opportunity window. What gets
> the resource now?

This judgment also appears during ordinary execution. A task can remain useful while
additional detail no longer controls whether the target is reached. Without an explicit
allocation checkpoint, the active task receives more resource merely because it is
already active, visible, and easy to continue.

Ordinary priority lists are insufficient because they often:

- rank single tasks even when value exists only as a bundle;
- hide target-threshold changes inside a cheaper plan;
- omit the strongest alternative because it is outside the current attention frame;
- mix hard gates, necessities, enhancements, and optional work into one score;
- treat different resource types as interchangeable;
- ignore switching cost or mistake sunk cost for a reason to continue;
- fail to produce an explicit defer and stop list;
- remain static after resources, evidence, risks, or opportunity windows change.

## Core Claim

> Feasibility and target necessity determine which bundles can qualify; direction,
> dependency, bottlenecks, and time windows determine what must happen first;
> risk-adjusted bundle value selects the current allocation; marginal value determines
> the next meaningful resource tranche.

Chinese short form:

> 先排除不可行，再保护达标必要项；方向、依赖、瓶颈和窗口决定先后；组合价值决定本轮投哪套；边际价值决定下一份资源投哪里。

Execution short form:

> 收缩找出不能删的；回补决定下一份值得加的。

SRA's judgment center is allocation under a shared scarce-resource constraint. It does
not independently own problem definition, structural truth, long-term trend, carrier
strategy, agentic control, artifact quality, or runtime state.

## Entry Contract

SRA begins by choosing one of four entry outcomes:

| Outcome | Meaning |
|---|---|
| `direct` | No real resource competition exists, or one obvious low-risk next action dominates. Execute directly. |
| `lite` | A bounded, reversible, local allocation decision exists. Authorize only the next meaningful tranche. |
| `full` | The decision affects bundles, major commitments, multiple constrained resources, direction, or irreversible exposure. |
| `blocked` | Target, threshold, evidence, decision authority, candidate readiness, or resource boundary is too incomplete to allocate responsibly. |

`direct` is an intervention outcome, not a third SRA reasoning mode.

### Positive Entry Shape

Use SRA when both are true:

1. At least two valid actions, bundles, or continuation postures compete for the same
   scarce resource, or the current path competes with switching, maintaining, deferring,
   stopping, or reserving that resource.
2. The allocation judgment changes the next action, resource ceiling, defer/stop list,
   or reranking trigger.

### Direct Boundary

Stay direct when:

- only one clear blocker or required next action exists;
- tasks use independent non-contested resources and can proceed in parallel;
- the choice is low-risk, reversible, and cheaper to try than to analyze;
- the work is a simple ordered checklist with no meaningful allocation trade-off.

### Analysis-Cost Gate

The allocation method is itself resource-constrained:

> Use a reasoning depth whose cost is lower than the plausible loss from a wrong
> allocation.

When a reversible local mistake costs less than an expanded allocation analysis, use
`direct` or `Lite`. Full analysis is justified when a wrong allocation could consume a
larger resource block, close an opportunity window, create irreversible loss, or cause
many downstream tasks to become invalid.

## Allocation Frame

Every SRA judgment names the minimum frame needed to compare actions:

- `parent_objective`: the result the allocation serves;
- `target_threshold`: what counts as success for this allocation window;
- `time_window`: how long the decision remains relevant;
- `risk_floor`: safety, compliance, ethics, authority, survival, or other hard limits;
- `decision_owner`: who can authorize the allocation and any stop or target change;
- `contested_resource`: the actual shared scarce resource;
- `evidence_ceiling`: what current evidence can and cannot support.

A target-threshold change is a new decision. Resource pressure does not silently lower
the target from "achieve the result" to "remain alive" or "look partially complete."

## Candidate Horizon Probe

Before choosing a priority, SRA performs a short Candidate Horizon Probe. The purpose is
to prevent the active task and the first remembered alternative from owning the entire
candidate set.

The probe scans for:

1. the current path;
2. a hard gate, blocker, or threshold-essential predecessor;
3. a direction-changing unknown, irreversible risk, or closing opportunity window;
4. the strongest feasible alternative contribution to the same objective;
5. maintenance, reserve, defer, and stop postures.

The probe is bounded. Lite normally keeps two to four actionable candidates. Full may
expand the set when bundle construction or multiple resource channels require it.

If a credible candidate cannot be compared because its target contribution, resource
demand, evidence state, dependency role, time window, or irreversibility is unknown,
SRA returns a minimal readiness request instead of inventing a priority.

## Priority Order

SRA applies this order before any ROI-style comparison:

1. `hard_gate`: safety, compliance, ethics, authority, irreversible-loss prevention,
   or another declared bottom line.
2. `feasible_bundle`: combinations that can reach the target threshold inside the time
   window and risk floor.
3. `threshold_essential`: components whose removal makes the current target bundle no
   longer sufficiently supported.
4. `direction_or_bottleneck`: small actions that can change the path, unlock many
   downstream actions, resolve the dominant constraint, or protect a closing window.
5. `risk_adjusted_bundle_value`: comparison among the remaining feasible bundles.
6. `marginal_tranche_value`: the next meaningful resource block that produces the
   largest objective-relevant gain.
7. `reserve`: intentionally uncommitted capacity whose option value exceeds an
   immediate allocation.

This order protects necessary work without granting it unlimited resource. Once a
necessary item reaches the evidence and completion level required by the target
threshold, additional improvement competes as `value_expanding` work.

## Candidate Roles

Each candidate or bundle can take one primary role for the current allocation window:

| Role | Meaning |
|---|---|
| `hard_gate` | Must be satisfied before ordinary value comparison. |
| `threshold_essential` | Required by the selected target-reaching bundle. |
| `enabler_or_bottleneck` | Removes a dominant constraint, changes direction, or unlocks multiple actions. |
| `value_expanding` | Improves the result beyond the current threshold. |
| `maintenance_or_option` | Preserves operation, reversibility, or future choice at minimum cost. |
| `defer_or_stop` | Receives no current growth allocation. |

The role is contextual. The same task may move from `threshold_essential` to
`value_expanding` after the target threshold has been reached.

## Evidence-Bounded Minimum Sufficient Bundle

SRA seeks a `current minimum sufficient bundle`, not a universally minimal task set.

A bundle qualifies when, under current evidence, explicit assumptions, the declared
window, and the risk floor:

1. it supports reaching the target threshold with the required confidence;
2. removing any non-substitutable component makes that target judgment no longer
   sufficiently supported;
3. it excludes work that only improves appearance or completeness without changing
   target attainment, risk, evidence, or required optionality.

Important consequences:

- backup, rollback, review, or redundancy may be essential when the risk floor requires
  them;
- alternatives create separate bundles rather than one bundle containing every
  substitute;
- "minimum" does not mean maximally fragile;
- a bundle may be conditional on named evidence or authority;
- when no bundle meets the threshold and risk floor, the outcome is `infeasible`;
- lowering the target requires an explicit new decision by the authorized owner.

For every load-bearing necessity claim, record:

- why the component is necessary now;
- the assumption and evidence supporting that judgment;
- what would make the necessity claim false or obsolete.

## Resource Model

SRA keeps scarce resources as a vector rather than collapsing them into one universal
score:

- time;
- money;
- specialist capacity;
- general labor;
- management attention;
- risk or exposure budget;
- opportunity window;
- another explicitly named constrained resource.

Before ranking, identify:

- which pool is actually contested;
- the current dominant constraint;
- which resources are substitutable;
- which tasks can proceed in parallel because they use different pools;
- which task needs a fixed threshold or indivisible resource block.

SRA uses qualitative ordering, dominance, and evidence-linked comparison by default.
It does not require a weighted scoring table.

## Meaningful Resource Tranche

"The next unit of resource" means the next decision-relevant tranche, not an arbitrary
single hour, dollar, token, or person.

A meaningful tranche may be:

- one complete validation experiment;
- one engineer-day;
- one review cycle;
- one deliverable work package;
- the smallest team or budget block that crosses a fixed threshold;
- another bounded allocation that can produce an observable outcome.

When value appears only after a fixed threshold, the whole threshold tranche is the
comparison unit. This prevents SRA from systematically preferring tiny immediate tasks
and starving large threshold-essential work.

## Lite Mode

### Purpose

Lite is the default execution-time allocation checkpoint. It answers:

> Should the next meaningful resource tranche continue on the current path, switch to
> the strongest alternative, maintain the current result, defer the work, stop it, or
> remain reserved?

Lite is intentionally small. It does not enumerate the full portfolio or build a
complex score. It keeps the method core by running one micro-contraction and one
micro-replenishment instead of the repeated Full loop.

### Lite Mainline

1. Lock the Allocation Frame at the smallest useful scope.
2. Run the Candidate Horizon Probe.
3. Identify hard gates, threshold-essential work, and the strongest feasible
   alternative.
4. Run one micro-contraction: cap, remove, downgrade, or move current work to maintenance
   until the next realistic reduction would threaten the unchanged target or risk floor.
5. Name the current floor and first break point.
6. Run one micro-replenishment from that floor: compare the next meaningful tranche
   across the surviving current path, strongest alternative, and reserve posture.
7. Separate real switching cost from sunk cost.
8. Choose one action: `continue`, `switch`, `maintain`, `defer`, `stop`, or `reserve`.
9. Set an investment ceiling, authorization horizon, displaced-work decision, and a
   reranking trigger.

A Lite result without both a contraction result and a replenishment result is ordinary
prioritization, not complete SRA fidelity.

### Lite Questions

- What target threshold does the next tranche serve?
- What can be removed, capped, downgraded, or moved to maintenance while the target and
  risk floor remain supported?
- Where is the first realistic break point?
- From that current floor, where should one next meaningful tranche go?
- Does the current path still change target attainment, or only improve completion?
- Is a hard gate, blocker, direction test, or closing window currently more decisive?
- What is the strongest credible alternative use of the same resource?
- What real switching cost applies from the current state?
- What is already sunk and therefore irrelevant to continuation?
- What evidence will the next tranche produce?
- What change should reopen the allocation?

### Lite Output

A user-visible Lite answer should normally fit in one paragraph or a short block:

```text
Decision: continue | switch | maintain | defer | stop | reserve
Why now: objective-relevant reason
Current floor: result of one bounded micro-contraction
Next tranche: result of one micro-replenishment from that floor
Investment ceiling: maximum current commitment
Authorization horizon: one action | one tranche | until named checkpoint
Defer/stop: explicit displaced work
Rerank trigger: evidence, resource, risk, threshold, or window change
```

Internal audit fields may be richer, but the default visible answer should not become a
methodology wall.

### Lite Escalation Conditions

Escalate to Full when any of the following is load-bearing:

- direction-changing uncertainty can alter the target or candidate set;
- multiple feasible bundles exist;
- the commitment is large, high-blast-radius, or hard to reverse;
- fixed thresholds, bundle effects, or indivisible investments control value;
- multiple constrained resource pools produce different allocation results;
- switching cost or path dependency is material;
- a credible alternative is missing or cannot be compared;
- Lite cannot distinguish continue, switch, stop, or reserve;
- the allocation will authorize more than one bounded tranche or checkpoint.

## Full Mode

### Purpose

Full handles project, Mission, portfolio, or major execution reallocations where the
cost of a wrong allocation justifies expanded judgment.

### Full Mainline

1. Lock objective, target threshold, time window, risk floor, decision owner, and
   evidence ceiling.
2. Identify the actually contested resource pools and dominant constraint.
3. Build minimum comparable candidate cards.
4. Resolve or route direction-changing unknowns only to the point required for current
   action.
5. Construct one or more current minimum sufficient bundles.
6. Eliminate infeasible and dominated bundles.
7. Run resource contraction to expose essential items, dependencies, false necessities,
   and failure boundaries.
8. Run resource replenishment to identify the highest-value next meaningful tranche.
9. Select the risk-adjusted feasible allocation and any reserve capacity.
10. Output main attack, necessary support, minimum maintenance, explicit defer, explicit
    stop, authorization, evidence ceiling, decision lifetime, and reranking triggers.

### Minimum Comparable Candidate Card

Full does not require complete 3L5S Definition for every candidate. It requires only:

```text
candidate_id
objective_contribution
resource_demand_vector
dependency_or_bundle_role
evidence_state
delay_cost_or_opportunity_window
irreversibility_or_downside
```

Candidate descriptions should remain granularity-stable. Splitting one candidate into
five subtasks must not increase its allocation merely because it occupies more rows.

### Direction-Changing Uncertainty Gate

An unknown receives priority when different plausible answers would:

- change the target;
- alter the feasible bundle set;
- reverse the main path;
- invalidate a large downstream investment;
- expose a large or irreversible loss.

The required action is the `minimum decision-enabling validation`: enough evidence to
support the current allocation, not exhaustive certainty.

SRA routes the unknown to the method or evidence owner that actually controls it:

- missing facts -> evidence acquisition;
- unstable proposition or false binary -> EDSP;
- system efficiency versus local advantage -> SELA;
- carrier, exposure, and path volatility -> MPG;
- unclear problem or candidate definition -> 3L5S;
- agentic control mismatch -> WAE;
- stakeholder authority or target trade-off -> human decision or Decision Context
  Calibration.

The routed result returns as an allocation constraint. SRA remains the owner only for
cross-candidate resource allocation.

### Resource Contraction

Keep the target threshold and risk floor fixed while applying realistic resource
pressure scenarios.

Ask:

- Which components remain indispensable?
- Which removal changes direction or invalidates many downstream actions?
- Which items can be substituted, combined, parallelized, or downgraded?
- Which items only raise completion quality beyond the threshold?
- Which resource pool breaks the bundle first?

Record the reason for retain, replace, defer, or remove decisions. Contraction finds:

- threshold-essential components;
- hidden dependencies;
- the dominant constraint;
- false necessities;
- the lowest feasible resource boundary.

### Resource Replenishment

Start from the lowest feasible bundle and add one meaningful tranche at a time.

Ask:

- Which tranche removes the current bottleneck?
- Which tranche unlocks the most downstream options?
- Which tranche produces the highest decision-relevant information gain?
- Which tranche protects the most valuable closing window?
- Which tranche produces the largest objective-relevant marginal gain?

When contraction removal order and replenishment addition order differ, inspect
 dependency, threshold effects, complementarity, switching cost, or unresolved
uncertainty. Preserve a partial or conditional order rather than forcing a false total
ranking.

### Feasibility And Dominance

Full comparison follows this order:

1. Remove bundles that violate a hard gate.
2. Remove bundles that cannot reach the target threshold.
3. Remove a bundle when another bundle uses no more of every contested resource and is
   strictly better on at least one load-bearing dimension.
4. Compare remaining non-dominated bundles using evidence, downside, delay cost,
   information value, optionality, and objective contribution.
5. Return a conditional allocation when no single bundle dominates across plausible
   states.

### Full Output

```text
allocation_outcome: allocate | conditional | infeasible | blocked
allocation_scope: problem_portfolio | execution_portfolio

objective and target threshold
time window and risk floor
contested resources and dominant constraint
decision owner and evidence ceiling

direction-changing unknowns and minimum validation
candidate bundles and feasibility status
contraction findings
replenishment findings

selected main allocation
necessary support
minimum maintenance line
explicit defer list
explicit stop list
reserved capacity and release trigger

next meaningful tranche
authorization boundary
decision lifetime
reranking triggers
```

## Reserve Capacity

SRA may intentionally leave a resource uncommitted when reserve creates more value than
an immediate allocation.

Reserve can protect:

- response capacity for unknown incidents;
- a closing but not yet confirmed opportunity;
- option value while direction evidence arrives;
- recovery and rollback capacity;
- survival under a volatile path.

A reserve decision names:

```text
reserved_resource
reserve_reason
release_trigger
expiry_or_review_time
```

Reserve is an explicit allocation posture, not an unexamined leftover.

## Switching Cost And Sunk Cost

SRA distinguishes:

- `sunk_cost`: already spent and unrecoverable; it does not justify continuation;
- `switching_cost`: new cost required to move from the current state to an alternative;
- `reusable_asset`: work already completed that retains future value;
- `remaining_cost`: additional resource required to finish the current path.

The comparison is between future resource consequences from the current state, not
between total historical spend on each path.

## Stop Conditions

### Lite Stop

Lite stops after one micro-contraction has identified the current floor, one
micro-replenishment has selected the next bounded tranche, and a reranking trigger is
named. It does not keep searching for a theoretically perfect alternative.

### Full Stop

Full stops when:

1. the selected bundle remains stable across adjacent realistic pressure scenarios;
2. the first meaningful resource tranche is clear;
3. remaining uncertainty is insufficient to change the current action;
4. another analysis round has no named positive-value hypothesis;
5. execution evidence and reranking triggers can handle the residual uncertainty.

## Guardrails

### Guardrail: Protect The Target Threshold

Protects the mainline from silently replacing the requested result with a cheaper
survival state. It cannot block an authorized target change.

### Guardrail: Protect Small But Decisive Actions

Protects direction tests, bottleneck removals, irreversible-risk prevention, and option
creation from being buried by task size. It cannot promote every small task into a
critical item.

### Guardrail: Judge Bundles Before Isolated Tasks

Protects complementary work whose value appears only together. It cannot hide weak
components inside a large bundle; contraction must still test each non-substitutable
role.

### Guardrail: Keep Evidence And ROI Separate

Protects factual honesty. ROI language may be quantitative when real measurements
exist, or qualitative when only ordinal evidence exists. SRA does not invent a common
currency for values, probabilities, safety, or stakeholder authority.

### Guardrail: Limit Analysis Cost

Protects ordinary work from methodology overhead. Lite preserves one micro-contraction
and one micro-replenishment while limiting candidate width and authorization horizon;
Full expands only under named escalation conditions and stops under an explicit
value-gain rule.

### Guardrail: Preserve Partial Orders

Protects dependency, threshold, parallelism, and resource-channel differences. SRA may
return conditional ordering or parallel allocations instead of a false total ranking.

## Method Architecture

SRA is a Judgment Kernel Skill. It owns allocation semantics and produces an allocation
decision. It does not own durable runtime state or mutation authority.

### Relationship To 3L5S

| Active question | Owner |
|---|---|
| What is the real problem, or how should a large problem be decomposed? | 3L5S |
| Which sufficiently defined problems or tasks receive the current scarce resource? | SRA |

Handshake:

```text
3L5S makes candidates minimally judgeable
    -> SRA allocates scarce resources
    -> selected candidates return to 3L5S when deeper definition or decomposition is needed
```

SRA requests only the minimum comparable candidate card. It does not require full
Definition for every candidate. After the requested fields are supplied, SRA must
allocate, return a conditional result, or block on a newly identified load-bearing gap;
it should not oscillate between 3L5S and SRA without new evidence.

### Relationship To EDSP

EDSP owns an unstable proposition, false binary, or structural coordinate system. SRA
may route a direction-changing unknown to EDSP, then use the returned structure as an
allocation constraint.

### Relationship To SELA

| Active question | Owner |
|---|---|
| Which paradigm has the long-term system-efficiency direction? | SELA |
| Given the current direction evidence, how should this period's limited resources be allocated? | SRA |

SELA may constrain direction. SRA owns the current cross-candidate allocation. They do
not produce two equal first theses.

### Relationship To MPG

| Active question | Owner |
|---|---|
| Multiple problems, tasks, objectives, or action bundles compete for a common resource pool. | SRA |
| One selected mainline needs a carrier, exposure budget, timing, optionality, and path posture. | MPG |

When an SRA candidate contains material carrier or path risk, MPG evaluates that
candidate and returns a path constraint. SRA does not redesign the carrier itself.

### Relationship To WAE

WAE applies only when an agentic system has a controller mismatch: scripts, workflow,
agentic judgment, evidence, review, or human authority control the wrong layer.

SRA's semantic allocation remains Agentic or human judgment. Scripts may validate
shape, references, and enum values; they do not compute priority or semantic ROI.

### Relationship To TVG

| Active question | Owner |
|---|---|
| Does another round improve a bounded artifact under its active value profile? | TVG |
| Should the next scarce-resource tranche go to this artifact or another task? | SRA |

TVG's internal value-gain loop remains closed. SRA enters only when the artifact
competes with an external use of the same resource.

### Relationship To Anti-Spiral

Anti-Spiral detects that repeated local repair may be replacing objective progress and
constrains the allowed next actions. SRA decides where the released resource goes.

```text
Anti-Spiral brake
    -> allowed action set
    -> SRA allocation
```

A single handoff owns the decision. The two mechanisms do not recursively call each
other.

### Relationship To TPlan

TPlan owns Mission state, evidence records, authority, recovery, Pulse routing, and task
mutations. SRA owns the semantic allocation judgment when real task or branch candidates
compete for a common resource pool.

Not every TPlan `selection` is SRA:

- Pulse Gate Arbitration remains deterministic TPlan workflow;
- residual Mission selection remains TPlan identity and authority handling;
- same-path continuation remains the TPlan Linear Continuation Gate;
- branch or task resource allocation may call SRA when competing candidates and a
  common constrained resource are explicit.

The first SRA implementation does not replace TPlan's existing `selection` or
`subtraction` hooks globally. A later integration may add a narrow
`allocation_review` hook after standalone SRA behavior is validated.

### Relationship To using-mindthus

Route to SRA by semantic shape:

> multiple valid candidates + a common scarce resource + an action-changing allocation

Do not route by the words `priority`, `ROI`, `important`, or `resource` alone.

SRA supports direct load. The entry skill is not a mandatory pre-hop.

## Pressure Test Design

### Lite Positive Cases

1. A product page has reached the release threshold, but visual polish can continue;
   payment validation still blocks launch.
2. A release-blocking test is being fixed when an adjacent refactor opportunity appears.
3. A high-severity security issue appears during feature development.
4. A new useful idea appears during a time-bounded delivery and competes with the active
   task for the same engineer-day.
5. A documentation section is already usable, but the author can either add detail or
   finish a missing operational example.

Expected behavior:

- uses Lite rather than Full;
- runs a bounded Candidate Horizon Probe;
- protects hard gates and threshold-essential work;
- names the strongest credible alternative;
- authorizes only one action, tranche, or checkpoint;
- explicitly defers or stops displaced work;
- names a reranking trigger.

### Full Positive Cases

1. Product defects, compliance work, technical debt, and new features compete for one
   Sprint and different specialist pools.
2. A startup has enough cash for either platform construction or a smaller customer
   validation path.
3. A research delivery needs additional evidence while the deadline is approaching.
4. One person has several long-term projects competing for attention and recovery
   capacity.
5. A Mission startup has several candidate bundles with fixed thresholds and different
   risk profiles.

Expected behavior:

- identifies the contested resource pools and dominant constraint;
- builds evidence-bounded minimum sufficient bundles;
- protects direction tests and small bottleneck-removing actions;
- runs contraction and replenishment without inventing a total score;
- returns main allocation, support, maintenance, defer, stop, reserve, and rerank
  conditions;
- returns `infeasible` when no bundle reaches the unchanged target threshold.

### Boundary Cases

| Case | Expected owner or action |
|---|---|
| One known release blocker and no credible alternative use of the same resource | direct execution |
| User says only "the system is bad" and candidate problems are not defined | 3L5S |
| A/B appears valid but the proposition or dimensions are unstable | EDSP |
| Long-term system efficiency versus local advantage | SELA |
| A selected mainline needs carrier and exposure strategy under volatility | MPG |
| A bounded artifact may benefit from another strengthening round | TVG |
| Scripts and agent judgment control the wrong layer | WAE |
| TPlan Pulse chooses which Gate handles runtime signals | TPlan workflow |
| Tasks use different non-contested resources and can proceed in parallel | direct or parallel execution |

### Adversarial Cases

1. **Candidate omission**: the current task and a weak alternative are visible while a
   critical blocker is outside the immediate frame.
2. **Granularity manipulation**: one candidate is split into many subtasks and another
   remains one line.
3. **Sunk-cost capture**: the current path has consumed most of the historical budget.
4. **Fixed threshold**: value appears only after a three-day or multi-person commitment.
5. **Multiple resource channels**: money is available but the only specialist is not.
6. **No feasible bundle**: every bundle violates either the target threshold or risk
   floor.
7. **Contraction-replenishment conflict**: removal and addition orders differ because of
   complementarity.
8. **Hard-gate low ROI**: compliance or safety work has no direct revenue but is
   mandatory.
9. **Analysis overkill**: a reversible ten-minute choice should stay direct or Lite.
10. **Reserve option**: immediate full allocation would destroy response capacity for a
    likely near-term event.

Expected behavior:

- exposes the hidden mechanism rather than producing a plausible-looking rank;
- preserves partial, parallel, conditional, or infeasible outcomes where appropriate;
- does not use a numeric score to hide missing evidence;
- selects the correct neighboring method when SRA is not the owner.

## Validation Contract

The first implementation should separate four claims:

1. `shape`: required fields and allowed outcomes are present;
2. `routing`: positive and boundary cases wake the correct owner;
3. `action_change`: SRA changes allocation, ceiling, defer/stop, reserve, or rerank
   behavior;
4. `priority_quality`: whether the allocation was substantively better under the case
   evidence.

Scripts may validate only `shape` and deterministic references. Routing and action
behavior require pressure-test review. Priority quality remains an agentic or human
judgment bounded by evidence.

A complete artifact or passing validator is not proof that the chosen priority is true.

### Initial Claim Ceiling

Allowed first-release claim:

> SRA provides a lightweight and expanded contract for making scarce-resource
> allocation explicit, evidence-bounded, and action-changing, with tested routing
> boundaries against neighboring Mindthus methods.

Disallowed first-release claims:

- SRA always finds the correct priority;
- SRA maximizes ROI;
- SRA computes an optimal allocation;
- passing pressure tests proves real-world business value;
- a shape-valid output proves semantic correctness.

## Implementation Scope

### Phase 1: Standalone SRA Contract

Create:

- `skills/sra/SKILL.md`;
- `skills/sra/resources/methodology.md`;
- `skills/sra/resources/fidelity-contract.md`;
- `skills/sra/templates/fidelity-output.json`;
- `skills/sra/scripts/validate_sra_output.py` as a shape-only validator;
- `docs/methodologies/sra.md`;
- `tests/test_sra_contract.py`;
- `tests/sra_pressure_tests.md` or an equivalent structured case surface.

Required behavior:

- direct / Lite / Full / blocked entry outcomes;
- Candidate Horizon Probe;
- fixed priority order;
- evidence-bounded minimum sufficient bundle;
- meaningful tranche, reserve, switching-cost, and authorization-horizon contracts;
- one Lite micro-contraction and micro-replenishment;
- Full contraction-replenishment loop;
- positive, boundary, and adversarial pressure cases.

### Phase 1.5: Context-Isolated Hybrid Runtime

After the standalone semantic contract is stable, add a Workflow shell around the
Agentic allocation owner:

- classify supplied context into admitted, quarantined, and excluded lanes;
- normalize candidate cards and generate deterministic blind aliases;
- seal and hash the admitted allocation packet;
- record a blind contraction/replenishment judgment before current-path state is shown;
- reconcile the blind result with switching cost, reusable assets, remaining cost,
  commitments, and sunk-cost rejection;
- support `packet_bound`, `fresh_context`, and `blind_then_state` carriers;
- validate packet/judgment hashes and references;
- render the final allocation without recomputing semantics.

The runtime reduces ambient-context influence without claiming complete context or
absolute host isolation. Scripts control deterministic order and evidence plumbing;
Agentic SRA retains necessity, feasibility, contraction, replenishment, and allocation
judgment. Detailed design: `2026-09-03-sra-context-isolated-runtime-design.md` and #157.

### Phase 2: Routing And Packaging

After Phase 1 pressure tests pass:

- add SRA to `skills/using-mindthus/SKILL.md` routing by semantic shape;
- add SRA to `AGENTS.md` skill map and combination guidance;
- update `docs/internal/skill-design-patterns.md` classification;
- add the public methodology link to `README.md`;
- update packaging and method-layering tests;
- register executable tests in the Test Lifecycle registry;
- verify Stable and ROI Beta packaging implications before release work begins.

### Phase 3: Integration Follow-Up

Create a separate follow-up only after standalone behavior is validated:

- evaluate a narrow TPlan `allocation_review` hook;
- compare it with existing selection, subtraction, and continuation ownership;
- preserve Pulse arbitration, Mission identity, and continuation authority;
- validate real TPlan cases before changing runtime ownership.

Phase 3 is not required for SRA to be independently useful.

## Non-Goals

The initial SRA implementation does not include:

- a weighted priority score;
- an automatic ROI calculator;
- linear-programming or optimization claims;
- exhaustive project-management planning;
- automatic target reduction;
- automatic task-tree mutation;
- automatic model invocation or full-conversation scraping;
- a claim of context-free or absolutely isolated judgment;
- global replacement of TPlan selection or subtraction;
- a requirement to run 3L5S before every allocation;
- a requirement to run SRA after every task or checkpoint;
- a fixed call chain among SRA and neighboring methods.

## Acceptance Criteria

### Method Identity

- [ ] SRA exists as an independent Judgment Kernel Skill.
- [ ] The core judgment is allocation among valid candidates sharing a scarce resource.
- [ ] Lite is the default; Full expands only under named escalation conditions.
- [ ] Lite and Full share the contraction-replenishment core; Lite performs one bounded
      micro-contraction and one micro-replenishment rather than generic task ranking.
- [ ] Direct and blocked outcomes prevent unnecessary or unsupported method use.

### Priority Effectiveness

- [ ] The Candidate Horizon Probe protects against active-task capture and missing
      blockers.
- [ ] Hard gates and feasible target-reaching bundles precede ROI-style comparison.
- [ ] Necessary, bottleneck, value-expanding, maintenance, defer, and stop roles are
      distinguishable.
- [ ] Minimum sufficient bundles are evidence-bounded and allow substitute bundles,
      redundancy, conditionality, and infeasibility.
- [ ] Different resource channels, fixed thresholds, parallelism, switching cost, sunk
      cost, and reserve capacity are represented without a universal score.
- [ ] Lite names the post-contraction current floor, chooses the next tranche through
      micro-replenishment, and authorizes only one action, one meaningful tranche, or
      one named checkpoint.
- [ ] Full produces main allocation, support, maintenance, defer, stop, reserve, and
      reranking conditions.

### Architecture Boundaries

- [ ] 3L5S owns problem definition and decomposition; SRA owns allocation among
      minimally comparable candidates.
- [ ] EDSP, SELA, MPG, WAE, and TVG boundaries are tested with negative cases.
- [ ] Anti-Spiral provides a brake and allowed action set; SRA decides the subsequent
      allocation without recursive handoff.
- [ ] TPlan retains Pulse arbitration, Mission identity, continuation, authority, and
      mutation ownership.
- [ ] The initial implementation does not globally replace TPlan `selection` or
      `subtraction`.
- [ ] using-mindthus routes by semantic resource competition rather than keywords.

### Evidence And Runtime Boundaries

- [ ] Validators report shape and evidence risk only.
- [ ] No script computes semantic priority, ROI, or allocation correctness.
- [ ] A shape pass is not reported as semantic approval.
- [ ] The first-release claim ceiling is explicit.
- [ ] Every applicable hybrid run records a context-admission ledger and sealed packet.
- [ ] Previous conclusions and advocacy are quarantined by default; user constraints
      remain constraints rather than factual proof.
- [ ] Blind judgment precedes state-aware reconciliation and uses packet-bound IDs.
- [ ] Same-context runs cannot claim fresh-context isolation.
- [ ] Pressure cases include positive, boundary, adversarial, contamination, and
      analysis-overhead controls.

### Project Readiness

- [ ] Method-layering tests cover the new skill.
- [ ] Packaging includes the intended SRA surfaces and excludes internal-only material.
- [ ] Test Lifecycle registry covers every new executable test exactly once.
- [ ] Full repository validation passes before merge.
- [ ] Two independent implementation audits confirm priority behavior and method
      ownership before release.

## Open Questions For Implementation Evidence

These questions should be answered by cases rather than by expanding the design before
coding:

1. Which Lite output fields are the smallest set that consistently changes action?
2. Does `SRA` remain the best public acronym after user-facing examples are tested?
3. How often does Candidate Horizon Probe surface a materially better alternative?
4. Which minimum candidate-card fields are truly necessary for Full mode?
5. Does a narrow TPlan `allocation_review` hook add value beyond existing continuation
   and Mission Review gates?
6. Which real-use cases demonstrate independent value over ordinary ranking, 3L5S,
   SELA, or TPlan selection?

## Release And Governance

This design authorizes implementation work through the registered issue and an isolated
branch or worktree. It does not by itself authorize a release.

The implementation should proceed in the order defined above:

1. standalone contract and pressure cases;
2. routing and packaging after contract acceptance;
3. TPlan integration as a separately reviewed follow-up.

Any project-level feature-freeze or real-use evidence governance still active at
implementation time must be resolved or explicitly superseded before merge. Release
work must preserve the project's Stable plus ROI Beta synchronization rule.
