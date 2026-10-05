# Explain V1 与 TPlan 进展输出：实现与开发期验证

- 日期：2026-10-05（Asia/Shanghai）
- 源码基线：`541049486ce8b61c4c7e212397922999a9b8ff2e`
- 交付版本：Unreleased
- 验证状态：除宿主侧“对话内可交互展示”外，Explain V1 核心技能、表达模式、TPlan 进展模型、chat-native 进度条、离线 HTML、打包与工程验证均已完成；交互表面仍待当前宿主现场验收，因此整体开发交付尚未关单。

## 最后交付返修（现场未验收）

- chat-native 文本进展视图新增直接可见的 Unicode 进度条：源数据提供百分比时按原值绘制；剩余占比区间用 `█` 表示确定下界、`▒` 表示不确定区间、`░` 表示其余范围。没有源百分比时不为“好看”而造数字。
- 交互需求已从 HTML 文件格式中解耦：用户只要“对话内可交互”时，可由宿主原生 artifact、已安装 interactive app/canvas 或其他 widget 直接消费同一只读 view；只有显式要求 HTML/文件导出时才必须生成下载文件。

- 新增 `skills/explain/scripts/prepare_html_delivery.py`：只读现有 HTML，输出可预览 HTML 代码块及同源 SHA-256；状态固定为 `prepared_not_verified`，不假装拥有宿主的显示回执。
- [当前任务的真实交付状态](current-delivery-status.html)替代先前无来源的87%进度图。该快照固定到 `c33957c9` 核查基线，并保留当前内嵌交付未验收、PR 草稿和未发布状态。
- 聚焦回归：70 项，69 通过、1 个既有可选依赖跳过；覆盖实际 HTML 内容与文件同源、反引号不逃逸、只读和五种打包布局。
- 同一 HTML 在 Chromium 的 1440px/390px 视口可展开原生 details，无横向溢出、外部请求或 JavaScript 错误。这是独立浏览器验证，不是当前对话显示验收。
- 当前对话已经尝试 HTML MIME 输出，但没有获得可见与交互回执；本轮实际交付改用完整 HTML 预览代码块并同时提供文件。当前宿主是否默认打开 Preview 仍需现场证据，任务不能据此自动标为完成。

## 已确认的产品范围

Explain 是独立的理解与表达技能。它解释已有结果，保留原判断、证据强度、状态、验收和执行权限。默认完整清晰；`--brief` 减少阅读负担，`--eli5` 按受众做最低必要降阶，`--audience` 覆盖受众，`--html` 交付单文件离线阅读产物。参数可以组合，任务入口与最终交付共用同一套转换规则。

TPlan 是首个正式上游接入场景。用户需要理解整体进展、剩余工作块、剩余估计、各块在剩余量中的占比，以及已知前置和并行条件。

用户追加确认：**风险与主要阻塞点为可选信息**。有当前来源时默认呈现重要内容；没有记录时省略栏目。影响、关联工作块和解除条件按已有来源说明，不要求用户填空表，不新增固定风险评估流程，也不把未提供信息写成“没有风险”。精简输出仍保留已知重大限制。

## 实现入口

Explain 的入口与按需参考材料位于 [skills/explain](../../../skills/explain/SKILL.md)。它未进入八个判断 owner、判断 trace enum 或固定加工流水线。TVG 保留原有强化能力；Explain 的普通执行没有独立复审循环。

```text
/mindthus:explain 把这份说明讲清楚，保留条件与未知。
/mindthus:explain --brief --eli5 --audience 产品负责人 解释这段技术材料。
/mindthus:explain --html --brief 把当前任务结果做成离线阅读报告。
```

TPlan 增加可选 `work_plan`。创建 Mission 的两个入口支持 `--work-plan-json`；已存在 Mission 使用受控元数据入口更新：

```bash
python3 skills/tplan/scripts/record_work_plan.py MISSION_DIR \
  --input work-plan.json --summary "更新剩余估计与已知条件"

python3 skills/tplan/scripts/render_user_update.py MISSION_DIR --progress
python3 skills/tplan/scripts/render_user_update.py MISSION_DIR \
  --html MISSION_DIR/reports/progress.html

python3 skills/tplan/scripts/render_progress_view.py MISSION_DIR --format json
```

完整字段语义见 [TPlan schema](../../../skills/tplan/resources/schema.md)，输出方式见 [user-output](../../../skills/tplan/resources/user-output.md)。HTML 与文字视图从一致快照读取信息；普通自动更新保留既有心跳与静默节奏。

## 数字和状态的含义

| 信息 | 处理方式 |
| --- | --- |
| 整体进展 | 保留源状态、已有结果与证据；数值只来自含义明确的上游指标 |
| 剩余估计 | 保留单位、上下界、依据与覆盖范围；未知不计作零 |
| 工作块占比 | 只对同单位、非重叠的已估剩余范围计算；部分覆盖明确标注 |
| 历史投入 | 继续由原执行报告承载，不倒算完成度或剩余量 |
| 并行条件 | 展示已声明的前置、资源条件及未确认信息，不自动派发或授权 |
| 规划更新 | 作为 `planning_metadata_updated` 状态记录，不计为任务或验收推进 |

父子范围不重复统计；缩减范围不算新增完成成果。`completed` 与合格证据分开，状态和剩余估计冲突时保留源信息并提示核对。旧 Mission 缺规划数据时仍可解释已登记信息，已存在的运行时兼容规则继续有效。

## 发行与职责接入

构建脚本的 `SKILL_NAMES` 加入 Explain，覆盖 Claude plugin、Claude personal skills、Codex skills、Codex plugin、OpenCode skills 五种布局及路径重写。README、Codex 安装说明、卸载清单和 Unreleased 记录同步更新。

技能本体保持薄入口，HTML、表达模式、TPlan 进展细则按需加载。工程结构检查只保护其能机械判断的合同；它们不能证明解释更容易理解。

## 开发期验证记录

### 工程检查

- 本轮返修前 `c33957c9` 的既有 GitHub 完整 unittest gate 通过：共 1,147 项，1,140 项通过，7 项按既有依赖条件跳过，0 失败、0 错误。首屏 UI Contract、区间占比不取中值和对话原生可视化 + HTML 文件/可选 inline preview 的多表面交付合同均有回归保护。7 个跳过项为既有可选依赖检查；本次没有改变跳过规则。
- CI 中四项 primitive/runtime smoke 命令全部通过。
- Explain 在 Claude plugin、Claude personal skills、Codex skills、Codex plugin、OpenCode skills 五种实际构建布局中均存在，资源与链接有效；八个判断 owner 保持原集合。
- TPlan 工作计划与进展视图回归覆盖未知、混单位、父子范围、区间份额、状态与证据冲突、共享风险、Guard、事务、来源诊断和首屏 UI Contract；最后的后端与 renderer 组合为 57 项通过。
- `runtime_doctor.py --format json` 返回 `ok`，无缺失脚本与诊断错误；返修后的运行时指纹为 `sha256:c155e5cb96aaac0314082cd0599dbb8067a70dcbd2170eb7ad5186ca114b774e`。

### 页面与保真检查

E 页面由公共 CLI 生成。第一次实现把限制、风险/阻塞、验收反例、已有结果、事实和下一步都提升到了剩余工作之前，虽然语义完整，但违背了原样板的阅读层级；本轮把它明确归类为 representation regression，只返修 HTML 表现层，不改 `work_plan`、剩余量、依赖、风险、阻塞、验收或来源逻辑。

修复后的首屏 UI Contract 固定为：Mission 极简状态行 → 整体进度 → 剩余总量 → 剩余工作块及占比条。风险、阻塞、依赖图、证据、估算依据、搜索/筛选、来源和历史执行链接全部进入一个默认折叠的详情区；折叠标题仍显示风险/阻塞/限制计数。区间占比使用确定段与区间段，不取中值。

**交付状态更正：**用户明确要求的是当前消息中可见、可交互的 HTML，同时可以独立下载。`c33957c9` 的图片优先合同不能代替这项验收。本轮新增实际 HTML 预览块准备器，保持源文件和预览内容一致；文件生成、代码测试、外部浏览器验证与当前对话内验收分开记录。没有宿主或用户的可见/交互证据前，内嵌交付保持未验收。

先前聊天图中的“87%”和“PR 已完成20%”来自临时人为权重，未见于源计划；撤回这些数字及“只剩合并发布”的结论。真实剩余工作是：内嵌交付现场验收、相应复核与任务关单；随后是待批准的合并和待决定的发布，剩余工作量与占比尚未估算。

在 Chromium 离线环境中实际测试 1440×1024 与 390×844 视口：桌面核心看板结束于约 927px、详情入口约 955px，可在一屏内读完核心信息；窄屏保持相同信息层级并纵向排列。两个视口均无页面横向溢出、外部 HTTP 请求或 JavaScript 异常；点击工作块会打开详情并定位对应依据，详情内搜索与筛选仍可用。D 页面原生详情展开与离线访问也保持通过。

独立复核已关闭。已报告的完成声明/剩余估计冲突、完成证据缺口、当前共享风险、运行时来源诊断、后续验收失败、Guard 解除和估计信心保留问题均已修复。被父工作块覆盖的前置任务，其证据警告仍完整保留在下钻详情中，且不被新增为计量块；这些语义完整性要求不再挤占核心看板。

A 的重复解释保留全部关键事实与限定，只有结构变化；D 内置引文与源材料的事实正文逐字一致，演示性质在引文前保留。

### 复现环境与既有实验探针

完整 gate 使用隔离 Python 3.11.16，并让子进程使用同一版本，与 CI 的 Python 3.11 系列一致。最初仅拉取 main 历史的开发克隆缺少既有测试所需的两个侧分支对象；已补回 `ed5171bf7b34746027acd730864d9c98ef1dd8d2` 与 `be25f4834e01596a0e62e311eccd3d42c4bab610`。这两条历史引用仍在远端存在，现有 CI 的完整历史 checkout 可取得它们。

另将 destination-first 研究 harness 的旧探针限定到它实际保护的 Task 控制合同节，避免把独立可选规划说明中的 `depends_on` 误认作 Task 调度支持。新增反例证明：Task 控制字段真的加入依赖，或合同节缺失时，探针仍失败。冻结期待值、历史 replay 与 source manifest 保留原样；本轮不将旧实验结果用作 Explain 的效果证明。

## 原材料与交付样例

这些都是开发期的合成样例，不是 Mindthus 项目的真实进度或效果统计：

| 场景 | 记录 |
| --- | --- |
| A：复杂任务进展，brief | [原材料与输出](samples/a-brief.md)、[重复解释](samples/a-brief-repeat.md) |
| B：概念解释，ELI5 + audience | [原材料与输出](samples/b-eli5.md) |
| C：操作说明，普通 Explain | [原材料与输出](samples/c-instructions.md) |
| D：组合参数离线 HTML | [源材料](samples/d-source.md)、[实际 HTML](samples/d-report.html) |
| E：TPlan 工作进展视图 | [输入与复现记录](samples/e-source.md)、[实际 HTML](samples/e-report.html)、[文字输出](samples/e-report.txt) |

A–D 由只获得技能、原始请求和源材料的独立会话完成，再进行原文对照。没有给执行者提供预期答案。E 使用真实 TPlan 脚本和合成 Mission，验证数据到视图的实现；六个工作块合计 13–22 小时，40 percent 是独立的人工显示样本，源数据和页面均明确标注其演示性质。

## 验证边界

这些有限样例与回归检查不构成跨模型的质量、token 节省率或金额 ROI 证明。它们不复用历史冻结实验为 Explain 背书，也不进入技能的正常运行链。当前变更属于 Unreleased，正式发布仍按项目原有发行流程处理。
