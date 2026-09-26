# 官方 TypeSafe 渠道恢复：真实 Jev 已返回，宿主回执未通过

## 本轮结果

根据用户“现在可以换成官方的Key了”的授权，当前driver显式选择typesafe，模型固定jev-1.13.0；新官方E/F冻结与历史OpenRouter及原TypeSafe记录分开。未修改运行代码、题义、阈值或默认Skill；无需重复工程回归。

E②的原NexusDock启动调用真实执行，本次没有执行前安全屏蔽。官方Jev完成1次请求，实际返回model=jev-1.13.0、provider=TypeSafe；6个判断均通过本地返回合同。记录耗时0.282356787秒，input_tokens=4907、output_tokens=295，cost_usd=null（费用未知，不计免费）。这已是有效推理返回，不只是鉴权或空请求。

EDSP适用性为0.68，未达到既定0.8方法提交阈值。局部覆盖成立，原有method-only有限回答出口启动；没有把未决方法伪称已提交。

下游当前Codex两次CLI调用均返回：组织约25.975秒，执行约143.924秒，请求gpt-6-sol/xhigh，实际服务端型号未单独核验。组织结果的goal为M0、scope为repo，语义信息不足；执行正文只有`v2`，source_ids为[`repo`]，实际可引用文档只有m0。适配器因此在转换引用时抛KeyError: repo，没有提交执行回执或进入最终接收。正文也不是有效任务回答，不能只改引用ID后宣布通过。原始prompt/schema/reply/outcome全部保留，不由作者补写答案。

这是宿主输出/消费失败，不是TypeSafe Key无效，不是Jev接口不可达，也不是这6个判断的准确率结论。方法与局部输出的综合效果仍未完成验收。

## 已保留与未完成

E⓪的原3次宿主结果直接复用，没有重跑；旧官方及OpenRouter共57份文件摘要未变。新F无任何intent；F⓪启动工具尝试返回连接错误后，核对确无执行记录，F⓪/F②均未运行。没有新CPA/OpenRouter调用，没有匿名逐维评阅。

本周期已使用1/8次Jev预算；原E②失败不自动重试。没有未知物理供应商或CLI请求，Episode保留未消费的本地宿主handoff；不得把它当作新的模型请求重发理由。代码与渠道配置已分清：官方渠道恢复成功，完整E②测试失败于宿主占位正文与非法来源引用。

## 下一断点

先诊断宿主为什么返回占位内容以及接口为何只在normalize时才发现非法source_id，保留现存请求/返回。任何修复需要按本单周期规则做有界技术处置，不把repo自动改成m0，不改写冻结或用旧好答案替换本次输出。未决F不据此记通过，#211仍NOT QUALIFIED；main/defaultSkill未变。

证据：同目录RESULT.json、E-evidence.tar.gz及其逐文件摘要；PLAN.md与E/F-freeze.json为先于推理的记录。归档不含密钥或隐藏推理流。
