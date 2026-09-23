# Relationship D2 — same-entry offline correction and episode recovery

Status: implementation contract for the Owner-approved D2 successor to `9065d18`.
The D1 question contract v0.3.1, its sources and all historical trials stay immutable.
This is a local execution contract, not a new semantic model qualification or D3 admission.

## Public seam

Use `entry.run(..., mode='relationship-frame.v1', corrector=..., organizer=...,
recheck=True)`. The existing default `assessment-v2` mode and its CLI keep their behavior.
Relationship mode delegates only persistence/budget support to `relationship_runtime.py`;
it compiles and consumes through the unchanged D1 module and evaluates through Session.
It never chains the old paid C01 router. `route=True` in this mode is rejected.
All providers/hooks must explicitly declare `is_live=False`; no credentials are read.
D3 will need a separate admission; D2 does not remove any existing live gate.

## Root, identity and ownership

`root` is one durable episode root, not a fresh directory per turn. An OS-user-local
registry keyed by the repository's Git common directory and the supplied episode ID
binds that episode to its root. Reopening the same episode at a different root is rejected.
A shared file lock serializes the whole episode; worktrees share its repository identity.
This guards accidental reset under the same user/repository, not malicious OS access,
manual deletion of journals, forged task IDs or different machines/users.

The immutable episode manifest binds mode, profile, D1 contract/sources, implementation,
provider configuration and original owner. Each turn/revision binds its exact raw packet,
recheck option and input hash. Same turn/revision with changed bytes is rejected; a new
revision still spends the SAME turn/episode allowances. The task owner supplies genuine
turn IDs; the plugin does not infer new task authorization from rhetoric or new evidence.
Successful resolved provider runtime is shared across every step/turn; drift is terminal.
Old-profile roots and cache identities are never reinterpreted as relationship episodes.

## Hook input/output

A correction request carries the immutable original/prepared input, the D1 CorrectionPlan,
current candidate text/version, a deterministic new candidate document ID, and owner/profile/
policy/contract identities. It is a named text correction, never permission to execute tools.
`corrector.identity` equals `authority.owner_ref`. `corrector.correct(request, timeout)` returns
exactly `{text, version, receipt_ref, usage, proposal}`. Usage is input_tokens/output_tokens/
cost_usd, with missing fields represented by null. Receipt is lineage, not proof of truth.
The hook adapter, not the language model, computes quote hashes from text/span outputs.

The runtime appends ONE new candidate document, preserves every original document byte,
authority, activation, episode/turn ID, and changes only revision/stage/proposal. The updated
proposal keeps frames, claims, scope corrections, relationship membership and non-target
references. References to the previous target are rebound to valid slices in the revision;
candidate thesis/controller/discriminator locations may be empty or rebound, never invented
by the runtime. Removing an inconvenient edge/frame/check to clear a recheck is rejected.
The returned packet must compile under D1. Invalid text/proposal/usage or late replies produce
a terminal failure outcome, not a retry. Valid structure is NOT proof of semantic faithfulness.

Optional organizer: only when the raw input has `proposal=null`, `organizer.identity` equals
`authority.owner_ref + ':organizer'`; `organize(request, timeout)` returns exactly
`{proposal, receipt_ref, usage}`. Original documents and authority cannot be changed.
Its output must compile, remains a proposal and undergoes Q0. One organizer call per episode;
no hidden extraction loop. No hook available means an awaiting state, not a provider call.

## Flow and accounting

1. Verify root/manifest/raw identity and reconcile recorded intents before any invocation.
2. Reuse a completed identical input. Otherwise organize only if the proposal is absent.
3. Run one D1 assessment batch. Missing/uncertain/source-conflicting inputs return to owner.
4. Only `request_correction` invokes the original host once; persist request then intent.
5. Preserve the immutable revision. If enabled, perform at most one S2 assessment. All new
   target-dependent references are checked against the revision, never the previous target.
6. Return corrected-unverified, corrected-rechecked, pending evidence, or returned-to-owner
   separately. A clear scan never sets task_complete/qualification or removes obligations.

Limits are independently counted: 4 judgment requests/episode, 2/turn; 2 corrections/episode,
1/turn; 1 organizer/episode; 7 total requests; 120 cumulative seconds, 45 per request.
Question/byte limits remain D1's 24/48 KiB. Recheck is part of the judgment allowance.
Actual records, not in-memory counters, define expenditure. Failed calls count. Host output
is bounded to 32 KiB including proposal; a full compiled packet still satisfies D1's limits.
Timeouts are passed to hooks and late returns are detected; arbitrary in-process callbacks
cannot be forcibly killed. D3 must enforce transport/subprocess deadlines independently.

Budget exhaustion returns the NEW unchanged raw packet to the owner, creates no new inference
intent, records why the plugin stopped, and never reuses an older answer as a fresh judgment.
Ordinary-host follow-up cost remains unknown, not zero. Outcome usage is summed only where
all values are known; fixture usage is not a monetary measurement.

## Recovery and acceptance

Session retains its own judgment intent/outcome. Host steps use the same immutable record
format. The episode aggregates both journals; there is no second shadow inference ledger.
An intent without outcome anywhere blocks further calls until reconciled. A completed outcome
without a final report is reused without calling provider/hook again. Normal exceptions are
terminal failed outcomes; process interruption may leave an unknown intent and is not retried.
Pending states (missing hook) are resumable; terminal input summaries are immutable.

D2 acceptance exercises the PUBLIC entry: two-turn Skills scope-vs-conclusion separation;
4K joint/conditional judgments without a fixed winner; unchanged original documents/authority;
revised-target recheck; disabled recheck; no-candidate/unknown/overflow paths; cross-turn ceilings;
new evidence after exhaustion; changed-root/revision/profile/provider/source refusals; concurrent
lock contention; crash before/after returned outcomes; invalid/late hooks; organizer single-use;
and old-mode regression. These are scripted control-flow tests, not real Jev or LLM accuracy.
