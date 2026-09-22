# C01-next P1/P2/P3 small live validation protocol

Status: preregistration for development evidence only. This is not a holdout, production qualification, or a continuation of the paused formal A/B/C campaign.

## Question

Does the frozen P1/P2/P3 detector catch three known failure modes without forcing broader framing onto three legitimate local/hypothetical answers, and can one targeted host correction improve a detected candidate without an answer-shopping loop?

## Frozen sample

`cases.json` contains six authored Chinese development controls:

- V01: locally true mechanical check promoted to release readiness;
- V02: unsupported user causal premise promoted to fact;
- V03: candidate escapes an explicit local comparison into architecture migration;
- N01: local hash evidence genuinely controls the asked result;
- N02: explicitly local regex explanation is sufficient;
- N03: explicit hypothetical reasoning remains a hypothesis.

Positive cases require their named `expected_hit`. Other hits on a positive case are reported as cross-hits rather than silently scored as failures. Any defect hit on a negative case is a false positive.

## Fixed engines and channels

- Detector: official TypeSafe Jev `jev-1.13.0`, native System-One endpoint, current assessment contract version 1.
- Corrector: CPA `deepseek-v4.1-flash`, temperature 0, no tools, one call per case only after the detector returns `request_correction`.
- No OpenRouter non-Jev call.
- No model substitution or automatic retry. A technical failure stays in the denominator and ends that branch.
- Credentials are read only through hidden local terminal input for the run and removed from the process afterward.

## Execution budget and recovery

- Six initial Jev batches maximum, each with P1/P2/P3 in the same State.
- At most six host corrections because a false positive must exercise the same production consequence.
- At most one Jev recheck after each completed correction.
- One correction and one recheck per case; no semantic revision, prompt tuning, relabeling, or retry after seeing results.
- Every Jev batch gets a single-request Session live admission. The initial request identities are frozen before inference. A recheck identity cannot exist before its host revision exists; it is deterministically bound and written once after that immutable revision, before the recheck, without changing questions, rubrics or case labels.
- Unknown/in-flight calls require reconciliation and are never blindly repeated.

Per Jev request reserve: USD 0.01, per-run Jev ceiling USD 0.12. CPA monetary cost is reported only if the provider returns a trustworthy numeric field; token counts and wall time are always recorded when available.

## Stop conditions

Stop the whole campaign on:

- source/freeze mismatch;
- provider/model identity drift;
- an unresolved prior external call;
- request outside the exact per-call admission;
- a secret/response reflection check failure;
- a budget/shape contract failure that makes later observations incomparable.

A semantic miss or false positive does **not** stop the campaign; it is the evidence being measured.

## Evaluation

Report separately:

1. positive detection: required expected hit observed / 3;
2. negative false positive: negative cases with any defect hit / 3;
3. cross-hits on positive cases;
4. correction execution rate for actual detector hits;
5. recheck disposition after one correction;
6. frozen correction criteria reviewed per positive case;
7. Jev input/output tokens, provider-reported cost when present, and wall time;
8. CPA prompt/completion tokens, provider-reported cost when present, and wall time.

The same Jev model recheck is a regression signal, not independent truth. Correction quality is reviewed against the preregistered case criteria and must be labeled author review unless an independent evaluator is separately added.

## Claim ceiling

A good result supports only a bounded development claim for these six authored controls. It does not establish general Chinese accuracy, production adoption, the economic value of a broad assessment matrix, or formal C01 admission.
