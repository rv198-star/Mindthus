---
name: using-mindthus
description: Use only for fact-sufficient hard-judgment routing among Mindthus lenses; structural, strategic, path, control, artifact, problem-definition, Mission-state, or allocation ambiguity. Never load for an ordinary request lacking facts or resource bounds to compare candidates; ask directly. SRA only after multiple judgeable candidates share a scarce resource.
---

## Core Claim

Truth Orientation / 真相优先：以事实和真相为先。用户观点是信号或假设，
用户目标、价值、风险姿态与权限是约束；二者不能混成事实证据。
上游注入背景只作线索或约束，当前输入优先；不能静默覆盖本轮明确指令。

## Mainline / 主路径

先看真实对象、底层约束和目标函数（Premise Calibration）：

- 明确、低风险、事实足够：直接执行。
- 缺文件、事实、运行证据或权限：先补输入，不能用方法填补。
- 有会改变判断或行动的 hard judgment point：用最小充分镜头。

### Input Framing Audit / 输入定框审计

只在 frame-risk 与 execution impact 同时存在时检查：当前说法是否把局部
真相当成全局定义？围绕用户实际目标保留、限定、重构，或因缺证据未决。
用户合法取舍可以主导行动；不是默认反对用户，也不是“更抽象就更全局”。
强烈立场不降低证据要求。充分的解释应保留。

Whole Elephant / Partial Truth Capture：区分所判断对象、真正控制结果的因素，
以及若局部框架接管会导致的错误行动。主次说清即可；不存在误导时允许局部定义
成立。把有效 Original Prompt Contract 留在约束层，不能接管判断。

### Skill Routing

| 判断缺口 | 镜头 |
| --- | --- |
| 问题未定义，或任务过大不可落地 | 3L5S |
| 多个可判断事项争同一稀缺资源 | SRA |
| 结构摇摆、伪二选一 | EDSP |
| 系统效率与局部优势的长期关系 | SELA |
| 方向已存在，但载体、暴露、路径或时机决定行动 | MPG |
| Agentic system 内 Workflow / Agentic / Evidence 控制错位 | WAE |
| 已成形、有界产物仍缺具体使用价值 | TVG |
| 需要持久 Mission 状态、恢复或人类权力边界 | TPlan |

按剩余判断缺口选方法，不按话题词选；已有依据足以回答就结束选路。
明确指定的方法仍按要求使用；握手只补缺口，不串固定流水线。
SELA owns direction pressure；MPG owns path-carrying action。
引用方法审计不自动让该方法成为当前 owner（Method Reference Boundary）。

### Execution Impact / 执行影响

输出清楚的判断、依据及行动后果，不堆内部术语。方法须改变策略、风险、
证据要求、下一动作、停止条件或交接；没有变化就退出方法层。
重复局部修补且无新证据时 Anti-Spiral；确认 canonical 根因后才 Root-Cause Replacement。

## Guardrails / 从属补漏

保护上述主路径：事实、价值、风险与 authority 分开；内部审计默认隐藏。
脚本只验证 shape/reference，不证明语义正确。普通措辞不决定通过与否。
真实权限、安全、证据和用户约束仍有 veto。pressure is not a route。

## Runtime Support / 按需支撑

主路径已经充分时不用展开。存在相应缺口再读（发布包别名 `resources/primitives/`）：

- 框架/问题层级：`docs/methodologies/primitives/frame-fitness-check.md`。
- 路由仍不清：`docs/methodologies/primitives/entry-triage.md`。
- owner 冲突：`docs/methodologies/primitives/aspect-ownership.md`。
- 行动者/时点/目标/取舍：`docs/methodologies/primitives/decision-context-calibration.md`。
- 局部真相争整体定义：`docs/methodologies/primitives/whole-elephant-protocol.md`。
- 压力/变量显影：`docs/methodologies/primitives/expression-pressure-and-gates.md`；
  AQM 假设数字仅显影关系，不能证明事实或计算决定。
- 主线/载体关系仍混淆：`docs/methodologies/primitives/mpg-scalar-commitment-unpack.md`。
- 已确认根因修复：`docs/methodologies/primitives/root-cause-replacement.md`。
- 明确需要 fidelity contract、trace、重放或校验：`resources/fidelity-contract.md`、
  `templates/fidelity-output.json`、`scripts/validate_using_mindthus_output.py`。
  `scripts/primitives/check.py` 仅提醒，不产生通过；未运行不能声称已验证。

## Boundaries

无 hard judgment 不介入；缺证据先补；另一个对象或方法接管时交回。
不建立全局路由器，不强制每题写字段、跑脚本或完整审计。
