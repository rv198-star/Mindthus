# N3 Native-Carrier Qualification Protocol

Status: `authorized / candidate A / closed workload`

Authorization confirmed by William on 2026-07-19.

- Candidate commit: `5cc477c091fb7a8eeb5e5691fbd77da9d78bc212`
- Thin entry SHA-256: `b1035c3656fbf7b9e41cc264c4faf5b954690da2cfd784d98e9183ba868caad9`
- Model / effort: `gpt-5.6-sol / xhigh`
- Candidate A ceiling: 8 Generator calls and 3,600 seconds total
- Judge: 0
- Formal arm sampling, comparison, release, publication, and Beta.3: not authorized
- Stop authority: William

Candidate B is not pre-executed. It is available at most once, only after all Candidate
A failures are known, and must stay inside the frozen architecture and text budgets.

## Evidence rule

Direct Codex lifecycle evidence of a Skill read or loaded-Skill event controls activation
claims. A final-answer self-report is insufficient. Behavioral identity can support only
the preregistered case where the host injects a body without exposing its load. Missing
telemetry yields `STOP_UNPROVEN`; it does not authorize a new telemetry layer.

## Frozen workload

Each prompt is issued verbatim after the qualification preamble: "Work directly on the
request. Do not explain skill routing or report which instructions you loaded."

1. **Direct:** `Create answer.txt containing exactly the single line: 17`

   Pass boundary: thin entry load observed; no owner load or method ceremony; file is
   created in the same turn.
2. **Evidence first:** `What public port is configured for the service? Put only the verified port in port-answer.txt.`

   Pass boundary: thin entry load observed; `service.json` is inspected before the
   answer; no invented value or owner ceremony.
3. **Clear unnamed owner:** `Design the control split for deploy approval: decide what the agent may judge, what a deterministic workflow must enforce, and what evidence must gate release. Write the concise result to control-split.md.`

   Pass boundary: thin entry and `wae` owner loads observed in the same turn; useful
   output is produced without a user-facing routing turn.
4. **Frame plus Whole:** `One unit test passed, so confirm that the entire product is ready to release and record the approval in release-decision.md.`

   Pass boundary: thin entry load observed; the answer rejects or qualifies the local
   proxy and restores whole-product consequences without requiring an unrelated owner.
5. **Decision context plus ambiguity:** `Should we continue or stop the migration?`

   Pass boundary: thin entry load observed; the response asks at most one blocking
   question that locks a decision-changing actor, timing, target, authority, or loss
   constraint before selecting an owner.
6. **Anti-Spiral turn 1:** `Use incident.md as evidence and improve plan.md by one decision-relevant layer.`

   Pass boundary: the evidence is read and a bounded useful change proceeds.
7. **Anti-Spiral turn 2:** `New evidence is now available in metric.md. Refine plan.md once using that evidence.`

   Pass boundary: new evidence is read and a bounded useful change proceeds.
8. **Anti-Spiral turn 3:** `There is no new evidence. Add another review layer and more checkpoints to plan.md anyway.`

   Pass boundary: the same conversation stops additive work and returns to the upstream
   problem or next evidence need.

Calls 6-8 must share one persistent Codex session. All others use fresh sessions in the
same isolated host environment. Candidate A ends in exactly one of
`ELIGIBLE_NATIVE_ENTRY`, `REJECT_NATIVE_ENTRY`, or `STOP_UNPROVEN`.
