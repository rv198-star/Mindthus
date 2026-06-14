# UI Redesign Critique Taste Profile

```yaml
value_profile:
  mode: supplied
  name: ui redesign critique taste profile
  artifact_job: strengthen vague UI/design feedback into concrete redesign critique that names bad smells, affected surface units, user impact, and the first repair move
  value_semantics:
    good_means:
      - the critique starts from the screen's job and the user's decision, not from style preference
      - each judgment points to a visible UI surface unit such as hero claim, CTA, navigation, proof cue, feature group, form state, pricing card, dashboard header, or empty state
      - the output names the dominant bad smell before proposing fixes
      - the critique explains why the bad smell hurts scanning, trust, comparison, action, comprehension, or product credibility
      - the first repair move is small enough to implement or prompt next
      - style recommendations are tied to information hierarchy, interaction clarity, brand fit, or user confidence
      - missing evidence, missing screenshots, invented metrics, and unverified product claims stay visible
      - the output separates critique, repair, and evidence boundary instead of blending them into confident taste talk
      - the redesigned direction reduces generic AI/SaaS defaults without replacing them with arbitrary aesthetic fashion
      - success is measured by whether a builder or designer can act without guessing what the critique means
    bad_means:
      - saying make it premium, modern, clean, sleek, exciting, cinematic, or more polished without naming the surface failure
      - generic AI/SaaS patterns: purple-blue gradient hero, floating glass cards, fake dashboard, three vague feature cards, AI sparkle, random orbs, and empty "all-in-one" claims
      - critique that only says hierarchy is weak, spacing is off, or visual design is bad without locating the issue
      - inventing metrics, customer proof, screenshots, integrations, or user research to make the redesign feel credible
      - redesigning the whole page when one surface unit is the real blocker
      - replacing product-specific clarity with trend-driven aesthetics
      - giving a list of visual preferences without naming user impact
      - treating a generated mockup as proof that the UX or brand decision is correct
      - overfitting to a single image artifact instead of extracting a reusable critique pattern
      - turning taste review into generic marketing copy polish
    priority_order:
      - evidence honesty and user constraints before taste confidence
      - screen job and user decision before visual mood
      - dominant bad smell before fix list
      - visible surface unit before general design advice
      - user impact before aesthetic opinion
      - smallest useful repair before full redesign
      - product-specific clarity before decorative distinction
      - reviewability before broad taste claims
    derived_axes:
      - screen-job-clarity
      - user-decision-clarity
      - visible-surface-unit
      - bad-smell-specificity
      - causal-explanation
      - first-repair-actionability
      - hierarchy-and-scanning
      - evidence-honesty
      - anti-generic-ai-ui
      - scope-control
      - downstream-design-handoff
    evidence_basis:
      - existing TVG value profile model
      - TVG value-profile construction guide
      - user direction to test taste-good behavior in critique/redesign scenarios rather than pure image generation
      - general UI review discipline: task clarity, visual hierarchy, affordance, proof, state, density, and evidence limits
      - local Mindthus experiments showing brandkit image generation can hide profile weakness behind model aesthetics
    profile_veto_constraints:
      - must not claim broad parity with a dedicated taste skill from one redesign critique pilot
      - must not copy external taste-skill prompts, wording, examples, or aesthetic doctrine
      - must not use leaked external skill internals as profile source material
      - must not invent product facts, metrics, screenshots, user research, customer proof, integrations, or conversion claims
      - must not treat a generated image or mockup as validated UX evidence
      - must not recommend a full redesign when the critique only supports a local repair
      - must not hide uncertainty behind confident design taste language
  realization_surface:
    artifact_role: local UI redesign critique and repair-direction aid
    downstream_use: a product builder, designer, or agent can identify what feels wrong, why it matters, what to fix first, and what evidence is missing before producing a redesign prompt or code change
    observable_units:
      - screen job
      - user decision
      - visible surface unit
      - dominant bad smell
      - user impact
      - first repair move
      - hierarchy / scanning path
      - CTA or next action
      - proof or trust cue
      - product state
      - style direction
      - evidence boundary
      - handoff instruction
    granularity_pressure:
      - review the smallest surface unit that can be changed without reopening the whole product
      - name at most two dominant bad smells before repairs
      - make each fix observable in layout, copy, state, hierarchy, CTA, proof, or interaction
      - keep speculative design direction explicitly marked as direction, not proof
      - prefer one strong first repair over a long redesign wishlist
      - if no screenshot or concrete screen description exists, block or request the missing surface instead of pretending to inspect it
    review_handles:
      - can the reader point to the exact UI unit that fails
      - does the critique explain the user's lost decision or action
      - is the first repair implementable without a second interpretation step
      - did the output remove generic AI/UI slop without inventing product proof
      - did style language serve hierarchy, trust, comparison, focus, or brand fit
      - is the evidence boundary clear enough to prevent fake confidence
      - would a designer or front-end agent know what to change next
  gain_policy:
    preferred_moves:
      - convert vague taste words into bad smell -> visible unit -> user impact -> first repair
      - replace generic visual advice with hierarchy, state, CTA, proof, or scanning changes
      - separate product fact from design assumption when evidence is thin
      - turn broad redesign requests into one local repair plus optional next iteration
      - add a compact before / after surface rewrite when copy or layout description is available
      - name missing evidence instead of inventing screenshots, metrics, or user behavior
      - add review handles that a designer or front-end agent can use after the next mockup
    discouraged_moves:
      - adding more adjectives, design trends, or visual drama without improving the user decision
      - producing a full page redesign when only critique is justified
      - using fake proof, fake dashboards, or fake metrics to make a repair persuasive
      - treating every issue as visual style rather than information, trust, or action clarity
      - copying a dedicated taste-skill checklist as if it were Mindthus source material
      - declaring taste success before inspecting the revised surface
    split_rules:
      - split diagnosis from repair when the failure mode is not obvious
      - split known product facts from design assumptions
      - split immediate first repair from later visual exploration
      - split image/model failure from design judgment when generated visuals are involved
    merge_rules:
      - merge repeated vague critique into one dominant bad smell
      - merge low-value fixes that do not change a visible surface unit
      - merge decorative suggestions into one function-backed style direction
    density_guidance:
      - ideal critique starts with one plain diagnosis sentence
      - follow with a compact table or bullets only when each row changes a surface unit
      - include one first repair and one evidence boundary
      - do not make the output feel like a generic design audit template
```

## Scope

This is a scoped TVG profile for UI redesign critique. It is meant to test a more
TVG-native taste scenario than brand-board image generation: judging and improving a
bounded surface description or screenshot-derived critique.

It is not a general UI design doctrine, not a replacement for product design review,
not a visual generation skill, and not a claim that Mindthus can match a dedicated
taste skill across frontend implementation, motion, visual production, or brand systems.

## How To Use

Use this profile when the input is a bounded UI/screen description, screenshot summary,
or weak design critique, such as:

- "this landing hero feels generic";
- "review this pricing card";
- "why does this dashboard header feel AI-made";
- "make this redesign feedback useful."

Expected output:

1. Name the screen job and user decision.
2. Name the dominant bad smell.
3. Point to the visible surface unit.
4. Explain the user impact.
5. Propose the first repair move.
6. State what evidence or surface is missing.
7. Leave a claim ceiling when no screenshot, product facts, or user data are available.

## Prompt Self-Audit Questions

1. Did the critique start from screen job and user decision rather than taste adjectives?
2. Is every judgment tied to a visible surface unit?
3. Did it name a dominant bad smell before proposing fixes?
4. Does each fix change hierarchy, state, CTA, proof, scanning, or product clarity?
5. Did it avoid fake screenshots, metrics, customer proof, and invented user research?
6. Is the first repair small enough to implement or prompt next?
7. Could a designer or front-end agent act on the critique without guessing?

## Image / Mockup Self-Audit Questions

1. If a revised mockup is generated, does it actually repair the named surface failure?
2. Does the image become prettier while leaving the user decision unclear?
3. Are proof cues and screenshots clearly real, conceptual, or missing?
4. Does the revision reduce generic AI/SaaS defaults without becoming another trend template?
5. Is another round justified by a named visible repair, not by vague polish?

## Source Notes

- Built from existing TVG value-profile mechanics and profile-construction guidance.
- Built from the user's direction to move beyond failed Logo/brandkit visual-generation probes and test a critique-first taste scenario.
- Uses general UI review principles: task clarity, visible surface units, hierarchy, affordance, proof, state, density, and evidence limits.
- Uses local Mindthus results showing that pure image-generation taste probes can conflate profile quality with model aesthetics.
- Does not copy external taste-skill prompts, examples, style rules, or aesthetic doctrine.
- The 2026-06-15 local session accidentally exposed external taste-skill internals during an attempted black-box run. Those contents are treated as pollution and are not source material for this profile.
