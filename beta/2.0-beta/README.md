# Mindthus 1.6.0 ROI Beta (GPT/Sol) package

Status: source tag `v1.6.0-roi-beta` is the supplemental experimental ROI package in
the same `v1.6.0` GitHub Release as Stable. Marketplace publication remains absent.

This checkpoint composes two immutable inputs:

- Shared Product Core: Mindthus `1.6.0` / `cb7057957660f042aff09a180cf0a9633e65088f`
- Runtime Profile: ROI.2 implementation / `493f9520b75f582aa22f6c8647ec08eab3e122d3`

ROI.2 qualification remains frozen at `4ee3e034`; the later convergence archive
`9a1c2268` is a historical decision-evidence identifier only. It is not a build
dependency and does not need to exist in a clean single-branch clone.

The assembly is identified as `1.6.0-roi-beta`. It uses the separate `mindthus-beta`
package and marketplace identities, replaces the full `using-mindthus` entry with the
frozen ROI.2 overlay, and applies the one qualified 3L5S Anti-Spiral sentence
replacement. All other packaged capabilities come byte-for-byte from the named v1.6.0
Stable shared core before namespace isolation. This includes Judgment Trace v1.1,
Case Export v1, `case-prep`, case collections, Test Lifecycle support, and the retained
TPlan runtime generation.

All textual plugin namespace references are rewritten to `mindthus-beta:` and the
packaged runtime diagnostic inspects Beta coordinates only.

Build locally from a clean `v1.6.0-roi-beta` checkout:

```bash
python3 beta/2.0-beta/build-internal-beta.py \
  --out /tmp/mindthus-1.6.0-roi-beta-marketplace \
  --archive /tmp/mindthus-beta-1.6.0-roi-beta.tar.gz
```

This command creates an inspectable Codex marketplace directory, a byte-reproducible
archive, and a one-asset checksum file. It does not install into the user's
`CODEX_HOME`, upload anything, or update a marketplace.

Rollback target: the paired `v1.6.0` Stable plugin package. Stable and ROI Beta belong
to one v1.6.0 GitHub Release, use different package, marketplace, cache, and skill
namespaces, and can be installed or removed independently. The ROI package remains
explicitly experimental and is not a replacement for Stable.
