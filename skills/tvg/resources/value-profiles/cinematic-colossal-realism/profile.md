# Cinematic Colossal Realism Compatibility Alias

`cinematic-colossal-realism` was the v1.4.6 package name. It bundled reusable cinematic
direction controls together with one colossal-pressure scene family, which made the
advanced Profile appear narrower than its actual purpose.

New work should resolve:

```yaml
value_profile:
  mode: supplied
  name: cinematic visual direction
  path: ../cinematic-visual-direction/profile.md
  adapters:
    - ../cinematic-visual-direction/resources/scene-adapters/colossal-pressure.json
  compatibility_alias: cinematic-colossal-realism
```

The canonical four-layer Profile is
[`cinematic-visual-direction`](../cinematic-visual-direction/profile.md). Its core owns
director shot spine, subtraction, scene relation, controlled fracture, shot economy,
camera-light-material credibility, and runtime-support boundaries.

The colossal-specific scale ladder, witness anchor, decisive partial threat, frame
overflow, environment feedback, and pressure 2-5 guidance now belong to the
[`colossal-pressure`](../cinematic-visual-direction/resources/scene-adapters/colossal-pressure.json)
adapter. They are not universal cinematic rules.

## Compatibility Boundary

The resources, scripts, and historical examples under this path remain available so
v1.4.6 references and prior evidence can still be replayed. They are compatibility and
scene-adapter support, not a second canonical Profile.

The external skill remains a behavior sample, not source truth. Compatibility scripts
must not decide aesthetic success, Profile maturity, or TVG exit, and must not copy the
external skill's concrete wording.

Generic atlas runtime support moved to `skills/tvg/scripts/atlas/` and
`skills/tvg/resources/atlas-search-contract.json`. The old package must not own board
layout, cross-Profile lineage, delivery readiness, or final taste authority.
