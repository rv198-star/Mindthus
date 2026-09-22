# C01-next I1 — scoped entry assessment and one correction

**Question-set successor v2:** existing P1/P2 boundaries are clarified under the
[bounded ablation protocol](boundary-ablation-v2/protocol.md). P3 text and the I1
execution mechanics stay intact; version/input checks reject cross-contract correction.
The six-case evidence below remains version 1 and is not rebound to the new questions.
No default Skill activation or production qualification follows from this revision.
The one-shot physical deletion comparison is now complete; read its
[disposition](boundary-ablation-v2/disposition.md). P1/P3 show distinct useful actions,
but P3 over-detection and an extra P1 hit in one reduced batch remain. P2's independent
benefit is not isolated. The eight authored controls do not confer production qualification.

Status: **implemented opt-in engineering slice; small live development validation completed; no production qualification**.
Design authority: [entry assessment design 0.1](../using-mindthus-assessment-design.md)
and [ten-rule manual 1.1](../../../../methodologies/typed-decision-principles.md).
Implementation baseline: `c164e98692ddea70e939b74908c01cc1beb83762`. Issue: #211.

## What now executes

The new `experiments/typed_decision/assessment.py` prepares P1 explanatory scope,
P2 premise treatment and P3 scope preservation as normal provider-neutral DecisionSpecs.
An existing Session evaluates the active questions in one same-State batch. The result
is a small object/scope-bound matrix plus `continue_original`, `request_correction`,
`acquire_information` or `return_original_owner` — not a new canonical audit verdict.

`experiments/typed_decision/entry.py` consumes that action, rather than merely logging it:

1. Preserve the original task, declared decision context, target and activation source.
2. Inspect an actual S0 user frame or an existing S1 candidate. Missing candidate means
   no answer inspection. P3 is skipped for a user frame; no frame-risk/impact means no
   optional scan. Required audits and known obligations are never discharged by a clear detector.
3. A positive defect result creates a named correction request. The original host supplies
   at most one revised target through its hook; the hook cannot replace the original task,
   goals, constraints, evidence or permissions through its response schema.
4. The revised target becomes S2 with parent State and assessment references. At most one
   batch rechecks the active dimensions affected by that target. Persisting defects or
   uncertainty returns the matter to the original owner; no second rewrite or automatic retry.
5. The optional routing continuation invokes the unchanged C01 graph4 and existing verified
   handoff/Trace. The revised text is explicitly a host proposal, not new established evidence.
   A correction retains an original-owner audit obligation, so its clear recheck does not
   silently permit skipping Frame Fitness, Whole Elephant or Fidelity responsibilities.

P1 and P3 can both fire: restore the valid object first, then qualify premises and rebuild
its main explanation. No voting, confidence grant, method-name heuristic or global all-green gate.
A high-risk target returns to its original owner rather than receiving automatic correction.

## Reproducible offline entry

From repository root:

```bash
python3 -m experiments.typed_decision.entry \
  --state-root /tmp/mindthus-entry-i1-example
# Same input/source/actor identity: all checks and correction are reused.
python3 -m experiments.typed_decision.entry \
  --state-root /tmp/mindthus-entry-i1-example
```

Use a separate explicitly named episode with `--route` to also exercise the old router:

```bash
python3 -m experiments.typed_decision.entry \
  --state-root /tmp/mindthus-entry-i1-route-example --route
```

The bundled fixture supplies detector answers **and** the revised host text. It tests
control flow, not Jev's ability to detect the defect or an LLM's ability to repair it.
CLI output is developer-facing diagnostic JSON, not a user-facing answer format.
The default example changes a draft claiming that matching file counts prove backup
reliability into a bounded statement retaining the missing content/recovery evidence.

## Host and provider seams

`assessment.assess(session, envelope, repo)` uses the supplied Session's existing
DecisionProvider. Native TypeSafe, OpenRouter Jev and an equivalent structured-choice
backend need no C01-specific transport. A live Session still requires its normal frozen
request allowlist, source identities, authorization and cost reservation.

The high-level `entry.run(...)` and CLI are **offline-only for this delivery**. They reject
live detector or correction hooks before sending anything. No credential is read, no
new live campaign is admitted, and the default installed `using-mindthus` is not changed.
A future live carrier must admit the combined detector + real host correction + recheck
scope, including dynamically produced S2 input, without silently resetting the parent
budget or retrying unknown calls. It must not reuse a historical trial freeze.

The correction hook implements:

```python
identity: str          # matches the declared correction_owner_ref
is_live: bool
correct(request: dict, timeout: float) -> dict
```

The returned dict has exactly `text`, `version`, `receipt_ref`, `usage`.
`usage` has `input_tokens`, `output_tokens`, `cost_usd`; missing observations are null.
Text and version must change; arbitrary extra task/state fields are rejected. A technical
error is terminal and error text is not persisted. KeyboardInterrupt or process loss after
intent leaves an unknown operation that must be reconciled, never automatically repeated.
This hook is trusted host code, not a sandbox for executing model-generated Python.
The host must enforce actual transport/subprocess timeouts; callback late-return detection
alone is not a process-kill guarantee.

## Input contract

The envelope contains `state_version`, the original C01 `task`, `decision_context`,
`target` and `activation` only. The declared decision context contains `object`, `goal`,
`scope`, `source_ref`; it is caller-supplied context, not an independently verified fact.

`target` is null or an identified/versioned `user_frame`, `candidate_frame`,
`candidate_thesis`, `candidate_plan` or `candidate_answer`. A user-frame selection must
quote the original request. The full original task always remains in the evaluation.
`activation` records `event`, `source_ref`, `reason`, explicit `frame_risk`,
`execution_impact`, `required` flags and the chosen subset of P1/P2/P3.
Those flags are a host event/assessment input; the Python code does not detect semantics
from keywords and does not treat absent activation as proof that no risk exists.

Matrix rows retain question/target/State identity, canonical source hashes, object scope,
S0/S1/S2, native value/status/uncertainty, evidence origin and consumption state.
`not_evaluated`, `not_applicable`, `insufficient_context`, non-ok provider status and a
positive defect are distinct. Provider failure preserves successful sibling observations
but does not trigger a correction from the failed assessment.

## Fixed engineering budget and recovery

Per episode: at most **2 detector batches + 1 host correction + 3 original routing calls**,
90 seconds shared accounted time, 30 seconds for the correction, a 16 KiB input/response
limit, and the existing 64 KiB projected-State / 96 KiB typed-request ceilings.
No new paid calls are authorized. Actual billing, setup, maintenance and value remain
unknown; batching economy is not inferred from the fixture or request shape.

The episode uses the existing immutable JSON records and POSIX lock pattern. Child
Sessions preserve original provider/engine identities; a shared resolved-runtime binding
also rejects detector/routing snapshot drift before consuming the drifted response.
Completed outcomes replay with zero provider/hook calls. Original facts or source changes
cannot reuse an old episode. Recovery does not reset the one-correction budget.
All active checks read the changed target, so recheck includes every active affected
check, not only the previously failing one. An S0 correction creates a candidate and
makes P3 eligible if it was included in the declared check subset.

Do not change directory merely to retry a failed/unknown episode. New input/source work
requires an explicit new identity and the prior failure remains in cumulative accounting.
The implementation digest changes because new runtime modules exist; old freezes must
not be rebound or rerun under the new digest.

## Evidence and next boundary

[Verification](verification.json) binds source, tests and the exact offline execution.
The required tests cover no-candidate/no-trigger paths, explicit scope controls, raw
State/candidate separation, simultaneous P1/P3 signals, unknown/failure states, original
obligations, one correction, one recheck, crash/reentry and old-router continuation.
Existing method files, graph4, Provider, Session and historical trial artifacts remain
unchanged. Formal A/B/C stays paused and #212 is not restarted.

The first bounded live development batch is now complete; see
[live protocol](live-validation/protocol.md),
[observation](live-validation/observation.json) and
[disposition](live-validation/disposition.md). Across six authored controls, required
positive detection was3/3, negative-case defect hits0/3, three bounded corrections completed,
and their one allowed recheck cleared all three dimensions. This is development evidence,
not an independent holdout or production qualification.

The reviewed replies satisfy their frozen criteria, but this does not certify all cross-hits:
V01/P2 has a user-premise/candidate-overclaim ambiguity and V03/P1 is likely outside narrow
P1 scope. Initial scores remain unchanged; see the separately labeled author analysis in
[the disposition](live-validation/disposition.md). The [evidence index](live-validation/evidence-index.json)
binds 77 byte-identical records and the [verification](live-validation/verification.json) records checks.
The live carrier reused assessment/Session, not live native `entry.run` or automatic activation.

Close this six-case task. Next design should resolve existing question boundaries and define
one bounded marginal-value/ablation comparison, rather than expand the question set or build
another framework. No new run, default entry hook or old graph4 A/B/C is admitted by these results.
