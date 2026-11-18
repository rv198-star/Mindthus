# Codex Dispatch v0.1：实现与交接证据

日期：2026-11-18（Asia/Shanghai）。设计与功能基准固定于提交 `215710730`。
实现提交的父提交即该基准；两份基准原样保留，设计处置由 A 完成。

## 真机只读验证

| 环境 | 实际操作 | 结果 |
| --- | --- | --- |
| 本机 CLI 0.169.0 的 App Server（16:39–16:42） | 只调用 `initialize`、`initialized`、`model/list`；默认范围、明确指定当前提供方两种读取分别用每页 3、2 条 | 均读全 13 个可见型号。另取不存在的提供方返回 RPC `-32600`，脚本退出 1、无清单输出。 |
| 本机运行中的 managed App Server 0.170.0（16:46） | 用 `codex app-server daemon version` 取得该守护进程的 Unix socket；经 WebSocket 接入，明确指定当前提供方，每页 2 条，沿游标读完 | 13 个可见型号。真正接入了运行中的守护进程；本处证据登记的是该端点，桌面选项 UI 和实际派工留给 A 验收。 |
| 当前聊天工具的运行时说明 | 核对 `spawn_agent` 的上下文继承与覆盖参数、`create_thread` 的工作区/待建引用、`send_message_to_thread` 的授权和调用宿主选择范围、`wait_threads` 与 `read_thread` | 实现按当前宿主接口分流。工具说明包含的选项仅用于其明确适用的目标。 |

清单抽样（测试证据，技能运行时重新获取）：

| 选择 ID | 支持档位 | 默认 |
| --- | --- | --- |
| `g-openai/gpt-6.2-sol` | low, medium, high, xhigh, max | xhigh |
| `g-openai/gpt-6.2-astra` | low, medium, high, xhigh, max | high |
| `group/deepseek-v4.1-flash` | low, medium, high, xhigh | high |

复核方式：运行 [清单脚本](../../../skills/codex-dispatch/scripts/model_inventory.py)；
参数见 [宿主操作](../../../skills/codex-dispatch/references/host-operations.md#inventory-for-the-target)。
本机读取采用 `--page-size 2` 可直接复核分页。

## 本地自动验证

- Skill Creator 的 `quick_validate.py` 通过。用 App Server 替身覆盖了分页和隐藏条目、
  每页沿用指定提供方、推理字段的准确投影，以及后续页 RPC 拒绝、游标循环和超时
  时不输出半份清单。
- Python 3.11.11 执行 `python3 -m unittest discover -s tests -q`：1,414 项，
  8 项跳过，其余通过。macOS 首次默认临时目录的 `/var` 符号链接触发了
  9 项既有 TPlan 路径检查；以 `mktemp -d /private/tmp/mindthus-dispatch-tests.XXXXXX`
  生成规范路径作为 `TMPDIR` 后全量复测通过。
- 在临时目录构建基线和候选的完整发行包，递归比较文件内容：Claude Code 和
  OpenCode 原样，Codex 的插件包与 skills 包均只新增 `codex-dispatch` 目录。
  源码安装验证覆盖 Codex 发现技能、Claude 跳过技能。

## 受控桌面演练：F1–F8

以下为 B 按技能规则走查的合成场景。本节中的人类输入、型号、调用日志、版本和宿主结果均为演练数据。

固定任务：A 负责设计与验收；B 在隔离目录遍历导入接口；C 独立审查 A 冻结的版本。
验收包括尾页、准确总数与游标循环处理。合成目标清单：A 已运行 `atlas/high`（交接备选
`mira/high`）；B 的目标支持 `forge/high,xhigh`、`mira/high`；C 的目标支持
`lens/high`、`prism/high`。B 和 C 从不同目标来源取清单。两组面向用户显示如下：

> 两组均保留 A（atlas/high；另行交接时可用 mira/high）。本批复用已授权的 B，
> 范围仅为导入隔离目录；B 交付后由 A 冻结版本再新建只读 C。提交选项授权 A 按
> 该组合执行列明的创建、联络与服务失败时的替补；A 会读取两份结果。

| 选择 | B · 实现（首选 → 替补） | C · 独立审计（首选 → 替补） | 取舍 |
| --- | --- | --- | --- |
| 1 · 依设计实现（推荐） | mira/high → forge/high | lens/high → prism/high | 契约清楚，保留已熟悉该类验收的审计方 |
| 2 · 深挖导入兼容 | forge/xhigh → mira/high | prism/high → lens/high | 把更多推理投入实现排障，C 使用另一合格审计方 |

> 可直接选组、输入“方案 2，B 改 high，其余照旧，开始”，或选择“暂不派工”。

| 场景 | 演练的输入、观察与处置 |
| --- | --- |
| F1 · 两类会话 | “临时查一下游标规范”走当前聊天的 SubAgent 约束；转成“持续实现并独立审计”后进入 B/C 独立聊天配置。TPlan 变体中 A 用原协议登记，B/C 只拿职责和产物引用。 |
| F2 · 目标约束 | 把 B 的目标替换为仅公布 `mira/high` 的宿主。用户锁定的 `forge/xhigh` 标为不可用；展示以 `mira/high` 代替的最近选项及替补缺口，等待用户修改锁定项后再派工。 |
| F3 · 一轮查证 | 合成陌生版本可能改变 C 的首选：集中查一次公开版本和审计能力，留来源、版本和选择影响。注入离线时列明待验证的能力，优先推荐已有依据者。同版同任务已有证据的变体直接组合。私有别名只用于宿主清单。 |
| F4 · 确认与取消 | 预选方案 1 后关闭控件：`create=0, send=0`。重新打开并提交“暂不派工”：仍是 `0,0`。仅说“B 倾向 forge”：锁定偏好，计数仍为 `0,0`。提交“方案 2，B 改 high，其余照旧，开始”：合法，先 `send(B, forge/high, intent-b1)` 一次；冻结 `v1` 后 `create(C, prism/high, review-v1)` 一次，C 的首条提示带完整 Brief，无二次发送。 |
| F5 · 失败与未知 | B 的首选明确被拒且无在途写入：查看部分产物后按获准顺序用 `mira/high`，记原因和请求/实跑状态。另一次 `send(B, intent-b1)` 超时：只查原 B；查到 `intent-b1` 在执行则跟踪该轮，未确认的变体挂起。两个变体均无第二条派工、无替补运行。模拟 `create` 返回待建引用时也保留原意图，等待映射为 chat ID。 |
| F6 · 自主修正 | 第二页返回剩余数据；B 本地补游标遍历并验证跨页，交付写“执行已解决，设计待回写”。A 将“读至末页”写入下一版设计的读取步骤，并关联测试。 |
| F7 · 上游决定 | 注入源端仅保留 100 条，B 提供保留规则与缺失样本，暂停全量历史验收，同时继续独立的游标循环防护。A 决定新增历史来源，或按原授权边界提交覆盖目标变更。 |
| F8 · 固定版本 | C 对 `v1` 发现尾页漏记，A 让 B 返修。收到 `v2` 后重新向已授权 C 交付 `v2` 和原验收条件；A 用 `v2` 的审计处置收口。 |

## 建议 A 回写与验收

| 设计位置 | 实际观察 | 建议处置 |
| --- | --- | --- |
| [设计 §1](design.md#1-先取目标环境清单) | 本机运行中的守护进程在控制 socket 使用 WebSocket，直接用 `app-server proxy` 转发 JSON 行时握手超时。已改用 WebSocket 并复核全量；CLI 的 stdio 仍是 JSON 行。 | 回写两种只读接入方式，并记录必须绑定目标端点；不要把本机 CLI 样本拿去填桌面或其他宿主。 |
| [设计 §3](design.md#3-组合提示与确认) | 选择控件取决于模式；部分工具限制用选择控件单独申请权限。已保留全案、自由文本和对话回退。 | 用实际验收宿主记录控件是否可用、提交前后计数和授权表达；确需另行授权时在主对话请求。 |
| [设计 §4](design.md#4-派工替补与审计) | 待建 `clientThreadId` 与可派工 `threadId` 有区别；超时的新建可能连待建引用也没有。已写入原目标对账和未决时的停留规则。 | 把待建引用和无回执两种情况纳入恢复说明；跟随真实轮次时分别记请求值和实跑值。 |
| [设计 §6](design.md#6-记录归属与首版验证) | 脚本、包和受控走查由 B 完成；当前任务范围包含只读宿主验证。 | A 在已授权宿主补真实选择、自由改档、确认后唯一发送、取消零派工、结果偏差和回写位置。未知投递带真实风险时用受控回执验证对账。 |
