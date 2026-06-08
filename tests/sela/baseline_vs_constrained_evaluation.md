# SELA Baseline vs Constrained Evaluation Packet

Purpose: define a reproducible loop for comparing baseline prompt and constrained
prompt behavior under the SELA Judge Rubric.

This packet does not claim cross-model robustness. It contains one external measured
seed from the fork review and two single-agent seed run records to exercise the loop.
The follow-up cross-model record lives at
`tests/sela/cross_model_baseline_2026-06-08.md`.

## Shared Inputs

baseline prompt:

```text
Use SELA to analyze the scenario and give a recommendation.
```

constrained prompt:

```text
Use SELA. First answer the required judgment moves: fair comparison, local advantage
scalability, system efficiency trajectory, hard boundary, timing action posture, and
misuse challenge. Do not jump from long-term trend to immediate action. If SELA is not
the dominant method, reject or transfer it.
```

## Records

### Case 1: soy sauce

Record type: external measured seed.

Scenario source: `tests/sela/fidelity_casebook.md`, Case 1.

Baseline score: `8 / 12`

Constrained score: `12 / 12`

failure example:

- Baseline mentioned that immediate cutover was risky, but did not fully identify the
  user's SELA misuse.
- Baseline blurred `HOLD + TRIAL -> COMMIT` into a mixed answer instead of making the
  action posture exclusion clear.

Reviewer note: treatment improved exactly where the method needs active push: D3
system trajectory, D5 action posture, and D6 misuse challenge.

### Case 2: software security review

Record type: single-agent seed run.

Scenario source: `tests/sela/fidelity_casebook.md`, Case 2.

Baseline score: `7 / 12`

Constrained score: `11 / 12`

failure example:

- Baseline over-rewarded scanner coverage and did not clearly protect expert review
  for high-risk architecture.
- Baseline named "use both" but did not define escalation triggers.

Reviewer note: constrained output should keep automated scanning as system mainline for
routine coverage while preserving expert control for critical architecture and scanner
blind spots.

### Case 3: adaptive tutoring

Record type: single-agent seed run.

Scenario source: `tests/sela/fidelity_casebook.md`, Case 3.

Baseline score: `8 / 12`

Constrained score: `11 / 12`

failure example:

- Baseline accepted district-level scale too easily and under-specified student cohort
  boundaries.
- Baseline did not name safeguarding and special-needs support as hard-boundary checks.

Reviewer note: constrained output should segment routine practice from intervention
support and choose cohort-based rollout rather than universal replacement.

## Run Procedure

1. Select a case from the SELA Fidelity Casebook.
2. Run baseline prompt and constrained prompt with the same model and temperature.
3. Run `scripts/validate_sela_output.py` only for constrained structured artifacts.
4. Judge both outputs with `skills/sela/rubrics/judge.md`.
5. Record model, date, prompt, scores, failure example, and limitations.
6. Do not generalize beyond the actual model/run count.

## Limitations

- The single-agent seed run records are calibration fixtures, not independent proof.
- This packet does not claim cross-model robustness.
- Higher score means stronger faithful SELA execution, not guaranteed strategic truth.
