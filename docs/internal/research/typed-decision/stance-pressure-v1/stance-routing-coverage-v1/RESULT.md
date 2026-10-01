# 四型号v2覆盖：5.5/5.6完成；5.4受限；DSF远端未知

2026-10-02。Owner要求补齐模型覆盖；固定执行源码
`2d673216ceba93efcfc636c38ab0c4c5f06664ee`，设计基线
`996c7bdeab156e1a40915147d13ab32b00af3117`。
这是同一公开Skills两轮争论的探索覆盖，不是holdout、独立内容审阅或多案例准确率测量。
既存6.1不重跑。新增5.5和5.6取得各自独立B/C核对；5.4被供应商明确拒绝，
DSF首次B路由在90秒本地截止时没有取得远端终态，停止后续派发。
**覆盖未全部完成；不能把受限或未返回当成Jev判断失败。**

本批观察：5.5/5.6中，Jev和同型号LLM均选择全象检查；Jev路由较快。
四份独立宿主核对均决定保留各自原A2，没有产生新增纠偏稿。
这没有证明Jev独有质量优势，也没有推翻用户指出的原答案价值解释缺口。
“宿主自称已充分”是待审产物，不能作为独立质量通过证据。

## 输入与比较身份

[事前范围](PLAN.md)、[冻结材料与型号](cases.business.json)、
[独立于业务输入的事前要点](norms.evaluation-only.json)、[生效登记](admission.json)。
U1/U2不改；5.5、5.6、DSF直接复用已绑定实际wire/raw/terminal的本型号A1/A2。
所有新路由只看完整U1/A1/U2一次，不带A2或事前规范；A2只进入之后的宿主核对。
同型号B/C路由用同题、相同S0；B分类不伪造概率，C按原0.8采纳。
不同型号A1自然不同，本批不是相同完整会话的跨模型排名。

gpt系列用已登记Sub2API、medium、非流式、max_completion_tokens8192；
DSF用既有CPA.rn-us、medium、thinking enabled、temperature0、max_tokens8192。
Jev保持官方jev-1.13.0。无新渠道、别名、账号或鉴权探针；凭据仅在进程中装载。
“medium”不是各供应商相同内部计算量的证明；实际生效配置保存于
`evidence/runtime/effective-config-*.json`。服务端返回型号保留原始身份，
不能据别名断言后台权重、账号或执行实现一致。

## 五型号实际状态及原始产物

| 型号 | A裸答 | B同题LLM入口 | C官方Jev入口 | U2载体限定控制 | 覆盖状态 |
|---|---|---|---|---|---|
| gpt-5.4 | 首轮明确拒绝，无答案 | 未发送 | 未发送 | 未发送 | 型号/账户准入受限 |
| gpt-5.5 | 既存实际两轮，逐字保留 | whole_check；独立核对kept | whole_check，0.84；独立核对kept | retain，0.95 | 新增覆盖完成 |
| gpt-5.6-sol | 既存实际两轮，逐字保留 | whole_check；独立核对kept | whole_check，0.90；独立核对kept | retain，0.95 | 新增覆盖完成 |
| gpt-6.1-sol | 既存实际两轮，逐字保留 | 既存whole_check | 既存whole_check，0.94；核对revised | 既存retain，0.89 | 历史路由覆盖保留；共享核对限制保留 |
| deepseek-v4.1-flash | 既存实际两轮，逐字保留 | 首次路由远端状态unknown，无有效判断 | 未发送 | 未发送 | 新unknown阻断，尚未完成 |

5.5：[首轮](gpt55-A.turn-1.reply.txt)、[原A2](gpt55-A.final.reply.txt)、
[B原始路由](gpt55-B.route.reply.json)、[C原始路由](gpt55-C.route.reply.json)、
[B核对原始产物](gpt55-B.handling.reply.json)、[C核对原始产物](gpt55-C.handling.reply.json)、
[B最终稿](gpt55-B.final.reply.txt)、[C最终稿](gpt55-C.final.reply.txt)、
[控制原始返回](gpt55-carrier.route.reply.json)。

5.6：[首轮](sol56-A.turn-1.reply.txt)、[原A2](sol56-A.final.reply.txt)、
[B原始路由](sol56-B.route.reply.json)、[C原始路由](sol56-C.route.reply.json)、
[B核对原始产物](sol56-B.handling.reply.json)、[C核对原始产物](sol56-C.handling.reply.json)、
[B最终稿](sol56-B.final.reply.txt)、[C最终稿](sol56-C.final.reply.txt)、
[控制原始返回](sol56-carrier.route.reply.json)。

DSF：[既存首轮](dsf41-A.turn-1.reply.txt)、[既存A2](dsf41-A.final.reply.txt)。
没有新B/C答案，不用原A2冒充新核对稿；[失败原始记录](evidence/runtime/calls/000011/raw.json)。
6.1沿用[固定历史报告及原文](../stance-routing-v2/RESULT-COMPLETE.md)
（提交434cc7a2422d8d53f135e589fb83eb606100cb75）：共同核对实际改写了
“输入载体归类已完整说清对象”的判断，但B/C共用一次宿主返回，不能称独立最终稿配对。

本批5.5/5.6核对wire各自相同，**每型号实际发两次独立核对**，有不同call_key、raw和terminal；
四份kept最终稿逐字等于各自实际A2。这是模型决定保留，不是夹具、人工作答或共享生成。
控制只改U2为明确只问载体的既有文本，保留同型号U1/A1；它是人工反事实，
没有补造自然A2，也没有额外宿主回答。

## 重要判断与尚未建立的收益

5.5原A2仍以“Skills不是Prompt之外的新东西，而是Prompt被工程化之后的名字”收束。
5.6原A2区分最终Prompt、生成策略和外部执行，但本批核对均没有进一步改变主次判断。
用户关心的知识/经验、Workflow/Agentic及SOP承载价值没有因为模型输出kept就被判为已解释充分。
是否原文本来充分、或者宿主核对仍偏向载体争论，需要内容审阅；本批不追加评阅模型或追分重跑。

有证据支持的局部结果是：新题义下，5.5/5.6的Jev路由有效采纳了whole_check，
并在载体限定控制中退出。Jev没有输出语义理由或原句定位；不能把后续宿主理由归到Jev。
普通同型号LLM也完成了相同路由，因此不存在本批证明的独有识别能力。
当前未出现新增弱模型纠偏稿；6.1先前的实际改写是保留的局部正向例，不外推为普遍优势。

## 性能：路由与整条处理分开

均为执行器会话时间，含传输与封装，不是纯推理或纯HTTP测量。

| 型号 | B路由秒 | C路由秒 | B独立核对秒 | C独立核对秒 | B路由＋核对秒 | C路由＋核对秒 |
|---|---:|---:|---:|---:|---:|---:|
| 5.5 | 6.197 | 0.992 | 44.833 | 40.220 | 51.031 | 41.212 |
| 5.6 | 4.224 | 1.117 | 32.515 | 42.063 | 36.740 | 43.180 |
| 6.1，历史 | 4.715 | 1.094 | 无独立B调用 | 48.193，共享返回 | 不可独立比较 | 不可独立比较 |

5.5/5.6单次路由分别少约5.206/3.107秒；C用一次Jev替代一次宿主路由，
但B/C主要路径总逻辑调用均为2（路由＋核对），并没有少一次总逻辑调用。
5.5本次C整段处理较快；5.6本次C反而较慢约6.440秒。核对长度、缓存、
非固定采样及单次传输波动都存在，不能据两行推算稳定均值或普遍收益。
5.5的C核对缓存3840token，5.6的B核对缓存2432token，原始usage均保存。
独立控制开销各保留：5.5为1.013秒，5.6为2.111秒，不隐藏在主路径优势之外。
冷却是实验调度要求；下表完整保留，不宣称它是模型固有延迟。

## 全部新增尝试、等待与用量

本地槽000000–000011对应父serial000087–000098；[逐请求摘要](actual-receipts.json)
保留request/wire/terminal摘要、原始返回、gap与完整usage。
宿主为HTTP适配器；本轮CLI启动0，额外评阅/鉴权探针0，外层与技术重试0。

| 父serial | 路径 | 终态 | 会话秒 | 主动等待秒 | 原始用量 |
|---|---|---|---:|---:|---|
| 000087 | 5.4裸答首轮 | failed / http_400 | 2.429 | 60.005 | unknown |
| 000088 | 5.5 B路由 | returned | 6.197 | 60.004 | prompt2918 / completion212，reasoning170 |
| 000089 | 5.5 C路由 | returned | 0.992 | 59.903 | input3617 / output45 |
| 000090 | 5.5 C控制 | returned | 1.013 | 59.905 | input3656 / output44 |
| 000091 | 5.5 B核对 | returned / kept | 44.833 | 59.924 | prompt4245 / completion2249，reasoning289 |
| 000092 | 5.5 C核对 | returned / kept | 40.220 | 59.899 | prompt4245 / completion2082，reasoning167 |
| 000093 | 5.6 C路由 | returned | 1.117 | 60.005 | input2473 / output45 |
| 000094 | 5.6 B路由 | returned | 4.224 | 59.911 | prompt1902 / completion118，reasoning76 |
| 000095 | 5.6 C控制 | returned | 2.111 | 59.914 | input2523 / output44 |
| 000096 | 5.6 C核对 | returned / kept | 42.063 | 59.894 | prompt2620 / completion2052，reasoning882 |
| 000097 | 5.6 B核对 | returned / kept | 32.515 | 59.910 | prompt2620 / completion1629，reasoning463 |
| 000098 | DSF B路由 | unknown / deadline_exceeded | 90.009 | 60.005 | unknown |

新增12次逻辑尝试＝8宿主＋4Jev；10返回、1明确失败、1unknown，全部计入。
继承89后累计101＝77宿主＋24Jev；本阶段上限111＝83宿主＋28Jev未超。
剩余10＝6宿主＋4Jev不是自动重试许可，也不能据此解除新unknown。
各供应商原始token分别保留，金额、精确底层HTTP/生成次数unknown。
本地没有观察到内部恢复；服务商后台是否恢复或重发未暴露，不能写成精确零次。

会话合计267.724秒（含90秒未知和5.4拒绝）；主动等待719.278秒；
装载0.005564秒；派发活动窗口和987.007秒。
首个profile启动至DSF本地停止988.402秒，约16.47分钟；不包括之后证据整理、提交或推送。
新12次实际间隔最小60.004344秒；sleep略少于60秒的记录有其他本地时间，
实际gap没有放宽。完整墙钟是截至本地停止，**不是远端未知工作完成时间**。

## 两处阻塞，准确分类

**5.4：供应商明确型号/账户准入拒绝。** 首次真实裸答得到绑定HTTP400及
invalid_request_error，原文：

> The 'gpt-5.4' model is not supported when using Codex with a ChatGPT account.

[原始诊断](evidence/runtime/calls/000000/raw.json)、[终态](evidence/runtime/calls/000000/terminal.json)。
模型目录可见不能证明该账号/渠道可用。没有答案、第二轮或5.4 B/C输入；
不换型号别名、账号、渠道或启动形式。没有把它称为新工具安全拒绝。
serial的本地invoke返回收据只表示失败已返回，不表示生成成功或供应商答案completion；
低层阶段诊断保留unknown，明确HTTP拒绝内容支持本次failed分类。

**DSF：本地截止，远端状态未知。** 新请求在parent_worker_wait阶段触及90秒；
没有HTTP响应、可绑定远端终态或生成受理证据。stream=false，不能擅称SSE空闲错误。
进程截止不能证明pre-send、远端已结束或必有后台工作。
它不是有效路由、模型能力失败或已观察到的安全拒绝。

- 父serial：000098；本地槽：000011。
- call_key：`stance-routing-coverage-v1:dsf41-current-B:0`。
- request_sha256：`346106b19d142cc27b46475a158ed1cd7a457c96aaf28215279ac61eb59ec6b5`。
- terminal_sha256：`4d285764d1a613de6d94de63acb2fb34cab9d99f4f4831aa200d54413cfbd424`。
- [原始诊断](evidence/runtime/calls/000011/raw.json)、[unknown终态](evidence/runtime/calls/000011/terminal.json)、
  [实际STOP](evidence/runtime/STOP.json)、[父意向](evidence/serial/000098/intent.json)。

原intent、raw、unknown、已耗尝试/等待保留，serial000098没有completion。
DSF C原题、C控制及两臂核对均未发送，没有新DSF路由结果。
旧000068的指定risk_accepted_remote_unknown继续保留，不能覆盖此次新unknown。
按[事前范围](PLAN.md)，不自动补试；若Owner希望继续，需要仅针对此call接受
可能重复计算/计费及远端重叠的剩余风险，或维持当前停止。
没有要求未经核实存在的特定“恢复文件”，也没有追加权限盘点或鉴权探针。

## 代码、证据与交付边界

最小代码仅增加四profile覆盖接线及测试，不改v2题面、阈值、消费模板或核心。
[5项定点测试日志](test-wiring.log)为真实执行的新增接线验证；旧GJ/R2不重审。
[本批证据对账](verify-actual-evidence.log)核对12份request→wire→raw→terminal→import，
生效源码摘要、独立核对及新serial间隔；它是执行端对账，非独立质量审查。
[证据索引](EVIDENCE-INDEX.json)只覆盖本批保存的字节，不声称重算旧全部档案哈希。

此次交付是两型号新增覆盖及两处明确阻塞的真实记录；完整四型号覆盖尚未达到。
局部路由效率价值成立于这些单次观测；新的纠偏收益、稳定端到端优势、默认采用或金额ROI未建立。
旧六案、已关闭设计/GJ/R2、main/默认Skill和ROI-Beta结论边界均保留。
