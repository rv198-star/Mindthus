# Collection Mode

Use when the user explicitly asks to export all current Mindthus-related cases.

## Candidate Selection

Keep only bounded, reusable events:

- judgment failure or repair;
- material value delta;
- routing ambiguity;
- regression-test candidate;
- named benchmark case;
- current TPlan blocker, acceptance, continuation, authority, recovery, provenance, or telemetry event.

Do not include ordinary acknowledgements, implementation progress without a judgment
failure, or repeated turns that describe the same root event. Prefer omission over
inventing a weak case.

## Mainline

1. Build each case through its existing judgment, benchmark, or TPlan adapter.
2. Keep every package independently valid and review-required.
3. Run collection packaging with repeated `--case-dir` arguments.
4. Return one collection archive plus a short inventory.

The collection is an index and delivery envelope. It is not one combined Judgment
Trace and does not merge TPlan runtime state into judgment data.

## Limits

- maximum 20 cases per collection;
- no automatic upload;
- no raw conversation dump;
- no full TPlan runtime dump;
- duplicate paths and duplicate case IDs are blocked;
- every nested case is revalidated before packaging and when validating the collection.
