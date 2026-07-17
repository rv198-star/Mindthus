# Beta.2 preregistered evaluation protocol v0.1

The frozen protocol is
[`protocols/evaluation-protocol-v0.1.json`](protocols/evaluation-protocol-v0.1.json).
It fixes what would count as success, harm, missing evidence, contamination, and a
reason to stop before any semantic smoke or matched output is generated.

## Frozen comparison

The three immutable arm ids are `stable`, `direct-only`, and `thin-kernel`. Runtime
identity still comes from each sealed arm manifest; the names alone are not evidence.

The matched workload contains 29 cases from the accepted matrix. The two real-task
replays remain excluded because no replay consent has been authorized. Four sealed
shadow receipts remain conditional on independent case-custodian binding and blindness
attestation before #119 authorization. Visible public and development cases are never
reported as blind evidence.

Both Codex and Claude package surfaces and all five entry modes are required strata.
There are three planned repeats per arm/host/case, producing a preregistered ceiling of
522 generation cells and two independent blinded judge records per output (1,044 judge
records before any allowed parse retry). The five-case smoke is one repeat across all
arms and both hosts—30 generation cells—and valid smoke outputs count as repeat one of
the matched set.

Three repeats are an exploration floor, not release proof. Missing hosts or entry modes
remain unknown; they cannot be replaced by another stratum or hidden in a global mean.

## Decision lines

Quality, owner fidelity, passive behavior, runtime load, efficiency, and interaction
cost remain separate. There is no composite score. The policy margins are preregistered
decision thresholds, not claims about expected data:

- normalized answer quality and execution-owner fidelity: no worse than Stable by more
  than 5 percentage points on the lower paired 95% interval;
- passive primitive recall: thin Kernel at least 10 points better than direct-only;
- joint owner-plus-primitive success: thin Kernel at least 8 points better than
  direct-only;
- false wakeup harm: no more than 3 points worse than Stable and no more than 5% absolute;
- lifecycle fidelity: every included thin-Kernel cell has its required native event;
- input tokens: at least 15% lower than Stable and no more than 8% above direct-only;
- wall time and native first-useful-action latency: p50 at least 10% lower than Stable,
  with p95 no worse than a 5% reduction target.

Every primary line must pass inside each host stratum and overall. An overall weighted
line cannot rescue a failing required host or entry mode. Secondary lines expose
primitive precision, token components, hops, clarification burden, notices/jargon,
retries, load contracts, and evidence provenance with explicit denominators.

## Missing evidence and vetoes

Zero/pass imputation is forbidden. A primary endpoint missing its required native,
deterministic, or two-judge evidence fires a stop veto. A secondary endpoint with
missing evidence is `blocked/unknown` unless it is independently marked as a veto; it
cannot be silently omitted.

The protocol stops on cross-arm contamination, identity/digest drift, partial or
untraceable artifacts, missing primary native evidence, judge contamination, a
systematic critical primitive miss, or authority/evidence regression. After a valid
matched run, insufficient Kernel benefit or negligible Stable savings produces a Stop
recommendation rather than another threshold-tuning round.

Model output that already exists is never discarded and replaced. Infrastructure may
retry once only when it proves no model output was produced. Contamination or digest
failure requires a new protocol version; it cannot be repaired by rerunning favorable
cells under v0.1.

## Freeze and authorization boundary

`runtime/freeze-evaluation-protocol.py` validates dependency receipts, endpoint
resolution, margins, evidence sources, workload partition, immutable arm ids,
randomization, vetoes, and authorization fields. `freeze` writes an atomic lock receipt;
subsequent edits to the protocol, dependency contracts, or validator fail validation.
The existing v0.1 lock cannot be overwritten. Any amendment requires a new version and
new lock.

The lock does not authorize model execution. Before #119, a maintainer must separately
name the exact protocol digest, generator model per host, judge model and reasoning,
generation/judge call ceilings, token or cost budget, and the person with stop
authority. A budget below the 29-case frozen design means do not start; it does not
authorize silently truncating the workload.

No semantic model output or A/B run was generated while creating or freezing v0.1.
