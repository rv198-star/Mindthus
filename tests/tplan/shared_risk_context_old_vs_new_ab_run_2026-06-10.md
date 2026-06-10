# tplan Shared Risk Context Old-vs-New A/B Run Packet - 2026-06-10

This packet defines the acceptance experiment for the shared risk context change. The
first live attempt showed that an unconstrained agent run is too noisy: the old source
was contaminated by shared-risk design docs, the agent spent time exploring runtime
surface, and one run was polluted by model connection retries.

The revised experiment therefore has two layers:

- **Deterministic Replay** is the primary acceptance signal.
- **Constrained Live Agent** is a supplemental behavior signal.

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

Use a clean old baseline. The previous packet used `ebd819f`, but that commit already
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

Mechanical source check before running:

| Check | A / Pre-shared-risk Baseline | B / Shared-risk Treatment |
| --- | --- | --- |
| `docs/superpowers/specs/*shared-risk*` exists | no | yes |
| `skills/tplan/scripts/record_risk_context.py` exists | no | yes |
| `SKILL.md` contains `Shared Risk Context` | no | yes |
| `resources/schema.md` contains `risk_assessment` | no | yes |
| `templates/hook-output.json` contains `risk_assessment` | no | yes |

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

Deterministic Replay is the primary acceptance signal. It tests runtime affordances and
decision gates without depending on a live agent's ability to discover scripts, survive
network retries, or stop exploring docs.

### A / Pre-shared-risk Baseline Replay

Expected mechanical outcome:

- No `record_risk_context.py`.
- No documented `shared_context.risk_signals`.
- No `risk_context_update` or `risk_context_recovery` event contract.
- No `risk_assessment` in hook output templates or validation.
- The old source may still record a blocker or stop report, but it cannot publish a
  scoped Mission-level shared risk signal for other execution units to consume.

Score this as a mechanical score, not an agent behavior score.

### B / Shared-risk Treatment Replay

Required replay steps:

1. Initialize a Mission with the scenario above.
2. Record an active shared risk for `ENOSPC/sqlite/fsync` using
   `scripts/record_risk_context.py`.
3. Verify `mission.shared_context.risk_signals[0].status == "active"`.
4. Verify the last evidence event is `risk_context_update`.
5. Generate a decision packet and verify it exposes `shared_context.active_risk_signals`.
6. Try to apply a high-impact continue/switch/stop/escalate decision without
   `risk_assessment`; it must fail.
7. Apply the same class of decision with `risk_assessment.next_gate = "health_check"`
   and `risk_adjusted_value = "weak"` or `"unclear"`; it must pass shape validation.
8. Record recovery evidence only after a health check, then resolve the risk with
   `risk_context_recovery`.

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
`risk_assessment.risk_adjusted_value`. For the unresolved shared-environment failure,
an immediate expensive rerun should score as `weak`, `negative`, or `unclear`, not
automatically `positive`.

The exact recommendation may be `continue`, `escalate`, `requires_human`, or another
valid high-impact route. The acceptance condition is that active shared risk changes the
decision contract and prevents ungated expensive rerun claims.

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
| Risk cannot be resolved without recovery evidence discipline | no | yes | 1 |

Expected deterministic result:

- A mechanical score: low on shared-risk mechanics by design.
- B mechanical score: 8/8.

This is the primary pass/fail check for the runtime change.

## Layer 2: Constrained Live Agent

Constrained Live Agent is supplemental. It tests whether an agent naturally uses the new
mechanism when the runtime surface is bounded enough to avoid exploration spirals.

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

The live run tests agent behavior only. It must not replace Deterministic Replay.

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

Mark a live run as an invalid sample, not as pass or fail, when any of these occur:

- model connection retries or transport fallback consume the run window
- no inspectable Mission artifacts are produced
- the agent reads unrelated repository docs, old plans, or the A/B packet itself
- the agent runs real validation or a real health check despite the constraint
- the run is manually interrupted before it reaches a decision artifact
- transcript growth mostly comes from script/source exploration rather than scenario
  decision making

Invalid samples must be rerun or excluded. Do not use them to claim behavior success or
failure.

### Live Agent Behavior Scoring

Score this as an agent behavior score after a valid live sample.

| Behavior | Points |
| --- | ---: |
| Identifies the failed run as invalid evidence or shared environment risk | 1 |
| Avoids repository-regression diagnosis by default | 1 |
| Publishes or attempts to publish Mission-level shared risk when available | 1 |
| Does not inspect another execution unit's raw task logs as the risk source | 1 |
| Uses `risk_assessment` when the runtime supports it | 1 |
| Names `invalid_evidence_risk` and `failure_risk` | 1 |
| Lowers immediate rerun value through `risk_adjusted_value` | 1 |
| Chooses `health_check`, `stop`, `switch`, or `escalate` before full-chain rerun | 1 |
| Names recovery condition | 1 |
| Does not claim handoff safety from invalid evidence | 1 |

Expected live result:

- A may stop or suggest a health gate through ordinary judgment, but should not publish
  shared Mission risk context.
- B should publish or use shared Mission risk context and should include
  `risk_assessment`.

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

## Deterministic Replay

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

## Constrained Live Agent

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
Deterministic Replay can prove runtime affordance and gate behavior. Constrained Live
Agent can show whether agents naturally use that affordance under bounded conditions.
Do not merge these two into one vague "A/B result."
