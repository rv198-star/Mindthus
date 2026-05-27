# Mindthus Skill Pattern Typicality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make existing Mindthus skills more structurally pattern-typical through lightweight internal labels, comments, and contract tests without changing behavior or public user flow.

**Architecture:** Keep the pattern taxonomy internal. Add short `Pattern Signature / 模式签名` H3 sections inside existing method layers where they clarify maintenance intent. Use tests to verify pattern identity and prevent accidental README exposure.

**Tech Stack:** Markdown documentation, Python `unittest`, existing Mindthus skill files and docs.

---

## File Responsibilities

- `docs/internal/skill-design-patterns.md`: Internal taxonomy and signature definitions for the three Mindthus patterns.
- `docs/superpowers/specs/2026-05-27-mindthus-skill-pattern-typicality-design.md`: Design rationale for Issue #8.
- `skills/using-mindthus/SKILL.md`: Judgment Kernel entry and routing signature.
- `skills/3l5s/SKILL.md`: Judgment Kernel problem-definition and decomposition signature.
- `skills/edsp/SKILL.md`: Judgment Kernel structural-judgment signature.
- `skills/sela/SKILL.md`: Judgment Kernel strategic-direction signature.
- `docs/methodologies/shared-primitives.md`: Cognitive Control primitive signature and non-authority boundary.
- `skills/wae/SKILL.md`: Cognitive Control boundary signature.
- `skills/tvg/SKILL.md`: Cognitive Control value-deepening signature.
- `docs/methodologies/anti-spiral-self-audit.md`: Cognitive Control brake signature.
- `skills/tplan/SKILL.md`: Runtime Governance signature.
- `tests/test_skill_pattern_contract.py`: New contract tests for pattern signatures.
- `tests/test_packaging_docs.py`: Keep internal docs discoverable by maintainers but absent from README.

---

## WO-8.1: Refine Internal Pattern Definitions

**Files:**
- Modify: `docs/internal/skill-design-patterns.md`
- Test: `tests/test_skill_pattern_contract.py`

- [ ] **Step 1: Add failing contract test for internal pattern signatures**

Create `tests/test_skill_pattern_contract.py`:

```python
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class SkillPatternContractTests(unittest.TestCase):
    def test_internal_pattern_doc_defines_mindthus_patterns(self):
        text = (REPO / "docs" / "internal" / "skill-design-patterns.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "Judgment Kernel Skill / 判断内核型 Skill",
            "Cognitive Control Skill / 认知控制型 Skill",
            "Runtime Governance Skill / 运行治理型 Skill",
            "Pattern Signature / 模式签名",
            "cognitive role",
            "implementation shape",
            "not part of the shallow user-facing guide",
        ):
            self.assertIn(phrase, text)

    def test_pattern_taxonomy_is_not_exposed_in_readme(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "skill-design-patterns.md",
            "Judgment Kernel Skill",
            "Cognitive Control Skill",
            "Runtime Governance Skill",
            "Pattern Signature",
        ):
            self.assertNotIn(phrase, readme)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract -v
```

Expected: fail because `Pattern Signature / 模式签名` is not yet defined in the internal pattern doc.

- [ ] **Step 3: Add explicit Pattern Signature section to internal doc**

In `docs/internal/skill-design-patterns.md`, after `## Core Claim`, add:

```md
## Pattern Signature / 模式签名

A pattern signature is a short maintainer-facing label that makes a skill's cognitive
role visible without changing behavior.

Pattern signatures should:

- sit inside existing method layers when added to `SKILL.md`
- describe cognitive role before implementation shape
- state trigger, core move, output or control effect, and boundary
- stay short enough that they do not become a second method body
- remain internal unless they directly improves user understanding
```

- [ ] **Step 4: Re-run the pattern contract test**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract -v
```

Expected: pass for WO-8.1 tests.

- [ ] **Step 5: Commit WO-8.1**

```bash
git add docs/internal/skill-design-patterns.md tests/test_skill_pattern_contract.py
git commit -m "test: define mindthus skill pattern contracts"
```

---

## WO-8.2: Add Judgment Kernel Pattern Signatures

**Files:**
- Modify: `skills/using-mindthus/SKILL.md`
- Modify: `skills/3l5s/SKILL.md`
- Modify: `skills/edsp/SKILL.md`
- Modify: `skills/sela/SKILL.md`
- Modify: `tests/test_skill_pattern_contract.py`

- [ ] **Step 1: Add failing tests for Judgment Kernel signatures**

Append this test method to `SkillPatternContractTests`:

```python
    def test_judgment_kernel_skills_have_pattern_signatures(self):
        cases = {
            "using-mindthus": (
                "Pattern: Judgment Kernel",
                "Trigger: task-level uncertainty about whether to execute directly, gather input, or enter Mindthus",
                "Core move: route by intervention boundary, judgment object, constraints, arbitration, and execution impact",
                "Boundary: do not use Mindthus when direct execution or information acquisition is sufficient",
            ),
            "3l5s": (
                "Pattern: Judgment Kernel",
                "Trigger: unclear problem definition or known problem that is too large to execute directly",
                "Core move: turn signal into falsifiable problem, then problem into verifiable action",
                "Boundary: do not run the full three-layer form when a single-layer BTGSB is enough",
            ),
            "edsp": (
                "Pattern: Judgment Kernel",
                "Trigger: structural ambiguity, malformed binary, unclear boundary, or trend judgment",
                "Core move: use extreme deduction to build a structural coordinate system before scenario projection",
                "Boundary: do not replace missing evidence, domain research, runtime proof, or stakeholder judgment",
            ),
            "sela": (
                "Pattern: Judgment Kernel",
                "Trigger: local advantage is real but system-level efficiency may be shifting the decision",
                "Core move: compare local advantage with system efficiency, then apply timing and role pressure",
                "Boundary: do not turn long-term direction into immediate action without timing and risk checks",
            ),
        }
        for skill, phrases in cases.items():
            text = (REPO / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("### Pattern Signature / 模式签名", text, skill)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{skill} missing {phrase!r}")
```

- [ ] **Step 2: Run the failing Judgment Kernel test**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract.SkillPatternContractTests.test_judgment_kernel_skills_have_pattern_signatures -v
```

Expected: fail because the signatures have not been added.

- [ ] **Step 3: Add signature to `skills/using-mindthus/SKILL.md`**

Inside `## Core Claim / 核心判断`, after the opening bullet list, add:

```md
### Pattern Signature / 模式签名

- Pattern: Judgment Kernel
- Trigger: task-level uncertainty about whether to execute directly, gather input, or enter Mindthus
- Core move: route by intervention boundary, judgment object, constraints, arbitration, and execution impact
- Output impact: changes method choice, evidence requirement, next action, stopping condition, or handoff packet
- Boundary: do not use Mindthus when direct execution or information acquisition is sufficient
```

- [ ] **Step 4: Add signature to `skills/3l5s/SKILL.md`**

Inside `## Core Claim / 核心判断`, after the two valid forms list, add:

```md
### Pattern Signature / 模式签名

- Pattern: Judgment Kernel
- Trigger: unclear problem definition or known problem that is too large to execute directly
- Core move: turn signal into falsifiable problem, then problem into verifiable action
- Output impact: changes problem statement, strategy, acceptance evidence, or next executable task
- Boundary: do not run the full three-layer form when a single-layer BTGSB is enough
```

- [ ] **Step 5: Add signature to `skills/edsp/SKILL.md`**

Inside `## Core Claim / 核心判断`, after the core claim summary, add:

```md
### Pattern Signature / 模式签名

- Pattern: Judgment Kernel
- Trigger: structural ambiguity, malformed binary, unclear boundary, or trend judgment
- Core move: use extreme deduction to build a structural coordinate system before scenario projection
- Output impact: changes the proposition, option boundary, scenario choice, or evidence requirement
- Boundary: do not replace missing evidence, domain research, runtime proof, or stakeholder judgment
```

- [ ] **Step 6: Add signature to `skills/sela/SKILL.md`**

Inside `## Core Claim / 核心判断`, after the core claim summary, add:

```md
### Pattern Signature / 模式签名

- Pattern: Judgment Kernel
- Trigger: local advantage is real but system-level efficiency may be shifting the decision
- Core move: compare local advantage with system efficiency, then apply timing and role pressure
- Output impact: changes strategic direction, timing, risk handling, or transition plan
- Boundary: do not turn long-term direction into immediate action without timing and risk checks
```

- [ ] **Step 7: Run tests for Judgment Kernel signatures and method layering**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract tests.test_method_layering_contract -v
```

Expected: pass. The H3 signature sections must not violate method layering H2 rules.

- [ ] **Step 8: Commit WO-8.2**

```bash
git add skills/using-mindthus/SKILL.md skills/3l5s/SKILL.md skills/edsp/SKILL.md skills/sela/SKILL.md tests/test_skill_pattern_contract.py
git commit -m "docs: mark judgment kernel skill signatures"
```

---

## WO-8.3: Add Cognitive Control Pattern Signatures

**Files:**
- Modify: `docs/methodologies/shared-primitives.md`
- Modify: `skills/wae/SKILL.md`
- Modify: `skills/tvg/SKILL.md`
- Modify: `docs/methodologies/anti-spiral-self-audit.md`
- Modify: `tests/test_skill_pattern_contract.py`

- [ ] **Step 1: Add failing tests for Cognitive Control signatures**

Append this test method:

```python
    def test_cognitive_control_surfaces_have_pattern_signatures(self):
        cases = {
            "docs/methodologies/shared-primitives.md": (
                "Pattern: Cognitive Control",
                "Trigger signal: a repeated small judgment rule controls quality across multiple methods",
                "Control action: cap, pressure, brake, translate, or reduce method use",
                "Non-authority: cognitive primitives do not own the main semantic judgment",
            ),
            "skills/wae/SKILL.md": (
                "Pattern: Cognitive Control",
                "Trigger signal: workflow, agentic judgment, evidence, or review may control the wrong part of the work",
                "Control action: reassign control among workflow, agentic judgment, evidence, and escalation",
                "Non-authority: WAE does not decide domain truth by worksheet completion",
            ),
            "skills/tvg/SKILL.md": (
                "Pattern: Cognitive Control",
                "Trigger signal: a bounded artifact looks complete but remains thin in practical value",
                "Control action: deepen value, name veto constraints, or block freeze",
                "Non-authority: TVG does not reopen whole-project strategy",
            ),
            "docs/methodologies/anti-spiral-self-audit.md": (
                "Pattern: Cognitive Control",
                "Trigger signal: third touch, negative feedback, add-layer impulse, or weak evidence delta",
                "Control action: brake local repair and return upstream",
                "Non-authority: Anti-Spiral does not forbid normal evidence-driven debugging",
            ),
        }
        for relative_path, phrases in cases.items():
            text = (REPO / relative_path).read_text(encoding="utf-8")
            self.assertIn("### Pattern Signature / 模式签名", text, relative_path)
            for phrase in phrases:
                self.assertIn(phrase, text, f"{relative_path} missing {phrase!r}")
```

- [ ] **Step 2: Run the failing Cognitive Control test**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract.SkillPatternContractTests.test_cognitive_control_surfaces_have_pattern_signatures -v
```

Expected: fail because signatures are not present.

- [ ] **Step 3: Add signature to `docs/methodologies/shared-primitives.md`**

Inside `## 核心判断`, after the three-point definition, add:

```md
### Pattern Signature / 模式签名

- Pattern: Cognitive Control
- Trigger signal: a repeated small judgment rule controls quality across multiple methods
- Protected failure mode: local guardrails duplicate, drift, or become new methods
- Control action: cap, pressure, brake, translate, or reduce method use
- Owner: the primitive index names the primary owner for each control point
- Non-authority: cognitive primitives do not own the main semantic judgment
```

- [ ] **Step 4: Add signature to `skills/wae/SKILL.md`**

Inside `## Core Claim / 核心判断`, after the mismatch bullet list, add:

```md
### Pattern Signature / 模式签名

- Pattern: Cognitive Control
- Trigger signal: workflow, agentic judgment, evidence, or review may control the wrong part of the work
- Protected failure mode: clean structure freezes uncertain truth or hides thin judgment
- Control action: reassign control among workflow, agentic judgment, evidence, and escalation
- Owner: WAE owns control-boundary judgment
- Non-authority: WAE does not decide domain truth by worksheet completion
```

- [ ] **Step 5: Add signature to `skills/tvg/SKILL.md`**

Inside `## Core Claim`, after the short rule and core inputs, add:

```md
### Pattern Signature / 模式签名

- Pattern: Cognitive Control
- Trigger signal: a bounded artifact looks complete but remains thin in practical value
- Protected failure mode: polished structure freezes low-value output
- Control action: deepen value, name veto constraints, or block freeze
- Owner: TVG owns bounded-artifact value pressure
- Non-authority: TVG does not reopen whole-project strategy
```

- [ ] **Step 6: Add signature to `docs/methodologies/anti-spiral-self-audit.md`**

Inside `## 核心判断`, after the core judgment paragraph, add:

```md
### Pattern Signature / 模式签名

- Pattern: Cognitive Control
- Trigger signal: third touch, negative feedback, add-layer impulse, or weak evidence delta
- Protected failure mode: local repair replaces upstream progress
- Control action: brake local repair and return upstream
- Owner: Anti-Spiral owns repeated local repair pressure
- Non-authority: Anti-Spiral does not forbid normal evidence-driven debugging
```

- [ ] **Step 7: Run Cognitive Control tests**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract tests.test_packaging_docs -v
```

Expected: pass.

- [ ] **Step 8: Commit WO-8.3**

```bash
git add docs/methodologies/shared-primitives.md skills/wae/SKILL.md skills/tvg/SKILL.md docs/methodologies/anti-spiral-self-audit.md tests/test_skill_pattern_contract.py
git commit -m "docs: mark cognitive control signatures"
```

---

## WO-8.4: Add Runtime Governance Pattern Signature

**Files:**
- Modify: `skills/tplan/SKILL.md`
- Modify: `tests/test_skill_pattern_contract.py`

- [ ] **Step 1: Add failing test for Runtime Governance signature**

Append this test method:

```python
    def test_tplan_has_runtime_governance_signature(self):
        text = (REPO / "skills" / "tplan" / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "### Pattern Signature / 模式签名",
            "Pattern: Runtime Governance",
            "Runtime state: stable Mission, task tree, active task, evidence, logs, and policy",
            "Evidence boundary: evidence constrains completion, continuation, split, stop, and closure claims",
            "Authority boundary: human-in-loop policy decides recommendation versus mutation",
            "Transition mechanics: continue, split, pause, subtract, stop, close, or hand off through a decision packet",
            "Boundary: tplan is runtime governance, not a fixed business pipeline",
        ):
            self.assertIn(phrase, text)
```

- [ ] **Step 2: Run the failing Runtime Governance test**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract.SkillPatternContractTests.test_tplan_has_runtime_governance_signature -v
```

Expected: fail because `tplan` has no signature yet.

- [ ] **Step 3: Add signature to `skills/tplan/SKILL.md`**

Inside `## Core Claim / 核心判断`, after the semantic judgment delegation summary, add:

```md
### Pattern Signature / 模式签名

- Pattern: Runtime Governance
- Runtime state: stable Mission, task tree, active task, evidence, logs, and policy
- Evidence boundary: evidence constrains completion, continuation, split, stop, and closure claims
- Authority boundary: human-in-loop policy decides recommendation versus mutation
- Transition mechanics: continue, split, pause, subtract, stop, close, or hand off through a decision packet
- Boundary: tplan is runtime governance, not a fixed business pipeline
```

- [ ] **Step 4: Run Runtime Governance and tplan tests**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract -v
python3 -m unittest discover -s tests/tplan -v
```

Expected: both pass.

- [ ] **Step 5: Commit WO-8.4**

```bash
git add skills/tplan/SKILL.md tests/test_skill_pattern_contract.py
git commit -m "docs: mark tplan runtime governance signature"
```

---

## WO-8.5: Final Contract Pass And Issue Update

**Files:**
- Modify if needed: `tests/test_packaging_docs.py`
- Modify if needed: `docs/internal/skill-design-patterns.md`
- External update: GitHub issue #8 comment

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_skill_pattern_contract -v
python3 -m unittest tests.test_packaging_docs -v
python3 -m unittest tests.test_method_layering_contract -v
```

Expected: all pass.

- [ ] **Step 2: Run full verification**

Run:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Expected: full suite passes and `git diff --check` has no output.

- [ ] **Step 3: Confirm shallow user docs are unchanged**

Run:

```bash
git diff -- README.md
```

Expected: no output unless the user explicitly approved a README change.

- [ ] **Step 4: Add issue progress comment**

Post a concise issue comment:

```bash
gh issue comment 8 --body "Pattern typicality design and implementation plan are recorded:

- Spec: docs/superpowers/specs/2026-05-27-mindthus-skill-pattern-typicality-design.md
- Plan: docs/superpowers/plans/2026-05-27-mindthus-skill-pattern-typicality.md
- Scope: lightweight pattern signatures and internal contract tests only; no behavior change or shallow README exposure.
"
```

- [ ] **Step 5: Commit any final adjustments**

If Step 1-3 required changes, commit them:

```bash
git add docs/internal/skill-design-patterns.md tests/test_packaging_docs.py tests/test_skill_pattern_contract.py
git commit -m "test: verify skill pattern typicality contracts"
```

If no files changed, skip this commit.

## Final Verification Checklist

- [ ] Internal docs define three Mindthus patterns.
- [ ] Relevant skill surfaces have lightweight pattern signatures.
- [ ] README does not expose internal taxonomy.
- [ ] `SKILL.md` files still obey method layering H2 constraints.
- [ ] Cognitive primitives remain non-standalone control points.
- [ ] `tplan` remains Runtime Governance, not fixed pipeline.
- [ ] Full test suite passes.
- [ ] `git diff --check` has no output.

