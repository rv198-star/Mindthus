# Sol5.6 / medium：CPA最小消息两回合重测

Owner本轮明确改用CPA，清单GET已成功并列出`gpt-5.6-sol`。
本次只重测两条原始用户消息；第二轮使用本次实际首答。
客户端请求不发送system/developer指令、JSON回答合同、工具、技能目录、
项目背景、旧CLI答案、认知规则、评语或独立判断要点。
返回正文仅在本地包装供既有consumer接收；不要求模型输出包装。

使用既有CPA POST传输、错误诊断、driver、父批次单发送者锁和serial。
前项明确结束后至少60秒；复用原generation-scheduling.v2。
最多2次生成、0次重试、0次CLI、0次Jev/评阅/纠偏。
继承70=54宿主+16Jev，最多72=56宿主+16Jev，不重置旧额度。
唯一额外非生成操作为本轮获准的模型清单GET；不发鉴权探针。

请求`gpt-5.6-sol / medium`、plain text、max_completion_tokens=8192；
90秒既有单次传输deadline。费用和代理下游HTTP次数未知。
CPA清单及返回model字段是服务方标识，不是底层权重/官方身份独立证明；
代理内部背景、实际reasoning档位如未反馈，保留未知。

两个问题逐字复用公开原题，不是holdout。norms仅供执行端读审，不入业务提示。
技术失败/unknown保留；unknown或拒绝停止，不自动补发或扩大旧风险接受。
旧两轮CLI的实际答案和裸测不合格更正均保持。
此次仅检查新增发送边界；不重审GJ/R2或旧实验，不追求制造偏差。
