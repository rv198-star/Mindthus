# Issue #246 / PR #247 第四轮独立审计：REVISE

日期：2026-11-17。审计 head：`d57d6816ebf27ca30441a68d5cd526341cee315d`；base：`520376990613eb34bfdbbdaa4fc4ba227d4fbcfb`。

## Core / 结论

**REVISE：B1 已报告的错误完成路径已修复；仍有一项 P1——修复责任只处理一层，完成后的修复任务再次修复时无法正常收口。**

源会话独立重跑 58 项协作测试、75 项证据/H1 相关测试及开发的 8 个隔离探针通过。精确 head 与远端一致，CI 全套运行 1399 项、跳过 7 项并成功。原 required C FAIL、AC 缺项、后续 FAIL、其他任务 PASS 的拒绝路径，以及合法本地/委派修复的公开 snapshot/survey 续接视图已核对。

新增两个正向闭环复现表明：T3 修复完成后，发现新缺陷并按原合同创建 T4；T4 合法完成后，最初的 T1→T3 责任仍永久指向已失效的 D3。A 因此会重复看到旧差距，无法依据已完成的合法继任收口。

## Mainline / C1 — P1：连续修复缺少验收责任继任投影

位置：`skills/tplan/scripts/collaboration.py:1340` 的 `_repair_obligation_satisfied` 与 `:1364` 的 `_task_acceptance_findings`。

两例共同的完整路径：

1. T1 的 D1/h1 审查与验收通过，T1 completed。
2. A 处置阻断性反馈，创建 T3，建立 T1→T3 的 A1 修复义务并保留 h1 的失效历史。
3. T3 的 D3/h3 获得 C PASS、新的 T3/A1 合格验收，T3 completed。
4. T3 出现新缺陷；A 按同一 `repair` 合同创建 T4，建立 T3→T4 的 A1 义务，D3/h3 标为 invalidated。
5. T4 完成。`completed_repair_has_valid_local_successor` 使用合法本地修复及新的 T4/A1 通过；`completed_repair_has_valid_delegated_successor` 另有 D4/h4 当前采用和 C PASS。

两例最终 T1、T3、T4 都 completed，成功关键任务与当前 T4 验收均满足，Mission 关闭仍报 `repair obligation ... (task T3) requires fresh acceptance/re-review`；resume 也保留 T3 的旧差距。拒绝未产生部分写入，原始结果见 [probe-results.jsonl](reviews/r4-audit/probe-results.jsonl)。

根因：最初义务只检查 T3 的直接委派。D3 因下一次合法 repair 失效后，这个检查固定返回 false，未沿已存在的 T3→T4 责任继续投影。`_task_acceptance_findings` 同时有 incoming/outgoing 时先返回 incoming，也没有把二者接起来。与最初 T1 可以通过修复任务承接责任相比，T3 作为修复任务后失去同一承接能力。终态任务重新派工入口又要求新建有界任务，所以原合同的正常续接路径就是已经建立的 T4。

### 根因修复合同

把既有 `repair_obligations` 纳入统一的当前责任连续投影：**一项修复再次被明确交给合法继任时，验收责任按所承接的 AC 继续传递；当前有效末端满足其全部验收与审查后，覆盖相应上游责任。** 保留原任务 completed 历史、失效采用和反馈记录。

- 沿显式责任关系与声明 AC 承接，不以任意下游 PASS 或任意已完成任务抵消上游缺口。未覆盖的 AC 继续开放。
- 当前末端继续使用 R4 的合格性、唯一引用、最新逐项观察、当前采用和 mandatory review 规则。下游 FAIL、缺审查、缺 AC 或尚未完成时，上游保持未满足；旧中间成果的 PASS 不替代末端验收。
- Mission 收口与 snapshot/survey resume 共用这一投影，Task 路径保持相同责任。合法修复完成后，历史 invalidated 记录保持历史身份，不再制造一个只能靠改写历史才能消除的缺口。
- 一批补足连续两层及更深一层的本地/委派正向收口，并覆盖 AC 部分承接、末端 FAIL/缺审查/未完成、无关分支 PASS 的拒绝。保持本轮 B1 的负向与正向测试。

这是已有责任连续性的主规则修复。复用当前函数和已存在的责任边，不引入第二套验收状态或调度系统。开发自主选择等价实现与测试组织。

## Runtime support / 证据与验证

- [独立验证记录](reviews/r4-audit/verification.txt)：58 + 75 项；原 8 个探针复跑的 [原始输出](reviews/r4-audit/r4-probe-rerun.jsonl)。
- 新增独立 [复现脚本](reviews/r4-audit/reproduce.py) 与 [结果](reviews/r4-audit/probe-results.jsonl)。每例在临时目录建立 Mission，使用正常协作/验收入口完成上述路径，然后清理；不修改实现。
- `TMPDIR=/private/tmp python3.11 -B docs/internal/tplan-collaboration/reviews/r4-audit/reproduce.py`。
- 原 R3 反例前两条复跑已被正确拒绝。其历史正向 helper 直接调用 `build_resume_view(state)` 且未传 events；这不作为 R4 公开查询缺陷。本轮公开 snapshot/survey 接收事件，已通过正向核对。

## Boundary / 完整返修与后续验收

开发按 C1 根因完成一个批次、自测、自审，再回传精确 head。已验收的六项源 Agent 受控目标保持行为记录继续保留；本轮新增证据类别为机械运行时探针。

真实三会话宿主 E2E、peer 来源/唤醒/重投去重/取消可观测性及 A→A writer 隔离仍沿原清单验收。PR 保持 draft，Issue 开放，合并/发布/部署及安装/生产权限沿原合同。

冻结前定位：目标是 A 在多轮反馈和返修后依据当前真实差距推进。当前产物是固定代码版本的独立审计；下一步是修复连续验收责任的完整正向与失败路径，保留 R4 末端资格判定。
