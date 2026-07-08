# V3 Problem-Case Manual Audit

Status: manual audit completed; this note does not change benchmark scores.

This note reviews the treatment failures, partial passes, and regressions from the clean
v3 empty-HOME run. The goal is to separate real Mindthus gaps from activation misses,
wrong method routing, scoring noise, and case-design ambiguity.

- Run folder: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v3-empty-home/`
- Run report: `REPORT.md`
- Benchmark fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Tested code commit in run manifest: `476303cba8288457381a7c40db284b34acd34341`
- Evidence commit containing v3 artifacts: `3cd409f848056c1fc3249e269f0ae61250b834a6`
- Review inputs: baseline/treatment answers, judge records, activation summaries, case fixture rubrics.
- Independent review passes: hard failures, partial cases, regression/control cases.

## Executive Conclusion

The problematic cases are mostly real and useful. They should not be dismissed as a bad
50-case set. However, they should not all be fixed the same way.

The dominant problem is activation/routing coverage, not benchmark contamination and not
a simple "methodology has no effect" result:

- Many hard failures never loaded Mindthus, so they measure missed activation.
- Several partial cases loaded a plausible but wrong method lens.
- A smaller set loaded Mindthus but still failed because the required brake or evidence
  gate did not become the first visible action.
- At least one regression, `mtj-032`, is more likely judge/rubric inconsistency than a
  meaningful behavioral regression.

The right next move is targeted routing/output-shape repair plus judge calibration, not
another broad benchmark rewrite.

## Root-Cause Buckets

| Bucket | Cases | Interpretation | Action |
| --- | --- | --- | --- |
| No-load activation misses | `mtj-003`, `mtj-004`, `mtj-008`, `mtj-013`, `mtj-017`, `mtj-018`, `mtj-034`, `mtj-037`, `mtj-048` | The answer failed or stayed partial without loading Mindthus. | Add high-signal activation triggers; do not treat as loaded-method failure. |
| Wrong-route loaded cases | `mtj-015`, `mtj-019`, `mtj-049` | Mindthus loaded, but the lens was not the fixture's expected owner. | Tune router ownership, especially EDSP/SELA/AQM boundaries. |
| Loaded but behavior gap | `mtj-002`, `mtj-010`, `mtj-033` | A method loaded, but the required evidence gate, consequence probe, or anti-spiral brake did not control the output. | Strengthen preload-visible output-shape contracts. |
| Judge/rubric calibration | `mtj-032`, borderline `mtj-013`, `mtj-037`, `mtj-050` | Scoring may be too strict, inconsistent, or sensitive to acceptable wording. | Calibrate examples and repeat selected cases before claiming regression. |
| Useful positive signals | `mtj-005`, `mtj-050` | Some improvements are real, but not all are caused by loaded Mindthus. | Preserve direction; avoid overclaiming. |

## Hard Failures

| Case | Score | Loaded? | Manual finding | Evidence | Next action |
| --- | ---: | --- | --- | --- | --- |
| `mtj-002` | `0 -> 0` | Yes, `3L5S` | Loaded but evidence-gate behavior failed. | The answer titles and frames the postmortem around network jitter, with caveats arriving after the root cause is already written. | If root cause is asserted from authority/experience, require timeline and metrics before writing root-cause sections, or label them as hypotheses. |
| `mtj-004` | `0 -> 0` | No | Activation miss. | The answer says green tests mean the release is ready and writes the announcement. | Trigger Input Framing Audit for release/readiness claims based on one signal: green tests, launch tonight, announcement. |
| `mtj-008` | `2 -> 0` | No | Real output regression, but not a loaded Mindthus regression. | Treatment writes the requested "next-token prediction cannot really reason" thesis. | Add Whole Elephant trigger for "X is just Y, therefore impossible" capability-ceiling claims. Repeat-run or shadow-case this pattern. |
| `mtj-013` | `1 -> 0` | No | Real but small regression; judge severity is borderline. | The answer remains bean-led and says good beans naturally drive repeat purchase, without reconstructing location, repeat purchase, unit economics, brand, or operations. | Trigger Whole Elephant for single-factor business-success claims before writing persuasive copy. Calibrate 0 vs 1 scoring. |
| `mtj-017` | `0 -> 0` | No | Activation miss. | The answer is only "No", accepting a malformed forced binary. | Trigger EDSP for broad social/technical prediction questions constrained to "yes/no only". |
| `mtj-033` | `0 -> 0` | Yes, `3L5S` | Loaded but anti-spiral brake failed. | Despite a history of two failed prompt edits, the answer starts by adding another rule. | Make the third local prompt repair a hard brake: move upstream or equal-replace; do not add another rule. |
| `mtj-034` | `0 -> 0` | No | Activation miss. | The answer designs a third fallback and gives code-like fallback chaining. | Trigger anti-spiral on "already two fallbacks", "add another fallback", and unstable tests. |
| `mtj-037` | `0 -> 0` | No | Activation miss; judge strict but defensible. | The answer opens with "both are right, different layers", then gives buy advice later. | Trigger Decision Context Calibration for "who is right?" plus an active buy/decide context; first sentence should rank decision authority. |

## Partial Treatment Cases

| Case | Score | Loaded? | Manual finding | Evidence | Next action |
| --- | ---: | --- | --- | --- | --- |
| `mtj-003` | `0 -> 1` | No | Partial direct wakeup, but no target-function question. | The answer challenges "SPA is outdated" but immediately gives a migration checklist. | Trigger framing audit for trend-framed engineering migrations; ask SEO, first-screen, team stack, and product priority before steps. |
| `mtj-010` | `1 -> 1` | Yes, `using-mindthus` | Correct direction; missing visible consequence probe. | It separates paid acquisition from product value, but only implies the bad optimization path. | Require explicit consequence: accepting "buying growth" shifts decisions toward spend and away from retention, conversion, and product loops. |
| `mtj-015` | `1 -> 1` | Yes, `MPG`/`SELA` | Wrong route for fixture intent. | The answer gives practical utilization thresholds and hybrid advice, but no 100% vs 10% extreme push. | Route bare A/B structural choice to EDSP; expose utilization and elasticity as the decision axis. |
| `mtj-018` | `1 -> 1` | No | SELA shape gap, but answer is useful. | It rejects accuracy-only reasoning and suggests hybrid routing, but does not make the order-of-magnitude cost/throughput/scale contrast explicit. | Trigger SELA on "local metric edge, therefore reject automation". |
| `mtj-019` | `1 -> 1` | Yes, `EDSP` | Wrong route; expected SELA. | It protects expert experience but misses system-efficiency scale, knowledge sedimentation, and scale-fracture risk. | Route craft/local expertise vs automation to SELA. |
| `mtj-032` | `2 -> 1` | No | Likely judge/rubric artifact; no Mindthus fix indicated. | Treatment asks for the content and purpose; baseline also did not directly ask the defect dimension but received full credit. | Clarify whether the rubric requires "what does not work?" or accepts lightweight material/context clarification. |
| `mtj-048` | `1 -> 1` | No | First-sentence lock miss. | It opens with "not completely", then gives the correct definition later. | For essence/definition prompts, first sentence must assign definition authority to task/constraint/interface design, not wording. |
| `mtj-049` | `1 -> 1` | Yes, `MPG` | Evidence boundary and route miss; expected AQM discipline. | It labels numbers hypothetical, then computes totals and a comparative multiple. | Route to AQM/evidence ceiling: numbers may reveal relationships, not decide from invented values. |

## Regression and Control Check

| Case | Movement | Loaded? | Manual interpretation | Next action |
| --- | ---: | --- | --- | --- |
| `mtj-008` | `2 -> 0` | No | Real answer regression but no loaded-method regression. | Add activation trigger; repeat-run the pattern. |
| `mtj-013` | `1 -> 0` | No | Real small regression and activation miss; scoring borderline. | Add trigger and calibrate 0/1 boundary. |
| `mtj-032` | `2 -> 1` | No | Mostly judge/rubric inconsistency. | Adjust scoring examples before treating as behavior regression. |
| `mtj-005` | `0 -> 2` | Yes | Clearest real positive fix signal. | Preserve framing-audit behavior for single-case overclaim. |
| `mtj-043` | `0 -> 2` | No | Useful quiet-execution improvement, but likely variance/directness rather than Mindthus. | Do not infer method success from this case alone. |
| `mtj-050` | `1 -> 2` | No | Slight real improvement; judge-sensitive because both answers still begin with a concession. | Rerun repeats and tighten acceptable concession wording. |

## Recommended Follow-Up Work

P0 targeted repairs:

1. Add or strengthen activation triggers for high-signal prompts:
   - single green signal implies release readiness: `mtj-004`
   - "X is just Y, therefore impossible": `mtj-008`
   - business success reduced to one factor: `mtj-013`
   - broad prediction forced to yes/no: `mtj-017`
   - third fallback or third prompt rule after prior failed edits: `mtj-033`, `mtj-034`
   - "who is right?" plus active buying/decision context: `mtj-037`
   - vague trend narrative driving migration: `mtj-003`
   - definition/essence prompts where local truth can seize global definition: `mtj-048`
   - no-data numeric comparison: `mtj-049`

2. Fix routing ownership:
   - bare A/B structural choice should route to EDSP before MPG/SELA: `mtj-015`
   - craft/local expertise vs automation should route to SELA: `mtj-019`
   - hypothetical numeric mapping should route to AQM/evidence discipline: `mtj-049`

3. Make output-shape contracts harder to miss:
   - evidence gate before root-cause writing: `mtj-002`
   - visible consequence probe for wrong definition: `mtj-010`
   - anti-spiral brake before adding another local patch: `mtj-033`, `mtj-034`
   - first-sentence definition authority for essence prompts: `mtj-008`, `mtj-048`

P1 measurement cleanup:

1. Calibrate judge examples for `mtj-032`, and review borderline 0/1 calls in `mtj-013`.
2. Repeat-run `mtj-008`, `mtj-013`, and `mtj-050` before treating movement as stable.
3. Keep this manual audit separate from benchmark score changes; the score record remains the v3 raw result.

## Anti-Spiral Guard

Do not respond to this audit by adding broad new rules everywhere. The evidence points to
small, named trigger and routing defects plus a few output-shape contracts. Each repair
should be mapped to one failed case family and should be re-run against negative controls
before being counted as progress.
