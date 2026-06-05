# tplan Read-only SubAgent Acceleration

## Core

SubAgents are scouts, not controllers.

They may accelerate discovery by investigating independent branches in parallel. They
must not own Mission state, task mutations, evidence recording, decisions, or final
user-facing conclusions.

SubAgent outputs are candidate findings. The main agent must verify, merge, decide,
and write any tplan runtime state.

## Allowed Read-only Work

SubAgents may:

- read files
- search code or docs
- inspect release packages
- compare candidate options
- collect candidate evidence
- perform read-only review
- summarize observations for the main agent

## Forbidden Work

SubAgents must not:

- edit files
- write mission.json
- write evidence.jsonl
- create, close, switch, or mutate Task/SubTask/Step nodes
- apply decisions
- delete, move, rename, or overwrite content
- call external systems with side effects
- make final user-facing conclusions on behalf of the main agent

## Trigger Conditions

Use read-only SubAgents when all are true:

- there are 2 or more independent investigation branches
- the branches are read-only or safely inspectable
- each branch has a clear output shape
- results can be merged by the main agent
- expected discovery speedup is larger than coordination cost

Do not use SubAgents when:

- the task is short enough that dispatch overhead dominates
- investigation depends on shared mutable state
- work requires writing, deletion, decision mutation, or external side effects
- the problem is still undefined enough that parallel search would amplify confusion

## Runtime Handling

SubAgent summaries are not evidence by default.

The main agent should:

1. receive SubAgent summaries
2. check for contradictions or missing context
3. decide what matters for the active Mission
4. record only verified acceptance, blocker, feedback, decision, state transition, or key finding evidence
5. update tplan runtime state itself if needed

The main agent records only verified evidence. Candidate findings that are useful but
not yet verified should remain in local notes, not `evidence.jsonl`.

## No User-facing Mode Switch

Do not add an `off / suggest / auto` mode switch for ordinary users.

Read-only SubAgent acceleration is a guardrail: it lets the main agent parallelize safe
investigation without changing the user's mental model. The visible rule is simply:

```text
SubAgents may investigate in parallel, but only the main agent controls tplan state.
```

## Handoff Shape

Each SubAgent should return a compact summary:

```text
Scope:
What was inspected:
Candidate findings:
Evidence candidates:
Uncertainty or conflicts:
Recommended main-agent follow-up:
```

The main agent decides whether any candidate finding becomes evidence, a blocker, a
decision input, or just a discarded note.
