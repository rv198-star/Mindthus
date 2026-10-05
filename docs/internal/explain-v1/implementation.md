# Explain V1 与 TPlan 进展输出：实现与开发期验证

- 日期：2026-10-05（Asia/Shanghai）
- 源码基线：`541049486ce8b61c4c7e212397922999a9b8ff2e`
- 交付版本：Unreleased
- 验证状态：ChatGPT 当前对话已现场确认 **Visualizations / app_block** 能直接呈现所需的内嵌交互效果；Explain V1 核心技能、默认人向交付、表达模式、TPlan 进展模型、chat-native 进度条、Visualizations adapter、离线 HTML、打包与工程验证均已完成验收；发行目标为 v1.12.0。

## 最后交付返修（Visualizations 已现场确认）

- chat-native 文本进展视图新增直接可见的 Unicode 进度条：源数据提供百分比时按原值绘制；剩余占比区间用 `█` 表示确定下界、`▒` 表示不确定区间、`░` 表示其余范围。没有源百分比时不为“好看”而造数字。
- `--html` 的 ChatGPT 宿主实现已定位并现场确认：使用 **Visualizations / app_block**，不是 Markdown HTML code block、附件、Jupyter HTML、MagicPath Canvas，也不是项目自定义 envelope。Explain 直接提交 `variant=inline`、`language=html` 的 raw HTML fragment，由 ChatGPT 提供 sandbox 与 iframe-like 宿主展示；Code/Preview 只属于源码查看面。TPlan 新增 `render_user_update.py --visualization` 与 `render_progress_view.py --format app-block`，从同一个 `tplan.progress_view.v1` 生成 Visualizations payload；工作块选择、dependency-edge 高亮、展开与本地交互继续存在。`--inline-html` 保留为非 ChatGPT 宿主的通用 transport，`.html` 只在显式文件导出时持久化。Explain portable core 仍不依赖具体插件或提供商。

- 新增 `skills/explain/scripts/prepare_html_delivery.py`：只读现有 HTML，输出可预览 HTML 代码块及同源 SHA-256；状态固定为 `prepared_not_verified`，不假装拥有宿主的显示回执。
- [当前任务的真实交付状态](current-delivery-status.html)替代先前无来源的87%进度图；状态页现在区分已完成 Skill 功能、当前交互表面验收、后续合并与发布，不再把下载 HTML 作为交互请求的必选项。
- 本轮 Python 3.11 聚焦回归：107 项，106 通过、1 个既有可选依赖跳过；覆盖 Explain 合同、`work_plan`、progress renderer、五种打包布局，以及新增聊天进度条/区间条。另单独运行 progress + Explain 29 项全部通过。
- 同一 HTML 在 Chromium 的 1440px/390px 视口可展开原生 details，无横向溢出、外部请求或 JavaScript 错误。这是独立浏览器验证，不是当前对话显示验收。
- 交互表面已在当前 ChatGPT 对话用 Visualizations / app_block 现场确认：用户明确反馈该效果就是此前满意的内嵌交互式可视化。HTML MIME、附件、PNG、Jupyter rich output、MagicPath Canvas 和 Code/Preview 均已实测排除为目标路径。后续验收只需确认 Mindthus 生成的 app_block payload 保留同一交互语义。

## 上一阶段：共享基础合同与依据边界

本节保留 `1f6e529a` / `4bcaf760` 阶段记录；默认触发策略已由下方的新决议替代。

依据为用户重新上传的 `mindthus-explain-v1-design-spec(2).md`，SHA-256：
`673b45a07122ed33c4dcc143095a04d12a8a65a04f2cda26efc2a4a58e004182`。
原文件不改写。

原稿 §16 规定独立 Skill、其他方法可依赖、上游 → Explain 以及 fail-open；§17 描述
Explain 产物的交付路径。§25 同时明确不强制所有 Skill 接入、不做全系统默认自动
Explain。原稿没有逐字规定“所有方法必须默认继承共享表达合同”。此前把这一具体
实现声称为原稿已经强制要求，属于审计归因过度，现更正。

本轮按用户随后明确批准的“列出偏移点，并逐个修复”执行：把已有表达原则复用为
默认基础合同，完整 Explain transformation 仍按需。不新增统一 Schema、第二模型
调用、运行时复审或插件前置。以下是相对于这项已确认接入目标的六个修复点，
不是对 §25 非目标的否定。

| 编号 | 原接入缺口 | 已完成修复与检查入口 |
| --- | --- | --- |
| D1 | 全局入口只描述按需 Explain，未区分基础表达纪律 | `AGENTS.md` / README 定义共享基础与按需转换；链接到同一合同 |
| D2 | Explain 本体没有把基础合同与完整转换分层 | `presentation-contract.md` 提取已有清晰表达原则；当前响应内执行，不增加模型轮次 |
| D3 | 路由入口仅声明“可选表达支撑” | `using-mindthus` 增加表达边界，八个判断 owner 及 trace enum 保持原样 |
| D4 | 八方法有分散表达规则但无共享合同入口 | 八个 `SKILL.md` 均链接到同一合同；直接调用也可解析，保留方法特有要求 |
| D5 | TPlan 专用集成与全方法基础接入混淆 | TPlan 是首个结构化展示适配器；其他方法不需要复制 renderer 才能继承表达规则 |
| D6 | 测试只能检查合同名称，未验证接线和范围 | 增加源目录及五种发行布局的九入口链接检查；明确机器输出、精确格式和必需交付物沿用上游合同 |

Visualizations / app_block 已获现场确认，是后续批准的展示适配，不在本轮回退或重做。
本轮不修改任何工作量计算、TPlan 状态、判断路由、证据校验或 HTML/Visualizations renderer。

### 本次中断恢复

`1f6e529a` 已完成主体接入并推送。GitHub run `37368761044` 因 hosted runner 未能领取
任务而取消，官方 annotation 为 “The job was not acquired by Runner of type hosted even
after multiple attempts”；测试步骤未运行，不能视作测试失败或通过。
本次只完成最终复核、合同链接、依据归因和最后验证，保留此前功能验收。

恢复后的 Explain/TPlan/打包集中回归共 149 项：148 通过，1 个既有可选依赖跳过；
新增测试覆盖九个直接入口及五种发行布局的共享合同链接，并约束机器输出合同保留。
Explain 可移植性 lint 为 `portable=true`，0 error / 0 warning。完整 unittest 与最终
提交的 GitHub CI 结果记录在 PR #224 和持久任务中，避免沿用旧提交的绿色状态。
这些检查证明合同/链接/打包接线及程序回归，不把文档断言当作所有模型输出质量的实测。

## 当前决议：默认使用 Explain Skill

用户在比较“只继承表达规则”与“实际默认使用 Explain”后，已批准后者。当前正式入口
为 `skills/explain/SKILL.md`，不是另一份基线规则：方法形成结果后，当前 Agent 默认
使用 Explain 的 clarity 模式组织人向交付。首次缺有效上下文则读取入口，之后复用；
增强资源按需读取，清楚的结果可以不改写。不新增独立 Agent、二次模型调用、原答案
重写流水线或运行时调用回执。

这是对早期 V1 默认接入策略的后续调整，不追认为原稿 §25 已经要求默认全方法调用。
纯机器输出、代码/命令/逐字引用/精确格式、内部记录沿用原合同；短确认不扩写。
TPlan 保留首个结构化展示适配器的位置；其工作量、状态、验收与 Visualizations 实现
不因本次策略调整而变化。其他方法无需复制 renderer，直接链接正式 Explain Skill。

决议、六个同源开发用例和成本口径见 [默认交付评审](default-delivery-review.md)。

用户追加确认：**风险与主要阻塞点为可选信息**。有当前来源时默认呈现重要内容；没有记录时省略栏目。影响、关联工作块和解除条件按已有来源说明，不要求用户填空表，不新增固定风险评估流程，也不把未提供信息写成“没有风险”。精简输出仍保留已知重大限制。

## 实现入口

Explain 的正式入口位于 [skills/explain](../../../skills/explain/SKILL.md)，
`presentation-contract.md` 是同一 Skill 的范围与保真资源，不再是跳过 Skill 的默认
替代路径。八个方法与 using-mindthus 的链接指向正式入口；Explain 仍未进入八个判断
owner、判断 trace enum 或独立复审循环。

```text
/mindthus:explain 把这份说明讲清楚，保留条件与未知。
/mindthus:explain --brief --eli5 --audience 产品负责人 解释这段技术材料。
/mindthus:explain --html --brief 把当前任务结果做成对话内可交互 HTML；需要文件时再明确要求导出。
```

TPlan 增加可选 `work_plan`。创建 Mission 的两个入口支持 `--work-plan-json`；已存在 Mission 使用受控元数据入口更新：

```bash
python3 skills/tplan/scripts/record_work_plan.py MISSION_DIR \
  --input work-plan.json --summary "更新剩余估计与已知条件"

python3 skills/tplan/scripts/render_user_update.py MISSION_DIR --progress
python3 skills/tplan/scripts/render_user_update.py MISSION_DIR --inline-html
python3 skills/tplan/scripts/render_user_update.py MISSION_DIR \
  --html MISSION_DIR/reports/progress.html  # 仅显式文件导出

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

**交付状态更正：**用户明确要求的是当前消息中直接可见、可交互的 HTML。现场探针最终确认目标宿主表面是 ChatGPT **Visualizations / app_block**；其宿主外壳提供右上角菜单（如复制为图像、发布为 Site），与此前成功样例一致。Markdown HTML code block 的 Code/Preview、文件附件、Jupyter rich HTML、直接 iframe 标签和 MagicPath Canvas 均不是该目标表面。Visualizations 的现场确认因此关闭“宿主是否存在”这一不确定性，项目侧改为输出 app_block payload。

先前聊天图中的“87%”和“PR 已完成20%”来自临时人为权重，未见于源计划；撤回这些数字及“只剩合并发布”的结论。Visualizations 宿主表面已经现场确认；真实剩余工作变为：项目侧 app_block adapter 的回归与交付复核、任务关单，随后是待批准的合并和待决定的发布。剩余工作量与占比仍未估算。

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
