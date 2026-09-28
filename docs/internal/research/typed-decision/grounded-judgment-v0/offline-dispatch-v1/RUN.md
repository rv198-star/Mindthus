# Executable wiring and future admission

From this checkout, with Python 3.12:

```sh
python3 -m experiments.grounded_judgment dispatch-demo --out /tmp/gj-new-simulation
```

This is the complete offline path. The output directory must be new. It uses mock time and
mock transport only. `dispatch-step` intentionally refuses a simulation batch with a live adapter.
Programmatic simulated transports use `Dispatcher(..., clock=..., monotonic=..., sleep=...)`.

For a future **separately approved** live batch (do not run these as this stage's validation):

1. Use existing `prepare-input --documents DOCUMENTS.json --repo CHECKOUT` for each business
   case. Its output is a packet with `documents`, `materials`, `initial_paths`; all arms share it.
2. The owner supplies one bundle containing `inputs` (case-id → packet), `norms` (same case-id →
   normative table), `provenance`, `owner_seal_ref`. `provenance=owner_supplied_unseen`, exactly
   eight cases and an owner seal reference are required for future acceptance admission.
   A public-development bundle remains unsealed. The program does not establish unseen status
   independently and never feeds `norms` or expected answers into business requests.
3. Import locally:

```sh
python3 -m experiments.grounded_judgment import-materials --bundle OWNER_BUNDLE.json --out MATERIALS
```

4. After actual authorization, fill `admission.example.json` with the authorization reference,
   imported material directory, manifest digest (the project's `contracts.digest`), approved
   per-case A/B/C limits, per-invocation timeouts and existing official Codex binary path.
   The example has `execution_authorized=false` and null seal/authorization. It cannot start a run.
   This application record represents authorization; it does not override system/tool permissions.
5. Prepare and dispatch through the same batch root:

```sh
python3 -m experiments.grounded_judgment dispatch-prepare --batch BATCH --inputs MATERIALS/inputs.json --admission APPROVED.json
python3 -m experiments.grounded_judgment dispatch-step --batch BATCH --run CASE-C
```

Each `dispatch-step` advances exactly one logical invocation, or returns done/stopped without
sending. Continue the approved order via the same `Dispatcher` instance for monotonic continuity,
or the CLI (restart uses the existing conservative 60-second wait). There is no retry loop and
no command to bypass unknown. Material reads are subsequent host invocations in the same scheduler.
The importer, preparation and `next` do not send; only explicit dispatch does. The live adapter
lazily uses the existing official credential mechanisms. No global config or base_url is changed.

## Budget proposal, not authorization

| Per case | A | B | C |
|---|---:|---:|---:|
| Usual no-revision path with findings (no extra reads) | 2 host | 3 host | 1 host + 4 Jev |
| No findings, no extra reads | 2 host | 2 host | 1 host + up to 3 Jev |
| All permitted revision, no extra reads | 3 host | 4 host | 2 host + 4 Jev |
| Up to three read continuations, plus check/revision | 6 host | 7 host | 5 host + 4 Jev |

C dependency-missing rounds can be skipped by the unchanged runtime, never padded to a target
count. B/C without findings skip the check. A retains its original one self-check. Each path
stops at its first completed workflow or failure; unused capacity is not semantic retry authority.

For eight cases, the usual with-findings/no-revision total is 80 logical calls (48 host + 32 Jev).
With every revision but no reads it is 104 (72 + 32); the proposed worst cap is 176 (144 + 32).
At 60 seconds between known terminals, these require 79/103/175 minutes of inter-call cooling
if all calls occur in one continuous batch. Processing, load, authentication/connection recovery
and human interruption add wall time; they are not included in those cooling numbers.
Suggested single-invocation ceilings remain 360 seconds host and 60 seconds Jev (existing Jev
transport hard maximum 90 seconds). These are still proposals, not newly granted budgets.

All attempted invocations, including failures, consume their path's call count. A known failure
stops that path; another independent path may continue after cooling. Unknown stops the batch,
leaves the serial intent incomplete, and never authorizes another attempt. Thus the cap arithmetic
is not a promise that a failing batch can always finish or that unknown work ended on timeout.
Original single-call timeout covers internal recovery; no outer retry budget is added.

Per call: preserve logical invocation, CLI starts, observed recovery logs, raw usage, active wait,
loading, invocation wall and dispatch wall separately. Underlying HTTP/generation counts and
connection/auth breakdown remain null when unobserved. Runtime wall also includes pauses between
steps. Amount and currency cannot be derived from summed tokens; approve monetary budget only
after applicable provider pricing/usage terms are established. None is approved here.
