# Gemini CLI Interaction Guard Adapter

Gemini CLI is a first-class interaction carrier for the platform-neutral TPlan guard.
It is not a different Mission model and does not gain authority over Plan changes.

## Native Event Mapping

- `BeforeAgent`: track a normal first prompt or open a guard for a second mid-turn
  message.
- `BeforeTool`: deny mutation-capable tools while the guard is open.
- `AfterAgent`: directly resolve `resume_original` at the first owned end when the
  baseline and all pending messages still match; otherwise mark the guard `orphaned`
  and end normally, without a retry prompt.

Generate a Mission-scoped Gemini `settings.json` snippet:

```bash
python3 skills/tplan/scripts/generate_interaction_hooks.py MISSION_DIR \
  --platform gemini-cli --state-dir HOST_PROTECTED_STATE_DIR --experimental
```

Merge the generated `hooks` object into a trusted Gemini CLI settings layer. The
adapter uses Gemini's millisecond timeout unit and native top-level `decision: deny`
shape for `BeforeTool`.

The native carrier never interprets prompt text as permission and never signs an
authority receipt. An explicit Plan change must stay in `await_clarification` until a
trusted external host authorizes the exact proposal. If hooks are unavailable, use the
prompt fallback from `resources/interaction-host-contract.md` and report
`advisory_only`.

The official Gemini CLI hook reference documents `BeforeAgent`, `BeforeTool`, and
`AfterAgent`. Generated configuration and unit tests do not replace a concrete-version
E2E before claiming `mutation_prevention`; this profile remains experimental:
https://geminicli.com/docs/hooks/reference/

## Boundaries

- Gemini hook schemas differ from Codex and Claude Code; only the TPlan disposition
  contract is shared.
- The adapter protects supported future actions after guard persistence. It cannot
  undo a tool that completed before the interrupting message arrived.
- Raw writes outside guarded TPlan APIs require host sandboxing for prevention; the
  baseline digest provides checkpoint detection.
- Reviewer-agent support is a separate feature and is not implied by this adapter.
