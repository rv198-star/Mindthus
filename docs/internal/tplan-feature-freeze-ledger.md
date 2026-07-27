# TPlan Feature Freeze Ledger

Status: active
Opened: 2026-07-26T18:03:23Z (when [#144](https://github.com/rv198-star/Mindthus/issues/144) was filed)
Closes: when `data/fidelity-usage-log.jsonl` holds 10 prospective `real_use` records and
the aggregate review in #144 is complete.

## Why this exists

Collecting real-use records has low immediate return; TPlan features have high immediate
return. Run both in parallel and collection loses every time. The freeze is what makes
the rest of #144 reachable.

The ledger's job is narrower than the freeze's: it removes the post-hoc wording argument.
Without a line written at merge time, "was that a defect fix or a feature?" gets decided
later, by whoever is arguing, with the answer already known. One line per merge, written
when the merge happens, is enough to make the question answerable.

## What the freeze covers

**Allowed during the freeze** — defect fixes, security and privacy fixes, release
hygiene, #144 itself, and #145.

**Blocked during the freeze** — new TPlan capabilities, new telemetry surfaces, new
methodology text.

## Ledger scope

**Every merge during the window gets a line**, not only the arguable ones. Defect fixes,
security fixes, and release hygiene are themselves categories of freeze exception, so
they belong here too. A ledger that records only the contested cases cannot show that
the window was respected — it only shows which cases someone thought to argue about.

If a merge does not fit an allowed category, it should not merge. Recording it here does
not authorize it.

Pending branch deliveries may be listed before merge so reviewers can audit freeze
compliance. They do not substitute for the final PR/merge row; that row is added when
the branch actually lands.

## Ledger

| Date | PR / commit | Category | Why |
| --- | --- | --- | --- |
| 2026-07-27 | `3f719157`, `f7b8776e` (pending branch delivery) | #144 + #145 | Phase 1 inventory/dry-run and real-use registry visibility/schema work. No artifact deletion; no freeze exit. |
| 2026-07-27 | `256f71d5`, `0c5f6a3e` (pending branch delivery) | #144 + #145 | External-audit repairs, including stable/traceable freeze counting, per-row inventory evidence, and the 14 retained-report archive pointers required by #145. No artifact deletion or migration. |

## Boundaries

- This ledger records merges. It does not lift the freeze, and it does not authorize new
  TPlan feature work.
- Freeze exit counts unique, traceable **prospective** records observed after
  `2026-07-26T18:03:23Z`. Retrospective records may inform the analysis; they do not
  unlock the freeze.
- Ten records is an observation window, not a statistical claim. It cannot certify
  judgment quality and must not be reported as if it could.
