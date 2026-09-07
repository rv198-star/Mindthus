# WAE Loop：显式启用 Pilot 与发布资格

## 当前状态（2026-09-07）

**G1 合成检查点已证明基础交接能力；下一阶段转入显式启用的真实项目 Pilot。**

用户已确认首版目标：

- WAE Loop 默认关闭，不干扰一般 WAE 使用；
- 用户、项目或授权宿主对一个有边界 scope **显式启用**后，Loop 在该 scope 内持续有效；
- Active scope 中，每次相关责任交接都必须经过 WAE `handoff / refine / need_input / stop` checkpoint；是否执行 checkpoint 不是 Agent 的自由选择；
- Loop 不规定层数或轮数，Owner 一次完成责任即可直接 handoff；
- 真实项目运行必须留下可回放日志，方便从 WFF / EKRI / Slidethus 项目取回后分析；
- TPlan 继续拥有 Mission/task lifecycle，WAE trace 只记录 delegation-depth control facts 与 outcome。

研究载体仍为 #207 / Draft PR #208。Stable 主线尚未包含该能力。`pilot.1` 保留首轮 WFF admission audit 身份；`pilot.2` 关闭 trace/guard/recovery/activation-shape 完整性问题；WFF 后续反馈又证明 `.2` 对 refine 仍偏“记录发生了什么”，无法约束局部 semantic drilldown。`v1.11.0-wae-loop-pilot.3` 因此新增 Parent Artifact → Refinement Unit → Refine Result → Absorb 一等生命周期，并经两条独立审计路径确认适合作为下一轮真实项目 Pilot 推荐版本。这些都不是 Stable、不是 ROI Beta，也不触发 Stable + ROI Beta 默认发行规则。Git commit/tag 尚待有 Mindthus Git mutation 权限的执行入口完成。

## 已完成阶段

| 阶段 | 当前可支持的结论 | 对应记录 |
| --- | --- | --- |
| 三场景设计评审 | v0.2 通用委派深度规则形成 | `docs/internal/research/wae-loop-v0.2/` |
| 第一波固定证据 | 三类小型交接跑通，夹具局限保留 | `docs/internal/research/wae-loop-mvp/` |
| 第二波压力实验 | 取证→交接路径成立，无 C 专属增量 | `docs/internal/research/wae-loop-pressure-v2/` |
| 收敛标准评审 | G0—G4、失败/停止条件明确 | `docs/internal/research/wae-loop-evaluation-review-v1/` |
| F0—F3 G1 | B/C 均通过基础功能检查，C 无净增量证据 | `docs/internal/research/wae-loop-checkpoints-v1/` |
| 跟踪评审 | 确认纯合成环境继续证明真实价值的边际收益降低 | `docs/internal/research/wae-loop-release-followup-v1/` |
| 显式启用运行时 | 默认 OFF；activation/checkpoint + bounded Refinement Unit/Result/Absorb + handoff/outcome/finish + 固定 trace/bundle 已实现，待真实项目 Pilot | `skills/wae/resources/delegation-loop.md`、`skills/wae/scripts/delegation_loop.py` |

## 当前产品边界

### 默认链路

普通 WAE 仍走 Minimal WAE Check / Ownership Closure，WAE Loop 不被动唤醒。

### 显式启用链路

显式启用一次后，运行时在目标项目记录：

```text
.mindthus/wae-loop/
├── active.json
└── runs/<activation-id>/
    ├── activation.json
    ├── trace.jsonl
    ├── summary.json
    └── wae-loop-run.json
```

`wae-loop-run.json` 是后续调研优先取回的单文件材料；`trace.jsonl` 带 SHA256 event chain。默认只记录 artifact ref/hash、短的 observable remainder/consequence/work/outcome、可得成本和 telemetry coverage，不保存私有思维链或整份 artifact 正文。

当前 runtime 能验证“是否 Active、trace shape/hash chain、Refinement Unit lifecycle、Parent lineage、terminal checkpoint 与 finish 是否一致”；`guard-handoff` 在 Loop 关闭时正常放行，在 Active 时只允许完整 authoritative state 上最新 checkpoint 为 `handoff` 且 artifact ref/hash 仍一致的交接。**semantic sufficiency 与 semantic locality 是否合理仍由业务 Agent/审计判断**。宿主级 Stop/SubAgent/phase-exit 需要把真实 handoff carrier 接到该 guard，并在实际 Pilot 中分别验证后，才能声称宿主无法静默绕过。

## 下一阶段工作包

- [x] **P0：基础机制与 Trace Runtime**  
  统一 Mechanical / Agentic handoff closure；实现 explicit activation、project-local trace、portable bundle、hash chain、`guard-handoff`、outcome/cost/coverage 记录；默认链路保持关闭。

- [x] **P0b：内部 Pilot package freeze / runtime hardening**  
  `pilot.1`：历史前版，ZIP SHA256 `06974a23c66e8bd884340faf978860a9c7c2cb358188731da5bee3c28d91d7ff`。  
  `pilot.2`：完整性修复前版，ZIP SHA256 `74b2b9a85ed59464061eb433ccd85174efabca5372ce142a6f2e7920a9f25cd3`，保留 WFF integrity re-audit 身份。  
  **当前推荐：`v1.11.0-wae-loop-pilot.3`**。`.3` 在 `.2` authoritative-state 机制上新增单一 bounded Refinement Unit、显式 Refine Result、Absorb 与 Parent lineage；project-file Parent 在 Result 前不能直接变化，resolved Unit 未 Absorb 不能 handoff，blocked Unit 只能 need_input/stop。Runtime integrity audit PASS；method-choice audit PASS WITH PILOT-SCOPE CAVEAT。内部 ZIP：`/var/lib/devspace/runtime-artifacts/mindthus-internal-releases/v1.11.0-wae-loop-pilot.3/mindthus-wae-loop-pilot-v1.11.0-wae-loop-pilot.3.zip`；SHA256：`c7dd2124f18d06955cb90ecbda110b1043cda41e3b1031e300f7b79f083bdc63`；67,668 bytes。ZIP CRC 与包内逐文件 `SHA256SUMS` 均 PASS。该坐标是当前不可变内部发行权威，不覆盖 `.1/.2`。Git tag 仍待 Mindthus Git mutation 入口完成。

- [ ] **P1：WFF Pilot**  
  在真实 P1/P2→下阶段的一段任务上显式启用。重点看：是否减少下游发明上游语义、return/rework；是否出现过度下钻；host 是否能可靠维持 Active 状态。取回 `wae-loop-run.json` 与必要 bounded artifact/source 做复盘。

- [ ] **P2：EKRI Pilot**  
  对真实 knowledge acquisition scope 显式启用。重点看：取证深度、知识包保留粒度、下游源码补查量、事实/未知保真及总成本。不要用“读完整仓”冒充自适应深度。

- [ ] **P3：Slidethus Pilot**  
  在策划→制作交接显式启用。重点看：制作方是否还需重建主张/论证/证据口径；策划是否过度接管视觉实现；实际页面/PPT结果是否保持原意。

- [ ] **P4：真实证据 G2/G3 裁定**  
  从三个项目中选择成功、失败、错误放手、过度深入和 need_input 案例；复验重要边界与成本。Case Prep 只打包选择后的有界材料。若普通工作已经同样可靠而 Loop 只增加负担，则停止 Stable 推广；不继续造题直到 Loop 获胜。

- [ ] **P5：宿主强制与最小正式产品化**  
  若真实 Pilot 支持继续，再为实际使用宿主验证 Stop/SubAgent/phase-exit 等 handoff carrier，确保 Active scope 不能因上下文漂移被静默跳过。只实现真实需要的宿主约束，不先造通用 hook 大系统。

- [ ] **P6：发布**  
  通过真实价值、宿主行为与打包验证后，再确定版本、CHANGELOG、能力/证据边界。Stable 默认同步同版 ROI Beta shared core；ROI Beta 不作为绕过 WAE 资格的实验桶。

## 发布资格

首版可以准确发布的目标能力是：

> WAE Loop 默认关闭；显式启用一个 bounded scope 后，每次相关 responsibility handoff 必须执行 WAE sufficiency checkpoint，当前 Owner 仅为自身真实交接障碍继续工作，并留下可回放的真实项目 trace。

发布前至少需要：

1. 三类真实场景中，同一通用规则可以应用，而不是每个项目私有调参；
2. 日志能重建 activation → checkpoint → Refinement Unit → Refine Result → Absorb → handoff → downstream outcome；
3. 能观察到正确放手与必要深入，且没有普遍性的过度设计/越权；
4. 下游返工、上游语义发明或理解成本至少在部分真实场景出现可复验改善，或有其他预先接受的净价值；
5. 宿主实际加载/持久化/恢复行为验证通过，未覆盖部分明确标 `partial/unknown`；
6. 正式安装上下文、五布局、完整回归、公共包边界与 release verification 通过。

如果真实 Pilot 只证明“方法逻辑合理”，但没有实际净价值，研究可以以“保留简单方案/不发布默认能力”结束。

## 当前证据边界

G1 仍只支持合成 F 检查点下的功能可行信号；不支持统计高可靠、完整 Web、真实 PPT、全仓 EKRI、Codex App 强制宿主控制或历史 16 小时过载已修复。

当前显式启用 runtime 是为真实 Pilot 服务的研究实现。它不自动获得 Stable 发布资格；日志存在也不证明 WAE 判断正确。
