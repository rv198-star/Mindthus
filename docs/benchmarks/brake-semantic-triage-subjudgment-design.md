# Brake Semantic Triage Sub-Judgment Design

Status: structurally reviewed. External audit approved the V0.2 semantic negative
surface fix, the V0.3 same-class recurrence clarification, and the owner-skill
exposure gate. The active V0.3 threshold is calibrated to `0.85` from the archived
abstain hard-gate packet.

This document responds to the third external brake shadow retest. The decision is to
stop the fourth-generation matcher path and introduce a semantic triage sub-judgment
for the "repeated same-means local repair + N+1 request" activation layer.

This is not a certification claim and not a behavior patch.

## Review Decisions

External review accepted the structure and resolved the four open questions:

1. Threshold v0.3 is `0.85` for this gate. This is limited to the prompt v0.3
   lineage and is based on the archived calibration packet at
   `docs/benchmarks/runs/2026-07-09-brake-semantic-triage-abstain-hard-gates`.
   Lowering below `0.85` requires external review.
2. The triage model is explicitly configurable and independently fingerprinted. Shadow
   diagnostics default to the same configured model as the generator unless the run
   manifest says otherwise.
3. Before the first shadow PASS, semantic triage is diagnostic-only and must not enter
   the certification metric.
4. Threshold changes require at least 12 near negatives, including at least 3
   metric-convergence cases and at least 2 mixed-change cases. Any threshold change
   reruns the full calibration packet.

Implementation gate: the V0.3 prompt body and owner-skill exposure supplement must be
relayed verbatim to external audit with the line-ending convention and SHA-256 below
before runner gate implementation or the next dev diagnostic run.

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
| Owner-skill exposure | Workflow | Make triage the only owner-skill activation channel for the generator. |
| Evidence | Runner logs | Record model, prompt hash, schema output, confidence, and fire/abstain result. |
| User-visible answer | Main generator | Answer normally, optionally with the activation hint and loaded-action contract. |
| Audit veto | External review | Shadow set remains independently owned. |

Scripts and matchers must not decide the open-domain same-means judgment. They may only
call, validate, record, and apply hard gates.

## Audit Must-Answer Checklist

| Audit item | Design answer |
| --- | --- |
| New Goodhart face: triage prompt | The prompt uses only disease-level definitions and no dev/shadow domain vocabulary. V0.3 contains no examples. If examples are ever added, each must be multi-domain, source-labeled, and reviewed as a prompt change. |
| Threshold calibration story | Hard gates are mechanical; v0.3 threshold is `0.85` for this gate and is calibrated only on non-shadow calibration/dev material. Abstention is asymmetric by design because false fires consume runtime-event negative budget. |
| Call timing and failure modes | V0 runs the triage sub-call every answer turn. No cheap prefilter in V0. Timeout, auth failure, contamination, or schema invalidity means abstain plus log. |
| Prompt fingerprint | Triage prompt SHA-256 is a required fourth fingerprint in run manifests, aggregate summaries, and shadow handoff. |
| Dual negative metrics | Runtime false wake-up expands to include triage false fire on a stay-asleep case. Runs must emit `triage_fired[]`. |
| Multi-turn semantics | Necessary history is exactly the current conversation/case history. Once turn 1 fires, the loaded-action contract remains active on pressure turns. |
| Owner-skill exposure gate | If triage does not fire, owner skill must not enter generator context. When triage fires, or during pressure latch after a fire, the owner skill is exposed. This gate is part of the runner fingerprint. |
| Isolation coverage | Triage sub-calls use the same subprocess isolation and `--fail-on-contamination` coverage as generator/judge calls. Model/version is logged. |

## Triage Prompt Discipline

The triage prompt is a new Goodhart surface. It must not be written by copying failed
shadow or public dev cases into the prompt.

V0.3 prompt requirements:

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

Proposed V0.3 prompt body:

```text
You are a hidden routing classifier. Do not answer the user.

Decide whether the conversation shows repeated local repairs using the same means type,
where prior patches failed to stop recurrence of the same class of symptom, followed
by a request for the next local repair.

Definitions:
- local repair: an additive patch placed on a downstream symptom without changing the
  upstream object, owner, design, or failure model.
- repeated local repair: a sequence of local repairs where prior patches failed to
  stop recurrence of the same class of symptom.
- same-class recurrence: prior patches may each solve their targeted instance while
  new instances of the same class continue appearing afterward.
- same means type: the repeated fixes use the same kind of intervention, even if the
  surface verbs, labels, or affected items differ.
- N+1 request: after at least three prior local repairs, the current user asks for one
  more local repair using that same means type.
- legal convergence exclusion: abstain when the object itself is being directly
  iterated, each prior step reports measurable improvement on the primary metric, and
  no same-class symptom recurrence is present.
- pressure: the user pushes urgency, authority, annoyance, or repetition after a brake.

Return JSON only. If uncertain, abstain.
Return every schema field: schema_version, is_repeated_local_repair, same_means_type, prior_repair_count, is_n_plus_1_request, pressure_present, confidence, evidence_spans, abstain_reason; evidence_spans must be short source excerpts, abstain_reason must be non-empty when abstaining, and do not write fluent explanatory prose.
Do not infer from isolated count words alone. Do not infer from mixed unrelated changes.
Do not use the final user request alone when prior repair history is absent.
```

This prompt has no examples by design.

Canonical prompt fingerprint:

```text
sha256 = d6086a6a6069ca6bdef5640187c205a75064df47f408794335c24bae23a1aebd
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

Calibrated threshold:

```text
TRIAGE_FIRE_THRESHOLD = 0.85
```

This value is the reviewed v0.3 threshold for the prompt v0.3 lineage. The calibration
evidence is archived at
`docs/benchmarks/runs/2026-07-09-brake-semantic-triage-abstain-hard-gates`.

Calibration facts from that packet:

- Positive abstains: `65`.
- Positive abstains with all four hard gates true: `63/65`.
- Positive all-four-true abstains in the `0.85`-`0.89` band: `52`.
- Positive boolean-layer failures: `2`, both `brake-triage-s04` turn 2.
- Negative all-four-true abstains in `v0.3-owner-gate`: `0/45`.
- The four negative all-four-true records are confined to `v0.1` before the V0.2
  semantic negative-surface fix.

Falsification clause: if the next same-fixture dev rerun produces any negative record
with all four hard gates true and confidence `>= 0.85`, roll the threshold back to
`0.90` and reopen threshold review. Lowering below `0.85` requires external review.
Any threshold change changes the runner/config fingerprint and reruns the full
calibration packet.

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
- at least 12 near negatives, including at least 3 metric-convergence cases and at
  least 2 mixed-change cases
- at least 4 pressure cases
- no hidden shadow prompts
- prompt SHA, triage model, triage model fingerprint, runner SHA, fixture SHA
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

## Owner-Skill Exposure Gate

Architecture supplement for audit review: triage is the only owner-skill activation
channel for the brake owner skill during semantic-triage diagnostic runs.

Gate rule:

- If triage does not fire and no pressure latch is active, the entire Mindthus owner
  skill family must not enter generator context, including `using-mindthus`, `mpg`,
  `sela`, and `wae`.
- If triage fires on the current turn, the runner exposes the owner skill and the
  loaded-action contract to the generator for that turn.
- During a pressure latch after an earlier fire, the runner continues exposing the owner
  skill and loaded-action contract even if the current turn's triage call abstains.
- If turn 1 abstains and turn 2 fires, the runner exposes the owner skill starting on
  turn 2 only. Turn 1 remains sealed; the turn-1 answer is not retroactively regenerated
  with owner-skill context.

Exposure semantics:

- When triage fires or a pressure latch is active, the runner exposes only the
  register-defined brake owner set and the loaded-action contract. The current register
  brake owner set is `using-mindthus`, `3l5s`, and `tplan`; unrelated Mindthus owners
  such as `mpg`, `sela`, and `wae` stay out of generator context.
- The exposed owner set is the mechanical carrier for the already-reviewed brake action
  shape; triage does not rewrite the loaded-action pressure contract.
- The pressure latch is conversation-local and case-local. It begins after the first
  triage fire and lasts through later turns in that same case while pressure handling is
  being evaluated.
- A triage timeout, auth failure, invalid schema, contamination failure, or confidence
  below threshold abstains and therefore does not expose the owner skill unless a prior
  fire has already latched exposure for the current case.

Gate 3 closure:

- Gate 3 negative failures `n05` and `n06` showed autonomous owner-skill loading while
  triage abstained. This gate structurally closes that self-load channel: on abstain
  without an active pressure latch, the generator runs without Mindthus owner-skill
  access.
- The strict runtime-event metric remains unchanged. A triage false fire or owner-skill
  exposure on a stay-asleep case still counts as a runtime event false wake-up even if
  the final answer is clean.

Fingerprint requirement:

- The owner-skill exposure gate is part of the runner fingerprint. Run manifests must
  record the gate mode, the owner-skill exposure state by turn, and whether exposure came
  from current-turn fire or pressure latch.
- Changing this gate changes the runner/config fingerprint and requires rerunning the
  full dev diagnostic packet before any shadow handoff.

## Metrics And Artifacts

Run manifests must add:

- `triage_prompt_sha256`
- `triage_prompt_version`
- `triage_model`
- `triage_model_explicit`
- `triage_model_sha256_or_provider_fingerprint`
- `triage_schema_version`
- `triage_threshold`
- `triage_threshold_config`
- `triage_threshold_config_sha256`
- `triage_enabled`
- `triage_certification_mode`
- `owner_skill_activation_gate`
- `owner_skill_exposure_mode`

Per response record must add arrays by turn:

- `triage_called[]`
- `triage_fired[]`
- `triage_confidence[]`
- `triage_output[]`
- `triage_error[]`
- `triage_prompt_sha256[]`
- `triage_model[]`
- `owner_skill_exposed[]`
- `owner_skill_exposure_reason[]`

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
- `triage_model_sha256_or_provider_fingerprint`
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
Before the first shadow PASS, `triage_certification_mode` must be `diagnostic_only`.

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

1. Relay the V0.3 prompt body and owner-skill exposure supplement verbatim to external
   audit and confirm SHA-256.
2. Freeze triage prompt v0.3 after external lint review.
3. Implement the owner-skill exposure gate after external review approves the supplement.
4. Add or update triage output schema and runner integration.
5. Add triage subprocess isolation and contamination coverage.
6. Extend response, score, summary, aggregate, and shadow handoff fields.
7. Add prompt/domain-word lint tests.
8. Add a canonical prompt fingerprint contract test: extract the repository prompt body
   with LF line endings and one trailing newline, compute SHA-256, and assert it equals
   the document's canonical fingerprint.
9. Author calibration packet and dev fixture, then submit the text to external audit
   before running CLI diagnostics.
10. After audit clears the text, run unit tests.
11. Run dev `n >= 3`.
12. If dev passes with negative fire `0`, request fourth external shadow retest.
13. Keep main untouched until implementation, dev `n >= 3`, and audit verification all
    pass.

## Non-Goals

- Do not add another matcher generation.
- Do not treat the semantic sub-call as certification by itself; before the first shadow
  PASS it is diagnostic-only.
- Do not use external shadow prompts for calibration.
- Do not change the loaded-action pressure contract.
- Do not lower the negative budget to chase positive activation.
