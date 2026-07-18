# Mindthus H1 Owner Metadata Candidate

Status: `UNPUBLISHED / STATIC QUALIFIED / LIVE QUALIFICATION PENDING`

This Codex-only candidate tests whether precise native Skill discovery metadata can
remove the two owner false positives observed in N3 while retaining direct owner recall.
It is a new profile built from `f9117426`; it does not repair or inherit the rejected
candidate's status.

The only intended behavioral delta is package-time replacement of the WAE and MPG
frontmatter descriptions. The thin entry, all seven owner bodies, the other five owner
descriptions, the topology, and the neutral plugin prompt remain unchanged.

Build for isolated inspection:

```bash
python3 scripts/build-release-pack.py \
  --release-line 2.0-routing-h1-metadata \
  --package plugins \
  --out /tmp/mindthus-h1-metadata
```

Then run the packaged static diagnostic. A pass proves package shape and reported
isolation only. It does not prove Skill activation, owner fidelity, passive recall,
answer quality, tokens, or latency.

Do not publish, merge, tag, enable beside Stable, modify a long-lived `CODEX_HOME`, or
treat this candidate as Beta.3.
