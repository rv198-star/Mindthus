# Issue #246 Development Results

Date: 2026-11-17. Development status: R5 C1 repair and regression verification complete; exact-head independent re-audit pending. R4 B1 paths were independently accepted in REVIEW-R4. Source-Agent controlled goal-preservation acceptance is recorded in REVIEW-R3; real host E2E remains pending.

## Source And Environment

- Issue: [Mindthus #246](https://github.com/rv198-star/Mindthus/issues/246)
- Source base: `520376990613eb34bfdbbdaa4fc4ba227d4fbcfb`
- Frozen design: `d7838a4ddd6255269e6c51698d9433e3945121f2`
- Branch: `codex/issue-246-tplan-collaboration`
- Isolated checkout: `/Users/william/.codex/worktrees/mindthus-246-collaboration/Mindthus`
- Required RED commit: `db0f1375a` (`test(tplan): define collaboration runtime contract and RED cases`)
- Implementation commit: `72570e5d3` (`feat(tplan): add goal-preserving collaboration runtime`)
- Model/reasoning configuration recorded for the initial development session: DeepSeek V4.1 Flash, `xhigh`. The local tool runtime does not expose a separate model-attestation field.
- CI-compatible isolated runtime: CPython 3.11.11 at `/private/var/tmp/mindthus-246-py311`.
- Final R4 test `TMPDIR`: `/private/tmp`, a writable canonical path for this sandbox. Earlier batches used `/private/var/tmp`. Explicit bytecode compilation uses an isolated temporary cache.

## Delivered Runtime

- Added optional `mission.json.collaboration` using `tplan.collaboration.v0.1`.
- Added pure schema, transition, projection, completion, and reducer logic in `skills/tplan/scripts/collaboration.py`.
- Added the locked JSON transaction CLI in `skills/tplan/scripts/collaboration_runtime.py`.
- Added internal collaboration writer authority. Public `write_mission` and `commit_mission_state` preserve the state and reject creation, removal, or mutation.
- Reused the existing Mission lock, journal, roll-forward recovery, Guard, runtime provenance, task normalization, evidence references, H1 authority, and Q2 command-result authority.
- Added focus-preserving delegated task updates without changing the default `set_task_status` behavior.
- Added collaboration feedback collection to Mission Pulse across non-active and completed tasks.
- Added the resume projection: objective, coordinator responsibility, acceptance gaps, focus, pending feedback, external work, waiting conditions, resume basis, and next action.
- Added task/Mission completion gates for pending feedback, current adoption, and required review bound to reviewer, delegation, round, contract, artifact digest, and scope.
- Added command replay/conflict history, stale-snapshot and stale-generation rejection, capacity bounds, and explicit original-writer recovery.
- Added Skill, schema, lifecycle, Codex host, and collaboration resource documentation.
- Added collaboration capability/scripts to the runtime manifest and verified five clean packaged layouts.

## Goal-Preservation Evidence

Actual source-Agent goal-preservation decisions for T23/T25/T26–T29 were executed and
accepted in [REVIEW-R3.md](REVIEW-R3.md). Inputs, Agent actions, tool results and state
are recorded in `reviews/r3-audit/source-actions.jsonl` and `final-states/`, classified
`controlled_source_agent_exercise`.

The original `tests/tplan/collaboration_behavior_replay.jsonl` is preserved as
`scenario_expectation`; the R2 driver and its runtime outputs are
`scripted_runtime_scenario`. These historical mechanical fixtures and the accepted
controlled source-Agent exercise have separate evidence roles. Real A/B/C host E2E
remains in the host acceptance list below.

## T01-T29 Status

| Case | Development status | Evidence |
| --- | --- | --- |
| T01 | PASS, mechanical | A moves focus to T2; T1 feedback still surfaces in Pulse; focus remains T2. |
| T02 | PASS, mechanical | Same-source/same-content replay has one business effect; changed content conflicts. |
| T03 | PASS, mechanical | h2 remains current after a late h1 review; h1 stays historical. |
| T04 | PASS, mechanical/replay | Contract/path revision creates a new delegation contract in one transaction; source audit covers clarification semantics. |
| T05 | PASS, mechanical/replay | B-owned repair and upstream path adjustment produce separate bounded actions. |
| T06 | PASS, mechanical | Waiting state, unresolved intents, and resume projection survive reload; no task completion is inferred. |
| T07 | PASS, mechanical | Unknown send blocks same-scope execution until the original intent is reconciled. |
| T08 | PASS, mechanical | Open Guard rejects collaboration writes with unchanged Mission bytes; synthetic replay imports once after resolution. |
| T09 | PASS, mechanical/replay | Dependency versions and resume basis are stored; A can pause an invalid path and move to an independent task. |
| T10 | PASS, mechanical | External waiting uses `waiting_external`; Mission remains `active`; no polling or `requires_human` is emitted. |
| T11 | PASS, mechanical | Review source must match the configured reviewer thread/host; required reviewer, scope, and artifact digest are checked. |
| T12 | PASS, mechanical | Crash recovery, command replay, stale snapshots, capacity refusal, and one-effect roll-forward are tested. |
| T13 | PASS, mechanical | Task completion and Mission closure reject missing/current-review gaps; ordinary non-delegated tasks remain valid. |
| T14 | PASS, mechanical | Stop-requested running work keeps the scope protected until a native stopped fact is recorded. |
| T15 | PASS, mechanical | Handoff increments generation; stale writer generation is rejected before persistence. |
| T16 | PASS, mechanical/replay | Multiple pending updates produce one Pulse candidate; replay batches and resumes the mainline. |
| T17 | PASS, mechanical | Repeated repairs carry declared AC responsibility to completed current endpoints; partial or failed successor responsibility stays open. |
| T18 | PASS, mechanical | Duplicate intent conflicts; unknown delivery is queried before replacement; no participant-side dedup service is required. |
| T19 | PASS for contract/package; host E2E pending | Five packaged A-only layouts execute snapshot/enable; B/C need no runtime in the protocol. Real B/C host isolation remains acceptance. |
| T20 | PASS, mechanical/replay | Normal-language return is stored with source and normalized association/evidence. |
| T21 | PASS, mechanical | Missing task/round/contract association stays `needs_association`; no task or acceptance is guessed. |
| T22 | PASS, mechanical | First authorized division enables collaboration without a mode phrase and preserves objective, acceptance, tasks, and focus. |
| T23 | PASS, controlled source-Agent exercise; scripted runtime scenario retained separately | Source Agent kept reference-only input on the ordinary path without enabling collaboration (REVIEW-R3 / source-actions.jsonl). |
| T24 | PASS, mechanical | `snapshot.get` reconstructs unresolved responsibility, feedback, external work, waiting, and next action. |
| T25 | PASS, controlled source-Agent exercise; scripted runtime scenario retained separately | Source Agent requested stop of the existing delegation, retained the running fact and continued A’s T2 responsibility (REVIEW-R3). |
| T26 | PASS, controlled source-Agent exercise; scripted runtime scenario retained separately | Source Agent deferred/rejected scope expansion and returned to the original acceptance gap (REVIEW-R3). |
| T27 | PASS, controlled source-Agent exercise; scripted runtime scenario retained separately | Source Agent returned fixture diagnosis/repair/self-test to B and retained A’s design/acceptance responsibility (REVIEW-R3). |
| T28 | PASS, controlled source-Agent exercise; scripted runtime scenario retained separately | Source Agent batched repeated input, recorded current C PASS and requested missing artifact/run evidence before adoption (REVIEW-R3). |
| T29 | PASS, controlled source-Agent exercise; scripted runtime scenario retained separately | Source Agent paused the failed path, retained responsibility, then superseded the old Mission and created canonical objective/acceptance under explicit user goal change (REVIEW-R3). |

## Initial Verification (historical)

All final checks used the isolated Python 3.11.11 environment.

```text
python3.11 -m unittest tests.tplan.test_collaboration -v
6 tests, OK

python3.11 -m unittest tests.tplan.test_collaboration_runtime -v
18 tests, OK

python3.11 -m unittest discover -s tests/tplan -v
612 tests, OK, 1 skipped

python3.11 -m unittest tests.test_packaging_docs -v
41 tests, OK, 1 skipped

python3.11 -m unittest discover -s tests -q
1365 tests, OK, 8 skipped
```

`tests.tplan.test_command_release_pack` also ran collaboration snapshot/enable from all five generated, archived, and cleanly extracted layouts. `git diff --check` and `py_compile` passed.

The system Python 3.9 run is not the CI environment. It reports 26 unrelated baseline errors from PEP 604 annotations and Python 3.10+ `unittest.TestCase.enterContext`; those files were not changed by this branch.

## Development Self-Audit

- The primary goal remains A's actual next action against the Mission objective and acceptance; delegation, delivery, version, and waiting remain support records.
- Stale snapshots, stale coordinator generations, Guard state, runtime mismatch, invalid references, and public-writer bypass are rejected before the journal is prepared.
- Same command/request/principal replays return the original result; different content or principal conflicts. Duplicate feedback source/content is a no-op; different content conflicts.
- Current adoption and required review are version-bound. A historical PASS cannot satisfy a newer artifact, and repair does not silently rewrite completed history.
- Normal external waiting keeps Mission status `active`. Mission completion separately requires no pending feedback and current accepted versions.
- Existing H1, Q1, and Q2 authority paths remain intact; ordinary TPlan and packaged layouts pass.
- No production Mission, installed Skill, hook, release, tag, deployment, or ROI Beta state was changed.

## Remaining Host And Human Acceptance

- A real three-session A/B/C E2E with ordinary B/C conversations and no participant TPlan access.
- Real Codex peer-source identity, cross-session wake-up behavior, message redelivery deduplication, and cancellation/stop observability.
- Host enforcement of A-to-A writer binding beyond the runtime generation check.
- Exact-head source-session re-audit of R4. Actual source-Agent T23/T25/T26–T29 controlled exercise is accepted in REVIEW-R3.
- Any merge, release, deployment, production Host activation, installed-Skill update, or ROI Beta action remains outside this development authorization.

## Reproduction And Rollback

Use the branch and isolated checkout above. Re-run the commands in `reviews/r4/verification.txt` with Python 3.11, `TMPDIR=/private/tmp`, and the recorded temporary bytecode cache. The RED commit `db0f1375a` shows the original failing contract tests; the implementation commits turn those tests green. Rollback is a normal branch revert to source base `520376990`; no external state was migrated or deployed.

## R2 Repair Batch (historical, 2026-11-17)

The R1 independent audit (REVISE, 7 P1 + 3 P2) was repaired by root cause in the same
branch. See [REPAIR-R2.md](REPAIR-R2.md) for the R01-R10 mapping, before/after probe
evidence (`reviews/r2/probe-results-after.jsonl`), and executed goal-preservation
behavior evidence (`reviews/r2/behavior-execution.jsonl` + transcript). The former
ideal-answer replay file is now `scenario_expectation`; T23/T25/T26-T29 have real
runtime execution evidence. Packaged protocol + cold-start closed loop ship with the
Skill and pass from all five clean extracted layouts.

Updated verification (CPython 3.11.11): collaboration 37 passed; behavior execution 3
passed; TPlan discover 628 passed / 1 skipped; packaging docs 41 passed / 1 skipped;
full repository discover 1381 passed / 8 skipped. Real three-session host E2E and
source semantic review of the executed decisions remain pending source acceptance.

## R3 Repair Batch (historical, 2026-11-17)

The R2 independent audit (REVISE, two P1 root causes A1/A2 + R02 classification) was
repaired by root cause in the same branch. See [REPAIR-R3.md](REPAIR-R3.md).

- A1: converged current-acceptance-responsibility projection (monotonic succession,
  adoption `invalidated` flag, repair obligations carried by a bounded repair task with
  fresh acceptance/re-review). Shared by Task completion, Mission close, and resume gaps.
  Retired attempts no longer erase the obligation; older-round PASS cannot mask a newer FAIL.
- A2: non-active Mission rejects new collaboration business writes (`mission_closed`);
  reads, historical replay, and prepared-transaction recovery remain available.
- R02: driver evidence reclassified `scripted_runtime_scenario` (preset dispositions, not
  autonomous agent trade-offs); T29 second step is a coordination-summary update only;
  T23 covers no-new-delegation after enable, not entry-not-enabled. Actual agent behavior
  acceptance for T23/T25/T26-T29 is the source session's responsibility.

R2's four probes re-run against the fixed code are all correctly rejected
(`reviews/r3/probe-results-after.jsonl`). New A1/A2 regressions include the three failure
paths and positive full chains. Real three-session host E2E and source semantic review of
actual agent decisions remain pending source acceptance.

## R4 Repair Batch (historical, 2026-11-17)

R3 found one remaining P1 root cause, B1: repair acceptance fell back to any historical
PASS with an AC intersection, bypassing required review and complete/latest coverage.
[REPAIR-R4.md](REPAIR-R4.md) records the replacement rule, regression mapping and probes.

- Every repair AC now requires its latest qualified PASS in the repair task scope.
  Current delegation/adoption and mandatory review constraints remain effective.
- Native qualification, unique references, task/ancestor coverage and H1 source-version
  rules are shared with Mission closure. Independent Task acceptance retains its own scope.
- Public completion, collaboration feedback completion, Mission close, snapshot resume and
  survey resume consume the same supplied evidence snapshot.
- Eleven added regressions cover required FAIL/missing/retired review, partial coverage,
  latest FAIL, unrelated PASS, ambiguous/invalid/legacy records, valid local/delegated
  full chains, and H1 current-source versions plus independent Task scope.
- R3 source-Agent controlled exercise remains accepted; R2 driver is still
  `scripted_runtime_scenario`. No additional ideal-answer driver was added.

Final local verification: targeted Ran 58; TPlan Ran 646 / skipped 1; packaging docs Ran 41 / skipped 1; full repository Ran 1399 / skipped 8. All results OK. Commands and unittest summaries: [verification.txt](reviews/r4/verification.txt).
R4 independent mechanical probes: [probe-results-after.jsonl](reviews/r4/probe-results-after.jsonl).
Local full-suite skip count and source/CI platform counts are reported separately.
Exact-head re-audit and real host acceptance remain the next handoff; PR stays draft,
Issue open, with the original merge/release/deploy/installed-Skill/production boundary.

## R5 Repair Batch (2026-11-17, current)

R4 independently accepted the reported B1 paths and found C1: a completed repair task
could not transfer its acceptance responsibility through a further explicit repair.
[REPAIR-R5.md](REPAIR-R5.md) records the replacement rule and test mapping.

The existing responsibility edges now project each affected task's ACs through all
applicable declared successors. Effective endpoints satisfy completion, latest qualified
per-AC acceptance and mandatory current review. Uncovered ACs stay with their source;
intermediate completed tasks, invalidated adoptions and feedback remain historical.
Task, Mission and both resume views use this same projection and supplied events.

Thirteen added C1 regressions cover two/three-layer local/delegated closure, preserved
history, partial/split AC transfer, uncovered original ACs, terminal FAIL/missing review/
incomplete/partial/latest-failed acceptance, separate branch PASS and an internal cycle.
Existing B1 regressions and source-Agent controlled behavior acceptance remain in place.

Original independent C1 probes re-run: [probe-results-after.jsonl](reviews/r5/probe-results-after.jsonl).
Original B1 probes re-run: [b1-probe-rerun.jsonl](reviews/r5/b1-probe-rerun.jsonl).
Local verification: targeted Ran 71; evidence/H1 Ran 75; TPlan Ran 659 / skipped 1; packaging Ran 41 / skipped 1; full repository Ran 1412 / skipped 8. All OK. Commands and actual summaries: [verification.txt](reviews/r5/verification.txt).
Source independent re-audit: **PASS** for code head
`223b7d2b99969c6a6ee9549730d2b8a2271d2401`; see [REVIEW-R5.md](REVIEW-R5.md).
The source reran 71 targeted tests, both original C1 probes and all eight B1 probes,
and added two independent checks for late current review FAIL and mixed split-AC
successors. Exact-head CI ran 1412 tests, skipped 7, and succeeded.
The next stage is the already-listed real host acceptance. PR remains draft and Issue
open; release permissions retain the existing boundary.
