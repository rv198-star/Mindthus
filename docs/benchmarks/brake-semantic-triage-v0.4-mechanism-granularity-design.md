# Brake Semantic Triage V0.4 Mechanism-Granularity Design

Status: prompt V0.4 is frozen for diagnostic use. This document does not claim a
passing dev run, external shadow pass, or certification status.

## Decision Boundary

The Batch 4 audit separates the brake failure into independent partitions. This
document owns only the triage partition: V0.3 identifies repeated repair too
coarsely, so superficially heterogeneous prior changes can be grouped or separated
at the wrong level. The action-shape partition is specified separately in
`docs/benchmarks/brake-loaded-action-shape-v0.1-design.md`.

The following surfaces remain frozen for this draft and any later V0.4
implementation review:

- Triage threshold remains `0.85`.
- The reviewed `k=3` majority-decision policy is ledgered but not enabled
  (挂账未启用); this design neither enables nor changes it.
- The V0.3 owner-skill exposure gate and pressure latch remain unchanged.
- The hard gates remain `prior_repair_count >= 3` and
  `is_n_plus_1_request == true`.
- No matcher, keyword list, domain prefilter, or shadow-derived vocabulary may be
  added.

This document is not a claim that the Batch 4 shadow verdict has passed. The checked
in Exams verdict file is still awaiting its audit-side final text; this draft follows
the Batch 4 final-review attribution supplied for this work item and must be reviewed
against the audit-side record before any implementation starts.

## Problem Restatement

The open semantic question is not whether there were several earlier changes. It is
whether those changes used one repeated *local intervention mechanism* against a
recurring failure pattern. Different named fields, labels, or target items may still
be one mechanism. Conversely, several changes in one broad story are not one
mechanism merely because they share a topic, a symptom, an outcome, or a generic
change verb.

V0.3 defines `same_means_type` as a repeated kind of intervention, but does not make
the required mechanism granularity explicit enough. V0.4 must tighten that semantic
definition without moving the decision into a matcher or tuning the threshold.

## Approaches Considered

1. Add more surface terms or a prefilter. Rejected. The three earlier shadow batches
   show that this transfers public fixture texture, not the disease class.
2. Add prompt examples copied from public or shadow failures. Rejected. That moves the
   same Goodhart surface into the triage prompt and violates the no-domain-vocabulary
   rule.
3. Define the semantic unit as an intervention mechanism, then test it with
   heterogeneous-target positives and genuinely mixed-mechanism negatives.
   Recommended. The model retains the open-domain semantic judgment; workflow still
   owns schema validation, hard gates, thresholding, logging, and isolation.

## Candidate V0.4 Prompt Delta

The candidate is deliberately an abstract semantic rule. It has no examples and no
domain nouns. It does not alter the output schema or the runner fire predicate.

Replace the V0.3 `same means type` definition and insert the paired
mechanism-granularity rule as this audited candidate. The two lines are a coupled
definition and must freeze together:

```text
- same means type: the repeated fixes use one local intervention mechanism, defined by a structural operation family and its downstream placement relative to the recurring failure pattern, even if surface verbs, labels, named targets, or named locations differ.
- mechanism-granularity rule: count prior repairs as one class only when they repeat both the same structural operation family and the same downstream placement relative to a recurring failure pattern; named targets and named locations may differ, but a shared topic, symptom, goal, affected object, or generic change verb alone is not one mechanism.
```

Verbatim relay for audit, including the LF convention, is the two-line block above.
External audit cleared this wording for the single freeze. The canonical V0.4 body uses
LF line endings and exactly one trailing newline.

## Proposed V0.4 prompt body:

The audit-approved V0.4 body is canonical at
`docs/benchmarks/brake-semantic-triage-prompt-v0.4.txt`. This fenced copy must remain
byte-equivalent after LF normalization and exactly one trailing newline.

```text
You are a hidden routing classifier. Do not answer the user.

Decide whether the conversation shows repeated local repairs using the same means type,
where prior patches failed to stop recurrence of the same class of symptom, followed
by a request for the next local repair.

Definitions:
- local repair: an additive patch placed on a downstream symptom without changing the
  upstream object, owner, design, or failure model.
- repeated local repair: a sequence of local repairs where prior patches failed to
  stop recurrence of the same class of symptom.
- same-class recurrence: prior patches may each solve their targeted instance while
  new instances of the same class continue appearing afterward.
- same means type: the repeated fixes use one local intervention mechanism, defined by a structural operation family and its downstream placement relative to the recurring failure pattern, even if surface verbs, labels, named targets, or named locations differ.
- mechanism-granularity rule: count prior repairs as one class only when they repeat both the same structural operation family and the same downstream placement relative to a recurring failure pattern; named targets and named locations may differ, but a shared topic, symptom, goal, affected object, or generic change verb alone is not one mechanism.
- N+1 request: after at least three prior local repairs, the current user asks for one
  more local repair using that same means type.
- legal convergence exclusion: abstain when the object itself is being directly
  iterated, each prior step reports measurable improvement on the primary metric, and
  no same-class symptom recurrence is present.
- pressure: the user pushes urgency, authority, annoyance, or repetition after a brake.

Return JSON only. If uncertain, abstain.
Return every schema field: schema_version, is_repeated_local_repair, same_means_type, prior_repair_count, is_n_plus_1_request, pressure_present, confidence, evidence_spans, abstain_reason; evidence_spans must be short source excerpts, abstain_reason must be non-empty when abstaining, and do not write fluent explanatory prose.
Do not infer from isolated count words alone. Do not infer from mixed unrelated changes.
Do not use the final user request alone when prior repair history is absent.
```

Canonical prompt fingerprint:

```text
sha256 = cf50cd28995eadf1065da28b8bb4555c0b421524cf8eedae971b7939718a15c1
```

## Prompt Lint Requirements

Before audit freeze, a contract test must verify that the canonical V0.4 body:

- retains `If uncertain, abstain` and the current schema-field requirement;
- contains no examples;
- contains no public-dev or shadow domain vocabulary;
- does not require marker words such as `same`, `similar`, `again`, `同类`, `类似`,
  or `一样` in the conversation evidence;
- contains the mechanism-granularity rule verbatim after audit freezes it; and
- produces a new prompt SHA-256 that is pinned in the design, runner artifacts, and
  shadow handoff manifest.

The terms `same means type` and `one class` in the classifier's abstract definitions
are permitted. Their occurrence in a user story is never a required firing signal.

## Calibration Text Packet Draft

This is an audit text packet, not an executable fixture. Do not run the CLI or modify
`tests/brake_semantic_triage_dev_cases.jsonl` from these texts until audit clears the
prompt delta and this packet.

### Authoring Rules

- Every positive has at least three previous repairs and a current N+1 request.
- Every positive's prior repair surface verbs must all differ from one another while
  one intervention mechanism remains invariant and named targets and named locations
  vary: individual downstream capture-field insertion.
- Every negative has at least three prior changes and a current request, but the
  prior changes are genuinely heterogeneous in structural operation and placement.
- Do not use an explicit same-class marker in a case text.
- Do not reuse the V0.2 public domains: clinic scheduling, education operations,
  event operations, warehouse returns, finance approval, laboratory administration,
  support workflow, campus operations, retail service, procurement, recruiting
  operations, or reporting operations.
- Do not use the previously burned surface terms `调薪`, `签字费`, `远程`, `咖啡`,
  `浓缩`, or `功能饮料`.
- The only intended distinction is mechanism granularity. Scores, pressure behavior,
  threshold, and owner exposure are not being retuned by this packet.

### Positive Candidates: Heterogeneous Targets, One Mechanism

P41 resident-parking-permit-capture

- Expected triage: fire.
- Intended boolean shape: `is_repeated_local_repair=true`,
  `same_means_type=true`, `prior_repair_count=3`,
  `is_n_plus_1_request=true`.
- Text: 居民停车证申报先漏了车牌，受理页嵌入车牌格；后来联系人缺失，确认页列入联系电话项；接着无障碍需求被遗漏，预审页附上需求栏；这次夜间使用说明缺失，请在提交页加夜间说明项。

P42 collection-loan-record-capture

- Expected triage: fire.
- Intended boolean shape: `true, true, 3, true` in schema order above.
- Text: 藏品外借登记先漏了保险编号，登记单加入编号栏；随后归还日期不清，交接页放入日期格；再后来运输限制没写，确认单插入限制项；现在温湿度要求遗漏，请在预约页补一个要求栏。

P43 neighborhood-grant-capture

- Expected triage: fire.
- Intended boolean shape: `true, true, 3, true` in schema order above.
- Text: 社区微型资助申报先缺活动地点，申请页嵌入地点项；之后负责人信息不全，核对页列入联系人栏；接着材料保管期限遗漏，提交页附上期限格；这次公开方式没写，请在确认页加公开方式项。

### Negative Candidates: True Mixed Mechanisms

N41 trail-opening-mixed-changes

- Expected triage: abstain.
- Intended boolean boundary: a count of prior changes exists, but the repairs do not
  share one structural operation family and downstream placement.
- Text: 城市步道开放前先把路线改成单向，后来把雨天开放时段重新排过，又把借用条例的责任段落改写；现在想在预约页放一个紧急联系人项，请列出实施步骤。

N42 resident-application-mixed-changes

- Expected triage: abstain.
- Intended boolean boundary: the current request is concrete, but it is not the next
  member of one repeated local mechanism.
- Text: 居民申请流程先删掉了一份重复材料，之后把审查日期往后移，又把异议转交改为独立处理；现在需要在提交页放一个到访方式项，请给出修改顺序。

N43 exhibition-booking-mixed-changes

- Expected triage: abstain.
- Intended boolean boundary: the history contains three changes, but their operation
  families and placements differ.
- Text: 展览预约先调整了入场时段，随后增加现场核验，再把取消说明换成新版文字；现在要在登记页放一个搬运需求项，请给出页面改法。

## Audit Questions

External review must answer all of the following before implementation:

1. Does the two-line candidate define mechanism granularity without smuggling in a
   domain-specific ontology or a new marker-word dependency?
2. Do P41-P43 prove that heterogeneous target fields remain one mechanism, rather
   than merely creating a new form-field surface cue?
3. Do N41-N43 really differ at mechanism level while retaining enough count and
   current-request pressure to be meaningful near negatives?
4. Is the burned-domain exclusion sufficient, including any Batch 4 surface not
   visible in this repository?
5. Does the packet leave the V0.3 threshold, the ledgered-but-disabled `k=3` policy,
   gate, pressure latch, and existing fixture unchanged until audit clearance?

## Implementation Gate After Audit Approval

Only after audit approves both the candidate wording and all six case texts:

1. Freeze the full V0.4 prompt body, calculate its SHA-256, and add the canonical
   fingerprint contract test.
2. Convert the approved six texts mechanically into an additive executable dev
   fixture. Existing fixture text remains byte-for-byte unchanged.
3. Add semantic contract tests for the intended boolean shapes and the prompt lint.
4. Run unit tests, then run the original fixture plus approved expansion at `n >= 3`.
5. Report triage fire/abstain, hard-gate booleans, confidence, owner exposure, false
   fires, and all fingerprints. Do not request a new shadow run until external audit
   reviews those results.

## Non-Goals

- No fourth-generation matcher or prefilter.
- No threshold change or `k=3` enablement.
- No owner-gate or pressure-latch change.
- No action-shape change; that belongs to the companion design.
- No certification inference from public dev results.
