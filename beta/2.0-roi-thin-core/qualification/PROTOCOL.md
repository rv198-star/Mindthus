# ROI Thin Core Qualification Protocol

Status: frozen before live calls.

Candidate implementation commit:
`6d79097b6303695c2b04ad307a4680dd79dc2797`

Candidate overlay SHA-256:
`4dc820a021598639ccb8e36a742422a2b3351796baa05fa4c47b4fc347e709e2`

Stable baseline: Mindthus 1.4.6 at
`00da11657bce553cb32e8e90c06ffe959dc08362`.

## Question

Does replacing only the frequently loaded `using-mindthus` body with the ROI Thin Core
produce a material cost reduction while preserving actions that matter?

## Arms

- Stable: the unmodified 1.4.6 Codex plugin.
- Candidate: the same plugin and owner trees with only the Thin Core overlay plus
  candidate identity metadata.

Use fresh isolated `CODEX_HOME` and workspace per call. Enable exactly one Mindthus arm.
Use `gpt-5.6-sol`, `xhigh`, the same prompt bytes, Codex CLI, and read-only execution.
Alternate arm order by case to reduce simple order bias.

## Five Cases

1. `direct`: ordinary fact-sufficient file read; no Mindthus Skill should load.
2. `evidence`: missing comparison baseline; do not invent improvement or load an owner.
3. `frame_whole`: preserve the local text truth but reject its claim to define a Skill.
4. `anti_spiral`: refuse a third unsupported fallback and return to the upstream failure.
5. `clear_owner`: native discovery loads SELA in the same user turn and gives the
   long-term direction without inventing a migration plan.

Final answers are inspected only for action, evidence, owner fidelity, and stopping
behavior. Terminology, formatting, and method-shaped explanation are not scored.

## Gates

Critical quality gate:

- Any arm error, explicit owner miss, invented evidence, wrong definition authority,
  unsupported third local repair, or needless blocking question rejects the candidate.
- A missing refinement that changes neither decision nor execution is allowed.

Lifecycle gate:

- Read commands in Codex JSONL are activation evidence; model self-report is not.
- Ordinary and near-negative work must not gain an unrelated owner or user-visible
  routing turn.

ROI gate:

- Median explicitly loaded Mindthus bytes must fall at least 50%.
- Host-reported median uncached input tokens should fall at least 10%.
- If token evidence is indistinguishable or reverses, cost remains unproven even when
  source bytes are smaller.
- Duration is supporting evidence only; five calls per arm cannot isolate host noise.

## Budget And Stop

Maximum: 10 Generator calls, no Judge, one call per arm per frozen case. Timeout is 900
seconds per call. No live semantic correction or rerun. A setup/authentication failure
before sampling may be repaired only when the failed call reports zero usage.

Do not add a Hook, router, owner index, fallback, or sixth case after sampling starts.
