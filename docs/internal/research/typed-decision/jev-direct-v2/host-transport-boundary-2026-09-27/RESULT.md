# #211：请求重试控制边界（零新增模型调用）

**A1⓪已交付，原答案和执行限制保持；A1③本轮未发送。** 最小候选配置可以控制普通 HTTP/流重试和 WebSocket，但不能控制独立的 401 认证恢复重发。因此当前严格的“每次实际请求之间至少60秒”还没有可验证保障，不能继续 A1③。这不是当前工具安全拒绝，也不表示存在未证实的后台任务。

基线修复 `0659bc5d7e08c82998ff3a507b4870651186241c`；原始结果 `c6bb209d3fe12f258056caaf0e6ad0cca92058d1`。本轮未修改实验运行代码、用户配置、安全设置、main、Jev问题或方法；R2四项保持 CLOSED。

## 保留的真实答案

```text
apple
pear
plum
```

[原始 JSON](../a1-native-format-repair-2026-09-27/evidence/runs/A1/native/host/1/reply.json)与[原始结果](../a1-native-format-repair-2026-09-27/RESULT.md)未改变。本轮仅核对文件摘要，没有重新生成或进行内容评阅。其余十一条路径仍未运行，③效果与净收益无结论。

## 版本、官方来源与实际配置解析

实际二进制仍是 `codex-cli 0.158.0-alpha.2`，SHA-256 `c3e30211bd454da70ceb4d9cbc2e05fe6466812ab05c311c3bbff6addeb14202`，与旧冻结一致。官方 tag `rust-v0.158.0-alpha.2` 指向源码提交 `10382da79a2a2d6e8ae221fa63077215389c1ad2`。这是版本标签及实际解析行为交叉核验，不冒称可复现构建证明。

[官方配置文档](https://learn.chatgpt.com/docs/config-file/config-reference)列出了三个字段，但并不证明可以覆盖内置 provider。对应版本的 [config_toml.rs](https://github.com/openai/codex/blob/10382da79a2a2d6e8ae221fa63077215389c1ad2/codex-rs/config/src/config_toml.rs#L935)明确禁止覆盖保留的 `openai` 标识。

使用实际二进制的 `app-server --strict-config --stdio`，只发送 `initialize / initialized / config/read`，没有创建 thread/turn，没有模型探针，未读取或提取 auth.json/登录凭据。三组真实解析夹具：

| 配置解析 | 观测 |
|---|---|
| [现有配置](baseline.json) + 明确 gpt-6-sol/xhigh | 返回配置；provider 未显式设置，使用内置默认。重试/WS字段未配置。 |
| [覆盖内置 openai](builtin-override.json) | CLI退出1：`Built-in providers cannot be overridden`。这是本地配置解析拒绝，不是安全拒绝或模型失败。 |
| [同官方认证的独立 provider 标识](candidate-official-alias.json) | 配置解析接受0/0/false，且 `unbounded_connection_retries=false`。这只证明配置解析，不是线上请求验证。 |

可复核命令在 [config-read-only-check.py](config-read-only-check.py)；敏感配置未输出，只保存白名单投影。用户 config.toml 检查前后 SHA 相同。版本、配置摘要、源码摘要与所用行号见 [official-source-evidence.json](official-source-evidence.json)。

## 哪层能控制，哪层仍不能控制

| 层级 | 对应版本证据与结论 |
|---|---|
| HTTP常规错误重试 | provider `request_max_retries` 传入 RetryPolicy；循环 `0..=max_attempts`。0保留首次请求，禁止该循环再次发送；不是“零次请求”。 |
| 流中断后的采样重试 | `stream_max_retries=0` 禁止普通计数分支继续采样，但不是所有分支的总开关。 |
| 无限连接恢复 | `features.unbounded_connection_retries` 在此版本默认true，独立于上项计数。候选必须显式false。 |
| WebSocket预热/回退 | `supports_websockets=false` 关闭WS连接与 `generate=false` 预热，同时使fallback不能激活。只设stream=0而保留WS时，仍可能立即转HTTPS并重置流重试计数。 |
| **401认证恢复后的重新发送** | **HTTP `stream_responses` 自带独立loop：收到可恢复401后执行官方认证恢复，再 `continue` 重新提交。它不受上述两个max_retries约束，也没有批次60秒回调。保留官方托管认证意味着该路径仍可发生。** |

关键代码：[HTTP retry](https://github.com/openai/codex/blob/10382da79a2a2d6e8ae221fa63077215389c1ad2/codex-rs/codex-client/src/retry.rs#L89)、[流重试/回退分支](https://github.com/openai/codex/blob/10382da79a2a2d6e8ae221fa63077215389c1ad2/codex-rs/core/src/responses_retry.rs#L69)、[独立401重发](https://github.com/openai/codex/blob/10382da79a2a2d6e8ae221fa63077215389c1ad2/codex-rs/core/src/client.rs#L1728)。未关闭认证、安全检查或通过转移凭据绕过该路径。

## 最小候选差异：仅解析，未启用

候选仅限未来本实验两臂共同使用，不写入全局配置：

```toml
model_provider = "mindthus_official_http"
[model_providers.mindthus_official_http]
name = "OpenAI"
requires_openai_auth = true
request_max_retries = 0
stream_max_retries = 0
supports_websockets = false
[features]
unbounded_connection_retries = false
```

没有 base_url、env_key、代理或新的认证材料；对应源码在原认证为ChatGPT时继续选择原官方Codex服务，并复用现有认证管理器。但上述401缺口未闭合，因此只登记 [candidate-profile.json](candidate-profile.json)，状态 `parser_verified_not_activated`；没有创建已生效的运行技术后继，也没有发送 A1③。正式启用时仍需两臂同配置、父冻结/新格式摘要和额度继承；不能拿候选新耗时直接与旧119秒作匹配对照。

## 旧请求的分层计数与发送阶段

[追加记录](counts-supplement.json)引用原请求、线程、轮次和文件摘要，没有改写历史 outcome：

| 层级（针对旧A1成功调用） | 已知值 |
|---|---:|
| 外层driver自动重试 | 0 |
| 用户授权的格式技术重试（该路径历史） | 1 |
| 该次宿主exec CLI启动 | 1 |
| A1/native累计宿主exec CLI启动 | 2 |
| 内部采样retry日志 / UI reconnect通知 | 5 / 4 |
| 实际底层生成请求、HTTP采样尝试、远端重叠 | unknown |

`automatic_retry=false` 只描述外层driver，不能覆盖CLI内部。本轮另有三次仅配置解析的app-server进程，不计为业务宿主exec或模型调用。

原预热 `tls handshake eof` 可定位在连接建立、生成帧发送之前。五条 `request timed out` 与源码15秒WS连接超时分支及日志节奏一致，支持连接阶段失败的解释；但保留日志没有逐次可绑定的发送确认/响应ID，不能将五条日志推算成“必然六次实际生成请求”。发送后的断流/无可靠终态仍应保持unknown。

同一成功线程/轮次确有已绑定终态和原答案。这既不能证明每次底层尝试均结束，也不能反向证明后台必有任务；追加记录保留这一证据上限，不用缺日志制造任务存在性结论。

## 下一步边界与一个最小协议建议

现行严格请求级规则不变，A1③条件未满足，故未发送；本轮没有新的服务拒绝或安全拒绝。缺口是当前CLI正规配置不能把独立401重发交给外层按60秒调度。

**供方案方决定、尚未采用的最小调整：**仅把有可绑定证据证明“未发送生成负载或被明确401拒绝、未受理生成”的连接/认证恢复列为传输恢复例外；所有可能启动生成的实际请求继续单在途并间隔60秒，状态未知与安全拒绝不得豁免。这是需要明确接受的协议边界调整，不是把间隔降为CLI启动间隔。若不接受该例外，则需要当前官方CLI提供能禁止该独立重发、或能在重发前执行间隔约束的正规控制；不另造客户端或运行平台。

本轮针对性验证见 [validation.log](validation.log)：实际解析夹具、来源/旧证据摘要、分层计数、配置未启用与额度未重置。没有重跑全仓审计、R2回归或A1答案。旧额度仍是按宿主CLI计数已用2/4、余2；底层尝试余额未知。工程控制结论与③真实效果分别报告，本轮没有新的路由、答案或分层推理耗时。
