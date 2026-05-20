# Mindthus / 此心

Mindthus 是一套面向 AI agent 的判断方法与技能包：它把复杂问题定义、结构判断、控制边界、长任务运行和反螺旋自检，整理成可以安装、调用、审查和测试的 `AGENTS.md` 与 `SKILLS`。

`Thus` 表示“所以 / 如此 / 就该这样”。`此心 / Mindthus` 的意思是：当一个人已经看清问题的形状，后续行动就不该再散乱地试错，而应该沿着那个判断展开。

短句理解：

> Mindthus 把一套个人哲学和方法论，做成 agent 真能用的判断镜头与运行纪律。

当前仓库版本：`v0.5.1`。`v0.5` 引入方法分层纪律，要求方法写作显式区分 `core`、`mainline`、`guardrail`、`boundary`、`example` 与 `runtime support`；`v0.5.1` 修正 EDSP skill frontmatter，保证技能包发现稳定。

安装后会暴露 `mindthus:*` 命名空间，例如 `mindthus:tplan`。

## 为什么值得试

很多 AI workflow 的失败，不是因为模型不会写、不会改、不会执行，而是因为它太早开始执行：把现象当问题，把模板当推理，把日志当证据，把局部修补当进展，把“再试一次”误认为真的在接近目标。

Mindthus 处理的正是这一层。它不追求让 agent 更快给出一个看似完整的答案，而是让 agent 先判断自己面对的是什么问题，再选择合适的方法镜头。这样做的收益很直接：

- 问题还没清楚时，先把问题定义对，而不是直接堆方案。
- 结构判断摇摆时，先建立坐标系，而不是在 A/B 之间反复横跳。
- 流程、agent 判断和证据互相抢控制权时，把边界重新划清。
- 长任务开始围着同一个局部对象反复修补时，及时停下来，回到上游。
- 文档或方案看起来完整但内容偏薄时，只在能增加真实价值的地方加深。

它的优势不是“更多流程”，而是把容易失控的判断点压成轻量、可复用、可审查的 skill。对新用户来说，Mindthus 提供的是一套可安装的判断操作系统：你可以直接用，也可以拆开读、改造、迁移到自己的 agent 项目里。

## 它是什么

Mindthus 不是笔记合集，也不是把 AI 输出包装得更整齐的模板工程。它是一组围绕真实工作失败模式设计的方法论：

- `using-mindthus` 提供默认姿态：遇事不要慌，先搞清楚情况再说。
- `SELA` 处理整体趋势与局部优势之间的战略张力。
- `3L5S` 处理问题从混乱信号到可执行任务的落地链条。
- `EDSP` 处理悬而不决、命题可能有问题的结构判断。
- `WAE` 处理 workflow、agentic judgment 与 evidence 的控制边界。
- `TVG` 处理 AI 产物形式完整但实质浅薄的问题。
- `tplan` 处理 Mission 级长任务的状态、证据、停止和继续。
- `Anti-Spiral` 作为跨方法执行纪律，阻止局部修补螺旋吞掉目标函数。

这些方法不是固定流水线。Mindthus 更强调“最小充分镜头”：能直接判断就不要开方法，一个 skill 足够就不要串联，轻量检查足够就不要展开完整仪式。

## 能做什么

Mindthus 适合放在真实 agent 工作流里，尤其是这些场景：

- 复杂任务刚开始，用户只给了模糊目标，需要先判断真实问题是什么。
- 一个方案看似合理，但长期方向、局部优势和切换时机彼此冲突。
- Agent 正在写脚本、规则、review gate 或 workflow，但不确定哪里该自动化，哪里必须保留判断。
- 长任务执行到中后段，任务列表开始漂移，日志很多，证据不清，停止条件不明确。
- 文档、计划、prompt、skill 已经成形，但读起来像“合格模板”，缺少判断、取舍、失败路径和下游可用性。

它不适合替代领域事实、运行时验证、法律/医疗/安全等高风险专家判断。Mindthus 的位置是判断框架和执行纪律：它帮助 agent 问对问题、选对控制面、保留证据约束，但不把方法本身冒充事实。

## 方法论导航

每个方法页都比 `SKILL.md` 更像说明书：`SKILL.md` 给 agent 执行入口，方法页给人讲清抽象含义、适用边界、常见误用和为什么值得用。

- [`SELA / 系统效率碾压局部优势`](docs/methodologies/sela.md)：讲清整体与局部、时机检查和长期方向。它解决的是“局部优秀真实存在，但系统级费效比正在改变主战场”时的战略误判。
- [`3L5S / 三层五步`](docs/methodologies/3l5s.md)：讲清问题如何从混乱信号走到可执行步骤。它解决的是“现象很多但问题没定义清楚”或“问题很大但不可执行”的落地失败。
- [`EDSP / Extreme Deduction + Scenario Projection`](docs/methodologies/edsp.md)：讲清结构判断如何先建坐标系再做场景投影。它解决的是 A/B 都像对、命题可能不成立、原则难落地的判断摇摆。
- [`WAE / Workflow-Agentic-Evidence`](docs/methodologies/wae.md)：讲清流程、判断和证据各自该管什么。它解决的是脚本、agent 和 review gate 互相越权，导致结构干净但真相不稳。
- [`TVG / Thinking Value-Gain`](docs/methodologies/tvg.md)：讲清如何把薄的成品加深成可用模块。它解决的是 AI 产物看似完整、表达流畅，但缺少证据、取舍、复用和下游行动价值。
- [`tplan / Mission-oriented project manager`](docs/methodologies/tplan.md)：讲清 Mission 级任务运行、状态和证据边界。它解决的是长任务中 task list 漂移、logs 和 evidence 混杂、继续/停止缺少权威入口。
- [`Anti-Spiral / 反螺旋自检`](docs/methodologies/anti-spiral-self-audit.md)：讲清如何防止局部修补变成死亡螺旋。它解决的是同一局部对象被第三次处理、负反馈变多、下一步只想继续加层时的目标函数丢失。

## 如何做到

Mindthus 的项目结构刻意保持简单：

- `AGENTS.md`：项目级姿态、skill 路由、方法分层纪律和反螺旋入口。
- `skills/*/SKILL.md`：每个 skill 的最小可加载入口，保证 agent 能在上下文里快速使用。
- `skills/*/resources/`：较长的方法资源、运行说明和哲学展开，不挤占 skill 入口。
- `skills/*/scripts/` 与 `templates/`：只在需要确定性运行支撑时存在，例如 `tplan` 和 `TVG`。
- `docs/methodologies/`：面向人的方法论说明页，帮助新用户理解每个方法为什么存在、何时使用、何时停止。
- `tests/`：把关键文档契约、skill frontmatter、方法分层和运行脚本固定下来，避免项目只靠口头约定维护。

核心纪律是：方法必须把主思想和补漏分支分开。`core` 与 `mainline` 先说明正常路径，`guardrail` 只防止误用，`boundary` 说明停止或转交条件，脚本和 schema 只能做运行支撑，不能替代 agentic judgment。

## 安装

### Codex

详细说明见 [.codex/INSTALL.md](.codex/INSTALL.md)。

在已有 checkout 中安装或刷新技能包：

```bash
scripts/install-skills.sh codex --force
```

这会创建 `~/.agents/skills/mindthus -> <repo>/skills`。重启 Codex 后，可以通过 `mindthus:*` 命名空间使用这些 skills，例如 `mindthus:tplan`。

### Claude Code

Claude Code personal skills 默认位于 `~/.claude/skills/`。

```bash
git clone https://github.com/rv198-star/Mindthus.git ~/.claude/mindthus
cd ~/.claude/mindthus
scripts/install-skills.sh claude --force
```

重启 Claude Code 后即可使用同一套本地 skills。Claude Code 的本地安装路径不会自动增加 `mindthus:` namespace prefix。

## 验证

运行文档与打包检查：

```bash
python3 -m unittest tests.test_packaging_docs -v
```

运行 `tplan` runtime 检查：

```bash
python3 -m unittest discover -s tests/tplan -v
```

运行完整测试：

```bash
python3 -m unittest discover -s tests -v
```

本仓库不是 Python library；安装的含义是把 `skills/` 暴露给目标 agent client。稳定打包面包括 `AGENTS.md`、`skills/*/SKILL.md`、`skills/*/resources/`、`skills/*/templates/` 和必要的 `skills/*/scripts/`。

## 写作与贡献规则

### Method Layering Discipline / 方法分层纪律

Mindthus 的方法写作追求可复用判断，而不是文档体量。新增或修订方法时：

1. 先澄清当前面对的真实对象、底层约束和目标函数。
2. 保留方法的哲学主张，不要让 guardrail 变成新的判断中心；`guardrail must not become a new judgment center`。
3. 让 `core` 和 `mainline` 足够短，未来 agent 只读主路径也能行动。
4. 把证据、边界、停止条件和常见误用写清楚。
5. 对脚本、schema、trace 保持克制：它们只能约束形状，不能替代判断。

Mindthus 不是方法论仓库，而是一套让 agent 在复杂工作里保持清醒判断的可执行基础设施。
