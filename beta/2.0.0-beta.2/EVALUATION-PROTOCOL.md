# Beta.2 preregistered evaluation protocol v0.1

The frozen protocol is
[`protocols/evaluation-protocol-v0.1.json`](protocols/evaluation-protocol-v0.1.json).
It fixes what would count as success, harm, missing evidence, contamination, and a
reason to stop before any semantic smoke or matched output is generated.

## Codex-only amendment v0.2

Protocol v0.2 preserves the three arms, 29-case matched workload, endpoint margins,
missing-evidence rules, vetoes, and three-repeat exploration floor from v0.1, but removes
the Claude execution stratum. It supports Codex-only claims and explicitly forbids
Claude or cross-host generalization.

The frozen v0.2 workload contains 261 generation cells and 522 independent judge
records. Its smoke contains 15 generation cells and 30 judge records; valid smoke
outputs count as repeat one. Generator and judge roles both use `gpt-5.6-sol` with
`xhigh` reasoning, but run in isolated sessions and homes. This is same-model blind
review, not independent-model validation.

The preregistered hard ceilings are 276 generation calls, 552 judge calls, and
25,000,000 aggregate input + output + reasoning tokens. Cached-input tokens are
reported separately and are not double-counted. William is the blinded human
adjudicator and stop authority.

The immutable v0.2 protocol digest is
`a886ebd0f94a4a01f28319f635b72999c28196b59956393eedc260e20db2d192`; its lock digest
is `72f4af3e14f6d76fa920d623aaa00436dd4bbde5fb22ff7d34b630d865be0edc`.
The v0.1 protocol and lock remain independently valid and unchanged.

## Visible-case amendment v0.3

Protocol v0.3 is the user-selected continuation after removing the four
`sealed-shadow` cases. It contains only the 25 implementation-visible public and
development cases. The four sealed cases and two unauthorized real-task replays are
explicitly excluded; no custodian or blindness claim is implied by their absence.

The matched workload is 25 cases × 3 arms × 3 repeats: 225 successful generation
outputs and 450 isolated judge records. Its five-case smoke remains 15 generation
outputs and 30 judge records. Generator and both judge sessions use `gpt-5.6-sol` with
`xhigh` reasoning. William remains the human adjudicator and stop authority.

The hard ceilings are 240 generation calls, 480 judge calls, and 22,000,000 aggregate
input + output + reasoning tokens. The immutable protocol SHA-256 is
`ce8c06eb0656e1023de9ff477ab7a0b5a3302194e9e5af952b916130a231b144`; its internal
lock digest is
`2bd081510deaf76ebbc8b96a630ba1ec1fa9c28b982cb2205fbc7df12e951466`.
The v0.1 and v0.2 protocol/lock pairs remain independently valid and unchanged.

The v0.3 claim ceiling is deliberately lower than the earlier design: results may be
reported only as exploratory evidence on implementation-visible Codex cases. They
cannot support hidden-set, sealed-case blindness, Claude, cross-host, independent-model,
generalization, or release-readiness claims.

## v0.3 execution status

The authorization and model-free rehearsal passed, but the first real smoke cell fired
the frozen `missing-primary-native-evidence` veto. Codex CLI 0.144.4 returned a valid
answer and token usage, but none of its JSONL events contained a timestamp from which
the required native `first_useful_action_latency_seconds` endpoint could be derived.

Execution therefore stopped after one generation call, zero judge calls, and 48,256
counted tokens. The remaining 14 smoke generations, all 30 smoke judges, and the
matched run were never started. The existing cell must not be rerun. Continuing requires
either a Codex host that emits the frozen native event or a separately reviewed protocol
version that changes the endpoint provenance requirement.

## Incremental filesystem-isolated amendment v0.5

v0.4 remains an immutable stopped experiment. Across the prior v0.3 and v0.4
executions, 146 generation attempts, 42 judge attempts, and 8,133,510 counted tokens
were consumed, but v0.4 produced no valid three-arm comparison record: judging closed
too late, and retrospective evidence showed that accepted processes could reach a
sibling package tree outside their nominal project roots. Those semantic outputs are
retained for audit but excluded from v0.5 comparison evidence.

v0.5 replaces the controller rather than adding another path-string exception. Its
atomic unit is one case/repeat triplet:

1. generate one fresh output for each of the three frozen arms;
2. require a passing native filesystem-isolation receipt for every semantic process;
3. obtain two blinded, isolated judge records for each output;
4. write one hash-chained batch commit; and
5. only then advance to the next case/repeat triplet.

There are 75 planned batches: 225 generation outputs and 450 judge records. The first
five batches are the smoke. If execution stops inside a batch, all artifacts from that
batch remain inspectable but do not count; resume must complete the same batch before
advancing. A binary disagreement between the two judges requires William's adjudication
before the next batch.

Filesystem access is enforced by a per-process macOS sandbox profile, not inferred
from command strings. Each profile denies the protected repository and home roots,
reopens only the exact execution inputs and output mailbox needed by that process, and
runs positive plus absolute-path, parent-traversal, and symlink-escape probes. The
profile and probe receipts are bound into each accepted record. Failure blocks the
batch before its commit.

Partial committed results are descriptive only: they may report denominators and means,
but cannot apply the preregistered comparison thresholds or support an architecture
conclusion. Those decision lines are evaluated only after all 75 committed batches.
The visible/startup-session, Codex-only, no-release claim ceiling remains unchanged.

The frozen v0.5 protocol SHA-256 is
`f9bc7232647b02a77c67010a74deff79f205cc99590452c2134c515e252b4336`; its
lock digest is
`8c2d7ddcb1aac478eae31b937afa85a63505d1d4e48f5082781aa6a5c7321713`.
The lock validates the 29 bound dependencies and does not authorize semantic model
execution.

## Frozen comparison

The three immutable arm ids are `stable`, `direct-only`, and `thin-kernel`. Runtime
identity still comes from each sealed arm manifest; the names alone are not evidence.

Under v0.1 and v0.2, the matched workload contains 29 cases from the accepted matrix. The two real-task
replays remain excluded because no replay consent has been authorized. Four sealed
shadow receipts remain conditional on independent case-custodian binding and blindness
attestation before #119 authorization. Visible public and development cases are never
reported as blind evidence.

Under v0.1, both Codex and Claude package surfaces and all five entry modes are required strata.
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
authority. A budget below the workload frozen in the selected protocol version means
do not start; it does not authorize silently truncating that workload.

No semantic model output was generated while creating or freezing v0.1, v0.2, or v0.3.
The single v0.3 output described above was generated only after its separate execution
authorization validated.
