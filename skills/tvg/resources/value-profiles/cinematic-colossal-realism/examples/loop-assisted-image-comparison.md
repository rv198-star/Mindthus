# Cinematic Colossal Realism Loop-Assisted Image Comparison

```yaml
loop_assisted_profile_use:
  profile_version: cinematic-colossal-realism-v0.1
  max_rounds_or_budget: "one baseline prompt, one basic TVG profile prompt, one advanced four-layer profile prompt, optional Images2 run"
  rounds_used: 0
  round_records:
    - round: 1
      change_type: prompt
      positive_value_hypothesis: "baseline ordinary expansion exposes what a prose-only prompt leaves underspecified"
      gate_result: freeze-with-review-bound-warning
      residual_failure_modes:
        - "weak human-scale anchoring"
        - "weak physical feedback"
    - round: 2
      change_type: profile
      positive_value_hypothesis: "basic profile adds scale and physical feedback"
      gate_result: freeze-with-review-bound-warning
      residual_failure_modes:
        - "less deterministic field and lint coverage"
    - round: 3
      change_type: profile
      positive_value_hypothesis: "advanced four-layer profile uses runtime support to improve reviewable surfaces"
      gate_result: freeze-with-review-bound-warning
      residual_failure_modes:
        - "generated image may still drift"
  runtime_rescue_cost: unknown
  final_artifact_path: "examples/loop-assisted-image-comparison.md"
  final_claim_ceiling: "Images2 output is loop-assisted production evidence for one run; it does not prove the profile is generally strong."
```

## Comparison Frame

Subject: `black tide dragon bone god`

Comparison target: baseline vs basic profile vs advanced four-layer profile.

Images2 output is loop-assisted production evidence. It does not prove the profile is
generally strong, and it does not prove future image models will preserve the same style.

## Prompt Packet A - Baseline Ordinary Expansion

A huge dragon-bone god rises from a black ocean, dark and cinematic, with mysterious
lighting, dramatic waves, ancient bones, and an epic atmosphere. The image should feel
realistic, detailed, and impressive.

## Prompt Packet B - Basic TVG Profile

A colossal dragon-bone deity appears in a black deep-sea current, partly hidden by
murky water and darkness. A small submersible and diver lights in the foreground provide
human scale, a broken shipwreck and trench wall sit in the midground, and the deity's
rib-like silhouette disappears into the distant water. Silt, loose cables, fish, and
light beams react to the moving current. Low witness viewpoint, restrained upward angle,
wide cinematic frame, deep blue-gray shadows, controlled highlights, realistic water
scatter, weathered bone texture.

## Prompt Packet C - Advanced Four-Layer Profile

Inside a small submersible looking through a scratched forward window, a black tide
pushes silt across the lamp beams as a dragon-bone god emerges only in fragments from
the deep-sea trench. The foreground holds instrument glow, a blurred observer shoulder,
and water marks on glass. The midground shows torn ship cables, broken mast ribs, and
fish suddenly turning away. In the background, a half-lit skull ridge and immense rib
arches cross the trench walls before vanishing beyond the frame. The camera stays low
and close to the witness position with medium telephoto compression, 2.39:1 widescreen
composition, layered dark exposure, submersible lamp scatter through turbid water,
stone-white bone, rusted gold sediment, near-black current shadows, fine film grain,
and imperfect lens-edge haze. Avoid plastic surface, weightless floating, blank clean
background, no environment contact, flat even lighting, poster centered subject,
missing human scale anchor, overly saturated color, and over-sharpened edges.

## Images2 Comparison Claim Ceiling

- This run can support one-run loop-assisted production observations.
- It cannot prove the profile is generally strong.
- It cannot prove future image models will preserve the same style.
- If generated images are stored, binary files should stay local or under ignored artifact paths unless explicitly requested.

## One-Run Observation

Local ignored artifacts:

- `tests/artifacts/tvg_cinematic_colossal_a_baseline.png`
- `tests/artifacts/tvg_cinematic_colossal_b_basic.png`
- `tests/artifacts/tvg_cinematic_colossal_c_advanced.png`

Artifact storage note: these files match the repository's ignored `tests/artifacts/tvg_*.png`
pattern. They are local comparison evidence, not release-pack fixtures.

Observed one-run comparison:

- A / baseline produced a dramatic full-subject monster image. It carried spectacle,
  but witness position, human-scale anchoring, field pressure, and physical feedback
  were weak.
- B / basic profile improved the scene into a readable underwater scale relation with
  submersible, wreck, trench, and partial colossal form. It still leaned toward
  impressive skeletal ruins more than a witnessed divine presence.
- C / advanced four-layer profile made the witness position much harder to lose:
  window, instruments, observer shoulder, turbid light beams, cables, silt, and
  frame-overflowing subject fragments were all more inspectable.

Review-bound conclusion:

The advanced four-layer profile produced the strongest prompt-to-image control in this
single run. This is loop-assisted production evidence only. It supports further profile
iteration, not a claim that the profile is mature or generally stronger than the
external skill.

## Stable Lessons From Loop-Assisted Comparison

The useful outcome of loop-assisted comparison is not "beat the donor skill on one
image." It is to translate repeated observations into reusable profile surfaces and
operating guidance.

Across the local runs, the stable lesson was:

- the advanced four-layer profile improves inspectable prompt surfaces compared with
  baseline ordinary expansion
- image comparisons are valid only when they become reusable profile semantics,
  review handles, or boundary language
- the external skill remains a behavior sample, not source truth and not the success
  criterion for this package

## Behavior-Surface Extraction

Loop-assisted comparison produced five profile-level extractions that survived beyond one
scene:

1. `decisive pressure frame`: high-pressure scenes need one dominant subject fragment
   that lands before secondary detail.
2. `director shot spine`: one focal decision, one eye path, one reveal reason, and
   secondary details that serve the chosen frame.
3. `controlled fracture coherence`: dirty, rainy, broken, or occluding material should
   read as usable pressure rather than random clutter.
4. `shot economy mode`: high-pressure prompts need subtractive selection so valid detail
   does not become equal-weight competition.
5. `director subtraction pass`: if a frame reads like many small actions, demote
   competing highlights, parallel micro-actions, gratuitous foreground intrusion, and
   decorative destruction until one major event survives first read.

These extractions are what justify the loop. If a future image comparison cannot be
translated into a reusable profile surface, gain move, or boundary rule, it should not
change this package.

## Pressure-Fit Guidance

The current profile behaves more like a pressure ladder than a single best setting:

- `pressure 2`: best for establishing shots, broader environment legibility, and calmer
  atmosphere
- `pressure 3`: best general starting point for this profile; it preserves scene width
  while adding clearer directorly pressure
- `pressure 4`: best working point when one decisive event should dominate the frame
  without losing witness scale
- `pressure 5`: strongest one-frame threat, useful when poster-force or peak oppression
  is wanted, with the known risk that field width may narrow

This is profile-scoped operating guidance, not proof that the pressure ladder is
globally optimal for TVG.

## Research Log

Detailed dated run notes, scene-specific comparisons, and local artifact inventories now
live in [loop-assisted-research-log.md](./loop-assisted-research-log.md). That split is
intentional: this file is the canonical exemplar note, while the research log preserves
local tuning evidence without turning session history into the main lesson.

This remains one-run loop-assisted production evidence, not proof that the external
skill is generally better or that the tuned profile is generally mature.
