# A1⓪ native：一次真实调用，输出 schema 被 API 拒绝

**实际状态：明确失败。没有原始答案，没有交付。**
本轮只执行 A1/native，未启动 Jev、其他场景或内容评阅；取得真实错误终态后停止，没有修改 schema 或重试。

## 原始错误与发生层级

实际 Codex 宿主会话 `01a0e2ac-1892-7ad2-8174-46902011b269` 于 `2026-09-27T11:42:33.154Z` 发出 `task_complete`，`last_agent_message=null`，错误如下：

```json
{
  "error": {
    "message": "Invalid schema for response_format 'codex_output_schema': In context=('properties', 'read_paths'), 'uniqueItems' is not permitted.",
    "type": "invalid_request_error",
    "param": "text.format.schema",
    "code": "invalid_json_schema"
  }
}
```

发生于 API 请求的输出格式 schema 校验层；不是工具安全拒绝、网络错误或生成后的答案格式不合格。
错误正文见 [host-api-error.json](evidence/host-api-error.json)，原始宿主终态事件见 [host-terminal-events.jsonl](evidence/host-terminal-events.jsonl)。没有替模型填写排序结果，也没有使用 fixtures。

外层驱动退出码1，抛出 `RecoveryRequired: pilot_remote_completion_unknown`，见 [原始 stderr](evidence/operator.stderr.txt)。驱动要求成功的 `turn.completed` 才写完成账本，因而此次保留 host/serial 意向，没有 outcome、serial completion、result 或 reply。实际 CLI 会话的明确错误终态补充了“为什么退出”的证据；本报告据此记为明确失败，但**不伪造或改写原账本完成记录，不自动重发**。

## 请求、身份与时间

- 源提交：`79acb4e3e4c7cb23045c40168af01818d50ed507`。R2 受审实现仍为 `7d07e4facb875d8f07dab5bacac1b417878aa5fe`，本轮源码未改。
- 宿主请求：`gpt-6-sol/xhigh`，与实际会话配置一致；服务端执行模型身份未获得独立回执。单次上限360秒，每臂最多4次/900秒。
- A1 原文仍为：`把下面三个词按英文字符字母顺序排列，只返回三行：pear、apple、plum。`
- raw SHA256：`f1fb54fde97adeee66ccb0bbbd2b8d90978a6342f882052b0f5ee5d55e4bfdb9`。原入口、完整可读路径目录、正常按需读取合同均进入 [实际请求](evidence/runs/A1/native/host/0/request.json)及 [prompt](evidence/runs/A1/native/host/0/prompt.txt)；[实际 schema](evidence/runs/A1/native/host/0/schema.json)原样保留。
- 技术后继根：`/Users/william/Documents/Codex/2026-09-27/mindthus-jev-direct-live-r2`。后继 freeze SHA256：`2701fad01df0d3f192fe9507dac1508fc554697ab42391a5476034585c8fc3b8`。现有 `pilot.prepare` 登记本地路径、R2代码与已变化的配置哈希；保留六案例和原额度，只授权本轮 A1/native 派发。父 freeze/本地旧准备根均未改写。

| 计量 | 实际值与口径 |
|---|---|
| 宿主调用 | 1次 CLI 调用；后续读取0、主动重试0。CLI未暴露逐次HTTP尝试计数。 |
| Jev／内容评阅 | 0／0 |
| 宿主实际会话耗时 | **28.518秒**，来自真实 `task_complete.duration_ms`；包含会话处理，不冒称纯HTTP推理耗时。 |
| 纯API请求耗时 | 未单独记录。驱动异常前的 monotonic elapsed 没有持久化，不能事后补造精确值。 |
| 主动冷却等待 | **0秒**；核对无前一业务请求，账本 `gap_basis=first_call`。没有第二次请求。 |
| 完整执行命令墙钟 | **30.22秒**，来自 `/usr/bin/time -p`；包含 Python/驱动/CLI启动、资料装载及错误退出。 |
| 资料装载开销 | 包含于完整墙钟，未单独测量。 |
| token／结算费用 | 未报告／未知，不能记为已测零成本。 |

本批宿主已消耗1次尝试，A1原调用上限下剩3次；这不是本轮继续授权。Jev仍0/12。其余十一条路径未启动。

## 发送前核对与证据边界

发送前读回旧 OCI 根：A1/native不存在，整个旧根无意向、返回或结果，无匹配 pilot 进程；四个本地旧根的非fixtures部分也无业务记录或匹配进程。没有既有完成答案或未知请求可供复用。远端只读工具会话为 `session-390d80e066d50886e229959e`，观察值与技术后继映射保存在 [preflight-and-successor.json](preflight-and-successor.json)。

本地二进制与旧登记哈希一致；配置provider为openai且未配置自定义endpoint，显式请求型号/推理强度不变。使用既有 `experiments.jev_direct.pilot run --case A1 --arm native` 入口，保留默认宿主只读模式与串行账本。历史整批/B1③拒绝继续保留；历史A1单独启动记录为网络错误，本次没有声称历史拒绝整体解除。

本轮另有一次 git fetch TLS错误：`LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to github.com:443`。后续同一仓库 `git ls-remote` 正常返回源SHA。它发生在准备阶段，与真实宿主返回的 schema 错误分列。

[证据索引](evidence-index.json)覆盖本目录交付文件；真实会话仅导出开始/错误终态原始事件及必要配置字段，不导出隐藏推理或无关会话内容。原现场意向和失败痕迹保留；[execution-disposition.json](evidence/execution-disposition.json)单列实际失败与驱动账本未收口的区别。

四项工程发现继续 CLOSED。本次新增事实仅证明当前既有 schema 在真实宿主 API 校验中被拒；未评估任务质量、③效果或净收益。后续若需要修复，必须保留此次失败与已消耗尝试；本轮不做修复或再次派发。
