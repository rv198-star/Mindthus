# SELA / EDSP Multi-Role A/B Pressure Tests

These tests evaluate the single-agent multi-role changes for `SELA` and `EDSP`.

The goal is not to prove that multi-role always changes the final answer. The goal is
to check two claims:

1. Non-trivial judgments gain useful pressure: missed risks, malformed binaries, or
   action-window mistakes become more explicit.
2. Lightweight cases do not pay unnecessary overhead: multi-role should not run when
   the decision is deterministic, low-stakes, reversible, or already bounded.

Run each scenario in two fresh sessions when possible:

- **A / baseline**: explicitly forbid the new multi-role names.
- **B / treatment**: use current rules and enable single-agent multi-role only when
  justified.

Do not score broader writing quality. Score whether the treatment adds decision value
without adding avoidable process weight.

## Scenario 1: EDSP Validation Control Boundary

### What This Tests

This scenario checks whether EDSP's multi-role pass adds useful challenge pressure for
a malformed binary: scripts for all validation versus agentic review for all validation.

Expected useful gain: treatment should separate the initial skeleton from challenge
findings, name why the binary is malformed, and produce a routed validation policy.

Expected no-negative result: treatment should not recommend extra agent review for
purely mechanical checks.

### A Prompt

```text
A/B baseline. Use EDSP-style extreme deduction, but do NOT use Multi-Role Challenge,
Builder, Challenger, or Synthesizer.

Scenario: We are deciding whether an AI engineering workflow should use scripts for
all validation or agentic review for all validation.

Known context:
- script checks are fast and reproducible
- agent review understands semantics but can be inconsistent
- artifacts include formatting, runtime tests, architecture judgments, business claims,
  and release readiness claims
- bad validation can either block useful work or falsely approve unsafe claims

Task: produce a concise JSON with fields: dimensions, extreme_projection,
collapsed_outcome, recommendation, risks, no_negative_overhead_check.
```

### B Prompt

```text
A/B treatment. Use EDSP with single-agent multi-role pressure.

Scenario and known context are the same as A.

Task: produce a concise JSON with fields: builder_dimensions, builder_skeleton,
challenger_findings, synthesizer_decision, final_recommendation, risks,
no_negative_overhead_check.
```

### Scoring

Score 1 point for each behavior:

- Identifies the original binary as malformed.
- Routes validation by claim/artifact type instead of validator identity.
- Separates deterministic checks from semantic claims.
- Names release readiness as a composite gate.
- Requires evidence or owner approval for business/release claims.
- Avoids agent review for purely mechanical checks.
- Avoids adding heavyweight process as a default.

Treatment passes at 6 or higher.

## Scenario 2: EDSP Low-Risk Deterministic Formatting

### What This Tests

This scenario checks whether current EDSP rules avoid multi-role overhead when the
question is deterministic.

Expected treatment behavior: `multi_role_used=false` and script-only validation.

### A Prompt

```text
A/B baseline. Use EDSP-style judgment, but do NOT use Multi-Role Challenge, Builder,
Challenger, or Synthesizer.

Scenario: A team asks whether a JSON formatting check should be handled by a
deterministic script or by agentic review.

Known context:
- the JSON schema is fixed
- the expected formatting is deterministic
- failure is reversible
- the only decision is whether formatting matches the schema

Task: produce concise JSON with fields: recommendation, reason, risks,
no_negative_overhead_check.
```

### B Prompt

```text
A/B treatment. Use EDSP current rules with single-agent multi-role only if justified.

Scenario and known context are the same as A.

Task: produce concise JSON with fields: multi_role_used, recommendation, reason, risks,
no_negative_overhead_check.
```

### Scoring

Treatment passes if it:

- sets or states `multi_role_used=false`
- recommends deterministic script validation
- says agentic review adds cost or variance without decision value

## Scenario 3: SELA SaaS Onboarding Replacement

### What This Tests

This scenario checks whether SELA multi-role pressure improves a non-trivial strategic
decision without turning long-term efficiency into immediate full replacement.

Expected useful gain: treatment should expose system efficiency, local advantage, and
timing separately, while preserving a staged action.

Expected no-negative result: treatment should not become anti-automation or demand a
heavy governance process.

### A Prompt

```text
A/B baseline. Use SELA, but do NOT use Multi-Role Check, System Advocate,
Local Defender, or Timing Auditor.

Scenario: A SaaS company is considering replacing human onboarding specialists with an
AI onboarding agent.

Known context:
- AI can answer common setup questions at 1/20th cost and 24/7
- top human specialists handle enterprise edge cases, trust-building, compliance
  exceptions, and angry high-value customers better
- switching all accounts immediately would save cost but migration is reversible only
  with contract and staffing delay

Task: produce a concise JSON with fields: system_efficiency_judgment,
local_advantage_judgment, action, timing_reason, risks, no_negative_overhead_check.
```

### B Prompt

```text
A/B treatment. Use SELA with single-agent multi-role pressure.

Scenario and known context are the same as A.

Task: produce a concise JSON with fields: system_advocate, local_defender,
timing_auditor, action, timing_reason, risks, no_negative_overhead_check.
```

### Scoring

Score 1 point for each behavior:

- Keeps AI as the standard/mainline path for common onboarding.
- Preserves human-led paths for enterprise, compliance-sensitive, or escalated accounts.
- Does not recommend immediate full replacement.
- Names rollback/migration delay as a timing concern.
- Names hidden escalation, specialist attrition, contract/SLA, or churn risk.
- Uses staged A/B or cohort rollout instead of heavy process.
- Checks that monitoring/escalation cost does not erase the efficiency gain.

Treatment passes at 6 or higher.

## Scenario 4: SELA Low-Risk Internal Digest

### What This Tests

This scenario checks whether SELA avoids multi-role overhead for a reversible,
low-stakes efficiency decision.

Expected treatment behavior: `multi_role_used=false` and `commit`.

### A Prompt

```text
A/B baseline. Use SELA, but do NOT use Multi-Role Check, System Advocate,
Local Defender, or Timing Auditor.

Scenario: A product team is deciding whether to replace a manually curated weekly
internal status digest with an automated digest.

Known context:
- the digest is internal only
- low stakes
- easy to revert
- current manual version takes 6 hours per week
- automated version is 90 percent accurate and can link to sources
- no customers or compliance decisions depend on it

Task: produce concise JSON with fields: system_efficiency_judgment,
local_advantage_judgment, action, timing_reason, risks, no_negative_overhead_check.
```

### B Prompt

```text
A/B treatment. Use SELA current rules with single-agent multi-role only if justified.

Scenario and known context are the same as A.

Task: produce concise JSON with fields: multi_role_used, system_advocate,
local_defender, timing_auditor, action, timing_reason, risks,
no_negative_overhead_check.
```

### Scoring

Treatment passes if it:

- sets or states `multi_role_used=false`
- recommends `commit`
- does not preserve a heavy manual review loop
- keeps review overhead far below the saved 6 hours/week

## Scenario 5: SELA AI PR Review Default At The Threshold

### What This Tests

This scenario checks a genuine threshold decision: whether AI should become the
default first-pass reviewer for pull requests while humans retain boundary-heavy
review.

Expected useful gain: treatment should make the default-vs-escalation split more
explicit and name the boundary conditions that keep humans in the loop.

Expected no-negative result: treatment should not turn the default into an extra
mandatory review layer on every PR.

### A Prompt

```text
A/B baseline. Use SELA, but do NOT use Multi-Role Check, System Advocate,
Local Defender, or Timing Auditor.

Scenario: A platform team is deciding whether to make AI the default first-pass reviewer
for pull requests.

Known context:
- AI review catches formatting issues, missing tests, obvious bugs, and simple security smells quickly
- AI review costs about 1/15 of a human review and returns results in minutes
- human reviewers are still much better at cross-service invariants, product semantics,
  hidden coupling, and rollout risk
- 80 percent of PRs are routine, but the last 20 percent of incidents usually came from
  boundary changes that looked routine at first
- the goal is not full replacement; the goal is whether AI should become the default
  first-pass reviewer, with human review reserved for flagged or boundary-heavy changes

Task: produce concise JSON with fields: system_efficiency_judgment,
local_advantage_judgment, action, timing_reason, risks, no_negative_overhead_check.
```

### B Prompt

```text
A/B treatment. Use SELA with single-agent multi-role pressure.

Scenario and known context are the same as A.

Task: produce concise JSON with fields: system_advocate, local_defender,
timing_auditor, action, timing_reason, risks, no_negative_overhead_check.
```

### Scoring

Treatment passes if it:

- keeps AI as the default first-pass reviewer
- preserves human review for boundary-heavy or high-risk changes
- does not add an extra mandatory review layer on every PR
- names rollout/risk concerns rather than collapsing them into a generic pro-AI answer

## Scenario 6: SELA Incentive Pressure Without Game-Theory Method

### What This Tests

This scenario checks whether incentive and game-theoretic concerns are handled as
Perspective Pressure inside SELA, not as a new method or standalone skill.

Expected useful gain: treatment should surface stakeholder incentives and likely
strategic reactions before deciding the rollout shape.

Expected no-negative result: treatment should not create or invoke a standalone
game-theory method, and should not turn the decision into a broad theory essay.

### A Prompt

```text
A/B baseline. Use SELA, but do NOT use Multi-Role Check, System Advocate,
Local Defender, or Timing Auditor. Do not mention Perspective Pressure.

Scenario: A consulting firm is deciding whether to replace senior consultants'
first-draft market analysis with an AI research workflow.

Known context:
- AI can produce draft market maps at 1/30th cost and 20x speed
- senior consultants say clients pay for judgment, not drafts
- partners benefit if margins rise but may understate delivery risk
- senior consultants benefit if AI adoption is delayed
- clients may accept AI-assisted drafts if a named senior still owns the final claim
- competitors are likely to advertise lower-cost AI-assisted analysis within six months

Task: produce concise JSON with fields: system_efficiency_judgment,
local_advantage_judgment, action, timing_reason, risks, no_negative_overhead_check.
```

### B Prompt

```text
A/B treatment. Use SELA with single-agent multi-role pressure. Treat stakeholder
incentives and game-theoretic reactions as Perspective Pressure, not as a standalone
game-theory method.

Scenario and known context are the same as A.

Task: produce concise JSON with fields: system_advocate, local_defender,
timing_auditor, action, timing_reason, risks, no_negative_overhead_check.
```

### Scoring

Treatment passes if it:

- uses Perspective Pressure as a challenge surface
- names partner, consultant, client, and competitor incentives or reactions
- keeps AI as the scalable draft path while preserving senior ownership of final claims
- recommends staged rollout or client-segmented adoption rather than immediate full replacement
- does not create or invoke a standalone game-theory method
- names an execution effect such as rollout shape, evidence requirement, risk handling,
  or stopping condition

## Scenario 7: EDSP Deterministic Boundary Skip

### What This Tests

This scenario checks whether EDSP skips pressure for low-risk deterministic work where
mechanical verification is sufficient.

Expected treatment behavior: `multi_role_used=false` and direct mechanical validation.

### A Prompt

```text
A/B baseline. Use EDSP-style judgment, but do NOT use Multi-Role Challenge, Builder,
Challenger, or Synthesizer.

Scenario: A maintainer asks whether to decide a generated YAML manifest's validity by
manual review or by running the schema validator.

Known context:
- the schema is fixed
- the manifest has no semantic product claims
- failure is reversible
- the validator returns deterministic pass/fail output
- the only question is whether the manifest conforms to the schema

Task: produce concise JSON with fields: recommendation, reason, risks,
no_negative_overhead_check.
```

### B Prompt

```text
A/B treatment. Use EDSP current rules with single-agent multi-role only if justified.
Apply the pressure surface rule: low-risk deterministic work should skip pressure.

Scenario and known context are the same as A.

Task: produce concise JSON with fields: multi_role_used, recommendation, reason, risks,
no_negative_overhead_check.
```

### Scoring

Treatment passes if it:

- sets or states `multi_role_used=false`
- says the case is low-risk deterministic
- recommends running the schema validator
- states that mechanical verification is sufficient
- does not add Builder/Challenger/Synthesizer ceremony
