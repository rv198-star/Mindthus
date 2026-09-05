# 方案审计 A：合同与测试保护

日期：2026-09-05
对象：docs/internal/maintenance-20260905-plan.md v1.1
源码基线：1de31845cce25126651231d51047564eb055e1da
载体：本会话 ChatGPT 自身；按用户最新指令执行。非外部 reviewer、非新上下文。

## 审计问题

依赖授权修复是否引入错误的完成判断？结构统一能否覆盖真实接收入口？测试清理是否以数量取代保护价值？

## 检查与发现

1. 查看 sra_runtime_core 的候选校验、Schema 生成和 judgment 接收逻辑：现有 depends_on 只检查 ID 引用，不能证明前置满足。v1.0 草案的五状态 waiver/substitute 容易在没有权限载体的情况下增加伪授权通道。v1.1 收敛到 satisfied/unmet/unknown；替代/豁免暂不建立新的 runtime 例外。已完成前置仍可零投入。
2. satisfied 的 evidence_refs 合法不证明事实真实。方案保留 Agentic 语义判断，Workflow 只检查边覆盖、引用及授权后果。当前资源与下一 tranche 都受前置约束，不能只检查后者。
3. 必须区分“前置列在组合里”和“前置已完成”。选择 B 且 A 未满足时不能立即投 B；选择 A 先做可以合法；conditional 仅保留计划，不授予当前投入。
4. Schema 已使用 oneOf/anyOf/not/pattern 等约束。只检查根字段不足，结构解释器必须拒绝不支持的 Schema 关键字，错误结构先返回而不送入假定类型正确的领域逻辑。
5. 没有依据把所有旧测试归为无效。沿用 lifecycle 逐项替代台账；安全/权限/恢复回归保持；故障变体用于证明替代 owner 真能捕获原风险。
6. 新字段对旧 run 的行为变化必须可见。无依赖 v0.3 结构保持；有依赖而缺解析记录明确不足，准备新 run，禁止 Repair 改造原始权威。

## 结论

v1.1 已纳入上述收敛，方案允许进入分项实施。实施代码仍需反例和正例验证，方案通过不等于产品修复通过。遗留子项不能因为父计划被接受而自动关闭。

Verdict: PASS for implementation planning, with explicit implementation gates.
