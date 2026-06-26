# Issue Draft: Keep TVG Exit Audit Internal To The TVG Loop

> Status note: this is a repair issue spec, not current routing guidance. Legacy
> wording quoted below is preserved as counterexample context; current routing guidance
> lives in `skills/using-mindthus/SKILL.md`, `skills/tvg/SKILL.md`, and
> `docs/methodologies/tvg.md`.

## Title

Prevent TVG internal exit audit from becoming a generic external audit route

## Context

Recent usage suggests a routing bug: `TVG` is sometimes being treated as a general
audit method because TVG contains an `agentic exit audit` and an
`independent_auditor` concept.

That is too wide. TVG's audit belongs inside the TVG value-gain loop. It decides
whether a TVG-run bounded artifact can honestly exit as `freeze`,
`freeze-with-review-bound-warning`, `return-remediate`, or `blocked`.

It is not a standalone external audit route for:

- code review
- release readiness
- workflow health
- method correctness
- factual verification
- strategic direction
- product taxonomy or requirement boundaries
- Mission runtime continuation
- generic document review

The current wording makes this bug plausible in two places:

- `skills/tvg/resources/exit-audit-template.md` says "audit" prominently, but does not
  explicitly say this audit is internal to an active TVG loop.
- Older tplan design language uses `artifact depth audit` and `depth_audit -> tvg`,
  which can make TVG look like an external audit capability rather than a value-gain
  loop with an internal exit gate.

## Core Principle

TVG is a value-directed transformation loop, not an audit service.

Its audit is an internal exit gate:

```text
TVG audit = TVG-loop exit judgment.
TVG audit != generic external audit route.
```

TVG may use an independent auditor only after TVG has an active bounded artifact,
expected value, evidence boundary, veto constraints, and exit decision to judge.

If the user asks to "audit" something without asking to run TVG on a bounded artifact,
the router should first identify the real audit object:

- code or implementation correctness -> code review / tests / verification
- release readiness -> evidence acquisition, tplan, or project release process
- workflow / controller mismatch -> WAE, if the WAE domain gate passes
- structural or category boundary -> EDSP
- problem definition or task landing -> 3L5S
- bounded artifact value-gain and exit -> TVG

## Target

Tighten TVG routing so that:

- TVG wakes for bounded artifacts that need value gain.
- TVG exit audit remains internal to the TVG loop.
- "audit" wording does not by itself route to TVG.
- `independent_auditor` is framed as separation of generator and exit judge, not as a
  general external audit persona.
- tplan and router docs do not use `depth_audit` in a way that suggests TVG owns all
  artifact, release, or workflow audits.

## Proposed Direction

### 1. Clarify TVG Skill Boundary

Update `skills/tvg/SKILL.md`:

- State that `agentic exit audit` is internal to TVG.
- State that TVG is not a standalone audit method.
- Add skip cases for external code, release, workflow, factual, method, strategy, and
  requirement-boundary audits.
- Keep existing TVG scope: bounded AI-generated artifact, expected value, evidence
  boundary, veto constraints, and value-gain exit.

### 2. Clarify Exit Audit Template

Update `skills/tvg/resources/exit-audit-template.md`:

- Rename or qualify the purpose as "TVG-loop exit audit."
- Add a hard note that the template must not be used as a generic audit template
  outside an active TVG run.
- Require `input_version_or_run` or equivalent TVG-run context when independence is
  claimed.

### 3. Tighten Router Language

Update `skills/using-mindthus/SKILL.md`:

- Add a skip rule: "Do not route to TVG merely because the user asks for an audit,
  review, or check."
- Route TVG only when the active object is a bounded artifact whose practical value is
  thin and whose expected value can be named.
- Keep the existing rule that TVG must not absorb upstream strategy, structure, or
  path-carrying judgment.

### 4. Mirror In AGENTS

Update `AGENTS.md`:

- TVG transforms a bounded artifact toward a value standard.
- TVG's audit is an internal exit check, not a general external audit route.
- External audits should route by object: code, release, workflow, structure, evidence,
  strategy, or Mission runtime.

### 5. Repair TPlan Terminology

Review older tplan docs that say `artifact depth audit` or `depth_audit -> tvg`.

Prefer wording such as:

```text
artifact_value_gain
bounded_artifact_value_check
TVG value-gain exit check
```

Do not imply that TVG is the default owner for release, workflow, code, or Mission
audits.

### 6. Add Contract Tests And Pressure Scenarios

Extend `tests/test_mindthus_router_contract.py` to require:

- TVG docs say exit audit is internal to TVG.
- `using-mindthus` says audit/review/check wording is not enough to route to TVG.
- `AGENTS.md` mirrors the internal-exit-audit boundary.
- tplan terminology does not present TVG as a generic audit route.

Extend `tests/mindthus_router_pressure_tests.md` with skip and positive cases:

- Positive: a bounded AI handoff artifact was improved by TVG and now needs an
  exit-state decision.
- Positive: a handoff-critical TVG output needs independent exit audit separated from
  generator work.
- Skip: "audit this release readiness" with missing runtime proof and stakeholder
  approval; do not route to TVG.
- Skip: "audit this workflow" where controller mismatch is active; route to WAE only
  if WAE's domain gate passes.
- Skip: "audit this taxonomy / requirement boundary"; route to EDSP or direct
  structural judgment, not TVG.
- Skip: "audit this code"; use code review and tests, not TVG.

## Non-Goals

- Do not remove TVG exit audit.
- Do not remove independent auditor separation for high-impact, high-uncertainty, or
  handoff-critical TVG outputs.
- Do not make TVG weaker at blocking unsafe or low-value exits.
- Do not turn TVG into a release, code, workflow, strategy, or factual-audit method.
- Do not create a new standalone audit skill.
- Do not weaken Evidence / Claim Ceiling or tplan Mission runtime gates.

## Acceptance Criteria

- `skills/tvg/SKILL.md` states that TVG audit is internal to the TVG loop.
- `skills/tvg/resources/exit-audit-template.md` says it is not a generic audit
  template outside an active TVG run.
- `skills/using-mindthus/SKILL.md` prevents audit/review/check wording from routing to
  TVG by itself.
- `AGENTS.md` mirrors the internal-exit-audit boundary.
- tplan docs no longer present `tvg` as a generic `artifact depth audit` route.
- Router pressure tests include TVG positive exit-audit cases and external-audit skip
  cases.
- Focused tests pass:

```bash
python3 -m unittest tests.test_mindthus_router_contract -v
python3 -m unittest tests.test_packaging_docs -v
```

## Implementation Notes

The fix should keep TVG strong where it belongs. The goal is not to remove audit
discipline from TVG. The goal is to prevent the internal audit mechanism from becoming
an external route trigger.

Short rule:

```text
No active TVG loop, no TVG audit.
No bounded artifact value-gain target, no TVG.
```
