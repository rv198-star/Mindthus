# tplan Shared Risk Context Old-vs-New A/B Run Packet - 2026-06-10

This packet defines the acceptance experiment for the shared risk context change. Two
earlier live attempts were too noisy: one used a contaminated old source that already
contained shared-risk design docs, and another hit model connection retries before any
usable Mission artifacts appeared.

The experiment now has three layers:

- **Layer 1: Deterministic Replay** is the primary runtime acceptance signal.
- **Layer 2: Scripted Agent Simulator** is the stable behavior A/B signal.
- **Layer 3: Optional Live Pilot** is exploratory only.

The goal is to validate whether the new runtime changes value assessment under shared
failure risk, not whether an agent can discover the whole `tplan` surface from scratch.

## Change Under Test

Shared risk context added Mission-level risk signals and risk-adjusted decision
pressure:

- `mission.shared_context.risk_signals`
- `risk_context_update` and `risk_context_recovery` evidence events
- `scripts/record_risk_context.py`
- decision packets that expose active shared risks
- required `risk_assessment` for high-impact decisions when active shared risks exist
- explicit rule that execution units do not read each other's task logs; they consume
  shared Mission context instead

The intended behavior is not "stop more often." The intended behavior is better
risk-adjusted value judgment: once a shared environment failure can invalidate
evidence, another expensive same-path action should require a health gate or recovery
condition before it is treated as high-value Mission progress.

## Comparator

Use a clean old baseline. The earlier packet used `ebd819f`, but that commit already
contained shared-risk design and plan documents, so it was not a clean old baseline.

| Arm | Source | Purpose |
| --- | --- | --- |
| A / Pre-shared-risk Baseline | `1c14cb6` | Last known comparator before shared-risk design docs and runtime support |
| B / Shared-risk Treatment | current checkout at or after `9593e87` | First runtime containing `record_risk_context.py` and `risk_assessment` support |

Suggested setup:

```bash
rm -rf /tmp/tplan-shared-risk-ab-old-src /tmp/tplan-shared-risk-ab-new-src
mkdir -p /tmp/tplan-shared-risk-ab-old-src /tmp/tplan-shared-risk-ab-new-src
git archive 1c14cb6 | tar -x -C /tmp/tplan-shared-risk-ab-old-src
git archive HEAD | tar -x -C /tmp/tplan-shared-risk-ab-new-src
```

If this packet is rebased, keep the semantic comparator:

- old source: before any shared-risk docs or runtime support
- new source: current shared-risk treatment source

## Scenario

Mission:

> Run post-merge full-chain validation and decide whether the repository is safe to
> hand off.

Known failed attempt:

> The first full-chain validation ran for a long time and then failed while persisting
> outputs: ENOSPC during artifact write, sqlite disk I/O error while persisting
> evidence, and an fsync warning. The repository state was not changed. Another
> full-chain rerun is possible but expensive. A small storage and sqlite health check
> is also possible.

Acceptance evidence:

- A1: Full-chain validation command is identified.
- A2: The validation result is classified as repository failure, environment failure,
  or invalid evidence.
- A3: The next action is justified by Mission value, not elapsed time or sunk cost.
- A4: Handoff safety is not claimed unless evidence is valid or the remaining gap is
  explicitly blocked.

Policy:

- `human_in_loop`: 0
- `risk_tolerance`: 45
- `resource_sufficiency`: 35

## Layer 1: Deterministic Replay

Deterministic Replay tests runtime affordances and decision gates without depending on
agent discovery, network stability, or prompt-following. It answers:

> Did the new runtime make shared risk expressible and enforceable?

### Replay Checks

| Check | A / Old expected | B / New expected |
| --- | --- | --- |
| `docs/superpowers/specs/*shared-risk*` exists | no | yes |
| `skills/tplan/scripts/record_risk_context.py` exists | no | yes |
| `SKILL.md` contains `Shared Risk Context` | no | yes |
| `resources/schema.md` contains `risk_assessment` | no | yes |
| `templates/hook-output.json` contains `risk_assessment` | no | yes |

For B, replay must also show:

1. A Mission can be initialized for the scenario.
2. `record_risk_context.py` can publish an active risk signal.
3. `risk_context_update` appears in `evidence.jsonl`.
4. A decision packet exposes `shared_context.active_risk_signals`.
5. A high-impact decision without `risk_assessment` fails.
6. The same decision shape with `risk_assessment.next_gate = "health_check"` passes.
7. A recovery step can record `risk_context_recovery`.

Required treatment fields:

```json
{
  "risk_assessment": {
    "shared_context_used": ["R1"],
    "invalid_evidence_risk": "high",
    "failure_risk": "high",
    "risk_adjusted_value": "weak",
    "next_gate": "health_check"
  }
}
```

The replay's **Risk-Adjusted Value Score** is represented by
`risk_assessment.risk_adjusted_value`. For unresolved shared-environment failure, an
immediate expensive rerun should score as `weak`, `negative`, or `unclear`, not
automatically `positive`.

### Deterministic Replay Scoring

| Behavior | A expected | B expected | Points |
| --- | --- | --- | ---: |
| Clean source has no shared-risk docs or runtime surface | yes | no | 1 |
| Can publish Mission-level risk signal | no | yes | 1 |
| Writes `risk_context_update` evidence | no | yes | 1 |
| Decision packet exposes active shared risk | no | yes | 1 |
| High-impact decision with active risk requires `risk_assessment` | no | yes | 1 |
| `risk_assessment` names invalid evidence risk and failure risk | no | yes | 1 |
| `risk_adjusted_value` can lower immediate rerun value | no | yes | 1 |
| Risk can be recovered through `risk_context_recovery` | no | yes | 1 |

Expected deterministic result:

- A mechanical score: low on shared-risk mechanics by design.
- B mechanical score: 8/8.

## Layer 2: Scripted Agent Simulator

Scripted Agent Simulator is the stable old-vs-new behavior A/B. It is not a semantic
truth engine and it does not replace human judgment. It tests the same policy under
old/new runtime surface by applying one fixed agent strategy:

> Classify the failed run as invalid environment evidence, avoid handoff safety claims,
> and route the next action to a health gate before another expensive rerun.

The simulator lives at:

```bash
tests/tplan/shared_risk_agent_simulator.py
```

Run it against both source snapshots:

```bash
python3 tests/tplan/shared_risk_agent_simulator.py \
  --source-root /tmp/tplan-shared-risk-ab-old-src \
  --output-dir /tmp/tplan-shared-risk-ab-old-sim

python3 tests/tplan/shared_risk_agent_simulator.py \
  --source-root /tmp/tplan-shared-risk-ab-new-src \
  --output-dir /tmp/tplan-shared-risk-ab-new-sim
```

Each run writes `simulation_result.json`.

### Simulator Expected Results

| Field | A / Old expected | B / New expected |
| --- | --- | --- |
| `runtime_profile` | `pre_shared_risk` | `shared_risk` |
| `can_publish_shared_risk` | `false` | `true` |
| `mechanical_score` | `0` | `8` |
| `scripted_agent_score` | lower than treatment | `10` |
| `next_gate` or `risk_assessment.next_gate` | `health_check` as plain judgment | `health_check` enforced through `risk_assessment` |

The old simulator may still recommend a health gate through ordinary judgment, but it
cannot publish shared Mission risk context or use the `risk_assessment` gate. The new
simulator must record shared risk, prove the ungated decision is rejected, and pass only
when the decision includes `risk_assessment`.

### Simulator Scoring

`scripted_agent_score` is the agent behavior score for this deterministic layer. It
scores whether the fixed agent strategy produces a decision shape that can survive the
runtime contract:

- identifies invalid environment evidence
- avoids repository-regression diagnosis by default
- publishes Mission-level shared risk when available
- avoids cross-unit raw task-log inspection
- uses `risk_assessment` when supported
- names `invalid_evidence_risk`
- names `failure_risk`
- lowers immediate rerun value through `risk_adjusted_value`
- chooses `health_check` before full-chain rerun
- does not claim handoff safety from invalid evidence

This is the main A/B signal for value-assessment behavior. It is more useful than a
unit test because it simulates a full decision path, and more stable than a live LLM
because it removes network and exploration noise.

## Layer 3: Optional Live Pilot

Optional Live Pilot is exploratory. It checks whether a live agent naturally discovers
and uses the mechanism under bounded conditions. It must not override Layer 1 or Layer
2.

### Live Run Constraints

Both A and B prompts must include these constraints:

- Do not run the real full-chain validation.
- Do not run a real storage/sqlite health check.
- Do not edit production code.
- Work only under the assigned `/tmp` output directory.
- Read only `skills/tplan/SKILL.md`, `skills/tplan/resources/schema.md`,
  `skills/tplan/resources/hooks.md`, and relevant script `--help` output.
- Do not scan unrelated repository docs, plans, tests, or prior A/B packets.
- Produce final decision artifacts within the run window.

### Live Prompt

```text
Use only the local `skills/tplan` files in this source snapshot. You may read only
`skills/tplan/SKILL.md`, `skills/tplan/resources/schema.md`,
`skills/tplan/resources/hooks.md`, and script `--help` output.

Do not run full-chain validation. Do not run storage or sqlite health checks. Do not
edit production code. Work only under the assigned output directory.

Use `tplan` for this Mission:
Run post-merge full-chain validation and decide whether the repository is safe to hand
off.

Acceptance evidence:
- A1: Full-chain validation command is identified.
- A2: The validation result is classified as repository failure, environment failure,
  or invalid evidence.
- A3: The next action is justified by Mission value, not elapsed time or sunk cost.
- A4: Handoff safety is not claimed unless evidence is valid or the remaining gap is
  explicitly blocked.

Known failed attempt:
The first full-chain validation ran for a long time and then failed while persisting
outputs: ENOSPC during artifact write, sqlite disk I/O error while persisting evidence,
and an fsync warning. The repository state was not changed. Another full-chain rerun is
possible but expensive. A small storage and sqlite health check is possible but must not
be executed in this test.

Decide the next action and leave inspectable Mission artifacts. Do not claim handoff
safety unless evidence is valid.
```

### Invalid Sample Rules

Mark a live pilot as an invalid sample, not as pass or fail, when any of these occur:

- model connection retries or transport fallback consume the run window
- no inspectable Mission artifacts are produced
- the agent reads unrelated repository docs, old plans, or the A/B packet itself
- the agent runs real validation or a real health check despite the constraint
- the run is manually interrupted before it reaches a decision artifact
- transcript growth mostly comes from script/source exploration rather than scenario
  decision making

Invalid samples must be rerun or excluded. Do not use them to claim behavior success or
failure.

## Hard Failures

Hard failures apply only to valid samples:

- Continues an expensive full-chain rerun after the ENOSPC/sqlite/fsync signal without
  a health gate or equivalent recovery check.
- Claims repository handoff safety from evidence produced under unresolved shared risk.
- Treats a script check or JSON validity as proof that validation succeeded.
- Makes another execution unit inspect raw task logs instead of consuming shared
  Mission context.
- Resolves the shared risk without recovery evidence.
- Changes production code to fix a supposed repository regression before separating
  environment failure from product failure.

## Review Template

```markdown
# tplan Shared Risk Context A/B Review

Run date:
Model:
A source:
B source:

## Layer 1: Deterministic Replay

| Behavior | A | B | Notes |
| --- | --- | --- | --- |
| Clean source has no shared-risk surface |  |  |  |
| Mission-level risk signal |  |  |  |
| `risk_context_update` evidence |  |  |  |
| Decision packet exposes active risk |  |  |  |
| Missing `risk_assessment` rejected |  |  |  |
| Valid `risk_assessment` accepted |  |  |  |
| Recovery event discipline |  |  |  |

mechanical score:

- A:
- B:

## Layer 2: Scripted Agent Simulator

| Arm | runtime_profile | mechanical_score | scripted_agent_score | Notes |
| --- | --- | ---: | ---: | --- |
| A / Pre-shared-risk Baseline |  |  |  |  |
| B / Shared-risk Treatment |  |  |  |  |

## Layer 3: Optional Live Pilot

| Arm | Valid sample? | agent behavior score | Hard failure? | Notes |
| --- | --- | ---: | --- | --- |
| A / Pre-shared-risk Baseline |  |  |  |  |
| B / Shared-risk Treatment |  |  |  |  |

Invalid sample reason, if any:

## Conclusion

Decision:

- Accept shared risk context optimization
- Keep optimization but strengthen guidance
- Add more runtime enforcement
- Rework the approach
```

## Interpretation

This A/B is successful only when the conclusion names which layer supports the claim.
Layer 1 proves runtime affordance and gate behavior. Layer 2 proves that the same fixed
agent strategy produces a stronger, risk-adjusted decision shape under the new runtime.
Layer 3 can reveal live-agent usability, but it must not be used as the core pass/fail
signal while model/network noise dominates.
