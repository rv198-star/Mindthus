# Worktree Lifecycle

Audit date: `2026-06-28`

`git worktree list` currently shows 2 worktrees including the main workspace, or 1
non-main worktree. The repository-local `.worktrees/` entries were removed during the
`2026-06-28` maintenance pass. One detached Codex worktree remains outside the
repository tree.

## Rules

1. Keep a worktree when it is the current active workspace or an intentionally retained,
   app-managed environment.
2. Remove a worktree only when all three are true:
   - the worktree is clean;
   - it is not detached;
   - the branch or context is already merged, clearly superseded, or no longer needs a
     dedicated checkout.
3. Do not remove a dirty or detached worktree blind. Audit its local changes first.
4. After each release or audit wave, run a quick maintenance pass:
   - `git worktree list --porcelain`
   - `git branch --merged main --format='%(refname:short)'`
   - `git status --short` inside each non-main worktree that looks removable

## Current Classification

### Keep

- `main`:
  current active workspace.
- external detached Codex worktree:
  intentionally retained because it is app-managed and still dirty; it should not be
  removed from the repository side without a deliberate review of its local files.

### Archive Or Review Before Removal

- local branch refs without attached worktrees:
  historical branches such as `codex/fix-codex-install-skills`,
  `codex/issue-33-tplan-continuation-authorization`,
  `codex/issue-49-tplan-mission-shared-context`, `codex/release-v1.1.1`,
  `codex/router-wakeup-canary`, `codex/tplan-shared-risk-context`, and
  `codex/v0.9-method-fidelity-harness` are now archive refs only. Keep or delete those
  refs based on branch-level value, but they no longer need dedicated worktrees.

### Removed In This Cleanup

These repository-local worktrees were removed during the `2026-06-28` maintenance
pass. Their branch refs were left unattached unless already deleted earlier:

- `codex/fix-codex-install-skills`
- `codex/issue-33-tplan-continuation-authorization`
- `codex/issue-49-tplan-mission-shared-context`
- `codex/release-v1.1.1`
- `codex/router-wakeup-canary`
- `codex/tplan-shared-risk-context`
- `codex/v0.9-method-fidelity-harness`
- earlier cleanup history still includes `codex/issue-27-thin-core-tplan-adapter`,
  `codex/issue-33-tplan-continuation-mainline`, and `release/v0.6.2-prep`

### Remove Candidates

After the `2026-06-28` cleanup, there are no repository-local non-main worktrees left
to prune. The only remaining non-main worktree is the external detached Codex
workspace, which stays in the review bucket because it is dirty and app-managed.

## Lightweight Lifecycle Note

The maintenance goal is not to minimize the worktree count at all costs. The goal is to
keep only worktrees that still carry active checkout value. Historical branch value can
stay as a plain ref without paying the cost of a dedicated worktree. If a worktree is
merged or superseded, clean, and no one can name why it needs its own checkout, remove
the worktree and keep the branch ref only if that history still matters.
