# Judgment Research Closure Summary

Date: 2026-07-13

## Decision

The active brake semantic-triage research line is closed. Mindthus will not continue
adding prompt revisions, thresholds, voting layers, retries, or team-authored case
variants for this pathology from the evidence already collected.

This is a research stop, not a passing certification. The public 50-case benchmark
remains useful as a release-level regression surface, but it is not the product goal.

## Evidence Boundary

- The latest complete public 50-case run improved the treatment positive mean from
  `1.184` to `1.447`, while the final-answer negative false-wake rate moved from
  `0.083` to `0.000`.
- The treatment result remains below the pre-registered `1.5` positive threshold.
- Later development diagnostics could pass team-authored gates, but independently
  owned shadow variants did not establish stable open-domain natural activation.
- Repeated matcher, prompt, threshold, and voting refinements produced diminishing
  product evidence and increasing fixture-overfitting risk.

The detailed research evidence remains on the archive branch
`codex/brake-semantic-triage-design`. The closure report at commit `f820a898` and the
later convergence inventory at `6efeda76` are historical audit records, not changes to
the released Mindthus skills.

## Durable Results

The project keeps the parts that remain useful outside the stopped pathology:

- the public bidirectional benchmark and blind generation/grading separation;
- separate final-answer and runtime-event false-wake metrics;
- separate activation, owner-fidelity, and loaded-action evidence;
- deterministic contract tests and explicit run fingerprints;
- malformed-binary calibration anchors that generalize beyond one public case; and
- fail-closed treatment of decisive negative-control violations.

Brake-specific prompts, scalar thresholds, k=3 voting, owner-gate experiments, and
team-authored shadow variants remain research evidence and are not product runtime.

## Reopening Conditions

Reopen this research line only when all of the following are true:

1. A material failure comes from a real user task or an independently owned unseen set.
2. The failure recurs or has credible impact beyond a single anecdote.
3. A proposed mechanism can be falsified without adding another sequence of
   team-authored variants.
4. The repair has a pre-registered stop condition and preserves negative controls.

Until then, engineering effort returns to product clarity, installation, explicit
invocation, public/runtime documentation boundaries, and real-task value.
