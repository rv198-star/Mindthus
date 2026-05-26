# Mindthus Shared Primitives / 横切原语

## 这是什么

Shared primitives are cross-cutting reasoning controls used by multiple Mindthus skills.

They are not standalone skills. They are closer to AOP concerns in software design:
logging, authorization, and transactions should not be hand-written inside every
business function; likewise, recurring reasoning brakes and pressure mechanisms should
not be reinvented inside every Mindthus method.

中文短句：

> 横切原语负责保护主方法，不负责替代主方法。

## 解决什么问题

Without shared primitives, Mindthus can decay in three ways:

- the same guardrail gets copied into several skills with different names;
- a guardrail quietly becomes a new judgment center;
- users must learn duplicated vocabulary before they can use the core method.

Shared primitives keep the main methods clean:

- `3L5S` still owns problem discovery, definition, and landing.
- `SELA` still owns system-efficiency versus local-advantage judgment.
- `EDSP` still owns structural ambiguity and scenario placement.
- `WAE` still owns control-boundary judgment.
- `TVG` still owns bounded thin-value deepening.
- `tplan` still owns Mission runtime discipline.

The primitive protects these mainlines at recurring failure points.

## 核心判断

Mindthus should extract a shared primitive only when all three conditions hold:

1. The mechanism appears across several methods.
2. It protects a mainline instead of becoming the mainline.
3. It can stay smaller than a standalone skill.

If a mechanism only belongs to one method, keep it inside that method. If a mechanism
needs its own goal, examples, boundaries, and runtime, it may be a future skill, not a
shared primitive.

## 怎么用

Use shared primitives as short triggered checks.

Do not run them by default. Trigger one only when its failure signal is present.

### Minimal Sufficient Lens

Use this when the agent may be over-methodizing.

Ask:

- Can this be answered directly?
- Is one skill enough?
- Is a lightweight check enough?

If yes, stop expanding method ceremony.

### Evidence / Claim Ceiling

Use this when a claim may be stronger than its proof.

Ask:

- What evidence constrains this claim?
- Is the missing input factual, domain-specific, runtime, or stakeholder-owned?
- Should the conclusion be downgraded to a hypothesis, open question, or review-bound
  statement?

Scripts, schemas, and complete templates do not raise claim confidence by themselves.

### Perspective Pressure

Use this when one viewpoint may be too self-consistent.

There are two useful forms:

- `Multi-Role Pressure`: synthetic roles challenge the reasoning structure. Example:
  `Builder / Challenger / Synthesizer`.
- `Adversarial Incentive Check`: stakeholder or incentive roles challenge whether real
  interests are distorting the judgment.

Use synthetic roles when the risk is single-perspective reasoning. Use incentive roles
when real participants may benefit, lose, hide, delay, or transfer risk.

### Anti-Spiral

Use this when local repair may be replacing objective progress.

Signals:

- same local object touched for the third time;
- user feedback gets worse or remains unsatisfied;
- next step adds another layer, fallback, rule, or special case;
- same-path continuation will not produce decision-constraining evidence.

Short rule:

> Third touch, stop first.

### No Abstract Jargon Wall

Use this when explanation starts to become internal vocabulary.

Before method labels, provide at least one of:

- a concrete example;
- a short story;
- a simple analogy;
- a direct consequence.

Say what this means for the user before naming what Mindthus calls it.

## 具体案例

### 案例 A：SELA 里出现真实利益冲突

A company considers replacing human onboarding with an AI onboarding agent. If the only
question is long-term efficiency versus local human advantage, `SELA` is enough.

If sales, customer success, finance, and onboarding specialists each have different
costs, benefits, and incentives to package the truth, trigger `Perspective Pressure`
with an `Adversarial Incentive Check`.

The primitive does not replace `SELA`. It protects SELA from accepting one stakeholder's
local optimum as the whole-company optimum.

### 案例 B：TVG 想继续加深第三轮

A handoff document has already been deepened twice. The next proposal is to add another
section, another checklist, and another reviewer note.

This may be a TVG task, but the repeated local expansion triggers `Anti-Spiral`.
The right move may be deletion, equal replacement, or returning to the earlier judgment
point, not a third value-gain round.

### 案例 C：WAE 输出很整齐但没有证据约束

A worksheet says a release is safe because every field is filled. This is a shape pass,
not proof.

Trigger `Evidence / Claim Ceiling`: identify the claim, link runtime evidence, or
downgrade the conclusion.

## 常见误用

First misuse: turning a shared primitive into a new skill by stealth. If every task must
run a primitive, it is no longer a triggered cross-cutting control.

Second misuse: copying the primitive into each skill with different names. That creates
architecture decay.

Third misuse: letting primitives decide the answer. They should pressure, brake, or cap
claims; the main method still owns the actual judgment.

## 边界

Shared primitives are not a master workflow.

They should not make simple tasks heavier. They should not replace facts, domain research,
runtime proof, or user judgment. They should not create a new label for every small
guardrail.

If a primitive starts to need many subrules, examples, and independent outputs, pause and
decide whether it is actually a method design problem.

## 与其他方法的关系

- `using-mindthus` should expose the smallest useful set of shared primitives.
- `WAE` helps decide whether a primitive belongs in workflow, agentic judgment, or
  evidence control.
- `TVG` can deepen a primitive description after the primitive's boundary is stable.
- `Anti-Spiral` remains both a named primitive here and a fuller methodology resource
  when the full protocol is needed.

## 导航

- 返回 [README](../../README.md)
- 查看 [Using Mindthus skill](../../skills/using-mindthus/SKILL.md)
- 查看 [Anti-Spiral 方法页](anti-spiral-self-audit.md)
