# Mindthus / 此心

Mindthus 是一个个人方法论与 agent 构建项目。

`Thus` 表示“所以 / 如此 / 就该这样”，带着一种已经定下判断的意味。`此心 / Mindthus` 的意思是：一旦这个心已经看清模式，工作就应该按那个形状展开。

方法不只是外部清单。Mindthus 想做的是把判断、证据边界、行动姿态和重复实践，变成可复用的 `AGENTS.md` 与 `SKILLS`。

短句理解：

> Mindthus 把个人哲学和方法论，整理成 agent 真能用的 `AGENTS.md` 指令和独立 `SKILLS`。

Mindthus can also be installed as a skills pack:

- `mindthus:using-mindthus`
- `mindthus:sela`
- `mindthus:3l5s`
- `mindthus:edsp`
- `mindthus:wae`
- `mindthus:tvg`
- `mindthus:tplan`

当前版本：`v0.5`

v0.5 新增方法分层纪律，要求方法写作显式区分 `core`、`mainline`、
`guardrail`、`boundary`、`example` 与 `runtime support`，避免主思想被从属补漏
和细节优化冲淡。本版本同时为 `SELA` 增加轻量时机检查，并将所有 `SKILL.md`
入口统一到同一套分层结构。

## 它是什么

Mindthus 是一套把方法、边界和控制权整理成可复用技能包的项目。

它不是单纯的笔记集合，也不是把 AI 产物包装得更整齐的文档工程。

## 它能做什么

- 让 agent 先判断问题类型，再选方法镜头
- 把复杂问题拆成可执行、可验证、可回退的任务
- 把长期任务的证据、日志和停止条件分开
- 把局部修补螺旋、过早切换和错误加层挡在外面

## 它如何做到

- `AGENTS.md` 提供项目级姿态和控制边界
- `skills/*/SKILL.md` 提供独立技能入口
- `skills/*/resources/` 提供长方法资源和运行支撑
- `docs/methodologies/` 放跨技能的方法资源，例如 Anti-Spiral
- `tests/` 把关键文档和格式约束固定下来

## 使用场景

- 重大趋势判断：`SELA`
- 混乱问题拆解：`3L5S`
- 结构判断：`EDSP`
- 控制边界：`WAE`
- 长任务编排：`tplan`
- 防止局部修补螺旋：`Anti-Spiral`

更完整的中文说明见 [中文说明书](docs/guide.md)。

## Project Posture

The root agent stance is:

> 遇事不要慌，先搞清楚情况再说。

This means every agent working in this project should prefer situation clarity before conclusion, evidence before confidence, bounded judgment before procedural motion, and executable next steps before decorative structure.

## Organization

Mindthus is organized through two surfaces:

1. `AGENTS.md` defines the project-level agent posture, operating rules, and contribution boundaries.
2. `skills/<skill-name>/` contains independent skills, each with its own `SKILL.md` and optional bundled resources.

Methodology resources that should not become standalone skills live under
`docs/methodologies/`. For example, Anti-Spiral Self-Audit is a cross-cutting execution
discipline that can be quoted directly in ordinary work and absorbed by `tplan` as a
runtime gate.

Current skills:

- `skills/using-mindthus/` — portable AGENTS-style entry skill for Mindthus posture and routing.
- `skills/sela/` — top-level decision principle: System Efficiency over Local Advantage.
- `skills/3l5s/` — structures vague, complex, or system-level problems through `Three Layers + Five Steps` (`三层五步`): `Discovery / Definition / Resolution` plus `Baseline -> Target -> Gap -> Strategy -> Breakdown`.
- `skills/edsp/` — handles ambiguous qualitative judgments through Extreme Deduction + Scenario Projection.
- `skills/wae/` — separates deterministic workflow control, agentic judgment, and evidence bridging.
- `skills/tvg/` — value-driven thinking-depth enhancer for shallow AI-generated artifacts.
- `skills/tplan/` — Mission-oriented runtime for Task/SubTask/Step state, evidence/log separation, decision hooks, and script-controlled structure changes.

Skill-specific resources live under `skills/*/resources/` so each skill can be used independently. Root-level files should stay limited to project orientation and agent posture.

## Install As A Skills Pack

### Codex

See [.codex/INSTALL.md](/root/mindthus/.codex/INSTALL.md).

Codex supports bundle-style discovery through `~/.agents/skills/`, so the intended namespace is `mindthus` and installation exposes the skills as `mindthus:*`.

Codex also has a system `skill-installer` capability for installing individual skills into `~/.codex/skills`, but that path is not the right fit for this repository's pack-style namespace. Mindthus is intended to be installed as one bundle so the skills remain grouped under `mindthus:*`.

For an existing checkout, install or refresh the Codex skills pack with:

```bash
scripts/install-skills.sh codex --force
```

This creates `~/.agents/skills/mindthus -> <repo>/skills`. Restart Codex after installing.

### Claude Code

Claude Code personal skills live under `~/.claude/skills/`.

1. Clone the repository:

   ```bash
   git clone https://github.com/rv198-star/Mindthus.git ~/.claude/mindthus
   ```

2. Create the local skills links:

   ```bash
   cd ~/.claude/mindthus
   scripts/install-skills.sh claude --force
   ```

3. Restart Claude Code.

This exposes the same skill set in Claude Code as local skills. Unlike Codex bundle discovery, this path does not currently add a `mindthus:` namespace prefix by itself.

## Verify

Run the repository checks:

```bash
python3 -m unittest tests.test_packaging_docs -v
python3 -m unittest discover -s tests/tplan -v
```

For `tplan` only:

```bash
python3 -m unittest discover -s tests/tplan -v
```

The runtime scripts are plain Python and shell scripts. They do not require package
installation inside the repository; installation means exposing the `skills/` directory
to the target agent client.

## Packaging Notes

Mindthus is packaged as a skills directory, not as a Python library. The stable package
surface is:

- `AGENTS.md`
- `skills/*/SKILL.md`
- `skills/*/resources/`
- `skills/*/templates/`
- `skills/*/scripts/` when a skill needs deterministic runtime support

Use `scripts/install-skills.sh` for local symlink installation. If a future client
needs an archive artifact, package the repository by preserving the `skills/`
directory layout exactly; skill paths are part of the runtime contract.

## Skill Rule

Each skill should stay portable and self-contained:

- Put trigger logic and operating procedure in `SKILL.md`.
- Put longer methodology text in `resources/methodology.md`.
- Do not make a skill depend on project-local memory unless the dependency is explicit.
- Do not turn a method into ceremony; preserve the judgment it was meant to protect.
- Do not let scripts, schemas, or templates replace agentic judgment when truth is uncertain.

### Method Layering Discipline / 方法分层纪律

When writing or revising a method, separate the main thought from patch branches.
Every major section should be identifiable as one of these layers:

- `core`: the method's central claim; this must stay short and first.
- `mainline`: the normal path a future agent should follow.
- `guardrail`: a subordinate check that prevents a known misuse; a guardrail must not become a new judgment center.
- `boundary`: when not to use the method, when to stop, or when to route elsewhere.
- `example`: illustrative material; examples must not silently become rules.
- `runtime support`: scripts, templates, schemas, traces, and validation helpers.

Guardrails must state what mainline misuse they protect against and what they cannot
override. If a new section cannot be assigned to one of these layers, do not add it
until its role is clear.

## Working Rule

When adding or revising a method:

1. Clarify the situation first.
2. Name the bounded method or skill being changed.
3. Preserve the method's philosophical claim.
4. Keep the `core` and `mainline` visible before any `guardrail`.
5. Convert the claim into usable agent behavior.
6. Add evidence, boundaries, and stop conditions.
7. Keep the skill lean enough to load in context.

Mindthus is not a warehouse of notes. It is a forge for reusable judgment.
