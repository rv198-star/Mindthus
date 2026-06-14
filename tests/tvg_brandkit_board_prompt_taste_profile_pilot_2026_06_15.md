# TVG Brandkit Board Prompt Taste Profile Pilot — 2026-06-15

## Purpose

This is the second local pilot for issue #47. The first pilot used a symbol-only Logo
task. That target was useful for testing Logo prompt constraints, but it was too narrow
for comparing against a dedicated taste-skill-style brand output.

This pilot moves the benchmark target closer to the external skill's natural output
space:

> a single brand-kit overview image prompt.

The goal is to test whether TVG + a scoped profile can turn a thin product brief into a
coherent brand-board prompt with brand thesis, panel roles, system constraints, bad-smell
avoidance, and review handles.

Claim ceiling: this supports only a local probe in brand-kit board prompt construction.
It does not prove that Mindthus has general visual taste, professional brand strategy,
trademark safety, or parity with a dedicated taste skill.

## Profile

Profile path:

`skills/tvg/resources/value-profiles/brandkit-board-prompt-taste.md`

Mode: `supplied`

Profile scope: brand-kit overview board image-generation prompts and prompt reviews.

Related narrower profile:

`skills/tvg/resources/value-profiles/logo-design-prompt-taste.md`

## Pollution Boundary

During the first external taste-skill black-box attempt on 2026-06-15, a CLI runner
unexpectedly printed external skill internals to stdout. That content is treated as
pollution:

- it must not be used as source material for this profile;
- it must not be copied, summarized, or converted into Mindthus profile rules;
- it may only be mentioned as a contamination risk in the audit record.

The external skill's final output prompt can still be used as a black-box output sample
for result-level comparison, but the leaked internal text cannot be used to construct
or revise the TVG profile.

## Benchmark Design

The fair comparison target is now a brand-board image, not a single Logo mark.

Run the same fixed brief through:

1. direct model brand-board prompt;
2. external taste-skill brandkit output, treated as a black-box final prompt;
3. TVG + `brandkit-board-prompt-taste`.

Blind-review the generated images without source labels.

Evaluation handles:

- brand thesis clarity;
- system coherence across panels;
- logo / palette / typography / UI or application fit;
- panel role clarity;
- visual density discipline;
- anti-generic AI/SaaS brand-board behavior;
- evidence honesty and claim ceiling;
- whether the image gives a designer or agent a useful next refinement target.

## Input Artifact

Artifact type: vague brand-board request.

Baseline request:

> Make a premium brand-kit overview board for MeetFlow, an AI meeting assistant. It
> should feel smart, elegant, futuristic, trustworthy, and useful for a launch.

Known brand facts available in this pilot:

- Name: MeetFlow.
- Product: AI meeting assistant.
- Product job: captures meetings, extracts decisions, and creates follow-up tasks.
- No real brand strategy, target audience research, competitor review, legal review,
  typography system, color system, product screenshots, metrics, customer proof, or
  existing assets are available.

## Expected Value

The output should help an image model generate a reviewable brand-kit board instead of a
generic AI SaaS moodboard.

Useful when:

- a brand thesis is visible;
- the board has bounded layout and panel jobs;
- logo, palette, type, UI/application, and atmosphere feel like one system;
- fake proof and fake screenshots are avoided;
- missing product and brand facts are visible;
- a reviewer can tell what should be improved next.

## Single-Pass Profile Power Test

Conditions:

- fixed profile;
- one pass;
- no TVG runtime remediation after the pass;
- no external taste-skill text copied into the profile or output.

Single-pass output:

> Dominant bad smell: generic premium AI SaaS brand board. The brief asks for smart,
> elegant, futuristic, and trustworthy, but those words do not define a brand system.
>
> Brand thesis: MeetFlow turns conversation drift into accountable flow.
>
> Board direction: use a 2x3 overview board. Panel jobs: logo concept, process
> metaphor, product application, palette/type system, meeting-to-task flow detail, and
> evidence boundary / launch direction. The system should repeat one visual idea:
> conversation lines becoming decision paths and task nodes.
>
> Evidence boundary: product UI panels are conceptual, not real screenshots; do not
> invent metrics, customer proof, awards, integrations, or legal trust claims.

Single-pass result:

```yaml
single_pass_profile_power:
  profile_version: brandkit-board-prompt-taste v0.1
  input_artifact_or_task: MeetFlow vague brand-board request
  value_semantics_result: "strong on brand thesis, bad-smell diagnosis, and evidence boundary"
  realization_surface_result: "partial: board layout and panel roles named, but image prompt still needs tighter constraints"
  gain_policy_result: "partial: system idea is useful, but density and application realism need loop refinement"
  profile_control_power: partial
  residual_failure_modes:
    - visual palette and type direction still too broad
    - UI/application panel risks becoming fake screenshot theater
    - no generated brand-board image has been inspected in this record yet
  claim_ceiling: "profile provides useful local control for a brand-board prompt, but not broad taste-skill parity"
```

## Loop-Assisted Production Test

Pressure: `4`

Debug log: enabled for this pilot record.

Value-gain scoring reference: 0-5 ordinal reference for comparing rounds only.

### Round 1

```yaml
round: 1
change_type: artifact
positive_value_hypothesis: "Replace vague premium/futuristic language with a brand thesis and panel structure."
value_axes_checked:
  - brand-thesis-clarity
  - panel-role-clarity
  - evidence-honesty
gate_result: return-remediate
reference_score: 3.5
residual_failure_modes:
  - palette/type still generic
  - product application not controlled enough
  - anti-generic constraints too implicit
```

Round 1 candidate kept:

> MeetFlow brand thesis: turn conversation drift into accountable flow. Use a bounded
> 2x3 brand-board prompt with panel jobs rather than a loose moodboard.

### Round 2

```yaml
round: 2
change_type: artifact
positive_value_hypothesis: "Align logo, palette, type, UI concept, and atmosphere around one repeated system idea."
value_axes_checked:
  - system-coherence
  - logo-system-fit
  - palette-and-typography-control
gate_result: return-remediate
reference_score: 4.3
residual_failure_modes:
  - prompt still risks polished fake UI
  - image self-audit needs stronger density and evidence checks
```

Round 2 candidate kept:

> Repeat one visual idea across panels: speech/conversation paths resolve into decisions
> and follow-up task nodes. Use calm blue, deep green, charcoal, and off-white. Keep type
> sparse and large; avoid fake data-heavy dashboards.

### Round 3

```yaml
round: 3
change_type: artifact
positive_value_hypothesis: "Compact the prompt into a single Image2-ready instruction with explicit negative constraints and review handles."
value_axes_checked:
  - anti-generic-brand-board
  - visual-density-discipline
  - prompt-reviewability
gate_result: freeze-with-review-bound-warning
reference_score: 4.7
residual_failure_modes:
  - generated image still needs blind review
  - external taste-skill comparison needs a cleaner runner that does not leak internals
  - professional brand strategy, typography, logo design, and legal review remain out of scope
```

## Brand-Board Image Blind Review

Image2 was used to generate three brand-board images from:

1. direct model brand-board prompt;
2. external taste-skill brandkit final prompt;
3. TVG + `brandkit-board-prompt-taste` v0.1 prompt.

The options shown to the user were anonymized:

```yaml
blind_review_round_1:
  option_R:
    source: "TVG + brandkit-board-prompt-taste v0.1"
    image_path: "/Users/william/.codex/generated_images/019eadbd-81e9-7d03-8a27-c0f383ace08d/ig_0f1ac7dae02c2862016a2edb583584819a90493256b2ca1699.png"
    user_feedback_initial: "比较一般"
    user_feedback_correction: "不是一般，是非常丑"
    interpreted_result: "strong negative visual-quality failure"
  option_S:
    source: "direct model brand-board prompt"
    image_path: "/Users/william/.codex/generated_images/019eadbd-81e9-7d03-8a27-c0f383ace08d/ig_0f1ac7dae02c2862016a2edad5c494819aab4f32de98d1e7e0.png"
    user_feedback: "综合"
  option_T:
    source: "external taste-skill brandkit final prompt"
    image_path: "/Users/william/.codex/generated_images/019eadbd-81e9-7d03-8a27-c0f383ace08d/ig_0f1ac7dae02c2862016a2edb0e4380819a95c19e48dcdfad08.png"
    user_feedback: "比较有质感"
```

Interpretation:

- The narrower Logo probe made the external skill look weak because the target was too
  constrained.
- The brand-board target is fairer and exposed a real TVG profile gap.
- TVG v0.1 was coherent and bounded in prompt structure, but the generated board was a
  strong visual-quality failure. The internal reference score overstated readiness
  because it measured prompt structure more than final image taste.
- Direct prompting produced a more balanced board than expected.
- The external taste-skill black-box output produced stronger perceived texture.

Supported conclusion:

> TVG + Profile v0.1 failed the brand-board image test on perceived surface quality.
> The next profile revision must treat art-directed surface quality as a hard visible
> gate, not a decorative nice-to-have, while still avoiding external skill contamination.

## Profile Revision After Blind Review

Change type: `profile`

Source basis:

- user blind-review feedback on generated images;
- inspected output-level difference only;
- no use of leaked external skill internals.

Revision:

- add `art-directed-surface-quality` as a derived axis;
- require enough material contrast, visual rhythm, and atmosphere to avoid a flat
  checklist-like brand board;
- keep fake-proof and evidence boundaries unchanged.

```yaml
profile_revision_after_blind_review:
  from_version: brandkit-board-prompt-taste v0.1
  to_version: brandkit-board-prompt-taste v0.2
  change_type: profile
  positive_value_hypothesis: "A brand-board prompt needs visible surface quality and rhythm as an exit requirement, not merely system coherence."
  forbidden_source: "leaked external taste-skill internals"
  expected_effect: "TVG output should avoid ugly, dutiful brand boards while preserving evidence honesty and system coherence."
```

## Strict-Shell Retest

The first brand-board blind review had two evaluation weaknesses:

- the Logo and board style made sources easier to infer;
- the prompt shell differed enough that layout and density could dominate the comparison.

A stricter retest therefore normalized the outer shell:

- all three outputs used a 16:10 board;
- all used a 2x3 grid;
- all used the same six panel roles;
- all used the same limited text set: `MeetFlow`, `Capture`, `Decide`, `Follow up`;
- all used the same palette range: charcoal, off-white, blue, green, and one warm accent;
- no metrics, awards, customer proof, legal claims, real screenshots, or dense text;
- a no-logo-control instruction tried to prevent Logo design from dominating the review.

The no-logo-control attempt was only partially successful. The image model still made
similar MeetFlow wordmark / placeholder-logo patterns, so this remains a weak anonymous
test rather than a statistically clean blind test.

```yaml
strict_shell_retest_round:
  option_A:
    source: "TVG + brandkit-board-prompt-taste v0.2 standardized no-logo shell"
    image_path: "/Users/william/.codex/generated_images/019eadbd-81e9-7d03-8a27-c0f383ace08d/ig_0f1ac7dae02c2862016a2edffb00a0819a9ed2ce219f9532d2.png"
    user_feedback: "A和C差一点"
  option_B:
    source: "direct model prompt standardized no-logo shell"
    image_path: "/Users/william/.codex/generated_images/019eadbd-81e9-7d03-8a27-c0f383ace08d/ig_0f1ac7dae02c2862016a2ee0455b10819abba09693c39d48e6.png"
    user_feedback: "配色和图标好一些"
  option_C:
    source: "external taste-skill final prompt standardized no-logo shell"
    image_path: "/Users/william/.codex/generated_images/019eadbd-81e9-7d03-8a27-c0f383ace08d/ig_0f1ac7dae02c2862016a2ee08aed6c819a874687ee06eae98b.png"
    user_feedback: "A和C差一点"
  overall_user_feedback: "目前看这三个就不分高低了，开始有些整体雷同，细节不同而已"
```

Interpretation:

- Once the shell was normalized and Logo identity was partly controlled, the three
  outputs converged.
- Direct prompting slightly led this specific retest on color and icon treatment.
- TVG v0.2 no longer showed the severe visual failure of v0.1, which points to a
  profile / prompt-realization problem rather than a complete TVG mechanism failure.
- TVG v0.2 also did not establish a clear advantage. It reached a comparable cluster,
  not a superior result.
- The external taste-skill output did not dominate after normalization, but this does
  not prove it is weaker; the normalization may suppress part of its natural strength.

Updated diagnosis:

> The main issue exposed by v0.1 was profile content: the profile had not made visible
> brand-board quality an exit requirement. After v0.2, TVG can reach the same rough
> quality cluster under a controlled shell. The remaining limitation is not only
> profile content, but benchmark design and realization strategy: stronger taste
> profiles must translate "good" into concrete visual moves without collapsing outputs
> into the same template.

## Final TVG + Profile Output

Dominant smell: generic premium AI SaaS brand board. The baseline gives mood words but
does not choose a brand system, so an image model will likely create a polished collage
with glowing gradients, fake dashboards, abstract tech marks, and unreadable UI filler.

Known facts:

- MeetFlow is an AI meeting assistant.
- It turns meeting conversations into decisions and follow-up tasks.
- Brand strategy, audience research, competitor review, real product screenshots,
  typography, customer proof, and legal clearance are missing.

Brand thesis:

> MeetFlow turns conversation drift into accountable flow.

Primary Image2 prompt:

> Create a single 16:10 premium brand-kit overview board for MeetFlow, an AI meeting
> assistant that captures meetings, extracts decisions, and creates follow-up tasks.
> The board should express one brand idea: conversation paths resolving into decisions
> and follow-up task nodes. Use a clean 2x3 grid with strong gutters and controlled
> visual density. Panel 1: simple logo direction, a speech/conversation path resolving
> into a decision/check-flow mark. Panel 2: logo construction or system motif, showing
> conversation lines becoming decision paths and task nodes. Panel 3: conceptual product
> application, a clean meeting review surface with decisions, owners, and tasks, clearly
> not a real screenshot. Panel 4: restrained color and typography system, calm blue,
> deep green, charcoal, and off-white, sparse large readable labels only. Panel 5:
> detail strip of task nodes, decision chips, and follow-up flow components. Panel 6:
> quiet launch direction panel with the short phrase "From meeting to momentum" if text
> renders cleanly. Make the board coherent, restrained, brand-system driven, and
> reviewable. Avoid generic AI gradients, glowing orbs, neural brains, circuit boards,
> hexagon badges, random sparkles, fake analytics, customer logos, awards, metrics,
> legal seals, stock people, dense tiny text, and over-polished mockup theater.

Image self-audit:

- Can the brand thesis be stated in one sentence after seeing the board?
- Do all six panels share the same conversation-to-decision system idea?
- Are product application panels clearly conceptual rather than fake proof?
- Is visual density controlled enough to inspect?
- Does the board avoid generic AI/SaaS visual defaults?
- Would a designer or agent know what to refine next?

Claim ceiling:

- This is a reviewable brand-board prompt direction, not validated brand strategy.
- Human brand design, logo refinement, typography cleanup, competitive distinctiveness,
  trademark review, and product proof remain outside this pilot.

## Source Attribution

Profile-derived:

- brand thesis before board style;
- panel-role clarity;
- system coherence across logo, palette, type, UI/application, and atmosphere;
- anti-generic AI/SaaS board constraints;
- art-directed surface quality as a visible gate after v0.2;
- evidence boundary and fake-proof vetoes.

TVG loop-derived:

- round-by-round value-gain hypotheses;
- pressure 4 loop budget;
- value-gain scoring reference;
- freeze-with-review-bound-warning exit state.

Independent artifact judgment:

- choosing "conversation drift into accountable flow" as the brand thesis;
- using a 2x3 board structure;
- choosing conversation paths, decisions, and task nodes as the repeated system idea;
- choosing a restrained blue / green / charcoal / off-white direction.

Possible uncertainty:

- generated images are referenced by local path but not committed to the repo;
- external taste-skill was compared as a final-output prompt only, after an earlier failed runner polluted local context;
- strict-shell retest reduced but did not eliminate identity leakage from wordmark / Logo-like areas;
- the strict shell may suppress the external skill's natural strengths;
- the local context contains polluted external skill internals from the failed runner attempt;
- no human brand designer, trademark search, or real brand strategy was involved.

## Final Claim

This pilot supports a narrow claim:

> TVG + a scoped brandkit-board prompt profile can move from a visibly failed
> brand-board prompt toward a comparable result cluster after profile revision:
> brand brief -> brand thesis -> panel system -> visible-quality gate -> generation
> constraints -> image self-audit -> claim ceiling.

It does not support a broad claim that Mindthus matches a dedicated taste-skill, has
stable visual judgment, outperforms direct prompting, or can generalize across brand
categories without further clean black-box benchmark tests.
