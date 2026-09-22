# Task-facing handoff replacement — pre-evaluation repair

## Named defect and scope

Recorded L27/L28 answers exposed internal applicability status/value and
`fallback_method_check`. The previous host prompt serialized the whole diagnostic proposal
and named the internal fields as instructions. The replacement renders the existing verdict
as task-facing directions and keeps the full machine record only in the audited handoff.
This is one named data-presentation repair before held-out arm results, not a routing or
semantic prompt optimization loop. No prior live result or frozen trial is rewritten.

## Delivered behavior

The host receives original task context, retained duties and complete selected/checked
method text. Rejection, uncertainty and failed applicability remain different. An uncertain
method is never described as rejected, and a rejected method is never selected. Runtime
identifiers, method digests, machine route reasons and the diagnostic proposal are omitted
from the task-facing envelope. If the user's actual task discusses those fields, its text
is retained verbatim; there is no keyword scrubbing or output postprocessor.

`handoff.prepare` and its v2 audit schema are unchanged. C01 graph4 and J1/J2/J4/J5,
canonical methods, providers and Session are unchanged. Only `handoff.host_prompt` changes.
The package runtime digest changes as expected: old live freezes remain historical and
are not regenerated. The separately frozen blind label review depends on unchanged method
contracts and remains mechanically valid; its tool invocation was rejected before command
execution, with no provider outcome observed.

## Evidence limits

Six new boundary tests and the 25 handoff/host tests pass. A fresh full repository run
completed 1235 tests with 1230 successful and 5 skipped. Raw log hash is recorded in
`presentation-verification.json`. No live post-repair answer has been obtained: prevention
of diagnostic fields in the host envelope is tested, but improvement of final wording
remains unqualified until a permitted, pre-admitted downstream trial is observed.
