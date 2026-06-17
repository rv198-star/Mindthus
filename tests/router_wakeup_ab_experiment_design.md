# Router Wake-Up A/B Experiment Design

This protocol certifies whether the router wake-up change improves real method
activation behavior. It does not treat static contract tests as proof of behavioral
success.

## Claim Under Test

The treatment router improves wake-up quality for low-frequency methods without
increasing overuse:

- `SELA` wakes when local advantage is real but system-level efficiency may become the
  strategic mainline.
- `MPG` wakes when a qualified mainline must be carried through carrier, exposure,
  timing, or counter-force volatility.
- `EDSP` wakes when A/B both look plausible because the proposition or dimensions may
  be malformed.
- `3L5S`, `WAE`, and `TVG` do not swallow adjacent strategic, path-bearing, or
  structurally ambiguous judgments.

## Experimental Variants

Use identical user prompts for both variants. The only intended difference is the
router text available to the agent.

- Baseline A: checkout immediately before the Wake-Up Probes change.
- Treatment B: checkout after the Wake-Up Probes change.

Both variants should load `using-mindthus`; do not tell B the expected answer. The
prompt should say only that the agent should use Mindthus to decide the right method
and next move.

## Primary Endpoint

Primary endpoint: positive wake-up recall.

For positive cases, score whether the answer selects the correct low-frequency owner:

- SELA positive case -> `sela`
- MPG positive case -> `mpg`
- EDSP positive case -> `edsp`

A positive wake-up counts only if the answer also names why that method owns the active
judgment object. A method name without ownership reasoning scores as incorrect.

## Secondary Endpoints

- skip precision: for skip cases, the answer must avoid the low-frequency method and
  choose direct execution, information acquisition, `3l5s`, `wae`, `tvg`, or another
  route only when justified by the active object.
- execution impact: the answer must change at least one downstream action: strategy,
  risk handling, evidence requirement, next action, stopping condition, method choice,
  or handoff packet.
- adjacent absorption rate: count cases where `3L5S`, `WAE`, or `TVG` wrongly absorbs
  an `SELA`, `MPG`, or `EDSP` judgment.
- over-methodization rate: count direct, deterministic, or evidence-missing cases that
  receive unnecessary method ceremony.

## Discriminability Gate

Before a scenario set can certify lift, run a small calibration pilot and check that it
has enough room for improvement.

If baseline positive wake-up recall is higher than the maximum recall that still leaves
room for the required lift, the set fails with `baseline-ceiling` and must be treated as
a smoke test only.

- Known set maximum baseline positive recall: 75%.
- Holdout set maximum baseline positive recall: 80%.
- If baseline is at or above ceiling, do not continue spending samples on that set.
- A set that fails `baseline-ceiling` can still prove non-regression or runner shape,
  but it cannot prove improved wake-up rate.

The June 17 pilot on Scenario 20-25 produced 100% baseline positive wake-up recall and
100% treatment positive wake-up recall. That means the set has no discriminability for
the lift claim. Treat Scenario 20-25 as acceptance/smoke coverage, not as the evidence
for significant improvement.

Discriminative scenarios should be weak-cue cases:

- do not name the method, wake-up probe, or method vocabulary in the prompt;
- avoid direct phrases such as "system efficiency versus local advantage", "qualified
  mainline", "false binary", or "structural ambiguity";
- make the surface task plausibly look like `3l5s`, `wae`, or `tvg`;
- still contain enough latent facts for a blind judge to identify the low-frequency
  owner;
- include adjacent skip traps so a model cannot pass by over-calling low-frequency
  methods.

Use `tests/router_wakeup_weak_cue_holdout_cases.md` as the first weak-cue candidate
pool. It is deliberately separate from `tests/mindthus_router_pressure_tests.md`
because Scenario 20-25 is now known to be too easy for certification.

## Experiment 1: Known Router Wake-Up Set

Use Scenario 20-25 from `tests/mindthus_router_pressure_tests.md`.

This set is now classified as smoke/acceptance coverage. It verifies that the expected
route remains allowed, but it cannot certify lift unless a future baseline calibration
falls below the `baseline-ceiling` gate.

Design:

- 6 scenarios: 3 positive wake-up cases and 3 skip cases.
- 10 independent fresh sessions per scenario per variant.
- 60 outputs per variant.
- Randomize scenario order.
- Keep the prompt text identical across A and B.
- blind the judge to variant and expected treatment behavior.

Success:

- positive wake-up recall improves by at least 25 percentage points.
- McNemar test on paired scenario-run outcomes is statistically significant at
  alpha = 0.05.
- skip precision is non-inferior: treatment skip precision is no more than 5 percentage
  points worse than baseline and remains at or above 90%.
- execution impact pass rate does not decrease.

## Experiment 2: Holdout Generalization Set

Use a holdout set that was not written into the router docs or pressure tests.

Minimum holdout:

- 4 SELA positive cases and 4 SELA skip cases.
- 4 MPG positive cases and 4 MPG skip cases.
- 4 EDSP positive cases and 4 EDSP skip cases.
- 24 scenarios total.
- 5 independent fresh sessions per scenario per variant.
- 120 outputs per variant.

Case construction rules:

- Positive cases must contain enough information to identify the method owner.
- Skip cases must be plausible traps: efficiency language that lacks evidence, naked
  trend slogans, empirical A/B questions with missing data, workflow mentions that are
  really not control-boundary questions, or polished artifacts whose missing value is
  upstream judgment.
- Do not include the strings `SELA`, `MPG`, `EDSP`, `Wake-Up Probes`, or method names in
  the user prompt.
- Prefer weak-cue wording that hides the intended owner behind ordinary product,
  workflow, review, planning, or writing language.

Success:

- Each method's positive wake-up recall improves by at least 15 percentage points.
- Overall positive wake-up recall improves by at least 20 percentage points.
- McNemar test is statistically significant overall.
- Method-level p-values are corrected with Holm adjustment.
- skip precision remains non-inferior by the same 5 percentage point margin.

## Experiment 3: Overuse Stress Set

This experiment protects against a fake improvement where the treatment simply wakes
low-frequency methods more often.

Minimum set:

- 10 clear direct-execution cases.
- 10 missing-evidence cases.
- 10 deterministic control or validation cases.
- 10 bounded-artifact TVG cases that should remain `tvg`.
- 5 genuine `3l5s` problem-definition cases.
- 45 scenarios total, 3 sessions per scenario per variant.

Success:

- Treatment low-frequency false-positive rate is not higher than baseline by more than
  5 percentage points.
- Treatment still chooses direct execution for at least 90% of direct cases.
- Treatment still chooses information acquisition for at least 90% of missing-evidence
  cases.
- Treatment does not reduce TVG/3L5S correctness by more than 5 percentage points.

## Experiment 4: Real-Use Replay And Logging

Use real or redacted transcripts after the synthetic experiments pass.

Sampling:

- Collect at least 50 real Mindthus routing moments.
- Label each transcript's active judgment object before seeing the agent answer.
- Replay the same prompt against baseline A and treatment B.
- blind judge outputs by hiding variant and file revision.

Success:

- Treatment improves correct owner selection by at least 15 percentage points.
- Adjacent absorption rate decreases.
- No material increase in over-methodization.

Record results with `scripts/log-fidelity-usage.py` using `record-type evaluation` or
`record-type real_use`.

## Scoring Rubric

Each output gets these fields:

```text
correct_owner: yes | no
positive_wakeup: yes | no | not_applicable
skip_correct: yes | no | not_applicable
execution_impact: yes | no
adjacent_absorption: none | 3l5s | wae | tvg | other
over_methodized: yes | no
evidence_ceiling_respected: yes | no
notes: short rationale
```

Primary binary outcome:

```text
primary_pass = correct_owner == yes and execution_impact == yes
```

For skip cases:

```text
skip_pass = skip_correct == yes and evidence_ceiling_respected == yes
```

## Executable Harness

After blinded scoring is collected, analyze the paired records with:

```bash
python3 scripts/router-wakeup-ab.py \
  --scores path/to/scores.jsonl \
  --experiment known \
  --write-report path/to/report.md \
  --fail-on-uncertified
```

Use `--experiment holdout`, `--experiment overuse`, or `--experiment real_use` for the
other experiment layers. Add `--json` when a CI job or follow-up script needs the
machine-readable report.

`tests/router_wakeup_ab_scores.fixture.jsonl` is a tiny shape fixture for validating
the runner. It is not a certification run and must not be cited as evidence of
behavioral lift.

The analyzer validates:

- every baseline record has exactly one treatment pair for the same `scenario_id` and
  `run_id`;
- baseline positive recall does not exceed the experiment's `baseline-ceiling` before
  lift is treated as certifiable;
- `positive_wakeup` matches `correct_owner` on positive cases and is null outside
  positive cases;
- `skip_correct` and `evidence_ceiling_respected` produce the skip precision guardrail;
- overuse stress records cover direct, missing-evidence, deterministic, `tvg`, and
  `3l5s` cases without low-frequency false-positive inflation.

## Statistical Analysis

Use paired analysis whenever A and B answer the same scenario-run pair.

- Positive wake-up recall: McNemar test on `primary_pass`.
- Skip precision: non-inferiority test with a 5 percentage point margin.
- Method-level positive recall: McNemar per method, corrected with Holm.
- effect size: report absolute percentage point lift and 95% confidence interval.

Suggested reporting:

```text
Baseline positive wake-up recall: 38 / 120 = 31.7%
Treatment positive wake-up recall: 78 / 120 = 65.0%
Lift: +33.3 percentage points
95% CI: [...]
McNemar p: ...
Skip precision delta: ...
```

## Minimum Success Threshold

This is the minimum success threshold for claiming the change is certified.

The change is certified only if all are true:

- Known set passes.
- Holdout set passes.
- Overuse stress set passes non-inferiority.
- Real-use replay passes or is explicitly marked pending with no claim of real-world
  proof.
- Overall positive wake-up recall lift is at least 20 percentage points.
- The lift is statistically significant.
- skip precision is non-inferior.
- execution impact does not decrease.

If only the known set passes, the correct claim is:

> The router wake-up mechanism works on the designed acceptance scenarios.

If known and holdout pass, but real-use replay is missing, the correct claim is:

> The router wake-up mechanism generalizes across synthetic pressure scenarios, but
> real-use lift is not yet proven.

Only after real-use replay or live logging passes can the project claim:

> The router wake-up change significantly improved observed wake-up behavior.
