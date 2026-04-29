# tplan Decision Hooks

Decision hooks standardize how `tplan` asks other Mindthus skills for semantic judgment.

Each hook defines:

- `trigger`
- `question`
- `primary_skill`
- `support_skill`
- `required_inputs`
- `expected_output`
- `mutation_rule`

Initial hooks:

| Hook | Trigger | Primary skill | Expected decision |
| --- | --- | --- | --- |
| `mission_intake` | new Mission | `3l5s` | initial Task nodes and acceptance coverage |
| `addition` | new work or missing dependency appears | `3l5s` | whether to add a task and where to attach it |
| `subtraction` | low value, resource pressure, repeated local expansion | `sela` | prune, downgrade, pause, abandon, or continue |
| `chain_role` | low immediate value but possible path dependency | `wae` | evidence-linked chain-role claim with confidence cap |
| `selection` | multiple candidate runtime nodes exist | `sela` | next active node or escalation |
| `loopback` | feedback contradicts current definition | `3l5s` | return to Discovery, Definition, or Resolution |
| `depth_audit` | bounded artifact looks complete but shallow | `tvg` | deepen, accept, or escalate |

Hook output must include recommendation, rationale, confidence, evidence links,
proposed mutations, and requires_human.

## Alignment And Mission Review Gates

Ordinary SubTask and Step hooks are parent-relative. Before a hook output can justify
an ordinary child mutation, it must state:

- `parent_alignment`: how the recommendation advances the parent node.
- `mission_trace`: the lightweight path from child -> parent -> Mission evidence.

High-impact hooks remain Mission-relative. Use `mission_alignment` when the decision
materially affects Mission convergence.

High-impact decisions use the full gate:

- `mission_review.objective_alignment`: how the decision relates to the current Mission
  objective.
- `mission_review.acceptance_gap`: which acceptance evidence is satisfied, still
  missing, protected, or intentionally deferred.
- `mission_review.task_contribution`: how the affected task contributes to Mission
  convergence.
- `mission_review.roi_effect`: one of `advance`, `protect`, `reduce_waste`,
  `defer_uncertain`, or `escalate`.
- `mission_review.non_action_risk`: what Mission risk increases if the decision is not
  taken.

High-impact decisions include adding or removing success-critical tasks, changing the
active task, closing the Mission, making subtraction decisions after resource pressure
changes, looping back because the problem definition is challenged, or expanding the
same supporting/exploratory branch more than once.

Scripts may validate hook output shape. They must not validate semantic correctness.
