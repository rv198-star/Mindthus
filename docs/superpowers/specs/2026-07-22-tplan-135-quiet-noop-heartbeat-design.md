# TPlan #135：Quiet no-op 与三次无变化心跳设计

Date: 2026-07-22
Status: **implemented / acceptance verified**
Parent: #132

## 0. 一页结论

自动状态更新没有新的 Mission / evidence 变化时，不应反复制造“我还在推进”的叙事；但连续
静默也会让用户怀疑任务是否停滞。因此采用一个有界节奏：

> 有变化立即说；没变化默认安静；连续三次自动检查没变化，发送一次明确不代表进度的状态心跳。

该能力是**展示节流**，不是进度评分器：

- 脚本只机械判断“与上一份 cursor 相比是否变化”；
- 调用方声明本次是自动更新还是用户主动询问；
- Agent 负责把变化解释成人话，但不能把心跳写成进度；
- #136 单独负责 telemetry / writeback / countable progress 的计量边界。

## 1. 要解决的真实问题

长 Mission 中常见两类坏体验：

1. 没有新 evidence、decision、blocker 或任务状态变化，仍反复发送厚重进度更新；
2. 为了避免噪音而长期完全沉默，用户无法区分“仍在运行”和“已经卡住”。

#135 只解决更新节奏，不推断工作价值，也不承诺检测宿主级进程死锁。

## 2. 行为规则

### 2.1 自动更新

同一展示通道持有上一轮 cursor：

| 情况 | 行为 | 下一轮 `quiet_streak` |
| --- | --- | ---: |
| 首次调用，无 cursor | 输出完整当前快照 | 0 |
| 有 Mission/evidence 变化 | 立即输出正常更新 | 0 |
| 第 1 次无变化 | 无用户文本 | 1 |
| 第 2 次连续无变化 | 无用户文本 | 2 |
| 第 3 次连续无变化 | 输出一次状态心跳 | 0 |

后续继续按 1、2、3 的节奏循环。心跳是 liveness feedback，不是 progress evidence。

### 2.2 用户主动询问

用户主动问“进度如何”时永远回答，不受 quiet 抑制：

- 有变化：正常说明新变化；
- 无变化：一句话说明“暂无新的可验证变化，当前仍在 X”；
- 回答后该展示通道的 `quiet_streak` 归零。

### 2.3 必须立即显示的变化

下列变化第一次出现时不能被静音：

- Mission / Task / active path 状态变化；
- 新 evidence、decision、blocker、failure、stop 或 requires-human 状态；
- acceptance 或 authority 边界变化；
- cursor 校验失败等会让静音判断不可信的错误。

变化已经成功显示后，后续相同快照重新进入普通三次心跳节奏，避免 terminal/blocker 被无限重复刷屏。

## 3. 什么算“无变化”

v0.2 使用保守且机械的判断：

- canonical 完整 `mission.json` digest 未变；
- `evidence.jsonl` 的已验证边界 digest 未变。
- Interaction Guard 的安全摘要（存在、phase、revision）未变；摘要不含消息正文。

以下变化不打断 quiet streak：

- `execution_trace.jsonl` 新 telemetry；
- task-local operational log；
- 单纯工具调用、耗时或 token 消耗。

这只说明“没有新的用户可见 TPlan 状态”，不等于“没有工作发生”。是否构成有效推进由 #136
定义，#135 不重复实现。

使用完整 Mission digest 是保守选择：未来新增控制字段默认会打断静默，不会因白名单遗漏而吞掉
重要变化。若后续证明某些内部字段噪音过大，再以明确排除项收窄，v0.1 不预先优化。

## 4. Delivery Cursor

cursor 是调用方持有的展示状态，不写入 Mission：

```json
{
  "schema_version": "tplan.user_update_cursor.v0.2",
  "mission_id": "mission-id",
  "mission_binding": "sha256:...",
  "mission_digest": "sha256:...",
  "evidence_digest": "sha256:...",
  "interaction_guard_digest": "sha256:...",
  "quiet_streak": 2
}
```

CLI 可将它编码为 opaque base64url token。约束：

- cursor 不是 evidence、checkpoint 或 source of truth；
- 每个展示通道独立持有 cursor，多个消费者不共享静默次数；
- cursor 不包含 prompt、日志、用户文本或 evidence 正文；
- mission id、Mission binding、schema、digest 或计数非法时，必须显式报错或完整重同步，禁止静默；
- Guard 的存在、阶段或 revision 变化使用不含消息正文的摘要参与比较，必须立即显示；旧 v0.1 cursor
  不兼容并要求完整重同步；
- Guard 当前存在时，完整更新必须显示事实化的写保护状态、phase 和 revision；刚解除时必须显示
  “交互保护：已解除”，不得只重发与变化前相同的正文；
- `quiet_streak` 的合法持久值为 `0..2`，第三次输出心跳后归零。

不增加 cursor sidecar，也不让只读 renderer 反向写 Mission。若发现未完成的 Mission transaction，
只读 renderer 与空 checkpoint 必须显式失败并保留 journal；恢复只能由 mutation-capable 命令完成。

## 5. Renderer 接口

扩展 `scripts/render_user_update.py`：

```bash
python3 skills/tplan/scripts/render_user_update.py MISSION_DIR \
  --delivery automatic \
  --cursor OPAQUE_CURSOR \
  --json
```

`--delivery`：

- `explicit`：用户主动询问；无变化也返回简短文本；
- `automatic`：按 quiet streak / heartbeat 规则输出；
- 未传 cursor 时保持当前完整快照行为，保证兼容。

机器输出：

```json
{
  "changed": false,
  "update_kind": "quiet | heartbeat | brief | full",
  "quiet_streak": 2,
  "cursor": "...",
  "text": ""
}
```

非 JSON 模式下，`update_kind=quiet` 成功退出且 stdout 为空；错误不得伪装成 quiet。

## 6. 心跳文案

默认中文模板：

> 状态心跳：连续 3 次自动检查没有新的 Mission 或验收证据变化。当前仍在“{active task}”；最近一次可验证变化是“{latest confirmed summary}”。

若没有 active task 或 confirmed summary，使用事实化降级文案，不猜测工作状态。禁止使用“进展顺利”、
“即将完成”等没有 evidence 支撑的表述。

## 7. Checkpoint 与 Pulse

### 7.1 Checkpoint

`checkpoint.py` 当前在既没有 log 也没有 evidence 时仍输出 `checkpoint recorded`。改为：

- JSON 增加 `noop: true | false`；
- 无写入时非 JSON 输出 `checkpoint_noop: survey only; no log or evidence recorded`；
- 不创建新 event、log、Step 或 cursor 状态。

### 7.2 Mission Pulse

现有 Pulse 已能在无 candidate 时只读返回 `next_gate=continue`，不需要重构或新增判断中心。
文档补充：自动调用方看到无 candidate 且 user-update cursor 无变化时，不生成进展叙事。

三次心跳不自动升级成 blocker、Anti-Spiral 或 continuation authorization。真实升级仍由已有证据和
Gate trigger 决定，避免把“长操作”机械误判成死锁。

## 8. 死锁边界

只要自动检查循环仍在运行，第三次无变化会给出心跳，因此可以减少“是否还活着”的焦虑。

如果 Agent、宿主或调度器已经完全停止，第三次检查本身不会发生，#135 无法检测这种死锁。真正的
process watchdog / lease timeout 属于宿主能力，不在本 issue 内伪装实现。

## 9. 改动范围

预计修改：

- `skills/tplan/scripts/tplan_runtime.py`：cursor 构造、校验和 deterministic delta 比较；
- `skills/tplan/scripts/render_user_update.py`：delivery mode、cursor、quiet/heartbeat 输出；
- `skills/tplan/scripts/checkpoint.py`：诚实 no-op 结果；
- `skills/tplan/resources/user-output.md`：自动/主动更新契约；
- `skills/tplan/resources/hooks.md`：Pulse 无候选时的 quiet 使用边界；
- 对应 `tests/tplan/` 回归测试。

不新增 Mission schema、全局 quota、scheduler、heartbeat daemon 或持久化展示 sidecar。

## 10. 验收测试

- [x] 无 cursor 的旧调用仍输出完整更新；
- [x] 自动更新连续两次无变化时 `text=""`；
- [x] 第三次无变化输出 heartbeat，并把 streak 重置为 0；
- [x] 第六次无变化再次输出 heartbeat；
- [x] 用户主动询问在无变化时返回简短现状并重置 streak；
- [x] 新 Mission 状态或 evidence 变化立即输出并重置 streak；
- [x] 仅 telemetry / task-local log 变化不冒充用户可见 delta；
- [x] blocker、stop、requires-human、terminal 首次变化不能被静音；Guard 的开启、phase/revision 变化和解除
  既不能静音，也必须在正文中显示；
- [x] 非法/跨 Mission cursor 不能造成 quiet；
- [x] 空 checkpoint 不写文件且不再声称 `recorded`；
- [x] Pulse 无 candidate 仍保持只读 `continue`，不因第三次 heartbeat 自动升级 Gate；
- [x] 压力例：九次 status-only 自动检查只产生三次诚实心跳，不产生 progress evidence。

## 11. Decision

```text
decision: accept with revision
reason: quiet no-op reduces attention waste, while a three-check heartbeat prevents indefinite silence and user anxiety.
constraints: presentation throttling only; no progress scoring, no Mission write-on-read, no fake deadlock claim, no overlap with #136.
implementation: delivered
verification: python3 -m unittest discover -s tests/tplan (269 tests passed)
```
