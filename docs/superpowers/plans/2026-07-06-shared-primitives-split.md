# Shared Primitives Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split high-complexity cognitive primitive bodies out of `shared-primitives.md` while keeping the index usable.

**Architecture:** Keep `docs/methodologies/shared-primitives.md` as the compact index and cross-primitive map. Move detailed primitive bodies into `docs/methodologies/primitives/` files, then update tests and packaging assertions to ensure the new files ship.

**Tech Stack:** Markdown documentation, Python pytest contract tests, release-pack copy-tree packaging.

---

### Task 1: Add Split Contract Tests

**Files:**
- Modify: `tests/test_mindthus_router_contract.py`
- Modify: `tests/test_packaging_docs.py`

- [ ] **Step 1: Add a failing router-doc test**

Add a test that asserts `shared-primitives.md` links to these files:

```text
primitives/aspect-ownership.md
primitives/frame-fitness-check.md
primitives/decision-context-calibration.md
primitives/whole-elephant-protocol.md
primitives/mpg-scalar-commitment-unpack.md
primitives/expression-pressure-and-gates.md
```

The same test should assert each file exists and contains its core phrases.

- [ ] **Step 2: Add a failing packaging test**

Extend release-pack assertions so Claude, Codex, Codex plugin, and OpenCode outputs include at least `docs/methodologies/primitives/whole-elephant-protocol.md`.

- [ ] **Step 3: Run tests and verify RED**

Run:

```bash
python3 -m pytest tests/test_mindthus_router_contract.py::MindthusRouterContractTests::test_shared_primitives_index_links_to_split_primitive_files tests/test_packaging_docs.py::PackagingDocsTests::test_release_pack_includes_split_primitive_docs -q
```

Expected: fail because the new files and links do not exist yet.

### Task 2: Create Primitive Detail Files

**Files:**
- Create: `docs/methodologies/primitives/aspect-ownership.md`
- Create: `docs/methodologies/primitives/frame-fitness-check.md`
- Create: `docs/methodologies/primitives/decision-context-calibration.md`
- Create: `docs/methodologies/primitives/whole-elephant-protocol.md`
- Create: `docs/methodologies/primitives/mpg-scalar-commitment-unpack.md`
- Create: `docs/methodologies/primitives/expression-pressure-and-gates.md`

- [ ] **Step 1: Add the six detail files**

Move existing content with minimal heading and link edits. Do not add new primitives.

- [ ] **Step 2: Keep support-only and guardrail boundaries visible**

Each file must state whether it is `judgment_owner`, `support`, `constraint`, or expression/gate support when relevant.

### Task 3: Compact The Shared Index

**Files:**
- Modify: `docs/methodologies/shared-primitives.md`

- [ ] **Step 1: Replace detailed sections with summaries and links**

Keep the Cognitive Primitive Index table and short boundary language. Replace moved sections with compact bullets linking to the new files.

- [ ] **Step 2: Preserve existing reference compatibility**

Keep these visible phrases in the index:

```text
Cognitive Primitives / 认知原语
Cognitive Primitive Index / 认知原语索引
Frame Fitness Check / 定框适配检查
Whole Elephant Protocol / 全象流程
Decision Context Calibration / 决策语境校准
MPG Scalar Commitment Unpack / MPG 标量承诺显影
```

### Task 4: Verify And Review

**Files:**
- No production edits unless tests reveal a broken reference.

- [ ] **Step 1: Run focused tests**

```bash
python3 -m pytest tests/test_mindthus_router_contract.py tests/test_packaging_docs.py -q
```

- [ ] **Step 2: Run full tests**

```bash
python3 -m pytest -q
```

- [ ] **Step 3: Check index size**

```bash
wc -l docs/methodologies/shared-primitives.md
```

Expected: meaningfully lower than the pre-split `761` lines.

- [ ] **Step 4: Stop instead of adding rules**

If tests fail because of missing links or packaging, fix those. If tests fail because a long old phrase moved out of the index, update the test to read the relevant detail file instead of duplicating text back into the index.
