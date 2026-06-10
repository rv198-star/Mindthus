# Shaw Brothers Studio-Era Wuxia / Fantasy Cinematic Prompt Profile

```yaml
value_profile:
  mode: supplied
  name: Shaw Brothers studio-era wuxia / fantasy cinematic prompt profile
  artifact_job: scoped profile for cinematic prompt and storyboard image generation
  value_semantics:
    good_means:
      - studio-era / backlot / set-built theatricality is legible as an expressive choice
      - studio artifice remains visible enough that the set reads as controlled production design, not hidden location realism
      - color is theatrical and graphic, using hard gel-lit separation rather than contemporary blue-gray realism
      - widescreen composition arranges body, prop, creature silhouette, weather, and set space into readable graphic relationships
      - medium-wide and wide tableau staging carries more value than macro surface detail when the artifact is a storyboard sheet
      - stylized wuxia / fantasy blocking carries mythic and emotional pressure
      - mythic creatures read as practical props, puppets, masks, costumes, or suit performance with visible material limits
    bad_means:
      - modern xianxia gloss replaces studio-era theatricality
      - modern CG spectacle overwhelms human / creature relation
      - generic AI video prompt inflation adds camera and mood without shot function
      - digital concept-art or animation surfaces replace live-action studio-film staging
      - high-budget fantasy realism hides painted backdrops, stage floors, theatrical lighting, and practical effect limits
      - mythic creatures become anatomically convincing modern monsters with high-detail horns, scales, wet eyes, and CG surface realism
      - contemporary cool-blue grading flattens the image into modern prestige fantasy or disaster realism
      - close-up density turns the storyboard into a creature/face showcase instead of a scene-blocking plan
    priority_order:
      - evidence honesty and contamination boundaries
      - studio-era theatrical space before naturalistic realism
      - wuxia / fantasy blocking and emotional tableau before generic cinematic prettiness
      - shot function and rhythm before larger shot count
    derived_axes:
      - studio-set-theatricality-depth
      - live-action-studio-film-surface-depth
      - visible-studio-artifice-depth
      - practical-creature-material-depth
      - theatrical-color-separation-depth
      - tableau-over-closeup-depth
      - widescreen-tableau-depth
      - wuxia-fantasy-blocking-depth
      - melodramatic-punctuation-depth
      - shot-function-rhythm-depth
    evidence_basis:
      - independent Shaw Brothers source notes listed below
    profile_veto_constraints:
      - must not infer profile rules from any existing expanded prompt, pilot record, Image2 result, or storyboard image
      - must not increase shot or panel count without assigning each unit a clear narrative, spatial, emotional, or transition function
      - must not let digital concept-art, anime, painterly fantasy illustration, or modern previsualization become the visual default
  realization_surface:
    artifact_role: director-style cinematic storyboard prompt for image generation and review
    observable_units:
      - shot
      - storyboard panel
      - screen relation
      - action phase
      - emotional turn
      - transition beat
      - source-attribution note
    downstream_use: a downstream image model, storyboard reviewer, or director-style prompt reviewer can inspect each panel-level unit
    granularity_pressure:
      - split when a physical action changes screen relation
      - split when emotional recognition and physical response would otherwise collapse into one vague beat
      - preserve transition beats when sound, movement, or visual dissolve carries narrative function
      - preserve source-attribution handles when profile judgment or independent storyboard judgment adds detail beyond the script
    review_handles:
      - every shot has a function, picture, shot size, camera movement or stillness, blocking, sound or transition, and source attribution
      - shot count explanation names why units were split or merged
      - profile-specific style choices are visible as set, composition, color, blocking, sound, or transition choices
      - live-action studio-film surface is visible as actor staging, imperfect practical effects, 35mm/optical texture, and theatrical lighting rather than painterly concept rendering
      - studio artifice is inspectable through painted backdrops, stage-floor snow, theatrical flats, visible smoke, and hard color-gel lighting
      - color separation is inspectable through red, teal, amber, green, or gold gel pools, hard shadows, and non-naturalistic stage contrast
      - panel mix is inspectable: wide and medium-wide relation shots should dominate, with closeups used only for necessary inserts or emotional turns
      - creature construction is inspectable through simplified silhouette, fabric/fur/latex material, mask or puppet limits, and modest articulation
  gain_policy:
    preferred_moves:
      - turn implied script action into visible shot-to-shot cause and effect
      - expose screen relations among bodies, creatures, props, weather effects, traces, entrances, exits, falls, gestures, and transitions
      - bind each invented visual choice to original script, supplied profile, or independent storyboard judgment
      - use sound, music, and transition only when they carry emotional punctuation or scene handoff
      - translate style words into reviewable set, light, color, blocking, costume, prop, creature, sound, or transition decisions
      - translate visual polish downward into period film-frame texture, simple painted backdrops, visible studio lighting, and practical effect limits when the output drifts toward modern illustration
      - make practical limitations visible when the output drifts toward seamless high-budget realism
      - reduce creature design complexity when the output drifts toward modern dragon, monster, or CG mascot design
      - replace modern blue-gray grading with hard theatrical color blocks when the image becomes contemporary, naturalistic, or prestige-fantasy
      - widen shots when the output becomes a chain of face, hand, or creature macro details without set/blocking information
    discouraged_moves:
      - adding push-ins, aerial views, slow motion, particles, or lens adjectives without new shot function
      - repeating closeups that only restate an already visible emotion
      - using Shaw Brothers as a label without concrete set, composition, color, blocking, gesture, sound, or transition choices
      - allowing high-detail fantasy concept art, anime/comic styling, or glossy CG creature design to carry the scene
      - hiding the studio set behind convincing natural mountain depth, seamless VFX, or contemporary production realism
      - giving mythic creatures contemporary creature-design realism instead of theatrical prop, puppet, mask, or suit logic
      - letting cool naturalistic snow lighting dominate when the target needs colored theatrical separation
      - using closeup density to hide weak set, staging, or screen relation logic
    split_rules:
      - split establishment, approach, reveal, relation shift, impact, response, contact, aftermath, and scene handoff when each has a distinct screen job
      - split a continuous action when it changes screen relation, emotional state, power relation, evidence visibility, or transition function
      - split physical contact into approach, recognition, contact, and aftermath only when each changes relation or emotion
    merge_rules:
      - merge redundant reaction closeups when they do not add information, spatial relation, or emotional turn
      - merge style-only coverage when it cannot be reviewed as a new narrative, spatial, emotional, or transition function
    density_guidance:
      - coverage-rich output is allowed only when every added unit remains reviewable and source-attributed
      - thickness should resemble director-style storyboard prompting, not generic AI video-prompt inflation
```

## Scope

This is not a universal definition of all Shaw Brothers films. It is a scoped profile
for cinematic prompt and storyboard image generation when the target is the studio-era
wuxia / fantasy lane associated with Shaw Brothers' controlled Hong Kong studio
production, especially the Clear Water Bay / Movietown production environment, widescreen
composition, constructed sets, theatrical blocking, saturated color, and melodramatic
punctuation.

The profile source must be independent from the artifact being improved. The original
script paragraph may define story content, but it is not a style source. Any existing
expanded prompt, pilot record, Image2 result, storyboard image, or generic AI expansion
is a contamination source for this profile. Do not infer Shaw Brothers rules from the
flawed expansion sample.

Audit guardrail: do not infer Shaw Brothers rules from the flawed expansion sample.

Layer note: this profile uses the optional `realization_surface` and `gain_policy`
layers because its downstream job is not only to judge style, but to produce thick
director-style storyboard prompts. These layers are not universal TVG requirements.
Director-style prompt references may calibrate thickness, shot granularity, and
storyboard technique only; they must not be treated as evidence for Shaw Brothers
value semantics unless they independently contain Shaw-specific source grounding.

## Good Means

- studio-era / backlot / set-built theatricality is legible as an expressive choice, not as failed realism
- widescreen / wide-screen composition arranges body, prop, animal/creature silhouette, weather, and set space into clear graphic relationships
- saturated color and strong graphic contrast organize hard light, shadow, smoke, weather effects, cloth, traces, props, and costume as readable screen elements
- stylized rather than naturalistic environments carry the mythic and emotional pressure of the beat
- martial / wuxia / fantasy blocking uses entrances, falls, kneeling, stillness, touch, weapon/prop placement, and posed bodies as story grammar
- melodramatic emotional punctuation is visible through posture, tableau, music cue, and transition, not only explanatory text
- practical-theatrical creature logic is preferred over modern CG spectacle when presenting mythic beings
- every shot or storyboard panel has a function: establish space, stress pressure, reveal hidden information, shift relation, mark impact, answer with response, or close / hand off the beat

## Bad Means

- modern xianxia gloss replaces studio-era theatricality with ethereal CG beauty and weightless streaming-drama polish
- modern CG spectacle overwhelms the human/creature relation or treats mythic beings as VFX showcases
- contemporary creature-design realism turns mythic beings into anatomically convincing monsters instead of practical theatrical presences
- modern animation, digital concept art, comic-panel rendering, or glossy previsualization replaces live-action studio-film staging
- naturalistic disaster film grammar turns the sequence into location survival realism instead of stylized studio fantasy
- cool-blue contemporary grading turns the scene into modern prestige fantasy rather than studio-era color design
- close-up density turns the prompt or image into creature/face showcase rather than storyboard blocking
- generic AI video prompt inflation adds aerial views, endless push-ins, glowing particles, hyperreal detail, or mood adjectives without changing shot function
- merely naming "Shaw Brothers" substitutes for concrete set, composition, color, blocking, gesture, sound, or transition choices
- shot count grows without rhythm, spatial continuity, or emotional punctuation
- explicit gore becomes the main aesthetic vehicle instead of graphic staging, costume, cloth, light, posture, and trace design

## Priority Order

1. User constraints, evidence honesty, claim ceilings, safety boundaries, and named veto constraints.
2. Independent profile source integrity before any style inference from the artifact being improved.
3. Studio-era theatrical space before naturalistic location realism.
4. Wuxia / fantasy blocking and emotional tableau before generic cinematic prettiness.
5. Widescreen graphic composition before photorealistic surface detail.
6. Shot function and rhythm before larger shot count.
7. Practical-mythic creature presence before modern CG spectacle.
8. Useful storyboard executability before ornamental style labels.

## Derived Axes

- `independent-profile-source-depth`
- `studio-set-theatricality-depth`
- `live-action-studio-film-surface-depth`
- `visible-studio-artifice-depth`
- `practical-creature-material-depth`
- `theatrical-color-separation-depth`
- `tableau-over-closeup-depth`
- `widescreen-tableau-depth`
- `graphic-weather-costume-prop-depth`
- `wuxia-fantasy-blocking-depth`
- `melodramatic-punctuation-depth`
- `practical-mythic-creature-depth`
- `anti-modern-xianxia-depth`
- `anti-modern-cg-spectacle-depth`
- `anti-naturalistic-disaster-depth`
- `anti-generic-ai-inflation-depth`
- `shot-function-rhythm-depth`

## Veto Constraints

- must not infer profile rules from any existing expanded prompt, pilot record, Image2 result, or storyboard image
- must not use a Shaw Brothers label when the prompt/image logic remains modern xianxia, modern CG spectacle, naturalistic disaster film, or generic AI video prompt inflation
- must not accept painterly concept art, animation, comic rendering, or modern digital previsualization as a successful Shaw-style film image
- must not accept seamless natural-location realism or high-budget fantasy realism when the scoped target calls for visible studio artifice
- must not accept anatomically convincing modern creature design as a substitute for practical puppet, mask, prop, or suit-performance logic
- must not let blue-gray naturalistic grading erase theatrical color separation when color is part of the scoped profile
- must not let close-up density replace set, blocking, and screen-relation legibility in a storyboard sheet
- must not increase shot or panel count without assigning each unit a clear narrative, spatial, emotional, or transition function
- must not claim this profile defines all Shaw Brothers directors, genres, eras, or films
- must not present generated image self-audit as proof of historical accuracy
- must not let aesthetic preference override original script content, evidence honesty, claim ceilings, user constraints, safety boundaries, or named veto constraints

## Prompt Self-Audit Questions

`prompt_self_audit_questions`:

1. Does the prompt translate the profile into constructed set space, widescreen composition, color, blocking, gesture, sound, and transition choices?
2. Does each shot/panel have a function that advances the script beat rather than merely adding coverage?
3. Does the sequence preserve spatial continuity among characters, creatures, props, weather effects, traces, impacts, gestures, and final relation changes?
4. Could the same prompt accidentally produce modern xianxia, modern CG spectacle, naturalistic disaster realism, or generic AI video prompt inflation?
5. Could the same prompt accidentally produce animation, painterly fantasy concept art, comic panels, or glossy previsualization instead of live-action studio-film frames?
6. Are emotional beats carried through tableau, posture, stillness, touch, framing, sound, and transition rather than explanation alone?
7. Are source boundaries and contamination exclusions visible enough that another auditor can tell where the profile came from?

## Image Self-Audit Questions

`image_self_audit_questions`:

1. Does the image read as a single-page storyboard sheet with multiple panels, not separate stills or a poster?
2. Do the panels show set-built theatricality or controlled studio space rather than a purely naturalistic mountain location?
3. Is the composition graphic and readable across bodies, costume, props, traces, creature silhouette, weather effects, and light?
4. Is the central character / creature or character / object relation visible through blocking and gesture?
5. Does the image avoid modern xianxia glow, modern CG spectacle, naturalistic disaster-film realism, and generic AI video prompt inflation?
6. Does the image look like live-action studio-film frames or production stills rather than animation, painterly concept art, comic rendering, or glossy digital previsualization?
7. Does the image allow the viewer to notice controlled studio artifice rather than hiding the scene inside seamless natural-location realism?
8. Does the image use theatrical color separation rather than defaulting to modern cool-blue realism?
9. Do wide and medium-wide tableau panels carry the scene, with closeups reserved for necessary inserts or emotional turns?
10. If alignment is weak, what one prompt change would most improve profile fit without inventing new script facts?

## Source Notes

`source_notes`:

- independent source notes: Hong Kong Memory and Shaw official studio material establish Shaw's studio-system production base and Clear Water Bay / Movietown context.
- independent source notes: David Bordwell's Shaw essay supports treating full color, Shawscope/widescreen presentation, and Movietown studio production as relevant framing sources.
- independent source notes: Harvard Film Archive's Shaw Scope program frames Shaw martial-arts cinema through the studio model and bodies in motion; its King Hu note is useful for thinking about composition, rhythm, and architectural/blocking control in wuxia cinema.
- independent source notes: Hong Kong Film Archive material on Chor Yuen's The Magic Blade supports using a Shaw/Chor Yuen wuxia-fantasy lane as a prompt target while keeping director and era specificity review-bound.
- scope note: the profile is built for prompt/storyboard/image generation, not film-historical taxonomy.
- contamination note: the original script supplies plot facts only; existing expanded storyboard prompts, pilot records, generated images, and old Image2 results are excluded.

Independent references used for this profile:

- Hong Kong Memory, Shaw Brothers movies collection and studio history: https://www.hkmemory.hk/en/collections/shaw_brothers_movies/
- Shaw Studios official history: https://www.shawstudios.hk/
- David Bordwell, "Another Shaw Production": https://www.davidbordwell.net/essays/shaw.php
- Harvard Film Archive, Shaw Scope program: https://harvardfilmarchive.org/programs/shaw-scope
- Harvard Film Archive, A Touch of Zen program note: https://harvardfilmarchive.org/calendar/a-touch-of-zen-2022-10
- Hong Kong Film Archive, The Magic Blade: https://www.filmarchive.gov.hk/en_US/web/hkfa/pe-event-2022-9-1-3.html
