# Case Prep Contract And Privacy Audit — 2026-08-06

## Scope

Independent review of `case-prep` data boundaries, consent flags, archive behavior,
Judgment/TPlan separation, excerpt handling, and validator failure modes.

## Review Questions

- Can the skill activate without an explicit user request?
- Can a package upload or submit itself?
- Can Judgment Trace and TPlan runtime contracts be silently merged?
- Can raw Mission, evidence payload, execution trace, or private runtime files enter a
  TPlan packet under another filename?
- Can output mutate or pollute the Mission runtime?
- Can unsafe excerpts, symlinks, path traversal, or malformed JSON bypass validation?
- Can archive naming collide or overwrite another case?

## Findings And Repairs

### 1. Archive suffix replacement could collide for dotted case IDs

Initial use of `Path.with_suffix()` changed `mindthus-case-case.prep.v1` into an archive
name that dropped the final dotted segment.

Repair: archive names now append `.tar.gz` to the complete package directory name.

Regression: `test_archive_name_preserves_dotted_case_id`.

### 2. Default TPlan IDs used only second-level timestamps

Two preparations in one second could select the same package path.

Repair: default IDs now include a random local suffix.

Regression: `test_tplan_default_ids_are_collision_resistant`.

### 3. Filename checks alone did not stop renamed full runtime content

A user could explicitly select `mission.json` after renaming it to a text excerpt.

Repair: validators now detect bounded content signatures for full Mission shape, raw
Evidence payload shape, and execution-trace span shape, independent of filename.

Regression: `test_tplan_validator_blocks_renamed_full_runtime_content`.

### 4. TPlan output could be placed inside the Mission directory

Writing a packet under the Mission would mutate/pollute the runtime even though the
read path was bounded.

Repair: TPlan mode fail-closes when the output root is the Mission directory or any of
its descendants.

Regression: `test_tplan_output_cannot_be_written_inside_mission_runtime`.

### 5. Tampered malformed JSON could raise instead of returning findings

Repair: packet validation now converts read, UTF-8, and JSON failures into structured
blocking findings.

Regression: `test_tplan_validator_returns_finding_for_malformed_json`.

### 6. Manifest subcontracts needed stricter consistency checks

Repair: consent/privacy/source/selection/link/files indexes are constrained; selected
IDs, trace links, excerpt indexes, privacy flags, and scan status must match actual
package contents.

## Confirmed Boundaries

- `case-prep` frontmatter and SKILL require explicit invocation.
- `using-mindthus` has no passive `case-prep` owner route.
- `automatic_upload` is always false and tampering is blocking.
- Judgment mode reuses Judgment Trace v1.1 / Case Export v1.
- TPlan mode uses an independent `tplan.case-packet.v1` manifest.
- TPlan packet output contains no event payload, full Mission, task tree, Evidence
  stream, step logs, execution trace, or telemetry stream.
- Optional Judgment Trace remains a separate file and contract.
- Excerpts require explicit selection and redaction confirmation.
- Archives contain one generated package root and reject symlinks.

## Verification

```text
python3 -m unittest tests.test_case_prep -v
12+ adversarial and contract tests passed during the audit cycle
```

The final complete suite result is recorded in the integration/release audit.

## Verdict

Passed after repairs. Structural and pattern checks do not prove anonymity or semantic
case relevance; manual review remains mandatory.
