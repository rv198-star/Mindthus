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
