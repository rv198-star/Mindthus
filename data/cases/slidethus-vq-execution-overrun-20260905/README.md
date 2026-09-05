# Slidethus 长任务执行过载：真实使用事故档案

记录 ID：`RU-20260905-SLIDETHUS-VQ-OVERRUN-01`
日期：2026-09-05
归属：#144 真实使用证据；一次回溯事故，非完成任务评测。

## 入库与隐私

用户已明确确认这是自己的使用场景，并批准将所提交的有限案例包及分析录入 Mindthus。
审批记录、原附件 SHA-256、逐文件哈希与样本纳入边界见 [admission.json](admission.json)。

`packet/` 内 10 个文件逐字节保留原附件内容。原件中的“未上传”、
`review_required_before_share=true` 和 `automatic_upload=false` 是导出当时的历史状态，
保持不变；本次单独的显式用户批准记录在 admission 中。该批准不授权额外收集或公开
完整 Mission、对话、PPT、凭据或其他未提供材料。
原始 selected-log-summary.txt 带一个EOF空行；仅对这个文件设置
`whitespace=-blank-at-eof`，保留其原字节，其余空白检查和产品规则不变。

已逐件阅读：保留项目名、工单/事件标识、相对源码路径、时间与哈希；没有原始模型
提示、客户内容、私人绝对路径或凭据。模式扫描只作辅助，不能证明绝对匿名。

## 证据到底覆盖什么

| 层次 | 可支持的结论 | 不支持的结论 |
|---|---|---|
| 原件的选取证据 | 两条 acceptance_failed 摘要，导出时 Mission active、活动游标为空 | 完整验收 payload、完整任务树与全过程 |
| 导出者的日志摘要 | 指向源哈希、原行号和事件 ID 的时序及工作区统计 | 本轮已独立重算全部 71 条原始事件或 140 次操作 |
| 本轮运行时探针 | 指定版本的公共 API 可以产生下述四类矛盾 | 原事故执行的确切源码版本、四类缺陷全部导致这次事故 |
| 用户反馈 | 约16小时执行未达到其预期；真实负面体验 | TPlan 造成全部耗时、SRA 导致失败、修复后必然节约多少 |

原包没有完整 execution trace、evidence log 或运行源码快照。
`runtime_provenance=exact` 只表示导出工具报告的本地兼容性，不等于已知原执行使用了
`v1.10.0`。`pulse.json` 明确是 **case-pulse-view**，不是执行时调用官方 Mission Pulse
或应用其决定的证据。

## 事故窗口（来源：原包摘要）

目标是完成真实 PPTX 首次成稿质量与成本修复，并通过真实 PowerPoint holdout。
报告的初始化时间为 `2026-09-04T19:56:31.895240Z`，VQ013 阻断为
`2026-09-05T12:03:43.060520Z`，相差约16小时07分。VQ012 在
`2026-09-05T03:42:42.653838Z` 被标完成，至上述阻断又过约8小时21分。

七个新验收工作区报告累计140次Host操作、60次provider exchange，未得到新样张或
全量PPTX。零产出口径仅限这七个工作区，不能抹掉其他代码、测试或历史 Office 工作。
单root的35次上限在B生效，C–G另外104次的事实支持研究累计投入与续投决策，
**不证明此前已经存在或被突破了35次的Mission总预算**。

VQ012 的验收范围与其局部测试支持不匹配是重要的调查方向；没有逐工单源码快照，
不能断言后来发现的每个缺陷在其完成时已经存在。Slidethus 编译分支问题是导出者
报告，本轮未检查相应产品源码，不把它当作当前独立代码复验结果。

## 当前代码复现

固定基线：`407112ded87377b5b7dd351c49dd0d20b1d598d4`；
TPlan 源码与 `v1.10.0` 一致；Python `3.10.12`。

| 编号 | 当前公共 API 观测 | 定位 |
|---|---|---|
| R1 | 不存在的 `EPLACEHOLDER` 或文件路径作为 evidence ID，仍写入 completed | trace refs 仅查字符串形状，未在事务内解析证据 |
| R2 | `add_task_node(status=active)` 创建活动根任务，游标仍 null，无 matching active-node event | 新增路径与统一激活路径分离 |
| R3 | 两个 success-critical Task 均 pending、无验收通过，仍能把 Mission 设为 completed；存在 acceptance_failed 也一样 | `apply_decision`/`validate_mission` 缺关闭后果检查 |
| R4 | `authorized_action=stop`，但 recommendation=continue 且包含激活 mutation，仍 applied 并激活T1 | 续行字段查枚举，没有校验行动与授权的机械一致性 |

R1/R2 与案例报告的机制对应；R3/R4 是本轮进一步合成复现，**不是声称原事故
发生过错误Mission关闭或存在一份被违反的stop授权**。原Mission仍是active。
正常证据引用、artifact_refs、pending新增及普通激活作为对照也已运行；
这些对照证明形状通路仍可用，不证明关键验收已满足。

完整机器输出：[current-runtime-observations.json](current-runtime-observations.json)。
修复方案：[TPlan 执行控制缺口修复计划](../../../docs/internal/issues/tplan-execution-overrun-remediation-20260905.md)。

对应issue：#196证据引用；#197活动游标；#198完成条件；#199续行授权后果。
四项为已复现、尚未修复的P1；#200另管外部执行与跨root续投的设计验证。
#200不是对既有全局预算绕过的定罪，也不是立即实施新的运行时功能。

## 重放与验证

从仓库根执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3.10 data/cases/slidethus-vq-execution-overrun-20260905/reproduce.py
PYTHONDONTWRITEBYTECODE=1 python3.10 data/cases/slidethus-vq-execution-overrun-20260905/reproduce.py --packet-only
python3.10 scripts/log-fidelity-usage.py --validate --log data/fidelity-usage-log.jsonl
```

可替换为项目支持的解释器。探针只在 TemporaryDirectory 中创建合成 Mission，
不改产品代码或原运行。它不是纳入CI的“必须继续有bug”测试；退出0表示诊断执行完，
不能写成正确性PASS。修复时应把相应场景变为期望拒绝的永久回归，并另保留合法对照。

原导出校验器要求固定目录名。入库放在packet目录，所以探针先逐字节校核，再将
原文件复制到新临时目录下的原导出目录名执行校验器。结果为0 blocker、0 warning、
`review_required`；用户的本次单独批准保存在admission，不篡改原包状态。

## 采集口径

现有 `data/fidelity-usage-log.jsonl` 仅增加一条 `record_type=real_use` 的档案引用，
沿用当前v0.1记录结构。稳定record_id、observed_at、retrospective与纳入判定在
admission.json中结构化记录，并在旧记录notes中明确引用。
现有logger只校验已支持字段；这不等于#144要求的分类型状态、元数据校验已实现。

本记录不是10个完整前瞻任务中的第1个：整体Mission未结束、调用模式未知、入库为
回溯。真实事故档案计数为1，本案例对完整前瞻任务分母的贡献为0。
它不会解除#144 freeze，也不会自动进入benchmark、对照保留集或SRA收益统计。
`constraint_helped`、`decision_changed`、`rework_reduced`、Mindthus额外负担及因果伤害
均为unknown；修复净收益尚未测量。后续追踪更新同一案例，不按root或缺陷拆成新样本。

## 工作边界

本次仅入库、复现、设计与issue登记。运行时修复和平台/预算扩展分开推进。
已验证的正确性问题符合冻结期缺陷例外；单案例提出的预算方案先做有界设计验证，
不凭这一例自动批准新SRA–TPlan集成、宿主Hook或常驻调度器。
