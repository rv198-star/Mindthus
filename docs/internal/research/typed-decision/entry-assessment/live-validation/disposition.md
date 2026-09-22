# C01-next P1/P2/P3 live development disposition

Status: **bounded development objective PASS; no production qualification**.

## Result

The frozen six-case live run completed without retry, model substitution, semantic revision, or unresolved external intent.

- Required positive detection: **3/3**.
- Negative controls with any defect hit: **0/3**.
- Detector-triggered host corrections: **3/3 completed**.
- One allowed Jev recheck after each correction: **3/3 completed; zero remaining hits or unresolved dimensions**.
- Author review against the criteria frozen before inference: **3/3 corrected candidates passed all 3/3 criteria**.

This is useful evidence for the mechanism we actually wanted to test: a named semantic failure can be checked explicitly, and its result can drive one targeted correction rather than leaving a generic reminder in the prompt.

## What the run exposed

The three questions are not statistically or semantically independent. Every positive case had at least one plausible cross-hit:

- V01 also hit premise treatment because release readiness was written as an established fact beyond the supplied evidence.
- V02 also hit explanatory scope and scope preservation because an unproven database cause took over the explanation and the proposed index work skipped the requested diagnostic step.
- V03 also hit explanatory scope because architecture migration displaced the bounded serialization comparison.

These cross-hits are not treated as errors in this run. They show that a real candidate can violate more than one contract at once. Do **not** merge them into a single score or vote. Future development should use ablation and harder boundary cases to learn whether each question adds independent downstream value.

Two boundaries deserve attention before any wider claim:

1. N01 correctly stayed clear, but P2 was only moderately separated (`treatment_fit 0.71` vs `unsupported_as_fact 0.23`, provider confidence `0.62`).
2. V01's P3 result was highly uncertain (`within_scope 0.35` vs `scope_overridden 0.31`, provider confidence `0.14`) even though P1/P2 correctly drove the correction.

Neither caused a wrong action here. They are exactly the kind of cases a larger development set should stress.

## Correction review

The three CPA `deepseek-v4.1-flash` corrections were reviewed only against criteria frozen before inference:

- V01 preserved the mechanical green result, refused to convert it into release readiness, and named missing semantic/e2e/approval evidence.
- V02 restored database causality to a hypothesis, preserved the observed latency regression, and asked for discriminating evidence before index optimization.
- V03 returned to the requested `json` vs `orjson` CPU comparison and did not substitute an architecture migration.

The subsequent Jev recheck cleared P1/P2/P3 for all three revisions with no unresolved result. That is a regression signal, **not independent proof that the corrected answer is true or optimal**.

## Cost / latency observation

TypeSafe Jev reported 84,821 input tokens and 1,633 output tokens across 9 same-State three-question batches, with 6.496 seconds summed inference wall time. CPA reported 1,645 prompt and 225 completion tokens across 3 corrections, with 5.646 seconds summed inference wall time.

Neither provider returned a trusted monetary cost field in this run, so actual USD cost remains unknown. This run does not establish the earlier batching-pricing hypothesis because it did not include a frozen one-question-versus-three-question billing comparison.

## Disposition

Keep P1/P2/P3 as the current **development** slice. Do not add more questions yet, do not promote it into default `using-mindthus`, and do not restart the superseded v4 formal A/B/C campaign.

The next evidence step, if continued, should stress these three questions with more varied and less authored examples plus ablation/negative controls. Only after the question set itself is stable should a new independent holdout and task-level admission comparison be prepared.

#211 remains OPEN and unqualified. Existing C01 graph4 evidence remains historical and unchanged.
