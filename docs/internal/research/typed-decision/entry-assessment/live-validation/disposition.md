# C01-next P1/P2/P3 live development disposition

Status: **campaign complete; feasibility supported on six authored controls; retain experimental**.
Review: author assessment of already-recorded outputs, not an independent model/human audit.
Source: `a0a32c989bf9445e69e4b9abfce88a83380f1be7`; admission freeze: `c32829eeafe7c789c62508c68adf7bbc7ae38e2d`.

## Result and decision

The frozen [protocol](protocol.md) evaluated six authored Chinese development controls,
not naturally sampled LLM failures or an independent holdout. Its reported measures are:

| Measure | Observed result |
| --- | --- |
| Positive cases containing their preregistered required hit | 3/3 |
| Negative controls with any defect hit | 0/3 |
| Negative controls sent to correction, information acquisition or fallback | 0/3 |
| Detector-triggered host corrections | 3/3 completed, once per case |
| Allowed rechecks | 3/3 completed; no remaining hit or unresolved dimension |
| Corrected candidates satisfying their frozen criteria, author review | 3/3 candidates; 9/9 criteria |
| Recorded external attempts | 9 Jev batches + 3 CPA corrections; all have outcomes |

These results support the narrow proposition that a named check can detect the intended
failure in these controls and trigger a useful one-shot correction while leaving these
three legitimate answers alone. They do not establish general detection precision,
three independent experts, automatic admission, or improvement over an ordinary LLM review.
The protocol did not specify a numerical production gate: this disposition introduces none.

**Close this six-case validation task; keep the implemented slice experimental and keep
#211 OPEN/unqualified.** Preserve the frozen questions, samples, requests and historical
records. Do not replay the terminal batch, expand the question bank, enable default
`using-mindthus`, or restart the paused graph4 formal A/B/C on the strength of these results.

## Correction review against the original criteria

The exact criteria remain in [cases.json](cases.json); exact replies and per-criterion
assessments are in [observation.json](observation.json). This is post-run author review,
not a relabeling of initial detector answers.

| Case | Before | Observed correction and review |
| --- | --- | --- |
| V01 | Schema/field checks were promoted to release readiness. | Retains the passed mechanical checks, says readiness cannot be established from them, and names the missing semantic/e2e/approval evidence. All three criteria met. |
| V02 | A suspected database cause was treated as established, with immediate index work proposed. | Restores causality to a hypothesis, retains the observed P95 degradation, and asks for discriminating latency evidence before index optimization. All three criteria met. |
| V03 | A narrow serialization comparison was replaced by an architecture migration. | Uses the supplied 18 ms/7 ms comparison, concludes only about this benchmark, and keeps architecture migration outside scope. All three criteria met. |

N01/N02/N03 produced no correction, so this run did not rewrite the already-acceptable
negative candidates. V01's revision appropriately says readiness is **not established**;
it does not prove the release is actually defective. The same Jev's clear recheck is a
regression signal, not an independent truth or optimality judgment.

## Cross-hit review: preserve attribution problems, not extra success credit

The protocol scored one required dimension per positive case; it did not preregister
all other cells as true or false. Extra hits therefore remain outside that initial
score. This does not make them automatically correct. The following is explicitly
post-run semantic interpretation of the frozen contract and recorded targets:

| Extra hit | Author interpretation | Why it is not another certified detection |
| --- | --- | --- |
| V01 / P2 | Label boundary ambiguous. | The candidate invents release readiness, but the user only asks whether readiness follows from known checks. P2 instructions refer to adopting an unsupported **user** premise, while its option text is broader. Candidate overclaim and user-premise adoption are not necessarily the same defect. |
| V02 / P1 | Possible explanatory overlap, not established. | One proposed cause takes over the diagnosis, but database causality is unproved, not a demonstrated locally true mechanism. The narrow P1 relation may not hold even though P2 clearly applies. |
| V02 / P3 | Plausible co-occurrence. | Direct index work substitutes intervention for the requested evidence-led diagnosis. This is compatible with a scope violation, but this extra label was not independently adjudicated. |
| V03 / P1 | Likely out-of-scope cross-hit under the narrow P1 definition. | The candidate replaces the task with a broader architecture topic. It does not clearly elevate an established local truth into the original object's whole explanation. P3 is the direct supported diagnosis. |

All three positive cases still deserved correction under their required check. That
case-level success does not validate every extra instruction sent to the corrector.
The three corrected replies show no additional violation against their frozen criteria,
but without an ablation we cannot isolate the effects of the extra instructions.
No statistical independence/dependence conclusion follows from three positive cases.
No per-dimension precision number or post-hoc replacement label is claimed.

Two local uncertainty observations are retained without adding a new threshold:

- N01/P2 selected `treatment_fit` with probability 0.71 versus 0.23 for
  `unsupported_as_fact`; provider confidence 0.62.
- V01/P3 selected `within_scope` with probability 0.35 versus 0.31 for
  `scope_overridden`; provider confidence 0.14. The runner still consumed this
  categorical answer as known; `unresolved=[]` is not proof of strong certainty.

## Actual cost and latency scope

| Component | Requests | Reported input/output tokens | Sum of recorded request elapsed time |
| --- | --- | --- | --- |
| TypeSafe `jev-1.13.0` | 9 (6 initial + 3 recheck) | 84,821 / 1,633 | 6.496222723 s |
| CPA `deepseek-v4.1-flash` | 3 corrections | 1,645 / 225 | 5.646400671 s |

Each Jev request evaluated three questions against one supplied State. Neither provider
returned a monetary cost value; actual charges remain unknown. The USD 0.12 allowance
was a reservation ceiling, not a measured bill. Request-time sums exclude preparation,
interruption, review and maintenance, and do not measure end-to-end speedup.
No batch-versus-split comparison was run, so State-sharing billing is still unverified.

## Evidence and implementation boundary

[records/manifest.json](records/manifest.json) and its 77 JSON records are byte-identical
copies of the source run, with an external [evidence index](evidence-index.json).
The raw `summary.json` deliberately retains `author_review_pending`; the completed
review is a separate derived artifact, not an edit to historical observations.
The records store validated adapter outputs and receipts, not raw HTTP headers or
provider-signed billing. Three host outcomes lack an explicit `evidence_kind` field;
their model, intent and returned reply remain present. That limitation is not silently patched.

The live carrier reused `assessment.assess` and `Session`; it was not a native invocation
of the general `entry.run` driver (still offline-only), automatic trigger discovery,
all-method routing, or default Skill integration. All six triggers and candidate targets
were authored beforehand. The candidate-generation cost and missed activation rate were
not measured. There is no no-check control, LLM-only reviewer or single-question ablation.

The next bounded decision should concern the **existing question boundaries and marginal
value**, especially P1 over-detection and P2 user-premise versus candidate-overclaim scope.
Use these six cases as development evidence only. Any future change/test needs its own
pre-results identity; this closeout authorizes no new run. Do not rebuild the platform
or broaden the scan to obtain a better score.
