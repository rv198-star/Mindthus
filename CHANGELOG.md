# Changelog

## v0.4

Release date: 2026-05-09

### Added

- Added the `tplan` Linear Continuation Gate for high-impact decisions.
- Added `path_assessment` with `marginal_roi`, `path_role`, and `evidence_delta` so
  same-path continuation must expose its Mission-relative reasoning surface.
- Added Premise Calibration to `using-mindthus` and `AGENTS.md` as a pre-route action
  for stripping second-hand concepts before selecting a Mindthus skill.
- Added Mindthus router pressure tests for ROI labels, first-principles name traps,
  workflow/agent false binaries, trend slogans, and polished-artifact traps.

### Changed

- High-impact `tplan` hook output now requires `path_assessment` when the decision is
  Mission-aligned, changes active task, changes Mission status, subtracts work,
  escalates, or closes a Mission.
- `tplan` docs now state that elapsed time is not the root continuation criterion;
  marginal Mission ROI, path dominance, and expected evidence delta are the relevant
  judgment surfaces.

### Verification

- `python3 -m unittest discover tests/tplan -v`
- `python3 -m unittest tests.test_packaging_docs tests.test_mindthus_router_contract -v`
