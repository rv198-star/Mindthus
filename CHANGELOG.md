# Changelog

## Unreleased

暂无。

## v0.6.1

发布日期：2026-05-27

说明：这是 `v0.6` 判断内核版本后的 patch release，重点不是修改 Mindthus 的核心
判断能力，而是把发布层和内部设计模式补齐，方便后续以“仓库私有、skills 免费开放”
的方式分发。

### 新增

- 新增内部 skill 设计模式文档：把 Mindthus 归纳为判断内核型、认知控制型和运行治理型
  skill，作为维护者设计和审查结构时的内部参考，不暴露给浅层用户。
- 新增 release pack builder：`scripts/build-release-pack.py` 可以生成面向 Claude Code、
  Codex 和 OpenCode 的平台化发布包。
- 新增 Claude Code marketplace 发布布局：生成 `claude-code/.claude-plugin/marketplace.json`
  与 `claude-code/claude-plugin/.claude-plugin/plugin.json`，并把 skills 放入
  `claude-code/claude-plugin/skills/`。
- 新增 Codex / OpenCode 发布布局：生成 Codex namespaced skills pack、project
  `AGENTS.md`，以及 OpenCode `.opencode/skills/mindthus/` 结构。
- 发布包同步包含 `docs/methodologies/`，避免 `AGENTS.md` 和 skill 正文中引用
  `docs/methodologies/shared-primitives.md` 等方法页时出现断链。
- 发布包只抽取公开 skill、平台入口和 `docs/methodologies/`，不把
  `docs/internal/`、`docs/superpowers/` 等内部设计和执行计划目录带入公开包。
- Codex / OpenCode 发布包会按平台重写 markdown 内的 skill 路径，避免
  `AGENTS.md`、方法页导航和命令示例仍指向源码仓库布局。

### 修复

- 修复 Claude Code marketplace `source` 不能引用 `..` 的发布包结构问题。现在生成的
  marketplace 固定使用 `source: "./claude-plugin"`。
- 增加测试锁定 Claude marketplace root layout，避免后续发布脚本再次生成 sibling
  plugin 引用。
- 发布包构建脚本增加输出目录保护，拒绝把仓库根目录、源码目录或过宽路径作为
  `--force` 输出目标。

### 验收

- 三平台 smoke 已实际验证过 skill / resource / agent 或 `AGENTS.md` 关键路径：
  OpenCode、Claude Code、Codex 均能在真实模型调用中返回预期 marker。
- Claude Code 同时补测了 direct Anthropic-compatible URL + API key 路径。
- 完整 Mindthus 包的 `claude plugin validate` 在当前环境未能及时完成，因此本版本只
  声明发布包结构和前述 smoke 路径通过，不声明完整包 validator 已通过。

### 校验

- `python3 -m unittest tests.test_packaging_docs -v`
- `python3 -m unittest discover -s tests -v`

## v0.6

发布日期：2026-05-26

说明：这是 Mindthus 判断内核入口层版本。`v0.5.x` 主要是在单个方法内部增强
压力检查、表达纪律和可测试性；`v0.6` 开始把跨方法复用的判断碎片抽成
认知原语，并把 Mindthus 从“选哪个 skill”推进到“先判断是否该介入、是否该补信息、
当前判断对象是什么，再决定怎么行动”。

这里的认知原语，指那些还没有完整到能成为方法论或哲学框架、但会决定判断质量的
微型控制点。之所以叫“原语”，是因为它们比 `SELA`、`EDSP`、`WAE`、`TVG` 或
`tplan` 更小，通常只是一类判断动作；之所以叫“认知”，是因为它们约束的是 agent
如何理解、判断、取舍和表达，而不是代码实现细节。比如：用多少方法才够、结论能不能
超过证据、单一视角是否需要被挑战、局部修补循环是否该刹车、抽象术语是否需要先翻译成
直接后果。

这也是一次能力跃迁版本：如果把 Mindthus 定位为 AI 认知体系的底层分析/决策底盘，
`v0.5.x` 更像一组可解释、可调用的方法，底盘能力大约在 `60-70` 分；`v0.6` 通过
认知原语、介入边界、判断对象路由、上下文注入口、约束识别、方法仲裁、施压面收束和
执行影响要求，把它推进到单模型验收下的 `90+` 可用水平。这个结论只对应当前
contract、pressure 和 live-behavior validation，不声明跨模型鲁棒性。

### v0.6 和 v0.5.x 的区别

- `v0.5.x` 强化的是方法内部质量：例如 SELA / EDSP 的多角色压力、表达纪律和
  方法分层。
- `v0.6` 强化的是方法入口判断：简单任务不介入，缺事实时先补信息，复杂任务先识别
  判断对象，再决定是否进入 `SELA`、`3L5S`、`EDSP`、`WAE`、`TVG` 或 `tplan`。
- `v0.6` 要求判断必须改变下游执行；如果没有改变策略、风险处理、证据要求、下一步行动、
  停止条件、方法选择或交接信息，就不算有效的 Mindthus 判断。

### 新增

- 新增认知原语：把最小充分镜头、证据与结论上限、视角与激励施压、反螺旋刹车、
  不堆抽象术语墙等跨方法复用的小判断规则集中成索引，通过横切方式被各方法引用，
  不再重复塞进每个 skill 正文，也不升级成新的总方法。
- 新增 Mindthus 介入边界：简单、低风险、事实足够的任务直接执行；缺事实、文件、
  数据、运行证明或用户澄清时先补信息；只有 hard judgment point 才进入 Mindthus。
- 新增判断对象路由：先识别问题定义失败、结构歧义、长期系统效率 vs 局部优势、
  控制边界错配、薄产物、Mission runtime 状态或局部修补螺旋，再选择 skill。
- 新增上下文注入口：上游平台可以注入长期目标、用户偏好、风险姿态、角色立场等
  判断约束；Mindthus 不实现 memory、retrieval、ranking 或 profile store。
- 新增判断约束识别：事实 claim 受证据约束；价值、偏好、利益、情绪、风险姿态和
  权限边界可以约束优先级、行动强度和责任归属，但不能伪装成事实。
- 新增方法仲裁动作：`dominate`、`defer`、`degrade`、`block`、`stop`，避免多个
  Mindthus 方法默认堆叠。
- 新增执行影响要求：Mindthus 判断必须改变策略、风险处理、证据要求、下一步行动、
  停止条件、方法选择或交接信息。
- 新增施压面收束：博弈和激励问题保留为视角与激励施压，不新增独立博弈论
  skill。

### 调整

- `using-mindthus` 从“选择 skill 的说明”升级为判断入口层，但仍保持最小充分镜头，
  不把自己变成新的总方法。
- `shared-primitives.md` 明确 pressure surface 只是被触发的挑战面，不是新 route
  或 standalone method。
- Mindthus router pressure tests 扩展到 direct execution、missing proof、
  context conflict、constraint recognition、method arbitration、execution impact
  和 pressure-surface behavior。

### 验收

- 新增 `tests/mindthus_judgment_kernel_acceptance_run_2026-05-26.md`：当前实现 live
  acceptance 行为分 `98 / 100`，保守有效分 `92 / 100`。
- 新增 `tests/mindthus_v0_6_version_acceptance_2026-05-26.md`：记录 v0.6 单模型版本
  验收范围、证据和非覆盖项。
- 本次版本验收不声明跨模型鲁棒性，也不是干净 old-vs-new A/B。

### 校验

- `python3 -m unittest tests.test_mindthus_router_contract -v`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## v0.5.2

发布日期：2026-05-23

说明：这是 `v0.5` 系列的小版本调优，重点是让 Mindthus 的复杂判断更可辩、
更可测，也更容易讲给非专业但聪明的读者听。

### 新增

- 新增 `SELA` 单 Agent 多角色压力检查：`System Advocate`、`Local Defender`、
  `Timing Auditor`。它用于非轻量战略判断，防止系统效率原则滑向过早、过绝对
  或过线性的行动结论。
- 新增 `EDSP` 单 Agent 多角色挑战：`Builder`、`Challenger`、`Synthesizer`。
  它用于保护极限推演的第一层结构骨架，避免坐标系干净但错误。
- 新增 SELA / EDSP 多角色 A/B pressure tests 和实际运行记录，覆盖非平凡判断、
  低风险确定性任务，以及一个压线摇摆场景。
- 新增 Mindthus `AGENTS.md` 的 `No Abstract Jargon Wall` 表达纪律：先讲
  “这对你意味着什么”，再讲 “Mindthus 把它叫做什么”。

### 调整

- `SELA` 文档明确：多角色是单 Agent 内部压力，不默认升级成多个 Agent；多个
  Agent 只作为高影响、强分歧或路径依赖场景的升级选项。
- `EDSP` 文档明确：如果 `Challenger` 发现决定性变量遗漏、维度重复、极端推演
  不充分或漂移读取偏置，不应继续做场景投影，而应重建第一层结构。
- `tplan` 方法页增加执行驱动的自适应规划架构图，强调它不是先完整规划再执行，
  而是在 Mission 固定的前提下，用执行反馈持续演化任务树。

### 校验

- `python3 -m unittest discover -s tests -v`

## v0.5 + v0.5.1

发布日期：2026-05-18

说明：GitHub Release 以 `v0.5.1` 发布，合并记录 `v0.5` 的方法分层纪律与
`v0.5.1` 的 EDSP frontmatter 修复。没有单独发布 GitHub Release `v0.5`。

### 新增

- 新增项目级方法分层纪律，要求方法写作显式区分 `core`、`mainline`、
  `guardrail`、`boundary`、`example` 与 `runtime support`，避免主思想被
  从属补漏和细节优化冲淡。
- 新增 `SELA` 时机检查，用临时保留、锁死未来、行动窗口三问，防止长期系统
  效率判断被误写成立刻切换动作。
- 新增方法分层契约测试，校验项目级规范存在、所有 `SKILL.md` 入口按分层顺序
  组织，并阻止未归入分层体系的额外 H2 段落。
- 新增 `SELA` 契约测试，校验时机检查保持轻量，不升级成独立原则或人文价值观。

### 调整

- 重构所有 `SKILL.md` 入口，使主路径、从属补漏、边界和运行支撑材料分层清晰。
- 将 `using-mindthus` 的前置校准保留为主路径，将 Anti-Spiral 保留为从属补漏。
- 将 `tplan` 的启动策略和运行循环保留为主路径，将 Alignment Gate、
  Anti-Spiral Gate、Linear Continuation Gate 等放入从属补漏层。
- 将 `WAE`、`TVG`、`3L5S`、`EDSP` 的脚本、模板、常见误用和停止条件从主路径中
  分离出来，降低入口阅读负担。

### 修复

- 修正 `EDSP` skill frontmatter YAML，使技能包发现和文档打包检查保持稳定。
- 增加 skill frontmatter 契约测试，避免同类问题回归。

### 校验

- `python3 -m unittest tests.test_packaging_docs -v`
- `python3 -m unittest tests.test_method_layering_contract -v`
- `python3 -m unittest discover -s tests -v`
- `python3 -m unittest discover -s tests/tplan -v`
- `git diff --check`

## v0.4

发布日期：2026-05-09

### 新增

- 新增 `tplan` Linear Continuation Gate，用于高影响决策。
- 新增 `path_assessment`，包含 `marginal_roi`、`path_role` 与 `evidence_delta`，
  要求同路径继续执行暴露 Mission-relative reasoning surface。
- 新增 Premise Calibration，并写入 `using-mindthus` 与 `AGENTS.md`，作为选择
  Mindthus skill 前去除二手概念的前置动作。
- 新增 Mindthus router pressure tests，覆盖 ROI 标签、first-principles 名称陷阱、
  workflow/agent 伪二分、趋势口号和 polished artifact 陷阱。
- 新增 Anti-Spiral Self-Audit 方法资源，并在 `AGENTS.md` 与 `using-mindthus`
  中提供激活入口。
- 新增 `tplan` `anti_spiral_audit` runtime gate 文档，覆盖重复局部修补、加层、
  负反馈和弱 evidence-delta continuation。
- 新增 WAE 指引，将局部修补螺旋视为 workflow/agent/evidence 控制边界失败模式。
- 新增 Anti-Spiral A/B pressure tests，分别评分 agent 是否触发机制以及是否退出螺旋。

### 调整

- 高影响 `tplan` hook output 在 Mission-aligned、切换 active task、改变 Mission status、
  subtraction、escalation 或 Mission closure 时要求 `path_assessment`。
- `tplan` 文档明确：elapsed time 不是 continuation 的根判断标准；marginal Mission ROI、
  path dominance 和 expected evidence delta 才是相关判断面。

### 校验

- `python3 -m unittest discover tests/tplan -v`
- `python3 -m unittest tests.test_packaging_docs tests.test_mindthus_router_contract -v`
