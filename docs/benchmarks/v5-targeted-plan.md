# Mindthus V5 Targeted Stabilization Plan

Status: planning handoff for the post-V4 targeted repair stage. This is not a passing
certification record. The V5 measuring stick is frozen in
`docs/benchmarks/v5-certification-protocol.md`.

## Objective

Move Mindthus from clean diagnostic evidence to a V5 certification candidate without
returning to broad prompt/rule patching.

The V4 treatment result is close to the public line (`1.447` positive mean vs `1.5`
target), but the remaining gap is small enough that judge drift, single-run noise, and
overfitting can easily be mistaken for capability progress. V5 work therefore starts by
freezing the measuring stick before changing behavior.

## Current Evidence

- Latest diagnostic run: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/`
- Raw run commit: `c4ee0549327e4b70840781b503c0921ce839b314`
- Archived result commit: `9fc7f1206b6e57fa4ac6678408cfee492b96c569`
- Treatment positive mean: `1.447`
- Public target: positive mean `>= 1.5`, negative false wake-up rate `<= 10%`
- Final-answer negative false wake-up: `0.000`
- Runtime/event caveat: #32 loaded Mindthus/3L5S and leaked method language.
- Treatment V3 -> V4 movement: `+0.052`; do not use the V4 baseline delta `+0.263` as
  the honest treatment-improvement number.

## Stage Discipline

This stage has one rule:

> Do not fix V5 by adding more broad rules.

Allowed mechanisms:

- rubric and judge calibration examples
- executable benchmark telemetry
- owner-fidelity fields
- targeted Entry Triage trigger probes
- small calibration examples that anchor output shape
- mechanical before-answer probes for required visible actions
- repeat runs and shadow-set vetoes

Disallowed mechanisms:

- catch-all prompt paragraphs
- public-case keyword stuffing
- raising verdict rate without an over-forced-verdict counter
- counting a single run as stability evidence
- merging score-improving changes that regress negative or shadow controls

## Work Order

### 1. Freeze Evaluation First

Freeze rubric/judge behavior before repairing behavior. The disputed cases are:

- #32: final-answer clean enough, but runtime/event over-wake and rubric ambiguity.
- #37: machine `0` likely too strict, but first-sentence mush is still a real failure.
- #43: full-score treatment result is rubric-sensitive.
- #47: full score is acceptable but should not be marketed as successful debugging.
- #50: machine `2` likely too generous; human review suggests `1`.

Acceptance:

- rubric freeze version is recorded
- judge model is explicit
- generate and judge phases are split
- case calibration examples are linked from the V5 run report
- fixture diff notes cover v2 -> v3 and confirm v3 -> v4 fixture SHA stability

Protocol: `docs/benchmarks/v5-certification-protocol.md`.

### 2. Add Measurement That Can See the Real Failure

Add fields that separate "loaded" from "loaded the right thing and did the visible
action."

Minimum new fields:

- `false_wakeup_final_answer`
- `false_wakeup_runtime_event`
- `loaded_owner`
- `expected_owner_loaded`
- `required_visible_action_present`
- `owner_fidelity_verdict`

Acceptance:

- final-answer and runtime-event false wake-up rates are both reported
- #32 is visible as event-level over-wake even if final-answer false wake-up is false
- `mindthus_loaded=true` no longer hides wrong-lens cases such as #15
- `over_forced_verdict_rate` is described as a strict judge-field rate, with #49 tracked
  as a separate AQM boundary risk if its field is null

Implementation note: `scripts/run-judgment-benchmark-cli.py` now emits these fields in
score records and summary output, with machine-readable `diagnostic` vs
`certification_candidate` run status. A no-writeback reanalysis of the V4 treatment artifacts
classifies #32 as `runtime_over_wake`, #15 as `wrong_owner_loaded`, and #48 as `no_load`.
The same reanalysis gives final-answer negative false wake-up `0.000` and runtime-event
negative false wake-up `0.083`; this is diagnostic attribution, not a new certified run.

### 3. Stabilize No-Load Cases

Target cases:

`#2`, `#3`, `#4`, `#13`, `#17`, `#33`, `#34`, `#48`, `#49`.

Important split:

- #48 belongs to the first-sentence output-shape family, but V4 did not load Mindthus.
  Fix activation first, then judge first-sentence shape.

Acceptance:

- each target case is rerun `n >= 3`
- all target cases load the expected owner or an explicitly accepted owner
- no public negative control gains a new runtime/event false wake-up
- shadow negatives do not regress

### 4. Fix Loaded-But-Wrong-Action Cases

Target cases:

- first-sentence / definition-authority shape: #8, #37, and loaded #48 once activation is fixed
- required visible action: #10, #2, #15, #19, #33, #34

Relationship to #100:

- #100 owns the definition-authority output-shape contract.
- V5 work should extend #100 with concrete V4 evidence and calibration anchors rather
  than opening a duplicate philosophy issue.

Acceptance:

- #8 and #37 pass under loaded conditions with stable first-sentence adjudication
- #10 visibly names the wrong-optimization consequence
- #2 holds root cause as hypothesis pending timeline/monitoring evidence
- #15 performs explicit extreme comparison
- #19 makes order-of-magnitude cost/throughput/scale contrast visible
- #33/#34 trigger an Anti-Spiral brake before adding another rule or fallback
- H-group brake rate moves above the three-run plateau of `0.500`

### 5. Run V5 Certification Candidate

V5 certification can run only after items 1-4 land.

Acceptance:

- explicit generator model and judge model
- split generate/judge phases
- public fixture SHA and runner SHA recorded
- runtime fingerprint strict status `ok`
- dual false-wakeup report
- owner-fidelity report
- target/disputed cases rerun `n >= 3`
- shadow set run and no-regression statement
- positive mean `>= 1.5`
- final-answer and runtime-event negative false wake-up rates each within budget

## Issue Map

| Track | Issue |
| --- | --- |
| Output-shape contract | #100 |
| Rubric freeze and V5 protocol | #102 |
| Dual false-wakeup and owner-fidelity telemetry | #103 |
| Entry Triage no-load stability | #104 |
| Loaded-action anchors and mechanical probes | #105 |
| V5 certification run | #106 |

## Stop Conditions

Stop and re-evaluate before adding more rules if any of these happen:

- the same case is locally patched for a third time without stable `n >= 3` evidence
- a public score gain causes any shadow negative regression
- runtime-event false wake-up exceeds budget
- judge calibration changes the interpretation of a previous score movement
- the repair can no longer be assigned to activation, routing, output shape, visible
  action, or judge calibration
