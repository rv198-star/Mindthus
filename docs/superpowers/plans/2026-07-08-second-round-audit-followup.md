# 2026-07-08 Second-round Audit Follow-up Plan

For agentic workers: this plan tracks the second external audit supplement after the
`v1.4.3-hotfix.1` benchmark work. Its job is to prevent duplicate fixes and to keep
public benchmark claims tied to evidence.

## Goal

Confirm the second-round audit findings, map every item to an action or defer reason,
and execute the smallest evidence-backed follow-ups needed before another benchmark
claim is made.

## Current State

- Branch: `codex/issues-91-100-hotfix`.
- Hotfix implementation commit: `662bc20`.
- Recorded benchmark/evidence commit: `aaa01b4`.
- Tag `v1.4.3-hotfix.1` points at `662bc20`; benchmark records live after the tag.
- Public issues `#91` through `#100` are all open.
- New follow-up issue created from this audit: `#101` public methodology docs versus
  agent runtime instruction surfaces.
- Full v3 benchmark is intentionally not part of this batch unless the user explicitly
  re-authorizes it; this plan prepares the protocol and cleanup work.

## Evidence Sources

- External audit supplement:
  `/Users/william/Downloads/Mindthus 再审计补充材料 · 修复后评估用（第二轮） a734917473c74f1f9df2b379f32040ba.md`
- Benchmark report:
  `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/REPORT.md`
- Case fixture:
  `tests/judgment_benchmark_50_cases.jsonl`
- Calibration fixture:
  `skills/using-mindthus/resources/calibration-pairs.yaml`
- Open GitHub issues:
  `#91` through `#100`
- Independent checks already completed in this session:
  Whole Elephant/calibration surface, 50-case v2 run records, and methodology
  doc/runtime-instruction leakage.

## Intake Matrix

| ID | Audit claim | Confirmed state | Decision |
| --- | --- | --- | --- |
| A1 | #91 needs the 50 cases themselves. | Implemented in `tests/judgment_benchmark_50_cases.jsonl`; report links the run. | No duplicate fixture work; update #91 with what remains. |
| A2 | #91 needs anti-overfit/shadow discipline and multi-turn execution. | Shadow warning exists; real v2 run is contaminated by host Superpowers; multi-turn exists but not fully scripted to ideal transcript level. | Keep as #91 follow-up: v3 empty-HOME protocol, activation rate, hard contamination fail. |
| A3 | #100 says calibration only has three pairs and no mush/multi-turn. | Obsolete. Current fixture has six pairs including balanced mush, pressure, and user-owned tradeoff guardrail. | Comment on #100 and reframe remaining work as behavior/routing stability. |
| A4 | Whole Elephant/direct answer contract already overlaps the new "definition authority" proposal. | Confirmed in `whole-elephant-protocol.md`, fidelity contract, and tests. | Do not add another philosophy layer; only patch missing measurable behavior. |
| A5 | #37 proves "loaded Mindthus" can still fail by answering balanced mush. | Confirmed: treatment #37 loaded `using-mindthus`, `mpg`, and `sela`, then failed. | Add a routing/activation regression for display-scaling/anti-mush after issue triage. |
| A6 | #50 pressure case is not a clean pass. | Confirmed: treatment score is partial, not hard zero; loading did not naturally reach Mindthus. | Track as multi-turn pressure activation follow-up, not evidence that method content is absent. |
| A7 | Group G does not need wholesale rewrite. | Confirmed: #31/#32 are stable; #30 is the real prompt/rubric edge. | Fix #30 or mark it as fixture v2 cleanup; avoid rewriting all G cases. |
| A8 | #48 and #49 need rubric cleanup. | Confirmed: #48 is first-sentence sensitivity; #49 is a real AQM boundary/rubric edge. | Include in fixture v2 cleanup before next public run. |
| A9 | `docs/methodologies` contains agent runtime command language. | Confirmed in `sela.md`, `mpg.md`, `wae.md`, and `primitives/whole-elephant-protocol.md`. | Create or update issue; treat as #92-adjacent but distinct from phrase anchors. |
| A10 | #92 phrase anchor issue extends beyond README/using-mindthus. | Confirmed: `test_sela_contract.py`, `test_mpg_contract.py`, and router tests assert literal phrases in methodology docs. | Expand #92 scope with exact files and replacement direction. |
| A11 | #93 may now be done. | Confirmed: no-script fallback text and tests exist. | Comment with evidence; close only after maintainer/user agrees or after verification pass. |
| A12 | #95-#99 need ordinary closure evidence. | Confirmed by targeted tests and issue comments on #95, #96, #97, #98, and #99. | Done for closure evidence; leave final closing to maintainer/user after full-suite verification. |
| A13 | N-3 hidden/occluded paragraphs should be locally checked. | Not yet separately checked; low-cost manual review. | Add to methodology-doc cleanup pass, no separate issue. |
| A14 | Description compression, Whole Elephant split, install script, English docs. | Mostly judgment/maintainability items, not hard benchmark evidence. | Defer until after certified v3 data or a separate maintainer request. |

## Execution Order

### Step 1: Stabilize the Audit Ledger

Status: completed for this batch.

Actions:

1. Keep this plan in `docs/superpowers/plans/2026-07-08-second-round-audit-followup.md`.
2. Keep mission state in `.tplan/missions/second-round-audit-followup-2026-07-08/`.
3. Add evidence entries for the subagent findings and issue updates.

Acceptance:

- Every audit claim above has a decision.
- The plan names the exact issue or future cleanup bucket for each accepted claim.

### Step 2: Update Public Issue Scope

Status: completed for first-pass public triage.

Actions:

1. Comment on `#91`:
   - 50-case fixture exists.
   - v2 run exists but is degraded by host Superpowers contamination.
   - v3 certification should use empty `HOME`, separate `CODEX_HOME`, hard contamination
     fail, and activation-rate reporting.
   - Fixture v2 cleanup should cover #30, #48, #49, and multi-turn transcript fidelity.
2. Comment on `#92`:
   - Phrase-anchor work must include `docs/methodologies`, SELA/MPG contract tests, and
     router tests.
   - Replacement target is semantic shape assertions and structured contract checks.
3. Comment on `#93`:
   - No-script fallback appears implemented.
   - Verification command and exact tests should be recorded before closure.
4. Comment on `#100`:
   - Current issue body is stale relative to the branch.
   - Remaining acceptance should focus on behavior/routing stability, not adding already
     present calibration pairs.
5. Create a new issue only if `#92` cannot carry the public-doc/runtime-instruction split.

Completed links:

- `#91`: <https://github.com/rv198-star/Mindthus/issues/91#issuecomment-4909518883>
- `#92`: <https://github.com/rv198-star/Mindthus/issues/92#issuecomment-4909520325>
- `#93`: <https://github.com/rv198-star/Mindthus/issues/93#issuecomment-4909522653>
- `#100`: <https://github.com/rv198-star/Mindthus/issues/100#issuecomment-4909525994>
- `#101`: <https://github.com/rv198-star/Mindthus/issues/101>
- `#95`: <https://github.com/rv198-star/Mindthus/issues/95#issuecomment-4909567615>
- `#96`: <https://github.com/rv198-star/Mindthus/issues/96#issuecomment-4909568557>
- `#97`: <https://github.com/rv198-star/Mindthus/issues/97#issuecomment-4909569508>
- `#98`: <https://github.com/rv198-star/Mindthus/issues/98#issuecomment-4909570556>
- `#99`: <https://github.com/rv198-star/Mindthus/issues/99#issuecomment-4909571563>

Acceptance:

- GitHub issue comments or new issue links are recorded in this plan or tplan evidence.

### Step 3: Prepare v3 Benchmark Protocol Without Running It

Status: protocol support implemented; full v3 run still intentionally not executed.

Files:

- `scripts/run-judgment-benchmark-cli.py`
- `docs/benchmarks/runs/2026-07-08-v1.4.3-hotfix.1/REPORT.md`
- future run directory under `docs/benchmarks/runs/`

Actions:

1. Add runner options or documented command wrappers for empty `HOME` plus separate
   `CODEX_HOME`.
2. Promote contamination flags from passive metadata to optional hard failure.
3. Report activation rates as first-class metrics:
   - Mindthus loaded.
   - Superpowers loaded.
   - no skill/plugin loaded.
   - forced-command versus natural activation when detectable.
4. Keep judge and generator isolation separate.
5. Do not execute the full v3 run in this batch.

Acceptance:

- A dry-run or unit-level verification proves the runner can be configured for v3.
- No new benchmark claim is made from v2 data beyond degraded/diagnostic language.

Completed:

- `scripts/run-judgment-benchmark-cli.py` now supports `--home`, `--empty-home-root`,
  and `--fail-on-contamination`.
- The runner writes `activation-summary.json` and embeds activation metrics in
  `summary.json`.
- Generator and judge contamination can be promoted to a nonzero exit before a run is
  treated as certification evidence.
- Verification: `python3 -m unittest tests.test_judgment_benchmark_cli_runner -v`
  passed 12 tests.

### Step 4: Fixture v2 Cleanup

Status: completed for confirmed post-v2 edges.

Files:

- `tests/judgment_benchmark_50_cases.jsonl`
- benchmark docs and report notes if a new fixture version is introduced

Actions:

1. Fix or explicitly mark #30 as a prompt-design edge because the current prompt asks for
   a document rewrite without providing the document body.
2. Recheck #48 first-sentence rubric so it distinguishes "not perfect first sentence" from
   "wrong judgment".
3. Recheck #49 so AQM misuse is treated as a real boundary breach when applicable, not just
   rubric strictness.
4. Preserve the current v1 fixture and v2 run records; do not mutate historical results.

Acceptance:

- Fixture changes are versioned or documented so v1/v2/v3 results remain comparable.

Completed:

- Case #30 now includes the actual thin risk-assessment body instead of referring to an
  absent attachment.
- Case #48 now distinguishes a soft first-sentence denial from a full definition-owner
  lock.
- Case #49 now makes the no-data/AQM boundary explicit and rejects decisions computed
  from invented numbers.
- `docs/benchmarks/judgment-50.md` records that historical reports remain tied to their
  fixture SHA-256.
- Verification: `python3 -m unittest tests.test_judgment_benchmark_cases -v` passed 4
  tests, and JSONL parsing confirmed 50 records.

### Step 5: Runtime Instruction Boundary Cleanup

Status: tracked in `#101`; not implemented in this batch.

Files:

- `docs/methodologies/sela.md`
- `docs/methodologies/mpg.md`
- `docs/methodologies/wae.md`
- `docs/methodologies/primitives/whole-elephant-protocol.md`
- corresponding `skills/*/SKILL.md` and `skills/*/resources/methodology.md`
- `tests/test_mindthus_router_contract.py`
- SELA/MPG/router contract tests

Actions:

1. Decide which lines are public methodology versus agent runtime instruction.
2. Move command obligations such as "must read `mindthus:mpg`" out of public methodology
   docs if they are meant only for skill runtimes.
3. Replace exact phrase anchors with semantic or structured checks where the test is
   shaping docs toward marker stuffing.
4. Preserve actual runtime safety where agent skills need mandatory read/validation rules.

Acceptance:

- Public docs read as methodology, not as hidden agent command scripts.
- Runtime skill surfaces still contain the actionable obligations needed by agents.
- Tests pass without requiring brittle exact wording in public docs.

### Step 6: Behavior Regression Targets

Status: completed for this batch.

Targets:

- Display-scaling balanced mush case (#37).
- Multi-turn pressure survival (#50 and calibration pressure pair).
- Definition-authority first sentence without over-forced verdicts.

Actions:

1. Add the smallest regression check that would fail on the current #37 treatment answer.
2. Keep user-owned tradeoff guardrails active so "verdict rate" cannot Goodhart into
   forced decisions.
3. Treat failures as routing/activation failures unless the loaded method content is proven
   absent.

Acceptance:

- Regression checks separate "method not loaded", "wrong method routed", and "loaded but
  output shape failed".

Completed:

- The CLI runner summary now includes `failure_diagnostics`, separating failed cases by
  Mindthus loaded, Superpowers loaded, no commands loaded, and multi-turn pressure.
- This makes #37-style loaded-but-failed cases and #50-style no-load pressure failures
  visible in future v3 runs without claiming the behavior is already fixed.
- Verification: `python3 -m unittest tests.test_judgment_benchmark_cli_runner -v`
  passed 12 tests.

### Step 7: Verify and Publish

Status: pending.

Commands:

```bash
python3 -m unittest tests.test_using_mindthus_whole_elephant_contract -v
python3 -m unittest tests.test_mindthus_router_contract -v
python3 -m unittest discover -s tests -q
```

Acceptance:

- Verification output is recorded.
- Changes are committed and pushed on `codex/issues-91-100-hotfix`.
- Final notes list which items are closed, which are tracked, and which are intentionally
  deferred.

Completed verification:

- `python3 -m unittest discover -s tests -q`: 542 tests passed.
- `python3 -m pytest -q`: 542 tests passed, 45 subtests passed.

## Non-goals For This Batch

- Do not run the full v3 benchmark unless explicitly re-authorized.
- Do not claim a clean causal Mindthus lift from the v2 run.
- Do not rewrite all Group G cases; #30 is the confirmed edge.
- Do not chase description compression, install script cleanup, English copy, or broad
  Whole Elephant splitting until benchmark evidence or maintainer priority says they matter.
- Do not add another conceptual layer for definition authority; use the existing Whole
  Elephant, Aspect Ownership, Decision Context Calibration, and calibration fixtures.
