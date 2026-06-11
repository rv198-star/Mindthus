# Mindthus / 此心

AI agent 最大的问题，常常不是不会做事，而是太早开始做事。

用户说“不好用”，它立刻改功能；两个方案都能讲通，它写一堆折中；长任务跑到一半，它被某个文件、prompt 或测试带偏；AI 生成的文档、代码和方案很顺，但没有判断、证据和下游价值。

Mindthus 是一套教 AI agent 在真实任务里“何时拿起哪把刀”的 skills pack。它让 agent 先判断问题形状，再决定该定义问题、推演结构、判断趋势、承载主线、划清控制边界、增厚产物，还是管住长任务。

> Mindthus 让 agent 先选对刀，再开始用力。

它是一套可安装的判断工具箱，不是把流程变多。它把容易靠临场感觉处理的判断点，压成可调用、可审查、可测试的 skills。你可以直接用，也可以拆开读、改造、迁移到自己的 agent 项目里。

`Thus` 表示“所以 / 如此 / 就该这样”。`此心 / Mindthus` 的意思是：看清问题形状之后，后续行动就不该散乱试错，而应该沿着那个判断展开。

## 为什么值得试

很多 AI workflow 的失败，不是因为模型写不出东西，而是它没有先问一句：我现在到底在处理哪类问题？

你可能见过这些情况：

- 模糊需求来了，agent 先动手，最后修错对象。
- A/B 都能讲通，agent 只会折中，不敢判断。
- CI、脚本、review gate 都有了，却没人说得清哪些结论真的有证据。
- 长任务跑到中后段，agent 围着同一个文件、prompt 或参数反复修补，还以为这是进展。
- AI 生成的文档、代码或方案看起来很完整，但只有表层结构，缺少深度、取舍和失败路径。

Mindthus 处理的正是这一层。它不追求让 agent 更快给出一个看似完整的答案，而是让 agent 先判断自己面对的是什么问题，再选择合适的方法镜头。

它的优势不是“更多流程”，而是把容易失控的判断点压成轻量、可复用、可审查的 skill。

## 能做什么

Mindthus 适合放进真实 agent 工作流，尤其是这些场景：

- 用户给了一个模糊目标，比如“把这个项目讲清楚”“把这个任务做完”，但真正的问题还没被定义。
- 团队在旧方案和新方案之间摇摆：旧方案局部很好，新方案系统效率更高，不知道该试点、等待还是切换。
- 主线看起来没错，但中间的博弈波动可能很大：AI 长期会走出来、房价长期承压、公司必须转型，却不知道当前载体能不能穿过路径。
- 你正在设计 agent workflow：哪些步骤该脚本化，哪些判断必须留给 agent，哪些结论必须有 evidence。
- 一个长任务已经积累了很多 logs，但没人说得清当前任务树是否还服务于原始 Mission。
- AI 生成的文档、代码、计划或 prompt 看似完整，但读起来浅，缺少判断、取舍、失败路径和下游可用性。

它不适合替代领域事实、运行时验证、法律/医疗/安全等高风险专家判断。Mindthus 的位置是判断框架和执行纪律：它帮助 agent 问对问题、选对控制面、保留证据约束，但不把方法本身冒充事实。

## 方法论导航

下面这些方法不是固定流水线，而是一组可按场景选择的刀。实际使用时，agent 只需要调用当前问题需要的 skill；方法页负责讲清每把刀解决什么问题、什么时候该用、什么时候不该用。

- [`SELA / 系统效率碾压局部优势`](docs/methodologies/sela.md)：判断一个东西虽然局部很强，但会不会被更高效的系统长期挤到边缘。比如手工记账再熟练，也很难长期打过自动化财务系统；手工的价值还在，但主战场可能已经变了。SELA 用来讲清整体与局部、时机检查和长期方向。
- [`MPG / 主线-路径博弈 / Mainline-Path Game`](docs/methodologies/mpg.md)：解决“看对长期方向，不等于能活着走到终点”。比如你相信 AI 是长期主线，但资金、职位或公司现金流撑不过中途波动，这个判断再对也没用。MPG 产出 Path-Carrying Strategy / 主线承载方案，关心的是怎么扛过路径，而不是只喊方向正确；输出要先讲人话，回放看推演耐久性，复杂变量可用 `MPG-AQM` / 非精准量化显影辅助显影。
- [`3L5S / 三层五步`](docs/methodologies/3l5s.md)：把乱问题变成真问题，再把真问题拆成能做的事。比如“项目不顺”太虚，它会先逼你分清是需求不清、资源不够、目标错了，还是执行断了；然后讲清问题如何从混乱信号走到可执行步骤。
- [`EDSP / Extreme Deduction + Scenario Projection`](docs/methodologies/edsp.md)：用在“两边好像都对”的时候。它会把关键变量推到极端，看这个问题到底是不是伪二选一。比如“要不要全面自动化”，推到极端后可能发现真正问题不是自动化与否，而是哪部分确定、哪部分还需要人判断。
- [`WAE / Workflow-Agentic-Evidence`](docs/methodologies/wae.md)：判断一件事应该由流程管、由 agent 判断，还是由证据说话。比如脚本、agent、review gate 都在“管事”，但表格打勾不能证明方案靠谱；表格能管顺序，不能替你判断真假。
- [`TVG / Thinking Value-Gain`](docs/methodologies/tvg.md)：把一段文字，迭代推向某个“好”的标准。它不只是润色，也不只是扩写；它会先明确这次“好”是什么意思，再围绕这个标准增强判断、厚度、结构、证据边界或输出形态。比如给它一段剧本文字和“分镜提示词要可画、可审查”的标准，TVG 会把原文一步步推成更有镜头、构图、动作和转场判断的分镜提示词。
- [`TPlan / OKR-Runtime`](docs/methodologies/tplan.md)：把一个长期目标变成会拆解、会对齐、会调整的任务运行系统。它不是季度 OKR 表，也不只是记 TODO，而是自动把 Mission 拆成任务、子任务和步骤，并持续检查每个子任务是否还服务总目标；某个地方发现的阻塞和风险，也会共享给整场任务，影响后续判断。比如发版时，测试失败、安装路径异常、包里混入日志都不是孤立小问题，TPlan 会判断它们是否影响发布目标、当前子任务还值不值得继续、该拆新任务、改路、暂停还是收束。它是长任务执行中的动态工作流。
- [`Anti-Spiral / 反螺旋自检`](docs/methodologies/anti-spiral-self-audit.md)：防止 agent 陷入“再试一次”的小修小补。比如同一个文件、prompt、参数或任务节点已经第三次被修，下一步还想继续加层，它会提醒你先回头看目标、素材或判断标准是不是错了，避免局部修补变成死亡螺旋。

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

## 版本与开发状态

当前仓库版本：`v0.6.3`。

`v0.6.3` 继承 `v0.6` 的单模型 contract、pressure 和 live-behavior validation；当前不声明跨模型鲁棒性。

这一版主要让 `tplan` 更适合日常长任务：小任务少记流水账，状态更新先说人话，多条只读调查线索可以安全并行；遇到删除关键任务、目标变更、阻塞或无法安全继续时，仍然保留 Mission、evidence、decision hook 和 graceful stop 这些底线能力。

对使用者来说，最直接的变化是：

- 低风险任务不会一上来就像完整项目管理流程。
- 进度汇报默认讲“当前目标、进展、已确认、下一步”，不再把 `T1`、`E2` 这类内部编号放在前面。
- `tplan` 可以用只读 SubAgent 加速搜索和检查，但最终判断、写入和对用户结论仍由主 agent 负责。

版本脉络：`v0.6` 补齐判断内核入口层，`v0.6.1` 增加平台化 release pack 并修复 Claude Code marketplace 发布包布局，`v0.6.2` 把 TVG 升级为 grounded insight value-gain，`v0.6.3` 聚焦 tplan 运行时优化和只读 SubAgent 加速。

安装后会暴露 `mindthus:*` 命名空间，例如 `mindthus:tplan`。

当前开发分支同步：`MPG / 主线-路径博弈` 已作为独立方法进入 Mindthus。它不是只判断“主线对不对”，而是给出 `Path-Carrying Strategy / 主线承载方案`：行动者如何在主线兑现前承受波动、保留可选性、识别触发器，并避免死在正确方向的半途。

MPG 的输出纪律是先讲人话，再给结构字段；回放案例看推演耐久性，而不是用事后结果粗暴打分。复杂变量关系可以用 `MPG-AQM` / 非精准量化显影作为显影层，但数字只是假设，关系才是重点；MPG 负责判断和承载方案，AQM 只负责把主线强度、路径阻力、载体脆弱度、信息缺口和触发器强度显出来。
