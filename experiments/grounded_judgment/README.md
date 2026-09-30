# grounded-judgment-v0 独立离线原型

唯一设计基线：`006731c43a48099d41bfbc5f3421bd5267a6404f`。
本模块不替换 `jev_direct`，不修改默认Skill，不发网络请求，不读取认证资料。
`core`负责引用、13项题组、适配、组合及按独立规范计分；`runtime`负责有界文件交换和记录；
`exchange`复用已有JevEngine做纯格式转换；`development`仅含公开模拟开发例。

## 离线复现

从仓库根运行（使用环境中可用的Python 3）：

```sh
python3 -m unittest tests.test_grounded_judgment -v
python3 -m experiments.grounded_judgment demo --out /tmp/grounded-demo-new
```

输出目录必须不存在，避免覆盖历史。demo通过正式的init/next/accept转移函数运行，
所有返回和答案均为显式模拟值，无真实模型调用；12条轨迹不是新六案或未见验收。
Skills仅改变S1、4K仅改变F1；其余句子与已通过设计逐字一致。

## 文件交换入口与返回合同

输入JSON含documents数组，每项字段为：
`id, revision, text, role, order, origin, available`。
origin为given/direct/reported/claim/missing/user/assistant；给定条件不是现实已验证事实。
可携带materials（路径→原文）和initial_paths。prepare-input对原入口及方法资源做本地快照，
宿主仅预装原入口与带description的目录，其余正常按需读取；三臂使用同一快照。

```sh
python3 -m experiments.grounded_judgment prepare-input --documents documents.json --repo /absolute/Mindthus > input.json
python3 -m experiments.grounded_judgment init --root /tmp/gj-one --input input.json --arm C
python3 -m experiments.grounded_judgment next --root /tmp/gj-one > request.json
python3 -m experiments.grounded_judgment accept --root /tmp/gj-one --reply response.json
python3 -m experiments.grounded_judgment status --root /tmp/gj-one
```

`next`对同一pending幂等返回，不派发。`accept`要求request_sha256精确绑定：

```json
{
  "request_sha256": "从request.json复制的摘要",
  "simulation": true,
  "status": "returned",
  "response": {},
  "measurement": {}
}
```

- B前置response按题ID给 `{value, semantic_state, unresolved_reason, basis_refs}`。
  不接受confidence字段。依次处理1/2/3轮依赖后，由程序生成发现；不得带draft字段。
- C前置/检查response按题ID使用既有DecisionResult格式：`status,value,uncertainty,reason`。
  `exchange.jev_payload(request)`或CLI `wire --root ...`输出官方Jev请求体，
  `exchange.jev_results(request, provider_answers)`复用现有严格校验并隔离题级合同错误。
  原始provider答案应一并放在返回信封的`raw_provider_answers`保存，不用归一化结果覆盖它。
- 宿主response为 `{kind: "answer"|"read", text, read_paths, objection}`。
  读取只能在首稿前，最多3次材料往返；路径须在快照且未加载，不允许重复路径或越界读取。
  这是可调整前必须登记的资源上限，不增加原子判断轮数；读取成本单列。
- A检查为 `{needs_revision: boolean, basis_text: 首稿原文片段}`；B/C检查用每项发现的
  LOC/OK原子结果，最多4题。无发现时B/C跳过检查；A可有一次正常自检机会。
  检查未知或不一致不触发修订；缺失要求内容（LOC=none且OK=deny）可修订一次。
- returned/failed/unknown/safety_refusal须由外部执行者按可绑定证据填写，不从退出码推断。
  failed/unknown/safety_refusal使本路径停止，无自动重试、强制解锁或改换渠道入口。
  interrupted事件事务也停止读取，不自动重放可能已派发的请求。

## 记录与计时

每条路径events是追加式摘要链，包含init、request、原始response、round_adapted、adapted、
combined、first_draft、check、revision及状态。首稿前组合顺序由状态机强制执行。
原文hash/位置、请求hash、材料hash、设计基线、simulation标识均保存。
`basis_refs`证明位置存在，不能证明模型语义正确；没有额外语义裁判。

measurement接受分别记录的cli_starts、observed_recoveries、underlying_requests、
active_wait_seconds、session_seconds、loading_seconds、usage、cost、transport_evidence。
未提供保持null；不从会话时长推算HTTP耗时，不跨供应商token相加充当费用。
运行root墙钟包含文件交换期间的人为停顿，不能拿它冒充连续模型处理耗时。
模拟计数是模拟逻辑交换，真实模型调用为0。真实运行的计量字段是执行者观测，不是本工具独立认证。

## 派发接线与后续预算（真实执行未授权）

同一可执行入口可用 `init --external-evidence` 记录真实外部返回；这只改证据模式，
不授权发送。该模式要求原入口和目录材料存在，不能用空材料削弱A。
新增 `dispatch.py` 已将request接到既有官方执行适配器，并复用SerialRequests完成
全批单发送者和明确终态后60秒冷却。新增batch采用dispatch-owned receipt导入；旧文件交换保持。
本轮只用模拟传输与时钟验证，真实批次仍须封存验收材料并取得预算/执行授权。
可执行入口、材料导入格式及原始离线证据见
[派发接线报告](../../docs/internal/research/typed-decision/grounded-judgment-v0/offline-dispatch-v1/RESULT.md)及
[运行入口](../../docs/internal/research/typed-decision/grounded-judgment-v0/offline-dispatch-v1/RUN.md)。
新运行请求明确记录官方jev-1.13.0或gpt-6.1-sol/xhigh、mindthus_official_http；请求配置不是服务端型号证明。
2026-09-30起按Owner选择统一新宿主/CLI评阅默认值；旧gpt-6-sol请求和答案保留，不回测。
新batch和各臂state冻结host_configuration，实际wire与请求必须一致；历史state缺此字段时沿用旧型号。

| 每例上限 | A原入口 | B精细提示Agent | C/Jev |
|---|---:|---:|---:|
| 前置判断调用 | 0 | 1宿主 | 3Jev |
| 首稿/检查/修订（不含按需读取） | 1/1/1宿主 | 1/1/1宿主 | 1宿主/1Jev/1宿主 |
| 额外材料读取往返 | ≤3宿主 | ≤3宿主 | ≤3宿主 |
| 总逻辑调用上限 | 6 | 7 | 9 |

若未来批准8个未见样本×三臂，无额外材料读取时上限104次逻辑调用（72宿主+32Jev）；
包含全部读取余量时176次（144宿主+32Jev）。这是建议预留上限，不是已增加的预算或必须用完额度。
每次宿主建议沿用360秒、每次Jev60秒单次超时上限；再次未知不重发，未用额度不是追分授权。
全批单生成在途且明确结束后≥60秒；176次全部用完对应至少175次间隔，单冷却约175分钟，
尚未含模型、装载、恢复或人工停顿。金额预算待供应商计价及原始用量确定，当前unknown。
是否值得这种额外介入必须允许被否定；未见8例尚未封存。

## GJ-01–04 接口修正

B的每题实际请求携带与消费者共用的output_contract，命题回复使用support/deny/unresolved，
不是true/false；Choice、等级、none/ambiguous、依据与弃权分别说明。检查请求同样带合同。
B/C均看到固定consumption_rules，执行者不需从开发夹具猜规则。
检查LOC/OK各自绑定具名发现并独立看全文；wire验证上下文依赖。返回后才检查依据是否相容。
C的OK依据标为程序的post-return LOC关联，不是模型原生引文；不再填首句占位符。
未决证据候选仍保留，但不输出成已采纳来源；低置信度none不等于确定缺失。
规范性目标缺失可由独立规范表判正确，模型弃权或错误依据不能因同样返回none而获成功。
