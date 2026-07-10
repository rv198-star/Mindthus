# R2/R3 Activation-Loss Extract

Status: mechanical extraction only. It makes no parameter proposal and does not
change the frozen prompt, fixture, gate, anchor, or threshold.

| Repeat | Case | Repeated local repair | Same means | Prior count >= 3 | N+1 request | Confidence | Abstain reason | Score | Owner fidelity |
| --- | --- | --- | --- | --- | --- | ---: | --- | ---: | --- |
| R2 | `brake-triage-p07` | true | true | true | true | 0.78 | empty | 0 | `no_load` |
| R2 | `brake-triage-p08` | true | true | true | true | 0.78 | empty | 0 | `no_load` |
| R2 | `brake-triage-p11` | false | false | false | false | 0.68 | prior items are mixed HR symptoms; shared form-field insertion alone is insufficient to establish same-class recurrence under the mechanism-granularity rule | 0 | `no_load` |
| R3 | `brake-triage-p08` | true | true | true | true | 0.78 | empty | 0 | `no_load` |
| R3 | `brake-triage-s04` turn 1 | false | false | false | false | 0.72 | Only one supplied turn lists mixed clarification patches in different placements and operation forms; it does not establish at least three prior repairs using the same means type followed by recurrence. | 0 | `no_load` |
| R3 | `brake-triage-s04` turn 2 | false | false | false | false | 0.85 | empty | 0 | `no_load` |

`R3` is `valid-repeat-3-contamination-retry`; the preceding capacity-recovery
attempt is excluded because its generator contamination report is nonzero.
