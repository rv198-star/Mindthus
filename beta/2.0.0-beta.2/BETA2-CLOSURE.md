# Mindthus 2.0 Beta.2 — Closure

Status: `STOP_UNPROVEN / SUPERSEDED`

Closed on: 2026-07-19

Terminal commit before this closure: `d2a4375`

Beta.2 is now a research and counterexample archive. It is not a release candidate,
an implementation base for the successor design, or an active evaluation program. No
further Generator, Judge, protocol-repair, release, publication, or promotion work is
authorized under the Beta.2 program.

## What the program established

- The Beta.1 package, owner namespace, isolation checks, and evaluation-arm machinery
  can be represented and audited independently from Stable.
- Primitive action and runtime skill loading must be scored separately.
- Missing host telemetry, carrier state, isolation evidence, or Judge evidence must cap
  the affected claim instead of being silently treated as product success or failure.
- The final qualification path did not produce an eligible Thin-Kernel arm for a formal
  Stable/direct-only/thin-Kernel comparison.
- Repeated protocol repair became a material source of cost and complexity: Beta.2
  accumulated multiple protocol generations and decision-recovery layers without
  producing route-wide comparative evidence.

## What the program did not establish

- It did not prove that a thin cognitive-primitive entry layer is ineffective.
- It did not prove that Stable, direct-only, or Thin-Kernel routing has superior answer
  quality, owner fidelity, recall, latency, or token efficiency.
- It did not prove that Codex cannot support passive activation through a different,
  natively discoverable carrier.
- It did not authorize a Beta release or Stable migration.

## Why this line stops

Beta.1 and Beta.2 separated a SessionStart passive Kernel from an arbitration-only
`using-mindthus`. The tested path did not yield an eligible formal arm, and continuing
would require changing the carrier and therefore the product hypothesis. That is a
successor design, not another repair to the frozen Beta.2 program.

External design evidence from `eagleagentic/superpowers-gpt-5.6` also makes a simpler
hypothesis worth testing: one very small, natively discoverable, always-available entry
skill can retain minimum passive guardrails while direct owner descriptions carry normal
routing. This removes the separate SessionStart Kernel and keeps arbitration inside the
same thin entry only when owner selection remains ambiguous.

## Reusable evidence and assets

The successor may selectively reuse, after an explicit relevance check:

- isolated arm identity and namespace checks;
- behavior-versus-load scoring semantics;
- per-turn evidence and missing-data fields;
- owner, primitive, lifecycle, and provenance case inventories; and
- bounded smoke and stop-gate principles.

Reuse means extracting the smallest applicable contract or fixture. It does not mean
inheriting the Beta.2 runtime wholesale.

## Non-inheritance boundary

The successor must not use Beta.2 as its implementation baseline or automatically carry
forward:

- the SessionStart passive-Kernel carrier;
- the v0.1–v0.6 protocol and amendment chain;
- the full authorization, replay, recovery, Generator, and Judge runner stack; or
- any Beta.2 result as equivalent-quality or route-effectiveness evidence.

The successor implementation should branch from the isolated Beta.1 checkpoint
`f131fd88`, retain the Beta namespace and direct-owner packaging that remain useful, and
replace the two-layer carrier/router design with a single native thin entry prototype.
It should remain unnamed as Beta.3 until a small eligibility qualification succeeds.

## Repository disposition

- Preserve this branch and its committed artifacts as historical evidence.
- Keep issue #112 open as the architecture-level parent.
- Close #113–#118 as completed Beta.2 research infrastructure.
- Close #119 without a formal comparison result because the authorized line stopped
  unproven and is superseded by a new carrier hypothesis.
- Remove local Beta.2 worktrees only after this closure is pushed; do not delete their
  remote branches.
