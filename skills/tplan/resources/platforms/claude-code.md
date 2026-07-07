# Claude Code Role-Separated Review Adapter

This is platform support for `tplan` Role-Separated Review Policy. It is outside
`tplan core`: it turns `advise`, `grade`, and `dream` into Claude Code reviewer
carriers when the Mission boundary justifies stronger isolation.

## Documentation-Backed Capability Surface

Claude Code custom subagents are a reasonable carrier for `tplan` review roles because
the official docs describe a fresh context window, custom system prompt, tool access,
and independent permissions. Claude Code also supports project/user subagent files,
explicit `@agent-...` invocation, `--agent`, subagent lifecycle hooks, and
`permissionMode: plan`.

Use this adapter only as a carrier layer. These are documentation-backed capabilities,
not proof that a generated agent has been installed or executed in the user's Claude
Code environment. It does not change Mission schema, evidence rules, or final
authority.

References:

- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/settings

## Core Boundary

Claude Code reviewers are carriers, not controllers.

- The main agent executes Mission work and owns final decisions.
- `tplan-advisor`, `tplan-grader`, and `tplan-dreamer` return candidate findings only.
- Reviewer agents must not edit files, Mission state, evidence, task tree, decisions,
  memory, or external systems.
- The main agent verifies, merges, records evidence, mutates Mission state, and writes
  the final user-facing conclusion.

## Script

Use `scripts/platform_review_packet.py` to generate Claude Code carrier artifacts:

```bash
python3 skills/tplan/scripts/platform_review_packet.py MISSION_DIR \
  --platform claude-code \
  --role grade \
  --output-dir /tmp/tplan-claude-code-review \
  --repo-root .
```

The script writes:

- `claude-code-<role>-review-packet.json`: machine-readable Mission review packet.
- `claude-code-<role>-reviewer-agent.md`: project/user subagent markdown.
- `claude-code-<role>-delegation-prompt.md`: prompt for invoking the reviewer.
- `claude-code-<role>-config-snippet.json`: optional lifecycle hook settings snippet.
- `claude-code-<role>-install-notes.md`: install and authority boundary notes.

Install generated agent markdown under `.claude/agents/` or the user-level agent
directory only when the extra isolation cost is worth it. Prefer `permissionMode: plan`
and a read/search-only tool allowlist for reviewer roles.

## Claude Code Orchestration Mode

Generate an orchestration plan with:

```bash
python3 skills/tplan/scripts/platform_review_packet.py MISSION_DIR \
  --platform claude-code \
  --orchestration-mode recommended \
  --output-dir /tmp/tplan-claude-code-review \
  --repo-root .
```

`recommended` mode creates packets for `advise`, `grade`, and `dream`, marks `grade`
required, and marks `advise` / `dream` conditional.

For stricter Mission boundaries:

```bash
python3 skills/tplan/scripts/platform_review_packet.py MISSION_DIR \
  --platform claude-code \
  --orchestration-mode strict \
  --output-dir /tmp/tplan-claude-code-review \
  --repo-root .
```

`strict` mode marks `advise` and `grade` required, while `dream` remains conditional
until a learning sink is being recorded.

This is not a mandatory four-agent runtime. `execute` remains with the main agent.
Claude Code subagents are boundary-triggered reviewers whose output still requires
main-agent verification.

## Role Mapping

- `advise`: direction-checking. Checks route, risk, continuation ROI, Mission
  alignment, and next gate. It does not grade acceptance.
- `grade`: acceptance-grading. Checks acceptance criteria, rubric, evidence links, and
  closure justification. It does not execute the work.
- `dream`: learning-candidate review. Proposes Mission Shared Context, Shared Risk
  Context, issue, or regression candidates. It does not write memory directly.

## Acceptance Discipline

Reviewer output is not acceptance evidence by itself. To use it in a Mission:

1. Main agent reads the reviewer output.
2. Main agent verifies referenced files, tests, evidence links, and claims.
3. Main agent records a normal tplan evidence event only for verified findings.
4. Main agent applies any decision through existing tplan decision surfaces.

Do not claim paper-level or benchmark-level improvement from this adapter without a
separate evaluation.
