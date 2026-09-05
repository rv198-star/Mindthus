# SRA Method-Fidelity Contract

## Purpose

This contract checks whether an applicable SRA judgment executed the required method
moves at the selected reasoning depth. It does not define a second resource-allocation result.

The canonical resource pools, quantities, candidate ledger, Full bundle decision, next
tranche, investment ceiling, reserve, outcome, finalization, comparison, and integrity
rules belong to the v0.3 runtime contract in `context-isolation.md` and
`scripts/sra_domain.py`.

Short rule:

> Audit whether SRA reasoning happened; reference the canonical runtime decision instead
> of copying its allocation fields.

A method-fidelity pass does not prove that the selected priority, necessity claim, ROI
judgment, bundle, or allocation is semantically correct.

This structured artifact protocol applies when a runtime/fidelity artifact is requested.
Conversational Lite may execute the same floor-and-next-tranche reasoning in a short
recommendation without creating these files. It claims neither a fidelity validator pass
nor runtime authorization. Method use alone is not a reason to pay the artifact cost.

## Entry Outcomes

Every fidelity artifact uses one `entry_outcome`:

- `direct`: no real shared-resource competition exists, or direct trial is cheaper than
  analysis;
- `lite`: one bounded action, tranche, or checkpoint was judged;
- `full`: bundle-level, multi-resource, major, or hard-to-reverse allocation was judged;
- `blocked`: a load-bearing target, evidence, authority, candidate, projection, or
  resource boundary was missing before applicable allocation began.

`direct` and `blocked` are accepted method exits. They require:

```text
plain_language_conclusion
exit_reason
transfer_to            # optional string
```

They do not require a runtime decision reference or applicable-run judgment moves.

## Applicable Fidelity Shape

Applicable `lite` and `full` artifacts require:

```text
schema_version: sra-fidelity-v0.2
method: SRA
entry_outcome: lite | full
plain_language_conclusion
runtime_decision_ref
required_judgment_moves
```

The fidelity artifact does not repeat:

- the Allocation Frame;
- resource-pool or quantity contracts;
- candidate assessments or allocation ledger;
- current-floor or maintenance resource amounts;
- Full bundle members, feasibility, dominance, or selected bundle;
- next-tranche resources;
- investment ceiling;
- reserve allocation;
- allocation outcome or finalization table.

Those fields are validated only by the canonical v0.3 runtime.

## Runtime Decision Reference

`runtime_decision_ref` records metadata for the terminal runtime artifact used by the
fidelity audit:

```text
schema_version: sra.final-decision.v0.3
artifact_path
artifact_hash: sha256:<64 lowercase hex>
mode: lite | full
allocation_outcome
authorization_horizon
finalization_status
```

The standalone fidelity validator checks metadata shape and deterministic consistency.
It does not open the referenced artifact or recompute its digest. Runtime integrity is
owned by `check_sra_run.py`.

The referenced mode must match `entry_outcome`.

Outcome and finalization must agree:

| Runtime outcome | Finalization |
|---|---|
| `allocate` | `finalized` |
| `conditional` | `conditional` |
| `infeasible` | `finalized` |
| `blocked` | `blocked` |
| `request_missing_context` | `blocked` |

Lite accepts only:

- `one_action`;
- `one_tranche`;
- `until_named_checkpoint`.

Full may additionally reference `bounded_decision_window`.

## Required Judgment Moves

Every applicable run requires:

- `candidate_horizon_probe`;
- `priority_order`;
- `resource_contention`;
- `evidence_bounded_necessity`;
- `contraction`;
- `replenishment`;
- `meaningful_tranche`;
- `switching_vs_sunk_cost`;
- `authorization_horizon`;
- `defer_stop_or_reserve`;
- `rerank_trigger`;
- `mode_boundary`;
- `claim_ceiling`.

Full additionally requires:

- `minimum_sufficient_bundle`;
- `resource_vector`;
- `feasibility_and_dominance`;
- `reserve_capacity`.

For Lite, `contraction` records one bounded micro-contraction and `replenishment` records
one next-tranche comparison from the resulting floor. For Full, the same method core
expands across explicit candidate bundles and resource channels.

Each move includes:

```text
status: addressed | not_applicable | transfer | challenge_premise
finding
failure_criteria_response
evidence_surface
```

A non-empty move is an auditable carrier, not proof that the reasoning is true.

## Analysis-Cost Boundary

The selected depth remains proportionate to the plausible loss from a wrong allocation.
A reversible local trial should stay direct or Lite. Bundle-level, major,
fixed-threshold, multi-resource, or irreversible decisions may justify Full.

The fidelity validator confirms that `mode_boundary` is recorded and Lite does not
reference a Full-only authorization horizon. It cannot determine whether the depth choice
was substantively correct.

## Failure Criteria

An applicable fidelity artifact has a shape or evidence risk when:

- no canonical runtime decision reference is recorded;
- the reference uses a non-v0.3 final-decision schema;
- its path or digest is malformed;
- its mode differs from the fidelity entry outcome;
- its outcome, finalization, or authorization horizon is inconsistent;
- no Candidate Horizon Probe is recorded;
- hard gates and target feasibility are not represented before ROI-style comparison;
- shared resource contention is not addressed;
- necessity is asserted without evidence or an overturn condition;
- Lite omits contraction or replenishment;
- sunk cost and switching cost are not separated;
- maintenance, defer, stop, or reserve consequences are not addressed;
- no reranking trigger is named;
- Full omits minimum sufficient bundle, resource vector, feasibility/dominance, or
  reserve-capacity moves;
- numeric scoring is presented as semantic proof.

## Routing Boundaries

A fidelity artifact may record a transfer or direct exit when another owner controls the
active question:

- 3L5S: problem definition or decomposition;
- EDSP: unstable proposition or structural binary;
- SELA: long-term system efficiency versus local advantage;
- MPG: carrier, exposure, timing, and path posture for one selected mainline;
- WAE: Agentic controller mismatch;
- TVG: value gain inside one bounded artifact;
- TPlan: Mission state, Pulse arbitration, continuation, authority, recovery, and
  mutation.

The validator can accept an explicit exit. It cannot determine whether the transfer is
semantically correct.

## Runtime Relationship

The canonical v0.3 runtime owns:

- situated and challenge question surfaces;
- declared context projections;
- declared resource pools and quantity contracts;
- candidate demand and allocation compatibility;
- one candidate allocation ledger;
- Full bundle members, feasibility, dominance, and selected bundle;
- independent challenge and situated packets;
- typed comparison and one-pass reconciliation;
- outcome/finalization mapping;
- deterministic state, Prompt, Dispatch, command, final-source, and trace
  reconstruction;
- bounded repair of derived artifacts;
- human-readable rendering.

Ordinary Lite may use one situated judgment. Full or material contamination uses a
challenge and situated judgment that cannot see each other's output. Agreement means the
same typed commitment survived both views; it remains corroboration rather than proof.
Conflict opens one targeted reconciliation that may remain conditional or blocked.

A runtime-integrity pass proves only that recorded artifacts conform to the declared
workflow. It does not prove complete context, correct projection quality, absent hidden
host context, or correct priority.

## Claim Ceiling

Supported claim:

> SRA method-fidelity validation verifies that required Lite or Full judgment moves were
> recorded and linked to canonical v0.3 terminal runtime-decision metadata.

Unsupported claims:

- SRA always finds the correct priority;
- SRA maximizes ROI or computes an optimal allocation;
- the fidelity artifact independently validates resource or bundle semantics;
- a referenced digest proves the runtime artifact exists or is correct;
- pressure tests prove real-world business value.

## Script Boundary

`scripts/validate_sra_output.py` emits an
`SRA Method-Fidelity & Evidence Risk Report`.

It validates fidelity evidence and canonical reference metadata. It does not validate or recreate the runtime allocation carrier, judge priority quality, determine necessity,
calculate semantic ROI, prove bundle sufficiency, or choose the strongest alternative.
