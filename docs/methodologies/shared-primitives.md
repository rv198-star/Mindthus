# Mindthus Cognitive Primitives / 认知原语

## 这是什么

Cognitive Primitives / 认知原语，是 Mindthus 方法论之外的小而关键的判断碎片。
它们通过横切方式介入不同方法，为主方法提供刹车、施压、证据上限、表达降噪或
交付前定位，避免 agent 过度方法化或在错误位置继续自信推进。

This is not a new method layer. 它不是第七个方法，也不是总入口；它只是把重复出现的
小型 guardrail 集中成一个 Cognitive Primitive Index / 认知原语索引，供 `AGENTS.md`、
`using-mindthus` 和各 skill 引用。

当认知原语需要比文档提醒更硬一点时，使用
[Primitive Activation / 原语唤起机制](primitive-activation.md)：它通过少数轻量事件
显性唤起相关原语，但仍然只做 shape-and-wording-risk reminder，不替代 agent 判断。

详细规则不再堆在本页：本页是索引和 cross-primitive map；具体规则正文在
[`primitives/`](primitives/) 下。`scripts/primitives/manifest.json` 承载运行时
切面注册，避免入口 skill 复制长规则。

## 解决什么问题

如果每个 skill 都把同一套刹车、证据上限、表达纪律重新写一遍，项目会有三个问题：

- 同一规则出现多个名字；
- guardrail 慢慢变成新的主方法；
- 修改一处边界时，其他 skill 还停在旧口径。

Use cognitive primitives by reference. 本页负责定义短规则；具体方法只写“何时触发”，
不要复制完整定义。

## 核心判断

认知原语必须同时满足三点：

- 多个方法都会用到；
- 只保护主方法，不替代主方法；
- 足够小，不值得变成独立 skill。

Do not copy the full definition into each skill. 如果某个规则需要长流程、独立产物或
完整运行时，它就不是认知原语。

## 怎么用

先看本页索引判断是否有横切原语相关信号；如果只是简单任务，直接执行。若信号成立，
进入对应 detail file，只引用最小必要规则，并让主方法继续拥有主判断。

不要把多个原语输出平均成“各有道理”。先决定谁是当前 `judgment_owner`，其他原语只能
作为证据、边界、表达或验证支持。

## Cognitive Primitive Index / 认知原语索引

| Primitive | Primary owner | Short rule |
|---|---|---|
| Minimal Sufficient Lens | `using-mindthus` | 能直接判断就不要开方法；一个 skill 足够就不要串联；轻量检查足够就不要展开完整流程。 |
| Evidence / Claim Ceiling | `WAE` | 结论强度不能超过证据；缺事实、领域输入、运行证明或 stakeholder 判断时，降级或阻断。 |
| Perspective Pressure | `SELA` / `EDSP` | 单一视角过度自洽时，用角色压力或激励检查挑战判断。 |
| Anti-Spiral | `anti-spiral-self-audit` / `tplan` | 同一局部对象第三次、负反馈或加层冲动出现时，先停下回看上游。 |
| No Abstract Jargon Wall | `AGENTS.md` | 先做表达定位：我代表什么立场、文字直接服务谁、要把对方带到哪里；先用例子、类比或直接后果讲清楚，再使用 Mindthus 术语。 |
| Approximate Quantified Mapping / 非精准量化显影 | `AGENTS.md` / `using-mindthus` | 数字是假设，关系才是重点；用假设数字显影变量、方向、主导项、敏感项和口径差，不用数字证明或计算结论。 |
| Frame Fitness Check / 定框适配检查 | `using-mindthus` / `shared-primitives` | 当局部框架可能接管全局判断时，先判断应保留、限定、重构还是因证据不足阻断。 |
| MPG Scalar Commitment Unpack / MPG 标量承诺显影 | `shared-primitives` / `scripts/primitives` | 路径波动下的单点承诺先显影 `mainline / carrier / path_volatility / exposure / commitment`，再判断是否交给 MPG。 |
| Decision Context Calibration / 决策语境校准 | `shared-primitives` / `scripts/primitives` | 处境化判断先锁定决策者、时点、目标函数和可接受损耗；全局不是更抽象，而是对当前决策更有定义权。 |
| Whole Elephant Protocol / 全象流程 | `shared-primitives` / `scripts/primitives` | 局部真相可能冒充整体时，先产出可校验全象审计包，再进入正式判断。 |
| Gate Probes / 冻结前定位自省 | `AGENTS.md` / `shared-primitives` | 交付、冻结、继续、转交或停止前，确认当前产物是什么、现在处于什么状态、接下来服务谁的什么行动。 |
| Failure Smells / 误用信号 | `shared-primitives` / 各方法 | 看见“像完成但没推进”的信号时先自审；普通信号触发返修或降级，硬边界触发 block / stop。 |

## Detail Files / 规则正文

- [Aspect Ownership Matrix / 切面主导权矩阵](primitives/aspect-ownership.md): prevents active aspects from being averaged into a balanced but toothless answer.
- [Frame Fitness Check / 定框适配检查](primitives/frame-fitness-check.md): input framing, local-frame capture, and the Original Prompt Contract / 原始有效提示词合同.
- [Decision Context Calibration / 决策语境校准](primitives/decision-context-calibration.md): actor/timing/target/tradeoff answer flip and `global_for_this_decision`.
- [Whole Elephant Protocol / 全象流程](primitives/whole-elephant-protocol.md): Partial Truth Capture, Compact Semantic Triad / 三根硬支柱, Result Controller Viewpoint / 结果主控视角, and validator boundaries.
- [MPG Scalar Commitment Unpack / MPG 标量承诺显影](primitives/mpg-scalar-commitment-unpack.md): Scalar Commitment Under Path Volatility / 路径波动下的标量承诺显影 and `mainline / carrier / path_volatility / exposure / commitment`.
- [Expression, Pressure, And Gate Primitives](primitives/expression-pressure-and-gates.md): Approximate Quantified Mapping / 非精准量化显影, Pressure Surface Consolidation / 施压面收束, Gate Probes / 冻结前定位自省, and Failure Smells / 误用信号.

## Aspect Ownership Summary / 切面主导摘要

Multiple cognitive primitives may activate at the same join point. That does not
mean their conclusions should be averaged. Choose one `judgment_owner` for the visible
first thesis; keep `constraint` and `support` primitives as evidence, boundary,
wording, or validation support.

Fairness is not 50/50 allocation. The first sentence belongs to the active judgment
owner. Boundary repairs gain thesis weight only if they change the result controller,
decision target, evidence ceiling, or definition authority.

See [Aspect Ownership Matrix](primitives/aspect-ownership.md).

## Active High-Risk Primitives / 高风险切面

- Frame Fitness Check catches local-frame capture: a locally true frame may be claiming global authority. Framing-risk signals are not keyword rules.
- Decision Context Calibration owns situated decision judgments when the answer would flip by actor, timing, target function, or acceptable tradeoff.
- Whole Elephant Protocol owns definition-authority judgments when local truth claims whole-object essence.
- MPG Scalar Commitment Unpack is support-only; it shapes MPG route input and never decides the path-carrying judgment.

## 具体案例

### 案例 1: 局部真相冒充整体

当用户说“X 本质上只是 Y”时，不要先顺着 Y 解释。先看
[Whole Elephant Protocol](primitives/whole-elephant-protocol.md)，判断 Y 是局部载体、
局部机制、证据，还是确实拥有定义权。

### 案例 2: 多个切面同时触发

当一个问题同时像定框问题、处境化决策和表达问题时，不要合计成温和折中。先看
[Aspect Ownership Matrix](primitives/aspect-ownership.md)，确定 visible first thesis
由谁主导，再让其他切面降级为支持。

## 常见误用

第一种误用，是把认知原语当成新流程。它只在信号出现时触发。

第二种误用，是在各 skill 里复制本页定义。这样会重新制造重复。

第三种误用，是让原语决定主问题。原语只刹车、施压或限制 claim，主判断仍归对应 skill。

第四种误用，是把非精准量化显影升级成精确模型。数字只是让博弈关系可见；一旦开始
防守具体数字，原语已经失效。

第五种误用，是把 Gate Probes 当成真正的 Gate。定位自省只能帮助 agent 发现自己是否
站错位置，不能替代具体方法的退出判断、证据、用户授权或停止条件。

第六种误用，是把 Failure Smells 当成机械阻断表。普通误用信号只要求暂停自审和调整行动；
只有触发证据、权限、安全、用户约束或 claim ceiling 底线时，才升级为 hard veto。

## 边界

认知原语不替代 `SELA`、`3L5S`、`EDSP`、`WAE`、`TVG` 或 `tplan`。

它也不替代 Gate、事实、领域研究、运行证明、用户判断或授权。遇到缺输入的问题，
正确动作通常是补输入、降级结论或停止，而不是新增方法层。

## 与其他方法的关系

- `using-mindthus` 引用本页来避免入口 skill 变厚。
- `AGENTS.md` 引用本页来保持默认姿态短。
- 各方法页只保留与本方法相关的触发条件。
- `Primitive Activation` 用脚本在少数关键事件上唤起原语，但不判断真伪、价值或 exit。

## 导航

- 返回 [README](../../README.md)
- 查看 [Primitive Activation](primitive-activation.md)
- 查看 [Using Mindthus skill](../../skills/using-mindthus/SKILL.md)
- 查看 [Anti-Spiral 方法页](anti-spiral-self-audit.md)
- 未来小原语全拆：[#83 Split remaining small cognitive primitives into standalone files](https://github.com/rv198-star/Mindthus/issues/83)
