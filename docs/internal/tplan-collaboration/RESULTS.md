# Issue #246 Development Results

Date: 2026-11-17. Development status: implementation and development self-audit complete; independent source-session audit pending.

## Source And Environment

- Issue: [Mindthus #246](https://github.com/rv198-star/Mindthus/issues/246)
- Source base: `520376990613eb34bfdbbdaa4fc4ba227d4fbcfb`
- Frozen design: `d7838a4ddd6255269e6c51698d9433e3945121f2`
- Branch: `codex/issue-246-tplan-collaboration`
- Isolated checkout: `/Users/william/.codex/worktrees/mindthus-246-collaboration/Mindthus`
- Required RED commit: `db0f1375a` (`test(tplan): define collaboration runtime contract and RED cases`)
- Model/reasoning configuration supplied to this session: DeepSeek V4.1 Flash, `xhigh`. The local tool runtime does not expose a separate model-attestation field.
- CI-compatible isolated runtime: CPython 3.11.11 at `/private/var/tmp/mindthus-246-py311`.
- Test `TMPDIR`: `/private/var/tmp`, avoiding the macOS `/var` to `/private/var` alias in H1 canonical-directory fixtures.

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

The reproducible agent behavior replay is in `tests/tplan/collaboration_behavior_replay.jsonl`. It records four multi-turn decisions and next actions, not a real three-session host run.

- T26: unrelated logging/cache suggestions remain deferred; no task or delegation is created from the suggestion alone.
- T27: B-owned debugging detail is routed back to B while A retains contract and acceptance responsibility.
- T28: high-frequency progress and repeated review text are batched; A records a target-relevant next result.
- T29: evidence-backed path revision and an explicit user scope change update the affected path/delegation while preserving history and authority.

These replay records are `source_audit=pending`; the source session must review the actual decisions and next actions. The replay is not presented as host E2E.

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
| T17 | PASS, mechanical | A defect after task completion blocks current acceptance until a success-critical repair task and later adoption/review. |
| T18 | PASS, mechanical | Duplicate intent conflicts; unknown delivery is queried before replacement; no participant-side dedup service is required. |
| T19 | PASS for contract/package; host E2E pending | Five packaged A-only layouts execute snapshot/enable; B/C need no runtime in the protocol. Real B/C host isolation remains acceptance. |
| T20 | PASS, mechanical/replay | Normal-language return is stored with source and normalized association/evidence. |
| T21 | PASS, mechanical | Missing task/round/contract association stays `needs_association`; no task or acceptance is guessed. |
| T22 | PASS, mechanical | First authorized division enables collaboration without a mode phrase and preserves objective, acceptance, tasks, and focus. |
| T23 | READY for source audit | Behavior replay keeps reference-only work on the ordinary path and creates no delegation. |
| T24 | PASS, mechanical | `snapshot.get` reconstructs unresolved responsibility, feedback, external work, waiting, and next action. |
| T25 | READY for source audit | Behavior replay records a current-session-only scope, no new delegation, and preserved history. |
| T26 | READY for source audit | Agent behavior replay only; formal source-session review pending. |
| T27 | READY for source audit | Agent behavior replay only; formal source-session review pending. |
| T28 | READY for source audit | Agent behavior replay only; formal source-session review pending. |
| T29 | READY for source audit | Agent behavior replay plus mechanical path-adjustment test; formal source-session review pending. |

## Verification

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
- Source-session semantic audit of T04-T05 and T23-T29 decisions and next actions.
- Any merge, release, deployment, production Host activation, installed-Skill update, or ROI Beta action remains outside this development authorization.

## Reproduction And Rollback

Use the branch and isolated checkout above. Re-run the five commands with Python 3.11 and `TMPDIR=/private/var/tmp`. The RED commit `db0f1375a` shows the original failing contract tests; the implementation commits turn those tests green. Rollback is a normal branch revert to source base `520376990`; no external state was migrated or deployed.

