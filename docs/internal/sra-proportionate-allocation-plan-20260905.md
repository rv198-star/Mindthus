# SRA proportionate allocation implementation plan

Baseline: `eeb7e5c7225d9600f07632cd9254f25d26db8628`
Authorization: maintainer approved final risk review, detailed planning and implementation on 2026-09-05.
Risk review: `audits/2026-09-05-sra-goal-risk-review.md`.
Parent discussion: #183. Existing implementation owners: #185 and #186.

## Product goal

以足够低的判断成本，先保护目标成立所必需的投入，再把下一份资源分给当前风险调整后边际价值最高的用途。Lite 与 Full 共享这一逻辑，仅支付当前决策值得支付的分析成本。

“先生存、再图强” protects the declared objective and non-negotiable constraints; it does not reduce the objective to bare survival, equate value with a convenient KPI, or rank people. Long-horizon, qualitative, maintenance, learning, care and option value remain eligible. Unknown benefit is not zero. Necessary work receives sufficient support, not unlimited investment.

## Bounded sequence

| Slice | Deliverable | Acceptance |
|---|---|---|
| G0 | Goal/mainline and final risk corrections | Three-step mainline; functional risk cases documented; no universal numeric scoring or new method |
| P1 | Version-bound proportionate calibration | Structural Full can be single only after an explicit ordinary/reversible assessment; uncertain/high-stakes/contaminated cases remain dual; coverage and authority unchanged; legacy runs keep prior selection |
| P2 (#185) | Draft intake and checked decision card | One canonical input; deterministic defaults only; unknown semantics stay incomplete; short card shows objective, protected boundaries, quantities/windows/ceilings, stop/start and review conditions |
| P3 (#186) | Completion-only references and precise conflict diagnostics | References bind a sourced, task-appropriate immutable criterion; raw prose remains conservative; real conflicts still reconcile; no broad semantic equivalence engine |
| P4 | Explicit re-ranking draft | New run identity and refreshed decision context; parent hash reference only; no old judgments, permissions or satisfied dependencies inherited; parent unchanged |
| Exit | Adversarial self-review and current-tree validation | Existing regressions + focused cases, full unittest, lifecycle, all package layouts, diff hygiene and remote CI |

Commit boundaries are goal/risk, the shared version-bound policy/criterion contract,
intake/card, and re-ranking/regressions. Policy and criteria touch the same packet/schema
and replay boundary, so that contract change is committed and verified together rather
than exposing a partially wired intermediate runtime. Approval covers SRA only. It does not implement #144/#184/#187, resume #112, delete benchmark artifacts, mutate TPlan, or publish a version/tag.

## Compatibility strategy

Use a named `execution_policy` extension in explicit v0.4 raw input, rather than silently changing the interpretation of old v0.3 runs. The old reader was experimentally shown to ignore unknown fields on v0.3 input; the new input version makes that reader reject new policy inputs. Both input versions share the same allocation engine. Absent extension retains v0.3 conservative mode/view selection and packet bytes. The current intake path can emit the named new policy after an explicit risk assessment. Both paths use the same validators, resource model, record/check/repair and authority boundary.

Completion references are an explicit additive, versioned input surface, validated before packet construction. Existing free-text decisions continue to use the legacy representation. New referenced decisions have one canonical criterion, not a second unbound condition string.

No Repair-based migration: changing inputs or policy creates a new prepared run. Existing journals and judgments remain immutable.

## Important limits

- Short execution time does not imply low consequence; compare analysis cost with avoidable error loss and the expected benefit of another reasoning step.
- Single-view Full does not claim independent corroboration. A missing or uncertain risk assessment cannot select the cheaper path.
- The parser/assembler is not an NLP truth classifier. Agentic intake supplies current sourced semantics; deterministic code generates boilerplate and checks the input.
- A criterion identity proves agreement on the same criterion, not that the criterion measures the real objective correctly.
- Detailed fields are retained in the checked run; the card is a read-only view, not a new authority object.
- Re-ranking is explicit, not an autonomous monitor. SRA allocation never bypasses the execution owner's approval.

## Evidence plan

Maintain separate evidence for static method contract, deterministic runtime behavior and reviewer-assessed design cases. Run ordinary Full/single, risky Full/dual, contaminated Lite/dual, unknown risk, forged downgrade, unchanged legacy replay; incomplete intake/no file mutation; all terminal card states; criterion tamper/wrong-target/changed-resource/changed-window; and re-ranking parent immutability/stale evidence/independent decisions. No claims of measured Token savings, business ROI or fresh-agent independence from these tests.
