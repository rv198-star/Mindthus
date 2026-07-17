# Cinematic Visual Direction TVG Profile

This is the canonical four-layer advanced TVG-Profile example for cinematic image
generation and review. The external prompt skill is a behavior sample, not source truth;
its concrete wording is not copied into this Profile.

The Profile is intentionally scene-general. Colossal pressure, poetic landscape,
intimate drama, action, and other scene families may supply adapters or task-local
constraints, but no one scene family owns the core definition of cinematic value.

```yaml
value_profile:
  mode: supplied
  name: cinematic visual direction
  artifact_job: turn bounded visual briefs into reviewable cinematic prompt packets and image decisions
  value_semantics:
    good_means:
      - one chosen frame has a primary read, eye path, reveal reason, and scene relation
      - director subtraction protects one major image from competing actions and highlights
      - controlled fracture keeps weather, damage, texture, and occlusion coherent
      - shot economy preserves quiet space and demotes correct-but-expensive detail
      - camera, light, atmosphere, material behavior, and motion remain physically credible
      - scene adapters add local value semantics without redefining the cinematic core
    bad_means:
      - cinematic adjectives replace reviewable camera, light, and spatial relations
      - several equal-strength actions or highlights split the first read
      - generic spectacle, decorative clutter, or polished emptiness replaces scene intention
      - a scene adapter silently turns its local rules into universal cinematic rules
      - scripts or generated images are treated as proof of aesthetic success
    priority_order:
      - evidence honesty and user constraints
      - primary image and director shot spine
      - subtraction before additive strengthening
      - scene relation and physical coherence
      - controlled texture and negative space
      - adapter fit before adapter intensity
      - runtime support boundary
    derived_axes:
      - primary-read-depth
      - director-shot-spine-depth
      - director-subtraction-depth
      - scene-relation-depth
      - controlled-fracture-coherence-depth
      - shot-economy-depth
      - camera-lighting-credibility-depth
      - adapter-fit-depth
      - runtime-support-boundary-depth
    evidence_basis:
      - external skill behavior sample, abstracted only as reusable control habits
      - TVG profile construction discipline
    profile_veto_constraints:
      - must not copy the external skill's concrete wording
      - must not freeze when no primary image or reviewable scene relation is present
      - scripts must not decide aesthetic success, profile maturity, or TVG exit
  realization_surface:
    artifact_role: cinematic image prompt packet, generated-image review, and candidate lineage
  gain_policy:
    preferred_moves:
      - preserve-and-repair the strongest one-frame intention
      - strengthen one weak realization surface at a time
      - subtract competing detail before increasing spectacle or texture
      - use a bounded scene adapter only when the task actually needs it
  runtime_support:
    purpose: deterministic prompt scaffolding, lint, field lock, atlas labels, lineage, and trace validation only
```

## Realization Surface

Value becomes reviewable through:

- primary read: where the first look lands and what must remain dominant
- shot spine: eye path, reveal aperture, edge occlusion, and frame hierarchy
- scene relation: how subject, event, environment, and viewpoint occupy one space
- director subtraction: which highlight, action, object, or texture is demoted
- controlled fracture: whether weather, damage, haze, reflection, and motion remain continuous
- shot economy: one primary image, bounded supporting vectors, and protected quiet areas
- camera and light: viewpoint, lens behavior, depth, exposure, source, atmosphere, and material response
- adapter surface: task-specific relations that are active only when explicitly resolved
- generated-image audit: observable findings remain capped to the current run

## Gain Policy

Use this order unless task evidence points elsewhere:

1. Name the primary image and scene relation.
2. Build one director shot spine.
3. Run subtraction before adding effects, objects, or texture.
4. Repair physical camera, light, material, motion, and atmosphere relations.
5. Keep useful mess coherent instead of sterilizing it.
6. Activate a scene adapter only for local constraints the core does not own.
7. Stop when remaining differences are user taste rather than a named value defect.

## Scene Adapters

Adapters extend the core; they do not fork it. The first packaged adapter is
`resources/scene-adapters/colossal-pressure.json`. It owns scale ladders, witness
anchors, decisive partial threat, frame overflow, and large-force environment feedback.
Those rules must not be imposed on quiet landscapes, intimate scenes, or unrelated
cinematic work.

## Operating Pressure

TVG method pressure remains resource investment. A scene adapter may separately define
an operating intensity ladder. Record those as different fields; do not use one number
as evidence for the other.

## Runtime Support

Profile-local scripts may build prompt skeletons, report deterministic lint findings,
and preserve user field layouts. Generic atlas support lives under
`skills/tvg/scripts/atlas/` because board shape, labels, lineage, delivery audit records,
and finalization state are not owned by one cinematic scene family.

Runtime support must not select parents, invent gain hypotheses, assess beauty, waive
vetoes, decide exit, or certify Profile maturity. Every script result means only:

> Deterministic support findings were produced; agentic TVG audit is still required.

## Audit Questions

1. Is there one primary read and one chosen frame?
2. Can the viewer's eye path and reveal reason be described concretely?
3. Does every secondary action, highlight, and texture serve that frame?
4. What was deliberately removed, demoted, darkened, blurred, or left quiet?
5. Are camera, light, material, atmosphere, and motion physically compatible?
6. Is useful weather, fracture, or mess coherent rather than decorative clutter?
7. Is every adapter rule active because of this task rather than habit?
8. Is the evidence claim capped to this run?
