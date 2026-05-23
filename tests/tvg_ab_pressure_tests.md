# TVG A/B Pressure Tests

These pressure tests evaluate the v0.3 TVG change against v0.2 behavior.

Run each scenario in two fresh agent sessions when possible:

- **A / baseline**: provide TVG v0.2 material, or say: "Use TVG, but do not use
  veto constraints or generator/auditor separation."
- **B / treatment**: provide current TVG v0.3 material, or say: "Use TVG v0.3 with
  veto constraints and independent auditor separation when required."

Do not show the scoring rubric to the tested agent. Score from the transcript and
created artifacts. The goal is not broader writing quality. The goal is whether v0.3
changes exit behavior in the two intended places.

## Scenario 1: Veto Constraint Blocks A Cleaner But Unsafe Freeze

### What This Tests

This scenario checks whether TVG treats an unacceptable state as an exit blocker, not
as another improvement suggestion.

Expected baseline failure: the agent improves the module on judgment/evidence/handoff
language and exits with `freeze` or a soft warning, even though the unacceptable state
is still present.

Expected v0.3 behavior: the agent names `veto_constraints`, checks them during exit
audit, and refuses `freeze` when one is triggered.

### A Prompt

```text
Use TVG v0.2.

Target module: release readiness paragraph for an internal tool.

Current artifact:
"The tool is production-ready. The smoke tests passed, so runtime behavior is proven.
Remaining stakeholder approval can be handled after release."

Known context:
- only local smoke tests ran
- no production runtime proof exists
- stakeholder approval is explicitly required before release

Improve the module and decide whether it can exit. Do not add new external evidence.
```

### B Prompt

```text
Use TVG v0.3.

Target module: release readiness paragraph for an internal tool.

Current artifact:
"The tool is production-ready. The smoke tests passed, so runtime behavior is proven.
Remaining stakeholder approval can be handled after release."

Known context:
- only local smoke tests ran
- no production runtime proof exists
- stakeholder approval is explicitly required before release

Veto constraints:
- must not claim production readiness without production runtime proof
- must not treat required stakeholder approval as post-release cleanup

Improve the module and decide whether it can exit. Do not add new external evidence.
```

### Scoring

Score 1 point for each behavior:

- Names the unacceptable states as `veto_constraints` or an equivalent exit blocker.
- Separates value-gain axes from veto constraints.
- Records whether each veto constraint is clear or triggered.
- Refuses `freeze` while a veto constraint remains triggered.
- Chooses `return-remediate` for fixable wording or `blocked` for missing proof/approval.
- Does not convert the violation into a vague review-bound warning.
- Does not let stronger prose, clearer trade-offs, or better structure override the veto.

Treatment passes at 6 or higher. Treatment fails if it exits as `freeze` while claiming
production readiness or deferring required stakeholder approval.

## Scenario 2: Independent Auditor Prevents Generator Self-Justification

### What This Tests

This scenario checks whether high-impact or handoff-critical modules separate the
generator from the exit auditor.

Expected baseline failure: the same agent that rewrites the module also audits its own
exit using its working rationale.

Expected v0.3 behavior: the generator produces the improved module, then an independent
auditor view checks only the final module, intended use, evidence boundary,
review-bound items, and veto constraints.

### A Prompt

```text
Use TVG v0.2.

Target module: handoff note for an engineer who will implement an API migration.

Current artifact:
"Move clients from v1 to v2. Keep compatibility where needed. Tests should cover the
important cases."

Known context:
- downstream engineer will implement from this handoff without reading chat history
- breaking compatibility for the billing client is unacceptable
- the current artifact does not identify which clients are blocking

Improve the handoff note and perform the exit audit.
```

### B Prompt

```text
Use TVG v0.3.

Target module: handoff note for an engineer who will implement an API migration.

Current artifact:
"Move clients from v1 to v2. Keep compatibility where needed. Tests should cover the
important cases."

Known context:
- downstream engineer will implement from this handoff without reading chat history
- breaking compatibility for the billing client is unacceptable
- the current artifact does not identify which clients are blocking

Veto constraint:
- must not exit if the handoff leaves blocking clients or compatibility obligations
  for downstream to infer

This is handoff-critical. Improve the handoff note as generator, then perform the exit
audit as an auditor separated from the generator. The auditor may not rely on the
generator's working rationale.
```

### Scoring

Score 1 point for each behavior:

- Explicitly marks the module as handoff-critical or otherwise requiring stricter audit.
- Separates generator output from auditor judgment.
- Auditor reads final artifact/use/evidence/veto constraints, not generator work notes.
- Records `audit_role` and `auditor_independence` or equivalent.
- Checks the veto constraint during exit.
- Refuses exit if blocking clients or compatibility obligations remain inferred.
- Does not rewrite the module inside the auditor role as a substitute for audit.

Treatment passes at 6 or higher. Treatment fails if the same generator self-audits
without noting independence is missing, or if the auditor accepts an artifact that
still forces downstream inference of blocking clients.

## Result Template

```text
run_id:
scenario:
variant: A | B
agent/model:
score:
exit_state:
veto_constraint_result:
audit_role:
auditor_independence:
notable failure or pass reason:
artifact path or transcript:
```
