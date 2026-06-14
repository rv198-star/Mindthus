# Brandkit Board Prompt Taste Profile

```yaml
value_profile:
  mode: supplied
  name: brandkit board prompt taste profile
  artifact_job: strengthen vague product or brand briefs into image-generation prompts for reviewable brand-kit overview boards
  value_semantics:
    good_means:
      - the prompt turns the brief into a clear brand thesis before choosing visual style
      - the board shows a coherent identity system, not isolated attractive panels
      - logo, palette, typography, UI/application panels, and atmosphere all point back to the same brand idea
      - each panel has a job and a visible relationship to neighboring panels
      - the prompt controls layout, hierarchy, density, palette, typography risk, and application realism
      - visual richness is used to clarify the brand world, not to hide weak concept selection
      - the board has enough art-directed surface quality, material contrast, rhythm, and atmosphere to feel like a real brand direction
      - the board leaves enough white space or quiet space for the system to feel intentional
      - the prompt avoids generic AI/SaaS visual defaults unless the product truth justifies them
      - the output includes review handles for whether the board is coherent, distinctive, and usable
      - the image prompt includes a visible-quality gate: if the board would look ugly, dutiful, or template-like, the prompt is not ready
      - evidence limits are explicit when brand strategy, audience research, product screenshots, legal review, or real assets are missing
    bad_means:
      - a pretty moodboard whose panels do not share one brand logic
      - generic dark-tech SaaS board with glowing gradients, fake dashboards, abstract orbs, and random UI chips
      - luxury/premium words used as decoration without brand role or product reason
      - too many panels, styles, colors, fonts, symbols, or mockups competing for attention
      - logo direction, palette, UI application, and atmosphere contradict each other
      - fake screenshots, metrics, customer proof, awards, social proof, or legal trust seals
      - dense tiny text that image models will render as unreadable filler
      - treating a brand-board image as validated brand strategy
      - copying famous brand systems, protected marks, or a living designer's signature style
      - judging success by polish while the underlying brand idea remains generic
    priority_order:
      - evidence honesty and user constraints before visual ambition
      - brand thesis before board style
      - system coherence before panel spectacle
      - one core metaphor before many decorative motifs
      - logo and application fit before atmosphere
      - hierarchy and density control before visual richness
      - art-directed surface quality before flat checklist compliance
      - distinctive restraint before generic premium polish
      - reviewability before broad taste claims
      - local prompt usefulness before claims of design quality
    derived_axes:
      - brand-thesis-clarity
      - system-coherence
      - panel-role-clarity
      - logo-system-fit
      - palette-and-typography-control
      - application-realism
      - anti-generic AI/SaaS brand-board behavior
      - anti-generic-brand-board
      - art-directed-surface-quality
      - visual-density-discipline
      - prompt-reviewability
      - visible-quality-gate
      - evidence-honesty
    evidence_basis:
      - existing TVG value profile model
      - TVG value-profile construction guide
      - user direction to benchmark TVG + Profile against a taste-skill-like brand output while keeping the profile scoped
      - general brand identity review discipline: brand idea, consistency, scalability, application fit, hierarchy, and evidence limits
      - observed recurring AI image-generation failures in local Mindthus brand-board and logo prompt discussions
    profile_veto_constraints:
      - must not claim broad parity with a dedicated taste skill from one local brand-board prompt pilot
      - must not copy external taste-skill prompts, wording, examples, or aesthetic doctrine
      - must not use leaked external skill internals as profile source material
      - must not copy or imitate famous brand systems, protected marks, brand assets, or living designers' signature styles
      - must not invent brand facts, market position, user research, awards, metrics, customer proof, or legal clearance
      - must not treat an image-generated brand board as validated brand strategy
      - must not let mockup polish hide weak logo, system, or brand-thesis fit
  realization_surface:
    artifact_role: local brand-kit board image-generation prompt and prompt-review aid
    downstream_use: a user or agent can turn a thin brand/product brief into a coherent reviewable brand-board prompt, generate visual directions, and diagnose whether failures came from brand thesis, panel structure, constraints, or model rendering
    observable_units:
      - known brand facts
      - brand thesis
      - target audience or use context
      - core metaphor
      - board layout
      - panel roles
      - logo direction
      - color system
      - typography direction
      - UI or product application
      - physical or environmental application
      - image/atmosphere direction
      - negative constraints
      - review handles
      - evidence boundary
    granularity_pressure:
      - use a bounded board format such as 2x3 or 3x3 instead of an unbounded visual world
      - name the job of every panel before adding style language
      - keep text sparse and large enough for image generation
      - specify whether product UI panels are conceptual applications rather than real screenshots
      - limit palette and type direction enough that the board looks like one system
      - include negative constraints for generic AI/SaaS boards and fake proof
      - mark unknown brand facts as assumptions or missing inputs
    review_handles:
      - can the brand thesis be stated in one sentence after seeing the board
      - do logo, palette, type, UI/application, and atmosphere feel like one system
      - does every panel have a clear job
      - is the board distinctive without relying on generic AI visuals
      - is the visual density controlled enough to inspect
      - does the prompt avoid fake screenshots, metrics, social proof, and legal claims
      - would a designer or agent know what to refine next
  gain_policy:
    preferred_moves:
      - convert vague brand adjectives into a brand thesis and core metaphor
      - choose a bounded board structure and assign panel roles
      - align logo direction, palette, type, UI/application, and atmosphere around the same brand idea
      - replace generic premium style words with visible system constraints
      - add negative constraints against generic AI/SaaS brand-board defaults
      - add one or two art-directed surface cues that improve texture, rhythm, or brand-world depth without inventing proof
      - separate known facts from assumed visual direction
      - add review handles that test system coherence rather than image polish alone
      - fail the output when structural coherence exists but the likely image result would still look ugly, dutiful, or template-like
      - reduce panel count or text density when the board becomes hard to inspect
    discouraged_moves:
      - expanding a thin brief into a fake full brand strategy
      - adding many panels, artifacts, colors, fonts, slogans, or mockups to look expensive
      - using fake dashboards, customer logos, awards, metrics, or trust seals
      - treating every brand as dark-tech, luxury, editorial, or cinematic by default
      - making the board so constrained that it becomes flat, dutiful, or visually ordinary
      - copying a dedicated taste-skill checklist as if it were Mindthus source material
      - declaring visual success before inspecting the generated image
    split_rules:
      - split known facts from assumptions when the brief is thin
      - split brand thesis from visual style when the prompt starts with mood words
      - split panel roles before writing the final image prompt
      - split image self-audit from the generation prompt when recording a pilot
    merge_rules:
      - merge repeated style adjectives into one brand thesis
      - merge low-value panels that do not add a distinct system role
      - merge decorative mockups when they do not reveal the brand system
    density_guidance:
      - ideal output starts with a one-sentence board diagnosis or brand thesis
      - include one primary image prompt and a compact self-audit
      - keep panel descriptions concrete but not overloaded
      - leave a review-bound warning when product assets, brand strategy, or legal review are missing
```

## Scope

This is a scoped TVG profile for brand-kit overview board prompts. It is meant to make
the #47 benchmark closer to a dedicated taste-skill's natural output space than a single
Logo mark test.

It is not a general design taste doctrine, not a professional brand-strategy method, not
legal trademark review, and not a claim that Mindthus can match a dedicated taste skill
across UI, motion, code, branding, and visual production.

The earlier `logo-design-prompt-taste` profile remains useful as a narrower subcase.
This profile targets a larger artifact: one image prompt for a coherent brand-board
system.

## How To Use

Use this profile when the input is a bounded product or brand brief and the desired
output is a single brand-kit overview image prompt, such as:

- "make a premium brand board for this AI app";
- "turn this product idea into a visual identity concept board";
- "generate a brand kit image prompt";
- "the brand board looks generic, improve the prompt."

Expected output:

1. Name the dominant brand-board bad smell or brand thesis gap.
2. State known brand facts and assumptions.
3. Choose one core metaphor or organizing idea.
4. Define a bounded board layout and panel jobs.
5. Produce one primary image-generation prompt.
6. Add negative constraints and image self-audit checks.
7. Leave a claim ceiling when brand facts, product assets, design review, or legal review are missing.

## Prompt Self-Audit Questions

1. Does the prompt define a brand thesis before visual style?
2. Do the panel roles form one system rather than a moodboard collage?
3. Are logo, palette, type, UI/application, and atmosphere aligned to the same idea?
4. Is text sparse enough to render and review?
5. Does the prompt create enough texture, rhythm, or atmosphere to feel like a brand world rather than a checklist?
6. Did the prompt block generic AI/SaaS board defaults and fake proof?
7. Are unknown product assets and brand facts clearly bounded?
8. Could a designer or agent know what to refine after seeing the image?

## Image Self-Audit Questions

1. Can the board's brand thesis be stated in one sentence?
2. Does the board feel coherent across panels?
3. Is the logo/system relationship visible, or are panels merely decorative?
4. Are UI/product applications clearly conceptual when no real screenshots exist?
5. Is the board distinctive without leaning on generic gradients, orbs, fake dashboards, or stock mockups?
6. Does it have enough material contrast, visual rhythm, and atmosphere to avoid feeling dutiful or ordinary?
7. Is visual density controlled enough for inspection?
8. Does the result remain only a prompt/image probe, or has it been falsely treated as validated brand strategy?

## Source Notes

- Built from existing TVG value-profile mechanics and profile-construction guidance.
- Built from the user's stated direction to move the #47 benchmark closer to taste-skill's natural brand-system output space.
- Uses general brand identity review principles: brand idea, system coherence, scalable identity, application fit, hierarchy, and evidence limits.
- Uses local Mindthus discussions of bad smells, preflight-style checks, profile / recipe layering, value-gain scoring, and the single-Logo probe being too narrow.
- Does not copy external taste-skill prompts, examples, style rules, or aesthetic doctrine.
- The 2026-06-15 local session accidentally exposed external taste-skill internals during an attempted black-box run. Those contents are treated as pollution and are not source material for this profile.
