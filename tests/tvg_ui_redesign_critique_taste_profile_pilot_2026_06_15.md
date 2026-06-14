# TVG UI Redesign Critique Taste Profile Pilot — 2026-06-15

## Purpose

This is the third local pilot for issue #47. Earlier probes tested Logo prompts and
brand-kit board prompts. Those probes were useful but showed a clear limitation:

- pure image-generation taste tests mix profile quality with image-model aesthetics;
- Logo and board layout can leak the source during blind review;
- a profile can look coherent in text while producing a bad image.

This pilot changes the target to a more TVG-native taste task:

> make weak UI redesign critique useful.

The test asks whether TVG + a scoped profile can turn vague taste feedback into a
reviewable critique that names the screen job, dominant bad smell, visible surface unit,
user impact, first repair move, and evidence boundary.

Claim ceiling: this supports only a local critique-quality probe. It does not prove that
Mindthus has general design taste, implementation skill, or parity with a dedicated
taste skill.

## Profile

Profile path:

`skills/tvg/resources/value-profiles/ui-redesign-critique-taste.md`

Mode: `supplied`

Profile scope: bounded UI redesign critique and first-repair direction.

## Test Scenario

Artifact type: weak design critique for a landing hero.

Surface description:

> MeetFlow is an AI meeting assistant. The current landing hero says: "MeetFlow helps
> teams work smarter with beautiful automated meeting notes." The hero uses a dark
> purple-blue gradient, floating glass cards labeled AI Summary / Smart Notes /
> Insights, three vague feature cards, and a CTA that says "Start free". Known product
> facts: it captures meetings, extracts decisions, and creates follow-up tasks. No real
> screenshot, customer proof, metrics, audience research, or integration list is
> available.

Weak critique baseline:

> The page feels generic and should look more premium. Improve the visual hierarchy,
> make the copy more specific, add stronger design polish, and make the CTA clearer.

## Expected Value

The output should help a builder, designer, or agent know what to change first without
inventing product proof.

Useful when:

- critique starts from screen job and user decision;
- dominant bad smell is named;
- feedback points to visible units;
- user impact is explained;
- the first repair is implementable;
- fake proof and screenshots are blocked;
- remaining uncertainty is visible.

## Single-Pass Profile Power Test

Conditions:

- fixed profile;
- one pass;
- no TVG remediation loop after the pass;
- no external taste-skill text copied into the profile or output.

Single-pass output:

> Screen job: convince a first-time visitor that MeetFlow turns meetings into concrete
> follow-up work.
>
> Dominant bad smell: generic AI SaaS hero. The hero uses purple-blue gradient, floating
> AI cards, "work smarter", and three vague feature blocks, but the visitor still cannot
> see the product moment where value appears.
>
> Visible unit: hero claim + hero visual + CTA.
>
> User impact: the page asks for signup before showing what the user can evaluate, so
> trust depends on generic AI styling rather than product clarity.
>
> First repair: make the hero about one reviewable state: after a meeting, decisions,
> owners, and follow-up tasks are ready for review. Replace "Start free" with "Review a
> sample meeting" unless the business explicitly requires signup-first.
>
> Evidence boundary: do not add metrics, customer logos, analytics charts, or real
> screenshots until those facts exist.

Single-pass result:

```yaml
single_pass_profile_power:
  profile_version: ui-redesign-critique-taste v0.1
  input_artifact_or_task: weak MeetFlow landing-hero critique
  value_semantics_result: "strong: screen job, bad smell, surface unit, user impact, and evidence boundary are present"
  realization_surface_result: "strong: hero claim, visual, and CTA are named as inspectable units"
  gain_policy_result: "partial: first repair is useful, but second-order layout and proof handling need loop refinement"
  profile_control_power: strong
  residual_failure_modes:
    - no concrete before/after layout order yet
    - feature-card repair not yet specified
    - revised copy still needs a compact handoff shape
  claim_ceiling: "profile appears stronger in critique mode than in brand-board image-generation mode, but this is one text-only pilot"
```

## Loop-Assisted Production Test

Pressure: `4`

Debug log: enabled for this pilot record.

Value-gain scoring reference: 0-5 ordinal reference for comparing rounds only.

### Round 1

```yaml
round: 1
change_type: artifact
positive_value_hypothesis: "Convert vague premium/design feedback into screen job, bad smell, visible unit, and user impact."
value_axes_checked:
  - screen-job-clarity
  - bad-smell-specificity
  - visible-surface-unit
gate_result: return-remediate
reference_score: 4.0
residual_failure_modes:
  - first repair exists but lacks a full handoff shape
  - feature cards remain generic
```

### Round 2

```yaml
round: 2
change_type: artifact
positive_value_hypothesis: "Add implementable first repair and feature-card replacement without inventing proof."
value_axes_checked:
  - first-repair-actionability
  - hierarchy-and-scanning
  - evidence-honesty
gate_result: freeze-with-review-bound-warning
reference_score: 4.6
residual_failure_modes:
  - a real screenshot or product state would still improve critique precision
  - visual polish cannot be validated without a revised mockup
```

## Final TVG + Profile Output

Diagnosis:

> This is not mainly a "make it premium" problem. The hero hides the product moment
> behind generic AI styling.

Screen job:

The first screen should help a visitor understand and evaluate one promise:

> MeetFlow turns a meeting into decisions, owners, and follow-up tasks.

Dominant bad smell:

Generic AI SaaS hero. The purple-blue gradient, floating AI cards, "work smarter", and
three vague feature cards make the product feel familiar, but not inspectable.

Visible surface units:

| Unit | Problem | First repair |
| --- | --- | --- |
| Hero claim | Says "work smarter" but not what changes after a meeting | Use: "Turn every meeting into decisions and follow-up tasks your team can review." |
| Hero visual | Floating AI cards show mood, not product state | Show a conceptual post-meeting review state: decisions, owners, follow-up tasks |
| CTA | "Start free" asks for commitment before evaluation | Use "Review a sample meeting" or "See a meeting turned into tasks" |
| Feature cards | Smart Notes / Faster Follow-up / Seamless Collaboration are generic | Replace with Capture decisions / Assign owners / Review follow-ups |
| Proof area | No real proof is available | Leave proof empty or label as "sample workflow"; do not invent logos or metrics |

Handoff direction:

1. Rewrite the hero around the post-meeting review state.
2. Replace abstract AI card visuals with a simple conceptual product state.
3. Change the CTA to invite evaluation before signup.
4. Rename features around decisions, owners, and follow-ups.
5. Keep all proof cues marked as missing until real evidence exists.

Claim ceiling:

- This critique supports a better first redesign direction.
- It does not validate conversion, brand quality, visual polish, or actual UX success.
- A real screenshot or prototype should be reviewed before claiming design quality.

## Comparison To Previous Probes

Logo / brandkit image-generation probes were dominated by image-model aesthetics and
source leakage. This critique probe is more aligned with TVG's strength:

- it operates on a bounded artifact;
- it can name exact value-gain axes;
- it can make the output more useful without pretending to be a designer;
- the output can be reviewed textually before any image/model generation.

Updated diagnosis:

> TVG+Profile is more promising as a taste-aware critique and repair-direction loop than
> as a pure visual-generation taste engine.

## Source Attribution

Profile-derived:

- screen job before visual mood;
- visible surface unit before general design advice;
- bad smell -> user impact -> first repair;
- fake proof and screenshot boundary;
- downstream handoff shape.

TVG loop-derived:

- round-by-round positive value hypotheses;
- pressure 4 loop budget;
- value-gain scoring reference;
- freeze-with-review-bound-warning exit state.

Independent artifact judgment:

- choosing the post-meeting review state as the first repair target;
- choosing "Review a sample meeting" as a CTA repair;
- mapping feature cards to decisions / owners / follow-ups.

Possible uncertainty:

- no real MeetFlow screenshot or prototype was inspected;
- no external taste-skill black-box critique output has been compared yet in this scenario;
- this is a text-only pilot and does not prove visual-generation quality;
- no user research, analytics, or conversion evidence was inspected.

## Final Claim

This pilot supports a narrower and more useful claim than the brandkit image probe:

> TVG + a scoped UI redesign critique profile can turn vague taste feedback into a
> concrete, evidence-bounded repair direction.

It does not support a claim that Mindthus can produce superior visual design, outperform
dedicated taste skills, or replace product/design review.

