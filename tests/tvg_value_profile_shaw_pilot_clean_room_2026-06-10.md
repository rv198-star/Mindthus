# TVG Value Profile Clean-Room Pilot: Shaw Brothers Snow Mountain Storyboard

## Clean-Room Boundary

- active_value_profile: Shaw Brothers studio-era wuxia / fantasy cinematic prompt profile
- profile_source_rule: do not infer Shaw Brothers rules from the flawed expansion sample
- contamination_excluded: existing expanded storyboard prompts, existing pilot records, existing Image2 outputs, existing storyboard images, and `.tplan/missions/issue-31-*`
- shot_count_not_preset: true

This pilot uses only GitHub issue #31, current TVG method/code, independently retrieved
Shaw Brothers source notes, and the issue #31 original script paragraph. It does not use
or preserve any existing expanded prompt sample.

## Original Script Source

original_script_source: GitHub issue #31 raw script text

```text
画面:雪山之巅，风雪之中。
头发花白且凌乱的老道人身穿蓑衣，头戴斗笠，艰难的迎着风雪行走，双手放在胸前，怀里紧紧抱着一只虚弱的麒麟幼兽。身后的雪地上滴下长长的一道血痕，没走几步老道终于支撑不住倒在雪地里。怀里的麒麟幼兽摔在雪地上，看着倒在雪地的老道，坚强的起身用舌头舔舐老道的面颊，老道奄奄一息的伸出手触摸麒麟。
```

## Active Value Profile Summary

profile_source: `skills/tvg/resources/value-profiles/shaw-brothers-wuxia-fantasy.md`

The scoped profile asks the storyboard to favor studio-era / backlot / set-built
theatricality, wide-screen composition, saturated color and strong graphic contrast,
stylized wuxia/fantasy blocking, melodramatic emotional punctuation, practical mythic
creature presence, and clear shot function. It rejects modern xianxia, modern CG
spectacle, naturalistic disaster film grammar, and generic AI video prompt inflation.

This is a scoped prompt/storyboard/image-generation profile, not a universal definition
of all Shaw Brothers films.

## shot_count_decision

shot_count_decision: 8 panels

Why 8: the raw script has eight functional beats that need separate visual jobs:
establish the snow peak, show the old Daoist's endurance, reveal the blood trail, mark
collapse, separate the qilin cub, show the cub recognizing the fallen Daoist, show the
licking gesture, and end on the dying touch. Fewer than 8 would collapse cause/effect or
emotion. More than 8 would risk coverage inflation unless a new function appeared.

## 多镜头分镜提示词

### Shot 01

- function: establish ritual space and weather pressure
- picture: snow mountain summit in wind and snow; the old Daoist appears small against a constructed mythic landscape
- composition / framing / blocking: wide Shawscope-like tableau; set-built rock forms and theatrical gate/cloth elements frame the figure
- sound or transition: wind and low percussion; cut on cloth/snow motion into the walking beat

### Shot 02

- function: show endurance and protectiveness
- picture: white-haired old Daoist in straw cloak and bamboo hat fights the wind while holding the weak qilin cub against his chest
- composition / framing / blocking: medium-wide side tableau; cloak and body angle form a diagonal against stylized snow
- sound or transition: wind rises; hard cut to a lower ground-level view

### Shot 03

- function: reveal hidden injury without gore
- picture: footprints and a thin blood trace extend behind the moving Daoist in the snow
- composition / framing / blocking: low wide composition with the Daoist receding; blood is a graphic line through white snow
- sound or transition: wind thins for one beat; cut forward with the blood line as visual bridge

### Shot 04

- function: mark collapse
- picture: the old Daoist finally loses support and falls into snow with the qilin still close
- composition / framing / blocking: diagonal fall; hat, cloak, and body staged as a melodramatic tableau under hard side light
- sound or transition: dull fall into snow; brief music hit

### Shot 05

- function: separate guardian and creature
- picture: the weak qilin cub tumbles beside the fallen Daoist
- composition / framing / blocking: wider two-body arrangement; the cub and Daoist separated by snow and blood trace
- sound or transition: snow hush; cut to the cub's effort

### Shot 06

- function: show recognition and will
- picture: the cub looks at the fallen Daoist and struggles upright
- composition / framing / blocking: small practical creature silhouette framed by smoke, snow, and painted mountain backdrop
- sound or transition: soft creature breath; cut closer on loyalty

### Shot 07

- function: punctuate loyalty and grief
- picture: the qilin cub licks the old Daoist's cheek
- composition / framing / blocking: close tableau; faces held in profile/three-quarter relation with cloak, snow, and side light creating graphic contrast
- sound or transition: wind drops under a restrained strings cue; dissolve or soft cut to final touch

### Shot 08

- function: close the beat with dying connection
- picture: the old Daoist weakly reaches out and touches the qilin cub
- composition / framing / blocking: held close tableau; hand, creature face, and exhausted face make the emotional triangle
- sound or transition: faint wind; hold to fade or snow-filled cut

## Image2 Pass 1

single_page_storyboard_image: `tests/artifacts/tvg_shaw_storyboard_clean_room_pass1.png`

Prompt summary: generated one single-page storyboard sheet with exactly 8 panels in a
4 columns by 2 rows grid, based on the shot plan above, with studio-era Shaw Brothers
wuxia/fantasy style instructions.

Self-audit:

- pass: exact 8-panel sheet; no missing major story beat; old Daoist / qilin relation is readable
- concern: too much modern photoreal concept-art and naturalistic disaster film surface
- concern: studio-era / set-built theatricality and saturated graphic contrast are weaker than the profile asks
- concern: one panel appears to include legible rock/sign text, which distracts from clean storyboard function
- iteration_result: Pass 1 was usable as a layout proof but not strong enough as a Shaw profile alignment proof

## Image2 Pass 2

single_page_storyboard_image: `tests/artifacts/tvg_shaw_storyboard_clean_room_pass2.png`

Prompt summary:

```text
Generate one single-page storyboard sheet with exactly 8 panels in a 4 columns x 2 rows grid. Keep the same story beats. Correct Pass 1 by making the snow mountain visibly soundstage / backlot / set-built theatrical space, with painted scenic backdrops, controlled artificial snow, stylized rock flats, shallow studio depth, hard colored theatrical lighting, saturated Eastmancolor-like reds/teals/golds against snow, smoke/fog as graphic stage elements, Shawscope-like wide tableau compositions, and a practical puppet/creature-suit qilin cub. No legible Chinese text. Avoid modern xianxia glow, modern CG spectacle, naturalistic disaster-film realism, documentary mountain photography, and generic AI video prompt inflation.
```

Image Self-Audit:

- pass: still a single-page storyboard sheet with exactly 8 panels
- pass: panel functions match the independent shot plan
- pass: stronger red/blue color separation, theatrical gate/set elements, smoke, cloth, and staged tableau than Pass 1
- pass: the blood trace remains restrained and graphic rather than gore-centered
- partial: the qilin cub reads more practical-creature than pure CG, but still has some modern high-detail fantasy texture
- partial: the image still has modern photoreal sharpness; it is not a reliable historical Shaw Brothers look
- clear: it does not primarily fall into modern xianxia, modern CG spectacle, naturalistic disaster film, or generic AI video prompt inflation
- iteration_result: Pass 2 improved profile alignment enough to serve as the pilot artifact, with residual review-bound risk

## Source Separation

From original script:

- snow mountain summit and storm
- old Daoist with white messy hair, straw cloak, bamboo hat
- weak qilin cub held at chest
- long blood trace in snow
- collapse
- cub falls, rises, licks face
- dying touch

From profile:

- set-built theatricality
- wide-screen composition
- saturated color and strong graphic contrast
- stylized environment over naturalistic disaster realism
- melodramatic emotional punctuation
- practical mythic creature preference
- rejection of modern xianxia, modern CG spectacle, naturalistic disaster film, and generic AI video prompt inflation

independent_storyboard_judgment:

- 8-shot rhythm and panel count
- shot functions and order
- where to use wide tableau, low blood-trace view, close tableau, and held final touch
- sound/transition suggestions
- choosing one 4x2 sheet because the shot count is 8, not because a preset grid was inherited

possible_pollution_or_uncertainty:

- The repository contains old pilot records and generated image artifacts that were declared pollution sources and not read for content.
- During test failure output, an existing Shaw profile file was exposed; it was treated as polluted and replaced. The new profile's evidence basis is independent source notes, not that file.
- Generated image self-audit is only a profile-alignment check. It does not prove historical accuracy.

## source_attribution_audit

- original_script_source: GitHub issue #31 raw script paragraph
- profile_source: independent Shaw Brothers source notes plus issue #31's profile-field requirements
- independent_storyboard_judgment: this run's shot-count and shot-plan decisions
- image_source: Image2 built-in generation, Pass 1 and Pass 2, copied into `tests/artifacts/`
- possible_pollution_or_uncertainty: old pilot/profile/image artifacts exist in the repo and were excluded; the existing profile content was not used as evidence

claim_supported:

- TVG + a supplied value_profile can change the axes and audit questions used by a storyboard/prompt run.
- The Shaw profile helped produce an independent shot-count decision, a multi-shot prompt, a single-page storyboard sheet, and a self-audit that names specific failure modes.
- The pilot supports a limited claim that TVG + profile can provide an independent storyboard view for this script under clean-room constraints.

evidence_ceiling:

- This is one clean-room pilot, not broad validation.
- The generated image is not proof of Shaw Brothers historical accuracy.
- A stronger claim would require more scripts, independent review, comparison against generic TVG without profile, and possibly human film-domain review.
