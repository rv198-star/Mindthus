# TVG Value Profile Construction Guide

## Core

A TVG `value_profile` should be evaluated in two different ways:

1. **Single-pass profile power test**: how much useful control the profile provides before
   TVG runtime has a chance to rescue the artifact through repeated remediation.
2. **Loop-assisted production test**: whether TVG can eventually produce a usable artifact
   with the profile, and how many rounds that costs.

Do not collapse these claims. A weak profile can look strong if the agent repeatedly
repairs prompts, images, documents, or plans during the TVG loop. That may be acceptable
for production, but it is not evidence that the profile itself is strong.

## Profile Layers

Minimum valid profile:

```yaml
value_profile:
  value_semantics:
    good_means: []
    bad_means: []
    priority_order: []
    derived_axes: []
    evidence_basis: []
    profile_veto_constraints: []
```

Optional advanced layers:

- `realization_surface`: where value becomes observable and reviewable.
- `gain_policy`: which deepening moves are likely to create real value gain.

Use optional layers when the default TVG gain moves are not specific enough. Do not add
them merely to make the profile look more complete.

## Construction Order

Build profiles in this order:

1. Define `value_semantics` from independent sources, owner judgment, domain material,
   or explicit user constraints.
2. Add `realization_surface` only when the artifact has domain-specific reviewable units.
3. Add `gain_policy` only when the useful deepening moves differ from TVG's default
   evidence / trade-off / failure-path / claim-ceiling moves.
4. Run a single-pass profile power test.
5. If single-pass control is weak, revise the profile by abstracting the failure mode.
6. Then run a loop-assisted production test when the downstream task needs final output.

Do not build the profile by copying the target artifact, the flawed sample, generated
images, or a human reference prompt. Those artifacts may pressure-test the profile, but
they are not automatically profile sources.

## Single-Pass Profile Power Test

Use this test when constructing or revising a profile.

Conditions:

- fixed profile
- one prompt/document/artifact generation pass
- no TVG remediation loop
- no hidden hand repairs except safety wording or mechanical formatting
- source boundaries recorded

Record:

```yaml
single_pass_profile_power:
  profile_version: ""
  input_artifact_or_task: ""
  output_artifact: ""
  value_semantics_result: ""
  realization_surface_result: ""
  gain_policy_result: ""
  profile_control_power: strong | partial | weak | unknown
  residual_failure_modes:
    - ""
  claim_ceiling: ""
```

Interpretation:

- `strong`: the profile alone creates most of the needed control.
- `partial`: the profile gives useful direction but predictable failures remain.
- `weak`: success would require substantial TVG runtime rescue.
- `unknown`: the test is inconclusive because inputs, evidence, or review criteria are
  missing.

## Loop-Assisted Production Test

Use this test when the goal is to produce a usable downstream artifact.

Conditions:

- TVG loop is allowed
- each round records whether the change was a profile change, artifact change, prompt
  change, evidence change, or user-constraint change
- each round names the gate result: `return-remediate`,
  `freeze-with-review-bound-warning`, `blocked`, or `freeze`
- final claim separates profile control from runtime recovery

Record:

```yaml
loop_assisted_profile_use:
  profile_version: ""
  max_rounds_or_budget: ""
  rounds_used: 0
  round_records:
    - round: 1
      change_type: profile | artifact | prompt | evidence | user-constraint
      positive_value_hypothesis: ""
      gate_result: return-remediate | freeze-with-review-bound-warning | blocked | freeze
      residual_failure_modes: []
  runtime_rescue_cost: low | medium | high | unknown
  final_artifact_path: ""
  final_claim_ceiling: ""
```

Interpretation:

- If single-pass is strong and loop cost is low, the profile is operationally strong.
- If single-pass is weak but loop-assisted output succeeds, the runtime rescued the
  artifact; the profile still needs work or should be marked high-cost.
- If loop cost stays high across tasks, do not call the profile mature.
- If a veto remains triggered, do not freeze merely because output quality improved.

## Human Reference Boundary

Human references can be useful, but name their role precisely.

Allowed:

- calibrating thickness, granularity, handoff usefulness, or review structure
- exposing gaps in `realization_surface` or `gain_policy`
- serving as an evaluation target when source attribution is explicit

Not allowed:

- copying the human reference's concrete content into a reusable profile
- treating a human reference as domain/aesthetic evidence unless it independently
  contains that evidence
- using loop-assisted success against a human reference as proof that the profile is
  generally strong

Example: a thick director prompt may teach a storyboard profile about shot granularity
and reviewable screen relations. It does not, by itself, prove Shaw Brothers aesthetics.

## Gate Discipline

A profile gate is not a domain quality score. It is a cross-artifact exit protocol that
decides whether the current module should freeze, return for remediation, block on
missing input, or run one more value-gain round.

Gate is not owned by the profile. A profile contributes value-semantics checks,
observable surfaces, and gain-policy preferences, but the exit gate still includes TVG's
fixed bottom lines, module responsibility, downstream use, evidence boundaries, and
next-round positive-value judgment.

Use these gates across creative prompts, business documents, plans, handoffs, and
reviews:

1. `hard veto gate`: evidence honesty, claim ceilings, user constraints, safety
   boundaries, module-specific veto constraints, and profile veto constraints remain
   non-overridable.
2. `value-semantics fit gate`: the artifact shows enough of the active profile's
   `value_semantics` for its actual job, without treating longer output as value.
3. `downstream-use gate`: the downstream user can act, review, decide, render, or hand
   off without inventing missing critical truth.
4. `next-round positive-value gate`: another round is allowed only if there is a named
   move likely to improve value rather than merely increase compliance, polish, or
   thickness.

Profile construction gates then ask:

1. Is `value_semantics` independently sourced or explicitly user-supplied?
2. Are optional layers abstract enough to generalize beyond the test case?
3. Did a single-pass test show actual profile control, or did runtime repair do the work?
4. How many TVG rounds were required to reach acceptable output?
5. Are residual failure modes still profile problems, model limitations, missing evidence,
   or user taste questions?
6. What claim ceiling is supported: profile strength, loop-assisted production usefulness,
   or only a one-off artifact success?

Calibrate the gate against at least two artifact families before promoting it as general:

- In a Shaw storyboard prompt, the gate checks script fidelity, profile fit, reviewable
  shot/panel units, downstream renderability, and whether another prompt/image round has
  a concrete repair target. It may support a usable storyboard prompt while still carrying
  a review-bound warning about image-model drift.
- In an RPD price-raising document, the gate checks whether the thickened document
  connects price to buyer outcome, scope, proof or assumptions, alternatives, risk
  ownership, implementation path, and the buyer's decision. It must not invent ROI,
  customer facts, competitor facts, authority, or willingness to pay. The claim ceiling is
  that TVG supports a more credible price justification, not that the customer will accept
  the higher price.
  Claim ceiling: supports a more credible price justification, not that the customer will accept the higher price.

Scripts may validate record shape if a workflow adds these fields, but scripts must not
decide profile strength, gate success, aesthetic quality, business persuasiveness, runtime
cost, or exit state.
