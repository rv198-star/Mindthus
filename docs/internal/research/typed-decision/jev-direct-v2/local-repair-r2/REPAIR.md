# R2：补齐孤立返回的恢复检查

依据：[原 ChatGPT 任务返回的独立 R1 复审](R1-INDEPENDENT-REVIEW.md)。其结论为 REVISE：四项中第2/3/4项关闭，第1项仅剩孤立返回恢复缺口。本轮未取得审计附件，依据已读取的明确反例补测试。

## 最小改动

`serial.py::_validate()` 从业务 `intent.json`、`outcome.json`、宿主 `reply.json`、Jev `provider-receipt.json` 双向发现已有请求。任一返回证据缺对应意向时，报 `serial_orphan_response_evidence`，不初始化 first_call；已有意向仍必须与串行记录绑定并有明确完成记录。

request/prompt/schema 等发送前材料不作为已发证据，仍可恢复。这一改动也覆盖原评阅路径。没有新增平台、修改题组/阈值/预算、改动已关闭的冷却与宿主入口逻辑。

## 三个新增反例

1. X 完成后，仅删除 serial、serial-bindings、X host intent，保留 outcome/reply/result/seal：Y 不得发送。
2. X 写出 reply 后中断，仅删除同样三处记录、没有 outcome：Y 不得发送。
3. 仅有 request/prompt/schema、没有发送或返回证据：可恢复，CLI 仅调用一次。

全部只操作新建夹具。`targeted.log`：33 项本地串行/恢复测试通过（含三个新增反例），未重跑其余已经独立关闭的整仓审计。旧原始证据与冻结仍保留。

## 独立复核结果

原 ChatGPT 会话已通过直接任务消息接收固定提交，并返回 [R2 独立定点 PASS](R2-INDEPENDENT-REVIEW.md)。其实际复跑三个新增测试，3/3通过，并用原独立脚本复查两个反例，均在发送前阻断；准备材料负对照只发送一次。两类检查有重叠，不当成五个独立业务样本。

至此，本次四项工程发现全部关闭。评阅者没有重新逐项核验383文件归档，该覆盖限制保留。审计附件仍位于其sandbox，仅将实际回复正文归档，不声称下载了附件。

状态：定点工程返修闭环完成。六场景两臂真实业务仍 UNRUN；质量、净收益未评估。业务外部模型调用0；工程PASS不构成真实业务续发许可。
