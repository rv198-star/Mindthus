# WAE Loop pilot.3 — Runtime Integrity Audit

日期：2026-09-08  
对象：`v1.11.0-wae-loop-pilot.3` 候选运行合同  
审计路径：A / Runtime integrity only  
性质：本会话同一 ChatGPT 实例的独立审计路径；与“方法是否值得采用”的审计分开执行。不是异模型、真人或组织外部独立认证。

## 结论

**PASS / 无已知接入阻断项。**

pilot.3 在保留 pilot.2 的持久化完整性修复基础上，把 `refine` 的有效状态从“一个标签 + changed_scope”提升为可恢复、可校验的单一 Refinement Unit 生命周期：

```text
Parent Handoff Artifact
  -> refine checkpoint / Refinement Unit
  -> bounded work (optional)
  -> Refine Result
  -> Absorb
  -> Parent Handoff Artifact'
```

Runtime 仍不判断业务语义是否正确，但已能确定性阻断以下结构性绕过：

1. 一个 `refine` 同时塞入多个独立 blocking remainder；
2. `refine` 没有绑定 Parent Artifact；
3. 同时存在两个未关闭 Refinement Unit；
4. project-file Parent 在 Refine Result 形成前被直接改写；
5. work/result 绑定到错误 Unit；
6. `resolved` Result 没有显式解决 Unit question；
7. Result 尚未形成或 resolved Result 尚未 Absorb 就再次 checkpoint/handoff；
8. blocked Unit 直接 handoff；
9. Absorb 使用错误 Unit、错误 result sequence 或错误 Parent-before；
10. `update` 吸收后 Parent identity 没变化；
11. `confirm` 吸收时 live project Parent 实际已变化；
12. 后续 handoff/refine 没沿用最近 Absorb 得到的新 Parent identity；
13. activation/event 持久化对象携带未声明的顶层扩展字段；
14. pilot.2 已修复的 trace hash/sequence、stale derived state recovery、activation digest 与 guard fail-closed 回归。

## 权威状态

pilot.3 继续沿用 pilot.2 的单一事实源：

```text
immutable activation.json agreement
+
valid fsynced hash-chain trace.jsonl
```

`summary.json` 与 `wae-loop-run.json` 只是 derived view。Refinement Unit、Result 与 Absorb 全部进入同一 append-only trace，不新增第二个事务日志或任务状态文件。

## Refine 生命周期不变量

### Unit 创建

- 只有 `checkpoint --decision refine` 创建 Unit；
- 每次只允许一个 blocking remainder；
- Runtime 顺序分配 `RU-0001`、`RU-0002` ...；
- Unit 绑定：question、unit kind、semantic scope boundary、completion criterion、Parent Artifact identity；
- 同时最多一个未关闭 Unit。

### Work

- `work` 是可选 trace 事件，不是完成门槛；
- 必须绑定当前开放 Unit；
- work 自身不关闭 Unit；
- project-file Parent 在 Result 前必须保持与 Unit 创建时一致。

### Refine Result

- 每个 Unit 最多形成一个当前 Result；
- `resolved` 必须显式包含原 Unit question 于 `resolved_remainders`；
- 大结果通过 result artifact 引用，trace summary 限制为 4096 chars；
- `blocked` 不冒充 resolved，后续只允许回到 `need_input / stop` 路径。

### Absorb

- 只接受 resolved Unit；
- `parent_before` 来自 Unit，不由调用方重新声明；
- `result_sequence` 必须精确绑定该 Unit 的 Result；
- `update` 要产生可区分的新 Parent identity；
- `confirm` 要保持相同 Parent identity，并对 project-file live state 做实际一致性检查；
- Absorb 完成后才允许开启下一 Unit 或 handoff。

## 恢复与篡改

pilot.2 的 WFF admission blocker 修复保持成立：

- append sequence 从有效 fsynced trace 推导，不从 stale summary 分配；
- guard-handoff 先消费完整 authoritative-run validation，再读取 handoff checkpoint；
- activation agreement 由 digest 绑定；
- persisted event 验证 required field、enum、semantic lifecycle 与精确允许字段；
- 结构合法但 hash 错误、hash 合法但结构/生命周期错误均 fail closed。

## 审计中发现并即时关闭的问题

### A-01 confirm Absorb live-state gap

初始 pilot.3 实现中，`confirm` 且省略 `--parent-after` 时直接复用 Unit 的旧 Parent identity。若 Result 后 live project file 已被修改，理论上会形成“实际变了但记录为 confirm”的错误。

修复：project-file Parent 使用 confirm 时重新读取 live ref/hash/bytes，并要求与 `parent_before` 完全一致。对应负向回归已加入。

### A-02 未知 persisted extension

初始 validator 对 required fields/enum 完整，但 activation/event 顶层未知字段仍可进入 hash 合法记录。

修复：activation 与每种 event type 使用精确 allowlist；未知顶层字段 fail closed。Unit、artifact、cost、coverage 子结构同样保持显式 shape 边界。

## 不属于 Runtime 能力的判断

Runtime **不能**且不应机械决定：

- `unit_scope` 的业务范围是否真的足够局部；
- 某个 dependency 是否属于该 Unit 的必要语义闭包；
- 一个 Absorb 修改了整份 Parent 是否业务上合理；
- Result 本身是否事实正确或设计优良。

这些仍属于 Agentic judgment / evidence / 后续审计。Runtime 的作用是把因果关系和越界路径变成可观察、可拒绝的结构合同。

## Host 责任保持

- WFF/EKRI/Slidethus 若需要 live artifact binding，必须把真正交接的 artifact/ref/hash 传给 `guard-handoff`；
- `need_input / stop` 后的项目阶段状态仍由项目/TPlan 持有；
- host 的 Stop/SubAgent/phase-exit carrier 是否物理接入 guard，仍需各项目分别验证。

## 最终审计裁定

在 pilot.3 当前范围内，未发现需要阻止生成内部压缩包的 Runtime integrity 缺陷。最终包仍需绑定完整测试、release-pack、ZIP CRC 与 SHA256SUMS 结果。
