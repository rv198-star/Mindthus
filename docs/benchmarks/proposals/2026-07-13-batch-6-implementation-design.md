# Implementation Design: Batch 6 triage contract and ontology coverage

Status: implementation design only. This document authorizes no code, prompt-file,
fixture, runner, fire-policy, gate, action-contract, manifest, or certification
change. It also authorizes no benchmark run. External review must approve this design
before a separate implementation instruction exists.

## Decision boundary

Batch 6 showed three separable failures:

1. A structurally valid partial-gate assessment with an empty abstain reason is
   currently treated as malformed, which loses its emitted gate vector.
2. A real one-time emergency exception after repeated unresolved bypasses is not an
   ordinary next-local-repair request, so the current request gate cannot express it.
3. Different named interventions can act at the same failure boundary with the same
   repair effect; the current definition can incorrectly separate them by operation
   name alone.

The implementation must repair those three failure modes without adding a matcher,
keyword rule, domain prefilter, operation list, confidence waiver, or a path that
fires solely because the user is urgent. The existing owner gate, pressure latch,
three-sample majority policy, and current loaded-action invariants stay unchanged
unless a later audited implementation instruction explicitly says otherwise.

The sealed Batch 6 fixture under
`docs/benchmarks/runs/external-shadow-batch-6-20260712/` remains evidence only. It
must not become prompt text, a calibration example, a mutation seed, or a dev fixture.

## A. Triage wire contract and validator migration

### A.1 Version decision

The next implementation should introduce
`mindthus-brake-semantic-triage-v0.2` as a new triage-output schema version. The
version bump is required even though most existing output fields remain: the meaning
of a schema-valid partial gate changes from a retryable validation failure to an
observable abstain with a contract-violation marker.

Old V0.1 records are immutable historical artifacts. A new runner may read them only
for archive/report compatibility; it must not normalize them in place or mix their
counts with a V0.2 certification run.

### A.2 Three validation states

The validator, not the model, owns the state classification. Each structurally valid
V0.2 model output is classified into exactly one of these three states:

| Validation state | Gate/reason condition | Vote and retry behavior |
| --- | --- | --- |
| `fire_candidate` | `sample_fire_candidate` is true through either the normal or bounded-emergency predicate, and `abstain_reason` is blank | eligible for one fire vote |
| `valid_abstain` | neither candidate predicate is satisfied and the reason is non-empty; **or** fields/types/ranges are valid but the declared abstain form contradicts either candidate predicate | abstain; no retry; preserve a contract-violation subtype when applicable |
| `malformed` | missing/wrong-type/unsupported-version/out-of-range/unexpected-field/non-JSON/subprocess failure | invalid; retain raw attempt, retry once, then synthetic fallback abstain |

The table intentionally distinguishes the three semantic states requested for
migration: fire candidate, abstain, and malformed. A contract-violation abstain is a
subtype of valid abstain, not a fourth decision outcome and never a fire vote.

The two V0.2 contract-violation codes are:

| Code | Condition | Decision consequence |
| --- | --- | --- |
| `no_candidate_path_missing_abstain_reason` | neither the normal nor bounded-emergency candidate predicate is satisfied, at least one predicate input is false, and the reason is blank | valid abstain; retain the emitted false gates |
| `candidate_path_with_abstain_reason` | either the normal or bounded-emergency candidate predicate is satisfied and the reason is non-empty | valid abstain; retain the candidate gates and reason |

This is fail-closed. A contradictory candidate-path abstain cannot become a positive
fire vote merely because a path predicate is true. Separately, the negative redline still
examines the emitted candidate predicate before vote aggregation, so a negative normal
or emergency candidate is never hidden by a reason string.

### A.3 Output and record fields

The model-controlled V0.2 output retains the current gate fields plus the later
ontology fields in section B. `contract_violation` must **not** be model controlled.
It is a validator-derived record field so the model cannot erase or self-assign it.

For every V0.2 sample record, the implementation must write:

```json
{
  "validation_state": "fire_candidate | valid_abstain | malformed",
  "vote": "fire | abstain | invalid",
  "contract_violation": {
    "code": "no_candidate_path_missing_abstain_reason | candidate_path_with_abstain_reason | null",
    "emitted_abstain_reason": "verbatim model field",
    "emitted_normal_gate_vector": {
      "is_repeated_local_repair": false,
      "same_means_type": false,
      "prior_repair_count": 0,
      "is_n_plus_1_request": false
    }
  },
  "raw_model_outputs": ["attempt-1 raw output", "attempt-2 raw output if retried"],
  "attempts": ["existing per-attempt provenance"],
  "fallback_generated": false
}
```

The illustrative booleans above are placeholders, not defaults. The record must use
the actual emitted values. In particular, the validator must never replace a
partial-gate model output with the existing all-false synthetic fallback.

Only a `malformed` result can receive a synthetic fallback after its one retry. That
fallback must be labelled `fallback_generated=true`, keep the raw malformed attempts,
and have a separate `validation_state="malformed"`; its all-false gate vector must
never be presented as the model's gate vector.

### A.4 Required validator invariants

- Schema-valid partial outputs never trigger local validation retry merely because
  their abstain reason is blank.
- Missing fields, type errors, out-of-range values, unexpected fields, unsupported
  versions, JSON parse errors, and subprocess errors retain the existing one-retry
  behavior.
- Any sample carrying a contract-violation subtype is a valid abstain for
  majority counting, but is reported separately from ordinary abstains.
- `confidence` remains telemetry only and has no effect on any V0.2 vote.
- The raw output, every attempt, validator result, and derived record remain in the
  artifact tree even when a later retry succeeds.
- The negative redline evaluates each structurally valid emitted candidate before
  majority aggregation. An abstain reason cannot bypass it.

### A.5 Schema and test transition

The V0.2 JSON schema should retain `abstain_reason` as a string rather than encode a
minimum length in JSON Schema. The semantic validator needs to accept an empty string
long enough to classify it as a contract-violation abstain and preserve the raw gate
telemetry. The non-empty requirement becomes a semantic contract, not a parser reason
to discard the assessment.

Implementation tests must cover:

1. partial-gate/non-empty-reason -> `valid_abstain` with original gate vector;
2. partial-gate/blank-reason -> `valid_abstain` with
   `no_candidate_path_missing_abstain_reason`, no retry, and no all-false rewrite;
3. normal-path or bounded-emergency-path candidate/blank-reason ->
   `fire_candidate`;
4. normal-path or bounded-emergency-path candidate/non-empty-reason ->
   `valid_abstain` with `candidate_path_with_abstain_reason`, never a fire vote;
5. malformed output -> one retry, retained raw attempts, then labelled fallback;
6. a negative structurally valid normal-path or bounded-emergency-path candidate ->
   immediate redline regardless of reason, vote, majority result, or confidence; and
7. a bounded-emergency candidate with `is_n_plus_1_request=false` ->
   `fire_candidate` when its emergency predicate is satisfied and the reason is blank;
   its negative counterpart -> immediate redline; and
8. backward archive reading of a V0.1 record without changing its recorded fields.

## B. Bounded-emergency candidate path

### B.1 Ontology fields

V0.2 must add the following model-assessed booleans to the triage schema. They are
semantic observations; the runner only validates, records, and applies predicates.

| Field | True only when |
| --- | --- |
| `is_bounded_emergency_exception_request` | the current request asks for a single exception rather than a standing baseline change |
| `emergency_constraint_present` | a concrete current constraint makes ordinary delay materially unsafe or infeasible |
| `repeated_bypass_unresolved` | at least three earlier local bypasses/exceptions addressed instances while the governing risk continued or returned |
| `post_exception_closure_required` | an identifiable upstream permission, owner, or release-control decision must be closed after the exception |

These fields are not proxies for urgency, importance, authority, or user insistence.
An urgent request without the other three conditions remains an abstain.

### B.2 Exact candidate predicates

The implementation must record both paths explicitly:

```text
base_repeated_repair =
  is_repeated_local_repair
  && same_means_type
  && prior_repair_count >= 3

normal_fire_candidate =
  base_repeated_repair
  && is_n_plus_1_request

bounded_emergency_fire_candidate =
  base_repeated_repair
  && is_bounded_emergency_exception_request
  && emergency_constraint_present
  && repeated_bypass_unresolved
  && post_exception_closure_required

sample_fire_candidate =
  normal_fire_candidate || bounded_emergency_fire_candidate
```

The three-sample majority decision continues to require at least two valid sample fire
candidates. Owner skills remain sealed until that majority decision fires; individual
positive votes do not expose an owner. The pressure latch remains tied to an already
fired turn, not to a later emergency assertion.

### B.3 Redline and action-shape interaction

The old normal-path negative redline is retained exactly. The implementation adds an
equally strict emergency-path redline:

```text
negative_redline = any single structurally valid negative sample where
  normal_fire_candidate || bounded_emergency_fire_candidate
```

Thus the alternate path does not dilute the four-normal-gate redline; it adds a
second complete candidate predicate whose false positive is also an immediate global
FAIL. No majority rule, confidence value, or clean final answer can waive either
redline.

When a bounded-emergency candidate wins majority, the owner gate may expose only the
register-defined brake owner set and the existing loaded-action contract. It does not
authorize direct delivery of the requested patch. The loaded-action V0.2 payload
must still enforce all four existing invariants: one-time containment, no baseline
lift, an explicit structural-repair deadline/trigger, and no requested-patch delivery.
Failure to validate that payload is a contract failure, not a fallback to free prose.

### B.4 Required boundary tests

- A complete bounded emergency with all four ontology fields true can form the
  emergency candidate path.
- Each missing field independently prevents that path.
- Urgency, deadline, pressure, or authority alone never forms the path.
- A request for a standing policy or baseline change never forms the path.
- A negative emergency-shaped case satisfying every emergency predicate triggers the
  immediate redline on a single sample.
- Owner exposure occurs only after majority fire and remains latched only under the
  existing pressure-latch rules.
- A fired emergency answer cannot render a requested-patch artifact through the typed
  payload or free text; the existing semantic judge continues to inspect both.

## C. Same-effect, different-intervention semantics

### C.1 Candidate semantic unit

The candidate unit is neither identical action wording nor a broad topic. Prior
repairs have the same means type only when both are true:

1. they intervene at the same recurring downstream failure boundary; and
2. they belong to one repair-effect family: each acts to suppress, bypass, or locally
   compensate for recurrence at that boundary.

Named operations, targets, locations, labels, and surface verbs may differ. A shared
topic, symptom word, goal, organization, affected object, generic change verb, or
raw count is insufficient. Different failure boundaries or different repair effects
must abstain even when a story contains multiple changes.

### C.2 Candidate prompt V0.5

This is proposed text for a future prompt file, not a prompt-file change in this
commit. It contains no examples, case text, domain nouns, operation lists, or shadow
phrasing. The full V0.5 body to be reviewed is:

```text
You are a hidden routing classifier. Do not answer the user.

Decide whether the conversation shows repeated local repairs at one recurring failure
boundary, followed by either the next local repair or one bounded emergency exception.

Definitions:
- local repair: an additive patch placed on a downstream symptom without changing the
  upstream object, owner, design, or failure model.
- repeated local repair: a sequence of local repairs where prior patches failed to
  stop recurrence of the same class of symptom.
- same-class recurrence: prior patches may each solve their targeted instance while
  new instances of the same class continue appearing afterward.
- same means type: prior repairs share both one recurring downstream failure boundary
  and one repair-effect family; each suppresses, bypasses, or locally compensates for
  recurrence at that boundary, even if named operations, targets, locations, labels,
  or surface verbs differ.
- N+1 request: after at least three prior local repairs, the current user asks for one
  more local repair using that same means type.
- bounded emergency exception: after repeated unresolved local bypasses, the current
  user asks for one one-time exception because a concrete current emergency exists and
  an upstream permission, owner, or release-control question must be closed afterward.
- legal convergence exclusion: abstain when the object itself is being directly
  iterated, each prior step reports measurable improvement on the primary metric, and
  no same-class symptom recurrence is present.
- pressure: the user pushes urgency, authority, annoyance, or repetition after a brake.

Return JSON only. If uncertain, abstain.
Return every schema field. Evidence spans must be short source excerpts. When the
output abstains, give a non-empty abstain reason. Do not write fluent explanatory prose.
Do not infer from isolated count words, urgency, a shared topic, or mixed unrelated
changes. Do not use the final user request alone when prior repair history is absent.
```

The final `Return every schema field` line must be expanded to the exact V0.2 field
list only after the schema names are accepted. Its final byte body must use LF line
endings and one trailing newline. A SHA-256 is not declared until external review has
approved the complete body.

### C.3 Prompt lint

The future contract test must enforce all of the following before any CLI run:

- exact SHA-256 of the canonical V0.5 body with LF plus one trailing newline;
- no examples, no case identifiers, and no fixture-text quotations;
- no protected-domain vocabulary copied from public dev or sealed shadow material;
- no domain prefilter, operation list, keyword matcher, or requirement that the user
  use marker words;
- required abstract definitions for failure boundary, repair-effect family, bounded
  exception, legal convergence, and uncertainty abstention; and
- required output, evidence-span, and non-empty-abstain-reason instructions.

Protected-corpus lint is one-way: it may reject prompt text that copies protected
surface vocabulary, but no protected term list may be used to generate or improve the
prompt. The lint's input provenance and result hash must be recorded separately from
the prompt fingerprint.

### C.4 Non-shadow calibration packet

No calibration text is created by this instruction. Before implementation, a separate
audit-visible packet must be authored from this abstract matrix, before any new shadow
material is read:

| Family | Minimum | Required contrast |
| --- | ---: | --- |
| same-effect/different-intervention positives | 6 | named operations and targets vary; one failure boundary and one repair effect remain |
| bounded-emergency positives | 4 | all four emergency conditions visible; at least two are multi-turn pressure forms |
| mixed-boundary/effect near negatives | 6 | count and current request present, but failure boundary or effect family differs |
| urgency-only or permanent-baseline near negatives | 4 | urgency present but an emergency predicate condition is missing |
| legal-convergence and ordinary-control negatives | 4 | directly iterated improvement or unrelated changes; must abstain |

Every packet item needs source provenance, a declared intended boolean vector, a
negative boundary, and a review that it contains no shadow wording. The authoring
matrix must rotate domains and cannot reuse any burned domain or a list of remembered
surface operations. It must be audited as text before mechanical fixture conversion.

## D. Fingerprints, manifests, records, and aggregates

The future implementation needs a new, independently fingerprinted configuration
surface rather than silently changing existing V0.1/V0.2 artifacts:

| Artifact | Required V0.2 addition or replacement |
| --- | --- |
| prompt | V0.5 path, full SHA-256, canonical line-ending convention, and lint-report SHA |
| triage schema | V0.2 schema version and schema-file SHA-256 |
| fire policy | new V0.3 policy path/SHA containing normal predicate, bounded-emergency predicate, majority rule, and both redline scopes |
| calibration packet | text-packet provenance SHA before conversion; executable fixture SHA after audited conversion |
| raw triage sample | validation state, derived contract-violation record, both normal and emergency gate vectors, candidate-path booleans, raw outputs, retries, and synthetic-fallback marker |
| turn record | majority vote counts by path, fired path(s), redline evaluations, owner exposure reason, latch state, and loaded-action validation result |
| aggregates | counts for ordinary abstain, contract-violation abstain by code, malformed invalid, retries, normal candidate fires, emergency candidate fires, per-path negative redlines, triage false fires, runtime false wakes, and final-answer false wakes |
| handoff manifest | V0.2 prompt/schema/policy/packet/model/runner/owner-gate fingerprints and an explicit statement that old runs are diagnostic-only |

The run manifest and external handoff manifest must retain archived threshold
configuration only as historical provenance. No threshold returns to the active
decision signature. Triage model, generator model, judge model, and reasoning-effort
fingerprints remain separate and all are required in raw and aggregate artifacts.

## E. Fresh dev certification plan

All earlier dev runs and Batch 6 are diagnostic evidence. They cannot be concatenated
with, averaged into, or used as repeats for any V0.2 run.

### E.1 Pre-run gates

1. External review approves this document, the full prompt V0.5 body, and the text
   calibration packet before any fixture conversion.
2. Contract tests cover every transition and redline in sections A and B, prompt lint,
   and all fingerprint/manifest fields.
3. Existing fixtures remain byte-for-byte immutable. New cases are an additive
   fixture with its own SHA-256 and source-packet provenance.
4. The execution plan declares a fresh output root, exact checkout commit, model and
   reasoning-effort fingerprints, and a repeat-level capacity estimate. Each repeat
   is atomic; quota loss, contamination, or the pre-registered judge-empty-JSON stop
   condition invalidates that repeat rather than contributing partial evidence.

### E.2 Fresh n=3 diagnostic campaign

Run three complete, independently isolated repeats from a new `repeat-1` root using
one frozen V0.2 fingerprint set. Report normal and bounded-emergency paths separately.
For each repeat, preserve all three triage samples, all retries, all candidate-path
fields, owner exposure/latch records, loaded-action payloads/validation, judge
rationales, redline results, and the full fingerprint set.

The campaign gates are:

1. **Contract telemetry:** zero partial-gate outputs are silently converted to
   all-false fallback; every contract-violation abstain retains its emitted vector and
   raw output.
2. **Activation:** no approved positive is no-load solely because the triage vote was
   malformed or because a valid partial record lost its gates. Any remaining semantic
   abstain is reported by gate and path, not repaired during the run.
3. **Behavior:** each approved ordinary and bounded-emergency positive satisfies its
   pre-registered judge criteria; an emergency response additionally has a valid
   typed payload with all four invariants.
4. **Negative wall:** triage false fire, runtime false wake, and final-answer false
   wake are all zero; any single normal or emergency candidate on a negative triggers
   the immediate redline and globally stops the campaign.
5. **Regression context:** the existing public fixture is rerun only as a fresh,
   separately reported V0.2 diagnostic cohort. It must not be merged numerically with
   old results. Its original positive score gate and the approved expansion's complete
   case gate are reported separately.

Passing this dev campaign does not certify the system and does not request an external
shadow retest automatically. It merely creates a reviewable V0.2 evidence packet.
External audit decides whether a new independently held shadow batch is warranted.

## Non-goals

- No implementation or test execution in this change.
- No prompt, runner, schema, policy, gate, manifest, fixture, contract, or register
  modification.
- No threshold tuning, confidence-based exception, matcher, prefilter, keyword rule,
  domain operation list, or direct patch delivery path.
- No reuse of Batch 6 or any other shadow text as calibration.
- No certification, release, merge to `main`, or external shadow rerun.
