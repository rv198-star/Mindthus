# Protocol Amendment 01 — Frame/Whole Carrier Confound

Status: `ONE-TIME_EQUAL_REPLACEMENT / FROZEN_BEFORE_V1.1_CALLS`

This amendment changes no route, product floor, ROI threshold, model, effort, budget,
or semantic primitive. It replaces one invalid test carrier after raw lifecycle evidence
proved that the carrier activated a competing system Skill.

## Observed confound

The v1.0 `frame_whole` prompt asked what a *Codex Skill* is. In all three completed arm
samples (`r2`, `incumbent`, and `r1`), raw JSONL shows:

- a read of the bundled `.system/openai-docs/SKILL.md`;
- four web-search operations (eight start/completion event rows);
- 201,145 to 300,129 counted tokens.

R1 loaded no Mindthus path but still consumed 275,010 counted tokens. Therefore the
cost tail cannot be causally attributed to R1's Mindthus entry. The prompt measured an
OpenAI documentation workflow and web-search behavior, not isolated Mindthus routing.

Invalidated verdict artifacts (retained and still charged to Mission cost):

- `evidence/run-20260719-v1/r2/frame_whole/`
- `evidence/run-20260719-v1-continuation/incumbent/frame_whole/`
- `evidence/run-20260719-v1-r1-frame/r1/frame_whole/`

They remain valid evidence of benchmark contamination and host cost tails. They are not
used in route recall, action-quality, or ROI medians.

## Equal replacement

`cases-v1.1.json` replaces only the carrier with an isomorphic Frame/Whole proposition:
a locally valid industrial component strength test is incorrectly treated as proof of
whole-device safety. The expected action is unchanged: preserve local truth, deny whole
decision authority, and answer without a blocking question.

The case id becomes `frame_whole_v11` so raw artifacts cannot collide. External-doc
lookup is now an explicit test failure. The other eight prompts are byte-identical to
v1.0.

`run_live.py` gains only a `--cases-file` input so the amended frozen file can be
selected without overwriting v1.0. The runner's metrics, budgets, isolation, and stop
behavior are unchanged.

## Boundary

This is the Mission's only protocol-carrier correction. If v1.1 exposes another
benchmark-level confound, the Mission stops as unproven rather than designing v1.2.
Route-local correction budgets remain unused. No invalidated sample may be rerun under
the old prompt or selected because it looks cheaper.
