# A1⓪ native：实际答案已交付，CLI 内部重试留下执行合规限制

代码固定提交：`0659bc5d7e08c82998ff3a507b4870651186241c`。基线：`ae8787084e39e2b4cfbd4a6570ab792fb3764815`。
分支：`experiment/jev-direct-full-context`；本轮未修改 main。

A1⓪实际状态：**已交付**。格式已被当前 API 接受；宿主已返回；本地完整 schema 与方法加载一致性检查通过。原题逐字检查也符合，但本次不能同时认定请求级串行/冷却合规通过：CLI 内部出现自动重试，见下文。没有 Jev、其他场景、内容评阅或第二次操作员调用。

## 真实原始返回

原题：把下面三个词按英文字符字母顺序排列，只返回三行：pear、apple、plum。

原始 `reply.json`（未补写、未改答案）：

```json
{"action":"answer","read_paths":[],"route_objection":"","text":"apple\npear\nplum","used_methods":[]}
```

其解码后的真实 text 有两处换行，共三行：

```text
apple
pear
plum
```

原始文件：[reply.json](evidence/runs/A1/native/host/1/reply.json)。宿主意向、完整输入、发送 schema、完整本地合同、stdout/stderr、outcome 和会话时间在同一目录。终态绑定见 [success observation](evidence/technical-retry-success-observation.json)。

- 线程：`01a0e301-2b01-7390-afd3-7e9fca05bfab`；轮次：`01a0e301-2b98-7800-864f-07a02f092db6`。
- 请求摘要与旧失败完全相同：`0e8c33f9e1975135c5306821ae5ebbf4a95d1964833cd1032120c3d246de9910`；原输入摘要 `f1fb54fde97adeee66ccb0bbbd2b8d90978a6342f882052b0f5ee5d55e4bfdb9`。
- 两次都请求 `gpt-6-sol/xhigh`，同一已登记二进制和宿主配置。新档案的 turn_context 确认请求配置；服务端实际型号的独立证明仍未观测。
- 正常入口、目录与可读路径保持原请求内容，used_methods=[]、read_paths=[]；没有后续读取调用。

## 旧失败对账和新旧 schema

旧请求的 `invalid_request_error / invalid_json_schema / text.format.schema` 与 `last_agent_message=null` 已通过原始 UserMessage、session/turn、工作目录、请求/提示词/schema 摘要可靠绑定，登记为**已确认格式失败**。旧 28.518 秒仍是归档宿主会话耗时；纯 HTTP 耗时、旧 token 和费用未知。

旧意向、错误正文、终态、schema、冻结全部保留且原文件摘要一致。追加 [reconciliation](evidence/runs/A1/native/host/0/reconciliation.json)、[原始失败绑定](evidence/runs/A1/native/host/0/schema-failure-receipt.json)、[串行 failure](evidence/serial/000000/failure.json) 和独立摘要绑定。没有删意向、伪造成功 completion 或用其他线程错误解锁。

[技术后继身份](evidence/technical-successor.json) 在原运行根、原串行账本上登记，父冻结摘要仍为 `2701fad01df0d3f192fe9507dac1508fc554697ab42391a5476034585c8fc3b8`；没有改写旧 hash 或新建运行根恢复额度。原 4 次宿主调用上限下，重试前已用 1、余 3；本轮新增 1，按冻结的宿主 CLI 调用计数累计 2、余 2。底层远端请求尝试数无法据此确定，不能把“余 2 次”解释成已核实的底层请求余额。

本地合同 SHA：`8b819c765eaee80278ec236f3fd4369cd366b5967002ab692f025abd6175ddd3`。
API 发送 SHA：`6f6afd070a41f9c02bcba12b489dc576ea59ffe1e0b59c29cef1c0e016fc2861`。
[差异](schema.diff)只有 read_paths、used_methods 两处 schema 级 uniqueItems；完整合同不变。两臂共用发送投影，本轮仅实际调用 native。[定点代码 diff](SCOPED.diff)、[修复说明](REPAIR.md)、[56 项相关测试原始日志](related-tests.log) 均已入库；测试通过与真实 API 接受分别记账。

## 实际次数、时间和费用

| 项目 | 新调用实际记录 |
|---|---:|
| 操作员/driver 新启动宿主 CLI | 1 |
| 原账本累计宿主 CLI / 4 次上限 | 2（旧格式失败 + 新交付） |
| CLI 内部采样重试日志 | 5 |
| 底层远端请求/实际在途数 | 未知 |
| 主动冷却等待 | 60.007606 秒 |
| 串行间隔保守下界 | 60.008276 秒 |
| 输入/身份验证及装载 | 0.195241 秒 |
| 新 CLI 会话墙钟 | 119.215100 秒 |
| 新归档 task duration（不同计时边界） | 111.551 秒 |
| 宿主 dispatch 墙钟（含等待） | 179.259121 秒 |
| 操作员 Python 区间完整墙钟 | 179.465908 秒 |
| `/usr/bin/time -p` 完整命令墙钟 | 179.60 秒 |
| 其余 Python 本地开销（差额） | 0.047961 秒 |
| 新输入 / 缓存输入 / 输出 token | 23711 / 0 / 84 |
| 纯 HTTP 耗时 / 新旧费用 / 旧 token | 未测量，保留未知 |

原失败归档耗时 28.518 秒、原完整命令 30.22 秒未改变。预算保守扣除旧完整墙钟 30.22 秒和新 CLI 会话 119.215100 秒；900 秒宿主预算按该口径余约 750.564900 秒。读者不要把不同计时边界相加后冒称纯推理或纯 HTTP 时间。机器可读记录见 [timing-and-counts.json](timing-and-counts.json)。

## 新观察到的 CLI 内部重试限制

实际宿主 CLI stderr 有 **5 条 `retrying sampling request`**，stdout 有 4 条 `Reconnecting... 2/5` 至 `5/5 (request timed out)`，随后 `Falling back from WebSockets to HTTPS transport. request timed out`。另有预热连接 `tls handshake eof`。这些是连接/超时观测，不是安全拒绝；最后同一线程/轮次有真实成功终态和答案。

这是原正常 CLI 在一次进程调用内自动进行的采样重试与传输回退；操作员没有再次启动宿主、改模型/供应商、换安全设置或改字段追试。但现有批次 scheduler 只包围整次 CLI 调用，**没有给 CLI 内部重试逐次施加 60 秒间隔，也不能证明每次超时后远端已经结束**。实际内部请求数、重叠情况及各次分项耗时未知，严格的请求级串行/冷却验收不能记 PASS。`outcome.automatic_retry=false` 仅描述外层 driver，不代表 CLI 内部没有重试。

该限制连同原日志原样交审：[execution caveat](evidence/technical-retry-execution-caveat.json)、[CLI stderr](evidence/runs/A1/native/host/1/cli.stderr.txt)、[CLI stdout](evidence/runs/A1/native/host/1/cli.stdout.jsonl)。发现后没有改设置、修代码再发或启动其他路径；R2 已关闭的四项工程结论保持原结论，不把本次 CLI 内部行为伪称旧四项回归。

## 交付边界

工程相关验证：56 项通过。API 格式接受：是。实际模型返回：是。答案交付：是。A1 字符顺序与三行要求：逐字确定性检查符合，未调用内容评阅。请求级运行纪律：因上述内部重试无法认定通过。质量提升/净收益/两臂对照：未测定，本次不作结论。

A1/native 已交付（执行合规受限）；A1/direct、B1/native、B1/direct、C1/native、C1/direct、D1/native、D1/direct、E-window/native、E-window/direct、F-window/native、F-window/direct 均未运行。A1 成功返回不代表③获准，也不代表六场景实验完成。

所有历史拒绝与暂停记录、旧冻结、旧错误继续保存。本轮停止于这次实际返回，没有新增业务请求。后续由 ChatGPT 对固定提交、原始答案与执行限制独立审计；不将本报告冒称独立验收。

完整文件摘要和来源见 [evidence-index.json](evidence-index.json)。
