# Worktree Lifecycle

Audit date: `2026-06-27`

`git worktree list` currently shows 9 worktrees including the main workspace, or 8
non-main worktrees. Most live under `.worktrees/`; one detached Codex worktree lives
outside the repository tree.

## Rules

1. Keep a worktree when the branch is active, unmerged, or intentionally retained for
   canary / release / historical replay work.
2. Remove a worktree only when all three are true:
   - the worktree is clean;
   - it is not detached;
   - the branch is already merged or clearly superseded by another kept branch.
3. Do not remove a dirty or detached worktree blind. Audit its local changes first.
4. After each release or audit wave, run a quick maintenance pass:
   - `git worktree list --porcelain`
   - `git branch --merged main --format='%(refname:short)'`
   - `git status --short` inside each non-main worktree that looks removable

## Current Classification

### Keep

- `codex/tplan-runtime-hardening`:
  current active workspace; dirty by design because this branch is in progress.
- `codex/fix-codex-install-skills`:
  clean but unmerged; keep until the branch is reviewed or merged.
- `codex/issue-49-tplan-mission-shared-context`:
  clean and unmerged; keep until its remaining delta is intentionally merged or dropped.
- `codex/tplan-shared-risk-context`:
  clean and unmerged; keep because the commit is not contained by the current branch.
- `codex/release-v1.1.1`:
  clean and unmerged; treat as intentionally retained release prep unless explicitly retired.
- `codex/router-wakeup-canary`:
  clean and unmerged; keep as canary / certification context for router wake-up work.

### Archive Or Review Before Removal

- external detached Codex worktree:
  dirty (`docs/superpowers/specs/2026-05-31-tvg-grounded-insight-loop-issue.md`, `ppt/`);
  the commit is contained by `main`, but the local detached state must be reviewed manually.
- `codex/v0.9-method-fidelity-harness`:
  merged into the current branch, but dirty (`.tplan/`); do not remove until the local runtime
  state is either copied out or discarded deliberately.
- `codex/issue-33-tplan-continuation-authorization`:
  clean but unmerged; audit notes describe it as a superseded attempt replaced by the kept
  mainline continuation branch, so archive or remove only after a human confirms the branch is
  no longer needed.

### Removed In This Cleanup

These clean, non-detached worktrees were already merged and were removed during the
`2026-06-27` maintenance pass. Their local branches were deleted with `git branch -d`:

- `issue-10-tvg-grounded-insight-loop`
- `codex/issue-27-thin-core-tplan-adapter`
- `codex/issue-33-tplan-continuation-mainline`
- `codex/pre-1.0-merge-validation`
- `release/v0.6.2-prep`

### Remove Candidates

After the `2026-06-27` cleanup, there are no remaining clean, non-detached worktrees
that are both obviously merged and obviously disposable. The remaining removal pressure
is concentrated in the review bucket: the detached dirty Codex worktree, the dirty
merged `codex/v0.9-method-fidelity-harness`, and the clean but likely superseded
`codex/issue-33-tplan-continuation-authorization`.

## Lightweight Lifecycle Note

The maintenance goal is not to minimize the worktree count at all costs. The goal is to
keep only worktrees that still carry active branch value or intentional historical value.
If a worktree is merged, clean, and no one can name why it must stay, remove it.
