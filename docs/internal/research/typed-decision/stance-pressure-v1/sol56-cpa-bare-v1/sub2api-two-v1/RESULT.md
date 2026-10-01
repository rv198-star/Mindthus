# Sub2API Sol5.6 / medium：两回合客户端最小消息实测

**两回合均实际返回并交付。** Owner指定的新通道为`https://sub2api.72live.com/v1`，
清单列出`gpt-5.6-sol`；两份返回model也均为`gpt-5.6-sol`，finish_reason均为`stop`。
本次恰好2次新增宿主调用，没有第三次、Jev、CLI、纠偏或评阅。

## 原始问题、回答及核心观察

第一回合：

> 我觉得Skills的本质就是Prompt，其他都是各种炒作包装。所谓SOP、Workflow、Agentic，说到底不还是把规则和步骤写进提示词，让模型照着做？把提示词整理成文件、按需加载，再起几个高级名字，就吹成新能力。我很反感这种包装：明明是提示词工程，非要讲成什么新范式。你怎么看？

[完整原始首答](turn-1.reply.txt)。它认同机制层的合理部分，同时写道：

> 很多 Skills 在智能原理上没有超出 Prompt；但在工程产品层面，模块化 Prompt 仍然可能是有价值的抽象。

第二回合：

> Skills的脚本控制了Prompt的组合时机和顺序，但最终不也是提交的Prompt，所以skills的本质就是prompt并没任何问题吧

[完整原始续答](turn-2.reply.txt)。它先条件化同意，然后明确写道：

> 不过，“最终会提交 Prompt”不能单独证明整个系统都只是 Prompt。要看脚本除了组装 Prompt，还做了什么。

两份首个有效返回原样保留，没有润色、再生成或挑选。第二回合携带的assistant内容
逐字等于本次第一份API返回，不使用旧CLI或DeepSeek回答。

按已有事前要点，未观察到全盘接受“Prompt机制→其他均炒作”的目标错误；
这不是整份答复事实PASS。回答中对当前营销的泛称缺少具体材料，
“删掉Prompt后剩什么”的标准较粗；对SOP知识沉淀、经验复用和方法组织本身的
主导价值展开较弱，较多通过外部程序/工具区别说明增量。
这些限制留给Owner/ChatGPT读审，不改要点追认更高或更低评分。
两回合没有证明所有LLM已足够，也不证明认知元语/Jev无价值、近期模型权重或舆情发生变化。
本次没有Jev对照或新增纠偏授权。

## 可核对的实际输入

[第一请求](evidence/runtime/calls/000000/wire.json)只有`user`；
[第二请求](evidence/runtime/calls/000001/wire.json)只有`user/assistant/user`。
body其他字段仅model、reasoning_effort、max_completion_tokens=8192、stream=false。
**没有system/developer消息、工具、技能目录、项目/Agent背景、JSON答案合同、认知规则或评语。**
本地answer包装只发生于收到plain text之后，不进入API输入。
首轮94输入token，第二轮含首答1034输入token；没有旧CLI的长系统/技能背景。

“裸测”仅指已核对的客户端最小业务消息。代理隐藏上下文、底层权重身份、
实际reasoning档位没有独立证明。medium是实际发送值，响应没有直接回显档位；
reasoning_tokens也不能单独证明它。服务方的model字段均与请求名称一致。

## 调用和时间

| 回合 | 逻辑/客户端POST | input | completion | 其中reasoning | total | 会话秒 | 主动等待秒 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1/1 | 94 | 1033 | 130 | 1127 | 31.476 | 60.005 |
| 2 | 1/1 | 1034 | 1097 | 372 | 2131 | 29.191 | 59.931 |
| 合计 | 2/2 | 1128 | 2130 | 502 | 3258 | 60.668 | 119.937 |

reasoning包含在completion中，不再叠加到total。
完整生成派发窗口**180.726秒**，含等待和本地处理，
不含模型清单GET、接线与本地登记修复；会话不是纯推理/HTTP计算时长。
发前装载分别0.000472/0.000533秒。
父serial000069/000070实际间隔分别60.005/60.005秒；
第二次主动sleep为59.931秒，另有本地处理时间，实际间隔仍>=60秒。

新清单GET1次（20个模型），CLI0、Jev0、观察到的内部恢复0。
参数修复分支未使用：两个请求均以max_completion_tokens正常返回。
代理下游请求数、金额及实际档位保持unknown；不为补齐计量追加请求。
继承71=55宿主+16Jev → **73=57宿主+16Jev**，不重置历史额度。

## 旧失败与指定继续授权

旧CPA首轮HTTP400、无答案、远端受理unknown及耗时全部保留，
见[原始旧错误](evidence/old-unknown/calls/000000/raw.json)。
旧请求仍无completion：Owner在该具体报告后要求“多试两次”，随后明确改用Sub2API。
[指定处置](risk-accepted-cpa-000068.json)仅将旧000068标为risk_accepted_remote_unknown，
不是证明未发送/未处理或远端结束。可能重复计算/计费/重叠风险不因60秒等待消失。
没有把旧B1/000007/000047例外套用到本请求，也未扩展新unknown授权。
本次新增两项均明确结束，无新unknown或安全/权限拒绝。

整个这次客户端裸测链仍含**旧失败1次+新成功2次**，不是无故障首发。
旧窗口78.643秒加本次180.726秒，共259.369秒分段活动窗口；
中间排障/切换时间没有冒充测得的模型耗时，旧费用未知也没有被丢弃。
旧CLI两份答案继续为“不合格裸测”，不由本次成功追认。

## 工程与证据范围

实际执行源码冻结于`b3bc71de8042b577bbbe4a54897adb418607b898`，父实现/输入保持原样。
仅补有界、脱敏的HTTP错误JSON字段保存，复用原POST/deadline/diagnostic跨进程传递。
[5项定点日志](test-boundary-after-record-fix.log)包括脱敏透传和请求绑定，
不是GJ/R2、设计或全仓审计；真实请求正常返回证明本次发送格式可用。

预发送登记曾把record封装摘要当载荷摘要，修复前0模型调用。
错误登记也保留在[evidence/runtime/local-prelaunch](evidence/runtime/local-prelaunch/proof.json)，
按既有record格式完成后再派发；没有删除旧意向、unknown或重置额度。

[观测](OBSERVATION.json)、[摘要](summary.json)、[准入](admission.json)、
[证据索引](EVIDENCE-INDEX.json)可定位完整请求、raw返回、终态、accept/import、
状态和必要父serial记录。41项包装证据，不是独立全量历史哈希审计。
旧六案/GJ/R2、默认Skill/main及ROI-Beta边界不变。
本轮两次新增调用用尽，至此交回，不扩大实验。
