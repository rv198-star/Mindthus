# v1.8.0 ROI Beta — Root-Cause Replacement Compatibility Qualification

Status: pre-registered before qualification execution.

## Goal

Qualify the smallest ROI runtime change required to synchronize the v1.8.0 Stable
Root-Cause Replacement capability into the ROI.2 thin `using-mindthus` entry without
changing owner routing, the historical ROI.2 3L5S correction, or the 2300-byte entry Gate.

## Candidate

- Stable shared core: `v1.8.0` / `42887387800806b08796c5972590272414c28c97`.
- Historical ROI.2 behavior remains frozen at implementation `493f9520` and qualification
  `4ee3e034`.
- New overlay implementation: `64df52651fcc710929ec5fff0e629eedd7b38b2a`.
- Overlay path: `beta/2.0-beta/overlays/using-mindthus-v1.8.0-rcr/SKILL.md`.

## Acceptance gates

1. Thin Core remains <= 2300 bytes.
2. Existing thin-floor obligations remain present: frame/whole, decision context,
   evidence ceiling, Anti-Spiral, one-thesis boundary, and direct-execution boundary.
3. RCR is visible in the thin entry only after evidence confirmation: wrong canonical
   rule/owner -> direct replacement + obsolete-exception removal.
4. Affirmative mainline does not erase real vetoes; local bugs remain local.
5. The historical ROI.2 3L5S correction remains exact and unchanged.
6. All non-declared-delta packaged files remain byte-identical to v1.8.0 Stable after
   normalizing `mindthus-beta:` back to `mindthus:`.
7. Root-Cause Replacement primitive docs, runtime manifest, WAE and TVG integrations are
   inherited from the exact Stable shared core.
8. Beta identity/namespace is isolated and archive composition remains reproducible.

## Behavioral cases

Four matched Stable/Beta live cases are pre-registered in `cases.json`:

- repeated permission exceptions -> canonical authorization owner replacement;
- explicit local initialization bug -> local fix, no architecture expansion;
- double-negative high-risk deletion rule -> positive mainline + explicit hard veto;
- one failed attempt with new causal evidence -> ordinary debugging, no third-touch brake.

Live model calls use `gpt-5.6-sol / xhigh` when authenticated Codex runtime is available.
If the release environment lacks Codex authentication, that fact must be recorded as a
qualification limitation; deterministic composition gates still run, and release notes
must not claim fresh live-model superiority evidence.
