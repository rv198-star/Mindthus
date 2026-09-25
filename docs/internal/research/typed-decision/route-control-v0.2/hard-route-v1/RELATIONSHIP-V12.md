# #211 关系复查 v1.2：已定位问题与有界修复

## 发现

原 v1.1 的 `local_transfer` 问题只说检查“显式前提→结论边”。S1/S3 的边定位在用户原话；当前 Codex 已写出否定该错误推论的候选后，边仍引用那段原话。Jev 和普通 Codex 的复查都继续选 `local_overreach`，消费器又无条件把它映射为 `qualify_local_transfer`，形成一轮纠偏后仍要再纠偏的假阳性。这是题目绑定与消费共同造成的设计问题，不能用重试消除。

K3 要评价某回复是否切中当前问题，属于 `explanation`。原消费器在 `readiness=conditional_decision` 且 `delivery=verdict_with_basis` 时，无论题目类型都强制 `state_conditions`；因此即使候选已明确说“没切中”并解释空间/字号冲突，也被要求进一步替用户做条件选择。这是任务层级错配。

## 改动

- 新合同 `relationship-contracts-v0.3.3.json`、政策 `mindthus.relationship-frame.v1.2`。`local_transfer` 明确只判断**当前候选**是否还在推广局部事实；用户原话仅定位待检关系，候选明确拒绝该推论时不再重复报错。
- `definition` 对“某组成部分完全没作用吗”允许有证据约束的功能说明，不要求对所有组成部分做孤立量化归因。
- `state_conditions` 只在当前选中 frame 为 `decision` 时强制；`explanation` 的明确相关性判断不会被改造成用户选项决策。
- v0.3.2 原合同和全部旧账本未改。新代码采用 v1.2；读取原 v1.1 冻结运行须使用其父代码版本，不能把新语义回写为旧回执。

## 验证

与关系评估相关的 139 项测试通过。全仓 1524 项测试在绑定的 Python 运行时下通过，2 项跳过。第一次全仓调用的子进程误用了 macOS 的系统 `python3`，因未接受 Xcode 许可出现大量环境失败；修正 `PATH` 后全套重跑通过，未将首次失败当作代码回归。

对 S1/S3/K3 的旧**错误候选**，新合同各做一次真实 TypeSafe `jev-1.13.0` 判断，3/3 仍要求纠偏。对这三题旧**已纠偏文本**，各做一次独立判断，3/3 均 `continue_original`；S1/S3 的 `local_transfer` 从旧批的 `local_overreach` 变为 `supported_within_scope`。K3 虽仍给 `readiness=conditional_decision`，但解释类消费不再误触发 `state_conditions`。六次 Jev 请求均完成，无重试，无 CPA/OpenRouter；费用字段缺失，按 Owner 口径暂计 0。

新冻结、意图、原始安全回执、用量和逐题矩阵位于：

- `/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v12-original-probe/`
- `/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v12-probe/`

这是**已暴露开发题的定点诊断**，不是新的盲测或完整端到端宿主接管。它证明两个已定位误判在这三题上消失，不能证明 Jev 语义判断有 100% 保证，也没有解决 K2 的提案映射缺项、K1 的预算条件遗漏或 #211 的总体资格门槛。Jev 负责返回结构化判断，当前 Codex 宿主负责编写纠偏；模型输出不自动等于真实世界事实或任务验收。
