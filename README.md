# Mindthus / 此心

让 AI agent 先看清问题，再开始用力。

AI 最让人累的错误，很多时候不是“不会做”，而是“做得很顺，但一开始就顺着错的框架走了”。用户给了一个听起来很专业、带有倾向性的输入，它就帮忙补论据；某个实现细节确实是真的，它就把这个细节当成了本质；测试绿了，它就默认事情已经可以交付。

这些回答不一定全错。麻烦正在这里：**局部是真的，但整体被带偏了。**

**Mindthus 是一套给 AI agent 用的判断与纠偏 skills pack。** 它不急着套方法，而是先让 agent 问清楚：这个问题是不是已经被提问方式绑到了错误层级？现在缺的是事实、结构判断、证据、控制边界，还是执行纪律？

**Truth Orientation / 真相优先**：user input is signal, constraint, or hypothesis; not evidence by itself. Mindthus 会尊重用户价值、偏好、审美和风险姿态，但不会把这些约束当成事实证据。它的目标不是让 agent 更会迎合，而是让它在尊重用户目标的同时，仍然追求事实、证据和更高层级的正确判断。

> Mindthus 不是让 agent 多跑几步流程，而是让它少在错误方向上越跑越远。

![Mindthus 项目总览：TPlan、判断镜头、TVG 与认知原语](docs/assets/mindthus-overview.png)

项目地址：<https://github.com/rv198-star/Mindthus>

它不是一个“多跑几步流程”的方法论仓库，而是一套可安装、可调用、可测试的 agent 判断基础设施。你可以安装到 Codex、Claude Code 或 OpenCode，也可以拆开读、改造、迁移到自己的 agent 项目里。

`Thus` 表示“所以 / 如此 / 就该这样”。`此心 / Mindthus` 的意思是：先看清当前判断真正站在哪个层级，后续行动才不该散乱试错，而应该沿着那个判断展开。

## 为什么值得试

如果你已经把 AI agent 用到真实工作里，下面这些时刻大概率见过：

- 你只是想听一个独立判断，agent 却顺着你给的结论一路补理由。
- 某句话在实现层没错，agent 却把它当成了定义、本质或完整解释。
- 两个选项都能讲通，agent 不敢重构问题，只给一个“各有道理”的软答案。
- 测试、脚本、review gate 都有，但关键结论到底有没有证据，没人说清。
- 长任务跑到后半段，agent 一直在改同一个文件、prompt 或参数，看起来很忙，其实已经局部打转。
- AI 产出的文档、代码或方案很完整、很顺，但你读完仍然不知道它的判断、取舍、风险和下一步在哪里。

Mindthus 处理的就是这类问题：**防止局部正确冒充整体，防止顺滑表达冒充判断，防止流程完整冒充证据。**

Five [before/after explanatory examples](docs/cases/before-after/) show the observable judgment delta in compact form. They are not quantitative proof; the public benchmark is the evidence surface for measurement.

它让 agent 在关键节点先停一下：现在该直接做，还是先补事实？该接受用户的说法，还是先重构问题？该继续修，还是该承认这条路径已经不值了？

## Quick Learning：Mindthus 怎么帮 agent 变清醒

Mindthus 的工作方式很简单：**先纠偏，再路由；先判断控制面，再执行。**

1. **看清输入**：用户的话是问题、约束、偏好，还是已经打包好的结论？
2. **看清层级**：现在讨论的是实现方式、定义、本质、证据、价值，还是行动方案？
3. **看清缺口**：缺的是事实、结构判断、长期方向、路径承载、控制边界，还是验收证据？
4. **选择最小方法**：能直接做就直接做；缺事实先取证；framing 歪了先纠偏；长任务漂移就回到 Mission。

Mindthus 不会要求 agent 每次都跑完整流程。它更像一组判断刹车和镜头：该快的时候快，该停的时候停，该反问问题层级的时候，不继续陪着错误叙事往下走。

在 `using-mindthus` 里，这个入口动作叫 `输入定框审计`。它只在出现 `framing-risk` 时触发：不是机械挑关键词，而是识别“局部正确正在接管整体判断”。

## 方法论导航

下面这些方法不是固定流水线，而是一组按场景选择的判断镜头：

- [`using-mindthus / 路由入口`](skills/using-mindthus/SKILL.md)：先判断要不要介入。低风险任务直接做；输入带偏时先纠偏；缺事实时先取证。
- [`3L5S / 三层五步`](docs/methodologies/3l5s.md)：问题还乱时，把“感觉不对”压成能复述、能验证、能执行的真问题。
- [`EDSP / Extreme Deduction + Scenario Projection`](docs/methodologies/edsp.md)：A/B 都像对时，先检查命题、边界和评价轴，避免温吞折中。
- [`SELA / 系统效率碾压局部优势`](docs/methodologies/sela.md)：旧方式局部很好时，判断它会不会被更高效的系统长期压过。
- [`MPG / 主线-路径博弈 / Mainline-Path Game`](docs/methodologies/mpg.md)：长期方向看对了，还要判断当前载体能不能穿过波动、成本和时机。
- [`WAE / Workflow-Agentic-Evidence`](docs/methodologies/wae.md)：脚本、agent、review gate 都在管事时，分清流程、判断和证据各该控制哪一段。
- [`TVG / Thinking Value-Gain`](docs/methodologies/tvg.md)：产物已经成形但价值薄时，补判断、取舍、证据边界、失败路径和下游可用性。
- [`TPlan / OKR-Runtime`](docs/methodologies/tplan.md)：长任务需要持续对齐目标、证据、任务状态和验收责任时，用它保持 Mission 不漂移。
- [`Anti-Spiral / 反螺旋自检`](docs/methodologies/anti-spiral-self-audit.md)：同一个局部反复修时，先问是不是目标、素材或路径错了，而不是继续加层。

## 从哪里开始

如果你只是想试一下，建议从 `using-mindthus` 开始。它会告诉 agent：什么时候直接做，什么时候先取证，什么时候进入某个 Mindthus 方法。

第一次阅读仓库，可以按这个顺序看：

- 想直接安装使用，先看下面的 `安装`。
- 想理解为什么它能防止局部正确带偏，读 `docs/methodologies/shared-primitives.md`。
- 想快速判断某个方法适不适合你，读 `docs/methodologies/`。
- 想让 Codex 或 Claude Code 实际调用，安装后使用 `skills/*/SKILL.md`。
- 想了解 agent 应该如何自动选择方法，看 `AGENTS.md`。

本仓库不是 Python library；安装的含义是把 `skills/` 暴露给目标 agent client。

## 安装

### 选择下载包

优先安装插件包；插件不可用或需要 portable skills 时，再安装 skills 包。

- Codex App / Codex CLI / Claude Code 支持插件：下载 `mindthus-plugins-1.4.3.tar.gz`。
- 不使用插件、需要 OpenCode、或只想复制 skills 目录：下载 `mindthus-skills-1.4.3.tar.gz`。

不要在同一个 client profile 里同时安装 plugin mode 和 skills-pack mode，除非你正在测试重复 discovery。

### 下载

插件包，供 Codex App / Codex CLI / Claude Code plugin mode 使用：

```bash
curl -L \
  -o /tmp/mindthus-plugins-1.4.3.tar.gz \
  "https://github.com/rv198-star/Mindthus/releases/download/v1.4.3/mindthus-plugins-1.4.3.tar.gz"
rm -rf /tmp/mindthus-plugins
mkdir -p /tmp/mindthus-plugins
tar -xzf /tmp/mindthus-plugins-1.4.3.tar.gz -C /tmp/mindthus-plugins --strip-components=1
```

Skills 包，供 Codex skills-pack / Claude Code personal skills / OpenCode 使用：

```bash
curl -L \
  -o /tmp/mindthus-skills-1.4.3.tar.gz \
  "https://github.com/rv198-star/Mindthus/releases/download/v1.4.3/mindthus-skills-1.4.3.tar.gz"
rm -rf /tmp/mindthus-skills
mkdir -p /tmp/mindthus-skills
tar -xzf /tmp/mindthus-skills-1.4.3.tar.gz -C /tmp/mindthus-skills --strip-components=1
```

### Codex Plugin Mode（推荐）

```bash
codex plugin marketplace add /tmp/mindthus-plugins/codex-plugin
codex plugin list --marketplace mindthus --available
codex plugin add mindthus@mindthus
codex plugin list
```

重启 Codex App 后使用。可直接提到 `mindthus:tplan`、`using-mindthus` 等 skill 名称。

卸载：

```bash
codex plugin remove mindthus@mindthus
codex plugin marketplace remove mindthus
```

### Claude Code Plugin Mode（推荐）

```bash
claude plugin marketplace add /tmp/mindthus-plugins/claude-code
claude plugin install mindthus@mindthus
claude plugin list
```

重启 Claude Code 后使用。调用 `/mindthus:using-mindthus`、`/mindthus:tplan` 等插件命名空间 skills。

卸载：

```bash
claude plugin uninstall mindthus
claude plugin marketplace remove mindthus
```

### Codex Skills-Pack Mode

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/mindthus"
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R /tmp/mindthus-skills/codex/skills/mindthus "${CODEX_HOME:-$HOME/.codex}/skills/mindthus"
```

重启 Codex 后使用 `mindthus:*` skills，例如 `mindthus:tplan`。

卸载：

```bash
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/mindthus"
```

### Claude Code Personal Skills Mode

```bash
mkdir -p ~/.claude/skills
rm -rf "$HOME/.claude/skills/_runtime"
cp -R /tmp/mindthus-skills/claude-code/skills/_runtime "$HOME/.claude/skills/_runtime"
for skill in /tmp/mindthus-skills/claude-code/skills/*; do
  [ -f "$skill/SKILL.md" ] || continue
  rm -rf "$HOME/.claude/skills/$(basename "$skill")"
  cp -R "$skill" "$HOME/.claude/skills/"
done
```

`_runtime` 是给 validator 和共享脚本使用的运行时支撑目录，不是可调用 skill。重启 Claude Code 后使用 `/<skill>`，例如 `/tplan`；personal skills mode 不会增加 `mindthus:` plugin namespace。

卸载：

```bash
rm -rf ~/.claude/skills/{3l5s,edsp,mpg,sela,tplan,tvg,using-mindthus,wae}
rm -rf ~/.claude/skills/_runtime
```

### OpenCode

```bash
cp -R /tmp/mindthus-skills/opencode/.opencode /path/to/your/opencode-project/
```

在该 OpenCode project 中使用 `.opencode/skills/mindthus/<skill>`。

## 验证

查看公开判断力基准状态：

- [Mindthus Judgment Benchmark Latest](docs/benchmarks/latest.md)
- [Before/after explanatory examples](docs/cases/before-after/) show what the benchmark is trying to measure; they are not quantitative proof.

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

当前仓库版本：`v1.4.3`。完整变化请看 [CHANGELOG.md](CHANGELOG.md) 和 [GitHub Releases](https://github.com/rv198-star/Mindthus/releases)。

Mindthus uses AGPLv3 + commercial dual licensing.

Open-source use is available under AGPLv3. You may use, modify, distribute, and deploy
Mindthus under the terms of AGPLv3. In short: closed-source commercial use requires a separate commercial license
from the author, including proprietary products, private SaaS, commercial platform
integration, or commercial use without releasing the corresponding source code required
by AGPLv3.

The release-pack Codex plugin manifest uses SPDX `AGPL-3.0-only` for the open-source
lane. The separate commercial path is described in
[COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md) rather than encoded in the SPDX field.

中文口径：开源使用、开源改造和开源部署按 AGPLv3；闭源商业产品、私有商业平台、商业 SaaS 或不公开对应源代码的商业集成，需要单独取得商业授权。

Mindthus 不是方法论仓库，而是一套让 agent 在复杂工作里保持清醒判断的可执行基础设施。
