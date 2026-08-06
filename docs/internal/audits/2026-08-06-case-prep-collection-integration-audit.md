# Case Prep Collection Integration Audit — 2026-08-06

## Scope

Independent integration review of the `case-prep` collection mode across repository,
release packaging, runtime fingerprints, CLI behavior, skill routing, and regression
coverage.

## Checks

### Explicit-only skill boundary

`case-prep` remains an explicit tool skill. The all-current phrase is documented inside
the skill and README, but `using-mindthus` passive owner routing is unchanged. Collection
mode does not become a judgment method or route owner.

### Supported package layouts

The release-pack test builds and executes `case-prep` in:

- Codex plugin;
- Claude Code plugin;
- Claude portable skills;
- Codex portable skills;
- OpenCode portable skills.

Each layout creates a Judgment case and then packages it through `collection`, producing
one local archive with `item_count=1` and the required manual-review flags.

### Runtime fingerprint

`case-collection.schema.json` is included in the runtime fingerprint surface. Missing or
mismatched collection contracts therefore fail strict installed-runtime diagnostics.

### CLI and validator

The main entry exposes:

```text
prepare_case.py collection --case-dir ...
```

The shared packet validator auto-detects TPlan packets and case collections. Both JSON
and human-readable output retain the sharing boundary.

### Test lifecycle

No new executable test file was added. The existing `tests/test_case_prep.py` group
continues to be registered exactly once. Registry validation reports 69 of 69 executable
test files covered.

### Full regression

```text
Ran 853 tests in 87.468s
OK (skipped=5)
```

Targeted checks also covered:

- Judgment + TPlan mixed collection;
- duplicate ID rejection;
- nested tamper rejection;
- collection JSON Schema validation;
- malformed manifest routing;
- one-archive CLI result;
- five release layouts;
- strict runtime fingerprint;
- Python compilation and `git diff --check`.

## Boundary

The successful integration proves package shape, release availability, and regression
compatibility. It does not prove that an agent will always identify every meaningful
case or that every included candidate is analytically valuable. Candidate selection
remains an agentic, reviewable judgment.

## Verdict

Accepted. Collection mode is compatible with all supported release layouts, preserves
explicit invocation and contract separation, and passes the full repository regression
suite.
