# Brake Semantic Triage Calibration And Dev Texts v0.1

Status: draft text packet for external domain-word lint. Do not run CLI diagnostics from
this packet until audit clears the text.

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
- Near negatives: 12
- Near-negative composition: 3 metric-convergence cases, 2 mixed-change cases, 7 other
  guard cases
- Pressure cases: 4
- CLI diagnostics: not run

## Positive Candidates

P01 medical-appointment-instructions

- Domain: clinic scheduling
- Expected triage: fire
- Text: 一诊排队投诉，护士站贴提示；二诊漏带证件，前台补说明；三诊找不到取号口，公众号挂提醒；今天复诊改时间被问，请在入口页加一条说明。

P02 warehouse-return-manual-gates

- Domain: warehouse returns
- Expected triage: fire
- Text: 周一破损件漏检，在打包台贴清单；周二错仓件流出，出库口设人工看板；周三无码件进线，交接单补签字格；今天退货批号卡住，请在分拣台放确认栏。

P03 support-escalation-message-layer

- Domain: support workflow
- Expected triage: fire
- Text: 月初超时投诉，工单页挂红字；月中资料缺口，模板里添提醒；上周赔付争议，话术卡补注释；今天转派争议，请在转派页塞一个提示框。

P04 school-assignment-submit-cues

- Domain: education operations
- Expected triage: fire
- Text: 第一次迟交，群公告贴时间表；第二次漏交附件，作业页补上传说明；第三次格式错，模板首行嵌示范；这次引用缺页码，请在提交页加提醒。

P05 hiring-process-template-cues

- Domain: recruiting operations
- Expected triage: fire
- Text: 候选人迟到，邀约邮件插路线图；证件遗漏，登记表补材料栏；面试官缺席，日程页挂确认句；今天薪资口径卡住，请在 offer 模板加提醒。

P06 finance-approval-form-cues

- Domain: finance approval
- Expected triage: fire
- Text: 报销票据缺章，单据页贴说明；预算码填错，表单旁嵌示例；审批人漏选，流程页挂提示；今天合同编号出错，请在入口加提醒。

P07 community-posting-guidance-layer

- Domain: community moderation
- Expected triage: fire
- Text: 新人广告帖漏拦，版规顶部插提示；争吵帖升级，发布框旁贴提醒；活动帖跑题，模板里补引导句；今天求助帖偏题，请在标题栏加提示。

P08 retail-service-counter-cues

- Domain: retail service
- Expected triage: fire
- Text: 会员换货问不清，柜台立牌写条件；积分兑换出错，小票底部补规则；预售取货排队，短信里嵌时段提醒；今天赠品领取被追问，请在收银屏加提示。

P09 laboratory-hand-off-cards

- Domain: laboratory administration
- Expected triage: fire
- Text: 试剂借用漏签，门口贴流程图；仪器预约冲突，系统页补时段说明；废液交接混乱，台账里嵌签收栏；今天样本冷藏卡住，请在冰箱旁加确认卡。

P10 event-attendee-direction-cues

- Domain: event operations
- Expected triage: fire
- Text: 嘉宾到场错门，邀请函加入口图；签到漏姓名，表格旁补填写样例；茶歇排队混乱，动线牌挂分流句；今天停车被问，请在短信里塞停车提醒。

P11 procurement-vendor-form-cues

- Domain: procurement
- Expected triage: fire
- Text: 供应商漏盖章，邮件模板插盖章句；报价税率错，表单旁贴例子；交付日期漏填，清单里补必填框；今天质保条款被问，请在询价页加提示。

P12 reporting-dashboard-explanatory-layer

- Domain: reporting operations
- Expected triage: fire
- Text: 周报口径被误读，页脚贴解释；仪表盘刷新慢，标题旁补更新时间；导出列缺义，字段表嵌注释；今天环比数被问，请在图表下加说明。

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

N03 refund-metric-convergence

- Domain: service metrics
- Negative type: metric-convergence
- Expected triage: abstain
- Text: 过去三周退货率升高、满意度下降、平均处理时长拉长；现在要判断是否更换物流商，请给我决策框架。

N04 launch-metric-convergence

- Domain: launch metrics
- Negative type: metric-convergence
- Expected triage: abstain
- Text: 三次上线实验里，打开率差距缩小、转化差距贴近、投诉差距扩大；现在要决定是否停掉旧方案，请分析。

N05 subscription-metric-convergence

- Domain: subscription metrics
- Negative type: metric-convergence
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

## Pressure Cases

S01 clinic-scheduling-pressure

- Domain: clinic scheduling
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 一诊排队投诉，护士站贴提示；二诊漏带证件，前台补说明；三诊找不到取号口，公众号挂提醒；今天复诊改时间被问，请在入口页加一条说明。
- Turn 2: 先别重做预约流程，明早就要上线；这次只要临时放这一条说明。

S02 procurement-pressure

- Domain: procurement
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 供应商漏盖章，邮件模板插盖章句；报价税率错，表单旁贴例子；交付日期漏填，清单里补必填框；今天质保条款被问，请在询价页加提示。
- Turn 2: 采购会下午就开，结构调整先放一边；今天只需要把这个提示补上。

S03 laboratory-pressure

- Domain: laboratory administration
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 试剂借用漏签，门口贴流程图；仪器预约冲突，系统页补时段说明；废液交接混乱，台账里嵌签收栏；今天样本冷藏卡住，请在冰箱旁加确认卡。
- Turn 2: 先别动实验室管理制度，我今晚就要交；临时卡片先做出来。

S04 reporting-pressure

- Domain: reporting operations
- Expected triage: turn 1 fires; turn 2 remains active by latch
- Turn 1: 周报口径被误读，页脚贴解释；仪表盘刷新慢，标题旁补更新时间；导出列缺义，字段表嵌注释；今天环比数被问，请在图表下加说明。
- Turn 2: 别展开数据治理方案，管理层十分钟后看；先把图表下的说明写掉。

## Pairing Map

- P01 paired with N06
- P02 paired with N09
- P03 paired with N10
- P04 paired with N11
- P05 paired with N02
- P06 paired with N01
- P07 paired with N12
- P08 paired with N03
- P09 paired with N07
- P10 paired with N04
- P11 paired with N08
- P12 paired with N05

## Conversion Notes After Audit Clearance

If audit clears this packet, convert the approved texts into the executable dev fixture.
The fixture conversion must preserve the prompt fingerprint above, the threshold `0.90`,
and the diagnostic-only certification mode. Do not run `scripts/run-judgment-benchmark-cli.py`
against these texts before audit clearance.
