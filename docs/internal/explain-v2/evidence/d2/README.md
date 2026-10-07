# D2 — fixed engineering result, model arm pending

Registration commit: `54f4988` (registered before execution).
Compiler candidate: `64ae68d69c9e5ba7a69540103784f2ae2bb07662`.

`registration.json` pins every runtime file and `cases.json`. Three constructed source
cases cover technical flow, qualified comparison and TPlan progress semantics. They
are development fixtures, not live production observations or generated model answers.

`results.json`: 3 cases × 2 engines × 2 wrappers × 3 repeats = **36/36** engineering
checks. Required visible statements, repeated/cross-engine text and graph relations,
exact export/recovery, and three isolated block patches passed. Source text embedded
for recovery is excluded from the visible-content comparison.

The reported wall time measures the local compile call in a running Python process.
It excludes model generation, context reads, tool transport and user comprehension.
HTML bytes are not tokens. These measurements are not a V1-vs-V2 model benefit result.

## Remaining before D2 can pass

- Task-specific permission for nine actual model pairs (18 generations), plus recorded
  provider/model/reasoning settings and cost allowance. A separate full model
  registration is required before starting; existing Jev authorizations do not apply.
- Genuine independent-reader/model comprehension evaluation or user observation,
  distinguished from this Agent's review of its own fixtures.
- Actual in-conversation HTML interaction evidence. Generated app-block JSON, an
  independent browser, a screenshot or a downloadable file is not that receipt.

D2 is **incomplete**, not passed. #229 remains waiting. No V2.1/V3 work was started.

## Reproduce

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 docs/internal/explain-v2/evidence/d2/check_engineering.py /tmp/new-d2-result.json
```

The runner checks pinned source hashes and refuses to overwrite an existing result.
This is a developer evidence runner, not a shipped Skill or runtime review loop.
