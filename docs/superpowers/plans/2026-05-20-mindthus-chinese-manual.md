# Mindthus 中文说明书与入口页更新 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `README.md` 改成中文入口页，并新增一份 `docs/` 下的中文总说明书，帮助新读者快速理解 Mindthus 是什么、能做什么、如何做到。

**Architecture:** `README.md` 保持项目首页和最短路径入口，新增的 `docs/guide.md` 承担中文总说明书和使用场景展开。`skills/sela/resources/methodology.md` 只补哲学说明，不新增 `SKILL.md` 层级。测试继续集中在 `tests/test_packaging_docs.py`，只为新文档链接和关键措辞加硬约束。

**Tech Stack:** Markdown, Python `unittest`, existing repository doc/test conventions.

---

### Task 1: Make the README a Chinese entry page with a docs link

**Files:**
- Modify: `README.md`
- Modify: `tests/test_packaging_docs.py`

- [ ] **Step 1: Write the failing test**

```python
def test_readme_links_to_chinese_manual(self):
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    self.assertIn("[中文说明书](docs/guide.md)", readme)
    self.assertIn("是什么", readme)
    self.assertIn("能做什么", readme)
    self.assertIn("如何做到", readme)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_packaging_docs.PackagingDocsTests.test_readme_links_to_chinese_manual -v`
Expected: FAIL because the README still has the current English-first layout and no docs link.

- [ ] **Step 3: Write minimal implementation**

```markdown
# Mindthus / 此心

Mindthus 是一个个人方法论与 agent 构建项目。

## 它是什么

Mindthus 把判断、边界、行动姿态和可复用技能整理成 `AGENTS.md` 和 `SKILLS`。

## 它能做什么

- 路由问题到合适的方法镜头
- 把复杂判断拆成可执行任务
- 把长期任务控制在可验证的边界内

## 它如何做到

- `AGENTS.md` 提供项目级姿态
- `skills/*/SKILL.md` 提供独立技能
- `docs/guide.md` 提供面向新读者的中文总说明书

更多说明见 [中文说明书](docs/guide.md)。
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_packaging_docs.PackagingDocsTests.test_readme_links_to_chinese_manual -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_packaging_docs.py
git commit -m "docs: add chinese manual entry in readme"
```

### Task 2: Add the Chinese manual in docs/

**Files:**
- Create: `docs/guide.md`
- Modify: `tests/test_packaging_docs.py`

- [ ] **Step 1: Write the failing test**

```python
def test_chinese_manual_covers_usage_scenarios(self):
    guide = (REPO / "docs" / "guide.md").read_text(encoding="utf-8")
    self.assertIn("Mindthus 是什么", guide)
    self.assertIn("Mindthus 能做什么", guide)
    self.assertIn("Mindthus 如何做到", guide)
    self.assertIn("使用场景", guide)
    self.assertIn("SELA", guide)
    self.assertIn("3L5S", guide)
    self.assertIn("WAE", guide)
    self.assertIn("tplan", guide)
    self.assertIn("Anti-Spiral", guide)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_packaging_docs.PackagingDocsTests.test_chinese_manual_covers_usage_scenarios -v`
Expected: FAIL because `docs/guide.md` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```markdown
# Mindthus 中文说明书

## Mindthus 是什么

Mindthus 是一套把方法论、边界和行动控制整理成可复用技能包的项目。

## Mindthus 能做什么

- 让 agent 先判断问题类型，再选方法
- 用分层格式表达方法，避免主思想被补丁淹没
- 把长任务控制、证据记录和停止条件写成可执行机制

## Mindthus 如何做到

- `AGENTS.md` 负责项目姿态
- `skills/` 负责具体方法
- `docs/methodologies/` 负责跨技能的方法资源

## 使用场景

- 重大趋势判断：用 `SELA`
- 混乱问题拆解：用 `3L5S`
- 结构判断：用 `EDSP`
- 控制边界：用 `WAE`
- 长任务控制：用 `tplan`
- 防止局部修补螺旋：用 `Anti-Spiral`

## 导航

- 回到 [README](../README.md)
- 查看 [SELA 方法资源](../skills/sela/resources/methodology.md)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_packaging_docs.PackagingDocsTests.test_chinese_manual_covers_usage_scenarios -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/guide.md tests/test_packaging_docs.py
git commit -m "docs: add chinese manual"
```

### Task 3: Add the overall-vs-local philosophy to SELA

**Files:**
- Modify: `skills/sela/resources/methodology.md`
- Modify: `tests/test_packaging_docs.py`

- [ ] **Step 1: Write the failing test**

```python
def test_sela_methodology_names_the_overall_local_tradeoff(self):
    text = (REPO / "skills" / "sela" / "resources" / "methodology.md").read_text(
        encoding="utf-8"
    )
    self.assertIn("整体与局部", text)
    self.assertIn("可逆", text)
    self.assertIn("反馈", text)
    self.assertIn("可修正", text)
    self.assertIn("不是静态最优", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_packaging_docs.PackagingDocsTests.test_sela_methodology_names_the_overall_local_tradeoff -v`
Expected: FAIL because the current SELA methodology does not yet spell out the feedback-loop framing.

- [ ] **Step 3: Write minimal implementation**

```markdown
## 整体与局部的平衡

SELA 不是要求把所有局部都压平到同一个效率目标上。更准确地说，它要求整体给方向，局部给真实性，边界给不可逾越的约束。

真正可落地的不是一次性静态最优，而是可逆、可观察、可修正的持续逼近：

- `可逆`：错了能退
- `可观察`：能及时看见偏差
- `可修正`：反馈来了能改

因此，SELA 反对把“长期方向正确”误写成“现在立刻全切”。整体最优和局部最优的关系，不是消灭局部，而是让局部保留校准系统的能力。
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_packaging_docs.PackagingDocsTests.test_sela_methodology_names_the_overall_local_tradeoff -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/sela/resources/methodology.md tests/test_packaging_docs.py
git commit -m "docs: clarify sela overall local balance"
```

### Task 4: Run the focused doc checks

**Files:**
- Modify: none

- [ ] **Step 1: Run the full packaging docs suite**

Run: `python3 -m unittest tests.test_packaging_docs -v`
Expected: PASS.

- [ ] **Step 2: Run the existing repository checks**

Run: `python3 -m unittest discover -s tests/tplan -v`
Expected: PASS.

- [ ] **Step 3: Check for unintended markdown churn**

Run: `git diff --check`
Expected: no whitespace or formatting errors.

- [ ] **Step 4: Commit the documentation bundle**

```bash
git add README.md docs/guide.md skills/sela/resources/methodology.md tests/test_packaging_docs.py
git commit -m "docs: add chinese manual and sela framing"
```
