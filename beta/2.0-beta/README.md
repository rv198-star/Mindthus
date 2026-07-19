# Mindthus 1.5.1 ROI Beta (GPT/Sol) package

Status: source tag `v1.5.1-roi-beta` is frozen; it is the ROI package in the same
1.5.1 release train as Stable. GitHub Release and marketplace publication remain absent.

This checkpoint composes two immutable inputs:

- Shared Product Core: Mindthus `1.5.1` / `144954531bbe34a2ed05d5d981cdbc3eb92d1f8d`
- Runtime Profile: ROI.2 implementation / `493f9520b75f582aa22f6c8647ec08eab3e122d3`

ROI.2 qualification remains frozen at `4ee3e034`; the later convergence archive
`9a1c2268` is a historical decision-evidence identifier only. It is not a build
dependency and does not need to exist in a clean single-branch clone.

The assembly is identified as `1.5.1-roi-beta`. It uses the separate
`mindthus-beta` package and marketplace identities, rewrites only the namespace mention
inside the inherited Codex default prompt, replaces the full `using-mindthus` entry with
the frozen ROI.2 overlay, and applies the one qualified 3L5S Anti-Spiral sentence
replacement. All other packaged product capabilities come from the named 1.5 shared
core Git object. All textual plugin namespace references are rewritten to
`mindthus-beta:` and the packaged runtime diagnostic inspects Beta coordinates only.

Build locally:

```bash
python3 beta/2.0-beta/build-internal-beta.py \
  --out /tmp/mindthus-1.5.1-roi-beta-marketplace \
  --archive /tmp/mindthus-beta-1.5.1-roi-beta.tar.gz
```

This command requires a clean checkout and builds both an inspectable Codex marketplace
directory and a byte-reproducible archive. It does not install into the user's
`CODEX_HOME` or update a marketplace.

Rollback target: the paired `v1.5.1` Stable plugin package (or the retained `v1.4.6`
Stable package). If future publication is authorized, both packages belong to one 1.5.1
GitHub Release; the ROI package remains explicitly experimental. Stable and ROI Beta use
different package, marketplace, cache, and skill namespaces and can be removed independently.
