# SRA Fidelity Contract

This contract supports the first SRA / Scarce Resource Allocation / 稀缺资源优先分配
implementation.

SRA fidelity checks whether a run executed the required allocation moves at the chosen
reasoning depth. It does not validate whether the selected priority, necessity claim,
ROI judgment, or allocation is semantically correct.

Short rule:

> Validate the allocation shape; keep priority quality agentic and evidence-bounded.

## Entry Outcomes

Every SRA artifact uses one `entry_outcome`:

- `direct`: no real resource competition, or direct trial is cheaper than analysis;
- `lite`: one bounded action, tranche, or checkpoint is authorized;
- `full`: bundle-level or major allocation is required;
- `blocked`: a load-bearing target, evidence, authority, candidate, or resource boundary
  is missing.

`direct` and `blocked` are accepted exits. They require a plain-language conclusion and
an explicit `exit_reason`, but they do not require applicable-run judgment moves.

## Analysis-Cost Boundary

The selected depth must remain proportionate to the possible loss from a wrong
allocation. A reversible local trial should stay direct or Lite; bundle-level, major,
fixed-threshold, multi-resource, or irreversible decisions may justify Full. The
validator can check the recorded `mode_boundary` move, but it cannot determine whether
the chosen depth was substantively correct.

## Applicable Output Shape

Applicable Lite and Full artifacts require:

- `schema_version`: `sra-fidelity-v0.1`;
- `method`: `SRA`;
- `entry_outcome`: `lite` or `full`;
- `plain_language_conclusion`;
- `allocation_action`;
- `allocation_frame`;
- `required_judgment_moves`.

Allowed `allocation_action` values depend on mode:

- Lite: `continue`, `switch`, `maintain`, `defer`, `stop`, or `reserve`;
- Full: `allocate`, `conditional`, `infeasible`, or `blocked`, matching
  `full_decision.allocation_outcome`.

## Allocation Frame

Applicable artifacts require non-empty fields:

- `parent_objective`
- `target_threshold`
- `time_window`
- `risk_floor`
- `decision_owner`
- `contested_resource`
- `evidence_ceiling`

The validator checks only that these fields are present and non-empty. It cannot prove
that the target, owner, risk floor, or resource boundary is correct.

## Required Judgment Moves

Every applicable run requires these moves:

- `candidate_horizon_probe`
- `priority_order`
- `resource_contention`
- `evidence_bounded_necessity`
- `contraction`
- `replenishment`
- `meaningful_tranche`
- `switching_vs_sunk_cost`
- `authorization_horizon`
- `defer_stop_or_reserve`
- `rerank_trigger`
- `mode_boundary`
- `claim_ceiling`

Full mode additionally requires:

- `minimum_sufficient_bundle`
- `resource_vector`
- `feasibility_and_dominance`
- `reserve_capacity`

For Lite, `contraction` records one bounded micro-contraction and `replenishment` records
one next-tranche comparison from the resulting current floor. For Full, the same moves
expand across candidate bundles and realistic pressure scenarios.

Each move includes:

- `status`: `addressed`, `not_applicable`, `transfer`, or `challenge_premise`;
- `finding`;
- `failure_criteria_response`;
- `evidence_surface`.

A non-empty move remains a shape carrier, not proof that the reasoning is true.

## Lite Decision Carrier

Lite requires `lite_decision` with:

- `considered_candidates`: two to four non-empty candidate or posture labels;
- `current_floor`;
- `next_tranche`;
- `investment_ceiling`;
- `authorization_horizon`;
- `displaced_work` as a list;
- `rerank_trigger`.

Allowed `authorization_horizon` values:

- `one_action`
- `one_tranche`
- `until_named_checkpoint`

Lite fails its method contract when it omits the post-contraction current floor, omits
the replenishment choice, or authorizes an open-ended continuation without a bounded
horizon and reranking trigger.

## Full Decision Carrier

Full requires `full_decision` with:

- `allocation_outcome`: `allocate`, `conditional`, `infeasible`, or `blocked`;
- `allocation_scope`: `problem_portfolio` or `execution_portfolio`;
- `contested_resources` as a non-empty list;
- `dominant_constraint`;
- `candidate_bundles` as a non-empty list of objects carrying a non-empty `bundle_id`
  and `status`: `feasible`, `infeasible`, `dominated`, or `conditional`;
- `contraction_findings` as a list;
- `replenishment_findings` as a list;
- `selected_main_allocation`;
- `necessary_support` as a list;
- `minimum_maintenance` as a list;
- `explicit_defer` as a list;
- `explicit_stop` as a list;
- `reserved_capacity` as an object;
- `next_tranche`;
- `authorization_boundary`;
- `decision_lifetime`;
- `rerank_triggers` as a non-empty list.

The validator does not require every list to be non-empty because a legitimate case may
have no maintenance, defer, stop, or reserve item. It checks required carriers and the
fields whose absence would make the decision unrecoverable.

## Failure Criteria

An applicable run has a shape or evidence risk when:

- the Allocation Frame is incomplete;
- no Candidate Horizon Probe is recorded;
- hard gates and target feasibility are not represented before ROI-style comparison;
- the common contested resource is absent;
- necessity is asserted without an evidence surface or overturn condition;
- the next resource unit is not a bounded meaningful tranche;
- sunk cost and switching cost are not separated;
- Lite omits one bounded micro-contraction, one micro-replenishment, or the resulting
  current floor;
- Lite has no bounded authorization horizon;
- defer, stop, maintenance, or reserve consequences are hidden;
- no reranking trigger is named;
- Full omits minimum sufficient bundle, expanded contraction, expanded replenishment,
  resource vector, feasibility, dominance, or reserve-capacity moves;
- Full lacks a decision lifetime or authorization boundary;
- numeric scoring is presented as semantic proof rather than an evidence-linked support
  surface.

## Routing Boundaries

A complete SRA artifact should transfer or stay direct when another owner controls the
active question:

- 3L5S: problem definition or decomposition;
- EDSP: unstable proposition or structural binary;
- SELA: long-term system efficiency versus local advantage;
- MPG: carrier, exposure, timing, and path posture for one selected mainline;
- WAE: agentic controller mismatch;
- TVG: value gain inside one bounded artifact;
- TPlan: Mission state, Pulse arbitration, continuation, authority, recovery, and
  mutation.

The validator can accept explicit exits. It cannot determine whether the transfer is
semantically correct.

## Context-Isolated Runtime Relationship

The optional hybrid runtime in `context-isolation.md` controls context admission,
candidate normalization, blind/state stage order, hashes, references, carrier records,
and rendering. It does not reduce any required SRA semantic move.

A runtime-integrity pass proves only that the recorded judgment stayed bound to the
sealed packet and declared workflow. It does not prove that the outer caller supplied
complete context, that a fresh host had no hidden context, or that the resulting
priority is correct. A same-context packet-bound judgment must remain labelled logical
isolation; fresh carriers without persisted receipts remain declared but unverified.

## Claim Ceiling

Allowed first-release claim:

> SRA provides lightweight and expanded contracts for making scarce-resource allocation
> explicit, evidence-bounded, and action-changing, with tested routing boundaries.

The contract does not support claims that SRA always finds the correct priority,
maximizes ROI, computes an optimal allocation, or proves real-world business value.

## Script Boundary

`scripts/validate_sra_output.py` emits an `SRA Shape & Evidence Risk Report`.

A shape pass is not semantic approval. The script cannot judge priority quality,
necessity truth, semantic ROI, bundle sufficiency, strongest-alternative quality, or real
allocation correctness.
