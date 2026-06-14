# Logo Design Prompt Taste Profile

```yaml
value_profile:
  mode: supplied
  name: logo design prompt taste profile
  artifact_job: strengthen vague logo requests into image-generation prompts and review notes that produce more usable, brand-grounded logo directions
  value_semantics:
    good_means:
      - the prompt starts from brand role, audience, and intended use before style adjectives
      - the logo has one clear visual idea instead of a pile of symbols
      - the mark can be imagined as a simple vector sign, not only as a rendered illustration
      - the prompt controls logo deliverability: flat mark, wordmark or symbol choice, color limits, background, and negative space
      - small-size recognizability, monochrome viability, and silhouette strength are treated as taste signals
      - visual metaphor is specific enough to guide generation but not so literal that it becomes clip art
      - typography direction supports the brand role and does not become random font decoration
      - variants explore meaningful strategic differences, not only color swaps or prompt noise
      - review names the exact bad smell and the first repair move
      - the output separates known brand facts from invented positioning or market claims
    bad_means:
      - generic AI logo language such as futuristic, premium, sleek, innovative, cutting-edge, or modern without brand reason
      - default AI logo tropes: glowing gradient orb, neural brain, circuit lines, hexagon tech badge, abstract swoosh, random spark, floating 3D icon
      - too many concepts forced into one mark
      - photorealistic mockups, embossed signage, dramatic lighting, or product packaging that hide whether the logo itself works
      - marks that only work as app icons but fail as brand identity
      - unreadable text, pseudo-letters, generated typography artifacts, or invented brand names
      - copying famous brand cues, protected marks, or recognizable designer signatures
      - taste critique that says "make it better" without naming a visible prompt unit
      - adding style density when the prompt needs concept reduction
      - claiming professional brand validation from a single image-generation result
    priority_order:
      - evidence honesty and user constraints before visual ambition
      - brand role before style mood
      - one memorable visual idea before many clever details
      - mark legibility before decorative richness
      - scalable vector-like structure before rendered scene
      - typography readability before font personality
      - controlled constraints before prompt inflation
      - useful variants before random alternatives
      - reviewable bad-smell repair before subjective taste claims
      - local prompt usefulness before broad design-quality claims
    derived_axes:
      - brand-role-clarity
      - visual-idea-focus
      - logo-deliverability
      - small-size-recognition
      - monochrome-and-silhouette-viability
      - typography-control
      - anti-generic-ai-logo
      - prompt-constraint-quality
      - variant-strategy
      - evidence-honesty
    evidence_basis:
      - existing TVG value profile model
      - TVG value-profile construction guide
      - user direction to build a local taste-skill-style profile without copying external taste-skill internals
      - general logo review discipline: simplicity, distinctiveness, scalability, reproducibility, brand fit, and usage-context awareness
      - observed recurring AI image-generation logo failures in local Mindthus discussions
    profile_veto_constraints:
      - must not claim broad parity with a dedicated taste skill from one local logo prompt pilot
      - must not copy external taste-skill prompts, wording, examples, or aesthetic doctrine
      - must not copy or imitate famous logos, protected marks, brand assets, or living designers' signature styles
      - must not invent brand facts, market position, user research, awards, metrics, or legal clearance
      - must not judge a logo successful only from a polished mockup without inspecting the mark itself
      - must not use prompt inflation as a substitute for visual concept selection
  realization_surface:
    artifact_role: local logo image-generation prompt and prompt-review aid
    downstream_use: a user or agent can turn a vague logo request into a constrained prompt, generate reviewable logo directions, and diagnose whether the result failed because of concept, constraints, or model rendering
    observable_units:
      - brand facts
      - brand role
      - target audience or use context
      - logo type
      - core visual idea
      - mark geometry
      - wordmark or typography direction
      - color constraints
      - style constraints
      - negative prompt / forbidden tropes
      - variant strategy
      - bad-smell diagnosis
      - image self-audit
      - evidence boundary
    granularity_pressure:
      - keep the first generated prompt focused on one dominant visual idea
      - name logo type explicitly: symbol, wordmark, lettermark, combination mark, or icon-only direction
      - specify flat vector-like output before any mockup or environmental presentation
      - limit color and material language unless the use case requires richer presentation
      - include negative constraints for generic AI logo tropes
      - ask for two to three strategic variants only when they test different ideas
      - keep brand assumptions marked as assumptions when the brief is thin
    review_handles:
      - can the logo idea be explained in one sentence
      - does the prompt make a mark, not just a mood board
      - would the mark still read at favicon or app-icon size
      - can it plausibly work in one color
      - does the typography direction reduce generated text risk
      - are generic AI-logo tropes actively blocked
      - are variants strategically different or merely decorative swaps
      - does the review identify concept failure, constraint failure, or model-rendering failure
  gain_policy:
    preferred_moves:
      - convert vague brand adjectives into a brand role and usage context
      - choose one visual metaphor or structural idea and remove competing motifs
      - translate visual taste into prompt-level constraints: flat vector, geometry, negative space, color limit, background, and typography
      - add explicit anti-trope constraints for common AI logo failures
      - separate the core prompt from variant prompts and review criteria
      - add an image self-audit that checks mark legibility before mockup polish
      - mark missing brand facts instead of inventing positioning
      - use small-size and monochrome tests as exit pressure
    discouraged_moves:
      - adding more adjectives such as premium, elegant, futuristic, iconic, or cinematic without changing the mark
      - asking for complex symbolic fusion when the brief cannot support it
      - using mockup language before the raw logo mark is stable
      - adding many variants that do not change the strategic idea
      - treating image-model polish as brand-quality evidence
      - writing a full brand strategy when the task only needs a logo prompt
    split_rules:
      - split known facts from assumptions when the brief is thin
      - split core logo prompt from image self-audit when generating visuals
      - split symbol direction from wordmark direction when text rendering is risky
      - split variants by concept, not by color
    merge_rules:
      - merge repeated mood adjectives into one brand role
      - merge competing symbols into one dominant visual idea
      - merge long negative-prompt lists into a few high-risk bad smells
    density_guidance:
      - ideal output starts with a one-sentence brand/taste diagnosis
      - include one primary logo prompt, two optional variant prompts, and a short image self-audit
      - keep prompt language concrete enough for image generation, but short enough to avoid prompt inflation
      - leave a review-bound warning when the brief lacks brand facts or when text rendering needs human cleanup
```

## Scope

This is a scoped TVG profile for logo image-generation prompts and logo prompt reviews.
It is meant to test whether TVG + Profile can reproduce one local part of a
taste-skill-style workflow: turning vague visual taste into concrete constraints,
bad-smell checks, and reviewable image prompts.

It is not a general design taste doctrine, not a professional logo-design method, not
legal trademark review, and not a claim that Mindthus can match a dedicated taste skill
across UI, motion, code, branding, and visual production.

## How To Use

Use this profile when the input is a bounded logo request or a weak logo prompt, such as:

- "make a modern AI logo for my app";
- "design a premium logo for a data product";
- "turn this brand idea into an image-generation prompt";
- "the generated logo looks generic, improve the prompt."

Expected output:

1. Name the dominant logo bad smell.
2. State known brand facts and assumptions.
3. Choose one visual idea and logo type.
4. Produce one primary image-generation prompt.
5. Add optional variants only when they test different strategic directions.
6. Add negative constraints and image self-audit checks.
7. Leave a claim ceiling when brand facts, legal clearance, or human design review are missing.

## Prompt Self-Audit Questions

1. Does the prompt define brand role before visual mood?
2. Is there one dominant visual idea, or did multiple symbols get stacked?
3. Is the output a logo mark, not a cinematic object, scene, or mockup?
4. Are flat vector-like structure, color limits, typography, and background controlled?
5. Did the prompt actively block generic AI logo tropes?
6. Can the mark plausibly work small and in one color?
7. Are variants meaningfully different in idea rather than only style?
8. Are missing brand facts and legal/design review limits visible?

## Image Self-Audit Questions

1. Can the mark be recognized without reading generated text?
2. Does it still work when imagined as a black one-color silhouette?
3. Is the wordmark readable, or should text be handled separately by a designer?
4. Does the image avoid default AI-logo tropes such as glow or random tech geometry?
5. Is the visual idea clear enough to explain in one sentence?
6. Did the image become a nice mockup while hiding a weak mark?
7. Is the result only locally usable, or is a human designer / legal review still required?

## Source Notes

- Built from existing TVG value-profile mechanics and profile-construction guidance.
- Built from the user's stated direction: benchmark TVG + Profile against a taste-skill-like effect as a black-box output comparison, without copying external taste-skill internals.
- Uses general logo review principles: simplicity, distinctiveness, scalability, reproducibility, brand fit, and usage-context awareness.
- Uses local Mindthus discussions of bad smells, preflight-style checks, profile / recipe layering, and value-gain scoring.
- Does not copy external taste-skill prompts, examples, style rules, or aesthetic doctrine.

