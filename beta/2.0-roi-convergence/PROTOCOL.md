# Mindthus 2.x ROI-First Convergence Protocol

Status: `FROZEN_BEFORE_LIVE_CALLS` once the implementation commit and protocol digest
are recorded below. Until then this document is a draft and no live model sampling is
allowed.

Mission: `mindthus-2x-roi-convergence-20260719`

Source context only (no inherited success or authority):

- ROI.2 branch commit: `4ee3e034db6bf8d1e34002d7f162e2b008516490`.
- Stable 1.4.6 source commit: `00da11657bce553cb32e8e90c06ffe959dc08362`.
- ROI.2 final report and both original comparison JSON files remain byte-preserved
  under `beta/2.0-roi-thin-core/qualification/`.

Implementation commit: `TO_BE_LOCKED`

Protocol SHA-256: computed after replacing the implementation placeholder; the digest
is recorded in `LOCK.json`, not self-embedded here.

## Decision question

How much of Mindthus discovery can be removed on `gpt-5.6-sol / xhigh` while retaining
a product floor for explicit owner recall, passive cognitive primitives, and
decision-changing action quality?

This Mission does not optimize recall as a maximum. Recall is a constraint; measured
runtime ROI is the objective. A Skill miss is allowed only above the frozen floor and
only when the correct action does not change.

## Frozen baseline and target

The incumbent is the qualified unpublished ROI.2 candidate, not Stable 1.4.6. Stable
remains the recall-first product baseline but rerunning it cannot answer whether a new
route improves on ROI.2.

The common panel runs the incumbent and all three new routes under the same Codex CLI,
model, effort, prompt bytes, fresh isolated `CODEX_HOME`, and read-only workspace.
Exactly one Mindthus arm is enabled per call. Raw JSONL read commands are activation
evidence; final-answer self-report is not.

## Product floor

All conditions are hard gates for a route to compete on ROI:

1. **Explicit owner recall:** all three frozen owner cases must read the named correct
   owner in the same user turn: SELA, MPG, and WAE. This is 3/3 on the panel, not a
   universal population claim.
2. **Passive primitive recall:** at least two of the three frozen families must have a
   credible Mindthus Skill read: Frame/Whole, Decision Context, and Anti-Spiral. The
   denominator and 2/3 threshold do not change after sampling begins.
3. **Action quality:** every case must satisfy its action rubric. A missed activation is
   not harmless if it changes strategy, evidence requirement, authority handling, next
   action, or stopping condition.
4. **Near-negative control:** new evidence on the second incident pass must permit the
   causal schema correction; over-braking fails.
5. **Interaction:** no route may add a user-visible routing round or ask a question
   except the single blocking Decision Context question.
6. **Ordinary/evidence-first precision:** these two cases may read a thin entry but must
   not read a formal owner, invent evidence, or delay the requested answer.

An unrelated companion owner read is recorded as cost and owner-fidelity debt. It is a
quality failure only when it changes the action or violates the case boundary; it is
not automatically hidden by a binary gate.

## ROI objective

Primary metric: median host-reported `uncached_input_tokens` across the nine frozen
cases (`input_tokens - cached_input_tokens`; cached input is not added again).

Supporting metrics:

- median explicitly loaded Mindthus bytes across all nine cases;
- median uncached input tokens across the six hard-judgment cases (`frame_whole`,
  `decision_context`, `anti_spiral`, `clear_sela`, `clear_mpg`, `clear_wae`);
- wall duration, reported but never used alone to select a route;
- per-case activation paths so a median cannot conceal a catastrophic owner cascade.

A route is a distinguishable ROI improvement only when it passes the product floor and
reduces the primary median by at least 5% relative to the current incumbent. Smaller
differences are treated as host/model noise. Among distinguishable routes, select the
lowest primary median; use hard-judgment median, loaded bytes, then duration only as
ordered tie-breakers. Source byte counts never substitute for host token evidence.

## Three distinct routes

The three routes are architecture/responsibility hypotheses, not successive prompt
patches. ROI.2 does not count as one of the three.

### R1 — Minimal Discoverable Entry

- Keep all seven owners natively discoverable.
- Keep one passively discoverable `using-mindthus`, but reduce it to a minimal shared
  floor with no method catalog, owner summaries, routing table, resources, or workflow.
- Keep the evidenced ROI.2 3L5S Anti-Spiral guardrail replacement.
- Change no owner discovery metadata or owner body.

Claim tested: the ROI.2 topology is sound, but its 2.3 KB entry still contains more
contract than Sol needs.

### R2 — Owner-local Passive Gates

- Keep all seven owners natively discoverable.
- Retain `using-mindthus` only as an explicit method-arbitration coordinate; it is not a
  default passive preflight.
- Lift the Frame/Whole trigger into EDSP discovery metadata using one exact
  package-time description replacement. Missing facts or comparison baselines remain
  explicitly excluded.
- Keep Anti-Spiral in the already-corrected 3L5S owner. Permit Decision Context to be
  the one passive family sacrificed if native Sol still asks before directing.
- Change no owner body beyond the frozen ROI.2 3L5S sentence.

Claim tested: passive AOP is cheaper when the minimum responsible owner is discoverable
directly and the central entry is no longer a general carrier.

### R3 — Native Owner Set, No Default Using Entry

- Use the same owner-local EDSP and 3L5S gates as R2.
- Remove `using-mindthus` from the packaged Skill inventory entirely.
- Keep all seven concrete owners discoverable and directly invokable.
- Add no replacement entry, Hook, prompt injection, owner index, router, or hidden
  resource carrier.

Claim tested: after two critical passive families have explicit owners, even the
explicit arbitration entry may be unnecessary overhead on high-capability Codex.

## Frozen nine-case panel

1. `direct`: report `billing / 8080` from `service.json`; no owner and no question.
2. `evidence`: refuse to claim improvement without a comparison baseline; no owner.
3. `frame_whole`: preserve that `SKILL.md` is text but reject the claim that this local
   fact defines the whole Skill; a Mindthus read counts toward passive recall.
4. `decision_context`: give no continue/hold/stop posture and ask exactly one
   action-changing context question; a Mindthus read counts toward passive recall.
5. `anti_spiral`: refuse a third unsupported fallback first and return upstream; a
   Mindthus read counts toward passive recall.
6. `anti_spiral_near_negative`: use new trace and failing test to replace the retry with
   a schema contract; do not over-brake.
7. `clear_sela`: read SELA and choose scalable B as long-term mainline with bounded A.
8. `clear_mpg`: read MPG and make a path-carrying action without requiring a new
   strategic-direction debate.
9. `clear_wae`: read WAE and separate agent judgment, deterministic workflow, and
   evidence gates.

Prompts and expected rubrics are frozen in `qualification/cases.json`. Case fixtures
are frozen under `qualification/fixtures/`.

## Corrections and anti-spiral rule

Each route has at most one correction, and only after a localized evidenced failure.
The correction must be deletion or equal replacement inside that route's declared
surface. It cannot add a new route, Skill, Hook, routing layer, fallback, hidden prompt,
case, or acceptance exception.

A corrected route first reruns the failed positive and its nearest negative control.
Only if it could beat the incumbent may it receive one full-panel requalification.
The correction is not a fourth route. A second failure closes that route.

The same local object may not receive a third structural change. Weak evidence delta,
repeated failure, or another-layer pressure routes through the TPlan Anti-Spiral Gate.

## Convergence rule

The Mission may close only after all three new routes have at least one frozen live
panel result, unless a resource/authority failure makes that impossible.

After three routes:

- continue the highest-ROI qualified route if it has a distinguishable improvement;
- otherwise stop optimization when no route improves the incumbent by at least 5%;
- stop earlier within a route when it reaches the passive 2/3 floor and the only next
  subtraction is expected to cross that floor without a distinguishable ROI gain;
- if all routes fall below the floor or have decision-changing regression, retain
  ROI.2 as incumbent and stop this convergence line.

No Candidate D, H4, second router, new evaluator platform, or post-hoc threshold change
is allowed. A successful result remains experimental: no release, merge, tag, Issue,
PR, marketplace deployment, or Stable installation change.

## Runtime budget

- Model/effort: `gpt-5.6-sol / xhigh` for every new call.
- Initial common panel: 9 incumbent calls + 27 route calls = 36 Generator calls.
- Corrections: at most 6 targeted calls total; a winning corrected route may use one
  final nine-case requalification only if remaining budget permits.
- Hard Mission cap: 51 Generator calls, 0 Judge by default, 5,000,000 counted tokens.
- Per call: 200,000 counted tokens and 900 seconds.
- A zero-usage setup/authentication failure may be repaired without consuming semantic
  correction budget. Usage is charged when the call ends.
- If a semantic rubric is genuinely ambiguous, the main Agent performs a separated
  evidence review; no Judge call is implied by this protocol.

## Evidence and responsibility separation

The runner records plugin identity, exact candidate digest, JSONL, stderr, final answer,
usage, duration, and loaded paths. Scripts report observations and arithmetic only.
They do not grade semantic truth or select the route.

The main Agent separately performs: implementation, direction check, rubric grading,
and Mission closure review. Important claims must link to raw artifacts or frozen
statistics. TPlan scripts own Mission state; no runtime status is hand-forged.
