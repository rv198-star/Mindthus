# Cinematic Colossal Realism Migration Notes

## Core

The external cinematic prompt skill is used as a behavior sample, not source truth.
This migration extracts behavior families into a TVG advanced profile package without
copying the original skill's concrete prompt wording.

## Behavior Mapping

| Behavior family | Profile layer | Migration result |
|---|---|---|
| Terse input expands without interrogation | `gain_policy` | Classify subject first, build a deterministic skeleton, then let TVG fill and audit. |
| Subject category changes defaults | `runtime_support` | `subject-taxonomy.json` returns candidate categories and scene hints. |
| Human-scale witness is required | `value_semantics` and `realization_surface` | The prompt must include a witness-scale or instrument-scale anchor. |
| Three-layer scale makes enormity readable | `realization_surface` | Foreground, midground, and background-colossus surfaces are review handles. |
| Physical environment feedback proves presence | `value_semantics` and `gain_policy` | TVG should add feedback before adding more adjectives. |
| Colossus is not fully mastered by the frame | `gain_policy` | Partial visibility and frame overflow are preferred moves. |
| Camera and lighting make "cinematic" reviewable | `realization_surface` | Lens, viewpoint, exposure, atmosphere, source light, and texture are audit surfaces. |
| Negative constraints avoid media pollution | `profile_veto_constraints` and `runtime_support` | `negative-constraints.json` and linting report forbidden media terms. |
| User field templates are preserved | `runtime_support` | `validate_field_lock.py` reports deterministic field drift. |

## Boundary

Runtime support can report missing surfaces and risky terms. It cannot decide aesthetic
success, profile maturity, TVG state routing, or final exit.

## Migration Claim

This example can support a claim that a TVG profile package can absorb runtime habits
from an external prompt skill more cleanly than a prose-only profile. It cannot support
a claim that the migrated profile is generally stronger than the original skill until
multiple single-pass and loop-assisted tests are run and reviewed.
