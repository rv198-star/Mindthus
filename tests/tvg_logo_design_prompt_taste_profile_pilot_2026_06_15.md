# TVG Logo Design Prompt Taste Profile Pilot — 2026-06-15

## Purpose

This is a local pilot for issue #47. It tests whether TVG + a scoped profile can mimic
one bounded part of a taste-skill-style workflow:

- turn a vague logo request into a constrained image-generation prompt;
- name common AI-logo bad smells before generating;
- preserve evidence honesty about missing brand facts and legal/design review;
- record whether value gain came from the profile itself or from TVG loop rescue.

Claim ceiling: this supports only a local probe in logo prompt construction. It does not
prove that Mindthus has general visual taste, professional logo-design ability, trademark
clearance, or parity with a dedicated taste skill.

## Profile

Profile path:

`skills/tvg/resources/value-profiles/logo-design-prompt-taste.md`

Mode: `supplied`

Profile scope: logo image-generation prompts and logo prompt reviews.

## Black-Box Benchmark Design

The intended taste-skill comparison is output-level only.

Do not copy or inspect external taste-skill internals for reusable rules. A fair
benchmark should run the same fixed logo briefs through:

1. direct model prompt generation;
2. external taste-skill output, treated as a black box;
3. TVG + `logo-design-prompt-taste`.

Blind-review the outputs without source labels.

Evaluation handles:

- brand role clarity;
- one clear visual idea;
- logo deliverability as a flat mark;
- small-size and monochrome viability;
- typography risk control;
- anti-generic-AI-logo constraints;
- useful variants instead of random prompt noise;
- evidence honesty and claim ceiling.

This pilot has not run the external taste-skill black-box comparison yet.

## Input Artifact

Artifact type: vague logo request.

Baseline request:

> Design a modern premium logo for an AI meeting assistant called MeetFlow. It should
> feel smart, elegant, futuristic, and trustworthy.

Known brand facts available in this pilot:

- Name: MeetFlow.
- Product: AI meeting assistant.
- Product job: captures meetings, extracts decisions, and creates follow-up tasks.
- No real brand strategy, audience research, legal review, competitor study, typography
  system, color system, or product screenshots are available.

## Expected Value

The output should help an image model or designer produce reviewable logo directions
instead of a generic AI-tech icon.

Useful when:

- generic AI-logo tropes are named and blocked;
- the prompt starts from brand role and usage context;
- one visual idea drives the mark;
- the prompt asks for a logo mark, not a cinematic mockup;
- text rendering risks are controlled;
- missing brand and legal facts remain visible.

## Single-Pass Profile Power Test

Conditions:

- fixed profile;
- one pass;
- no TVG runtime remediation after the pass;
- no external taste-skill text copied into the profile or output.

Single-pass output:

> Dominant bad smell: generic premium AI logo. The request asks for smart, elegant,
> futuristic, and trustworthy, but none of those words choose a mark. The prompt risks a
> glowing brain, abstract circuit swoosh, or polished 3D app icon.
>
> Primary direction: make the logo about meetings turning into accountable flow. Use one
> simple continuous-line mark: a speech bubble that resolves into a check-mark path or
> task-flow node. Keep it flat, vector-like, and readable in one color.
>
> Primary image prompt: "Create a flat vector logo concept for MeetFlow, an AI meeting
> assistant that turns conversations into decisions and follow-up tasks. Combination
> mark: simple continuous-line symbol plus clean readable wordmark. Symbol idea: a
> speech bubble subtly resolving into a check-mark flow path, with strong negative space,
> rounded geometry, no 3D, no mockup, no gradients, no glow, white background, two-color
> limit, scalable at small size."
>
> Evidence boundary: brand strategy, final typography, legal clearance, and real visual
> distinctiveness still need human review.

Single-pass result:

```yaml
single_pass_profile_power:
  profile_version: logo-design-prompt-taste v0.1
  input_artifact_or_task: MeetFlow vague logo request
  value_semantics_result: "strong on bad-smell diagnosis and logo deliverability"
  realization_surface_result: "partial: mark, type, color, and forbidden tropes named; variants absent"
  gain_policy_result: "partial: prompt is usable but lacks image self-audit and variant strategy"
  profile_control_power: partial
  residual_failure_modes:
    - wordmark rendering risk remains
    - only one concept direction has been tested
    - no generated image has been inspected in this pilot record
  claim_ceiling: "profile provides useful local control for a logo prompt, but not broad taste-skill parity"
```

## Loop-Assisted Production Test

Pressure: `4`

Debug log: enabled for this pilot record.

Value-gain scoring reference: 0-5 ordinal reference for comparing rounds only.

### Round 1

```yaml
round: 1
change_type: artifact
positive_value_hypothesis: "Replace vague visual adjectives with brand role, logo type, and one mark idea."
value_axes_checked:
  - brand-role-clarity
  - visual-idea-focus
  - anti-generic-ai-logo
gate_result: return-remediate
reference_score: 3.4
residual_failure_modes:
  - generated text risk not isolated
  - no variant strategy
  - image review criteria too implicit
```

Round 1 candidate kept:

> MeetFlow logo direction: a flat vector combination mark where a speech bubble resolves
> into a check-mark flow path, expressing conversation becoming accountable next steps.

### Round 2

```yaml
round: 2
change_type: artifact
positive_value_hypothesis: "Separate symbol generation from wordmark risk and add negative constraints."
value_axes_checked:
  - logo-deliverability
  - typography-control
  - prompt-constraint-quality
gate_result: return-remediate
reference_score: 4.2
residual_failure_modes:
  - variants still too close to the same idea
  - evidence boundary needs to be explicit
```

Round 2 candidate kept:

> Generate the symbol alone first if text artifacts appear. Wordmark can be added by a
> designer later. Avoid glowing brain, circuit board, hexagon badge, random spark,
> floating 3D object, gradient orb, and cinematic mockup.

### Round 3

```yaml
round: 3
change_type: artifact
positive_value_hypothesis: "Add strategically different variants and a compact image self-audit."
value_axes_checked:
  - variant-strategy
  - small-size-recognition
  - monochrome-and-silhouette-viability
gate_result: freeze-with-review-bound-warning
reference_score: 4.6
residual_failure_modes:
  - generated image still needs blind review
  - no external taste-skill benchmark has been run
  - professional design and legal review remain out of scope
```

## Final TVG + Profile Output

Dominant smell: generic premium AI logo. The input uses taste adjectives but does not
choose a mark, so an image model will likely produce a glowing tech badge, abstract
swoosh, brain/circuit symbol, or polished 3D app icon.

Known facts:

- MeetFlow is an AI meeting assistant.
- It turns meeting conversations into decisions and follow-up tasks.
- Brand strategy, audience research, competitor review, and legal clearance are missing.

Primary logo prompt:

> Create a flat vector logo concept for `MeetFlow`, an AI meeting assistant that turns
> conversations into decisions and follow-up tasks. Use a combination-mark direction:
> a simple continuous-line symbol plus a clean readable wordmark. Core symbol idea:
> a speech bubble subtly resolving into a check-mark flow path, suggesting conversation
> becoming accountable next steps. Use rounded geometry, strong negative space, a
> two-color limit, white background, no mockup, no 3D, no glow, no gradients, no neural
> brain, no circuit-board pattern, no hexagon badge, no random spark. The mark should
> remain recognizable at small size and still work as a one-color silhouette.

If text rendering fails, generate the symbol only:

> Flat vector symbol for an AI meeting assistant: speech bubble resolving into a
> check-mark flow path, rounded geometry, strong negative space, two-color limit,
> white background, scalable, one-color silhouette viability, no text, no mockup,
> no glow, no gradients, no generic AI tech symbols.

Variant prompts:

1. Flow-first variant:
   > Use a compact path of three rounded nodes forming a subtle check mark inside a
   > speech-bubble outline. Emphasize workflow and ownership, not AI magic.
2. Meeting-first variant:
   > Use two minimal conversation lines converging into one clear decision mark.
   > Emphasize alignment after a meeting, not automation spectacle.

Image self-audit:

- Does the mark read without the word `MeetFlow`?
- Does it work as a black one-color silhouette?
- Is the symbol one idea, or did it stack bubble, check, nodes, AI sparkle, and circuit
  language at once?
- Did the image become a glossy app icon or mockup instead of a logo?
- Is the wordmark readable, or should typography be handled separately?
- Does it avoid common AI-logo defaults?

Claim ceiling:

- This is a reviewable prompt direction, not final brand identity.
- Human logo design, typography cleanup, competitive distinctiveness, trademark review,
  and brand-strategy validation remain outside this pilot.

## Source Attribution

Profile-derived:

- brand role before visual mood;
- one visual idea before symbol stacking;
- flat vector-like deliverability;
- anti-generic-AI-logo constraints;
- small-size and monochrome self-audit;
- evidence boundary and legal/design claim ceiling.

TVG loop-derived:

- round-by-round value-gain hypotheses;
- pressure 4 loop budget;
- value-gain scoring reference;
- freeze-with-review-bound-warning exit state.

Independent artifact judgment:

- choosing a speech bubble resolving into a check-mark flow path;
- isolating symbol-only generation when wordmark rendering is risky;
- using flow-first and meeting-first variants as strategic alternatives.

Possible uncertainty:

- no generated image is included in this repo record;
- no external taste-skill black-box output has been compared yet;
- no human logo designer, trademark search, or real brand strategy was involved.

## Final Claim

This pilot supports a narrow claim:

> TVG + a scoped logo-design prompt profile can produce a local taste-skill-style prompt
> pattern: bad smell -> brand role -> one visual idea -> generation constraints ->
> image self-audit -> claim ceiling.

It does not support a broad claim that Mindthus matches a dedicated taste-skill, has
stable visual judgment, or can generalize across branding categories without further
black-box benchmark tests.

