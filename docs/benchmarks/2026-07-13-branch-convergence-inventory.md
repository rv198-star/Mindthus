# Brake Research Branch Convergence Inventory

Date: 2026-07-13

Compared branches:

- stable baseline: `main` / `origin/main` at
  `d6ab0dc97ce911417542910fbf3f5c9827c59881`
- research archive: `codex/brake-semantic-triage-design` at
  `f820a8985ba84ce28d67ce9003c893d9da34862a`
- merge base: `d6ab0dc97ce911417542910fbf3f5c9827c59881`

## Executive Decision

Do not merge the research branch wholesale into `main`.

The branch is 65 commits ahead and zero commits behind, but almost all of its size is
diagnostic evidence and brake-specific benchmark machinery. It changes no file under
`skills/`, so it does not directly alter the user-facing Mindthus methods. Its useful
production residue should be recovered selectively on a clean branch from `main`.

## Inventory

The full branch diff contains:

| Surface | Count or size | Disposition |
| --- | ---: | --- |
| Total changed files | `24,275` | Never merge as one unit |
| Added lines | `1,281,784` | Dominated by generated evidence |
| Deleted lines | `162` | Small relative to archive volume |
| Added run-artifact files | `24,230` | Keep only on the research archive branch |
| Non-run files | `45` | Review individually |
| Checked-out `docs/benchmarks/runs` size | about `263 MB` | Includes earlier baseline evidence as well as branch additions |
| `skills/` changes | `0` | No direct product-method behavior delta |

The 45 non-run files divide into:

| Class | Files | Notes |
| --- | ---: | --- |
| Plugin visual assets | `4` | Two PNG delivery assets and two SVG sources |
| Scripts | `2` | Release pack builder and judgment benchmark runner |
| Tests and executable fixtures | `7` | Packaging, runner, benchmark-contract tests, and four brake fixtures |
| Benchmark docs outside `runs/` | `30` | Designs, prompts, policies, manifests, proposals, and closure record |
| Other design docs | `2` | Freeze plan and icon design record |

The source-and-test delta outside generated runs is still substantial: `4,415`
insertions and `151` deletions across 13 script, test, fixture, and asset files. Of that,
the brake runner adds about `1,994` changed lines and its runner contract test adds about
`2,333` changed lines.

## Keep For Main

### 1. Plugin visual packaging

Candidate commit: `5ba5f530` (`feat: add Mindthus plugin icon`).

It is an independent six-file change:

- `assets/mindthus-icon.png`
- `assets/mindthus-icon.svg`
- `assets/mindthus-logo.png`
- `assets/mindthus-logo.svg`
- `scripts/build-release-pack.py`
- `tests/test_packaging_docs.py`

Verification against a temporary clean snapshot of `main`:

- the commit patch applies cleanly;
- `python3 -m unittest tests.test_packaging_docs -q` passes `32/32`.

This is the only complete commit currently suitable for direct selective integration.

### 2. Timeout stream normalization

Source commit: `c6c28418` (`fix: preserve byte timeout streams in benchmark runner`).

The useful part is a small generic fix in the benchmark runner: normalize byte-valued
`TimeoutExpired.stdout` and `.stderr` before writing text artifacts. Its focused test
also applies cleanly to `main`.

Verification against the same temporary `main` snapshot:

- the two-file script/test patch applies cleanly;
- `python3 -m unittest tests.test_judgment_benchmark_cli_runner -q` passes `42/42`.

Do not cherry-pick the whole source commit because it also advances a brake shadow
handoff manifest that does not belong on `main`. Reapply only the script and focused
test on a clean integration branch.

## Preserve Only As Research Evidence

### Brake triage runner architecture

Keep the semantic sub-judgment, owner exposure gate, pressure latch, scalar-free fire
policy, k=3 voting, loaded-action payload, and dual-path V0.2 contract on the archive
branch. These changes are well tested as benchmark machinery, but they are specific to
the closed brake research line and are not production Mindthus runtime.

This includes the large accumulated delta in:

- `scripts/run-judgment-benchmark-cli.py`
- `tests/test_judgment_benchmark_cli_runner.py`
- the four brake JSONL fixtures
- prompt, policy, threshold, handoff, and action-contract documents

### Raw campaigns and incidents

Keep the compact `docs/benchmarks/runs/**` evidence spine on the archive branch. Reports,
manifests, aggregate results, focused extracts, invalid-attempt summaries, and decisive
redline evidence preserve the research conclusions without carrying the full runtime
checkout cost.

The 23,847 generated prompt, response, event, stderr, judge, and intermediate files were
removed from the branch tip after closure. They remain recoverable from
`6efeda766c47d1606191b872d72e2bd1ccb8b087`; see
[`runs/ARCHIVE-POLICY.md`](runs/ARCHIVE-POLICY.md). This remains archive-only evidence and
must not be merged wholesale into `main`.

### Prompt V0.6 and permanent-baseline packet

Retain these as inactive text artifacts. They were never converted into executable
fixtures or activated in the runner. They must not enter `main` as an implied behavior
repair or certification result.

## Do Not Cherry-Pick Directly

- `f820a898` closure documentation depends on reports that are not present on `main`.
  A future public status update should be a compact standalone note, not a partial copy
  with broken local evidence links.
- `c810a0cd` judge retry is useful in principle but is interleaved with the triage runner
  generation. Reconsider it only when the base benchmark runner produces a real retry
  failure; then implement the smallest generic version directly on `main`.
- `a26006c8` xhigh pin solved a campaign-specific provider contract change. The base
  `main` runner does not currently force the obsolete value, so no compatibility patch
  is required there.
- All threshold, prompt, majority, owner-gate, and loaded-action commits are research
  dependencies, not independent mainline features.

## Clean Integration Sequence

When integration is authorized, use a new branch from `main` rather than merging or
rebasing the research archive:

1. Cherry-pick `5ba5f530` and run packaging plus full repository tests.
2. Reapply only the two-file timeout normalization from `c6c28418`; run the focused
   runner test and the full repository suite.
3. Add no brake fixture, prompt, policy, handoff manifest, or raw run artifact.
4. Keep `codex/brake-semantic-triage-design` as a remote evidence archive.
5. Treat any compact public closure note as a separate documentation decision.

This sequence recovers the small durable value without importing the stopped research
loop into the product branch.
