# H2.1 Frozen Stable Comparison Protocol

This protocol activates only if C1-C3 and H2 Q1-Q7 all pass. It is frozen before C1.

## Arms

- Candidate arm: reuse the H2.1 Q1-Q7 outputs and lifecycle produced during the frozen
  qualification. Do not reuse any old `9c271c1f` output.
- Stable arm: run Mindthus 1.4.6 once on exact Q1-Q7 prompts and fixtures with Sol/xHigh,
  matched session shape, fresh isolated Stable-only homes, and no candidate present.
- In both arms Q1/Q2 share one fresh home, workspace, and thread. Q3, Q4, Q5, Q6, and
  Q7 each use their own fresh arm-only home, session, and workspace. C2/C3 causal homes
  are not part of either comparison arm.

Reusing the candidate qualification arm is pre-registered to avoid duplicate calls. It
is valid only when prompts, fixtures, model, effort, cwd isolation, and host lifecycle
evidence match the Stable arm.

## Lifecycle and loaded-byte ledger

For each case, derive from host JSONL:

- ordered Mindthus file reads;
- unique loaded bytes: UTF-8 content bytes returned to the model for each distinct
  Mindthus contract/resource content hash;
- total observed loaded bytes: sum every attributable Mindthus content payload returned
  by command lifecycle, including a repeated payload each time it is actually returned;
- owner fidelity and user-visible interaction rounds;
- input, cached input, output, reasoning output, and counted tokens.

Do not count plugin manifests, diagnostics, path listings, `stat` output, test fixtures,
command output unrelated to Mindthus content, or files merely present on disk. When one
command mixes content and unrelated output and the content bytes cannot be isolated,
the loaded-byte metric is unknown, not zero.

For Q4/Q5/Q7, compute each case's reduction in total observed Mindthus loaded bytes,
then take the three-case median. It must be at least 50%. Unique bytes remain a secondary
diagnostic and cannot replace the repeated-inclusive controlling metric.

For every Q1-Q7 completed call, compute `uncached_input = input_tokens -
cached_input_tokens`, then the paired reduction
`(stable_uncached - candidate_uncached) / stable_uncached`. The median of all seven
paired reductions must be at least 10%. A zero/missing Stable denominator makes the
metric unproven. Source words or bytes cannot substitute for this host metric.

## Critical behavioral gates

Every case is pass/fail before aggregation:

- Q1: Decision Context changes action without premature direction.
- Q2: correct MPG path action and no unrelated owner.
- Q3: correct Agent/Workflow/Evidence control split.
- Q4: Evidence First, Frame, and Whole change the release action.
- Q5: exact ordinary artifact and no added interaction round.
- Q6: one answer-changing ambiguity question and no owner-body guess.
- Q7: Anti-Spiral stops another local layer and preserves the artifact.

One decision-changing candidate regression, unrelated owner load, lost passive
obligation, or new user interaction round blocks continuation. Average quality cannot
hide it.

## Paired Judge

Run one Sol/xHigh Judge for each complete Q1-Q7 pair, with a 200,000 counted-token
rejection line inside the 400,000 outer authorization. Give it the exact task, fixture
facts, both final outputs, relevant artifact diff, and lifecycle read summary. Hide arm
identity:

- odd cases: candidate = A, Stable = B;
- even cases: Stable = A, candidate = B.

Judge returns only:

- candidate critical regression: `yes | no | unclear`;
- owner fidelity: `pass | fail | unknown`;
- passive recall: `pass | fail | not-applicable | unknown`;
- practical usability: `pass | fail | unknown`;
- short evidence-linked rationale.

Style, verbosity, wording, or different but equally sound action plans are not failures.
The main Agent verifies Judge claims against raw outputs and lifecycle before recording
evidence.

Any `critical regression=yes`, owner-fidelity failure, passive-recall failure, or
practical-usability failure blocks continuation. If more than one case contains any
`unclear`/`unknown`, the result is `STOP_UNPROVEN`. If exactly one case is unresolved,
the reserved eighth Judge reviews that lowest-numbered case once; any remaining unknown
or unclear field is `STOP_UNPROVEN`.

## One noise review

The result alone never triggers a rerun. A noise review is allowed only when all semantic
and loaded-byte gates pass, the seven-case uncached-token median is below 10%, and the
median-determining paired case has an observable cache asymmetry: the two arms' reported
`cached_input_tokens / input_tokens` fractions differ by at least 0.50.

If that median-determining case is Q3-Q7, rerun that exact case once on both arms in
fresh mirrored homes. For each arm, combine the original and rerun uncached values using
the arithmetic median of two observations (their mean), recompute that case's paired
reduction, then recompute the seven-case median. If the median-determining case is Q1 or
Q2, the two-call reserve cannot reproduce its shared-session shape, so no review is
authorized and the token benefit is unproven.

The reserved eighth Judge follows only the unresolved-field rule above. No other rerun
is allowed.

If noise remains indistinguishable, cost benefit is unproven and continuation fails.
