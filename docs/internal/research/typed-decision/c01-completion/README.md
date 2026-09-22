# C01 可运行实验入口

`experiments.typed_decision.c01_host` 把当前C01图、不可变日志、核验交接与CPA中文回答串成
一个只读实验入口。不是原生Codex hook，不改变Mindthus默认路由，不启用外部工具。

## 使用

在仓库根目录，用Python3.12。先把本次输入准备为C01 context对象；当前已验证的Jev
执行分布是英文State加完整英文derived canonical。中文请求需先保留事实、约束、权限
和来源地转为英文执行视图，再冻结；本入口没有偷偷增加在线翻译或动态设计器。

```sh
python3.12 -m experiments.typed_decision.c01_host prepare \
  --context /absolute/path/to/context.json \
  --method-root /absolute/path/to/matching-method-snapshot \
  --model deepseek-v4.1-flash \
  --authorization-ref '本次已授权的只读实验及预算来源' \
  --manifest /absolute/path/to/new-admission.json

python3.12 -m experiments.typed_decision.c01_host run \
  --manifest /absolute/path/to/new-admission.json \
  --state-root /absolute/path/to/trial
```

凭据从进程环境提供：`TYPESAFE_API_KEY`、`MINDTHUS_HOST_API_KEY`；不要把key写在命令、
manifest或仓库文件里。准备步骤不需要key，也不推理。授权引用只是可追溯记录，不能
替代用户真实授权。清单冻结精确context、所有方法摘要、代码身份、模型/渠道与预算。
改任一项须重新审视授权和版本，不能篡改旧清单继续使用旧结果。

## 实际执行与恢复

每个清单最多3次TypeSafe官方Jev调用（60秒、USD0.008064预留），再最多1次CPA
指定模型调用（60秒、1600输出tokens、49152请求字节）。CPA费用仍未知，无美元上限
或厂商直连价格估算。默认DeepSeek；明确清单才能选已授权GLM，运行中无自动切换。

正常路径读取选中方法的完整合同、核验调用记录、交给宿主生成回答。回退路径保留
义务；如果已检查过某方法，handoff v2另带其完整合同和真实status/value用于解释。
这不会把被拒绝的方法放进selected_method，也不会把unclear/error写成no。
C01 graph4及其语义问题未改。

- 已完成的summary：再次运行直接读取，0新调用。
- 路由已完成、宿主尚未启动：可复用路由，继续尚未发生的宿主调用。
- host intent存在但outcome缺失：停止，不重发；先核对原请求的服务端结果。
- 返回了技术失败：失败作为该次结果保留，无自动重试；不通过换目录抹去成本或失败。
- 源码/输入/合同/配置变更：清单不匹配，停止。
- 活跃链路使用独占锁；读取旧路由做交接仍使用其原共享日志锁。

C01自身仍报告consumption=not_executed；独立host记录能证明提交的上下文与生成回答。
回答生成不等于外部动作或原生skill加载，native_skill_load仍为not_observed。
不要把技术status=complete解释成任务验收passed。

## 本轮收尾验证

[本轮结果与剩余缺口](disposition.md)：代码及全仓回归完成；固定5项中3项任务标准通过、
1项连接失败、1项未测。完整真实Jev→宿主链路尚未验证，不能把这个入口当作已验收默认能力。
L27/L28内部字段泄漏另列为表达缺点，未继续调提示词。两次trial均已终止，不复跑。

[预冻结协议](protocol.md)覆盖2个方法拒绝、2个已成功控制项，以及1个新场景真实完整链路。
原终止试验及其失败保留；不新增Jev语义调参。旧N03路由误挡不能因宿主恢复而改判。
完整任务资格还需要独立holdout、真实原版A及正式比较；本入口不冒充这些证据。
