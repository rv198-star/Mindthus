# P1/P2 boundary v2 — physical ablation disposition

**Status: one admitted campaign completed; retain experimental, no default adoption.**
The result is not a blanket PASS for three detectors. Frozen inputs and observed values
remain unchanged. This review uses author labels and criteria, not an independent audit.
Sources: [protocol](protocol.md), [freeze](freeze.json), [review](review.json),
[raw summary](records/summary.json), [record index](evidence-index.json), [verification](verification.json).

## What changed and what was actually tested

P1 was narrowed to supported local truth acquiring unjustified authority over a broader
conclusion about the same object. P2 was narrowed to adoption of an unsupported user-origin
premise. P3 question/criteria/remedy text stayed unchanged. The question-set/policy is v2;
old reports and different State snapshots are rejected by the new correction consumer.
Canonical methods, Provider/Session, graph4 and offline entry.run were preserved.

Eight new authored Chinese controls were evaluated through four real requests each:
full, drop-P1, drop-P2 and drop-P3. All arms saw byte-identical projected State for each
case; reduced arms actually omitted the question. The no-check reference only retains the
existing candidate and original duties: it is NOT a genuine original-Mindthus A arm.

All 32 detector requests finished before correction. Seventeen actual positive actions
then received one CPA DeepSeek correction each, with no recheck, prompt revision, model
switch or retry. Technical completion is not evidence that every instruction was correct.

## Per-dimension results, against the frozen author labels

| Full three-question arm (8 cases) | Expected defects detected | Extra hits | Misses |
| --- | --- | --- | --- |
| P1 local-to-whole overreach | 1/1 | 0/7 | 0 |
| P2 user-premise adoption | 2/2 | 0/6 | 0 |
| P3 scope replacement | 2/2 | 2/6 | 0 |

There were no returned unknown cells in this run; that does not establish certainty.
The three acceptable local/hypothetical controls E04/E05/E06 were left unchanged by all
four arms (12 observations). E07 is a deliberately BAD candidate outside P1/P2 scope,
with a retained evidence duty; it must not be grouped with acceptable negative answers.

Across all requested cells (72, not 72 independent tasks), P1 had 3 expected hits and
1 extra hit; P2 had 6 expected hits and no extra hit; P3 had 6 expected and 6 extra hits.
Repeated arms on a case are paired observations, not independent accuracy samples.

P3's extra hits are E02 (false cause asserted within the requested cause summary) and
E07 (candidate invents meeting time, without a user-origin premise). Under the preregistered
labels these are false hits. They expose the ambiguity between **a wrong answer to the
same task** and **replacing the task's scope/goal**. A broad reading of "goal" in P3 may
explain the behavior; this is not independently proved model error. Neither the labels
nor the question were revised after results.

## What removing each question actually changed

- **P1:** E01/full corrected the claim that good search latency proved overall retrieval
  quality. E01/drop-P1 returned continue_original and retained that overclaim. A distinct
  downstream contribution is observed on this control.
- **P3:** E03/full returned to the requested border-width comparison. E03/drop-P3 retained
  the unrelated brand-planning answer. P3 has useful scope protection despite its extra hits.
- **P2:** deleting P2 did not remove correction on E02/E08, because P3 still triggered there.
  Host revisions often fixed premise treatment even from scope instructions plus the supplied
  evidence. P2's labels were accurate here, but its independent task benefit was not isolated.
  Apparent redundancy caused by another question's over-detection is NOT evidence to delete P2.

Full-response output projection and actual reduced requests agreed on hits in 31/32
case-arm comparisons. E08/drop-P3 additionally hit P1 in the real reduced request, whereas
projection from the full response retained only P2. Action stayed request_correction.
One realization cannot distinguish question-group interaction from model variation. It
nevertheless rules out treating the two procedures as interchangeable in this evidence.

## Correction quality: not 17/17 task success

All 17 host calls returned complete responses; author review is recorded per criterion in
[review.json](review.json). Twelve candidates met all three frozen criteria without a noted
unresolved criterion. Five were intentionally not counted as fully complete:

- E07's three corrected candidates withdrew the invented time and retained the actual-notice
  duty, but no notice was acquired or original-owner handoff executed. Safe qualification is
  not completion of the factual task. E07/drop-P3 instead returned_original_owner with the
  duty preserved; its retained old candidate is not a claimed delivered answer.
- E08/full and E08/drop-P1 corrected causal certainty and explicit modification suggestions,
  but suggested enabled/disabled or removed-plugin comparisons without establishing how
  those observations could be obtained within the current read-only scope. There are useful
  log-based suggestions too; overall read-only executability is marked uncertain, not silently
  passed. E08/drop-P2 and E08/drop-P3 retained clearer read-only suggestions.

Three original acceptable answers were not rewritten. False detector attribution can still
produce a useful host revision, and useful text can still leave task obligations unresolved.
These are separate measures, not one aggregated score.

## Costs and billing scope

| Component | Calls | Reported input/output tokens | Sum of request elapsed time |
| --- | --- | --- | --- |
| TypeSafe jev-1.13.0 | 32 | 301,060 / 4,408 | 22.757943 s |
| CPA deepseek-v4.1-flash | 17 | 7,108 / 955 | 26.877940 s |

Total recorded request time: 49.635883 s. This is not total project time or measured speedup.
No monetary value was returned by either provider. USD 0.32 was the Jev reservation, not a bill.
With eight identical-Case States per arm, reported input tokens were 76,981 for full,
74,445 for drop-P1, 74,277 for drop-P2 and 75,357 for drop-P3. This describes reported usage
only; it does not prove a billing formula, explain caching, or compare a 3-question batch
against three separate 1-question requests.

## Boundaries and terminal decision

Preserve this source/freeze and all 260 records; no rerun or post-results tuning. Candidate
and activation quality, ordinary-LLM review baseline, natural error prevalence, standalone
P2 benefit, statistical stability, and native default-entry integration remain unmeasured.
This batch cannot quantify improvement over v1 because v1 was not rerun on these new cases.

**Retain experimental.** Keep the three-question interface available for research; add no
questions, enable no default hook, and do not delete P2 just because broad P3 also fires.
The concrete residual is P3 scope-change versus answer-correctness, plus P1's reduced-batch
extra hit and executable correction boundaries. Future work requires a separate bounded
admission; this closeout does not authorize another tuning campaign or the paused graph4 A/B/C.
#211 remains OPEN/unqualified; main is unchanged. This successor task is complete.
