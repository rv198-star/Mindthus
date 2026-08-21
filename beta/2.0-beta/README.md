# Mindthus 1.8.0 ROI Beta (GPT/Sol) package

Status: source tag `v1.8.0-roi-beta` is the synchronized supplemental experimental asset
for the existing `v1.8.0` GitHub Release. Marketplace publication remains absent.

This checkpoint composes two controlled inputs:

- Shared Product Core: Mindthus `1.8.0` / `42887387800806b08796c5972590272414c28c97`.
- Runtime Profile: qualified ROI.2 behavior plus the bounded v1.8.0 Root-Cause Replacement thin-entry adaptation.

The historical ROI.2 implementation and qualification remain immutable. The v1.8.0
adaptation does not modify that frozen tree: it supplies a new compact `using-mindthus`
overlay that keeps the ROI.2 routing floor while adding the shared-core recovery rule:
after evidence confirms a wrong canonical rule or owner, replace it directly, remove
obsolete exceptions, state the intended mainline positively, and keep real vetoes
explicit. Clear local bugs still remain local.

The assembly uses the separate `mindthus-beta` package and marketplace identities and
retains the previously qualified one-sentence 3L5S Anti-Spiral correction. All other
packaged capabilities come from the exact v1.8.0 Stable shared core before namespace
isolation, including Root-Cause Replacement, WAE Ownership Closure, competitive-frame
convergence, Judgment Trace, Case Export, case-prep, Test Lifecycle and TPlan.

All textual plugin namespace references are rewritten to `mindthus-beta:` and the
packaged runtime diagnostic inspects Beta coordinates only.

Build from a clean `v1.8.0-roi-beta` source checkout:

```bash
python3 beta/2.0-beta/build-internal-beta.py \
  --out /tmp/mindthus-1.8.0-roi-beta-marketplace \
  --archive /tmp/mindthus-beta-1.8.0-roi-beta.tar.gz
```

The command creates an inspectable Codex marketplace directory, a byte-reproducible
archive and a one-asset checksum file. It does not install, upload or publish.

Rollback target: the paired `v1.8.0` Stable plugin package. Stable and ROI Beta share one
GitHub Release but use different package, marketplace, cache and skill namespaces. The
ROI package remains experimental and does not replace Stable.
