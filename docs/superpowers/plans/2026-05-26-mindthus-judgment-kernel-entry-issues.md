# Mindthus Judgment Kernel Entry Issues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first batch of Mindthus judgment-kernel issues: intervention boundary, judgment-object routing, and context injection point.

**Architecture:** Keep the change in `using-mindthus` as the router surface, with a short mirror in `AGENTS.md`. Add contract tests first, then update the router text and pressure-test scenarios. Do not implement memory, retrieval, method arbitration, or full 6+1 capability in this batch.

**Tech Stack:** Markdown docs, Python `unittest`, existing Mindthus contract and pressure-test files.

---

## File Structure

- Modify: `tests/test_mindthus_router_contract.py`
  - Static contract tests for the new entry boundary, judgment-object routing, and context injection point.
- Modify: `skills/using-mindthus/SKILL.md`
  - Primary router implementation surface.
  - Add entry-boundary, judgment-object, and context-injection sections under `### Skill 路由`.
- Modify: `AGENTS.md`
  - Short project-level mirror of the entry-boundary and context-injection discipline.
- Modify: `tests/mindthus_router_pressure_tests.md`
  - Add pressure scenarios for direct execution, missing information, judgment-object routing, and injected-context conflicts.
- Existing files intentionally not modified in this batch:
  - `docs/methodologies/shared-primitives.md`: no new primitive yet.
  - Individual skill files: no changes to SELA / 3L5S / EDSP / WAE / TVG / tplan core methods.
  - Runtime scripts: no memory, retrieval, or router automation.

## Task 1: Add Router Contract Tests

**Files:**
- Modify: `tests/test_mindthus_router_contract.py`

- [ ] **Step 1: Add failing tests for intervention boundary**

Add this method inside `MindthusRouterContractTests` after `test_minimal_sufficient_lens_does_not_change_tplan_activation`:

```python
    def test_using_mindthus_defines_intervention_boundary_before_skill_choice(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Intervention Boundary / 介入边界",
            "Direct execution / 直接执行",
            "Information acquisition / 信息补全",
            "Mindthus intervention / Mindthus 介入",
            "do not use Mindthus",
            "facts, files, data, runtime proof, or user clarification",
            "hard judgment point",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 2: Add failing tests for judgment-object routing**

Add this method after the intervention-boundary test:

```python
    def test_judgment_object_routing_precedes_individual_skill_routes(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("#### Judgment Object Routing / 判断对象路由")
        first_skill = text.index("#### `sela`", start)
        section = text[start:first_skill]
        for phrase in (
            "Problem-definition failure",
            "False binary or structural ambiguity",
            "Long-term system efficiency versus local advantage",
            "Agentic-system control-boundary mismatch",
            "Bounded artifact with thin practical value",
            "Mission runtime state",
            "Repeated local repair",
        ):
            self.assertIn(phrase, section)
```

- [ ] **Step 3: Add failing tests for conservative TVG and tplan activation**

Add this method after the judgment-object routing test:

```python
    def test_tvg_and_tplan_are_non_proactive_routes(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "TVG requires a bounded artifact",
            "tplan requires Mission-level runtime state",
            "do not proactively activate",
            "ordinary complexity is not enough",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 4: Add failing tests for context injection interface**

Add this method after the TVG/tplan test:

```python
    def test_context_injection_point_is_interface_not_memory_implementation(self):
        text = (REPO / "skills" / "using-mindthus" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Context Injection Point / 上下文注入口",
            "does not implement memory",
            "storage, retrieval, ranking",
            "current user input takes priority",
            "must not silently override",
            "user_preference",
            "long_term_objective",
            "risk_posture",
            "authority_boundary",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 5: Add failing tests for AGENTS mirror**

Add this method after the context injection test:

```python
    def test_agents_mentions_entry_boundary_and_context_injection(self):
        text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
        for phrase in (
            "介入边界",
            "直接执行",
            "先补事实",
            "Mindthus 介入",
            "上下文注入口",
            "当前用户输入优先",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 6: Run tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: FAIL with missing phrases from the new tests.

## Task 2: Update `using-mindthus` Entry Router

**Files:**
- Modify: `skills/using-mindthus/SKILL.md`

- [ ] **Step 1: Add entry-boundary section under Skill Routing**

In `skills/using-mindthus/SKILL.md`, immediately after `### Skill 路由`, add:

```markdown
#### Intervention Boundary / 介入边界

Before choosing a Mindthus skill, decide whether Mindthus should intervene at all.

- Direct execution / 直接执行: the task is clear, low-risk, bounded, and facts are
  sufficient. In this case, do not use Mindthus; answer or execute directly.
- Information acquisition / 信息补全: facts, files, data, runtime proof, or user
  clarification are missing. First gather the missing input or ask the user; do not
  turn missing information into a confident method judgment.
- Mindthus intervention / Mindthus 介入: the task contains a hard judgment point such
  as unclear problem definition, structural ambiguity, trend or timing judgment,
  control-boundary mismatch, thin bounded artifact, Mission-runtime drift, or repeated
  local repair.

Short rule: simple tasks stay with the base model; missing facts get more input; hard
judgment points enter Mindthus.
```

- [ ] **Step 2: Add judgment-object routing section**

Immediately after the intervention-boundary section, add:

```markdown
#### Judgment Object Routing / 判断对象路由

After Mindthus intervention is justified, identify the active judgment object before
choosing an individual skill:

| Judgment object | Default route | Do-not-trigger boundary |
|---|---|---|
| Problem-definition failure | `3l5s` | Do not run full 3L5S when the task is already clear and directly executable. |
| False binary or structural ambiguity | `edsp` | Do not use EDSP when the missing input is facts, domain research, runtime proof, or stakeholder judgment. |
| Long-term system efficiency versus local advantage | `sela` | Do not turn long-term direction into immediate action without timing and risk checks. |
| Agentic-system control-boundary mismatch | `wae` | No agentic system or controller mismatch, no WAE. |
| Bounded artifact with thin practical value | `tvg` | TVG requires a bounded artifact; do not proactively activate it for vague dissatisfaction or ordinary writing quality. |
| Mission runtime state, evidence, continuation, or stopping problem | `tplan` | tplan requires Mission-level runtime state; ordinary complexity is not enough. |
| Repeated local repair or add-layer spiral | `Anti-Spiral` | Use the brake to return upstream; do not make Anti-Spiral a standalone skill. |

If no judgment object is active, return to direct execution, information acquisition,
or user clarification.
```

- [ ] **Step 3: Add context-injection section**

Immediately after the judgment-object routing section, add:

```markdown
#### Context Injection Point / 上下文注入口

Mindthus may receive relevant contextual constraints from an upstream platform, but it
does not implement memory, storage, retrieval, ranking, or profile management.

Optional injected context may include:

- `current_goal`
- `user_preference`
- `long_term_objective`
- `role_or_stake`
- `prior_experience`
- `risk_posture`
- `emotional_signal`
- `authority_boundary`
- `fresh_context`

Use injected context only as judgment constraints or signals. The current user input
takes priority over older context, and injected context must not silently override the
user's current instruction. If injected context conflicts with current input, surface
the conflict before using it.
```

- [ ] **Step 4: Run focused router tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: the new `using-mindthus` tests pass, but the AGENTS mirror test still fails.

## Task 3: Update `AGENTS.md` Mirror Guidance

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add concise entry-boundary text**

In `AGENTS.md`, after the paragraph about premise calibration, add:

```markdown
在选择具体 skill 前，先做介入边界判断：

- 简单、明确、低风险、事实足够的任务，直接执行，不用 Mindthus。
- 信息不足时，先补事实、读文件、运行验证或继续问用户，不要用方法包装缺口。
- 只有出现 hard judgment point 时才进入 Mindthus 介入，例如问题未定义、结构判断、
  趋势/时机取舍、控制边界、薄产物、长任务漂移或局部修补螺旋。
```

- [ ] **Step 2: Add concise context-injection text**

Immediately after the entry-boundary paragraph, add:

```markdown
上游平台可以通过上下文注入口提供少量相关背景，例如长期目标、用户偏好、历史经验、
风险姿态、角色立场或权限边界。当前用户输入优先；注入上下文只能作为判断约束或线索，
不能静默覆盖本轮明确指令。
```

- [ ] **Step 3: Run focused router tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: all router contract tests pass.

## Task 4: Extend Router Pressure Tests

**Files:**
- Modify: `tests/mindthus_router_pressure_tests.md`

- [ ] **Step 1: Add capability-target bullets**

In `## Capability Target`, append:

```markdown
- choosing direct execution when the task is clear and low-risk
- choosing information acquisition when facts, files, data, runtime proof, or user
  clarification are missing
- identifying the active judgment object before naming a skill
- treating injected context as a constraint, not an override
```

- [ ] **Step 2: Add Scenario 6 for direct execution**

Add before `## Evaluation Template`:

````markdown
## Scenario 6: Simple Direct Task

### What This Tests

The prompt is clear, low-risk, and directly executable. A good treatment should not
force Mindthus intervention.

### A Prompt

```text
Use Mindthus normally.

Please rewrite this sentence to be shorter: "The current implementation provides a
large number of useful capabilities, but it may be too verbose for release notes."
```

### B Prompt

```text
Use `using-mindthus`. Apply the intervention boundary before choosing any skill.

Please rewrite this sentence to be shorter: "The current implementation provides a
large number of useful capabilities, but it may be too verbose for release notes."
```

### Expected Treatment Behavior

- Chooses direct execution.
- Does not invoke 3L5S, EDSP, SELA, WAE, TVG, or tplan.
- Produces the shorter sentence.
````

- [ ] **Step 3: Add Scenario 7 for missing information**

Add after Scenario 6:

````markdown
## Scenario 7: Missing Runtime Proof

### What This Tests

The prompt asks for a judgment that depends on missing runtime evidence. A good
treatment should gather or request evidence before judging.

### A Prompt

```text
Use Mindthus normally.

The new parser is probably safe. Should we remove the old parser path?
```

### B Prompt

```text
Use `using-mindthus`. Apply the intervention boundary before choosing any skill.

The new parser is probably safe. Should we remove the old parser path?
```

### Expected Treatment Behavior

- Chooses information acquisition before final judgment.
- Names missing runtime proof, comparison evidence, rollback risk, or test coverage.
- Does not turn "probably safe" into a confident conclusion.
- May route later to WAE or tplan only after the missing evidence is identified.
````

- [ ] **Step 4: Add Scenario 8 for judgment-object routing**

Add after Scenario 7:

````markdown
## Scenario 8: Thin Artifact Versus Problem Definition

### What This Tests

The prompt contains both dissatisfaction and an existing bounded artifact. A good
treatment should identify whether the active judgment object is a thin artifact or an
undefined problem.

### A Prompt

```text
Use Mindthus normally.

This design note is complete but still does not help the implementation agent decide
what to do next. Should we rewrite it?
```

### B Prompt

```text
Use `using-mindthus`. Identify the judgment object before selecting a skill.

This design note is complete but still does not help the implementation agent decide
what to do next. Should we rewrite it?
```

### Expected Treatment Behavior

- Identifies a bounded artifact with thin practical value.
- Routes to TVG only because the artifact exists and the weakness is downstream value.
- Names implementation handoff, actionability, evidence, or failure paths as the value
  surfaces.
````

- [ ] **Step 5: Add Scenario 9 for injected-context conflict**

Add after Scenario 8:

````markdown
## Scenario 9: Injected Context Conflict

### What This Tests

Injected context can constrain judgment, but it must not silently override the user's
current instruction.

### A Prompt

```text
Use Mindthus normally.

Injected context: the user usually prefers long-term maintainability over speed.

Current user request: for this one-off internal script, optimize for fastest safe
delivery and avoid broad refactors.

Should we redesign the module before making the script change?
```

### B Prompt

```text
Use `using-mindthus`. Apply the context injection point rules.

Injected context: the user usually prefers long-term maintainability over speed.

Current user request: for this one-off internal script, optimize for fastest safe
delivery and avoid broad refactors.

Should we redesign the module before making the script change?
```

### Expected Treatment Behavior

- Surfaces the conflict between older preference and current instruction.
- Gives priority to the current explicit request.
- Uses injected context only as a caution against unsafe shortcuts.
- Does not silently expand scope into broad redesign.
````

- [ ] **Step 6: Update evaluation table**

Add rows to the `## Scores` table:

```markdown
| Simple Direct Task |  |  |  |  |
| Missing Runtime Proof |  |  |  |  |
| Thin Artifact Versus Problem Definition |  |  |  |  |
| Injected Context Conflict |  |  |  |  |
```

- [ ] **Step 7: Run focused router contract tests**

Run:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
```

Expected: PASS.

## Task 5: Verify Packaging And Full Test Suite

**Files:**
- No code edits unless tests expose a real contract gap.

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

## Task 6: Commit First Batch

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

Expected: diff only contains first-batch entry-boundary, judgment-object routing, and
context-injection changes.

- [ ] **Step 2: Stage files**

Run:

```bash
git add tests/test_mindthus_router_contract.py skills/using-mindthus/SKILL.md AGENTS.md tests/mindthus_router_pressure_tests.md
```

- [ ] **Step 3: Commit**

Run:

```bash
git commit -m "docs: add mindthus judgment entry boundary"
```

Expected: commit succeeds.

## Follow-Up Work Not In This Plan

These are intentionally separate issues:

- Issue 4: Judgment Constraint Recognition
- Issue 5: Method Arbitration Rules
- Issue 6: Execution Impact Requirement
- Issue 7: Pressure Surface Consolidation

Do not implement them in this first batch except where wording is necessary to keep
entry-boundary and context-injection semantics accurate.

## Self-Review Checklist

- Spec coverage: implements Issues 1-3 from `docs/superpowers/specs/2026-05-26-mindthus-judgment-kernel-issues-design.md`.
- No memory implementation: plan only documents an injection point.
- No roadmap claim: plan does not assign work to a version release.
- No full meta-framework: changes stay in router guidance and tests.
- Existing constraints preserved: `minimal_sufficient_lens_does_not_change_tplan_activation` still passes because new sections live under `### Skill 路由`.
