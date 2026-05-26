# Mindthus / 此心

Mindthus 是一套教 AI agent 在真实任务里“何时拿起哪把刀”的 skills pack。

人们常说 AI agent 缺乏人类的分析能力、决策能力和架构能力。但这可能只说对了一半：很多时候，agent 真正缺的不是“会不会思考”，而是不知道当前任务到底该用哪种思考方式。

用户说“这个系统不好用”，agent 应该先改界面，还是先定义问题？两个方案都像对，agent 应该继续折中，还是先把结构推到极端？任务已经第三次修改同一个 prompt，agent 应该继续加规则，还是停下来回到上游？AI 生成的文档、代码和方案很顺，但很浅，agent 应该怎么把它做深？

Mindthus 试图把这些场景里的判断，变成 agent 能安装、调用、审查和测试的 skills。当 agent 能判断什么时候该用问题定义、结构推演、趋势取舍、控制边界、价值加深或长任务运行纪律时，它的输出就不只是“生成得更像”，而是更接近真正会分析和决策。

`Thus` 表示“所以 / 如此 / 就该这样”。`此心 / Mindthus` 的意思是：当一个人已经看清问题的形状，后续行动就不该再散乱地试错，而应该沿着那个判断展开。

短句理解：

> Mindthus 把一组哲学和方法论，做成 AI agent 能安装、调用、审查和测试的锋利工具。

当前仓库版本：`v0.5.2`。这一版在 `v0.5.1` 的方法分层纪律基础上，继续补齐了 SELA / EDSP 的单 Agent 多角色压力、压线 A/B 证据，以及 Mindthus 自己的“不要堆抽象术语墙”表达纪律。

安装后会暴露 `mindthus:*` 命名空间，例如 `mindthus:tplan`。

## 为什么值得试

很多 AI workflow 的失败，不是因为模型不会写、不会改、不会执行，而是因为它太早开始执行。

你可能见过这些情况：

- 用户只说“不好用”，agent 立刻开始改功能，最后修错了对象。
- A 方案和 B 方案都能讲通，agent 写了一堆折中建议，但没有真正判断。
- CI、脚本、review gate 都有了，却没人知道哪些结论真的有证据。
- 长任务跑到中后段，agent 围着同一个文件、prompt 或参数反复修补，还以为这是进展。
- AI 生成的文档、代码或方案看起来很完整，但只有表层结构，缺少深度、丰度、取舍和失败路径。

Mindthus 处理的正是这一层。它不追求让 agent 更快给出一个看似完整的答案，而是让 agent 先判断自己面对的是什么问题，再选择合适的方法镜头。

它的优势不是“更多流程”，而是把容易失控的判断点压成轻量、可复用、可审查的 skill。对新用户来说，Mindthus 提供的是一套可安装的判断工具箱：你可以直接用，也可以拆开读、改造、迁移到自己的 agent 项目里。

## 能做什么

Mindthus 适合放在真实 agent 工作流里，尤其是这些场景：

- 用户给了一个模糊目标，比如“把这个项目讲清楚”“把这个任务做完”，但真正的问题还没被定义。
- 团队在旧方案和新方案之间摇摆：旧方案局部很好，新方案系统效率更高，不知道该试点、等待还是切换。
- 你正在设计 agent workflow：哪些步骤该脚本化，哪些判断必须留给 agent，哪些结论必须有 evidence。
- 一个长任务已经积累了很多 logs，但没人说得清当前任务树是否还服务于原始 Mission。
- AI 生成的文档、代码、计划或 prompt 看似完整，但读起来浅，缺少判断、取舍、失败路径和下游可用性。

它不适合替代领域事实、运行时验证、法律/医疗/安全等高风险专家判断。Mindthus 的位置是判断框架和执行纪律：它帮助 agent 问对问题、选对控制面、保留证据约束，但不把方法本身冒充事实。

## 方法论导航

下面这些方法不是固定流水线，而是一组可按场景选择的刀。实际使用时，agent 只需要调用当前问题需要的 skill；方法页负责讲清每把刀解决什么问题、什么时候该用、什么时候不该用。

- [`SELA / 系统效率碾压局部优势`](docs/methodologies/sela.md)：旧方法仍有高手、好体验和局部优势，但新系统的成本、速度和规模化能力正在改写主战场时，用它讲清整体与局部、时机检查和长期方向。
- [`3L5S / 三层五步`](docs/methodologies/3l5s.md)：用户给了一堆现象，大家都在提方案，但没人能一句话说清问题是什么时，用它讲清问题如何从混乱信号走到可执行步骤。
- [`EDSP / Extreme Deduction + Scenario Projection`](docs/methodologies/edsp.md)：A/B 都像对、原则一落地就摇摆、命题本身可能有坑时，用它先建结构坐标，再做场景投影。
- [`WAE / Workflow-Agentic-Evidence`](docs/methodologies/wae.md)：脚本、agent、review gate 都在“管事”，但没人知道流程、判断和证据各自该管什么时，用它重新划清控制边界。
- [`TVG / Thinking Value-Gain`](docs/methodologies/tvg.md)：AI 生成的文档、代码或方案看起来完整，却停在表层、缺少深度和丰度时，用它把薄产物加深成有判断、有取舍、有下游价值的可用模块。
- [`tplan / Mission-oriented project manager`](docs/methodologies/tplan.md)：长任务跑着跑着任务列表漂了、logs 和 evidence 混在一起、继续或停止没人负责时，用它管理 Mission 级任务运行、状态和证据边界。
- [`Anti-Spiral / 反螺旋自检`](docs/methodologies/anti-spiral-self-audit.md)：同一个文件、prompt、参数或任务节点已经第三次被修，下一步还想继续加层时，用它防止局部修补变成死亡螺旋。

## 项目组成

Mindthus 的项目结构保持简单，方便直接安装，也方便拆开阅读：

- `skills/*/SKILL.md`：可安装、可调用的 skill 入口。
- `docs/methodologies/`：面向人的方法说明，解释每个方法解决什么问题、何时使用、何时停止。
- `skills/*/resources/`：更长的方法资源、运行说明和配套材料。
- `skills/*/scripts/` 与 `templates/`：少量确定性运行支撑，例如 `tplan` 和 `TVG`。
- `AGENTS.md`：给使用 Mindthus 的 agent 提供默认姿态和路由规则。
- `tests/`：固定关键文档契约、skill frontmatter 和运行脚本，避免技能包在迭代中悄悄失效。

想快速了解一个方法，先读 `docs/methodologies/`。要让 agent 实际使用，安装后调用对应 skill。

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

## 维护者说明

### Method Layering Discipline / 方法分层纪律

这部分主要给贡献者看。修订方法时，Mindthus 使用 Method Layering Discipline：把 `core`、`mainline`、`guardrail`、`boundary`、`example` 与 `runtime support` 分开，避免主思想被补漏分支冲淡。`guardrail must not become a new judgment center`。

Mindthus 不是方法论仓库，而是一套让 agent 在复杂工作里保持清醒判断的可执行基础设施。
