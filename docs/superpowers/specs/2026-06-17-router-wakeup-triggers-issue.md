# Issue Draft: Improve Router Wake-Up Triggers For Low-Frequency Mindthus Methods

> Status note: this is a historical wake-up design issue, not current routing guidance.
> Descriptions of over-activation are problem statements; current route selection should
> be read from `skills/using-mindthus/SKILL.md`, `AGENTS.md`, and the active skill docs.

## Title

Improve Mindthus router wake-up triggers for SELA, MPG, and EDSP

## Context

Real usage suggests that `3L5S`, `WAE`, and `TVG` are activated much more often than
`SELA`, `MPG`, and `EDSP`.

Part of this is structurally correct: daily agent work often involves unclear problems,
control-boundary decisions, and thin bounded artifacts. `SELA`, `MPG`, and `EDSP` are
intentionally narrower because they handle strategic direction, path-carrying strategy,
and structural ambiguity.

The suspected gap is not method content. The suspected gap is router exposure:
`using-mindthus` defines the routes, but it does not give enough positive wake-up
probes for agents to notice when a low-frequency method owns the active judgment object.
As a result:

- `3L5S` can absorb questions that are already structural, strategic, or path-bearing.
- `WAE` can absorb questions where the deeper issue is not control boundary but
  strategic system/local trade-off.
- `TVG` can absorb polished artifacts that actually need upstream structural or path
  judgment before another value pass.

## Core Principle

Do not broaden low-frequency methods until they become generic.

Instead:

```text
Keep SELA / MPG / EDSP narrow.
Expose clearer wake-up probes at the router surface.
Add pressure tests for "should wake" and "should skip" cases.
```

The fix should make the right method easier to notice without increasing method
ceremony or weakening direct-execution and information-acquisition boundaries.

## Target

Improve the `using-mindthus` router and project-level AGENTS guidance so that agents can
more reliably identify:

- `SELA` wake-up: a real local advantage may be losing to system-level cost,
  scale, feedback, or distribution efficiency.
- `MPG` wake-up: a qualified mainline exists, but the actor's carrier, exposure,
  timing, or vehicle may fail before the mainline resolves.
- `EDSP` wake-up: A/B both look true because the proposition, dimensions, or structure
  may be malformed.

Also preserve boundaries:

- Use `3L5S` for problem-definition failure, not as a default sink for all hard
  judgment.
- Use `WAE` for control-boundary mismatch, not as a generic route for every automation
  or process decision.
- Use `TVG` only after a bounded artifact exists and the active weakness is practical
  value, not upstream strategy or structure.

## Proposed Direction

### 1. Add Router Wake-Up Probes

Add a short `Wake-Up Probes / 唤醒探针` section after `Judgment Object Routing` in
`skills/using-mindthus/SKILL.md`.

The section should be compact and action-bearing. It should not become a second route
matrix or method tutorial.

### 2. Add AGENTS Mirror Guidance

Add a short project-level reminder in `AGENTS.md`:

- `3L5S` is a default problem-processing kernel only when the active object is a
  problem-definition or task-landing failure.
- If the active object is already structural ambiguity, strategic system/local trade-off,
  or mainline-path carrying, route directly to `EDSP`, `SELA`, or `MPG`.

### 3. Add Acceptance Experiments

Extend `tests/mindthus_router_pressure_tests.md` with router-level wake-up pressure
tests. These tests should complement, not replace, existing method-specific tests.

Minimum scenarios:

- SELA positive wake-up: real human or legacy local advantage exists, but system-level
  efficiency may become the mainline.
- SELA skip: a low-risk deterministic or purely missing-evidence task should not become
  a strategic trend judgment.
- MPG positive wake-up: a long-term mainline is already accepted, but the actor's
  carrier, exposure, or timing may fail before the mainline resolves.
- MPG skip: a naked trend slogan or missing-fact claim should not produce a
  Path-Carrying Strategy.
- EDSP positive wake-up: A/B both look right because the proposition or dimensions may
  be malformed.
- EDSP skip: a missing-data question should first acquire evidence rather than use
  structural projection.

### 4. Add Static Contract Tests

Update `tests/test_mindthus_router_contract.py` so future edits preserve:

- router wake-up probes for `SELA`, `MPG`, and `EDSP`
- route boundaries preventing `3L5S`, `WAE`, and `TVG` from swallowing adjacent
  judgments
- pressure-test coverage for positive and skip wake-up cases
- `AGENTS.md` mirror guidance

### 5. Add Behavioral Certification Gates

The first shipped canary and weak-cue pilot are useful smoke coverage, but both hit
`baseline-ceiling`. They must not be cited as a significant wake-up-rate lift.

Add runner-level gates so later certification cannot pass on thin evidence:

- known set: at least 60 paired routing moments;
- holdout set: at least 120 paired routing moments;
- overuse stress set: required direct, missing-evidence, deterministic, `tvg`, and
  `3l5s` buckets;
- real-use replay: at least 50 paired routing moments.

Runs that miss these gates fail with `minimum-pairs` or a specific
`minimum-<case-type>` failed check before any certification claim is allowed.

## Non-Goals

- Do not rewrite `SELA`, `MPG`, or `EDSP` core methodology.
- Do not make low-frequency methods broadly proactive.
- Do not create a new router skill or new cognitive primitive.
- Do not add a classifier, scoring engine, or automated semantic router.
- Do not weaken direct execution, information acquisition, evidence ceilings, or method
  arbitration.
- Do not make `3L5S` less useful for genuinely unclear or too-large problems.

## Acceptance Criteria

- `using-mindthus` contains compact wake-up probes for `SELA`, `MPG`, and `EDSP`.
- `using-mindthus` explicitly states when `3L5S`, `WAE`, and `TVG` should defer to
  adjacent methods.
- `AGENTS.md` says that `3L5S` must not swallow structural, strategic, or path-carrying
  judgments once the active object is already clear.
- `tests/mindthus_router_pressure_tests.md` includes router-level wake-up experiments
  for `SELA`, `MPG`, and `EDSP`, with both positive and skip cases.
- `scripts/router-wakeup-ab.py` blocks certification when the sample is below the
  documented minimum paired routing moments or overuse stress coverage.
- Contract tests fail before the router/docs changes and pass after them.
- Focused tests pass:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
python3 -m unittest tests.test_router_wakeup_ab_runner -v
python3 -m unittest tests.test_packaging_docs -v
```

## Implementation Notes

Keep the wording short. The router surface should help an agent notice the correct
judgment owner, then move into that method. It should not teach the whole method again.

The most important behavior change is not "use SELA / MPG / EDSP more often"; it is:

```text
When the active object is already strategic, path-bearing, or structurally ambiguous,
do not detour through the higher-frequency methods just because they are familiar.
```
