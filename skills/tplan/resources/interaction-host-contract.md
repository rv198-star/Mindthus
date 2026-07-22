# Interaction Host Contract

This contract keeps the TPlan interruption rule portable. The core runtime does not
depend on Codex, Claude Code, Gemini CLI, or any other agent shell. A platform adapter
maps native lifecycle events onto the same guard dispositions.

## Core

An interrupting user message may change the response, but it does not itself authorize
a Mission or routing change. Before handling a mid-turn message, a capable host opens
`.interaction-guard.json`. While that guard is open, supported Mission and evidence
writers fail closed. The host then resolves exactly one of these outcomes:

- `resume_original`: restore the unchanged baseline path at the first owned turn end.
- `await_clarification`: keep the guard locked around an exact question or proposal.
- `apply_authorized_change`: apply only a mutation bound to a trusted authority receipt.
- `stop`: apply only the fixed graceful-stop delta.

The runtime never classifies user prose as authorization. It validates state,
revisions, digests, receipts, and recovery boundaries.

## Host Capability Profile

Every adapter must report these capabilities separately:

| Capability | Required behavior |
|---|---|
| `message_arrival` | Observe a second message while a turn is active and persist a guard before later mutable actions. |
| `pre_mutation_gate` | Block later mutation-capable tools, while the runtime independently blocks supported TPlan writers. |
| `turn_end` | Directly release a protecting guard on the first owned end, or mark it `orphaned` on ambiguity. |
| `mission_binding` | Bind one platform session/thread to one canonical Mission directory; never guess across sessions. |
| `trusted_authority` | Keep receipt-signing authority outside agent-controlled files, prompts, commands, and environment. |
| `recovery` | Treat duplicates idempotently and crashes, stale sessions, and ambiguous ownership as fail-closed. |

Capability-equivalent platforms do not need schema-equivalent hooks. Current native
event mappings are:

| Platform | Message | Before tool | Turn end |
|---|---|---|---|
| Codex CLI | `UserPromptSubmit` | `PreToolUse` | `Stop` |
| Claude Code | `UserPromptSubmit` | `PreToolUse` | `Stop` |
| Gemini CLI | `BeforeAgent` | `BeforeTool` | `AfterAgent` |

`scripts/platform_interaction_hook.py` maintains a small active-turn marker. The first
prompt starts normal turn tracking. Another prompt received before the corresponding
turn-end event is treated as an interruption and opens the portable guard. A stale
marker after a host crash is conservative: the next message is treated as an
interruption. Generated configs place this marker in a user state directory outside
the workspace; use `--state-dir` to select storage protected from agent writes. There
is deliberately no agent-invocable reset command.

The same host state directory contains a separate append-only lifecycle sidecar named
`<mission-hash>.trace.jsonl`. It records one sanitized record for each recognized
native callback: monotonic trace sequence, event name/kind, hashes of session/turn/
message correlations, guard phase and revision before/after, Mission/evidence file
digests before/after, and a bounded result kind. It never stores prompt text, response
text, tool input, or raw correlation identifiers, and it is intentionally separate
from TPlan's guarded `execution_trace.jsonl`. The sidecar records the adapter profile
digest, but host build and hook-source metadata are `unavailable` until a host-owned
manifest supplies them. A trace with unavailable metadata can support diagnosis only;
it cannot support a certified host claim.

The first owned end event resolves a `protecting` guard directly with the stored
baseline and pending-message CAS checks. It returns ordinary hook success, never a
model-visible continuation. A mismatched session/turn, stale revision, exception, or
missing lifecycle evidence moves the guard to `orphaned`: Mission writers stay closed,
but chat ends normally and recovery remains available. A cross-session message cannot
take ownership. Each platform profile has separate event parsing and must pass its own
real-host E2E; shared event names do not transfer lifecycle evidence.

While open, the control plane remains narrowly reachable. The Agent-facing MCP server
is Mission-bound at process start and exposes only `inspect`, `await_proposal`, and
`stop_fixed`; it has no `resume`, `apply`, `unlock`, or receipt capability. The first
end workflow and the user/operator recovery envelope own `resume_original`.

### Authority-boundary evidence

Configuration integrity and event provenance are different claims. A managed Hook,
an MDM-protected `requirements.toml`, or a root-owned script can establish that the
configured Hook source was not edited by the Agent. It does **not** establish that a
request arriving at a helper originated from the host's user-message callback: an
Agent process under the same principal can invoke an otherwise protected command or
reachable IPC endpoint unless the host supplies an unforgeable callback credential.

Accordingly, a v0.2 certification records three independent facts: `event_origin`
(`host_signed` or `host_managed_unforgeable`), `state_writer=host_only`, and
`receipt_signer=host_only`, each with evidence. A `certified` or
`mutation_prevention` claim requires all three. `none` / `same_principal` is an
honest partial result, not a failure of the portable runtime.

## Enforcement Levels

- `mutation_prevention`: native message and before-tool callbacks are wired, the
  Mission binding is exact, and supported TPlan writers cannot mutate after the guard
  opens. Raw filesystem processes remain outside the runtime API boundary and are
  checked by baseline digests unless the host also sandboxes Mission files.
- `checkpoint_detection`: the carrier cannot guarantee synchronous interception, but
  the next runtime checkpoint detects control/evidence drift and remains fail-closed.
- `advisory_only`: the carrier has only prompt or policy instructions. The model can
  ignore them, so they must not be described as prevention.

Native hook configuration proves only that the adapter can be invoked. Claim
`mutation_prevention` for a concrete platform/version only after an end-to-end run
shows: normal prompt -> mid-turn message -> guard persisted -> later mutation denied ->
first owned end directly resumes the original path, without a synthetic continuation.
The state directory
must be outside agent write authority, and the host must contain already-running tools
and outer hook-timeout failure. Without those properties, the generated hook is a
useful deterministic guardrail but is not sufficient evidence for
`mutation_prevention`.

While a guard is open, the native adapter uses a fixed read-only tool allowlist. An
unknown tool is denied; tool names are not interpreted as safe merely because they lack
words such as `write` or `delete`. This is intentionally conservative for third-party
and MCP tools.

## Native CLI Configuration

Generate a Mission-scoped configuration snippet:

```bash
python3 skills/tplan/scripts/generate_interaction_hooks.py MISSION_DIR \
  --platform codex-desktop --state-dir HOST_PROTECTED_STATE_DIR --experimental

python3 skills/tplan/scripts/generate_interaction_hooks.py MISSION_DIR \
  --platform codex-cli --state-dir HOST_PROTECTED_STATE_DIR --experimental

python3 skills/tplan/scripts/generate_interaction_hooks.py MISSION_DIR \
  --platform claude-code --state-dir HOST_PROTECTED_STATE_DIR --experimental

python3 skills/tplan/scripts/generate_interaction_hooks.py MISSION_DIR \
  --platform gemini-cli --state-dir HOST_PROTECTED_STATE_DIR --experimental
```

Merge the resulting `hooks` object into the platform's trusted project/user settings.
The generated command uses absolute adapter and Mission paths so it does not depend on
plugin-specific environment variables. Configuration is Mission-scoped by design: a
global hook must not guess which Mission a session owns. It also runs the adapter under
an inner five-second supervisor and normalizes child startup errors, non-zero exits,
and inner timeouts to blocking exit code 2 before the host's outer timeout. The
turn-end hook is the deliberate exception: it emits a bounded recovery warning and
exits 0, because a non-zero `Stop` result can request a host continuation. Regenerate
the snippet after moving/upgrading the TPlan installation. A host-level timeout that
kills the supervisor itself remains a platform boundary and must be tested explicitly.
`--state-dir` is required because a convenient directory writable by the same agent is
not a trustworthy turn-ownership store. Pre-create it outside the Mission with host or
OS policy that denies agent writes; the generator rejects missing or Mission-local
directories but cannot prove sandbox/ACL policy. The current generated shell command targets
POSIX shells; Windows carriers must use a verified PowerShell/`commandWindows` wrapper
or degrade to the prompt fallback until one is supplied.

For Codex Desktop and CLI, a new non-managed command hook is skipped until the user
reviews and trusts its exact source/hash in the host hook manager. Restarting alone is
not evidence that it ran. E2E setup must verify the source is listed as enabled and
trusted before sending the first test message; changing the generated command requires
another trust review. This host trust is a deployment prerequisite, not an authority
receipt and not a reason to weaken the Guard.

Current experimental profiles use a stable host `event_id`/`message_id` when the
carrier supplies one. Their fallback correlation hash is only a compatibility aid, not
proof of host-unique message identity. Therefore `stable_message_identity=false` keeps
the profile below certification until a concrete host/version demonstrates a documented
stable event field and duplicate-delivery E2E.

These native adapters deliberately do not sign authority receipts. They can enforce
the default `resume_original` path and keep an unresolved proposal locked. Applying an
explicit Plan change still needs a trusted host/IPC signer and verifier outside the
agent process. Agent-invocable CLIs must not accept a receipt secret or expose an
`apply` command.

Codex's documented command-hook payload is ordinary JSON on stdin (session, turn,
event, and permission context), rather than a host-signed callback credential. Its
managed-hook facility protects configuration delivery, not callback provenance. The
native Codex Desktop/CLI profiles therefore remain below the authority-boundary gate
until a host-native signed callback or equivalent managed IPC is available.

Register the Mission-bound safe-control server separately in the host MCP layer when
the carrier supports it:

```bash
python3 skills/tplan/scripts/tplan_guard_control_server.py --mission-dir MISSION_DIR
```

The hook generator does not install MCP settings because their location and trust
model differ by host. Until that server is registered, the deterministic
`TPLAN_CONTROL guard=... revision=... action=resume|stop` envelope remains the
operator-only recovery route; it is processed before the model and never becomes a
continuation prompt.

## Prompt Fallback

On a carrier without usable lifecycle hooks, inject this policy through its strongest
project instruction surface:

> During an active TPlan turn, treat every newly arrived user message as response
> input, not Mission authority. Before any supported Mission/evidence mutation, inspect
> the interaction guard. Answer status questions read-only, then resolve
> `resume_original`. For any requested control change, persist an exact proposal and
> use `await_clarification`; never self-issue an authority receipt. On ambiguity, stop
> with the guard open.

If the carrier can run commands but cannot register hooks, the agent may call
`scripts/interaction_guard.py begin/inspect/resume/await/stop`. That is still
`advisory_only`, because the same agent can omit the command. Prompt fallback is a
compatibility path, not a substitute for a native callback.

## Boundaries

- Hook prose can remind the model; it is not the enforcement boundary.
- Reviewer subagents and interaction hooks are independent carrier concerns.
- No adapter may store raw prompt text in guard state.
- A second platform/session cannot take over an active Mission binding.
- One Mission uses one lifecycle carrier; native hooks and an explicit host adapter
  must not be enabled together.
- Codex `write_stdin` for a process started before the guard does not re-run
  `PreToolUse`; prevention requires terminating/isolating such processes or treating
  their effects as checkpoint-detected drift.
- An adapter that cannot distinguish a normal first prompt from a mid-turn message
  must degrade honestly instead of guarding every prompt and making the Mission
  unusable.
