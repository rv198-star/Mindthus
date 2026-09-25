# Runtime support：①来源异议的回复与消费

主路径：原宿主给出实际文本，并声明当前用户任务在这些限制下能否交付。运行时核对字段/引用、保留限制、传递给候选检查及最终接收；不替宿主判断缺失事实的重要性。

执行回复保留原 `route_id/revision/issue_id/performed_methods/text/objection/usage`。
①新增可选字段 `advisory_status`：

| 状态 | 含义 | 后果 |
| --- | --- | --- |
| answer | 无具名异议，正常答案 | 必须有正文，继续检查和接收 |
| bounded_answer | 来源/范围或方法边界使结论有限，但当前任务有可交付答案 | 必须有正文和合法异议；把异议及来源随答案交给最终原宿主 |
| unresolved | 必要事实/权限缺失或仍不能作答 | 合法接收回复，保留未决；不能签发成功接收，独立事项可继续 |

兼容旧回复：objection=null 且无新字段，沿用 answer；有 objection 且无新字段，保守视为 unresolved。
因此旧封存原文不再因“非空异议”直接被合同拒绝，也不会被脚本擅自解释为已解决。

Guardrail：bounded_answer 只防止“辅助未知被误当成完全不能答”这一主路径误用。
它不能覆盖 permission/dependency/new_fact 异议、原宿主已确定的 acquire_fact 前提或未接受的依赖。
权限/依赖/新事实异议必须保持 unresolved；错误引用/版本仍拒绝。
同一回复带异议时不能同时为依赖产物签发接受凭据。

引用检查：至少一条真实 user/source 引用；可以同时保留准确绑定的历史 assistant 引用，说明此前争议。
历史助手转述不升级成原始事实。检查所有引用位置/hash，而非只检查主引用。

输出中的 `advisory_objection` 保存原 objection、disposition 与 host_context_ref；最终接受请求的
`evidence.advisory_objections` 完整转交。接受仍绑定当前正文 hash，原宿主可拒绝。
bounded_answer 不保证语义正确，也不自动证明任何外部事实；②合同保持不变。
