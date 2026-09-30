# Eight-case exploration — 50-call checkpoint

**PARTIAL: 12 delivered, 2 format failures, 2 remote states unknown, 8 not sent.** The new full-batch content assessment is incomplete. No independent review PASS or Jev quality/default/ROI claim. All 24 paths remain in the denominator.

## Frozen scope and continuation

Owner authorized eight executor-prepared synthetic extensions, not independent holdout, and 24 A/B/C paths. Business inputs, separate norms, 13 questions, three rounds, thresholds, two findings and one check/revision are unchanged. Host gpt-6.1-sol/xhigh and official HTTP, CLI 0.159.2; official Jev jev-1.13.0. No old batch is rerun or reviewer model invoked.

Initial execution source 9978805eee2420fe1b08b2f30a1a20bc9e26248e. Read sending clarification 3a408a43aa4869de37fbdc1291517bfbdd4e71f9 preserved 34 ended calls and both failed paths; it changed sending instructions, not local judgment acceptance. [Repair and three scoped tests](READ-CONTRACT-REPAIR.md).

Owner subsequently accepted only 000047 remote compute/billing/overlap risk and bounded budget flexibility. Named continuation source 02687f24f289f9ed9ae9d65d1138dd39bc921d91 retains the unknown/debit and permits nine unsent paths without replay. [Actual disposition](risk-accepted-000047.json) · [scope](CONTINUE-000047.md) · [three scoped synthetic tests](resume-000047-tests.log).

## Every path and raw product

Linked products contain first draft, check, final or explicitly no answer, local failures and original returns. A returned read request is not an answer.

| Case | A | B | C |
|---|---|---|---|
| display-goal-1 | [delivered / 2 calls](answers/display-goal-1-A.md) | [delivered / 2 calls](answers/display-goal-1-B.md) | [delivered / 4 calls](answers/display-goal-1-C.md) |
| display-goal-2 | [delivered / 3 calls](answers/display-goal-2-A.md) | [delivered / 3 calls](answers/display-goal-2-B.md) | [format_failure / 4 calls](answers/display-goal-2-C.md) |
| mechanism-object-1 | [delivered / 4 calls](answers/mechanism-object-1-A.md) | [delivered / 2 calls](answers/mechanism-object-1-B.md) | [delivered / 4 calls](answers/mechanism-object-1-C.md) |
| mechanism-object-2 | [format_failure / 2 calls](answers/mechanism-object-2-A.md) | [delivered / 4 calls](answers/mechanism-object-2-B.md) | [delivered / 5 calls](answers/mechanism-object-2-C.md) |
| record-source-1 | [delivered / 3 calls](answers/record-source-1-A.md) | [unknown / 2 calls](answers/record-source-1-B.md) | [delivered / 4 calls](answers/record-source-1-C.md) |
| record-source-2 | [not_sent / 0 calls](answers/record-source-2-A.md) | [unknown / 2 calls](answers/record-source-2-B.md) | [not_sent / 0 calls](answers/record-source-2-C.md) |
| skills-scope-1 | [not_sent / 0 calls](answers/skills-scope-1-A.md) | [not_sent / 0 calls](answers/skills-scope-1-B.md) | [not_sent / 0 calls](answers/skills-scope-1-C.md) |
| skills-scope-2 | [not_sent / 0 calls](answers/skills-scope-2-A.md) | [not_sent / 0 calls](answers/skills-scope-2-B.md) | [not_sent / 0 calls](answers/skills-scope-2-C.md) |

## Two different unknown events

**000047 / record-source-1-B:1**: request 3f5d271f948d80feb91dc7083080d48a05a69fafda03c020cf3ba8aba1f38c5c. Local subprocess TimeoutExpired at the frozen 360-second timeout, session 360.032818s, no bound CLI terminal or answer. Owner explicitly accepted this named risk. It is not resent or converted to completion; B remains unknown with 2/7 consumed, its prior atoms/composition unchanged. [Raw error](failures/000047/raw.json) · [terminal](failures/000047/terminal.json).

**000049 / record-source-2-B:1**: request 0817e559b299453a5902667c85da2e69ec5b3280eb0bee4c66d0b2d35b4a800a. CLI thread 01a0f279-8047-7521-9a0b-eb97737c8a72 emitted turn.failed with ordinary message `stream disconnected before completion: idle timeout waiting for SSE`; no structured failure code or reply. Session 343.275067s, returncode 1. This is an SSE stream failure, distinct from local subprocess timeout, and does not prove provider generation ended. It remains unknown. [Raw CLI events](failures/000049/raw.json) · [terminal](failures/000049/terminal.json) · [stop](STOP-000049.json).

Neither event is a safety/permission refusal. No fabricated serial completion, automatic replay or channel change. A proposal asks Owner to allow at most two additional pure-text timeout/stream-unknown dispositions including 000049, no replay and original caps; it is pending, not active. The batch sender is stopped. No local timeout/configuration change is made: extending local wait alone does not fix the observed SSE idle failure. The earlier user-facing local-timeout attribution for 000049 was corrected from its actual events.

## Definite local format failures

000011 (display-goal-2-C) and 000029 (mechanism-object-2-A) have reliable returned transport terminals, but kind=read with nonempty text. Local acceptance correctly rejected read_only_before_first_draft; no delivered answers. Both remain consumed failures and are never retried. The shared outgoing instructions were clarified forward; subsequent reads were accepted. This does not reinterpret either failure as success or a Jev semantic failure. [First raw read](failures/000011/envelope.json) · [second raw read](failures/000029/envelope.json).

## Costs and boundaries

50 logical calls = 35 host CLI starts + 15 Jev. Original caps remain 176 / 144 host / 32 Jev, unused 126 / 109 / 17. Owner accepts controlled/explained 2–3x overruns, but that allowance is not used or required. Unused budget does not clear a remote unknown. Driver retries and reviewer-model calls are zero; exact underlying HTTP/generation counts and dollar amounts remain unknown.

Processing/session 3702.905s (61.72min); active wait 2874.961s (47.92min). First send to last local terminal 13924.856s (232.08min), including engineering and Owner pauses. Local execution windows from the driver log total 6667.581s. Outside-window wall is not model processing. Local terminal timestamps for unknowns do not prove remote finish; host session is not pure HTTP latency.

| Arm | Logical | Host | Jev | Session s | Wait s |
|---|---:|---:|---:|---:|---:|
| A | 14 | 14 | 0 | 888.133 | 763.863 |
| B | 15 | 15 | 0 | 2310.202 | 873.675 |
| C | 21 | 6 | 15 | 504.570 | 1237.423 |

Raw usage and missing usage remain separately by provider in [summary](summary.json) and [calls](calls.jsonl). No cross-provider token-to-cost conversion. 000049 observes no internal recovery logs, but this does not prove zero underlying attempts.

Initial source covers 34 calls, read clarification 14, named risk continuation 2. No business prompt/judgment/threshold/model change in the named continuation. Mixed-source, failed and unknown pairs cannot be dropped to present a full-batch speed advantage.

## Executor observations, not independent content review

Purchase/current-display goal: A/B change the actionable suggestion with the goal. C first side delivered; second has no answer due to interface failure. Full C reversal success is not established.

Generation-stage/whole-service object: delivered answers preserve the sufficient local explanation and limit it for the whole service with signature checks/refusal. C has no adopted finding behind its answers; whole-service B has one limit finding and completed its check. Whole-service A failed before an answer; the full three-way pair is incomplete.

Direct record: A/C retain arithmetic (12 to 3) but reject direct-original-record wording because the scenario is synthetic. The fixed norm distinguishes case-internal direct metadata from real-device verification. Preserve possible over-limitation and material-boundary ambiguity; do not rewrite the norm after outputs. B formed a limit finding with ES contract error, then its draft timed out. Reported record B atoms now adopt reported origin and a limit finding without ES error; its draft lost the stream. A/C counterparts are unsent. Full source-reversal comparison is untested.

Across five sent C cases, raw P equals the C sentence each time: P is low-confidence twice and adopted three times. No adopted R/S finding is formed; all five have zero findings/checks, including one format failure. Three impact judgments preserve provider_error. This is localization/coverage evidence, not proof no correction was needed or a unique-root-cause diagnosis. B formed five findings in four cases, including the two unknown drafts. Completed paths have no revision. Both Skills quantifier cases are unsent.

All 104 atoms per B/C arm remain in the planned denominator. States, skipped phases and missing results are descriptive, not independently scored accuracy; frozen brief norms require semantic review.

## Evidence and unfinished work

[24 products](answers/) · [50 bound calls](calls.jsonl) · [file index](evidence-index.json) · [base JSON evidence through 000047](business-evidence.tar.gz) + [continuation JSON evidence](business-evidence-after-000047.tar.gz) · [execution log](execution.log) · [50-call checkpoint](CHECKPOINT-000050.md). Failed requests and readable products are directly in the repository; archive transfer is not needed to continue. [Grouping-concealed packets](blind-review/) and [separate mapping](private-review-map.json) prepare downstream review; no independently blinded review is claimed.

Unfinished: 000049 disposition, eight unsent paths, full-batch content comparison. No further model request is sent. Old six/four-case conclusions retain their historical scope; closed GJ/R2, default NOT QUALIFIED, main/default Skill and ROI-Beta boundary are unchanged.
