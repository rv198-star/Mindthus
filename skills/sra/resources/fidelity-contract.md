# SRA Fidelity Contract

This contract defines the required judgment moves and structured trace for SRA.

SRA fidelity asks whether the run executed the contraction–replenishment method. It does
not prove that the target is correct, a bundle is truly feasible, the selected tranche
has the highest real value, or the allocation will maximize ROI.

Short rule:

> Contract to discover the current floor; replenish to choose the next tranche.

## Applicability

Use `applicability: applicable` only when multiple valid candidates or postures compete
for a shared scarce resource and the judgment changes allocation behavior.

Use a normal Fidelity exit when:

- `not_applicable`: one clear action exists, resources are independent, or trying the
  reversible option is cheaper than analysis;
- `transfer`: candidate definition, structural truth, direction, carrier strategy,
  controller ownership, artifact-internal strengthening, or Mission runtime is the
  actual judgment owner;
- `challenge_premise`: the claimed competition, target, or resource boundary is
  malformed.

A direct-execution result should normally use `not_applicable` with a plain-language
`exit_reason` rather than pretending that SRA ran.

## Required Top-Level Fields

For an applicable run:

- `schema_version`: `sra-fidelity-v0.1`
- `method`: `SRA`
- `applicability`: `applicable`
- `plain_language_conclusion`
- `action_posture`: `allocate`, `conditional`, `infeasible`, `blocked`, or `unclear`
- `required_judgment_moves`
- `allocation_trace`

## Required Judgment Moves

Each move must contain `status`, `finding`, `failure_criteria_response`, and
`evidence_surface`.

Required moves:

- `allocation_frame`
- `candidate_horizon`
- `bundle_hypotheses`
- `contraction`
- `floor_bundle_selection`
- `replenishment`
- `allocation_lanes`
- `authorization_and_rerank`
- `evidence_boundary`

## Structured Allocation Trace

`allocation_trace` is review support. Its shape protects the canonical sequence without
computing the semantic answer.

Required fields:

```text
outcome
allocation_frame
candidate_horizon
bundle_hypotheses
contraction
qualification_and_selection
replenishment
allocation_lanes
investment_ceiling
authorization_horizon
evidence_ceiling
reranking_triggers
```

### Allocation Frame

Required non-empty values:

```text
parent_objective
target_threshold
time_window
risk_floor
decision_owner
contested_resources[]
```

### Candidate Horizon

For an applicable run, `candidate_horizon` contains at least two candidates or
continuation postures at comparable granularity.

Each candidate must be an object with:

```text
candidate_id
objective_contribution
resource_demand_vector
```

Additional evidence, dependency, delay-window, and downside fields are recommended.

### Bundle Hypotheses

`bundle_hypotheses` contains target-reaching hypotheses. Before contraction they must not
be labelled as already-proven minimum bundles.

### Contraction

Required fields:

```text
target_held_constant: true
floor_bundle_basis: "post_contraction"
tested_changes[]
floor_bundle[]
first_break_point
```

For `infeasible`, `floor_bundle` may be empty only when `infeasibility_reason` is a
non-empty string.

The validator checks that contraction is represented and that the floor bundle is
explicitly based on post-contraction discovery. It does not decide whether the tested
changes were sufficient or whether the break point is true.

### Qualification And Selection

Required non-empty fields:

```text
qualification_result
selection_reason
```

This section may record dependency, bottleneck, dominance, parallelism, or conditional
findings. It must not claim that one universal numeric score settled all logical layers.

### Replenishment

Required fields:

```text
status: "selected" | "conditional" | "not_available"
options_considered[]
selected_next_tranche
selection_reason
```

Every applicable run includes a replenishment result. An `infeasible` or `blocked` run
may use `not_available`, but it must explain why no next tranche can be selected under
the current frame.

### Allocation Lanes

Required list fields:

```text
main_allocation[]
necessary_support[]
maintenance[]
reserve[]
defer[]
stop[]
```

Empty lists are allowed when a lane is not used. For `allocate` and `conditional`,
`main_allocation` must be non-empty.

### Authorization And Rerank

The trace must name:

- a non-empty `investment_ceiling`;
- a non-empty `authorization_horizon`;
- a non-empty `evidence_ceiling`;
- one or more `reranking_triggers`.

## Root-Cause Regression Rules

The following shapes are fidelity failures:

1. an applicable output has no contraction section;
2. an applicable output has no replenishment section;
3. `floor_bundle_basis` says or implies that the minimum was declared before
   contraction;
4. `target_held_constant` is missing or false;
5. the output recreates the former mixed seven-step `Priority Order` as a required
   universal ladder;
6. candidate granularity is represented only by task row count;
7. a shape pass is reported as semantic priority or ROI approval.

The validator can enforce items 1–4 and required shape surfaces. Items 5–7 require
contract tests and review because they involve meaning and claims.

## Script Boundary

`scripts/validate_sra_output.py` emits an `SRA Shape & Evidence Risk Report`.

A passing report means only that required fields, enums, and canonical sequence markers
are present. Agentic or human review remains required for target validity, necessity,
feasibility, value, risk, and allocation quality.
