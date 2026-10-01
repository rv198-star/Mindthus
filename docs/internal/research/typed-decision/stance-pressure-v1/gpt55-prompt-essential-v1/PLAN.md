# GPT-5.5 / medium：同题两回合探索对照

Owner于2026-10-01明确要求“那我们测下5.5吧”。本轮最多2次宿主生成，
只用https://sub2api.72live.com/v1/chat/completions，gpt-5.5／medium，
max_completion_tokens=8192、stream=false，与上一轮配置只有模型不同。
没有CLI、Jev、评阅、纠偏、技术或语义重试；任一失败停止。

两回合问题逐字复用sol56-prompt-essential-v1；第二轮只携带本次5.5首答。
规范文件字节也复用，不进入API消息。只发送user及实际assistant，
无system/developer、工具、Skill目录、AGENTS背景或输出JSON合同。
不把“本质Prompt”的条件化认可本身当成错误，不靠缺关键词判错。

已有通道清单列出gpt-5.5，无须重新GET或发鉴权探针。
官方型号依据：https://developers.openai.com/api/docs/models/gpt-5.5
该文档支持medium，列出snapshot gpt-5.5-2026-04-23；允许返回alias或该snapshot，
不允许其他型号。服务端后台权重、隐藏背景及实际档位仍未独立证明。

继承75=59宿主+16Jev，上限77=61宿主+16Jev，最多新增2宿主，0Jev。
父serial现有000000–000072；沿用单发送者、60秒冷却及指定旧000068处置。
旧unknown、意向、返回和消耗不改写；没有新unknown例外。
失败保留，不用新根重置或自动重发。

最早Skills场景记录于2026-06-29，早于5.6 Sol公开发布；原模型身份未记录。
本次不能确认当时是5.5，也不能证明代际变化是差异的唯一原因。
仅观察当前同题返回，保留两个首个产物，结果允许无明显偏差。
不改旧六案、GJ/R2关闭、设计、默认Skill/main或ROI-Beta边界。
