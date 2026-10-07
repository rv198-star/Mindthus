# Explain HTML V2 — 执行计划与恢复入口

## 当前状态

2026-10-08 交付与主题整改：ChatGPT 暴露 Visualizations 时，Explain 交互式 HTML 必须在当前对话直接通过宿主能力交付；Codex 按实际渲染能力，其他环境保真降级。编译器和内嵌原型默认跟随系统明暗并支持真实宿主主题覆盖，深色高对比色已修复。Python 109项（108通过/1既有skip），浏览器主题144/144、原展示8/8，Skill lint 57文件零错误。见 [R1证据](evidence/d2/host-theme-r1/RESULT.md)。这仍是开发分支实现，**编译器生成的HTML尚待真实宿主回执**，不把此前手工 AppBlock 的可见性追认给编译器。


2026-10-08 最新纠正：Owner 明确 HTML 最终应直接在 ChatGPT 对话内显示，不能把独立宽屏 Dashboard 或 HTML 下载当作目标。已新增 **Inline Container 原型**：默认 stdout fragment／prepare-only app-block；按实际容器宽度重排，不复制网页外壳或写死 ChatGPT 宽度。1440px 浏览器内嵌 320/390/480/640/768/960px 容器，96/96 本地浏览器检查通过；原材料、共享 Skill/TPlan 和历史18次生成不变。真实 ChatGPT raw-HTML 展示入口本会话仍未取得，实际可见可操作回执保持未完成，不能用截图或文件链接替代。见 [内嵌纠正](prototypes/analysis-layout-r1/INLINE.md)。恢复任务 `tsk_c2e804d5d586cc9f`；证据 `/srv/agentdock/.cache/mindthus-explain-inline-r1/qa/`。

### 宽屏原型（历史，只作信息组合参考）

2026-10-08 最新：按已确认的 Dashboard / Report 方向完成 **Analysis Layout R1 可操作原型**，先供 Owner 视觉确认，不覆盖共享运行时。四种样例为执行简报、进度分析、方案矩阵、组合图解；均绑定既有材料。48/48 浏览器检查、2/2 打印检查、24/24 新旧查看器检查通过；原 18 次生成、Skill/TPlan 功能和发布状态不变。见 [原型与来源说明](prototypes/analysis-layout-r1/README.md)。本轮恢复任务 `tsk_b4fe243f717e595e`，最终查看器 `/srv/agentdock/.cache/mindthus-explain-analysis-r1/final/index.html`。下一步按实际页面反馈决定是否提炼通用布局，不再仅作字号或配色微调。

### Compact Style R1（历史，未被 Owner 认可为最终风格）

2026-10-08：Owner 已认可现有功能，要求重新设计为更紧凑、小一号、减少通用大卡片感的风格。本轮 **Compact Style R1 已实现，视觉风格待 Owner 确认**。基线为 `0b13845`，在原分支 `feat/explain-html-v2` 只更换共享 CSS、更新资产摘要/开发版本及说明；解析器、renderer、图布局、JS 与输入源稿保持不变。11份原稿 × Node/Python 的22组输出除 CSS/版本显示外完全一致；88组浏览器前后对照、7项主题/对比度/打印/窄屏检查通过。没有新增模型生成，没有合并或发布。见 [视觉重构证据](evidence/d2/compact-style-r1/README.md)。

当前可恢复任务：`tsk_9fff52e20e6b14f0`；产物缓存：`/srv/agentdock/.cache/mindthus-explain-compact-r1`。后续先查看新版与同稿前后对照；不重开已认可功能，不把主观风格自行判定为用户已验收。原宿主 inline 回执仍是独立边界。

### 上轮记录（历史，保留原证据）

本轮最新结果：#228真实主生成18/18与独立匿名评审1轮保持原样、0重生成；评审指出的11B/12B默认全图显示共享缺口已完成 **Display Repair R1 PASS**。修正版默认适配全图并保留原始大小切换，前移 `sequence`、收紧信息密度并恢复蓝/绿/琥珀/红语义层级；原9个B短稿仅重渲染，D2浏览器检查108/108通过。见 [原真实批次结果](evidence/d2/model-r1/RESULT.md)、[显示修复结果](evidence/d2/display-repair-r1/RESULT.md) 与 [18份原始查看器](evidence/d2/model-r1/index.html)。ChatGPT宿主inline app-block真实回执仍未由本修复证明；#229 tree/timeline继续等待，不重复模型生成。以下状态段为历史记录。

最新授权：用户批准完成#228的18次真实生成和独立评审；旧Jev渠道/额度约束已归档，不再参与当前任务。当前执行依据为 evidence/d2/model-r1/registration.json。用户交付要求是18份可点击产物及对照索引；以下旧阻塞文字仅为历史背景。

当前精确进度：#227 实现提交 `64ae68d`，Draft PR #230；#228 已按 `54f4988` 预登记完成36/36固定工程检查与3个局部更新检查，真实模型配对/独立理解/宿主inline回执仍未完成，详见 [D2结果](evidence/d2/README.md)。#229 尚未开工。以下旧段落保留为恢复背景，不覆盖本行最新状态。

2026-10-07 实施更新：#227 已有真实编译器与工程证据，见 [implementation.md](implementation.md)。
当前分支为 `feat/explain-html-v2`；D0 段落保留为历史。#228 下一步固定同源验证，模型调用与宿主可见验收仍需实际授权/证据；#229 继续受此前置约束。V2.1/V3 本轮不处理。

本计划继承 [design.md](design.md) 的“原方案完整承接”表；用户只修改 lint 与 Node 两点。七类组件、自动布局、源稿恢复、机械诊断、双交付表面、TPlan 边界和分阶段验证均继续有效，D1 子集不等于 V2 全部范围。

- 本轮范围：D0 设计与任务落地；不是 V2 工程实现或发布。
- 总任务：[#226](https://github.com/rv198-star/Mindthus/issues/226)。
- 设计：[design.md](design.md)。执行前同时读取项目 `AGENTS.md` 与正式 `skills/explain/SKILL.md`。
- 下一项工作：D1 / #227。D2 等 D1；D3 等 D2 的明确收益判定。

## 本地恢复点

- 节点：OCI，通过 Nexus-Dock-US；执行用户为 agentdock。
- 仓库：`/srv/agentdock/projects/Mindthus`，原 Jev 实验分支保留，不在这里开发 V2。
- V2 worktree：`/srv/agentdock/worktrees/Mindthus-explain-v2-design-20261007`。
- V2 分支：`docs/explain-html-v2-design`。
- 本轮同步的 main：`9a40b151cad20cdda52697a605bc6038922126c7`。
- 原实验 HEAD：`8e47cdacc63d3ad53c7fd0f64aa77d9a25e4ebd2`；本轮不切换、不重置、不清理实验。
- AgentDock D0 任务：`tsk_caca38073d6ad5ae`。
- 2026-10-07 本地实测：Python 3.10.12，Node 22.23.1；这是单个节点的环境观察，不代表用户群安装比例，不证明 V2 探测/回退代码已经存在。

## 阶段与完成条件

| 阶段 | 任务 | 前置 | 本阶段交付 |
| --- | --- | --- | --- |
| D0 | #226 的设计切片 | 用户确认方向 | 设计、分阶段任务、恢复入口与范围复核 |
| D1 | [#227](https://github.com/rv198-star/Mindthus/issues/227) | 读取 D0、核对 live main | 最小编译器、Node/Python 双后端、部分写作 lint、工程/打包验证 |
| D2 | [#228](https://github.com/rv198-star/Mindthus/issues/228) | D1 工程通过、固定 candidate | 同源保真、表面验收、真实成本与理解效果的配对证据 |
| D3 | [#229](https://github.com/rv198-star/Mindthus/issues/229) | D2 明确通过 | 按收益扩组件、逐步复用 TPlan 展示层 |

### D1 — 完整而小的第一版

实现一个 Python 入口，单次解析/检查/lint 后选择 renderer；Node >=20 可用则优先，环境不满足走 Python。后端共享 IR、规则和静态资产。MVP 限于 callout/table/flow/progress-range 与 doc/sheet。

验收关注：

1. 环境选择矩阵，含 Node 缺失/旧版本/异常/超时和显式强制后端；损坏安装、稿件错误、renderer 缺陷与环境缺失分开。
2. 双后端保留全部文本限定、引用、数值、单位、节点和有向边；Python 仍生成 HTML 图形与阅读交互。
3. lint warn/off、无自动改写、无强制清零；代码/引用/术语/未知/约数等固定正反例。
4. 离线、390px/1440px、键盘、无JS可读；五种发行布局；Explain/TPlan 原合同回归。
5. 显式导出页的源稿恢复与按块局部更新；未改块/引用/限定和样式选择保持不变，定位不唯一时不覆盖。编译错误包含源行、组件及正确示例，修复有界。

完成 D1 只说明可用，不说明更快、更便宜或理解效果更好。

### D2 — 同源对照，不拿短代替好

先冻结技术流程、比较报告、TPlan进展三类源材料。工程层把相同稿件/IR分别交给Node/Python；模型层以同一模型和源材料对照 V1 直接HTML 与 V2短稿+renderer，每类先3次配对。

登记所有输出、失败与修正；批次中不边跑边修。记录 input/cache/output token、工具轮次、渲染耗时、工具结果读取及最终交付（含HTML回传）。费用、宿主显示和独立理解效果缺失时明确未测，不让固定夹具或同Agent自查冒充。

增加固定工程用例验证导出后恢复源稿、再渲染语义一致，以及只更新指定块且其余不变。

关键条件/否定/未知/关系不能丢；折叠后的第一印象也应准确。以固定理解问题核对读者能否读出结论、限制与下一步。两种后端与两类包装、实际宿主显示分别留证据。

关键保真全过且交付无退步，并出现一致的可读性或完整交付效率收益后，才能进入D3。结果不充分则inconclusive；只少token不够。

### D3 — 扩展必须有依据

D2 显示修复已将 sequence 前移，用于避免相对原 Explain 演示的表达能力退化；D3 只按证据逐项考虑 tree/timeline，各项仍需同时定义 Python 回退并验证关系完整。TPlan继续是状态/计算/验收owner；只逐步复用表示组件，保留首屏、区间、未知、混单位、父子范围、标准执行报告与原判断边界。

## 保留的后续候选

`ask` / 页面回复保留原判断为 V2.1 候选，视频为 V3/Companion 候选，不在本批执行，也不是从方案中删除。ask 只呈现上游已有待决事项，不把预选当同意，不直接授权动作或改 TPlan 状态；视频单独设计验证。候选版本只是讨论位置，不是发布承诺。

## 集中停止条件

双语法/双词表分叉、Python变成丢内容的简版、语法错被回退掩盖、lint推动删风险或补数值、重写TPlan权责、为跑通增加运行时AI Review，均先回到已证根因；不通过继续堆组件解决。

HTML默认全量生成、视频/配音、ask/页面回复、外部操作和新的付费模型渠道不在本批授权范围。设计、工程通过、宿主验收和合并发布是不同状态，按已有授权分别处理。

## D0 核查口径

本轮只新增这两份设计文档，并创建 #226–#229；检查相对链接、差异范围、空白格式、源码基线和旧工作区状态。未修改发布技能、renderer、TPlan状态或共享安装；不重跑未改代码的全量测试，不声称做过模型A/B或V2页面验收。

后续恢复时先核对本文件与live issues/branch；按已完成证据继续，不重建任务、不回到旧Jev分支，也不把“方案已记录”当成“功能已实现”。

## D0 承接补正

用户指出上一轮只围绕两点汇报。核对确认主体方案仍在，但缺完整继承表，源稿恢复/局部更新未进入验收，后续候选定位弱化。本次定点补正上述内容及 #226/#227/#228，沿用 #229 与原阶段顺序；不新建 GitHub 任务，不把补正文档计为 V2 实现。
