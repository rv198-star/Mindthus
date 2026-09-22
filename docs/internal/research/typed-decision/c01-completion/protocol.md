# C01完整链路：回退依据补齐 + 一次真实端到端运行

用户要求连续推进，不在每个小步骤后索要“继续”。本轮闭合一个明确实现阶段：
Jev路由 → 可核验交接 → 用户授权CPA宿主回答，并保留可重入的不可变日志。
不改C01 graph4、J1/J2/J4/J5语义、不重做Engine/Provider抽象，不扩C02。

## 已观察到的缺口及替换

原交接在J5拒绝后只带owner=null和一般fallback原因，缺少已读取的被检查方法合同。
现在handoff v2从核验过的J5 State/answer保留fallback_method_check，携带owner、
status/value和完整合同及摘要；no/unclear/provider_error不混同，不包含confidence。
selected_method仍为空；这些是解释证据，不是执行被拒绝方法的指令。

新c01_host模块是单场景薄串联入口。prepare写入冻结manifest，run复用Session与handoff；
TypeSafe最多3次，CPA最多1次，无自动重试/切模型。已完成summary直接读取；
未知host intent没有outcome时拒绝重发。源代码、输入或合同改变时旧manifest拒绝执行。
不启动agent工具循环，不改变任何平台全局配置或生产入口。

## 预冻结检查

1. L27：复用旧WAE不适用的真实决策。中文回答须解释任务只是已定规则排序、没有agent
   控制权判断，WAE不适用；给出A、B、C、D；不得把方法拒绝说成工具没装或调用失败。
2. L28：复用旧MPG不适用决策。须说明单纯词语替换无主线/载体/暴露/路径判断，不能套MPG；
   返回“Practice the first phrase, then practice the second phrase.”，不动其他文字。
3. L22：原已成功控制项。推荐层拥有适配标准/语义选择，renderer仅按确定结果展示；
   不声称修改系统，不让renderer自行定义“适合初学者”。
4. N03：原已成功的宿主恢复控制项。具体询问时间地点，不捏造、不强迫用户解释一个
   泛化“义务”，不因SRA名字展开无资源竞争的分析。原Jev误挡仍为失败，不改原标签。
5. E01：一项新的合成工作流输入，真正调用官方Jev并经新入口生成CPA回答。冻结路由
   预期intervene/wae；下游回答须区分schema完整性检查与证据支持/语义真值判断，
   将后者留给有任务上下文的Agent并受来源证据约束；机械validator不能宣布回答有依据。
   技术完整、路由和下游质量分别报告，不能以回答好掩盖路由错。

前4项不重问Jev，只重放已冻结证据生成更新交接。E01是连通性/执行链检查，不是holdout。
no/unclear/provider_error不混同与中断恢复先用离线控制测试验证，不冒充真实模型答对。
每项一次；semantic失败测完列表，technical失败立即停后续，不新增题、不改答案标准。
本轮是数据交接缺口修复后的单次反馈，不续跑任何已终止trial，也不重置旧语义调优额度。

## 模型与预算

CPA https://cpa.72live.com/v1/chat/completions，固定deepseek-v4.1-flash，temperature0，
max_tokens1600，每次最多60秒；本批最多5次CPA请求、总输出参数上限8000tokens，
每个请求体最多49152字节。无GLM调用。模型报告必须与冻结名一致，不代表上游可独立核验。
CPA费用/价格/币种仍未知；控制调用/时间/字节/tokens，不编造美元上限或套用厂商价格。

E01使用TypeSafe官方jev-1.13.0、choice_rounding=True，最多3次/60秒，
每次预留USD0.002688、上限USD0.008064，估算与账单分开。
批次最多8次模型调用；请求时间预算按4个重放宿主×60秒 +完整链路路由60/宿主60秒，
合计最多360秒调用预算（本地文件操作另计）。失败/未知费用保留。
两类key只在进程环境/内存中，进程退出释放；不写源码、配置文件、Git或日志。

## 停止与证据

所有离线检查和冻结核验必须在有副作用调用前单独确认退出码；不把测试与真实启动串在
不检查返回码的shell序列里。第一次live之前commit固定源码；开跑后无修改。
保存各阶段请求摘要、允许的usage/返回model、结果与最终回答，禁止保存headers或reasoning。
评价由父代理按上述标准做非盲内容核对。主结论是此实验入口是否可用，不是独立语义资格。
不做原版A提示词替身，不称正式A/B/C、native skill load或生产采用。main不变。
