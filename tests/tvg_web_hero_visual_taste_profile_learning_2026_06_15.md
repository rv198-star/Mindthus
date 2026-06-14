# TVG Web Hero Visual Taste Profile Learning Record — 2026-06-15

## Purpose

This record follows issue #47 after two true image blind tests showed that TVG+Profile
did not beat direct prompting or an external visual taste benchmark in single hero
image generation.

The user then asked whether Mindthus profiles should start learning from Taste.

This record answers yes, with a boundary:

> Learn the domain discipline, not the external prompt text.

The resulting profile is:

`skills/tvg/resources/value-profiles/web-hero-visual-taste.md`

## Why A New Profile

The previous `ui-redesign-critique-taste` profile is text-first. It helps turn weak
UI feedback into a concrete critique and first repair direction.

The blind tests showed that this is not enough for visual generation:

- a prompt can become more correct while the image becomes visually weaker;
- product semantics and evidence honesty do not automatically create first-look force;
- direct prompting can outperform a TVG prompt when the model already has strong
  visual priors for the scene;
- a dedicated visual taste benchmark remains stronger in some frontend-image cases.

Therefore the visual generation surface needs a distinct profile.

## Learning Boundary

Allowed learning:

- use external visual taste tools as black-box benchmarks;
- extract abstract domain principles from observed failures and reference material;
- name common AI-default visual tells;
- require composition, visual protagonist, media/material treatment, hierarchy, and
  CTA priority to be visible in the prompt and output;
- compare against direct prompting before claiming improvement.

Disallowed learning:

- copying external Taste Skills prompt wording;
- copying checklist wording, examples, or internal section structure;
- rebuilding another skill under Mindthus labels;
- optimizing toward one winning benchmark image's exact composition;
- claiming parity from one or two local blind tests.

## Abstracted Lessons

The new profile adds a visual-generation control layer that the critique profile did not
own strongly enough:

```yaml
learned_axes:
  - first-look-visual-force
  - visual-protagonist
  - composition-specificity
  - media-material-direction
  - typography-and-hierarchy
  - CTA-priority
  - palette-and-style-coherence
  - anti-template-specificity
  - frontend-reference-usability
```

Key change:

> A visual prompt is not good just because it is honest, specific, and product-aware.
> It must also make a clear visual choice.

## Source Attribution

TVG / Mindthus-derived:

- value_profile shape;
- evidence honesty;
- claim ceilings;
- veto constraints;
- profile source boundary;
- loop and Gate discipline.

Local experiment-derived:

- DeskPilot blind result: external visual benchmark first, direct second, TVG third.
- Clayroom blind result: direct first, external benchmark second, TVG third.
- Diagnosis: TVG self-iteration can narrow the gap, but does not yet prove visual taste
  parity.

External domain-reference-derived:

- avoid common AI-default visual tells;
- do not rely on generic premium adjectives;
- make composition explicit;
- use image/material/product state as the design carrier;
- keep CTA and hierarchy visible;
- run pre-output checks before claiming a visual is good.

Explicitly not used:

- external prompt wording;
- external examples as reusable Mindthus content;
- exact external checklist structure;
- one benchmark image's winning composition as a general rule.

## Expected Next Test

The next fair test should not reuse the DeskPilot or Clayroom scenes.

Suggested scene categories:

- a cultural venue or museum exhibition landing hero;
- a complex nonprofit donation hero with evidence boundaries;
- a consumer product page where fake proof and stock imagery are tempting;
- a multi-section landing page where section rhythm matters more than one hero image.

Success should not mean "TVG beats Taste once." A better claim ladder is:

1. TVG no longer degrades direct prompting in simple hero tasks.
2. TVG beats direct prompting in constraint-heavy hero tasks.
3. TVG produces useful critique and repair directions even when it loses first-look
   image beauty.
4. Only repeated blind wins across scenes can support a stronger visual taste claim.

## Final Claim

This learning step supports a limited design change:

> TVG profiles can learn domain-specific visual-generation discipline from external
> benchmarks by abstracting principles into value semantics, realization surfaces, and
> gain policies.

It does not support:

- TVG replicates Taste Skills;
- TVG beats direct prompting for single hero images;
- TVG has general visual taste parity;
- external benchmark content can be copied into Mindthus.
