# Invalid Attempt: System Scratch Disk Exhaustion

Status: excluded from all `n=3` evidence and every gate denominator.

The first manually restarted `valid-repeat-1` used `/private/tmp` for isolation scratch.
The system data volume reached 100% capacity while plugin synchronization attempted to
write its temporary cache. The captured stderr contains eight `No space left on device`
markers. The runner and its remaining child processes were stopped before judging began;
the directory contains 217 preserved partial artifacts.

This is an infrastructure failure, not a model result. The subsequent valid campaign
restarts from zero at `valid-repeat-1/` with only runtime scratch relocated to the
external volume; runner, prompt, fixtures, gate, model selections, and all measured
fingerprints remain unchanged.
