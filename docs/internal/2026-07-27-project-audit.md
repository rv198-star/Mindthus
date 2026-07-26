# Mindthus 项目审计 / 2026-07-27

## 状态

内部审计记录。审计对象是 `main` @ `57319d8d`（`v1.5.3`）的仓库整体，不是某一次发布或某个
方法的正确性。

> **基线说明**：`origin/main` 已比该审计基线多一个文档型提交 `476053e6`
> (`docs(release): add v1.5.3 ROI Beta asset`)。本文所有实测数字取自 `57319d8d`；
> 该提交只增加发布文档，不影响本文结论。#145 开工时应从最新 `origin/main` 重新生成
> inventory 与体积基线。

本文只做诊断和建议，不授权修改运行时、发布包或方法正文。任何落地都需要单独批准。

已立项：

- [#144](https://github.com/rv198-star/Mindthus/issues/144) — R1 + R2（P0，真实使用日志空转与冻结）
- [#145](https://github.com/rv198-star/Mindthus/issues/145) — R3 第一步（P2，per-call artifacts 迁出 HEAD）

两条均已收到独立复核意见（2026-07-27），**结论都是方向认可、规格需修订后开工**。
复核指出的事实错误已回写本文：F1 的因果叙事（#141/#142 确有真实任务来源）、
R3 的 `<10 MB` 验收不可达（实测迁出后仍为 10.711 MiB）。两条 issue 的规格修订
待维护者确认后再更新 issue 正文，本文不代为改动。

R4 已按维护者输入下调为搁置；搁置期间的只读复核结论见 R4 补充探索一节。

审计边界：本文不评价 Mindthus 方法论在判断质量上是否成立。那个问题属于公开基准和真实
使用证据，本文只审计**项目当前把力气花在哪里、证据面是否成立、以及叙事与资产是否对齐**。

## 一页结论

工程面是健康的，问题在证据面和战略面。

已核实的健康信号：

- `python3 -m unittest discover -s tests -q` → `Ran 761 tests`，`OK`，42 秒。
- `scripts/build-release-pack.py --out` 构建成功；从构建产物冷跑 validator 与
  `scripts/primitives/check.py` 均正常退出。
- `scripts/install-skills.sh claude` 符号链接模式端到端可用。
- 代码卫生干净：无 `shell=True`、`eval`、`pickle`、裸 `except:`；`except Exception` 仅 5 处。
- 自我诚实度高于同类项目：`latest.md` 主动标注 `1.447 < 1.5` 且写明 "Do not quote this as a
  passing benchmark"；`shape-evidence-risk-report.md` 明令 validator 不得输出语义结论；
  retention policy、anti-overfitting rule、reopening conditions 均为预注册。

核心问题一句话：

> 2026-07-13 研究关闭时写明 "engineering effort returns to product clarity, installation,
> explicit invocation, public/runtime documentation boundaries, and real-task value"。
> 此后 65 个 commit、108 个文件变更落在 `skills/tplan`，而 `data/fidelity-usage-log.jsonl`
> 至今 0 条记录。

用项目自己的语言：这是 **Anti-Spiral 该触发而没触发**。它不是"反复修同一个局部"那种典型
螺旋，而是更隐蔽的一种——**用可控的工程确定性，替代不可控的产品验证**。TPlan 有 schema、
有测试、有 CI，改它一定有产出；真实使用日志需要有人真的用它做真实任务，不可控。项目沿
阻力最小的方向前进了两周。

这不否定 TPlan 工程质量。它质疑的是**优先级来源**：07-13 之后的工程投入，没有一条能追溯
到"某个真实任务因为这个问题受损"。

## 发现

### F1. 唯一的产品验证通道是空的，且其空转在 CI 中不可见

严重度：高。这是本次审计的头号发现。

`docs/real-use-validation.md` 的设计是好的：纳入条件严格（真实工作需求、完整任务、已脱敏、
记录调用方式、结果可观察时才记）、五个观察字段、10–20 个自然任务观察窗口、并且明确写了
立项纪律"没有重复机制就不改 prompt、matcher、runtime gate 或方法正文"。

实测：

```
$ python3 scripts/log-fidelity-usage.py --validate --log data/fidelity-usage-log.jsonl
Fidelity Usage Log Report
Log file: data/fidelity-usage-log.jsonl
Records: 0
No usage-log data yet; the default log is optional until the first record is appended.
No usage-log shape risks detected.
exit=0
```

`data/` 目录下只有 `README.md`；日志文件根本不存在。

`.github/workflows/python-validation.yml` 每次都跑这条命令，每次都绿。**0 条记录与 20 条
健康记录在 CI 上表现完全一致。** 这是一个恒真的门。

**审计更正（2026-07-27，#144 复核后）**：初稿写的是"07-13 后没有任何工程项可追溯到真实
任务失败"。这句话是错的，已核实：#141 明确源自真实 WFF #508 Mission 并附事故证据（stale
detached checkout 生成了非 TPlan 的 `completion-flow.svg`；v1.5.2 把 71 秒 trace 片段误标
为 Mission 全长，而实际工作约 56 分钟），#142 又从同一事故拆出。真实任务证据**是存在的**。

准确的问题定义是：

> 真实任务证据存在，但散落在 issue / 事故链里，没有进入统一的 real-use registry，
> 因此**不能聚合、不能检查重复机制、不能约束后续立项**。

这不削弱本条的优先级——registry 缺位这个缺口本身成立——但它不支持把近期 TPlan 工作
整体描述为"无真实证据导航"。

后果不是"少了点数据"，而是**项目失去了把分散证据聚合成立项依据的通道**。按项目自己
的规定，公开基准"只能帮助确认修完有没有破坏已知行为"，不能承担优化导航；导航责任被明确
指派给了真实使用记录——而那个聚合位置是空的。于是"重复机制才立项"这条纪律无法执行：
判断一个机制是否重复出现，需要能横向比对的记录，而不是逐个翻 issue。

补充证据：`docs/internal/fidelity-usage-log.md` 写明这条线的目的是"让项目有能力用数据砍掉
测不出效果的东西"。0 条记录意味着这个砍除能力从未上线。

### F2. 761 个测试中约三分之二在断言 markdown 字符串

严重度：中高。这是自我一致性缺口。

统计：

- `tests/*.py` 中 `assertIn` 共 1038 处，其中约 667 处的断言对象是文档文本变量
  （`changelog` / `readme` / `using_compact` / `primitives` / `contract_compact` 等）。
- `tests/test_packaging_docs.py` 单文件出现 `changelog` 70 次。
- 真正执行运行时代码（`subprocess` / 导入 `tplan_runtime` / `runpy`）的测试文件只有 48 个，
  且主要集中在 `tests/tplan`（320 tests，这部分是扎实的状态机与持久化测试）。

典型形态：

```python
self.assertIn("发布日期：2026-06-05", changelog)
self.assertIn("自适应记录密度", changelog)
self.assertIn("source: \"./claude-plugin\"", changelog)
```

这些锁定的是历史 changelog 条目的中文措辞。它们既不会失败（除非有人改历史条目），也不
保护任何行为。它们把"文档里写了那句话"当成了"系统具备那个性质"。

自我一致性问题在于：项目对自己的 validator 有一条硬规矩——

> shape pass is not semantic approval.（`docs/internal/shape-evidence-risk-report.md`）

但项目自己的 CI 正是把 shape pass 当成了 semantic approval：`SKILL.md` 里含有
"Truth Orientation / 真相优先" 这个字符串，不等于 agent 在真实任务里做到了真相优先。

区分要讲清楚，避免误伤：`tests/tplan` 的 320 个测试、fidelity validator 测试、
release-pack 构建测试都是真行为测试，应当保留。问题集中在文档措辞断言这一类。

### F3. 仓库历史重量的绝大部分来自已关闭研究线，且主要在历史而非工作树

严重度：中。**本条修正了初审时"减小 HEAD 即可降低 clone 成本"的判断，结论方向变了。**

实测数据：

| 口径 | 数值 |
| --- | --- |
| 新鲜 `git clone` 后 `.git` | 173 MB |
| HEAD 工作树（tracked） | 35.6 MB / 6903 文件 |
| 其中 `docs/benchmarks/runs/` | 27.9 MB / 6493 文件 |
| 历史全部 blob 归因 `docs/benchmarks` | 192.3 MB |
| 历史全部 blob 归因 `tests/artifacts` | 65.4 MB（**HEAD 中已不存在**） |
| 历史全部 blob 归因 `artifacts/images2` | 14.7 MB（**HEAD 中已不存在**） |

关键推论：**约 80 MB 是已经删除、只存在于历史中的文件**（TVG 图像试验产物等）。这意味着：

- 仅把 `docs/benchmarks/runs/` 从 HEAD 移走，clone 成本**不会**明显下降——历史里的 blob
  还在。想真正降到个位数 MB，需要 `git filter-repo` 级别的历史重写。
- 历史重写会改写所有 commit SHA。而 `docs/benchmarks/latest.md` 记录了
  `Raw run commit: c4ee0549...`，`2026-07-13-research-closure-summary.md` 记录了归档分支
  `codex/brake-semantic-triage-design` 与 commit `f820a898`、`6efeda76`。**重写会使这些
  预注册的证据指针全部失效**，直接损害项目最宝贵的资产——可审计的研究诚实性。

因此这是一个真实的权衡，不是一个纯粹的清理任务。见 R3 的分级建议。

另注：`docs/benchmarks/runs/` 下有 5 个目录在 git 中为 0 文件（本地存在、未提交），
说明 `run-artifact-retention-policy.md` 已经在新 campaign 上生效了。policy 本身没问题，
问题只是历史存量。

### F4. TPlan 已事实上成为项目主资产，但 README 仍按判断力工具定位

严重度：中。这是叙事与资产的错配。

| 指标 | TPlan | 其余 7 个 skill 合计 |
| --- | --- | --- |
| Python LOC | 15,757 | 3,886 |
| `scripts/` 下脚本数 | 37 | ~15 |
| 07-13 之后文件变更次数 | 108 | ~50（其中 tvg 44） |

TPlan 包含 hook supervisor、telemetry adapter、interaction guard、guard control server、
execution cost tree、runtime provenance、runtime doctor——这是一个完整的 agent 长任务运行时，
代码量是全部判断力 skill 之和的 4 倍。

而 `README.md` 299 行里，前 60 行讲的全是判断与纠偏；TPlan 首次作为方法出现在第 64 行，
是"方法论导航"的第 8 条。此后的出现几乎都在安装命令示例里。

风险：潜在用户读 README 期待"判断力提升"（该主张**尚未认证**，`1.447 < 1.5`），实际拿到
的最成熟资产是"长任务 Mission 运行时"（工程扎实，320 个运行时测试）。**强资产被弱主张的
未认证状态拖累。**

### F5. `using-mindthus` 的上下文成本未经验证，且已知的验证手段已多轮未收敛

严重度：中高（若数字成立则为高）。

**审计更正（2026-07-27，维护者输入后）**：本条初稿写的是"spec 已 hold 十天，缺的只是执行"。
这个判断是错的。维护者确认 matched A/B **已经跑过多轮，最终未能得出结论**，因此搁置。

仓库证据支持这一点：`tests/router_wakeup_ab_experiment_design.md`（完整的 primary endpoint
与变体设计）、`tests/router_wakeup_weak_cue_calibration_2026-06-17.md`（weak-cue 可判别性
预试）、`tests/router_wakeup_weak_cue_holdout_cases.md`、`docs/benchmarks/runs/2026-07-08-v5-naturalization/`，
以及 `scripts/router-wakeup-ab.py`（688 LOC 的成套 runner）。

这个更正改变了结论方向：`using-mindthus` 的成本/收益问题**不是"被回避的事"，而是"已经用
现有手段试过并且失败的事"**。二者的正确处置完全不同——前者该催办，后者该换手段或明确
接受不确定性。**这与 F1 不是同一类问题，不应并列。**

`docs/superpowers/specs/2026-07-17-using-mindthus-passive-activation-refactor-design.md`
记录了一个 n=1 诊断：三个正向场景中，treatment 相对 baseline 增加约 **+483% input、
+195% output、+430% reasoning、+23.9% wall time**；两个应睡眠场景开销很低（+8.8% input）。

spec 自己诚实标注"不是认证证据""样本太小""没有形成可复跑 artifact"，状态 `proposal / hold`。
**这个判断是正确的**，不应该因为一个 n=1 就重开已关闭的调参路线。

可核实的静态事实：条件资源加载面合计 56.6 KB，其中 `whole-elephant-protocol.md` 单文件
18.6 KB；八个 `SKILL.md` 各 4.2–8.6 KB。

判断：**如果那个 483% 大致成立，这比 benchmark 分数更致命。** 一个让 agent 判断更好但贵
五倍的工具，在真实工作里不会被反复使用——它会在用户第三次注意到账单或延迟时被卸载。
基准分数只影响项目可信度，成本结构直接影响留存。

但**成本问题重要 ≠ 现在该继续投**。多轮 A/B 未收敛本身就是一个信息量很高的结果。

**归因要说准（2026-07-27 复核）**：失败的直接原因是 `baseline-ceiling`——baseline 与
treatment 双双 100%，lift 数学上不可能为正。更深一层的原因是**主终点方向选错**：归档 A/B
两臂都加载完整 `using-mindthus`，只差路由文案，测的是一条已于 07-13 正式关闭的 prompt 迭代线；
而 R4 真正要问的是成本。详细推导与替代路径见 R4 补充探索一节。

正确处置是**换测量口径而不是换参数**——具体到"换主终点方向"，不只是换样本来源：成本侧
（token / wall time / skill hops）是确定性可测的，不需要 judge，也不需要收益侧收敛，且量程
（+483%）远大于原实验的 0pp；收益侧降为非劣护栏，或等 F1 的真实使用记录积累后间接观察。
即：先把能确定测的那一半单独测掉，另一半挂到真实数据上，而不是继续做需要两边同时收敛的
整体实验。此项不列入当前优先级，作为 F1 有产出后的候选。

### F6. 版本与打包面一致，无发现

核查通过，记录以免后续重复审计：`runtime-manifest.json` 的 `package_version` = `1.5.3`
与 README、CHANGELOG 一致；release pack 四个 host lane（claude-code / codex / codex-plugin /
opencode）均正确包含 `_runtime` 与 `runtime_bootstrap.py`；copy 安装若漏拷这两者会
`ModuleNotFoundError`，但 README 的 Personal Skills Mode 已明确要求拷贝，属已知并已文档化。

## 建议

优先级依据：能否恢复"判断下一步该修什么"的能力 > 能否降低留存风险 > 能否减少维护摩擦。

### R1. 让空日志变成可见的红灯（本周，低成本）

不是逼自己造数据，而是**让缺口停止隐身**。

- 给 `scripts/log-fidelity-usage.py` 增加 `--min-records N`，CI 以外可选调用；或
- 在 `README.md` / `docs/benchmarks/latest.md` 顶部显式渲染 `real-use records: 0/10`。

要点：不建议直接让 CI 因 0 条而失败——那会把一个战略问题变成 merge 阻塞噪音。目标是让
每个看仓库的人（包括未来的自己）**撞见**这个 0，而不是让它藏在一条恒绿的 CI 步骤里。

### R2. 自己用，并补满 10 条记录（本周开始，2–3 周完成）

维护者本人显然在大量使用 Codex / Claude Code 开发本项目。**项目自身的开发任务完全符合
`real-use-validation.md` 的纳入条件**：来自正常工作需求、非为测试 Mindthus 编写、可脱敏、
调用方式明确、结果可观察。

具体起点：`#141` 的时间轴真实性问题是如何被发现的？那次判断有没有被某个 Mindthus 镜头
改变？`#134` bounded interaction guard 的范围决定呢？——这些就是第 1、2 条记录。

配套纪律（这是 R2 的关键，不是附注）：

> **在补满 10 条之前，冻结所有非缺陷性的 TPlan 特性开发。**

这不是我的额外要求，这正是项目自己写下的立项纪律："没有重复机制就不改 prompt、matcher、
runtime gate 或方法正文。" 现在的状况是这条纪律对方法正文生效，对 TPlan 特性没生效。

### R3. benchmark 存量按分级处理，不要一次性历史重写（本周决策，分两步执行）

鉴于 F3 的修正结论，建议拆成两个独立决策：

**第一步（低风险，建议做）**：把 `docs/benchmarks/runs/` 的 per-call artifacts
（`answers/` `prompts/` `events/` `judge-*` `raw-responses.jsonl` `stderr`）迁出主仓，
迁往独立归档仓库或 audit 分支。主仓每个 run 只保留 `REPORT.md` + `run-manifest.json` +
聚合 `summary.json` + fingerprint。这与 `run-artifact-retention-policy.md` 的"Keep In Git"
清单完全一致，只是把已声明的 policy 补用到历史存量上。

效果：日常 `grep` / IDE 索引 / code review 体验明显改善。
**但 clone 成本基本不变**（历史 blob 仍在）。要如实说明这一点，不要把它宣传成 clone 瘦身。

**验收口径更正（2026-07-27，#145 复核后）**：初稿写"降到约 8 MB"、并把 `<10 MB` 当验收线。
这个数字算错了——它假设 `docs/benchmarks/runs/` 整个迁出（27.887 MiB 全走），但 issue 自己
的 keep 规则要保留 REPORT / manifest / 聚合 summary / fingerprint。按该规则复核：

| 项 | 复核时 | inventory 执行后 |
| --- | --- | --- |
| tracked 工作树 | 35.635 MiB | 35.635 MiB |
| 可迁出集合 | 24.924 MiB（6241 文件） | 25.136 MiB（6334 文件） |
| **迁出后剩余** | **10.711 MiB** | **10.499 MiB** |

即全部迁完也**达不到** `<10 MB`，且没给 keep 留余量。全仓阈值同时受无关文件影响，本来也
不是好指标。改用直接对应目标的验收：

- migrate 集合与已批准 inventory 逐条一致（先产出 `path / blob OID / keep|migrate / reason /
  destination` 的机器可读 inventory，review 通过后才允许删除）；
- 净体积**分项报告**（迁出量与本次新增的证据/工具体积分别列出），不作为通过/失败判据——
  否则 inventory 越完整越容易"失败"，激励方向是反的；
- `docs/benchmarks/runs/` 收缩到约 3 MiB。

另外两项 #145 复核提出、我认可的开工前置：分类口径需可复现（初稿的 164/6273/56 无法从正文
规则推出）；以及保留下来的 `HUMAN_REVIEW_PACKET.md` 等文件直接引用待迁移的 `answers/`
`events/` `score-records.jsonl`，只给 REPORT 加指针不足以保住审计链——每份保留报告都需要
archive base pointer，且引用必须能在 HEAD 或**固定 commit/tag**（不是可移动分支）中解析，
删除只能发生在可达性校验通过之后。

**inventory 已执行（`scripts/benchmark-artifact-inventory.py`，baseline `476053e6`）**，
结果 keep 159 / migrate 6334 / unmatched 0。与复核基线（150/6241/102）的差异全部来自那 102 个
待定文件的逐条定性，依据是保留政策原文而非新规则：

| 文件 | 数量 | 判定 | 依据 |
| --- | ---: | --- | --- |
| `judge-output-schema.json` | 50 | migrate | 50 份同一 blob，且可由 `judge_schema()` 逐字节复现 |
| `activation-summary.json` | 43 | migrate | 43/43 与同目录 `summary.json["activation"]` 完全相等，无报告引用 |
| `summary-aggregate.json` | 4 | keep | 被各自 REPORT.md 的 Artifacts 列表引用，承载 gate 结论 |
| strict fingerprint | 4 | keep | 被 EXTERNAL_AUDIT_HANDOFF / HUMAN_REVIEW_PACKET 直接引用 |
| `issue-108-variant-cases.jsonl` | 1 | keep | 报告的核心主张就是这批变体的措辞/领域差异，缺它无法核验 |

后两项修正了我此前的判断：`activation-summary.json` 我原按"聚合结果"保留，实测是纯重复；
`issue-108-variant-cases.jsonl` 我原按"影子 fixture"迁出，但它符合政策的 Exception Test。

引用扫描同样已执行：15 份保留报告中 **3 份**引用了迁移后会失效的证据，集中在 v3/v4 两个
run 目录（v4 `HUMAN_REVIEW_PACKET.md` 最重，整张人工复核表的证据列都指向 `answers/` 与
`events/`）。删除前必须先给这 3 份补 archive base pointer。

**第二步（高风险，建议暂缓）**：`git filter-repo` 重写历史以真正回收约 250 MB。
暂缓理由：会使 `latest.md` 的 `Raw run commit: c4ee0549`、closure summary 的 `f820a898` /
`6efeda76` 等**预注册证据指针全部失效**。项目最稀缺的资产是可审计的诚实性，不值得用它换
克隆速度。

若将来仍要做，前置条件是：先产出一份 commit SHA 新旧映射表并提交到仓库，让历史指针可追溯，
再执行重写。在那之前，173 MB 的 clone 是可以接受的成本。

### R4. `using-mindthus` 成本/收益：不列入当前优先级（搁置，附换手段条件）

**本条已按维护者输入下调。** 初稿建议"跑一次 matched A/B 结束 hold"，判断依据是"实验设计
已写好、缺执行"。事实是多轮 A/B 已经跑过且未收敛（见 F5 更正）。继续投入等于第三次触碰
同一个局部，正是项目自己的 Anti-Spiral 要拦的动作。

搁置期间**不做**：新一轮 matched A/B、新增团队自建场景、prompt / matcher / threshold 迭代。

#### 补充探索（2026-07-27）：失败原因是主终点方向错，不是采样不够

搁置期间做了一轮只读复核，结论比"样本太easy"更具体，记录在此以免将来重复推导。

**（a）撞的是量程，不是效果。** `tests/router_wakeup_weak_cue_calibration_2026-06-17.md:49-52`：
baseline positive recall **100%**、treatment **100%**、lift **0pp**、McNemar p **1.0**，
`failed_checks` 首项即 `baseline-ceiling`。baseline 已满分时 lift 在数学上不可能为正。
校准文档自己的判语："both the known set and weak-cue v1 are too easy for the current baseline."

**（b）归档 A/B 测的是一条已关闭的问题线。** `tests/router_wakeup_ab_experiment_design.md:26-27`
定义两臂为"Wake-Up Probes 改动前 / 后的 checkout"，且"Both variants should load `using-mindthus`"
——即**两臂都是完整 router，唯一差异是路由文案措辞**。这正是 v1.4.5 已停、
`2026-07-13-research-closure-summary.md` 又正式关闭的 prompt/matcher 迭代线。

而 `docs/superpowers/specs/2026-07-17-...-passive-activation-refactor-design.md` 问的是另一个
问题——薄 weaver 能不能**更便宜**且召回不塌。两者主终点方向相反：

| | 归档 A/B | R4 spec |
| --- | --- | --- |
| 主终点 | 质量 recall **优效** | 成本 **优效** + 质量**非劣** |
| 需要 baseline | 表现**差**（留量程） | 表现**贵**（留量程） |

因此**用 `scripts/router-wakeup-ab.py` 跑 R4 是范畴错误**：其主终点只支持优效检验
（`:414-415`），非劣机制仅挂在 skip / false-positive 等次要终点（`:419` `:443`），
且全文无任何 token / 时间 / 成本字段。沿用它会因同一原因再撞一次天花板。

**（c）翻转主终点后天花板问题自动消失。** n=1 诊断显示 **+483% input / +430% reasoning**
（spec `:60`）——5.8 倍不是 0pp，量程问题不复存在。成本由平台直接上报，不需要 judge，
单轮成本低、n 可做大。质量侧则从主终点降为护栏，这与 spec `:684` 的硬门措辞
（"不得出现系统性召回坍塌"）本来就一致——那是非劣，不是优效。

**（d）变体差异要机械化，不要文案化。** spec `:599` 已列 `direct-only-ablation` 臂
（完全绕过 router）。`current-full` vs `ablation` 在 AOP-only 场景上有真实分离度，因为它是
**结构删除**而非换词。当年天花板的成因恰恰是两臂都是完整 router。

**（e）与 R1/R2 的关系要说准。** 设计文档 Experiment 4（`:193`）说用 `scripts/log-fidelity-usage.py`
记录，且 `real_use` 档唯独没有 `baseline_ceiling`（`scripts/router-wakeup-ab.py:86`）。但两边
schema 现在**接不上**：fidelity log 记 `baseline_score` / `constrained_score` / `invocation_mode`，
A/B analyzer 要 `expected_owner` / `selected_owner` / `variant` / `case_type`，交集几乎为空。
准确说法是：真实使用记录是 Experiment 4 的**必要前置**（提供非作者设计、不会人为暴露 owner
的题源），但不是现成的 A/B 输入，需要补 router 字段或写转换层。另外 `real_use` 没有 ceiling
是"没配"，不是"已证明不会饱和"。

#### 重启路径（替代原先的抽象条件）

**不做第五轮合成 A/B。** 按 spec `:705`，同一文案第三次局部修改无新独立证据即应停——已触发。

真正可推进的是拆成两件独立的事：

1. **成本侧**（不依赖 R1/R2，随时可做）：`current-full` / `thin-weaver` / `direct-only-ablation`
   三臂，主终点 token in/out/reasoning + skill hops + wall time，质量做非劣护栏。
   需新写 harness——现有 runner 无法表达这个假设。
2. **质量侧**（依赖 R1/R2）：等真实路由时刻攒够，同时给 fidelity log 补 router 字段，
   届时才谈 Experiment 4。

在此之前，**接受"入口成本未知"这个不确定性并明说**，比再跑一轮不收敛的实验更诚实。

### R5. 把 changelog 字符串测试换成结构测试（1 周，可与 R2 并行）

不是删测试，是换断言对象。用结构约束替换措辞约束：

- changelog 存在 `## vX.Y.Z` 段落结构；
- 最新版本号与 `skills/tplan/resources/runtime-manifest.json` 的 `package_version` 一致；
- 每个 release 段落有对应的 `docs/releases/vX.Y.Z.md` 文件；
- 每个 `SKILL.md` 有合法 frontmatter（`name` / `description`）——此项已存在，保留。

保留约束力，去掉措辞脆性。预计可清理掉 70 处 changelog 断言中的大部分。

**明确不动**：`tests/tplan` 全部 320 个测试、fidelity validator 测试、release-pack 构建测试。
这些是真行为测试。

### R6. README 重定位为双产品线（2 周内，依赖 R4 结论）

明确分开两条线，各自标注证据状态：

- **判断镜头**（3L5S / EDSP / SELA / MPG / WAE / TVG / using-mindthus）：研究性质，
  公开基准未认证（`1.447 < 1.5`），诚实标注，欢迎试用与反馈。
- **TPlan Mission 运行时**：工程成熟，320 个运行时测试，多 host 适配，有遥测与恢复语义。

现状是两者混在一个叙事里，导致 F4 描述的错配。分开之后，用户可以按自己的需要选择入口，
强资产不再被弱主张拖累，而弱主张也不必为了撑场面而被过度包装。

## 未来规划

三条路线，建议第二条。

### 路线一：继续做判断力基准认证

需要独立第三方持有 unseen set。07-13 已判定 diminishing return，且 reopening conditions
要求"真实任务失败 + 可复现 + 可证伪机制 + 预注册停止条件"。

**关键推论：在真实使用日志仍为 0 的情况下，这些条件在结构上不可能被满足——因为没有任何
真实任务正在被观察。** 换句话说，路线一当前不是"不划算"，而是"入口被 F1 堵死了"。

不建议现在重启。

### 路线二：TPlan 作为主产品，判断镜头作为差异化内核（推荐）

理由：

1. 市场侧：agent 长任务运行时（Mission 状态、恢复、human authority、成本可见性）是真需求，
   且比"提升判断力"容易验证。
2. 资产侧：TPlan 已有 15.7k LOC + 320 测试 + 遥测 + 四个 host lane 适配。
3. 方法侧：判断镜头不必单独证明"提升判断力"这种难以证伪的命题，而是作为 TPlan 内部的
   漂移检测与停止条件——**在一个有状态、有验收、有证据链的容器里，"判断"第一次变得可观测**。
4. 最关键：TPlan 的真实使用**天然产生 real-use 记录**，直接解决 F1。判断镜头的价值可以
   从 Mission 数据里被间接测量（漂移次数、返工率、停止条件命中率），而不必依赖题库分数。

这条路把项目最强的工程资产和最独特的方法资产接在了一起，且让证据自动积累。

### 路线三：收缩为纯方法论文档库

放弃可执行基础设施，只留 `docs/methodologies/`。会浪费掉真正扎实的工程资产。不建议。

### 若选路线二，未来三个月的顺序

```
1. R1 + R2：冻结 + 补满 10 条真实使用日志 → 验证：log 有 >=10 条 real_use 记录，且完成第 10 条聚合 review
2. R3 第一步：per-call artifacts 迁出 HEAD → 验证：`docs/benchmarks/runs/` 收缩到约 3 MiB 且体积减少量 >= inventory 字节数，REPORT/manifest/fingerprint 完整保留且引用可在固定 commit/tag 解析
3. 按日志暴露的重复机制立项               → 验证：每个新 issue 能指向 >=2 条独立真实记录
4. 再谈 v1.6 特性与 R4 是否重启
```

顺序本身就是建议的一部分：**先恢复导航能力，再谈往哪走。** 而不是继续在 TPlan 上叠特性。

## 最后

项目最大的风险不是任何一个技术缺陷，而是：

> 它建立了一套优秀的、防止自我欺骗的制度，然后在制度的空转处继续快速前进。

benchmark 关闭得对，retention policy 写得对，real-use validation 设计得对。真正的检验是：
当"该做的事"（找真实用户、面对不确定性）比"能做的事"（改 TPlan、加测试、发版本）
更痛苦时，选哪个。

65 个 commit 和 0 条日志，已经把答案写出来了。

需要与 F5 区分清楚：`using-mindthus` A/B 多轮未收敛**不属于**上面这个模式。那是认真做了、
做不出来、按纪律停下——和"没做"是两回事。本审计初稿把两者混为一谈，已在 F5 / R4 更正。

这份审计本身也适用同一条标准——它只有在改变了下一步做什么的时候才算产生了执行影响。
