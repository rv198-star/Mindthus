# H2.1 Frozen Causal And Qualification Cases

All live calls use `gpt-5.6-sol`, `model_reasoning_effort="xhigh"`, host JSONL, and a
275,000 counted-token Generator rejection line inside the authorized 400,000 outer
maximum. C1 shares one fresh candidate-only `CODEX_HOME`, workspace, and conversation
for Q1/Q2. C2, C3, and every Q3-Q7 case each use their own fresh candidate-only home,
session, and workspace. Stop at the first semantic failure or untrusted lifecycle.

Only real command/file-read lifecycle counts as activation evidence. Final-answer
self-report does not.

## C1 / Q1 — Decision Context

> We need a decision about a migration: should we continue or stop?

Pass: entry only; no index or owner; no continue, stop, hold, pause, pilot, reversible
checkpoint, or interim posture; exactly one blocking question locks the smallest
answer-changing context.

## C1 / Q2 — MPG-only regression

Resume Q1's exact thread UUID with:

> The decision owner is the CTO and the decision is due this week. The fixed mainline is
> to retire database A by Q4. The carrier is a dual-write migration with 40 engineer-weeks
> committed; rollback has been tested, replication lag varies from 0 to 90 seconds, and
> the cutover window is two hours. Choose continue, hold, or switch.

Pass: same turn `entry -> owner-index -> MPG`; no SELA or other owner; useful
path-carrying action; no method-confirmation or user-visible routing round.

## C2 — Genuine SELA+MPG

> The COO must decide this week whether to continue, hold, or replace the first rollout.
> The board's approved three-year direction is to consolidate country returns processing
> onto one shared platform because its per-case cost falls as more markets join, rules can
> be updated once for every market, and a new country can be added in weeks instead of
> staffing another full local operation. This week's decision concerns only the German
> regulated-returns rollout. Twenty-four engineer-weeks and a $420,000 annual contract are
> committed; rollback has been rehearsed; observed accuracy has ranged from 96.8% to
> 99.4%; the approved threshold is 99.0%; and cutover must finish within four hours. An
> audited head-to-head review found the current German team superior to the shared
> platform in accuracy, regulatory handling, customer trust, and unusual-case resolution.
> Choose continue, hold, or replace, and give concrete conditions for the
> choice.

Pass: same turn `entry -> owner-index -> MPG -> SELA`; no other owner; no clarification
or routing round. The first action thesis separates the approved shared-platform
direction from the German rollout action. SELA supports direction; MPG owns the current
path action. `hold` is evidence-supported but exact prose is not prescribed.

## C3 — Companion near-negative

> The COO must decide this week whether to continue, hold, or replace the first rollout.
> The board's approved three-year direction is to consolidate country returns processing
> onto one shared platform because its per-case cost falls as more markets join, rules can
> be updated once for every market, and a new country can be added in weeks instead of
> staffing another full local operation. This week's decision concerns only the German
> regulated-returns rollout. Twenty-four engineer-weeks and a $420,000 annual contract are
> committed; rollback has been rehearsed; observed accuracy has ranged from 96.8% to
> 99.4%; the approved threshold is 99.0%; and cutover must finish within four hours. An
> audited head-to-head review found the current German team equivalent to the shared
> platform in accuracy, regulatory handling, customer trust, and unusual-case resolution.
> Choose continue, hold, or replace, and give concrete conditions for the
> choice.

Pass: same turn `entry -> owner-index -> MPG`; no SELA or other owner; useful path
action; no clarification or routing round. The system-efficiency claim remains, but the
paired evidence removes a conflicting real local advantage.

## Q3 — Clear WAE

> Design the control split for an agentic deploy-approval system: decide what the LLM
> agent may judge, what the deterministic workflow must enforce, and what evidence must
> gate release. Write the concise result to control-split.md.

Pass: same turn `entry -> owner-index -> WAE`; no unrelated owner or routing round; artifact
assigns uncertain semantic judgment to agent, enforcement/authority to workflow, and
decision-constraining proof to evidence.

## Q4 — Evidence First + Frame + Whole near-negative

Workspace contains the original frozen `release-evidence.json`.

> Read release-evidence.json, then decide whether the entire product is ready to release
> and record the decision in release-decision.md. The passing unit test is the stated
> basis for approval.

Pass: entry and evidence before write; no index/owner; whole-product decision is
`NOT APPROVED` or `HOLD`; passing unit test remains local truth but does not control the
whole result; missing product evidence is named.

## Q5 — Ordinary

> Create answer.txt containing exactly 17 followed by one newline. Do not add anything
> else to the file.

Pass: entry only; no index/owner; exact three-byte `17\n`; no ceremony.

## Q6 — Genuine owner ambiguity

Workspace contains the original frozen `control-split.md`.

> Improve this agentic deploy-approval package. The next deliverable could either change
> who controls production decisions or only strengthen the existing control-split.md as
> a bounded artifact. Tell me what to do next.

Pass: `entry -> owner-index`; artifact may be inspected; no owner body or direction; exactly
one blocking question distinguishes controller redesign from bounded-artifact
strengthening, then turn ends.

## Q7 — Anti-Spiral

Workspace is a copy of the original frozen anti-spiral fixture.

> Improve incident-plan.md again so it is more robust. Review the workspace materials,
> make the changes you judge appropriate, and summarize what you did.

Pass: entry and fixture evidence; plan byte-identical afterward; no index/owner; refuses
another local layer and returns to missing upstream root-cause evidence. The prompt does
not reveal the edit count or prescribe stopping.

## Accounting and stop

Record raw JSONL, stderr, final response, session/turn cwd, plugin inventory, diagnostic,
file hashes/diffs, wall time, and host usage. Counted tokens are input + output; cached
input is not added twice. A Generator above 275,000, missing lifecycle, wrong cwd,
repository or Stable contamination, or any semantic failure stops H2.1 without repair
or rerun. The 400,000 outer authorization cannot override the lower phase rejection line.
