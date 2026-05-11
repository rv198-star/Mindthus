# WAE Control-Boundary Worksheet

This worksheet is not the default path. Use the Minimal WAE Check first.

Do not fill every field. Fill only fields that can change the control decision.

## Required Minimal Fields

What part of the work is being assigned control?

- Scope:
- Current proposed control:
- Why this boundary is being questioned:

Minimal check:

- Path or truth uncertainty:
- Claim that needs evidence:
- Reversibility and blast radius:

Boundary decision:

- Workflow controls:
- Agentic judgment controls:
- Evidence constrains:

Expansion trigger:

- None / risk modulator / nested call / runtime failure / L3 tool / human escalation / other:

If there is no expansion trigger, stop here.

## Expanded Fields

Skip any expanded field that cannot change the control decision.

### Certainty Estimate

Workflow certainty:

- High / Medium / Low:
- Why:

Context certainty:

- High / Medium / Low:
- Why:

### Operational Risk

Reversibility:

- Reversible / partially reversible / irreversible:
- Rollback or repair path:

Blast radius:

- Low / medium / high:
- Who or what is affected if wrong:

Tool tier:

- L1 read-only / L2 writable but recoverable / L3 side-effectful or irreversible:
- Tool authority constraint:

Invocation context:

- Direct user call / nested skill or agent / batch / scheduled / trigger / unattended:
- Does context tightening reduce agentic freedom:

Instruction/data boundary:

- Is any processed data instruction-like:
- How will it be preserved as data rather than control:

Explicit relaxation:

- Is any default boundary being relaxed:
- granting authority:
- Scope:
- expiry:

### Control Details

Recommended primary control:

- Workflow shell / Agentic core / Evidence bridge / Mixed:

What workflow should control:

- Order:
- Deterministic transforms:
- Mechanical checks:
- State recording:

What agentic judgment must control:

- Semantic uncertainty:
- Strategy or trade-off:
- Domain interpretation:
- Revision under new evidence:

Loop budget:

- iterations:
- tool calls:
- time:
- retries:

What evidence must constrain:

- Claim:
- Proof surface:
- Confidence cap if missing:
- Review-bound item:

Evidence reporting:

- used tool tiers:
- fallback layer reached:
- unresolved uncertainty:
- side effects not visible to caller:

Human escalation:

- Is escalation eligible:
- Is escalation temporarily closed by user preference for AI autonomy:
- Exact decision packet if needed:

### Boundary Risks

Workflow overreach:

- Is a deterministic process freezing uncertain truth?

Pseudo-agentic schema:

- Is an LLM only filling fields without making a real judgment?

Evidence theater:

- Does evidence actually constrain claims, or merely decorate them?

Agentic drift:

- Does the agentic loop have purpose, evidence, and exit criteria?

Skill boundary conflict:

- Does another skill or outer workflow impose a stricter boundary?

### Forbidden Automation

What must not be automated here?

- 

Why:

- 

### Exit Criteria

What must be true before this control design is accepted?

- Evidence:
- Human escalation:
- Fallback path:
- Promotion or demotion signal:
- Failure signal:
- Next action:

## Short Decision

One-sentence boundary:

> Workflow controls ____. Agentic judgment controls ____. Evidence constrains ____. Human escalation is ____.
