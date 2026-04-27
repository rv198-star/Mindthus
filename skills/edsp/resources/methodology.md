# EDSP / Extreme Deduction + Scenario Projection

## Purpose

This document defines EDSP, a project-level diagnostic method for ambiguous judgment problems where both `A` and `B` initially seem plausible.

`EDSP` means `Extreme Deduction + Scenario Projection` (`极限推演 + 场景投影`).

It is normally used inside the primary `3L5S` working method when a Discovery or Definition layer exposes a fuzzy structural/configuration judgment. Use it when the task needs fast structural diagnosis, proposition testing, trend reading, or concrete option selection.

This is a reasoning method, not a document-shaping template and not a replacement for BTGSB evidence, falsifiability, or action landing. Its value is judged by whether it improves applied decisions and output quality.

## Method Positioning

> **Extreme Deduction** turns a continuous, ambiguous judgment problem into a discrete positioning problem through extreme projection, then uses real-world drift vectors to locate the truth.

> **L2 Scenario Projection** projects concrete scenarios into an already-built discrete coordinate system and outputs actionable selection guidance.

Scenario Projection is a supplement to Extreme Deduction, not a peer method. Together they form EDSP and can be used inside 3L5S:

- `Extreme Deduction` builds the skeleton — it answers `what is this`
- `L2 Scenario Projection` adds flesh — it answers `what should we choose here`

If the skeleton is not stable, adding flesh only makes the result drift in the wrong direction.

## When To Use / When Not To Use

### Use When

Use this method when facing questions like:

- `A also seems right, B also seems right; which is actually better?`
- `Is this a real binary choice, or is the question itself malformed?`
- `Should this be decided structurally, or does it depend on scenario boundaries?`
- `Which option is becoming the natural mainline under current drift?`
- `How should a general principle land in concrete service, skill, phase, or runtime choices?`

### Do Not Use It To

Do not use this method to:

- replace 3L5S evidence acquisition, falsifiability, or action landing
- replace domain research, runtime proof, or stakeholder judgment when those are the actual missing inputs
- make a malformed coordinate system look rigorous
- force static snapshots onto open, dynamic, game-theoretic, or long-cycle phase-change problems
- produce elegant structure that does not improve applied decisions or output quality

### Trigger Question

> `Inside the active 3L5S layer, is this a structure problem, or a configuration problem?`

## L1 Extreme Deduction（Structure Layer）

### Core Action

Turn a fuzzy continuous space into a finite set of discrete single-pole outcomes through extreme projection, then locate the current reality by reading drift.

```text
[Phenomenon X, continuous ambiguity]
        │
        ▼
①  Dimension decomposition: identify 2–7 key variables
        │
        ▼
②  Extreme projection: push each variable to 0 / ∞ / ± extremes
        │
        ▼
③  Outcome collapse: derive N discrete single-pole outcomes, usually N ≤ 5
        │
        ▼   ← coordinate system is built here
        ▼
④  Drift reading: observe which pole reality is currently moving toward
        │
        ▼
⑤  Positioning / diagnosis: locate the judgment or reveal that the proposition is synthetic
```

Steps ①②③ are `geometry`: they discretize the fuzzy space into a coordinate system.

Steps ④⑤ are `physics`: they read motion inside that coordinate system.

The heart of the method is the bite between geometry and physics.

### Procedure

1. `Dimension decomposition`
   - identify 2–7 variables that actually drive the judgment
   - prefer variables that change the conclusion when pushed to extremes
   - avoid decorative dimensions that only rename the same uncertainty
2. `Extreme projection`
   - push each variable to `0`, `∞`, or positive / negative extremes
   - ask what the world becomes if this variable dominates completely
   - do not stop at moderate cases; moderation belongs to L2
3. `Outcome collapse`
   - collapse the extreme projections into discrete outcomes
   - typical outcomes fall into one of five forms:
     - single-pole `A`
     - single-pole `B`
     - independent third party `C`
     - shared kernel
     - pseudo-proposition, where `X` is actually a composite object
4. `Drift reading`
   - observe which outcome reality is moving toward now
   - read incentives, cost curves, failure modes, evidence direction, adoption pressure, and operational friction
5. `Positioning / diagnosis`
   - if reality collapses toward one pole, give the structural judgment
   - if no unique pole emerges, diagnose that the original question is wrong, underspecified, or scenario-dependent

### L1 Stop Condition

Stop at L1 when the task is:

- structural judgment
- proposition diagnosis
- trend identification
- deciding whether a binary is real or synthetic
- determining that a question needs a third axis or shared-kernel framing

If L1 produces a stable structural answer, do not run L2 just to make the output look more detailed.

## L2 Scenario Projection（Scenario Layer）

### Core Action

Receive the L1 output, project concrete scenarios into the coordinate system built by L1, and derive actionable selection guidance.

L2 does not start from a blank whiteboard. It must work inside the coordinate system built by L1.

The order cannot be reversed: without a coordinate system, there is nowhere to project.

### Interface: What L1 Hands To L2

L1 must hand three things to L2:

1. `coordinate-axis definition`
   - which dimensions are truly decisive
   - L1 has already filtered these for L2
2. `discrete outcome set`
   - the answer space has collapsed into a finite set
   - L2 should not reopen infinite options by default
3. `drift prior`
   - which outcome reality is currently moving toward
   - this is a strong prior that narrows L2 search

If any of these three are missing, do not pretend L2 can produce reliable scenario guidance.

### When To Enable L2

Enable L2 only after L1 has built a usable coordinate system and the remaining task is concrete selection.

Use L2 when the question becomes:

- `Which option should this specific scenario choose?`
- `Where is the boundary between A and B in practice?`
- `Which service, runtime, skill, phase, or operator path should use which control mode?`
- `How should a principle become an actionable selection guide?`

### Three-Step Procedure

1. `Scenario dimensionalization`
   - list variables that describe real scenarios
   - important: these are variables of the world the user faces, not variables of the abstract problem itself
   - examples include task structure, tolerance for error, cost, iteration frequency, evidence availability, reversibility, and operational load
2. `Per-scenario projection`
   - project each scenario into the coordinate system built by L1
   - use scenario variable values to judge which quadrant, pole, hybrid, third axis, or shared kernel it lands on
   - state the trade-off curve, not only the final label
3. `Boundary fitting`
   - accumulate projected scenarios until usage boundaries naturally emerge
   - turn the boundary into decision trees, selection rules, and anti-patterns

### L2 Stop Condition

Stop L2 when:

- concrete scenarios can be classified consistently
- boundary rules are explainable without memorizing cases
- selection guidance is usable by future operators
- adding more scenarios no longer changes the boundary materially

If L2 repeatedly fails to choose, return to L1 and rebuild the coordinate system.

## Decision Rule: Ask One Question First

When a 3L5S layer exposes a fuzzy judgment, first ask:

> `Inside the active 3L5S layer, is this a structure problem, or a configuration problem?`

| Problem Type | Signal | Method |
|---|---|---|
| `Structure problem` | asks `what is X really`, `where is the boundary`, or `how many things is this actually` | `L1`, then stop |
| `Configuration problem` | structure is already clear; asks which configuration fits this concrete scenario | `L1 → L2` |
| `Mixed problem` | looks like configuration, but repeated selection attempts fail | return to `L1` and rebuild the coordinate system |

The third case is the most important: when a configuration problem repeatedly cannot be solved, the structure problem is usually unresolved. Forcing L2 at that point wastes effort.

## Integration Diagram

```text
Fuzzy phenomenon
   │
   ▼
[L1 Extreme Deduction] ──► discrete skeleton + drift prior
   │
   │ Is the decision now qualitatively clear enough?
   ├── Yes ──► output diagnosis / proposition judgment, then stop
   │
   └── No ──┐
            ▼
   Concrete scenario description ──► [L2 Scenario Projection]
                                      │
                                      ▼
                         scenario → quadrant mapping
                         + decision tree
                         + anti-patterns
                                      │
                                      │ Are numbers required?
                                      ├── No ──► engineering / product decision, then stop
                                      └── Yes ──► [L3 Quantitative Modeling], outside this method
```

## Trigger Rules

- `Structural judgment / proposition diagnosis / trend identification` → stop at `L1` and return to the active 3L5S layer
- `Concrete scenario selection / service-boundary landing` → run `L1 → L2`, then return to the active 3L5S layer
- `L2 repeatedly cannot choose` → return to `L1` and rebuild the coordinate system before continuing BTGSB
- `Evidence is missing` → acquire evidence before pretending L1 or L2 can decide
- `The output becomes elegant but not useful` → treat the method use as failed

## Anti-Patterns

| Anti-Pattern | Symptom |
|---|---|
| Using L1 output as if it were L2 guidance | treats a pseudo-proposition diagnosis as an actionable selection guide |
| Skipping L1 and jumping directly to L2 | scenario analysis becomes fishing in open water because there is no coordinate system |
| Choosing the wrong L1 dimensions | the skeleton is wrong, so more precise L2 projection only deepens the error |
| Mistaking skeleton clarity for skeleton correctness | the clean feel of the method suppresses doubt; this is the most dangerous failure mode |
| Forcing the method onto open, dynamic, or game-theoretic problems | a static snapshot method is misapplied to reflexive systems, games, or long-cycle phase changes |
| Treating elegance as output value | the result becomes easier to explain but no more useful in practice |

## Limits

This method optimizes how to think about what the operator can already see. It cannot optimize how much the operator is able to see.

> `The ceiling of the method is the ceiling of the operator's field of vision.`

This gap cannot be fixed inside the method itself. It must be compensated outside the method through curiosity, humility, evidence acquisition, and the ability to be surprised.

## Risk Warnings

- A clear skeleton does not mean the skeleton is correct.
- The ceiling of the method is the ceiling of the operator's field of vision.
- Bad dimension decomposition makes every later step look rigorous but wrong.
- L2 cannot repair a malformed L1 coordinate system.
- Scenario projection can overfit to remembered examples if the boundary is not generalized.
- This method should expose ambiguity, not hide it under sharper language.

## One-Line Summary

> `L1 builds the skeleton: push the problem to extremes, see how it collapses, then read which outcome reality is drifting toward. If it does not drift, the question is probably wrong.`

> `L2 adds flesh: project scenarios onto the skeleton, and the quadrant boundaries naturally emerge.`

## Minimum Evidence Record

When this method materially affects a decision, record:

- `question`
- `L1_dimensions`
- `extreme_projections`
- `collapsed_outcomes`
- `drift_reading`
- `L1_position_or_diagnosis`
- `L2_scenarios` when L2 is used
- `scenario_boundary` when L2 is used
- `decision_effect`
- `remaining_uncertainty`

Do not claim material use if the method name appears but the dimensions, projections, drift, or scenario boundary did not change the conclusion.
