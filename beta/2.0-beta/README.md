# Mindthus 2.0 Beta Prerelease

Status: GitHub prerelease candidate; not a Stable release or marketplace package.

This checkpoint composes two immutable inputs:

- Shared Product Core: Mindthus `1.5.1` / `16f4b9dcda7b7200f92c16274704fab5b66a9e4c`
- Runtime Profile: ROI.2 implementation / `493f9520b75f582aa22f6c8647ec08eab3e122d3`

ROI.2 qualification remains frozen at `4ee3e034`; the later convergence archive
`9a1c2268` is a historical decision-evidence identifier only. It is not a build
dependency and does not need to exist in a clean single-branch clone.

The assembly is identified as `2.0.0-beta.1`. It uses the separate
`mindthus-beta` package and marketplace identities, rewrites only the namespace mention
inside the inherited Codex default prompt, replaces the full `using-mindthus` entry with
the frozen ROI.2 overlay, and applies the one qualified 3L5S Anti-Spiral sentence
replacement. All other packaged product capabilities come from the named 1.5 shared
core Git object. All textual plugin namespace references are rewritten to
`mindthus-beta:` and the packaged runtime diagnostic inspects Beta coordinates only.

Build locally:

```bash
python3 beta/2.0-beta/build-internal-beta.py \
  --out /tmp/mindthus-2.0-beta.1-marketplace \
  --archive /tmp/mindthus-beta-2.0.0-beta.1.tar.gz
```

This command requires a clean checkout and builds both an inspectable Codex marketplace
directory and a byte-reproducible archive. It does not install into the user's
`CODEX_HOME` or update a marketplace.

Rollback target: the retained `v1.4.6` Stable plugin package. Stable and Beta use
different package, marketplace, cache, and skill namespaces and can be removed independently.
