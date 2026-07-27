# TPlan Feature Freeze Ledger

Status: active
Opened: 2026-07-26 (when [#144](https://github.com/rv198-star/Mindthus/issues/144) was filed)
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

## Ledger

| Date | PR / commit | Category | Why |
| --- | --- | --- | --- |
| 2026-07-27 | `3f719157` | #145 | Artifact inventory dry-run. Classification and reference scan only; no deletion, nothing under `docs/benchmarks/runs/` modified. |
| 2026-07-27 | (this commit) | #144 | Phase 1: typed validator status, schema fields for prospective/retrospective collection, rendered status surface, freshness check, this ledger. |
| 2026-07-27 | (this commit) | #144 + #145 | External audit repair. 缺陷修复，未新增能力：#144 时间戳校验、稳定 record ID（`logged_at` 移出 seed）、freeze 日期门；#145 引用记账恒等式、派生 basename 索引、CSV 契约与 LF 换行。强制 `source` 提案已驳回——`docs/real-use-validation.md` 无此要求，且 `source` 是自由文本，强制非空只会把"没填"变成"随便填"。不解除冻结，不授权删除。 |

## Boundaries

- This ledger records merges. It does not lift the freeze, and it does not authorize new
  TPlan feature work.
- Freeze exit is counted on **prospective** records observed after 2026-07-26. Retrospective
  records may inform the analysis; they do not unlock the freeze.
- Ten records is an observation window, not a statistical claim. It cannot certify
  judgment quality and must not be reported as if it could.
