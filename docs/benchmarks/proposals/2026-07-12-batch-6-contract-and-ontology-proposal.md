# Proposal: preserve partial-gate telemetry and extend brake ontology coverage

Status: proposal only. Awaiting external audit. This document authorizes neither an
implementation nor any benchmark rerun.

## Decision boundary

Batch 6 established two separate defects in the brake route:

1. A mechanically valid, honest partial-gate triage assessment can be rejected as an
   invalid sample solely because its `abstain_reason` is empty.
2. The current ontology does not cover two structural shapes: an urgent request for
   one bounded exception after repeated bypasses, and a sequence of differently named
   repairs that have the same downstream effect on one recurring failure site.

The first defect distorts telemetry but fails closed: invalid samples cannot count as
fire votes. The second defect creates false negatives: the owner remains sealed and a
bare generator answer can accidentally satisfy a score rubric without demonstrating
the intended route.

This proposal owns only a future design for these two defects. It does not modify the
frozen prompt, fire policy, runner, schema, owner gate, pressure latch, action
contract, fixtures, scoring, or certification state.

## Evidence boundary

The evidence source is the sealed Batch 6 record at
`docs/benchmarks/runs/external-shadow-batch-6-20260712/`. Its fixture remains
evidence, not calibration material. This proposal deliberately uses only abstract
failure shapes; it does not quote, paraphrase into examples, or add vocabulary from
the shadow cases.

Observed facts behind this proposal:

- Repeated partial-gate outputs were JSON-valid and type-correct, but had an empty
  `abstain_reason`. The current validator accepts only all-four-gates fire or an
  abstain with a non-empty reason, so these outputs became invalid and their false
  hard-gate values were replaced by fallback values.
- One positive shape involved a real emergency plus a request to permit exactly one
  bounded exception after repeated bypasses. Its request was not represented as an
  N+1 local repair under the current ontology.
- Another positive shape used distinct named interventions with one downstream
  effect on a recurring failure site. The current `same_means_type` reading treated
  the named interventions as heterogeneous.

## A. Partial-gate telemetry contract

### Goal

Make every schema-valid partial-gate assessment observable as an abstain record, with
the individual hard-gate values preserved. Fire remains reserved for valid samples
where all four hard gates are true.

### Candidate contract

The future schema/validator contract should distinguish three states:

| State | Condition | Decision effect |
| --- | --- | --- |
| fire candidate | all four hard gates true and `abstain_reason` empty | eligible for a fire vote |
| explicit abstain | one or more hard gates false and `abstain_reason` non-empty | valid abstain; retain all gate values |
| malformed output | missing field, wrong type, unsupported schema version, invalid range, unexpected field, or contradictory state | invalid; retry once, then fallback abstain |

The specific repair candidate is to make a non-empty `abstain_reason` mandatory for
every partial-gate output, while preserving the emitted false gates and evidence
spans. A validator may normalize a schema-valid partial-gate output with an empty
reason into an abstain only if it records a distinct contract-violation field and
retains the original raw output. It must not rewrite the hard-gate values into an
all-false fallback.

### Required invariants

- A partial-gate sample is never a fire vote.
- A negative-control sample whose four gates are true remains the existing immediate
  redline; this proposal supplies no exception and no confidence-based waiver.
- Every valid abstain retains all four booleans, the original reason, evidence spans,
  sample index, retry history, and raw model output.
- A malformed sample remains invalid and follows the existing one-retry discipline.
- Aggregates must report valid-abstain, contract-violation abstain, and malformed
  invalid separately. They must not pool them into a generic error count.

### Tests required before any implementation approval

- A partially true, non-empty-reason output is accepted as an abstain and preserves
  its gate vector.
- An all-true, empty-reason output is a fire candidate.
- A partially true, empty-reason output follows the selected strict contract path and
  never becomes a fire or an all-false synthetic record.
- A negative all-true output still triggers the redline before any majority decision.
- Retry artifacts retain both attempts, including the original raw output.

## B. Bounded-emergency route

### Goal

Recognize the structural shape where a genuine emergency is used to request one
limited exception after a recurring local bypass pattern, without relabeling every
urgent request as a brake event.

### Candidate ontology

Introduce a future semantic distinction between:

- `next_local_repair_request`: another downstream patch of the same repair class;
  and
- `bounded_emergency_exception_request`: a request to make one explicitly limited
  exception to a repeated bypass pattern because a concrete emergency is active.

The second is not a relaxed version of N+1. It has its own necessary structural
conditions:

1. a real, current emergency constraint;
2. repeated earlier bypasses or local exceptions that left the governing risk
   unresolved;
3. a request for one exception, not a standing baseline change; and
4. an identifiable upstream permission, owner, or release-control question that must
   be closed after the exception.

The future fire predicate must be specified explicitly rather than inferred from this
proposal. One candidate is an auditable disjunction: the existing four-gate path, or
a separate bounded-emergency path with all of the above conditions. Both paths must
still feed the same negative redline and owner-exposure controls. No future route may
fire on urgency alone.

### Action-shape boundary

When this route fires, it may expose the existing loaded-action contract only for the
already-defined bounded-emergency response shape. That response requires an actually
bounded exception, no baseline lift, a stop/review condition, and upstream closure.
This proposal neither weakens those invariants nor decides how the typed payload
should change. The action-shape design remains its own owner.

### Tests required before any implementation approval

- Positive structural cases that contain a real emergency, a one-time request, an
  unresolved repeated bypass, and a post-exception closure requirement.
- Near negatives with urgency but no repeated bypass, repeated bypass but no genuine
  emergency, and an emergency request that seeks a permanent baseline change.
- A negative all-four-gates result remains a redline regardless of whether the new
  route is under consideration.
- The generator cannot treat route activation as permission to deliver an unbounded
  exception.

## C. Same-effect, different-intervention semantics

### Goal

Extend `same_means_type` beyond identical named operations without collapsing a
multi-change story into a single repair class merely because it shares a topic or a
symptom.

### Candidate definition

Future semantic triage should treat prior changes as the same means type when they
share both:

1. one recurring failure site or downstream control boundary; and
2. one repair-effect family: each change attempts to suppress, bypass, or locally
   compensate for that same failure at that same boundary.

The named operation, component, target, label, or placement may differ. A shared
topic, outcome, organization, generic change verb, or count of changes alone remains
insufficient.

This is deliberately stricter than a broad “same symptom” rule and broader than an
identical-operation rule. Its decision unit is the effect of the intervention at the
failure boundary, not the surface verb used to describe it.

### Guardrails

- Do not add a keyword matcher, domain prefilter, operation list, or marker-word
  requirement.
- Do not use the Batch 6 fixture as a prompt example or public calibration text.
- A sequence with genuinely different failure sites or different repair-effect
  families must abstain even if it contains three changes and a current request.
- Legal convergence remains excluded when the object itself is directly iterated,
  the primary metric improves each step, and no recurring failure class reappears.

### Tests required before any implementation approval

- Multi-domain positives with distinct surface operations that share one downstream
  failure boundary and one repair effect.
- Mixed-operation negatives that share a broad narrative but differ in failure site
  or repair effect.
- A mutation suite that swaps domains, targets, operation labels, and direction while
  holding the structural relation fixed.
- Negative cases that contain repeated count language but no shared repair effect.

## Evaluation and rollout gate

Before any code change, external audit must approve a separate implementation design
that pins:

1. exact schema/validator transition rules and whether the schema version changes;
2. the bounded-emergency fire predicate and interaction with the four-gate redline;
3. the same-effect semantic definition, prompt text, lint rules, and non-shadow
   calibration packet;
4. fingerprint, manifest, raw-record, and aggregate-field changes; and
5. a fresh dev certification plan. Existing dev and Batch 6 results are diagnostic
   evidence only and must not be pooled with any future run.

## Non-goals

- No implementation in this change.
- No prompt or fire-policy wording patch.
- No threshold change, majority-rule change, owner-gate change, or pressure-latch
  change.
- No repair rerun, diagnostic rerun, or certification inference.
- No new shadow fixture, no reuse of Batch 6 text as calibration, and no merge to
  `main`.
