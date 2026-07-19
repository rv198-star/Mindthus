# H2 Qualification Continuation Authorization

Authorized by William after the prior `STOP_2X_EXPLORATION` result: “预算翻倍，继续”.

This is a new TPlan Mission and a new qualification run. It uses the previous Mission,
candidate, protocol, and raw JSONL only as source context; it does not rewrite the prior
terminal status or inherit its success state.

## Resource interpretation

- total Mission counted-token ceiling: `8,000,000`, inclusive of the prior Mission's
  `1,061,528` counted tokens
- remaining at continuation start: `6,938,472`
- per completed Generator or Judge call ceiling: `400,000` counted tokens
- overall call ceilings remain `32 Generator` and `8 Judge`; 11 Generator and 0 Judge
  were already consumed
- one fresh seven-call H2 qualification is authorized despite the former qualification
  sub-cap; this is the concrete meaning of “continue” after the failed two-call run
- if H2 qualifies, the frozen 14-Generator / 7-Judge Stable comparison still fits the
  overall call ceilings exactly: `11 + 7 + 14 = 32 Generator`, `7 Judge`

Counted tokens remain `input_tokens + output_tokens`; cached input is not added twice.

## Frozen scope

- candidate remains exactly commit `9c271c1f3fb86f1e81f4860d32d9e5ac4f08b59c`
- no candidate correction, H3, Hook, second entry, AGENTS injection, defaultPrompt,
  model-name routing, owner-body rewrite, release work, or relaxed semantic criterion
- rerun all Q1-Q7 as one fresh digest; do not resume the contaminated old thread
- the qualification carrier fix is process-only: start Q1 and resume Q2 with the host
  process working directory set to the isolated Q1/Q2 workspace
- Q2 must still explicitly resume Q1's exact thread UUID
- if the resumed turn reports any other cwd or reads project/Stable surfaces, reject H2
- all other cases remain separate isolated workspaces

## Terminal outcomes

- H2 failure or untrusted activation evidence: `STOP_2X_EXPLORATION`
- H2 technical pass but explicit owner-coordinate compatibility controls the product
  decision: `REQUIRES_WILLIAM`
- H2 and Stable comparison pass every critical gate: `CONTINUE_2X_SINGLE_ENTRY_TOPOLOGY`

No result from the previous stopped Mission is erased. This continuation can supersede
its product decision only with new complete evidence.
