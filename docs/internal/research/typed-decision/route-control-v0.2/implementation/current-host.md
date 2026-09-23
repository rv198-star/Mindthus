# Current-Agent host integration

The default `route-control.v0.2.1` CLI host is now `current-agent`. The Agent already running Mindthus executes the committed method or performs the named correction. CPA/DeepSeek is an explicitly selected experimental adapter, not a product prerequisite. The decision engine remains provider-neutral; a real Jev request still needs its own credential and exact admission. Existing CPA requests retain max reasoning when that adapter is chosen.

## Same entry, no additional LLM credential

```bash
python3 -m experiments.typed_decision.entry \
  --mode route-control.v0.2.1 \
  --fixture experiments/typed_decision/fixtures/route-control.json \
  --state-root /absolute/path/outside/repository/unique-episode
```

This example supplies **offline judgment observations**, not live Jev accuracy evidence. Unlike `--host fixture`, it does not use the fixture's answer text. The command commits the route, reads actual method files, and returns `status=awaiting_current_agent` with `host_request`, pointing to a checksummed `handoff.json` in the same episode.

The current Agent reads that handoff's instruction, original materials, exact committed scope and loaded methods, then performs the work. The request provides `reply_shape`: completion declares only the methods actually used; a source-referenced objection is the alternative. For correction, the existing typed reply/rebinding contract applies (`relationship_runtime.revision_packet`); original sources are never replaced. Unknown usage stays null. This host port does not grant any external tool permissions.

Write a response object as plain JSON:

```json
{
  "schema": "mindthus.current-host-response.v1",
  "request_id": "copy from handoff",
  "request_sha256": "copy from handoff",
  "owner_ref": "copy from handoff",
  "host_context_ref": "actual host context reference",
  "elapsed_seconds": null,
  "reply": {"...": "the completed typed reply, as declared in reply_shape"}
}
```

The example above is a schema guide, not a valid completed reply. Resume the **same command, input and root**, adding:

```bash
--host-response /absolute/path/current-agent-response.json
```

The response is checked before being stored and checked again on consumption. A wrong method set, wrong route revision, changed request hash, unrelated source or changed correction proposal is rejected; the legitimate outstanding request remains recoverable. Repeating the identical submission is idempotent. Accepted responses and completed calls are immutable.

Python hosts can use `CurrentAgentHost(owner, role='execution'|'correction'|'arbitration')` with the existing `entry.run`, and `submit_response(root, repo, payload)`. The existing host-owned `artifact_acceptor` remains the release authority for dependent artifacts; a returned answer does not accept its own downstream use. The CLI does not invent that callback: unaccepted dependent uses remain pending.

## Waiting and authority

A local handoff intent is a **known outstanding request**, not an unknown supplier call. It reserves one existing role slot without claiming an invocation completed. `counts` count completed records; `reserved_counts` expose outstanding reservations. Reentry exports the identical request without re-running the judgment or allocating another slot. New input/turns cannot abandon an outstanding request to reset the allowance. Unknown external supplier intents retain the existing non-resend rule.

The host's response consumes that same reservation. Elapsed execution/analysis telemetry is host-reported when available; if unavailable, the reservation ceiling is charged conservatively and `reported_elapsed_seconds=null` / `elapsed_basis=reserved_ceiling_actual_unknown` distinguish it from a measurement. Waiting between commands is not fabricated as model request time. Monetary usage remains unknown when the host cannot observe it; zero **additional outbound LLM requests** does not mean the current Agent's work was free.

Named arbitration is a separate handoff with the original objection, observations and contracts. It requires a host context different from the executor's declared context. The application checks this declaration but cannot attest actual context isolation. A platform unable to provide an independent context keeps the objection unresolved; it does not reuse the executor as its own judge or silently call CPA. All stages retain one episode root and one shared journal.

## Explicit experimental options

- `--host fixture`: injected answer replay, never actual host reasoning evidence.
- `--host cpa`: explicit live experiment with matching admission and CPA credential; no automatic fallback from current-agent. Legacy relationship live CLI calls now also require explicit `--host cpa`.
- In current-agent mode the host configuration is `current-agent-handoff.v1`, with no vendor/model/endpoint requirement. Admission must bind this host configuration; an old CPA freeze cannot silently become a current-Agent run.

## What this does and does not establish

Programmatic commitment, actual file loading, a resumable current-Agent request and validated response are implemented. Judgment provider liveness and local host transport are independent. Existing Noul/Choice/Score questions, method definitions and Skills/display semantics are unchanged. The default non-Jev Skill and main branch remain unchanged.

This is a tool-capable host integration port, not automatic native installation for every Agent product. A host must actually read and execute the request and submit its result; merely showing a prompt remains advisory. Receipt conformance does not prove semantic method fidelity, factual correctness, or task completion. Tests use injected judgments/text unless an evidence record explicitly states current-Agent authorship; they are not a new Jev real-world benchmark. The previously platform-blocked paid batch is retained unrun and is not bypassed by this implementation.
