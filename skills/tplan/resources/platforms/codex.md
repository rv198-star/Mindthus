# Codex Role-Separated Review Adapter

This is platform support for `tplan` Role-Separated Review Policy. It is outside
`tplan core`: it provides stronger Codex carriers for `advise`, `grade`, and `dream`
without changing Mission schema or final authority.

## Core Boundary

Codex reviewers are carriers, not controllers.

- The main agent executes Mission work and owns final decisions.
- Codex SubAgents or clean CLI runs return candidate findings only.
- Reviewer carriers must not edit files, Mission state, evidence, task tree, decisions,
  memory, or external systems.
- The main agent verifies, merges, records evidence, mutates Mission state, and writes
  the final user-facing conclusion.

## Interaction Guard Adapter

Interaction protection is defined by the platform-neutral
`resources/interaction-host-contract.md`, not by Codex semantics. Codex has three
separate lifecycle profiles:

- `codex-desktop`: experimental Desktop hook mapping for `UserPromptSubmit`,
  `PreToolUse`, and `Stop`; it has its own certification record.
- `codex-cli`: experimental CLI hook mapping for the same event names, but it does
  not inherit Desktop lifecycle evidence.
- `scripts/codex_interaction_adapter.py`: explicit host/IPC integration seam for a
  host that owns message IDs, thread binding, completion, and receipt signing.

Choose exactly one lifecycle carrier for a Mission. Do not run the native hook and
`codex_interaction_adapter.py` together: they use different delivery semantics and a
guard intentionally rejects competing platform/session bindings.

Generate an experimental Mission-scoped hook configuration for the target surface:

```bash
python3 skills/tplan/scripts/generate_interaction_hooks.py MISSION_DIR \
  --platform codex-desktop --state-dir HOST_PROTECTED_STATE_DIR --experimental

python3 skills/tplan/scripts/generate_interaction_hooks.py MISSION_DIR \
  --platform codex-cli --state-dir HOST_PROTECTED_STATE_DIR --experimental
```

Merge the generated `hooks` object into a trusted Codex hook layer only for a recorded
E2E. The first prompt starts active-turn tracking; another prompt before `Stop` opens
the guard. Subsequent new local tool invocations are denied unless they are on the
Codex-specific read-only or exact safe-control allowlist, and supported TPlan writers
independently fail closed until resolution. The first **owning** `Stop` directly
restores the unchanged baseline with CAS and digest checks, then returns ordinary hook
success. It must not request, emit, or depend on a synthetic continuation. Turn mismatch
or hook failure leaves the Mission locked as `orphaned` but never traps the conversation.

The host owns the lifecycle. It must call `message-arrived` **before** any later
mutable TPlan action, with an explicit `thread_id -> mission_dir` binding. The adapter
persists that supplied thread id into the open guard and rejects later cross-thread
completion; it does not discover or authenticate the initial binding. It must then
call exactly one completion disposition on normal response, abort, error, or
compaction: `response-resume-original`, `response-awaiting-confirmation`,
or `response-stop`.

Example read-only interruption:

```bash
python3 skills/tplan/scripts/codex_interaction_adapter.py message-arrived MISSION_DIR \
  --thread-id THREAD --message-ref MESSAGE

python3 skills/tplan/scripts/codex_interaction_adapter.py response-resume-original MISSION_DIR \
  --thread-id THREAD --guard-id IG... --expected-revision 1 --message-ref MESSAGE
```

An exact Plan change is mechanically two-stage. The host first keeps the guard open
while the agent shows a complete proposal. Only a **new, still-pending** user message
received after that proposal can be confirmed. The host signs a one-time authority
receipt through a host-only signer or IPC capability (with a secret outside
agent-controlled state), then invokes the runtime verifier inside that trusted host
boundary. The receipt binds the guard, revision, baseline,
proposal, complete decision digest, exact mutation digest, and confirmation reference;
agent-generated prose is not an authority receipt. Neither CLI adapter exposes an
`apply` command or accepts a verifier-secret environment variable, because an
agent-invocable process cannot constitute a host-only authority boundary.

Use `capabilities` to expose the contract. `tplan_api_mutation_prevention` applies only
when a real host wires both lifecycle callbacks, protects its signing capability, and
routes Mission writes through the guarded runtime APIs. Raw filesystem writes are not
contained by this Python adapter; a host that needs that guarantee must sandbox Mission
files.

Managed Codex hooks are valuable source-integrity controls, but they are not an
authority signer. Codex documents command-hook input as ordinary JSON and does not
document a host-signed callback credential. A separate macOS user, root-owned Hook
script, or helper service is insufficient by itself: the Agent and the Hook child
share the Codex host principal and can reproduce an agent-invocable request. Do not
deploy such a helper as evidence of trusted authority. The required integration is a
host-native signer/IPC that accepts only an unforgeably authenticated lifecycle event,
owns state writes and receipt issuance, and exposes no equivalent Agent tool path.

Generated configuration and contract tests are not a real-host E2E result. All hook
profiles currently require `--experimental`; report a concrete Desktop or CLI version
as `mutation_prevention` only after that profile's separate E2E gate passes. Do not
infer Desktop support merely because it bundles a Codex binary, or infer CLI support
from a Desktop trace.

When the carrier supports MCP registration, run the Mission-bound
`scripts/tplan_guard_control_server.py` as server name `tplan_guard`. It exposes only
`inspect`, `await_proposal`, and `stop_fixed`; `resume_original` stays outside the
Agent tool surface. Without MCP registration, the deterministic `TPLAN_CONTROL`
operator envelope is the recovery route.

For Desktop E2E, merge the emitted JSON into the trusted project hook layer, restart
the app if it has not loaded the project layer, and explicitly trust the exact
non-managed command-hook hash in the Hooks manager. Record the app build, profile
digest, hook source/hash, trust state, state-directory isolation, and all active hook
sources before asserting a capability. Remove the temporary E2E hook after the run;
it is not a default-on project configuration.

Codex does not re-run `PreToolUse` when `write_stdin` sends input to an execution that
started before the guard, and specialized tool paths may bypass the normal local-hook
path. Generated hooks alone therefore do not satisfy the prevention claim unless the
host also terminates/isolates pre-existing mutable executions and protects hook state.

Official hook reference: https://learn.chatgpt.com/docs/hooks

## Script

Use `scripts/codex_review_packet.py` to generate concrete Codex review artifacts:

```bash
python3 skills/tplan/scripts/codex_review_packet.py MISSION_DIR \
  --role grade \
  --output-dir /tmp/tplan-codex-review \
  --repo-root .
```

The script writes:

- `codex-<role>-review-packet.json`: machine-readable Mission review packet.
- `codex-<role>-subagent-prompt.md`: prompt for a read-only Codex SubAgent.
- `codex-<role>-subagent-dispatch.json`: structured payload for a main agent to
  dispatch a Codex explorer/reviewer.
- `codex-<role>-cli-prompt.md`: prompt for a clean Codex CLI review.
- `codex-<role>-cli-command.sh`: executable command template using
  `codex -s read-only -a never exec --ephemeral`.

For stronger isolation, explicitly run the CLI carrier:

```bash
python3 skills/tplan/scripts/codex_review_packet.py MISSION_DIR \
  --role grade \
  --output-dir /tmp/tplan-codex-review \
  --repo-root . \
  --run-cli
```

`--run-cli` executes an ephemeral Codex CLI review and stores stdout, stderr, and final
review output under the adapter output directory. The generated reviewer turn uses the
Codex `read-only` sandbox so model-generated shell commands cannot mutate the repo;
the adapter still writes the captured final review through the CLI output file. This
can be expensive; use it when context contamination risk justifies the cost.

`--run-cli` is only for a single `--role` packet. Orchestration mode generates carrier
artifacts and a plan; the main Codex host decides which required or conditional
reviewers to dispatch.

## Codex Review Orchestration Mode

When `tplan` is actively used on Codex, the recommended Codex tplan path is not to ask
"whether review is needed" from scratch. Instead, ask which Mission boundary needs a
reviewer carrier and which carrier can be skipped.

Generate an orchestration plan with:

```bash
python3 skills/tplan/scripts/codex_review_packet.py MISSION_DIR \
  --orchestration-mode recommended \
  --output-dir /tmp/tplan-codex-review \
  --repo-root .
```

`recommended` mode creates packets for `advise`, `grade`, and `dream`, marks `grade`
required, and marks `advise` / `dream` conditional. This is the recommended Codex
tplan path for ordinary long-running Missions because acceptance is where self-approval
is most likely to collapse judgment.

For stricter Mission boundaries:

```bash
python3 skills/tplan/scripts/codex_review_packet.py MISSION_DIR \
  --orchestration-mode strict \
  --output-dir /tmp/tplan-codex-review \
  --repo-root .
```

`strict` mode marks `advise` and `grade` required, while `dream` remains conditional
until a learning sink is being recorded.

This is not a mandatory four-agent runtime. `execute` remains with the main agent.
Reviewer carriers are boundary-triggered:

- `advise`: before route changes, same-path continuation under uncertainty,
  stop/switch decisions, repeated failure, or Mission alignment doubt.
- `grade`: before closure, release, handoff, method change, authority-sensitive
  completion, or meaningful acceptance claims.
- `dream`: before recording reusable learning, Mission Shared Context, Shared Risk
  Context, issue candidates, or regression candidates.

Skip rules remain explicit:

- Skip reviewer dispatch for a low-risk lite Mission when direct evidence is obvious
  and review would not change action, evidence, risk handling, or closure.
- Skip `dream` review when no learning or memory candidate is being recorded.
- Skip `advise` review when route, continuation, and Mission alignment are already
  supported by fresh evidence and no switch/stop decision is pending.

## Role Mapping

- `advise`: direction-checking. Checks route, risk, continuation ROI, Mission
  alignment, and next gate. It does not grade acceptance.
- `grade`: acceptance-grading. Checks acceptance criteria, rubric, evidence links, and
  closure justification. It does not execute the work.
- `dream`: learning-candidate review. Proposes Mission Shared Context, Shared Risk
  Context, issue, or regression candidates. It does not write memory directly.

## When To Use

Use Codex adapter review for high-risk, release-facing, authority-sensitive,
method-design, repeated-failure, or meaningful closure claims.

Do not use it for simple, reversible tasks where direct evidence is obvious and the
review would not change action, evidence, risk handling, or closure.

## Acceptance Discipline

Reviewer output is not acceptance evidence by itself. To use it in a Mission:

1. Main agent reads the reviewer output.
2. Main agent verifies referenced files, tests, evidence links, and claims.
3. Main agent records a normal tplan evidence event only for verified findings.
4. Main agent applies any decision through existing tplan decision surfaces.

Do not claim paper-level or benchmark-level improvement from this adapter without a
separate evaluation.
