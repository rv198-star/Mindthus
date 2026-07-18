# Mindthus 2.0 Beta — Codex route-decision evaluation v0.6

Status: design candidate; zero semantic calls are authorized by this document.

## Core

This experiment answers one bounded product question:

> On visible Codex / `gpt-5.6-sol` / `xhigh` workloads, does the Thin Kernel add
> action-changing passive recall over direct owner discovery while preserving Stable
> quality and producing a material reduction in at least one user-cost dimension?

The result is binary for this Beta route: `route-supported` or `route-rejected`.
`experiment-invalid` is reserved for infrastructure failure and is never counted as
product evidence. This is an exploratory continuation decision, not release proof,
hidden-set proof, cross-host proof, or a claim that the architecture is universally
valid or invalid.

## Mainline

### Workload

Eight visible cases are fixed before execution and repeated three times. One matched
batch is one case/repeat triplet containing Stable, Direct-only, and Thin-kernel.

| Bucket | Cases | Cells per arm |
| --- | --- | ---: |
| Kernel benefit | `b2-public-frame`, `b2-public-whole`, `b2-public-anti-spiral`, `b2-dev-multi-primitive` | 12 |
| Routing integrity | `b2-dev-owner-wae`, `b2-dev-arbitrator-overlap` | 6 |
| Stay asleep | `b2-dev-near-normal-debugging`, `b2-dev-near-sufficient-evidence` | 6 |

The first repeat of `b2-public-frame`, `b2-dev-multi-primitive`, and
`b2-dev-near-normal-debugging` is the infrastructure pilot. Those three commits count
toward the final 24; they are not regenerated. The pilot gate inspects only artifact,
schema, isolation, blinding, budget, and resume integrity. It does not select the route
from early semantic scores.

### Calls and judging

Each batch runs three isolated Generators. The three original answers are preserved.
Each Judge receives one content-addressed payload containing the same three opaque
candidate views in a slot-specific deterministic shuffle. Arm names, namespaces,
paths, telemetry, execution order, and package diagnostics are absent. Owner names
needed to score routing remain visible.

Two isolated Judge sessions independently score every candidate inside that one
payload. Therefore the full decision surface requires 72 successful Generator outputs
and 48 successful Judge calls, instead of 144 Judge calls under per-output judging.
Binary disagreements are recorded as each batch commits, but they do not control
independent downstream batches. After all 24 commits, William receives one accumulated
adjudication round bound to the individual disagreement packets; the final decision
waits for complete resolutions.

### Decision gates

`route-supported` requires every gate below:

1. **Kernel benefit:** across the 12 passive-obligation pairs, Thin joint
   owner-plus-primitive success is at least 9/12 and exceeds Direct-only by at least
   three successes.
2. **Stable preservation:** across all 24 matched units, Thin mean normalized quality
   is no more than `0.05` below Stable and Thin owner-success rate is no more than one
   cell below Stable.
3. **Routing integrity:** Thin succeeds on owner/action behavior in at least 5/6
   routing-integrity cells.
4. **Stay asleep:** Thin has at most one false wakeup across six negative-control cells
   and no more than one additional false wakeup versus Stable.
5. **Authority and evidence:** Thin has zero adjudicated authority/evidence
   regressions.
6. **Material cost value:** Thin improves at least one of the following versus Stable:
   median input tokens by at least 10%, median wall time by at least 10%, or total
   observable Generator skill hops by at least 25%. Skill hops are an explicit burden
   proxy; the runtime does not claim to observe the semantic owner-transition instant.
7. **Cost guardrails:** Thin/Stable median input-token ratio is at most `1.08`,
   Thin/Stable median wall-time ratio is at most `1.10`, and Thin/Direct-only median
   input-token ratio is at most `1.08`.

If the experiment is valid and any gate fails, the result is `route-rejected`; the
report names every failed gate. Rejection means the current Thin-Kernel Beta route did
not meet its burden of proof on this frozen Codex surface. It is not a universal theorem
about all possible future kernels.

### Controller assignment

- Workflow owns order, immutable identities, native isolation, atomic writes, ledger
  reconstruction, budgets, schema validation, and deterministic calculations.
- Generator owns the user-facing answer; workflow must not rewrite it.
- Judge owns blinded semantic scoring under the frozen rubric.
- William owns only disputed binary axes and stop authority.
- Evidence owns the claim ceiling: a product decision exists only after all 24 valid
  commits and all decision denominators are complete.

The authoritative state is reconstructed from final attempt records and the
hash-chained batch ledger on every start. `run-state.json` is a disposable projection,
not a frozen source snapshot. A finalized attempt without its next derived record is
promoted without another model call. Human adjudication changes analysis state, not
the prior usage baseline.

## Guardrails

These guardrails protect the mainline from known v0.3–v0.5 failures; they do not create
new judgment centers.

- Wall time is the required latency/cost surface. Runner-observed first action and
  host-native first-useful-action timing are retained when available, but either may
  remain unknown and neither can veto the product experiment.
- The OpenAI-compatible paired-Judge schema is used from the first call. A stricter
  local validator checks candidate cardinality, uniqueness, expected primitive ids,
  and nullability.
- Candidate blinding and namespace removal are native v0.6 behavior, not amendments.
  Exact sensitive-path exposure remains terminal `experiment-invalid`.
- The Generator wrapper names no plugin, method, skill, arm, or competing framework.
  It contains only answer-language, brevity, and evaluation-resource isolation rules;
  routing pressure must come from the actual arm and the user case.
- A resource-unreadable statement is scored as an authority/evidence regression unless
  the retained runtime trace contains an observed read failure. The evaluator does not
  insert a prompt rule that hides this product behavior.
- Process interruption and post-adjudication resume must pass zero-model fault
  injection before freeze. The rehearsal must reuse finalized attempts and must not
  compare current usage with a pre-run snapshot.
- One explicit infrastructure retry is permitted only when the failed attempt contains
  no semantic output and complete zero-token evidence. Any other infrastructure defect
  returns `experiment-invalid`; v0.6 receives no compatibility amendment.
- Pilot completion automatically opens the remaining frozen batches because the gate
  is mechanical. Pilot scores cannot change cases, thresholds, prompts, or workload.

## Boundary

- Previous v0.3–v0.5 outputs remain audit history and are excluded from v0.6
  denominators.
- Previous authorizations do not transfer.
- No semantic call may start until the protocol, arm set, paired-Judge schema, zero-model
  rehearsal, model roles, call ceilings, token ceiling, adjudicator, and stop authority
  are bound by a fresh authorization digest.
- The proposed execution ceiling is 74 Generator calls, 50 paired-Judge calls, and
  4,000,000 counted input + output + reasoning tokens. Each call is additionally bound
  to a 131,072-token context ceiling, and the runner reserves that full amount before
  starting a call. Codex exposes aggregate multi-turn usage only after an in-flight
  process completes, so token enforcement has one-call measurement latency: the runner
  rejects a per-call overage and starts no further call after the aggregate ceiling,
  but cannot preempt a running process at an exact token. Successful evidence is capped
  at 72 Generator outputs and 48 Judge records; headroom cannot expand the evidence set.
- Generator and both Judges use `gpt-5.6-sol` / `xhigh`; same-model blind review is an
  explicit limitation.
- No publication, release preparation, Stable migration, Claude claim, hidden-set
  claim, or cross-host claim is authorized.

## Runtime support

v0.6 intentionally has one deterministic core, one semantic runner, one paired-Judge
schema/rubric, one protocol/lock pair, one authorization packet, and one focused test
module. It must not grow an amendment wrapper chain.
