# MPG Scalar Commitment Unpack SubAgent Review 2026-07-06

Issue: #82 `Add MPG scalar-to-vector unpack primitive`

This is a human review note for real-output SubAgent tests. It is not a pytest
shape check and not semantic proof. It records whether the current implementation
actually changed visible answers in fresh-agent style runs. This run sampled the
casebook; it did not execute every manual review case.

## Implementation Under Review

- `mpg_scalar_commitment_unpack` registered as a `before-route` support primitive.
- `using-mindthus` wake-up line names `MPG-unpack:scalar-commitment`.
- `shared-primitives.md` defines the abstract trigger, latent vector, route states,
  visible behavior, and boundaries.
- `fidelity-contract.md` records the support-only MPG routing move.

Verification before SubAgent review:

- `python3 -m pytest -q`
- Result: `485 passed, 35 subtests passed`
- `skills/using-mindthus/SKILL.md`: `923` words, `10240` bytes

## SubAgent Runs

### Positive MPG-Unpack Cases

SubAgent: `019f332c-b208-7243-88a1-5fab37d74987`

Cases: P1, P4, P5 from `scalar_commitment_unpack_manual_review_cases.md`.
P2 and P3 remain covered by the casebook but were not re-run in this review.

Review:

- P1 scored 5/5. It separated `AI long-term mainline` from `OrionAI equity carrier`,
  named valuation/drawdown/competition/narrative volatility, treated liquid savings as
  exposure, and returned `needs_one_clarification` instead of direct investment advice.
- P4 scored 5/5. It separated `open-source model progress` from the current internal
  platform carrier, named budget, delivery delay, hosted API pricing, and team trust as
  path/exposure constraints, and returned `mpg_ready`.
- P5 scored 5/5. It separated `developer tools long-term value` from the specific
  open-source project carrier, named weekend time, paid-work decline, reputation, and
  emotional energy as exposure, and returned `mpg_ready`.

Sampled positive average: `5.0 / 5`.

Residual risks:

- P1 remains financial-advice-sensitive; future answers must keep Evidence / Claim
  Ceiling visible and avoid actionable investment certainty.
- P5 may need one target-function clarification if the user's real goal is emotional
  duty, community reputation, or income recovery rather than project strategy.

### Boundary And Conflict Cases

SubAgent: `019f332c-cf1d-7910-a492-76dad2c4bf29`

Cases: S3, S4, C2, C3 from `scalar_commitment_unpack_manual_review_cases.md`.
S1, S2, S5, S6, and C1 remain covered by the casebook but were not re-run in
this review.

Review:

- S3 scored 5/5. It did not treat "AI is the future" as action-ready; it asked for the
  missing carrier and avoided forced MPG.
- S4 scored 5/5. It treated "next Elon Musk" as an evidence gap, not as a mainline
  worthy of path-carrying strategy.
- C2 scored 5/5. It let Decision Context own the purchase decision while using
  long-horizon exposure only as support; it did not turn a camera purchase into a
  generic MPG case.
- C3 scored 5/5. It named the WAE/MPG ambiguity, then selected migration-through-Black
  Friday path risk as the current owner instead of averaging methods.

Sampled boundary/conflict hard failures: `0`.

Residual risks:

- C3 can still drift toward WAE if "release safety controller" becomes the active
  question. That is acceptable only when the prompt truly becomes a controller
  assignment problem; otherwise MPG path-carrying remains the better owner.

## Human Review Verdict

The current #82 implementation passes this sampled manual review:

- Sampled positive cases average >= 4.0: pass.
- Sampled skip/boundary/conflict cases have zero forced-MPG hard failures: pass.
- Sampled conflict cases name ambiguity and avoid method averaging: pass.
- Two independent SubAgents produced visible answers for human review: pass.

This does not prove general semantic reliability or full-case pass status. It does
show the implementation improves MPG activation for sampled scalar commitment
questions without making MPG a generic strategy/risk matrix. Unrun casebook items
remain future holdout candidates.
