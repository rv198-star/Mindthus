# 合同修复与维护优化：执行方案 v1.1

日期：2026-09-05
计划：mindthus-maintenance-20260905
基线：1de31845cce25126651231d51047564eb055e1da

## 授权与范围

用户批准：修复 SRA 依赖授权和结构合同；清理重复/过期测试；按职责拆分 SRA、TPlan 大脚本；归档历史基准逐调用材料。用户本轮明确使用 ChatGPT 自身开展两轮审计，不要求额外 CLI 或独立模型。审计如实标记为同一 ChatGPT 的两个审查阶段，不声明认知隔离或外部模型通过。

本轮创建并维护 issue，按事项提交与验证。代码合并仍须满足各项出口。版本、发布、业务效果研究、路由改造和 Git 历史重写均不在本轮范围。

## 顺序与工作包

| 标识 | 工作 | 出口 |
|---|---|---|
| C01 | SRA 同一输出 Schema 驱动接收结构检查 | 根/嵌套未知字段、缺失、类型、分支被正确拒绝；有效模板通过；拒绝无写入 |
| C02 | 依赖满足与授权 | 未满足前置阻断立即投入；已完成前置零投入合法；多级依赖和两视图别名一致 |
| M01 | 测试清理两波 | 逐项台账含旧断言、保护对象、替代 owner、失效变体验证；不按数量达标 |
| M02 | SRA 按职责抽取 | schema/结构、依赖、比较/投影、carrier 与核心解耦；公共入口不变 |
| M03 | TPlan 分片拆分 | 先纯函数和展示，后 provenance；事务/锁/权限最后处理，不与大批退役混合 |
| #145 | 历史逐调用材料归档 | 先 inventory-only、恢复和引用复核，后批准集合迁出 HEAD |

缺陷、纯重构、退役、归档各自独立提交，不能以一个整体 PASS 掩盖未完成工作包。模块拆分允许按片交付并在 issue 中保留余项。

## C01 唯一结构合同

复用当前 SRA 输出 Schema，以有界的标准库结构解释器校验当前使用的 object/array/type/required/properties/const/enum/oneOf/anyOf/not/长度/范围/唯一性/pattern 关键字。未知 Schema 关键字使检查失败；不声称实现完整 Draft-07。结构不合法先返回，领域检查随后执行。Coverage/Challenge/Situated/Reconciliation 使用相同入口，record/check/repair 经现有 validator 复用。Workflow final 保持从已校验 judgment 确定性重建。无未知字段自动丢弃或静默纠正。

## C02 依赖语义

依赖边只来自 packet 的 depends_on。每条边的判断记录绑定 dependent/prerequisite、状态、证据和理由。初始支持 satisfied、unmet、unknown；satisfied 必须有 packet 中的证据引用。引用存在仅证明引用合法，语义满足仍由 Agentic 审查负责。替代或豁免不能由 Agent 随便填字符串获得权限；本轮不新增通用 waiver 控制通道，来源若未在合法输入中消除原硬前置，按 unmet/unknown 处理。

当前资源和立即下一批次的每个候选，其硬前置都需要已满足；把前置选入 Bundle 不是完成证据。已满足的前置可以没有当前投入。前置未满足时可以先投前置，或为后续给 conditional 并明确启动条件。没有依赖的既有 v0.3 判断结构不变；有依赖但缺少解析记录的旧判断只能诊断为不足，需从来源准备新 run，Repair 不补造权威。

新解析字段进入 Challenge 别名转换、比较和 reconciliation 证据集合。依赖图检查按已满足边截断，避免把已完成历史链误判为当前死锁。未满足闭环不能产生立即授权。

## M01 测试

保留既有 lifecycle registry。旧测试需有可核对的不变量与替代覆盖；表格参数化保留案例标识和失败定位。当前 CI 数量与静态 test_* 数量分别报告。事务、隐私、权限、数据损失、恢复和已知缺陷回归不按年龄清理。第一波只收敛明确重复的静态/打包断言，第二波整理拆分后的 owner。测试数和耗时是观测，不是删除目标。

## M02/M03 拆分约束

一个错误类型、一个锁、一个事务 owner。纯函数先提取，保留实际公共 import 入口；内部依赖明确，不用复制实现或循环回导制造小文件。代码移动和行为修复分开。测试需确认 fault injection 命中新 owner。TPlan read_mission 的锁内恢复仍归持久化。新实现模块加入 required_scripts 与 fingerprint_files，并验证丢失/篡改检测。物理拆分会改变 fingerprint，不能为旧 Mission 绕过现有 provenance 检查。

## #145 归档

复用 issue #145。源钉住 v1.9.1 peeled commit d735d11c14d92325607fe6b844eb29f7c426df62。范围 docs/benchmarks/runs/；原统计 6493 文件，逐调用候选 6241，报告/汇总等至少保留 202，50 个 judge-output-schema 默认保留。

先形成可重放的逐文件清单（path/blob/bytes/disposition/reason/recovery ref），核对依赖它们的报告、测试、脚本。材料性例外默认保留。完整 source tree OID 可作为清单来源锚点，但不能只给一条“去历史找”的模糊说明。新临时目录真实恢复比对后才删已批准集合。引用既包括 Markdown 链接，也包括 code block 和程序路径。当前 CI 不依赖联网拉历史材料。保留所有旧 commit，禁止 filter-repo/force push/移动已发 tag。

## 出口

每个工作包：基线、复现/保护、实现、定向复审、聚焦测试、全套 unittest、lifecycle、全布局打包、diff 检查、独立提交、issue 状态更新。使用已验证的 Python 3.10+ 解释器，分别报告执行/通过/跳过。外部模型和宿主实测未运行就不声明。
