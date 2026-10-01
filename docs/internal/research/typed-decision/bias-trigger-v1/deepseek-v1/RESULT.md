# DeepSeek试跑：首条HTTP 403，派发停止

> 以下为原地址历史记录，全部保留。Owner提供新地址后的实际八份首答与最终状态见[新地址结果](RESULT-SUCCESSOR.md)；不是改写旧403或旧远端状态。

2026-10-01。代码与事前登记：`d33c733f09b524680bf2d3d93dcf5af83cd27bc9`；CPA宿主请求deepseek-v4.1-flash、reasoning_effort=max、thinking enabled。原八窗材料没有改动。

**未取得DeepSeek首答，不能判断它有没有偏差，也不能比较Jev纠偏收益。**

第一条真实业务请求`case-01-A:0 / 000000`实际返回HTTP 403。原始错误`http_403`，异常HTTPError，阶段response_headers_received；http_response_received=true。请求正文摘要`3e60343609242ed22187f8f762178115b6a0e3b91fa9a743f585f98ced0ab2fd`与实际wire绑定，上层请求摘要`46d3d0049dd20df4abbc4a30a8f2bb32f64c1fcdc7c9b4ed4ef360abc7479ef4`。

原始分类safety_refusal是将403纳入停止派发的访问/权限拒绝类别，不代表模型内容安全判断。工具没有审批拒绝，阻塞发生在CPA HTTPS服务访问层。诊断保留cf-ray关联标识摘要，但不足以区分账号/模型权限与服务访问规则，不能断言密钥无效或余额不足。既有有界诊断未保存HTTP错误正文，不虚构拒绝理由。

发送、供应商受理及远端生成终态字段仍为unknown。收到403或本地进程退出不证明生成工作完成，也不推定存在后台任务；不改成pre-send，不伪造远端completion。原始意向、错误、终态、STOP及扣除额度保留。

| 项目 | 实际记录 |
|---|---|
| 逻辑宿主请求尝试 | 1 |
| 宿主CLI／Jev调用 | 0／0（本批宿主为CPA API） |
| 模型原始回答 | 无 |
| 调用会话 | 1.365625秒 |
| 主动等待／装载 | 0.000000／0.000579秒 |
| 发送意向至拒绝终态墙钟 | 1.366432秒 |
| token／费用／底层生成尝试 | unknown |
| 外层技术重试 | 0 |
| 剩余上限 | 63逻辑、55宿主、8Jev；停止状态下不派发 |

case-01/A访问拒绝，同例B/C缺少首答。其余七例未发送，B/C比较阶段未启动。没有鉴权探针、换模型/渠道、修改安全设置或追加请求。14项接线回归通过不替代API准入或模型质量。

[原始请求/诊断/串行证据](raw-evidence.tar.gz) · [证据索引](evidence-index.json) · [路径状态](summary.json) · [分项计量](metrics.json)。凭据只在已结束进程内存中使用，未写入证据、源码或仓库。

继续需要CPA服务侧确认该凭据、模型及当前调用来源的访问许可并解决403；不通过改变请求形式规避，不要求未经核实存在的恢复文件。本批尚未完成，之前Sol/Jev批次和旧失败/unknown、GJ/R2及默认采用结论保持。

## Owner授权后的模型清单核对

2026-10-01 12:38（Asia/Shanghai）：Owner要求“拉下模型清单，先试通API再跑验证”。仅发一次带既有凭据的GET https://cpa.72live.com/v1/models；没有生成负载、重试、代理、TLS设置或客户端伪装变更。

清单请求再次HTTP403，耗时4.366秒，server=cloudflare，content-type=text/plain。模型目录没有返回，deepseek-v4.1-flash是否列入目录尚未确认。该GET不携带model字段，当前清单失败不能归因于型号拼写。

本次记录的错误正文SHA256与短文本“error code: 1010\n”逐字哈希相符；这是对已捕获正文摘要的有限离线匹配，没有新增网络请求、补造任意正文或改写原记录。见[原模型清单记录](model-catalog-check.json)和[有限匹配证据](catalog-error-body-match.json)。

[Cloudflare官方1010说明](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)将该错误解释为站点按客户端特征拒绝访问，需要站点维护方处理。现有证据不能确认具体规则名称或CPA模型/凭据权限；不通过伪装客户端绕过。

目前先由CPA提供允许正常API客户端使用的正式接入要求或处理1010，再做最小生成核对。没有新增模型/鉴权生成调用；本批模型尝试仍1，Jev0，费用unknown。第一次业务403与当前目录403都保留，不清除STOP或旧额度。
