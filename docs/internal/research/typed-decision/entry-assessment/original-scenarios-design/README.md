# Skills / 4K 入口：D3核心真实纠偏链路已覆盖

先读 [当前R3实测结论](D3-repair-r3/disposition.md)、[逐条真实回答与作者评审](D3-repair-r3/review.json)、[验证](D3-repair-r3/verification.json)。
Skills两轮、4K当前使用/购前两轮，已实际检查、纠偏并复查；原文整理分支也完成，合理简单解释保持。
R3有7个输入、5次真实纠偏、5次复查、1次真实整理；新增实质缺失控制被Q0挡回。不是D4独立净收益证明。
当前合同v0.3.2、通用CPA引用/绑定适配器v1.3；原始失败和各后继批次均保留，未更改历史审计意见。
R2的F反向期望未满足，保留作者对冗余范围的归因；B2来源归属措辞偏具体，未把窄验收通过当完美事实精度。
全仓1417=1412成功+5跳过，focused182通过，生命周期85/85；7输入重入新增调用0、记录不变。
当前任务 `tsk_1a35f6536ac65d76`；#211仍OPEN，默认不启用、main未变。内部缺陷已在授权内继续处理，无需Owner逐项确认。

## 历史首轮D3（失败记录；已由后继继续推进）

# Skills / 4K 入口：D3真实接线与首轮负面结果

**当时结论：D3首轮完整纠偏验收未通过；负面记录保持原样。**

先读 [D3实测结论](D3-live/disposition.md)、[派生诊断](D3-live/derived-observation.json)、
[验证与调用账](D3-live/verification.json)。同入口实际发生5次Jev检查、1次CPA整理，
四个目标轮次Q0回退、一个反例保持、一个整理引用失败；真实纠偏/复查均为0。
不要把未消费的细分信号或离线规则投影当成功。D1题义和旧档案保持；后续先修正
输入位置/来源提案与引用消歧合同，不直接放开Q0、不重跑这个终止批次。#211保持OPEN。

任务：`tsk_8dc1ae88072bbe94`；D3 source `6fa33f2` / freeze `716496e`。

## 历史D2交付（离线工程证据）
# Skills / 4K 入口：Relationship D2

**D2 已接通同一入口的离线纠偏与跨轮恢复；尚未启用真实模型或默认 Skill。**

先读 [D2合同](D2-contract.md)、[验证](D2-verification.json) 与 [离线执行观察](D2-offline-observation.json)。
实现通过 `entry.run(..., mode='relationship-frame.v1')`；CLI 为 `python3 -m experiments.typed_decision.entry --mode relationship-frame.v1 --fixture <显式离线夹具> --state-root <固定episode目录>`。
原 `assessment-v2` 模式保持默认。一次修正、可选一次复查、跨轮4/2/1请求额度和未知调用恢复均由代码执行；不把回退或清晰扫描当成任务完成。

64项新D2控制及全仓1388项（1383成功、5跳过）通过。Skills两轮与4K处境演示为固定脚本判断和修正，不是模型行为测量；原始记录及重入校验已归档。
下一步是D3同入口的真实宿主适配与单独live准入，再做D4原文端到端对比。当前没有新付费调用授权、没有默认启用、没有重跑旧6/8例。
当前D2任务：`tsk_d959a7cf9cf7dcf4`；#211仍OPEN。

## 历史 D1 交付

**当前：D1离线实现完成；独立快速设计审计REVISE但允许offline D1，作者局部处置后按v0.3.1开发。不是全面审计PASS或真实效果验证。**

先读 [D1合同处置与实现边界](D1-contract-resolution.md)，再读 [设计v0.3](design-v0.3.md)、
[实际机器合同v0.3.1](relationship-contracts-v0.3.1.json)、[验收v0.3](acceptance-v0.3.json) 和
[D1验证](D1-verification.json)。实现源码 `experiments/typed_decision/relationship_assessment.py`。

本轮一份真实独立上下文 [快速审计](quick-audit-v03/review.json) 与 [作者处置](quick-audit-v03-disposition.json)
分别保存；原被审v0.3未修改。43新离线测试、全仓1324项（1319成功/5跳过）通过，生命周期83/83。
14个语义判例是作者预期，不是Jev实测正确率。本轮没有Jev场景调用或真实宿主纠偏。

**当时下一步D2（已由上文完成）**：同一entry.run的显式离线profile、一次宿主纠偏、跨turn/episode账本与恢复；
D3/D4真实接线、准入和独立效果验证随后另行冻结。旧6/8例不重跑，默认Skill和main不变，#211仍OPEN。
当前可恢复任务：`tsk_578fb8c8ab5b17bc`。

## 历史 v0.2 交付（原四份审计，已封存）

将 Skills 两轮对象锁与 4K 使用/购前/评论的不同主判断恢复为主验收目标。
方案区分原文、来源事实、用户约束、宿主提案、候选回答；关系检查形成保留/修正/目标/缺口四类纠偏内容。
模型判断不成为事实认证，不预设反对用户、不固定某个产品或解释胜出。代码只执行已声明分支。

两个隔离的新模型上下文（同一已授权DeepSeek型号）对同一冻结材料做首审；v0.2修订后各做一次聚焦复审。
共4次真实审计调用，没有第三轮、没有Jev场景试验。原始审计不可变，所有版本分别保留。
这不是作者角色扮演，也不是统计独立或外部真人审计。复审看到了固定首审意见，但看不到另一个复审的结论。

## 审计证据

- [首审 A](round-1/A/review.md)、[首审 B](round-1/B/review.md)
- [复审 A](round-2/A/review.md)、[复审 B](round-2/B/review.md)
- [首审处置](finding-disposition.json)、[复审作者归因](review-adjudication.json)
- [调用与结果汇总](audit-summary.json)、[来源索引](source-index.json)、[验证](verification.json)

审计完成不是自动通过。剩余G1/G2要把“真正重建主判断”和“多个共同因素如何形成同一个或有条件的结论”做成有判别力的合同；G3补足工程字段映射与之后的独立验证计划。
部分审计修法违反canonical边界，已说明不采纳，例如固定反对prompt carrier、只能有一个决定因素、递归改题、用关键词证明语义正确。

## 恢复与边界

任务 `tsk_2bfdada6228fc895`：仅设计与内部审计交付。#211仍OPEN。
未改运行代码、默认Skill、已有方法/原语、旧试验或main。后续先完成实施关口，不重跑旧6/8例，不另建通用题库或路由平台。
