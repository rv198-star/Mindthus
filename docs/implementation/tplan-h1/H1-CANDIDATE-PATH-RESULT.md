# H1 candidate content path repair — source result

## Result

The candidate storage operation now uses held directory descriptors for all
reads, directory creation, staging, publication, cleanup and directory fsync.
Checking a path and opening that string later is no longer its security boundary.
The prior same-SHA ancestor-symlink probe passes against the changed source.

This is a candidate-filesystem repair. It does not supply authenticated Owner
events, Host/Member privilege separation, a trusted signer, or live DSH evidence.
The Host trust seam remains disabled.

## Changes

- Walk the selected absolute Mission path and `artifacts/h1` one directory at a
  time with `O_DIRECTORY | O_NOFOLLOW`, retaining the current descriptor.
- Create only the two store directories; resolve later names relative to the
  retained descriptor. Replacing an ancestor cannot redirect a later open,
  link, unlink or fsync to the outside directory.
- Publish immutable bytes with the existing create/link design. Remove the
  staging link before checking that the permanent file has exactly one link.
- Refuse symlink/hardlinked/nonregular leaf files and enforce the byte bound
  both before and after reading, then verify the SHA. Unsupported filesystem
  primitives fail closed.
- Preserve canonical H1 command fields, candidate identities, transaction
  authority, receipt semantics and the disabled live trust boundary.

## Evidence from local temporary filesystems

The first 14 tests were run against the original source before changing it:
7 passed, 6 failed and 1 errored. The failures exposed the prior read redirection,
ancestor-following path, hardlink acceptance, post-stat growth and outside
publication. The error exposed string-path verification after a staging swap.

After the repair, the complete 16-test `test_h1_candidate_paths.py` suite passed
with no failures or skips. It covers stable roundtrip/idempotence, the original
same-SHA ancestor attack, fixed-inode reads during a later ancestor swap, static
ancestor/leaf symlinks, hardlinks, FIFO/directory leaves, size and growth bounds,
staging/publication/cleanup confinement, descriptor cleanup, immutable digest
conflict, and unsupported secure primitives.

The unchanged AIWork `probe_h1_candidate_ancestor.py` also passed (1 test). All
bytes and Mission paths in these checks were synthetic temporary files; no real
Mission, installed Skill, external account or service was used. The parent
integration records remote affected-H1 regression and combined-chain evidence
separately on the final source commit; this note does not claim those runs early.

## Remote affected-H1 verification — 2026-10-21

The final source files were copied into the independent OCI worktree based on
`1da99d96c37c8e20899943a0c7e348079e30e2fd`. Python 3.12 ran all four
`tests/tplan/test_h1*.py` modules: **84 PASS, 0 FAIL, 0 SKIP**. This includes
the 16 new path cases, existing canonical H1 commands, result/completion, and
legacy writer protection. Command:

```sh
/srv/agentdock/.local/bin/python3.12 -m unittest discover -s tests/tplan -p 'test_h1*.py' -v
```

The output is in
[`evidence/candidate-path-h1-python312.txt`](evidence/candidate-path-h1-python312.txt).
The unchanged AIWork ancestor-replacement probe also passed against this
worktree (one case); its evidence is retained in the paired AIWork integration
slice. No broader historical suite is counted as a run on this source.

## Operational boundary

A descriptor can keep reading or writing the original directory after that
directory is renamed. That prevents redirection; it does not guarantee that the
old pathname remains connected or that a subsequent operation can use it. The
trusted Host must still protect the Mission and its ancestors from Member writes.

A process crash specifically between creating the permanent hardlink and
unlinking the staging name can leave two names for the same inode. The
single-link guard rejects that content until controlled recovery resolves the
staging artifact. This slice deliberately does not delete historical files or
guess which external hardlink is trusted. A failed publication may also leave
unreferenced immutable content, as before; no canonical acceptance is inferred
from its existence.

## Review boundary

Self-review found no remaining string-path operations in candidate content IO.
The wider canonical Mission writer and Host OS isolation are outside this
change. No historical full-suite result is presented as a result on this source.
