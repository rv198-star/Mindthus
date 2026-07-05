# MPG Scalar Commitment Unpack / MPG 标量承诺显影

`Scalar Commitment Under Path Volatility / 路径波动下的标量承诺显影` is a
support primitive, not a judgment owner and not a general unpack skill. It exists
only to make MPG-eligible questions visible before routing. MPG still owns the
path-carrying judgment.

## Core Rule

> When a single-point decision hides a mainline-carrier-path-exposure-commitment
> structure, surface that latent vector before deciding whether MPG owns.

Use it when the user asks a compressed commitment question whose success depends on
whether a long-term mainline can be carried by a specific carrier through path
volatility under an exposure budget.

## Internal Shape

- `mainline`: long-term direction, strategic target, convergence claim, or hypothesis.
- `carrier`: stock, company, job, role, product, project, city, technical route, plan,
  or other vehicle carrying the mainline.
- `path_volatility`: drawdown, cashflow valley, policy friction, competition,
  execution resistance, trust loss, market delay, ecosystem risk, or other
  path-shaping force.
- `exposure`: time, money, trust, authority, opportunity cost, liquidity, runway,
  user trust, reputation, or emotional cost that must be carried.
- `commitment`: commit, hold, add, reduce, quit, join, pivot, wait, switch, hedge,
  exit, or probe.

Compact form: `mainline / carrier / path_volatility / exposure / commitment`.

## Route State

- `mpg_ready`: at least three latent fields are non-trivial; route to MPG.
- `needs_one_clarification`: one essential missing field blocks MPG; ask one
  targeted clarification only.
- `mainline_unclear`: the mainline itself is not qualified; route to SELA, EDSP,
  or premise calibration before MPG.
- `evidence_missing`: key factual claims are missing; gather facts or apply
  Evidence / Claim Ceiling before MPG.
- `not_applicable`: no latent path-carrying structure; direct answer or default route.

## High-Confidence Examples

These are examples, not sufficient keyword rules:

- buy / hold / sell under drawdown;
- quitting for a startup with runway risk;
- funding a transformation through a cashflow valley;
- migrating a product or technical route under ecosystem risk;
- maintaining a project whose value depends on whether it can carry a longer mainline.

## Visible Behavior

- Do not expose a field table by default.
- Start with a plain-language reframe of what the user may really be deciding.
- Ask at most one clarification question.
- If the user asks for a direct/simple answer and no path-carrying structure remains,
  step aside and route normally.

## Boundaries

- Do not trigger for pure fact lookup, simple consumer preference, naked trend claims
  with no actor/carrier/exposure/commitment, evidence-missing hype, empirical A/B
  questions without data, or WAE-style control-boundary problems.
- Do not let this support primitive decide whether the mainline is true, whether the
  carrier is good, or whether the commitment is wise. It only changes route input.

## Test Material

Manual review cases live at
`tests/mpg/scalar_commitment_unpack_manual_review_cases.md`. SubAgent sampled review
evidence lives at
`tests/mpg/scalar_commitment_unpack_subagent_review_2026-07-06.md`.
