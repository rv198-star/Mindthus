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

## True Image Blind Test

After the text-first critique pilot, one extra image blind test was run on the
DeskPilot support-ticket hero scenario.

Setup:

- Three independent image prompts were generated for the same product facts.
- The three sources were direct prompt, TVG+profile prompt, and an external
  taste-skill image-generation prompt used as a benchmark candidate.
- Images were generated independently, then randomly shuffled into A/B/C.
- The contact sheet was kept local and was not added to the repository:
  `/private/tmp/mindthus_blindtest_deskpilot_20260615/deskpilot_blind_contact_sheet.png`
- Source mapping was hidden during user review.

Hidden mapping after review:

```yaml
A: taste_skill
B: tvg_profile
C: direct
```

User review:

> A最优，C和B差距不大，但C更好一些

Result:

```yaml
true_image_blind_test:
  best: taste_skill
  second: direct
  third: tvg_profile
  result_for_tvg_profile: failed_to_win_visual_blind_test
  interpretation: "TVG+profile improved product-specific reasoning, but did not beat the dedicated visual taste prompt or the direct prompt in first-look hero quality."
```

Blind-test diagnosis:

- The dedicated visual taste prompt produced the strongest first-screen image.
- The direct prompt beat TVG+profile by a small margin in this run.
- TVG+profile remained useful for critique and evidence-bounded repair direction, but
  its current image prompt tends to over-prioritize correctness and product semantics
  over visual force, commercial hero tension, and first-look appeal.
- This supports a sharper limitation: text-first critique quality and visual-generation
  taste must be evaluated separately.

## Cross-Scene Anti-Overfit Blind Test

Because the DeskPilot image test could overfit to SaaS hero conventions and the
external benchmark's winning case-file direction, a second scene was tested without
reusing the customer-support / review-board domain.

Scene:

> Clayroom is a small neighborhood pottery studio offering beginner wheel-throwing
> classes, glazing sessions, and private group workshops. The page goal is to make a
> first-time visitor feel that the studio is warm, real, beginner-friendly, and worth
> booking for an intro class.

Hard constraints:

- no fake reviews;
- no star ratings;
- no fake scarcity;
- no discounts;
- no invented teacher bio;
- no metrics or proof claims.

TVG self-iteration before blind test:

```yaml
cycles:
  - cycle: 1
    positive_value_hypothesis: "Start with a clear, honest class-booking hero."
    self_audit: "clear but too much like a generic class booking card; risk of unsupported availability language"
  - cycle: 2
    positive_value_hypothesis: "Make the tactile hand-making moment the visual protagonist."
    self_audit: "stronger and more human, but booking usefulness became too weak"
  - cycle: 3
    positive_value_hypothesis: "Restore lightweight booking information without returning to a sales-card template."
    self_audit: "best balance so far, but still close to a conventional pretty craft-site solution"
  - cycle: 4
    positive_value_hypothesis: "Add a memorable handmade bowl artifact as a brand signature."
    self_audit: "more memorable, but the CTA drifted toward visiting the studio rather than booking"
  - cycle: 5
    positive_value_hypothesis: "Merge the handmade bowl artifact with a clear beginner-class booking CTA."
    self_audit: "selected as final TVG candidate; warm, honest, bookable, and not obviously fake-proof driven"
```

Blind setup:

- TVG candidate was frozen after cycle 5.
- Direct prompt and external visual-taste benchmark were generated only after the TVG
  candidate was frozen.
- Three images were randomly shuffled into A/B/C.
- The contact sheet was kept local and was not added to the repository:
  `/private/tmp/mindthus_blindtest_clayroom_20260615/clayroom_true_blind_contact_sheet.png`

Hidden mapping after review:

```yaml
A: taste_skill_benchmark
B: direct
C: tvg_profile_cycle5
```

User review:

> B最精致，A次之，C最次，但三个差距不是太大

Result:

```yaml
clayroom_cross_scene_blind_test:
  best: direct
  second: taste_skill_benchmark
  third: tvg_profile_cycle5
  result_for_tvg_profile: failed_to_win_but_gap_narrowed
  interpretation: "TVG self-iteration reduced the earlier negative-optimization problem, but still did not beat direct prompting in first-look visual quality."
```

Cross-scene diagnosis:

- Switching away from SaaS/support prevented the test from simply optimizing toward the
  previous case-file visual.
- TVG self-iteration produced a usable candidate and avoided obvious evidence-boundary
  violations.
- The user still preferred direct prompting and ranked TVG third.
- The gap was smaller than the DeskPilot blind test, so the loop may be helping, but the
  evidence does not yet support visual taste parity or superiority.

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
- external taste-skill was used only as a benchmark candidate in the blind image test,
  not as source material for the Mindthus profile;
- this pilot includes one image blind test, but the sample size is still too small to
  prove stable visual-generation quality;
- the Clayroom cross-scene test suggests TVG self-iteration can narrow the gap, but did
  not win against direct prompting in that run;
- no user research, analytics, or conversion evidence was inspected.

## Final Claim

This pilot supports a narrower and more useful claim than the brandkit image probe:

> TVG + a scoped UI redesign critique profile can turn vague taste feedback into a
> concrete, evidence-bounded repair direction.

It does not support a claim that Mindthus can produce superior visual design, outperform
dedicated taste skills, or replace product/design review.

The additional blind image test makes this limit stronger: in one true image blind run,
the external visual taste benchmark won, direct prompt came second, and TVG+profile came
third. TVG+profile should therefore not claim visual taste parity from this issue.

The cross-scene Clayroom test further narrows the evidence: five TVG self-iteration cycles made the output more competitive,
but the blind ranking was still direct first, external taste benchmark second, and TVG third.
