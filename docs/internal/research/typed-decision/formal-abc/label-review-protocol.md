# C01 formal A/B/C — holdout label review protocol

## Purpose

Prepare candidate inputs for a possible #211 holdout after the earlier C01 development,
language-diagnostic, paired-retest, host-handoff and completion-recovery work.
This packet is not yet an admitted independent holdout; candidate independence, label
validity and the original-A carrier remain unqualified.

The 18 candidate scenarios in `holdout-candidates.json` were authored after those
campaigns. A leakage audit found no exact request+evidence duplicate against 105 historical
C01 contexts; the highest simple lexical/sequence similarity was 0.45 and no candidate
was >=0.80. This is a mechanical screen, not proof of semantic independence.

## Label independence

Before any A/B/C tested-arm inference:

1. An independent GLM 5.3 Flash reviewer receives:
   - original candidate contexts with opaque review IDs only; **without** family/stratum,
     author expected labels, task criteria, catastrophic criteria or the private ID map;
   - current canonical `using-mindthus` plus all eight method SKILL contracts;
   - the C01 route vocabulary and a request to return JSON judgments.
2. The reviewer returns per case:
   `entry_mode`, `unresolved_obligation`, `owner`, `applicable`, `route`,
   plus a short rationale and any ambiguity flag.
3. Author labels are compared mechanically after the response is immutable.
4. Exact agreement freezes normally.
5. Disagreement is resolved **before** tested-arm results:
   - if canonical contracts clearly support one side, record the adjudication;
   - if both are defensible, freeze an explicit allowed-set or remove the case;
   - do not change a label after A/B/C results are visible.

The GLM review is label adjudication only. It is not a tested arm and is not a task-quality
judge for its own outputs.

## Reviewer serving/budget

- CPA endpoint: `https://cpa.72live.com/v1/chat/completions`
- model: `glm-5.3-flash`
- temperature: 0
- one call only, no retry/model switch
- max output tokens: 6000
- request body ceiling: 196608 bytes
- timeout: 90 seconds
- price/currency: unknown unless service reports a documented value

GLM is proposed for the separate label-review role because DeepSeek is the preferred
tested host. This does not change DeepSeek priority for host execution, authorize silent
model switching, or relax the OpenRouter Jev-only restriction. The review input and
transport must be admitted through the existing authorized credential path; a platform
tool rejection is not a provider response and is not a reason to bypass that rejection.

## Stop rule

A technical failure leaves the formal holdout unreviewed and blocks A/B/C. Do not switch
to DeepSeek or self-certify the labels merely to continue.

No TypeSafe/Jev, DeepSeek A/B/C, original-A carrier or downstream task-generation call is
permitted until the reviewed label set and formal A/B/C protocol are frozen in a later
commit.

## Recovery preflight correction (before any observed review result)

The first proposed blind payload included `family` values such as `sra`, `wae`, and
`explicit-wae-inapplicable`. Those are author answer cues, not task evidence. The
replacement `review_packet.py` exports exactly opaque ID plus original context per
case, with the canonical methods. Author fields stay in the original candidate file;
no question, context, label or prior trial is rewritten. `offline_check.py` checks
this separation without inference. Only `payload.json` is model-facing; the manifest
and its ID map remain local. This packet is still prepared, not sent.

Before final scoring admission, resolve these existing distinctions explicitly:
- `owner` in a final C01 result is null on fallback; the checked/rejected method is a
  separate `checked_owner`. H12 author owner=wae denotes the candidate, not an accepted
  final owner. No field-by-field mixing of incompatible accepted paths is allowed.
- H14 has author family `no-match` but expects direct execution for an explicitly
  arbitrary choice. It does not supply a genuine semantic no-match control.
- No exact text duplicate and a low lexical similarity do not establish task-family
  independence. The cases were authored by the implementation context. A separate AI
  label reviewer alone cannot certify independent sampling.
- Original-A must be the actual non-Jev host with its recorded plugin/model/tool
  configuration, not a new prompt-only stand-in. An installed Codex binary alone is
  not this evidence. Keep task quality, method preference and safety/authority failures
  separate when freezing the eventual admission and scoring rules.

## Executable admission v1

`label_review.py` builds the blind payload from `review_packet.py`, freezes the exact
request hash and source digests, and records intent before one CPA request. The earlier
blocked inline tool attempt is not relabeled a provider failure. This new admission uses
the corrected blind payload and the ordinary authorized tool path; a platform rejection
ends this attempt without credential rerouting or alternate transport.

Reviewer output separates final `owner` from `checked_owner`. The latter may name a
rejected method while final owner remains null. Judgments and bounded original content
are preserved before comparison; invalid JSON is not semantically repaired or retried.
Credentials are process environment only and are excluded from every persisted record.
10 additional offline controls passed, including unknown-intent and completed-result
reentry. Runtime and historical source/observations remain unchanged.

This is a blinded AI label review, not proof that these author-created, partly repeated
problem families are independently sampled. All 18 candidates remain in the review;
no post-result cherry-picking. Task acceptability and routing preferences are separate.
