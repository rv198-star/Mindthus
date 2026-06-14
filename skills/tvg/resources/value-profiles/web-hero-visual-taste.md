# Web Hero Visual Taste Profile

```yaml
value_profile:
  mode: supplied
  name: web hero visual taste profile
  artifact_job: strengthen a website hero image-generation prompt into a visually strong, conversion-aware, evidence-honest frontend reference
  value_semantics:
    good_means:
      - the hero has a clear first-viewport job tied to the user's decision or next action
      - the prompt chooses one visual protagonist instead of listing many decorative elements
      - visual direction is derived from the brief, domain, audience, and conversion job rather than from generic premium adjectives
      - composition is a deliberate choice, not an automatic centered hero or default left-text / right-asset split
      - image, material, product state, photography, or spatial artifact carries the design, not decoration around text
      - typography hierarchy, CTA priority, spacing, palette, and media treatment are all visible in the generated frame
      - the result feels like a frontend reference that could be implemented, not a mood poster or abstract AI art
      - the prompt blocks unsupported proof such as fake metrics, fake reviews, fake customer logos, fake scarcity, and fake screenshots
      - the output has first-look visual force while still serving the product, venue, offer, or user decision
      - the prompt names a small set of avoidable AI-default visual tells relevant to the brief
    bad_means:
      - making the prompt more correct while flattening the first-look visual appeal
      - using style adjectives such as premium, modern, clean, or cinematic without a concrete composition, media, material, or typography decision
      - default AI/SaaS visuals such as purple-blue glow, floating glass cards, fake dashboards, sparkles, generic bot icons, or random orbs
      - warm local-business templates that look pleasant but generic, with no memorable visual subject
      - overloading the prompt with checklists until the image becomes a requirements diagram
      - inventing reviews, ratings, customer proof, metrics, discounts, live availability, teacher bios, screenshots, or integrations
      - repeating three equal cards, centered slab sections, decorative labels, fake status strips, or bottom text ornaments when they do not serve the user decision
      - treating visual taste as only evidence honesty, product semantics, or critique correctness
      - copying external visual taste-skill wording, prompt structures, examples, or checklists as reusable Mindthus content
      - claiming parity with a dedicated visual design skill from one or two local blind tests
    priority_order:
      - user constraints and evidence honesty before visual persuasion
      - hero job before aesthetic mood
      - visual protagonist before decorative list
      - composition choice before prompt ornament
      - first-look force before secondary detail
      - domain fit before generic premium style
      - CTA clarity before visual cleverness
      - implementable frontend reference before poster-like atmosphere
      - claim ceiling before benchmark claims
    derived_axes:
      - hero-job-clarity
      - first-look-visual-force
      - visual-protagonist
      - composition-specificity
      - media-material-direction
      - typography-and-hierarchy
      - CTA-priority
      - palette-and-style-coherence
      - anti-template-specificity
      - evidence-honesty
      - frontend-reference-usability
      - benchmark-claim-ceiling
    evidence_basis:
      - existing TVG value profile model
      - TVG profile construction guidance
      - local issue #47 blind tests where TVG critique improved reasoning but did not win single-image visual hero tests
      - external visual taste-skill repository used only as a domain reference and benchmark signal
      - general frontend design discipline around hierarchy, composition, media treatment, CTA clarity, spacing, typography, and evidence boundaries
    profile_veto_constraints:
      - must not copy external taste-skill prompts, paragraphs, examples, checklist wording, or proprietary-looking structure into Mindthus
      - must not treat a visual benchmark result as source material for exact prompt imitation
      - must not claim TVG+profile can replicate or outperform a dedicated visual taste skill without repeated blind evidence
      - must not invent product facts, proof, screenshots, reviews, ratings, metrics, scarcity, discounts, or integrations
      - must not pass a prompt that is correct but likely to produce a flat requirements diagram
      - must not hide that image-model aesthetics can dominate profile quality
  realization_surface:
    artifact_role: web hero image-generation prompt and self-audit aid
    downstream_use: an agent can generate a stronger single hero reference, inspect whether it has visual force and claim honesty, then decide whether to iterate or keep it as a candidate
    observable_units:
      - hero job
      - target visitor decision
      - visual protagonist
      - composition anchor
      - image / material / product-state treatment
      - typography hierarchy
      - CTA treatment
      - palette and texture logic
      - spacing and density
      - anti-template avoid list
      - evidence boundary
      - generated-image self-audit
    granularity_pressure:
      - use one hero frame as the bounded module unless the user asks for multi-section work
      - choose one primary visual idea, not five competing motifs
      - keep the prompt concise enough for the image model to execute
      - make the first visual repair visible in composition, media, material, hierarchy, or CTA treatment
      - stop adding constraints when they no longer improve first-look quality
      - if the generated image loses beauty while gaining correctness, return-remediate instead of freezing
    review_handles:
      - can a viewer describe the hero's visual subject after one glance
      - does the frame feel like a homepage hero rather than a diagram, ad poster, or dashboard screenshot
      - is the CTA visible and aligned with the page job
      - did the image avoid unsupported proof and fake precision
      - is the composition different because the brief demanded it, not because novelty was forced
      - would a frontend builder understand layout, hierarchy, spacing, media treatment, and CTA priority
      - did the output beat or at least not degrade a clear direct prompt candidate
  gain_policy:
    preferred_moves:
      - turn vague taste goals into hero job -> visual protagonist -> composition anchor -> media/material treatment -> CTA priority
      - add visual force by selecting a stronger subject, crop, perspective, scale contrast, or material surface
      - replace generic feature cards with domain-specific visual evidence or an honest conceptual state
      - translate critique into image-executable prompt language without copying an external skill's phrasing
      - add a small anti-template avoid list tailored to the brief
      - preserve unsupported-proof boundaries while still allowing atmosphere, photography, texture, and editorial composition
      - compare against a direct prompt candidate before claiming improvement
    discouraged_moves:
      - adding more adjectives when the visual protagonist is weak
      - adding more constraints after the image already feels visually flat
      - forcing SaaS hero rules onto local venue, editorial, craft, consumer, or culture scenes
      - using evidence honesty as an excuse for boring visuals
      - imitating a benchmark's winning composition after seeing it win
      - using one blind-test win or loss as a broad profile verdict
    split_rules:
      - split critique profile from visual generation profile
      - split semantic correctness from first-look visual quality
      - split external benchmark learning from source copying
      - split image-model failure from profile failure when self-auditing
    merge_rules:
      - merge repeated visual constraints into one clear art-direction sentence
      - merge decorative avoid lists into a few high-impact anti-template tells
      - merge feature lists into one visual product, place, object, or material story when possible
    density_guidance:
      - prompt should be specific but not encyclopedic
      - visual direction should name concrete composition/media choices
      - audit should be short, comparative, and honest about whether the result improved over direct prompting
```

## Scope

This is a scoped TVG profile for website hero visual prompt generation. It is not a
general frontend design doctrine, not a replacement for a dedicated visual design
skill, and not a claim that TVG can replicate Taste Skills.

Its purpose is narrower: help TVG stop producing prompts that are merely correct,
well-bounded, and product-specific while still visually flat.

## Learning Boundary

Learn the domain discipline, not the external prompt text.

This profile may learn from external visual taste tools in the following way:

- use them as black-box benchmarks;
- extract abstract design principles such as avoiding common AI-default visual tells,
  choosing a composition deliberately, using imagery or material as the main design
  carrier, and checking first-look force;
- record negative results honestly when TVG loses.

It must not learn by:

- copying external prompt wording, examples, or checklist text;
- rebuilding another skill's internal structure under Mindthus names;
- optimizing toward one benchmark image's exact winning composition;
- claiming parity without repeated blind tests across different scenes.

## How To Use

Use this profile when the bounded artifact is a website hero image-generation prompt or
a generated hero image that needs visual prompt repair.

Expected output should include:

1. Hero job and visitor decision.
2. One visual protagonist.
3. Composition anchor.
4. Media / material / product-state direction.
5. Typography, CTA, palette, and spacing cues.
6. Brief-specific anti-template avoid list.
7. Evidence boundary.
8. Self-audit comparing the result against direct prompting when possible.

## Prompt Self-Audit Questions

1. Did the prompt name one strong visual protagonist?
2. Is the composition chosen because of the brief rather than by habit?
3. Does the image direction have first-look force, not only semantic correctness?
4. Did the prompt avoid fake proof, fake metrics, fake scarcity, fake screenshots, and fake customer logos?
5. Does the frame likely read as a homepage hero rather than a requirements diagram?
6. Is the prompt concise enough for the image model to execute?
7. Is this profile learning an abstract visual principle rather than copying a benchmark prompt?

## Image Self-Audit Questions

1. Would this beat or at least not degrade a clear direct prompt candidate?
2. What is the first thing a viewer notices, and is that the intended visual protagonist?
3. Does the image feel domain-specific or merely styled?
4. Did evidence honesty make the image boring?
5. Did visual ambition introduce unsupported proof?
6. Should the next round change profile strategy, prompt wording, or simply reject the candidate?

## Source Notes

- Built from existing TVG profile mechanics and issue #47 local blind tests.
- The external Taste Skills repository is treated as a domain reference and benchmark
  signal, not as text to copy into Mindthus.
- The DeskPilot and Clayroom blind tests showed that TVG self-iteration can improve
  reasoning and narrow gaps, but current evidence does not show visual taste parity.
- This profile therefore focuses on the missing layer: visual generation control,
  first-look force, and anti-template discipline.
