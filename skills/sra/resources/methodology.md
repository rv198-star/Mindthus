# SRA / Scarce Resource Allocation / 稀缺资源优先分配 Methodology

## Purpose

SRA is a standalone Mindthus Judgment Kernel Skill for deciding where a shared scarce
resource goes now.

It applies when several problems, tasks, branches, projects, continuation choices, or
postures are all valid enough to consider, but they compete for the same limited time,
money, specialist capacity, management attention, risk budget, or opportunity window.

SRA does more than rank a list. It can:

- select a minimum sufficient bundle;
- protect hard gates and threshold-essential work;
- prioritize a small action that changes direction or removes a bottleneck;
- place work on a minimum maintenance line;
- defer or stop work explicitly;
- keep reserve capacity uncommitted;
- authorize only one bounded resource tranche;
- rerun the allocation when evidence, resources, risk, or time windows change.

Short rule:

> 先排除不可行，再保护达标必要项；方向、依赖、瓶颈和窗口决定先后；
> 组合价值决定本轮投哪套；边际价值决定下一份资源投哪里。

Execution shorthand:

> 收缩找出不能删的；回补决定下一份值得加的。

Every applicable SRA judgment uses this same semantic core. Lite performs one bounded
`micro-contraction` and one `micro-replenishment`; Full expands the same operations
across candidate bundles, resource channels, and realistic pressure scenarios.

SRA is not a universal priority scorer. It is an evidence-bounded allocation judgment.

## Why Priority Ranking Is Not Enough

A ranked list such as `A > B > C` hides several mechanisms that control real allocation:

- A and C may only work as a bundle.
- B may be a safety or compliance gate with little direct revenue.
- D may be a ten-minute direction test that prevents a month of wrong construction.
- A and B may use different non-contested resources and should run in parallel.
- The current task may look important only because it is already active.
- A large threshold-essential investment may look weaker than a tiny immediate task when
  comparison uses arbitrary one-hour units.
- Reserve capacity may be more valuable than filling every available slot.
- No available combination may meet both the target threshold and the risk floor.

SRA therefore owns allocation among sufficiently judgeable candidates under an explicit
shared resource constraint. It may return a partial order, parallel allocation,
conditional result, reserve posture, infeasible result, or blocked result rather than a
false total ranking.

## Core Judgment

SRA answers:

> Which valid work receives the current scarce resource, which work receives only the
> minimum needed to preserve operation or optionality, and which work is deferred or
> stopped?

The judgment is governed by this order:

1. hard gates and authority;
2. target-reaching feasibility;
3. threshold necessity;
4. direction, dependency, bottlenecks, and opportunity windows;
5. risk-adjusted value among feasible bundles;
6. marginal value of the next meaningful resource tranche;
7. option value of reserve capacity.

This order prevents a high-looking ROI from deleting required work, while also
preventing the label `necessary` from becoming a claim on unlimited resources.

## Entry Outcomes

SRA begins with one of four entry outcomes.

### `direct`

Use direct execution when:

- one obvious blocker or required next action exists;
- there is no credible competing use of the same resource;
- tasks use independent resources and can proceed in parallel;
- the choice is low-risk, reversible, and cheaper to try than to analyze;
- the work is a simple ordered checklist.

Direct is a successful intervention decision. It means the method correctly stayed out.

### `lite`

Use Lite for one bounded execution-time decision. Lite chooses the next action or
meaningful resource tranche and sets a short authorization horizon.

Typical questions:

- Should the current detail work continue?
- Should the engineer switch to the release blocker?
- Should a useful new idea enter the current delivery window?
- Should this artifact receive another strengthening round or move to maintenance?
- Should capacity remain reserved until a near-term event resolves?

### `full`

Use Full when the wrong allocation could consume a major resource block, invalidate
many downstream actions, close a valuable window, or create hard-to-reverse loss.

Typical triggers:

- multiple feasible bundles;
- multiple constrained resource pools;
- fixed investment thresholds or indivisible teams;
- direction-changing uncertainty;
- project, portfolio, or Mission-level reallocation;
- material switching cost or path dependency;
- major, high-blast-radius, or irreversible commitment;
- an authorization horizon longer than one bounded tranche or checkpoint.

### `blocked`

Use blocked when allocation would require inventing:

- the objective or target threshold;
- decision authority;
- a load-bearing fact;
- candidate contribution or resource demand;
- the common contested resource;
- the risk floor;
- a comparison that a plausible missing fact could reverse.

Blocked should request only the minimum missing input that can change the allocation.

## Analysis-Cost Gate

SRA itself consumes resources.

> Use a reasoning depth whose cost is lower than the plausible loss from a wrong
> allocation.

A reversible ten-minute choice should remain direct or Lite. A Sprint allocation, a
cash-runway decision, or an irreversible construction path may justify Full.

`auto` starts from Lite and expands only when a named escalation condition is
load-bearing. It is a mode selector, not a third analysis depth.

## Context-Calibrated Hybrid Runtime

SRA is independent from inherited conclusions, not from relevant context. The v0.3
runtime keeps the current objective, user constraints, authority, evidence, assumptions,
and real execution state while removing inherited decision authority from prior
conclusions, advocacy, ambient inference, and sunk-cost narrative.

The caller or an Agentic intake step supplies:

- situated wording for the real current decision;
- a sourced `challenge_projection` that preserves the allocation question while removing
  active-path identity, prior conclusions, and historical spend;
- separately sourced context fragments and challenge projections;
- declared resource pools, quantity contracts, capacities, and candidate demand.

Workflow:

1. validates declared question and context projections without attempting semantic text
   splitting;
2. records context admission and quarantine lanes;
3. validates measured, ordinal, and indivisible resource contracts;
4. rejects candidate cards that pre-label SRA roles or scores;
5. builds independent challenge and situated packets plus deterministic Prompt, schema,
   Dispatch, and command surfaces;
6. records one allocation-ledger posture per candidate;
7. requires explicit Full bundle assessments and selected-bundle membership;
8. compares candidate roles, bundle identity, resource commitments, reserve, missing
   information, and authorization as typed fields;
9. opens one targeted reconciliation only when the views materially conflict;
10. reconstructs state and final output from raw input plus valid recorded judgments.

Agentic SRA owns relevance, feasibility, candidate roles, necessity, bundle sufficiency,
contraction, replenishment, situated state interpretation, and conflict reconciliation.
Workflow owns deterministic structure and consequences. Evidence constrains claims.

View plans:

- `situated_only`: ordinary reversible Lite;
- `dual_view`: contaminated Lite and Full, with mutually hidden challenge and situated
  judgments;
- optional coverage review checks packet readiness but cannot choose allocation.

Agreement means the same typed commitment survived both views; it remains corroboration,
not proof. Conflict receives one bounded reconciliation that may remain conditional or
blocked. Fresh-context execution is a carrier property rather than proof of better
judgment. See `context-isolation.md`.

## Allocation Frame

Every applicable SRA judgment establishes the smallest sufficient frame:

| Field | Question |
|---|---|
| `parent_objective` | What result does this allocation serve? |
| `target_threshold` | What state counts as success in this window? |
| `time_window` | How long is this decision valid? |
| `risk_floor` | What safety, compliance, ethics, authority, survival, or other limit cannot be crossed? |
| `decision_owner` | Who can authorize allocation, stopping, or a target change? |
| `resource_pools` | Which specific resources are shared and scarce, what capacity exists, and under which measured, ordinal, or indivisible quantity contract? |
| `evidence_ceiling` | What can current evidence support, and what remains assumption? |

The target threshold remains fixed during allocation pressure tests. A cheaper survival
state does not silently replace the requested target. An authorized owner may change the
target, but that creates a new allocation decision.

## Candidate Horizon Probe

The active task has an unfair advantage: it is visible, already loaded into context, and
easy to continue. SRA counters that bias with a bounded Candidate Horizon Probe.

Scan for:

1. the current path;
2. a hard gate, blocker, or threshold-essential predecessor;
3. a direction-changing unknown, irreversible risk, or closing opportunity window;
4. the strongest feasible alternative contribution to the same objective;
5. maintain, reserve, defer, and stop postures.

Lite normally keeps two to four actionable candidates. Full may expand the set when
bundle construction or multiple resource channels require it.

The probe is not exhaustive portfolio discovery. It is a short protection against:

- active-task capture;
- first-alternative capture;
- omitted blockers;
- omitted stop and reserve options;
- mistaken assumption that every visible task must receive growth resources.

When a credible candidate lacks a load-bearing comparison field, request the minimum
candidate data instead of assigning a plausible-looking priority.

## Candidate Readiness

Full mode uses a minimum comparable candidate card:

```text
candidate_id
action_statement
expected_target_effect
resource_demand -> resource_id + exact | bounded | ordinal | indivisible quantity
depends_on
unlocks
substitutes_for
deadline_or_window
downside
reversibility
evidence_refs
assumption_refs
```

The input describes observable actions, relations, evidence, and claims. It must not
pre-label `hard_gate`, `threshold_essential`, `value_expanding`, another SRA role, or a
priority/ROI score; those are Agentic SRA outputs.

This is not a full 3L5S Definition. It is the minimum information needed to decide
whether candidates can share a comparison surface.

Candidate granularity must remain stable. Splitting one candidate into five subtasks
must not increase its allocation claim merely because it occupies more rows.

## Priority Order

### 1. Hard Gate

Hard gates include declared safety, compliance, ethics, authority, irreversible-loss
prevention, survival, or another bottom line.

A hard gate is not just a task with a high score. It controls whether ordinary value
comparison may proceed.

### 2. Feasible Bundle

A bundle is feasible when it can reach the target threshold inside the time window and
risk floor with the required level of evidential support.

Remove bundles that violate a hard gate or cannot reach the target before comparing
marginal value.

### 3. Threshold-Essential Work

A component is threshold-essential when removing it makes the current target-reaching
bundle no longer sufficiently supported.

Threshold-essential does not mean permanently important. Once the item reaches the
required evidence and completion level, more work on it becomes value-expanding and must
compete again.

### 4. Direction, Bottleneck, And Window

Small actions may deserve the first resource tranche when they:

- change the viable path;
- test a direction that could invalidate large downstream work;
- remove the dominant constraint;
- unlock several actions;
- prevent an irreversible loss;
- protect a closing opportunity window.

Task size is not priority.

### 5. Risk-Adjusted Bundle Value

Use risk-adjusted bundle value among remaining feasible bundles. Compare:

- objective contribution;
- downside and irreversibility;
- delay cost;
- evidence strength and success uncertainty;
- information value;
- optionality;
- resource demand by channel.

Use real quantitative data when it exists. Otherwise use explicit qualitative ordering.
Do not manufacture a common currency for money, safety, trust, authority, evidence, and
stakeholder values.

### 6. Marginal Tranche Value

The next resource unit is the next decision-relevant tranche, not an arbitrary hour,
dollar, token, or person.

Examples:

- one complete validation experiment;
- one engineer-day;
- one review cycle;
- one deliverable work package;
- the smallest team or budget block that crosses a fixed threshold.

Compare the smallest resource block capable of producing an observable result. This
protects threshold-essential work from being starved by tiny tasks with immediate but
shallow returns.

### 7. Reserve

Reserve is an explicit allocation posture. It may preserve:

- incident response capacity;
- recovery and rollback capacity;
- a likely near-term opportunity;
- option value while direction evidence arrives;
- survival under path volatility.

A reserve decision names:

```text
reserved_resource
reserve_reason
release_trigger
expiry_or_review_time
```

When the next tranche itself is `reserve`, the next-tranche and reserve records describe
one identical commitment. Workflow requires an exact typed match and counts it once.

## Candidate Roles

For the current allocation window, each candidate or bundle takes one primary role:

| Role | Meaning |
|---|---|
| `hard_gate` | Must be satisfied before ordinary value comparison. |
| `threshold_essential` | Required by the selected target-reaching bundle. |
| `enabler_or_bottleneck` | Removes a dominant constraint, changes direction, or unlocks multiple actions. |
| `value_expanding` | Improves the result beyond the current target threshold. |
| `maintenance_or_option` | Preserves operation, reversibility, or future choice at minimum cost. |
| `defer_or_stop` | Receives no current growth allocation. |

The role is contextual and time-bounded.

## Evidence-Bounded Minimum Sufficient Bundle

SRA seeks a `current minimum sufficient bundle`, not a universally minimal task set.

A bundle qualifies when, under current evidence, explicit assumptions, the declared
window, and the risk floor:

1. it supports reaching the target threshold with the required confidence;
2. removing any non-substitutable component makes that target judgment no longer
   sufficiently supported;
3. it excludes work that only improves appearance or formal completeness without
   changing target attainment, risk, evidence, or required optionality.

Consequences:

- backup, rollback, review, and redundancy may be essential;
- alternatives form separate bundles rather than one bundle containing every substitute;
- minimum does not mean maximally fragile;
- a bundle may be conditional on named evidence or authority;
- `infeasible` is correct when no bundle meets the unchanged target and risk floor;
- lowering the target requires an explicit new decision.

For each load-bearing necessity claim, record:

- why it is necessary now;
- the assumption and evidence supporting the claim;
- what would make the claim false or obsolete.

## Resource Model

Keep scarce resources as a vector:

- time;
- money;
- specialist capacity;
- general labor;
- management attention;
- risk or exposure budget;
- opportunity window;
- another explicitly named resource.

Before ranking, identify:

- which pool is actually contested;
- the dominant constraint;
- which resources are substitutable;
- which tasks can proceed in parallel;
- which tasks require a fixed or indivisible resource block.

Tasks that use independent non-contested resources do not need a forced global rank.

Runtime quantities preserve their native meaning:

- `measured`: exact or bounded amount in one declared unit with additive `sum`;
- `ordinal`: one level from a declared ordered scale with `exclusive` allocation;
- `indivisible`: one or more named resource blocks with block-set allocation.

Candidate demand, current allocation, bundle requirements, next tranche, reserve, and
investment ceiling all reference the same resource-pool contract. Workflow checks
mechanical compatibility, capacity, and each candidate's cumulative current-plus-next
commitment against its declared demand; Agentic SRA still decides semantic value.

The runtime records one allocation-ledger row per candidate:

```text
candidate_id
posture: floor | maintenance | candidate | defer | stop
current_allocations[]
reason
```

This single ledger replaces overlapping posture lists. `floor` and `maintenance` carry
nonzero current resource; `candidate`, `defer`, and `stop` carry zero.

## Lite Mode

### Lite Question

> Where should the next meaningful resource tranche go?

### Lite Mainline

1. Lock the smallest useful Allocation Frame.
2. Run the Candidate Horizon Probe.
3. Identify hard gates, threshold-essential work, and the strongest alternative.
4. Run one micro-contraction against the current path or target-reaching posture: cap,
   remove, downgrade, or maintain work until the next realistic reduction would break
   the unchanged target threshold or risk floor.
5. Name the resulting current floor and its first break point.
6. Run one micro-replenishment from that floor: compare the next meaningful tranche
   across the surviving current path, strongest alternative, and reserve posture.
7. Separate switching cost from sunk cost.
8. Choose `continue`, `switch`, `maintain`, `defer`, `stop`, or `reserve`.
9. Set the investment ceiling, authorization horizon, displaced-work decision, and
   reranking trigger.

A Lite answer that only compares two attractive tasks without exposing both the current
floor and the next-tranche choice is ordinary prioritization, not complete SRA fidelity.

### Micro Contraction

Ask:

> What can be removed, capped, downgraded, or moved to maintenance while the current
> target threshold and risk floor remain supported?

Stop at the first realistic reduction that would threaten the target, risk floor, or a
necessary option. This identifies the `current_floor`; it does not prove universal
minimality.

### Micro Replenishment

Starting from the current floor, ask:

> Which one next meaningful tranche best protects the threshold, removes the bottleneck,
> changes direction, protects the window, creates decision-relevant evidence, or expands
> objective value?

The answer becomes the bounded next allocation. Lite stops after this comparison and a
reranking trigger.

### Lite Output

```text
Decision: continue | switch | maintain | defer | stop | reserve
Why now: objective-relevant reason
Current floor: post-contraction minimum for this bounded decision
Next tranche: replenishment choice from the current floor
Investment ceiling: maximum current commitment
Authorization horizon: one_action | one_tranche | until_named_checkpoint
Defer/stop: displaced work
Rerank trigger: evidence, resource, risk, threshold, or window change
```

Ordinary user-facing output should fit in one paragraph or a short block.

### Lite Example: Release Threshold Versus Polish

Situation:

- product page is usable and meets the release threshold;
- animation polish can still improve it;
- payment validation still blocks launch;
- the same engineer owns both.

Decision:

> Switch the next engineer-day to payment validation. Keep the product page on a
> release-blocking-defect-only maintenance line and defer animation polish. Reopen the
> allocation when payment validation passes or the page develops a release blocker.

The micro-contraction places the page on a release-blocking-defect-only floor. The
micro-replenishment then sends the next engineer-day to payment validation. The method
does not call polish worthless; it states that polish no longer controls the current
target threshold.

### Lite Escalation

Escalate to Full when any load-bearing condition appears:

- direction-changing uncertainty alters the target or candidate set;
- multiple feasible bundles exist;
- commitment is large, high-blast-radius, or hard to reverse;
- fixed thresholds, bundle effects, or indivisible investments control value;
- multiple constrained resource pools produce different results;
- switching cost or path dependency is material;
- a credible alternative is missing or incomparable;
- Lite cannot distinguish continue, switch, stop, or reserve;
- allocation authorizes more than one bounded tranche or checkpoint.

## Full Mode

### Full Mainline

1. Lock the Allocation Frame.
2. Identify contested resource pools and the dominant constraint.
3. Build minimum comparable candidate cards.
4. Resolve or route direction-changing uncertainty only to the point needed for current
   action.
5. Construct one or more evidence-bounded minimum sufficient bundles.
6. Remove infeasible and dominated bundles.
7. Run resource contraction.
8. Run resource replenishment.
9. Select the risk-adjusted feasible allocation and reserve.
10. State main attack, necessary support, minimum maintenance, explicit defer, explicit
    stop, next tranche, authorization, decision lifetime, and reranking triggers.

### Direction-Changing Uncertainty Gate

Give an unknown early resource only when different plausible answers would:

- change the target;
- alter the feasible bundle set;
- reverse the main path;
- invalidate a large downstream investment;
- expose a large or irreversible loss.

The goal is `minimum decision-enabling validation`: enough evidence for current action,
not exhaustive certainty.

Route the unknown to its owner:

| Unknown | Owner |
|---|---|
| Missing facts | Evidence acquisition |
| Unstable proposition or false binary | EDSP |
| System efficiency versus local advantage | SELA |
| Carrier, exposure, and path volatility | MPG |
| Unclear problem or candidate | 3L5S |
| Agentic controller mismatch | WAE |
| Stakeholder authority or target trade-off | Human decision / Decision Context Calibration |

The returned result becomes an allocation constraint. SRA remains owner only for the
cross-candidate resource decision.

### Resource Contraction

Hold the target threshold and risk floor fixed while applying realistic resource
pressure.

Ask:

- Which components remain indispensable?
- Which removal changes direction or invalidates many downstream actions?
- Which items can be substituted, combined, parallelized, or downgraded?
- Which items only improve quality beyond the threshold?
- Which resource channel breaks the bundle first?

Record retain, replace, defer, and remove reasons. Contraction reveals:

- threshold-essential components;
- hidden dependencies;
- the dominant constraint;
- false necessities;
- the lowest feasible resource boundary.

### Resource Replenishment

Start from the lowest feasible bundle and add one meaningful tranche at a time.

Ask:

- Which tranche removes the bottleneck?
- Which tranche unlocks the most downstream options?
- Which tranche produces the highest decision-relevant information gain?
- Which tranche protects the most valuable closing window?
- Which tranche creates the largest objective-relevant marginal gain?

If contraction removal order and replenishment addition order conflict, inspect:

- dependency;
- complementarity;
- fixed threshold;
- switching cost;
- unresolved uncertainty.

Preserve a partial or conditional order rather than forcing a false total rank.

### Feasibility And Dominance

1. Remove bundles violating a hard gate.
2. Remove bundles unable to reach the target threshold.
3. Remove a bundle when another feasible or conditional bundle uses no more of every
   contested resource and is strictly better on at least one load-bearing dimension.
4. Keep dominance references acyclic and evidence-linked.
5. Compare the remaining non-dominated bundles by evidence, downside, delay cost,
   information value, optionality, and objective contribution.
6. Return a conditional allocation when no single bundle dominates across plausible
   states.

A Full `infeasible` outcome means every bundle is coded infeasible or unresolved; a
feasible bundle cannot be hidden behind a `dominated` label. An infeasible bundle may
contain members also assessed infeasible. The selected bundle's resource vector bounds
its members' current and next commitment. `floor` belongs to the selected bundle, while
maintenance may remain outside it.

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

## Switching Cost And Sunk Cost

Compare future consequences from the current state:

- `sunk_cost`: already spent and unrecoverable; it does not justify continuation;
- `switching_cost`: new future cost required to change paths;
- `reusable_asset`: completed work that retains future value;
- `remaining_cost`: additional resource required to finish the current path.

This prevents both sunk-cost capture and reckless path switching.

## Stop Conditions

### Lite Stop

Stop after one bounded allocation is authorized and a reranking trigger is named. Do not
keep searching for a theoretically perfect alternative.

### Full Stop

Stop when:

1. the selected bundle remains stable across adjacent realistic pressure scenarios;
2. the first meaningful tranche is clear;
3. remaining uncertainty cannot change the current action;
4. another analysis round has no named positive-value hypothesis;
5. execution evidence and reranking triggers can handle the residual uncertainty.

## Method Ownership

### 3L5S

3L5S owns problem discovery, definition, and decomposition. SRA owns allocation among
minimally comparable candidates.

```text
3L5S makes candidates judgeable
    -> SRA allocates
    -> selected work returns to 3L5S when deeper definition or decomposition is needed
```

Do not oscillate between methods without new evidence. SRA requests only the minimum
candidate fields needed to allocate.

### EDSP

EDSP owns unstable propositions, false binaries, and structural coordinate systems. SRA
may use EDSP output as an allocation constraint.

### SELA

SELA owns long-term system-efficiency versus local-advantage direction pressure. SRA
owns current allocation given the available direction evidence.

### MPG

SRA owns competition among problems, tasks, objectives, or action bundles sharing a
resource pool. MPG owns carrier, exposure, timing, optionality, and path posture for one
selected mainline. SRA does not redesign the carrier.

### WAE

SRA uses a WAE-shaped hybrid runtime: Workflow owns admission mechanics, candidate
structural alignment, packet hashes, typed comparison, status transitions, and reference
checks; Agentic SRA owns semantic allocation and conflict reconciliation; Evidence
constrains claims. WAE re-enters only when those controller boundaries are misassigned.

### TVG

TVG owns another value-gain round inside one bounded artifact. SRA owns whether the next
scarce-resource tranche goes to that artifact or an external task.

### Anti-Spiral

Anti-Spiral detects repeated local repair and constrains the allowed action set. SRA
allocates the released resource. Use one handoff, not recursive calls.

### TPlan

TPlan owns Mission state, evidence records, Pulse arbitration, Mission identity,
continuation, authority, recovery, and task mutation.

SRA may provide semantic allocation only when real task or branch candidates compete for
a common resource. It does not replace:

- Pulse Gate Arbitration;
- residual Mission selection;
- Linear Continuation Gate;
- mutation authority.

A later integration may evaluate a narrow `allocation_review` hook after standalone SRA
behavior is validated.

## Human-Readable First

Start with what should happen now:

> Stop animation polish and move the next engineer-day to payment validation.

Then explain why, what receives maintenance, what is deferred, and what trigger reopens
the decision. Internal field names belong in audit, validation, or handoff views.

## Claim Ceiling

Allowed runtime claim:

> SRA provides lightweight and expanded contracts for making scarce-resource allocation
> explicit, evidence-bounded, and action-changing, with typed resource pools, explicit
> Full bundle assessments, deterministic allocation invariants, and tested routing
> boundaries against neighboring Mindthus methods.

The runtime does not claim that SRA:

- always finds the correct priority;
- maximizes ROI;
- computes an optimal allocation;
- proves real-world business value through pressure tests;
- turns a shape-valid artifact into semantic approval.

## Script Boundary

Scripts may:

- validate caller-supplied situated wording and challenge projections;
- build a declared-fragment context-admission ledger and shared decision base;
- align candidate cards and create input-order-independent challenge aliases;
- validate measured, ordinal, and indivisible resource contracts;
- bind actual allocation and bundle requirements to candidate demand, including each
  candidate's cumulative current-plus-next commitment;
- reject pre-decided semantic role or score fields;
- generate independent challenge and situated packets plus deterministic Prompt, schema,
  Dispatch, and command surfaces;
- validate one candidate posture per allocation-ledger row;
- validate Full bundle members, coded feasibility/dominance consistency, acyclic
  dominance references, selected-bundle postures, and resource capacity;
- compare candidate roles, bundle identity, resources, reserve, missing information, and
  authorization without selecting a winner;
- generate one targeted reconciliation packet on conflict;
- reconstruct the exact run-state shape, canonical claim boundary, plans, hashes,
  comparison, reconciliation, final source, carrier receipts, and trace;
- repair derived artifacts only while prepared-input and judgment-event anchors still
  match, without changing Agentic judgments;
- check that sunk cost is rejected as a continuation basis;
- render terminal authorization without recomputing priority;
- validate method-fidelity evidence by reference to the canonical runtime decision.

Scripts do not:

- semantically split raw conversation text into projections;
- classify semantic context truth or guarantee complete context;
- choose the priority;
- compute semantic ROI;
- decide whether a bundle is genuinely sufficient;
- prove a hard gate applies;
- determine the strongest alternative;
- authorize or mutate a real project or TPlan allocation;
- claim fresh-context isolation without an observable carrier boundary.

Prepared v0.2 run directories are version-bound and are not resumed under v0.3. The
caller prepares a new run from the source decision context.
