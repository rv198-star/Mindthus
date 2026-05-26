# Mindthus Pressure Surface Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Issue 7 by consolidating Mindthus pressure surfaces without creating a new method layer or standalone game-theory skill.

**Architecture:** Keep pressure as a triggered challenge surface inside `using-mindthus` and `shared-primitives.md`. Add contract tests first, then add concise router and primitive wording, and extend pressure scenarios for incentive/game-theoretic pressure and low-risk skip behavior.

**Tech Stack:** Markdown docs, Python `unittest`, existing Mindthus router and multi-role pressure tests.

---

## File Structure

- Modify: `tests/test_mindthus_router_contract.py`
  - Static contract tests for pressure-surface ownership, skip boundaries, and no standalone game-theory route.
- Modify: `skills/using-mindthus/SKILL.md`
  - Add a lightweight Pressure Surface Check after judgment constraints and before method arbitration.
- Modify: `docs/methodologies/shared-primitives.md`
  - Add concise consolidation wording for Perspective Pressure without expanding the primitive index into a new method layer.
- Modify: `tests/multi_role_ab_pressure_tests.md`
  - Add pressure scenarios for incentive/game-theoretic challenge and low-risk deterministic skip.
- Existing files intentionally not modified:
  - Individual SELA / EDSP method bodies unless tests expose a contract gap.
  - Runtime scripts.
  - Any memory, retrieval, context-ranking, or user-profile implementation.
  - Any standalone game-theory skill.

## Task 1: Add Pressure Consolidation Contract Tests

**Files:**
- Modify: `tests/test_mindthus_router_contract.py`

- [ ] **Step 1: Add failing router pressure-surface test**

Add a test asserting that `using-mindthus` contains:

- `Pressure Surface Check / 施压面检查`
- pressure is not a standalone route
- low-risk deterministic work skips pressure
- Perspective Pressure covers incentive/game-theoretic concerns
- pressure must name owner, reason, and execution effect

- [ ] **Step 2: Add failing shared-primitives consolidation test**

Add a test asserting that `shared-primitives.md` contains:

- `Pressure Surface Consolidation / 施压面收束`
- `not a standalone method`
- `not a new route`
- `game-theoretic`
- `incentive`
- `low-risk deterministic`

- [ ] **Step 3: Add no-standalone-game-theory test**

Assert that no `skills/game-theory`, `skills/game_theory`, or `skills/gametheory` directory exists.

- [ ] **Step 4: Run focused tests and verify failure**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: FAIL on the newly required pressure-surface phrases.

## Task 2: Consolidate Pressure Surface Guidance

**Files:**
- Modify: `skills/using-mindthus/SKILL.md`
- Modify: `docs/methodologies/shared-primitives.md`

- [ ] **Step 1: Add router Pressure Surface Check**

In `skills/using-mindthus/SKILL.md`, after `Judgment Constraint Recognition` and before `Method Arbitration`, add a short section that:

- skips pressure for clear, low-risk, deterministic, reversible, mechanically verifiable work
- routes single-view, incentive, or game-theoretic concerns to Perspective Pressure
- keeps SELA / EDSP as the Perspective Pressure owners
- points TVG pressure to bounded artifact value depth
- points Evidence / Claim Ceiling to proof limits
- points Anti-Spiral to repeated local repair
- requires owner, reason, and execution effect

- [ ] **Step 2: Add shared primitive consolidation note**

In `docs/methodologies/shared-primitives.md`, add a concise section after the primitive index explaining that pressure surfaces are triggered challenges, not standalone routes.

- [ ] **Step 3: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: PASS.

## Task 3: Extend Multi-Role Pressure Scenarios

**Files:**
- Modify: `tests/multi_role_ab_pressure_tests.md`

- [ ] **Step 1: Add Scenario 6 for incentive/game-theoretic pressure**

Add a SELA scenario where multiple stakeholders have incentives to frame the same automation decision differently. Expected treatment should use role/incentive pressure without creating a game-theory method.

- [ ] **Step 2: Add Scenario 7 for low-risk deterministic skip**

Add an EDSP scenario where the task is deterministic and reversible. Expected treatment should state `multi_role_used=false` and avoid pressure overhead.

- [ ] **Step 3: Run multi-role focused tests**

Run:

```bash
python3 -m unittest tests.test_multi_role_ab_contract -v
```

Expected: existing tests pass.

## Task 4: Verify Third Batch

**Files:**
- No edits unless verification exposes a contract gap.

- [ ] **Step 1: Run router tests**

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

- [ ] **Step 2: Run packaging docs tests**

```bash
python3 -m unittest tests.test_packaging_docs -v
```

- [ ] **Step 3: Run full tests**

```bash
python3 -m unittest discover -s tests -v
```

- [ ] **Step 4: Check whitespace**

```bash
git diff --check
```

## Task 5: Commit Third Batch

**Files:**
- Modify: `tests/test_mindthus_router_contract.py`
- Modify: `skills/using-mindthus/SKILL.md`
- Modify: `docs/methodologies/shared-primitives.md`
- Modify: `tests/multi_role_ab_pressure_tests.md`
- Create: `docs/superpowers/plans/2026-05-26-mindthus-pressure-surface-consolidation.md`

- [ ] **Step 1: Review diff**

Run:

```bash
git diff -- tests/test_mindthus_router_contract.py skills/using-mindthus/SKILL.md docs/methodologies/shared-primitives.md tests/multi_role_ab_pressure_tests.md docs/superpowers/plans/2026-05-26-mindthus-pressure-surface-consolidation.md
```

- [ ] **Step 2: Stage files**

```bash
git add tests/test_mindthus_router_contract.py skills/using-mindthus/SKILL.md docs/methodologies/shared-primitives.md tests/multi_role_ab_pressure_tests.md docs/superpowers/plans/2026-05-26-mindthus-pressure-surface-consolidation.md
```

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: consolidate mindthus pressure surfaces"
```

## Follow-Up Work Not In This Plan

- Version boundary or changelog decision.
- Runtime memory or retrieval.
- Standalone game-theory skill.
- Broader rewrite of SELA, EDSP, TVG, WAE, or tplan internals.
