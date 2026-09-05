# SRA proportionate allocation — implementation review

Date: 2026-09-05
Baseline: `eeb7e5c7225d9600f07632cd9254f25d26db8628`
Reviewed executable/test revision: `6ab3aa7303d60dc3e2b43187a1dbea8b57a45bb1`
Reviewed tree: `b0636e4e75ea3219abe9b5cac321847c51d24bc4`
Scope: #188, #189, #185, #186 and #190.
Reviewer: ChatGPT self-review and executed tests; no external CLI reviewer or independent-model claim.

## What changed

The user-approved goal remains viability before worthwhile strengthening, with analysis
cost proportional to the decision. Risk review preserves the actual objective, time
horizon, dignity/commitments, qualitative value, long-term capability, learning and reserve.
These are method rules, not a claim that scripts can prove semantic optimality.

Implementation adds a named calibration policy, canonical draft intake, checked result
cards, completion-only references with precise conflict diagnostics, and explicit new
re-ranking drafts. It retains one allocation engine and the existing demand, capacity,
dependency, outcome and repair invariants.

## Risk and regression findings resolved during review

1. **Entry growth:** the first rewritten SKILL entry exceeded the existing 10 KiB gate.
   Detailed runtime guidance was moved to an on-demand resource; the gate was not relaxed.
   Final entry size is 10,075 UTF-8 bytes.
2. **Forward compatibility:** the old parser accepts unknown fields on v0.3 input.
   A policy-name field alone would therefore let an old executable silently ignore new
   behavior. New extensions now require `sra.decision-context-input.v0.4`; the older
   executable explicitly rejects that input. Legacy v0.3 inputs keep their exact policy.
3. **Re-ranking source race:** the parent raw input and decision are compared before and
   after the integrity assessment. A changing parent is refused, not attributed to a
   verified snapshot. This is local drift detection, not tamper-proof external storage.
4. **Renderer compatibility:** default legacy CLI output stays full. New policy runs use
   the card; explicit `--view full` and JSON remain available. No-start statuses remain
   conspicuous, including the reconciliation-only missing-context outcome.

## Executed boundary coverage

The added `tests/test_sra_proportionate.py` uses 16 grouped tests and reuses the existing
fixture and runtime helpers. Covered cases include:

- Lite/Full × ordinary/consequential/unknown × contamination;
- explicit consequence signals and prior conclusions cannot be washed by a low-risk label;
- missing/invalid policy, old input with new fields, and Full/single replay;
- unchanged legacy defaults and unknown risk in newly assembled drafts;
- missing dependency knowledge, timestamp, owner and malformed draft input;
- exclusive draft output and absence of allocation decisions in drafts;
- criterion identity/hash, task scope, window and per-view packet binding;
- shared criteria with different rationale, changed resource commitments, and unbound
  free-text paraphrase remaining a conflict;
- referenced dual-view record/check/repair and read-only card/full projections;
- blocked, infeasible, conditional and missing-context rendering;
- explicit refreshed re-ranking, new identity, immutable parent, no inherited judgment,
  parent corruption and concurrent parent change.

Existing SRA demand, dependencies, graph, authority, schema and repair regressions were
retained. Existing TPlan and other project suites were not changed.

## Local verification

Interpreter: CPython 3.10.12.

```text
python3 -m unittest discover -s tests -q
Ran 1053 tests; OK (skipped=5)
= 1048 passed, 5 optional-dependency skips

python3 scripts/check-test-lifecycle.py --json
valid; 78 / 78 executable test files registered

git diff --check
PASS
```

The method identity assertion was updated to the approved core statement, not removed.
The five optional skips were inherited; no test was skipped to make the feature pass.

## Cross-version executable replay

A one-time probe prepared and finalized synthetic decisions using the unchanged baseline
checkout, then ran the new checker and renderer against those directories:

| Old run | New checker | Parent/run file bytes |
|---|---|---|
| clean Lite | ok | unchanged |
| contaminated Lite | ok | unchanged |
| Full | ok | unchanged |

The reverse probe passed new v0.4 input to the old executable. It rejected the input with
`schema_version must be sra.decision-context-input.v0.3`.

These are deterministic compatibility tests, not independent Agentic judgments. The
probe used temporary run directories and did not modify either checkout's product files.

## Packaging and release boundary

All five supported release-pack layouts include `sra_policy.py`, `sra_criteria.py`,
`draft_sra_context.py` and `rerank_sra_context.py`. Full package tests are part of the suite;
a separate build also completed. PR CI is recorded by GitHub on the exact pushed commit,
not inferred from this local result.

No version/tag/release, ROI Beta asset, TPlan schema or runtime generation, host permission,
benchmark deletion, personnel scoring system or autonomous scheduling change is made.

## Verdict and remaining evidence

The exercised implementation and compatibility boundaries pass. This supports landing
the bounded functional MVP. It does not establish measured Token savings, lower total
user effort, model independence, better business outcomes, an optimal allocation, or
complete protection from biased risk/criterion assessments. #185/#186 retain benefit
observation items separately from implementation completion; other #183 discussions are
not implemented by this work.
