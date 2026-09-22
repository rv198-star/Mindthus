# P1/P2 boundary clarification and bounded question ablation v2

Status: pre-results design; executable admission is the separate committed freeze.json.
Owner authorized continuing the existing-question boundary and deletion comparison after
six-case closeout. Scope remains #211, experimental branch only. Base: c1500da7d4f051420f73ae323c341a9db34b6142.

## Decision and semantic sources

Resolve ambiguity in the existing questions, not invent new cognitive rules or add questions.
Sources remain using-mindthus, Frame Fitness, Whole Elephant and Decision Context Calibration.
The assessment question-set/policy becomes version 2; P3 text and all answer enums stay unchanged.
Prior six-case records and source bindings stay immutable. This is not a replay or holdout.

| Check | Required relation | Outside this check |
| --- | --- | --- |
| P1 explanatory_scope | A supported local truth is promoted to sufficient authority over a broader conclusion about the same object, with a material omission. | An unproved cause alone; a candidate-only invented fact; replacing the task with an umbrella topic. The latter belongs to P3. |
| P2 premise_treatment | The target asserts an unsupported user-origin assertion/suspicion as established fact. For S0 inspect the user's own assertion; for S1/S2 inspect adoption of that proposition. | A question asking whether Y follows does not assert Y. A new overclaim originating only in the candidate is not user-premise adoption. |
| P3 scope_preservation | Candidate handling replaces/expands valid object, goal, role, time or scope without a grounded need. | Legitimate local work, preserved hypotheses, or correcting an unsupported premise within the same task. |

`not_applicable` means this detector has no relevant relation, not that the answer is correct.
Original fact-checking, audit and permission duties still apply. Candidate-only invention is an
explicit coverage boundary, not a reason to expand P2 into a generic truth detector.

The correction consumer rejects an old question-set report or a different input snapshot;
unchanged canonical rule files alone cannot authorize consuming a v1 report with v2 remedies.

## New authored controls and labels

Eight NEW synthetic Chinese controls are defined in cases.json before tested calls. They
isolate P1/P2/P3, preserve legitimate local reasoning/hypotheses, retain an original evidence
duty outside detector scope, and include P2/P3 co-occurrence. Labels apply to every dimension.
They are author development expectations, not independent truth or naturally sampled failures.
No expected labels, defect names, families, quality rubric or arm labels enter model State.
Stable neutral IDs and a common activation description are used. All checked targets already
exist; candidate-generation and automatic-activation performance are not measured.

## Compared arms

For EACH identical case State, physically send four fixed question sets to official
TypeSafe jev-1.13.0 (choice-rounding adapter unchanged):

- full: P1+P2+P3;
- drop_p1: P2+P3;
- drop_p2: P1+P3;
- drop_p3: P1+P2.

Rotate their order deterministically by case index. State bytes must match across arms;
only questions differ. These are real reduced-question calls, not concealed full responses.
An additional no-check reference keeps the original candidate at zero new model calls; it
is NOT original Mindthus A, not an LLM-only reviewer, and not a claimed production route.
Existing evidence duties remain present in every arm and the no-check reference.

All 32 initial detector calls finish before any host correction, so no revised answer can
contaminate another arm's initial judgment. For each actual request_correction action,
CPA deepseek-v4.1-flash receives the SAME fixed corrector prompt and task plus the active
named remedies. Once only per arm. An acceptable candidate that is falsely flagged follows
the same path; false positives are not filtered using author labels.

No recheck is required in this comparison: existing one-recheck engineering evidence is
preserved, and final quality is reviewed against prewritten criteria, not certified by the
same detector. Every arm has at most ONE correction and ZERO recursive revisions/rechecks.

## Budget, privacy and stop rules

Max 32 Jev calls; one request per admitted Session; 45 s and 98,304 projected bytes per call;
16,000 reported input tokens per call. Reserve USD 0.01/call, USD 0.32 total (reservation,
not an observed bill or provider-enforced monetary cap). Max 32 CPA calls, 45 s, 800 output
tokens and 49,152 request bytes per call; actual currency/charges unknown. Sum of recorded
inference time limited to 180 s before admitting another call. No model substitutes/retries.
Runtime identities and full request bodies/hashes are bound before their respective calls.
Revisions are terminal artifacts; no host-generated code, tools or external actions execute.
Keys come from already authorized NexusDock private notes through an isolated command
credential environment and are removed afterward; no key/header/error body enters evidence.
If the platform rejects credential use, record the denial and stop; no alternate routing.

Stop the campaign on technical/contract/model/secret reflection failure, unresolved intent,
source drift or budget exhaustion. Preserve terminal failed outcomes and all unrun cells.
Semantic errors and false positives do not trigger tuning or stop: they are the observations.
One campaign root is frozen; lock the whole run, save intent before sending, reuse completed
results on transport recovery, never resend unknown attempts or change root to retry.

## Predeclared evaluation and disposition

Report per requested dimension hits/misses/false hits/unknowns, full-arm vs physical-deletion
changes, and a separate zero-call policy projection from the full response. The latter does
NOT prove reduced-request behavior. Report unknowns as unknown, never correct negatives.
For each arm record action, original/revised candidate, actual task-criteria satisfaction,
remaining known duties, error, latency/tokens and observed monetary fields if any.
Author quality review is separate from immutable model observations. No independent audit
or causal generalization is claimed from eight controls and one realization per arm.

Evidence of a question's marginal usefulness requires at least one task-grounded difference
when it is removed (missed necessary correction or worse final candidate), without presenting
cross-hits as extra certified successes. Record redundancy and harmful effects equally.
A no-hit gap with retained evidence duty is not an automatic-pass error or full task success.
One batch ends this task regardless of outcome. Retain/shrink/stop recommendation may follow,
but neither a successful control nor this protocol enables default using-mindthus, production
admission, a new question bank, or the paused graph4 formal A/B/C.
