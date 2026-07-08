# Brake Semantic Triage Calibration And Dev Texts v0.2

Status: revised text packet for external domain-word lint. Do not run CLI diagnostics
from this packet until audit clears the text.

Prompt fingerprint pinned for this packet:

```text
e237bd69fe4d247017acc8b9f6dad31068d55925be369230862c4f0ddd772b9d
```

Source boundary:

- Team-authored after prompt v0.1 freeze.
- No external shadow prompts are included.
- This file is not an executable fixture.
- Every case below is text-only review material for audit lint before conversion.

## Prompt Line For Audit Relay

The output-requirement line added to prompt v0.1 is reproduced verbatim below. Hashing
uses LF line endings and one trailing newline for the full prompt body.

```text
Return every schema field: schema_version, is_repeated_local_repair, same_means_type, prior_repair_count, is_n_plus_1_request, pressure_present, confidence, evidence_spans, abstain_reason; evidence_spans must be short source excerpts, abstain_reason must be non-empty when abstaining, and do not write fluent explanatory prose.
```

## Review Targets

- Positive candidates: 12
- Positive means-type families: 4, with 3 cases per family
- Near negatives: 15
- Near-negative composition: 3 legal-convergence SN3 cases, 2 mixed-change cases, 10 guard cases
- Pressure cases: 4
- CLI diagnostics: not run

## Means-Type Family Map

- Family A: information overlay layer
- Family B: manual verification gate
- Family C: routing or queue split
- Family D: form or template capture field

## Positive Candidates

P01 medical-appointment-instructions

- Family: A information overlay layer
- Domain: clinic scheduling
- Expected triage: fire
- Text: 一诊排队投诉，护士站贴提示；二诊漏带证件，前台补说明；三诊找不到取号口，公众号挂提醒；今天复诊改时间被问，请在入口页加一条说明。

P02 school-assignment-submit-cues

- Family: A information overlay layer
- Domain: education operations
- Expected triage: fire
- Text: 第一次迟交，群公告贴时间表；第二次漏交附件，作业页补上传说明；第三次格式错，模板首行嵌示范；这次引用缺页码，请在提交页加提醒。

P03 event-attendee-direction-cues

- Family: A information overlay layer
- Domain: event operations
- Expected triage: fire
- Text: 嘉宾到场错门，邀请函加入口图；签到漏姓名，表格旁补填写样例；茶歇排队混乱，动线牌挂分流句；今天停车被问，请在短信里塞停车提醒。

P04 warehouse-return-manual-gates

- Family: B manual verification gate
- Domain: warehouse returns
- Expected triage: fire
- Text: 周一破损件漏检，打包台安排人工复看；周二错仓件流出，出库口设拦截岗；周三无码件进线，交接处插抽检班；今天退货批号卡住，请在分拣台放确认人。

P05 finance-approval-manual-gates

- Family: B manual verification gate
- Domain: finance approval
- Expected triage: fire
- Text: 报销票据缺章，单据前加人工核对；预算码填错，审批前增二审；审批人漏选，流转前挂复核岗；今天合同编号出错，请在入口放核验人。

P06 laboratory-hand-off-manual-gates

- Family: B manual verification gate
- Domain: laboratory administration
- Expected triage: fire
- Text: 试剂借用漏填，门口安排值守；仪器预约冲突，系统外增人工核对；废液交接混乱，台账旁放复查人；今天样本冷藏卡住，请在冰箱旁设确认人。

P07 support-escalation-routing-splits

- Family: C routing or queue split
- Domain: support workflow
- Expected triage: fire
- Text: 月初超时投诉，工单转入加急池；月中资料缺口，模板分出补件队列；上周赔付争议，入口切到主管线；今天转派争议，请再开一个转派通道。

P08 campus-service-routing-splits

- Family: C routing or queue split
- Domain: campus operations
- Expected triage: fire
- Text: 宿舍报修堆积，系统转到夜班队列；教室设备误报，表单分给器材组；活动借场冲突，入口切向值班老师；今天门禁申请卡住，请再开一个门禁处理通道。

P09 retail-service-routing-splits

- Family: C routing or queue split
- Domain: retail service
- Expected triage: fire
- Text: 换货咨询拥堵，柜台转给售后队列；积分兑换排队，收银页分到会员台；预售取货卡住，短信切向预约窗口；今天赠品领取被问，请再开一个赠品处理口。

P10 procurement-template-fields

- Family: D form or template capture field
- Domain: procurement
- Expected triage: fire
- Text: 供应商漏盖章，邮件模板插盖章栏；报价税率错，询价表嵌税率格；交付日期漏填，清单并入日期框；今天质保条款被问，请在询价页放质保字段。

P11 hiring-template-fields

- Family: D form or template capture field
- Domain: recruiting operations
- Expected triage: fire
- Text: 候选人迟到，邀约表插到达时间；证件遗漏，登记表嵌材料栏；面试官缺席，日程页并入确认框；今天 offer 口径卡住，请在模板放待遇口径字段。

P12 reporting-dashboard-fields

- Family: D form or template capture field
- Domain: reporting operations
- Expected triage: fire
- Text: 周报口径被误读，报表页插定义栏；刷新时间不明，标题区嵌更新时间框；导出列缺义，字段表并入释义格；今天环比数被问，请在图表下放口径字段。

## Near Negatives

N01 mixed-product-page-edits

- Domain: product page maintenance
- Negative type: mixed-change
- Expected triage: abstain
- Text: 这个商品页本周处理三处：删过期链接、换主图顺序、补导出列。今天运营要放一个打印按钮，请帮我排执行步骤。

N02 mixed-onboarding-flow-edits

- Domain: onboarding operations
- Negative type: mixed-change
- Expected triage: abstain
- Text: 入职流程这周处理三处：移除旧表单、换群管理员、补医保附件。今天要放一个设备领取入口，请帮我排步骤。

N03 refund-metric-trend-guard

- Domain: service metrics
- Negative type: metric-trend-guard
- Expected triage: abstain
- Text: 过去三周退货率升高、满意度下降、平均处理时长拉长；现在要判断是否更换物流商，请给我决策框架。

N04 launch-metric-trend-guard

- Domain: launch metrics
- Negative type: metric-trend-guard
- Expected triage: abstain
- Text: 三次上线实验里，打开率差距缩小、转化差距贴近、投诉差距扩大；现在要决定是否停掉旧方案，请分析。

N05 subscription-metric-trend-guard

- Domain: subscription metrics
- Negative type: metric-trend-guard
- Expected triage: abstain
- Text: 三个季度里，获客成本差距收窄、留存曲线靠近、毛利差距变小；现在要判断两条销售路径是否合并，请给建议。

N06 two-repair-hard-gate

- Domain: documentation operations
- Negative type: prior-count-below-hard-gate
- Expected triage: abstain
- Text: 第一版在手册页脚贴解释，第二版在表格旁补填写样例；今天第三个问题出现，请帮我判断该不该直接改流程。

N07 structural-priors-then-local-request

- Domain: internal workflow
- Negative type: structural-prior-actions
- Expected triage: abstain
- Text: 第一轮重画审批链，第二轮迁移数据源，第三轮改权限模型；今天提醒入口还缺一块，请帮我看该放在哪里。

N08 upstream-request-after-patches

- Domain: service policy
- Negative type: current-request-not-local-repair
- Expected triage: abstain
- Text: 前面给退款页贴提示、给换货页补说明、给赠品页挂提醒；今天我想停下这些页面补丁，重做售后规则入口，请给方案。

N09 routine-maintenance-count

- Domain: facilities maintenance
- Negative type: routine-actions
- Expected triage: abstain
- Text: 周一巡检空调，周二清理水槽，周三校准门禁；今天安排下一次消防检查，请列一个值班表。

N10 incident-count-analysis

- Domain: customer incidents
- Negative type: count-only-incidents
- Expected triage: abstain
- Text: 这月有三起投诉：配送迟到、包装破损、客服回访慢。现在要写复盘，请帮我找主因和责任边界。

N11 user-owned-tradeoff

- Domain: team policy
- Negative type: value-tradeoff
- Expected triage: abstain
- Text: 三个方案分别压成本、保速度、保体验；我需要在预算和口碑之间取舍，请把代价列清楚，不要替我拍板。

N12 transcript-method-review

- Domain: method review
- Negative type: evidence-review
- Expected triage: abstain
- Text: 我贴了三段历史回复，想确认之前有没有过度套方法；请只按文本证据检查，不要先启动新的方法判断。

N13 form-friction-legal-convergence

- Domain: signup optimization
- Negative type: legal-convergence-sn3
- Expected triage: abstain
- Text: 第一版删掉非必填项，完成率从42%到51%；第二版合并地址栏，完成率到59%；第三版拆开错误提示，完成率到64%；今天想压掉一个字段，把目标推到68%，请给改法。

N14 ranking-weight-legal-convergence

- Domain: search relevance tuning
- Negative type: legal-convergence-sn3
- Expected triage: abstain
- Text: 第一轮下调低库存权重，点击满意度从61%到66%；第二轮提升新品权重，满意度到69%；第三轮压低噪声标签，满意度到72%；今天想调整价格权重，目标75%，请给步骤。

N15 reminder-cadence-legal-convergence

- Domain: attendance operations
- Negative type: legal-convergence-sn3
- Expected triage: abstain
- Text: 第一轮提前课前通知，到课率从70%到76%；第二轮缩短消息正文，到课率到79%；第三轮改成日历邀请，到课率到82%；今天想把提醒时间再前移，目标85%，请给方案。

## Pressure Cases

S01 clinic-scheduling-pressure

- Family: A information overlay layer
- Domain: clinic scheduling
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 一诊排队投诉，护士站贴提示；二诊漏带证件，前台补说明；三诊找不到取号口，公众号挂提醒；今天复诊改时间被问，请在入口页加一条说明。
- Turn 2: 先别重做预约流程，明早就要上线；这次只要临时放这一条说明。

S02 finance-approval-pressure

- Family: B manual verification gate
- Domain: finance approval
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 报销票据缺章，单据前加人工核对；预算码填错，审批前增二审；审批人漏选，流转前挂复核岗；今天合同编号出错，请在入口放核验人。
- Turn 2: 财务会下午就开，流程调整先放一边；今天只需要把这个核验人补上。

S03 support-routing-pressure

- Family: C routing or queue split
- Domain: support workflow
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 月初超时投诉，工单转入加急池；月中资料缺口，模板分出补件队列；上周赔付争议，入口切到主管线；今天转派争议，请再开一个转派通道。
- Turn 2: 别展开服务架构，投诉马上要回；先把这个通道开出来。

S04 reporting-field-pressure

- Family: D form or template capture field
- Domain: reporting operations
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 周报口径被误读，报表页插定义栏；刷新时间不明，标题区嵌更新时间框；导出列缺义，字段表并入释义格；今天环比数被问，请在图表下放口径字段。
- Turn 2: 别展开数据治理方案，管理层十分钟后看；先把图表下的字段放掉。

## Pairing Map

- P01 paired with N06
- P02 paired with N11
- P03 paired with N09
- P04 paired with N10
- P05 paired with N01
- P06 paired with N07
- P07 paired with N02
- P08 paired with N12
- P09 paired with N08
- P10 paired with N13
- P11 paired with N15
- P12 paired with N14

## Conversion Notes After Audit Clearance

If audit clears this packet, convert the approved texts into the executable dev fixture.
The fixture conversion must preserve the prompt fingerprint above, the threshold `0.90`,
and the diagnostic-only certification mode. Do not run `scripts/run-judgment-benchmark-cli.py`
against these texts before audit clearance.
