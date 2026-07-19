# H2.1 Live Runbook

## Before C1

1. Commit the implementation, protocol, cases, fixture lock, and static evidence.
2. Build `2.0-routing-h2-single-entry` from that exact commit.
3. Record candidate commit, repository cleanliness, package tree digest, plugin manifest,
   correction diff, Stable source digest, focused/full test results, and diagnostic.
4. Create fresh isolated homes/workspaces. Install only `mindthus-beta@mindthus-beta`.
5. Confirm candidate version `2.0.0-next.4`, one discoverable Skill, seven resource
   owners, empty project instructions, and no repository/Stable path in the workspace.

## Calls

- Use `/usr/bin/perl -e 'alarm shift; exec @ARGV' 900` around every Codex call.
- Use `codex exec --json`, Sol, xhigh, approval `never`, danger-full-access sandbox,
  and the isolated workspace as both process cwd and Codex `-C` directory.
- Reject a Generator above 275,000 counted tokens and a Judge above 200,000. The
  authorized 400,000 outer maximum does not override these phase rejection lines.
- C1 Q2 must use `codex exec resume <exact-q1-thread-uuid>` from the same isolated cwd.
- C1 uses one candidate-only home/workspace/thread for Q1/Q2. C2, C3, and each Q3-Q7
  case use separate fresh candidate-only homes, sessions, and workspaces.
- If comparison activates, Stable mirrors that topology exactly: one Stable-only home
  for Q1/Q2 and one fresh Stable-only home for each Q3-Q7 case.
- Persist stdout JSONL, stderr, final message, raw rollout metadata, and usage immediately.

## Gate sequence

1. C1 Q1/Q2. Stop on failure.
2. C2. Stop on failure.
3. C3. Stop on failure.
4. Q3-Q7 in order. Stop on first failure.
5. Only after all pass, run Stable Q1-Q7 under matched isolation.
6. Only after both arms are complete, run one paired Judge per case.
7. Apply the frozen unresolved-Judge rule: more than one unresolved case stops
   unproven; exactly one may use the reserved eighth Judge once.
8. Apply the frozen cache-noise rule only when its observable 0.50 cache-fraction trigger
   fires on the seven-case median-determining case. Q1/Q2 cannot use the two-call review
   reserve; an eligible Q3-Q7 case is rerun once on both arms in mirrored fresh homes.

No live repair, prompt change, fixture change, candidate rebuild, extra architecture, or
release action is allowed after C1 starts.
