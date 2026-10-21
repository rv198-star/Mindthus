# H1-C2 independent review: REVISE at 636a2e2

## Core / historical review status

Independent read-only session: `acps_6db8078d74195cc673b8bb43`.
Reviewed frozen HEAD: `636a2e24e6c7e76249ea6a18ec69f20cd66d7f53`.
Conclusion forwarded by Owner: **REVISE**. This conclusion is retained; subsequent
fixes and green tests do not turn it into an independent approval.

The current tools cannot open another session transcript, and no copy was found
in this worktree. The following are the Owner-forwarded findings verbatim, not a
claim to have retrieved the complete original report.

## Evidence / Owner-forwarded findings (verbatim)

> P1：Mission-close 只验证 B completion，却没有按当前 Owner adopt 的 A 候选重核其合格验收。反例：基于 A-v1 完成 B，A-v1 后来发生符合version绑定的 acceptance_failed，晚到 A-v2 合格验收可能按同 AC 掩盖v1失败（反之仅v2失败可误伤v1）。现 _source_failure(v1) 正确拒绝，但 _mission_completion_findings 会得出无错。应让受控 H1源的 Mission-close 采用当前 adoption 的候选+SHA/attempt的合格验收语义，与 H1 claim/adoption 一致；修复时不让无关C受影响、不更改非H1关闭语义。请先编写两个正反 RED用例，修复并测试。

> P2：H1新 task.complete 增加 prepared_evidence_events 时计算 prospective evidence_bytes 只用于 free-space估算，未限制 MAX_ARTIFACT=4MiB；旧 _load 对超限证据会拒绝，使已committed命令之后重放、查询及 Q2 recover受阻。独立纯内存探针提交前 evidence 4,193,954 B 加后4,195,122 B >4,194,304仍committed。请添加硬上限 evidence_bytes <= MAX_ARTIFACT 的提交前检查，测试越界时 mission/evidence/nonce/command记录全保持不变；不清理用户数据。

## Mainline / bounded remediation contract

1. Reproduce both source-version directions after legitimate synthetic B completion:
   adopted v1 failed plus late accepted v2 must block close; only v2 failed must not
   invalidate still-qualified adopted v1. Verify actual original Mission-close,
   current source projection, and independent C behavior.
2. Share the existing source-version acceptance projection between adoption/claim
   and Mission-close. Close reads its supplied evidence snapshot and current
   adoption, preserving SHA/attempt, inherited coverage and conservative failure
   semantics. Other candidates and unrelated C must not replace that projection;
   non-H1 closure keeps its existing AC semantics.
3. Reject prospective H1 evidence larger than `MAX_ARTIFACT` before preparing any
   transaction. Check unchanged Mission/evidence/trace, nonces and command results;
   do not delete or trim data. This is the existing 4 MiB reader limit, not a new
   retention policy or storage subsystem.
4. Record RED before runtime changes, then run directed H1 and affected native
   acceptance/closure, Q1/Q2, persistence/provenance and packaging regressions. The
   unchanged full-repository suite is not repeated merely to increase test counts.

## Boundary / review handoff

Only the original Mindthus worktree and branch are changed. No AIWork/workbench
or production operation, installed Skill edit, real Mission, credential change,
merge or release. Host `_trust_config()` stays None; #124 HOLD. New frozen source
and verification will be linked from the result document and Draft PR #243.
Independent re-review remains pending.

Freeze probe: this is a recorded REVISE finding and bounded regression contract;
it authorizes the already-approved repair, not live Host enablement or PR merge.

## Runtime support / pre-fix reproduction

`python3.12 -m unittest` on the three new directed completion tests ran 3 tests,
all 3 failed on the unchanged reviewed runtime. P1 reproduced both the hidden v1
failure and false v1 rejection; P2 reproduced a committed completion with evidence
already at `MAX_ARTIFACT - 1` before adding the acceptance event. Full tracebacks
are retained in [the RED log](../evidence/h1c2-review-red.log). These are temporary
synthetic Missions only. This review record, fixtures and RED log are committed
before runtime source changes.
