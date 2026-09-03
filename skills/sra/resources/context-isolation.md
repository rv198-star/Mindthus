# SRA Context Isolation / 上下文隔离运行合同

## Purpose

SRA should make the allocation judgment relatively independently from the context that
created, defended, or prolonged the current work.

Relative independence is not context-free judgment. SRA still needs the current
objective, target threshold, risk floor, user values, authority, candidates, resource
constraints, evidence, and explicit assumptions.

The runtime boundary is:

> Only decision-relevant, classified, provenance-bearing context enters the allocation
> packet. Ambient conversation, previous conclusions, candidate advocacy, current-task
> richness, and sunk-cost narrative do not silently gain evidential authority.

## WAE Assignment

SRA uses a hybrid control shape.

### Workflow owns

- context-kind admission policy;
- admitted / quarantined / excluded ledgers;
- stable candidate IDs and normalized cards;
- deterministic blind aliases and order;
- packet-specific Agent output schemas;
- packet and judgment hashes;
- runtime stage order;
- evidence and assumption reference checks;
- fresh-context carrier artifacts;
- concise decision rendering.

### Agentic owns

- context relevance challenges;
- candidate-surface sufficiency;
- hard-gate and target-feasibility judgment;
- necessity and bundle sufficiency;
- contraction and first break point;
- replenishment and next tranche;
- state-aware adjustment;
- final allocation recommendation.

### Evidence owns

- observable sources;
- claim ceilings;
- explicit assumptions and overturn conditions;
- references used by each load-bearing judgment;
- observable carrier receipts where available.

### Outer caller owns

- raw context and candidate collection;
- execution authority;
- TPlan or project mutation;
- any final human-authority decision.

## Threat Model

The packet boundary reduces:

- active-task capture;
- previous-Agent conclusion reuse;
- candidate advocacy asymmetry;
- recency and input-order effects;
- sunk-cost continuation pressure;
- cross-project historical leakage;
- unsupported factual claims embedded inside value constraints;
- clean but post-hoc completion of a final SRA form.

It cannot prove that the outer caller supplied every relevant fact or candidate.

## Context Admission Kinds

| Kind | Default treatment |
|---|---|
| `current_instruction` | admitted as current authority |
| `user_constraint` | admitted as a value, target, or risk constraint; not factual proof |
| `authority_decision` | admitted inside declared scope and expiry |
| `observed_fact` | admitted inside source and claim ceiling |
| `runtime_evidence` | admitted inside source and claim ceiling |
| `assumption` | admitted as an assumption with overturn condition |
| `historical_context` | quarantined by default; admitted only by explicit scoped admission with evidence/assumption support; no inherited authority |
| `candidate_advocacy` | quarantined as a claim |
| `previous_conclusion` | quarantined as a prior conclusion |
| `ambient_inference` | quarantined unless restated as an explicit assumption |

Historical context uses `requested_disposition: admit` only when the outer caller has
identified current decision relevance and bound it to evidence or an explicit
assumption. Otherwise it remains quarantined.

The ledger preserves excluded items. Nothing disappears silently. At least one
`current_instruction` anchors every applicable run, and current instructions, current
user constraints, and authority decisions cannot be silently excluded by the outer
caller.

Scripts can apply the kind-based policy. They cannot determine that an item was
classified correctly or that admitted evidence is true.

## Candidate Symmetry

Every candidate uses the same card:

```text
candidate_id
title
objective_contribution
resource_demand
dependency_or_bundle_role
delay_cost_or_opportunity_window
irreversibility_or_downside
evidence_refs
assumption_refs
```

Workflow generates blind aliases from deterministic content ordering. Input order and
current-task position do not control blind ordering.

A large candidate-context imbalance produces a warning. It does not automatically make
the richer or thinner candidate better.

## Isolation Profiles

### `packet_bound`

The current Agent uses only a sealed packet and cites packet IDs. This is logical
isolation. It does not prove the model forgot ambient context.

Use it for ordinary Lite decisions when fresh execution costs more than the reversible
allocation error. If Full or declared contamination pressure exists, an explicit
`packet_bound` override requires a recorded `isolation_override_reason` and remains a
visible degraded-isolation warning.

### `fresh_context`

A fresh, read-only subagent or ephemeral CLI receives the packet and judge contract
without the task conversation.

The generated carrier uses:

- `fork_context: false` for subagent dispatch;
- read-only authority;
- no file, Mission, task, memory, or external-system mutation;
- ephemeral CLI execution;
- ignored project rules and user configuration where the host supports those flags;
- an empty review workspace.

The runtime gives fresh carriers packet-specific output schemas whose constants and
enums bind packet hashes and candidate/evidence/assumption/state IDs. It records the
requested carrier and persists any supplied receipt. A fresh carrier without a receipt
remains a declared claim and produces a warning. A carrier
label or receipt does not prove the absence of hidden host context.

### `blind_then_state`

This is the strongest initial profile.

1. Blind pass: normalized candidates, no original title/ID, no active identity, no
   switching cost, no reusable assets, no remaining cost, no historical spend, and no
   current commitment.
2. State-aware pass: reveal the locked blind result plus current identity, switching
   cost, reusable assets, remaining cost, commitments, authority, and historical spend
   labelled as sunk-cost-only.

When possible, run each pass in a separate fresh context.

The second pass states whether state information changed the blind result and why. Each
state adjustment cites stable `state_id` values of the matching state kind; a changed
result without cited admitted state is blocked.

## Runtime Files

For project-local use, prefer `.sra/<run-id>/`; the repository ignores `.sra/` so
runtime packets and receipts do not enter source control accidentally. An explicit
external or temporary directory is also valid.

A prepared run contains:

```text
run.json
raw-input.json
context-admission.json
sealed-packet.json
blind-packet.json
blind-agent-prompt.md
blind-output-schema.json
blind-subagent-dispatch.json
blind-codex-command.sh
fresh-context-workspace/
trace.jsonl
```

After blind judgment:

```text
judgments/blind.json
state-packet.json
state-aware-agent-prompt.md
state-aware-output-schema.json
state-aware-subagent-dispatch.json
state-aware-codex-command.sh
fresh-context-workspace-state/
```

After state-aware reconciliation:

```text
judgments/state-aware.json
final-decision.json
```

## State Machine

```text
prepared -> blind_recorded -> finalized
```

A later stage cannot be recorded before its predecessor. Recorded judgments are not
overwritten.

## Blind Boundary

The blind packet omits:

- original candidate title and ID;
- active candidate identity;
- switching cost;
- reusable assets;
- remaining cost;
- historical spend;
- current commitments;
- quarantined context statements;
- evidence and assumptions used only by state-aware switching, spend, commitment, or
  authority records.

The blind Agent evaluates every candidate alias, runs contraction, names a current
floor, and proposes a replenishment tranche.

References outside the packet are blocked.

## State-Aware Boundary

The state packet adds only state information relevant to future consequences:

- blind-to-original candidate mapping;
- active candidate identity;
- switching costs;
- reusable assets;
- remaining costs;
- current commitments and authority;
- historical spend explicitly labelled as sunk-cost-only;
- the locked blind judgment and hash.

Every switching-cost, reusable-asset, remaining-cost, commitment, historical-spend, or
authority state item must cite admitted evidence or an explicit assumption before it can
influence reconciliation. A structured state sentence without provenance remains
inadmissible context, not stronger evidence.

The final judgment records:

- whether the result changed;
- state adjustments and evidence/assumption references;
- rejection of sunk cost as a continuation basis;
- current floor and next tranche;
- investment ceiling and authorization horizon;
- maintenance, reserve, defer, and stop lanes;
- reranking triggers and claim ceiling.

## Lite And Full

### Lite

- uses one micro-contraction and one micro-replenishment;
- remains packet-bound even when it uses the current Agent;
- prefers a fresh blind pass when contamination signals are present;
- authorizes one action, one tranche, or one named checkpoint;
- does not require a complete fidelity artifact for ordinary visible output.

### Full

- targets `blind_then_state`;
- persists both judgments and their hashes;
- records a decision lifetime, reserve, and reranking conditions;
- prefers two fresh contexts when available.

The Analysis-Cost Gate remains active. Isolation is a means to improve allocation, not
an excuse for a larger planning ceremony.

## Script Commands

Prepare:

```bash
python3 skills/sra/scripts/prepare_sra_run.py \
  --input skills/sra/templates/context-input.json \
  --dir /tmp/sra-run
```

Record blind Agentic output:

```bash
python3 skills/sra/scripts/record_sra_judgment.py \
  --dir /tmp/sra-run \
  --stage blind \
  --input /tmp/blind-judgment.json \
  --carrier packet_bound
```

Record state-aware output:

```bash
python3 skills/sra/scripts/record_sra_judgment.py \
  --dir /tmp/sra-run \
  --stage state-aware \
  --input /tmp/state-judgment.json \
  --carrier packet_bound
```

Check and render:

```bash
python3 skills/sra/scripts/check_sra_run.py --dir /tmp/sra-run
python3 skills/sra/scripts/render_sra_decision.py --dir /tmp/sra-run
```

Generated `*-subagent-dispatch.json` and `*-codex-command.sh` provide stronger carrier
options when the host supports them.

## Hard Boundaries

- Scripts do not select semantic priority.
- Scripts do not decide that a candidate is necessary or sufficient.
- Scripts do not calculate semantic ROI.
- Scripts do not scrape the full conversation automatically.
- The runtime does not mutate TPlan or project state.
- A packet-bound same-context run cannot claim fresh-context isolation.
- A fresh carrier cannot claim complete absence of hidden host context.
- Context isolation does not prove complete candidates or correct allocation.
