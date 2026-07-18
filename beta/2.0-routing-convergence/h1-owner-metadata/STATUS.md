# Mindthus H1 Owner Metadata Candidate

Status: `H1_REJECTED / unpublished / route closed`

This Codex-only candidate tests whether precise native Skill discovery metadata can
remove the two owner false positives observed in N3 while retaining direct owner recall.
It is a new profile built from `f9117426`; it does not repair or inherit the rejected
candidate's status.

Candidate A passed the WAE positive and near-negative probes but failed the missing
decision-context probe by loading 3L5S and recommending a pause. The one permitted
correction therefore adds a package-time 3L5S description replacement grounded in its
existing body domain. See `CORRECTION.md` in the source tree. The thin entry, all seven
owner bodies, the other four owner descriptions, the topology, and the neutral plugin
prompt remain unchanged.

The correction preserved 3L5S recall and eliminated every owner load on the fresh
missing-context case. H1 still failed: after reading only the thin entry, Codex stated
`hold the migration` before obtaining the answer-changing context. Owner metadata can
control discovery precision, but it cannot make an already injected thin entry obey the
required decision sequencing. No further H1 correction is allowed. See
`qualification/h1-20260719/RESULT.md`.

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
