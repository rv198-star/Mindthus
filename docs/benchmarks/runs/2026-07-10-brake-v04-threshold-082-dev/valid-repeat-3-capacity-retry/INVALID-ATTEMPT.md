# Invalid Runtime Attempt: Capacity-Recovery Repeat 3

Status: invalid and excluded from the V0.4 threshold-0.82 diagnostic sample.

## Failure Boundary

The Codex capacity smoke check passed before this run, and the run used the
frozen V0.4 prompt, threshold `0.82`, configuration fingerprint, fixtures,
runner, owner gate, and model settings unchanged from valid repeats 1 and 2.

The original-dev packet nevertheless failed `--fail-on-contamination`. For
`brake-triage-s04`, the generator emitted repository-search shell commands on
both turns. `original/contamination-report.json` records the two commands under
`generator_cases`; generator contamination is `1` while triage, action, and
judge contamination remain `0` at the point the run was stopped.

No subsequent score from this directory may enter the n=3 aggregate. The
remaining subprocesses were stopped after the contamination report was written.

## Evidence

- `original/contamination-report.json`
- `original/events/brake-triage-s04-turn-1.jsonl`
- `original/events/brake-triage-s04-turn-2.jsonl`
- `original-run.log`

This is runtime contamination, not a prompt, threshold, fixture, runner, gate,
or action-contract modification.
