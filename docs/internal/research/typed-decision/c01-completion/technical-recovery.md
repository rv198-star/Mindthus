# 一次客户端标识技术修复

初始冻结源码9d1f97774，首项L27收到ProviderError:http_403，0.598538秒；无答案/usage，
其余4项未执行，Jev调用0。原trial和freeze.json保持终止，不覆盖、不计为语义失败。

对同一CPA /v1/models做两次不带key的只读诊断，仅改变User-Agent：
Python-urllib/3.12返回403纯文本；Mindthus-C01-integration/1返回401 JSON（鉴权层）。
上一轮六次成功宿主调用使用后者，新c01_host入口遗漏了它。证据支持客户端标识影响
访问层；不能从这些状态码断言具体WAF策略或账单是否为零。

本次仅恢复已有成功请求的User-Agent，不修改题目、模型、host messages、Jev问题或标签。
原失败记录保留；独立技术恢复根trial-user-agent-recovery-1最多再5次CPA+3次官方Jev，
仍按原固定5项顺序、原评分、零语义修订、零自动重试、零模型切换执行。
两轮累计上限6次CPA+3次Jev；Jev预留上限USD0.008064不变，CPA总费用未知。
任何新的技术失败终止该恢复，不再追加技术重试。此次不是“迭代到答对”。

recovery-freeze.json绑定修复后的源码、原protocol和本文件；freeze.json保留初始身份。
run的显式freeze_path参数只选冻结证据，仍要求逐项精确匹配且不接受已有trial根。
先完成修改相关离线/全仓检查并单独确认退出码，再提交源码，再执行一次恢复。
本次交付仍服务可用的实验入口，不增加框架或扩大#211语义资格。
