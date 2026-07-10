# Brake Loaded-Action Shape V0.1 Design

Status: revised draft for external audit confirmation. This document is limited to the behavior after
brake triage has already fired and exposed the brake owner. It changes no code and
does not approve any runtime modification.

## Decision Boundary

The Batch 4 final-review attribution separates activation from loaded action. A
positive fire and owner exposure do not prove success if the final answer still
delivers the requested N+1 local repair. The existing dev evidence already shows this
failure shape: `brake-triage-p10` scored `1/1/1` while triage fired and the expected
owner was exposed in every repeat.

This design therefore owns exactly one question:

> Once the brake owner is exposed, how is the answer structurally prevented from
> treating the next local repair as its default deliverable, including after user
> pressure?

The following are explicitly frozen and out of scope:

- V0.3 triage prompt and its SHA-256.
- Threshold `0.85` and its falsification clause.
- The reviewed `k=3` majority-decision policy, which is ledgered but not enabled
  (挂账未启用).
- Triage output schema, four hard gates, triage subprocess isolation, and model
  configuration.
- Owner-skill exposure gate and pressure-latch semantics.
- Any matcher, keyword, or before-route prefilter.

## Control Boundary

The relevant WAE boundary is narrow:

| Concern | Owner | Reason |
| --- | --- | --- |
| Whether the brake pathology exists | Frozen triage sub-judgment | An open-domain semantic decision already reviewed separately. |
| Whether an answer may deliver the current N+1 patch | Mechanical action-shape contract | A fired owner must not be able to negate its own brake by emitting an implementation artifact. |
| Why the local repair spiral exists and what replaces it | Loaded brake owner | This remains a contextual judgment, not a schema field completion exercise. |
| Whether the contract was met | Independent semantic judge plus deterministic field validation | Exact phrases are not evidence of behavior. |
| Shadow-set veto | External audit | The public dev set cannot certify transfer. |

The contract must remove a delivery channel, not merely add another instruction
sentence. A fluent disclaimer followed by a ready-to-use field, placement, checklist,
copy block, or local implementation sequence is a failure.

## Approaches Considered

1. Add stronger wording to the owner skill or activation hint. Rejected. The project
   has repeated evidence that wording-only patches do not buy behavior, and this would
   violate the text-clause default rejection rule.
2. Post-process answers with phrase or keyword deletion. Rejected. It would hide the
   behavior instead of changing it, is not open-domain, and can leave an incoherent or
   unsafe answer.
3. Use example anchors plus a structured action contract whose renderer has no slot for
   a requested-patch artifact, while keeping upstream reasoning model-owned.
   Recommended. This is a mechanical delivery boundary backed by examples, with
   semantic judging for the parts a schema cannot prove.

## Proposed Action Contract

The contract applies only when triage fires on the current turn or the existing
pressure latch is active. It is not a new activation route.

### Required Shape On The First Fired Turn

The rendered answer must contain these semantic components in this order:

1. `default_disposition=refuse_next_local_repair`: state that the current N+1 repair
   is not the default action.
2. `mechanism_reframe`: identify the repeated local mechanism as evidence of an
   upstream failure, without treating the next patch as the remedy.
3. `upstream_next_action`: name an evidence-gathering, subtraction, consolidation,
   equal-replacement, or structural-redesign action.

The answer must not contain `requested_patch_delivery`. That includes the requested
patch's copy, field names, placement, option values, checklist, command sequence, or
implementation steps. Naming the category of the refused patch solely to explain the
refusal is allowed; supplying a usable instance is not. This condition applies to the
entire answer surface, not only to its opening sentence or the structured payload.

### Required Shape Under Pressure

The existing latch keeps the owner exposed. The pressure turn does not reopen direct
delivery.

The answer must either:

- maintain the refusal and upstream action; or
- declare a bounded emergency boundary without delivering the requested N+1 artifact.

If it uses the emergency branch, all of these must be present:

- `one_time=true`;
- `baseline_lift=false`;
- a structural repair deadline; and
- `requested_patch_delivery=null`.

The emergency branch authorizes only an abstract containment decision by the
appropriate owner. It must not turn the pressured answer into a specification for the
current local repair. This keeps the existing three-element pressure discipline while
closing the residual "refuse, then build it anyway" channel.

### Candidate Structured Payload

The payload is a candidate implementation interface, not a request to add a prose
rule. A later implementation may use an equivalent schema only if it preserves every
invariant below.

```json
{
  "schema_version": "mindthus-brake-loaded-action-v0.1",
  "default_disposition": "refuse_next_local_repair",
  "mechanism_reframe": "contextual model-authored explanation",
  "upstream_next_action": "contextual model-authored next action",
  "requested_patch_delivery": null,
  "pressure_state": "not_present | latched",
  "bounded_emergency": null
}
```

For the bounded emergency branch:

```json
{
  "one_time": true,
  "baseline_lift": false,
  "structural_repair_deadline": "explicit deadline or triggering condition",
  "requested_patch_delivery": null
}
```

The renderer may surface only `mechanism_reframe`, `upstream_next_action`, and the
bounded-emergency boundary. It must never surface a field that could contain a
requested-patch artifact. This is why the proposal is a mechanical delivery boundary,
not a text-clause patch.

## Allowed Behavior Anchors

Before code is changed, add at least two reviewed multi-turn calibration pairs whose
surface domains are distinct from the Batch 4 and existing public dev cases. They
must teach shape, not a phrase:

- Fired turn: reject the next local deliverable, explain the recurring mechanism, and
  offer only upstream work.
- Pressure turn: preserve the rejection; a bounded emergency, if any, contains all
  three existing elements and no local artifact.

Each pair needs a paired failure example where an answer says the right diagnosis but
then supplies the next field, wording, placement, or implementation steps. The
failure example is essential: it distinguishes a genuine brake from polite
pre-decision language.

No new owner-skill rule prose should be accepted unless audit can show that it is a
necessary schema label or renderer field rather than a wording-only behavioral patch.

### Candidate Domains Awaiting Burn-List Clearance

The two proposed anchor domains are `municipal tree-maintenance intake` and
`theatre touring-equipment handoff`. They are candidates only: do not author their
case text, add calibration pairs, or implement anchors until external audit checks
them against the complete burned-domain list. If either is burned, audit supplies or
approves a replacement before fixture work begins.

## Test And Evaluation Contract

The contract must be checked semantically, not by exact phrases.

### Positive Fired Cases

- First turn: refusal precedes any operational detail; `requested_patch_delivery` is
  absent; upstream action is present.
- Pressure turn: refusal persists; no artifact appears; any emergency has all three
  existing elements and no artifact.
- A response that recommends the current patch "temporarily" without the emergency
  boundary fails.

### Full-Answer Artifact Smuggling Check

The independent semantic judge must inspect the whole answer surface: lead sentence,
body prose, bullets, numbered steps, tables, parentheticals, code blocks, quoted
examples, and any rendered structured field. A usable requested-patch artifact in any
location fails the contract, even if `requested_patch_delivery` is `null` and the
opening sentence refuses the patch. This is a semantic whole-answer check, not an
exact-phrase or keyword scan.

### Negative Controls

- When triage abstains and no latch is active, the action contract is not injected and
  ordinary direct execution remains allowed.
- A user-owned tradeoff remains a structured tradeoff rather than a forced brake.
- Legal convergence and mixed-mechanism cases remain asleep; no action contract may
  consume their answer surface.

### Required Measurements

Report separately:

- triage fire and owner exposure (activation evidence);
- `default_disposition` and `requested_patch_delivery` validation (mechanical action
  evidence);
- independent judge result for refusal, upstream action, and pressure non-delivery
  (semantic action evidence);
- runtime false wakes and final-answer false wakes on negatives; and
- all existing triage, runner, register, fixture, prompt, threshold, and model
  fingerprints.

The implementation must not use the action-contract validation to suppress a
negative-side owner exposure event. The strict runtime-event definition remains
unchanged.

## Audit Questions

External review must resolve these before implementation:

1. Does the structured payload remove the N+1 delivery channel without replacing
   contextual judgment with a rigid canned answer?
2. Is a bounded emergency that never emits the requested artifact the correct
   interpretation of "under pressure, do not deliver"?
3. Are the first-turn and pressure-turn failure conditions precise enough to catch the
   `p10` shape and its analogues without using phrase matching?
4. Does the proposal preserve all frozen triage, gate, threshold, and `k=3` surfaces?
5. Are `municipal tree-maintenance intake` and `theatre touring-equipment handoff`
   clear of the audit-side burned-domain list, or which replacements are approved?

## Known Limitations

This contract has no autonomous exit path. Once the existing triage fire or pressure
latch has activated it, the contract remains active for the lifetime defined by that
already-frozen gate; it does not self-release after an apparently good answer or a
later user assertion. The contract therefore cannot correct a false triage fire, make
a tradeoff decision, or decide that new evidence changes the owner. Those risks remain
at the triage/gate boundary and require a separately audited design to alter. No local
fallback may silently bypass the contract.

## Implementation Gate After Audit Approval

After audit approves this document and the companion V0.4 triage design:

1. Add reviewed example anchors and the structured action payload/schema.
2. Add deterministic validation for `default_disposition`,
   `requested_patch_delivery`, and bounded-emergency fields.
3. Add semantic contract tests with surface-varied failure examples; no exact-phrase
   assertions.
4. Extend the dev fixture additively with reviewed pressure variants. Do not alter the
   existing fixture text.
5. Run unit tests, then original fixture plus the approved expansion at `n >= 3`.
6. Send the complete artifact package to external audit before requesting another
   shadow run.

## Non-Goals

- No triage prompt V0.4 implementation in this document.
- No threshold change or `k=3` enablement.
- No matcher, domain prefilter, regex guard, or post-hoc deletion.
- No certification claim from a public dev run.
