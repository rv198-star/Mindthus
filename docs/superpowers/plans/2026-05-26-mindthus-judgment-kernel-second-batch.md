# Mindthus Judgment Kernel Second Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the second batch of Mindthus judgment-kernel issues: judgment constraint recognition, method arbitration rules, and execution impact requirement.

**Architecture:** Extend the `using-mindthus` router after judgment-object routing with lightweight post-route judgment controls. Add contract tests first, then update `using-mindthus`, mirror only the smallest project-level guidance in `AGENTS.md`, and extend pressure tests with boundary cases. Do not implement Issue 7 pressure consolidation or create a standalone arbitration method.

**Tech Stack:** Markdown docs, Python `unittest`, existing Mindthus router contract tests and pressure-test documents.

---

## File Structure

- Modify: `tests/test_mindthus_router_contract.py`
  - Static contract tests for judgment constraints, method arbitration, and execution impact.
- Modify: `skills/using-mindthus/SKILL.md`
  - Primary router surface for Issue 4-6.
- Modify: `AGENTS.md`
  - Concise mirror guidance for constraints, arbitration, and execution impact.
- Modify: `tests/mindthus_router_pressure_tests.md`
  - Add pressure scenarios for value/emotion constraints, method arbitration, and execution-impact failure.
- Existing files intentionally not modified:
  - `docs/methodologies/shared-primitives.md`: Issue 7 will decide whether any wording belongs there.
  - Individual skill entrypoints: do not change SELA / EDSP / WAE / TVG / tplan core methods in this batch.
  - Runtime scripts: no automation or scoring engine.

## Task 1: Add Second-Batch Router Contract Tests

**Files:**
- Modify: `tests/test_mindthus_router_contract.py`

- [ ] **Step 1: Add failing tests for judgment constraint recognition**

Add this method after `test_context_injection_point_is_interface_not_memory_implementation`:

```python
    def test_using_mindthus_defines_judgment_constraint_recognition(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Judgment Constraint Recognition / 判断约束识别",
            "Facts and evidence constrain factual claims",
            "Values and preferences constrain priorities",
            "Interests and incentives constrain stakeholder interpretation",
            "Emotional signals constrain attention",
            "Risk posture and reversibility constrain action strength",
            "Authority boundaries constrain who may decide",
            "do not let values or emotion assert factual claims",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 2: Add failing tests for method arbitration**

Add this method after the constraint test:

```python
    def test_using_mindthus_defines_method_arbitration_actions(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Method Arbitration / 方法仲裁",
            "`dominate`",
            "`defer`",
            "`degrade`",
            "`block`",
            "`stop`",
            "TVG vs Anti-Spiral",
            "SELA vs WAE",
            "EDSP vs evidence",
            "3L5S vs direct execution",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 3: Add failing tests for execution impact**

Add this method after the arbitration test:

```python
    def test_using_mindthus_requires_execution_impact(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Execution Impact / 执行影响",
            "strategy",
            "risk handling",
            "evidence requirement",
            "next action",
            "stopping condition",
            "method choice",
            "handoff packet",
            "If a judgment changes none of these",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 4: Add failing tests for AGENTS mirror**

Add this method after the execution-impact test:

```python
    def test_agents_mentions_constraints_arbitration_and_execution_impact(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "判断约束",
            "事实 claim",
            "价值、利益、情绪",
            "方法冲突",
            "dominate / defer / degrade / block / stop",
            "执行影响",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 5: Run tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: FAIL with missing phrases from the new second-batch tests.

## Task 2: Update `using-mindthus` With Judgment Constraints

**Files:**
- Modify: `skills/using-mindthus/SKILL.md`

- [ ] **Step 1: Add judgment-constraint section**

In `skills/using-mindthus/SKILL.md`, immediately after `#### Context Injection Point / 上下文注入口`, add:

```markdown
#### Judgment Constraint Recognition / 判断约束识别

After identifying the judgment object, identify what can legitimately constrain the
judgment:

- Facts and evidence constrain factual claims.
- Values and preferences constrain priorities and acceptable trade-offs.
- Interests and incentives constrain stakeholder interpretation.
- Emotional signals constrain attention, trust, discomfort, urgency, or caution.
- Risk posture and reversibility constrain action strength.
- Authority boundaries constrain who may decide.
- Injected context constrains interpretation only when it is relevant to the current
  task and does not silently override current user input.

Do not turn every judgment into evidence-only reasoning. Also do not let values or
emotion assert factual claims without support. If constraints conflict, surface the
conflict before choosing a route or action.
```

- [ ] **Step 2: Run focused router tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: constraint test passes; arbitration, execution impact, and AGENTS mirror
tests still fail.

## Task 3: Update `using-mindthus` With Method Arbitration

**Files:**
- Modify: `skills/using-mindthus/SKILL.md`

- [ ] **Step 1: Add method-arbitration section**

Immediately after the judgment-constraint section, add:

```markdown
#### Method Arbitration / 方法仲裁

When multiple Mindthus methods seem applicable, do not stack methods by default.
Choose an arbitration action:

- `dominate`: one method owns the main judgment.
- `defer`: one method waits for another method to resolve a prerequisite.
- `degrade`: a method may speak only as a weaker claim because constraints are
  insufficient.
- `block`: a method prevents another method from making an over-strong conclusion.
- `stop`: Mindthus should not continue; use direct execution, information acquisition,
  user clarification, or handoff.

Common conflict checks:

- TVG vs Anti-Spiral: if another value pass is becoming local repair, Anti-Spiral blocks
  or redirects TVG.
- SELA vs WAE: a long-term system-efficiency direction can dominate strategic direction,
  while WAE may block or degrade immediate action under high risk or irreversibility.
- EDSP vs evidence: EDSP may give a structural direction, but evidence constraints can
  degrade or block factual confidence.
- 3L5S vs direct execution: if the user supplied a clear, bounded, low-risk task, direct
  execution wins.
```

- [ ] **Step 2: Run focused router tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: constraint and arbitration tests pass; execution impact and AGENTS mirror
tests still fail.

## Task 4: Update `using-mindthus` With Execution Impact

**Files:**
- Modify: `skills/using-mindthus/SKILL.md`

- [ ] **Step 1: Add execution-impact section**

Immediately after the method-arbitration section, add:

```markdown
#### Execution Impact / 执行影响

A Mindthus judgment should change downstream work. Before treating a judgment as useful,
name at least one execution impact:

- strategy
- risk handling
- evidence requirement
- next action
- stopping condition
- method choice
- handoff packet

If a judgment changes none of these, it is probably only a coherent explanation. Return
to direct execution, information acquisition, constraint clarification, or a sharper
judgment object.
```

- [ ] **Step 2: Run focused router tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: all `using-mindthus` tests pass; AGENTS mirror test still fails.

## Task 5: Update `AGENTS.md` Mirror Guidance

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add concise guidance after context-injection paragraph**

In `AGENTS.md`, after the context-injection paragraph added in the first batch, add:

```markdown
判断时要识别判断约束：事实 claim 受证据约束；价值、利益、情绪、风险姿态和权限边界
可以约束优先级、行动强度和责任归属，但不能伪装成事实。多个方法冲突时，不要堆叠方法，
先判断谁 dominate / defer / degrade / block / stop。输出必须产生执行影响：改变策略、
风险处理、证据要求、下一步行动、停止条件、方法选择或交接信息。
```

- [ ] **Step 2: Run focused router tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: all router contract tests pass.

## Task 6: Extend Router Pressure Tests

**Files:**
- Modify: `tests/mindthus_router_pressure_tests.md`

- [ ] **Step 1: Add capability-target bullets**

In `## Capability Target`, append:

```markdown
- identifying whether facts, values, interests, emotion, risk, authority, or injected
  context legitimately constrain the judgment
- resolving method conflicts with dominate, defer, degrade, block, or stop instead of
  stacking methods
- requiring judgments to change downstream strategy, risk handling, evidence
  requirements, next action, stopping condition, method choice, or handoff packet
```

- [ ] **Step 2: Add Scenario 10 for values and emotion constraints**

Add before `## Evaluation Template`:

````markdown
## Scenario 10: Values And Emotion Are Constraints, Not Facts

### What This Tests

The prompt includes emotional discomfort and a value preference. A good treatment should
let them constrain priorities without turning them into factual claims.

### A Prompt

```text
Use Mindthus normally.

The automated moderation summary is probably accurate, but I feel uneasy using it for
appeals because users deserve a human-readable explanation. Should we ship it as the
default appeal reviewer?
```

### B Prompt

```text
Use `using-mindthus`. Identify judgment constraints before choosing a route.

The automated moderation summary is probably accurate, but I feel uneasy using it for
appeals because users deserve a human-readable explanation. Should we ship it as the
default appeal reviewer?
```

### Expected Treatment Behavior

- Treats unease and dignity/explanation values as legitimate constraints on action.
- Does not claim the summary is inaccurate merely because the user feels uneasy.
- Separates factual accuracy evidence from value and trust constraints.
- Recommends a bounded next action such as evidence gathering, human review boundary,
  explanation requirement, or staged rollout.
````

- [ ] **Step 3: Add Scenario 11 for method arbitration**

Add after Scenario 10:

````markdown
## Scenario 11: TVG Versus Anti-Spiral Arbitration

### What This Tests

The prompt asks for another value-deepening pass, but repeated local repair may be the
real failure. A good treatment should arbitrate instead of stacking TVG and
Anti-Spiral.

### A Prompt

```text
Use Mindthus normally.

We have rewritten this handoff document twice with TVG. It is still not helping the
implementation agent. Should we run another TVG pass and add a checklist?
```

### B Prompt

```text
Use `using-mindthus`. If multiple methods seem applicable, use method arbitration.

We have rewritten this handoff document twice with TVG. It is still not helping the
implementation agent. Should we run another TVG pass and add a checklist?
```

### Expected Treatment Behavior

- Identifies TVG vs Anti-Spiral conflict.
- Uses `block` or `stop` against another same-path TVG pass unless new evidence exists.
- Returns upstream to judgment object, acceptance criteria, implementation blocker, or
  missing evidence.
- Does not stack another checklist merely because the artifact is thin.
````

- [ ] **Step 4: Add Scenario 12 for execution impact**

Add after Scenario 11:

````markdown
## Scenario 12: Coherent But No Execution Impact

### What This Tests

The prompt invites a polished conceptual judgment. A good treatment should require the
judgment to change execution.

### A Prompt

```text
Use Mindthus normally.

Our agent workflow should be more rigorous. Please analyze the situation and explain
the principles we should keep in mind.
```

### B Prompt

```text
Use `using-mindthus`. Require execution impact from the judgment.

Our agent workflow should be more rigorous. Please analyze the situation and explain
the principles we should keep in mind.
```

### Expected Treatment Behavior

- Avoids stopping at generic principles.
- Names what the judgment changes: strategy, risk handling, evidence requirement, next
  action, stopping condition, method choice, or handoff packet.
- If the prompt is too vague, asks for the missing work item or proposes a bounded next
  diagnostic instead of producing a broad essay.
````

- [ ] **Step 5: Update evaluation table**

Add rows to the `## Scores` table:

```markdown
| Values And Emotion Are Constraints, Not Facts |  |  |  |  |
| TVG Versus Anti-Spiral Arbitration |  |  |  |  |
| Coherent But No Execution Impact |  |  |  |  |
```

- [ ] **Step 6: Run focused router tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: PASS.

## Task 7: Verify Second Batch

**Files:**
- No edits unless verification exposes a contract gap.

- [ ] **Step 1: Run packaging docs tests**

Run:

```bash
python3 -m unittest tests.test_packaging_docs -v
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 3: Check whitespace**

Run:

```bash
git diff --check
```

Expected: no output.

## Task 8: Commit Second Batch

**Files:**
- Modify: `tests/test_mindthus_router_contract.py`
- Modify: `skills/using-mindthus/SKILL.md`
- Modify: `AGENTS.md`
- Modify: `tests/mindthus_router_pressure_tests.md`

- [ ] **Step 1: Review diff**

Run:

```bash
git diff -- tests/test_mindthus_router_contract.py skills/using-mindthus/SKILL.md AGENTS.md tests/mindthus_router_pressure_tests.md
```

Expected: diff only contains second-batch constraint recognition, method arbitration,
and execution-impact changes.

- [ ] **Step 2: Stage files**

Run:

```bash
git add tests/test_mindthus_router_contract.py skills/using-mindthus/SKILL.md AGENTS.md tests/mindthus_router_pressure_tests.md
```

- [ ] **Step 3: Commit**

Run:

```bash
git commit -m "docs: add mindthus judgment arbitration controls"
```

Expected: commit succeeds.

## Follow-Up Work Not In This Plan

- Issue 7: Pressure Surface Consolidation
- Any changelog or release-version decision
- Any runtime memory, retrieval, or context-ranking implementation
- Any standalone game-theory skill

## Self-Review Checklist

- Spec coverage: implements Issues 4-6 from `docs/superpowers/specs/2026-05-26-mindthus-judgment-kernel-issues-design.md`.
- Scope guard: does not implement Issue 7 pressure surface consolidation.
- No over-rigor: judgment constraints include values, interests, emotion, risk, and authority, not only evidence.
- No method stacking: arbitration actions force dominate / defer / degrade / block / stop.
- Execution value: pressure tests require downstream effect, not only coherent explanation.
