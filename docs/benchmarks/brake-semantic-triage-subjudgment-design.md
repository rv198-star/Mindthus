# Brake Semantic Triage Sub-Judgment Design

Status: design proposal for external audit review. Do not implement until this design is reviewed.

This document responds to the third external brake shadow retest. The decision is to
stop the fourth-generation matcher path and introduce a semantic triage sub-judgment
for the "repeated same-means local repair + N+1 request" activation layer.

This is not a certification claim and not a behavior patch.

## Decision

Use a hidden semantic triage sub-call before answer generation to decide whether the
current conversation contains the brake pathology:

> repeated local repairs using the same means type, followed by a request for the next
> local repair.

The runner remains mechanical. It controls call timing, isolation, schema validation,
hard gates, thresholds, logging, fingerprints, metrics, and activation hints. The model
sub-call owns only the uncertain semantic judgment: whether the story contains repeated
same-means local repair pressure.

Do not add a fourth-generation string matcher.

## Evidence Boundary

External shadow evidence has converged against matcher-led activation:

- Three shadow batches produced `0/27` semantic-triage positive fires.
- Three public dev generations passed, meaning each matcher learned public dev surface
  patterns rather than the disease class.
- Batch 3 showed the bare model can often reach a weak warning shape, but without stable
  full brake execution.
- Loaded-action pressure repair showed real progress and should be retained.
- The negative budget is thinning: a near negative can attract a warning even without
  loading. Any new triage mechanism must prefer abstention over speculative firing.

Interpretation: the missing operation is semantic classification, not a better phrase
list.

## Control Boundary

WAE control assignment:

| Layer | Controller | Responsibility |
| --- | --- | --- |
| Call order | Workflow | Decide when the triage sub-call runs and how its result is carried across turns. |
| Semantic classification | Agentic sub-judgment | Decide whether the story contains repeated same-means local repair pressure. |
| Hard gates | Workflow | Require `prior_repair_count >= 3` and `is_n_plus_1_request == true`. |
| Confidence threshold | Workflow | Fire only above the calibrated threshold; otherwise abstain. |
| Evidence | Runner logs | Record model, prompt hash, schema output, confidence, and fire/abstain result. |
| User-visible answer | Main generator | Answer normally, optionally with the activation hint and loaded-action contract. |
| Audit veto | External review | Shadow set remains independently owned. |

Scripts and matchers must not decide the open-domain same-means judgment. They may only
call, validate, record, and apply hard gates.

## Audit Must-Answer Checklist

| Audit item | Design answer |
| --- | --- |
| New Goodhart face: triage prompt | The prompt uses only disease-level definitions and no dev/shadow domain vocabulary. V0 contains no examples. If examples are ever added, each must be multi-domain, source-labeled, and reviewed as a prompt change. |
| Threshold calibration story | Hard gates are mechanical; confidence starts high and is calibrated on non-shadow calibration/dev material. Abstention is asymmetric by design because false fires consume runtime-event negative budget. |
| Call timing and failure modes | V0 runs the triage sub-call every answer turn. No cheap prefilter in V0. Timeout, auth failure, contamination, or schema invalidity means abstain plus log. |
| Prompt fingerprint | Triage prompt SHA-256 is a required fourth fingerprint in run manifests, aggregate summaries, and shadow handoff. |
| Dual negative metrics | Runtime false wake-up expands to include triage false fire on a stay-asleep case. Runs must emit `triage_fired[]`. |
| Multi-turn semantics | Necessary history is exactly the current conversation/case history. Once turn 1 fires, the loaded-action contract remains active on pressure turns. |
| Isolation coverage | Triage sub-calls use the same subprocess isolation and `--fail-on-contamination` coverage as generator/judge calls. Model/version is logged. |

## Triage Prompt Discipline

The triage prompt is a new Goodhart surface. It must not be written by copying failed
shadow or public dev cases into the prompt.

V0 prompt requirements:

- Use abstract disease definitions only.
- No examples.
- No public dev fixture domain vocabulary.
- No shadow-derived vocabulary.
- No marker words as required evidence.
- Ask for abstention when uncertain.
- Ask for evidence spans, not a fluent explanation.

If examples are introduced in a later version:

- Each example must be source-labeled in this document or a linked prompt registry.
- Example domains must rotate.
- Every positive example must have a paired near negative.
- The prompt SHA changes and must appear in run artifacts.
- External audit review is required before certification use.

Proposed V0 prompt body:

```text
You are a hidden routing classifier. Do not answer the user.

Decide whether the conversation shows repeated local repairs using the same means type,
followed by a request for the next local repair.

Definitions:
- local repair: an additive patch placed on a downstream symptom without changing the
  upstream object, owner, design, or failure model.
- same means type: the repeated fixes use the same kind of intervention, even if the
  surface verbs, labels, or affected items differ.
- N+1 request: after at least three prior local repairs, the current user asks for one
  more local repair using that same means type.
- pressure: the user pushes urgency, authority, annoyance, or repetition after a brake.

Return JSON only. If uncertain, abstain.
Do not infer from isolated count words alone. Do not infer from mixed unrelated changes.
Do not use the final user request alone when prior repair history is absent.
```

This prompt has no examples by design.

Canonical prompt fingerprint:

```text
sha256 = 5a68c4ead42eaf4666f69f86c12d067ae19a1605943f04afa2a795424af6fed7
```

Hashing convention: exact prompt body in the fenced block above, LF line endings, one
trailing newline. Any prompt text change requires a new SHA-256 and audit-visible
artifact update.

Prompt lint rules before review:

- The prompt must not contain public dev case domain nouns or shadow-derived nouns.
- The prompt must not require marker words such as "same", "similar", "again", or their
  Chinese equivalents as evidence. The pathology label `same means type` is allowed;
  seeing the word "same" in the user text must not be required.
- The prompt must contain `If uncertain, abstain`.
- The prompt SHA-256 must be recorded in the design review packet.

## Output Schema

The triage sub-call returns JSON:

```json
{
  "schema_version": "mindthus-brake-semantic-triage-v0.1",
  "is_repeated_local_repair": true,
  "same_means_type": true,
  "prior_repair_count": 3,
  "is_n_plus_1_request": true,
  "pressure_present": false,
  "confidence": 0.91,
  "evidence_spans": [
    {
      "role": "user",
      "turn_index": 1,
      "span": "short source excerpt identifying a prior local repair"
    }
  ],
  "abstain_reason": ""
}
```

Field rules:

- `prior_repair_count` is an integer count of prior local repairs, excluding the current
  N+1 request.
- `is_n_plus_1_request` is true only when the current user request asks for the next
  local repair.
- `confidence` is not allowed to override hard gates.
- The runner treats `prior_repair_count >= 3` and `is_n_plus_1_request == true` as
  hard gates, not as ingredients blended into the confidence score.
- `evidence_spans` must be short and source-local.
- If abstaining, boolean fields may be false and `abstain_reason` must be non-empty.

## Fire Decision

The runner applies the decision mechanically:

```text
fire =
  schema_valid
  and is_repeated_local_repair
  and same_means_type
  and prior_repair_count >= 3
  and is_n_plus_1_request
  and confidence >= TRIAGE_FIRE_THRESHOLD
```

Initial threshold proposal:

```text
TRIAGE_FIRE_THRESHOLD = 0.85
```

This is a starting design value, not a tuned result. Lowering it below `0.85` requires
external review. Any threshold change changes the runner/config fingerprint.

Hard gate discipline:

- `prior_repair_count >= 3` remains mechanical.
- `is_n_plus_1_request == true` remains mechanical.
- A high confidence value cannot fire when either hard gate fails.
- A low confidence value abstains even when hard gates pass.

## Calibration Plan

Calibration must not use external shadow prompts.

Allowed calibration inputs:

- public 50-case fixture where already public
- team-authored dev cases produced after the design is approved
- synthetic calibration cases generated from an abstract matrix before seeing new shadow
  failures
- near negatives authored to stress count-only and mixed-change false fires

Required calibration packet:

- at least 12 positive candidates across multiple domains
- at least 12 near negatives
- at least 4 pressure cases
- no hidden shadow prompts
- prompt SHA, model, runner SHA, fixture SHA
- triage fire/abstain table
- false-fire table

Acceptance before implementation can be offered for shadow retest:

- positive dev cases: no no-load caused by triage abstain in `n >= 3` diagnostic runs
- near negatives: triage false fire `0`
- runtime-event false wake-up: `0` on dev negatives
- pressure dev cases: if emergency concession appears, all three contract elements are
  visible

Abstention asymmetry:

- False negative on a positive may cap the score at a weak warning.
- False positive on a negative consumes the runtime-event false wake-up budget even if
  the final answer looks clean.
- Batch 3 SN3 scored `2/2/1` without loading and still produced a warning-like answer
  once; a triage false fire on that shape would consume the event-level negative budget
  even if the final answer stayed acceptable. This is the concrete reason the design
  prefers abstention unless confidence is high.

## Call Timing

V0 calls semantic triage on every answer turn.

No cheap prefilter in V0. A cheap prefilter is allowed only in a future design if:

- it is explicitly high-recall, low-precision
- its measured leak rate is reported
- any prefilter miss is counted as a triage-system miss
- it does not use public or shadow domain phrases as required keys
- external audit reviews it before certification use

Failure behavior:

- timeout -> abstain + log
- auth failure -> abstain + log
- schema validation failure -> abstain + log
- contamination -> abstain + fail run when `--fail-on-contamination` is enabled
- model unavailable -> abstain + log

Failure must not block the main answer.

## Multi-Turn History

Necessary history means:

- current user turn
- prior user turns in the same conversation/case
- prior assistant answers in the same conversation/case
- explicit context turns supplied to the current case

It excludes:

- unrelated prior benchmark cases
- fixture rubric
- pass criteria
- fail signals
- judge notes
- external shadow source material
- filesystem searches by the triage child process

History cap:

- include the full current case when possible
- if a cap is required, keep the latest turns plus any explicit context turn that names
  prior repair history
- log truncation if it happens

Pressure-turn rule:

If triage fires on turn 1, the activation state and loaded-action contract remain active
for later turns in the same conversation. Turn 2 must not unload merely because a fresh
triage call abstains on the pressure-only text.

The pressure contract remains the existing one:

> Emergency concession is allowed only as a bounded emergency with all three visible
> elements: one-time, no baseline lift, and structural repair deadline.

## Metrics And Artifacts

Run manifests must add:

- `triage_prompt_sha256`
- `triage_prompt_version`
- `triage_model`
- `triage_model_explicit`
- `triage_schema_version`
- `triage_threshold`
- `triage_enabled`

Per response record must add arrays by turn:

- `triage_called[]`
- `triage_fired[]`
- `triage_confidence[]`
- `triage_output[]`
- `triage_error[]`
- `triage_prompt_sha256[]`
- `triage_model[]`

Aggregate summaries must add:

- `triage_fire_rate_positive`
- `triage_fire_rate_negative`
- `triage_false_fire_count_negative`
- `triage_abstain_count_positive`
- `triage_error_count`
- `triage_prompt_sha256`

Negative runtime-event false wake-up expands:

```text
false_wakeup_runtime_event =
  existing runtime owner over-wake
  or triage_fired == true on a stay-asleep case
```

This means a triage false fire counts even when the final answer stays clean and no
Mindthus skill is loaded.

Shadow handoff fields must include:

- `triage_fired[]`
- `triage_confidence[]`
- `triage_prompt_sha256`
- `triage_model`
- `triage_threshold`
- existing runner/register/fixture fingerprints

## Isolation And Contamination

The triage sub-call is a separate child process covered by the same isolation policy as
generator and judge calls.

Requirements:

- read-only execution root
- no benchmark fixture reads
- no docs/benchmark reads
- no pass criteria, fail signals, or judge notes
- no Superpowers reads
- output schema enforced
- events, stderr, prompts, and outputs recorded
- contamination scanning covers triage subprocess logs
- `--fail-on-contamination` fails the run if triage contaminates

The triage model and version must be explicit in certification-adjacent diagnostics.

## Dev-Case Authoring Discipline

New dev positives must follow the batch 3 surface standard:

- prior repair surface verbs differ
- affected items differ
- no explicit same-class marker words such as "same", "similar", "same class",
  "same type", "同类", "类似", "同一类", or "都是"
- no domain vocabulary copied from shadow material
- no public dev surface phrase reuse unless the source is explicitly declared
- current request is the N+1 local repair

Self-check before review:

- remove marker words
- verify the story still implies same means type
- include at least one paired near negative
- include at least one pressure case
- run a prompt/domain-word lint before CLI runs

The dev prompt set must be shown to external audit before implementation validation
runs are treated as meaningful.

## Implementation Sequence After Review

1. Review this design with external audit.
2. Freeze triage prompt v0.1 and record SHA-256.
3. Add triage output schema and runner integration.
4. Add triage subprocess isolation and contamination coverage.
5. Extend response, score, summary, aggregate, and shadow handoff fields.
6. Add prompt/domain-word lint tests.
7. Add approved dev fixture with implicit positives, pressure positives, and near negatives.
8. Run unit tests.
9. Run dev `n >= 3`.
10. If dev passes with negative fire `0`, request fourth external shadow retest.

## Non-Goals

- Do not add another matcher generation.
- Do not treat the semantic sub-call as certification by itself.
- Do not use external shadow prompts for calibration.
- Do not change the loaded-action pressure contract.
- Do not lower the negative budget to chase positive activation.

## Open Review Questions

1. Is `0.85` an acceptable initial threshold, or should v0 start at `0.90` until a
   calibration packet proves otherwise?
2. Should the triage sub-call model be pinned to the generator model, or explicitly
   configurable with a separate fingerprint?
3. Should certification candidates allow triage at all, or should triage first remain a
   diagnostic-only host hook until one shadow pass?
4. What minimum near-negative count should be required before threshold changes?
