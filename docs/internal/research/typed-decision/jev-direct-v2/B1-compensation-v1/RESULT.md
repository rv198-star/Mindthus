# B1③授权补试已交付；旧远端状态仍未知

实施提交：`0cddccc1fcbca6c38a081536e085802b25e58be6`。
Owner明确“批准”后，先提交[单次例外授权](AUTHORIZATION.md)、登记技术后继，再发送。
后继摘要：`4758ef9be0aa37cdaf001768eee94ec50eabe10ac4810f68dfb592500a517d14`。
本次只完成B1/direct补偿路径，未启动B1/native或其他八条未运行路径。

## 实际路由与原始答案

官方Jev `jev-1.13.0` 首层实际处理全目录及71题，返回 `mode=judgment`；
选择WAE为primary、scope=U（当前用户原文），FIT=0.76。
`rounds=1`、`requested_details=[]`，未触发按需第二层。
实际加载 `skills/wae/SKILL.md` 和 `docs/methodologies/wae.md`；
宿主未重新加载入口或方法目录，无前置LLM。使用方法为wae，显式route_objection为空。

[真实路由](evidence/runs/B1/direct/route-compensation/result.json)、
[真实宿主请求](evidence/runs/B1/direct/host/0/request.json)、
[原始reply](evidence/runs/B1/direct/host/0/reply.json)、
[CLI完成事件](evidence/runs/B1/direct/host/0/cli.stdout.jsonl)、
[同线程/轮次归档终态](evidence/B1-compensation-host-success.json)。

原始正文（第一份完整实际返回，未挑选或改写）：

给定记录显示，验收门只检查“结论”和“依据”字段是否存在，却把字段齐全当作事实已验证。库存为正、为负的相反结论都能通过，说明该门只能证明结构完整，不能证明库存事实；现有材料也不足以判断真实库存。

最小修复是把“结构通过”与“事实验证通过”分成两个状态。字段检查仍由规则执行；库存结论须关联可核对的库存数据、对象和时间，由负责事实判断的环节核对。缺少数据或数据冲突时保持“待验证”。若终态要求业务验收，签字应单独核验，不能由字段齐全推定。

验证时重放这两份相反结论：没有库存数据时，两份都不得标为事实通过；提供同一份有效库存记录后，只允许与记录一致的结论通过；数据冲突或缺少必要签字时，不得标为最终验收通过。这是建议的验证办法，尚未执行。

宿主API格式接受、结构及已加载方法声明校验通过，答案实际交付；
内容质量交ChatGPT独立审阅，本次没有模型评阅或Jev胜负/净收益结论。

## 旧unknown与新请求的绑定

旧调用：`61784cbf0798ceba12ce2b8dcf0c90a97799011df3848a5904ac0cc9f595a31c`。
新调用：`05ff7650c4f16af70592214af2ae4b3c6256f8a5650f8bfd556a9addd2eb25e8`。
[请求关联记录](evidence/B1-compensation-request-link.json) 绑定旧/新意向及后继摘要。
两次保存的原始state和71题逐项相同；由旧绑定输入重建的wire-body摘要与新供应商receipt相符。
这是输入相同的证据，不是旧请求是否真正发出的证据。

旧 `serial/000004` 只追加[风险处置](evidence/serial/000004/accepted-unknown.json)，
状态为risk_accepted_remote_unknown，无completion，旧意向/outcome/额度未改。
新slot000005的previous_completion_sha256和previous_end_epoch均为null，
另行绑定previous_disposition_sha256和本地处置时间；不把风险接受冒充远端完成。
只给这个指定旧调用例外，其他unknown及安全/权限拒绝仍不能放行。

本次新Jev与宿主均明确返回，无新的未知调用，无观察到的401/连接恢复/采样重试。
旧调用远端终态、可能重叠及重复计算/计费仍未知，Owner已接受该剩余风险。
新成功不能反向证明旧工作已经结束。底层宿主HTTP/精确生成尝试数仍unknown。

## 配置、次数与分项时间

客户端归档确认provider=`mindthus_official_http`，请求`gpt-6-sol/xhigh`。
七项调用级覆盖与A1③相同，官方服务/认证保持；服务端宿主型号证明仍未观察到。
线程 `01a0e398-a928-7cc2-8ee5-c4891ec57511`，轮次 `01a0e398-aa3c-7883-9f7e-c58db183cb36`。

| 项目 | 本次实测/观察 |
|---|---:|
| 新Jev逻辑调用 / 宿主CLI启动 | 1 / 1 |
| 外层重试 / 可观察内部恢复 | 0 / 0 |
| 新明确返回的生成工作 | 2 |
| 主动等待合计 | 119.952124s |
| 补试前主动等待 | 60.005218s |
| Jev→宿主主动等待 | 59.946907s |
| Jev→宿主完整单调间隔 | 60.005203s |
| Jev evaluate | 3.833971s |
| 宿主CLI会话 / 归档task | 37.460029s / 27.073s |
| 本次完整执行墙钟 | 161.527518s |
| 其他装载/校验/记账残差 | 0.281394s |
| 纯HTTP、认证/连接恢复独立耗时 | unknown |

本地准备工作包含在完整间隔中，因此第二次sleep略少于60秒，而完整单调间隔超过60秒。
第一段等待只约束获准后的本地派发，不证明与旧远端工作无重叠。
保留旧run-start导致原路径wall=4772.359775s，其中含旧失败及人工暂停；
该数不能当作本次推理耗时。本次运行独立墙钟以上述161.527518s为准。

Jev input/output=15653/3604；宿主input/cached/output=25489/0/903。
金额未提供，保持unknown；不把不同供应商token直接相加充当费用。
B1总Jev尝试2（旧unknown1+技术补试1），额外授权额度已用1/1；原可选第二层额度未使用。
B1宿主已用1/4，剩3次；A1/native仍2/4，A1/direct仍1/4；全批Jev尝试累计3。
没有预算重置，未使用额度不授权挑结果或重复生成。

## 证据与交付边界

[72文件索引](evidence-index.json)、[完整机器摘要及十二条状态](summary.json)、
[定点接线diff](SCOPED.diff)、[封存路径结果](evidence/runs/B1/direct/result.json)。
旧文件摘要核对保持不变，原A1答案不变。没有追加诊断研究、鉴权探针、离线测试或R2复审。
本轮只检查新增例外接线的语法和执行所需身份/证据绑定。

十二条路径目前：A1两条已交付；B1/direct已通过本次授权补偿交付；其余九条未发送。
B1/native未运行，尚无B1配对比较；旧失败的未知费用与补偿开销必须保留，不能包装成干净首发。
A1因传输条件不同仍排除匹配性能比较。一般质量与净收益继续待独立审阅和剩余实验。
