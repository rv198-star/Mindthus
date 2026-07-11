# Brake Semantic Triage K=3 Majority-Decision Design

Status: design only. Requires external audit approval before implementation.

## Decision

Replace the active one-sample fire decision with three independently executed
triage samples for each user turn. This is a response to observed boolean-layer
flip losses, not a prompt, fixture, or semantic-definition change.

For each turn, the future runner will execute exactly three samples using the
same frozen prompt, model configuration, schema, and four hard gates. Each
sample must have its own empty `HOME` isolation root and must not resume another
sample's session. Each sample independently receives the existing local
validation rule: one retry after a local validation failure; retry failure ends
that sample in the documented fallback abstain state.

Let `vote_i` be `fire` only when sample `i` is valid and all four hard gates are
true:

```text
is_repeated_local_repair
&& same_means_type
&& prior_repair_count >= 3
&& is_n_plus_1_request
```

The turn fires only when at least two samples vote `fire`:

```text
majority_fire = count(vote_i == fire) >= 2
```

An invalid sample cannot vote fire. Two valid fire votes are sufficient even if
the third sample is invalid. Confidence remains telemetry only: it is neither a
vote weight nor a fire threshold. This design does not reinstate threshold
configuration.

## Safety Red Line Is Not A Majority Vote

The existing negative-case red line remains stricter than the fire rule. For a
negative case-turn, any one valid sample whose four hard gates are true triggers
the red line immediately:

```text
negative_red_line = any(valid_i && all_four_hard_gates_true_i)
```

This is a global stop event even if the other two samples abstain and
`majority_fire` is false. The run must stop, preserve all raw artifacts, and go
to rollback and architecture review. No vote aggregation, confidence value, or
subsequent sample may clear this event.

An invalid sample has no parsed hard-gate result, so it cannot itself establish
the red line. It must remain separately recorded; existing invalid-attempt and
provider-capacity rules continue to determine whether the enclosing run is
valid for a gate.

## Owner Exposure And Latch

`majority_fire` is the only new signal allowed to open or extend the brake
owner-skill latch.

- A majority fire on the current turn exposes only the register-defined brake
  owner set and loaded-action contract.
- Once latched, exposure remains for the configured pressure follow-up turn;
  a later single-sample abstain cannot unload it.
- A turn-one majority abstain creates no latch and exposes no Mindthus owner
  skill. If a later turn reaches majority fire, exposure begins on that later
  turn.
- A single fire vote without a majority neither exposes the owner nor creates a
  latch. On a negative case, it still invokes the red line above.

This preserves the current owner-gate boundary: on no fire and no existing
latch, the full Mindthus owner-skill family remains out of generator context.

## Required Telemetry And Archive Shape

The implementation must preserve every sample and every retry attempt. The
following field names are proposed implementation contracts, not a change to
the current artifact schema:

```text
triage_samples[]:
  sample_index: 1 | 2 | 3
  isolation_home
  raw_model_outputs[]
  validation_attempts[]
  valid
  hard_gates:
    is_repeated_local_repair
    same_means_type
    prior_repair_count_at_least_3
    is_n_plus_1_request
  all_four_hard_gates_true
  vote: fire | abstain | invalid
  confidence_telemetry
  abstain_reason
  fallback_error

triage_vote_count_fire
triage_vote_count_abstain
triage_vote_count_invalid
triage_majority_fired
triage_negative_four_true_red_line
triage_abstain_reasons[]
triage_invalid_sample_errors[]
owner_skill_exposed[]
exposure_reason[]
```

`triage_abstain_reasons[]` must be the unedited list of the original reasons
from valid abstaining samples, ordered by sample index. The runner must not
synthesize a majority explanation. A fallback error belongs in
`triage_invalid_sample_errors[]`, never in a fabricated abstain reason.

Each sample's isolation path, raw response before and after an allowed retry,
parse/validation outcome, and final vote must be retained in the run archive.
The enclosing run manifest must also include the future K=3 fire-policy
configuration fingerprint, runner fingerprint, prompt fingerprint, register
fingerprint, fixture fingerprint, triage-model fingerprint, and owner-gate
identifier.

## Evidence Base

This design treats the following as minority-flip evidence rather than evidence
for another prompt edit. It does not copy sealed external prompts or add any of
these cases to a calibration fixture.

| Evidence | Recorded observation | Role in this design |
| --- | --- | --- |
| `p08-R3` | Archived public diagnostic evidence of a one-sample decision flip. | Shows a boolean-level decision can be unstable despite frozen semantics. |
| `p11` and `s04` | Archived public flip-family observations. | Supports sampling the same decision rather than tuning confidence. |
| `S9-R2` | Sealed Batch 5 external audit record; remains outside this repository. | Confirms the failure family appears outside public development cases. |
| `p02`, `p03`, `p11` | The validation-retry dev gate recorded three genuine semantic abstains, producing `3/48` boolean-flip loss. | Direct trigger for the pre-registered K=3 alternative. |
| Negative package | The current public package records zero single-sample negative four-true events across `54` case-runs. | Supports retaining a strict one-sample red line; it does not prove the risk is zero. |

The direct public source for the current loss and negative result is
`docs/benchmarks/runs/2026-07-11-triage-validation-retry-dev/REPORT.md` and
its `aggregate.json` / `activation-boolean-evidence.json` artifacts. `S9-R2`
is intentionally referenced only by adjudicated identifier because its input is
a sealed, consumed external shadow case.

## Cost And Capacity

K=3 triples the nominal triage call count per evaluated turn. Because each
sample may use one local-validation retry, the worst case is six triage model
calls for that turn. Generator, judge, and loaded-action calls do not multiply
solely because K=3 is enabled.

The next dev `n=3` campaign must reserve capacity for the A1/A2 anchor packet
before it starts. Each valid repeat must retain enough provider capacity for all
four anchor turns and their judges, yielding all 12 required payload
observations across three repeats. The anchor packet is scheduled as a
protected packet within each repeat, with capacity checked before the campaign;
an explicit provider quota failure isolates that repeat as an
`INVALID-ATTEMPT`, never as partial passing evidence. This is a capacity
discipline, not a relaxation of the A1/A2 evidence requirement.

## Known Limitations

- A two-of-three result can still be wrong when two samples make the same
  semantic mistake. Separate empty `HOME` roots isolate session state; they do
  not make same-model samples statistically independent.
- Majority voting can mask a minority warning on positive cases. The retained
  per-sample archive is required so this residual can be reviewed rather than
  silently averaged away.
- The strict negative red line catches any observed single-sample four-true
  false positive, but it cannot guarantee that an unobserved negative sample
  will never be misread.
- K=3 addresses decision variance only. It does not repair the documented
  narrow-reading boundary cases, the semantic definition, or loaded-action
  behavior.
- Provider limits can invalidate a run. The larger triage call budget makes
  capacity reservation and explicit invalid-attempt handling more important.

## Implementation Contract After Audit Approval

The implementation review must demonstrate all of the following before any dev
run:

1. Exactly three isolated triage samples run for every evaluated turn; each has
   its own validation-and-one-retry lifecycle.
2. Two valid fire votes fire, while one fire vote does not expose the owner or
   latch it.
3. A negative case with even one valid four-true sample immediately triggers
   the red line even when majority fire is false.
4. Latch behavior is driven only by majority fire and preserves the existing
   follow-up-turn exposure semantics.
5. All raw outputs, attempts, votes, abstain-reason originals, invalid errors,
   exposure records, and fingerprints are archived.
6. Confidence is recorded but has no branch in the fire decision.
7. The full test suite covers the red line, retries, two-of-three rule, one-of-
   three abstain, invalid-sample handling, and latch behavior.

After those checks and external implementation review, the next dev `n=3` must
run the original fixture, expansion fixture, and A1/A2 anchor packet under one
frozen configuration. It must return all 12 A1/A2 payload observations, retain
the negative red-line appendix, and report individual ballots beside the
existing activation, behavior, and loaded-action evidence. No Batch 6 request
is implied by this design.

## Frozen Surfaces And Non-Goals

This design changes no runtime behavior. It does not modify or authorize a
change to the V0.4 prompt, active fire-policy definition, fixtures, owner gate,
register anchors, loaded-action contract, triage model, or current runner. The
current fire policy remains `four_hard_gates_only` until a separately reviewed
implementation is approved.

No prompt wording, threshold, matcher, prefilter, case-specific rule, or
calibration example is proposed here. Implementation begins only after external
audit approves this document.
