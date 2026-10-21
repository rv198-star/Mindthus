# H1 candidate content path repair — 2026-10-21

## Decision and scope

Prior decision: H1-C2 canonical task completion is merged, while the trusted Host
integration is still blocked. The AIWork ancestor-swap probe demonstrated that
`_content_path` checks followed by a string-path `open(O_NOFOLLOW)` can follow a
replaced ancestor outside the selected candidate store. A matching SHA does not
establish that the file was read from the selected Mission.

The Owner corrected recovery to the AgentTeam conversation, then explicitly
requested “继续完成吧”. This slice continues the existing H1 implementation by
repairing candidate storage in `tplan_h1_commands.py`. It does not provision Host
trust, enable services, install a runtime, deploy, touch Media, or release #124.

## Implementation

Open the selected absolute Mission directory component by component with
`O_DIRECTORY | O_NOFOLLOW`, then hold directory descriptors for `artifacts/h1`.
Use descriptor-relative directory creation, file opens, publication, cleanup and
fsync. Read an opened regular file with a bounded read and verify its immutable
SHA. Refuse hardlinked leaf files, symlink leaves/ancestors, nonregular files,
oversized/growing bytes and unsupported secure filesystem primitives. The path
constructor will only express the canonical relative layout, never confer trust.

The protected Host must still own the Mission and its ancestors. Descriptor pinning
prevents path substitution from redirecting this operation; it cannot establish
Member/Host OS isolation or stop an authorized writer from mutating storage later.

## Acceptance

- A real temporary-filesystem reproduction of the prior ancestor swap is rejected.
- Replacement during read/staging cannot read or write the outside directory;
  stable eligible candidates retain round-trip and idempotent storage behavior.
- Leaf symlinks, ancestor symlinks, hardlinks, FIFO/nonregular files and oversized
  files are rejected; a file that grows after initial stat remains bounded.
- Failure cleanup stays in the held store and closes acquired descriptors.
- New path tests and affected H1 core/completion tests pass on the changed source.
  Existing full-suite results are historical, not rerun or relabeled.
- Parent integration runs the real canonical H1 synthetic chain on this source;
  that is filesystem/protocol evidence, not a real Owner or DSH live E2E claim.
