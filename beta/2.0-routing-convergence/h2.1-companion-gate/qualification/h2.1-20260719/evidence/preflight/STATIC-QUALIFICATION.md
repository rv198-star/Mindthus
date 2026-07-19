# H2.1 Static Qualification

Date: 2026-07-19

Result: `PASS / LIVE NOT STARTED`

## Source boundary

- branch: `codex/2.0-h2-companion-gate`
- base and fetched predecessor tip:
  `11e3d43e2e735cfc1a5898315fd4e60fa7c0064f`
- profile: `2.0-routing-h2-single-entry`
- candidate identity: `mindthus-beta / 2.0.0-next.4 / h2.1-companion-gate`
- canonical Stable owner sources changed relative to the base: zero
- built topology: one discoverable `using-mindthus/SKILL.md`, seven resource owners,
  no Hook, `defaultPrompt`, second Skill, AGENTS carrier, model route, or semantic router

The exact candidate commit is assigned after this report and the frozen protocol are
committed. A separate candidate lock records that immutable commit and a clean rebuild
before C1.

## Authorized package diff

Only these normalized built owner paths differ from the frozen H2 owner package:

| Path | Before SHA-256 | After SHA-256 | Delta |
| --- | --- | --- | ---: |
| `skills/using-mindthus/references/owners/mpg/OWNER.md` | `67583180c0cc4c48eda1946ac5df4cb02c6f555d4d2e76195f7ff62bbe3f1c4c` | `8288099e0e0cf8d4b5583759d5b5b83516e0b0d118220a4bf6d83f8eb0fd3ef9` | -15 bytes |
| `skills/using-mindthus/references/owners/mpg/resources/methodology.md` | `df2ada6a8f4b707ca27089c2744dfd7eab3997685e49071485b46f1e21d14a6a` | `790a94ef58aafbf2725539ed00477cfd1f9a0790b8f9f7788d7d05f818d7edcd` | -87 bytes |

Total correction: `-102 bytes`. Reverse-applying only those two exact replacements
restores the frozen normalized MPG digest
`8084f8a07fb9cb30ca8c4f8f8074f3473a39c5e519d1bd3dfbfd54d269ce487f`.
All other owner locks pass unchanged.

## Reproducible build snapshot

Command:

```text
python3 scripts/build-release-pack.py \
  --out <empty-output> --package plugins \
  --release-line 2.0-routing-h2-single-entry
```

Observed clean snapshot before commit freeze:

- package files: 121
- relative-path/content tree digest: `b552d5935ffb5466702b1778d391d49c4f1d5fd5dfb6e4fdb009d091979d2934`
- owner tree digest: `acc9ca4a6353aff12c857d8a975ed8fd7e00714fc74a64b7b4c1e59ef5a149c4`
- plugin manifest: `cee68a71b80003d9a490dcd1f5cf676cc5d7d1aca1475be86f20d8e27dec89df`
- packaged release profile: `caaf2ac920f665cba6960292b3f2485cffd78312ee5c0748e2d68e1082503c1e`

The tree digest is the SHA-256 of the sorted `shasum -a 256` lines for every relative
regular-file path under the packaged plugin root. The candidate-lock rebuild must match
these values byte for byte.

## Verification

- packaged fail-closed topology diagnostic: `integrity=ok`; every check `ok`
- duplicate correction target negative test: rejected
- MPG companion text drift negative test: rejected
- focused H2 tests: 10/10 passed
- full repository tests: 646/646 passed
- Skill Creator structural validation of the built entry: `Skill is valid!`
- fixture lock: all authored contracts, inherited cases, and inherited fixtures match

## Responsibility-separated review

- build/package reviewer: `PASS`; exact two-path, -102-byte diff and deterministic
  rebuild confirmed
- causal reviewer: initially blocked a second newline variable in C2/C3; the newline was
  made identical, the fixture lock was refreshed, and re-review returned `PASS`
- comparison/budget reviewer: `PASS`; cumulative calls/tokens, repeated-inclusive loaded
  bytes, seven-case uncached-token median, cache-noise trigger, mirrored isolation, and
  unresolved-Judge closure are mutually consistent

No reviewer changed code, evidence, or Mission state.

## Claim ceiling

This proves only package integrity, static isolation shape, the exact subtractive diff,
and frozen test/protocol consistency. It does not prove live entry activation, owner
reads, passive obligations, quality, token savings, or usability. Those claims remain
gated by C1-C3, Q3-Q7, and—only after qualification—the Stable comparison.
