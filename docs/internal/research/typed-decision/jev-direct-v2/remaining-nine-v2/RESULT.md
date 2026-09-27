# 六场景真实配对：执行与证据交付

十二条路径均已交付首份实际答案。新增九条已完成；没有继续生成或新增模型评阅。内容质量及去留交 ChatGPT 独立审阅，不把交付成功称为 Jev 净收益通过。

[十二份完整原始答案](ANSWERS.md) · [机器汇总](summary.json) · [476 项原始证据索引](evidence-index.json) · [本轮授权范围](SCOPE.md)

## 身份与执行边界

执行源码 `f31f8147da689cb0ce29c86ecde857003b8563b8`；父受审提交 `d3a58c613cb06fd7023de1326290d56bb451a7b4`。技术后继 `ea60d19888f22d7eafe5148d8f8b1957e3b87aef8e2c707a3ba1ecab2e2f9a82`，继承原 freeze、全部额度与历史记录。原始输入、71 题、卡片、阈值、评分、宿主提示构建均未改。只有续接范围登记和具名派发允许列表改变；B1 两臂完整提交不同，业务代码/材料一致；C–F 两臂完整源码相同。

沿用 generation-scheduling.v2 和调用级官方 HTTP 配置、gpt-6-sol/xhigh；Jev 为官方 jev-1.13.0。14 个新增宿主请求均绑定实际线程/轮次与完成事件，metadata 确认 mindthus_official_http；模型字段是请求配置，非供应商内部型号的独立证明。见 [终态绑定](evidence/remaining-nine-host-terminals.json) 和 [技术后继](evidence/remaining-nine-successor.json)。

本轮18个生成工作均返回；所有新增 serial 的实际间隔≥60秒。主动等待可小于60秒，因为其余本地处理时间已经计入间隔。单发送者、原有锁及串行机制沿用。未观察到401、连接恢复、采样重试或新未知发送；这不是底层精确HTTP次数为1的证明。认证/连接恢复独立耗时未暴露，记 unknown，未伪造为0。

## 十二条路径与分项时间

单位秒。宿主列为CLI会话耗时，不是纯HTTP时间；Jev列为evaluate耗时。完整墙钟含等待、装载、调用与本地记账。A1/native列仅成功技术重试阶段，旧格式失败另列。B1/direct列合并旧失败和补试的两个活动窗口，排除中间人工停顿；不能当作干净首发成本。

| 路径 | 状态 | 宿主CLI/Jev逻辑调用 | 主动等待 | Jev处理 | 宿主会话 | 活动完整墙钟 |
|---|---|---:|---:|---:|---:|---:|
| A1/native | 已交付 | 2/0 | 60.008 | 0.000 | 119.215 | 179.269 |
| A1/direct | 已交付 | 1/1 | 119.969 | 1.959 | 17.237 | 139.470 |
| B1/native | 已交付 | 2/0 | 119.951 | 0.000 | 48.665 | 168.901 |
| B1/direct | 已交付 | 1/2 | 179.957 | 11.821 | 37.460 | 229.718 |
| C1/native | 已交付 | 3/0 | 179.583 | 0.000 | 73.539 | 253.594 |
| C1/direct | 已交付 | 1/1 | 119.600 | 4.043 | 48.429 | 172.497 |
| D1/native | 已交付 | 2/0 | 119.588 | 0.000 | 55.610 | 175.615 |
| D1/direct | 已交付 | 1/1 | 119.611 | 1.042 | 37.516 | 158.596 |
| E-window/native | 已交付 | 2/0 | 119.563 | 0.000 | 56.184 | 176.199 |
| E-window/direct | 已交付 | 1/1 | 119.559 | 1.763 | 62.256 | 184.045 |
| F-window/native | 已交付 | 1/0 | 59.651 | 0.000 | 44.480 | 104.439 |
| F-window/direct | 已交付 | 1/1 | 119.546 | 0.918 | 32.334 | 153.264 |

新增九条总墙钟 **1547.515秒**；主动等待 1076.653秒，Jev处理 7.767秒，宿主会话 459.013秒。共14次宿主CLI、4次Jev逻辑调用；外层自动重试0。未单独测量的装载/调度成本保留在完整墙钟中，不冒充网络耗时。

全历史共18次宿主CLI意向和7次Jev业务意向：宿主17次返回、1次明确schema失败；Jev6次返回、1次旧远端未知。23个返回逻辑工作、1个明确失败、1个已接受风险的unknown。底层HTTP/生成尝试次数仍unknown。未用额度不构成继续重试授权。

## ③路由、合同错误与实际装载

| 场景 | 实际方法：角色/范围；执行顺序 | 有效判断/合同错误 | 未决方法 |
|---|---|---|---|
| A1 | 无具名方法；无 | 71/0 | 无 |
| B1 | wae:primary/U；wae | 70/1 | 3l5s, edsp |
| C1 | mpg:primary/U；sela:support/U；sra:stage/U；sela → mpg → sra | 70/1 | edsp |
| D1 | 3l5s:stage/U1；edsp:stage/U1；sra:stage/U2；3l5s → edsp → sra | 70/1 | 无 |
| E-window | edsp:primary/m0；edsp | 71/0 | 无 |
| F-window | 无具名方法；无 | 70/1 | edsp |

六条③有效路由均只执行首层全目录71题，没有第二层具名细读，没有前置LLM。所有宿主显式 route_objection 为空。B/C/D/F 的 EFFORT 均为 `provider_error: answer_contract:ContractError:weighted_rating/distribution_mismatch`，effort=null；A/E 分别0.01/0.94。没有修改精度容差或追加方法来消除未决项。

C：SELA支持MPG；MPG与SELA分别支持SRA。D：3L5S与EDSP独立，二者均先于SRA；stage不改称primary。详细关系、作用范围、认知约束和加载顺序原样见 summary.json 的 route。

- A1/native：实际追加装载 `无`；宿主声明方法 `无`。原始请求/读取回复见 `evidence/runs/A1/native/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- A1/direct：实际追加装载 `无`；宿主声明方法 `无`。原始请求/读取回复见 `evidence/runs/A1/direct/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- B1/native：实际追加装载 `skills/wae/SKILL.md`；宿主声明方法 `wae`。原始请求/读取回复见 `evidence/runs/B1/native/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- B1/direct：实际追加装载 `docs/methodologies/wae.md, skills/wae/SKILL.md`；宿主声明方法 `wae`。原始请求/读取回复见 `evidence/runs/B1/direct/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- C1/native：实际追加装载 `skills/mpg/SKILL.md, skills/sela/SKILL.md`；宿主声明方法 `sela, mpg`。原始请求/读取回复见 `evidence/runs/C1/native/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- C1/direct：实际追加装载 `docs/methodologies/mpg.md, docs/methodologies/sela.md, docs/methodologies/sra.md, skills/mpg/SKILL.md, skills/sela/SKILL.md, skills/sra/SKILL.md`；宿主声明方法 `sela, mpg, sra`。原始请求/读取回复见 `evidence/runs/C1/direct/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- D1/native：实际追加装载 `skills/edsp/SKILL.md, skills/sra/SKILL.md`；宿主声明方法 `edsp, sra`。原始请求/读取回复见 `evidence/runs/D1/native/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- D1/direct：实际追加装载 `docs/methodologies/3l5s.md, docs/methodologies/edsp.md, docs/methodologies/sra.md, skills/3l5s/SKILL.md, skills/edsp/SKILL.md, skills/sra/SKILL.md`；宿主声明方法 `3l5s, edsp, sra`。原始请求/读取回复见 `evidence/runs/D1/direct/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- E-window/native：实际追加装载 `docs/methodologies/primitives/frame-fitness-check.md, docs/methodologies/primitives/whole-elephant-protocol.md`；宿主声明方法 `无`。原始请求/读取回复见 `evidence/runs/E-window/native/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- E-window/direct：实际追加装载 `docs/methodologies/edsp.md, skills/edsp/SKILL.md`；宿主声明方法 `edsp`。原始请求/读取回复见 `evidence/runs/E-window/direct/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- F-window/native：实际追加装载 `无`；宿主声明方法 `无`。原始请求/读取回复见 `evidence/runs/F-window/native/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。
- F-window/direct：实际追加装载 `无`；宿主声明方法 `无`。原始请求/读取回复见 `evidence/runs/F-window/direct/host/`。native初始入口/目录是基线预装材料，不能把这里的‘无追加’误读为未提供入口。

## 原始用量与旧失败成本

以下逐CLI保留原始 input/cached-input/output；同线程resume的CLI统计可能包含累计上下文，未自行相减或声称为净计费用量。Jev原始input/output另列，不跨供应商相加充当费用。所有金额unknown。

| 路径 | 宿主原始用量（逐CLI：input/cached/output） | Jev原始用量（逐调用：input/output） |
|---|---|---|
| A1/native | unknown；23711/0/84 | — |
| A1/direct | 20040/0/90 | 15530/3596 |
| B1/native | 23718/0/233；58558/23552/961 | — |
| B1/direct | 25489/0/903 | None/None；15653/3604 |
| C1/native | 23856/0/231；64237/23680/294；117507/63872/1400 | — |
| C1/direct | 37091/0/1869 | 15743/3622 |
| D1/native | 23851/13056/223；60085/36736/1375 | — |
| D1/direct | 33917/0/1272 | 16185/3682 |
| E-window/native | 23599/0/308；61554/23424/1526 | — |
| E-window/direct | 23043/0/1079 | 15553/3614 |
| F-window/native | 28786/0/1335 | — |
| F-window/direct | 25150/0/793 | 24007/4014 |

A1/native原schema失败保留：宿主归档会话28.518秒，旧预算计账30.22秒，两者不等同纯HTTP耗时；缺失token/费用unknown。成功阶段119.215秒含历史连接重试，5条内部重试日志和WebSocket回退不推算成必然6次底层请求。A1/native仍已用2/4，不改写历史outcome。

B1旧首层：Jev evaluate7.987117秒，主动等待60.005245秒，活动墙钟68.190610秒；71项provider_error来自同一次transport_failure传播。serial/000004及原意向、错误outcome不变，无completion；处置仍risk_accepted_remote_unknown。现存材料不能进一步归因，无法排除重复计算/计费或旧远端重叠。

B1指定补试：Jev3.833971秒、宿主37.460029秒、等待119.952124秒、活动墙钟161.527518秒。额外一次预算已经用完。result中的4772.359775秒包含旧运行起点至恢复的人工暂停，不与活动墙钟混用。旧/新请求绑定与风险接受见 evidence 下 B1-compensation 文件及 serial/000004。

## 可比较性与交接

A1仅核对内容，二者原答案均为 apple、pear、plum（三行）；传输条件不同，排除匹配速度/费用比较。B1可比较实际答案，但全量费用与旧远端耗时不完整。C–F保持相同宿主配置、源码与各场景原始输入；方法及读取轮数是实验处理差异。缓存、单样本与服务波动仍限制性能外推。

B1③已有一次知晓分组的内容审阅，diagnosis/minimal_repair/verification通过；不是匿名评阅或工程全审。其余新增答案未由本执行者或额外模型评阅。工程运行、供应商返回、答案交付、内容质量和净收益分层：本轮证明真实交付完成，质量/去留/净收益交ChatGPT。

当前没有阻止这九条交付的新增阻塞；仍未解决旧B1远端发送/受理状态、精确底层计数和缺失费用，以及四条EFFORT合同错误的批后归因。所有不利记录保留。没有重开R2、全仓审计、鉴权探针或改题追分。

本次仅进行交付记账核对：476份导出字节摘要一致、历史保护通过、14个宿主真实终态绑定、18个新增serial完成与间隔记录、12个交付结果。它不是72文件工程审计PASS。产物服务固定提交上的独立内容审阅；下一步由方案方给去留结论。
