# SRA Contraction–Replenishment Pressure Tests

Status: Phase 1 standalone behavior surface
Issue: #156

These cases test whether SRA changes resource allocation through its defining
contraction–replenishment loop. They do not prove universally correct priority, business
ROI, or mathematical optimality.

## Review Protocol

For every case, review the answer in this order:

1. Did SRA actually own the judgment, or should execution or a neighboring method own it?
2. If SRA owned it, were the target threshold and risk floor held constant?
3. Were target-reaching bundle hypotheses contracted before any bundle was called the
   current floor or minimum?
4. Did the answer include a replenishment result after contraction?
5. Did the result change the next tranche, ceiling, maintenance, reserve, defer/stop, or
   reranking behavior?
6. Did the visible answer remain shorter than the internal audit structure?

A fluent priority explanation fails when it does not expose both a contraction result
and a replenishment result.

## Positive Cases

### SRA-P01 — Launch Blocker Versus Visual Polish

**Prompt shape**

A product page is already usable. One engineer-day can either complete payment
validation, which still blocks launch, or improve visual polish.

**Expected owner**

SRA, ordinary-depth pass.

**Expected contraction**

Contract the launch-readiness bundle while holding the launch threshold fixed. Defer
additional polish; retain payment validation and minimum rollback/release evidence.
The first break point is removal of payment validation.

**Expected replenishment**

Allocate the next engineer-day to payment validation because it removes the launch
bottleneck. Authorize only through that checkpoint, then rerank.

**Failure signs**

- merely says payment is “higher priority”;
- calls a bundle minimum before testing removal;
- authorizes open-ended launch work;
- does not explicitly defer polish.

### SRA-P02 — Sprint With Several Resource Pools

**Prompt shape**

A Sprint contains a compliance deadline, a severe production defect, technical debt,
and new features. Money is available, but only one compliance specialist and two general
engineers are available.

**Expected owner**

SRA, expanded pass.

**Expected contraction**

Construct separate target-reaching Sprint bundles. Keep resources as a vector. Expose
which work needs the compliance specialist, which can use general engineers, and which
can proceed in parallel. Do not trade the compliance gate against feature value in one
score.

**Expected replenishment**

Select the next specialist and engineer tranches separately. Return parallel or partial
allocation when resource channels do not conflict.

**Failure signs**

- collapses all capacity into “team points”;
- serializes independent work;
- ranks compliance by revenue ROI;
- allocates every resource with no reserve or rerank trigger.

### SRA-P03 — Platform Build Versus Customer Validation

**Prompt shape**

A startup has enough cash for a large platform foundation or a smaller customer
validation bundle. The platform produces no usable evidence until a fixed team and
three-month threshold is crossed.

**Expected owner**

SRA unless the product direction itself is structurally undefined, in which case the
minimum decision-enabling uncertainty routes outward and returns as a constraint.

**Expected contraction**

Treat the platform threshold as one indivisible tranche rather than three one-month
fragments. Contract both target-reaching hypotheses without silently changing the
startup objective to “spend less.”

**Expected replenishment**

Compare the complete platform threshold with the customer-validation tranche by target
contribution, information value, downside, and optionality. A conditional result is
acceptable.

**Failure signs**

- systematically favors the smaller action because it is cheaper;
- breaks an indivisible threshold into misleading increments;
- changes the target to survival without owner authorization;
- invents precise ROI from qualitative evidence.

### SRA-P04 — Research Evidence Under Deadline

**Prompt shape**

A research report can receive another broad literature sweep, a focused validation of
its decisive claim, or more presentation polish before a deadline.

**Expected owner**

SRA after the claim and delivery threshold are sufficiently defined.

**Expected contraction**

Find the smallest delivery bundle that still supports the report’s declared claim and
review standard. Presentation polish may remain outside the floor; decisive evidence may
remain inside it.

**Expected replenishment**

Choose the next bounded validation or writing tranche that changes evidence support or
submission readiness. Name the evidence ceiling.

**Failure signs**

- equates more sources with better evidence;
- optimizes presentation while the decisive claim remains unsupported;
- reports shape completeness as research truth.

### SRA-P05 — Personal Projects And Recovery Capacity

**Prompt shape**

One person has several valuable long-term projects competing for attention and recovery
capacity. Continuing all of them at growth pace is unsustainable.

**Expected owner**

SRA for current cross-project allocation. MPG may constrain one selected project if its
carrier or exposure path is the active uncertainty.

**Expected contraction**

Find a floor bundle that protects health/recovery limits, essential obligations, and the
minimum maintenance needed to preserve valuable options. Do not treat recovery capacity
as interchangeable with money.

**Expected replenishment**

Allocate the next sustainable attention tranche to the project with the strongest
current bottleneck, window, information value, or objective contribution. Explicitly
maintain, defer, stop, or reserve the rest.

**Failure signs**

- maximizes nominal project output while violating recovery limits;
- gives every project a token allocation to avoid making a decision;
- treats a long-running project’s sunk effort as a continuation reason.

## Direct And Neighboring-Method Boundaries

### SRA-B01 — One Known Release Blocker

One release blocker exists and no credible alternative use of the same engineer is
present.

**Expected:** direct execution. Do not run SRA merely because a resource exists.

### SRA-B02 — Undefined Problems

The only input is “the system is bad; which problem should we fix first?” Candidate
problems are not yet minimally defined.

**Expected:** 3L5S Discovery/Definition before allocation.

### SRA-B03 — Unstable A/B Proposition

Two options look valid because the comparison dimensions and proposition are unstable.
No reliable target-reaching bundles can yet be formed.

**Expected:** EDSP owns the structural judgment; SRA may use the result later.

### SRA-B04 — Long-Term Paradigm Direction

The question is whether a scalable AI system will eventually displace a locally
excellent manual process.

**Expected:** SELA owns direction. SRA applies only if current limited resources must
then be allocated among concrete actions.

### SRA-B05 — Carrying One Selected Mainline

One mainline has already been selected. The remaining question is how much exposure to
accept, which vehicle to use, and when to hedge or exit under path volatility.

**Expected:** MPG.

### SRA-B06 — Controller Mismatch

A script, agent, evidence gate, and human reviewer control the wrong parts of an
agentic workflow.

**Expected:** WAE.

### SRA-B07 — Another Round Inside One Artifact

A single bounded document is already formed; the only question is whether another
strengthening round adds value under its active quality profile.

**Expected:** TVG. SRA enters only when that round competes with an external resource use.

### SRA-B08 — TPlan Pulse Arbitration

A Mission Pulse must choose which deterministic Gate handles a runtime signal.

**Expected:** TPlan workflow. SRA does not replace Pulse arbitration.

### SRA-B09 — Independent Parallel Resources

A designer and a database engineer can work independently, and neither task uses the
other’s constrained pool.

**Expected:** parallel execution, not a false competition.

### SRA-B10 — Ten-Minute Reversible Choice

Two local implementation options are cheap to try, easy to roll back, and unlikely to
consume downstream work.

**Expected:** direct experiment. Analysis cost exceeds plausible allocation loss.

## Adversarial Cases

### SRA-A01 — Active-Task Capture

The current task is visible and nearly complete. A release-critical blocker sits outside
the immediate frame.

**Expected:** Candidate Horizon exposes the blocker before contraction. Near-completion
alone does not grant the current task the next tranche.

### SRA-A02 — Granularity Manipulation

Candidate A is represented as eight subtasks; candidate B is represented as one bundle.

**Expected:** compare stable-granularity bundles. Row count has no allocation weight.

### SRA-A03 — Sunk-Cost Capture

Most historical budget has already been spent on the current path. Switching now has a
smaller new cost than finishing it.

**Expected:** separate sunk cost, switching cost, reusable assets, and remaining cost.
Compare future consequences from the current state.

### SRA-A04 — Fixed Threshold

A validation produces value only after three uninterrupted days. One-day fragments
produce no evidence.

**Expected:** the meaningful tranche is the three-day threshold. SRA must not starve it
by comparing arbitrary single-day units.

### SRA-A05 — Multiple Resource Channels

A task has budget but no available specialist. Another task uses general labor and can
proceed immediately.

**Expected:** keep resource channels separate and permit partial or parallel allocation.
Money does not substitute for unavailable expertise unless a real substitution path is
named.

### SRA-A06 — No Feasible Bundle

Every bundle either misses the unchanged target threshold or violates the risk floor.

**Expected:** `infeasible`. Do not select the cheapest failure and call it the target.

### SRA-A07 — Contraction/Replenishment Asymmetry

The first component removed under pressure is not the first component worth adding back,
because a different tranche crosses a fixed threshold and unlocks several options.

**Expected:** preserve the asymmetric orders and explain threshold, complementarity,
switching cost, path dependency, or unresolved uncertainty.

### SRA-A08 — Hard Limit With No Direct ROI

Mandatory compliance work has no direct revenue contribution.

**Expected:** treat compliance as qualification/risk-floor work, not a low-ROI candidate
inside a score.

### SRA-A09 — Reserve Option

Allocating all available capacity now would remove incident response and rollback
capacity before a likely volatile event.

**Expected:** explicit reserve with amount, reason, release trigger, and review/expiry.

### SRA-A10 — Hidden Target Reduction

A cheaper bundle can only “keep the project alive,” while the declared target is a
working release.

**Expected:** reject the cheaper bundle as non-target-reaching unless the decision owner
explicitly authorizes a new target.

## Root-Cause Regression Cases

### SRA-R01 — Applicable But No Contraction

An answer compares the current task with one alternative, chooses one, and names a rerank
trigger. It contains no removal/reduction/substitution test and no first break point.

**Expected:** fidelity failure. This is ordinary prioritization, not SRA.

### SRA-R02 — Applicable But No Replenishment

An answer finds a lowest feasible bundle but never decides the next meaningful resource
tranche.

**Expected:** fidelity failure. Contraction alone does not complete allocation.

### SRA-R03 — Minimum Declared Before Contraction

A bundle is called the “minimum sufficient bundle” before any pressure operation is
performed; later analysis only defends it.

**Expected:** fidelity failure. It may be a target-reaching hypothesis, but the floor is
discovered only post-contraction.

### SRA-R04 — Target Changes During Contraction

The method removes work until it reaches a cheaper plan, then quietly redefines success.

**Expected:** fidelity failure unless an authorized target change creates a new frame.

### SRA-R05 — Mixed Universal Priority Ladder

An answer uses one fixed ladder to combine hard gates, feasible bundles, necessities,
bottlenecks, ROI, marginal value, and reserve as though they were one logical type.

**Expected:** review failure. Qualification, sequencing, roles, selection, and
replenishment remain separate.

### SRA-R06 — Shape Pass Reported As Semantic Approval

A validator passes and the answer claims the selected bundle is therefore correct or ROI
optimal.

**Expected:** claim-boundary failure. Shape validation does not approve semantic
allocation quality.

## Phase 1 Exit

Phase 1 is ready for routing and packaging work only when:

- all standalone files exist and agree on the same contraction–replenishment core;
- the passing template validates;
- missing contraction, missing replenishment, predeclared floor, and target-change
  fixtures fail deterministically;
- positive, boundary, adversarial, and root-cause cases are represented;
- no standalone SRA contract requires a Lite path that omits the core;
- no standalone SRA contract requires the former mixed universal priority ladder.
