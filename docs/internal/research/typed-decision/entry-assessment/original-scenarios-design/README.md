# Skills / 4K 入口：合同完善与 Relationship D1

**当前：D1离线实现完成；独立快速设计审计REVISE但允许offline D1，作者局部处置后按v0.3.1开发。不是全面审计PASS或真实效果验证。**

先读 [D1合同处置与实现边界](D1-contract-resolution.md)，再读 [设计v0.3](design-v0.3.md)、
[实际机器合同v0.3.1](relationship-contracts-v0.3.1.json)、[验收v0.3](acceptance-v0.3.json) 和
[D1验证](D1-verification.json)。实现源码 `experiments/typed_decision/relationship_assessment.py`。

本轮一份真实独立上下文 [快速审计](quick-audit-v03/review.json) 与 [作者处置](quick-audit-v03-disposition.json)
分别保存；原被审v0.3未修改。43新离线测试、全仓1324项（1319成功/5跳过）通过，生命周期83/83。
14个语义判例是作者预期，不是Jev实测正确率。本轮没有Jev场景调用或真实宿主纠偏。

**下一步D2**：同一entry.run的显式离线profile、一次宿主纠偏、跨turn/episode账本与恢复；
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
