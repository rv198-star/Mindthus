# Plain Sharp Skill Intro Profile

```yaml
value_profile:
  mode: supplied
  name: plain sharp skill intro profile
  artifact_job: turn method or skill descriptions into plain, sharp, example-backed introduction copy
  value_semantics:
    good_means:
      - a first-time reader can repeat what the skill is for after one pass
      - the core sentence names the skill's real job, not its internal machinery
      - the first sentence has a memorable aphoristic quality: rhythmic, contrastive, and worth quoting while staying accurate
      - the wording is short, vivid, and specific enough to name the skill's real job
      - high density comes from short sentences carrying key judgments, not from compressing many claims into long sentences
      - a familiar example explains the judgment surface through one concrete action rather than a long setup
      - every sentence has a visible job in the argument, such as essence, reason, example, contrast, boundary, or use condition
      - information density feels like the top 20 percent of usable intro copy: each sentence carries a choice-relevant point, not filler
      - boundaries are visible enough that the reader knows when not to use the skill
      - the copy makes the skill feel usable rather than ceremonial
    bad_means:
      - acronym-first explanation that forces the reader to learn internal vocabulary before understanding the value
      - abstract praise such as rigorous, systematic, advanced, powerful, or comprehensive without a concrete job
      - long method summaries that repeat the documentation instead of sharpening the entry point
      - long sentences that hide multiple functions inside one line in the name of high density
      - examples that expand background instead of showing one ordinary action or choice
      - examples that are clever but do not clarify when to use the skill
      - deleting sentences merely because they are not core, instead of first trying to give them a useful argumentative job
      - overselling the skill as a conclusion machine, truth machine, or universal fixer
      - making every introduction sound like generic better thinking
      - making every sentence equally explanatory so the opening line loses force
    priority_order:
      - one-sentence essence before method detail
      - first-sentence aphorism before full explanation, as long as accuracy is preserved
      - short sentence carrying one key judgment before long compressed sentence
      - sentence-function assignment before deletion or compression
      - top-20-percent information density before stylistic polish
      - plain user-facing language before internal terms
      - one-action everyday example before abstract taxonomy
      - honest boundary before promotional force
      - brevity with enough context to act
    derived_axes:
      - essence-sharpness
      - first-sentence-aphorism
      - plain-language-transfer
      - short-sentence-density
      - sentence-function-discipline
      - top-20-percent-information-density
      - one-action-example-clarity
      - boundary-honesty
      - memorability-without-sloganizing
      - actionability
    evidence_basis:
      - explicit user-provided quality definition for the intro copy
      - existing Mindthus skill and methodology documents
      - TVG default practical-value profile
    profile_veto_constraints:
      - must not describe a skill as deciding truth, strategy, or domain facts beyond its documented boundary
      - must not hide required evidence, user judgment, runtime proof, or stakeholder authority
      - must not use unexplained internal labels as the main explanation
      - must not make the skill sound like a generic thinking improvement
      - must not treat higher pressure as permission to make sentences longer
  realization_surface:
    artifact_role: public-facing skill introduction copy for README, docs navigation, marketplace descriptions, or agent onboarding
    downstream_use: a reader or agent can quickly decide whether this skill is relevant before opening the full method page
    observable_units:
      - quotable first sentence
      - essence sentence
      - sentence function
      - when-to-use cue
      - familiar example
      - boundary sentence
    granularity_pressure:
      - first sentence should hit like a classic line: rhythmic, contrastive, memorable, and accurate
      - second sentence explains the first sentence in plain short language
      - third sentence chooses either example or boundary according to need; do not force both into every intro
      - explicit boundary appears only when misuse risk is high
      - keep each skill intro to one sharp essence plus one example-backed explanation unless the surface explicitly needs more
      - keep single sentences short by default; split a long sentence when it carries more than one argumentative function
      - assign every sentence one primary function before deciding whether to rewrite, merge, or delete it
      - keep examples to one concrete action, choice, or mistake; do not expand background
      - under high pressure, remove weak connectors and explanatory setup instead of packing more information into longer sentences
      - split method detail from example only when the example would otherwise obscure the essence
    review_handles:
      - the first sentence can stand alone
      - the first sentence is quotable without becoming vague or inaccurate
      - the second sentence explains rather than decorates
      - the third sentence uses either scenario/example or boundary, not both by default
      - every sentence can be tagged as essence, reason, example, contrast, boundary, or use condition
      - most sentences are short enough to be read in one breath
      - the example uses ordinary language and one concrete stake or action
      - the boundary prevents overuse
      - the intro does not depend on acronym expansion to make sense
  gain_policy:
    preferred_moves:
      - compress method machinery into the user-facing job
      - replace abstract method praise with a concrete failure the skill prevents
      - make the first sentence more rhythmic or contrastive before adding explanation
      - use one familiar scenario to reveal the hidden judgment surface
      - add a short boundary only when the skill is easy to overuse
      - convert weak sentences into reason, example, contrast, boundary, or use-condition sentences before considering deletion
      - split overloaded sentences before trying to make them more elegant
      - sharpen verbs before adding nouns
      - prefer contrast pairs such as looks right vs carries through, signal vs problem, workflow vs judgment
    discouraged_moves:
      - explaining every field, phase, or internal label
      - stacking adjectives to sound impressive
      - using slogans without an example
      - making the opening line accurate but forgettable
      - turning examples into mini case studies
      - adding caveats that bury the core sentence
      - making high-pressure output by lengthening sentences
      - deleting non-core sentences before checking whether they can serve the core argument
      - making every skill introduction follow exactly the same rhythm
    split_rules:
      - split into essence, example, and boundary when one paragraph becomes dense
      - split first-sentence aphorism from second-sentence explanation when accuracy needs support
      - split any sentence that carries two or more primary functions
    merge_rules:
      - merge repeated boundary caveats that all say the skill is not a truth machine
      - merge method detail back into the essence when it does not change user choice
    density_guidance:
      - ideal intro is 2 to 4 short sentences
      - default intro shape is quotable first sentence, plain explanation, then either one scenario or one boundary
      - every sentence must either clarify essence, trigger use, explain by example, or prevent misuse
      - treat top 20 percent information density as a practical bar: remove or rewrite any sentence that a reader could skip without losing understanding, distinction, or action guidance
      - high pressure means harsher selection and cleaner sentence function, not longer sentences
      - brevity is achieved by functionalizing sentences first and deleting only when no useful function remains
```

## Scope

This is a scoped profile for rewriting Mindthus method / skill introductions. It is not
a general marketing-copy profile and not a personal writing-style profile.

The profile's job is to make a skill introduction easier to understand and harder to
misuse. It should help a reader quickly answer:

- What is this skill really for?
- What kind of mistake does it prevent?
- What ordinary example makes the skill's judgment surface obvious?
- When should I not use it?

## Construction Note

This profile is built from the user's stated quality target:

> 通俗易懂，言简犀利，能一针见血地道破本质，同时可以通过通俗的例子进一步解释细节；信息密度要接近同类介绍词的前 20%；高密度不是长句压缩，而是短句承载关键判断。

The profile uses existing Mindthus skill and methodology documents as source material
for what each skill actually does. It must not invent new skill capabilities.

## Prompt Self-Audit Questions

1. Can a first-time reader repeat the skill's job without knowing the acronym?
2. Does the first sentence name the hidden failure mode the skill prevents?
3. Does high density come from short, sharp choices rather than long compressed sentences?
4. Does each sentence carry only one primary argumentative function?
5. Does the example show one concrete action or choice instead of expanding background?
6. Does the intro preserve the skill's boundary and avoid claiming domain truth?
7. Can every sentence be tagged with a useful function? If not, was it rewritten into a function before deletion was considered?
8. Would removing any sentence leave the reader with the same understanding and action guidance? If yes, rewrite or remove it.

## Source Notes

- User-supplied quality definition in the current task.
- Current `skills/*/SKILL.md` files and public methodology pages.
- TVG default practical-value profile.
