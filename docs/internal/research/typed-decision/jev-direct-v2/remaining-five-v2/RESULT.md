# B1首层真实传输失败；发送状态未知，剩余批次未完成

执行源码固定提交：`71bd3b7a4dfc635563c0d4845efb5c61c3058a16`。
执行前通过 `git ls-remote` 确认父远端为 `11404c0c0d6170ecc05657c1acd9d63d462188d0`。
本轮已经正常启动 B1/direct 官方 Jev 首层，随后遇到实际传输错误。
不是只做配置解析，也不是沿用历史拒绝作出的谨慎暂停；没有观察到新的安全或权限拒绝。

## 本次具体阻塞及原始证据

- 操作：`POST https://api.typesafe.ai/v1/systemone`，`jev-1.13.0`，B1/direct第一层，原始输入、全10张目录卡片、71题。
- 调用键：`61784cbf0798ceba12ce2b8dcf0c90a97799011df3848a5904ac0cc9f595a31c`。
- 意向时间：`2026-09-27T14:42:30.102682+00:00`。
- 请求上下文摘要：`51ef46018348dc8a28aa9cce14a66d49271d794b71fb07dc2ccde6f9fe29b046`。
- 原始保存错误：`ProviderError:transport_failure`。71项 `provider_error` 是同一次调用错误的传播，不能计成71次调用。
- 层级：现有 Python HTTP transport；尚无供应商响应 receipt。
- 本地 evaluate 已结束，但没有可绑定的远端终态或未受理证据；生成负载是否发出仍 unknown。
- 全局账本 `serial/000004` 保留意向，未伪造 completion；校验返回 `serial_unknown_request_no_resubmit`。

[真实请求](evidence/runs/B1/direct/route/level-1/request.json)、
[调用意向](evidence/runs/B1/direct/route/level-1/journal/calls/61784cbf0798ceba12ce2b8dcf0c90a97799011df3848a5904ac0cc9f595a31c/intent.json)、
[实际错误 outcome](evidence/runs/B1/direct/route/level-1/journal/calls/61784cbf0798ceba12ce2b8dcf0c90a97799011df3848a5904ac0cc9f595a31c/outcome.json)、
[串行意向](evidence/serial/000004/intent.json)、[本轮执行 checkpoint](evidence/remaining-five-checkpoints/B1-direct.json)。

原适配器把 URLError、TimeoutError 和 socket.timeout 统一保存为 transport_failure，
没有保留底层异常细节。不能将约8秒耗时、当前进程结束或泛化错误解释成发送前失败；
也不能把它写成 HTTP 401、安全拒绝、已确认 TLS 失败或明确远端结束。
本地 checkpoint 的 `RecoveryRequired` 是安全化后的异常类名；上述追加观察补充了实际账本错误，
没有改写原 checkpoint、原 outcome 或发送意向。

按照已采用的 generation-scheduling.v2，本批不能在未知生成工作之后继续派发。
因此 B1没有第二层或宿主，B1/native及其后八条路径未发送。没有改题、换渠道、换根、清除意向、
补造答案或对失败重试。影响范围是同一批次后续派发，不是一个泛化的全项目安全暂停。
继续所缺的是能绑定到这次请求的供应商或既有传输记录，证明未受理或明确终态；
当前没有这项证据，也不假定某个特定名称的恢复文件或复核接口存在。

## 十二条路径状态与答案

| 场景 | native | direct |
|---|---|---|
| A1 | 已交付、内容正确；保留旧执行限制 | 已交付，协议v2；一层、无具名方法 |
| B1 | 未发送，同批未知调用阻塞 | 本地传输失败；远端发送/终态未知；无答案 |
| C1 | 未发送，同批未知调用阻塞 | 未发送，同批未知调用阻塞 |
| D1 | 未发送，同批未知调用阻塞 | 未发送，同批未知调用阻塞 |
| E-window | 未发送，同批未知调用阻塞 | 未发送，同批未知调用阻塞 |
| F-window | 未发送，同批未知调用阻塞 | 未发送，同批未知调用阻塞 |

A1两份原始正文均保持：

```text
apple
pear
plum
```

[已固定入库的两份A1答案及终态](../a1-direct-transport-v2/RESULT.md) 未改写或重跑。
本轮其余路径没有真实答案；不存在可以报告的B–F实际方法选择、作用范围、主辅/先后关系、
加载材料或路由异议。B1供应商错误不被转成“选择direct/无方法”的有效判断。

## 分层计数、时间和预算

| 本轮项目 | 实际记录 |
|---|---:|
| Jev逻辑调用 / transport调用 | 1 / 1 |
| 宿主CLI启动 / 外层重试 | 0 / 0 |
| 可观察内部恢复 | 0 |
| 实际底层HTTP数、生成尝试数 | unknown |
| 已取得模型返回 | 0 |
| 未解决逻辑调用 | 1 |
| 主动等待 | 60.005245s |
| 冷却单调间隔下界 | 60.005364s |
| Jev evaluate至本地错误 | 7.987117s |
| 宿主会话 | 0s（未启动） |
| B1/direct路径墙钟 | 68.182495s |
| 本轮完整执行墙钟 | 68.190610s |
| 其他装载/校验/记账残差 | 0.198248s |
| 纯HTTP、认证/连接恢复、远端生成耗时 | unknown |
| input/output token、金额 | unknown |

累计宿主CLI仍为 A1/native 2次、A1/direct 1次；其他路径0。
Jev业务原有A1成功1次，加本次B1未知1次，累计尝试2次。
B1首层已消耗一次尝试，不能因失败或登记后继而恢复额度；宿主4次/900秒均未动用。
其余路径原额度保持。未使用的Jev层数并不授权重发未知请求。

## 配对条件与交付范围

[追加范围登记](SCOPE.md) 及 [实际后继记录](evidence/remaining-five-scope.json)
引用原传输后继和未修改的 `mindthus.generation-scheduling.v2`；历史“A1/direct only”记录不改写。
新范围摘要：`761741c53cfd32b525db9f01e2f6647c9ee83f7f33ce1fb04b24f223a4bb199e`。
新增代码只接入这个追加范围及其父身份校验，未改公共调用、CLI、schema、串行冷却或路由逻辑。
原输入、卡片、71题、阈值、材料、模型与候选覆盖配置均保持；B–F若继续，使用同一固定源码和配置。
本轮宿主未启动，因此没有新的宿主配置生效事件，不冒称十条路径已验证匹配。
A1不同传输条件的耗时继续排除；B–F没有完成配对，无法计算质量差异、速度或成本改善。

[完整机器摘要](summary.json)、[35文件证据索引](evidence-index.json)、
[执行驱动副本](execution-driver.py)、[最小范围接线验证](scope-validation.log)。
所有旧证据摘要保持，未重开R2、未跑全仓审计、未重做配置解析或鉴权探针，未启动模型评阅。
工程范围登记完成；真实传输发生错误；答案交付未完成；质量/净收益均无新结论。
