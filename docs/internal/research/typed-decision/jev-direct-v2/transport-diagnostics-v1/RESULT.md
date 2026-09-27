# 传输诊断定点修复；B1旧unknown未解除

基线：`6b21dc333ef49da1e866a1690d0ad89af05c1901`。
本轮新增模型请求0、鉴权/网络探针0；未改变generation-scheduling.v2，未启用技术补试。

## 最小实现范围

保留 `transport_failure`、`http_NNN`、`invalid_json` 等兼容错误码。
`ProviderError` 新增独立diagnostic属性。仍用标准库urllib、同一官方服务、同一认证及TLS验证；
仅在原HTTPS连接的connect/send/getresponse边界观察阶段，未更换客户端栈或添加重试。

- 类型来自固定异常类别；仅保留有界整数errno、SSL错误码及证书验证码，不保存异常消息、repr或traceback。
- 阶段只来自实际进入的连接建立、请求写入、响应头等待、响应体读取边界；最多保留16个阶段事件。
- 仅在本次 `HTTPSConnection.connect` 明确抛错且生成HTTP写入尚未开始时标记pre_send；代理CONNECT/TLS属于连接建立。
- 普通URLError即使reason是ConnectionRefusedError，若没有上述实际阶段观测也仍为unknown。
- 本地write返回、响应读取超时、进程退出均不证明供应商受理或远端完成。
- 收到完整响应头时记录HTTP状态。关联头仅允许x-request-id、request-id、x-correlation-id、cf-ray；值最长256字符且只保存SHA256，避免头值反射凭据。没有保存原始响应头、Cookie或Authorization。
- `_http_worker`通过原有Pipe传递结构化诊断；父进程原样附于ProviderError。
- `Session`将诊断写入独立、不可变的 `calls/<call_key>/transport-diagnostic.json`，绑定call_key、意向摘要、context/questions摘要及实际canonical请求body摘要、开始/结束时间。原outcome结构保持兼容。
- 父进程deadline或EOF只记录父进程实际观察到的等待/退出错误，子进程未知阶段不猜测。

诊断不构成调度解除指令，serial/000004及其他恢复约束没有改变。新代码会改变实现摘要；
没有将其登记为已获准的业务重跑身份，也未改写旧冻结、预算或后继。

## 受影响验证

[测试日志](tests.log)：25项通过，其中7项新离线反例覆盖：
明确connect拒绝、SSL安全码、收到响应后的读取超时、HTTP错误与脱敏关联标识、
缺少阶段观测不能声称pre-send、真实fork/Pipe到Session落盘并绑定、父进程deadline仍unknown。
跨进程测试使用含测试凭据的异常消息与认证头，确认全部落盘JSON没有凭据；
HTTP响应测试同时向白名单ID和Cookie放入测试凭据，只留下允许ID的摘要。
其余是原provider映射、旧outcome回放、意向不重发、错误不泄密及deadline的受影响回归。
未重复全仓审计、R2、配置解析或业务效果评阅。离线通过不等于真实供应商诊断已验证。

## 旧B1一次有限检查

[检查记录及12份原文件摘要](old-B1-inspection.json)。范围限定为B1/direct的既存案内文件、
serial/000004及其独立锚、关联checkpoint/执行/观察记录；全部与基线已提交证据一致。
没有provider receipt、底层诊断或serial completion；唯一保存的错误仍为
`ProviderError:transport_failure`。**现存材料不能进一步归因**。
不制造探针，不把新离线反例作为旧调用未发送的证明。

尚未解决的逻辑调用：
`61784cbf0798ceba12ce2b8dcf0c90a97799011df3848a5904ac0cc9f595a31c`，B1/direct首层。
其发送、受理与远端终态仍unknown；旧意向、outcome、serial/000004和已消耗一次尝试完整保留，
没有补写completion。A1两份实际答案保持；旧native底层尝试数/状态的既有不可观测限制也未追溯消除。

Owner尚未确认“一次B1技术补试、额外最多1次Jev额度、保留按需第二层”的建议；
本轮没有将它写入生效协议或执行。工程修复完成不改变B1无有效路由/答案的事实。
