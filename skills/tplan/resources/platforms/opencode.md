# OpenCode Role-Separated Review Adapter

This is platform support for `tplan` Role-Separated Review Policy. It is outside
`tplan core`: it turns `advise`, `grade`, and `dream` into OpenCode reviewer carriers
when the Mission boundary justifies stronger isolation.

## Documentation-Backed Capability Surface

OpenCode has primary agents, subagents, `@` invocation, custom agents in
`.opencode/agents/`, built-in read-only `explore` and `scout` subagents, and per-agent
permissions. The official docs describe `edit: deny`, task permission controls, and
custom markdown agents, which makes OpenCode a viable `tplan` review carrier.

Use this adapter only as a carrier layer. These are documentation-backed capabilities,
not proof that a generated agent has been installed or executed in the user's OpenCode
environment. It does not change Mission schema, evidence rules, or final authority.

References:

- https://open-code.ai/en/docs/agents
- https://opencode.ai/docs/config/

## Core Boundary

OpenCode reviewers are carriers, not controllers.

- The main agent executes Mission work and owns final decisions.
- `tplan-advisor`, `tplan-grader`, and `tplan-dreamer` return candidate findings only.
- Reviewer agents must not edit files, Mission state, evidence, task tree, decisions,
  memory, or external systems.
- The main agent verifies, merges, records evidence, mutates Mission state, and writes
  the final user-facing conclusion.

## Interaction Guard Status

This repository does not currently provide a verified OpenCode native lifecycle-hook
mapping for mid-turn messages. Use the prompt fallback in
`resources/interaction-host-contract.md` and report `advisory_only`. OpenCode reviewer
support below does not imply interaction-guard enforcement.

## Script

Use `scripts/platform_review_packet.py` to generate OpenCode carrier artifacts:

```bash
python3 skills/tplan/scripts/platform_review_packet.py MISSION_DIR \
  --platform opencode \
  --role grade \
  --output-dir /tmp/tplan-opencode-review \
  --repo-root .
```

The script writes:

- `opencode-<role>-review-packet.json`: machine-readable Mission review packet.
- `opencode-<role>-reviewer-agent.md`: project/user subagent markdown.
- `opencode-<role>-delegation-prompt.md`: prompt for invoking the reviewer.
- `opencode-<role>-config-snippet.json`: optional `opencode.json` agent snippet.
- `opencode-<role>-install-notes.md`: install and authority boundary notes.

Install generated agent markdown under `.opencode/agents/` only when the extra
isolation cost is worth it. Keep reviewer permissions read-only: deny `edit`, deny
nested `task` delegation, deny `bash`, and use OpenCode native `read` / `glob` /
`grep` / `list` permissions for bounded inspection.

## OpenCode Orchestration Mode

Generate an orchestration plan with:

```bash
python3 skills/tplan/scripts/platform_review_packet.py MISSION_DIR \
  --platform opencode \
  --orchestration-mode recommended \
  --output-dir /tmp/tplan-opencode-review \
  --repo-root .
```

`recommended` mode creates packets for `advise`, `grade`, and `dream`, marks `grade`
required, and marks `advise` / `dream` conditional.

For stricter Mission boundaries:

```bash
python3 skills/tplan/scripts/platform_review_packet.py MISSION_DIR \
  --platform opencode \
  --orchestration-mode strict \
  --output-dir /tmp/tplan-opencode-review \
  --repo-root .
```

`strict` mode marks `advise` and `grade` required, while `dream` remains conditional
until a learning sink is being recorded.

This is not a mandatory four-agent runtime. `execute` remains with the main agent.
OpenCode subagents are boundary-triggered reviewers whose output still requires
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
