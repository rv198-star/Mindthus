# TVG Cinematic Profile Package Design

## Issue

GitHub issue: https://github.com/rv198-star/Mindthus/issues/79

## Goal

Create a TVG advanced value-profile example that migrates an external cinematic image-prompt skill as a behavior sample, without copying the original skill into Mindthus or turning the profile into a standalone prompt skill.

The example should show that a TVG profile can be more than a prose prompt. It can carry four layers:

1. `value_semantics`: what good, bad, priorities, axes, evidence basis, and veto constraints mean.
2. `realization_surface`: where profile value is observable and reviewable in a prompt or image.
3. `gain_policy`: which TVG value-gain moves tend to improve the artifact.
4. `runtime_support`: deterministic resources and scripts that support the profile without deciding final quality.

## Framing

The external skill is a behavior sample. It is useful because it shows many small runtime habits: terse user input is expanded without interrogation, mythical subjects are classified, scale anchors are added, colossus bodies remain partially occluded, physical environment feedback is required, camera and lighting logic become concrete, user field templates are respected, and negative constraints avoid media-term contamination.

Those behaviors should be abstracted into reusable profile controls. The concrete wording, example prompts, and specific phrasing of the external skill must not become Mindthus source truth.

## Non-Goals

- Do not create a new user-facing prompt skill that bypasses TVG.
- Do not copy long passages from the external skill into repository resources.
- Do not claim Images2 output proves the profile is generally strong.
- Do not implement video-prompt mode in the first version.
- Do not alter existing TVG core method semantics beyond adding a bounded example.

## Architecture

Add one profile package under `skills/tvg/resources/value-profiles/cinematic-colossal-realism/`.

The package contains:

- `profile.md`: the human-readable TVG value profile, including `value_semantics`, `realization_surface`, `gain_policy`, and `runtime_support` boundaries.
- `resources/subject-taxonomy.yaml`: deterministic subject categories and default routing hints.
- `resources/scene-defaults.yaml`: default scene packages by subject category.
- `resources/camera-lighting.yaml`: reusable camera, framing, light, color, and texture defaults.
- `resources/negative-constraints.yaml`: forbidden media-pollution terms and safe visual-problem replacements.
- `resources/field-templates.yaml`: fixed field-template behavior for user-supplied structures.
- `resources/image-audit-rubric.yaml`: review handles for prompt and generated-image comparison.
- `scripts/classify_subject.py`: returns candidate subject categories and scene hints.
- `scripts/build_prompt_skeleton.py`: assembles a prompt skeleton from deterministic resource hints.
- `scripts/lint_prompt_packet.py`: reports missing or risky deterministic surfaces in a prompt packet.
- `scripts/validate_field_lock.py`: checks whether an output preserved a user-supplied field list.
- `examples/migration-notes.md`: maps original behavior families into the four TVG profile layers.
- `examples/single-pass-profile-power.md`: records a fixed-profile single-pass control test.
- `examples/loop-assisted-image-comparison.md`: records baseline, basic profile, and advanced profile package comparison discipline.

Runtime scripts are intentionally support-only. They may emit findings such as "missing human scale anchor" or "forbidden media term found." They must not output `PASS`, select TVG exit state, score aesthetic success, or decide whether the profile is strong.

## Data Flow

1. A TVG run resolves the active `cinematic-colossal-realism` profile.
2. Runtime support may classify the terse subject into candidate categories.
3. Runtime support may assemble a prompt skeleton from deterministic defaults.
4. TVG/agentic reasoning fills and improves the prompt according to expected value, profile semantics, evidence boundary, and gain policy.
5. Runtime support lints the candidate prompt packet and reports deterministic defects.
6. TVG/agentic reasoning decides whether defects require remediation, warning, block, or freeze.
7. Images2 comparison artifacts may be recorded as loop-assisted production evidence, not profile-proof evidence.

## Control Boundary

Workflow support controls order, deterministic checks, and resource lookup.

Agentic TVG controls semantic judgment: whether a scene choice fits the subject, whether pressure feels grounded, whether another round has positive value, and whether the artifact can freeze.

Evidence records constrain claims: a generated image may support "this prompt produced one usable image in this run"; it does not support "the profile is generally strong."

## Acceptance Criteria

- The profile package exists and is discoverable under TVG value profiles.
- The profile explicitly contains the four-layer construction: `value_semantics`, `realization_surface`, `gain_policy`, and `runtime_support`.
- The package documents the contamination boundary: original skill as behavior sample, not source truth.
- Runtime scripts perform deterministic support checks and include boundary wording that script output is not semantic approval.
- Tests cover profile existence, boundary wording, resource shape, script behavior, and packaging inclusion.
- Example records document single-pass profile-power and loop-assisted Images2 comparison discipline with claim ceilings.

## Testing

Add focused unittest coverage in `tests/test_tvg_contract.py` and packaging coverage in `tests/test_packaging_docs.py`.

Expected test groups:

- Profile resource exists and names the four layers.
- Profile rejects copying external skill text as source truth.
- Runtime support section says scripts cannot decide aesthetic success, profile maturity, or TVG exit.
- Resource YAML files contain required top-level keys.
- `classify_subject.py` returns category hints for known inputs and unknown fallback.
- `lint_prompt_packet.py` detects missing human scale, missing physical feedback, forbidden media terms, and field-lock defects.
- Packaging docs/build tests include nested profile package resources and scripts.
- Example comparison record separates single-pass profile control from runtime rescue.

## Implementation Notes

Keep script dependencies to the Python standard library plus PyYAML only if the repository already uses it. If PyYAML is unavailable, use JSON-compatible YAML subsets and a tiny local parser only for the constrained resources, or store runtime resources as JSON. Prefer simple standard-library parsing if possible.

Do not add broad release documentation unless packaging tests require a reference. This is a bounded TVG example, not a release announcement.

## Self-Audit

- Placeholder scan: no TODO, TBD, or unspecified acceptance criteria remain.
- Scope check: first implementation is image-prompt profile support only; video mode is excluded.
- Boundary check: runtime support cannot decide TVG exit, aesthetic success, or profile strength.
- Evidence check: Images2 comparison is loop-assisted production evidence with a claim ceiling, not proof of general profile power.
- Method-layering check: profile content is split into core value semantics, reviewable surfaces, gain policy, and runtime support; guardrails remain subordinate to the mainline.
