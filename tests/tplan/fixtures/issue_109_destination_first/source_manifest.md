# Issue #109 Destination-First Research: Source Manifest

## Purpose

This manifest makes the #109 replay inputs inspectable without pretending that a
committed test fixture independently verifies historical Mission interpretation.

The committed [replay input fixture](replay_inputs.json) is the deterministic,
owner-curated coding used by the harness. It was distilled from the anchors below.
The harness does not parse the historical snapshots at run time; that choice keeps
the test deterministic and exposes the interpretation for review rather than
presenting it as automated fact extraction.

## Public anchors

- V5 follow-up issues: [#104](https://github.com/rv198-star/Mindthus/issues/104),
  [#105](https://github.com/rv198-star/Mindthus/issues/105),
  [#106](https://github.com/rv198-star/Mindthus/issues/106),
  [#107](https://github.com/rv198-star/Mindthus/issues/107), and
  [#108](https://github.com/rv198-star/Mindthus/issues/108).
- TVG value-profile Mission: [#31](https://github.com/rv198-star/Mindthus/issues/31).
- Repository baseline contracts are read directly by
  `tests/tplan/destination_first_discovery_experiment.py` from
  `skills/tplan/resources/schema.md`, `hooks.md`, `lifecycle.md`, and
  `skills/tplan/scripts/tplan_runtime.py` at the checked-out revision.

## Locally captured runtime anchors

These runtime files were intentionally ignored by the repository when the research
was run. Their recorded SHA-256 values provide a content identity for the source
snapshots, but not public availability or independent historical verification.

| Local path | SHA-256 | Use in replay |
| --- | --- | --- |
| `.tplan/missions/mission-v5-targeted-stabilization/mission.json` | `d3547cd8965cd80727ee40edfc1e49563a279ab746ba6470599ee834aae87a11` | V5 root Task count and identity |
| `.tplan/shared_contexts/tplan_mission_shared_context-mission-v5-targeted-stabilization.md` | `72ce07cbedd93182aebb73e8fdd852cf45bb90e04f2f782976bd860e3919f3fe` | V5 Shared Context finding count |
| `.tplan/missions/issue-31-tvg-value-profiles-run/mission.json` | `70d7cfee0b3d11ff67eb9ac980fe4c91d83aa5224c58f0ac7cb1d7571add2081` | Issue #31 initial Task shape |
| `.tplan/missions/issue-31-tvg-value-profiles-run/evidence.jsonl` | `65499f1b83e6cda141ae39b88f32d8e034fa1aed071727f70867b17c49bdd402` | Issue #31 clean-room evidence finding |
| `.tplan/missions/issue-31-tvg-value-profiles-run/logs/task-pilot-loop.jsonl` | `5f590c2c72f229a4225e45f91981ca328299499e9a630434b3424c9554db6e99` | 18-panel delivery correction |
| `.tplan/missions/mainline-path-game-tvg-2026-06-08-run/mission.json` | `fcbbf11862ad9ccee8ec1fe12a0724b5f2a1d3961314382cd8436cc9334ce9e1` | MPG initial/terminal Task coherence |
| `.tplan/missions/mainline-path-game-tvg-2026-06-08-run/mainline-path-game-tvg-analysis.md` | `2a5a962b72ad852cdfca4fcd50cf3794df8c37cc6f092d10c727e69aa8b6605c` | MPG negative-control interpretation |

## Reproduction

From a checkout of the commit that contains this fixture:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.tplan.test_destination_first_discovery_experiment -v

python3 tests/tplan/destination_first_discovery_experiment.py \
  --source-root . \
  --output-dir /tmp/issue-109-destination-first
```

The first command verifies the committed reduced result in
[expected_result.json](expected_result.json). The second writes a full
`simulation_result.json` report. Its `source_root` field is environment-specific, so
the reduced result fixture is the byte-stable comparison surface.

## Claim boundary

The fixture makes the product decision and its assumptions reviewable and mechanically
reproducible. It does not upgrade the historical replay assertions from owner-reported
evidence to independently reproduced evidence. It therefore supports the no-go
decision without claiming a stronger proof level than the sources permit.
