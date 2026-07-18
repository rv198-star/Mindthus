# H2 Qualification Runbook

This runbook executes only the seven frozen cases in `FROZEN-CASES.md`. It is a
case-specific evidence procedure, not a reusable evaluator or telemetry platform.

## Frozen runtime

- model: `gpt-5.6-sol`
- reasoning effort: `xhigh`
- concurrency: `1`
- per-call timeout: `900` seconds
- per-call counted-token ceiling: `200000`
- output: raw Codex `--json`, stderr, and `--output-last-message`
- sandbox: isolated disposable case directories with
  `--dangerously-bypass-approvals-and-sandbox`
- preamble: none; send each prompt verbatim
- user/project rules: no case directory contains `AGENTS.md`; use the isolated
  `CODEX_HOME` and candidate plugin only

Before Q1, record the candidate commit, source/profile/package/manifest hashes,
`fixture-lock.json` verification, Codex version, plugin inventory, and successful
packaged diagnostic. Create seven case directories; copy only the named frozen fixture
into Q4, Q6, and Q7. Record each directory's before hash.

## Invocation form

For Q1 and Q3-Q7, invoke:

```text
CODEX_HOME=<isolated-home> /usr/bin/perl -e 'alarm shift; exec @ARGV' 900 \
  codex exec --json \
  --model gpt-5.6-sol -c model_reasoning_effort='"xhigh"' \
  --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
  --cd <case-directory> --output-last-message <case-final.txt> \
  <verbatim-prompt>
```

Do not use `--ephemeral`: Q1 must persist. Extract Q1's exact UUID from its
`thread.started` JSONL event. Q2 must explicitly invoke:

```text
CODEX_HOME=<isolated-home> /usr/bin/perl -e 'alarm shift; exec @ARGV' 900 \
  codex exec resume <q1-thread-uuid> --json \
  --model gpt-5.6-sol -c model_reasoning_effort='"xhigh"' \
  --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check \
  --output-last-message <q2-final.txt> <verbatim-q2-prompt>
```

Never use `--last`. Run serially and stop at the first critical failure.

## Evidence readout

For each completed call, inspect host JSONL for:

1. `thread.started` identity and completed turn.
2. Exact command/file-read lifecycle for entry, index, and any `OWNER.md`.
3. Fixture evidence read before a consequential write where required.
4. No unrelated owner read and no user-visible routing turn.
5. `turn.completed` usage. Counted tokens are `input_tokens + output_tokens`; uncached
   input is `input_tokens - cached_input_tokens`.
6. Final text and workspace after hash/diff against the frozen before state.

Model claims such as “I used WAE” do not count as activation. If JSONL cannot establish
required reads, record `STOP_UNPROVEN`; do not infer from the answer or build new
telemetry. Before every call, confirm Mission balance can cover that call and all
still-required calls: `remaining_total_tokens >= 200000 * remaining_H2_calls`. A
completed call is charged even if it fails. If one completed call exceeds 200,000
counted tokens, record an authorization violation and immediately map it to
`H2_REJECTED` then `STOP_2X_EXPLORATION`; do not rerun it.

## Terminal mapping

- First trusted semantic failure: `H2_REJECTED` then `STOP_2X_EXPLORATION`.
- Missing trustworthy lifecycle/isolation evidence: `STOP_UNPROVEN` then
  `STOP_2X_EXPLORATION`.
- Seven passes: `H2_ELIGIBLE_FOR_STABLE_COMPARISON`, except explicit owner-coordinate
  compatibility remains a pre-registered critical usability issue.
- If that compatibility choice alone controls continuation: `REQUIRES_WILLIAM`.
