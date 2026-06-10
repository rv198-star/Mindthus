# Mindthus / 此心

Mindthus 是一套教 AI agent 在真实任务里“何时拿起哪把刀”的 skills pack。

人们常说 AI agent 缺乏人类的分析能力、决策能力和架构能力。但这可能只说对了一半：很多时候，agent 真正缺的不是“会不会思考”，而是不知道当前任务到底该用哪种思考方式。

用户说“这个系统不好用”，agent 应该先改界面，还是先定义问题？两个方案都像对，agent 应该继续折中，还是先把结构推到极端？任务已经第三次修改同一个 prompt，agent 应该继续加规则，还是停下来回到上游？AI 生成的文档、代码和方案很顺，但价值不足，agent 应该怎么把它强化到真正可用？

Mindthus 试图把这些场景里的判断，变成 agent 能安装、调用、审查和测试的 skills。当 agent 能判断什么时候该用问题定义、结构推演、趋势取舍、主线承载、控制边界、定向价值强化或长任务运行纪律时，它的输出就不只是“生成得更像”，而是更接近真正会分析和决策。

`Thus` 表示“所以 / 如此 / 就该这样”。`此心 / Mindthus` 的意思是：当一个人已经看清问题的形状，后续行动就不该再散乱地试错，而应该沿着那个判断展开。

短句理解：

> Mindthus 把一组哲学和方法论，做成 AI agent 能安装、调用、审查和测试的锋利工具。

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
- 主线看起来没错，但中间的博弈波动可能很大：AI 长期会走出来、房价长期承压、公司必须转型，却不知道当前载体能不能穿过路径。
- 你正在设计 agent workflow：哪些步骤该脚本化，哪些判断必须留给 agent，哪些结论必须有 evidence。
- 一个长任务已经积累了很多 logs，但没人说得清当前任务树是否还服务于原始 Mission。
- AI 生成的文档、代码、计划或 prompt 看似完整，但读起来浅，缺少判断、取舍、失败路径和下游可用性。

它不适合替代领域事实、运行时验证、法律/医疗/安全等高风险专家判断。Mindthus 的位置是判断框架和执行纪律：它帮助 agent 问对问题、选对控制面、保留证据约束，但不把方法本身冒充事实。

## 方法论导航

下面这些方法不是固定流水线，而是一组可按场景选择的刀。实际使用时，agent 只需要调用当前问题需要的 skill；方法页负责讲清每把刀解决什么问题、什么时候该用、什么时候不该用。

- [`SELA / 系统效率碾压局部优势`](docs/methodologies/sela.md)：旧方法仍有高手、好体验和局部优势，但新系统的成本、速度和规模化能力正在改写主战场时，用它讲清整体与局部、时机检查和长期方向。
- [`MPG / 主线-路径博弈 / Mainline-Path Game`](docs/methodologies/mpg.md)：主线已经看见，但路径会经过对抗力量、载体脆弱性、暴露预算和触发条件时，用它产出 Path-Carrying Strategy / 主线承载方案。它要求先讲人话，回放时看推演耐久性；复杂变量关系可以用 `MPG-AQM` / 非精准量化显影辅助显影，但不替代 MPG 判断。
- [`3L5S / 三层五步`](docs/methodologies/3l5s.md)：用户给了一堆现象，大家都在提方案，但没人能一句话说清问题是什么时，用它讲清问题如何从混乱信号走到可执行步骤。
- [`EDSP / Extreme Deduction + Scenario Projection`](docs/methodologies/edsp.md)：A/B 都像对、原则一落地就摇摆、命题本身可能有坑时，用它先建结构坐标，再做场景投影。
- [`WAE / Workflow-Agentic-Evidence`](docs/methodologies/wae.md)：脚本、agent、review gate 都在“管事”，但没人知道流程、判断和证据各自该管什么时，用它重新划清控制边界。
- [`TVG / Thinking Value-Gain`](docs/methodologies/tvg.md)：AI 生成的文档、代码、方案或提示词看起来完整却价值不足时，用它把文本更接近某个“好”的标准；这个标准可以来自默认实用价值，也可以由 profile 定义。
- [`tplan / OKR-Runtime`](docs/methodologies/tplan.md)：长任务跑着跑着任务列表漂了、logs 和 evidence 混在一起、继续或停止没人负责时，用它管理目标、验收证据、任务状态和停止条件。它不是季度 OKR 表，而是长任务执行中的动态工作流：目标稳定，任务树跟着 checkpoint、evidence、blocker 和用户反馈短周期调整。
- [`Anti-Spiral / 反螺旋自检`](docs/methodologies/anti-spiral-self-audit.md)：同一个文件、prompt、参数或任务节点已经第三次被修，下一步还想继续加层时，用它防止局部修补变成死亡螺旋。

## 从哪里开始

第一次使用时，可以按这个顺序看：

- 想快速判断某个方法适不适合你，先读 `docs/methodologies/`。
- 想让 Codex 或 Claude Code 实际调用，安装后使用 `skills/*/SKILL.md` 里的 skill。
- 想了解 agent 应该如何自动选择方法，看 `AGENTS.md`。
- 想研究配套脚本，再看 `skills/*/scripts/` 与 `templates/`。

本仓库不是 Python library；安装的含义是把 `skills/` 暴露给目标 agent client。

## 安装

### Codex

详细说明见 [.codex/INSTALL.md](.codex/INSTALL.md)。

在已有 checkout 中安装或刷新技能包：

```bash
scripts/install-skills.sh codex --force
```

这会创建 `${CODEX_HOME:-~/.codex}/skills/mindthus -> <repo>/skills`。重启 Codex 后，可以通过 `mindthus:*` 命名空间使用这些 skills，例如 `mindthus:tplan`。

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

## 可选：记录使用效果

如果你在真实任务里试用 Mindthus，并愿意反馈效果，可以用下面的脚本记录一条脱敏使用日志：

```bash
python3 scripts/log-fidelity-usage.py --help
```

默认记录文件是 `data/fidelity-usage-log.jsonl`。它适合记录场景、使用的方法、模型、约束版有没有帮上忙和简单评分，方便之后比较哪些方法真的有效。

## 版本与许可

当前仓库版本：`v1.1.0`。完整变化请看 [CHANGELOG.md](CHANGELOG.md) 和 [GitHub Releases](https://github.com/rv198-star/Mindthus/releases)。

Mindthus uses AGPLv3 + commercial dual licensing.

Open-source use is available under AGPLv3. You may use, modify, distribute, and deploy
Mindthus under the terms of AGPLv3. In short: closed-source commercial use requires a separate commercial license
from the author, including proprietary products, private SaaS, commercial platform
integration, or commercial use without releasing the corresponding source code required
by AGPLv3.

中文口径：开源使用、开源改造和开源部署按 AGPLv3；闭源商业产品、私有商业平台、商业 SaaS 或不公开对应源代码的商业集成，需要单独取得商业授权。

Mindthus 不是方法论仓库，而是一套让 agent 在复杂工作里保持清醒判断的可执行基础设施。
