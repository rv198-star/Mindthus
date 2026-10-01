# DeepSeek分层试跑登记

2026-10-01；Owner提出用DeepSeek试跑，并明确提供CPA服务及deepseek-v4.1-flash。
服务：https://cpa.72live.com/v1；模型请求deepseek-v4.1-flash；reasoning_effort=max，thinking.type=enabled，temperature=0，max_tokens=8192。实际服务端确认与请求配置分别保存；不凭型号假定参数规模或较弱能力。

复用上一批固定的八窗业务输入、独立规范及两项偏差定义；父证据525745f19926cc9134652cff0b90a3be677bd6a7，材料设计c8507534e4c7b8e331150b2eb0715ff3ceabf9c0。不是holdout，不是现实原图复现。

先取得A八份首答并作执行端定点阅读：若未发现重要偏差，停止本批，不再重复Jev/LLM检查的开销比较。若观察到重要偏差，追加绑定当前首答的stage-A-review.json，再比较全部八个固定候选的B/C，以保留条件反转和不应纠偏的对照。审阅记录及规范不进入业务提示。

A首答、B检查和B/C纠偏均使用同一CPA DeepSeek配置，C判断仍使用官方jev-1.13.0；不使用Sol补写或兜底。两个判断和共同核对模板保持不变；每窗最多一次纠偏，未决不强制改结论。

沿用原方案有限上限64逻辑调用（DeepSeek56、Jev8）；是本次新模型试跑上限，不使用旧批次余额，也不更改旧已消耗次数。无必要读取、未启动B/C时预计8次；启动比较且无纠偏时24次。上限不是调用目标，实际失败计入，不自动技术补试、不调用评审模型。CPA费用按回包记录，缺失保持unknown。

复用既有deadline_post_json、错误诊断、SerialRequests和generation-scheduling.v2：一个生成工作在途，可靠结束后至少60秒间隔。CPA单次90秒，Jev60秒；发送后超时/断流仍unknown，安全/权限拒绝停止，不换模型、账号或渠道，不扩展旧指定风险例外。没有鉴权探针。

只增加CPA发送/回包适配和“先A后比较”入口；不改判断题、采纳阈值或旧GJ/R2算法。14项受影响接线回归通过；首轮测试夹具缺atoms的失败日志保留，未涉及模型请求。

密钥由隐藏终端输入装载至执行进程内存；不写配置文件、源码、Git、报告或请求正文。Jev复用既有获授权的官方配置入口。

CPA首答的实际环境为chat API，没有CLI的系统上下文；与上一批Sol不能作为纯模型能力/时间因果对照。本批B/C在同一DeepSeek候选、同一材料下比较，模型响应报出的身份与底层实际权重不可观察性分开。

执行入口：python -m experiments.bias_trigger.deepseek --prepare；已有首答错误且登记stage-A-review后，python -m experiments.bias_trigger.deepseek --compare。未知发送没有重发入口。

## 当前终态

第一条case-01/A真实HTTP 403，错误http_403；无回答，Jev0。已保存STOP并停止后续派发，没有技术重试。是服务访问拒绝，未证明模型内容安全拒绝或判断能力失败。见RESULT.md。
