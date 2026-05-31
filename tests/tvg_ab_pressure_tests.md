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

## Issue 10: Thin But Polished Artifact Needs Depth Formation

### What This Tests

This scenario checks whether TVG recognizes that a clean artifact can still be
under-thick. The expected treatment is `deepen`, not premature refinement.

Expected baseline weakness: the agent tightens wording while leaving missing
constraints, alternatives, and failure paths implicit.

Expected issue #10 treatment behavior: the agent identifies `under-thick`, names the
missing thinking substrate, and runs a depth-formation pass before refinement.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: product recommendation paragraph.

Current artifact:
"We should add team dashboards because teams need visibility. This will improve
collaboration and make the product more useful."

Known context:
- no user segment is named
- no substitute workflow is compared
- no failure path or adoption condition is described
- the paragraph should become decision-useful, not just more polished

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Chooses `under-thick` or equivalent thickness-insufficient state.
- Adds real constraints, target user, substitute, failure path, or adoption condition.
- Does not compress before the missing thinking substrate exists.
- Explains why polish alone would be low value.
- Keeps the added thickness tied to decision value.

Treatment passes at 4 or higher.

## Issue 10: Adequately Thick But Loose Artifact Needs Refinement

### What This Tests

This scenario checks whether TVG stops expanding once the thought substrate is adequate
and instead improves value density.

Expected baseline weakness: the agent adds another section or checklist.

Expected issue #10 treatment behavior: the agent chooses `adequate-but-loose` and
performs `refine` by consolidating repeated claims into sharper judgment.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: method note.

Current artifact:
"This method helps teams decide when to automate a review. It should be used when the
steps are repetitive, when the reviewer has clear criteria, and when the cost of a wrong
decision is low. It should not be used when the decision is uncertain, when the facts
are missing, or when human judgment is central. In short, automate repetitive clear
checks, but keep uncertain judgment human."

Known context:
- the core constraints are already present
- the module feels repetitive and loose
- the output should stay compact

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Chooses `adequate-but-loose` or equivalent.
- Performs `refine`, not another deepening pass.
- Reduces repetition while preserving constraints.
- Produces a sharper decision rule.
- Does not remove necessary boundaries for the sake of brevity.

Treatment passes at 4 or higher.

## Issue 10: Over-Thick Low-Density Artifact Needs Compact Strengthening

### What This Tests

This scenario checks whether TVG detects over-thick low-density output and selects
compact strengthening.

Expected baseline weakness: the agent adds more examples or a new taxonomy.

Expected issue #10 treatment behavior: the agent chooses `over-thick` and removes or
compresses low-value structure while preserving the strongest insight.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: review checklist.

Current artifact:
"Check the goal. Check the user. Check the stakeholder. Check the reader. Check the
consumer. Check the input. Check the context. Check the framing. Check the evidence.
Check the proof. Check the assumptions. Check the claims. Check the risks. Check the
edge cases. Check the downstream. Check the handoff. Check the final answer."

Known context:
- the checklist is long but repetitive
- the intended reader needs a compact review aid
- no new facts are available

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Chooses `over-thick` or equivalent.
- Performs `compact-strengthen`.
- Consolidates repeated checks into fewer higher-signal checks.
- Preserves evidence, risk, and downstream concerns.
- Does not add a new checklist layer.

Treatment passes at 4 or higher.

## Issue 10: Fresh But Ungrounded Viewpoint Needs Claim Warning Or Rejection

### What This Tests

This scenario checks whether TVG allows fresh thinking without accepting unsupported
fantasy.

Expected baseline weakness: the agent accepts a striking claim because it sounds deep.

Expected issue #10 treatment behavior: the agent marks the idea as ungrounded, downgrades
it to speculation, or rejects it if no anchor exists.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: strategy insight.

Current artifact:
"The next generation of documentation will disappear entirely because agents will infer
all project intent from code. Therefore, teams should stop writing docs and invest only
in code-reading agents."

Known context:
- no evidence is provided
- some teams still need human-readable policy, onboarding, and review records
- the user wants a fresh viewpoint, but not free fantasy

Decide the TVG state route and improve or reject the viewpoint.
```

### Scoring

Score 1 point for each behavior:

- Detects that the claim is fresh but insufficiently grounded.
- Uses claim calibration as a warning, not as a blanket ban on exploration.
- Downgrades the claim to a bounded hypothesis or rejects the unsupported version.
- Names what anchor or evidence would make the idea productive.
- Avoids presenting the speculation as fact.

Treatment passes at 4 or higher.

## Issue 10: Grounded Stretch Accepts Productive Speculation

### What This Tests

This scenario checks whether TVG can go beyond current reality when the stretch has an
anchor and useful recovery path.

Expected baseline weakness: the agent either rejects the idea as unproven or overclaims
it as fact.

Expected issue #10 treatment behavior: the agent classifies it as `productive-speculation`
and keeps the anchor visible.

### Prompt

```text
Use TVG issue #10 treatment behavior.

Target module: future workflow insight.

Current artifact:
"Review tools may shift from checking completed artifacts to shaping the artifact while
it is being generated."

Known context:
- current tools already provide inline suggestions
- agent workflows increasingly generate drafts interactively
- the claim is not proven as a market trend
- the goal is to produce an insight that is fresh but still grounded

Decide the TVG state route and improve the insight.
```

### Scoring

Score 1 point for each behavior:

- Accepts the idea as grounded stretch or productive speculation.
- Names the anchor in current inline tools and interactive generation.
- Avoids claiming the trend is already proven.
- Explains why the frame changes product or workflow thinking.
- Keeps the output useful rather than purely speculative.

Treatment passes at 4 or higher.

## Issue 10: Coverage-Rich Profile Allows Useful Thickness Without Bloat

### What This Tests

This scenario checks whether `coverage_rich` changes delivery shape without lowering
the value standard.

Expected baseline weakness: the agent treats coverage-rich as permission to expand
everything.

Expected issue #10 treatment behavior: the agent includes useful context, examples,
reasoning path, and boundaries while rejecting ornamental completeness.

### Prompt

```text
Use TVG issue #10 treatment behavior with output_profile=coverage_rich.

Target module: onboarding explanation for a methodology skill.

Current artifact:
"Use this skill when AI output looks complete but lacks value."

Known context:
- new contributors need enough context to apply the skill correctly
- examples are useful
- low-value expansion is not acceptable

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Treats `coverage_rich` as delivery bias, not a workflow fork.
- Adds context or examples that improve correct use.
- Keeps each expansion tied to thinking thickness, grounded insight, or value density.
- Rejects ornamental completeness.
- Does not lower the value-density standard.

Treatment passes at 4 or higher.

## Issue 10: Insight-Dense Profile Must Not Skip Thinking Thickness

### What This Tests

This scenario checks whether `insight_dense` compresses delivery only after sufficient
thinking substrate exists.

Expected baseline weakness: the agent jumps to a punchy line before resolving missing
constraints.

Expected issue #10 treatment behavior: the agent first identifies the missing thickness,
then produces a compact final expression.

### Prompt

```text
Use TVG issue #10 treatment behavior with output_profile=insight_dense.

Target module: executive summary.

Current artifact:
"The platform should become more agentic because agentic products are the future."

Known context:
- the target user is not named
- the risk boundary is not named
- no substitute or timing condition is named
- the final output should be short and sharp

Decide the TVG state route and improve the module.
```

### Scoring

Score 1 point for each behavior:

- Does not compress before identifying missing thickness.
- Names the missing user, risk, substitute, or timing constraint.
- Produces a compact final expression after grounding the idea.
- Treats `insight_dense` as delivery bias only.
- Avoids a catchy but unsupported claim.

Treatment passes at 4 or higher.

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
