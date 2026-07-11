# INVALID-ATTEMPT: judge parse-failure stop threshold

Status: invalid; do not score or aggregate.

The generator phase completed all 31 original-fixture records. The first judge
pass stopped during telemetry aggregation, so its raw judge artifacts were
preserved under `original/invalid-judge-attempt-list-telemetry-20260711T154412+0800/`.
A judge-only recovery pass then completed the aggregation fix, but produced
double parse failures for `brake-triage-n07` through `brake-triage-n15`.

The pre-registered stop rule requires global stop when a normal-quota run
accumulates three cases with two empty/unparseable judge JSON attempts. That
threshold was crossed before the judge-only pass completed. Its fallback score
zeros are therefore transport failures, not negative-control behavior scores.

Do not use this attempt for any of the six dev gates. No expansion fixture or
repeat-2/repeat-3 run was started. All generator, triage, action, judge, retry,
and contamination artifacts remain preserved for audit.
