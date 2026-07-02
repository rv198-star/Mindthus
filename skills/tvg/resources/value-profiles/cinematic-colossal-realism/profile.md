# Cinematic Colossal Realism TVG Profile

This profile treats the external cinematic prompt skill as a behavior sample, not source truth.
It must not copy the external skill's concrete wording into reusable Mindthus resources.

The purpose is to demonstrate a TVG advanced profile package. The profile defines what
"good" means, where that value becomes observable, which value-gain moves are useful,
and which deterministic runtime support can help without replacing TVG judgment.

```yaml
value_profile:
  mode: supplied
  name: cinematic colossal realism
  artifact_job: scoped profile for cinematic image-prompt generation and image review
  value_semantics:
    good_means:
      - terse mythic or colossal subjects become concrete, reviewable image prompt packets
      - human-scale viewpoint anchors make the viewer feel present and small
      - three-layer scale relation connects human scale, environment scale, and colossus scale
      - first-read cinematic pressure comes from one decisive subject fragment threatening the witness field
      - director shot spine makes focus, eye path, reveal logic, and edge occlusion serve one chosen frame
      - controlled fracture coherence makes messy material becomes readable pressure instead of random damage
      - shot economy mode uses subtractive selection before additive strengthening at high pressure
      - physical environment feedback makes the subject feel materially present
      - partial occlusion and frame overflow preserve credible enormity and mystery
      - camera, light, atmosphere, texture, and negative constraints are visible and reviewable
    bad_means:
      - cinematic adjectives replace camera, scale, light, and physical relations
      - full-body centered poster staging replaces witnessed presence
      - evenly distributed checklist detail weakens the primary threat image
      - secondary details compete with the chosen shot instead of supporting it
      - rain, haze, debris, broken reflections, or partial occlusion become random clutter
      - high-pressure prompts fill every region instead of protecting one primary image
      - media-pollution terms appear in positive or negative prompts
      - scripts or generated images are treated as proof of aesthetic success
    priority_order:
      - evidence honesty and user constraints
      - TVG control boundary before prompt convenience
      - human-scale and environment-scale anchoring before spectacle
      - first-read cinematic pressure before secondary detail density
      - director shot spine before adding more scene coverage
      - controlled fracture coherence before texture density
      - shot economy mode before high-pressure expansion
      - physical feedback and credible light before surface detail
      - partial visibility before complete monster display
      - negative-constraint hygiene before prompt inflation
    derived_axes:
      - human-scale-anchor-depth
      - three-layer-scale-depth
      - decisive-pressure-frame-depth
      - director-shot-spine-depth
      - controlled-fracture-coherence-depth
      - shot-economy-mode-depth
      - physical-feedback-depth
      - partial-visibility-depth
      - camera-lighting-credibility-depth
      - negative-constraint-hygiene-depth
      - runtime-support-boundary-depth
    evidence_basis:
      - external skill behavior sample, abstracted only as runtime habits
      - TVG profile construction discipline
    profile_veto_constraints:
      - must not copy the external skill's concrete wording
      - must not freeze when the prompt lacks human-scale anchoring
      - must not freeze when the prompt lacks physical environment feedback
      - scripts must not decide aesthetic success, profile maturity, or TVG exit
  realization_surface:
    artifact_role: cinematic image prompt packet and generated-image review record
  gain_policy:
    preferred_moves:
      - classify terse subject into candidate visual category before expansion
  runtime_support:
    purpose: deterministic support only
```

## Scope

This is a scoped profile for cinematic image prompts involving mythic, divine,
monstrous, disaster-scale, deep-sea, sky, or cosmic colossus subjects. It is not a
general film theory profile and not a complete prompt-generation skill.

The external reference may calibrate behavior families such as terse-input expansion,
field preservation, scale anchoring, physical feedback, and negative-constraint hygiene.
It must not supply reusable wording, facts, or final aesthetic authority.

## Realization Surface

Value becomes observable through:

- subject identity: the prompt names what kind of presence is being rendered
- viewer position: a human-scale or instrument-scale witness is located in the scene
- scale ladder: human scale, environment scale, and colossus scale are all visible
- decisive pressure frame: one near-overhead head, hand, claw, eye, rib arc, shadow, or body fragment dominates the upper-third first read without deleting the witness field or drifting to the far edge
- director shot spine: primary focus, viewer-eye path, reveal aperture, edge occlusion, and secondary details serve the shot; reveal light must keep the primary focus readable
- controlled fracture coherence: rain, haze, debris, partial occlusion, broken reflections, and damaged surfaces stay physically continuous and compositionally useful
- shot economy mode: one primary image, a small number of supporting vectors, limited texture budget, and explicit demotion of correct-but-expensive details
- partial visibility: the subject exceeds the frame or is occluded by atmosphere, terrain, structures, or water
- physical feedback: clouds, rain, dust, water, lights, debris, fabric, cables, trees, crowds, or instruments react
- camera and light: lens, framing, viewpoint, exposure, light source, atmosphere, and texture are reviewable
- negative constraints: visual failure modes are named without media-pollution terms
- generated-image audit: output can be checked for scale, feedback, visibility, light, and medium drift

## Gain Policy

Useful TVG moves usually happen in this order:

1. Classify the terse subject into a candidate visual family.
2. Build a three-layer scale ladder before adding surface detail.
3. Use a decisive pressure frame when the artifact needs high first-read cinematic pressure, especially at pressure 4-5.
4. Add a director shot spine so the prompt chooses one focal decision, one eye path, and one reveal reason.
5. Use controlled fracture coherence so dirt, weather, damage, and occlusion support focus, scale, motion, or atmosphere.
6. At pressure 4-5, run shot economy mode: select one primary image, limit supporting vectors, cap texture budget, and demote attention-expensive elements before adding more.
7. Add environment feedback before adding more adjectives.
8. Use partial visibility to preserve weight, mystery, and frame pressure.
9. Translate "cinematic" into camera, light, atmosphere, exposure, and material behavior.
10. Clean negative constraints so forbidden media labels do not pollute generation.
11. Run deterministic lint only as a support check, then let TVG decide remediation or exit.

Discouraged moves:

- adding longer lists of cinematic adjectives without new reviewable surfaces
- using full centered subject display as the default for colossal subjects
- treating a script finding as a semantic verdict
- treating one generated image as proof that the profile is generally strong

## Runtime Support

Runtime support may:

- classify a terse subject into candidate categories
- build a prompt skeleton from deterministic defaults
- expose decisive-pressure-frame cues for agentic filling
- expose director-shot-spine cues for agentic filling
- expose controlled-fracture-coherence cues for agentic filling
- expose shot-economy-mode cues for agentic filling
- report missing human scale, missing physical feedback, media-term contamination, or field drift
- preserve user-supplied field templates
- record image-comparison evidence with a claim ceiling

Runtime support must not:

- decide TVG exit state
- output `PASS`
- score aesthetic quality
- decide profile maturity
- waive veto constraints
- prove historical, cinematic, or model-generation truth

Every runtime-support result means only:

> Deterministic support findings were produced; agentic TVG audit is still required.

## Prompt Self-Audit Questions

1. Does the prompt establish a human-scale witness or instrument-scale witness?
2. Does it show a three-layer relation among witness, environment, and colossus?
3. Does it contain one decisive subject fragment that creates first-read cinematic pressure?
4. Does the prompt name the primary focus, viewer-eye path, reveal logic, and edge occlusion?
5. Do messy, broken, or occluding materials point to focus, scale, motion, or atmosphere?
6. Does high-pressure expansion name what is removed, demoted, darkened, or left quiet?
7. Does the subject change the surrounding physical world?
8. Is the subject partially occluded, frame-overflowing, or otherwise too large to be fully mastered by the image?
9. Are camera, light, atmosphere, exposure, and material behavior concrete enough to review?
10. Are negative constraints phrased as visual failure modes rather than forbidden media labels?
11. Could a downstream reviewer identify what came from profile defaults, what came from user input, and what came from TVG judgment?

## Image Self-Audit Questions

1. Does the image show a witness-scale anchor rather than only a large subject?
2. Does the environment make the subject's scale legible?
3. Does the first read land on a dominant but partial threat fragment?
4. Does the shot read as one chosen frame rather than evenly distributed coverage?
5. Does dirt, haze, debris, reflection, or occlusion read as controlled texture rather than random clutter?
6. Do quiet, dark, or low-detail zones protect the primary image instead of being treated as missing detail?
7. Is there visible physical feedback from the subject?
8. Does the image avoid centered poster display when the profile calls for witnessed scale?
9. Does light behave as if it comes from a credible source and passes through atmosphere, water, dust, smoke, rain, or haze?
10. Does the image avoid media drift toward animation, game, concept-art, or plastic surfaces?
11. Is the evidence claim capped to this run?

## Source Notes

- External reference role: behavior sample for runtime habits.
- Contamination boundary: do not copy prompt wording, examples, or concrete phrasing.
- TVG boundary: profile and scripts contribute value semantics, review surfaces, and support findings; TVG still owns exit judgment.
- Image-generation boundary: Images2 outputs can support loop-assisted observations, not general profile-strength proof.
