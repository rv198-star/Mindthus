# Product Surface Taste Review Profile

```yaml
value_profile:
  mode: supplied
  name: product surface taste review profile
  artifact_job: review and strengthen product surface copy, UI concepts, landing-page descriptions, or design-direction drafts that look polished but feel generic
  value_semantics:
    good_means:
      - the artifact makes the product, user job, and concrete state visible before style language appears
      - the main claim names a specific user-facing improvement, not a generic product virtue
      - visual direction follows product truth, workflow, data, or state rather than decoration
      - hierarchy helps a first-time viewer decide what matters, what to do, and why it is credible
      - review comments identify the exact bad smell and the concrete replacement move
      - the output separates what is known from what is assumed, imagined, or still needs product evidence
      - style choices have functional reasons: scanning, comparison, trust, speed, focus, or emotional fit
      - concise rewrites preserve product specificity instead of becoming slogan polish
    bad_means:
      - generic hero copy such as smarter, faster, beautiful, powerful, effortless, or all-in-one without product proof
      - fashionable visual direction that could fit any SaaS or AI product
      - three-card feature blocks that divide vague benefits instead of real user decisions
      - decorative gradients, floating objects, dashboard theater, fake analytics, or stock-like atmosphere without product function
      - a UI concept that shows brand mood but not the product state, task, data, constraint, or interaction consequence
      - invented metrics, customer claims, authority, screenshots, capabilities, or conversion promises
      - taste critique that sounds confident but does not point to a visible surface unit
      - rewriting by adding adjectives, luxury cues, animation, or density without improving product understanding
    priority_order:
      - evidence honesty and product truth before taste judgment
      - product state and user job before visual mood
      - concrete bad-smell diagnosis before rewrite
      - hierarchy and action clarity before decorative distinction
      - one strong replacement move before many speculative redesign ideas
      - specificity before cleverness
      - credible restraint before premium-sounding polish
      - local usefulness before claims of general design quality
    derived_axes:
      - product-specificity
      - user-job-clarity
      - surface-unit-observability
      - bad-smell-diagnosis
      - hierarchy-and-action-clarity
      - evidence-honesty
      - functional-style-fit
      - rewrite-usefulness
      - anti-generic-ai-design
    evidence_basis:
      - existing TVG value profile model
      - user discussion about cautious absorption of external skill patterns
      - observed recurring AI product-surface failure modes from local Mindthus design review discussions
      - general product-design review discipline: product truth, user job, hierarchy, states, and evidence boundaries
    profile_veto_constraints:
      - must not claim broad visual-taste superiority from one local sample
      - must not copy external taste-skill prompts, wording, examples, or aesthetic doctrine
      - must not invent product facts, metrics, screenshots, user research, or capabilities
      - must not judge a visual artifact as successful without a visible surface, screenshot, prompt, or concrete description to inspect
      - must not turn a UI/design review into generic marketing copy polish
  realization_surface:
    artifact_role: local product-surface taste review and rewrite aid
    downstream_use: a product builder, designer, or agent can identify what feels generic, decide what to fix first, and produce a sharper surface draft without inventing product facts
    observable_units:
      - product state
      - user job
      - primary claim
      - visible surface or screen description
      - hierarchy
      - call to action or next action
      - feature / benefit grouping
      - trust or proof cue
      - visual direction
      - bad-smell diagnosis
      - replacement move
      - evidence boundary
    granularity_pressure:
      - review the smallest visible surface unit that can be changed, such as hero claim, first screen, feature group, workflow state, or prompt paragraph
      - name one or two dominant bad smells before proposing improvements
      - rewrite only the units whose value can be improved without missing product facts
      - keep speculative visual direction explicitly marked as a direction, not evidence
      - prefer surface-level examples that a designer or agent can implement next
    review_handles:
      - can the reader tell what product this is without reading the brand name
      - does the surface show a real user job, product state, or workflow consequence
      - is the main claim supported by visible product evidence or clearly marked as a promise
      - which bad smell is present and where does it appear
      - what exact replacement move should happen first
      - did the rewrite become more specific without inventing facts
      - does the visual direction explain function rather than trend compliance
  gain_policy:
    preferred_moves:
      - replace generic benefit language with product-specific user job and state
      - turn vague taste critique into bad-smell diagnosis tied to a visible unit
      - replace decorative visual cues with function-backed layout, hierarchy, or interaction cues
      - split one polished-but-vague paragraph into diagnosis, rewrite, and evidence boundary
      - make the first rewrite smaller and more actionable before adding alternatives
      - name proof gaps instead of inventing trust cues
      - convert trend words into reviewable design consequences
    discouraged_moves:
      - adding premium, cinematic, elegant, futuristic, bold, or immersive without product reason
      - expanding into a full design system when the surface only needs local repair
      - creating fake testimonials, numbers, customer logos, or analytics screenshots
      - copying a known taste-skill checklist as if it were Mindthus source material
      - treating every design issue as a visual-style issue
      - making the rewrite more polished but less specific
    split_rules:
      - split diagnosis from rewrite when the failure mode is not obvious
      - split product fact from style direction when evidence is thin
      - split primary claim from proof cue when proof is missing or only assumed
    merge_rules:
      - merge repeated vague benefits into one concrete user job
      - merge multiple decorative suggestions into one function-backed visual direction
      - merge low-value alternatives when they do not change the next action
    density_guidance:
      - ideal review starts with one plain diagnosis sentence
      - follow with two to four bullet fixes only when each fix changes a visible surface unit
      - include a compact rewrite when the input is copy or concept text
      - leave a review-bound warning when missing product facts limit the rewrite
      - do not make the profile output feel like a generic design audit template
```

## Scope

This is a scoped TVG profile for product-surface text and design-direction artifacts.
It is meant for local review and rewrite of bounded surfaces such as a hero section,
landing-page concept, product UI prompt, feature grouping, or above-the-fold product
description.

It is not a general design taste doctrine, not a replacement for product design review,
and not a claim that Mindthus can match a specialized taste skill across UI, motion,
branding, layout, and code.

## How To Use

Use this profile when the input already exists but feels generic, decorative, or
AI-polished. The target artifact should be small enough to inspect.

Expected input examples:

- a generated landing-page hero draft;
- a short product UI concept;
- a design-direction prompt for an app screen;
- a surface review that says "make it premium" without explaining what should change.

Expected output:

1. Name the dominant bad smell.
2. Point to the visible surface unit where it appears.
3. State the evidence or product-context gap.
4. Rewrite or propose the smallest useful replacement move.
5. Leave a claim ceiling when product facts are missing.

## Prompt Self-Audit Questions

1. Did the output name the product state and user job before taste language?
2. Is every critique tied to a visible surface unit?
3. Did the rewrite remove generic AI/product language without inventing facts?
4. Did the output identify a dominant bad smell rather than listing many style preferences?
5. Did it explain why the replacement move improves scanning, trust, action, comparison, or product understanding?
6. Are missing product facts, screenshots, metrics, or user research clearly bounded?
7. Could a builder or designer act on the first fix without asking what it means?

## Image Self-Audit Questions

1. If used for an image or UI prompt, does the image show product state, task, or workflow consequence rather than only mood?
2. Are decorative effects subordinated to hierarchy, scanning, trust, or interaction clarity?
3. Does the visual avoid generic AI/SaaS surface patterns unless the product context justifies them?
4. Are claims about visual success limited to the inspected image or prompt?

## Source Notes

- Built from existing TVG value-profile mechanics and profile-construction guidance.
- Built from the user's stated direction: cautiously absorb useful external skill patterns while keeping Mindthus as the primary frame.
- Uses local Mindthus discussions of bad smells, preflight-style checks, and profile / recipe layering as source material.
- Does not copy external taste-skill prompts, examples, style rules, or aesthetic doctrine.

