# Brake Semantic-Triage Research Closure

Date: 2026-07-13

Closure baseline: `adbda9eb2fe84b79e8eaf09581f2f4f79e15f75f`

## Decision

Active brake semantic-triage refinement stops at this point. The repository will not
add another prompt version, calibration fixture, threshold, voting layer, retry path,
or model campaign for this pathology from the evidence already collected.

This is a research closure, not a passing certification. It preserves the useful
diagnostic evidence while declining further low-yield optimization against public or
team-authored cases.

## Existing Evidence Used For Closure

| Evidence | Result | Claim boundary |
| --- | --- | --- |
| Full public 50-case V4 run | Treatment positive mean `1.447`, below the `1.5` target; final-answer negative false wake-up `0.000` | Clean directional evidence, not a passing benchmark and not proof of zero runtime over-wake |
| Xhigh fresh dev `n=3` | Six pre-registered dev gates passed; original positive means `1.938 / 2.000 / 2.000`; negative triage/runtime/final false wakes `0/54` | Diagnostic dev evidence only |
| Triage V0.2 calibration campaign | Fail-closed red line on N08 after three valid fire votes | Valid evidence that permanent-baseline conversion was misread as an N+1 local repair; the incomplete run is not an `n=3` result |
| Current deterministic repository suite | `python3 -m unittest discover -s tests -q`: `631` tests passed in `22.096s` | Contract and repository integrity only; no live model behavior claim |

The authoritative artifacts remain:

- `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/REPORT.md`
- `docs/benchmarks/runs/2026-07-12-xhigh-dev-n3/REPORT.md`
- `docs/benchmarks/runs/2026-07-13-triage-v02-dev-n3/REPORT.md`

## Frozen Disposition

- Prompt V0.6 and the permanent-baseline calibration packet are retained as reviewed
  text artifacts. They are not converted into executable fixtures and are not active
  runtime or certification surfaces.
- The failed V0.2 campaign remains preserved exactly as a fail-closed diagnostic. It
  is not rerun to obtain a more favorable sample.
- Existing public, dev, and archived shadow cases remain evidence. No additional
  team-authored case is added to improve the same pathology score.
- No certification, release, or full 50-case passing claim is made from this branch.

## What Is And Is Not Established

Established:

- the benchmark can distinguish final-answer and runtime-event false wake-up;
- the fail-closed red line works mechanically;
- the existing dev configuration can pass its pre-registered dev gates repeatedly;
- loaded-action and activation behavior remain separable failure surfaces.

Not established:

- stable open-domain natural activation;
- generalization to an independently owned, unseen shadow distribution;
- a public 50-case treatment mean at or above `1.5`;
- production value sufficient to justify further brake-specific architecture.

## Reopening Conditions

This research line may reopen only when all of the following are true:

1. A new failure comes from a real user task or an independently owned unseen set and
   is not a mutation of the existing public, dev, or burned shadow material.
2. The failure has material user impact or credible recurrence evidence.
3. A proposed repair identifies a mechanism that can be falsified without creating a
   new sequence of team-authored calibration cases.
4. The repair can be checked with the existing deterministic suite plus one independent
   external evaluation, with a pre-registered stop condition.

Until then, effort should return to broader Mindthus usability, natural invocation,
installation, and real-task value rather than further optimization of this pathology.
