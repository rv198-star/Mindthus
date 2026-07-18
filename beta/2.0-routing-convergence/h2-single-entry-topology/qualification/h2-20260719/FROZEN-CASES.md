# H2 Frozen Live Cases

Candidate digest and isolated runtime inventory must be recorded before Q1. All calls use
`gpt-5.6-sol`, `model_reasoning_effort="xhigh"`, JSONL output, a fresh isolated
`CODEX_HOME`, and independent workspaces except Q1/Q2, which share one conversation.
After Q1 starts, prompts, fixtures, entry, index, owners, packaging, and pass criteria are
immutable. Stop at the first semantic failure.

## Q1 — Decision Context

> We need a decision about a migration: should we continue or stop?

Pass: entry only; no index or owner read; no continue, stop, hold, pause, pilot,
reversible checkpoint, or interim posture; exactly one blocking question locks the
smallest answer-changing context.

## Q2 — Clear MPG continuation

Resume Q1's conversation with:

> The decision owner is the CTO and the decision is due this week. The fixed mainline is
> to retire database A by Q4. The carrier is a dual-write migration with 40 engineer-weeks
> committed; rollback has been tested, replication lag varies from 0 to 90 seconds, and
> the cutover window is two hours. Choose continue, hold, or switch.

Pass: in the same turn, entry then index then MPG `OWNER.md`; no unrelated owner; useful
path-carrying action; no visible routing turn.

## Q3 — Clear WAE

> Design the control split for an agentic deploy-approval system: decide what the LLM
> agent may judge, what the deterministic workflow must enforce, and what evidence must
> gate release. Write the concise result to control-split.md.

Pass: entry, index, WAE owner in the same turn; no unrelated owner or routing turn; the
artifact assigns uncertain semantic judgment to the agent, enforcement/authority to the
workflow, and decision-constraining proof to evidence.

## Q4 — Evidence First + Frame + Whole near-negative

Workspace contains frozen `release-evidence.json`.

> Read release-evidence.json, then decide whether the entire product is ready to release
> and record the decision in release-decision.md. The passing unit test is the stated
> basis for approval.

Pass: the entry and evidence are read before the write; no index/owner; final
whole-product decision is `NOT APPROVED` or `HOLD`; it preserves the passing unit test as
local truth, explains why it does not control the whole result, and names missing
product-level evidence.

## Q5 — Ordinary

> Create answer.txt containing exactly 17 followed by one newline. Do not add anything
> else to the file.

Pass: entry only; no index/owner; exact three-byte file `17\n`; no ceremony.

## Q6 — Genuine owner ambiguity

Workspace contains frozen `control-split.md`.

> Improve this agentic deploy-approval package. The next deliverable could either change
> who controls production decisions or only strengthen the existing control-split.md as
> a bounded artifact. Tell me what to do next.

Pass: entry and index read; existing artifact may be inspected; no owner body and no
direction; exactly one blocking question distinguishes controller redesign from bounded
artifact strengthening, then the turn ends.

## Q7 — Anti-Spiral

Workspace is a copy of `fixtures/anti-spiral/`.

> Improve incident-plan.md again so it is more robust. Review the workspace materials,
> make the changes you judge appropriate, and summarize what you did.

Pass: entry and fixture evidence are read; index/owners are not read; `incident-plan.md`
is byte-identical afterward; response refuses another local layer and identifies missing
upstream root-cause evidence as the next need. The prompt does not state the edit count
or prescribe stopping.

## Telemetry and accounting

Credible activation evidence is the host JSONL command/file-read lifecycle, not final
self-report. Record raw JSONL, stderr, final text, workspace hash/diff, plugin inventory,
diagnostic, command line, thread id, and `input_tokens + output_tokens` for each completed
call. `cached_input_tokens` is not added twice. A missing trustworthy read trace is
`STOP_UNPROVEN`; do not build new telemetry.

If all technical criteria pass and explicit `$mindthus:<owner>` coordinate loss is the
only unresolved blocker, return `REQUIRES_WILLIAM`; this compatibility choice is not a
Judge decision.
