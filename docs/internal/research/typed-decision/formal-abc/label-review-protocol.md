# C01 formal A/B/C — holdout label review protocol

## Purpose

Create a genuinely new formal holdout for #211 after all earlier C01 development,
language-diagnostic, paired-retest, host-handoff and completion-recovery work.

The 18 candidate scenarios in `holdout-candidates.json` were authored after those
campaigns. A leakage audit found no exact request+evidence duplicate against 105 historical
C01 contexts; the highest simple lexical/sequence similarity was 0.45 and no candidate
was >=0.80. This is a mechanical screen, not proof of semantic independence.

## Label independence

Before any A/B/C tested-arm inference:

1. An independent GLM 5.3 Flash reviewer receives:
   - candidate contexts with IDs/families but **without** author expected labels,
     task criteria or catastrophic criteria;
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

DeepSeek is deliberately not used for label review because it will participate in the
formal tested paths. This role separation overrides the ordinary host preference for this
single pre-results adjudication call.

## Stop rule

A technical failure leaves the formal holdout unreviewed and blocks A/B/C. Do not switch
to DeepSeek or self-certify the labels merely to continue.

No TypeSafe/Jev, DeepSeek A/B/C, original-A carrier or downstream task-generation call is
permitted until the reviewed label set and formal A/B/C protocol are frozen in a later
commit.
