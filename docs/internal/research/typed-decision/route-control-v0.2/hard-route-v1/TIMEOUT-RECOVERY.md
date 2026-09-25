# #211 普通 Codex 路由超时补充对照（2026-09-25）

## 结论

Owner 允许把原 B 路由的两次超时当作技术问题补做对照。补充已完成：S1 原 CLI 事件中已有完整、符合 schema 的模型答案和 `turn.completed`，只是进程未在 44 秒内退出；本次从原字节恢复该答案，不重发初检。K1 原事件只有 `thread.started` / `turn.started`，无答案；本次用相同问题、材料和 schema 做一次新请求，技术等待窗口放宽至 100 秒。原 Episode、失败回执、C/Jev 结果均保持原样。

S1 恢复的普通 Codex 判断触发了一次纠偏；纠偏文本正确限定发票脱敏 Skill、样本拦截和零遗漏证据边界，但普通 Codex 的复查仍判 `local_transfer=local_overreach`，要求再次纠偏，按一次纠偏边界退回。K1 的新初检在约 41.08 秒内完成，判 `q0=material_omission`，因此没有纠偏。S1 的新复查约 41.24 秒。新增普通 Codex 调用共三次：S1 纠偏与复查、K1 初检；新增 Jev 调用 **0**。

因此原同图配对在消除技术超时后，普通 Codex 的宿主放行仍是 **1/6**，Jev＋Codex 仍是 **2/6**。这个数量差本身不等于 Jev 判断更准：K1 的提案没有显式承载预算未知，Jev 放行的纠偏文本也漏了这一条冻结要求；B/C 在映射完整性上的分歧需要独立核对。补充的直接纯 Codex 基线仍为原候选判断 6/6 正确拒绝、严格逐项 5/6 完整。本批 AI 合成开发题没有证明“整体不输纯 LLM 且难题有明显增益”，#211 仍未通过。

## 审计边界

- 补充脚本：`retry_comparison.py`，执行前固定于提交 `115d35209`。它验证新请求的初始 prompt SHA-256 与原超时调用完全一致，schema SHA-256 也一致；S1 须在原事件中出现 `turn.completed` 才可恢复。
- 新冻结、原失败引用、完整判断矩阵和原始模型调用账本：`/Users/william/Documents/Codex/2026-09-25/mindthus-hard-route-v1/timeout-recovery-v1/`；新增调用原始事件在同级 `codex-calls/` 的 `*-timeout-recovery-v1-*` 目录。补充是独立、来源绑定的消费，不冒充原 `relationship_runtime` Episode 已成功。
- 补充没有重试成功的旧请求，也没有改动旧超时 `outcome.json`、Jev 原始返回、原宿主回执或预算。S1 原调用仍记 `timeout_unknown_billing`；其实际写出的完整答案只作为补充恢复证据。实际费用未知，按 Owner 口径暂计 0。
