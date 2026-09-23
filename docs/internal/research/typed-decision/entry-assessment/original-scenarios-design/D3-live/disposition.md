# D3 首轮实测结论：真实接线已执行，完整纠偏验收未通过

Status: terminal batch; real integration exercised; **D3 correction acceptance NOT MET**.
D1 questions are unchanged. Source: `6fa33f2`; admission: `716496e25688ac936c18ed8e292cbb3ddb33689a`.
This is author review of recorded observations, not independent effect validation.

## 1. 实际结果，不用工程通过代替场景成功

本批四个episode、六个输入都已获得终止状态。实际发生5次TypeSafe Jev请求、1次CPA结构整理；
**真实纠偏0次、真实复查0次**。Skills/4K的四个主目标轮次均被Q0挡回原责任方，未产生新候选。
简单Skills解释保持原答案；原文整理分支在引用验证失败后终止。没有重试、改题、改标签或换模型。

| 输入 | 实际入口状态 | 场景结论 |
|---|---|---|
| Skills首轮 | Q0=`both`，返回原责任方 | 未验证纠偏；无新回答 |
| Skills范围纠正后第二轮 | Q0=`both`，返回原责任方 | 未验证纠偏；范围/定义细分信号未消费 |
| 4K现有设备/评论帮助判断 | Q0=`both`，返回原责任方 | 未把无主判断的候选改成处境化结论 |
| 4K购前第二轮 | Q0=`both`，返回原责任方 | 未产生预算/锐度条件化修正 |
| 有依据的最小Skills解释 | Q0=`usable`，continue_original | 本反例未被强制反对，未触发重写 |
| 原文输入的评论相关性 | organizer_failed | 重复引用无法消歧；未进入Jev判断 |

原始summary里的`final_text`在回退路径只是保留的候选文本，不是宿主已经交付给用户的最终答案。
插件没有把错误候选当成新通过的答案。原宿主后续处理没有运行，所以也不能算成“原宿主已补救成功”。

第二轮确实包含前轮实际返回的候选，而非偷偷插入正确答案；但前轮没有纠偏，故承接的是保留候选。
所有新轮候选仍是作者预置压力材料。源观察明确为开发对照给定，不能当真实产品实验或独立事实。
这不是自然多轮失败采样，不是D4原文端到端A/B/C，也不证明默认Skill已启用。

## 2. 同批细分信号存在，但被前置条件挡住

原始55个类型化答案中有以下针对性信号：

- Skills首轮：alignment=object_substituted。
- Skills第二轮：scope_acceptance=preserved、alignment=aligned，local_transfer=local_overreach，
  definition=carrier_only_unjustified。即“接受范围”与“接受解释”在返回值中能被区分。
- 4K当前使用：readiness=decide_now、delivery=list_only；物理限制被评为claim_limit，
  给定可用性改进被评为decision_driver。
- 4K购前：readiness=conditional_decision、local_transfer=local_overreach。

四轮Q0都选择`both`（结构遗漏且映射有问题），所以以上信号按冻结合同未被消费。
这些不是四次成功纠偏，也不证明每个细分信号正确；不能用它们覆盖Q0结果。
离线诊断将Q0人为设为usable后可生成具名修正计划，仅保存为**counterfactual policy projection**。
它没有触发真实纠偏或新模型调用，不属于实测成绩，更不构成删除Q0的批准。

## 3. 可核实的问题与尚未隔离的原因

### 输入位置提案：确有需修正之处，不能先给Q0判误报

预置packet为候选的thesis_refs和controller_refs统一引用整段候选。尤其4K当前使用候选
只有“双方各对、无法判断谁切题”的罗列，本来就未表达结果控制关系，却仍提供整段controller_refs。
这至少暴露了作者输入准备过粗；D1的字节引用检查只证明位置存在，不证明这种语义标注成立。
部分frame概括也全部标explicit，没有逐项区分直接陈述与推断。

**尚不能确定四次Q0否决分别由哪些项造成。**Q0没有返回理由/具体错误位置，本轮没有做新的
对照推断。可能包括实际提案缺陷，也可能包括将待评候选的错误当成提案错误的混淆；后者只是
待验证假设，不写成已证根因。正确处理是回到引用/角色提案，而不是调低门槛或跳过Q0。

### 原文整理：技术拒绝已离线复现，且存在接口歧义

实际CPA返回在`proposal.frames[0].actor.refs[0]`引用`U`中的“楼主”。该词出现两次。
`locate()`要求子串唯一，因此返回`model_quote_missing_or_ambiguous`，未产生任何Jev请求。
原始请求要求精确非空引用或full，但没有明确要求唯一匹配/消歧位置；适配器要求比请求合同更严。
这属于具体的引用接口缺口，不是网络连接失败、限流或密钥错误。

可行修复方向是有界预编号片段或显式出现次数选择，验证后由代码算位置/哈希；
不要默选第一次、模糊匹配、自动改写原文或要求模型生成哈希。
此外，整理输出把若干合法范围/目标约束放在user_hypothesis claims中，未选择两项给定来源观察；
即便修复引用格式，也不能因此假称语义整理已正确。原始返回全文和离线定位结果都已保存。

## 4. 工程证据与用量

- Same `entry.run` / CLI → D2 runtime → D1 compile/consume → existing Session，未走替代执行图。
- 5个Jev结果均为实际固定版本`jev-1.13.0`；CPA结构整理返回`deepseek-v4.1-flash`。
- 66份不可变JSON、6个外部intent、6个outcome；无未知在途调用。
- 六个终止输入逐一从PUBLIC entry重新读取，守卫transport调用0，所有记录摘要保持不变。
- 默认无准入仍拒绝真实调用；D1语义、Provider/Session/C01与旧终止试验均未改。
- 20个新增D3控制与173项集中回归通过；全1408=1403成功+5跳过，零失败；lifecycle85/85。

| 部分 | 请求 | input/output tokens | 请求耗时累计 |
|---|---:|---:|---:|
| TypeSafe Jev | 5 | 37,644 / 3,403 | 1.492282 s |
| CPA原文整理 | 1 | 930 / 1,134 | 5.676946 s |
| CPA纠偏 / Jev复查 | 0 / 0 | 未发生 | 未发生 |

双方没有返回实际金额。不能把预留USD0.12当账单，不能把7.169228秒请求时间当总开发用时或速度收益。
凭据仅注入单个命令进程环境；即时精确扫描1636文件零命中。没有写入持久Skill环境或Git。
收尾不需要重读Key、调用模型或重复全仓测试。

## 5. 终止决议与下一步

**本批实测终止并归档；D3代码接线已实现，但真实纠偏验收没有通过。#211继续OPEN。**
CPA纠偏适配器有离线测试，没有本批真实调用证明；S2复查也未被本批覆盖。D4未启动，默认Skill和main不变。

接下来的修复对象已经具体：
1. 将位置/来源提案按原文真实语义构建；没有主结论/控制关系就留空，区分explicit与inferred。
2. 明确Q0只核对提案忠实度，不因忠实描述了一份错误候选就要求候选预先正确；先检查实际输入缺陷。
3. 统一原文整理的引用选择合同与适配器验证规则；单独验证整理的语义角色。

未来验证需独立的新版本与结果前准入；保留本批负面证据，不续跑终止root、不强行放开Q0、
不把未消费信号或离线投影冒充真实纠偏成功。本轮没有悄悄开始第二个追分批次。
