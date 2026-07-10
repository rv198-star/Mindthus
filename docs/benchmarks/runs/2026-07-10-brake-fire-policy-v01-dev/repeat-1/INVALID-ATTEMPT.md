# Invalid Attempt: Judge Quota Exhaustion

Status: excluded from all `n=3` evidence and every gate denominator.

This initial attempt started before the quota recovered. Generator and triage artifacts
are preserved, but the judge subprocesses returned the usage-limit response instead of
parseable rubric JSON. The run contains 37 judge record files and 78 usage-limit markers
across the original and V0.4 expansion packets. It never reached the anchor packet or
later repeats.

The runner-derived scores from this directory are not measurements: judge fallbacks can
look like zeroes while the judge was unavailable. The complete directory is retained for
traceability only. The valid campaign begins at `valid-repeat-1/` after the quota reset.
