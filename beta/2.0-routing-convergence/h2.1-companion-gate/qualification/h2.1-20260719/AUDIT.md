# H2.1 Terminal Responsibility Review

Result: `STOP_REQUIRED / EVIDENCE_TRUSTED`

Three read-only reviewers independently inspected the frozen contracts and raw live
artifacts. They did not edit code, evidence, or Mission state.

## Evidence integrity review

Result: `EVIDENCE_TRUSTED`

- C1 Q1/Q2 use one UUID and two turns in the same isolated cwd.
- Q1 reads entry only; Q2 reads index then MPG only.
- C2 timestamps and both CLI event layers independently establish
  `entry -> index -> SELA -> MPG`.
- Candidate `mindthus-beta / 2.0.0-next.4` is the only enabled plugin in each home.
- No repository or Stable Mindthus path appears in the command lifecycle.
- All three completed calls have trustworthy usage and remain below 275,000 tokens.

## Causal mapping review

Result: `FAIL_MAPPING`

The C2 read order violates the exact frozen positive contract. Because the existing
SELA handshake caused the MPG read, the candidate's modified MPG gate was bypassed. A
useful final answer cannot prove the intended causal branch or override the lifecycle
criterion. This is a trusted semantic/causal failure, not `STOP_UNPROVEN`.

## Stop and budget review

Result: `STOP_REQUIRED`

The first C2 failure blocks C3, Q3-Q7, Stable, and Judge under the frozen protocol.
The unauthenticated HTTP 401 attempt had no sampling, completed turn, output, or usage,
so it is an infrastructure preflight event rather than a Generator call.

Verified program ledger after C2:

- 16 Generator used / 16 remaining
- 0 Judge used / 8 remaining
- 1,375,303 counted tokens used / 6,624,697 remaining

## Main-Agent verification

The main Agent independently checked the raw JSONL, rollout metadata, exact prompts,
cwd, plugin inventories, diagnostics, usage events, final outputs, and frozen protocol.
It agrees with all three reviews and maps the result to
`H2.1_REJECTED -> STOP_2X_EXPLORATION`.
