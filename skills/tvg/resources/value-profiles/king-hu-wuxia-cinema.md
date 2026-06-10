# King Hu Wuxia Cinema Prompt / Storyboard Profile

```yaml
value_profile:
  mode: supplied
  name: King Hu wuxia cinema prompt / storyboard profile
  artifact_job: scoped profile for cinematic prompt and storyboard image generation
  value_semantics:
    good_means:
      - spatial intelligence is the first carrier of style: routes, hiding places, heights, thresholds, witnesses, and eye-lines are established before combat
      - delayed action creates suspense through watching, listening, false calm, partial knowledge, and sudden release
      - combat grows from stillness into percussive bursts shaped by Chinese opera rhythm, editing, and performer movement
      - swordplay reads as choreographed movement through readable space, not only impact, pose, or technique display
      - mise-en-scene, movement, decor, and frame composition express character relations and moral pressure
      - female knight-errant figures, when present, are tactical and moral agents rather than decorative fantasy icons
      - spiritual, political, or philosophical pressure appears through space, timing, silence, monastery/temple presence, landscape, or unresolved stillness
    bad_means:
      - Shaw Brothers Clear Water Bay / Movietown backlot theatricality used as a King Hu proxy
      - saturated red-blue Shaw-style hard-light spectacle used as the default color or set logic
      - modern wire-fu inflation, modern xianxia gloss, particle magic, weightless hovering, or trailer-poster hero posing
      - natural-location prettiness or disaster realism that gives landscape spectacle without staged spatial relations
      - dense fight coverage that skips setup, witness knowledge, routes, occlusion, and delayed payoff
      - generic AI director-prompt inflation: camera moves, lens words, and mood adjectives without screen function
      - copying a human reference prompt's concrete beats into the reusable profile instead of abstracting granularity and reviewability
    priority_order:
      - user constraints, evidence honesty, claim ceilings, safety boundaries, and named veto constraints
      - independent King Hu source integrity before inference from the artifact, generated images, Shaw profiles, or human prompt examples
      - spatial legibility before action density
      - delay, watching, and withheld knowledge before spectacle payoff
      - opera/editing rhythm and readable movement before generic martial-arts motion
      - moral, political, or spiritual pressure before decorative heroism
      - reviewable shot/panel function before larger shot count
    derived_axes:
      - independent-profile-source-depth
      - spatial-intelligence-depth
      - delayed-action-depth
      - watcher-and-knowledge-state-depth
      - opera-editing-rhythm-depth
      - choreographed-space-combat-depth
      - mise-en-scene-relation-depth
      - female-knight-errant-agency-depth
      - moral-political-spiritual-pressure-depth
      - anti-shaw-pollution-depth
      - anti-modern-wuxia-inflation-depth
      - prompt-granularity-without-copying-depth
    evidence_basis:
      - independent King Hu source notes listed below
    profile_veto_constraints:
      - must not infer King Hu rules from Shaw Brothers profile content, Shaw Clear Water Bay / Movietown theatricality, generated images, or the story artifact being improved
      - must not copy the concrete events, camera sequence, or object choices of a human reference prompt into the reusable profile
      - must not increase shot or panel count without assigning each unit a narrative, spatial, knowledge-state, ethical, or transition function
      - must not present loop-assisted prompt/image success as proof that the profile itself is strong
  realization_surface:
    artifact_role: director-style cinematic shot plan and storyboard prompt for image generation and review
    observable_units:
      - shot
      - storyboard panel
      - spatial setup
      - line-of-sight relation
      - occlusion or glimpse beat
      - watcher knowledge-state shift
      - action burst
      - moral or political pressure beat
      - sound or edit transition
      - source-attribution note
    downstream_use: a downstream image model, storyboard reviewer, or director-style prompt reviewer can inspect each panel-level unit for spatial readability, rhythm, and source attribution
    granularity_pressure:
      - split when the viewer's knowledge changes, not merely when a new angle sounds cinematic
      - split setup, watching, withheld information, action burst, aftermath, and scene handoff when each has a different screen job
      - preserve witness or secondary viewpoint when the scene is understood through watching, overhearing, concealment, or delayed recognition
      - translate editing into panel sequence, partial visibility, occlusion, offscreen implication, or abrupt transition cues
      - preserve source-attribution handles when profile judgment or independent storyboard judgment adds detail beyond the script
    review_handles:
      - every shot or panel has a function, picture, spatial relation, shot size, blocking, rhythm cue, sound or transition, and source attribution
      - the reader can point to entrances, exits, thresholds, heights, hiding places, witnesses, and lines of sight before the action payoff
      - wide and medium-wide relation shots establish the tactical field before closeups or inserts
      - closeups and inserts are used for eye-line, concealment, weapon/prop information, recognition, or ethical turn rather than generic emotion padding
      - style choices are visible as space, timing, gesture, editing logic, restraint, or moral pressure, not only as the label "King Hu"
      - color and set choices do not default to Shaw-style saturated studio hard-light spectacle
  gain_policy:
    preferred_moves:
      - begin by mapping the scene's tactical space: routes, thresholds, height levels, hiding places, sightlines, witnesses, and blocked knowledge
      - thicken the script into setup, watching, withheld information, reveal, action burst, response, and handoff only where those beats change screen function
      - convert style terms into reviewable staging decisions: inn/courtyard/temple/bamboo/fort/road when story-appropriate, plus doors, windows, rafters, screens, rocks, paths, and offscreen entry points
      - use a witness or secondary viewpoint when it helps create delayed recognition or political/moral pressure without inventing unsupported plot
      - replace spectacle adjectives with bodies moving through readable space: pause, glance, listen, hide, cross threshold, emerge, strike, vanish, or leave a silence behind
      - use long shot and medium-wide relation shots before closeups when the scene needs spatial intelligence
      - use partial visibility, occlusion, offscreen implication, sudden cuts, percussion, or silence to adapt editing rhythm into still-image or storyboard form
      - bind each invented visual choice to original script, supplied profile, or independent storyboard judgment
      - use human reference prompts only to calibrate output thickness, shot granularity, and reviewable structure; abstract the lesson, do not copy the content
    discouraged_moves:
      - importing Shaw Brothers studio-era color, backlot, creature, or tableau rules as if they define King Hu
      - forcing inns, bamboo, monks, female warriors, or Zen imagery into a scene when the script gives no usable opening
      - adding eighteen shots, push-ins, aerials, slow motion, or closeups by default
      - making every beat a beautiful action pose instead of a readable knowledge, space, rhythm, or moral-pressure change
      - fixing image drift by direct prompt patching while leaving the profile failure unrecorded
      - using modern xianxia glow, CG particles, superhero flight, painterly fantasy illustration, anime surfaces, or generic wuxia trailer polish
    split_rules:
      - split a beat when it changes viewer knowledge, tactical relation, moral pressure, action phase, or scene handoff
      - split action when the screen relation changes from watcher to target, hidden to revealed, above to below, outside to inside, stillness to burst, or burst to aftermath
      - split closeup/insert only when it reveals concealed information, eye-line, weapon/prop relation, recognition, or ethical turn
    merge_rules:
      - merge redundant reaction closeups that restate the same emotion without new knowledge or moral pressure
      - merge style-only panels that cannot be reviewed as a new spatial, rhythmic, narrative, or transition function
      - merge extra action poses when they hide weak setup or make the scene read like generic martial-arts coverage
    density_guidance:
      - coverage-rich output is allowed, but thickness must come from reviewable screen jobs rather than fixed shot count
      - a strong single-pass profile should already steer the first prompt toward spatial setup, delay, and panel function
      - loop-assisted production may improve a prompt or image, but the final claim must separate profile control from runtime rescue
```

## Scope

This is not a universal definition of all King Hu films or of the whole wuxia genre. It
is a scoped profile for cinematic prompt and storyboard image generation when the target
is a King Hu wuxia grammar: spatial suspense, delayed action, Chinese opera rhythm,
editing-shaped bursts, moral and political pressure, female knight-errant agency when
the story calls for it, and spiritual or philosophical pressure carried by space and
timing.

King Hu worked in and beyond Shaw contexts. This profile is not a studio taxonomy and
must not collapse into Shaw Brothers Clear Water Bay / Movietown theatricality, modern
wire-fu, glossy xianxia, or generic AI wuxia trailer language.

Pollution boundary: do not use any existing expanded prompt, prior pilot record, Image2
result, storyboard image, Shaw profile, or the snow mountain / qilin script as King Hu
evidence. The script being improved is story content only. A human prompt reference may
calibrate thickness and shot granularity, but its concrete beats must not be copied into
this reusable profile.

Layer note: this profile uses the optional `realization_surface` and `gain_policy`
layers because the downstream job is not only to judge style. It must help TVG produce
director-style shot plans and storyboard prompts with enough panel-level thickness to be
reviewed, while still preserving the claim boundary between profile strength and
loop-assisted runtime rescue.

## Good Means

- spatial intelligence before action density: the viewer understands routes, thresholds, heights, hiding places, witnesses, and eye-lines before the action erupts
- delayed action: suspense, watching, listening, false calm, concealment, and partial knowledge make the burst meaningful
- Chinese opera rhythm and editing: movement can be fluid, staccato, percussive, or suddenly withheld; the value is rhythm through space, not weightless spectacle
- combat as choreographed relation: bodies, props, beams, doors, windows, courtyards, paths, bamboo, rocks, screens, and offscreen entry points shape the fight
- mise-en-scene expresses character relation: frame composition, decor, movement, and timing show who watches, who knows, who is trapped, who controls the field
- moral and political pressure remains visible, especially around corrupt authority, loyalty, justice, protection, restraint, and sacrifice
- female knight-errant figures, when present, act as competent tactical and moral agents rather than decorative icons
- spiritual or philosophical pressure is expressed through landscape, temple/monastic presence, stillness, silence, irony, or unresolved aftermath
- glimpses, occlusion, partial visibility, and abrupt transitions can carry more value than showing every move plainly

## Bad Means

- Shaw-style backlot spectacle substitutes stone flats, red-blue hard-light theatricality, and studio tableau for King Hu spatial suspense
- modern xianxia gloss turns wuxia into luminous celestial fantasy, romance poster surfaces, or weightless magic
- modern wire-fu inflation makes action float without tactical space, watcher knowledge, or rhythmic payoff
- natural-location realism or disaster spectacle gives impressive mountains, snow, wind, or ruins without staged spatial relations
- generic AI wuxia trailer inflation adds aerials, particles, slow motion, heroic closeups, lens words, and mood adjectives without shot function
- every panel becomes a beautiful action pose while ignoring entrances, exits, eye-lines, concealment, witnesses, and moral pressure
- "King Hu" becomes a label for any vintage martial image instead of a specific grammar of setup, delay, editing, movement, and ethical pressure
- female warriors are treated as costume spectacle rather than active moral and tactical agents
- spiritual imagery becomes vague mystic glow instead of silence, relation, irony, or philosophical pressure

## Priority Order

1. User constraints, evidence honesty, claim ceilings, safety boundaries, and named veto constraints.
2. Independent source integrity before inference from the artifact, generated images, Shaw profiles, or human prompt examples.
3. Spatial legibility before action density.
4. Delayed action, watcher knowledge, and withheld information before spectacle payoff.
5. Opera/editing rhythm and choreographed movement before generic martial-arts motion.
6. Moral, political, or spiritual pressure before decorative heroism.
7. Reviewable shot/panel function before larger shot count.

## Derived Axes

- `independent-profile-source-depth`
- `spatial-intelligence-depth`
- `delayed-action-depth`
- `watcher-and-knowledge-state-depth`
- `opera-editing-rhythm-depth`
- `choreographed-space-combat-depth`
- `mise-en-scene-relation-depth`
- `female-knight-errant-agency-depth`
- `moral-political-spiritual-pressure-depth`
- `glimpse-occlusion-adaptation-depth`
- `anti-shaw-pollution-depth`
- `anti-modern-wuxia-inflation-depth`
- `prompt-granularity-without-copying-depth`

## Veto Constraints

- must not infer King Hu rules from Shaw Brothers profile content, Shaw Clear Water Bay / Movietown theatricality, generated images, or the story artifact being improved
- must not use saturated red-blue Shaw-style hard-light spectacle as the default color or set logic
- must not copy the concrete events, camera sequence, object choices, or phrasing of a human reference prompt into the reusable profile
- must not increase shot or panel count without assigning each unit a narrative, spatial, knowledge-state, ethical, or transition function
- must not force inns, bamboo, monks, female warriors, or Zen imagery into a scene when the script gives no usable opening
- must not let modern xianxia, modern wire-fu, CG particles, anime surfaces, superhero flight, or generic AI wuxia trailer polish become the visual default
- must not present generated image self-audit as proof of historical accuracy
- must not present loop-assisted prompt/image success as proof that the profile itself is strong

## Realization Surface

`realization_surface`:

- artifact role: director-style cinematic shot plan and storyboard prompt for image generation and review
- observable units: shot, storyboard panel, spatial setup, line-of-sight relation, occlusion/glimpse beat, watcher knowledge-state shift, action burst, moral or political pressure beat, sound/edit transition, source-attribution note
- downstream use: a downstream image model, storyboard reviewer, or director-style prompt reviewer can inspect each panel-level unit for spatial readability, rhythm, and source attribution
- granularity pressure: split only when viewer knowledge, tactical relation, moral pressure, action phase, or scene handoff changes
- review handles: every shot/panel should expose function, picture, spatial relation, shot size, blocking, rhythm cue, sound/transition, and source attribution

## Gain Policy

`gain_policy` is a route preference for value-gain actions, not a reward model and not a
fixed recipe. It tells TVG where useful thickness usually comes from for this profile.

Preferred:

- map the tactical space before expanding shots
- add setup, watching, concealment, reveal, action burst, response, and handoff only when they create new screen function
- translate style labels into concrete staging: thresholds, heights, lines of sight, partial visibility, offscreen entry, silence, percussion, and relation shots
- use long shot and medium-wide relation shots before closeups when the scene depends on spatial intelligence
- bind invented visual choices to original script, supplied profile, or independent storyboard judgment
- use human prompt references only to calibrate thickness, shot granularity, and reviewable structure

Discouraged:

- copying Shaw profile rules or human prompt content
- adding eighteen shots by default
- adding push-ins, aerials, slow motion, particles, closeups, or lens adjectives without new screen function
- using direct prompt patching to hide a profile weakness without recording the profile failure mode

## Prompt Self-Audit Questions

`prompt_self_audit_questions`:

1. Does the prompt establish tactical space before action: entrances, exits, thresholds, heights, hiding places, witnesses, and lines of sight?
2. Does it create delay through watching, listening, concealment, or partial knowledge, or does it rush into action coverage?
3. Does each added shot or panel have a screen job: spatial setup, knowledge shift, action burst, moral pressure, response, or handoff?
4. Does movement feel shaped by Chinese opera rhythm, editing, and readable space rather than generic wire-fu or xianxia gloss?
5. Are moral, political, or spiritual stakes visible enough to keep action from becoming decorative?
6. If a female knight-errant appears, is she an agent with restraint, competence, and tactical/moral force?
7. Could the same prompt accidentally generate Shaw-style backlot spectacle, saturated red-blue studio hard light, modern xianxia, modern wire-fu, or generic AI wuxia trailer polish?
8. Are human prompt references used only for granularity and review structure, without copying their concrete beats?

## Image Self-Audit Questions

`image_self_audit_questions`:

1. Can the viewer read where people could enter, exit, hide, watch, overhear, or suddenly appear?
2. Does the image show waiting, watching, concealment, partial visibility, or delayed recognition, not only combat impact?
3. Do bodies move through widescreen or medium-wide space rather than posing as isolated hero icons?
4. Do architecture, path, bamboo, courtyard, temple, inn, fort, rocks, screens, windows, doors, beams, or landscape shape the action when story-appropriate?
5. Does the image avoid Shaw Brothers Clear Water Bay / Movietown backlot theatricality, saturated red-blue Shaw-style hard-light spectacle, modern wire-fu inflation, modern xianxia glow, anime surfaces, CG particles, and generic AI trailer polish?
6. Does glimpse editing translate into partial visibility, occlusion, offscreen implication, or panel sequencing rather than a single overloaded still?
7. What one change would most improve King Hu alignment without inventing unsupported plot facts?

## Source Notes

`source_notes`:

- independent source notes: Harvard Film Archive frames King Hu as a major wuxia auteur whose mise-en-scene, movement, decor, art direction, and spatial composition express character relations. It also emphasizes his preference for protagonist skill over magical power, his reliance on performer skill and editing, philosophy presented through spatial and temporal relations, and the female swordfighter as a moral center.
- independent source notes: David Bordwell's Criterion essay on `A Touch of Zen` is used for story delay, protagonist/witness suspense, Beijing opera-derived combat rhythm, dance comparison, intricate staging, female warrior agency, and the value of cutting, glimpses, and withheld action.
- independent source notes: Bordwell's later King Hu writing is used for slow buildup followed by percussive bursts, staccato dance, opera rhythm, moral rectitude, and long-shot spatial play.
- independent source notes: Senses of Cinema is used for Hu's tavern/inn grammar, political and historical pressure, Chinese opera influence, female knight-errant model, and mythical or spiritual movement.
- independent source notes: Reverse Shot is used as secondary support for deliberate delay, stasis before combat, watcher positions, and Hu's editing-driven action grammar.
- scope note: this profile is built for prompt/storyboard/image generation, not a complete film-historical account.
- adaptation note: editing must be translated into panel sequence, partial visibility, occlusion, offscreen implication, abrupt transitions, sound cues, or rhythm notes because a still image cannot literally edit.
- human-reference note: a thick human prompt may calibrate output thickness and shot granularity. It is not King Hu evidence and must not be copied into the reusable profile.
- contamination note: Shaw Brothers profile content, generated images, Image2 records, prior pilot records, and the original snow mountain / qilin script are not King Hu evidence.

Independent references used for this profile:

- Harvard Film Archive, King Hu and the Art of Wuxia: https://harvardfilmarchive.org/programs/king-hu-and-the-art-of-wuxia
- Criterion, David Bordwell, "A Touch of Zen: Prowling, Scheming, Flying": https://www.criterion.com/current/posts/4141-a-touch-of-zen-prowling-scheming-flying
- David Bordwell, Observations on Film Art, Directors: King Hu: https://www.davidbordwell.net/blog/category/directors-king-hu/
- Senses of Cinema, Hu, King: https://www.sensesofcinema.com/2002/great-directors/hu/
- Reverse Shot, "Come Drink With Me": https://reverseshot.org/reviews/entry/2157/come_drink
