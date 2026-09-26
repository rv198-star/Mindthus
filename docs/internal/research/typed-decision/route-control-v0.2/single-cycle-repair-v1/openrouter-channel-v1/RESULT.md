# OpenRouter 接线与本次实际尝试

## 结果

按用户授权完成 OpenRouter Jev 显式接线与新 E/F 冻结，但 E② 的唯一启动调用被 OpenAI 工具安全检查在执行前拒绝。没有启动任何新的 Jev、Codex 或 CPA 推理；不声称端到端测试完成。具体触发规则未披露，不根据这个提示推断密钥无效或 OpenRouter 服务异常。

此前 OpenRouter GET /api/v1/key 鉴权成功，不能替代 POST Decisions 推理成功。本次没有再次鉴权测试，没有更改请求形式重试。

## 完成的代码与验证

实现提交 f20c71f；预登记/冻结提交 c79596e。既有 Jev 引擎继续使用，增加 v0.3 对固定 OpenRouter serving 的显式准入及 driver --serving 选择。requested_model=typesafe/jev-1.13，实际 resolved runtime 仍须按返回记录。本地供应商身份替换会被原冻结准入拒绝；不自动回退，不允许其他模型。

原题文、阈值、消费语义、宿主型号/配置、默认Skill和main未改。正常入口仍不预加载八个方法。旧 TypeSafe 冻结及代码工作树保留，新渠道使用新root。E⓪旧基线原45个文件逐字不变，原始输入、入口及宿主配置与新E冻结精确核对一致。

渠道/比较定向23项通过。初始312项回归中唯一失败是旧错误文本匹配，已同步断言，未改变拒绝行为。最终全仓1654项运行，1649成功、5跳过、0失败；生命周期95/95。日志已归档。均为工程验证，不是模型准确率证据。

## 固定进度

| 来源与方式 | 真实状态 |
|---|---|
| E⓪：Skills首轮无Jev | 旧3次宿主调用及最终接收复用，本次未重跑；内容尚无新独立评阅 |
| E②：Skills首轮OpenRouter Jev | 新freeze完成；启动命令被拒，0请求，UNRUN |
| F⓪：4K后期快照无Jev | 新freeze完成；未启动 |
| F②：4K后期快照OpenRouter Jev | 新freeze完成；未启动 |
| ①及匿名逐维评阅 | 未启动，无胜负结论 |

E/F根目录均只有准备记录，没有intent、outcome或未知在途请求。E输入只有第一条用户消息；F仅限缺图后期回归，不冒充原始失败重现。本周期仍最多8次新Jev请求；本次使用0次。后续若获准执行，直接使用新OpenRouter冻结，不改写旧TypeSafe记录或重跑已完成E⓪。

## 证据

同目录 preflight.json、E-freeze.json、F-freeze.json、execution-attempt.json、full.log、serving.log；上级 OPENROUTER-PLAN.md。启动拒绝为实际工具返回，execution-attempt.json 是操作者对该工具结果的记录，并非来自供应商的HTTP响应。
