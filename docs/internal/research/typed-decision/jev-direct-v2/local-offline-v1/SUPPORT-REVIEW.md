# 平台支持/正规审批的最小复核材料

## 被拒操作与用途

Mindthus #211，六个既有低风险、只读开发案例比较原入口⓪与两层 Jev 直达入口③。官方 Jev 根据原始任务、方法卡片和 71 道类型题做路由，Codex 生成文本答案。不开启外部写入、交易、真实案例导出或产品默认路由。

历史操作：在 OCI 节点启动 `experiments.jev_direct.pilot` 的冻结正式业务；记录包括 B1③官方启动被工具安全检查拒绝。具体触发规则未知。此处不提供替代启动通道，不重发请求。

## 目标服务与最小权限

- TypeSafe：`POST https://api.typesafe.ai/v1/systemone`，固定模型 `jev-1.13.0`；本地已授权 TYPESAFE_API_KEY 只应进入请求认证头，不进入证据。
- Codex：本地 CLI 的现有 OpenAI 登录配置，模型请求 `gpt-6-sol/xhigh`；实际服务端模型身份需要回执确认。认证文件仅检查存在性，没有复制或读取认证内容。
- 本地只读访问冻结原始资料、Skill/方法正文和 schema；仅写新试验目录的提示、返回、账本与时间记录。原 freeze、main 和旧证据不写入。
- 不调用 CPA 或 OpenRouter；不要求关闭审批、绕过安全检查或降低沙箱设置。

## 发送数据范围

六个既有开发输入：字母排序、Agent 形式/事实验证、方向与具体承载、结构选择及六人日分配、Skills 首轮原文、4K 晚期缺图对话。包含原用户/助手/来源文本、顺序、来源标识和权限描述；未包含缺失原图，也未补造。

Jev 首层同时提供全部十张入口卡片、八种可路由方法、六项认知描述及 71 题。可选第二层最多读取两主题原 Skill/方法正文，仍保留原文与卡片，最多一次。Codex 原入口可正常申请原方法；③只消费 Jev 路由及对应原文。

脱敏实际请求在 `offline-evidence.tar.gz` 的 `requests/`；认证头完全省略。`verification.json` 与 `evidence-index.json` 提供版本、输入哈希和逐文件校验。`fixtures/` 是合成响应，不代表真实调用或未来路由。

## 已有拒绝证据（保留原始身份）

- `../blocked-launch.json`：原业务启动阻塞记录。
- `../channel-retest-v1/RESULT.md`：官方小探针成功、正式业务启动被拒的区别。
- `../channel-retest-v1/evidence/business-outer-plans/B1-direct.json`：脱敏外层拟调用参数，不是服务端 trace。
- `../channel-retest-v1/evidence/business-reconciliation.json`：十二业务路径均未进入的核对。
- `../channel-retest-v1/evidence/tool-observations.json`：操作者转录的工具结果；平台 trace ID 未提供，不冒称完整平台内部日志。

已记录拒绝文字：“此工具调用被 OpenAI 的安全检查屏蔽。请仔细检查你发送的内容。”本轮没有再次提交该业务来试探拒绝条件。

## 请平台复核的问题

请确认被拒的是哪项操作/数据范围/权限，是否有获准的明确恢复条件，及是否存在可关联的请求或审核编号。不能凭最小探针成功、换主机或用户口头授权推断拒绝已撤销。

本材料仅供复核，尚未发送到任何外部支持渠道。实际业务保持 UNRUN。
