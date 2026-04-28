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
| `mission_intake` | new Mission | `3l5s` | initial level-2 Plan Tasks and acceptance coverage |
| `addition` | new work or missing dependency appears | `3l5s` | whether to add a task and where to attach it |
| `subtraction` | low value, resource pressure, repeated local expansion | `sela` | prune, downgrade, pause, abandon, or continue |
| `chain_role` | low immediate value but possible path dependency | `wae` | evidence-linked chain-role claim with confidence cap |
| `selection` | multiple candidate Plan Tasks exist | `sela` | next active task or escalation |
| `loopback` | feedback contradicts current definition | `3l5s` | return to Discovery, Definition, or Resolution |
| `depth_audit` | bounded artifact looks complete but shallow | `tvg` | deepen, accept, or escalate |

Hook output must include recommendation, rationale, confidence, evidence links, proposed
mutations, and requires_human.

Scripts may validate hook output shape. They must not validate semantic correctness.
