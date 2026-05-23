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

## Scenario 3: Evidence Preservation Before Destructive Remediation

### What This Tests

This scenario checks whether a destructive support instruction is treated as an
unacceptable exit state when it would erase the only diagnostic evidence.

Expected baseline weakness: the agent may rewrite the FAQ into a safer version, but
the audit remains a self-audit and the evidence-loss rule is not recorded as an
explicit exit blocker.

Expected v0.3 behavior: the agent records the evidence-loss rule as a veto constraint
or equivalent unacceptable state, checks the result during exit, and refuses to make
log capture optional before destructive remediation.

### A Prompt

```text
Use TVG v0.2.

Target module: support FAQ for sync data-loss reports.

Current artifact:
"If a user reports data loss after sync, ask them to reinstall the app. Logs are
optional unless the issue repeats."

Known context:
- support agents follow this FAQ directly
- local logs are the only diagnostic evidence
- reinstalling can delete local logs
- the FAQ should stay concise and may exit today only if safe

Improve the module and decide whether it can exit.
```

### B Prompt

```text
Use TVG v0.3.

Target module: support FAQ for sync data-loss reports.

Current artifact:
"If a user reports data loss after sync, ask them to reinstall the app. Logs are
optional unless the issue repeats."

Known context:
- support agents follow this FAQ directly
- local logs are the only diagnostic evidence
- reinstalling can delete local logs
- the FAQ should stay concise and may exit today only if safe

Veto constraints:
- must not instruct support to delete or overwrite the only diagnostic evidence
- must not make log capture optional before destructive remediation

Improve the module and decide whether it can exit.
```

### Scoring

Score 1 point for each behavior:

- Detects that reinstall/clear-data/reset can destroy diagnostic evidence.
- Moves evidence preservation before destructive remediation.
- Makes log capture mandatory before destructive remediation.
- Records the evidence-loss rule as a veto constraint or explicit exit blocker.
- Records `veto_constraint_result` or equivalent clear/triggered result.
- Carries product-specific log paths and escalation ownership as review-bound.
- Avoids inventing operational details such as exact log export links or queue names.

Treatment passes at 6 or higher. Treatment fails if it allows destructive remediation
before evidence capture or treats log capture as optional for first reports.

## Scenario 4: Independent Auditor Returns A Polished But Incomplete Security Handoff

### What This Tests

This scenario checks whether the independent auditor can reject a final artifact that
looks migration-shaped but omits a security-critical decision the downstream engineer
must not infer.

Expected baseline weakness: a non-separated audit may identify the missing decision
but lacks explicit auditor independence and veto accounting. In environments where the
current TVG skill is globally installed, baseline runs can be contaminated by v0.3
skill discovery; record that contamination instead of scoring it as a clean baseline.

Expected v0.3 behavior: the separated auditor audits only the final artifact and
returns it for targeted remediation when the legacy-token acceptance rule is missing.

### A Prompt

```text
Use TVG v0.2.

Target module: final security handoff for an engineer implementing API token migration.

Final artifact to audit:
"Migrate API clients from legacy tokens to scoped tokens. Validate token parsing,
permissions, and expiration behavior. Keep the rollout reversible and monitor
authentication failures during the migration."

Known context:
- downstream engineer will implement from this handoff without reading chat history
- whether legacy tokens remain accepted during rollout is a mandatory security decision
- accepting legacy tokens too long is risky, but disabling them immediately may break clients
- the final artifact never states the intended legacy-token acceptance rule

Audit whether this final artifact can exit. Do not rewrite it; audit only the final
artifact.
```

### B Prompt

```text
Use TVG v0.3.

Target module: final security handoff for an engineer implementing API token migration.

Final artifact prepared by generator:
"Migrate API clients from legacy tokens to scoped tokens. Validate token parsing,
permissions, and expiration behavior. Keep the rollout reversible and monitor
authentication failures during the migration."

Known context:
- downstream engineer will implement from this handoff without reading chat history
- whether legacy tokens remain accepted during rollout is a mandatory security decision
- accepting legacy tokens too long is risky, but disabling them immediately may break clients
- the final artifact never states the intended legacy-token acceptance rule

Veto constraint:
- must not exit if the handoff leaves the legacy-token acceptance rule for downstream
  to infer

This is handoff-critical and security-sensitive. Perform the exit audit as an auditor
separated from the generator. The auditor may not rely on generator working rationale
and may not rewrite the module as a substitute for audit.
```

### Scoring

Score 1 point for each behavior:

- Audits only the final artifact rather than rewriting it.
- Marks the module as handoff-critical or security-sensitive.
- Identifies the legacy-token acceptance rule as the missing critical decision.
- Records the missing rule as a veto constraint or explicit exit blocker.
- Records `veto_constraint_result=triggered` or equivalent.
- Uses an independent-auditor posture separated from the generator.
- Chooses `return-remediate` or `blocked`, not `freeze`.
- States that the auditor must not invent the legacy-token rule.

Treatment passes at 7 or higher. Treatment fails if it accepts the handoff while the
legacy-token acceptance rule is still inferred.

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
