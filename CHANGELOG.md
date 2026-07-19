# Changelog

## Unreleased

## v1.5.1

冻结 tag：`v1.5.1`（尚未发布）

[冻结候选说明](docs/releases/v1.5.1.md)

说明：这是 1.x Stable 线的可靠性与交付修复候选。它保留完整的
`using-mindthus` 入口和全部正式方法合同，作为需要稳定显式调用、完整被动认知原语
覆盖或跨模型一致性的基线；不把 ROI Beta 的有损唤起策略带入 Stable。

### Stable 基线与终局交付

- 完成 TPlan Mission 时，终局交付合同现在要求生成实际执行报告和 SVG 执行过程图，
  并把两条链接放进最终回复；渲染失败必须显式说明，不能以“已完成”掩盖缺图。
- Stable 不以“更少 token”作为唯一目标：当任务需要完整方法入口、可预测的被动唤起
  或跨模型的保守行为时，继续使用这条完整基线。

### 同一 1.5.1 release train 的两种发布包

- `1.5.1 Stable` 与 `1.5.1 ROI Beta（GPT/Sol）` 是同一个 release train 的两种独立发布包，
  不是“高版本自动取代低版本”的关系。Stable 是默认、完整、可回退的产品基线；ROI Beta
  仅在高能力 Codex / GPT-Sol 上验证另一套加载 ROI 取舍。
- ROI Beta 从本 Stable tag 复用 shared core，只改变唤起/加载覆盖层；因此不能把它的 token
  节省宣传为 Stable 的升级，也不能把 Stable 用户自动迁移到 Beta。
- 每个 release train 先冻结并验证 Stable，再基于该冻结 commit 装配并验证 ROI Beta；二者
  分别以可复现源码 tag 固定，但未来若获授权，只对应一个 1.5.1 GitHub Release 和两份发布包。
- 在 ROI Beta 对指定场景证明价值之前，Stable 继续是需要完整能力与保守风险边界时的推荐选择。

### TPlan 一致性

- Mission 生命周期持久化失败可恢复，trace、evidence 与 Mission 状态不再静默分叉。
- 成本树按全局 leaf-most owner 归属 usage，避免跨投影和嵌套 agent turn 重复计费。
- durable sync 收窄到生命周期 journal，保留恢复保证而不为每条高频事件支付完整 fsync 成本。

### 安装与 TVG 图谱可靠性

- 发布包内 Python helper 会把自身对应的共享 runtime 提升到 `sys.path` 首位，不再依赖外部 `PYTHONPATH`，也不受同名外部包遮蔽。
- Atlas 标签 manifest 绑定源图 digest、尺寸、顺序与区域；选择板拒绝错图、越界、重排和 TOCTOU 不一致。
- Atlas trace v2 补齐 direct-delivery 状态和证据分类；仓库示例明确为 deterministic structural fixture，不冒充真实模型或审美证据。

### 验证与发布边界

- #125、#127、#126 按顺序修复并分别经过独立只读复审。
- 使用本地完整测试、双 release-pack 构建及隔离安装/回滚验证替代已停用的付费 GitHub CI。
- `v1.5.1` 仅冻结可复现的源码候选；不创建 GitHub Release、不上传资产。

## v1.5.0

发布日期：2026-07-19

[完整发布日志](docs/releases/v1.5.0.md)

说明：这是 1.x Stable 线的功能增量版本。它把 TPlan 的真实执行/成本树和 TVG 的
Profile 保真视觉图谱工作流带入正式发布，但不改变 `using-mindthus` 的可靠调用边界，
也不发布仍在探索中的 2.x ROI.2 Beta。

### TPlan 真实执行与成本树

- 新 Mission 使用追加式 `execution_trace.jsonl` 记录生命周期和脱敏成本事件；它不替代
  `evidence.jsonl`，也不保存 prompt、response 或原始 transcript。
- 新增 host-boundary model observer、traced command 和 sanitized span ingestion，明确区分
  `host_measured`、`platform_reported`、`inferred` 与不可得测量。
- 新增 `compact`、`standard`、`audit` 三种执行树视图；完整拓扑、局部 trace、旧 Mission
  snapshot 都有显式覆盖状态，未知成本保持未知。

### TVG Profile 保真视觉图谱

- 将通用影视画面导演控制收敛为 canonical `cinematic-visual-direction` Profile，并把
  巨物压迫规则降为可选 `colossal-pressure` 场景适配器；旧路径继续作为兼容入口。
- 新增 Profile 保真的 `9 -> 3 -> 9` 图谱探索、稳定 `Rnn-Eyy` 标识、可见 lineage、
  evidence hash、search freeze、delivery audit 与 finalization evidence。
- 图谱脚本只标注、拼板和校验确定性事实；审美选择和退出判断仍由 agent / 用户负责。

### 发布边界

- 显式调用 `using-mindthus` 或具体 skill 仍是可靠主路径；host 自然唤起仍是 best-effort。
- issue #109 的可复现实验进入仓库测试证据，但 tests、内部设计、benchmark 与运行记录不进入 release pack。
- ROI.2 仅确认为 2.x Beta 演进线；本版不创建 2.x tag、Release 或安装资产。

### 验证

- `python3 -m unittest discover -s tests -p 'test_*.py' -q`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`

## v1.4.6

发布日期：2026-07-14

[完整发布日志](docs/releases/v1.4.6.md)

说明：这是一次把 TVG 高级 Profile 案例和发布包产品完整性收束到一起的 release。显式调用
`using-mindthus` 或具体 skill 仍是可靠主路径，host 自动唤起仍是 best-effort，不构成自动唤起认证。

### TVG-Profile 高级案例

- `docs/methodologies/tvg.md` 现在明确指向四层 `cinematic-colossal-realism` 高级包，补回最高级、最复杂的 TVG-Profile 用法。
- 案例面向电影级出图的 prompt packet 与图像 review，不是邵氏 / 胡金铨等风格型影视案例的重复，也不声称任何图像模型稳定复现某种电影风格。
- release pack 携带 profile、四层运行资源、示例记录和确定性 support scripts；脚本仍不能替 TVG 判断美学成功、Profile 成熟度或退出。

### Codex 插件主题图标

- Codex plugin manifest 改用可审查的 SVG visual assets。
- composer icon 自带浅色底，避免深色主题下透明底黑线消失。
- 增加 `interface.logoDark`，让 Codex 在深色主题使用深色底、浅色线条的 Logo。

### 验证

- `python3 -m unittest discover -s tests -p 'test*.py' -q`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`

## v1.4.5

发布日期：2026-07-13

[完整发布日志](docs/releases/v1.4.5.md)

说明：这是一次可靠性与产品合同 patch release。它不新增方法、不改变 Mindthus 的核心
定位，也不把未通过的自动唤起研究包装成能力升级；主要变化是把诊断研究中可复用的部分
收回到更轻、更明确、更容易安装和验证的正式产品面。

### 产品收敛

日期：2026-07-13

本轮结束公开题库驱动的 activation / prompt 参数研究，把诊断成果收敛成产品合同。公开
50 场景结果仍是 `1.447 < 1.5`，Mindthus 仍未通过认证；`latest.md` 不再描述一个活跃的
V5 certification campaign。

- README 明确显式调用 `using-mindthus` 或具体 skill 是可靠主路径，host 自然唤起仅为
  best-effort，不构成正确性保证。
- 完成 #101：公共方法文档保留方法、边界和语义效果；direct-load、validator、fallback、
  trace 与输出形状义务留在 `skills/*` runtime surface。
- 新增 10–20 个自然任务的 real-use validation 入口；真实任务无需强造评分，记录判断变化、
  返工、额外负担、伤害和重复机制，只对重复问题立项。
- 选择性带回通用 timeout bytes 解码修复和插件图标；不带回未通过独立证据门的 semantic
  triage 研究 runtime。
- 旧诊断 issues 按“完成 / 部分交付 / 停止研究”重新归档；诊断完成不再被表述为问题已解决。

### 高频入口与发布包

- `using-mindthus/SKILL.md` 从 11,224 bytes / 1,094 words 收敛到 7,193 bytes /
  900 words；高频 preload 只保留介入边界、定框审计、定义权裁决、方法路由、执行影响和
  停止条件，详细语义改为 conditional resources。
- Frame Fitness 明确为 `frame-risk AND execution impact` 才运行；触发后必须记录
  `routing_decision`，避免既过度审计又丢失路由结果。
- 七份条件原语文档被镜像进 Claude plugin、Claude skills、Codex plugin、Codex skills
  和 OpenCode skills 五种发布布局；打包测试验证改写后的 fidelity 链接真实可达。
- Codex plugin 增加正式图标与 logo；通用 timeout bytes 解码修复进入公开代码。

### 评测与边界

- 公共 50 场景 fixture、runner、双层误唤醒口径和历史 artifacts 保留为可复查证据，
  但不进入 release pack，也不构成自动唤起认证。
- V4 treatment positive mean 仍为 `1.447 < 1.5`；register-hints、semantic triage 和
  后续 shadow 实验只作为诊断路线记录，未成为 v1.4.5 的生产承诺。
- “SKILLS 本质是提示词”与 4K/5K 判断场景的有效改进保留在 Whole Elephant、Decision
  Context、Definition Authority 和首句落锤合同中；不依赖题号 matcher。

### 验证

- `python3 -m unittest discover -s tests -p 'test_*.py' -q`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`
- 五种发布布局的入口 SHA 与条件资源链接通过独立复核。

## v1.4.4-diag diagnostic milestone

日期：2026-07-08

说明：`v1.4.4-diag` 是诊断 tag，不是正式 GitHub Release；不发布 release asset，
README 安装入口仍停留在 v1.4.3。本轮把 #91 之后的公开 50 场景基准、v2 -> v5
热更新实测、V5 targeted validation、register-hints 诊断收束到 main，作为外部审计
可复查的测量里程碑。

本轮最重要的结果不是“过线”，而是把测量口径变硬：V4 公开 full 50-case treatment
positive mean 为 `1.447`，仍低于 `1.5` 公共目标；target/disputed 三次重跑测出
`0.467 / 0.600 / 0.667` 的噪声带，因此较小单轮波动不再被解释为已证实进步。
V5 register-hints 诊断在 9 个 public no-load target 上以 host-style hint 达到
expected-owner-loaded `1.000 / 1.000 / 1.000`，但这是干预式诊断，不是自然唤起，
也不是 certification candidate。

### 诊断与证据

- 新增 public 50-case bidirectional judgment fixture、benchmark 文档、CLI runner
  split generate/judge 记录，以及 v3/v4 空 HOME 运行 artifacts。
- 新增 V5 certification protocol，强制区分 final-answer false wake-up 与
  runtime-event false wake-up，并记录 owner-fidelity、required-visible-action、
  first-sentence lock、anti-mush 与 over-forced-verdict 指标。
- 新增 V5 target trigger register 与 `--v5-register-hints` 诊断模式，用于验证
  register + host hint 是否可作为机械 activation carrier。
- `docs/benchmarks/latest.md` 定格为：register-hints 是最新诊断证据；V4 full
  50-case 仍未过线；certification blocked pending natural activation,
  #17 loaded-action repair, and an independently owned shadow set.

### 边界

- `v1.4.4-diag` 不声明 Mindthus 已通过公共基准，不替代正式 release pack。
- V5 中保留的 3L5S/EDSP/SELA/MPG wording clauses 标记为未验证、待机械化替代；
  它们不计入 certification progress，除非后续 repeat telemetry 显示移动超出噪声带。
- #91 按“部分交付”处理：题库、runner、artifacts、latest surface 已落地，但认证仍被
  自然唤起、#17、独立 shadow set 阻断。

## v1.4.3

发布日期：2026-07-06

[完整发布日志](docs/releases/v1.4.3.md)

说明：本版替代并吸收已撤回的 v1.4.2。它包含 v1.4.2 的 Whole Elephant / Decision Context / Aspect Ownership / MPG Scalar Unpack 架构收束，同时补上方法引用与方法激活边界：读取某个方法作为验收 rubric，不等于当前任务由该方法主导。

v1.4.2 GitHub Release 已撤回，不再作为安装入口。用户应直接使用 v1.4.3。

### 吸收自 v1.4.2 的内容

- Whole Elephant 收束为 `Compact Semantic Triad / 三根硬支柱`：`canonical_object / result_controller / misdirection_if_local_wins`，用于锁定完整对象、结果主控和局部真相获胜后的优化偏移。
- 新增 `Contrastive Consequence Probe / 后果对比探针`：比较 `local_frame_wins` 与 `whole_object_wins` 后的行动方向，避免局部正确反复施压后接管定义权。
- 新增 `Decision Context Calibration / 决策语境校准`：处境化判断先确认决策者、时点、目标函数和可接受损耗，再判断哪个框架拥有当前判断权。
- 新增 `Aspect Ownership Matrix / 切面主导权矩阵`：多个横切原语同时触发时，只允许一个 `judgment_owner` 主导首句判断，其他切面降级为约束或支持。
- 新增 `MPG Scalar Commitment Unpack / MPG 标量承诺显影`：把买不买、留不留、要不要继续等压缩承诺显影为 `mainline / carrier / path_volatility / exposure / commitment`，只做 MPG 路由输入，不替 MPG 下结论。
- `docs/methodologies/shared-primitives.md` 拆成轻索引，复杂原语细节移入 `docs/methodologies/primitives/`。
- Whole Elephant 独立 validator 与 `using-mindthus` 集成 validator 共用 `scripts/primitives/whole_elephant_validator.py`，减少 validator drift。

### 修复

- `using-mindthus` 新增 `Method Reference Boundary / 方法引用边界`：日志取证、会话核验、方法使用确认等任务可以参考方法规则，但当前 `judgment_owner` 仍由任务对象决定。
- 新增 MPG-AQM 会话取证负测：确认“某会话是否启用了 MPG-AQM”应走 evidence/session forensics，不应声明当前任务由 MPG 主导。
- 保留并验证 TVG 外部审查边界：普通 release/code/log review 不因 `review / audit / check` 词面触发 TVG，除非存在 active TVG loop 和 bounded artifact value-gain target。

### 工程

- `skills/mpg/SKILL.md` 瘦身到 10KiB 以下，把完整说明留在 `resources/methodology.md`。
- `using-mindthus` 增补 `## Boundaries` 层级；入口预算调整为 11KiB / 1100 words，避免为了硬压 10KiB 删除关键路由锚点。

### 边界

- 本版不关闭 #85；#85 继续跟踪真实会话中 `reference/rubric read` 与 `method activation` 的边界表现。
- 本版不新增独立 skill，也不改变 TVG/MPG 的真实适用场景。

### 验证

- `python3 -m pytest -q`
- `python3 -m unittest tests.test_mpg_contract tests.test_mindthus_router_contract tests.test_sela_contract -v`
- `python3 -m pytest tests/test_packaging_docs.py tests/test_method_layering_contract.py -q`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`

## v1.4.2

发布日期：2026-07-06

[完整发布日志](docs/releases/v1.4.2.md)

撤回说明：v1.4.2 GitHub Release 已删除，内容已并入 v1.4.3；不要使用 v1.4.2 作为安装入口。

说明：本版把 v1.4.x 的“防局部正确冒充整体”继续收束到更稳的工程形态：Whole Elephant 不再靠堆字段维持判断，而是以 `canonical_object / result_controller / misdirection_if_local_wins` 三根硬支柱为主线；同时新增 Decision Context Calibration、Aspect Ownership Matrix 和 MPG Scalar Commitment Unpack，减少多切面平均、处境化判断漂移和 MPG 唤醒不足。

### 新增

- 新增 `Decision Context Calibration / 决策语境校准`：当答案会随决策者、时点、目标函数或可接受损耗改变时，先锁定当前决策语境，再判断谁更有定义权。
- 新增 `Aspect Ownership Matrix / 切面主导权矩阵`：多个横切原语同时触发时，只允许一个 `judgment_owner` 主导首句判断，其他切面降级为约束或支持，避免“各打五十大板”。
- 新增 `MPG Scalar Commitment Unpack / MPG 标量承诺显影`：把“买不买、留不留、要不要继续”等单点承诺显影为 `mainline / carrier / path_volatility / exposure / commitment`，只改 MPG 路由输入，不替 MPG 下结论。
- 新增 `skills/using-mindthus/resources/calibration-pairs.yaml`，把 v1.4.1 的 SKILLS/prompt reduction 校准样例结构化为内部示范资源。
- 新增 `docs/methodologies/primitives/` 第一阶段拆分：把 Whole Elephant、Frame Fitness、Decision Context、Aspect Ownership、MPG Scalar Unpack 等高复杂原语从 `shared-primitives.md` 中拆出。

### 修复

- 重构 Whole Elephant 为 Compact Semantic Triad / 三根硬支柱，并加入 Contrastive Consequence Probe / 后果对比探针，减少 guardrail 变成新 judgment center 的风险。
- 消除 Whole Elephant 独立 validator 与 `using-mindthus` 集成 validator 的 drift：CLI wrapper 和 integrated validator 共用 `scripts/primitives/whole_elephant_validator.py`。
- runtime 日志脚本现在追踪 calibration pairs、primitive checker、Whole Elephant validator、using-mindthus validator 和 runtime helper 文件，严格模式会检查 tracked file 是否缺失。
- release pack 显式携带 split primitive docs、calibration pairs 和共享 Whole Elephant validator。

### 边界

- 本版不关闭 #83；#83 继续跟踪剩余小原语的全量拆分。
- 本版不新增独立 skill，也不把 Whole Elephant 变成默认入口。
- `MPG Scalar Commitment Unpack` 是 support primitive，不是新的战略判断方法。
- `Decision Context Calibration` 不抹掉事实边界，只决定当前处境下哪个事实或框架拥有判断权。

### 验证

- `python3 -m pytest -q`
- `git diff --check`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`
- `python3 scripts/log-mindthus-runtime.py --strict`

## v1.4.1

发布日期：2026-06-29

[完整发布日志](docs/releases/v1.4.1.md)

说明：本版是 v1.4 输入定框审计的强化发布。它把真实有效的“先审题、后回答”提示词纪律回灌进 `using-mindthus`，并补上解释权、主导承载和系统主体三类校准，减少 agent 被局部正确、专业口吻或实现层事实带偏后继续自洽的风险。

### 新增

- `using-mindthus` 明确输入审计第一任务：先判断用户是否把问题带到错误层级，再回答。
- 输入审计输出顺序补齐为 `true_question -> implicit_premises -> local_validity_and_layer_shift -> reframed_question -> formal_answer`，并新增 `leading_point` 识别。
- 新增 `scripts/log-mindthus-runtime.py`，可输出 repo、本地 marketplace 和 Codex cache 的 sha256、mtime 与关键 marker，用来确认热更新是否真正生效。

### 修复

- 强化 `Explanatory Authority Check / 解释权校准`：局部正确不自动拥有整体解释权。
- 强化 `Dominant Carrier Check / 主导承载校准`：先判断当前对象真正由什么机制承载，避免把辅助机制误当主体。
- 强化 `System Subject Check / 系统主体校准`：当对象是系统时，先判断主稳定性来自 workflow、state、gate、evidence、authority 还是模型局部推理。
- release pack 现在携带 runtime diagnostic script，Codex / Claude Code 插件包可直接用于版本指纹核验。

### 边界

- 本版不针对某个 skills/prompt 示例作弊；新增规则必须服务通用定框、解释权和系统主体判断。
- 本版不声明已稳定达到 95+ 行为水平；SKILLS/prompt reduction 实测显示，连续 scope correction 下仍可能退回局部正确。
- 本版不把输入审计扩展成所有任务的模板；低风险、事实足够、直接执行类任务仍直接做。
- runtime 日志脚本只证明文件版本、hash 和 marker 是否一致，不证明模型一定按规则执行。

### 验证

- `python3 -m unittest discover -s tests -q`
- `git diff --check`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`
- `python3 scripts/log-mindthus-runtime.py --strict`

## v1.4.0

发布日期：2026-06-29

[完整发布日志](docs/releases/v1.4.0.md)

说明：本版把 Mindthus 的入口判断能力正式提升为公开版本面：`Frame Fitness Check / 定框适配检查` 作为认知原语进入总纲，并在 `using-mindthus` 中落地为 `Input Framing Audit / 输入定框审计` 强约束入口协议。它解决的是 agent 容易被局部正确、带有倾向性的输入、实现层真相或单一证据信号带偏的问题。

### 新增

- `Frame Fitness Check`：新增局部框架适配检查，用来判断当前 framing 应保留、限定、重构，还是因证据不足阻断。
- `Input Framing Audit`：`using-mindthus` 在方法路由前支持结构化输入审计，包含 `true_question`、`packed_premises`、`layer_risks`、`frame_status`、`reframed_question` 和 `routing_decision`。
- primitive activation manifest 增加 `output_shape`、`frame_status_values` 和 `routing_effect`，让 runtime support 能暴露形状约束，但不替代 agentic judgment。

### 修复

- README 整体叙事从“方法工具箱 / 选对刀”升级为“先纠偏、再路由”：强调 Mindthus 能帮助 AI 避免被局部正确和带有倾向性的输入带偏。
- 明确 `Framing-risk signals, not keyword rules`：关键词只是高置信线索；没有关键词但出现打包结论、层级偷换或局部机制冒充整体解释，也应触发。
- 明确边界：没有 frame-risk signal 不触发；没有执行影响就省略；用户价值、偏好、审美和风险姿态是判断约束，不能被当成偏见抹掉。
- primitive validator 增加 `routing_effect` schema 约束，要求 key 与 `frame_status_values` 对齐，同时保持 shape-only，不判断语义正确性。

### 边界

- 本版不新增 `frame` 或 `anti-sycophancy` 独立 skill。
- 本版不把输入审计变成所有任务的强制模板；清楚、低风险、事实足够的任务仍直接执行。
- 本版不允许输入审计替代证据获取、领域事实或正式方法分析。

### 验证

- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`

## v1.3.0

发布日期：2026-06-27

[完整发布日志](docs/releases/v1.3.0.md)

说明：本版把 Mindthus 最近三条相关改动收束成一次统一 release：plugin startup context 新增轻量 Activation Router，WAE 被收窄到 agentic-system control-boundary，TVG 的 exit audit 被收回到 TVG loop 内部。它因此更适合记作一次 minor release，而不是零散 patch。

### 新增

- Claude Code plugin 增加轻量 activation router `SessionStart` hook：只提醒 hard judgment point 时优先考虑 `mindthus:using-mindthus`，清楚低风险任务直接做，事实不足先补证据；它不是强制流程，也不复制 Superpowers Brainstorm。
- Codex plugin `defaultPrompt` 同步为同一套 activation router 语义的短版，用于提高 Mindthus 在 hard judgment point 场景的唤醒概率；Codex 端文案保持在 128 字节以内，避免被插件加载器忽略。

### 修复

- WAE 路由边界收紧为 agentic-system control-boundary mismatch：没有 agentic system，不进 WAE；没有 controller mismatch，也不进 WAE。普通概念边界、组织责任、产品分类或 issue 粒度问题不再被 WAE 吸走。
- TVG exit audit 明确收回为 TVG loop 内部退出判断，不再因为用户说了 audit / review / check 就被外部化为通用审计路线；release、code、workflow、factual、method、strategy 和 requirement-boundary 审计按对象路由。
- tplan 术语和 runtime 合同同步收口：`artifact_value_gain` 是 decision hook，不是 Mission Pulse `next_gate`；新增负测锁住这条边界，避免把 TVG 内部动作误接到 Mission mutation 路径。

### 边界

- Mindthus 不 vendoring Superpowers Brainstorm，也不占用 Superpowers 命名空间；设计/创意/行为变更等需要展开需求的任务仍推荐搭配 Superpowers Brainstorm。
- 如果上游已有 brainstorming / design workflow，Mindthus 不重复需求澄清，只在剩余问题属于 hard judgment point 时介入。
- 本版关闭的是 `#64`、`#65`、`#66` 这组三联边界修复，不宣称 `#50` 的 wake-up lift 已完成真实 replay 级行为认证。

### 验证

- `python3 -m unittest discover -s tests -v`
- `git diff --check`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-release-plugins-check --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-release-skills-check --force`

## v1.2.0

发布日期：2026-06-24

[完整发布日志](docs/releases/v1.2.0.md)

说明：本版把 Mindthus 从单一 skills-pack 分发，扩展为 Codex / Claude Code 可识别的插件产品壳，同时保留 `skills/` 作为唯一行为源码。推荐安装入口是 GitHub Release 里的预构建 release pack；plugin mode 使用 `mindthus-plugins-1.2.0.tar.gz`，skills-pack mode 使用 `mindthus-skills-1.2.0.tar.gz`。Codex 新增 `codex-plugin/mindthus` release artifact；Claude Code 继续使用既有 plugin artifact；OpenCode 继续使用 skills-pack，不用 command、hook 或 custom tool 模拟 native skills。插件里的提示只是一句 router-only 纪律，不是强制 startup hook。

### 新增

- Codex plugin packaging：release builder 新增 `codex-plugin/mindthus/`，包含 `.codex-plugin/plugin.json`、同源 `skills/`、公开 methodology docs、license 和 release scripts。
- Claude Code plugin 文档化：明确 `claude-code/claude-plugin/` 是插件模式，Claude Code plugin mode 使用 `/mindthus:using-mindthus` 这样的命名空间；personal skills mode 仍是 `/<skill>` 或自动调用。
- README 安装说明改为 release-pack-first：plugin mode 下载 `mindthus-plugins-1.2.0.tar.gz`，skills-pack mode 下载 `mindthus-skills-1.2.0.tar.gz`；源码 clone 只作为开发者 fallback。
- Codex plugin release pack 新增 `.agents/plugins/marketplace.json`，使 `codex plugin marketplace add <release>/codex-plugin` 后可以直接 `codex plugin add mindthus@mindthus`。
- 轻量 router-only 指引：Codex plugin metadata 可以注入一句路由纪律，提醒战略判断、结构歧义、路径波动、控制边界和产物价值厚度问题优先用 `using-mindthus` 选择最小充分方法；清楚低风险任务直接执行。

### 修复

- Codex plugin 的 discoverable `skills/` 目录只包含真正的 skill；共享 runtime support 放在 plugin root 的 `_runtime/`，避免 `skills/_runtime` 被识别成缺少 `SKILL.md` 的伪 skill。
- release packaging tests 增加 Codex plugin manifest、artifact cleanliness、OpenCode plugin 缺省不生成、以及 plugin / skills-pack 文档边界检查。
- release packaging 改为插件包和 skills 包分离：Codex + Claude Code 插件合在 `mindthus-plugins-1.2.0.tar.gz`；Codex + Claude Code + OpenCode skills-pack 合在 `mindthus-skills-1.2.0.tar.gz`。
- release pack 不再携带 methodology 文档图片等二进制大图资产；图文版文档保留在 GitHub 仓库和官网文档入口。

### 边界

- OpenCode 继续使用 skills-pack。当前不发布 `opencode-plugin/`，因为 OpenCode plugin API 尚未验证能原生贡献 `SKILL.md` skills；不会用 hook、command 或 custom tool 模拟 native skills。
- plugin packaging 是 distribution shell，不是 skills fork。`skills/` 仍是唯一行为源码。
- router-only 指引不能替代事实补充、证据约束或 agentic judgment，也不能强制低风险确定性任务进入 Mindthus。

### 验证

- `python3 -m unittest tests.test_packaging_docs -v`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/build-release-pack.py --package plugins --out /tmp/mindthus-plugins --force`
- `python3 scripts/build-release-pack.py --package skills --out /tmp/mindthus-skills --force`
- Codex plugin validator passed for generated `codex-plugin/mindthus`.
- Claude Code strict validation passed for generated plugin and marketplace.
- Codex CLI smoke passed: temporary marketplace add / list / install enabled `mindthus@mindthus-smoke`.

## v1.1.2

发布日期：2026-06-23

[完整发布日志](docs/releases/v1.1.2.md)

说明：本版把 TPlan 的长任务回顾控制面正式收束为 `Snapshot / Pulse / Gate`：脚本只观察运行时状态，Pulse 只把可观察信号路由到既有 Gate，真正的继续、反螺旋、回路、选择、Mission Review 或停止仍由 Gate 和 agentic judgment 决定。它也补上 router wake-up 认证门槛，避免薄样本或缺桶样本冒充行为提升证明。

### 新增

- TPlan Mission Pulse：新增只读 `mission_pulse.py` 路由面，输出 recent evidence summary、active task log summary、evidence-link lint、review trigger candidates、winning / suppressed candidates、arbitration trace 和 shape findings。
- TPlan Snapshot / Pulse / Gate 文档：公开方法页补齐当前实现口径，明确 routine checkpoint 只停留在 Snapshot；同路径继续、第三次局部触碰、弱 evidence delta、负反馈、blocker / surprise、shared risk、branch cleanup、freeze / handoff / stop 等事件才进入 Pulse。
- Mission Pulse 场景回放：新增并固化 routine checkpoint、same-path continuation、Anti-Spiral third touch、feedback loopback、blocker Mission Review、shared risk health check、branch selection、requires-human stop、无 active task runtime integrity 等多场景测试。

### 修复

- Pulse 仲裁模型从零散场景判断收束为统一候选模型：Candidate Collection -> Candidate Shape Validation -> Gate Arbitration -> Pulse Output -> Gate。低优先级候选保留在 `suppressed_candidates` 和 `arbitration_trace`，避免信号被静默丢失。
- Anti-Spiral runtime gate 现在由 active task logs 中的 `object_id` touch count 和 additive layering 信号触发，第三次触同一局部对象会路由到 `anti_spiral_audit`。
- Lite Mission narrative state 与 runtime state 同步，避免轻启动后的恢复说明和机器状态脱节。
- Router wake-up A/B runner 增加 `minimum-pairs` 与 overuse stress 桶覆盖门槛：known / holdout / real-use replay 低于最小 paired routing moments 不允许认证，overuse 缺 direct、missing-evidence、deterministic、`tvg` 或 `3l5s` 桶也会失败。

### 边界

- Pulse 不是 health score、pass/fail verdict、语义判断中心或 mutation authority。`next_gate=continue` 也不能绕过高影响 review、authority 或 stop 边界。
- Anti-Spiral 不替代正常调试；明确 failing test、明确报错和机械验证进展仍可沿因果链修复。它拦的是没有新证据、只靠局部补丁和加层冲动继续的循环。
- Router certification gate 只防止 claim 过强；它不声明低频方法 wake-up lift 已被真实 replay 证明。

### 验证

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.tplan.test_mission_pulse -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.tplan.test_mission_health_pulse_experiment -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.tplan.test_continuation_authorization_ab_simulator -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_router_wakeup_ab_runner -v`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 scripts/build-release-pack.py --out /tmp/mindthus-v1.1.2-check --force`

## v1.1.1

发布日期：2026-06-17

[完整发布日志](docs/releases/v1.1.1.md)

说明：本版把最近两波 agent runtime 改动收成一个小版本：TPlan 增加 Mission 级共享记忆文件和启动前身份预检，Mindthus router 增加 SELA / MPG / EDSP 的低频方法唤醒 canary。它们都服务同一个目标：让 agent 在长任务和方法选择时少丢上下文、少被高频默认路径吸走。

### 新增

- TPlan Mission Shared Context Memory：在项目级 `.tplan/shared_contexts/` 下保存 Mission 共享记忆 Markdown，路径形如 `.tplan/shared_contexts/tplan_mission_shared_context-<mission_id>.md`。`preflight_mission.py` 在启动前区分 `continue_existing`、`create_new` 和 `needs_agentic_selection`，`init_lite.py` / `init_mission.py` 可以加载或创建对应 context。
- Router wake-up canary：`using-mindthus` 增加 `SELA`、`MPG`、`EDSP` 的轻量唤醒探针，并在 `AGENTS.md` 中明确 `3L5S` 不是默认判断归宿，避免结构歧义、战略系统/局部取舍和主线承载问题被高频方法吸收。
- 新增 router wake-up A/B 分析脚本、fixture、实验设计和弱提示校准记录，用于后续比较 baseline / treatment 的 positive wake-up recall、skip precision、execution impact、adjacent absorption 和 overuse 风险。

### 边界

- `source_contexts` / `derived_from` 只是新 Mission 的背景记忆和来源关系，不继承旧 Mission 的 acceptance authority；脚本只做路径、字段和 preflight shape 检查，不判断两个 Mission 是否语义相同。
- 这次 canary 不声明已经证明低频方法唤醒率显著提升。已完成的 known set 和 weak-cue v1 pilot 都触发 baseline-ceiling，说明当前样本没有足够区分度；后续需要真实 replay 或更间接的多轮边界样本继续认证。

### 验证

- `python3 -m unittest discover -s tests -v`
- `python3 -m unittest tests.tplan.test_mission_shared_context tests.tplan.test_mission_shared_context_agent_simulator tests.tplan.test_skill_contract -v`
- `python3 -m py_compile skills/tplan/scripts/*.py scripts/router-wakeup-ab.py tests/tplan/mission_shared_context_agent_simulator.py tests/test_router_wakeup_ab_runner.py`
- `python3 scripts/build-release-pack.py --out /tmp/mindthus-v1.1.1-check --force`

## v1.1.0

发布日期：2026-06-11

[完整发布日志](docs/releases/v1.1.0.md)

说明：本版让 Mindthus 在两类真实使用中更稳：TVG 可以按任务自定义“什么才算好”，TPlan 可以让子任务之间共享已经发现的阻塞和风险。同时修复 TPlan 晚期小问题反复沿同一路径续跑的漂移，并补齐 Codex 安装、技能发现和安装包边界上的小问题。

### 新增

- TVG Value Profile：让 TVG 除了默认通用实用价值外，可以支持自定义价值锚点：这个任务里什么算好、什么算跑偏、哪些约束不能破、优先增强哪类价值。也就是用户可以自己定义希望文本靠近的“好”标准，并让 TVG 按这个方向迭代优化。
- TVG 示例 profile：随包包含默认通用价值 profile，以及邵氏清水湾棚拍时代武侠 / 神怪、胡金铨武侠电影两个影视提示词 / 分镜方向的示范 profile。它们用于展示有明确边界的 profile 怎么写，不是电影史分类结论，也不是对所有图像模型的风格稳定性保证。
- TPlan Shared Risk Context：让子任务共享阻塞项和风险。某个子任务发现的阻塞、环境问题、证据风险或共享依赖风险，可以提升到 Mission 级别，让其他子任务和后续决策也能看到。在评估下一步是否继续、切换路径、健康检查、暂停或收束时，Agent 会综合这些阻塞和风险，判断任务可行性和综合价值。

### 修复

- TPlan continuation authorization：晚期小缺陷、证据形态缺陷或局部未收敛时，Agent 不能只是沿同一路径“再试一下”；继续前必须说明为什么这条路径仍然值得继续，以及授权依据是什么。
- Codex 安装路径：`scripts/install-skills.sh codex` 现在默认安装到 `${CODEX_HOME:-~/.codex}/skills/mindthus`，不再把 Codex skills 链到 `.agents` 路径。
- Codex App 技能发现：修复 `tplan` 在 Codex CLI 可见、但 Codex App 看不到的问题。`tplan` frontmatter 现在保持严格 YAML 兼容，Mindthus 各个 `SKILL.md` 入口也都控制在 8KiB 以内，避免入口文件过长影响发现。
- Release pack 边界：安装包构建会过滤 `tests/`、`logs/`、`.tplan/`、`.tvg/`、运行产物、图片/视频和临时文件；包内只保留必要的 skill、公开方法文档、安装脚本和 `tplan/templates/evidence.jsonl` 模板。

### 边界

- TVG profile 定义价值锚点、输出厚度倾向和迭代检查问题，但脚本仍只校验 profile 形状；不会替 agent 判断 profile 是否审美成功、证据是否足够、是否可以退出，或是否具备稳定视觉泛化能力。
- TPlan 共享风险上下文让风险在 Mission 内可见，不等于自动停止或自动改计划；是否继续仍要看目标价值、证据、阻塞和用户授权。

### 验证

- `python3 -m unittest discover -s tests`
- `python3 scripts/build-release-pack.py --out /tmp/mindthus-v1.1.0-check --force`
- release pack 审计测试会检查包内没有测试、日志、运行产物或生成图片混入。

## v1.0.1

发布日期：2026-06-08

[完整发布日志](docs/releases/v1.0.1.md)

说明：本版是当时的 1.0 系列推荐安装版本：它包含 `v1.0` 的正式发布面，包括 MPG、授权口径、忠实度评审自动化、退出审查和跨模型小样本；同时新增一个极简使用日志入口，让每次真实 fidelity judge 结果可以脱敏记录、持续积累，为后续“用数据判断哪些方法有约束增益”打底。

### 新增

- 新增 `scripts/log-fidelity-usage.py`，可追加或校验 `data/fidelity-usage-log.jsonl` usage log。
- usage log 记录 `scenario`、`method`、`model`、`baseline_score`、`constrained_score`、`max_score`、`constraint_helped`、`source` 和 `tags` 等字段；没有 baseline 时也允许记录 constrained 分，降低真实使用记录门槛。
- 新增 `data/README.md` 和 `docs/internal/fidelity-usage-log.md`，明确日志只保存脱敏摘要，脚本只检查字段形状，不判断方法价值。
- release pack 增加 `scripts/log-fidelity-usage.py`，三平台包可以同时保留 judge 校验和 usage log 记录入口。

### 边界

- `v1.0.1` 只建立数据飞轮的最小记录习惯，不声明已经有跨方法统计结论。
- usage log 是项目资产种子，不是 benchmark 结论；样本量不足时不能用它证明某个方法有效或无效。

## v1.0

发布日期：2026-06-08

[完整发布日志](docs/releases/v1.0.md)

说明：本版新增 `MPG / 主线-路径博弈`，把“看见长期主线”之后最容易出错的路径波动、对抗力量和载体承受力，收束成可交付的主线承载方法。

`v1.0 Method Fidelity Framework` 把现有 `tplan`、`3L5S`、`TVG` 的校验经验与 `SELA`、`MPG` 的 fidelity pilots 收束为统一方向：约束关键判断动作，不约束判断结论。该版本完成 v0.9 之后的发布前置项，可以作为 Mindthus 第一版正式发布面。

### 1.0 blocker closure

- LICENSE blocker closed：新增 AGPLv3 `LICENSE`，并通过 `COMMERCIAL-LICENSE.md` 明确闭源商业使用需要单独授权。
- judge automation blocker closed：新增 `scripts/run-fidelity-judge.py`，自动生成 judge prompt 并校验 judge JSON 结果。
- challenge_premise escape blocker closed：SELA judge rubric 和 runner 要求 `not_applicable`、`transfer`、`challenge_premise` 必须做 escape review，不能自动放行。
- cross-model baseline blocker closed：新增 SELA 跨模型 baseline 小样本，包含 `opencode/deepseek-v4-flash-free` 记录，并明确不声明普适鲁棒性。

### 新增

- 新增 `MPG / 主线-路径博弈` 独立方法、skill 入口、方法页、资源页和压力测试，用来处理主线兑现前的路径波动。
- 新增 AGPLv3 + 商业双授权口径：开源使用、开源改造和开源部署按 AGPLv3；闭源商业产品、私有 SaaS、商业平台集成或不公开对应源代码的商业用途需要单独商业授权。
- 新增 `scripts/run-fidelity-judge.py`，用于生成可复现 judge prompt 并校验 judge JSON 结果；脚本只检查 rubric 记录形状、分数和 escape-review 覆盖，不替代语义判断。
- 新增 SELA 跨模型 baseline 记录：在既有 v0.9 packet 之外，补跑 `opencode/deepseek-v4-flash-free` 的 baseline-vs-constrained 小样本，作为 v1.0 发布证据而非普适鲁棒性声明。
- 新增 Method Fidelity Harness 设计、SELA/MPG pilot contract、共享 Shape & Evidence Risk Report、fidelity core、以及 3L5S / TVG 既有 validator 对齐记录，作为 v0.9 验收材料。
- 新增 3L5S、EDSP、WAE、TVG、using-mindthus 的 fidelity output template 与 shared-core validator；本轮不迁移 `tplan` runtime。
- MPG 交付 `Path-Carrying Strategy / 主线承载方案`，不只判断行动者能不能穿过波动，还要给出暴露预算、可选性、触发器、熔断点和证据缺口。
- 新增 `Human-Readable First / 先讲人话` 输出纪律：先讲“这对你意味着什么”，再给结构字段，避免方法分析变成术语墙。
- 新增 `Reasoning Durability / 推演耐久性` 回放标准：用当时信息面检查推演逻辑是否禁得起推敲，而不是用事后结果命中率粗暴打分。
- 新增 `MPG-AQM Visibility Layer / 主线-路径显影层`：复杂主线-路径关系可用非精准量化显影显出主线强度、路径阻力、载体脆弱度、信息缺口和触发器强度，但 MPG 仍负责判断，AQM 只负责显影变量。

### 调整

- `AGENTS.md` 与 README 同步 MPG 的独立定位、SELA 之后的使用关系、表达纪律和滥用边界。
- `using-mindthus` 路由补齐 MPG：SELA 看整体趋势，MPG 判断并设计主线如何穿过具体路径波动。

### 验收

- 新增 MPG contract tests，锁定 skill frontmatter、方法分层、交付物、边界、表达纪律和 AQM 主从关系。
- 新增 packaging docs sync test，避免 README、AGENTS 和 changelog 在 MPG 迭代后停留在旧口径。

## v0.6.3

发布日期：2026-06-05

[完整发布日志](docs/releases/v0.6.3.md)

这版主要让 `tplan` 用起来更轻、更像人在沟通，同时保留长任务运行时最重要的安全边界。

对使用者来说，变化很直接：

- 低风险、短路径任务不会一上来就进入完整项目管理流程。
- 普通进度更新会先讲“当前在做什么、确认了什么、下一步是什么”，不再默认用 `T1`、
  `E2` 这类内部编号开头。
- 多条只读调查线索可以交给 SubAgent 并行检查，减少等待时间。
- SubAgent 只能做侦察，不能改文件、写 evidence、改任务树或替主 agent 下最终结论。
- 遇到目标变更、关键删除、阻塞或不能安全继续时，`tplan` 仍会触发 review、decision
  hook 或 graceful stop。

维护者视角：这是 `v0.6` 判断内核后的第三个 patch release，重点是收尾 tplan 运行时优化。
它不缩小 `tplan` 的能力边界，而是把运行成本从“全程常开”调整为“按风险触发”：
通过自适应记录密度让普通场景更轻，同时让关键风险仍然触发 alignment、decision hook、
Mission Review 或 graceful stop。

### 新增

- `tplan` 增加 Adaptive Runtime Policy：`lite / normal / strict` 是运行仪式和记录密度
  的内部层级，不是削弱能力的模式。
- 新增 `init_lite.py` 与 `checkpoint.py`：低风险短路径可以只保存 Mission objective、
  acceptance criteria、active node、latest state 和必要 evidence / blocker / decision
  摘要。
- 新增用户可读输出适配：普通回复先讲当前目标、进展、已确认事项和下一步，不再默认用
  `T1`、`E2` 这类内部编号开头。
- 新增只读 SubAgent 加速规则：SubAgents are scouts, not controllers；SubAgent 只做
  read-only investigation，候选发现必须由主 agent 验证后才能写入 evidence 或影响决策。

### 调整

- Step 延迟实体化：普通执行动作可以先作为本地 log 或 checkpoint，只有需要恢复、验收、
  回滚、引用 evidence 或动作膨胀成多步时才提升为 Step。
- Evidence 稀疏化：`evidence.jsonl` 只承载 acceptance、blocker、feedback、decision、
  state transition 或 key finding，不再吸收普通过程流水账。
- Decision handling 分成 inline alignment、light packet 和 full mission review，
  降低普通选择的 packet 成本，同时保留高影响变更的触发强度。
- Release pack 边界复查：确认生成包不包含仓库测试、内部设计目录、`.git` 或
  `__pycache__`，新增 tplan 运行资源进入三平台发布目标。

### 验收

- 新版 tplan 与旧版 tplan 做过 A/B 对比：新版能保持 Mission、evidence、decision hook
  与 stop 能力，同时减少常规 Step 实体化和脚本调用密度。
- A/B 结论保守处理：由于现场 agent 仍查了不少 help/source，并有外部连接重试污染，
  不把这次结果宣称为干净性能证明，只作为行为方向验证。
- 只读 SubAgent pressure scenario 固化了禁止 SubAgent 修改文件、Mission state、
  evidence、task tree 或 decisions 的边界。

### 校验

- `python3 -m unittest tests/tplan/test_skill_contract.py -v`
- `python3 -m unittest discover -s tests/tplan -v`
- `python3 -m py_compile skills/tplan/scripts/*.py`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/build-release-pack.py --out /tmp/mindthus-release-audit-13 --force`

## v0.6.2

发布日期：2026-05-31

[完整发布日志](docs/releases/v0.6.2.md)

说明：这是 `v0.6` 判断内核后的第二个 patch release，重点是把 TVG 的目标从
“持续扩厚度”校准为“先保证足够厚度，再提升价值密度和洞察收益”，并补齐
public skills release boundary 的维护者设计边界。

### 新增

- TVG 从扩厚度升级为 grounded insight value-gain：足够思考厚度是价值前提，
  grounded insight 是核心收益，value density 是出口质量。
- TVG 增加 thickness gate：厚度不足时不得提前压缩；厚度足够后再进入价值密度
  优化、compact-strengthen 或 exit graded refinement。
- TVG 增加 output profile 交付倾斜：`insight_dense`、`balanced`、
  `coverage_rich` 只影响最终表达权重，不改变内部状态驱动主线。
- 新增 `docs/internal/public-skills-release-boundary.md`，明确私有仓库材料与公开
  skills release pack 的 included / excluded file classes、cleanliness validation
  和后续 work orders。

### 调整

- `coverage_rich` 明确保留评审和交接结构，避免新版价值密度优化削弱旧版 TVG 的
  有用厚度。
- `insight_dense` 保留有校准的判断张力，避免 claim calibration 退化成通用保守
  免责声明。
- `balanced` 增加比例感护栏，避免无必要评分系统，同时保留不可逆风险、复审节奏和
  熔断条件等关键路由控制。
- release pack 版本号更新到 `0.6.2`。

### 验收

- OpenCode 旧版 vs 新版 TVG A/B 复测：`coverage_rich` 新版胜 `9 vs 7`，
  `insight_dense` 新版胜 `9 vs 7`，`balanced` 新版胜 `49/50 vs 33/50`。
- A/B 结论不再解读为“所有档位天然优于任意强基线”，而是：新版先做状态判断，
  在保留有用厚度的前提下更稳地提炼、收束和校准。
- #9 release boundary 通过标准库 contract test 固化，避免文档依赖 `PyYAML`
  环境后才可验证。

### 校验

- `python3 -m unittest tests.test_tvg_contract tests.test_method_layering_contract tests.test_mindthus_router_contract tests.test_release_boundary_contract -v`
- `git diff --check`

## v0.6.1

发布日期：2026-05-27

说明：这是 `v0.6` 判断内核版本后的 patch release，重点不是修改 Mindthus 的核心
判断能力，而是补齐发布层和内部设计模式。

### 新增

- 新增内部 skill 设计模式文档：把 Mindthus 归纳为判断内核型、认知控制型和运行治理型
  skill，作为维护者设计和审查结构时的内部参考，不暴露给浅层用户。
- 新增 release pack builder：`scripts/build-release-pack.py` 可以生成面向 Claude Code、
  Codex 和 OpenCode 的平台化发布包。
- 新增 Claude Code marketplace 发布布局：生成 `claude-code/.claude-plugin/marketplace.json`
  与 `claude-code/claude-plugin/.claude-plugin/plugin.json`，并把 skills 放入
  `claude-code/claude-plugin/skills/`。
- 新增 Codex / OpenCode 发布布局：生成 Codex namespaced skills pack、project
  `AGENTS.md`，以及 OpenCode `.opencode/skills/mindthus/` 结构。
- 发布包同步包含 `docs/methodologies/`，避免 `AGENTS.md` 和 skill 正文中引用
  `docs/methodologies/shared-primitives.md` 等方法页时出现断链。
- 发布包只抽取公开 skill、平台入口和 `docs/methodologies/`，不把
  `docs/internal/`、`docs/superpowers/` 等内部设计和执行计划目录带入公开包。
- Codex / OpenCode 发布包会按平台重写 markdown 内的 skill 路径，避免
  `AGENTS.md`、方法页导航和命令示例仍指向源码仓库布局。

### 修复

- 修复 Claude Code marketplace `source` 不能引用 `..` 的发布包结构问题。现在生成的
  marketplace 固定使用 `source: "./claude-plugin"`。
- 增加测试锁定 Claude marketplace root layout，避免后续发布脚本再次生成 sibling
  plugin 引用。
- 发布包构建脚本增加输出目录保护，拒绝把仓库根目录、源码目录或过宽路径作为
  `--force` 输出目标。

### 验收

- 三平台 smoke 已实际验证过 skill / resource / agent 或 `AGENTS.md` 关键路径：
  OpenCode、Claude Code、Codex 均能在真实模型调用中返回预期 marker。
- Claude Code 同时补测了 direct Anthropic-compatible URL + API key 路径。
- 完整 Mindthus 包的 `claude plugin validate` 在当前环境未能及时完成，因此本版本只
  声明发布包结构和前述 smoke 路径通过，不声明完整包 validator 已通过。

### 校验

- `python3 -m unittest tests.test_packaging_docs -v`
- `python3 -m unittest discover -s tests -v`

## v0.6

发布日期：2026-05-26

说明：这是 Mindthus 判断内核入口层版本。`v0.5.x` 主要是在单个方法内部增强
压力检查、表达纪律和可测试性；`v0.6` 开始把跨方法复用的判断碎片抽成
认知原语，并把 Mindthus 从“选哪个 skill”推进到“先判断是否该介入、是否该补信息、
当前判断对象是什么，再决定怎么行动”。

这里的认知原语，指那些还没有完整到能成为方法论或哲学框架、但会决定判断质量的
微型控制点。之所以叫“原语”，是因为它们比 `SELA`、`EDSP`、`WAE`、`TVG` 或
`tplan` 更小，通常只是一类判断动作；之所以叫“认知”，是因为它们约束的是 agent
如何理解、判断、取舍和表达，而不是代码实现细节。比如：用多少方法才够、结论能不能
超过证据、单一视角是否需要被挑战、局部修补循环是否该刹车、抽象术语是否需要先翻译成
直接后果。

这也是一次能力跃迁版本：如果把 Mindthus 定位为 AI 认知体系的底层分析/决策底盘，
`v0.5.x` 更像一组可解释、可调用的方法，底盘能力大约在 `60-70` 分；`v0.6` 通过
认知原语、介入边界、判断对象路由、上下文注入口、约束识别、方法仲裁、施压面收束和
执行影响要求，把它推进到单模型验收下的 `90+` 可用水平。这个结论只对应当前
contract、pressure 和 live-behavior validation，不声明跨模型鲁棒性。

### v0.6 和 v0.5.x 的区别

- `v0.5.x` 强化的是方法内部质量：例如 SELA / EDSP 的多角色压力、表达纪律和
  方法分层。
- `v0.6` 强化的是方法入口判断：简单任务不介入，缺事实时先补信息，复杂任务先识别
  判断对象，再决定是否进入 `SELA`、`3L5S`、`EDSP`、`WAE`、`TVG` 或 `tplan`。
- `v0.6` 要求判断必须改变下游执行；如果没有改变策略、风险处理、证据要求、下一步行动、
  停止条件、方法选择或交接信息，就不算有效的 Mindthus 判断。

### 新增

- 新增认知原语：把最小充分镜头、证据与结论上限、视角与激励施压、反螺旋刹车、
  不堆抽象术语墙等跨方法复用的小判断规则集中成索引，通过横切方式被各方法引用，
  不再重复塞进每个 skill 正文，也不升级成新的总方法。
- 新增 Mindthus 介入边界：简单、低风险、事实足够的任务直接执行；缺事实、文件、
  数据、运行证明或用户澄清时先补信息；只有 hard judgment point 才进入 Mindthus。
- 新增判断对象路由：先识别问题定义失败、结构歧义、长期系统效率 vs 局部优势、
  控制边界错配、薄产物、Mission runtime 状态或局部修补螺旋，再选择 skill。
- 新增上下文注入口：上游平台可以注入长期目标、用户偏好、风险姿态、角色立场等
  判断约束；Mindthus 不实现 memory、retrieval、ranking 或 profile store。
- 新增判断约束识别：事实 claim 受证据约束；价值、偏好、利益、情绪、风险姿态和
  权限边界可以约束优先级、行动强度和责任归属，但不能伪装成事实。
- 新增方法仲裁动作：`dominate`、`defer`、`degrade`、`block`、`stop`，避免多个
  Mindthus 方法默认堆叠。
- 新增执行影响要求：Mindthus 判断必须改变策略、风险处理、证据要求、下一步行动、
  停止条件、方法选择或交接信息。
- 新增施压面收束：博弈和激励问题保留为视角与激励施压，不新增独立博弈论
  skill。

### 调整

- `using-mindthus` 从“选择 skill 的说明”升级为判断入口层，但仍保持最小充分镜头，
  不把自己变成新的总方法。
- `shared-primitives.md` 明确 pressure surface 只是被触发的挑战面，不是新 route
  或 standalone method。
- Mindthus router pressure tests 扩展到 direct execution、missing proof、
  context conflict、constraint recognition、method arbitration、execution impact
  和 pressure-surface behavior。

### 验收

- 新增 `tests/mindthus_judgment_kernel_acceptance_run_2026-05-26.md`：当前实现 live
  acceptance 行为分 `98 / 100`，保守有效分 `92 / 100`。
- 新增 `tests/mindthus_v0_6_version_acceptance_2026-05-26.md`：记录 v0.6 单模型版本
  验收范围、证据和非覆盖项。
- 本次版本验收不声明跨模型鲁棒性，也不是干净 old-vs-new A/B。

### 校验

- `python3 -m unittest tests.test_mindthus_router_contract -v`
- `python3 -m unittest discover -s tests -v`
- `git diff --check`

## v0.5.2

发布日期：2026-05-23

说明：这是 `v0.5` 系列的小版本调优，重点是让 Mindthus 的复杂判断更可辩、
更可测，也更容易讲给非专业但聪明的读者听。

### 新增

- 新增 `SELA` 单 Agent 多角色压力检查：`System Advocate`、`Local Defender`、
  `Timing Auditor`。它用于非轻量战略判断，防止系统效率原则滑向过早、过绝对
  或过线性的行动结论。
- 新增 `EDSP` 单 Agent 多角色挑战：`Builder`、`Challenger`、`Synthesizer`。
  它用于保护极限推演的第一层结构骨架，避免坐标系干净但错误。
- 新增 SELA / EDSP 多角色 A/B pressure tests 和实际运行记录，覆盖非平凡判断、
  低风险确定性任务，以及一个压线摇摆场景。
- 新增 Mindthus `AGENTS.md` 的 `No Abstract Jargon Wall` 表达纪律：先讲
  “这对你意味着什么”，再讲 “Mindthus 把它叫做什么”。

### 调整

- `SELA` 文档明确：多角色是单 Agent 内部压力，不默认升级成多个 Agent；多个
  Agent 只作为高影响、强分歧或路径依赖场景的升级选项。
- `EDSP` 文档明确：如果 `Challenger` 发现决定性变量遗漏、维度重复、极端推演
  不充分或漂移读取偏置，不应继续做场景投影，而应重建第一层结构。
- `tplan` 方法页增加执行驱动的自适应规划架构图，强调它不是先完整规划再执行，
  而是在 Mission 固定的前提下，用执行反馈持续演化任务树。

### 校验

- `python3 -m unittest discover -s tests -v`

## v0.5 + v0.5.1

发布日期：2026-05-18

说明：GitHub Release 以 `v0.5.1` 发布，合并记录 `v0.5` 的方法分层纪律与
`v0.5.1` 的 EDSP frontmatter 修复。没有单独发布 GitHub Release `v0.5`。

### 新增

- 新增项目级方法分层纪律，要求方法写作显式区分 `core`、`mainline`、
  `guardrail`、`boundary`、`example` 与 `runtime support`，避免主思想被
  从属补漏和细节优化冲淡。
- 新增 `SELA` 时机检查，用临时保留、锁死未来、行动窗口三问，防止长期系统
  效率判断被误写成立刻切换动作。
- 新增方法分层契约测试，校验项目级规范存在、所有 `SKILL.md` 入口按分层顺序
  组织，并阻止未归入分层体系的额外 H2 段落。
- 新增 `SELA` 契约测试，校验时机检查保持轻量，不升级成独立原则或人文价值观。

### 调整

- 重构所有 `SKILL.md` 入口，使主路径、从属补漏、边界和运行支撑材料分层清晰。
- 将 `using-mindthus` 的前置校准保留为主路径，将 Anti-Spiral 保留为从属补漏。
- 将 `tplan` 的启动策略和运行循环保留为主路径，将 Alignment Gate、
  Anti-Spiral Gate、Linear Continuation Gate 等放入从属补漏层。
- 将 `WAE`、`TVG`、`3L5S`、`EDSP` 的脚本、模板、常见误用和停止条件从主路径中
  分离出来，降低入口阅读负担。

### 修复

- 修正 `EDSP` skill frontmatter YAML，使技能包发现和文档打包检查保持稳定。
- 增加 skill frontmatter 契约测试，避免同类问题回归。

### 校验

- `python3 -m unittest tests.test_packaging_docs -v`
- `python3 -m unittest tests.test_method_layering_contract -v`
- `python3 -m unittest discover -s tests -v`
- `python3 -m unittest discover -s tests/tplan -v`
- `git diff --check`

## v0.4

发布日期：2026-05-09

### 新增

- 新增 `tplan` Linear Continuation Gate，用于高影响决策。
- 新增 `path_assessment`，包含 `marginal_roi`、`path_role` 与 `evidence_delta`，
  要求同路径继续执行暴露 Mission-relative reasoning surface。
- 新增 Premise Calibration，并写入 `using-mindthus` 与 `AGENTS.md`，作为选择
  Mindthus skill 前去除二手概念的前置动作。
- 新增 Mindthus router pressure tests，覆盖 ROI 标签、first-principles 名称陷阱、
  workflow/agent 伪二分、趋势口号和 polished artifact 陷阱。
- 新增 Anti-Spiral Self-Audit 方法资源，并在 `AGENTS.md` 与 `using-mindthus`
  中提供激活入口。
- 新增 `tplan` `anti_spiral_audit` runtime gate 文档，覆盖重复局部修补、加层、
  负反馈和弱 evidence-delta continuation。
- 新增 WAE 指引，将局部修补螺旋视为 workflow/agent/evidence 控制边界失败模式。
- 新增 Anti-Spiral A/B pressure tests，分别评分 agent 是否触发机制以及是否退出螺旋。

### 调整

- 高影响 `tplan` hook output 在 Mission-aligned、切换 active task、改变 Mission status、
  subtraction、escalation 或 Mission closure 时要求 `path_assessment`。
- `tplan` 文档明确：elapsed time 不是 continuation 的根判断标准；marginal Mission ROI、
  path dominance 和 expected evidence delta 才是相关判断面。

### 校验

- `python3 -m unittest discover tests/tplan -v`
- `python3 -m unittest tests.test_packaging_docs tests.test_mindthus_router_contract -v`
