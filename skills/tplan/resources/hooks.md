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

## Anti-Spiral Runtime Gate

`anti_spiral_audit` is a runtime gate, not a standalone Mindthus skill. It exists so a
Mission can activate the Anti-Spiral Self-Audit without relying on the agent to notice
its own loop.

Do not run it on a fixed step-count interval by default. Trigger it when observable
signals show that local repair may be replacing Mission progress:

- the same file, parameter, prompt segment, task node, or local object is touched for
  the third time
- user feedback reports that the result is not good enough, should be tried again, or
  got worse
- the next proposed mutation adds a new function, file, phase, fallback, rule set, or
  special-case branch
- a same-path continuation has weak, unclear, or no expected evidence delta

The gate asks five observable questions:

1. Did the last move add a structural layer?
2. Is this the third or later touch of the same local object?
3. Is the quality signal probabilistic or subjective?
4. Is the next repair aimed at downstream output instead of the upstream cause?
5. If the last move were deleted, would the system lose little or become clearer?

Gate result:

- `green`: zero or one `yes`; continuation is allowed.
- `yellow`: two `yes`; next action must be subtraction or equal replacement.
- `red`: three or more `yes`, or Q3 is `yes`; brake, restate the root problem, return
  to the nearest stable state, and allow only modification of existing structure or
  deletion.

Anti-Spiral evidence should point to step logs, object touch counts, feedback events,
diff summaries, or mechanical checks. Scripts may validate the shape of the audit and
count observable traces. They must not decide whether the root cause is true.

## Linear Continuation Gate

Elapsed time is not the root criterion for stopping or continuing. A long path may be
correct when it is the unique blocker and still has positive marginal Mission ROI. A
short path may already be wasteful when it is one of many options and the next action
will not produce new evidence.

High-impact recommendations must include `path_assessment`. This includes selection,
subtraction, loopback, chain-role, active-task switches, Mission closure, escalation,
and high-impact continuation decisions:

```json
{
  "path_assessment": {
    "marginal_roi": "positive | weak | negative | unclear",
    "path_role": "unique_blocker | dominant_path | one_of_many | unclear",
    "evidence_delta": "new_evidence_expected | weak_evidence_expected | no_new_evidence_expected | unclear"
  }
}
```

Workflow validates only object shape and enum values. Agentic judgment decides whether
the current path really has positive ROI or dominant path status. Evidence links should
constrain confidence; a complete field set is not proof that continuation is correct.

If `marginal_roi` is weak, negative, or unclear, explain why switch, loopback,
subtraction, escalation, or stop is worse before continuing. If `path_role` is
`one_of_many` or `unclear`, compare alternatives. If `evidence_delta` is
`no_new_evidence_expected` or `unclear`, do not call the next action verification unless
it can produce decision-constraining evidence.

When weak evidence delta combines with repeated local edits or additive layering,
route through `anti_spiral_audit` before authorizing same-path continuation.

## Shared Risk Context Gate

Shared Risk Context carries Mission-level risk signals that can change risk-adjusted
value assessment for later decisions. It is deliberately not cross-task log sharing:
execution units do not read each other's task logs. A unit publishes a scoped signal
when a blocker, degraded shared condition, invalid evidence risk, abnormal cost, or
recovery result can affect other units.

Risk context is recorded through `risk_context_update` and `risk_context_recovery`
evidence events, with live state in `mission.shared_context.risk_signals`.

When a high-impact hook output is produced while active shared risks exist, include:

```json
{
  "risk_assessment": {
    "shared_context_used": ["R1"],
    "invalid_evidence_risk": "low | medium | high | unclear",
    "failure_risk": "low | medium | high | unclear",
    "risk_adjusted_value": "positive | weak | negative | unclear",
    "next_gate": "continue | health_check | switch | stop | escalate"
  }
}
```

Workflow validates only object shape and enum values. Agentic judgment decides whether
the shared signal applies to the active decision, how much it changes risk-adjusted
value, and whether the next gate is continuation, health check, switch, stop, or
escalation.

If a decision ignores active shared risks, its rationale should explain why the risk is
out of scope, or set `risk_adjusted_value` to `unclear`.

## Alignment And Mission Review Gates

Adaptive runtime levels reduce packet frequency, not risk sensitivity. In any runtime
level, high-impact changes still require alignment or review before mutation.

Ordinary SubTask and Step hooks are parent-relative. Before a hook output can justify
an ordinary child mutation, it must state:

- `parent_alignment`: how the recommendation advances the parent node.
- `mission_trace`: the lightweight path from child -> parent -> Mission evidence.

Use three decision handling levels:

- `inline alignment`: ordinary Step/SubTask choices with a short `parent_alignment`
  note and lightweight `mission_trace`.
- `light packet`: subpath switch, blocker, repeated failed attempt, or meaningful
  uncertainty that may affect the parent node.
- `full mission review`: high-impact Mission-facing choices that can materially affect
  convergence or authority.

High-impact hooks remain Mission-relative. Use `mission_alignment` when the decision
materially affects Mission convergence. The `full mission review` path uses the full
gate:

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
