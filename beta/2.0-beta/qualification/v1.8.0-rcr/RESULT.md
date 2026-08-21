# v1.8.0 ROI Beta RCR Qualification Result

Verdict: **QUALIFIED FOR SYNCHRONIZED PUBLICATION — compatibility scope**.

## Deterministic evidence

The frozen candidate passed the pre-registered compatibility gates:

- Thin Core: `2292 / 2300` bytes.
- Shared Product Core: exact `v1.8.0` commit
  `42887387800806b08796c5972590272414c28c97` and tree
  `276c1df23a2503bd2a202a6d22cf6ff982c1c9d2`.
- RCR thin-entry semantics present after evidence confirmation:
  canonical rule/owner replacement, obsolete-exception removal, affirmative mainline,
  explicit real vetoes, and local-bug boundary.
- Historical ROI.2 3L5S Anti-Spiral correction remains exact.
- Root-Cause Replacement primitive/runtime manifest and WAE/TVG integrations are inherited
  from Stable shared core.
- Every non-declared-delta plugin file is byte-identical to v1.8.0 Stable after Beta
  namespace normalization.
- Beta package namespace is isolated.
- Packaged runtime diagnostic `--strict`: `status=ok`, all tracked files present, all
  required markers present, all available hashes match.
- Two independent archive builds were byte-identical.
- Qualification archive SHA-256:
  `9396bc2baf7b08a3248deedece171d3b8355aa8734880a1d1926dbdde3d884e3`.

## Live-call boundary

Four matched Stable/Beta `gpt-5.6-sol / xhigh` cases were pre-registered. Fresh Codex
calls could not run on the OCI release node because that node has no Codex API credential;
a smoke call returned HTTP `401 Unauthorized` before model execution.

This is recorded as an environment limitation, not converted into a behavioral PASS.
The release therefore makes **no fresh claim** that v1.8.0 ROI Beta improves model quality,
win rate, or token ROI over v1.7.1 ROI Beta. Historical ROI.2 live qualification remains
the evidence for the thin-core runtime shape; the new v1.8.0 qualification is limited to
RCR compatibility, exact shared-core inheritance, negative-boundary preservation, package
composition and reproducibility.

## Publication decision

The v1.8.0 change is a shared-product-core capability that intersects the thin entry.
The bounded overlay restores that shared RCR recovery semantic without adding a route,
owner, Hook, fallback or second 3L5S correction. Deterministic qualification shows no
structural regression and preserves the existing ROI.2 boundaries.

Under that claim ceiling, `v1.8.0-roi-beta` is accepted as the synchronized experimental
asset for Stable `v1.8.0`.
