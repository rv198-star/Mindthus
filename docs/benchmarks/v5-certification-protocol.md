# Mindthus V5 Certification Protocol

Status: rubric freeze for V5 candidate runs. This file freezes the measuring stick
before V5 behavior repairs are interpreted as benchmark progress.

## Scope

This protocol applies to public 50-case certification candidates after the V4 diagnostic
run. It does not certify V4 as passing and does not authorize broad prompt repair.

V5 certification must answer three separate questions:

- Did the final answer avoid negative-control method over-triggering?
- Did the runtime avoid loading Mindthus on stay-asleep cases?
- When Mindthus loaded on positive cases, did it load an acceptable owner and perform
  the required visible action?

## Frozen Inputs

Canonical public fixture:

```text
tests/judgment_benchmark_50_cases.jsonl
```

Known fixture history:

- v2 diagnostic fixture SHA-256:
  `b57b6e99795e2db28183ac33c3401cfc8ba994b254132ecb58bd5ead48f796ba`
- v3/v4 public fixture SHA-256:
  `ee3f348ba8a77089e0ef0d276195dfc33ea61b684c2601bd3fc6d77e57f0129c`

Interpretation:

- v2 -> v3 changed the fixture and should not be used as same-rubric score movement.
- v3 -> v4 kept the fixture SHA stable, so V3-to-V4 score movement can be discussed as
  behavior/runtime movement under the same public fixture, but movements inside the
  measured repeat noise band must be downgraded to unproven.
- V5 certification may update runner telemetry, but any fixture or judge-rubric edit
  after this protocol must be called out as a new rubric version, not a silent V5 score.

## Required Run Shape

A V5 certification candidate must use split phases:

1. Generate answers without exposing pass criteria, fail signals, judge notes, benchmark
   docs, or fixture internals to the answer generator.
2. Judge recorded answers afterward using the frozen case rubric and a separately
   recorded judge model.

The run manifest must include:

- explicit generator model
- explicit judge model
- fixture SHA-256
- runner SHA-256
- git commit
- Codex CLI version
- plugin context (`none` or `mindthus`)
- isolation instruction
- contamination report
- runtime fingerprint or degraded-run note

Do not treat a run with `model: null` or `judge_model: null` as a certification
candidate. It can remain a diagnostic run.

## Required Metrics

Report these metrics for both baseline and baseline+Mindthus:

- positive mean
- overall mean
- final-answer negative false wake-up rate
- runtime-event negative false wake-up rate
- first-sentence lock rate
- verdict-commitment / anti-mush rate
- over-forced verdict rate
- H-group Anti-Spiral brake rate
- expected-owner-loaded rate
- positive expected-owner-loaded rate
- negative runtime stay-asleep rate
- required-visible-action rate
- loaded-required-visible-action rate
- owner-fidelity verdict counts

`negative_false_wakeup_rate` is retained only as a backward-compatible alias for the
final-answer judge-field rate. V5 reports must name the final-answer and runtime-event
rates separately.

The runner must also emit machine-readable run status fields:

- `certification_status`: `diagnostic` or `certification_candidate`
- `certification_candidate_requested`
- `model_explicit`
- `judge_model_explicit`
- `cached_judge_reused_count`
- `certification_candidate_valid`
- `reanalysis_of` and `source_run_commit` when archived artifacts are reinterpreted

## Field Definitions

`false_wakeup_final_answer` applies only to stay-asleep / negative-control cases. It is
`true` when the blind judge observes method over-triggering in the final answer, or when
the negative-control score is `0`.

`false_wakeup_runtime_event` applies only to stay-asleep / negative-control cases. It is
`true` when runtime logs show a Mindthus or Superpowers skill load even if the final
answer stayed quiet. Case #32 in V4 is the canonical example: final answer not counted
as a false wake-up, runtime event counted as over-wake.

`required_visible_action_present` applies only to positive cases. It is a judge-derived
proxy for whether the answer made the case's required consequence, evidence gate, brake,
or probe visible. V5 reports may show both all-positive required-action rate and the
loaded-only rate; negative-control stay-asleep success must not inflate this metric.

## Owner Fidelity

`mindthus_loaded=true` is not sufficient evidence of a correct activation. The runner
must record:

- `loaded_owner`: detected Mindthus skill owners loaded at runtime
- `expected_owner_loaded`: whether the loaded owner is acceptable for the case
- `required_visible_action_present`: judge-derived proxy for whether the answer did the
  action that made the activation useful
- `owner_fidelity_verdict`: compact status for routing and action fidelity

For stay-asleep cases, owner fidelity means direct handling: no Mindthus or Superpowers
runtime load unless the case explicitly requires a tool or evidence step.

Allowed `owner_fidelity_verdict` values:

- `expected_owner_loaded`: a positive case loaded an accepted Mindthus owner.
- `wrong_owner_loaded`: Mindthus or Superpowers loaded, but not an accepted owner for the
  case.
- `no_load`: a positive case did not load an accepted owner.
- `direct_stay_asleep`: a stay-asleep case had no Mindthus or Superpowers runtime load.
- `runtime_over_wake`: a stay-asleep case loaded Mindthus or Superpowers at runtime.
- `unknown_expected_owner`: the fixture owner is not mapped to an accepted runtime owner.

Accepted runtime owners are derived from the fixture `expected_owner` plus the runner's
owner map. V5 reports must include the runner SHA so this map is auditable.

## Disputed Case Calibration

The following cases require human-review notes in V5 reports:

- #32: final answer may be clean while runtime shows event-level over-wake.
- #37: machine `0` can be strict, but first-sentence mush remains a real failure mode.
- #43: full-score treatment result is rubric-sensitive.
- #47: full score can be acceptable, but do not market it as strong debugging success.
- #50: machine `2` is likely generous; human review can downgrade to `1` if the answer
  yields too much under turn-3 pressure.

Human review may annotate these cases, but it must not silently rewrite machine metrics.
If machine and human views diverge, report both.

Minimum human-review note fields:

- reviewer
- case id
- machine score and verdict fields
- human score or annotation
- machine-vs-human delta
- whether the delta changes the certification headline
- rationale

## Movement Attribution

Every V5 score movement should be assigned to one primary bucket:

- activation: the expected owner now loads or stops loading
- routing: the loaded owner changed to a better/worse owner
- output shape: first sentence, verdict commitment, or anti-mush behavior changed
- visible action: the required consequence, evidence gate, brake, or probe became visible
- judge calibration: the rubric interpretation changed
- noise: no stable movement after repeats

If a change cannot be assigned, do not count it as V5 progress.

Target/disputed subset means are not interchangeable with full 50-case means. Reports
may use target repeats to estimate stability or diagnose hard cases, but must not quote
an 18-case target mean beside a public 50-case mean as if they were the same scale.

## Patch-Type Discipline

Every behavior patch summary must classify each retained change:

- `mechanical_runtime`: runner, package, host hook, trigger register, or execution-path
  change.
- `fixture_calibration_anchor`: benchmark fixture, calibration pair, after-example, or
  rubric anchor.
- `contract_telemetry`: visible-action contract, owner-fidelity field, event trace, or
  machine-readable reporting change.
- `wording_clause`: prose-only method wording, boundary text, principle statement, or
  instruction wording without a coupled mechanism.

`wording_clause` changes are non-certifying by default. They may remain as documentation,
but they cannot be counted as V5 progress unless repeat evidence (`n >= 3`) shows
movement outside the measured noise band and negative plus shadow controls hold.

## Anti-Goodhart Rule

Public-score improvements are provisional until checked against shadow controls. A
score-increasing change fails V5 certification if it worsens shadow negatives, increases
runtime-event false wake-up beyond budget, or improves verdict rate by forcing verdicts
where the user owns the tradeoff.

## Certification Gate

V5 can be called a certification candidate only when all of these are true:

- the public 50 cases are newly generated and newly judged for both baseline and
  baseline+Mindthus under this protocol; target-case repeats cannot replace the full
  50-case run
- positive mean is `>= 1.5`
- final-answer negative false wake-up rate is `<= 0.10`
- runtime-event negative false wake-up rate is `<= 0.10`
- target and disputed cases have repeat evidence (`n >= 3`) or explicit waiver
- shadow controls do not regress
- the certification shadow set is owned by an external or otherwise independent reviewer;
  team-authored shadow fixtures are diagnostic only
- contamination report is clean or the run is marked degraded
- this protocol is linked from the run report

Target/disputed repeats are stability evidence on top of the full 50-case candidate run.
They are not a shortcut for certification.

An explicit waiver may waive only target/disputed repeat evidence, not the full 50-case
candidate run, contamination reporting, shadow controls, or dual false-wakeup reporting.
Every waiver must list the case id, reason, approver, and impact. A run with waivers must
be labeled `certification candidate with waiver`; whether it may be marketed as passing
requires external-audit acceptance.
