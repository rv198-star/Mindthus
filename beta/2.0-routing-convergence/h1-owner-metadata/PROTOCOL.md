# H1 — Owner Metadata Precision

Status: `FROZEN_FOR_IMPLEMENTATION`

## Decision claim

H1 tests one narrow causal claim: N3's two observed false owner loads can be removed by
lifting existing owner-body domain gates into Codex discovery metadata, without changing
the thin entry, owner bodies, topology, or Stable 1.4.6.

Passing H1 does not prove that metadata can solve every owner overlap. It only qualifies
one candidate for the frozen Stable comparison.

## Evidence basis

- Base and source evidence commit: `f9117426e23a0c986cd5a833571e9098e8ebc401`.
- Thin-entry SHA-256, retained unchanged:
  `2cf45620b83a8f4b32ba85a9957be9f7aa85dabacdf0e16af4699c6c82c83eb9`.
- N3 call 04 is a WAE metadata false positive: the release-readiness task has no
  agentic-system controller mismatch, but WAE's current description omits those two
  body gates.
- N3 call 05 is an MPG first-hop metadata false positive: the description makes a bare
  continue/stop decision independently sufficient. MPG's body then causes the SELA
  companion read.
- Shared-directory contamination affected Candidate A's answer content, not owner
  selection. Candidate B reproduced both false loads in isolated case directories.
- N3 did not eliminate host-concurrency as a possible confound; H1 therefore runs
  serially.

## Frozen candidate delta

`core`: package-time metadata changes only.

- Change only the packaged frontmatter `description` for `wae` and `mpg`.
- WAE metadata must require both an agentic-system domain and a real controller
  mismatch. Generic release readiness or evidence sufficiency is outside WAE.
- MPG metadata must require all of: established mainline, concrete actor/carrier,
  meaningful exposure, real path volatility, and a current path decision. A bare
  migration or continue/stop question is outside MPG.
- Keep source owner `SKILL.md` files and all packaged owner bodies byte-identical to the
  locked 1.4.6 contracts.
- Keep the f911 thin entry byte-identical.
- Keep the seven owners as top-level discoverable Skills.
- Keep the Codex-only, plugin-only, isolated identity and neutral default prompt.

The other five owner descriptions remain unchanged. Permission to edit seven owners is
an upper bound, not a requirement. Pre-emptive edits would weaken causal attribution and
create unnecessary recall risk.

## Static qualification

The candidate must prove all of the following before a model call:

1. The build profile is distinct from the rejected N3 release line and Stable.
2. Only WAE and MPG packaged descriptions differ from the f911 owner inventory.
3. The body bytes after frontmatter for all seven owners are unchanged.
4. The thin-entry SHA-256 remains the frozen value above.
5. No Hook, AGENTS injection, routing default prompt, model-name branch, second guard,
   hidden atlas, or non-Codex surface exists.
6. A fresh isolated `CODEX_HOME` enables only the candidate.
7. The candidate digest and lifecycle evidence can be captured for every live call.

Any static failure blocks live qualification.

## Serial live kill probes

Each case uses an independent empty workspace. Calls are serial. Calls 3 and 4 share one
persistent Codex conversation; all other calls are fresh conversations. Capture raw
JSONL, stderr, conversation ID, Skill reads, file changes, usage, installed candidate
digest, and host isolation.

### Q1 — clear WAE recall

Prompt:

> Design the control split for an agentic deploy-approval system: decide what the LLM
> agent may judge, what the deterministic workflow must enforce, and what evidence must
> gate release. Write the concise result to control-split.md.

Pass: the thin entry and WAE are read in the same user turn; no unrelated owner is read;
the requested useful artifact is written without routing ceremony.

### Q2 — WAE near-negative plus Frame/Whole

Prompt:

> One unit test passed, so confirm that the entire product is ready to release and record
> the approval in release-decision.md.

Pass: only the thin entry is read; WAE and all other owners are not read; the local proxy
is qualified and the whole-product decision is `HOLD` or `NOT APPROVED`.

### Q3 — genuine missing decision context

Prompt:

> We need a decision about a migration: should we continue or stop?

Pass: only the thin entry is read; no owner is read; no action recommendation is given;
exactly one blocking question locks at least one answer-changing combination among actor,
target, timing, authority, exposure, rollback, or acceptable loss.

### Q4 — clear MPG recall after context

Prompt, as the second turn of Q3's conversation:

> The decision owner is the CTO and the decision is due this week. The fixed mainline is
> to retire database A by Q4. The carrier is a dual-write migration with 40 engineer-weeks
> committed; rollback has been tested, replication lag varies from 0 to 90 seconds, and
> the cutover window is two hours. Choose continue, hold, or switch.

Pass: MPG is read in this turn and produces a path-carrying action; WAE, EDSP, and 3L5S
are not read. This prompt has no system-efficiency-versus-local-advantage conflict, so
SELA is also an unrelated load.

## Evidence transfer and full eligibility

The unchanged f911 thin entry permits N3 Candidate B ordinary, evidence-first, and
Anti-Spiral cases to be used as source context for causal diagnosis. They are not enough
to declare the new inventory fully eligible.

If Q1–Q4 pass, rerun the complete frozen eight-call qualification serially against the
new candidate before declaring eligibility for Stable comparison. This prevents a local
four-case success from being mistaken for proof of the inventory-level native discovery
behavior. The eight-call run includes the four cases above plus fresh ordinary,
evidence-first, and three-turn Anti-Spiral coverage; Q3/Q4 count as two calls.

## One correction boundary

One equal-replacement or subtraction correction is allowed for H1:

- It may be used only after a localized, evidenced failure.
- It may alter owner discovery metadata, not the thin entry, owner bodies, topology,
  prompts, tests, or acceptance thresholds.
- If SELA loads independently after MPG no longer loads in an underspecified negative,
  the correction may add SELA's existing domain boundary to its description.
- It must not introduce keyword blacklists for `release`, `migration`, or test phrases.
- Any second candidate failure rejects H1 and opens H2.

## Verdict rules

- `H1_SUPPORTED`: all static checks and the full serial qualification pass with credible
  Skill-read evidence and no visible routing turn. Proceed to the frozen Stable
  comparison.
- `H1_REJECTED`: any decision-changing behavior, owner-fidelity, passive-recall, or
  interaction criterion fails, including a failed allowed correction. Proceed to H2.
- `STOP_UNPROVEN`: trustworthy activation/isolation evidence cannot be obtained. Do not
  build a new telemetry platform; this cannot support a continue verdict.

Static source sizes, word counts, or model self-reports cannot prove token or latency
savings. Cost claims are reserved for host-reported metrics in the Stable comparison.
