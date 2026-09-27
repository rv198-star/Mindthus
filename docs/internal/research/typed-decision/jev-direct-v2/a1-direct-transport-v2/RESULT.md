# A1③已真实交付：一层 Jev，无具名方法

实施固定提交：`7d90845486daad1467f53caf6ffc791ef16c56d4`。
父提交：`62845d9139c701715b875a186695637a434ced76`。
本轮只执行 A1/direct；A1/native 未重跑，其余十条路径仍 UNRUN。

## 实际答案与内容比较

宿主原始 JSON 的 `text` 为实际换行的三行：

```text
apple
pear
plum
```

[原始 reply.json](evidence/runs/A1/direct/host/0/reply.json)、[原始 CLI stdout](evidence/runs/A1/direct/host/0/cli.stdout.jsonl)、
[交付 result](evidence/runs/A1/direct/result.json)、[绑定到同线程/轮次的真实归档终态](evidence/transport-v2-host-success.json)。
本地完整 schema 和分支合同通过；真实 API 接受了本次发送 schema，模型已返回，答案已交付。
确定性的 A1 排序与三行要求符合，与已接受的 A1/native 正文完全相同；未调用内容评阅模型。
这不构成其余场景质量结论，也不构成净收益结论。

官方 TypeSafe `jev-1.13.0` 首层真实读取全目录并回答原定 71 题。
[路由返回](evidence/runs/A1/direct/route/result.json)：`mode=direct`、`methods={}`、
`rounds=1`、`requested_details=[]`，因此没有第二层请求。
宿主 `gpt-6-sol/xhigh` 加载方法为空，入口和目录未由宿主重跑，前置 LLM 数为 0。
完整原问题、方法卡片、阈值及原始供应商 receipt 均在证据包。

## 协议与实际配置

[PROTOCOL.json](PROTOCOL.json) 在执行前提交，随后追加技术后继：
`239204bf08c04fa31a534cce205a8cea397336f0382b6a04eb95f37c4f6b5340`。
[技术后继](evidence/transport-successor-v2.json) 保留旧冻结与父身份、历史文件摘要及已消耗额度。
[实际调用配置](evidence/runs/A1/direct/host/0/effective-transport-config.json) 使用原候选七项覆盖：
官方 HTTP provider 别名、官方认证、request/stream retries=0、WebSocket=false、unbounded connection retries=false。
归档 `session_meta.model_provider=mindthus_official_http`，同一轮次 `turn_context` 确认请求型号和 xhigh；
这属于客户端生效配置证据，宿主服务端型号证明仍未观察到。
不改全局配置、认证、服务端点、安全设置、题目或预算。

线程：`01a0e33d-6804-7063-af03-3d57e480f01e`；轮次：`01a0e33d-6911-7540-aa01-491815c44809`。
请求摘要：`293120a58263298d0cfb0ecd30d5f7c0b1657c478ca1be44bfc132cd7f956bf0`。
原答案摘要：`24be6bf9ab8cee7f1b560afb942ec3188949ee8f6709a7959eedc534db49d600`。

## 次数、时间与未知项

| 项目 | 本轮实测/观察 |
|---|---:|
| 外层 driver 重试 | 0 |
| 宿主 CLI 启动 | 1 |
| Jev evaluate / transport 调用 | 1 / 1 |
| 已返回的生成工作 | 2（Jev + 宿主） |
| 可观察采样重试 / 401认证恢复 / 连接恢复日志 | 0 / 0 / 0 |
| 宿主底层 HTTP 总次数、精确生成尝试数 | unknown；至少一次宿主成功生成 |
| 主动等待合计 | 119.969186s |
| Jev 前保守等待 | 60.005218s |
| Jev→宿主主动等待 | 59.963968s |
| Jev→宿主完整单调时钟间隔 | 60.000125s |
| Jev evaluate（含适配与校验） | 1.958979s |
| 宿主 CLI 会话 | 17.237451s |
| 归档宿主 task | 6.971s |
| 宿主 dispatch（含冷却） | 77.217271s |
| 完整执行墙钟 | 139.469893s |
| 路径墙钟（run-start→seal） | 139.260724s |
| 其余装载/校验/记账残差合计 | 0.304277s |
| 单独装载、纯 HTTP、认证/连接恢复分项时间 | 未独立测量，unknown |

第二次主动 sleep 少于60秒，因为已在本地准备工作中经过约0.036秒；完整单调间隔超过60秒。
认证或连接恢复若发生，其耗时包含在宿主会话中；本次未观察到401或恢复，未制造探针。
无日志不等于底层实际次数可确定，也不等于恢复耗时已测得为0。
Jev usage 为 input=15530、output=3596；宿主 input=20040、cached=0、output=90。
金额均未提供，不推算费用。详见 [summary.json](summary.json)。

未观察到协议例外或无法归类的内部重发。四条现存账本记录（含旧两条）都有各自可靠终态，
本轮逻辑调用无未解决发送状态，未触发后续派发停止标记。旧 A1/native 底层尝试仍 unknown，
既不追认其每次底层尝试结束，也不据此断言存在后台任务。

A1/native 仍已用2/4；A1/direct 已用1/4，余3次宿主额度、882.762549s；
Jev 已用1/2。未用额度不授权追分重跑。父历史文件摘要核对未变化。

## 验证与证据交付

[定点 diff](SCOPED.diff)、[五项接线/停止边界测试](targeted-tests.log)、[56文件证据索引](evidence-index.json)。
只验证新增接线与必要边界；未重复三组配置解析、17项旧证据检查或R2审计。
原失败/对账与原生臂完整包仍在父版本及 `a1-native-format-repair-2026-09-27/`，未改写。
执行前确认同批无其他实验执行者；继续使用原运行根、原串行锁和账本。
历史拒绝保留，本轮没有新的工具安全拒绝；没有借换渠道或启动形式重试受限业务操作。
Git fetch 和首次 push 的本地错误为 `LibreSSL SSL_connect: SSL_ERROR_SYSCALL`，属于 GitHub 传输层，
不是 Jev/宿主模型失败。最终推送结果另附提交交付信息。

工程接线通过；真实传输与交付完成；A1确定性内容正确；③一般质量和净收益仍未建立。
两臂传输条件不同，旧native约119秒与新direct宿主约17秒不能用于可信速度或成本改善计算。
到首份完整答案即停止，无额外模型调用。
