# TVG Product Surface Taste Profile Pilot — 2026-06-14

## Purpose

This is a local pilot for issue #47. It tests whether TVG + a scoped profile can mimic
part of a taste-skill-style workflow in one bounded scenario:

- identify generic AI/product-surface bad smells;
- tie critique to visible surface units;
- rewrite the surface without inventing product facts;
- record whether value gain came from the profile or from TVG loop rescue.

Claim ceiling: this supports only a local probe. It does not prove that Mindthus has
general visual taste, product-design judgment, or parity with a specialized taste skill.

## Profile

Profile path:

`skills/tvg/resources/value-profiles/product-surface-taste-review.md`

Mode: `supplied`

Profile scope: product-surface copy and design-direction artifacts such as landing-page
hero copy, product UI concepts, or small screen descriptions.

## Input Artifact

Artifact type: generated landing-page hero concept.

Baseline:

> MeetFlow AI helps teams work smarter with beautiful automated meeting notes. Capture
> every conversation, unlock insights, and collaborate effortlessly. A premium dark
> gradient hero shows floating glass cards with AI summaries, action items, analytics,
> and team avatars. Three feature cards say Smart Notes, Faster Follow-up, and Seamless
> Collaboration. CTA: Start free.

Known product facts available in this pilot:

- The product is an AI meeting-notes app.
- It captures meetings, extracts decisions, and creates follow-up tasks.
- No real screenshots, metrics, customer claims, integrations, or user research are
  available.

## Expected Value

The output should help a product builder or design agent turn a generic AI landing-page
concept into a more product-specific, reviewable surface.

Useful when:

- dominant bad smells are named;
- critique points to surface units;
- rewrite improves product specificity and user-job clarity;
- no metrics, screenshots, customers, or capabilities are invented;
- missing evidence is visible.

## Single-Pass Profile Power Test

Conditions:

- fixed profile;
- one pass;
- no TVG runtime remediation after the pass;
- no external taste-skill text copied into the profile or output.

Single-pass output:

> Dominant bad smell: generic AI SaaS hero. The surface says "smarter", "beautiful",
> "insights", and "effortlessly", but does not show the meeting state or the user
> decision it improves. The floating glass-card direction is dashboard theater because
> no real screen or data is available.
>
> Replacement move: make the hero about one concrete workflow: after a meeting, the
> user sees decisions, owners, and follow-up tasks in one reviewable list.
>
> Draft rewrite: "Turn every meeting into a decision list your team can act on. MeetFlow
> captures the call, pulls out decisions and owners, and drafts follow-up tasks for
> review before they enter your workflow."
>
> Evidence boundary: do not show analytics, customer proof, or real screenshots until
> those facts exist.

Single-pass result:

```yaml
single_pass_profile_power:
  profile_version: product-surface-taste-review v0.1
  input_artifact_or_task: MeetFlow AI landing-page hero concept
  value_semantics_result: "strong on bad-smell diagnosis and evidence boundary"
  realization_surface_result: "partial: visible units named, but hierarchy and CTA remain thin"
  gain_policy_result: "partial: rewrite is more specific, but lacks alternative visual direction"
  profile_control_power: partial
  residual_failure_modes:
    - CTA still generic
    - visual direction not yet reviewable enough for a designer
    - no explicit before/after hierarchy recommendation
  claim_ceiling: "profile provides useful local control, but not complete production-ready taste output in one pass"
```

## Loop-Assisted Production Test

Pressure: `4`

Debug log: enabled for this pilot record.

Value-gain scoring reference: 0-5 ordinal reference for comparing rounds only.

### Round 1

```yaml
round: 1
change_type: artifact
positive_value_hypothesis: "Replace generic AI SaaS language with product-specific meeting workflow."
value_axes_checked:
  - product-specificity
  - user-job-clarity
  - evidence-honesty
gate_result: return-remediate
reference_score: 3.3
residual_failure_modes:
  - visual direction still generic
  - CTA does not reflect the review workflow
  - critique does not yet expose hierarchy
```

Round 1 candidate kept:

> Turn every meeting into a decision list your team can act on. MeetFlow captures the
> call, pulls out decisions and owners, and drafts follow-up tasks for review.

### Round 2

```yaml
round: 2
change_type: artifact
positive_value_hypothesis: "Tie visual direction and CTA to the reviewable product state."
value_axes_checked:
  - surface-unit-observability
  - hierarchy-and-action-clarity
  - functional-style-fit
gate_result: return-remediate
reference_score: 4.1
residual_failure_modes:
  - feature grouping still reads like generic benefits
  - proof gap needs a clearer warning
```

Round 2 candidate kept:

> Hero surface: show a post-meeting review state, not floating glass cards. The first
> screen should center a meeting title, three extracted decisions, named owners, and
> draft follow-up tasks waiting for review.
>
> CTA: "Review a sample meeting" is stronger than "Start free" because it matches the
> product job without inventing conversion proof.

### Round 3

```yaml
round: 3
change_type: artifact
positive_value_hypothesis: "Compress diagnosis, rewrite, hierarchy, and evidence warning into a handoff-ready review."
value_axes_checked:
  - bad-smell-diagnosis
  - rewrite-usefulness
  - value-density
gate_result: freeze-with-review-bound-warning
reference_score: 4.5
residual_failure_modes:
  - visual success still needs a real screen or generated image review
  - profile usefulness has only been tested on one product-surface example
```

## Final TVG + Profile Output

Dominant smell: generic AI SaaS hero.

The baseline promises smarter work, insights, and effortless collaboration, but it
does not show the meeting state where value appears. The floating glass-card direction
is decorative dashboard theater until there is a real screen, data model, or product
state to inspect.

Rewrite the hero around one reviewable workflow:

> Turn every meeting into a decision list your team can act on.
>
> MeetFlow captures the call, pulls out decisions and owners, and drafts follow-up
> tasks for review before they enter your workflow.

Surface direction:

- First screen: a post-meeting review state, not abstract AI cards.
- Centerpiece: meeting title, extracted decisions, owners, and draft follow-up tasks.
- Hierarchy: decisions first, owners second, tasks third.
- CTA: "Review a sample meeting" rather than "Start free", unless the business goal
  requires direct signup.
- Feature grouping: replace Smart Notes / Faster Follow-up / Seamless Collaboration
  with Capture decisions / Assign owners / Review follow-ups.

Evidence boundary:

- Do not show analytics, customer logos, or productivity metrics without proof.
- Do not imply real screenshots until a product screen exists.
- Treat the visual direction as a reviewable concept, not validated design success.

## Source Attribution

Profile-derived:

- bad-smell diagnosis before rewrite;
- product state and user job before visual mood;
- evidence boundary for invented metrics, screenshots, and customer claims;
- surface-unit review handles.

TVG loop-derived:

- round-by-round value-gain hypotheses;
- pressure 4 loop budget;
- value-gain scoring reference;
- freeze-with-review-bound-warning exit state.

Independent artifact judgment:

- choosing "post-meeting review state" as the replacement surface;
- changing CTA to "Review a sample meeting";
- regrouping feature cards around decisions / owners / follow-ups.

Possible uncertainty:

- no real MeetFlow product exists in this pilot;
- no screenshot or user research was inspected;
- visual taste remains review-bound until a concrete image or UI surface is tested.

## Final Claim

This pilot supports a narrow claim:

> TVG + a scoped product-surface taste profile can produce a local taste-skill-style
> review pattern: bad smell -> visible surface unit -> replacement move -> evidence
> boundary.

It does not support a broad claim that Mindthus matches a dedicated taste-skill, has
stable visual judgment, or can generalize across product categories without further
profile tests.

