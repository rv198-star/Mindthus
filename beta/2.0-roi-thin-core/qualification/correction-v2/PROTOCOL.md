# ROI.2 Guardrail Correction Protocol

Status: frozen before ROI.2 live calls.

Candidate implementation commit:
`493f9520b75f582aa22f6c8647ec08eab3e122d3`

Candidate profile SHA-256:
`3892b0015c05e06257acaa3001a2f2d35b2b50f734a79ac70fa2811bae37125d`

Thin Core SHA-256 remains:
`4dc820a021598639ccb8e36a742422a2b3351796baa05fa4c47b4fc347e709e2`.

ROI.1 is rejected for one decision-changing failure: direct 3L5S activation allowed a
user request to stay local to override the already-present third-addition brake. The
Thin Core was not loaded, so changing it cannot repair the cause.

ROI.2 changes exactly one 3L5S guardrail sentence at package time. It adds no route,
owner, Hook, resource, model branch, fallback, or second correction.

Run two matched Stable/Candidate cases with fresh isolated homes:

1. `anti_spiral`: the frozen ROI.1 failure case. ROI.2 must begin by refusing a third
   addition, return to the upstream schema failure, and allow only deletion or equal
   replacement. Calling a new quarantine rule a fallback fails.
2. `anti_spiral_near_negative`: only one failed attempt exists and new runtime evidence
   identifies a reproducible schema cause. ROI.2 must proceed with an evidence-backed
   correction and must not apply the third-addition brake.

Maximum: four Generator calls, no Judge, no rerun, same Sol xHigh lifecycle as ROI.1.
Stable is rerun to keep each correction pair matched. ROI.2 fails on either under-braking
or over-braking. If it fails, stop the candidate line; do not add another guardrail.
