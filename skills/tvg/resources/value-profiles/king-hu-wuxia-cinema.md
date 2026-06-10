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
      - knowledge-state is staged visually: what is seen, hidden, overheard, half-seen, or discovered matters more than facial emotion alone
      - combat grows from stillness into percussive bursts shaped by Chinese opera rhythm, editing, and performer movement
      - rhythm is created by held space, silence, empty intervals, withheld display, and sudden compression, not by filling every panel with visible action
      - swordplay reads as choreographed movement through readable space, not only impact, pose, or technique display
      - mise-en-scene, movement, decor, and frame composition express character relations and moral pressure
      - female knight-errant figures, when present, are tactical and moral agents rather than decorative fantasy icons
      - spiritual, political, or philosophical pressure appears through space, timing, silence, monastery/temple presence, landscape, or unresolved stillness
      - storyboard-sheet composition preserves relation shots as the dominant carrier of meaning; close shots are rare punctuation, not the emotional default
    bad_means:
      - Shaw Brothers Clear Water Bay / Movietown backlot theatricality used as a King Hu proxy
      - saturated red-blue Shaw-style hard-light spectacle used as the default color or set logic
      - modern wire-fu inflation, modern xianxia gloss, particle magic, weightless hovering, or trailer-poster hero posing
      - natural-location prettiness or disaster realism that gives landscape spectacle without staged spatial relations
      - weather, terrain, or hardship realism replaces wuxia spatial grammar when no built architecture is present
      - creature or prop design becomes a realism showcase instead of serving blocking, relation, and moral pressure
      - dense fight coverage that skips setup, witness knowledge, routes, occlusion, and delayed payoff
      - closeups replace knowledge-state staging, turning suspense into facial emotion or creature contact alone
      - a storyboard sheet becomes a chain of portraits or creature closeups instead of a sequence of relation shots
      - generic AI director-prompt inflation: camera moves, lens words, and mood adjectives without screen function
      - vintage film texture is treated as the style while rhythm, empty space, delay, and abruptness remain generic
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
      - seen-hidden-reveal-depth
      - opera-editing-rhythm-depth
      - silence-and-empty-space-rhythm-depth
      - choreographed-space-combat-depth
      - mise-en-scene-relation-depth
      - female-knight-errant-agency-depth
      - moral-political-spiritual-pressure-depth
      - anti-shaw-pollution-depth
      - anti-modern-wuxia-inflation-depth
      - prompt-granularity-without-copying-depth
      - panel-composition-ratio-depth
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
      - preserve empty or nearly empty panels when silence, absence, route, distance, or aftermath carries the beat
      - preserve witness or secondary viewpoint when the scene is understood through watching, overhearing, concealment, or delayed recognition
      - when no separate witness exists, use concealed or partially blocked viewpoints to make the viewer's knowledge change visible
      - translate editing into panel sequence, partial visibility, occlusion, offscreen implication, or abrupt transition cues
      - preserve source-attribution handles when profile judgment or independent storyboard judgment adds detail beyond the script
    review_handles:
      - every shot or panel has a function, picture, spatial relation, shot size, blocking, rhythm cue, sound or transition, and source attribution
      - the reader can point to entrances, exits, thresholds, heights, hiding places, witnesses, and lines of sight before the action payoff
      - wide and medium-wide relation shots establish the tactical field before closeups or inserts
      - a multi-panel storyboard sheet keeps wide and medium-wide relation shots dominant; close shots should be limited and must retain a spatial or ethical handle
      - closeups and inserts are used for eye-line, concealment, weapon/prop information, recognition, or ethical turn rather than generic emotion padding
      - contact closeups retain enough surrounding space to preserve route, threshold, or relation; they do not become isolated face/creature portraits
      - style choices are visible as space, timing, gesture, editing logic, restraint, or moral pressure, not only as the label "King Hu"
      - at sheet level, at least one panel may carry value through absence, route, stillness, or silence rather than character display
      - color and set choices do not default to Shaw-style saturated studio hard-light spectacle
  gain_policy:
    preferred_moves:
      - begin by mapping the scene's tactical space: routes, thresholds, height levels, hiding places, sightlines, witnesses, and blocked knowledge
      - thicken the script into setup, watching, withheld information, reveal, action burst, response, and handoff only where those beats change screen function
      - convert style terms into reviewable staging decisions: inn/courtyard/temple/bamboo/fort/road when story-appropriate, plus doors, windows, rafters, screens, rocks, paths, and offscreen entry points
      - when the scene has no built architecture, use terrain as architecture: slope, ridge, rock, tree, windbreak, snow line, shadow, path edge, and offscreen direction must still create thresholds, cover, routes, and sightlines
      - use a witness or secondary viewpoint when it helps create delayed recognition or political/moral pressure without inventing unsupported plot
      - if the story gives no witness character, stage the camera/viewer as a watcher through rock, screen, snow, shadow, doorway, bamboo, or offscreen sound so knowledge changes remain visible
      - replace spectacle adjectives with bodies moving through readable space: pause, glance, listen, hide, cross threshold, emerge, strike, vanish, or leave a silence behind
      - make rhythmic contrast visible: held empty route, partial glimpse, sudden action, then aftermath or silence
      - use long shot and medium-wide relation shots before closeups when the scene needs spatial intelligence
      - set a sheet-level shot-size ratio before generation: most panels are wide or medium-wide relation shots, at most one or two are contextual close relation shots
      - use partial visibility, occlusion, offscreen implication, sudden cuts, percussion, or silence to adapt editing rhythm into still-image or storyboard form
      - bind each invented visual choice to original script, supplied profile, or independent storyboard judgment
      - use human reference prompts only to calibrate output thickness, shot granularity, and reviewable structure; abstract the lesson, do not copy the content
    discouraged_moves:
      - importing Shaw Brothers studio-era color, backlot, creature, or tableau rules as if they define King Hu
      - forcing inns, bamboo, monks, female warriors, or Zen imagery into a scene when the script gives no usable opening
      - adding eighteen shots, push-ins, aerials, slow motion, or closeups by default
      - making every beat a beautiful action pose instead of a readable knowledge, space, rhythm, or moral-pressure change
      - using facial closeups or contact closeups as a substitute for what the viewer learns, fails to see, or suddenly understands
      - letting a creature head, face, or wound fill the panel unless the panel also preserves the relevant route, threshold, relation, or ethical turn
      - making every panel equally illustrative, leaving no held pause, silence, offscreen implication, or abrupt rhythmic contrast
      - allowing weather hardship, landscape beauty, or creature realism to replace spatial suspense and readable blocking
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
- knowledge-state is visible as seen/hidden/revealed relations; facial emotion alone is not enough
- Chinese opera rhythm and editing: movement can be fluid, staccato, percussive, or suddenly withheld; the value is rhythm through space, not weightless spectacle
- silence and empty space are allowed to carry value: a path, threshold, trace, or aftermath panel can be more King Hu-aligned than another expressive face
- combat as choreographed relation: bodies, props, beams, doors, windows, courtyards, paths, bamboo, rocks, screens, and offscreen entry points shape the fight
- mise-en-scene expresses character relation: frame composition, decor, movement, and timing show who watches, who knows, who is trapped, who controls the field
- moral and political pressure remains visible, especially around corrupt authority, loyalty, justice, protection, restraint, and sacrifice
- female knight-errant figures, when present, act as competent tactical and moral agents rather than decorative icons
- spiritual or philosophical pressure is expressed through landscape, temple/monastic presence, stillness, silence, irony, or unresolved aftermath
- glimpses, occlusion, partial visibility, and abrupt transitions can carry more value than showing every move plainly
- in storyboard outputs, wide and medium-wide relation panels carry the grammar; close relation shots are punctuation and should remain contextual

## Bad Means

- Shaw-style backlot spectacle substitutes stone flats, red-blue hard-light theatricality, and studio tableau for King Hu spatial suspense
- modern xianxia gloss turns wuxia into luminous celestial fantasy, romance poster surfaces, or weightless magic
- modern wire-fu inflation makes action float without tactical space, watcher knowledge, or rhythmic payoff
- natural-location realism or disaster spectacle gives impressive mountains, snow, wind, or ruins without staged spatial relations
- weather, terrain, or hardship realism becomes the main image logic instead of a controlled grammar of route, threshold, cover, sightline, pause, and release
- generic AI wuxia trailer inflation adds aerials, particles, slow motion, heroic closeups, lens words, and mood adjectives without shot function
- old-film texture or muted color is used as a surface filter while the panel sequence still lacks pause, withholding, suddenness, and aftermath
- every panel becomes a beautiful action pose while ignoring entrances, exits, eye-lines, concealment, witnesses, and moral pressure
- closeups turn the sequence into emotional illustration or creature contact while the viewer's knowledge state stops changing
- a storyboard sheet becomes mostly faces, wounds, creature heads, or emotional inserts, hiding the spatial grammar it should reveal
- creature, animal, prop, or costume design becomes the visual attraction while the surrounding space and relation logic become thin
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
- `seen-hidden-reveal-depth`
- `opera-editing-rhythm-depth`
- `silence-and-empty-space-rhythm-depth`
- `choreographed-space-combat-depth`
- `mise-en-scene-relation-depth`
- `female-knight-errant-agency-depth`
- `moral-political-spiritual-pressure-depth`
- `glimpse-occlusion-adaptation-depth`
- `anti-shaw-pollution-depth`
- `anti-modern-wuxia-inflation-depth`
- `prompt-granularity-without-copying-depth`
- `panel-composition-ratio-depth`

## Veto Constraints

- must not infer King Hu rules from Shaw Brothers profile content, Shaw Clear Water Bay / Movietown theatricality, generated images, or the story artifact being improved
- must not use saturated red-blue Shaw-style hard-light spectacle as the default color or set logic
- must not copy the concrete events, camera sequence, object choices, or phrasing of a human reference prompt into the reusable profile
- must not increase shot or panel count without assigning each unit a narrative, spatial, knowledge-state, ethical, or transition function
- must not force inns, bamboo, monks, female warriors, or Zen imagery into a scene when the script gives no usable opening
- must not let natural terrain or severe weather become mere location realism; even outdoor scenes need readable routes, thresholds, cover, sightlines, and offscreen direction
- must not let creature/prop realism substitute for screen relation, restraint, and moral pressure
- must not let closeups replace visible knowledge-state changes; contact shots still need a route, threshold, occlusion, or relation handle
- must not let more than a small minority of panels become close portraits or creature-detail panels in a storyboard sheet meant to test spatial grammar
- must not fill every panel with direct character display when silence, absence, route, trace, or aftermath would carry stronger rhythm
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
- when there is no building or courtyard, convert natural terrain into staging grammar: ridge as threshold, rocks as cover, slope as power relation, wind/snow/fog as occlusion, and path edge as route pressure
- when no witness character is justified, make the viewer's partial knowledge explicit through blocked view, glimpse, offscreen sound, eye-line, revealed trace, or delayed line-of-sight
- use long shot and medium-wide relation shots before closeups when the scene depends on spatial intelligence
- pre-commit to a shot-size mix for storyboard sheets: wide/medium-wide relation shots dominate; close relation shots are rare and justified by recognition, concealed information, or ethical turn
- include at least one held-space or aftermath beat when the scene depends on spiritual, moral, or fatal pressure
- bind invented visual choices to original script, supplied profile, or independent storyboard judgment
- use human prompt references only to calibrate thickness, shot granularity, and reviewable structure

Discouraged:

- copying Shaw profile rules or human prompt content
- adding eighteen shots by default
- adding push-ins, aerials, slow motion, particles, closeups, or lens adjectives without new screen function
- using direct prompt patching to hide a profile weakness without recording the profile failure mode
- spending prompt detail on creature/prop anatomy when the panel still lacks route, sightline, threshold, cover, or relation change
- using a closeup when a medium-wide relation shot could show the same emotion plus a new knowledge, space, or moral-pressure change
- centering creature anatomy, face detail, or wound detail when the same beat could be staged through distance, relation, route, gesture, or stillness
- using vintage film grain, muted color, or old costume as a substitute for editing rhythm and spatial suspense

## Prompt Self-Audit Questions

`prompt_self_audit_questions`:

1. Does the prompt establish tactical space before action: entrances, exits, thresholds, heights, hiding places, witnesses, and lines of sight?
2. Does it create delay through watching, listening, concealment, or partial knowledge, or does it rush into action coverage?
3. What does the viewer learn, fail to see, or suddenly understand in each added shot?
4. Does each added shot or panel have a screen job: spatial setup, knowledge shift, action burst, moral pressure, response, or handoff?
5. Does the storyboard sheet define a shot-size mix where wide and medium-wide relation panels dominate?
6. Does the sequence include held space, silence, absence, or aftermath rather than filling every panel with direct character display?
7. Does movement feel shaped by Chinese opera rhythm, editing, and readable space rather than generic wire-fu or xianxia gloss?
8. Are moral, political, or spiritual stakes visible enough to keep action from becoming decorative?
9. If a female knight-errant appears, is she an agent with restraint, competence, and tactical/moral force?
10. If the scene is outdoors or weather-heavy, does terrain still function as architecture rather than location spectacle?
11. Could the same prompt accidentally generate Shaw-style backlot spectacle, saturated red-blue studio hard light, modern xianxia, modern wire-fu, disaster realism, or generic AI wuxia trailer polish?
12. Are human prompt references used only for granularity and review structure, without copying their concrete beats?

## Image Self-Audit Questions

`image_self_audit_questions`:

1. Can the viewer read where people could enter, exit, hide, watch, overhear, or suddenly appear?
2. Does the image show waiting, watching, concealment, partial visibility, or delayed recognition, not only combat impact?
3. Do bodies move through widescreen or medium-wide space rather than posing as isolated hero icons?
4. Do architecture, path, bamboo, courtyard, temple, inn, fort, rocks, screens, windows, doors, beams, or landscape shape the action when story-appropriate?
5. Does the image avoid Shaw Brothers Clear Water Bay / Movietown backlot theatricality, saturated red-blue Shaw-style hard-light spectacle, modern wire-fu inflation, modern xianxia glow, anime surfaces, CG particles, and generic AI trailer polish?
6. Does glimpse editing translate into partial visibility, occlusion, offscreen implication, or panel sequencing rather than a single overloaded still?
7. If the setting is outdoor or weather-heavy, can the viewer still read route, threshold, cover, sightline, and offscreen direction?
8. Do closeups preserve a visible knowledge, route, threshold, or relation change rather than becoming isolated emotion?
9. Across the sheet, do wide and medium-wide relation panels dominate over portraits and inserts?
10. Is at least one panel valuable because of silence, empty space, trace, route, or aftermath rather than character display?
11. Does any creature, prop, costume, or weather effect dominate the panel without serving spatial relation or moral pressure?
12. What one change would most improve King Hu alignment without inventing unsupported plot facts?

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
