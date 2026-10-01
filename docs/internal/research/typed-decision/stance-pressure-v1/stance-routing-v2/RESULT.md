# v2实际路由：原论证触发，载体限定退出

2026-10-02。本组探索中的两次官方Jev检测已完成；B对照及宿主答案处理尚未发送。
设计基线`996c7bdeab156e1a40915147d13ab32b00af3117`；实际执行源码
`d1d9c844065d9f7c2bcbf687a6c583b5a4b09858`。
不是新模型版本：两次均官方jev-1.13.0，所选概率>=0.8采纳，未改阈值或归一化分布。

## 实际原始判断

| 输入 | 原生Choice | 全部分布 | 原生confidence | 消费 |
|---|---|---|---:|---|
| 真实U1/A1/U2，主张载体相同已说明Skills本质 | whole_check | whole_check 0.94 / retain 0.05 / clarify 0.01 | 0.91 | 已采纳，等待一次全象核对 |
| 仅将U2改为明确只问输入载体，其他原文保持 | retain | retain 0.89 / whole_check 0.10 / clarify 0.01 | 0.84 | 已采纳，保持局部范围，不触发全象核对 |

原始回答为供应商结构化Choice JSON，分别保存在
[current.route.reply.json](current.route.reply.json)和[carrier.route.reply.json](carrier.route.reply.json)。
检测器没有返回语义理由或原句定位；表中的输入说明是执行者对已固定材料的描述，不伪装成Jev理由。

原始用户追问为：

> 脚本控制了Prompt的组合时机和顺序，但最终提交的还是Prompt。这不正好说明我的判断成立吗？组织方式再复杂，也没有改变本质吧？

完整U1/A1/U2在[snapshots.json](snapshots.json)。Jev待发送body只出现一次完整S0，
没有A2、重叠原文窗口、前置LLM提名、评价规范或原答案复核结论。
首条实际wire为5632字节，供应商报告2257input/45output；旧四题v1为32163input。
两版判断对象与题义不同，这个差别只说明实际材料负担变化，不构成同等有效判断的净性能比较。

## 答案状态与当前限制

- A：既存实际第二轮回答完整保留于[A.original.reply.txt](A.original.reply.txt)，未重生成。
- C正例：检测返回并已采纳whole_check；宿主核对未发送，没有新的纠偏答案。
- C载体边界：检测返回并已采纳retain；人工反事实开发材料，不是自然新回答或holdout。
- B正例：路由与按需处理均未发送；不能声称C比普通Agent更有效。

原因是当前执行进程缺少已登记Sub2API的MINDTHUS_HOST_API_KEY，项目与专用已查入口未找到。
已询问本地凭据文件路径；官方Jev凭据经既有授权入口正常装载。
没有发送鉴权探针、切换渠道、启动宿主CLI或从聊天历史复制密钥。
这是宿主凭据装载缺口，不是供应商失败或安全拒绝。

宿主待发送的[具体核对请求](request-S-current-C-handling.json)与
[实际格式](wire-S-current-C-handling.json)已经导出，含A2和被采纳分支，不含评价规范。
装载该服务既有凭据后，`python -m experiments.bias_trigger.stance_routing --run-host`
只执行C一次处理、B一次路由及按需一次处理，仍共用原父serial与剩余额度。
也可用`--host-env-file`指向Owner指定的本地入口；不需重做这两次Jev判断。

## 失败、计数与时间

最初新组调用键与已完成的旧v1调用键冲突，**在serial发送前本地被拒绝**。
原准备目录仅有request/wire/binding，没有intent/raw/terminal，也没有新增serial槽。
已追加[定点技术处置](local-call-key-repair.json)，完整准备目录移至同一运行根的
`prelaunch-call-key-collision/000000`归档；不删除历史，不创建completion或清除unknown。
新增可选版本前缀仅用于此Driver；旧Driver默认不变。
共享账本因此使用`stance-routing-v2:S-current-C:0`和
`stance-routing-v2:S-carrier-scope-C:0`，没有重发旧请求。
这是本地接线返修，模型调用0、预算重置0；不是一次Jev传输失败或技术模型补试。

| 计量 | 实际值 |
|---|---:|
| 新逻辑调用 / 宿主 / Jev | 2 / 0 / 2 |
| 可观察业务POST | 2；供应商底层次数unknown |
| CLI / 评阅模型 / 自动重试 / 技术模型补试 | 0 / 0 / 0 / 0 |
| 两次处理会话 | 1.094秒 / 1.045秒；合计2.139秒 |
| 主动等待 | 60.005秒 / 59.924秒；合计119.929秒 |
| 装载 | 合计0.000864秒 |
| 处理＋等待＋装载活动窗口和 | 122.069秒 |
| 首次登记到最后终态墙钟 | 451.182秒，含本地键修复、测试和工程间隙 |
| 原始用量 | 正例2257input/45output；边界2293input/44output |
| 金额、精确供应商HTTP/生成次数 | unknown |

第二次主动sleep略少于60秒，因为之前已有本地处理时间；两次派发的单调时钟间隔
均由原serial记录保证>=60秒。不能拿sleep字段单独当生成工作的完整间隔。
新增serial000082/000083均有明确终态及导入；新unknown0，安全/权限拒绝0。
旧000068仍risk_accepted_remote_unknown，不被这次成功清除。
累计86=66宿主+20Jev。本组硬上限89=69宿主+20Jev，尚余3次宿主、0次Jev；未用额度不代表必须调用。

新增接线的7项测试通过；先前两个离线错误及最初未发送日志均保留。
5次模拟轨迹明确simulation=true，与真实记录分开；不重复已关闭核心测试或全仓审计。
[summary.json](summary.json)为实际计数、分项时间和状态；
[32项本组证据索引](EVIDENCE-INDEX.json)定位请求、原始返回、终态、导入及串行记录。

## 当前能得出的结论

**新的直接语义路由在这一个公开正例及其单变量范围反转上形成了预期区分。**
这支持“上一版用法可能限制检测表现”的假设，尚未分离输入表示、题义和采纳方式的贡献，
更没有证明唯一根因。原v1两个0.27及合同错误继续原样保留。

Jev判断检查必要性不等于已经发现事实错误。当前无宿主纠偏答案、B对照或独立内容审阅，
不能宣称答案改善、Jev相对B增量、一般检测准确率或默认采用资格。
本组未完成：宿主凭据装载及至多三条宿主调用仍待执行。无需重复Jev，不扩展新批次。
旧实验、GJ/R2 CLOSED、main/默认Skill和ROI-Beta边界不变。
