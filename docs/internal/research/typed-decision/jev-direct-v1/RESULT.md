# ③完整输入准备与容量核验

Owner明确要求Jev直接接收用户请求和完整SKILLS/方法论，不由LLM先摘要或筛选候选。旧②结论保留，③尚未完成路由及效果对照。

已实现full_context.py：完整原文字节、来源路径、SHA-256、用户消息顺序/身份与权限均保留；拒绝摘要、候选预筛、删减和额外评阅字段。新分支experiment/jev-direct-full-context，父版本83dfa80。

完整输入范围：10份skills/*/SKILL.md（含入口和显式case-prep）＋25份docs/methodologies/**/*.md（含认知原语与公开方法示例），共35份，299105字节/206976字符；State308970字节。另导出含所有skills Markdown配套资料的95份资源配置，808981字节/707550字符，未提交供应商。完整参考不等于所有文档均为自动执行目标。脚本、二进制、历史评测不属于描述性正文。

唯一真实容量探针发送完整35份正文、原E首条用户问题和Noul/Choice/Score各一题。请求310101字节，未截断。官方HTTP400，0.336秒，返回`{"detail":{"error_type":"max_tokens_exceeded"}}`。这是服务端容量限制，不是工具拦截、Key失效或方法判断错误；无模型答案，实际token及费用未知。三题是容量探针，不是完整路由题组。

官方https://docs.typesafe.ai/models 声明64k总预算、State加最长题32k。字节不是token。新诊断显式2MiB上限不改变旧transport或服务端限制。文档核查日2026-09-27；原始节点时间2026-09-26T22:27:16Z原样保留。

无损全方法分组并行可作为后续协议：所有方法完整资料都由Jev读、共享认知约束保留、跨方法关系再次带完整相关原文；不由LLM筛选。但这不等于全部文档在同一State中同时可见，未自动切换、未实测。不得悄悄摘要/删文件后仍叫全量单State。

19项新增离线测试及4项生命周期测试通过，共23项，登记97/97；没有重跑旧全仓。新调用仅1次官方容量探针，前置LLM/宿主答题/OpenRouter/CPA为0，未重试，无未知请求。main、默认技能及旧②证据未改。本轮交付输入准备及容量事实，不宣称③已运行。

证据：source-manifest.json、inventory.json、capacity-intent.json、capacity-outcome.json、focused.log。
