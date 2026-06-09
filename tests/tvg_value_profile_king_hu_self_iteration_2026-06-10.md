# TVG Self-Iteration: King Hu Wuxia Cinema Profile

## Run Boundary

- iteration_mode: profile_self_iteration
- target_profile: `skills/tvg/resources/value-profiles/king-hu-wuxia-cinema.md`
- value_profile_mode: supplied
- artifact_job: scoped profile for cinematic prompt and storyboard image generation

This run constructs a King Hu wuxia profile by the same clean-room discipline used for
the Shaw profile: independent sources first, then TVG audit, then a revised profile.
It does not infer style rules from any generated image, old pilot, or prompt sample.

## V1 Sketch

The first sketch emphasized:

- old-style wuxia atmosphere
- elegant swordplay
- bamboo forests, temples, inns, and historical costume
- stillness before action
- rejection of modern xianxia and generic AI trailer language

## V1 Audit

v1_audit_result: return-remediate

Why v1 was not enough:

- It risked becoming "tasteful vintage wuxia" rather than specifically King Hu.
- It named stillness, inns, and swordplay but did not turn them into operational axes.
- It lacked a strong value hierarchy: spatial intelligence before action density, delayed spectacle before action payoff.
- It under-specified Beijing opera rhythm and dance-like combat.
- It did not make the inn / confined-space faction choreography actionable enough for storyboard planning.
- It mentioned female warriors but did not protect female knight-errant agency from decorative fantasy treatment.
- It did not make spiritual or philosophical pressure distinct from vague mystic atmosphere.
- It did not sufficiently avoid generic AI wuxia trailer inflation.

## V2 Changes

what_changed:

- Added `spatial intelligence before action density` as a dominant axis.
- Added `delayed spectacle before action payoff` as a rhythm rule.
- Strengthened Beijing opera rhythm and dance-like combat as movement grammar.
- Added inn / confined-space faction choreography as a specific storyboard axis.
- Added widescreen compositions full of graceful character movement to prevent isolated hero-pose prompts.
- Added female knight-errant agency as a constraint, not decoration.
- Added moral/political pressure and spiritual or philosophical pressure as separate value axes.
- Added explicit vetoes for modern wire-fu inflation and generic AI wuxia trailer inflation.
- Added prompt and image audit questions that force space, rhythm, action ethics, and anti-inflation checks.

## V2 Audit

v2_audit_result: freeze-with-review-bound-warning

Why v2 can freeze with warning:

- It now gives a downstream prompt/storyboard generator usable axes, not just style adjectives.
- It makes King Hu alignment depend on spatial setup, delayed action, Beijing opera movement rhythm, moral pressure, and female knight-errant agency.
- It provides veto constraints against modern wire-fu inflation, modern xianxia gloss, and generic AI wuxia trailer inflation.
- It keeps the profile scoped and avoids claiming to define all King Hu films or all wuxia.

Review-bound warning:

- This profile is still a prompt/storyboard working profile, not a scholarly film-history taxonomy.
- It should be pressure-tested with actual storyboard prompts and generated images before claiming strong visual control.
- Human film-domain review would be needed to upgrade from useful scoped profile to high-confidence King Hu aesthetic profile.

## Source Attribution Audit

source_attribution_audit:

- profile_source: independent source notes from Harvard Film Archive, Criterion / David Bordwell, Bordwell's King Hu writing, and Senses of Cinema.
- independent_profile_judgment: translating source themes into prompt/storyboard axes and veto constraints.
- user_constraint: user asked for a King Hu wuxia film style profile and self-iteration.
- not_used_as_source: generated images, old pilot records, old expanded prompts, or any artifact being improved.

claim_supported:

- TVG can build a scoped King Hu wuxia prompt/storyboard profile from independent source notes.
- TVG self-iteration improved the profile from broad vintage-wuxia taste language into more operational axes and audit questions.
- The resulting profile is ready to use for a pilot storyboard/image run with honest review-bound warnings.

evidence_ceiling:

- This does not prove generated images will match King Hu style.
- This does not prove historical completeness.
- This does not validate the profile across multiple scripts, films, or human expert review.

## Image Pilot After User Pollution Challenge

User feedback:

- The first image pilot looked too much like Shaw Brothers / Clear Water Bay studio style rather than King Hu.
- This was treated as a real profile-control failure, not a minor prompt taste issue.

Root-cause diagnosis:

- The first image prompt still carried Shaw-style visual execution habits from the immediately preceding Shaw profile run: theatrical snow set, red-blue hard light, rock-flat spectacle, and practical qilin closeups.
- The source script itself contains snow mountain, rescue melodrama, and mythic creature material; these do not strongly encode King Hu motifs, so the image model easily regressed to generic vintage/Shaw wuxia.
- The King Hu profile was under-specified on anti-Shaw contamination: it said not to collapse into generic Shaw style, but did not explicitly block Clear Water Bay / Movietown backlot theatricality or saturated red-blue Shaw-style hard-light spectacle.

Profile remediation:

- Added explicit pollution boundary: do not use Shaw Brothers Clear Water Bay / Movietown backlot theatricality as a King Hu proxy.
- Added explicit color/look boundary: do not use saturated red-blue Shaw-style hard-light spectacle as the default color logic.
- Added `natural-architectural-space-depth`.
- Added prompts for natural or architectural space: ruined fort, inn, courtyard, temple, bamboo, desert edge, mountain path, or village threshold.
- Added still-image translation rule for glimpse editing: partial visibility, occlusion, offscreen implication, or panel sequencing.
- Added claim boundary: the original snow mountain / qilin script is a story constraint, not King Hu evidence.

Image2 Pass 1:

- image_path: `tests/artifacts/tvg_king_hu_storyboard_pass1.png`
- result: 10-panel sheet generated from the initial King Hu profile.
- audit: too close to Shaw Brothers snow-set visual grammar; insufficient anti-Shaw boundary; profile control failed user expectation.
- exit: return-remediate.

Image2 Pass 2:

- image_path: `tests/artifacts/tvg_king_hu_storyboard_pass2_reboot.png`
- prompt change: fresh generation, no previous image as reference, explicit anti-Shaw boundary, muted natural/architectural period-cinema look, ruined mountain temple threshold, bamboo/winter branches, negative space, footprints, partial visibility, offscreen implication, and moral/spiritual stillness.
- audit: improved; red-blue Shaw spectacle and Clear Water Bay snow-set feeling reduced; architecture, thresholds, bamboo/branches, path, footprints, and waiting-space now carry more of the storyboard grammar.
- remaining risk: final panel compresses licking and touch; King Hu alignment remains mostly spatial/rhythmic rather than strongly iconographic because the original snow/qilin story is not a native King Hu scenario.
- exit: freeze-with-review-bound-warning for the corrected profile and image pilot.
