# Issue Draft: Use Read-only SubAgents To Accelerate tplan Discovery

## Title

Use read-only SubAgents to accelerate tplan discovery

## Context

`tplan` can benefit from parallel work, but SubAgents introduce real control risks if
they are allowed to mutate files, Mission state, task trees, evidence, decisions, or
external systems.

A full SubAgent mode switch such as `off / suggest / auto` would add user-facing
complexity. The better direction is simpler:

```text
SubAgent may be used by default for read-only parallel investigation.
All writing, decisions, evidence recording, and Mission state updates remain owned by the main agent.
```

This keeps user mental overhead near zero while still allowing `tplan` to gain speed
when several independent discovery tasks can run in parallel.

## Core Principle

SubAgents are scouts, not controllers.

They may produce candidate findings. The main agent must verify, merge, decide, and
write any runtime state.

```text
SubAgent = read-only investigation
Main agent = judgment, merge, evidence, mutation, user-facing conclusion
tplan = Mission state, evidence boundary, decision authority
```

## Target

Add a `tplan` guardrail for read-only SubAgent acceleration.

This should let `tplan` use SubAgents when there are independent, low-risk investigation
branches, without introducing a user-facing mode switch or weakening `tplan` authority.

## Allowed SubAgent Work

SubAgents may:

- read files
- search code or docs
- inspect release packages
- compare candidate options
- collect candidate evidence
- perform read-only review
- summarize observations for the main agent

## Forbidden SubAgent Work

SubAgents must not:

- edit files
- write `mission.json`
- write `evidence.jsonl`
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
- the work requires writing, deletion, decision mutation, or external side effects
- the real problem is still undefined enough that parallel search would amplify confusion

## Runtime Handling

SubAgent outputs should be treated as candidate findings, not evidence by default.

The main agent should:

1. receive SubAgent summaries
2. check for contradictions or missing context
3. decide what matters for the active Mission
4. record only verified acceptance, blocker, feedback, decision, state transition, or key finding evidence
5. update `tplan` runtime state itself if needed

## Non-Goals

- Do not add a user-facing `off / suggest / auto` mode switch.
- Do not let SubAgents mutate `tplan` runtime state.
- Do not treat SubAgent summaries as evidence without main-agent verification.
- Do not use SubAgents for ordinary short tasks where dispatch cost exceeds benefit.
- Do not weaken human-in-loop, decision hook, alignment, or graceful stop rules.

## Acceptance Criteria

- `tplan` docs define read-only SubAgent acceleration as a guardrail, not a user-facing mode.
- Docs state that SubAgents may only perform read-only investigation.
- Docs state that all writes, evidence records, task mutations, decisions, and final
  conclusions remain with the main agent.
- Trigger and non-trigger conditions are documented.
- Tests or pressure scenarios cover parallel read-only investigation and reject mutation
  by SubAgents.
- Existing adaptive runtime and user-facing output behavior remains intact.
