# #211 本单周期的显式 OpenRouter 接续（2026-09-26）

用户明确要求先用 OpenRouter 完成测试。父版本 c184467（运行语义 ea05409）；本次只调整固定 Jev 引擎的允许服务路径与 driver 显式配置，不改题文、阈值、来源、默认 Skill 或 main，不读取 TypeSafe 凭据。OpenRouter 只用于 Jev，不调用其他模型。

## 路径与身份

模型 `typesafe/jev-1.13`，接口 `https://openrouter.ai/api/alpha/decisions`。请求模型、实际返回 snapshot、实际 provider、usage 和计时分别保留；同引擎不同服务不声称数值或运行实例等同。旧 TypeSafe root/freeze/账本不可改写；旧代码保留于 `/srv/agentdock/worktrees/mindthus-single-cycle-typesafe-c184467`。

新根目录：
- E：`/srv/agentdock/tmp/mindthus-single-cycle-openrouter-E-20260926`。
- F：`/srv/agentdock/tmp/mindthus-single-cycle-openrouter-F-20260926`。

⓪为正常入口无 Jev；①建议式；②约束式。主运行 E②、F⓪/F②；①不默认增加。E⓪复用已完成的 `/srv/agentdock/tmp/mindthus-single-cycle-E-first-ea05409/results/pure_codex.json`，仅当原始材料、宿主配置、入口正文及无 Jev 语义保持一致；不重生成或改写其来源，时间分离限制如实报告。F⓪使用本次同宿主新会话。

## 输入与预算

E 使用已保存第一条用户请求，cutoff=0/initial，不含范围纠正；不是历史原失败重现。F 使用 cutoff=12/after_user_correction，原图缺失，只做后期快照回归，不证明最初自主识别。源文件及来源窗口由现有 evaluation_integrity 校验。

宿主沿用当前 OCI Codex `gpt-6-sol/xhigh` 与现有配置，不是 CPA；与用户桌面插件环境不能直接等同。每分支4个执行槽、一次复核/纠偏、一次仲裁，原时间及字段规则不变。每新 root 最多4次 Jev，两 root 总上限8次（预留每次0.02美元、总0.16美元），不是额外于本修复周期的8次；此前本周期 Jev 调用数为0。每分支至多8次 CLI。技术/语义不利结果不自动重试、不切模型；未知 intent 先核对，不重新提交。

## 验收与比较

沿用 PLAN.md 及 evaluation_integrity.TARGET_DIMENSIONS。每个来源至多两次独立上下文、匿名 Codex 内容评阅（合计4次；单次240秒），不调用 OpenRouter 普通 LLM。评阅只获原始可见材料、匿名实际最终正文、实际已读入口与方法资料和原逐维标准，不获方式名、Jev 分数、预期赢家或他臂结果归因。

分别报告实际路由提交、被宿主接收的正文、局部未决、全部消费、逐维内容与成本。空答/拒绝/未决保留在分母，不通过缺失文件数或回执形状推断语义正确。评价声明限定为本次两个来源窗口的开发观察；无统计优势、全八方法资格或自动推广。

## 开跑检查

先完成渠道准入反例与当前全仓回归；记录源码 commit、driver hash、旧 E⓪文件摘要与新 freeze。已完基线/旧调用不重跑；没有修改方法和消费者语义的原因不重做前期修复。认证信息只在执行进程环境使用，不进仓库、日志或证据包。若工具层明确拒绝，保存真实结果并停止，不改变传输来规避。
