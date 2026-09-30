# Eight-case exploration — execution ended

**24 paths actually dispatched: 21 delivered, 2 local format failures, 1 undelivered/remote unknown. No unsent path remains.** This is not 24 successful answers or a fault-free first-attempt result. Independent content review of this new batch remains pending; executor observations below are not an independent PASS.

## Scope and raw products

Eight executor-prepared synthetic extensions, not independent holdout. Inputs and separate evaluation norms were frozen before inference. All 13 questions, three rounds, thresholds, maximum two findings and one check/revision remain. Host is gpt-6.1-sol/xhigh through the existing official HTTP profile; Jev is official jev-1.13.0. No old batch, model reviewer or second batch was run.

| Case | A original entrance | B precise Agent | C Jev |
|---|---|---|---|
| display-goal-1 | [delivered / 2 calls](answers/display-goal-1-A.md) | [delivered / 2 calls](answers/display-goal-1-B.md) | [delivered / 4 calls](answers/display-goal-1-C.md) |
| display-goal-2 | [delivered / 3 calls](answers/display-goal-2-A.md) | [delivered / 3 calls](answers/display-goal-2-B.md) | [format_failure / 4 calls](answers/display-goal-2-C.md) |
| mechanism-object-1 | [delivered / 4 calls](answers/mechanism-object-1-A.md) | [delivered / 2 calls](answers/mechanism-object-1-B.md) | [delivered / 4 calls](answers/mechanism-object-1-C.md) |
| mechanism-object-2 | [format_failure / 2 calls](answers/mechanism-object-2-A.md) | [delivered / 4 calls](answers/mechanism-object-2-B.md) | [delivered / 5 calls](answers/mechanism-object-2-C.md) |
| record-source-1 | [delivered / 3 calls](answers/record-source-1-A.md) | [unknown / 2 calls](answers/record-source-1-B.md) | [delivered / 4 calls](answers/record-source-1-C.md) |
| record-source-2 | [delivered / 2 calls](answers/record-source-2-A.md) | [delivered / 4 calls](answers/record-source-2-B.md) | [delivered / 4 calls](answers/record-source-2-C.md) |
| skills-scope-1 | [delivered / 2 calls](answers/skills-scope-1-A.md) | [delivered / 2 calls](answers/skills-scope-1-B.md) | [delivered / 4 calls](answers/skills-scope-1-C.md) |
| skills-scope-2 | [delivered / 3 calls](answers/skills-scope-2-A.md) | [delivered / 3 calls](answers/skills-scope-2-B.md) | [delivered / 4 calls](answers/skills-scope-2-C.md) |

Every linked product preserves first draft, check and final. A missing answer is explicitly marked as missing; raw read returns/errors are not substituted for answers. All 24 paths and 104 planned atoms per B/C arm remain in their respective denominators.

## SSE compensation and retained failures

000049 / record-source-2-B:1 lost its stream after 343.275067 seconds, with `stream disconnected before completion: idle timeout waiting for SSE`, no reply and no structured definite-failure code. It remains risk-accepted/remote-unknown; success of a later request does not prove the old generation ended.

Owner’s retry request was handled as one bounded technical compensation under the ongoing continuation and bounded-budget authorization. [Exact scope](CONTINUE-000049.md) · [registered successor](retry-000049.json). Execution source b0a7467acc3d38ba2ede62786c01dd5a73cf354a. Only record-source-2/B received a path cap of 8 rather than 7, actual use 4; total 176/144/32 caps stayed unchanged. No general ignore-unknown policy was adopted.

000050 / record-source-2-B:2 returned a complete draft after 95.330691 seconds. Its actual wire is identical to 000049; atoms/composition digests match the registered prior results. One normal check followed. The final is the first complete draft; no revision. Old intent, unknown, consumed call and session are retained. No authentication probe, channel/model/configuration/timeout change or automatic retry loop. [Actual reply, check and final](answers/record-source-2-B.md).

000047 / record-source-1-B:1 remains the separately authorized remote unknown from a 360.032818-second local subprocess timeout, without a reply or reliable CLI terminal. It was never replayed. The accepted risk is not a completion. That B path has no answer.

000011 / display-goal-2-C and 000029 / mechanism-object-2-A returned transport terminals but requested reads with nonempty text. Local `read_only_before_first_draft` rejected them. They remain two undelivered format failures, not semantic failures or successful answers, and were not retried. Forward sending-contract clarification remains recorded in [repair](READ-CONTRACT-REPAIR.md). [Old 50-call report](RESULT-000050.md) and [checkpoint](CHECKPOINT-000050.md) preserve the prior stop.

No new unknown, safety/permission refusal or unclassified internal recovery occurred during the 26-call continuation. Serial receipts remain bound; conservative cooling after the accepted unknown does not prove absence of old remote overlap.

## Actual calls and time

76 logical calls = 52 host CLI starts + 24 Jev; 74 returned transport records and 2 historical unknown calls. Local path failures and transport statuses are different. One explicitly authorized technical compensation; automatic outer-driver retries zero. Internal auth/fallback/reconnect/sampling recovery log counts observed zero; exact underlying HTTP and generation attempts remain unknown.

Unused original caps: 100 logical / 92 host / 8 Jev. Owner’s 2–3x controlled-overrun allowance was not used. Unused quota is not permission to seek better answers.

Total session/processing 5101.169s (85.02min); active cooling wait 4310.681s (71.84min). Local execution windows 9642.691s; first send to last local terminal 19673.930s, including engineering and Owner pauses. A host session is not pure HTTP time; unknown-call local endings are not remote-completion evidence.

| Arm | Logical | Host | Jev | Session s | Active wait s |
|---|---:|---:|---:|---:|---:|
| A | 21 | 21 | 0 | 1372.404 | 1148.301 |
| B | 22 | 22 | 0 | 2955.447 | 1261.749 |
| C | 33 | 9 | 24 | 773.318 | 1900.630 |

Old 000047/000049 failures and 000050 compensation are included. New continuation: 26 calls (17 host / 9 Jev). Raw token usage and missing usage are reported separately by provider in [summary](summary.json) and [bound calls](calls.jsonl); dollars remain unknown, no cross-provider token-as-price arithmetic. Full failures/mixed execution sources cannot be dropped to claim clean matched ROI.

## Executor content observations — not independent review

| Fixed contrast | Actual observation | Limit |
|---|---|---|
| Purchase vs current-display goal | Delivered A/B shift from comparison of 5K candidates to adjustment of the current display. First C side is reasonable. | C second side has no answer; full C reversal is not proven. |
| Generation stage vs whole service | Delivered B/C preserve the adequate local explanation and add signature/refusal control for the whole service. | Whole-service A has no answer; no three-way complete pair. |
| Direct vs reported case record | Reported-side A/B/C reject an unsupported direct-verification claim without declaring the report false. Direct-side A/C also reject case-internal original-record verification wording. | This differs from the frozen direct-side expectation; preserve possible over-limitation and wording/provenance ambiguity. Metadata origin was present in the actual A prompt. Direct-side B has no answer. |
| This Skill vs all Skills | All three preserve the sufficient local explanation and limit the generalization on the other side. | No material C correction of an important A/B final judgment was observed. |

C produced no adopted finding or draft check in all eight cases. This is not automatically failure: a completed sufficient relation could warrant no correction. Here raw P equals the C claim window 8/8, three P results are low-confidence and five are adopted. Seven R results are unresolved (dependency missing or low confidence); reported-source R is adopted as sufficient despite the frozen overreach expectation. Correct final answers do not establish correct underlying Jev relations. These observations do not uniquely separate wording, candidate expression, thresholds and model capability; no threshold was lowered or result regenerated.

B records 95 support, 6 deny, 2 unresolved and 1 invalid atom (record-source-1 ES contract error); C records 38 support and 66 unresolved atoms. These are descriptive interface states, not normative success scores. B can form specific limit/reanchor findings. At least reported-source and all-Skills draft checks retain `check_conflict` unresolved bases rather than silently claiming full implementation verification. No completed path used revision. Jev provider/contract-error fallback reasons remain in the raw atomic records (including impact questions); they are not relabeled as valid judgments. Descriptive atom states, contract errors, missing dependencies and normative uncertainty remain separate; no post-hoc aggregate accuracy score is invented.

On these products, executor observation is no clear additional important final-judgment correction by C over A/B. This is bounded to the new exploratory material/model/configuration and includes three undelivered paths; it is not a universal Jev failure conclusion, stable mean, independent blinded result or default-adoption qualification. Old conclusions remain historical, not retrospectively upgraded.

## Evidence and next review

[24 original products](answers/) · [76 bound calls](calls.jsonl) · [all file locations](evidence-index.json) · [execution log](execution.log) · [base evidence](business-evidence.tar.gz) + [additive evidence](business-evidence-after-000047.tar.gz). Original base archive is unchanged. The new index is packaging verification, not an independent all-hash audit. Group-concealed [review packets](blind-review/) and [separate mapping](private-review-map.json) preserve the intended later review; execution is not claimed blind.

Execution scope has no unsent item. Remaining limitations: 000047 and historical 000049 remote status/fees unknown; three paths have no final answer; new-batch independent content review pending. No additional dispatch is authorized by this report. Closed GJ/R2, original design, main/default Skill, default NOT QUALIFIED and ROI-Beta boundary are unchanged.
