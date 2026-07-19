# Mindthus Judgment Benchmark Latest

Status: Not yet certified as passing. Active brake semantic-triage refinement closed on
2026-07-13; see
`docs/benchmarks/2026-07-13-research-closure-summary.md`. This is a research stop, not a
GitHub Release or certification result.

The repository now contains the public 50-case input fixture and a clean Codex CLI
baseline vs baseline+Mindthus execution using empty `HOME` isolation. The v4 run keeps
the v3 isolation fix, adds strict Entry Triage runtime fingerprint coverage, and improves
the treatment score, but still misses the public positive-score threshold:
`1.447 < 1.5`.

Any future certification candidate must follow
`docs/benchmarks/v5-certification-protocol.md` before behavior fixes are counted as
score movement. No active V5 certification campaign is planned at this closure point.

The closing evidence combines the complete public V4 run with later dev and external
shadow diagnostics. The public result remains directional rather than passing:
`1.447 < 1.5`. Later diagnostics did not establish stable open-domain natural
activation, so the project stopped pathology-specific refinement instead of adding
another prompt, threshold, matcher, or team-authored case set.

Certification remains blocked pending independently owned unseen evaluation and
non-diagnostic real-task evidence. Team-authored fixtures may be reported as
diagnostics, but cannot serve as the anti-overfitting veto.

## Research Closure

The 50-case benchmark is now a release-level regression surface, not a score-optimization
loop. Existing brake diagnostics remain historical evidence. Reopening requires a
material real-task or independently owned failure, recurrence evidence, a falsifiable
mechanism, and a pre-registered stop condition.

Sections below preserve the public run and diagnostic history. They do not describe an
active repair campaign.

## Current Case Set

- Fixture: `tests/judgment_benchmark_50_cases.jsonl`
- Benchmark documentation: `docs/benchmarks/judgment-50.md`
- Case count: 50
- Negative/stay-asleep controls: 12
- Multi-turn cases: #12, #35, #50

## Required Result Fields

Future certified reports should include:

- date and commit
- baseline model and parameters
- baseline+Mindthus model and parameters
- executor type: independent SubAgent or CLI harness
- installed-code fingerprint
- hot-update verification evidence
- loaded files / method files
- raw response artifact path
- score record artifact path
- judge model and blind-grading setup
- human spot-check sample and disagreement handling
- positive mean score
- final-answer negative false wake-up rate
- runtime-event negative false wake-up rate
- first-sentence lock rate
- verdict-commitment / anti-mush rate
- over-forced verdict rate
- Anti-Spiral brake execution rate
- expected-owner-loaded rate
- positive expected-owner-loaded rate
- negative runtime stay-asleep rate
- required-visible-action rate
- loaded-required-visible-action rate
- owner-fidelity verdict counts
- headline delta: treatment - baseline

## Latest Full 50-Case Run

- Run folder: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/`
- Report: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/REPORT.md`
- Human review packet: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/HUMAN_REVIEW_PACKET.md`
- External audit handoff: `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1-v4-empty-home/EXTERNAL_AUDIT_HANDOFF.md`
- Raw run commit: `c4ee0549327e4b70840781b503c0921ce839b314`
- Tag: none; this run is after `v1.4.3-hotfix.1`
- Fixture SHA-256: `ee3f348ba8a77089e0ef0d276195dfc33ea61b684c2601bd3fc6d77e57f0129c`
- Runner SHA-256: `4e11d65054abf5ead1a1638570ad0e6264222f67243dfa8b09387e1d4c3f9773`
- Baseline: `baseline-clean-v4-empty-home`
- Treatment: `baseline+Mindthus-hotfix-v4-empty-home`
- Cleanliness: generator and judge contamination were 0/50 for both variants.
- Activation: treatment loaded Mindthus in 18/38 positive cases and 0/12 negative cases.
- Human-review caveat: #32 shows runtime/event-level Mindthus/3L5S over-wake even though
  the final-answer judge false-wakeup rate is 0.000.

## Results

| Variant | Positive mean | Final-answer negative false wake-up rate | First-sentence lock rate | Verdict-commitment / anti-mush rate | Over-forced verdict rate | H-group brake rate |
| --- | --- | --- | --- | --- | --- | --- |
| baseline v4 | 1.184 | 0.083 | 0.625 | 0.629 | 0.150 | 0.250 |
| baseline+Mindthus hotfix v4 | 1.447 | 0.000 | 0.706 | 0.824 | 0.050 | 0.500 |

Headline delta: positive mean `+0.263`, overall mean `+0.240`, first-sentence lock
`+0.081`, verdict-commitment / anti-mush `+0.195`, over-forced verdict `-0.100`.

Do not quote this as a passing benchmark. The v4 execution is clean and directionally
better, but the treatment positive mean is `1.447`, below the `1.5` public target.
Also do not quote `0.000` false wake-up as zero runtime over-wake; it is a final-answer
judge-field metric.

The archived V4 result table predates V5 runtime-event telemetry and therefore does not
include a certified runtime-event false wake-up column.

Key remaining hard failures under treatment: #4, #8, #13, #17, #33, #34, and #37.

## Latest V5 Diagnostic

### Brake Implicit-Trigger And Pressure-Contract Dev Diagnostic

- Run folder: `docs/benchmarks/runs/2026-07-09-brake-implicit-pressure-dev/`
- Report: `docs/benchmarks/runs/2026-07-09-brake-implicit-pressure-dev/REPORT.md`
- Implementation commit under test: `d66ffb4`
- Mode: `--v5-semantic-triage-hints`, no case-id register hints; diagnostic only.
- Trigger repair: #33/#34 brake semantic features now use
  `inferred_signal: repeated_local_repair_action`; matcher terms no longer include
  explicit same-class marker words such as `同类`, `类似`, `同一类`, `都是`, or `一样`.
- Loaded-action repair: the pressure-round contract allows emergency concession only as
  a bounded emergency with all three visible elements: one-time, no baseline lift, and
  structural repair deadline.
- Public implicit-trigger positives: organization/process and documentation exception
  scenarios, `n = 3`, scores `2/2/2` for both cases, loaded owner `3l5s` in all repeats.
- Public pressure positive: two-turn non-code pressure case, `n = 3`, scores `2/2/2`,
  loaded owner `3l5s` in all repeats.
- Public near negative: mixed unrelated prior changes, `n = 3`, scores `2/2/2`,
  runtime owner `[]` and runtime false wake-up `0/3`.
- Aggregate: positive mean `2.000 / 2.000 / 2.000`, expected-owner-loaded rate
  `1.000 / 1.000 / 1.000`, required-visible-action rate `1.000 / 1.000 / 1.000`,
  negative runtime-event false wake-up `0.000 / 0.000 / 0.000`.

Historical interpretation at the time of this run: the dev repair addressed the second
external shadow retest's two public failure attributions and awaited another independent
variant. The 2026-07-13 research closure supersedes that planned retest; this result remains
diagnostic, not certification.

### Brake Semantic-Generalization Dev Diagnostic

- Run folder: `docs/benchmarks/runs/2026-07-09-brake-generalization-dev/`
- Report: `docs/benchmarks/runs/2026-07-09-brake-generalization-dev/REPORT.md`
- Implementation commit under test: `25e2c28`
- Mode: `--v5-semantic-triage-hints`, no case-id register hints; diagnostic only.
- Trigger repair: #33/#34 brake semantic features now use same-class local repair count
  `>= 3` plus the next same-class repair request, without code-domain matcher words.
- Public non-code dev positives: organization/process and documentation exception
  scenarios, `n = 3`, scores `2/2/2` for both cases, loaded owner `3l5s` in all repeats.
- Public near negative: mixed unrelated prior changes, `n = 3`, scores `2/2/2`,
  runtime owner `[]` and runtime false wake-up `0/3`.
- Aggregate: positive mean `2.000 / 2.000 / 2.000`, expected-owner-loaded rate
  `1.000 / 1.000 / 1.000`, required-visible-action rate `1.000 / 1.000 / 1.000`,
  negative runtime-event false wake-up `0.000 / 0.000 / 0.000`.

Historical interpretation at the time of this run: the dev repair cleared the public
non-code migration check and kept the near negative asleep. The 2026-07-13 research closure
supersedes the planned shadow rerun; the prior external failure remains unresolved.

### V5 Naturalization Diagnostic

- Run folder: `docs/benchmarks/runs/2026-07-08-v5-naturalization/`
- Report: `docs/benchmarks/runs/2026-07-08-v5-naturalization/REPORT.md`
- Implementation commit under test: `9d31aea`
- Mode: diagnostic host hints only; not a certification candidate and not a shadow-set
  substitute.
- #17 full-config/register-hint probe: `5/5` score `2`, loaded owner `edsp`, required
  visible action present.
- #104 semantic triage positives: 9 registered targets, `n = 3`, expected-owner-loaded
  `9/9` in every repeat, no no-load or wrong-owner cases.
- #104 semantic triage positive means: `1.889 / 1.889 / 1.889`; residual loaded-action
  quality gaps remain (#13 in repeats 1-2, #49 in repeat 3).
- Negative controls: final-answer false wake-up `0/12`, runtime-event false wake-up
  `0/12`, #25 loaded owner `[]`.

Interpretation: disease-level semantic triage now solves the public 9-case no-load
activation target in diagnostic mode, and the #25 MPG-AQM evidence-review over-wake is
cleared. This is still not certification: the route uses host hints, the shadow set is
not independently owned, and loaded-action quality residuals remain.

### Register Action-Probe Diagnostic

- Run folder: `docs/benchmarks/runs/2026-07-08-v5-register-action-probes/`
- Report: `docs/benchmarks/runs/2026-07-08-v5-register-action-probes/REPORT.md`
- Commit under test: `4cbba4f`
- Mode: `--v5-register-hints`, diagnostic only.
- Caveat: #8/#13/#37/#49 were cross-reviewed as narrow-fitting suspect pending #108.
  Do not cite the four focus-case green result as disease-level generalization evidence
  until a post-#108 run supersedes it.

### Issue 108 Generalized Probe Diagnostic

- Run folder: `docs/benchmarks/runs/2026-07-09-issue-108-generalized-probes/`
- Report: `docs/benchmarks/runs/2026-07-09-issue-108-generalized-probes/REPORT.md`
- Implementation commit: `9825730`
- Run commit: `6d42d4d`
- Mode: diagnostic host hints only; not a certification candidate and not a shadow-set
  substitute.
- Original public #8/#13/#37/#49 register-hint n=3: score-2 `11/12`, score-1 `1/12`,
  expected-owner-loaded `12/12`, required-visible-action `11/12`.
- Surface-changed #108 variants semantic-triage n=3: score-2 `24/24`,
  expected-owner-loaded `24/24`, required-visible-action `24/24`.
- Residual: original #13 repeat 3 scored `1` because the legacy public rubric still
  asks for coffee-shop-specific dimensions. The probe must not regain those public-case
  terms merely to satisfy the old rubric.

### Register-Hint Diagnostic

- Run folder: `docs/benchmarks/runs/2026-07-08-v5-register-hints-diagnostic/`
- Report: `docs/benchmarks/runs/2026-07-08-v5-register-hints-diagnostic/REPORT.md`
- Raw answer generation commit: `98aebe65afc6e35523062a164e70622c8c94209b`
- Summary reanalysis commit: `8b803923f986e3a38508db6b3dd0bfc543b1832f`
- Mode: `--v5-register-hints`, diagnostic only; not natural activation and not a
  certification candidate.
- Target repeats: 9 registered no-load target cases, `n = 3`
- Target positive mean: `1.667 / 1.778 / 1.778`
- Target expected-owner-loaded rate: `1.000 / 1.000 / 1.000`
- H-group brake rate: `1.000 / 1.000 / 1.000`
- Negative controls: final-answer false wake-up `0/12`, runtime-event false wake-up
  `1/12`, register hints applied `0/12`

Historical interpretation at the time of this run: the host-hint register mechanically
solved public no-load activation in diagnostic mode, while #17 remained a stable
loaded-but-wrong-action failure. No active certification campaign now follows from this
diagnostic result.

Wording-clause disposition: the retained 3L5S brake wording, EDSP anti-mush wording,
SELA build-vs-rent boundary wording, and MPG method-reference boundary wording are
non-certifying. They are retained only as documented, unverified wording cleanup and
should be replaced or backed by mechanical hooks, calibration anchors, or repeatable
telemetry before being counted as behavior progress.

## Current Disposition

- No active brake-specific stabilization or certification campaign is planned.
- Issues #104-#107 are closure or known-limitation work, not the current product
  roadmap.
- Future benchmark changes must preserve separate final-answer, runtime-event,
  owner-fidelity, and loaded-action evidence.
- Raw run output follows
  `docs/benchmarks/run-artifact-retention-policy.md` for new campaigns.
- Product work returns to explicit invocation, installation, public/runtime
  documentation boundaries, and real-task evidence.

Historical V4 and V5 reports remain archived under their original runner SHA. Their
diagnostic results must not be promoted into a passing certification claim.
