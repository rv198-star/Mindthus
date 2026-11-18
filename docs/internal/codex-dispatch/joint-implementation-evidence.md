# Codex Dispatch × TPlan 联合实现证据

2026-11-18。基线 `a660e39ce`；实施合同 `joint-v1`、轮次 1。下列 Mission 均为独立临时样本，本记录由 B 维护。

| 证据类别 | 路径与结果 |
| --- | --- |
| 真实宿主，只读 | 从候选 Codex 插件包取 TPlan 和 Dispatch，置于隔离 Git 项目的 `.agents/skills/`；正在运行的本机 App Server 的 `skills/list` 返回两个启用的 repo skill，路径均指向本次打包文件。确认了宿主发现和入口文件位置。 |
| 真实宿主，已知会话的本轮输入 | B 在现有会话收到了 A 发来的 `D-joint-1 / I-joint-1 / r1 / joint-v1` 委派。回执写入旧 Mission、选型执行链和最终采用由 A 从原会话核对。B 未触碰 A 的 Mission 或 owner 验收记录。 |
| 自动回放，已知会话 | 用真实候选事务 writer 准备并占用，宿主替身记一次 `send_message_to_thread`；原请求重放仅返回 `replayed`，第二占用被拒。错误 host/chat/attempt 与过期回执被拒。同一个早到反馈在已关联前无法采用，确认后用同一来源重新关联并采用。 |
| 自动回放，新建晚到 ID | 同一真实 writer 先保存逻辑参与者和意图，再记录一次模拟 `create_thread`。待建 ID 和超时保持在途，同一参与者的另一写入被拒。提交原宿主和正式 ID 的证据后原子绑定；不能用待建 ID、他人 ID 或第二个正式 ID 改绑。下一轮可复用已绑定 chat；旧轮反馈留在原历史。 |
| 自动回放，替补 | 无原生证据时不能释放执行。原生拒绝且确定未启动后，持久化获授权的替补参与者和后续轮次，再以新的意图占用一次派工。 |
| 版本自举 | 源码基线 `a660e39ce` writer 在隔离 Mission 完成原协同闭环；候选 `1.7.0` writer 读取该 Mission 返回 `runtime_mismatch`。Mission JSON、Markdown、证据和执行追踪逐字节未变。Codex 插件与便携包的打包用例分别用包内脚本启动并完成原闭环。 |

本轮回放命令（Python 3.11；macOS 使用规范的 `TMPDIR`）：

```sh
python3 -m unittest tests.tplan.test_collaboration_runtime tests.test_packaging_docs -v
python3 -m unittest discover -s tests -q
```

最终全量结果：1,417 项，1,409 通过、8 跳过。TPlan 入口为 7,995 字节，
通过 8 KB 发现上限和用户输出合同检查。

设计处置见[功能 F9/F10](requirements.md#首版验收场景)和[设计 §6](design.md#6-记录归属与首版验证)。
原命令 envelope 与基础 schema 保持，新增显式的 `native_binding` 能力。
占用提交后、原生回执未明时保护写入范围；即使恢复时发现占用结果已提交，也先向原宿主对账。
协议校验身份一致性、代际和状态；A 负责验证宿主证据是否确实对应首条 Brief。

真机联合验收由 A 完成：核实当前既有会话的派工、回执和采用；在具备新能力且获得授权的 Mission 上，
验证真实创建晚到 ID 与首次回读绑定。用户实际选择控件和自由改档也由 A 在合适的批次观察。
