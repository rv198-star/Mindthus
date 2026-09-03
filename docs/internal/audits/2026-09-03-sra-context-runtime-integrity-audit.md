# SRA Context Runtime Integrity Audit

Date: 2026-09-03

Issue: #157

Branch: `feat/sra-context-isolated-runtime`

Audit focus: packet integrity, stage integrity, reference closure, contamination leakage

Verdict: **PASS FOR DETERMINISTIC RUNTIME CONTRACT**

## Audit Question

Can the Phase 1.5 runtime preserve the intended SRA context boundary from raw input to
final decision without allowing tampering, stage skipping, hidden identity leakage,
unsupported state adjustment, or an inflated isolation claim?

This audit is independent of the companion WAE audit. It does not decide whether the
Workflow/Agentic split is philosophically correct; it checks whether the implemented
runtime enforces the declared split.

## Runtime Under Audit

The runtime creates and validates this sequence:

```text
raw context input
-> context admission ledger
-> sealed packet
-> anonymous blind packet
-> recorded blind judgment
-> state-aware packet
-> recorded final judgment
-> final decision and user-readable rendering
```

State transitions:

```text
prepared -> blind_recorded -> finalized
```

Primary commands:

```text
prepare_sra_run.py
record_sra_judgment.py
check_sra_run.py
render_sra_decision.py
```

Shared deterministic implementation:

```text
sra_runtime.py
```

## Integrity Surfaces

### Input And Admission

- schema and stable IDs;
- current-instruction anchor;
- allowed context kinds;
- evidence and assumption references;
- authority scope and expiry carriers;
- state-item provenance;
- historical-context explicit admission;
- quarantined and excluded ledger retention.

### Packet Binding

- raw-input hash;
- context-manifest hash;
- sealed-packet content hash;
- blind-packet content hash;
- deterministic candidate alias map;
- packet-specific output schema constants and enums.

### Judgment Binding

- blind judgment packet hash and mode;
- one assessment for every blind candidate;
- allowed evidence and assumption references;
- original candidate identity leakage check;
- blind judgment hash embedded in state packet;
- state packet hash;
- final judgment packet and blind-judgment hashes;
- state ID kind matching;
- final decision copy and isolation claim consistency.

### Carrier Reporting

- requested isolation profile;
- actual recorded carrier per stage;
- optional observable receipt and receipt hash;
- warnings for missing receipt or same-context degradation;
- final isolation claim recomputed from recorded state.

## Findings And Repairs

### R1 — State-Only Evidence Was Initially Visible To The Blind Pass

The initial packet builder omitted state fields but still exposed the complete evidence
and assumption collections. A historical-spend fact or switching-cost assumption could
therefore leak into the blind pass through its evidence record.

Repair:

- blind packets now include only evidence and assumptions referenced by blind candidate
  cards or admitted blind context;
- state packets include only blind references plus evidence and assumptions referenced
  by normalized state items;
- unused evidence remains in the sealed audit packet but is absent from both judge
  packets.

Regression coverage checks exact state-only and unrelated evidence strings.

Status: **FIXED**.

### R2 — Structured State Records Could Initially Be Unsupported Prose

A switching-cost or remaining-cost state item could have a stable state ID without an
evidence or assumption reference. The final Agent could then cite the state ID even
though the underlying statement remained unsupported.

Repair:

- every switching cost, reusable asset, remaining cost, historical spend, commitment,
  and authority boundary must cite evidence or an explicit assumption;
- unknown references fail preparation;
- authority boundaries have a distinct state kind;
- the state-aware output can cite only generated state IDs.

Status: **FIXED**.

### R3 — A Final Agent Could Claim The Blind Result Was Unchanged While Replacing It

The initial state validator checked the boolean `blind_result_changed` but did not
compare the final current floor and replenishment choice with the locked blind result.

Repair:

- `blind_result_changed=false` requires the final floor to match the mapped blind floor;
- it also requires the final next tranche to match the blind replenishment choice;
- changes require explicit state-aware attribution.

Status: **FIXED**.

### R4 — Identity Or Sunk Cost Could Have Been The Only Cited Reason For A Change

A changed result initially needed state references, but those references could have
consisted only of the current candidate identity or historical spend.

Repair:

- changed results require a non-identity, non-sunk state reference;
- changed results require a substantive state adjustment of a matching kind;
- sunk cost remains usable only through `sunk_cost_rejected`;
- `sunk_cost_used_as_reason=true` is blocked.

Status: **FIXED**.

### R5 — Final Isolation Metadata Could Have Been Tampered After Recording

The initial checker validated judgment and carrier fields but did not independently
recompute the final isolation label.

Repair:

- isolation claims are generated by one shared deterministic function;
- run state and final decision must both match the recomputed result;
- final carrier receipts and requested profile must match run state;
- final isolation boundary must be present;
- a tampered fresh-context claim is a blocking integrity error.

Status: **FIXED**.

### R6 — Weak Isolation Could Have Silently Override A Strong Need

An outer caller could explicitly choose `packet_bound` even when Full or contamination
signals requested stronger separation.

Repair:

- explicit packet-bound use under Full or contamination pressure requires a non-empty
  `isolation_override_reason`;
- the reason is stored in raw input, sealed packet, run state, trace, and final decision;
- the checker always emits a degraded-isolation warning;
- the weaker profile is not reported as fresh context.

Status: **FIXED**.

### R7 — Current Instructions Or User Constraints Could Have Been Explicitly Excluded

The generic exclusion ledger initially applied to every context kind.

Repair:

- every applicable packet requires at least one `current_instruction`;
- current instruction, current user constraint, and authority decision cannot be
  explicitly excluded;
- other exclusions remain visible in the ledger.

Status: **FIXED**.

### R8 — Candidate Presentation Order Could Influence Blind IDs

Repair:

- candidate aliases are assigned from a neutral content digest rather than input order;
- reversing the input candidate list produces the same blind candidates and mapping.

Status: **FIXED**.

### R9 — Generated Fresh Carrier Could Mutate Or Load Project Context

Repair:

- subagent dispatch uses `fork_context=false`, read-only/no-tools authority, and an
  explicit no-mutation boundary;
- Codex CLI carrier uses an empty workspace, read-only sandbox, ephemeral execution,
  ignored project rules and user configuration, and packet-specific output schema;
- scripts only generate carriers; they do not invoke a model automatically.

Status: **FIXED AT ARTIFACT CONTRACT LEVEL**. Actual hidden host context remains outside
deterministic proof.

## Adversarial Regression Coverage

The executable suite covers:

- missing current instruction;
- excluded current constraint;
- previous conclusion and candidate advocacy admission attempts;
- historical context without explicit scoped admission;
- input-order reversal;
- rich-versus-thin candidate context asymmetry;
- state-only and unused evidence leakage;
- packet hash mismatch;
- unknown candidate, evidence, assumption, and state references;
- original candidate identity in blind output;
- candidate-map tampering;
- state-ref kind mismatch;
- unsupported state record without provenance;
- blind result change without state references;
- change based only on active identity and sunk cost;
- false unchanged result with replaced floor and tranche;
- same-context mode claiming fresh context;
- fresh carrier without receipt;
- tampered final isolation claim;
- packet and admission artifact tampering;
- renderer output without semantic recomputation.

## Mechanical Evidence

```text
git diff --check                         PASS
Python compileall                        PASS
context-isolation unit tests             28 PASS
Test Lifecycle executable coverage      72 / 72
full unittest suite                      920 PASS, 5 skipped
release-pack all-platform build          PASS
SRA Skill entry                          9,983 bytes
TPlan hooks/schema/runtime diff          EMPTY
```

The generated all-platform package includes the context-isolation resource, three input
or judgment templates, shared runtime, four CLI entry scripts, and existing SRA fidelity
surfaces in Claude Code plugin/skills, Codex plugin/skills, and OpenCode layouts.

## Live Carrier Attempt

The generated Codex blind carrier was invoked from its empty read-only workspace with a
packet-bound JSON output schema. The CLI reached `gpt-5.6-sol` transport and returned
HTTP 401 because no usable API bearer credential was available on the OCI node.

Therefore:

- carrier command construction: observed;
- empty workspace and read-only invocation: observed;
- model execution: not observed;
- blind semantic judgment: not produced;
- natural host isolation quality: not passed or failed.

## Remaining Boundaries

The deterministic runtime cannot prove:

- completeness of the raw candidate surface;
- semantic correctness of context-kind assignment;
- truth of an evidence statement;
- absence of hidden system/developer context in a host;
- independence of two model calls merely because two receipts exist;
- semantic correctness of the allocation.

These limits are named in run and final-decision claim ceilings.

## Verdict

- Packet and stage integrity: **PASS**.
- Blind/state separation: **PASS**.
- State provenance closure: **PASS**.
- Isolation-claim truthfulness: **PASS**.
- Release-package inclusion: **PASS**.
- TPlan control-boundary preservation: **PASS**.
- Live fresh-context semantic qualification: **PENDING due OCI authentication**.
