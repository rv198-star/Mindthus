# Typed Decision — recovery entry

Active branch: `experiment/typed-decision-runtime`.
Remote base HEAD: `1d29b980355c67c9b57c44004378877cc429c9f9`.
Formal main: `1527f32b99c375db9ff73f80812c644686a6576a` (GitHub API rechecked).
Local main was `7c0eab827547afe2b2a5a1aa972c7a8fb5606db8` and was not advanced.

## Current local workspace

Workspace: `/Users/william/Projects/Github/Mindthus`.
Owner approved this location on 2026-09-22. The branch was fetched and checked out at
`1d29b98`, then all 14 recovery files were applied and verified byte-for-byte against
`recovery-manifest.json`. Runtime, source-file and development freeze hashes match.
The preexisting untracked files were preserved. Local main was not changed.

The previous `/Volumes/Data/My Projects/Github` directory disappeared during handoff.
The independent recovery bundle remains at
`/Users/william/Documents/Codex/2026-09-22/mindthus-c01-v2-recovery` with the original
patch, exact edit operations and test logs. It is now historical recovery evidence,
not the active workspace. OCI is no longer the working location.

## Goal and boundaries

Complete #211 C01 in sequence: contract correction, offline verification, frozen Chinese
development, official TypeSafe semantic trial, at most one bounded semantic revision,
independent holdout once, then A/B/C. #212 stays conditional and unstarted. Keep formal
main, Engine/Provider architecture, #112 HOLD and #207 unchanged. No generic graph platform
or dynamic designer. Confidence, interface compatibility and schema tests confer no
behavioral qualification or execution permission.

Credential dependency resolved on 2026-09-22: the owner linked task
`01a0c4f6-befa-7f41-b4b0-27e77e38892e`, which identified an existing local `.env`
containing both service keys (mode 600). The official key was loaded directly into
process memory from that user-authorized file. No new credential file was created in
Mindthus. OpenRouter was not called. Exact-key scanning found neither key in any trial
JSON artifact. Do not copy keys into source, Git, issue text or diagnostic logs.

## Completed source slice

C01-v2 has J1 `entry_mode` plus J2 `unresolved_obligation` sharing one State/batch, explicit
`unclear`/no-match, deterministic D0 field/provenance/freshness/advisory-scope checks,
owner selection/binding only after intervention, then complete selected SKILL contract
read and dependent applicability. See `c01-v2-contract.md`. The facts-sufficiency and
hard-judgment questions were removed; old trace hard-judgment is conservatively derived.

Known/observed obligations survive sibling failures and cannot be cleared by a model.
Explicit method requests do not prove applicability. Both accepted and rejected
applicability bind the selected method hash; unavailable contracts return missing context.
Engine/serving/resolved-runtime implementation remains unchanged.

## Evidence

C01-v2 functional source commit: `61063b773698368e55e1c9bd122fc510dadc525a`.

`verification.json` binds the final runtime digest and source-file hashes. Prior evidence
is preserved in `verification-engine-serving-e9e78cc.json`.

- 61 typed-decision tests passed.
- Final source full suite: 1145 tests run, 0 failures/errors, 7 skipped on Python 3.12.9.
  Five skips need Pillow; two need jsonschema. The optional dependency download failed
  with PyPI TLS EOF. The initial system-Python 3.9 run failed on preexisting import syntax;
  that is not the accepted full-suite run.
- Test Lifecycle remains 80/80.
- Exact-operation recovery was checked with 61 targeted tests and an end-to-end probe:
  first 3 batches; resume 0 new / 3 reused; same run ID; SRA selected; native load unobserved.
- These are mechanical checks and author review, not independent semantic qualification.

## Local live carrier (engineering complete)

Carrier source commit: `ff4b1d309c383d3dd380dd573b428115bd9aa3f8`.
`verification-live-carrier.json` binds the new runtime/source digest and evidence; it does
not replace the earlier C01 evidence in `verification.json`.

- 75 typed-decision tests passed (14 added carrier/credential tests, injected transport only).
- Final full suite: 1159 tests run, zero failures/errors, 7 optional-dependency skips.
- Test Lifecycle: 80/80. Frozen-file hashes, C01 vendor scan and secret-pattern scan passed.
- Existing Engine/Provider/Resolved Runtime abstraction and all frozen C01 semantics unchanged.
- New Session admission binds exact egress, runtime/serving, cumulative limits and cost reserve.
- The evaluator separates expected labels, reports all routes/pairs/failures, and stops on
  catastrophic errors. A completed campaign cannot be rerun; unknown calls cannot be retried.

Official TypeSafe development is prepared at
`/Users/william/Documents/Codex/2026-09-22/mindthus-c01-typesafe-dev-1/campaign.json`:
26 cases, 225 prospective exact request hashes, at most 78 calls / 300 inference seconds /
USD 0.25. The first real development batch failed local validation (`ContractError`)
and the immutable campaign stopped at D01, with zero accepted semantic batches and
25 cases unrun. The original response and precise validation cause were not retained;
the cause remains unknown. Do not infer Jev contradiction, failed semantic choice,
key failure or a specific rounding defect from this record.

Three separately admitted one-call diagnostics followed (all on official TypeSafe):
Chinese direction, explicitly excluded D01 replay, and a probability-format probe.
All passed adapter validation with resolved model `jev-1.13.0`; the D01 diagnostic
returned `mindthus_intervention + clear`. None replaces the original failure or counts
toward development acceptance. The final probe predeclared a stop; do not keep retrying.

See `c01-v2-typesafe-dev-1.json` for complete results and artifact hashes. Four total
attempts reserve USD 0.010752. The three diagnostics reported 3723 input / 221 output
tokens, estimated USD 0.000156366 at the documented rate. The initial failure's tokens
and cost are unknown, so total actual cost remains unknown. Original campaign,
per-probe intents/outcomes and summary remain intact. No source or validator was changed
in response to this observation. No OCI command was executed.

## Development freeze and next step

`c01-v2-development-freeze.json` binds 26 Chinese synthetic cases in 13 paired families,
all relevant canonical SKILL sources, the graph, source and semantic plan. Expected labels
are separate author judgments. Official development was attempted and stopped on a
technical validation failure; semantic revisions used: 0/1. Holdout has not been created/frozen or evaluated.

Next: repair the narrow failure-observation gap before any new technical recovery run.
Retain a bounded local validation code and safe response/usage evidence, without remote
exception text, headers or credentials. The original failure cannot be reconstructed;
none of the diagnostic successes explains it. A recovery run needs a named technical
delta, parent failure identity and cumulative accounting, not deletion/reset of this
trial. Keep the C01 contract, case labels, validators and one semantic-revision allowance
unchanged until an observed failure justifies a change. Unchanged passed tests need no
rerun. OpenRouter remains a separately reported backup, not an automatic substitution.

Only after development stabilizes may holdout be frozen and accepted once. Full A/B/C,
native host consumption, net-value evidence and #212 remain unstarted. See
`c01-v2-semantic-plan.md` for frozen development scoring and separation rules.

## Resume discipline

Read this file and Git status before editing. Verify source hashes before reusing evidence.
Do not rerun unchanged passed work merely to recover context. Goal, criteria, permissions
or semantic revisions require a named delta; preserve old records and data labels.
