# Typed Decision — recovery entry

Active branch: `experiment/typed-decision-runtime`.
Remote base HEAD: `1d29b980355c67c9b57c44004378877cc429c9f9`.
Formal main: `1527f32b99c375db9ff73f80812c644686a6576a` (GitHub API rechecked).
Local main was `7c0eab827547afe2b2a5a1aa972c7a8fb5606db8` and was not advanced.

## Reviewed live development r1 — completed, planning gates not met

Owner requested completing tests before resolving GitHub connectivity. Source `9b4e0acc8`;
see [protocol](review-remediation/live-protocol.md), [observations](review-remediation/live-observation.json),
and [disposition](review-remediation/live-disposition.md).
All 17 prelisted items ran once (N01 excluded beforehand); 19 official TypeSafe calls,
resolved model `jev-1.13.0`, no technical failure or drift, no unrun/ad hoc retry.
C01: joint2/3, entry3/3; N04 selected SRA then applicability=unclear, not a wrong owner.
C02: joint6/8, route7/8, utility7/8, raw action6/8, support7/7 (N10 unscored).
Fixed-artifact fidelity:6/6 from two parent scenarios; not real generated artifacts.
N08 unsupported action was blocked by correct missing-source routing; N12 missed a
required reason. Original summary remains intact; supplemental node observations expose
N04's inner abstention and distinguish selected owner from final handoff owner.

Both planning gates unmet; actual generation, holdout and A/B/C were NOT admitted.
This protocol permits zero semantic revisions. Do not rerun or alter labels/thresholds.
61212 input/2481 output tokens; 22.368 inference seconds; input-price estimate
USD0.002570904, actual billing and host costs unknown; reserved USD0.051072.
All 95 trial JSON wrappers and exact-key scan passed. Source freeze remains unchanged.
Trial: `/Users/william/Documents/Codex/2026-09-22/mindthus-jev-reviewed-development/trial`.
Mission: `/Users/william/Documents/Codex/2026-09-22/mindthus-jev-reviewed-development/mission`.
New carrier tests:112 targeted; full1196 total=1189 successful+7 skipped; lifecycle81/81.
Read existing evidence, do not rerun unchanged checks. Current planning remains unqualified;
new research needs a named new hypothesis, not automatic continuation of this campaign.

## Current development after review — C01 v3 / C02 v2

Owner authorized implementing the independent-review recommendations. See
[revision design and limits](review-remediation/README.md),
[follow-up review](review-remediation/REVIEW.md), and
[verification](review-remediation/verification.json).
Current source is C01 graph 3 / C02 graph 2; all older sections below describe historical
qualification runs. Historical source is recoverable at `26c3f5e72`; old data, freeze
manifests, scores and observations remain unchanged. Their hashes intentionally reject
the new source; do not update old freezes to admit it.

C01 no longer treats an existing weak artifact as sufficient reason for intervention.
C02 plans utility/support/action in one State batch, returns incompatible answers to
the original owner, and rechecks utility/fidelity on a new artifact. Final TVG exit
remains host-owned. Engine/Provider/Session and canonical method contracts are unchanged.
New cases are public development diagnostics: 4 C01, 8 C02, and 6 fidelity specimens
from 2 parent cases. N01 has canonical alternatives but unresolved contract gold;
N10 support is unscored. None is holdout or a new live acceptance set.

Offline verification: 105 targeted tests successful; full suite 1189 total = 1182
successful + 7 skipped, no failures/errors; lifecycle 81/81. First full run exposed an
unregistered test file; registration was fixed and the full suite rerun successfully.
No new live calls. No behavioral qualification or cost-saving claim.
The remediation TPlan Mission is separate at
`/Users/william/Documents/Codex/2026-09-22/mindthus-jev-review-remediation/mission`;
it is completed for offline remediation, not for #211/#212 semantic/value acceptance.
Next experimental admission still needs resolved scoring standards, a new frozen
protocol/data identity and exact budget/request admission. Do not resume old campaigns.

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

## TPlan sequential Mission

Owner explicitly invoked TPlan to finish #209–#212 in order. Runtime:
`/Users/william/Documents/Codex/2026-09-22/mindthus-jev-issues/mission`.
Installed skill runtime is pinned at `mindthus/1.9.1/skills/tplan`; human_in_loop=0,
risk_tolerance=25, resource_sufficiency=50. Failure observability is repaired at `b945c40c5`, verified with 79 targeted tests,
1163 full-suite tests (7 skipped), and 19 official calls. Shared risk R1 is resolved for
future observation; the lost original response remains unknown. The one allowed C01
semantic revision finished and failed its frozen stop rule. See
`c01-v2-disposition.md`. C02 then completed its first frozen development run and stopped
on contract/label validity defects; see `c02-disposition.md`. The TPlan Mission is now
`abandoned` (bounded stop, not completed acceptance). #211/#212 full value acceptance
remains unmet; GitHub issues remain OPEN. C03–C08 remain unstarted portfolio candidates.

A named source-only technical recovery adds safe validation codes and whitelist numeric
wire evidence without changing C01 questions/labels/validators or Engine/Provider
abstraction. See `c01-v2-technical-recovery.md`. The recovery manifest is prepared at
`/Users/william/Documents/Codex/2026-09-22/mindthus-c01-typesafe-recovery-1/campaign.json`.
Its completed regression/live outcome is recorded below and in the disposition;
do not resubmit or regenerate a trial root to bypass an existing record.

## Goal and boundaries

Complete #211 C01 in sequence: contract correction, offline verification, frozen Chinese
development, official TypeSafe semantic trial, at most one bounded semantic revision,
independent holdout once, then A/B/C. This is the intended sequence, not completed
acceptance. C01 stopped; #212 was conditionally admitted and C02 also stopped after
its first development run. Keep formal
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
technical validation failure; at that historical checkpoint revisions used were 0/1.
Current C01 revisions used are 1/1 (see below). Holdout has not been created/frozen or evaluated.

Technical recovery 1 stopped at D09 after 19 calls: D01–D08 matched their frozen entry,
route and selected-owner labels; D09 returned direct execution instead of the expected
artifact-value intervention. See `c01-v2-typesafe-recovery-1.json`. Model snapshot stayed
`jev-1.13.0`, 62928 input / 1568 output tokens, estimated USD 0.002642976; actual cost
is unknown. All 19 calls have safe wire observations. No original failed batch was replaced.

One bounded semantic revision is now used (1/1): J1 clarifies artifact-value judgment
versus fully prescribed transformation; no other judgment/control/source truth changes.
The competing simple-synthesis interpretation of D09 is documented; labels are not
infallible. Cases/labels/criteria thresholds remain identical. See `c01-v2-r1-review.md`
and `c01-v2-r1-development-freeze.json` (graph 2.1). Original freeze remains historical.

The final regression ran 1163 tests: 1156 successful, 7 skipped, no failures/errors. Revision-1 development ran once at:
`/Users/william/Documents/Codex/2026-09-22/mindthus-c01-typesafe-semantic-r1`.
It stopped at D09 on the same hard-judgment/direct label mismatch, after 19 calls and
9 observed cases. See `c01-v2-typesafe-semantic-r1.json`; all original artifacts remain.
There are 42 total series attempts, reserving USD 0.112896. Semantic revisions: 1/1.
C01 qualification is stopped. Do not rerun, change labels or narrow to observed successes
to bypass the failed protocol. D09's plausible direct-synthesis interpretation is an
explicit label limitation, not permission to alter the frozen score.

Holdout and full A/B/C were not admitted. Native host consumption and net-value evidence
remain unmeasured. #212 now follows its separate admission decision. See
`c01-v2-semantic-plan.md` for frozen development scoring and separation rules.

## C02 current checkpoint

`c02-admission.md` records the conditional decision after C01 stopped. C02 uses existing
DecisionSpec/Session, with no new Engine/Provider abstraction or graph platform.
`c02.py` runs same-State utility/support questions, dependent action selection, one
host-generation intent/outcome, and one changed-artifact recheck. The original TVG
agent still owns exit; no script writes freeze/PASS. No canonical method was changed.

`c02-local-contract.json`, `c02-independent-standards.json`, `c02-zh-development.json`
and `c02-protocol.md` are bound by `c02-development-freeze.json`. There are 12 Chinese
synthetic development cases across operating-instruction/design-explanation purposes,
each including thin/adequate/missing-evidence/redundant/conflict/outside-scope examples.
Standards and labels are author-created, not independent human adjudication.

91 targeted tests and lifecycle 80/80 passed. Final-source full regression ran
1175 total tests: 1168 successful, 7 skipped, no failures/errors; see `verification-c02-engineering.json`.
The full log is `/Users/william/Documents/Codex/2026-09-22/mindthus-jev-issues/c02-final-full-suite.log`.
Do not rerun unchanged passed checks. A previous intermediate full suite ran 1173
tests (1166 successful, 7 skipped); it predates the final trial driver and two final checks.

Official development root is prepared at
`/Users/william/Documents/Codex/2026-09-22/mindthus-c02-typesafe-dev-1`:
36 exact request variants, max 24 calls / 120 inference seconds, USD 0.064512 reserve;
entire C02 development Jev series cap USD 0.25. It ran once: 18 calls, all 12 cases,
10/12 route matches, 9/12 utility matches and 5/6 expected action selections. The frozen
local decision gate was not met. Safe original observations are in `c02-typesafe-dev-1.json`.
Semantic revisions used: 0/1. The two redundant-but-usable deficit labels lack a stable
independent standard, so changing a question alone is not a defensible repair. The current
contract/data qualification path is stopped. Do not relabel, change targets, retry, or
silently replace the dataset. No generation, live recheck, holdout or A/B/C was admitted.
Host LLM design/context/review costs remain unknown, never zero. No saving claim.

The terminal TPlan report and SVG are under
`/Users/william/Documents/Codex/2026-09-22/mindthus-jev-issues/mission/reports/`.
They describe lifecycle and observed telemetry only; inference accounting is also
recorded in the two pilot observation reports. A new experimental proposal would need
independent adjudication of disputed standards and a new data/protocol identity, not
a reset of either stopped campaign. Preserve all original evidence.

## Independent reconsideration — 2026-09-22

Three independent AI contexts completed two-round written review; this is not human or
cross-model adjudication. See [meeting minutes](independent-review-2026-09-22/README.md)
and the six preserved reviewer opinions. Both old protocols remain NOT PASSED; no new
calls, code changes, relabeling, holdout, or A/B/C promotion occurred during review.
D09's canonical ambiguity, C02 redundancy-label validity, and action necessity limit
attribution to engine failure. Source sufficiency does not establish changed-artifact
fidelity; original TVG owner retains that audit responsibility, not yet live-tested.
Stopping the current qualification campaigns does not prove the research direction
has failed. C02's unused 0/1 revision is optional, not an obligation to keep tuning.
Next research work should first clarify standards with offline counterexamples; changed
standards/labels need a new protocol/data identity. Original Mission remains historical.

## Resume discipline

Read this file and Git status before editing. Verify source hashes before reusing evidence.
Do not rerun unchanged passed work merely to recover context. Goal, criteria, permissions
or semantic revisions require a named delta; preserve old records and data labels.
