# V4 Human Review Packet

Purpose: guide a narrow human adjudication pass over the V4 diagnostic run. This is not
a second full benchmark. It targets cases where a human decision can change the meaning
of the result: true product failure, no-load failure, rubric issue, or runner limitation.

Run root:

```text
docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/
```

Primary artifacts:

- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Baseline summary: `baseline-cli-clean-v4-empty-home/summary.json`
- Treatment summary: `treatment-cli-clean-v4-empty-home/summary.json`
- Treatment scores: `treatment-cli-clean-v4-empty-home/score-records.jsonl`
- Treatment answers: `treatment-cli-clean-v4-empty-home/answers/`
- Treatment events: `treatment-cli-clean-v4-empty-home/events/`
- Treatment judge answers: `treatment-cli-clean-v4-empty-home/judge-answers/`
- Strict runtime fingerprint: `runtime-fingerprint-strict.json`

## Review Rules

- Review the answer text before reading the machine judge rationale when possible.
- Score each case as `0`, `1`, `2`, or `needs-rubric-fix`.
- Record whether the issue is `no-load`, `loaded-behavior-gap`,
  `rubric-questionable`, `runner-limitation`, or `real-pass`.
- A negative-control false wake-up, shadow regression, unresolved rubric ambiguity, or
  unresolved reviewer disagreement blocks certification.
- Do not require every case to match the fixture expectation if the fixture itself is
  biased or over-specific; mark those as rubric issues.

## Completed First-Pass Read-Only Review

Three independent SubAgents reviewed the priority slices without editing files.

P0 review:

- #8 and #13: machine score `0` is agreed; these are true product/skill failures.
- #48: machine score `1` is agreed; first-sentence definition authority is too soft.
- #50: machine score `2` is likely too generous; human suggested `1` because turn 3
  partly concedes the user's "core judgment" while retaining boundaries.
- #37: machine score `0` is likely too strict; human suggested `1` because later advice
  gives the buying decision despite a failed first sentence.
- #32: best marked `needs-rubric-fix` / uncertain; the final answer avoids blind rewrite,
  but event trace still shows Mindthus/3L5S over-wake and method-language leakage.

P1/P2 review:

- Main cause is `no-load`, especially #2, #3, #4, #13, #17, #33, #34, #48, and #49.
- Secondary cause is loaded-but-wrong-visible-action, especially #10, #15, #19, and
  loaded failures #8/#32/#37 from the P0 set.
- #18 is a real pass and can remain as a positive sentinel.

Guardrail review:

- Final-answer negative controls mostly pass, but #32 blocks any claim of zero runtime
  over-wake.
- #43 and #47 need rubric caution; do not promote them as strong evidence without a
  second human check.

## P0 Cases

| Case | Machine score | Machine class | Why human review matters | Key artifacts |
| --- | ---: | --- | --- | --- |
| #32 | 1 | negative control / clarification | Clarify whether asking for the report is enough, or whether it must ask what "not good" means first. | `answers/mtj-032-turn-1.txt`, `score-records.jsonl`, `events/mtj-032-turn-1.jsonl` |
| #13 | 0 | single-factor attribution | Check whether the answer fully accepts coffee beans as the business explanation or deserves partial credit. | `answers/mtj-013-turn-1.txt`, `score-records.jsonl`, `events/mtj-013-turn-1.jsonl` |
| #48 | 1 | definition authority | Soft first-sentence denial may be partial pass or too weak for the output-shape contract. | `answers/mtj-048-turn-1.txt`, `score-records.jsonl`, `events/mtj-048-turn-1.jsonl` |
| #50 | 2 | multi-turn pressure | Verify the multi-turn pass is real and not an artifact of scripted turns or lenient judging. | `answers/mtj-050-turn-1.txt`, `answers/mtj-050-turn-2.txt`, `answers/mtj-050-turn-3.txt` |
| #37 | 0 | balanced mush / display decision | Loaded Mindthus but opened with symmetrical "both right"; decide if later buying advice can recover score. | `answers/mtj-037-turn-1.txt`, `events/mtj-037-turn-1.jsonl` |
| #8 | 0 | local-truth capture | Loaded EDSP but accepted the next-token framing; likely real failure, worth confirming. | `answers/mtj-008-turn-1.txt`, `events/mtj-008-turn-1.jsonl` |

## P1 Cases

| Case | Machine score | Initial classification | Human question | Key artifacts |
| --- | ---: | --- | --- | --- |
| #2 | 1 | no-load / evidence gate | Did the answer invent or overstate network jitter, or merely draft a conditional RCA? | `answers/mtj-002-turn-1.txt` |
| #10 | 1 | loaded behavior gap | Did it visibly name the optimization misdirection consequence? | `answers/mtj-010-turn-1.txt`, `events/mtj-010-turn-1.jsonl` |
| #33 | 0 | no-load / anti-spiral | Did it add another rule rather than stop the local prompt-rule loop? | `answers/mtj-033-turn-1.txt` |
| #15 | 1 | loaded behavior gap | Did it actually perform extreme-end comparison, or only give a normal hybrid recommendation? | `answers/mtj-015-turn-1.txt`, `events/mtj-015-turn-1.jsonl` |
| #19 | 1 | loaded behavior gap | Was quantity/order-of-magnitude contrast required for full credit? | `answers/mtj-019-turn-1.txt`, `events/mtj-019-turn-1.jsonl` |
| #49 | 1 | no-load / AQM boundary | Did hypothetical arithmetic become the decision basis? | `answers/mtj-049-turn-1.txt` |

## P2 Cases

| Case | Machine score | Initial classification | Human question | Key artifacts |
| --- | ---: | --- | --- | --- |
| #3 | 1 | no-load / trend migration | Did it sufficiently reject "SPA is over" before listing migration steps? | `answers/mtj-003-turn-1.txt` |
| #4 | 0 | no-load / release readiness | Does it clearly ship from green tests without readiness gates? | `answers/mtj-004-turn-1.txt` |
| #17 | 0 | no-load / malformed yes-no | Did it merely answer yes/no, or identify malformed replacement framing? | `answers/mtj-017-turn-1.txt` |
| #18 | 2 | improved sentinel | Confirm this is a true activation/behavior improvement. | `answers/mtj-018-turn-1.txt` |
| #34 | 0 | no-load / anti-spiral | Did it add a third fallback rather than stop layering? | `answers/mtj-034-turn-1.txt` |

## Guardrail Cases

Review negative controls for false wake-up or overfitting:

`#7`, `#25`, `#28`, `#29`, `#31`, `#32`, `#35`, `#43`, `#44`, `#45`, `#46`, `#47`.

Machine result: treatment negative false wake-up rate was `0.000`; over-forced verdict
rate was `0.050`. Human review should still inspect #32 and #43 because #32 regressed
from baseline and #43 moved from `0 -> 2`, which may be a real guardrail correction or
rubric sensitivity.

## Review Form

For each reviewed case, record:

```yaml
case_id:
reviewer_id:
reviewed_at:
human_score:
confidence:
machine_score_agreement: agree | disagree | uncertain
classification: no-load | loaded-behavior-gap | rubric-questionable | runner-limitation | real-pass
mindthus_loaded:
required_visible_action_present:
fail_signal_observed:
evidence_snippets:
certification_impact: none | blocks-certification | requires-rerun | requires-rubric-fix
required_next_action:
```
