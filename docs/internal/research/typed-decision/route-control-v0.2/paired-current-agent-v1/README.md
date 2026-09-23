# 六场景对照：当前状态与恢复入口

当前后续诊断与已存内容评阅：[continuation-diagnostics-v1](continuation-diagnostics-v1/README.md)。此链接更新进度，不覆盖历史快照。

## Latest retry checkpoint — 2026-09-23

[Same-channel retry and preserved live records](retry-evidence-20260923/README.md): original command succeeded with eight real Jev requests (six valid typed batches, two local contract rejections). Seven current-Agent replies are staged; the next same-channel continuation was blocked before execution, so no recheck or final paired result is claimed. Prior UNRUN descriptions below are historical snapshots. Runtime and original freeze remain unchanged.


本批场景用A–F，模式用①建议式/②约束式。完整材料、顺序和边界见 [PLAN.md](PLAN.md)。

**已完成清单、9份输入及标准、既有entry调用准入和调用前冻结。已尝试执行；命令被平台安全检查在执行前阻止，没有真实Jev请求或对照回答。**

| 场景 | 输入 | ①建议式 | ②约束式 |
|---|---|---|---|
| A 日常处理 | A1排序、A2通知缺时间 | UNRUN | UNRUN |
| B 单方法诊断 | B1 Agent字段门 | UNRUN | UNRUN |
| C 主辅协作 | C1长期方向/当前路径 | UNRUN | UNRUN |
| D 阶段接力 | D1结构澄清/资源分配 | UNRUN | UNRUN |
| E Skills争论 | E1第二轮快照、E2最小提示反例 | UNRUN | UNRUN |
| F 4K处境 | F1当前使用、F2购前快照 | UNRUN | UNRUN |

没有使用预置答案、历史结果或离线夹具替代本次实测；没有在平台拒绝后换工具、代理、编码或供应商重发。CPA未参与，当前Agent尚未收到执行交接。

## 已核实

- 源提交 `2f2d9d1`；freeze提交 `a016b4c882ae5329f796dbc6217b71db108a7955`；父运行代码 `c3661391f2abcc77226fbf3da8e8b9f68013120c` 未改。
- 9个精确输入/准入已编译，运行指纹和输入文件hash与freeze一致。
- 最多12次Jev请求，单次预留0.02美元，共0.24美元预留；不是实收费用。
- 唯一实测命令被拦截；目录不存在，供应商intent/outcome各0，Jev/CPA调用各0，宿主交接0。
- E/F是已暴露历史快照回归；两臂共享当前会话背景，不是独立双盲或因果收益证明。

## 恢复

任务 `tsk_33474a9c1917c41c` 的freeze完成，execute被平台阻碍。恢复前核对 `execution-attempt.json`、`freeze.json` 和实时ledger；未知外部调用不得重发，已知宿主等待只消费原请求。

下一步仍是这批真实端到端和配对消费对照，不另设计题组、不重开旧CPA批次。仅在平台允许的条件下继续。没有输出前不评价①②孰优，不报告通过率。

本轮未改默认Skill、方法正文、运行代码、main，也未重跑无关全仓测试。
