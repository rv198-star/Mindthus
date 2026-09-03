# v1.9.0 ROI Beta — SRA Compatibility Qualification

Status: pre-registered before qualification execution.

## Goal

Qualify the smallest ROI runtime change required to synchronize the v1.9.0 Stable SRA
capability into the ROI.2 thin `using-mindthus` entry without copying SRA implementation,
changing the historical ROI.2 3L5S correction, or exceeding the 2300-byte entry Gate.

## Candidate

- Stable shared core: `v1.9.0` / `3dfbd563315b761bae0ea2d1a9e0f04d9ff1b946`.
- Historical ROI.2 behavior remains frozen at implementation `493f9520` and qualification
  `4ee3e034`.
- New overlay implementation: `0bd58701fd36f33d5640ff2d00aa5e208026dbfa`.
- Overlay path: `beta/2.0-beta/overlays/using-mindthus-v1.9.0-sra/SKILL.md`.

## Acceptance gates

1. Thin Core remains <= 2300 bytes.
2. Existing thin-floor obligations remain present: frame/whole, decision context,
   evidence ceiling, Anti-Spiral, one-thesis boundary, and direct-execution boundary.
3. Multiple judgeable candidates sharing one scarce resource route to SRA.
4. Missing comparison facts, one obvious action, independent resources, or adjacent-owner
   problems do not become SRA solely because the prompt says “priority”.
5. The historical ROI.2 3L5S correction remains exact and unchanged.
6. All non-declared-delta packaged files remain byte-identical to v1.9.0 Stable after
   normalizing `mindthus-beta:` back to `mindthus:`.
7. SRA Skill, public methodology, templates, scripts and context-isolation contract are
   inherited from the exact Stable shared core.
8. Beta identity/namespace is isolated and archive composition remains reproducible.

## Behavioral cases

Five Stable/Beta cases are registered in `cases.json` for later matched model runs:

- two judgeable candidates share one engineer-day -> SRA;
- named tasks use independent resources -> direct, not SRA;
- candidates share time but outcome evidence is missing -> evidence-first / blocked;
- one selected mainline needs exposure and exit conditions -> MPG, not SRA;
- a third local repair releases time across candidates -> Anti-Spiral first, then SRA.

The deterministic qualification verifies composition and semantic markers; it does not
execute these model cases. Stable v1.9.0 has separate natural-wakeup acceptance evidence.
Until matched Beta calls are run, release notes must not claim a Beta-specific wake-up
rate, relative model-quality gain, or Token-ROI improvement.
